import pickle, numpy as np, pandas as pd, itertools
M = pickle.load(open("modpnl.pkl", "rb"))
ap = open("apex_policy.py").read(); exec(ap[ap.index("def sim("):ap.index("POL = {")])
def apply(F, K=99, dl=None, dp=None, same=99, w=None):
    keep = []; wt = []
    for d, g in F.groupby("date", sort=False):
        g = g.sort_values("tin"); openp = []; closed = []
        for r in g.itertuples():
            q = (w or {}).get(r.mod, 1.0)
            live = [(to, dd) for (to, dd) in openp if to > r.tin]
            real = sum(u for (to, u) in closed if to <= r.tin)
            if dl is not None and real <= -dl: continue
            if dp is not None and real >= dp: continue
            if len(live) >= K: continue
            if sum(1 for _, dd in live if dd == r.d) >= same: continue
            openp.append((r.tout, r.d)); closed.append((r.tout, r.u * q)); keep.append(r.Index); wt.append(q)
    T = F.loc[keep].copy(); T["q"] = wt; T["uw"] = T.u * T.q
    return T
def perf(T, days):
    d = T.groupby("date").uw.sum().reindex(days, fill_value=0); eq = d.cumsum(); dd = (eq.cummax() - eq).max(); u = T.uw
    tot = np.zeros(len(days)); mn = np.zeros(len(days)); mx = np.zeros(len(days)); idx = {x: i for i, x in enumerate(days)}
    for x, g in T.groupby("date"):
        c = np.cumsum(g.sort_values("tout").uw.to_numpy()); i = idx[x]; tot[i] = c[-1]; mn[i] = min(0, c.min()); mx[i] = max(0, c.max())
    a = sim(tot, mn, mx, lambda e, p: 2 if p - e < 800 else 1, maxd=22); b = sim(tot, mn, mx, lambda e, p: 1, maxd=44)
    return dict(tpd=round(len(T) / len(days), 2), wr=round(100 * (u > 0).mean(), 1), pf=round(u[u > 0].sum() / -u[u <= 0].sum(), 3), sharpe=round(d.mean() / d.std() * np.sqrt(252), 2),
                mo=round(d.mean() * 21), maxdd=round(dd), ad30=f"{a[0]:.0f}/{a[1]:.0f}", f1_60=f"{b[0]:.0f}/{b[1]:.0f}")
if __name__ == "__main__":
    RULES = {"base": {}, "ICTx2": dict(w={"ICT": 2.0}), "K2": dict(K=2), "K3": dict(K=3), "same1": dict(same=1), "same2": dict(same=2),
             "dl300": dict(dl=300), "dl500": dict(dl=500), "dp600": dict(dp=600), "dp1000": dict(dp=1000)}
    rows = []
    for nm, kw in RULES.items():
        for per in ("IS", "C24", "REAL"):
            P, F = M["mnq_fut"] if per == "REAL" else M["nq_1m"]
            if per == "IS": F = F[F.date < 20240101]; days = P.index[P.index < 20240101]
            elif per == "C24": F = F[F.date >= 20240101]; days = P.index[P.index >= 20240101]
            else: days = P.index
            r = perf(apply(F, **kw), np.array(days)); r.update(rule=nm, per=per); rows.append(r)
    g = pd.DataFrame(rows)
    for c in ("tpd", "pf", "sharpe", "mo", "maxdd", "ad30", "f1_60"):
        print(c); print(g.pivot(index="rule", columns="per", values=c).to_string())
