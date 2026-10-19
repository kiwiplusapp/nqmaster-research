"""Strategy miner on Bitcoin (Binance spot BTCUSDT as a proxy for CME micro BTC, research/data/btc_1m.npz, 2017-08 -> 2026-10), 2026-10-19.
Thin wrapper over run_mine_db.py (same families, same executor, same task function) with Bitcoin periods and costs:
  real : $ per MBT contract, $3.00 commission + 1 tick ($0.50) slippage per side -> T1 = 2020-23, T2 = 2024-26
  norm : cost = BTC's own 2024-26 cost/ATR ratio (env MINE_NORM, default 0.0255 = 2.55% of the RTH daily ATR), P&L in % of ATR
         -> A = 2017-08..2019-12 (the extra regime block), T1n, T2n
Selection protocol (btc_select.py, fixed before looking at T2): chosen on T1 only (n >= 100, WR >= 55, PF >= 1.3); T2 PF >= 1.2,
A norm PF >= 1.0, +4 ticks T2 PF >= 1.1, plateau (neighbouring cells T1 PF >= 1.15).
Usage: cd research/mine && MINE_PROCS=2 python3 run_mine_btc.py [FAMILY ...]   -> results_btc.csv, trades_btc.pkl"""
import os, sys, time, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("MINE_DATA", "btc_1m.npz")
import run_mine_db as M

if __name__ == "__main__":
    M.NORM = float(os.environ.get("MINE_NORM", "0.0255"))
    M.PARTS_R = (("T1", 20200101, 20240101), ("T2", 20240101, 20991231))
    M.PARTS_N = (("A", 20170801, 20200101), ("T1n", 20200101, 20240101), ("T2n", 20240101, 20991231))
    fams = sys.argv[1:] or list(M.FAMILIES)
    tasks = [(f, j) for f in fams for j in range(len(M.FAMILIES[f][1]))]
    if os.environ.get("MINE_LIMIT"): tasks = tasks[: int(os.environ["MINE_LIMIT"])]
    print("configs:", len(tasks), {f: len(M.FAMILIES[f][1]) for f in fams}, "| norm cost", M.NORM, "| data", os.environ["MINE_DATA"], flush=True)
    t0 = time.time(); rows = []; trades = {}; tag = os.environ.get("MINE_TAG", "btc")
    with Pool(int(os.environ.get("MINE_PROCS", "2")), initializer=M.init) as pool:
        for k, (row, keep) in enumerate(pool.imap_unordered(M.task, tasks, chunksize=2)):
            rows.append(row)
            if keep is not None: trades[(row["fam"], row["j"])] = keep
            if k % 1000 == 0: print(k, round(time.time() - t0), "s", flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(f"results_{tag}.csv", index=False); pickle.dump(trades, open(f"trades_{tag}.pkl", "wb"))
    print("done", round(time.time() - t0), "s; errors:", int(R["err"].notna().sum()) if "err" in R else 0, flush=True)
