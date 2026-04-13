#!/usr/bin/env python3

import re
import sys
import uuid
from datetime import datetime, timezone

import requests

CSE_BASE = "http://localhost:8081"
CSE_ID = "id-mn"
CSE_NAME = "cse-mn"
ORIGIN = "CAdmin"

AE_NAME = "CAdmin"
CNT_NAME = "proximity"

ID_RE = re.compile(r"^[0-9A-Fa-f]{16}$")
DIST_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")

TAG_NAME_MAP = {
    "6E4ABBD598C5AB18": "Luggage_A",
}

DEFAULT_TAG_NAME = "UnknownTag"
last_id = None


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def cin_url():
    return f"{CSE_BASE}/~/{CSE_ID}/{CSE_NAME}/{AE_NAME}/{CNT_NAME}"


def headers():
    return {
        "X-M2M-Origin": ORIGIN,
        "X-M2M-RI": str(uuid.uuid4()),
        "X-M2M-RVI": "5",
        "Content-Type": "application/json;ty=4",
        "Accept": "application/json",
    }


def tag_name_from_id(tag_id):
    if not tag_id:
        return DEFAULT_TAG_NAME
    return TAG_NAME_MAP.get(tag_id, DEFAULT_TAG_NAME)


def post_distance(distance_m, tag_id):
    url = cin_url()
    payload = {
        "m2m:cin": {
            "con": {
                "distance_m": distance_m,
                "tag_id": tag_id,
                "tag_name": tag_name_from_id(tag_id),
                "ts": now_iso(),
            }
        }
    }

    try:
        r = requests.post(url, headers=headers(), json=payload, timeout=5)
        print(f"[POST] url={url}", file=sys.stderr, flush=True)
        print(f"[POST] status={r.status_code}", file=sys.stderr, flush=True)
        print(f"[POST] body={r.text}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[POST ERROR] {e}", file=sys.stderr, flush=True)
        return

    if r.status_code not in (200, 201):
        print("[POST FAILED]", file=sys.stderr, flush=True)
        return

    print(
        f"[POST OK] distance={distance_m:.2f} tag_id={tag_id} tag_name={tag_name_from_id(tag_id)}",
        file=sys.stderr,
        flush=True,
    )


def main():
    global last_id

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue

        print(f"[IN] {line}", file=sys.stderr, flush=True)

        if ID_RE.fullmatch(line):
            last_id = line.upper()
            print(f"[ID] updated last_id={last_id}", file=sys.stderr, flush=True)
            continue

        if DIST_RE.fullmatch(line):
            post_distance(float(line), last_id)
            continue

        print(f"[IGNORED] {line}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
