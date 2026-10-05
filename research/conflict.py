import numpy as np, pandas as pd
PROFILES = {"MAX_SHARPE": {"ORB60": 0.6, "MSEQ": 0.5, "CRT11": 2.0, "MOM13": 1.0, "ON07": 1.0, "ICT": 1.0, "LON": 2.0, "GOLD": 2.0, "MOM11": 0.3, "MOM1030": 0.3, "REV06": 0.3},
            "WR70": {"ORB60": 0.75, "MSEQ": 0.5, "CRT11": 2.0, "ON07": 1.0, "ICT": 1.0, "MOM11": 0.3, "MOM1030": 0.3, "REV06": 0.3}}
def pick(V, prof): return pd.concat([V[(V["mod"] == m) & (V["var"] == v)] for m, v in prof.items()])
def conflict_filter(T):
    keep = []
    for d, g in T.groupby("date", sort=False):
        g = g.sort_values("tin"); openpos = []   # (tout, dir) for NQ trades
        for r in g.itertuples():
            if r.mod == "GOLD": keep.append(r.Index); continue
            live = [(to, dd) for (to, dd) in openpos if to > r.tin]
            if any(dd == -r.d for _, dd in live): continue
            openpos.append((r.tout, r.d)); keep.append(r.Index)
    return T.loc[keep]
def stats(T, days):
    d = T.groupby("date").usd.sum().reindex(days, fill_value=0.0)
    u = T.usd
    return d.mean() / d.std() * np.sqrt(252), 100 * (u > 0).mean(), u[u > 0].sum() / -u[u <= 0].sum(), len(T) / len(days), d.sum()
for tag, lo, split in (("nq_1m", 20200201, 20240101), ("mnq_fut", 20240201, None)):
    V = pd.read_pickle(f"variants_{tag}.pkl"); V = V[(V.date >= lo) & ~V.fomc]
    for pn, prof in PROFILES.items():
        T = pick(V, prof).reset_index(drop=True); F = conflict_filter(T)
        parts = [("IS", lambda x: x[x.date < split]), ("C24", lambda x: x[x.date >= split])] if split else [("REAL", lambda x: x)]
        for lab, f in parts:
            a, b = f(T), f(F); days = np.array(sorted(f(V).date.unique()))
            s1, s2 = stats(a, days), stats(b, days)
            print(f"{pn:10s} {lab:4s}: independent -> Sharpe {s1[0]:.2f} WR {s1[1]:.1f}% PF {s1[2]:.2f} {s1[3]:.2f}/day | single strategy (no opposite NQ positions) -> Sharpe {s2[0]:.2f} WR {s2[1]:.1f}% PF {s2[2]:.2f} {s2[3]:.2f}/day | blocked {100*(1-len(b)/len(a)):.1f}% of trades")
