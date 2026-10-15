"""2026-10-15 prop lifecycle check of the size multipliers shipped on 2026-10-15 (MOM1030 x4, CPI09 x4, active in evals and funded unless
the cushion gear sets noBoost) and of sniper sizing, per 12-month seat (eval with serial restarts -> funded -> payouts -> bust -> new eval):
MFFU Rapid EOD 50K (life_m: eval profit stop 800, funded risk cap $300 below a $2,000 cushion, keep $4,100) and Lucid Flex 50K (acct1c_lib:
eval profit stop 1,350, funded risk cap $300 below a $1,000 cushion, payout at $4,000). Variants: multiplier m in eval x m in funded.
Paths = rest of Ultra (UltraR) + m x (MOM1030 + CPI09 at 1 contract), +1 tick per side, edge 0 / 35 % haircut. -> sniper_life.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from wrq_lib import getD
from mffu_rapid import life_m
import acct1c_lib as A
H = 252


def build(E, D):
    X = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["UltraR"][0]
    C = pickle.load(open(os.path.join(HERE, "ultraq_trades.pkl"), "rb"))["UltraQ"][0]; C = C[C["mod"] == "CPI09"].copy()
    key = pd.Series(np.arange(len(D.o)), index=pd.MultiIndex.from_arrays([D.date, D.sm])); key = key[~key.index.duplicated()]
    C["fi"] = [key.get((a, b), -1) for a, b in zip(C.date, C.tin)]; C["xi"] = [key.get((a, b), -1) for a, b in zip(C.date, C.tout)]
    C = C[(C.fi >= 0) & (C.xi >= 0)].copy(); C["e"] = D.o[C.fi.to_numpy()]
    C["risk"] = 0.35 * D.atr[D.day[C.fi.to_numpy()]] * D.pv		# red team 2026-10-16: D.atr is per day (was always 0 -> CPI09 never capped)
    X = RB.attach(X, E)
    cols = ["date", "mod", "tin", "tout", "d", "u", "fi", "xi", "w", "e", "risk"]
    T = pd.concat([X[cols], C[cols]], ignore_index=True).dropna(subset=["e"]).sort_values(["date", "tin"]).reset_index(drop=True)
    return T


if __name__ == "__main__":
    E = RB.setup(); D = getD(RB.NAME)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]; n = len(days); idx = np.arange(n, dtype=np.int64)
    T = build(E, D); T = T[T.date.isin(days)]; S = T["mod"].isin(["MOM1030", "CPI09"])
    P = {}
    for cap in (0, 300):
        R0 = T[~S]; S1 = T[S].assign(w=1.0)
        if cap: R0 = R0[R0.risk <= cap]; S1 = S1[S1.risk / S1.w.clip(lower=1) <= cap] if "risk" in S1 else S1
        P[cap] = (full_paths(R0, days), full_paths(S1, days), R0.w.groupby(R0.date).sum().reindex(days, fill_value=0).to_numpy(),
                  S1.w.groupby(S1.date).sum().reindex(days, fill_value=0).to_numpy())
        print("paths cap", cap, len(R0), len(S1), flush=True)
    d24 = int(np.searchsorted(days, 20240101))
    base_fin = P[0][0][2] + P[0][1][2]; mu1 = float(base_fin[:d24].mean()); mu2 = float(base_fin[d24:].mean())

    def vecm(cap, m, G, h):
        a, b, ca, cb = P[cap]
        cc = ca + m * cb
        return vectors(a[0] + m * b[0] - cc[:, None] - h[:, None], a[1] + m * b[1] - cc[:, None] - h[:, None], a[2] + m * b[2] - cc - h, G)

    def summ(o, st):
        a = o[(st + H) < d24]; b = o[st >= d24]
        return {p: dict(per_month=round(float(x[:, 0].mean() / 12)), p10_month=round(float(np.percentile(x[:, 0], 10) / 12)),
                        accounts_lost=round(float((x[:, 1] - x[:, 2] + x[:, 3]).mean()), 2), funded_busts=round(float(x[:, 3].mean()), 2),
                        neg_year_pct=round(100 * float((x[:, 0] < 0).mean()), 1)) for p, x in (("T1", a), ("T2", b))}
    OUT = {}
    for me, mf in ((1, 1), (4, 4), (4, 1), (1, 4), (2, 2), (2, 1), (8, 4), (8, 8), (8, 1), (6, 4)):
        for hc in (0.0, 0.35):
            h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
            # MFFU Rapid EOD 50K
            ev = vecm(0, me, 800.0, h); EL = np.ascontiguousarray(np.array([ev[0], ev[0]])); EC = np.ascontiguousarray(np.array([ev[1], ev[1]]))
            hf = vecm(0, mf, 0.0, h); lf = vecm(300, mf, 0.0, h)
            FL = np.ascontiguousarray(np.array([lf[0], hf[0], hf[0]])); FC = np.ascontiguousarray(np.array([lf[1], hf[1], hf[1]]))
            out = np.zeros((n, 9)); k = life_m(EL, EC, -1e9, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0, 1e9, 4100.0, 0, idx, H, 5, out)
            OUT[f"MFFU 50K | eval x{me} funded x{mf} | edge-{int(hc*100)}%"] = r1 = summ(out[:k], np.arange(k) * 5)
            # Lucid Flex 50K
            ev = vecm(0, me, 1350.0, h); EL = np.ascontiguousarray(np.array([ev[0], ev[0]])); EC = np.ascontiguousarray(np.array([ev[1], ev[1]]))
            FL = np.ascontiguousarray(np.array([lf[0], hf[0], hf[0]])); FC = np.ascontiguousarray(np.array([lf[1], hf[1], hf[1]]))
            out = np.zeros((n, 9)); k = A.life(EL, EC, -1e9, 3000.0, 2000.0, 0.5, np.ones(n, np.bool_), 146.0, FL, FC, 1000.0, 1000.0,
                                               0, 4000.0, 150.0, 2000.0, 2000.0, idx, H, 5, out)
            OUT[f"Lucid Flex 50K | eval x{me} funded x{mf} | edge-{int(hc*100)}%"] = r2 = summ(out[:k], np.arange(k) * 5)
            print(f"x{me}/x{mf} edge-{int(hc*100):2d}% | MFFU $/mo {r1['T1']['per_month']}/{r1['T2']['per_month']} lost {r1['T1']['accounts_lost']}/{r1['T2']['accounts_lost']}"
                  f" | Lucid $/mo {r2['T1']['per_month']}/{r2['T2']['per_month']} lost {r2['T1']['accounts_lost']}/{r2['T2']['accounts_lost']}", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "sniper_life.json"), "w"), indent=1)
