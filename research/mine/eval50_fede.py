"""Lucid 50K eval speed and lifecycle for Federico's NT settings vs alternatives (all with the night modules; daily account profit stop
$1,400 for the 50% consistency rule). Federico: WR70Plus, adaptive size 4 -> 1 when the drawdown from the peak exceeds $800 (cushion < $1,200
before the lock), daily loss limit $500. Funded phase for every row: 2 contracts, cushion gating (SAFE < 750 <= NOB < 1500 <= FULL), payout
at $4k. Eval stats over every start day; lifecycle history / +1 tick / 1,000 bootstrap years. -> eval50_fede.csv"""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib
import lc_lib as L
from acct_life import CFG
from acct_policy import vec
from final_verify_lib import exits
@njit(cache=True)
def estats(LO, CL, k0, kdd, c1, out):
    nd = LO.shape[1]; r = 0
    for s in range(nd - 60):
        res, j = L.ev_p(LO, CL, k0, kdd, c1, 999, k0, 0.0, s, nd); out[r, 0] = res; out[r, 1] = j - s + 1; r += 1
    return r
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
EU = L.define("F50_EU", CFG["UA_FULL_GR"] + NIGHT); FU = tuple(L.define("F50_U" + x, CFG[x] + NIGHT) for x in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"))
EW = L.define("F50_EW", CFG["WR_FULL_GW"] + NIGHT); FW = tuple(L.define("F50_W" + x, CFG[x] + NIGHT) for x in ("WR_SAFE_GW", "WR_NOB_GW", "WR_FULL_GW"))
CASES = {  # name: (eval cfg, funded cfgs, k0, kdd, cushion threshold, daily loss limit $)
    "Ultra 2 fijo (recomendado 50K)": (EU, FU, 2, 2, 0.0, 0.0),
    "Ultra 3 fijo": (EU, FU, 3, 3, 0.0, 0.0),
    "WR70Plus 2 fijo": (EW, FW, 2, 2, 0.0, 0.0),
    "WR70Plus 3 fijo": (EW, FW, 3, 3, 0.0, 0.0),
    "WR70Plus 4 fijo": (EW, FW, 4, 4, 0.0, 0.0),
    "WR70Plus 4->1 @$800 + stop diario $500 (tu config)": (EW, FW, 4, 1, 1200.0, 500.0),
    "Ultra 4->1 @$800 + stop diario $500": (EU, FU, 4, 1, 1200.0, 500.0),
    "WR70Plus 3->1 @$800 + stop diario $500": (EW, FW, 3, 1, 1200.0, 500.0)}
rows = []; erows = []
for per in ("IS", "C24", "REAL"):
    for nm, (e, f, k0, kdd, c1, DL) in CASES.items():
        ce = exits(per, e); fv = [vec(per, c, 0.0, 0.0) for c in f]; cf = np.array([exits(per, c) for c in f]); nd = None
        V = {k: vec(per, e, DL / k if DL > 0 else 0.0, 1400.0 / k) for k in (1, 2, 3, 4)}; nd = len(V[1][0])
        for test in ("historia", "costo +1 tick", "Monte Carlo"):
            cst = test == "costo +1 tick"
            LO = np.zeros((5, nd)); CL = np.zeros((5, nd))
            for k in (1, 2, 3, 4): LO[k] = k * (V[k][0] - (ce if cst else 0)); CL[k] = k * (V[k][1] - (ce if cst else 0))
            if test == "historia":
                o = np.zeros((nd, 2)); m = estats(LO, CL, k0, kdd, c1, o); o = o[:m]; ps = o[:, 0] == 1
                erows.append(dict(per=per, caso=nm, pasa=100 * ps.mean(), p15=100 * (ps & (o[:, 1] <= 15)).mean(), p22=100 * (ps & (o[:, 1] <= 22)).mean(),
                                  mediana=np.median(o[ps, 1]) if ps.any() else np.nan, quema=100 * (o[:, 0] == -1).mean()))
            f0 = 2 * (np.array([v[0] for v in fv]) - (cf if cst else 0)); f1 = 2 * (np.array([v[1] for v in fv]) - (cf if cst else 0))
            pol = (k0, kdd, c1, 999, k0, 0.0)
            if test != "Monte Carlo":
                out = np.zeros((1000, 6)); mm = L.life_p(LO, CL, *pol, f0, f1, 1.0, 750.0, 1500.0, 4000.0, 252, 3, out); Lr = out[:mm]
            else:
                o1 = np.zeros((2, 6)); Lr = []
                for q in range(1000):
                    idx = np.concatenate([np.arange(s, s + 10) % nd for s in np.random.default_rng(31 + q).integers(0, nd, 27)])[:253]
                    L.life_p(LO[:, idx].copy(), CL[:, idx].copy(), *pol, f0[:, idx].copy(), f1[:, idx].copy(), 1.0, 750.0, 1500.0, 4000.0, 252, 252, o1); Lr.append(o1[0].copy())
                Lr = np.array(Lr)
            rows.append(dict(per=per, caso=nm, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean()))
    print(per, flush=True)
R = pd.DataFrame(rows); E = pd.DataFrame(erows); R.to_csv("eval50_fede.csv", index=False); pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
S = R.groupby("caso").agg(mes_por_cuenta=("mo", "mean"), peor=("mo", "min"), p_anio_neg=("ploss", "max")).join(E.groupby("caso")[["pasa", "p15", "p22", "mediana", "quema"]].mean())
print(S.round(1).sort_values("mes_por_cuenta", ascending=False).to_string())
