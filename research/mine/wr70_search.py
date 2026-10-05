import pickle, numpy as np, pandas as pd, random
A = pickle.load(open("wr70_variants.pkl", "rb"))
def agg(df, days):
    x = df.u * df.w
    g = df.assign(win=(df.u > 0).astype(int), gp=np.where(x > 0, x, 0), gl=np.where(x <= 0, -x, 0)).groupby(["mod", "var"]).agg(n=("u", "size"), wins=("win", "sum"), gp=("gp", "sum"), gl=("gl", "sum"))
    return g, days
P = {}
nq = A["nq_1m"]; mq = A["mnq_fut"]
P["IS"] = agg(nq[(nq.date >= 20200201) & (nq.date < 20240101)], nq[(nq.date >= 20200201) & (nq.date < 20240101)].date.nunique())
P["C24"] = agg(nq[nq.date >= 20240101], nq[nq.date >= 20240101].date.nunique())
P["REAL"] = agg(mq[mq.date >= 20240201], mq[mq.date >= 20240201].date.nunique())
OPTS = {}
for (m, v) in P["IS"][0].index: OPTS.setdefault(m, []).append(v)
MODS = sorted(OPTS); print({m: OPTS[m] for m in MODS})
def score(sel, per):
    g, nd = P[per]; n = w = gp = gl = 0
    for m, v in sel.items():
        if v is None or (m, v) not in g.index: continue
        r = g.loc[(m, v)]; n += r.n; w += r.wins; gp += r.gp; gl += r.gl
    return (100 * w / n if n else 0), (gp / gl if gl else 0), n / nd, (gp - gl) / nd * 21
def obj(sel, wrmin=70.5, tpdmin=3.0):
    wr, pf, tpd, mo = score(sel, "IS")
    pen = max(0, wrmin - wr) * 0.2 + max(0, tpdmin - tpd) * 0.5
    return pf - pen
random.seed(1); best = []
for start in range(400):
    sel = {m: random.choice(OPTS[m] + [None]) for m in MODS}
    improved = True
    while improved:
        improved = False
        for m in random.sample(MODS, len(MODS)):
            cur = obj(sel); bv = sel[m]
            for v in OPTS[m] + [None]:
                sel[m] = v; o = obj(sel)
                if o > cur + 1e-9: cur = o; bv = v; improved = True
            sel[m] = bv
    key = tuple(sorted((m, v) for m, v in sel.items() if v is not None))
    if key not in [b[1] for b in best]: best.append((obj(sel), key))
best.sort(reverse=True)
rows = []
for o, key in best[:25]:
    sel = dict(key); r = dict(obj=round(o, 3), mods=" ".join(f"{m}:{v}" for m, v in key))
    for per in ("IS", "C24", "REAL"):
        wr, pf, tpd, mo = score(sel, per); r.update({per + "_wr": round(wr, 1), per + "_pf": round(pf, 3), per + "_tpd": round(tpd, 2), per + "_mo": round(mo)})
    rows.append(r)
R = pd.DataFrame(rows); pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 200)
print(R.to_string(index=False))
pickle.dump(best[:25], open("wr70_best.pkl", "wb"))
