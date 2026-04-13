#!/bin/bash
set -e

cd /home/raaid/Desktop/capstone2
source .venv/bin/activate

exec python3 read_upload.py
