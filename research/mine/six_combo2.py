"""2026-10-16 six-year round, step 5b: six_combo.py added several variants of the same signal (same entries, different target), which a
single NinjaTrader module cannot do. Here: one representative per signal cluster, chosen by standalone T1 Sharpe (T2 not used), ENG10
family excluded (the coded ENG10 fails T2: PF 1.105), NF05 re-parameterisations excluded (G_DRIVE 20:00 x540 = NF05), LATE_MOM uses the
already-coded LATEFH. Then forward selection on T1 Sharpe (>= +0.01 per addition). -> six_combo2.json"""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import six_lib as S
from six_modules import mod_daily

CLUSTERS = {"CA_SVWAP04": [("CLOCK_ANCHOR", 916), ("CLOCK_ANCHOR", 918)], "CA_SOPEN04": [("CLOCK_ANCHOR", 1527)],
            "ENG0206": [("ENGULF_4H", 25), ("ENGULF_4H", 28), ("ENGULF_4H", 408)], "ORFAIL": [("OR_FAIL", 142)],
            "GD03": [("G_DRIVE", 3922)], "RVOL11": [("RVOL_DRIVE", j) for j in (4224, 4225, 4226, 4229)], "RVOL11hi": [("RVOL_DRIVE", 3649)],
            "RVOL1030": [("RVOL_DRIVE", 2880)], "CAM3": [("PIVOT_FADE", 365)], "DAYMR": [("DAY_MR", 1250), ("DAY_MR", 1538)]}


def sr(x): return float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else 0.0


if __name__ == "__main__":
    TR = {}
    for f in ("trades_db_old.pkl", "trades_db_new.pkl"): TR.update(pickle.load(open(os.path.join(HERE, f), "rb")))
    R = pd.concat([pd.read_csv(os.path.join(HERE, f)) for f in ("results_db_old.csv", "results_db_new.csv")], ignore_index=True)
    U = S.base(); M = mod_daily(U); idx = M.index; t1 = idx < S.MID
    X = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["Ultra"][0]
    g = X[(X["mod"] == "LATEFH") & (X.date >= S.START)]
    reps = {"LATEFH": ((g.w * g.u).groupby(g.date).sum().reindex(idx, fill_value=0.0), (g.w * g.u).to_numpy(), g.date.to_numpy(), "existing code UseLateFh")}
    for cl, mem in CLUSTERS.items():
        best = None
        for key in mem:
            t = TR[key]["real"]; t = t[t.date >= S.START]; d = t.usd.groupby(t.date).sum().reindex(idx, fill_value=0.0)
            s = sr(d[t1])
            if best is None or s > best[0]:
                p = R[(R.fam == key[0]) & (R.j == key[1])].params.iloc[0]
                best = (s, (d, t.usd.to_numpy(), t.date.to_numpy(), f"{key[0]}#{key[1]} {p}"))
        reps[cl] = best[1]
    tot = M.sum(axis=1); chosen = []
    while True:
        best = (sr(tot[t1]) + 0.01, None)
        for k in reps:
            if k in chosen: continue
            s = sr((tot + reps[k][0])[t1])
            if s > best[0]: best = (s, k)
        if best[1] is None: break
        chosen.append(best[1]); tot = tot + reps[best[1]][0]
        print("add", best[1], reps[best[1]][3], "T1 SR", round(best[0], 3), flush=True)
    b = S.metr(M.sum(axis=1)); c = S.metr(tot)
    n4 = sum(pd.Series(reps[k][2]).value_counts().reindex(idx, fill_value=0).to_numpy() for k in chosen)
    c4 = S.metr(S.daily(U, extra=3.0) + sum(reps[k][0] for k in chosen) - 3.0 * n4)
    # per-trade portfolio stats
    allu = np.concatenate([(U.w * U.u).to_numpy()] + [reps[k][1] for k in chosen]); alld = np.concatenate([U.date.to_numpy()] + [reps[k][2] for k in chosen])
    OUT = dict(chosen={k: reps[k][3] for k in chosen}, base=b, combined=c, combined_plus4=c4, base_plus4=S.metr(S.daily(U, extra=3.0)),
               trades=S.tstats(allu, alld), base_trades=S.tstats((U.w * U.u).to_numpy(), U.date.to_numpy()),
               standalone={k: dict(stats=S.tstats(reps[k][1], reps[k][2]), plus4=S.tstats(reps[k][1] - 3.0, reps[k][2]), desc=reps[k][3]) for k in reps})
    print("base    ", {p: (b[p]['sharpe'], b[p]['net'], b[p]['maxdd'], b[p]['worst_month']) for p in b})
    print("combined", {p: (c[p]['sharpe'], c[p]['net'], c[p]['maxdd'], c[p]['worst_month']) for p in c})
    print("+4 ticks base", {p: OUT['base_plus4'][p]['sharpe'] for p in b}, "combined", {p: c4[p]['sharpe'] for p in c4})
    print("trades base", OUT["base_trades"], "\ntrades comb", OUT["trades"])
    json.dump(OUT, open(os.path.join(HERE, "six_combo2.json"), "w"), indent=1, default=str)
