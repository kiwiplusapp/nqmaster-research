import itertools, numpy as np, pandas as pd
TC = pd.read_pickle("timeline_nq_1m.pkl"); TR = pd.read_pickle("timeline_mnq_fut.pkl")
TC = TC[TC.date >= 20200201]; TR = TR[TR.date >= 20240201]
def apply(T, skip_fomc, dls, dps, mods=None, scale=1.0):
    if mods is not None: T = T[T["mod"].isin(mods)]
    if skip_fomc: T = T[~T.fomc]
    out = []
    for d, g in T.groupby("date", sort=True):
        tin = g.tin.to_numpy(); tout = g.tout.to_numpy(); u = g.usd.to_numpy() * scale
        take = np.zeros(len(g), bool)
        for i in range(len(g)):
            real = u[take & (tout <= tin[i])].sum()
            if dls and real <= -dls: continue
            if dps and real >= dps: continue
            take[i] = True
        out.append((d, u[take].sum(), int(take.sum())))
    return pd.DataFrame(out, columns=["date", "pnl", "n"]).set_index("date")
def sh(x): return x.mean() / x.std() * np.sqrt(252)
def combine(x, T, D, cons, maxd=400):
    res = []
    for st in range(len(x)):
        eq = 0; pk = 0; best = 0; r = None
        for k in range(st, min(len(x), st + maxd)):
            eq += x[k]; best = max(best, x[k]); pk = max(pk, eq)
            if eq <= pk - D: r = ("b", k - st + 1); break
            if eq >= max(T, best / cons if cons else T): r = ("p", k - st + 1); break
        res.append(r)
    p = [r[1] for r in res if r and r[0] == "p"]; b = [r for r in res if r and r[0] == "b"]
    p20 = sum(1 for r in res if r and r[0] == "p" and r[1] <= 20)
    return 100 * len(p) / len(res), 100 * len(b) / len(res), (np.median(p) if p else np.nan), 100 * p20 / len(res)
allC = pd.Series(0.0, index=sorted(TC.date.unique())); allR = pd.Series(0.0, index=sorted(TR.date.unique()))
rows = []
for sf, dls, dps in itertools.product((0, 1), (0, 300, 500, 700, 1000), (0, 700, 1000, 1400)):
    a = apply(TC, sf, dls, dps).pnl.reindex(allC.index, fill_value=0); r = apply(TR, sf, dls, dps).pnl.reindex(allR.index, fill_value=0)
    IS = a.index < 20240101
    ts = combine(r.to_numpy(), 3000, 2000, 0.5); ts_is = combine(a[IS].to_numpy(), 3000, 2000, 0.5)
    k25 = combine(r.to_numpy(), 1500, 1500, 0)
    rows.append(dict(skip_fomc=sf, dls=dls, dps=dps, sh_IS=round(sh(a[IS]), 2), sh_C24=round(sh(a[~IS]), 2), sh_REAL=round(sh(r), 2),
                     net_real_yr=round(r.mean() * 252), ts_IS_pass=round(ts_is[0]), ts_IS_bust=round(ts_is[1]), ts_real_pass=round(ts[0]), ts_real_bust=round(ts[1]), ts_real_days=ts[2],
                     k25_pass=round(k25[0]), k25_bust=round(k25[1]), k25_days=k25[2], k25_p20=round(k25[3])))
g = pd.DataFrame(rows); g.to_csv("acct_rules.csv", index=False)
print(g.sort_values("ts_IS_pass", ascending=False).head(12).to_string(index=False))
print("\nbaseline (no rules):"); print(g[(g.skip_fomc == 0) & (g.dls == 0) & (g.dps == 0)].to_string(index=False))
print("skip FOMC only:"); print(g[(g.skip_fomc == 1) & (g.dls == 0) & (g.dps == 0)].to_string(index=False))
