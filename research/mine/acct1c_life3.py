"""acct1c step 4 (Lucid Flex 50K): funded account with NQMaster's EXISTING AdaptiveSize (SizeHigh 2 while the strategy's P&L is
less than SizeDownDrawdown below its peak since go-live, SizeLow 1 otherwise) + GoldMaster Robust at a fixed 1 or 2 MGC, after
an eval at ONE contract. SizeDownDrawdown = 1e9 -> fixed 2 (reference), 0 -> fixed 1. Decision at the start of each day (NT
switches after each closed trade: slightly more defensive than modelled). 9 tests. -> acct1c_life3.csv, acct1c_life3_summary.csv"""
import sys, time, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import acct1c_lib as A
from acct1c_life import FEE, ACC
from acct1c_life2 import EV as EV2
from acct1c_life import summary

EVS = ["Flex U/EST C1200 oroWRx2 G1400", "Flex U/EST C900 oroWRx2 G1400", "Flex U fijo oroR G1400", "Flex W fijo oroWR G1400"]
SS = (0.0, 300.0, 500.0, 700.0, 1000.0, 1500.0, 1e9)
GOLDK = (1.0, 2.0)
XS = (4000.0, 5000.0)


def run(nmc=1000):
    rows = []; t0 = time.time()
    for per in A.PERS:
        nd = A.ndays(per); allok = np.ones(nd, bool)
        IDX = [A.boot_idx(nd, q, 253, 10, 31) for q in range(nmc)]; hidx = np.arange(nd, dtype=np.int64)
        nq1 = A.items(A.UA_FULL); _, nqc = A.dv(per, nq1); enq = A.exits(per, nq1)
        FV = {}
        for g in GOLDK:
            for cost in (False, True):
                L = []; Cc = []; N = []
                for k in (1.0, 2.0):
                    it = A.items(A.UA_FULL, A.GR, g, k); lo, cl = A.dv(per, it); e = A.exits(per, it) if cost else 0.0
                    L.append(lo - e); Cc.append(cl - e); N.append(k * (nqc - (enq if cost else 0.0)))
                FV[(g, cost)] = tuple(np.ascontiguousarray(np.array(v)) for v in (L, Cc, N))
        for en in EVS:
            acc, hi, lo, C, Ge, DLe, useatr = EV2[en]
            T, D, cons, Q, cap1, cap2, firm = ACC[acc]; fee = FEE[acc]
            EVV = {}
            for cost in (False, True):
                lH, cH = A.dv(per, hi, DLe, Ge); lL, cL = (lH, cH) if lo is None else A.dv(per, lo, DLe, Ge)
                eH = A.exits(per, hi) if cost else 0.0; eL = (A.exits(per, lo) if lo is not None else eH) if cost else 0.0
                EVV[cost] = (np.ascontiguousarray(np.array([lL - eL, lH - eH])), np.ascontiguousarray(np.array([cL - eL, cH - eH])))
            for g, S, X in itertools.product(GOLDK, SS, XS):
                for test in ("historia", "costo +1 tick", "Monte Carlo"):
                    cost = test == "costo +1 tick"; EL, EC = EVV[cost]; FL, FC, NQ = FV[(g, cost)]
                    if test != "Monte Carlo":
                        out = np.zeros((nd, 9)); m = A.life_dd(EL, EC, C, T, D, cons, allok, fee, FL, FC, NQ, S, X, Q, cap1, hidx, 252, 3, out); Lr = out[:m]
                    else:
                        Lr = np.zeros((nmc, 9)); o1 = np.zeros((2, 9))
                        for q, idx in enumerate(IDX):
                            A.life_dd(EL, EC, C, T, D, cons, allok, fee, FL, FC, NQ, S, X, Q, cap1, idx, 252, 252, o1); Lr[q] = o1[0]
                    fm = Lr[:, 6].sum() / 21.0
                    fn = "fijo 1" if S == 0 else ("fijo 2" if S > 1e8 else f"Adaptive 2->1 DD {S:.0f}")
                    rows.append(dict(per=per, eval=en, acc=acc, fprof=f"NQ {fn} + oro Robust x{g:.0f}", k=2, c1=S, c2=g, X=X, G=0.0, test=test,
                                     mo=Lr[:, 0].mean() / 12, p10=np.percentile(Lr[:, 0], 10) / 12, ploss=100 * (Lr[:, 0] < 0).mean(),
                                     evals=Lr[:, 1].mean(), passes=Lr[:, 2].mean(), fbust=Lr[:, 3].mean(), payouts=Lr[:, 4].mean(),
                                     eval_days=Lr[:, 5].mean(), funded_share=100 * Lr[:, 6].mean() / 252, cash_per_funded_month=Lr[:, 7].sum() / max(fm, 1e-9),
                                     wait_days=Lr[:, 8].mean()))
            print(per, en, round(time.time() - t0), flush=True)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    R = run(); R.to_csv("acct1c_life3.csv", index=False)
    S = summary(R); S.to_csv("acct1c_life3_summary.csv", index=False)
    pd.set_option("display.width", 320); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 50)
    for ev in S["eval"].unique():
        print("\n##", ev); print(S[S["eval"] == ev].sort_values("mean9", ascending=False).head(14).drop(columns=["eval", "acc", "G", "k"]).to_string(index=False))
