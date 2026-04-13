#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

import requests
import serial

BAUD = 115200
READ_TIMEOUT_S = 0.2
PROBE_SECONDS_PER_PORT = 1.5

MIN_M = 0.0
MAX_M = 20.0
UPLOAD_DELTA_M = 0.3

CSE_BASE = "http://localhost:8081"
CSE_ID = "id-mn"
CSE_NAME = "cse-mn"
ORIGIN = "CAdmin"
AE_NAME = "CAdmin"
CNT_NAME = "proximity"


DEFAULT_TAG_ID = "UNKNOWN"
DEFAULT_TAG_NAME = "UnknownTag"

DIST_PATTERNS = [
    re.compile(r"^\s*DIST\s*:\s*([+-]?\d+(?:\.\d+)?)\s*$", re.IGNORECASE),
    re.compile(r"^\s*distance(?:_m)?\s*[:=]\s*([+-]?\d+(?:\.\d+)?)\s*$", re.IGNORECASE),
    re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*$"),
]

ID_PATTERN = re.compile(r"^\s*([0-9A-Fa-f]{16})\s*$")

TAG_NAME_MAP = {
     "6E4ABBD598C5AB18": "Luggage_A",
     "FADB056E3FE90D5D": "Luggage_B"
}


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_distance_m(line: str) -> Optional[float]:
    s = line.strip()
    if not s:
        return None

    for pat in DIST_PATTERNS:
        m = pat.match(s)
        if not m:
            continue
        try:
            v = float(m.group(1))
        except Exception:
            return None
        if v < MIN_M or v > MAX_M:
            return None
        return v

    return None


def parse_id(line: str) -> Optional[str]:
    s = line.strip()
    if not s:
        return None
    m = ID_PATTERN.match(s)
    if not m:
        return None
    return m.group(1).upper()


def open_serial(port: str) -> serial.Serial:
    return serial.Serial(
        port=port,
        baudrate=BAUD,
        timeout=READ_TIMEOUT_S,
        write_timeout=READ_TIMEOUT_S,
    )


def candidate_ports():
    return sorted(set(
        glob.glob("/dev/ttyACM*") +
        glob.glob("/dev/ttyUSB*") +
        glob.glob("/dev/serial/by-id/*")
    ))


def score_line(line: str) -> int:
    if parse_distance_m(line) is not None:
        return 2
    if parse_id(line) is not None:
        return 3
    return 0


def probe_port_for_target_output(port: str) -> Tuple[bool, int]:
    ser = None
    try:
        ser = open_serial(port)
    except Exception as e:
        log(f"[probe] cannot open {port}: {e}")
        return (False, -1)

    buf = b""
    score = 0
    found = False
    start = time.time()

    try:
        while time.time() - start < PROBE_SECONDS_PER_PORT:
            chunk = ser.read(256)
            if not chunk:
                continue
            buf += chunk

            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                line = raw.replace(b"\r", b"").decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                s = score_line(line)
                if s > 0:
                    score += s
                    found = True

        return (found, score)

    except Exception as e:
        log(f"[probe] error on {port}: {e}")
        return (False, -1)

    finally:
        try:
            ser.close()
        except Exception:
            pass


def auto_select_port() -> Optional[str]:
    env_port = os.environ.get("SERIAL_PORT")
    if env_port:
        return env_port

    ports = candidate_ports()
    if not ports:
        log("No candidate serial ports found.")
        return None

    log(f"Found candidate ports: {', '.join(ports)}")

    best_port = None
    best_score = -1

    for p in ports:
        ok, score = probe_port_for_target_output(p)
        log(f"[probe] {p}: ok={ok}, score={score}")
        if ok and score > best_score:
            best_port = p
            best_score = score

    if best_port is None:
        log("No serial port looked like the target board.")
        return None

    log(f"Selected port: {best_port}")
    return best_port


def cin_url() -> str:
    return f"{CSE_BASE}/~/{CSE_ID}/{CSE_NAME}/{AE_NAME}/{CNT_NAME}"


def headers():
    return {
        "X-M2M-Origin": ORIGIN,
        "X-M2M-RI": str(uuid.uuid4()),
        "X-M2M-RVI": "5",
        "Content-Type": "application/json;ty=4",
        "Accept": "application/json",
    }


def safe_tag_id(tag_id: Optional[str]) -> str:
    return tag_id if tag_id else DEFAULT_TAG_ID


def tag_name_from_id(tag_id: Optional[str]) -> str:
    if not tag_id:
        return DEFAULT_TAG_NAME
    return TAG_NAME_MAP.get(tag_id, DEFAULT_TAG_NAME)


def post_distance(distance_m: float, tag_id: Optional[str]) -> bool:
    payload = {
        "m2m:cin": {
            "con": {
                "distance_m": distance_m,
                "tag_id": safe_tag_id(tag_id),
                "tag_name": tag_name_from_id(tag_id),
                "ts": now_iso(),
            }
        }
    }

    try:
        r = requests.post(cin_url(), headers=headers(), json=payload, timeout=5)
    except Exception as e:
        log(f"[post error] {e}")
        return False

    if r.status_code not in (200, 201):
        log(f"[post failed] status={r.status_code} body={r.text}")
        return False

    log(
        f"[post ok] distance={distance_m:.2f} "
        f"tag_id={safe_tag_id(tag_id)} "
        f"tag_name={tag_name_from_id(tag_id)}"
    )
    return True


def should_upload(distance_m: float, last_uploaded_distance: Optional[float]) -> bool:
    if last_uploaded_distance is None:
        return True
    return abs(distance_m - last_uploaded_distance) > UPLOAD_DELTA_M


def run_once(port: str) -> None:
    last_id = None
    last_uploaded_distance = None

    ser = open_serial(port)
    log(f"Connected to {port} at {BAUD} baud")

    buf = b""
    try:
        while True:
            chunk = ser.read(256)
            if not chunk:
                continue

            buf += chunk

            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                line = raw.replace(b"\r", b"").decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                sid = parse_id(line)
                if sid is not None:
                    last_id = sid
                    log(f"[id] {last_id}")
                    continue

                d = parse_distance_m(line)
                if d is None:
                    continue

                if not should_upload(d, last_uploaded_distance):
                    log(
                        f"[skip] distance={d:.2f} "
                        f"last_uploaded={last_uploaded_distance:.2f} "
                        f"delta={abs(d - last_uploaded_distance):.2f}"
                    )
                    continue

                if post_distance(d, last_id):
                    last_uploaded_distance = d

    finally:
        try:
            ser.close()
        except Exception:
            pass


def main() -> int:
    while True:
        port = auto_select_port()
        if not port:
            time.sleep(1)
            continue

        try:
            run_once(port)
        except KeyboardInterrupt:
            log("Interrupted by user.")
            return 0
        except Exception as e:
            log(f"[serial error] {e}")
            time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
