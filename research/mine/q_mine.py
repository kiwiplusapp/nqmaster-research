"""Mine the Q families (q_families.py) on CFD NQ 2020-26 (IS 2020-23 / C24 2024-26), real MNQ 2024-26 (REAL) and histdata NQ 2015-19
cost-normalised (TR, norm_cost 0.345% of ATR, slip 0). Single process.
usage: python3 q_mine.py Q_CAL Q_REBAL ...   -> q_results_<fam>.csv, q_daily_<fam>.npz (daily $ per config, CFD and REAL), q_trades_<fam>.pkl"""
import os, sys, time, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import Data, run_events, split_stats
from q_families import QFAMILIES
NORM = 0.00345

def run_cfg(D, fam, p, slip=0.25, norm_cost=None):
    gen, _, maxday, flat_fn = QFAMILIES[fam]; flat = flat_fn(p) if flat_fn else 955
    if fam == "Q_NOISE":
        o = gen(D, p, slip=slip, flat=flat)["direct"]; fi = o[:, 1].astype(np.int64)
        df = pd.DataFrame(dict(date=D.date[fi], usd=o[:, 0] * D.pv - D.comm, fi=fi, xi=o[:, 2].astype(np.int64), d=o[:, 3], risk=o[:, 4]))
        if norm_cost is not None:
            A = D.atr[D.day[fi]]; df["usd"] = np.where(A > 0, (o[:, 0] - norm_cost * A) / np.where(A > 0, A, 1) * 100, 0.0)
    else:
        df = run_events(D, gen(D, p), flat=flat, maxday=maxday, slip=slip, norm_cost=norm_cost)
    if len(df):
        df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
    else:
        df = pd.DataFrame(columns=["date", "usd", "fi", "xi", "d", "risk", "tin", "tout"])
    return df

def daydates(D, start):
    dd = np.unique(D.daydate[D.ro >= 0]); return dd[dd >= start]

def load_all():
    t = time.time(); G = {"cfd": Data("nq_1m.npz"), "real": Data("mnq_fut.npz"), "long": Data("nqhd_long.npz")}
    print("data loaded", round(time.time() - t), "s", flush=True); return G

if __name__ == "__main__":
    fams = sys.argv[1:] or list(QFAMILIES)
    G = load_all()
    DAYS = {"cfd": daydates(G["cfd"], 20200201), "real": daydates(G["real"], 20240201)}
    for fam in fams:
        grid = QFAMILIES[fam][1]; t0 = time.time(); rows = []; keep = {}
        M = {k: np.zeros((len(grid), len(DAYS[k])), np.float32) for k in DAYS}
        for j, p in enumerate(grid):
            row = dict(fam=fam, j=j, params=repr(p)); tr = {}
            try:
                for key in ("cfd", "real", "long"):
                    D = G[key]; nc = NORM if key == "long" else None
                    df = run_cfg(D, fam, p, slip=0.0 if nc else 0.25, norm_cost=nc)
                    st = split_stats(D.name, df)
                    if key == "long": st = {k: v for k, v in st.items() if k.startswith("TR")}
                    row.update(st); tr[key] = df[["date", "usd", "tin", "tout", "d"]].copy()
                    if key in DAYS and len(df):
                        s = df.groupby("date").usd.sum(); M[key][j] = s.reindex(DAYS[key], fill_value=0.0).to_numpy()
            except Exception as e:
                row["err"] = repr(e)[:300]; print("ERR", fam, j, row["err"], flush=True)
            rows.append(row)
            if (row.get("IS_n", 0) or 0) >= 40 and (row.get("IS_pf", 0) or 0) >= 1.05: keep[j] = tr
            if j % 100 == 0: print(fam, j, "/", len(grid), round(time.time() - t0), "s", flush=True)
        R = pd.DataFrame(rows); R.to_csv(f"q_results_{fam}.csv", index=False)
        np.savez_compressed(f"q_daily_{fam}.npz", cfd=M["cfd"], real=M["real"], cfd_days=DAYS["cfd"], real_days=DAYS["real"])
        pickle.dump(keep, open(f"q_trades_{fam}.pkl", "wb"))
        print("done", fam, len(grid), "configs", round(time.time() - t0), "s", flush=True)
