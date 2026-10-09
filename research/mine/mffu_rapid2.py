"""mffu_rapid.py follow-up: buffer B beyond 6,100 (grid edge), news blackout haircut and a 'moved to live after N payouts' cap.
Funded variants limited to the best of mffu_rapid.py. -> mffu_rapid2.csv"""
import sys, time, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import acct1c_lib as A
from mffu_rapid import EV, FUND, life_m, FEE
SEL_F = ["1c Ultra", "Ultra 1c -> 2c desde colchon 3000", "Ultra 1c -> 2c desde colchon 4000", "2c Ultra escalones 750/1500", "1c WR70Plus"]
SEL_E = ["Estable C1200 (Ultra/Estable + oro WR x2) 1c", "Ultra fijo 1c + oro Robust", "WR70Plus fijo 1c + oro WinRate"]
BUF = (5100.0, 6100.0, 7100.0, 8100.0, 10100.0); NP = (0, 12)
if __name__ == "__main__":
    rows = []; t0 = time.time(); nmc = 1000
    for per in A.PERS:
        nd = A.ndays(per); IDX = [A.boot_idx(nd, q, 253, 10, 31) for q in range(nmc)]; hidx = np.arange(nd, dtype=np.int64)
        for en in SEL_E:
            hi, lo, C, G = EV[en]
            for fn in SEL_F:
                tiers, c1, c2 = FUND[fn]
                for cost in (False, True):
                    lH, cH = A.dv(per, hi, 0.0, G); lL, cL = (lH, cH) if lo is None else A.dv(per, lo, 0.0, G)
                    eH = A.exits(per, hi) if cost else 0.0; eL = (A.exits(per, lo) if lo is not None else eH) if cost else 0.0
                    EL = np.ascontiguousarray(np.array([lL - eL, lH - eH])); EC = np.ascontiguousarray(np.array([cL - eL, cH - eH]))
                    L = []; Cc = []
                    for it, k in tiers:
                        l_, c_ = A.dv(per, it); e = A.exits(per, it) if cost else 0.0; L.append(k * (l_ - e)); Cc.append(k * (c_ - e))
                    FL = np.ascontiguousarray(np.array(L)); FC = np.ascontiguousarray(np.array(Cc))
                    for B, npm in itertools.product(BUF, NP):
                        tests = ("costo +1 tick",) if cost else ("historia", "Monte Carlo")
                        for test in tests:
                            if test != "Monte Carlo":
                                out = np.zeros((nd, 8)); m = life_m(EL, EC, C, 3000.0, 2000.0, 0.3, 4, FEE, FL, FC, c1, c2, B, npm, hidx, 252, 3, out); Lr = out[:m]
                            else:
                                Lr = np.zeros((nmc, 8)); o1 = np.zeros((2, 8))
                                for q, idx in enumerate(IDX):
                                    life_m(EL, EC, C, 3000.0, 2000.0, 0.3, 4, FEE, FL, FC, c1, c2, B, npm, idx, 252, 252, o1); Lr[q] = o1[0]
                            fm = Lr[:, 6].sum() / 21.0
                            rows.append(dict(per=per, eval=en, fprof=fn, B=B, npmax=npm, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(),
                                             evals=Lr[:, 1].mean(), fbust=Lr[:, 3].mean(), payouts=Lr[:, 4].mean(), cash_fm=Lr[:, 7].sum() / max(fm, 1e-9),
                                             funded_share=100 * Lr[:, 6].mean() / 252))
            print(per, en, round(time.time() - t0), flush=True)
    R = pd.DataFrame(rows); R.to_csv("mffu_rapid2.csv", index=False)
    S = R.groupby(["eval", "fprof", "B", "npmax"]).agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), cash_fm=("cash_fm", "mean"),
                                                       fbust=("fbust", "mean"), payouts=("payouts", "mean"), evals=("evals", "mean")).round(0).reset_index()
    S.to_csv("mffu_rapid2_summary.csv", index=False); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    print(S.sort_values(["eval", "fprof", "npmax", "B"]).to_string(index=False))
