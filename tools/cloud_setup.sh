#!/usr/bin/env bash
# One-time setup for a cloud (Linux) session: Python packages + data files.
set -e
cd "$(dirname "$0")/.."
python3 -m pip install -q -r requirements.txt
python3 tools/restore_data.py
# dense per-module account grids (research/tmp/dense, git-ignored, ~2.1 GB): needed by tools/propcycle_test/run_test.py and the account
# simulators (acct_lab, acct1c_lib, prop_wf). Rebuilt from the trade pickles in the repo; measured 2026-10-26: 55 + 19 + 40 + 15 + 60 + 58 s.
if [ ! -f research/tmp/dense/meta.pkl ]; then
  (cd research/mine && for s in dense_build ict_redo dense_profiles dense_extra gnq_port nqdrive_port; do echo "== $s.py"; python3 $s.py > /dev/null; done)
fi
# C# 5 syntax check of the NinjaScript files needs mono: apt-get install -y mono-mcs (~4 min) if 'mcs' is missing
command -v mcs > /dev/null || echo "mcs not found: tools/nt8_stub/check.sh and tools/propcycle_test need 'apt-get install -y mono-mcs'"
