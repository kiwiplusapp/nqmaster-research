#!/usr/bin/env bash
# One-time setup for a cloud (Linux) session: Python packages + data files.
set -e
cd "$(dirname "$0")/.."
python3 -m pip install -q -r requirements.txt
python3 tools/restore_data.py
