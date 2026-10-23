"""2026-10-19 Federico: 'negative RR can improve it? test on 2020-2023 then 2023-2026'. Reward-to-risk below 1 for every Ultra module:
target at RR x (base stop distance) with the stop widened x ks (RR 0.2 / 0.3 / 0.5 / 0.75, ks 1 / 1.5 / 2 / 3; the module's own target is
the base). Real Databento NQ futures, wrq exit engine on 1-minute bars from each module's own fills, $1.90 + 1 tick per side,
Ultra as coded (ORB trigger filter, VOLB break-even, MOM1030/MOM13 agreement, context / confluence boosts, ICT x2, MOM1030 x4; CPI09
not in the wrq entries). T1 = 2020-01-01..2023-12-31 (choose), T2 = 2024-01-01..2026-10-08 (check, never used to choose).
Per module: every cell's n / WR / PF / net / daily Sharpe in T1 and T2. Portfolio: base vs (a) uniform negative-RR settings,
(b) per-module cell chosen on T1 by Sharpe with WR >= base WR, (c) chosen on T1 by $ -> negrr_lab.json, negrr_cells.csv"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import robust2_build as RB
import db_long, wrq_port, wrq_combo
import final3y as F3
from wrq_lib import getD
T1 = (20200101, 20240101); T2 = (20240101, 20261231)
RRS = (0.2, 0.3, 0.5, 0.75); KSS = (1.0, 1.5, 2.0, 3.0)


def daily_stats(X, lo, hi, days):
    X = X[(X.date >= lo) & (X.date < hi)]; dd = days[(days >= lo) & (days < hi)]
    x = (X.u * X.w).to_numpy(); d = pd.Series(x, index=X.date.to_numpy()).groupby(level=0).sum().reindex(dd, fill_value=0.0)
    w = x[x > 0].sum(); l = -x[x <= 0].sum(); eq = d.cumsum()
    return dict(n=int(len(X)), wr=round(100 * float((X.u > 0).mean()), 1) if len(X) else None, pf=round(float(w / l), 3) if l > 0 else None,
                net=round(float(x.sum())), per_month=round(float(d.mean() * 21)), sharpe=round(float(d.mean() / d.std() * np.sqrt(252)), 2) if d.std() > 0 else 0.0,
                maxdd=round(float((eq.cummax() - eq).max())))


def build(over_extra, cache):
    mods, over, agr, boosts = F3.PROFILES["Ultra"]; wrq_port.PROFILES["_n"] = mods
    ov = {k: v for k, v in over.items() if k in mods}
    for m, q in over_extra.items():
        if m not in mods: continue
        q0, kf = ov.get(m, ({}, None)); ov[m] = ({**(q0 or {}), **q}, kf)
    X = wrq_combo.build("DB", "_n", ov, tuple(a for a in agr if a in mods), cache=cache)
    X = X[X.date >= 20200101].copy(); X.loc[X["mod"] == "MOM1030", "w"] = X.loc[X["mod"] == "MOM1030", "w"] * 4.0   # current default x4
    return X.sort_values(["date", "tin"]).reset_index(drop=True)


if __name__ == "__main__":
    E = RB.setup(); D = getD(db_long.NAME); days = RB.days_real()
    mods = list(F3.PROFILES["Ultra"][0])
    # base reward/risk of each module's own exit
    En = E[E["mod"].isin(mods)]; rr0 = ((En.tp0 - En.ent0).abs() / (En.sl0 - En.ent0).abs()).groupby(En["mod"]).median().to_dict()
    print("base RR per module:", {k: round(v, 2) for k, v in rr0.items()}, flush=True)
    cache = {}; base = build({}, cache); B1, B2 = daily_stats(base, *T1, days), daily_stats(base, *T2, days)
    print("BASE T1", B1, "\nBASE T2", B2, flush=True)
    # per-module cells (module alone, same rules as inside the portfolio: take the module's rows out of the full build)
    rows = []; cells = {}
    for m in mods:
        bm = base[base["mod"] == m]; b1, b2 = daily_stats(bm, *T1, days), daily_stats(bm, *T2, days)
        rows.append(dict(mod=m, rr="base", ks=1.0, kt=1.0, **{"T1_" + k: v for k, v in b1.items()}, **{"T2_" + k: v for k, v in b2.items()}))
        for rr in RRS:
            for ks in KSS:
                if rr0.get(m, 1.0) <= 0 or np.isnan(rr0.get(m, np.nan)): continue
                kt = rr * ks / rr0[m]
                X = build({m: dict(kt=kt, ks=ks)}, cache); xm = X[X["mod"] == m]
                s1, s2 = daily_stats(xm, *T1, days), daily_stats(xm, *T2, days); cells[(m, rr, ks)] = (X, s1, s2)
                rows.append(dict(mod=m, rr=rr, ks=ks, kt=round(kt, 3), **{"T1_" + k: v for k, v in s1.items()}, **{"T2_" + k: v for k, v in s2.items()}))
        print(m, "done", flush=True)
    R = pd.DataFrame(rows); R.to_csv(os.path.join(HERE, "negrr_cells.csv"), index=False)
    OUT = {"base_rr": {k: round(v, 2) for k, v in rr0.items()}, "base": {"T1": B1, "T2": B2}, "portfolios": {}}
    # (a) uniform settings
    for rr in RRS:
        for ks in (1.0, 2.0):
            ov = {m: dict(kt=rr * ks / rr0[m], ks=ks) for m in mods if m in rr0 and rr0[m] > 0}
            X = build(ov, cache); OUT["portfolios"][f"uniform RR {rr} ks {ks}"] = {"T1": daily_stats(X, *T1, days), "T2": daily_stats(X, *T2, days)}
            print("uniform", rr, ks, OUT["portfolios"][f"uniform RR {rr} ks {ks}"], flush=True)
    # (b)/(c) per-module choice on T1
    for crit in ("sharpe", "net"):
        ov = {}; chosen = {}
        for m in mods:
            bm = R[(R["mod"] == m) & (R.rr == "base")].iloc[0]; best = None
            for rr in RRS:
                for ks in KSS:
                    r = R[(R["mod"] == m) & (R.rr == rr) & (R.ks == ks)]
                    if r.empty: continue
                    r = r.iloc[0]
                    if r["T1_wr"] is None or r["T1_wr"] < bm["T1_wr"]: continue          # the point is a higher win rate
                    if r["T1_" + crit] <= bm["T1_" + crit]: continue
                    if best is None or r["T1_" + crit] > best[0]: best = (r["T1_" + crit], rr, ks, r["kt"])
            if best: ov[m] = dict(kt=best[3], ks=best[2]); chosen[m] = dict(rr=best[1], ks=best[2])
        X = build(ov, cache); OUT["portfolios"][f"T1-chosen by {crit}"] = {"chosen": chosen, "T1": daily_stats(X, *T1, days), "T2": daily_stats(X, *T2, days)}
        print("chosen", crit, chosen, "\n   T1", OUT["portfolios"][f"T1-chosen by {crit}"]["T1"], "\n   T2", OUT["portfolios"][f"T1-chosen by {crit}"]["T2"], flush=True)
    json.dump(OUT, open(os.path.join(HERE, "negrr_lab.json"), "w"), indent=1)
