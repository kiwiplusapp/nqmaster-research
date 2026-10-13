"""2026-10-13 'one eval, no second purchase, pass >= 70%'. Single attempt only (no restarts). Real Databento NQ 2020-26, current profiles
(UltraR / WR70R / Estable, trade filters by $ risk 150-300), +1 tick per side. Levers searched together:
  - firm shape (bot-friendly firms from propfirms_2026.md)
  - two gears by cushion (eq - trailing threshold): LOW set below C, FULL set at/above C (FULL may be 1 or 2 contracts)
  - optional deadline push: from list day d0, FULL gear uses PUSH set (2-3 contracts) while the eval is not passed
  - account daily loss stop L (whole day stops at -L, from the minute path) and the consistency profit stop G = 0.9 x cons x target
Pass measured within 20 list days (~1 month), 30, 44 (~2 months), 66 (~3 months) and 120 (~6 months).
Chosen on T1 (starts 2020-03..2023-10) per firm and objective; reported on T2 (starts 2024-01..2026-04) and with a 35% edge haircut.
-> single70.json, single70_grid.csv"""
import os, sys, json, pickle, itertools, numpy as np, pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_life import SP

H = 120
WS = (20, 30, 44, 66, 120)
FIRMS = {  # target, dd, consistency, min days, dll, max micros in eval
    "Lucid Pro 25K": (1250, 1000, 0.0, 0, 0, 20), "Lucid Flex 25K": (1250, 1000, 0.5, 0, 0, 20),
    "FundedNext Rapid Pro 25K": (1500, 1000, 0.0, 0, 0, 20), "Bulenox Opt2 25K": (1500, 1500, 0.0, 0, 500, 30),
    "Lucid Pro 50K": (3000, 2000, 0.0, 0, 0, 40), "Lucid Flex 50K": (3000, 2000, 0.5, 0, 0, 40),
    "Bulenox Opt2 50K": (3000, 2500, 0.0, 0, 1100, 70), "MFFU Rapid EOD 50K": (3000, 2000, 0.3, 4, 0, 30)}


@njit(cache=True)
def ev_g(EL, EC, C, d0, T, D, cons, mind, s, n):
    """single eval with gears: 0 LOW (cushion < C), 1 FULL, 2 PUSH (FULL gear from list day d0 on). returns (result, offset)"""
    eq = 0.0; pk = 0.0; best = -1e9; d = s
    while d < n:
        thr = 100.0 if pk >= D + 100.0 else pk - D
        g = 1 if eq - thr >= C else 0
        if g == 1 and d0 >= 0 and d - s >= d0: g = 2
        if eq + EL[g, d] <= thr: return -1, d - s
        c = EC[g, d]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= T and d - s + 1 >= mind and (cons <= 0.0 or best <= cons * eq): return 1, d - s
        d += 1
    return 0, n - s


@njit(cache=True)
def run_starts(EL, EC, C, d0, T, D, cons, mind, starts, Hh, out_r, out_d):
    for i in range(len(starts)):
        s = starts[i]; r, o = ev_g(EL, EC, C, d0, T, D, cons, mind, s, min(len(EL[0]), s + Hh)); out_r[i] = r; out_d[i] = o


def vec(low, close, fin, G, L):
    """day vectors (intraday low, day result) with an account profit stop G and loss stop L (first touch wins)"""
    nd = low.shape[0]; lo = low.min(1); cl = fin.copy()
    for d in range(nd):
        tg = np.argmax(close[d] >= G) if G > 0 and (close[d] >= G).any() else 99999
        tl = np.argmax(low[d] <= -L) if L > 0 and (low[d] <= -L).any() else 99999
        if tg == 99999 and tl == 99999: continue
        if tl <= tg: lo[d] = -L; cl[d] = -L
        else: lo[d] = low[d, :tg + 1].min(); cl[d] = close[d, tg]
    return np.minimum(lo, cl), cl


def metrics(r, o):
    out = {f"p{w}": round(100 * float(np.mean((r == 1) & (o < w))), 1) for w in WS}
    out["bust"] = round(100 * float(np.mean(r == -1)), 1)
    pas = o[r == 1]; out["med_days"] = float(np.median(pas) + 1) if len(pas) else None
    return out


if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb")); n = len(days)
    d24 = int(np.searchsorted(days, 20240101))
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0].astype(np.int64)
    s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - H].astype(np.int64)
    SETS = {"U": ("UltraR", 0), "U150": ("UltraR", 150), "U200": ("UltraR", 200), "U300": ("UltraR", 300),
            "W": ("WR70R", 0), "W200": ("WR70R", 200), "E": ("Estable", 0), "E200": ("Estable", 200)}
    VC = {}

    def V(key, k, G, L, hc):
        kk = (key, k, G, L, hc)
        if kk not in VC:
            low, close, fin = P[SETS[key]]; c = P[SETS[key] + ("cost",)]
            mu1 = fin[:d24].mean(); mu2 = fin[d24:].mean(); h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
            VC[kk] = vec(k * (low - c[:, None] - h[:, None]), k * (close - c[:, None] - h[:, None]), k * (fin - c - h), G, L)
        return VC[kk]

    LOWS = [("U", 1), ("U150", 1), ("U200", 1), ("U300", 1), ("W", 1), ("W200", 1), ("E", 1), ("E200", 1)]
    FULLS = [("U", 1), ("W", 1), ("U", 2), ("W", 2), ("E", 2)]
    rows = []
    for firm, (T, D, cons, mind, dll, mx) in FIRMS.items():
        G = 0.9 * cons * T if cons > 0 else 0.0
        Cs = [0, 0.4 * D, 0.6 * D, 0.8 * D, 1.0 * D, 1.3 * D]
        Ls = sorted(set([dll] + [x for x in (0, 0.3 * D, 0.45 * D, 0.6 * D) if dll == 0 or x < dll]))
        PUSH = [(-1, None), (8, ("U", 2)), (12, ("U", 2)), (15, ("U", 2)), (12, ("U", 3)), (15, ("U", 3))]
        cnt = 0
        for (lo_s, lo_k), (fu_s, fu_k), C, L, (d0, pu) in itertools.product(LOWS, FULLS, Cs, Ls, PUSH):
            if C == 0 and (lo_s, lo_k) != LOWS[0]: continue                    # no low gear -> one representative
            if pu is not None and pu[1] <= fu_k: continue
            if 11 * max(fu_k, pu[1] if pu else 0) > 1.25 * mx: continue
            rec = dict(firm=firm, low=f"{lo_s}x{lo_k}", full=f"{fu_s}x{fu_k}", C=C, L=L, d0=d0, push="" if pu is None else f"{pu[0]}x{pu[1]}")
            for hc in (0.0, 0.35):
                Ls_ = L if L > 0 else 0.0
                A = V(lo_s, lo_k, G, Ls_, hc); B = V(fu_s, fu_k, G, Ls_, hc); Cc = V(pu[0], pu[1], G, Ls_, hc) if pu else B
                EL = np.ascontiguousarray(np.array([A[0], B[0], Cc[0]])); EC = np.ascontiguousarray(np.array([A[1], B[1], Cc[1]]))
                for tag, st in (("T1", s1), ("T2", s2)):
                    r = np.zeros(len(st), np.int64); o = np.zeros(len(st), np.int64)
                    run_starts(EL, EC, float(C), int(d0), float(T), float(D), float(cons), int(mind), st, H, r, o)
                    m = metrics(r, o); sfx = "" if hc == 0 else "_h35"
                    for kx, vx in m.items(): rec[f"{tag}_{kx}{sfx}"] = vx
            rows.append(rec); cnt += 1
        print(firm, cnt, flush=True)
    R = pd.DataFrame(rows); R.to_csv(os.path.join(HERE, "single70_grid.csv"), index=False)
    OUT = {}
    base_cols = ["low", "full", "C", "L", "d0", "push"]
    for firm in FIRMS:
        F = R[R.firm == firm]
        for obj in ("p20", "p30", "p44", "p120"):
            b = F.sort_values(f"T1_{obj}", ascending=False).iloc[0]
            fixed1 = F[(F.low == "Ux1") & (F.full == "Ux1") & (F.C == 0) & (F.L == FIRMS[firm][4]) & (F.d0 == -1)].iloc[0]
            OUT[f"{firm} | best on T1 for {obj}"] = {**{c: (b[c] if not isinstance(b[c], (np.integer, np.floating)) else float(b[c])) for c in base_cols},
                                                       **{c: float(b[c]) if b[c] == b[c] else None for c in R.columns if c.startswith(("T1_", "T2_"))}}
            OUT[f"{firm} | Ultra 1c fixed"] = {c: float(fixed1[c]) if fixed1[c] == fixed1[c] else None for c in R.columns if c.startswith(("T1_", "T2_"))}
            print(f"{firm:26s} {obj:5s} best T1: low {b.low} full {b.full} C {b.C:.0f} L {b.L:.0f} push {b.push or '-'}@{b.d0} | "
                  f"T1 " + " ".join(f"{b[f'T1_p{w}']:.0f}" for w in WS) + " | T2 " + " ".join(f"{b[f'T2_p{w}']:.0f}" for w in WS) +
                  " | h35 T1 " + " ".join(f"{b[f'T1_p{w}_h35']:.0f}" for w in WS) + " T2 " + " ".join(f"{b[f'T2_p{w}_h35']:.0f}" for w in WS) +
                  f" | med {b.T1_med_days}/{b.T2_med_days}", flush=True)
        print(f"{firm:26s} Ultra 1c fixed: T1 " + " ".join(f"{fixed1[f'T1_p{w}']:.0f}" for w in WS) + " | T2 " + " ".join(f"{fixed1[f'T2_p{w}']:.0f}" for w in WS), flush=True)
    json.dump(OUT, open(os.path.join(HERE, "single70.json"), "w"), indent=1)
