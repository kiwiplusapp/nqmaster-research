"""Federico 2026-10-07: 'pass each eval in 75-80% of the cases within 20 days max'.
Pass probability within 20 TRADING days for every start day (history), per period IS / C24 / REAL, on the dense minute grids
(intraday adverse equity vs an EOD-trailing threshold that locks at start + 100, like Lucid / Apex EOD / Topstep).
1) Lucid Flex 50K (target 3,000, MLL 2,000, best day <= 50% of profit, daily profit stop 1,400): profiles x fixed contracts x
   size policies.  2) Account-shape map: target and drawdown in 1-contract units (T1 = T / k, D1 = D / k) with / without the
   consistency rule -> which (T, D, k) combinations reach 75-80% in 20 days.  -> eval20.csv, eval20_map.csv"""
import sys, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib
from acct_life import CFG
from acct_policy import vec

NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
CFG["E_WRN"] = CFG["WR_FULL"] + NIGHT                    # what Federico runs on MNQ: WR70Plus + NightOnWr70
CFG["E_WRN_GW"] = CFG["WR_FULL_GW"] + NIGHT              # + GoldMaster WinRate
CFG["E_UAN_GR"] = CFG["UA_FULL_GR"] + NIGHT              # Ultra (ampliado + night) + GoldMaster Robust
CFG["E_UAN"] = CFG["UA_FULL"] + NIGHT
CFG["E_WRSAFE_N"] = CFG["WR_SAFE"] + NIGHT               # WR70Plus without x2 boosts, MOM11, VOLB
CFG["E_WRNOB_N"] = CFG["WR_NOB"] + NIGHT                 # WR70Plus without x2 boosts

@njit(cache=True)
def ev(LO, CL, T, D, cons, maxd, k0, kdd, c1, dsw, kl, goal, s, n):
    """LO/CL[k, d]: day low / close P&L at k contracts. Returns (1 pass / -1 bust / 0 time-out, trading days used)."""
    eq = 0.0; pk = 0.0; best = -1e9; d = s
    while d < n and d - s < maxd:
        thr = 100.0 if pk >= D + 100.0 else pk - D
        k = k0
        if eq - thr < c1: k = kdd
        elif d - s >= dsw and eq < goal: k = kl
        if eq + LO[k, d] <= thr: return -1, d - s + 1
        c = CL[k, d]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= T and (cons <= 0.0 or best <= cons * eq): return 1, d - s + 1
        d += 1
    return 0, d - s

@njit(cache=True)
def stats(LO, CL, T, D, cons, maxd, k0, kdd, c1, dsw, kl, goal, win):
    n = LO.shape[1]; m = n - win; out = np.zeros((m, 2))
    for s in range(m):
        r, j = ev(LO, CL, T, D, cons, maxd, k0, kdd, c1, dsw, kl, goal, s, n); out[s, 0] = r; out[s, 1] = j
    return out

def mats(per, cfg, G=0.0, kmax=4):
    nd = len(vec(per, cfg, 0.0, 0.0)[0]); LO = np.zeros((kmax + 1, nd)); CL = np.zeros((kmax + 1, nd))
    for k in range(1, kmax + 1):
        lo, cl = vec(per, cfg, 0.0, G / k if G > 0 else 0.0); LO[k] = k * lo; CL[k] = k * cl
    return LO, CL

def summ(o):
    ps = o[:, 0] == 1
    return dict(p20=100 * ps.mean(), bust=100 * (o[:, 0] == -1).mean(), timeout=100 * (o[:, 0] == 0).mean(),
                med=float(np.median(o[ps, 1])) if ps.any() else np.nan)

if __name__ == "__main__":
    PERS = ("IS", "C24", "REAL"); rows = []
    PROF = {"WR70Plus+noche (tu prueba)": "E_WRN", "WR70Plus+noche+oro WinRate": "E_WRN_GW", "Ultra+noche+oro Robust": "E_UAN_GR",
            "Ultra+noche": "E_UAN", "WR70Plus sin x2 +noche": "E_WRNOB_N", "WR70Plus SAFE +noche": "E_WRSAFE_N"}
    # size policies: (k0, kdd, cushion c1, from day dsw, kl, goal)
    POL = {"1 fijo": (1, 1, 0.0, 999, 1, 0.0), "2 fijo": (2, 2, 0.0, 999, 2, 0.0), "3 fijo": (3, 3, 0.0, 999, 3, 0.0), "4 fijo": (4, 4, 0.0, 999, 4, 0.0)}
    for k0, dsw, kl, goal, kdd, c1 in itertools.product((1, 2), (5, 8, 10, 12), (2, 3, 4), (1500.0, 2100.0), (1, 2), (0.0, 800.0, 1200.0)):
        if kl <= k0 or (kdd > k0) or (c1 == 0.0 and kdd != k0): continue
        POL[f"{k0}->{kl} dia{dsw} si <{goal:.0f}" + (f", {kdd} si colchon<{c1:.0f}" if c1 > 0 else "")] = (k0, kdd, c1, dsw, kl, goal)
    for per in PERS:
        for pn, cfg in PROF.items():
            for G in (1400.0, 0.0):
                LO, CL = mats(per, cfg, G)
                for poln, p in POL.items():
                    if pn not in ("WR70Plus+noche (tu prueba)", "WR70Plus+noche+oro WinRate", "Ultra+noche+oro Robust") and not poln.endswith("fijo"): continue
                    o = stats(LO, CL, 3000.0, 2000.0, 0.5, 20, *p, 20)
                    rows.append(dict(per=per, perfil=pn, stop_ganancia=G, politica=poln, **summ(o)))
        print(per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("eval20.csv", index=False)
    S = R.groupby(["perfil", "stop_ganancia", "politica"]).agg(p20=("p20", "mean"), p20_min=("p20", "min"), bust=("bust", "mean"), med=("med", "mean")).reset_index()
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
    print("\nLucid 50K, aprobar en <= 20 dias habiles (promedio IS/C24/REAL, minimo de los 3):")
    print(S.sort_values("p20", ascending=False).head(30).round(1).to_string(index=False))
    print(S[S.politica.str.endswith("fijo")].sort_values(["perfil", "politica"]).round(1).to_string(index=False))
    # 2) account-shape map in 1-contract units (k = 1, no profit stop)
    mrows = []
    for per in PERS:
        for cfg in ("E_WRN", "E_UAN_GR"):
            LO, CL = mats(per, cfg, 0.0, 1)
            for T1 in (500, 750, 1000, 1250, 1500, 2000, 3000):
                for D1 in (500, 750, 1000, 1250, 1500, 2000, 2500, 3000):
                    for cons in (0.0, 0.5):
                        o = stats(LO, CL, float(T1), float(D1), cons, 20, 1, 1, 0.0, 999, 1, 0.0, 20)
                        mrows.append(dict(per=per, cfg=cfg, T1=T1, D1=D1, cons=cons, **summ(o)))
    M = pd.DataFrame(mrows); M.to_csv("eval20_map.csv", index=False)
    for cfg in ("E_WRN", "E_UAN_GR"):
        for cons in (0.0, 0.5):
            g = M[(M.cfg == cfg) & (M.cons == cons)].groupby(["T1", "D1"]).p20.min().unstack()
            print(f"\n{cfg} consistencia {cons}: % que aprueba en <=20 dias (PEOR de IS/C24/REAL), filas = objetivo por contrato, columnas = drawdown por contrato")
            print(g.round(0).to_string())
