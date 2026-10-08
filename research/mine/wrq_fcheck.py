"""wrq_fcheck: plateau + portfolio check of the IS-selected one-feature filters that also raised PF out of sample in
wrq_filters.py (ORB60 pdcd, VOLB_tf1 tso, LF0430 pdcd, CRT11 pdr, ORB90 atrr). Threshold grids per period (module level, current
exits) and portfolio effect of the IS-chosen threshold (Ultra / WR70Plus, rules + conflict filter, +4 ticks).
-> wrq_fcheck.csv, wrq_fcheck_port.csv"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_lib import getD, PER, SLIP
from wrq_exits import arrays, sim, st
from wrq_port import build_profile, metrics, days_of, PROFILES

FT = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wrq_feats.pkl"), "rb"))
CHECK = {"ORB60": ("pdcd", "lt", (-0.3, -0.2, -0.1, 0.0, 0.05, 0.0988, 0.15, 0.2, 0.3)),
         "ORB90": ("atrr", "gt", (0.9, 1.0, 1.07, 1.15, 1.25, 1.4)),
         "VOLB_tf1": ("tso", "gt", (30, 45, 60, 77, 90, 120, 180, 240)),
         "LF0430": ("pdcd", "gt", (-0.3, -0.2, -0.1, -0.0223, 0.05, 0.1, 0.2)),
         "CRT11": ("pdr", "lt", (0.5, 0.6, 0.7, 0.726, 0.8, 0.9, 1.0))}
SEL = {"ORB60": 0.0988, "ORB90": 1.07, "VOLB_tf1": 77, "LF0430": -0.0223, "CRT11": 0.726}

def keepfn(mod, thr):
    f, op, _ = CHECK[mod]
    def k(E, name):
        x = FT[name].loc[E.index, f].to_numpy()
        drop = (x < thr) if op == "lt" else (x > thr)
        return ~np.nan_to_num(drop, nan=0).astype(bool)
    return k

EN = pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wrq_entries.pkl"), "rb"))

if __name__ == "__main__":
    RUNS = [("IS", "nq_1m.npz", SLIP, False), ("C24", "nq_1m.npz", SLIP, False), ("REAL", "mnq_fut.npz", SLIP, False), ("L15", "nqhd_long.npz", 0.0, True),
            ("REAL+4", "mnq_fut.npz", SLIP * 5, False)]
    rows = []
    for mod, (f, op, grid) in CHECK.items():
        for lab, name, slip, norm in RUNS:
            E = EN[name][EN[name]["mod"] == mod]; A = arrays(E); u, ok, _ = sim(A, getD(name), slip, {}, norm)
            per = lab.replace("+4", ""); _, lo, hi = PER[per]
            msk = ok & (A["date"] >= lo) & (A["date"] < hi) & (~A["fomc"] if per != "L15" else True)
            x = FT[name].loc[E.sort_values("fi", kind="stable").index, f].to_numpy()
            for thr in (None,) + tuple(grid):
                k = msk.copy()
                if thr is not None: k &= ~np.nan_to_num((x < thr) if op == "lt" else (x > thr), nan=0).astype(bool)
                n, wr, pf_, ex, net = st(u[k])
                rows.append(dict(mod=mod, rule="base" if thr is None else f"{f} {'<' if op == 'lt' else '>'} {thr} out", per=lab, n=n, frac=n / max(msk.sum(), 1), wr=wr, pf=pf_, exp=ex, net=net))
    R = pd.DataFrame(rows); R.to_csv("wrq_fcheck.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    for mod in CHECK:
        P = R[R["mod"] == mod].pivot_table(index="rule", columns="per", values=["frac", "wr", "pf"], sort=False)
        print("----", mod); print(P[[("frac", "IS"), ("wr", "IS"), ("pf", "IS"), ("wr", "C24"), ("pf", "C24"), ("wr", "REAL"), ("pf", "REAL"), ("wr", "L15"), ("pf", "L15"), ("pf", "REAL+4")]].round(3).to_string())
    # portfolio effect of the IS-chosen thresholds
    prow = []; cache = {}
    for prof in ("Ultra", "WR70Plus"):
        for per in ("IS", "C24", "REAL", "L15"):
            days = days_of(per)
            for slip, tag in ((SLIP, ""), (SLIP * 5, " +4t")):
                if per == "L15" and tag: continue
                cands = [("base", None)] + [(f"{m} {CHECK[m][0]} filter", {m: ({}, keepfn(m, SEL[m]))}) for m in CHECK if m in PROFILES[prof]]
                for nm, over in cands:
                    X = build_profile(per, prof, over, slip=slip, cache=cache); r = metrics(X, days); r.update(prof=prof, per=per + tag, cand=nm); prow.append(r)
            print(prof, per, flush=True)
    PR = pd.DataFrame(prow); PR.to_csv("wrq_fcheck_port.csv", index=False)
    for prof in ("Ultra", "WR70Plus"):
        for c in ("wr", "pf", "sharpe", "mo"):
            print(f"=== {prof} {c}"); print(PR[PR.prof == prof].pivot_table(index="cand", columns="per", values=c, sort=False).round(3).to_string())
