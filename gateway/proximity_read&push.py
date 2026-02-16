#!/usr/bin/env python3
import json
import time
import uuid
from urllib import request, error


JSONL_PATH = "distance.jsonl"

HOST = "10.0.0.148"
PORT = 8081
CSE_ID = "id-mn"
CSE_NAME = "cse-mn"
AE_NAME = "WheelchairHubAE"
CNT_NAME = "proximity"

CONTAINER_URL = f"http://{HOST}:{PORT}/~/{CSE_ID}/{CSE_NAME}/{AE_NAME}/{CNT_NAME}"

ORIGIN = "CAdmin"
RVI = "3"


def follow_lines(path: str, poll_s: float = 0.1):
    with open(path, "r", encoding="utf-8") as f:
        # we only record new objects
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(poll_s)
                continue
            line = line.strip()
            if line:
                yield line


def post_cin(container_url: str, record_obj: dict):
    body = {
        "m2m:cin": {
            "con": json.dumps(record_obj, ensure_ascii=False),
            "cnf": "application/json:0",
        }
    }

    data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    headers = {
        "Content-Type": "application/json;ty=4",
        "Accept": "application/json",
        "X-M2M-Origin": ORIGIN,
        "X-M2M-RI": str(uuid.uuid4()),
        "X-M2M-RVI": RVI,
    }

    req = request.Request(container_url, data=data, headers=headers, method="POST")
    with request.urlopen(req, timeout=5) as resp:
        text = resp.read().decode("utf-8", errors="replace")
        return resp.status, text


def main():
    print("Watching:", JSONL_PATH)
    print("Posting to:", CONTAINER_URL)

    for line in follow_lines(JSONL_PATH):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        try:
            status, _ = post_cin(CONTAINER_URL, obj)
            print("POST", status, "iso =", obj.get("iso"))
        except error.HTTPError as e:
            msg = e.read().decode("utf-8", errors="replace")
            print("POST HTTPError", e.code, msg)
            time.sleep(1)
        except Exception as e:
            print("POST failed:", e)
            time.sleep(1)


if __name__ == "__main__":
    main()
