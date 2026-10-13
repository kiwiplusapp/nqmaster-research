"""2026-10-13 'one funded account within a month, >= 75-80%'. Current Ultra (UltraR), real Databento NQ 2020-26, +1 tick per side, contracts per module
k = 1..4 (paths scaled by k), firm rules from propfirms_2026.md, daily profit stop 0.9 x consistency x target, eval always full profile.
STRICT month: the pass must come within 21 list days of the first start (list skips FOMC / ATR<150 days ~3-5% -> ~22 real trading days), fixing the
off-by-one found by the 2026-10-13 review. Two numbers per setup: single eval (one attempt) and serial restarts (new eval the day after a bust).
Edge 0% and 35% haircut. 44-day block bootstrap 90% interval for the main candidates.  -> month80.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_life import vectors, SP
from mffu_rapid import ev_m
W = 20                       # pass offset <= 20 -> pass on list day 21 at the latest
H = 120
SET = {  # target, dd, consistency, min days, dll, fee, max micros in eval
    "Lucid Flex 25K": (1250, 1000, 0.5, 0, 0, 89, 20), "Lucid Pro 25K": (1250, 1000, 0.0, 0, 0, 123, 20),
    "Lucid Flex 50K": (3000, 2000, 0.5, 0, 0, 146, 40), "Lucid Pro 50K": (3000, 2000, 0.0, 0, 0, 192, 40),
    "Bulenox Opt2 25K": (1500, 1500, 0.0, 0, 500, 175, 30), "Bulenox Opt2 50K": (3000, 2500, 0.0, 0, 1100, 175, 70),
    "FundedNext Rapid Pro 25K": (1500, 1000, 0.0, 0, 0, 80, 20), "FundedNext Rapid Pro 50K": (3000, 2000, 0.0, 0, 0, 150, 40),
    "MFFU Rapid EOD 50K": (3000, 2000, 0.3, 4, 0, 157, 30)}


def outcomes(lo, cl, T, D, cons, mind, n):
    EL = np.ascontiguousarray(np.array([lo, lo])); EC = np.ascontiguousarray(np.array([cl, cl])); idx = np.arange(n, dtype=np.int64)
    res = np.zeros(n, np.int8); dd = np.zeros(n, np.int32)
    for s in range(n):
        r, j = ev_m(EL, EC, -1e9, float(T), float(D), float(cons), int(mind), idx, s, min(n, s + H)); res[s] = r; dd[s] = j - s
    return res, dd                       # dd = offset of the pass/bust day from the start


def serial_first(res, dd, s0, W):
    s = s0; k = 0
    while s < len(res) and s - s0 <= W:
        k += 1
        if res[s] == 1: return (s + dd[s] - s0) <= W, k
        if res[s] == -1: s = s + dd[s] + 1
        else: return False, k
    return False, k


def summary(res, dd, starts, fee):
    single = np.mean([(res[s] == 1) and dd[s] <= W for s in starts])
    ser = [serial_first(res, dd, s, W) for s in starts]
    return round(100 * float(single), 1), round(100 * float(np.mean([a for a, _ in ser])), 1), round(float(np.mean([k for _, k in ser])), 2), round(float(np.mean([k for _, k in ser])) * fee)


def boot(res, dd, starts, fee, B=400, blk=44, seed=7):
    """block bootstrap over start days (blocks of consecutive starts) -> 90% interval of the serial-restart rate"""
    rng = np.random.default_rng(seed); ser = np.array([serial_first(res, dd, s, W)[0] for s in starts], float); sg = np.array([(res[s] == 1) and dd[s] <= W for s in starts], float)
    nb = max(1, len(starts) // blk); out = []; out2 = []
    for _ in range(B):
        st = rng.integers(0, len(starts) - blk, nb); ii = np.concatenate([np.arange(a, a + blk) for a in st]); out.append(ser[ii].mean()); out2.append(sg[ii].mean())
    return [round(100 * float(np.percentile(out, 5)), 1), round(100 * float(np.percentile(out, 95)), 1)], [round(100 * float(np.percentile(out2, 5)), 1), round(100 * float(np.percentile(out2, 95)), 1)]


if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb")); n = len(days)
    low, close, fin = P[("UltraR", 0)]; c = P[("UltraR", 0, "cost")]
    d24 = int(np.searchsorted(days, 20240101)); mu1 = float(fin[:d24].mean()); mu2 = float(fin[d24:].mean())
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 40]
    OUT = {}
    for name, (T, D, cons, mind, dll, fee, mx) in SET.items():
        G = 0.9 * cons * T if cons > 0 else 0.0
        for k in (1, 2, 3, 4):
            if 11 * k > mx * 1.25: continue                          # validated peak ~11 MNQ per base contract
            for hc in (0.0, 0.35):
                h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
                lo, cl = vectors(k * (low - c[:, None] - h[:, None]), k * (close - c[:, None] - h[:, None]), k * (fin - c - h), G)
                if dll > 0:
                    hit = lo <= -dll; cl = np.where(hit, -float(dll), cl); lo = np.where(hit, -float(dll), lo)
                res, dd = outcomes(lo, cl, T, D, cons, mind, n)
                a = summary(res, dd, s1, fee); b = summary(res, dd, s2, fee)
                rec = dict(T1=dict(single=a[0], serial=a[1], evals=a[2], fees=a[3]), T2=dict(single=b[0], serial=b[1], evals=b[2], fees=b[3]))
                if hc == 0.0: rec["T2_ci90_serial"], rec["T2_ci90_single"] = boot(res, dd, s2, fee); rec["T1_ci90_serial"], rec["T1_ci90_single"] = boot(res, dd, s1, fee)
                OUT[f"{name} | {k}c | edge-{int(hc*100)}%"] = rec
                print(f"{name:26s} {k}c edge-{int(hc*100):2d}% | single T1 {a[0]:5.1f} T2 {b[0]:5.1f} | restarts T1 {a[1]:5.1f} T2 {b[1]:5.1f} (evals {b[2]}, ${b[3]})" + (f" | CI90 T2 {rec['T2_ci90_serial']} T1 {rec['T1_ci90_serial']}" if hc == 0 else ""), flush=True)
    json.dump(OUT, open(os.path.join(HERE, "month80.json"), "w"), indent=1)
