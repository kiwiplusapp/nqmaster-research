"""Federico 2026-10-08: 'isn't WR70Plus with 1 contract better in the funded account?'. Same LucidPro 50K lifecycle as lucidpro.py
(eval Ultra+night+gold Robust 4c, no consistency, immediate restarts; funded: buffer 2,100, caps 2,000/2,500, 40% consistency per
payout cycle, payout as soon as possible, 5 payouts) with the funded profile / contracts / daily profit stop varied.
9 tests (history / +1 tick / 1,000 bootstrap years x IS / C24 / REAL). -> funded_wr.csv"""
import sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import lc_lib as L
from acct_life import CFG
from acct_policy import vec
from final_verify_lib import exits
from lucidpro import EU, NIGHT, mats, life2, FEE_PRO
FUND = {"Ultra+noche+oro Robust (con escalones 750/1500)": tuple(L.define("FW_U" + x, CFG[x] + NIGHT) for x in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR")),
        "WR70Plus+noche+oro WinRate (con escalones 750/1500)": tuple(L.define("FW_W" + x, CFG[x] + NIGHT) for x in ("WR_SAFE_GW", "WR_NOB_GW", "WR_FULL_GW")),
        "WR70Plus+noche+oro WinRate (completo siempre)": (L.define("FW_WFULL", CFG["WR_FULL_GW"] + NIGHT),) * 3}
CASES = [(fn, fk, G) for fn in FUND for fk in (1, 2) for G in (0.0, 250.0, 300.0, 400.0, 500.0, 700.0)]
if __name__ == "__main__":
    rows = []
    for per in ("IS", "C24", "REAL"):
        MM = {c: mats(per, EU, 0.0, 0.0, c) for c in (False, True)}; nd = MM[False][0].shape[1]
        IDX = [np.concatenate([np.arange(s, s + 10) % nd for s in np.random.default_rng(31 + q).integers(0, nd, 27)])[:253] for q in range(1000)]
        for fn, fk, G in CASES:
            fs = FUND[fn]; fv = [vec(per, c, 0.0, G / fk if G > 0 else 0.0) for c in fs]; cf = np.array([exits(per, c) for c in fs])
            F0 = np.array([v[0] for v in fv]); F1 = np.array([v[1] for v in fv])
            for test in ("historia", "costo +1 tick", "Monte Carlo"):
                cost = test == "costo +1 tick"; LO, CL = MM[cost]
                f0 = fk * (F0 - (cf if cost else 0)); f1 = fk * (F1 - (cf if cost else 0))
                if test != "Monte Carlo":
                    out = np.zeros((1000, 6)); m = life2(LO, CL, 4, 4, 0.0, 0.0, f0, f1, 1.0, 1, 500.0, 5, FEE_PRO, 252, 3, out); Lr = out[:m]
                else:
                    o1 = np.zeros((2, 6)); Lr = []
                    for idx in IDX:
                        life2(LO[:, idx].copy(), CL[:, idx].copy(), 4, 4, 0.0, 0.0, f0[:, idx].copy(), f1[:, idx].copy(), 1.0, 1, 500.0, 5, FEE_PRO, 252, 252, o1); Lr.append(o1[0].copy())
                    Lr = np.array(Lr)
                rows.append(dict(per=per, fondeada=fn, k=fk, stop=G, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(),
                                 evals=Lr[:, 1].mean(), fondeadas=Lr[:, 2].mean(), quemas=Lr[:, 3].mean(), pagos=Lr[:, 4].mean()))
        print(per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("funded_wr.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60); pd.set_option("display.max_rows", 100)
    S = R.groupby(["fondeada", "k", "stop"]).agg(mes=("mo", "mean"), peor=("mo", "min"), p_anio_neg=("ploss", "max"), quemas=("quemas", "mean"),
                                                 pagos=("pagos", "mean"), fondeadas=("fondeadas", "mean"), evals=("evals", "mean")).round(1)
    print(S.sort_values("mes", ascending=False).to_string())
