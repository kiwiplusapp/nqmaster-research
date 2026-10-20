"""2026-10-20 Federico (screenshot lucidtrading.com, Lucid Pro 50K eval: target $3,000, max loss $2,000 EOD trailing, daily loss limit $1,200 or OFF,
4 minis / 40 micros, no eval consistency, $115.40 with coupon, reset $115): 'pass this eval within a week at least 50% of the time, with 3 accounts,
then a normal conservative strategy that makes at least $1,000 a month'.
Paths: the 2027 default (Ultra as coded + durable six-year modules SO04/RV11/ORFAIL/CAM3 + GoldMaster Robust), real NQ 2020-02..2026-10,
+1 tick per side (acct2027_paths.pkl, built by acct_2027.py). Per base contract k, MOM1030 + CPI09 at m lots (NQMaster EvalHighWrMultiplier).
Eval race at MINUTE resolution: bust when equity + open low <= EOD threshold (threshold = peak close - 2,000, locks at +100 once the peak
reaches 2,100), pass the minute equity reaches +3,000 (NQMaster EvalTarget flattens there). DLL 1,200 = day stopped (soft) at -1,200.
Windows: 5 / 10 / 20 trading days. Three-account plans (all start the same day unless stated):
  same     : 3 identical evals (same path -> they pass or bust together)
  ladder   : 3 evals at different sizes
  serial   : up to 3 evals one after the other (a new one the day after a bust), all inside the window
Edge full / -35% / zero (zero = gambler's-ruin baseline).  T1 starts 2020-03..2023-10, T2 starts 2024-01..2026-09 (nothing is fitted).
Funded part: 12-month seats (eval -> funded Lucid Pro 50K: buffer 2,100, caps 2,000 then 2,500, 40% consistency per cycle, 5 payouts,
90% split) at 1c with different daily profit stops, block bootstrap.  -> lucidpro_week.json"""
import os, sys, json, pickle, numpy as np
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_life import vectors, SP
import acct1c_lib as A
T, D, FEE = 3000.0, 2000.0, 115.4


@njit(cache=True)
def race(LO, CL, idx, s, n, dll):
    """minute-level eval race; LO/CL [day, minute] cumulative intraday P&L (low / close). Returns (result, last position)."""
    eq = 0.0; pk = 0.0; d = s
    while d < n:
        t = idx[d]; thr = 100.0 if pk >= D + 100.0 else pk - D
        last = 0.0
        for j in range(LO.shape[1]):
            if dll > 0 and CL[t, j] <= -dll:
                last = -dll; break
            if eq + LO[t, j] <= thr: return -1, d
            if eq + CL[t, j] >= T: return 1, d
            last = CL[t, j]
        eq += last
        if eq > pk: pk = eq
        d += 1
    return 0, n


@njit(cache=True)
def all_starts(LO, CL, idx, starts, H, dll, res, off):
    n = len(idx)
    for i in range(len(starts)):
        r, e = race(LO, CL, idx, starts[i], min(n, starts[i] + H), dll); res[i] = r; off[i] = e - starts[i]


def mats(P, k, m, h):
    a, b, ca, cb = P[0]; cc = (ca + m * cb)
    LO = k * (a[0] + m * b[0] - cc[:, None] - h[:, None]); CL = k * (a[1] + m * b[1] - cc[:, None] - h[:, None])
    return np.ascontiguousarray(np.minimum(LO, CL)), np.ascontiguousarray(CL)


def outcomes(LO, CL, n, dll, H=60):
    idx = np.arange(n, dtype=np.int64); st = np.arange(n - 1, dtype=np.int64); res = np.zeros(len(st), np.int8); off = np.zeros(len(st), np.int64)
    all_starts(LO, CL, idx, st, H, float(dll), res, off); return res, off


def p_win(res, off, s, W): return res[s] == 1 and off[s] < W


def plans(R, starts, W):
    """R: dict size-label -> (res, off). Returns single-eval rates per size and 3-account plans."""
    out = {}
    for lab, (res, off) in R.items():
        out[f"single {lab}"] = dict(pass_=100 * np.mean([p_win(res, off, s, W) for s in starts]),
                                    bust=100 * np.mean([res[s] == -1 and off[s] < W for s in starts]))
    def serial(lab):
        res, off = R[lab]; ok = []; used = []
        for s0 in starts:
            s = s0; k = 0; got = False
            while k < 3 and s - s0 < W:
                k += 1
                if res[s] == 1 and s + off[s] - s0 < W: got = True; break
                if res[s] == -1 and s + off[s] - s0 < W: s = s + off[s] + 1
                else: break
            ok.append(got); used.append(k)
        return 100 * np.mean(ok), float(np.mean(used))
    for lab in R:
        p, u = serial(lab); out[f"serial 3 x {lab}"] = dict(pass_=p, evals=u)
    labs = list(R)
    for combo in (labs[:3], labs[-3:], [labs[0], labs[len(labs) // 2], labs[-1]]):
        if len(set(combo)) < 3: continue
        hit = [any(p_win(*R[l], s, W) for l in combo) for s in starts]
        both = [sum(p_win(*R[l], s, W) for l in combo) for s in starts]
        out["ladder " + "+".join(combo)] = dict(pass_any=100 * np.mean(hit), mean_funded=float(np.mean(both)))
    return {k: {kk: round(vv, 1) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in out.items()}


def funded(P, h, n, rng, eval_k, eval_m, nb=200):
    """12-month seats: Lucid Pro 50K eval (serial restarts, size eval_k / x eval_m, daily-resolution race) -> funded variants."""
    def vec(k, m, cap, G):
        a, b, ca, cb = P[cap]; cc = ca + m * cb
        return vectors(k * (a[0] + m * b[0] - cc[:, None] - h[:, None]), k * (a[1] + m * b[1] - cc[:, None] - h[:, None]), k * (a[2] + m * b[2] - cc - h), G)
    two = lambda v: (np.ascontiguousarray(np.array([v[0], v[0]])), np.ascontiguousarray(np.array([v[1], v[1]])))
    EL, EC = two(vec(eval_k, eval_m, 0, 0.0)); one = np.ones(n, np.bool_)
    VAR = {"1c no stop": (1.0, 0.0), "1c stop 500": (1.0, 500.0), "1c stop 700": (1.0, 700.0), "1c stop 1000": (1.0, 1000.0), "2c stop 500": (2.0, 500.0)}
    res = {}
    for name, (fk, G) in VAR.items():
        low = vec(fk, 4, 300, G); full = vec(fk, 4, 0, G)
        FL = np.ascontiguousarray(np.array([low[0], full[0], full[0]])); FC = np.ascontiguousarray(np.array([low[1], full[1], full[1]]))
        res[name] = (FL, FC)
    return EL, EC, one, res


if __name__ == "__main__" and "funded" not in sys.argv:
    days, P = pickle.load(open(os.path.join(SP, "acct2027_paths.pkl"), "rb")); n = len(days); d24 = int(np.searchsorted(days, 20240101))
    a, b, ca, cb = P[0]; fin = a[2] + 4 * b[2] - ca - 4 * cb; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 25]
    SIZES = {"1c x4": (1, 4), "2c x4": (2, 4), "2c x8": (2, 8), "3c x4": (3, 4), "3c x8": (3, 8), "4c x4": (4, 4)}
    OUT = {"mu_per_contract_day": [round(mu1, 1), round(mu2, 1)]}
    for hc in (0.0, 0.35, 1.0):
        h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
        for dll in (0, 1200):
            R = {lab: outcomes(*mats(P, k, m, h), n, dll) for lab, (k, m) in SIZES.items()}
            for W in (5, 10, 20):
                for per, st in (("T1", s1), ("T2", s2)):
                    key = f"edge-{int(hc*100)}% | DLL {dll or 'OFF'} | {W}d | {per}"; OUT[key] = plans(R, st, W)
            for W in (5, 10):
                print(f"edge-{int(hc*100):3d}% DLL {str(dll or 'OFF'):4s} {W:2d}d  single " +
                      "  ".join(f"{lab} {OUT[f'edge-{int(hc*100)}% | DLL {dll or chr(79)+chr(70)+chr(70)} | {W}d | T1'][f'single {lab}']['pass_']:4.1f}/"
                                f"{OUT[f'edge-{int(hc*100)}% | DLL {dll or chr(79)+chr(70)+chr(70)} | {W}d | T2'][f'single {lab}']['pass_']:4.1f}" for lab in SIZES), flush=True)
    json.dump(OUT, open(os.path.join(HERE, "lucidpro_week.json"), "w"), indent=1)


def part2(NB=200):
    """12-month Lucid Pro 50K seats: eval 4c x4 serial restarts (daily resolution) -> funded variants; median $/month per seat."""
    days, P = pickle.load(open(os.path.join(SP, "acct2027_paths.pkl"), "rb")); n = len(days); d24 = int(np.searchsorted(days, 20240101))
    a, b, ca, cb = P[0]; fin = a[2] + 4 * b[2] - ca - 4 * cb; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())
    rng = np.random.default_rng(11); H = 252; OUT = {}
    for hc in (0.0, 0.35, 1.0):
        h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
        EL, EC, one, V = funded(P, h, n, rng, 4.0, 4.0)
        for per, lo, hi in (("T1", 0, d24), ("T2", d24, n)):
            acc = {k: [] for k in V}; lost = {k: [] for k in V}; pays = {k: [] for k in V}; evs = {k: [] for k in V}
            for _ in range(NB):
                bi = np.concatenate([np.arange(s, s + 21) for s in rng.integers(lo, hi - 21, H // 21 + 3)])[:H + 6].astype(np.int64)
                for name, (FL, FC) in V.items():
                    out = np.zeros((2, 9)); A.life(EL, EC, -1e9, T, D, 0.0, one, FEE, FL, FC, 1000.0, 1000.0, 1, 2000.0, 0.0, 2000.0, 2500.0, bi, H, 5, out)
                    acc[name].append(out[0, 0]); lost[name].append(out[0, 3]); pays[name].append(out[0, 4]); evs[name].append(out[0, 1])
            for name in V:
                x = np.array(acc[name]) / 12.0
                OUT[f"edge-{int(hc*100)}% | {per} | {name}"] = dict(median_month=round(float(np.median(x))), p10_month=round(float(np.percentile(x, 10))),
                    P_neg_year=round(100 * float((x < 0).mean()), 1), P_ge_1000=round(100 * float((x >= 1000).mean()), 1),
                    funded_busts_yr=round(float(np.mean(lost[name])), 2), payouts_yr=round(float(np.mean(pays[name])), 2), evals_yr=round(float(np.mean(evs[name])), 2))
                r = OUT[f"edge-{int(hc*100)}% | {per} | {name}"]
                print(f"edge-{int(hc*100):3d}% {per} {name:12s} median {r['median_month']:5d}/mo p10 {r['p10_month']:6d} P(>=1000) {r['P_ge_1000']:5.1f}% P(neg) {r['P_neg_year']:5.1f}% busts {r['funded_busts_yr']} payouts {r['payouts_yr']} evals {r['evals_yr']}", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "lucidpro_week_funded.json"), "w"), indent=1)


if __name__ == "__main__" and "funded" in sys.argv:
    part2()
