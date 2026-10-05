"""Time stop for ORB60/ORB90/CRT11/MSEQ/MSEQS: if the trade is still open N minutes after entry, exit at that bar's close
(-1 tick). Entry price: ORB = OR high/low +-1 tick (or bar open if gapped through), others = entry-bar open +-1 tick.
Trades that closed before N keep their real result."""
import pickle, numpy as np, pandas as pd
from ict import load
def sm(om): return (np.asarray(om) - 1080) % 1440
T = pickle.load(open("feat_trades2.pkl", "rb"))
def run(per, F, Ns=(15, 30, 60, 90, 120, 180)):
    D = load("mnq_fut.npz" if per == "REAL" else "nq_1m.npz"); date = D["date"]; smm = sm(D["om"]); o, h, l, c, om = D["o"], D["h"], D["l"], D["c"], D["om"]
    first = pd.Series(np.arange(len(date))).groupby(date).first(); last = pd.Series(np.arange(len(date))).groupby(date).last()
    rows = []
    for r in F[F["mod"].isin(["ORB60", "ORB90", "CRT11", "MSEQ", "MSEQS"])].itertuples():
        if r.date not in first.index: continue
        a, b = first[r.date], last[r.date] + 1; mm = smm[a:b]
        i0 = a + min(np.searchsorted(mm, r.tin), b - a - 1)
        if r.mod in ("ORB60", "ORB90"):
            rng = 60 if r.mod == "ORB60" else 90
            sel = (om[a:b] >= 570) & (om[a:b] < 570 + rng)
            if not sel.any(): continue
            lev = (h[a:b][sel].max() + 0.25) if r.d == 1 else (l[a:b][sel].min() - 0.25)
            e = max(o[i0], lev) if r.d == 1 else min(o[i0], lev)
        else:
            e = o[i0] + 0.25 * r.d
        dur = r.tout - r.tin
        rec = dict(date=r.date, mod=r.mod, u=r.u, w=r.base_w * (2.0 if r.rev_bucket else 1.0))
        for N in Ns:
            if dur > N:
                j = min(i0 + N, b - 1)
                rec[f"u{N}"] = r.d * (c[j] - 0.25 * r.d - e) * 2 - 1.9
            else: rec[f"u{N}"] = r.u
        rows.append(rec)
    return pd.DataFrame(rows)
def pf(u): return round(u[u > 0].sum() / -u[u <= 0].sum(), 3) if (u <= 0).any() and len(u) >= 15 else np.nan
if __name__ == "__main__":
    out = {}
    for per, (F, days) in T.items():
        X = run(per, F); out[per] = X
    pickle.dump(out, open("timestop.pkl", "wb"))
    for m in ("ORB60", "ORB90", "CRT11", "MSEQ", "MSEQS"):
        print(m)
        for col in ["u"] + [f"u{N}" for N in (15, 30, 60, 90, 120, 180)]:
            s = " | ".join(f"{p}: PF {pf(X[X['mod']==m][col])} net {X[X['mod']==m][col].sum():7.0f}" for p, X in out.items())
            print(f"   {'real exit' if col=='u' else 'stop '+col[1:]+'m':10s} {s}")
