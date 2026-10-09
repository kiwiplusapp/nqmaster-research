"""MFFU Rapid EOD 50K lifecycle under a forward edge haircut (audit_ report: realistic = 35% of the edge removed): every day's P&L
(eval and funded, every gear) is reduced by h x the mean daily P&L of that set in the period. Plus Lucid Flex 50K 1c/1c for reference
is in acct1c_*. -> mffu_haircut.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
import acct1c_lib as A
from mffu_rapid import EV, FUND, life_m, FEE, eval_stats
CASES = [("Estable C1200 (Ultra/Estable + oro WR x2) 1c", "1c Ultra", 4100.0), ("Estable C1200 (Ultra/Estable + oro WR x2) 1c", "Ultra 1c -> 2c desde colchon 3000", 6100.0),
         ("Ultra fijo 1c + oro Robust", "1c Ultra", 4100.0)]
if __name__ == "__main__":
    rows = []; nmc = 600
    for per in A.PERS:
        nd = A.ndays(per); IDX = [A.boot_idx(nd, q, 253, 10, 31) for q in range(nmc)]; hidx = np.arange(nd, dtype=np.int64)
        for en, fn, B in CASES:
            hi, lo, C, G = EV[en]; tiers, c1, c2 = FUND[fn]
            for h in (0.0, 0.25, 0.35, 0.5):
                for cost in (False, True):
                    lH, cH = A.dv(per, hi, 0.0, G); lL, cL = (lH, cH) if lo is None else A.dv(per, lo, 0.0, G)
                    eH = A.exits(per, hi) if cost else 0.0; eL = (A.exits(per, lo) if lo is not None else eH) if cost else 0.0
                    mH = h * cH.mean(); mL = h * cL.mean()
                    EL = np.ascontiguousarray(np.array([lL - eL - mL, lH - eH - mH])); EC = np.ascontiguousarray(np.array([cL - eL - mL, cH - eH - mH]))
                    L = []; Cc = []
                    for it, k in tiers:
                        l_, c_ = A.dv(per, it); e = A.exits(per, it) if cost else 0.0; m_ = h * c_.mean()
                        L.append(k * (l_ - e - m_)); Cc.append(k * (c_ - e - m_))
                    FL = np.ascontiguousarray(np.array(L)); FC = np.ascontiguousarray(np.array(Cc))
                    tests = ("costo +1 tick",) if cost else ("historia", "Monte Carlo")
                    for test in tests:
                        if test != "Monte Carlo":
                            out = np.zeros((nd, 8)); m = life_m(EL, EC, C, 3000.0, 2000.0, 0.3, 4, FEE, FL, FC, c1, c2, B, 0, hidx, 252, 3, out); Lr = out[:m]
                            o = np.zeros((nd, 2)); mm = eval_stats(EL, EC, C, 3000.0, 2000.0, 0.3, 4, hidx, 60, o); es = A.esumm(o[:mm])
                        else:
                            Lr = np.zeros((nmc, 8)); o1 = np.zeros((2, 8)); es = {}
                            for q, idx in enumerate(IDX):
                                life_m(EL, EC, C, 3000.0, 2000.0, 0.3, 4, FEE, FL, FC, c1, c2, B, 0, idx, 252, 252, o1); Lr[q] = o1[0]
                        fm = Lr[:, 6].sum() / 21.0
                        rows.append(dict(per=per, eval=en, fprof=fn, B=B, haircut=h, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(),
                                         fbust=Lr[:, 3].mean(), cash_fm=Lr[:, 7].sum() / max(fm, 1e-9), pass_pct=es.get("pass_pct", np.nan), med_days=es.get("med_days", np.nan)))
            print(per, en, fn, flush=True)
    R = pd.DataFrame(rows); R.to_csv("mffu_haircut.csv", index=False); pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
    S = R.groupby(["eval", "fprof", "haircut"]).agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), cash_fm=("cash_fm", "mean"), fbust=("fbust", "mean"),
                                                   pass_hist=("pass_pct", "mean"), med_days=("med_days", "mean")).round(1)
    print(S.to_string())
