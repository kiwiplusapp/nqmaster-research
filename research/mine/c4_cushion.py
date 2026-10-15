"""2026-10-16 C4: funded-account cushion policy for MFFU Rapid EOD 50K at 1 base contract, current defaults (Ultra + CPI09, MOM1030 /
CPI09 x4 funded, eval x8 + profit stop 800). Pre-registered grid (48 policies):
  c1 = FundedRiskCapCushion (risk cap $300 per base contract below it) in {0, 1000, 2000, 3000}
  c2 = FundedStepUpCushion (2 contracts at/above it) in {off, 3000, 4000, 5000} with c2 > c1
  B  = profit kept after a payout (payout requested at B + 500) in {4100, 5100, 6100}
Metrics: 12-month lifecycle per seat ($/month net of eval fees, accounts lost per year) on starts in each calendar year 2020-2025
(6 blocks: chosen on 2020-23, checked on 2024-25), with full edge and 35% less edge; summer-2026 stress = P(funded account lost within
60 trading days) for a fresh funded account started on every day 2026-06-01..2026-08-31; plateau check on the neighbours.
Accept a change vs today (c1 2000, c2 off, B 4100) only if $/month >= today in >= 5 of 6 year-blocks at both edge levels, accounts lost
per year not higher in the 2024-25 blocks, and summer-2026 loss not higher. -> c4_cushion.json"""
import os, sys, json, itertools, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import pickle
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from wrq_lib import getD
from mffu_rapid import life_m, fu_m
from sniper_life import build
H = 252

if __name__ == "__main__":
    E = RB.setup(); D = getD(RB.NAME)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]; n = len(days); idx = np.arange(n, dtype=np.int64)
    T = build(E, D); T = T[T.date.isin(days)]; S = T["mod"].isin(["MOM1030", "CPI09"])
    P = {}
    for cap in (0, 300):
        R0 = T[~S]; S1 = T[S].assign(w=1.0)
        if cap: R0 = R0[R0.risk <= cap]
        P[cap] = (full_paths(R0, days), full_paths(S1, days), R0.w.groupby(R0.date).sum().reindex(days, fill_value=0).to_numpy(),
                  S1.w.groupby(S1.date).sum().reindex(days, fill_value=0).to_numpy())
    d24 = int(np.searchsorted(days, 20240101)); fin = P[0][0][2] + 4 * P[0][1][2]; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())

    def vecm(cap, m, G, h, k=1.0):
        a, b, ca, cb = P[cap]; cc = k * (ca + m * cb)
        lo, cl = vectors(k * (a[0] + m * b[0]) - cc[:, None] - k * h[:, None], k * (a[1] + m * b[1]) - cc[:, None] - k * h[:, None], k * (a[2] + m * b[2]) - cc - k * h, G)   # haircut scales with size (red team)
        return lo, cl
    years = days // 10000
    OUT = {"policies": []}
    s_summer = np.nonzero((days >= 20260601) & (days <= 20260831))[0]
    for hc in (0.0, 0.35):
        h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
        ev = vecm(0, 8, 800.0, h); EL = np.ascontiguousarray(np.array([ev[0], ev[0]])); EC = np.ascontiguousarray(np.array([ev[1], ev[1]]))
        full = vecm(0, 4, 0.0, h); low = vecm(300, 4, 0.0, h); dbl = vecm(0, 4, 0.0, h, 2.0)
        FL = np.ascontiguousarray(np.array([low[0], full[0], dbl[0]])); FC = np.ascontiguousarray(np.array([low[1], full[1], dbl[1]]))
        for c1, c2, B in itertools.product((0, 1000, 2000, 3000), (1e9, 3000, 4000, 5000), (4100, 5100, 6100)):
            if c2 <= c1: continue
            out = np.zeros((n, 9)); k = life_m(EL, EC, -1e9, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, float(c1), float(c2), float(B), 0, idx, H, 5, out)
            o = out[:k]; st = np.arange(k) * 5; yb = years[st]
            rec = dict(edge=f"-{int(hc*100)}%", c1=c1, c2=("off" if c2 > 1e8 else int(c2)), B=B)
            for y in range(2020, 2026):
                x = o[yb == y]
                if len(x): rec[f"{y}_usd_mo"] = round(float(x[:, 0].mean() / 12)); rec[f"{y}_lost"] = round(float((x[:, 1] - x[:, 2] + x[:, 3]).mean()), 2)
            lost60 = []
            for s0 in s_summer:
                cash, mm, status, last = fu_m(FL, FC, float(c1), float(c2), idx, int(s0), int(min(n, s0 + 60)), float(B), 2000.0, 0)
                lost60.append(status == -1)
            rec["summer26_funded_lost_60d"] = round(100 * float(np.mean(lost60)), 1) if lost60 else None
            OUT["policies"].append(rec)
        print("edge", hc, "done", flush=True)
    R = pd.DataFrame(OUT["policies"]); R.to_csv(os.path.join(HERE, "c4_cushion.csv"), index=False)
    today = R[(R.c1 == 2000) & (R.c2 == "off") & (R.B == 4100)].set_index("edge")
    verdict = []
    yrs = [f"{y}_usd_mo" for y in range(2020, 2026)]
    for (c1, c2, B), g in R.groupby(["c1", "c2", "B"]):
        g = g.set_index("edge"); ok = True; wins = {}
        for e in ("-0%", "-35%"):
            w = int(sum(g.loc[e, c] >= today.loc[e, c] for c in yrs)); wins[e] = w
            ok &= w >= 5
            ok &= all(g.loc[e, f"{y}_lost"] <= today.loc[e, f"{y}_lost"] for y in (2024, 2025))
            ok &= g.loc[e, "summer26_funded_lost_60d"] <= today.loc[e, "summer26_funded_lost_60d"]
        verdict.append(dict(c1=c1, c2=c2, B=B, blocks_won_full=wins["-0%"], blocks_won_h35=wins["-35%"], accepted=bool(ok),
                            usd_mo_mean_full=round(float(g.loc["-0%", yrs].mean())), usd_mo_mean_h35=round(float(g.loc["-35%", yrs].mean())),
                            lost_2024_25_full=round(float(g.loc["-0%", ["2024_lost", "2025_lost"]].mean()), 2), summer_lost=g.loc["-0%", "summer26_funded_lost_60d"]))
    V = pd.DataFrame(verdict).sort_values("usd_mo_mean_h35", ascending=False); OUT["verdict"] = V.to_dict("records")
    OUT["today"] = today.reset_index().to_dict("records")
    print(V.head(20).to_string(index=False)); print("accepted:", V[V.accepted].to_string(index=False))
    json.dump(OUT, open(os.path.join(HERE, "c4_cushion.json"), "w"), indent=1, default=str)
