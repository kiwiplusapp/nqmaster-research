import pickle, numpy as np, pandas as pd
B = pickle.load(open("base_feats.pkl", "rb")); R = pd.read_csv("filt_mine.csv")
PRE = {"ON07", "REV06", "LON"}
ok = ~R["mod"].isin(["LON"]) & ~(R["mod"].isin(PRE) & R.feat.isin(["gap", "open", "rng", "vw"]))
R = R[ok & (R.IS_n >= 40)]
def pf(x):
    l = -x[x <= 0].sum(); return x[x > 0].sum() / l if l > 0 and len(x) >= 15 else np.nan
def mask(G, r):
    x = G[r.feat]; return (x < r.hi) if r.bucket.startswith("low") else (x >= r.lo)
VAL = {p: B[p][0][B[p][0].date < 20260101] for p in ("C24", "REAL")}
TEST = {p: (B[p][0][B[p][0].date >= 20260101], np.array([d for d in B[p][1] if d >= 20260101])) for p in ("C24", "REAL")}
sel = []
for r in R.itertuples():
    vin = []; vout = []
    for p in ("C24", "REAL"):
        G = VAL[p][VAL[p]["mod"] == r.mod]; m = mask(G, r).fillna(False); x = G.u * G.w
        vin.append(pf(x[m])); vout.append(pf(x[~m & G[r.feat].notna()]))
    if np.isnan(vin).any(): continue
    if r.IS_pf_in < 1.0 and r.IS_pf_out > 1.2 and max(vin) < 1.0: sel.append((r, "drop"))
    if r.IS_pf_in > 1.9 and min(vin) > 1.7 and min(np.array(vin) - np.array(vout)) > 0.3: sel.append((r, "boost"))
print("rules passing IS + 2024-25 (both CFD and real):")
for r, k in sel: print(f"  {k:5s} {r.mod:8s} {r.feat:6s} {r.bucket:7s} IS in {r.IS_pf_in:.2f} out {r.IS_pf_out:.2f}")
def apply(F, rules):
    keep = pd.Series(True, index=F.index); b = pd.Series(1.0, index=F.index)
    for r, k in rules:
        m = ((F["mod"] == r.mod) & mask(F, r)).fillna(False)
        if k == "drop": keep &= ~m
        else: b[m] = 2.0
    return F[keep].assign(w=F.w[keep] * b[keep])
def metrics(F, days):
    x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0); eq = d.cumsum()
    return dict(n=len(F), wr=round(100 * (F.u > 0).mean(), 2), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3), sharpe=round(d.mean() / d.std() * np.sqrt(252), 2), mo=round(d.mean() * 21), maxdd=round((eq.cummax() - eq).max()))
print("\n2026 HOLDOUT (never used for selection):")
for p in ("C24", "REAL"):
    F, days = TEST[p]
    for nm, rules in (("base", []), ("drops", [s for s in sel if s[1] == "drop"]), ("boosts", [s for s in sel if s[1] == "boost"]), ("all", sel)):
        print(p, f"{nm:7s}", metrics(apply(F, rules), days))
pickle.dump([(dict(mod=r.mod, feat=r.feat, bucket=r.bucket, lo=r.lo, hi=r.hi), k) for r, k in sel], open("filt_sel.pkl", "wb"))
