"""Deterministic history stress (2026-10-12 overhaul): an MFFU Rapid EOD 50K eval and a fresh funded account started on EVERY real
trading day 2020-26 (no resampling), 1 contract, old default (Ultra, no risk cap) vs new default (UltraR = Ultra - ENG10 - LATEFH -
2 context boosts + 0.10 ATR min stop, with the $300 per-contract risk cap below a $1,200 eval / $2,000 funded cushion) and WR70Plus.
Eval: target $3,000, $2,000 EOD trailing (lock +100), 30% consistency with the $800 daily profit stop, min 4 days.
Funded: $2,000 trailing from a fresh start, withdraw above $4,100; bust = within 60 trading days.
Summer 2026 table: every start from 2026-06-01 (the August 2026 drawdown) to the end of the data.
-> stress_hist.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from mffu_rapid import ev_m, fu_m

if __name__ == "__main__":
    E = RB.setup(); TRD = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))
    days = pickle.load(open(os.path.join(SP, "robust2_paths.pkl"), "rb"))[0]
    V = {}
    for name in ("Ultra", "UltraR", "WR70Plus", "WR70R"):
        X = RB.attach(TRD[name][0][TRD[name][0].date.isin(days)], E)
        for sfx, XX in (("", X), ("_cap300", X[X.risk <= 300])):
            low, close, fin = full_paths(XX, days)
            for G in (0.0, 800.0): V[(name + sfx, G)] = vectors(low, close, fin, G)
    POL = {"OLD Ultra (no cap)": ("Ultra", "Ultra", 0, 0), "NEW Ultra (UltraR + cap300 e1200 f2000)": ("UltraR_cap300", "UltraR", 1200, 2000),
           "OLD WR70Plus": ("WR70Plus", "WR70Plus", 0, 0), "NEW WR70Plus (WR70R + cap)": ("WR70R_cap300", "WR70R", 1200, 2000)}
    n = len(days); idx = np.arange(n, dtype=np.int64); OUT = {}
    for pol, (low, high, Ce, Cf) in POL.items():
        EL = np.ascontiguousarray(np.array([V[(low, 800.0)][0], V[(high, 800.0)][0]])); EC = np.ascontiguousarray(np.array([V[(low, 800.0)][1], V[(high, 800.0)][1]]))
        FL = np.ascontiguousarray(np.array([V[(low, 0.0)][0], V[(high, 0.0)][0], V[(high, 0.0)][0]])); FC = np.ascontiguousarray(np.array([V[(low, 0.0)][1], V[(high, 0.0)][1], V[(high, 0.0)][1]]))
        rows = []
        for s in range(n):
            r, j = ev_m(EL, EC, float(Ce), 3000.0, 2000.0, 0.3, 4, idx, s, n)
            cash, m, st, fj = fu_m(FL, FC, float(Cf), float(Cf), idx, s, min(n, s + 60), 4100.0, 2000.0, 0)
            rows.append(dict(start=int(days[s]), eval=int(r), eval_days=int(j - s + 1) if r != 0 else None, funded_bust60=int(st == -1), funded_cash60=round(float(cash))))
        R = pd.DataFrame(rows)
        def agg(Q):
            done = Q[Q["eval"] != 0]
            return dict(starts=int(len(Q)), eval_pass=round(100 * float((done["eval"] == 1).mean()), 1) if len(done) else None,
                        eval_bust=round(100 * float((done["eval"] == -1).mean()), 1) if len(done) else None, unfinished=int((Q["eval"] == 0).sum()),
                        median_days_to_pass=float(done[done["eval"] == 1].eval_days.median()) if (done["eval"] == 1).any() else None,
                        funded_bust_60d=round(100 * float(Q.funded_bust60.mean()), 1), funded_cash_60d=round(float(Q.funded_cash60.mean())))
        full = R[R.start <= int(days[max(0, n - 61)])]
        OUT[pol] = {"2020-23": agg(full[full.start < 20240101]), "2024-26": agg(full[full.start >= 20240101]),
                    "summer 2026 starts (Jun 1 - Aug 31)": agg(R[(R.start >= 20260601) & (R.start <= 20260831)]),
                    "starts Jul 15 - Aug 15 2026": agg(R[(R.start >= 20260715) & (R.start <= 20260815)])}
        print(pol, json.dumps(OUT[pol]), flush=True)
    json.dump(OUT, open(os.path.join(HERE, "stress_hist.json"), "w"), indent=1)
