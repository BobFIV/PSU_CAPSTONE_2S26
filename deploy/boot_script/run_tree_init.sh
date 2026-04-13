#!/bin/bash
set -e

until nc -z localhost 8081; do
    sleep 2
done

sleep 2

cd /home/raaid/Desktop/capstone2
source .venv/bin/activate

python3 init_tree.py