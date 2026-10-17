"""2026-10-17 Federico: '$200 per day PER ACCOUNT, robust'. Size ladder inside a funded account: contracts grow with the day-start cushion
(cushion = balance - trailing floor), the account withdraws only the excess above the cushion the ladder needs, so income per account
scales with retained profit and stops growing by itself if the edge fades. Seats on the same real NQ minute paths as seats_plan.py
(Ultra + six-year modules + gold Robust, or Ultra + gold), eval as today (MFFU 1c x8 + $800 stop; Lucid 150K 6c + $4,050 stop).
Funded ladders: MFFU Rapid EOD 50K: k = 1 + floor(cushion / S) capped at K (gear 0 = 1c with the $300 risk cap below a $2,000 cushion),
withdraw bal - B whenever >= $500 (B = retained balance; MFFU buffer 2,100 applies), 90% split, 30-micro cap -> K <= 4.
Lucid Flex 150K: k = 3 + floor(max(0, cushion - c0) / S) capped at K (5 -> 40-micro cap), payouts as Flex (5 days >= $250, min(3,000, 50%, bal - B)),
5 payouts then a new eval. Edge full / -35% / -50%; history (starts every 5 days) + 400 block-bootstrap years per period. -> ladder_plan.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from robust2_life import vectors, SP
from mffu_rapid import ev_m
from acct1c_lib import ev1
H = 252; NB = 400
CACHE = os.path.join(os.path.dirname(SP), "scratchpad", "ladder_paths.pkl")


@njit(cache=True)
def fu_ladder_m(FL, FC, cLow, S, K, B, idx, start, n, D, out_days):
    """MFFU funded with a size ladder. FL/FC[g, day]: g=0 1c capped, g=k k contracts full. Returns (cash, payouts, status, last pos)."""
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; d = start
    while d < n:
        t = idx[d]
        thr = 100.0 if pk >= D + 100.0 else pk - D
        cu = bal - thr
        k = 1 + int(cu / S)
        if k > K: k = K
        g = 0 if (k == 1 and cu < cLow) else k
        if bal + FL[g, t] <= thr: return cash, m, -1, d
        bal += FC[g, t]; out_days[g] += 1
        if bal > pk: pk = bal
        if bal - B >= 500.0:
            amt = bal - B; bal -= amt; cash += 0.9 * amt; m += 1
        d += 1
    return cash, m, 0, n


@njit(cache=True)
def fu_ladder_flex(FL, FC, k0, c0, S, K, B, idx, start, n, D, Q, cap, out_days):
    """Lucid Flex 150K funded with a ladder from k0 contracts; payouts need 5 days >= Q, amount min(cap, 50% bal, bal - B) >= 500, 5 payouts max."""
    bal = 0.0; pk = 0.0; locked = False; cash = 0.0; m = 0; qd = 0; cyc0 = 0.0; d = start
    while d < n:
        t = idx[d]
        thr = 100.0 if (locked or pk >= D + 100.0) else pk - D
        cu = bal - thr
        k = k0 + int(max(0.0, cu - c0) / S)
        if k > K: k = K
        if bal + FL[k, t] <= thr: return cash, m, -1, d
        c = FC[k, t]; bal += c; out_days[k] += 1
        if bal > pk: pk = bal
        if c >= Q: qd += 1
        if qd >= 5 and bal - cyc0 > 0 and bal - B >= 500.0:
            amt = min(cap, min(0.5 * bal, bal - B))
            if amt >= 500.0:
                bal -= amt; cash += 0.9 * amt; m += 1; qd = 0; cyc0 = bal; locked = True
                if m == 5: return cash, m, 1, d
        d += 1
    return cash, m, 0, n


@njit(cache=True)
def life_ladder(firm, EL, EC, T, D, cons, mind, fee, FL, FC, cLow, k0, c0, S, K, B, Q, cap, idx, H, step, out, days_at):
    N = len(idx); r = 0
    for s in range(0, N - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0; fdays = 0.0
        while i < end:
            fees += fee; nev += 1
            if firm == 0: res, j = ev_m(EL, EC, -1e9, T, D, cons, mind, idx, i, end)
            else: res, j = ev1(EL, EC, -1e9, T, D, cons, idx, i, end)
            if res != 1:
                i = j + 1; continue
            npass += 1
            if firm == 0: c, m, st, j2 = fu_ladder_m(FL, FC, cLow, S, K, B, idx, j + 1, end, D, days_at[r])
            else: c, m, st, j2 = fu_ladder_flex(FL, FC, k0, c0, S, K, B, idx, j + 1, end, D, Q, cap, days_at[r])
            fdays += min(j2, end - 1) - j; cash += c; npay += m; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb; out[r, 4] = npay; out[r, 6] = fdays; out[r, 7] = cash; r += 1
    return r


def build_sets():
    if os.path.exists(CACHE): return pickle.load(open(CACHE, "rb"))
    import robust2_build as RB
    from wrq_lib import getD
    from sniper_life import build
    from wrq_port import conflict_filter
    from six_life import new_trades
    from seats_plan import paths
    E = RB.setup(); D = getD(RB.NAME)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]
    T = build(E, D); T = T[T.date.isin(days)]
    NW = new_trades(D, json.load(open(os.path.join(HERE, "six_final_set.json")))); NW = NW[NW.date.isin(days)]
    NW = NW.assign(tin=D.sm[NW.fi.to_numpy().astype(int)], tout=D.sm[NW.xi.to_numpy().astype(int)] + 1)
    sets = {"Ultra+gold": paths(conflict_filter(T.sort_values(["date", "tin"]).reset_index(drop=True)), days, "Robust"),
            "Ultra+six+gold": paths(conflict_filter(pd.concat([T, NW], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)), days, "Robust")}
    pickle.dump((days, sets), open(CACHE, "wb")); return days, sets


def gears(P, h, K, G_ev, me, ke):
    def vecm(cap, m, G, k=1.0):
        a, b, ca, cb = P[cap]; cc = ca + m * cb
        return vectors(k * (a[0] + m * b[0] - cc[:, None] - h[:, None]), k * (a[1] + m * b[1] - cc[:, None] - h[:, None]), k * (a[2] + m * b[2] - cc - h), G)
    ev = vecm(0, me, G_ev, ke); EL = np.ascontiguousarray(np.array([ev[0], ev[0]])); EC = np.ascontiguousarray(np.array([ev[1], ev[1]]))
    low = vecm(300, 4, 0.0); full = vecm(0, 4, 0.0)
    FL = np.ascontiguousarray(np.array([low[0]] + [k * full[0] for k in range(1, K + 1)])); FC = np.ascontiguousarray(np.array([low[1]] + [k * full[1] for k in range(1, K + 1)]))
    return EL, EC, FL, FC


def summ(x, nb, size):
    d = x / 365.0
    return dict(mean_day=round(float(d.mean())), median_day=round(float(np.median(d))), p10_day=round(float(np.percentile(d, 10))), p90_day=round(float(np.percentile(d, 90))),
                P_neg_year=round(100 * float((x < 0).mean()), 1), P_ge_200_day=round(100 * float((d >= 200).mean()), 1), busts_per_year=round(float(nb.mean()), 2), mean_size=round(float(size.mean()), 2), n=int(len(x)))


POL = {"MFFU 1c (today)": dict(firm=0, K=1, S=1e9, B=4100.0), "MFFU step-up 2c @4k (keep 6.1k)": dict(firm=0, K=2, S=4000.0, B=6100.0)}
for K in (3, 4):
    for S in (2000.0, 3000.0, 4000.0):
        for extra in (0.0, 2000.0):
            POL[f"MFFU ladder K{K} S{int(S/1000)}k B{int(((K-1)*S+100+extra)/1000)}k"] = dict(firm=0, K=K, S=S, B=(K - 1) * S + 100.0 + extra)
POL["Lucid150K 3c (today)"] = dict(firm=1, K=3, k0=3, c0=0.0, S=1e9, B=6000.0)
for K in (4, 5):
    for S in (3000.0, 4500.0):
        POL[f"Lucid150K ladder 3->{K}c S{S/1000:g}k"] = dict(firm=1, K=K, k0=3, c0=1687.5, S=S, B=1687.5 + (K - 3) * S + 100.0 + 2000.0)

if __name__ == "__main__":
    days, sets = build_sets(); n = len(days); idx = np.arange(n, dtype=np.int64); d24 = int(np.searchsorted(days, 20240101)); rng = np.random.default_rng(23)
    OUT = {}
    for nm, P in sets.items():
        fin = P[0][0][2] + 4 * P[0][1][2]; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())
        for hc in (0.0, 0.35, 0.5):
            h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
            GM = gears(P, h, 4, 800.0, 8, 1.0); GL = gears(P, h, 5, 4050.0, 4, 6.0)
            for pol, c in POL.items():
                EL, EC, FL, FC = GM if c["firm"] == 0 else GL
                def run(ix):
                    out = np.zeros((len(ix), 9)); da = np.zeros((len(ix), 6))
                    if c["firm"] == 0: k = life_ladder(0, EL, EC, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0, 1, 0.0, c["S"], c["K"], c["B"], 0.0, 0.0, ix, H, 5, out, da)
                    else: k = life_ladder(1, EL, EC, 9000.0, 4500.0, 0.5, 4, 285.0, FL, FC, 0.0, c["k0"], c["c0"], c["S"], c["K"], c["B"], 250.0, 3000.0, ix, H, 5, out, da)
                    o = out[:k]; da = da[:k]; sz = (da * np.arange(6)[None, :]).sum(1) / np.maximum(1, da.sum(1)); sz = np.where(da.sum(1) > 0, sz, np.nan)
                    return o, sz
                o, sz = run(idx); st = np.arange(len(o)) * 5; rec = {}
                for per, ok in (("T1", (st + H) < d24), ("T2", st >= d24)):
                    rec[per + "_hist"] = summ(o[ok, 0], o[ok, 3], np.nan_to_num(sz[ok], nan=1.0))
                for per, lo, hi in (("T1", 0, d24), ("T2", d24, n)):
                    xs = []; bs = []; ss = []
                    for b in range(NB):
                        bi = np.concatenate([np.arange(s, s + 10) for s in rng.integers(lo, hi - 10, H // 10 + 2)])[:H + 1].astype(np.int64)
                        ob, sb = run(bi); xs.append(ob[0, 0]); bs.append(ob[0, 3]); ss.append(np.nan_to_num(sb[0], nan=1.0))
                    rec[per + "_boot"] = summ(np.array(xs), np.array(bs), np.array(ss))
                OUT[f"{nm} | edge-{int(hc*100)}% | {pol}"] = rec
                print(f"{nm:15s} -{int(hc*100):2d}% {pol:36s} hist $/day {rec['T1_hist']['mean_day']:4d}/{rec['T2_hist']['mean_day']:4d}  boot med {rec['T1_boot']['median_day']:4d}/{rec['T2_boot']['median_day']:4d} p10 {rec['T1_boot']['p10_day']:4d}/{rec['T2_boot']['p10_day']:4d}  P(>=200) {rec['T1_boot']['P_ge_200_day']:3.0f}/{rec['T2_boot']['P_ge_200_day']:3.0f}  P(neg) {rec['T1_boot']['P_neg_year']:4.1f}/{rec['T2_boot']['P_neg_year']:4.1f}  busts/yr {rec['T1_boot']['busts_per_year']:.2f}/{rec['T2_boot']['busts_per_year']:.2f}  size {rec['T2_boot']['mean_size']:.2f}", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "ladder_plan.json"), "w"), indent=1)
