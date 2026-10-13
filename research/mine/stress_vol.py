"""High-volatility guard for prop accounts (2026-10-12). Theory: with a fixed $ trailing drawdown the race odds of an edge scale with
mu / sigma^2; module stops and targets scale with the daily ATR, so both mu and sigma scale with ATR and mu/sigma^2 ~ 1/ATR ->
high-ATR regimes are worse for prop accounts even when the edge per trade is unchanged. Guard: when today's daily ATR is above
k x its 250-day median, the per-trade $ risk cap applies at ANY cushion (cap X), not only below the cushion threshold.
Chosen on 2020-23 deterministic history + bootstrap lifecycle; 2024-26 = check; summer 2026 only reported.
Base = NEW Ultra (UltraR + cap300 below $1,200 eval / $2,000 funded cushion). -> stress_vol.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, vectors, boot, run_life, SP
from mffu_rapid import ev_m, fu_m
from wrq_lib import getD

if __name__ == "__main__":
    E = RB.setup(); TRD = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))
    days = pickle.load(open(os.path.join(SP, "robust2_paths.pkl"), "rb"))[0]
    D = getD("nqdb.npz")
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last(); atr = atr[atr.index > 0]
    med = atr.rolling(250, min_periods=120).median(); ratio = (atr / med).reindex(days).to_numpy()
    OUT = {"share_days_ratio": {f">{k}": {p: round(float(np.nanmean(ratio[m] > k)), 3) for p, m in (("2020-23", days < 20240101), ("2024-26", days >= 20240101))} for k in (1.2, 1.35, 1.5)}}
    print(OUT, flush=True)
    V = {}
    for name in ("UltraR", "WR70R"):
        X = RB.attach(TRD[name][0][TRD[name][0].date.isin(days)], E)
        for cap in (0, 300, 200, 150):
            XX = X if cap == 0 else X[X.risk <= cap]
            low, close, fin = full_paths(XX, days)
            c = (XX.w * 1.0).groupby(XX.date).sum().reindex(days, fill_value=0.0).to_numpy()
            for G in (0.0, 800.0):
                V[(name, cap, G)] = vectors(low, close, fin, G); V[(name, cap, G, "t1")] = vectors(low - c[:, None], close - c[:, None], fin - c, G)
        print("paths", name, flush=True)
    n = len(days); idx = np.arange(n, dtype=np.int64)
    IDS = {"2020-23": boot(days, (days >= 20200101) & (days < 20240101), 11), "2024-26": boot(days, days >= 20240101, 12)}

    def mix(name, base_cap, k, xcap, G, t1=False):
        """gear vector: cap base_cap on normal days, min(base_cap, xcap) on days with ratio > k (k=0: off)"""
        key = lambda c: (name, c, G, "t1") if t1 else (name, c, G)
        lo, cl = V[key(base_cap)]
        if k <= 0: return lo, cl
        cc = xcap if base_cap == 0 else min(base_cap, xcap)
        hl, hc = V[key(cc)]; hi = np.nan_to_num(ratio, nan=0.0) > k
        return np.where(hi, hl, lo), np.where(hi, hc, cl)

    for name in ("UltraR", "WR70R"):
        for k, xcap in [(0, 0)] + [(k, c) for k in (1.2, 1.35, 1.5) for c in (300, 200, 150)]:
            pol = f"{name} | guard ratio>{k} cap{xcap}" if k else f"{name} | no guard"
            def gears(G, t1=False):
                g0 = mix(name, 300, k, xcap, G, t1); g1 = mix(name, 0, k, xcap, G, t1); return g0, g1
            (e0l, e0c), (e1l, e1c) = gears(800.0); (f0l, f0c), (f1l, f1c) = gears(0.0)
            EL = np.ascontiguousarray(np.array([e0l, e1l])); EC = np.ascontiguousarray(np.array([e0c, e1c]))
            FL = np.ascontiguousarray(np.array([f0l, f1l, f1l])); FC = np.ascontiguousarray(np.array([f0c, f1c, f1c]))
            rows = []
            for s in range(n):
                r, j = ev_m(EL, EC, 1200.0, 3000.0, 2000.0, 0.3, 4, idx, s, n)
                cash, m, st, fj = fu_m(FL, FC, 2000.0, 2000.0, idx, s, min(n, s + 60), 4100.0, 2000.0, 0)
                rows.append((days[s], r, j - s + 1, st == -1, cash))
            R = pd.DataFrame(rows, columns=["start", "ev", "dd", "fb", "cash"])
            def agg(Q):
                dn = Q[Q.ev != 0]
                return dict(eval_pass=round(100 * float((dn.ev == 1).mean()), 1), med_days=float(dn[dn.ev == 1].dd.median()) if (dn.ev == 1).any() else None,
                            funded_bust60=round(100 * float(Q.fb.mean()), 1), funded_cash60=round(float(Q.cash.mean())))
            full = R[R.start <= days[n - 61]]
            rec = {"hist 2020-23": agg(full[full.start < 20240101]), "hist 2024-26": agg(full[full.start >= 20240101]),
                   "summer 2026": agg(R[(R.start >= 20260601) & (R.start <= 20260831)])}
            # lifecycle (resampled 12-month paths): plug the mixed vectors into run_life as 'Ultra' (high gear) and 'LOW' (low gear)
            VV = {}
            for t1 in (False, True):
                sfx = "_t1" if t1 else ""
                for G in (0.0, 800.0):
                    g0, g1 = gears(G, t1); VV[("LOW" + sfx, G)] = g0; VV[("Ultra" + sfx, G)] = g1
            for per, ids in IDS.items():
                a = run_life(VV, "MFFU", "LOW", 1200, "LOW", 2000, ids, False); b = run_life(VV, "MFFU", "LOW", 1200, "LOW", 2000, ids, True)
                rec["life " + per] = dict(per_month=a["per_month"], p10=a["p10_month"], lost=a["accounts_lost"], neg_yr=a["p_neg_year"], per_month_t1=b["per_month"], lost_t1=b["accounts_lost"])
            OUT[pol] = rec; print(pol, json.dumps(rec), flush=True)
    json.dump(OUT, open(os.path.join(HERE, "stress_vol.json"), "w"), indent=1)
