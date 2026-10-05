"""Cross-asset confirmation for gold trades: at the entry minute, the move of EUR/USD (USD weakness = gold-positive) and
of silver over the last 30 / 60 minutes and since the RTH open / session open, oriented with the gold trade direction.
PF of gold trades when the other markets agree vs disagree, per period (CFD 2020-23 / CFD 2024-26 / MGC 2024-26)."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, S
from news import NEWS
FOMC = set(NEWS["FOMC"])
def closes(name):
    D = Data(name)
    s = pd.Series(D.c, index=pd.MultiIndex.from_arrays([D.date, D.sm]))
    s = s[~s.index.duplicated()]
    return s, pd.Series(D.atr[D.day], index=s.index if False else None) if False else D
def table(name):
    D = Data(name); df = pd.DataFrame(dict(date=D.date, sm=D.sm, c=D.c, o=D.o, atr=D.atr[D.day]))
    df = df.drop_duplicates(["date", "sm"]).set_index(["date", "sm"]).sort_index()
    return df
EUR = table("eur_hd.npz"); XAG = table("xag_hd.npz")
def lookup(T, date, sm):
    # last close at or before (date, sm): forward-fill inside the day
    idx = pd.MultiIndex.from_arrays([date, sm])
    full = T.c.reindex(T.index.union(idx)).groupby(level=0).ffill()
    return full.reindex(idx).to_numpy(), T.atr.groupby(level=0).first().reindex(date).to_numpy()
def feats(F, T, tag):
    date = F.date.to_numpy(); tin = F.tin.to_numpy().astype(int); d = F.d.to_numpy()
    c0, A = lookup(T, date, tin - 1)
    out = {}
    for lab, back in (("30", 30), ("60", 60)):
        cb, _ = lookup(T, date, np.maximum(tin - 1 - back, 0)); out[f"{tag}{lab}"] = (c0 - cb) / A * d
    co, _ = lookup(T, date, np.full(len(F), S(930)))
    out[f"{tag}rth"] = np.where(tin - 1 > S(930), (c0 - co) / A * d, np.nan)
    cs, _ = lookup(T, date, np.zeros(len(F), int))
    out[f"{tag}sess"] = (c0 - cs) / A * d
    return pd.DataFrame(out, index=F.index)
def pf(x): return round(float(x[x > 0].sum() / -x[x <= 0].sum()), 3) if (x <= 0).any() and len(x) >= 20 else np.nan
R = pd.read_csv("results_goldlongnorm.csv"); TR = pickle.load(open("trades_goldlongnorm.pkl", "rb"))
R["minpf"] = R[["G1_pf", "G2_pf", "T1_pf", "T2_pf", "REAL_pf"]].min(axis=1)
cand = R[(R.T1_n >= 80) & (R.REAL_n >= 40) & (R.minpf >= 1.0)].sort_values("minpf", ascending=False)
cand = [(r.fam, r.j, r.params) for r in cand.itertuples() if (r.fam, r.j) in TR][:40]
print("modules:", len(cand))
rows = []
for fam, j, ps in cand:
    tr = TR[(fam, j)]
    for per, key, lo, hi in (("IS", "nq", 20200201, 20240101), ("C24", "nq", 20240101, 30000000), ("REAL", "mnq", 20240201, 30000000)):
        F = tr[key]; F = F[(F.date >= lo) & (F.date < hi) & ~F.date.isin(FOMC)].reset_index(drop=True)
        if len(F) < 20: continue
        X = pd.concat([feats(F, EUR, "eur"), feats(F, XAG, "xag")], axis=1); u = F.usd.to_numpy()
        r = dict(mod=f"{fam}#{j}", per=per, n=len(F), pf=pf(u))
        for f in X.columns:
            v = X[f].to_numpy(); ok = np.isfinite(v)
            r[f + "+"] = pf(u[ok & (v > 0)]); r[f + "-"] = pf(u[ok & (v <= 0)])
        rows.append(r)
G = pd.DataFrame(rows); G.to_csv("gold_xasset.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 300)
# summary: median over modules of PF(agree) - PF(disagree) per feature and period
feat = [c[:-1] for c in G.columns if c.endswith("+")]
S_ = pd.DataFrame({per: {f: round(float(np.nanmedian(G[G.per == per][f + "+"] - G[G.per == per][f + "-"])), 3) for f in feat} for per in ("IS", "C24", "REAL")})
print("median PF(agree) - PF(disagree) across modules:"); print(S_.to_string())
for f in feat:
    sub = G[["mod", "per", "pf", f + "+", f + "-"]]
    print("\n", f); print(sub.pivot(index="mod", columns="per", values=[f + "+", f + "-"]).round(2).to_string())
