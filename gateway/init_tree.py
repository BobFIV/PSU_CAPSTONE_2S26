#!/usr/bin/env python3

import uuid
import requests

CSE_BASE = "http://localhost:8081"
CSE_ID = "id-mn"
CSE_NAME = "cse-mn"
ORIGIN = "CAdmin"

AE_NAME = "CAdmin"

CONTAINERS = [
    ("proximity", 200),
    ("status", 50),
    ("session", 20),
    ("alerts", 100),
]


def headers(ty=None):
    h = {
        "X-M2M-Origin": ORIGIN,
        "X-M2M-RI": str(uuid.uuid4()),
        "X-M2M-RVI": "5",
        "Accept": "application/json",
    }
    if ty is not None:
        h["Content-Type"] = f"application/json;ty={ty}"
    return h


def root_url():
    return f"{CSE_BASE}/~/{CSE_ID}/{CSE_NAME}"


def create_container(name, mni):
    url = f"{root_url()}/{AE_NAME}"
    payload = {
        "m2m:cnt": {
            "rn": name,
            "mni": mni,
        }
    }

    r = requests.post(url, headers=headers(3), json=payload, timeout=10)

    if r.status_code in (200, 201):
        print(f"Container created: {name}")
    elif r.status_code == 409:
        print(f"Container already exists: {name}")
    else:
        print(f"Container create failed: {name}")
        print(r.status_code, r.text)
        raise SystemExit(1)


def main():
    for name, mni in CONTAINERS:
        create_container(name, mni)
    print("Done.")


if __name__ == "__main__":
    main()
