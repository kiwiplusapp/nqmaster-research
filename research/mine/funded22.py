"""Federico 2026-10-08: 'pass evals at a very high rate in no more than 22 days'. One eval at a time cannot do it with our edge
(50K, 22 trading days: <= ~50-55%). What can: P(holding a funded account within 22 trading days) when a NEW eval is started the
day after a bust (Lucid evals are bought instantly, no limit on attempts). Exact dense grids (intraday adverse equity vs EOD
trailing threshold locking at start + 100), every start day with >= 22 trading days left, IS / C24 / REAL.
Accounts: LucidPro 25K/50K/100K/150K (no eval consistency, no-DLL add-on), LucidFlex 25K/50K (50% consistency + daily profit stop
at 0.4667 x target). Contracts limited by Lucid's eval max micros (p99 ~7-8 micros per base contract, max ~11).
-> funded22.csv"""
import sys, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib  # noqa: F401
import lc_lib as L
from acct_life import CFG
from acct_policy import vec
from eval20 import ev

NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
PROF = {"Ultra+noche+oro Robust": L.define("F22_EU", CFG["UA_FULL_GR"] + NIGHT),
        "WR70Plus+noche+oro WinRate": L.define("F22_EW", CFG["WR_FULL_GW"] + NIGHT)}
# name: (target, drawdown, consistency, eval fee with ~28% coupon (+ no-DLL add-on for Pro), max base contracts)
ACC = {"Pro 25K": (1250.0, 1000.0, 0.0, 89.0, 2), "Pro 50K": (3000.0, 2000.0, 0.0, 152.0, 4),
       "Pro 100K": (6000.0, 3000.0, 0.0, 246.0, 6), "Pro 150K": (9000.0, 4500.0, 0.0, 328.0, 9),
       "Flex 25K": (1250.0, 1000.0, 0.5, 64.0, 2), "Flex 50K": (3000.0, 2000.0, 0.5, 105.0, 4)}
W = 22


@njit(cache=True)
def window(LO, CL, T, D, cons, k, W, out):
    n = LO.shape[1]; m = n - W
    for s in range(m):
        i = s; att = 0; first = 0.0; ok = 0.0; dfun = 0.0
        while i < s + W:
            att += 1
            r, used = ev(LO, CL, T, D, cons, s + W - i, k, k, 0.0, 999, k, 0.0, i, n)
            if att == 1: first = 1.0 if r == 1 else 0.0
            if r == 1: ok = 1.0; dfun = i - s + used; break
            if r == 0: break
            i += used
        out[s, 0] = first; out[s, 1] = ok; out[s, 2] = att; out[s, 3] = dfun
    return m


def mats(per, cfg, G, kmax):
    nd = len(vec(per, cfg, 0.0, 0.0)[0]); LO = np.zeros((kmax + 1, nd)); CL = np.zeros((kmax + 1, nd))
    for k in range(1, kmax + 1):
        lo, cl = vec(per, cfg, 0.0, G / k if G > 0 else 0.0); LO[k] = k * lo; CL[k] = k * cl
    return LO, CL


if __name__ == "__main__":
    rows = []
    for per in ("IS", "C24", "REAL"):
        for (pn, cfg), (an, (T, D, cons, fee, kmax)) in itertools.product(PROF.items(), ACC.items()):
            G = 0.4667 * T if cons > 0 else 0.0
            LO, CL = mats(per, cfg, G, kmax)
            for k in range(1, kmax + 1):
                out = np.zeros((LO.shape[1], 4)); m = window(LO, CL, T, D, cons, k, W, out); o = out[:m]; ok = o[:, 1] == 1
                rows.append(dict(per=per, perfil=pn, cuenta=an, k=k, una_eval_22d=100 * o[:, 0].mean(), fondeada_22d=100 * ok.mean(),
                                 intentos=o[:, 2].mean(), costo=fee * o[:, 2].mean(), dias_mediana=float(np.median(o[ok, 3])) if ok.any() else np.nan))
        print(per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("funded22.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    S = R.groupby(["perfil", "cuenta", "k"]).agg(una_eval=("una_eval_22d", "mean"), fondeada=("fondeada_22d", "mean"), fondeada_min=("fondeada_22d", "min"),
                                                 intentos=("intentos", "mean"), costo=("costo", "mean"), dias=("dias_mediana", "mean")).round(1)
    print(S.to_string())
