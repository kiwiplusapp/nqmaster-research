"""2026-10-19 Federico: 'do you recommend many Lucid 25K accounts?' + the 2027 setup. Minute paths of the recommended 2027 set
(Ultra as coded + the 4 durable six-year modules SO04 / RV11 / ORFAIL / CAM3 + GoldMaster Robust; six_oos.py), real NQ 2020-02..2026-10.
Seats (12-month lifecycles, new eval the day after a bust, 5 payouts then a new eval where the firm caps payouts):
  Lucid Flex 25K 1c  : target 1,250, EOD trailing 1,000, 50% consistency (eval profit stop 560), fee 89; funded 1c, risk cap 150 below a 500
                       cushion, payout days >= $100, cap 1,000, request at 1,500.
  LucidPro 25K 2c/1c : eval 2c no consistency, fee 123; funded 1c, buffer 1,100, caps 1,000 then 1,500, 40% consistency per cycle.
  Lucid Flex 50K 2c  : eval 2c (x8 lots), stop 1,350, fee 146; funded 2c, cap 300 below 1,000, payout at 4,000, cap 2,000, days >= $150.
  Lucid Flex 150K    : eval 6c, stop 4,050, fee 285; funded 3c, cap 300 below 1,687, payout at 6,000, cap 3,000, days >= $250.
  MFFU 50K 1c        : today's preset (eval x8 + stop 800; funded cap 300 below 2,000, keep 4,100), fee 157.
  MFFU ladder        : 1c -> 2c at 3,000 cushion, +1 per 3,000 up to 4c, keep 11,100; account daily stop 1,500 per contract.
Plans: 5 x each Lucid seat (Lucid allows 5 funded per household), 3 MFFU (MFFU allows 3), combos. Same market path for every seat
(correlated), starts 5 days apart. Edge full / -35% / -50%; 300 block-bootstrap years per period (21-day blocks), T1 2020-23 / T2 2024-26.
-> acct_2027.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from robust2_life import vectors, SP, full_paths
from mffu_rapid import life_m
import acct1c_lib as A
from ladder_plan import life_ladder
from ladder_stop import gears_stop
H = 252; NB = 300; NS = 8
CACHE = os.path.join(SP, "acct2027_paths.pkl")
DURABLE = [{"fam": "CLOCK_ANCHOR", "j": 1527}, {"fam": "RVOL_DRIVE", "j": 4226}, {"fam": "OR_FAIL", "j": 142}, {"fam": "PIVOT_FADE", "j": 365}]


def build():
    if os.path.exists(CACHE): return pickle.load(open(CACHE, "rb"))
    import robust2_build as RB
    from wrq_lib import getD
    from sniper_life import build as sbuild
    from wrq_port import conflict_filter
    from six_life import new_trades
    from seats_plan import gold_paths
    E = RB.setup(); D = getD(RB.NAME)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]
    T = sbuild(E, D); T = T[T.date.isin(days)]
    NW = new_trades(D, DURABLE); NW = NW[NW.date.isin(days)]
    NW = NW.assign(tin=D.sm[NW.fi.to_numpy().astype(int)], tout=D.sm[NW.xi.to_numpy().astype(int)] + 1)
    X = conflict_filter(pd.concat([T, NW], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
    g = gold_paths(days, "Robust"); S = X["mod"].isin(["MOM1030", "CPI09"]); P = {}
    for cap in (0, 150, 300):
        R0 = X[~S]; S1 = X[S].assign(w=1.0)
        if cap: R0 = R0[R0.risk <= cap]; S1 = S1[S1.risk / S1.w.clip(lower=1) <= cap]
        a = full_paths(R0, days); a = (a[0] + g[0], a[1] + g[1], a[2] + g[2])
        P[cap] = (a, full_paths(S1, days), R0.w.groupby(R0.date).sum().reindex(days, fill_value=0).to_numpy(), S1.w.groupby(S1.date).sum().reindex(days, fill_value=0).to_numpy())
    pickle.dump((days, P), open(CACHE, "wb")); return days, P


def seat_runs(P, h, idx):
    n = len(idx)
    def vecm(cap, m, G, k=1.0, hs=1.0):
        a, b, ca, cb = P[cap]; cc = ca + m * cb
        hh = hs * h
        return vectors(k * (a[0] + m * b[0] - cc[:, None] - hh[:, None]), k * (a[1] + m * b[1] - cc[:, None] - hh[:, None]), k * (a[2] + m * b[2] - cc - hh), G)
    two = lambda v: (np.ascontiguousarray(np.array([v[0], v[0]])), np.ascontiguousarray(np.array([v[1], v[1]])))
    R = {}; one = np.ones(len(h), np.bool_)
    def lifeA(name, ev, low, full, c1, firm, X, Q, cap1, cap2, T, D, cons, fee):
        EL, EC = two(ev); FL = np.ascontiguousarray(np.array([low[0], full[0], full[0]])); FC = np.ascontiguousarray(np.array([low[1], full[1], full[1]]))
        out = np.zeros((n, 9)); k = A.life(EL, EC, -1e9, T, D, cons, one, fee, FL, FC, c1, c1, firm, X, Q, cap1, cap2, idx, H, 5, out); R[name] = out[:k].copy()
    # eval haircut scaled to the eval mix (red team M3): a + m b carries (1 + m) / (1 + 4) of the funded haircut per lot unit, approx 1.12 at m = 8
    lifeA("LF25", vecm(0, 4, 560.0, 1.0), vecm(150, 4, 0.0), vecm(0, 4, 0.0), 500.0, 0, 1500.0, 100.0, 1000.0, 1000.0, 1250.0, 1000.0, 0.5, 89.0)
    lifeA("LP25", vecm(0, 4, 0.0, 2.0), vecm(150, 4, 0.0), vecm(0, 4, 0.0), 500.0, 1, 1000.0, 100.0, 1000.0, 1500.0, 1250.0, 1000.0, 0.0, 123.0)
    lifeA("LF50", vecm(0, 4, 1350.0, 2.0, 1.12), vecm(300, 4, 0.0, 2.0), vecm(0, 4, 0.0, 2.0), 1000.0, 0, 4000.0, 150.0, 2000.0, 2000.0, 3000.0, 2000.0, 0.5, 146.0)
    lifeA("L150", vecm(0, 4, 4050.0, 6.0), vecm(300, 4, 0.0, 3.0), vecm(0, 4, 0.0, 3.0), 1687.5, 0, 6000.0, 250.0, 3000.0, 3000.0, 9000.0, 4500.0, 0.5, 285.0)
    ev = vecm(0, 8, 800.0, 1.0, 1.12); EL, EC = two(ev); low = vecm(300, 4, 0.0); full = vecm(0, 4, 0.0)
    FL = np.ascontiguousarray(np.array([low[0], full[0], full[0]])); FC = np.ascontiguousarray(np.array([low[1], full[1], full[1]]))
    out = np.zeros((n, 9)); k = life_m(EL, EC, -1e9, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0, 1e9, 4100.0, 0, idx, H, 5, out); R["MF1"] = out[:k].copy()
    FL, FC = gears_stop(P_view(P), h, 4, 1500.0)
    out = np.zeros((n, 9)); da = np.zeros((n, 6))
    k = life_ladder(0, EL, EC, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0, 1, 0.0, 3000.0, 4, 11100.0, 0.0, 0.0, idx, H, 5, out, da); R["MFL"] = out[:k].copy()
    return R


def P_view(P): return {0: P[0], 300: P[300]}


PLANS = {"5 x Lucid Flex 25K": [("LF25", 5)], "5 x LucidPro 25K": [("LP25", 5)], "5 x Lucid Flex 50K 2c": [("LF50", 5)], "5 x Lucid 150K": [("L150", 5)],
         "3 x MFFU 1c": [("MF1", 3)], "3 x MFFU ladder": [("MFL", 3)], "3 MFFU ladder + 5 Lucid 25K": [("MFL", 3), ("LF25", 5)],
         "3 MFFU ladder + 5 Lucid 150K": [("MFL", 3), ("L150", 5)]}
SEATS = ["LF25", "LP25", "LF50", "L150", "MF1", "MFL"]


def summ(x, nb):
    d = x / 365.0
    return dict(median_day=round(float(np.median(d))), p10_day=round(float(np.percentile(d, 10))), mean_day=round(float(d.mean())),
                P_neg_year=round(100 * float((x < 0).mean()), 1), P_ge_200_day=round(100 * float((d >= 200).mean()), 1), P_ge_300_day=round(100 * float((d >= 300).mean()), 1),
                accounts_lost_per_year=round(float(nb.mean()), 2) if nb is not None else None)


if __name__ == "__main__":
    days, P = build(); n = len(days); d24 = int(np.searchsorted(days, 20240101)); rng = np.random.default_rng(57)
    fin = P[0][0][2] + 4 * P[0][1][2]; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())
    print("mean $/trading day per contract (full mix) T1/T2", round(mu1, 1), round(mu2, 1), flush=True)
    OUT = {}
    for hc in (0.0, 0.35, 0.5):
        h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2); res = {}
        for per, lo, hi in (("T1", 0, d24), ("T2", d24, n)):
            seat = {s: [] for s in SEATS}; lost = {s: [] for s in SEATS}; plans = {p: [] for p in PLANS}
            L = H + 5 * NS + 1
            for b in range(NB):
                bi = np.concatenate([np.arange(s, s + 21) for s in rng.integers(lo, hi - 21, L // 21 + 2)])[:L].astype(np.int64)
                Rb = seat_runs(P, h, bi)
                for s in SEATS: seat[s].append(Rb[s][0, 0]); lost[s].append(Rb[s][0, 1] - Rb[s][0, 2] + Rb[s][0, 3])
                for pl, spec in PLANS.items():
                    tot = 0.0; j = 0
                    for key, cnt in spec:
                        for _ in range(cnt): tot += Rb[key][j, 0]; j += 1
                    plans[pl].append(tot)
            res[per] = {"seats": {s: summ(np.array(seat[s]), np.array(lost[s])) for s in SEATS}, "plans": {p: summ(np.array(v), None) for p, v in plans.items()}}
        OUT[f"edge-{int(hc*100)}%"] = res
        print(f"== edge -{int(hc*100)}%", flush=True)
        for s in SEATS: print(f"  seat {s:5s} median $/day T1/T2 {res['T1']['seats'][s]['median_day']:4d}/{res['T2']['seats'][s]['median_day']:4d}  p10 {res['T1']['seats'][s]['p10_day']:4d}/{res['T2']['seats'][s]['p10_day']:4d}  P(neg) {res['T1']['seats'][s]['P_neg_year']:4.1f}/{res['T2']['seats'][s]['P_neg_year']:4.1f}  lost/yr {res['T1']['seats'][s]['accounts_lost_per_year']:.2f}/{res['T2']['seats'][s]['accounts_lost_per_year']:.2f}", flush=True)
        for p in PLANS: print(f"  plan {p:30s} median $/day T1/T2 {res['T1']['plans'][p]['median_day']:4d}/{res['T2']['plans'][p]['median_day']:4d}  p10 {res['T1']['plans'][p]['p10_day']:4d}/{res['T2']['plans'][p]['p10_day']:4d}  P(>=300) {res['T1']['plans'][p]['P_ge_300_day']:3.0f}/{res['T2']['plans'][p]['P_ge_300_day']:3.0f}  P(neg) {res['T1']['plans'][p]['P_neg_year']:4.1f}/{res['T2']['plans'][p]['P_neg_year']:4.1f}", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "acct_2027.json"), "w"), indent=1)
