"""2026-10-17 'que siga funcionando en el futuro': what the size ladder does when the edge DIES during the window. Edge haircut ramps
linearly from 0% at the start of each 3-year window to 100% (no edge) at its end (and a faster ramp to 100% within 18 months, then zero
edge), applied per position in the window to both the eval and the funded gears. MFFU 50K, Ultra + six-year modules + gold Robust, policies
1c / ladder K4 S3k B11.1k / ladder + $1,500 per-contract daily stop. 300 block-bootstrap 3-year paths per period. Reports income by year
(1, 2, 3), busts, and whether the retained ladder cushion is given back. -> ladder_decay.json"""
import os, sys, json, pickle, numpy as np
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from ladder_plan import CACHE, gears
from ladder_stop import gears_stop
from mffu_rapid import ev_m
H3 = 756; NB = 300


@njit(cache=True)
def ev_d(EL, EC, hp, T, D, cons, mind, idx, s, n):
    eq = 0.0; pk = 0.0; best = -1e9; d = s
    while d < n:
        t = idx[d]
        thr = 100.0 if pk >= D + 100.0 else pk - D
        if eq + EL[0, t] - 8.0 * hp[d] <= thr: return -1, d
        c = EC[0, t] - 8.0 * hp[d]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= T and d - s + 1 >= mind and (cons <= 0.0 or best <= cons * eq): return 1, d
        d += 1
    return 0, n


@njit(cache=True)
def life3d(EL, EC, hp, T, D, cons, mind, fee, FL, FC, cLow, S, K, B, idx, H, step, out):
    """out: 0/1/2 net cash year 1/2/3, 3 busts, 4 retained balance at the end (0 if busted / in eval), 5 busts in year 3"""
    N = len(idx); r = 0
    for s in range(0, N - H, step):
        end = s + H; i = s; cash = np.zeros(3); nb = 0; nb3 = 0; bal_end = 0.0
        while i < end:
            cash[min(2, (i - s) // 252)] -= fee
            res, j = ev_d(EL, EC, hp, T, D, cons, mind, idx, i, end)
            if res != 1:
                i = j + 1; continue
            bal = 0.0; pk = 0.0; d = j + 1; st = 0
            while d < end:
                t = idx[d]
                thr = 100.0 if pk >= D + 100.0 else pk - D
                cu = bal - thr; k = 1 + int(cu / S)
                if k > K: k = K
                g = 0 if (k == 1 and cu < cLow) else k
                kk = 1.0 if g == 0 else float(g)
                if bal + FL[g, t] - kk * hp[d] <= thr: st = -1; break
                bal += FC[g, t] - kk * hp[d]
                if bal > pk: pk = bal
                if bal - B >= 500.0:
                    amt = bal - B; bal -= amt; cash[min(2, (d - s) // 252)] += 0.9 * amt
                d += 1
            if st == -1:
                nb += 1
                if d - s >= 504: nb3 += 1
                bal_end = 0.0
            else: bal_end = bal
            i = d + 1
        out[r, 0] = cash[0]; out[r, 1] = cash[1]; out[r, 2] = cash[2]; out[r, 3] = nb; out[r, 4] = bal_end; out[r, 5] = nb3; r += 1
    return r


if __name__ == "__main__":
    days, sets = pickle.load(open(CACHE, "rb")); n = len(days); d24 = int(np.searchsorted(days, 20240101)); rng = np.random.default_rng(41)
    P = sets["Ultra+six+gold"]; fin = P[0][0][2] + 4 * P[0][1][2]; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())
    h0 = np.zeros(n); EL, EC, _, _ = gears(P, h0, 4, 800.0, 8, 1.0)
    pos = np.arange(H3 + 1)
    RAMPS = {"constant full edge": np.zeros(H3 + 1), "constant -35%": np.full(H3 + 1, 0.35), "dies over 3 years": np.minimum(1.0, pos / H3), "dies over 18 months": np.minimum(1.0, pos / 378.0), "dies over 6 months then zero": np.minimum(1.0, pos / 126.0)}
    POLS = {"1c": (1e9, 1, 4100.0, 0.0), "ladder K4 S3k B11.1k": (3000.0, 4, 11100.0, 0.0), "ladder + stop 1500/contract": (3000.0, 4, 11100.0, 1500.0)}
    OUT = {}
    for per, lo_, hi_, mu in (("T1", 0, d24, mu1), ("T2", d24, n, mu2)):
        for rn, ramp in RAMPS.items():
            hp = ramp * mu
            for pol, (S, K, B, L) in POLS.items():
                FL, FC = gears_stop(P, h0, 4, L)
                xs = []
                for b_ in range(NB):
                    bi = np.concatenate([np.arange(s_, s_ + 21) for s_ in rng.integers(lo_, hi_ - 21, H3 // 21 + 2)])[:H3 + 1].astype(np.int64)
                    out = np.zeros((1, 6)); life3d(EL, EC, hp, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0, S, K, B, bi, H3, 5, out); xs.append(out[0])
                x = np.array(xs)
                rec = dict(y1=round(float(np.median(x[:, 0]) / 365)), y2=round(float(np.median(x[:, 1]) / 365)), y3=round(float(np.median(x[:, 2]) / 365)), total3y=round(float(np.median(x[:, :3].sum(1)))),
                           total3y_p10=round(float(np.percentile(x[:, :3].sum(1), 10))), busts_3y=round(float(x[:, 3].mean()), 2), busts_y3=round(float(x[:, 5].mean()), 2), retained_end=round(float(np.median(x[:, 4]))), P_total_neg=round(100 * float((x[:, :3].sum(1) < 0).mean()), 1))
                OUT[f"{per} | {rn} | {pol}"] = rec
                print(f"{per} {rn:28s} {pol:28s} $/day y1 {rec['y1']:4d} y2 {rec['y2']:4d} y3 {rec['y3']:4d}  3y total {rec['total3y']:7,d} (p10 {rec['total3y_p10']:7,d})  busts 3y {rec['busts_3y']:.2f} (y3 {rec['busts_y3']:.2f})  retained end {rec['retained_end']:6,d}  P(3y<0) {rec['P_total_neg']:4.1f}", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "ladder_decay.json"), "w"), indent=1)
