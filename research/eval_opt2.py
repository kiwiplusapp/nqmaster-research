"""Tiered sizing by pullback depth (2-day move against trend) and gap-with-trend; eval pass rates IS-chosen, OOS reported."""
import sys, numpy as np, pandas as pd
from eval_opt import T, build_days, score, portfolio, DAYS
from common import Ctx
from nt_v2_replica import daily_stats
cx = Ctx(); A, Tr, _ = daily_stats(cx)
nd = cx.nd; cl = np.full(nd, np.nan); op = np.full(nd, np.nan)
for d in range(nd):
    a, b = cx.open_idx[d], cx.close_idx[d]
    if a >= 0 and b > a: cl[d] = cx.c[b]; op[d] = cx.o[a]
ret2 = {}; gap = {}
for d in range(3, nd):
    t = Tr[d]; a = A[d]
    if t == 0 or not a > 0: continue
    p = d - 1
    while p > 0 and np.isnan(cl[p]): p -= 1
    q = p - 1
    while q > 0 and np.isnan(cl[q]): q -= 1
    r = q - 1
    while r > 0 and np.isnan(cl[r]): r -= 1
    ret2[cx.dates[d]] = (cl[p] - cl[r]) / a * t
    gap[cx.dates[d]] = (op[d] - cl[p]) / a * t if not np.isnan(op[d]) else 0.0
T["ret2"] = T.date.map(ret2); T["gap"] = T.date.map(gap)
full = {"orb60": (0.6, 0.35), "vw60": (0.6, 0.35), "orb30": (0.75, 0.35), "orb15": (0.75, 0.35), "vw30": (0.75, 0.35), "mseq": None}
sub = {k: full[k] for k in ("orb60", "vw60", "orb30", "mseq")}
rows = []
for vn, cfgm in (("all6", full), ("orb60_vw60_orb30_mseq", sub)):
    for th in (0.2, 0.44):
        P = portfolio(cfgm, th)
        nm = P["mod"].to_numpy() != "mseq"
        r2 = P.ret2.fillna(0).to_numpy(); gp = P.gap.fillna(0).to_numpy()
        tiers = {"flat": np.ones(len(P)),
                 "deep2x": np.where(nm & (r2 < -0.37), 2.0, 1.0),
                 "deep2x_gap2x": np.where(nm & ((r2 < -0.37) | (gp > 0.17)), 2.0, 1.0),
                 "deep3_gap2": np.where(nm & (r2 < -0.37), 3.0, np.where(nm & (gp > 0.17), 2.0, 1.0)),
                 "skip_ext2": np.where(nm & (r2 > 0.63), 0.0, 1.0),
                 "deep2x_skip_ext2": np.where(nm & (r2 < -0.37), 2.0, np.where(nm & (r2 > 0.63), 0.0, 1.0))}
        for tn, sz in tiers.items():
            for dsw, dsl, mo in ((0, 0, 0), (0, 0, 4), (0, 700, 0), (1000, 0, 0)):
                days = build_days(P, sz, dsw, dsl, mo)
                u = P.usd.to_numpy() * sz
                pf = u[u > 0].sum() / -u[u < 0].sum()
                for acc, tg, dd in (("50K", 3000, 2500), ("50K-2000", 3000, 2000), ("25K", 1500, 1500)):
                    best = None
                    for scale in (0.5, 0.75, 1, 1.25, 1.5, 2, 2.5, 3, 4):
                        (pi, bi, di), (po, bo, do) = score(days, scale, tg, dd, 20)
                        if best is None or pi > best[1]: best = (scale, pi, bi, di, po, bo, do)
                    (p60i, _, _), (p60o, b60o, _) = score(days, best[0], tg, dd, 60)
                    (p30i, _, _), (p30o, b30o, _) = score(days, best[0], tg, dd, 30)
                    rows.append(dict(var=vn, th=th, tier=tn, dsw=dsw, dsl=dsl, mo=mo, acc=acc, pf=round(pf, 2), trades_wk=round((sz > 0).sum() / 350, 2),
                                     scale=best[0], is20=round(best[1]*100), is20b=round(best[2]*100), oos20=round(best[4]*100), oos20b=round(best[5]*100),
                                     oos_days=round(best[6], 1), oos30=round(p30o*100), oos30b=round(b30o*100), is60=round(p60i*100), oos60=round(p60o*100), oos60b=round(b60o*100)))
        print(vn, th, "done"); sys.stdout.flush()
g = pd.DataFrame(rows); g.to_csv("eval_opt2.csv", index=False)
for acc in ("50K", "50K-2000", "25K"):
    print(f"\n==== {acc}: top 12 by IS pass<=20d")
    print(g[g.acc == acc].sort_values("is20", ascending=False).head(12).to_string(index=False))
