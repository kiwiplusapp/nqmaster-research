"""Eval-oriented optimisation of the pullback-day engine. Parameters chosen on eval starts in 2020-2023 (IS);
pass rates for starts in 2024-01 -> 2026-08 (OOS) reported untouched. Drawdown checked on intraday REALIZED P&L
(trades ordered by exit time) with a trailing peak - stricter than end-of-day."""
import itertools, sys
import numpy as np, pandas as pd
from numba import njit
from common import Ctx
cx = Ctx(); DAYS = np.array(cx.rth_days)
T = pd.read_pickle("eval_trades.pkl")

@njit(cache=True)
def evals(tot, mn, mx, target, dd, maxdays, s0, s1):
    npass = 0; nbust = 0; nn = 0; dsum = 0
    for s in range(s0, s1):
        nn += 1; eq = 0.0; peak = 0.0
        for k in range(s, min(len(tot), s + maxdays)):
            if eq + mn[k] <= peak - dd:
                nbust += 1; break
            peak = max(peak, eq + mx[k])
            eq += tot[k]
            if eq >= target:
                npass += 1; dsum += k - s + 1; break
            if eq <= peak - dd:
                nbust += 1; break
    return npass / nn, nbust / nn, (dsum / npass if npass else 0.0)

def build_days(tr, size, day_stop_win=0.0, day_stop_loss=0.0, maxopen=0):
    tr = tr.assign(sz=size).sort_values(["date", "t_in"])
    tot = {}; mn = {}; mx = {}
    for d, g in tr.groupby("date", sort=False):
        ins = g.t_in.to_numpy(); outs = g.t_out.to_numpy(); u = (g.usd.to_numpy()) * g.sz.to_numpy()
        take = np.zeros(len(g), bool)
        for i in range(len(g)):
            if g.sz.iat[i] <= 0: continue
            done = take & (outs <= ins[i])
            real = u[done].sum()
            if day_stop_win and real >= day_stop_win: continue
            if day_stop_loss and real <= -day_stop_loss: continue
            if maxopen and (take & (outs > ins[i])).sum() >= maxopen: continue
            take[i] = True
        o = np.argsort(outs[take]); seq = np.cumsum(u[take][o]) if take.any() else np.zeros(1)
        tot[d] = seq[-1]; mn[d] = min(0.0, seq.min()); mx[d] = max(0.0, seq.max())
    f = lambda D: pd.Series(D).reindex(DAYS, fill_value=0.0).to_numpy()
    return f(tot), f(mn), f(mx)

IS_END = int(np.searchsorted(DAYS, 20240101)); N = len(DAYS)
def score(days, scale, target, dd, maxdays):
    t, a, b = (x * scale for x in days)
    return evals(t, a, b, target, dd, maxdays, 0, IS_END - maxdays // 2), evals(t, a, b, target, dd, maxdays, IS_END, N - 15)

def portfolio(mods_cfg, th):
    parts = []
    for mod, v in mods_cfg.items():
        if mod == "mseq":
            parts.append(T[T["mod"] == "mseq"])
        else:
            t1, cap = v
            s = T[(T["mod"] == mod) & (T.t1 == t1) & (T.cap == cap)]
            parts.append(s[s.prevret < th])
    return pd.concat(parts)

if __name__ == "__main__":
    ACC = [("50K", 3000, 2500), ("25K", 1500, 1500)]
    full = {"orb60": (0.6, 0.35), "vw60": (0.6, 0.35), "orb30": (0.75, 0.35), "orb15": (0.75, 0.35), "vw30": (0.75, 0.35), "mseq": None}
    variants = {
        "all6": full,
        "no_orb15_vw30": {k: v for k, v in full.items() if k not in ("orb15", "vw30")},
        "orb60_vw60_mseq": {k: full[k] for k in ("orb60", "vw60", "mseq")},
        "all6_cap25": {k: ((v[0], 0.25) if v else None) for k, v in full.items()},
        "all6_t1_1.0": {k: ((1.0, v[1]) if v else None) for k, v in full.items()},
        "all6_t1_0.5": {k: ((0.5, v[1]) if v else None) for k, v in full.items()},
    }
    rows = []
    for vn, cfgm in variants.items():
        for th in (0.0, 0.2, 0.44, 0.6):
            P = portfolio(cfgm, th)
            riskusd = P.risk_pts.to_numpy() * 2.0 + 1.0
            sizings = {"fixed1": np.ones(len(P))}
            for R in (150, 250):
                sizings[f"risk{R}"] = np.maximum(0, np.floor(R / riskusd + 0.5))
            tier = np.where(P.prevret.to_numpy() < -0.3, 2.0, 1.0); tier[P["mod"].to_numpy() == "mseq"] = 1.0
            sizings["tier"] = tier
            for sn, sz in sizings.items():
                for dsw, dsl, mo in ((0, 0, 0), (0, 0, 3), (800, 0, 0), (0, 600, 0), (800, 600, 3)):
                    days = build_days(P, sz, dsw, dsl, mo)
                    for acc, tg, dd in ACC:
                        best = None
                        for scale in (0.5, 0.75, 1, 1.5, 2, 2.5, 3, 4):
                            (pi, bi, di), (po, bo, do) = score(days, scale, tg, dd, 20)
                            if best is None or pi > best[1]:
                                best = (scale, pi, bi, di, po, bo, do)
                        (p60i, b60i, _), (p60o, b60o, _) = score(days, best[0], tg, dd, 60)
                        rows.append(dict(var=vn, th=th, sizing=sn, dsw=dsw, dsl=dsl, maxopen=mo, acc=acc, scale=best[0],
                                         is20=round(best[1]*100), is20bust=round(best[2]*100), is_days=round(best[3], 1),
                                         oos20=round(best[4]*100), oos20bust=round(best[5]*100), oos_days=round(best[6], 1),
                                         is60=round(p60i*100), oos60=round(p60o*100), oos60bust=round(b60o*100)))
            print(vn, th, "done"); sys.stdout.flush()
    g = pd.DataFrame(rows); g.to_csv("eval_opt.csv", index=False)
    for acc in ("50K", "25K"):
        print(f"\n==== {acc}: top 20 by IS pass-in-20-days")
        print(g[g.acc == acc].sort_values("is20", ascending=False).head(20).to_string(index=False))
