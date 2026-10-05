"""Maximise $/month subject to WR >= 70.5%, PF >= 1.45 and Sharpe >= 3.0 on IS (2020-23), choosing per module: off / variant x
size (1 or 2 lots; ICT keeps its x2 base). Daily P&L matrix per (module, variant) -> exact Sharpe and maxDD for any combination."""
import pickle, numpy as np, pandas as pd, random
A = pickle.load(open("wr70_variants.pkl", "rb"))
def mats(df, days):
    x = df.u * df.w
    keys = sorted(set(zip(df["mod"], df["var"])))
    M = {}; S = {}
    for (m, v), g in df.assign(x=x).groupby(["mod", "var"]):
        M[(m, v)] = g.groupby("date").x.sum().reindex(days, fill_value=0).to_numpy()
        S[(m, v)] = (len(g), int((g.u > 0).sum()), g.x[g.x > 0].sum(), -g.x[g.x <= 0].sum())
    return M, S
nq = A["nq_1m"]; mq = A["mnq_fut"]
def period(df, lo, hi):
    d = df[(df.date >= lo) & (df.date < hi)]; days = np.array(sorted(d.date.unique())); return mats(d, days) + (days,)
PER = {"IS": period(nq, 20200201, 20240101), "C24": period(nq, 20240101, 30000000), "REAL": period(mq, 20240201, 30000000)}
OPTS = {}
for (m, v) in PER["IS"][1]: OPTS.setdefault(m, []).append(v)
MODS = sorted(OPTS)
CHOICES = {m: [None] + [(v, k) for v in OPTS[m] for k in (1, 2)] for m in MODS}
def evalsel(sel, per):
    M, S, days = PER[per]; d = np.zeros(len(days)); n = w = gp = gl = 0
    for m, c in sel.items():
        if c is None or (m, c[0]) not in S: continue
        v, k = c; d += k * M[(m, v)]; a = S[(m, v)]; n += a[0]; w += a[1]; gp += k * a[2]; gl += k * a[3]
    eq = np.cumsum(d); dd = (np.maximum.accumulate(eq) - eq).max() if len(eq) else 0
    return dict(wr=100 * w / n if n else 0, pf=gp / gl if gl else 0, sharpe=d.mean() / d.std() * np.sqrt(252) if d.std() > 0 else 0, mo=d.mean() * 21, dd=dd, tpd=n / len(days))
def obj(sel):
    r = evalsel(sel, "IS")
    pen = (max(0, 70.5 - r["wr"]) + max(0, 1.45 - r["pf"]) * 10 + max(0, 2.97 - r["sharpe"]) * 5 + max(0, r["dd"] - 2000) / 100) * 1e5
    return r["mo"] - pen
random.seed(7); best = []
for start in range(300):
    sel = {m: random.choice(CHOICES[m]) for m in MODS}
    improved = True
    while improved:
        improved = False
        for m in random.sample(MODS, len(MODS)):
            cur = obj(sel); bc = sel[m]
            for c in CHOICES[m]:
                sel[m] = c; o = obj(sel)
                if o > cur + 1e-6: cur = o; bc = c; improved = True
            sel[m] = bc
    key = tuple(sorted((m, c) for m, c in sel.items() if c is not None))
    if key not in [b[1] for b in best]: best.append((obj(sel), key))
best.sort(reverse=True)
ref = {"CRT11": (2.0, 1), "ICT": (1.0, 1), "MOM11": (0.3, 1), "MSEQ": (0.5, 1), "MSEQS": (0.75, 1), "ORB60": (0.75, 1), "ORB90": (0.6, 1), "REV06": (0.3, 1), "VOLB_tf1": (0.5, 1), "VW13": (0.5, 1), "VW13b": (0.5, 1)}
rows = [dict(name="WR70Plus actual", mods="", **{f"{p}_{k}": round(v, 2) for p in ("IS", "C24", "REAL") for k, v in evalsel(ref, p).items()})]
for o, key in best[:12]:
    sel = dict(key); rows.append(dict(name=f"cand {len(rows)}", mods=" ".join(f"{m}:{c[0]}x{c[1]}" for m, c in key), **{f"{p}_{k}": round(v, 2) for p in ("IS", "C24", "REAL") for k, v in evalsel(sel, p).items()}))
R = pd.DataFrame(rows); pd.set_option("display.width", 320); pd.set_option("display.max_colwidth", 230)
for p in ("IS", "C24", "REAL"):
    print(p); print(R[["name"] + [f"{p}_{k}" for k in ("wr", "pf", "sharpe", "mo", "dd", "tpd")]].to_string(index=False))
print(R[["name", "mods"]].to_string(index=False))
pickle.dump(best[:12], open("wr70_money_best2.pkl", "wb"))
