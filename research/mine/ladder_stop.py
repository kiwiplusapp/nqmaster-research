"""2026-10-17 (after the red team): protect the ladder's retained cushion with an ACCOUNT daily loss stop and read the steady state.
MFFU 50K, Ultra + six-year modules + gold Robust, same paths as ladder_plan.py (scratchpad cache). Ladder K4 S3k B11.1k and K4 S2k B8.1k
(the T1-only choice) with a daily loss stop L per base contract (the account flattens when the day's equity reaches -L x contracts; the
day then ends at -L x contracts), L in {none, 1000, 1500, 2000}. 36-month windows -> year 1 vs years 2-3 (steady state), full edge and
-35%; history (every 5th start) and 300 block-bootstrap 3-year paths per period. -> ladder_stop.json"""
import os, sys, json, pickle, numpy as np
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_life import vectors
from ladder_plan import CACHE, fu_ladder_m, gears
from mffu_rapid import ev_m
H3 = 756; NB = 300


@njit(cache=True)
def life3(EL, EC, T, D, cons, mind, fee, FL, FC, cLow, S, K, B, idx, H, step, out):
    """3-year slots; out: 0 net cash year 1, 1 net cash years 2-3, 2 busts, 3 evals"""
    N = len(idx); r = 0
    da = np.zeros(6)
    for s in range(0, N - H, step):
        end = s + H; i = s; cash1 = 0.0; cash23 = 0.0; nev = 0; nb = 0
        while i < end:
            fee_i = fee
            if i - s < 252: cash1 -= fee_i
            else: cash23 -= fee_i
            nev += 1
            res, j = ev_m(EL, EC, -1e9, T, D, cons, mind, idx, i, end)
            if res != 1:
                i = j + 1; continue
            # funded with per-day cash attribution: run day by day (re-implement fu_ladder_m inline)
            bal = 0.0; pk = 0.0; d = j + 1; st = 0
            while d < end:
                t = idx[d]
                thr = 100.0 if pk >= D + 100.0 else pk - D
                cu = bal - thr; k = 1 + int(cu / S)
                if k > K: k = K
                g = 0 if (k == 1 and cu < cLow) else k
                if bal + FL[g, t] <= thr: st = -1; break
                bal += FC[g, t]
                if bal > pk: pk = bal
                if bal - B >= 500.0:
                    amt = bal - B; bal -= amt
                    if d - s < 252: cash1 += 0.9 * amt
                    else: cash23 += 0.9 * amt
                d += 1
            nb += st == -1; i = d + 1
        out[r, 0] = cash1; out[r, 1] = cash23; out[r, 2] = nb; out[r, 3] = nev; r += 1
    return r


def with_stop(P, L):
    """apply an account daily loss stop at -L per base contract to the 1-contract paths (low, close, fin) of P[cap] component a"""
    if L <= 0: return P
    Q = {}
    for cap, (a, b, ca, cb) in P.items():
        low, close, fin = a                                  # non-x4 part; the x4 part b is added at scale m -> approximate: stop on the total handled in gears? keep simple: stop on component a only
        Q[cap] = (a, b, ca, cb)
    return Q


def gears_stop(P, h, K, L):
    """gears with a daily loss stop: the day's total path (a + 4b) at 1 contract is cut at -L (close = -L from the first minute it is reached)."""
    def tot(cap):
        a, b, ca, cb = P[cap]; cc = ca + 4 * cb
        lo = a[0] + 4 * b[0] - cc[:, None] - h[:, None]; cl = a[1] + 4 * b[1] - cc[:, None] - h[:, None]; fin = a[2] + 4 * b[2] - cc - h
        if L > 0:
            hit = lo <= -L; has = hit.any(1); t = hit.argmax(1)
            lo = lo.copy(); cl = cl.copy(); fin = fin.copy()
            for d in np.nonzero(has)[0]: lo[d, t[d]:] = -L; cl[d, t[d]:] = -L; fin[d] = -L
        return lo.min(1), fin
    low = tot(300); full = tot(0)
    FL = np.ascontiguousarray(np.array([low[0]] + [k * full[0] for k in range(1, K + 1)])); FC = np.ascontiguousarray(np.array([low[1]] + [k * full[1] for k in range(1, K + 1)]))
    return FL, FC


if __name__ == "__main__":
    days, sets = pickle.load(open(CACHE, "rb")); n = len(days); idx = np.arange(n, dtype=np.int64); d24 = int(np.searchsorted(days, 20240101)); rng = np.random.default_rng(31)
    P = sets["Ultra+six+gold"]; fin = P[0][0][2] + 4 * P[0][1][2]; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())
    OUT = {}
    for hc in (0.0, 0.35):
        h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
        EL, EC, _, _ = gears(P, h, 4, 800.0, 8, 1.0)
        for lad, (S, B) in {"K4 S3k B11.1k": (3000.0, 11100.0), "K4 S2k B8.1k": (2000.0, 8100.0), "K3 S3k B8.1k": (3000.0, 8100.0), "1c": (1e9, 4100.0)}.items():
            K = 1 if lad == "1c" else (3 if lad.startswith("K3") else 4)
            for L in (0.0, 1000.0, 1500.0, 2000.0):
                FL, FC = gears_stop(P, h, 4, L)
                def run(ix):
                    out = np.zeros((len(ix), 4)); k = life3(EL, EC, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0, S, K, B, ix, H3, 5, out); return out[:k]
                o = run(idx); st = np.arange(len(o)) * 5; rec = {}
                for per, lo_, hi_ in (("T1", 0, d24), ("T2", d24, n)):
                    ok = (st >= lo_) & (st + H3 <= hi_) if per == "T2" else (st + H3 <= d24)
                    x = o[ok] if ok.any() else None
                    xs = []
                    for b_ in range(NB):
                        bi = np.concatenate([np.arange(s_, s_ + 21) for s_ in rng.integers(lo_, hi_ - 21, H3 // 21 + 2)])[:H3 + 1].astype(np.int64)
                        xs.append(run(bi)[0])
                    xs = np.array(xs)
                    rec[per] = dict(hist_n=int(0 if x is None else len(x)), hist_y1=round(float(x[:, 0].mean() / 365)) if x is not None else None, hist_y23=round(float(x[:, 1].mean() / 730)) if x is not None else None,
                                    boot_y1=round(float(np.median(xs[:, 0]) / 365)), boot_y23=round(float(np.median(xs[:, 1]) / 730)), boot_y23_p10=round(float(np.percentile(xs[:, 1], 10) / 730)),
                                    P_y23_ge_200=round(100 * float((xs[:, 1] / 730 >= 200).mean()), 1), P_y23_neg=round(100 * float((xs[:, 1] < 0).mean()), 1), busts_per_year=round(float(xs[:, 2].mean() / 3), 2))
                key = f"edge-{int(hc*100)}% | {lad} | stop {int(L)}"; OUT[key] = rec
                r1, r2 = rec["T1"], rec["T2"]
                print(f"{key:36s} boot y1 {r1['boot_y1']:4d}/{r2['boot_y1']:4d}  y2-3 {r1['boot_y23']:4d}/{r2['boot_y23']:4d} (p10 {r1['boot_y23_p10']:4d}/{r2['boot_y23_p10']:4d})  P(y2-3>=200) {r1['P_y23_ge_200']:3.0f}/{r2['P_y23_ge_200']:3.0f}  P(y2-3 neg) {r1['P_y23_neg']:4.1f}/{r2['P_y23_neg']:4.1f}  busts/yr {r1['busts_per_year']:.2f}/{r2['busts_per_year']:.2f}  hist y2-3 {r1['hist_y23']}/{r2['hist_y23']}", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "ladder_stop.json"), "w"), indent=1)
