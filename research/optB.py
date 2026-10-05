import itertools, numpy as np, pandas as pd
exec(open("optA.py").read().split("rules = {}")[0])
keep_rules = {"LON": [("onrng", 0)], "ON07": [("onrng", 0)]}
def filt(df):
    parts = []
    for mod in df["mod"].unique():
        m = df[df["mod"] == mod]
        for f, val in keep_rules.get(mod, []): m = m[~(bucket(m, f) == val)]
        if mod == "MOM11": m = m[m.vw_agree == 1]
        parts.append(m)
    return pd.concat(parts)
def dmat(df, days):
    return df.pivot_table(index="date", columns="mod", values="usd1", aggfunc="sum").reindex(days, fill_value=0).fillna(0)
Cf, Rf = filt(C), filt(R)
dC = sorted(C.date.unique()); dR = sorted(R.date.unique())
MC = dmat(Cf, dC); MR = dmat(Rf, dR)
mods = list(MC.columns)
ISm = MC[MC.index < 20240101]; C24m = MC[MC.index >= 20240101]
def sh(x): return x.mean() / x.std() * np.sqrt(252)
print("per-module Sharpe IS | C24 | REAL (after filters)")
for m in mods: print(f"  {m:8s} {sh(ISm[m]):5.2f} | {sh(C24m[m]):5.2f} | {sh(MR[m]):5.2f}")
eq = np.ones(len(mods))
res = [("equal 1 each", eq)]
mu = ISm.mean(); var = ISm.var(); w = (mu / var).clip(lower=0); w = w / w[w > 0].min()
res.append(("IS mean/var (raw)", w.to_numpy()))
res.append(("IS mean/var rounded 1-3", np.clip(np.round(w / w.median()), 0, 3).to_numpy()))
best = None
for combo in itertools.product(*[(0, 1, 2)] * len(mods)):
    wv = np.array(combo, float)
    if wv.sum() == 0: continue
    s = sh(ISm.to_numpy() @ wv)
    if best is None or s > best[0]: best = (s, wv)
res.append(("IS max-Sharpe integer 0-2", best[1]))
for name, wv in res:
    wv = np.asarray(wv, float)
    print(f"{name:28s} w={dict(zip(mods, np.round(wv,2)))}\n   Sharpe IS {sh(ISm.to_numpy()@wv):.2f} | C24 {sh(C24m.to_numpy()@wv):.2f} | REAL {sh(MR.to_numpy()@wv):.2f}")
base_all = dmat(C, dC); base_r = dmat(R, dR)
print(f"\nv5 unfiltered equal: IS {sh(base_all[base_all.index<20240101].sum(axis=1)):.2f} C24 {sh(base_all[base_all.index>=20240101].sum(axis=1)):.2f} REAL {sh(base_r.sum(axis=1)):.2f}")
pd.to_pickle((MC, MR), "optB_mats.pkl")
