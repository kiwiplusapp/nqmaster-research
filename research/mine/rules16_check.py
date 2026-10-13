"""Do the current NQMaster rules hold on data they never saw? (2026-10-12)
The 12 context rules (filt_sel.pkl: 11 x2 boosts + 1 skip) and the 2 confluence rules were chosen on CFD 2020-23 and checked on
2024-25 + a 2026 holdout. Here: Ultra modules (no rules) rebuilt on REAL Databento NQ futures 2010-2026 (db_long machinery);
for every rule, the trades it touches vs the other trades of the same module, PF and WR per block:
2010-14 and 2015-19 (cost-normalised, never used to choose anything), 2020-23 and 2024-26 (real $). -> rules16_check.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import robust2_build as RB
import wrq_port, filt_feats
from wrq_lib import getD, S
from final3y import PROFILES
from db_long import FOMC_1019

BLOCKS = (("2010-14n", "DB_N", 20100601, 20150101), ("2015-19n", "DB_N", 20150101, 20200101), ("2020-23", "DB", 20200101, 20240101), ("2024-26", "DB", 20240101, 20991231))


def pf(x):
    x = np.asarray(x); l = -x[x <= 0].sum(); return round(float(x[x > 0].sum() / l), 2) if l > 0 and len(x) >= 10 else None


if __name__ == "__main__":
    RB.setup(); D = getD(RB.NAME)
    mods, over, agr, boosts = PROFILES["Ultra"]
    X = {}
    for per in ("DB", "DB_N"):
        T = wrq_port.build_profile(per, mods, {k: v for k, v in over.items() if k in mods}, rules=False)
        if per == "DB": T = T[T.atr >= 150] if "atr" in T else T
        X[per] = T.sort_values(["date", "tin"]).reset_index(drop=True)
        print(per, len(T), flush=True)
    sel = pickle.load(open(os.path.join(HERE, "filt_sel.pkl"), "rb"))
    OUT = {"context": [], "confluence": []}
    F = {per: filt_feats.feats(D, X[per][["date", "mod", "tin", "d"]]) for per in X}
    for r, kind in sel:
        rec = dict(rule=f"{kind} {r['mod']} {r['feat']} {r['bucket']}", blocks={})
        for lab, per, lo, hi in BLOCKS:
            T = X[per]; f = F[per][r["feat"]]
            m = (T["mod"] == r["mod"]) & (T.date >= lo) & (T.date < hi)
            hit = m & ((f < r["hi"]) if r["bucket"].startswith("low") else (f >= r["lo"])).fillna(False)
            rest = m & ~hit
            rec["blocks"][lab] = dict(n_hit=int(hit.sum()), pf_hit=pf(T.u[hit]), wr_hit=round(100 * float((T.u[hit] > 0).mean()), 1) if hit.any() else None,
                                      pf_rest=pf(T.u[rest]), wr_rest=round(100 * float((T.u[rest] > 0).mean()), 1) if rest.any() else None)
        OUT["context"].append(rec)
        print(rec["rule"], {k: (v["n_hit"], v["pf_hit"], v["pf_rest"]) for k, v in rec["blocks"].items()}, flush=True)
    # confluence A: late modules after 11:00 against MOM11 and with the overnight sign; B: REV06 after LON same way
    for per in X:
        T = X[per]
        m11 = T[T["mod"] == "MOM11"].groupby("date").d.first()
        on = T[T["mod"].isin(["ON07", "REV06", "LON"])].groupby("date").d.agg(lambda s: np.sign(s.sum()))
        T["A"] = T["mod"].isin(["CRT11", "MOM13", "MSEQ", "MSEQS"]) & (T.date.map(m11) * T.d == -1) & (T.date.map(on) * T.d == 1) & (T.tin > S(1100))
        lon = T[T["mod"] == "LON"].drop_duplicates("date").set_index("date")
        T["B"] = (T["mod"] == "REV06") & (T.date.map(lon.d) == T.d) & (T.date.map(lon.tin) <= T.tin)
    for rule, base in (("A late x2 (against MOM11, with overnight)", ["CRT11", "MOM13", "MSEQ", "MSEQS"]), ("B skip REV06 after same-way LON", ["REV06"])):
        rec = dict(rule=rule, blocks={})
        for lab, per, lo, hi in BLOCKS:
            T = X[per]; m = T["mod"].isin(base) & (T.date >= lo) & (T.date < hi); hit = m & T[rule[0]]; rest = m & ~T[rule[0]]
            rec["blocks"][lab] = dict(n_hit=int(hit.sum()), pf_hit=pf(T.u[hit]), pf_rest=pf(T.u[rest]),
                                      wr_hit=round(100 * float((T.u[hit] > 0).mean()), 1) if hit.any() else None, wr_rest=round(100 * float((T.u[rest] > 0).mean()), 1))
        OUT["confluence"].append(rec); print(rule, {k: (v["n_hit"], v["pf_hit"], v["pf_rest"]) for k, v in rec["blocks"].items()}, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "rules16_check.json"), "w"), indent=1)
