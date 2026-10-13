"""Portfolio effect of removing the context rules that did not hold on 2010-19 + 2024-26 (rules16_check.json). Ultra as coded
(BE, ORBt, MOM agreement), real Databento NQ 2020-26 (MinATR 150) and cost-normalised 2010-19. -> rules16_prune.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import robust2_build as RB
import wrq_port, db_long
from wrq_lib import getD
from news import NEWS

DROPS = {"current": [], "-ORB90vw -ORB60atr": [("ORB90", "vw"), ("ORB60", "atr")],
         "-ORB90vw -ORB60atr -CRT11trend": [("ORB90", "vw"), ("ORB60", "atr"), ("CRT11", "trend")],
         "-ORB90vw -ORB60atr -CRT11trend -ORB60gap": [("ORB90", "vw"), ("ORB60", "atr"), ("CRT11", "trend"), ("ORB60", "gap")],
         "no context rules": "all"}


def stats(X, lo, hi, real, alld, atr_d):
    s = X[(X.date >= lo) & (X.date < hi)]; x = s.u * s.w
    r = dict(n=int(len(s)), wr=round(100 * float((s.u > 0).mean()), 2), pf=round(float(x[x > 0].sum() / -x[x <= 0].sum()), 3))
    if real:
        dd = alld[(alld >= lo) & (alld < hi)]; dd = dd[atr_d.reindex(dd).to_numpy() >= 150]
        d = x.groupby(s.date).sum().reindex(dd, fill_value=0.0); eq = d.cumsum(); mo = d.groupby(d.index // 100).sum()
        r.update(per_month=round(float(d.mean() * 21)), sharpe=round(float(d.mean() / d.std() * np.sqrt(252)), 2), max_dd=round(float((eq.cummax() - eq).max())), worst_month=round(float(mo.min())))
    return r


if __name__ == "__main__":
    RB.setup(); D = getD(RB.NAME)
    alld = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); alld = alld[~np.isin(alld, list(NEWS["FOMC"]))]
    atr_d = pd.Series(D.atr, index=D.daydate).groupby(level=0).last()
    full = pickle.load(open(os.path.join(HERE, "filt_sel.pkl"), "rb")); OUT = {}
    for name, drop in DROPS.items():
        wrq_port._SEL = [] if drop == "all" else [(r, k) for r, k in full if (r["mod"], r["feat"]) not in drop]
        Xr = db_long.trades("Ultra", "DB"); Xr = Xr[Xr.atr >= 150]; Xn = db_long.trades("Ultra", "DB_N")
        rec = {"2010-14n": stats(Xn, 20100601, 20150101, False, alld, atr_d), "2015-19n": stats(Xn, 20150101, 20200101, False, alld, atr_d),
               "2020-23": stats(Xr, 20200101, 20240101, True, alld, atr_d), "2024-26": stats(Xr, 20240101, 20991231, True, alld, atr_d)}
        OUT[name] = rec; print(f"{name:42s}", {k: (v["wr"], v["pf"], v.get("per_month"), v.get("sharpe"), v.get("max_dd"), v.get("worst_month")) for k, v in rec.items()}, flush=True)
    wrq_port._SEL = full
    json.dump(OUT, open(os.path.join(HERE, "rules16_prune.json"), "w"), indent=1)
