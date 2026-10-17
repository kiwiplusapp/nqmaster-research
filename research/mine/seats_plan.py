"""2026-10-17 'quiero $250-300 por dia': income of a SET of funded seats on the same market path (same strategies -> correlated),
real Databento NQ 2020-02..2026-10 minute paths of the current Ultra (UltraR + CPI09, MOM1030/CPI09 x4; eval x8), optionally + the
six-year modules (group 11). Seats: MFFU Rapid EOD 50K 1c (today's preset: eval profit stop 800, funded cap 300 < $2,000, keep $4,100),
MFFU 1c with step-up 2c at a $4,000 cushion (keep $6,100), Lucid Flex 50K at 1c and 2c (eval profit stop 1,350, funded cap 300 below a
$1,000 cushion, payout at $4,000, 5 payouts then a new eval). Starts staggered 5 trading days. History (every 5th start, T1 starts
2020-02..2023-10 / T2 2024-01..) and 10-day block bootstrap years per period. Edge: full / -35% / -50% / zero (haircut of the mean
daily P&L per contract, scaled with size). Output per plan: $/month and $/calendar day mean, median, p10, p90, P(year < 0),
P(avg >= $250/day), P(avg >= $300/day). -> seats_plan.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from wrq_lib import getD
from mffu_rapid import life_m
from sniper_life import build
import acct1c_lib as A
H = 252; NSEAT = 8; NB = 400

PLANS = {"1 MFFU 50K 1c": [("MFFU", 1)], "3 MFFU 50K 1c": [("MFFU", 3)], "3 MFFU step-up": [("MFFUs", 3)],
         "5 Lucid Flex 50K 2c": [("LF2", 5)], "5 Lucid Flex 50K 1c": [("LF1", 5)],
         "3 MFFU 1c + 5 Lucid 2c": [("MFFU", 3), ("LF2", 5)], "3 MFFU step-up + 5 Lucid 2c": [("MFFUs", 3), ("LF2", 5)],
         "3 MFFU 1c + 5 Lucid 1c": [("MFFU", 3), ("LF1", 5)]}


GOLD = {"Robust": ["OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206"], "WinRate": ["OD1030", "ENG0408", "SVWAP22"]}


def gold_paths(days, prof="Robust"):
    """GoldMaster minute grids from the dense store (1 MGC; CFD XAU 2020-23 'IS', MGC real 'REAL' from 2024-02-16, CFD 'C24' in between),
    mapped to the Databento NQ day list: low path = dense L (realized + open P&L at the adverse extreme), close path ~ realized R."""
    DN = os.path.join(os.path.dirname(HERE), "tmp", "dense"); nd = len(days); pos = {d: i for i, d in enumerate(days)}
    low = np.zeros((nd, 1440)); clo = np.zeros((nd, 1440))
    for per, lo, hi in (("IS", 0, 20240101), ("C24", 20240101, 20240216), ("REAL", 20240216, 30000000)):
        z = np.load(os.path.join(DN, per + ".npz")); zd = z["days"]
        for m in GOLD[prof]:
            L = z[f"G:{m}|L"]; R = z[f"G:{m}|R"]
            for k, d in enumerate(zd):
                if lo <= d < hi and d in pos: low[pos[d]] += L[k]; clo[pos[d]] += R[k]
    return low, clo, clo[:, -1]


def paths(T, days, gold=None):
    S = T["mod"].isin(["MOM1030", "CPI09"]); P = {}
    g = gold_paths(days, gold) if gold else None
    for cap in (0, 300):
        R0 = T[~S]; S1 = T[S].assign(w=1.0)
        if cap: R0 = R0[R0.risk <= cap]; S1 = S1[S1.risk / S1.w.clip(lower=1) <= cap]
        a = full_paths(R0, days)
        if g is not None: a = (a[0] + g[0], a[1] + g[1], a[2] + g[2])
        P[cap] = (a, full_paths(S1, days), R0.w.groupby(R0.date).sum().reindex(days, fill_value=0).to_numpy(),
                  S1.w.groupby(S1.date).sum().reindex(days, fill_value=0).to_numpy())
    return P


def seat_runs(P, h, idx, step=5):
    """per seat type: out rows (one per start every `step` positions of idx) -> net cash of a 12-month seat"""
    n = len(idx)
    def vecm(cap, m, G, k=1.0):
        a, b, ca, cb = P[cap]; cc = ca + m * cb
        return vectors(k * (a[0] + m * b[0] - cc[:, None] - h[:, None]), k * (a[1] + m * b[1] - cc[:, None] - h[:, None]), k * (a[2] + m * b[2] - cc - h), G)
    R = {}
    # MFFU 1c
    ev = vecm(0, 8, 800.0); EL = np.ascontiguousarray(np.array([ev[0], ev[0]])); EC = np.ascontiguousarray(np.array([ev[1], ev[1]]))
    full = vecm(0, 4, 0.0); low = vecm(300, 4, 0.0); dbl = vecm(0, 4, 0.0, 2.0)
    FL = np.ascontiguousarray(np.array([low[0], full[0], full[0]])); FC = np.ascontiguousarray(np.array([low[1], full[1], full[1]]))
    out = np.zeros((n, 9)); k = life_m(EL, EC, -1e9, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0, 1e9, 4100.0, 0, idx, H, step, out); R["MFFU"] = out[:k].copy()
    FL = np.ascontiguousarray(np.array([low[0], full[0], dbl[0]])); FC = np.ascontiguousarray(np.array([low[1], full[1], dbl[1]]))
    out = np.zeros((n, 9)); k = life_m(EL, EC, -1e9, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0, 4000.0, 6100.0, 0, idx, H, step, out); R["MFFUs"] = out[:k].copy()
    # Lucid Flex 50K, k contracts: eval k x (normal + x8 lots total -> at k=2 the x8 rule gives 8 lots = 2 x 4)
    for key, kc in (("LF1", 1.0), ("LF2", 2.0)):
        me = 8.0 / kc
        ev = vecm(0, me, 1350.0, kc); EL = np.ascontiguousarray(np.array([ev[0], ev[0]])); EC = np.ascontiguousarray(np.array([ev[1], ev[1]]))
        full = vecm(0, 4, 0.0, kc); low = vecm(300, 4, 0.0, kc)
        FL = np.ascontiguousarray(np.array([low[0], full[0], full[0]])); FC = np.ascontiguousarray(np.array([low[1], full[1], full[1]]))
        out = np.zeros((n, 9)); k = A.life(EL, EC, -1e9, 3000.0, 2000.0, 0.5, np.ones(len(h), np.bool_), 146.0, FL, FC, 1000.0, 1000.0, 0, 4000.0, 150.0, 2000.0, 2000.0, idx, H, step, out)
        R[key] = out[:k].copy()
    return R


def plan_totals(R, plan, nrows):
    """row r = year starting at position 5r; seat j of the plan starts at 5(r+j)"""
    tot = np.zeros(nrows); j = 0
    for key, cnt in plan:
        for _ in range(cnt):
            tot += R[key][j:j + nrows, 0]; j += 1
    return tot


def summ(x):
    d = x / 365.0
    return dict(mean_month=round(float(x.mean() / 12)), median_month=round(float(np.median(x) / 12)), p10_month=round(float(np.percentile(x, 10) / 12)), p90_month=round(float(np.percentile(x, 90) / 12)),
                mean_day=round(float(d.mean())), median_day=round(float(np.median(d))), p10_day=round(float(np.percentile(d, 10))),
                P_neg_year=round(100 * float((x < 0).mean()), 1), P_ge_250_day=round(100 * float((d >= 250).mean()), 1), P_ge_300_day=round(100 * float((d >= 300).mean()), 1), n=int(len(x)))


if __name__ == "__main__":
    E = RB.setup(); D = getD(RB.NAME)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]; n = len(days); idx = np.arange(n, dtype=np.int64)
    T = build(E, D); T = T[T.date.isin(days)]
    from wrq_port import conflict_filter
    sets = {"Ultra": conflict_filter(T.sort_values(["date", "tin"]).reset_index(drop=True))}
    if "--six" in sys.argv:
        from six_life import new_trades
        NW = new_trades(D, json.load(open(os.path.join(HERE, "six_final_set.json")))); NW = NW[NW.date.isin(days)]
        NW = NW.assign(tin=D.sm[NW.fi.to_numpy().astype(int)], tout=D.sm[NW.xi.to_numpy().astype(int)] + 1)
        sets["Ultra+six"] = conflict_filter(pd.concat([T, NW], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
    gold = "Robust" if "--gold" in sys.argv else None
    d24 = int(np.searchsorted(days, 20240101)); rng = np.random.default_rng(17); OUT = {}
    for nm, X in sets.items():
        if gold: nm = nm + "+gold"
        P = paths(X, days, gold); fin = P[0][0][2] + 4 * P[0][1][2]; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())
        print(nm, "mean $/trading day per contract T1/T2", round(mu1, 1), round(mu2, 1), flush=True)
        for hc in (0.0, 0.35, 0.5, 1.0):
            h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
            R = seat_runs(P, h, idx); st = np.arange(len(R["MFFU"])) * 5
            res = {}
            for per, ok in (("T1", (st + H + 5 * NSEAT) < d24), ("T2", (st >= d24) & (st + H + 5 * NSEAT <= n))):
                rows = np.nonzero(ok)[0]
                for pl, spec in PLANS.items():
                    tot = plan_totals(R, spec, len(R["MFFU"]) - NSEAT)[rows]
                    res.setdefault(pl, {})[per + "_hist"] = summ(tot)
            # block bootstrap years per period
            for per, lo, hi in (("T1", 0, d24), ("T2", d24, n)):
                L = H + 5 * NSEAT + 1; nblk = L // 10 + 2; boots = {pl: [] for pl in PLANS}
                for b in range(NB):
                    bi = np.concatenate([np.arange(s, s + 10) for s in rng.integers(lo, hi - 10, nblk)])[:L].astype(np.int64)
                    Rb = seat_runs(P, h, bi)
                    for pl, spec in PLANS.items(): boots[pl].append(plan_totals(Rb, spec, 1)[0])
                for pl in PLANS: res[pl][per + "_boot"] = summ(np.array(boots[pl]))
            OUT[f"{nm} | edge-{int(hc*100)}%"] = res
            for pl in PLANS:
                r = res[pl]; print(f"  {nm:9s} edge-{int(hc*100):3d}% {pl:28s} hist T1/T2 $/day {r['T1_hist']['mean_day']:5d}/{r['T2_hist']['mean_day']:5d}  boot T1/T2 median $/day {r['T1_boot']['median_day']:5d}/{r['T2_boot']['median_day']:5d}  p10 {r['T1_boot']['p10_day']:5d}/{r['T2_boot']['p10_day']:5d}  P(>=250) {r['T1_boot']['P_ge_250_day']:4.0f}/{r['T2_boot']['P_ge_250_day']:4.0f}  P(neg yr) {r['T1_boot']['P_neg_year']:4.1f}/{r['T2_boot']['P_neg_year']:4.1f}", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "seats_plan%s.json" % ("_gold" if gold else "")), "w"), indent=1)
