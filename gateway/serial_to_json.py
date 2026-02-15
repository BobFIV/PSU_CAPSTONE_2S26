#!/usr/bin/env python3
import json
import time
import re
from datetime import datetime

import serial

PORT = "/dev/ttyACM1"
BAUD = 115200
OUT_FILE = "distance.jsonl"

pattern = re.compile(
    r"method:\s*([0-9]+(?:\.[0-9]+)?)\s*meters\s*\(derived from\s*([0-9]+)\s*samples\)",
    re.IGNORECASE
)

def parse_value(line: str):
    m = pattern.search(line)
    if not m:
        return None, None
    return float(m.group(1)), int(m.group(2))

def main():
    ser = serial.Serial(PORT, BAUD, timeout=1)
    ser.flushInput()

    f = open(OUT_FILE, "a", encoding="utf-8") if OUT_FILE else None

    current = {}

    try:
        while True:
            time.sleep(0.01)
            raw = ser.readline()
            if not raw:
                continue

            s = raw.decode(errors="replace").strip()
            if not s:
                continue

            if "Estimated distance to reflector" in s:
                current = {}
                continue

            if ("Round" in s) and ("Timing" in s) and ("method:" in s):
                val, n = parse_value(s)
                if val is not None:
                    current["round_trip_m"] = val
                    current["round_trip_samples"] = n

            if ("Phase" in s) and ("Ranging" in s) and ("method:" in s):
                val, n = parse_value(s)
                if val is not None:
                    current["phase_based_m"] = val
                    current["phase_based_samples"] = n

            if ("round_trip_m" in current) and ("phase_based_m" in current):
                record = {
                    "ts": time.time(),
                    "iso": datetime.now().isoformat(timespec="milliseconds"),
                    "round_trip": {
                        "meters": current["round_trip_m"],
                        "samples": current["round_trip_samples"],
                    },
                    "phase_based": {
                        "meters": current["phase_based_m"],
                        "samples": current["phase_based_samples"],
                    },
                }

                j = json.dumps(record, ensure_ascii=False)
                print(j, flush=True)

                if f:
                    f.write(j + "\n")
                    f.flush()

                current = {}

    except KeyboardInterrupt:
        pass
    finally:
        if f:
            f.close()
        ser.close()

if __name__ == "__main__":
    main()
