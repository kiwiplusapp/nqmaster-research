"""Other aggressor-delta features (of_trades.py: delta over the last 5 / 15 / 30 minutes before the fill bar, oriented with the trade)
on the NEW months 2025-05..2026-03 with quintile edges from the original Apr-Oct 2026 sample. A feature counts only if its
quintile ordering repeats (Spearman of avg trade vs quintile in both samples). -> of_validate_other.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from wrq_lib import getD
from scipy.stats import spearmanr

if __name__ == "__main__":
    D = getD("nqdb.npz"); ep_all = np.load(os.path.join(os.path.dirname(HERE), "data", "nqdb.npz"))["epoch"]
    M = pd.concat([pickle.load(open(os.path.join(HERE, "of_minutes_2025.pkl"), "rb"))[["buy", "sell"]],
                   pickle.load(open(os.path.join(HERE, "of_minutes.pkl"), "rb"))[["buy", "sell"]]]).groupby(level=0).sum().sort_index()
    S = M.reindex(ep_all).fillna(0.0); cb, cs = np.cumsum(np.r_[0, S.buy.to_numpy()]), np.cumsum(np.r_[0, S.sell.to_numpy()])
    first = D.ds[D.day]
    Xr, _ = pickle.load(open(os.path.join(HERE, "db_long_trades.pkl"), "rb"))["Ultra"]
    X = Xr[(Xr.atr >= 150) & (Xr.date >= 20250501)].copy(); i = X.fi.to_numpy(); d = X.d.to_numpy()
    X = X[ep_all[first[i]] >= M.index.min()]; i = X.fi.to_numpy(); d = X.d.to_numpy()
    for k in (5, 15, 30):
        lo = np.maximum(i - k, first[i]); B = cb[i] - cb[lo]; A = cs[i] - cs[lo]
        X[f"dl{k}"] = np.where(B + A > 0, (B - A) / np.maximum(B + A, 1), np.nan) * d
    NEW = X.date < 20260401; OUT = {}
    for ft in ("dl5", "dl15", "dl30"):
        q = np.nanquantile(X.loc[~NEW, ft], [0.2, 0.4, 0.6, 0.8]); b = np.digitize(X[ft], q)
        r = {}
        for lab, m in (("original", ~NEW), ("new", NEW)):
            av = [float((X.u * X.w)[m & (b == k)].mean()) for k in range(5)]
            r[lab] = dict(avg_by_quintile=[round(v, 1) for v in av], n=[int((m & (b == k)).sum()) for k in range(5)],
                          rank_corr=round(float(spearmanr(range(5), av)[0]), 2))
        OUT[ft] = r; print(ft, json.dumps(r), flush=True)
    json.dump(OUT, open(os.path.join(HERE, "of_validate_other.json"), "w"), indent=1)
