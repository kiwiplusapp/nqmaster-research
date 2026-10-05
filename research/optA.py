"""Stage A: per-module exclusion filters chosen on CFD 2020-23 only; checked on CFD 2024-26 and REAL MNQ 2024-26."""
import numpy as np, pandas as pd
C = pd.read_pickle("trades_nq_1m.pkl"); R = pd.read_pickle("trades_mnq_fut.pkl")
# MOM11 VWAP agreement flag
exec(open("mom11_feat.py").read().split("for f in [")[0])
for tag, T in (("nq_1m.npz", C), ("mnq_fut.npz", R)):
    va = out[tag].set_index("date").vw_agree.astype(float)
    T["vw_agree"] = np.where(T["mod"] == "MOM11", T.date.map(va), np.nan)
C = C[C.date >= 20200201]; R = R[R.date >= 20240201]
IS = C[C.date < 20240101]; C24 = C[C.date >= 20240101]
def pf(u): return u[u > 0].sum() / -u[u <= 0].sum() if (u <= 0).any() and len(u) else np.nan
# bucket edges from IS (per feature, global)
feats = {"atr_ratio": "q", "ret1_d": [-0.3, 0.3], "ret2_d": [-0.5, 0.5], "gap_d": [-0.1, 0.1], "onrng": "q", "prng": "q", "dow": "cat", "with_trend": "cat", "vw_agree": "cat"}
edges = {}
for f, spec in feats.items():
    if spec == "q": edges[f] = list(IS[f].quantile([1 / 3, 2 / 3]).to_numpy())
    elif spec == "cat": edges[f] = None
    else: edges[f] = spec
def bucket(df, f):
    if edges[f] is None: return df[f]
    return pd.Series(np.digitize(df[f], edges[f]), index=df.index).where(df[f].notna())
rules = {}
report = []
for mod in sorted(C["mod"].unique()):
    ism = IS[IS["mod"] == mod].copy(); excl = []
    for it in range(2):
        best = None
        for f in feats:
            b = bucket(ism, f)
            if b.isna().all(): continue
            for val in b.dropna().unique():
                sel = b == val
                if sel.sum() < 30 or (~sel).sum() < 0.5 * len(IS[IS["mod"] == mod]): continue
                p_ex = pf(ism.usd1[sel]); p_keep = pf(ism.usd1[~sel])
                if p_ex < 0.9 and (best is None or ism.usd1[sel].sum() < best[2]):
                    best = (f, val, ism.usd1[sel].sum(), p_ex, p_keep)
        if best is None: break
        excl.append(best[:2]); ism = ism[~(bucket(ism, best[0]) == best[1])]
    rules[mod] = excl
    def apply(df):
        m = df[df["mod"] == mod].copy()
        for f, val in excl: m = m[~(bucket(m, f) == val)]
        return m
    a0, a1 = IS[IS["mod"] == mod], apply(IS); b0, b1 = C24[C24["mod"] == mod], apply(C24); r0, r1 = R[R["mod"] == mod], apply(R)
    report.append(dict(mod=mod, rules=" & ".join(f"not {f}={v}" for f, v in excl) or "-", IS=f"{pf(a0.usd1):.2f}->{pf(a1.usd1):.2f} ({len(a1)}/{len(a0)})",
                       C24=f"{pf(b0.usd1):.2f}->{pf(b1.usd1):.2f} ({len(b1)}/{len(b0)})", REAL=f"{pf(r0.usd1):.2f}->{pf(r1.usd1):.2f} ({len(r1)}/{len(r0)})",
                       wr_real=f"{100*(r0.usd1>0).mean():.0f}->{100*(r1.usd1>0).mean():.0f}%"))
print(pd.DataFrame(report).to_string(index=False))
def apply_all(df):
    parts = []
    for mod, excl in rules.items():
        m = df[df["mod"] == mod].copy()
        for f, val in excl: m = m[~(bucket(m, f) == val)]
        parts.append(m)
    return pd.concat(parts)
def port(df, label):
    days = sorted(df.date.unique())
    d = df.groupby("date").usd1.sum()
    print(f"{label:28s} trades {len(df):5d} WR {100*(df.usd1>0).mean():.1f}% PF {pf(df.usd1):.2f} daily Sharpe*sqrt252 {d.mean()/d.std()*np.sqrt(252):.2f}")
print()
for lab, df in (("IS 2020-23", IS), ("CFD 2024-26", C24), ("REAL 2024-26", R)):
    port(df, lab + " before"); port(apply_all(df), lab + " after")
pd.to_pickle((rules, edges), "optA_rules.pkl")
