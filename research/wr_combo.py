import itertools, numpy as np, pandas as pd
VC = pd.read_pickle("variants_nq_1m.pkl"); VR = pd.read_pickle("variants_mnq_fut.pkl")
VC = VC[(VC.date >= 20200201) & ~VC.fomc]; VR = VR[(VR.date >= 20240201) & ~VR.fomc]
per = {"IS": (VC, 20200201, 20231231), "C24": (VC, 20240101, 20991231), "REAL": (VR, 20240201, 20991231)}
stats = {}
for pn, (V, lo, hi) in per.items():
    s = V[(V.date >= lo) & (V.date <= hi)]; days = np.array(sorted(s.date.unique()))
    for (m, v), g in s.groupby(["mod", "var"]):
        d = g.groupby("date").usd.sum().reindex(days, fill_value=0.0).to_numpy()
        stats[(pn, m, v)] = (d, len(g), int((g.usd > 0).sum()), g.usd[g.usd > 0].sum(), -g.usd[g.usd <= 0].sum())
    stats[(pn, "_days")] = days
opts = {"ORB60": [0.4, 0.5, 0.6, 0.75], "MSEQ": [0.4, 0.5], "CRT11": [None, 1.0, 1.5, 2.0], "MOM13": [None, 0.5, 0.75, 1.0], "ON07": [0.5, 0.75, 1.0],
        "ICT": [0.75, 1.0], "LON": [None, 1.0, 1.5, 2.0], "GOLD": [None, 1.0, 1.5, 2.0], "MOM11": [0.3], "MOM1030": [0.3], "REV06": [0.3]}
names = list(opts)
def evalc(combo, pn):
    tot = None; n = w = gw = gl = 0
    for m, v in zip(names, combo):
        if v is None: continue
        d, nn, ww, a, b = stats[(pn, m, v)]
        tot = d.copy() if tot is None else tot + d; n += nn; w += ww; gw += a; gl += b
    return tot.mean() / tot.std() * np.sqrt(252), 100 * w / n, gw / gl, n / len(stats[(pn, "_days")])
rows = []
for combo in itertools.product(*[opts[k] for k in names]):
    s_is, wr_is, pf_is, tpd = evalc(combo, "IS")
    rows.append((combo, s_is, wr_is, pf_is, tpd))
df = pd.DataFrame(rows, columns=["combo", "sh_IS", "wr_IS", "pf_IS", "tpd_IS"])
cur = tuple({"ORB60": 0.6, "MSEQ": 0.5, "CRT11": 2.0, "MOM13": 1.0, "ON07": 1.0, "ICT": 1.0, "LON": 2.0, "GOLD": 2.0, "MOM11": 0.3, "MOM1030": 0.3, "REV06": 0.3}[k] for k in names)
def show(combo, label):
    out = f"{label}\n   " + ", ".join(f"{k}={'off' if v is None else v}" for k, v in zip(names, combo)) + "\n"
    for pn in ("IS", "C24", "REAL"):
        s, wr, p, tpd = evalc(combo, pn); out += f"   {pn:4s}: Sharpe {s:.2f} | WR {wr:.1f}% | PF {p:.2f} | trades/day {tpd:.2f}\n"
    print(out)
show(cur, "CURRENT v8 (VWAP60 off)")
for target in (68, 70):
    c = df[df.wr_IS >= target].sort_values("sh_IS", ascending=False)
    if len(c): show(c.iloc[0].combo, f"BEST IS Sharpe with IS WR >= {target}%")
