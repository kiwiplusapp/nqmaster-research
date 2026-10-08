"""acct1c step 3 (Lucid Flex 50K): eval at ONE contract (high-pass Estable gating at C900/C1200/C1500, Ultra / WR70Plus fixed) x
funded variants incl. a cushion-based size-up (1 contract until the cushion over the EOD-trailing threshold reaches c2, then 2):
tiers = [(set, contracts) below c1, (set, contracts) c1..c2, (set, contracts) >= c2]. Flex funded max 20 micros -> at most 2 base
contracts (p99 at 1 contract ~7-8 micros, max ~11). Same 9 tests as acct1c_life.py. -> acct1c_life2.csv, acct1c_life2_summary.csv"""
import sys, time, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import acct1c_lib as A
from acct1c_life import FEE, ACC, UE, UT, WT, summary

EV = {
    "Flex U/EST C900 oroWRx2 G1400": ("Flex50", UE[0], UE[1], 900.0, 1400.0, 0.0, False),
    "Flex U/EST C1200 oroWRx2 G1400": ("Flex50", UE[0], UE[1], 1200.0, 1400.0, 0.0, False),
    "Flex U/EST C1200 oroWRx2 G1400 ATR": ("Flex50", UE[0], UE[1], 1200.0, 1400.0, 0.0, True),
    "Flex U/EST C1500 oroWRx2 G1400": ("Flex50", UE[0], UE[1], 1500.0, 1400.0, 0.0, False),
    "Flex U fijo oroR G1400": ("Flex50", A.items(A.UA_FULL, A.GR, 1.0), None, 0.0, 1400.0, 0.0, False),
    "Flex W fijo oroWR G1400": ("Flex50", A.items(A.WR_FULL, A.GW, 1.0), None, 0.0, 1400.0, 0.0, False),
}
S_, N_, F_ = UT; WS, WN, WF = WT
# funded: name -> ((items, k) x 3 tiers, c1, c2)
FUND = {
    "1c Ultra completo": (((F_, 1), (F_, 1), (F_, 1)), 0.0, 0.0),
    "1c Ultra escalones 750/1500": (((S_, 1), (N_, 1), (F_, 1)), 750.0, 1500.0),
    "2c Ultra completo": (((F_, 2), (F_, 2), (F_, 2)), 0.0, 0.0),
    "2c Ultra escalones 750/1500": (((S_, 2), (N_, 2), (F_, 2)), 750.0, 1500.0),
    "2c WR70 escalones 1500/3000": (((WS, 2), (WN, 2), (WF, 2)), 1500.0, 3000.0),
}
for c2 in (1500.0, 2100.0, 2600.0, 3100.0):
    FUND[f"Ultra 1c -> 2c desde colchon {c2:.0f}"] = (((F_, 1), (F_, 1), (F_, 2)), 0.0, c2)
    FUND[f"Ultra SAFE1c<750, 1c -> 2c desde {c2:.0f}"] = (((S_, 1), (F_, 1), (F_, 2)), 750.0, c2)
    FUND[f"WR70 1c -> Ultra 2c desde {c2:.0f}"] = (((WF, 1), (WF, 1), (F_, 2)), 0.0, c2)
XS = (3000.0, 4000.0, 5000.0)


def run(nmc=1000):
    rows = []; t0 = time.time()
    for per in A.PERS:
        nd = A.ndays(per); atr_ok = A.hiatr(per) < 1.15; allok = np.ones(nd, bool)
        IDX = [A.boot_idx(nd, q, 253, 10, 31) for q in range(nmc)]; hidx = np.arange(nd, dtype=np.int64)
        FV = {}
        for fn, (tiers, c1, c2) in FUND.items():
            for cost in (False, True):
                L = []; Cc = []
                for it, k in tiers:
                    lo, cl = A.dv(per, it); e = A.exits(per, it) if cost else 0.0
                    L.append(k * (lo - e)); Cc.append(k * (cl - e))
                FV[(fn, cost)] = (np.ascontiguousarray(np.array(L)), np.ascontiguousarray(np.array(Cc)))
        for en, (acc, hi, lo, C, Ge, DLe, useatr) in EV.items():
            T, D, cons, Q, cap1, cap2, firm = ACC[acc]; fee = FEE[acc]; okst = atr_ok if useatr else allok
            EVV = {}
            for cost in (False, True):
                lH, cH = A.dv(per, hi, DLe, Ge); lL, cL = (lH, cH) if lo is None else A.dv(per, lo, DLe, Ge)
                eH = A.exits(per, hi) if cost else 0.0; eL = (A.exits(per, lo) if lo is not None else eH) if cost else 0.0
                EVV[cost] = (np.ascontiguousarray(np.array([lL - eL, lH - eH])), np.ascontiguousarray(np.array([cL - eL, cH - eH])))
            for (fn, (tiers, c1, c2)), X in itertools.product(FUND.items(), XS):
                for test in ("historia", "costo +1 tick", "Monte Carlo"):
                    cost = test == "costo +1 tick"; EL, EC = EVV[cost]; FL, FC = FV[(fn, cost)]
                    if test != "Monte Carlo":
                        out = np.zeros((nd, 9)); m = A.life(EL, EC, C, T, D, cons, okst, fee, FL, FC, c1, c2, firm, X, Q, cap1, cap2, hidx, 252, 3, out); Lr = out[:m]
                    else:
                        Lr = np.zeros((nmc, 9)); o1 = np.zeros((2, 9))
                        for q, idx in enumerate(IDX):
                            A.life(EL, EC, C, T, D, cons, okst, fee, FL, FC, c1, c2, firm, X, Q, cap1, cap2, idx, 252, 252, o1); Lr[q] = o1[0]
                    fm = Lr[:, 6].sum() / 21.0
                    rows.append(dict(per=per, eval=en, acc=acc, fprof=fn, k=max(k for _, k in tiers), c1=c1, c2=c2, X=X, G=0.0, test=test,
                                     mo=Lr[:, 0].mean() / 12, p10=np.percentile(Lr[:, 0], 10) / 12, ploss=100 * (Lr[:, 0] < 0).mean(),
                                     evals=Lr[:, 1].mean(), passes=Lr[:, 2].mean(), fbust=Lr[:, 3].mean(), payouts=Lr[:, 4].mean(),
                                     eval_days=Lr[:, 5].mean(), funded_share=100 * Lr[:, 6].mean() / 252, cash_per_funded_month=Lr[:, 7].sum() / max(fm, 1e-9),
                                     wait_days=Lr[:, 8].mean()))
            print(per, en, round(time.time() - t0), flush=True)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    R = run(); R.to_csv("acct1c_life2.csv", index=False)
    S = summary(R); S.to_csv("acct1c_life2_summary.csv", index=False)
    pd.set_option("display.width", 320); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 45)
    for ev in S["eval"].unique():
        print("\n##", ev); print(S[S["eval"] == ev].sort_values("mean9", ascending=False).head(12).drop(columns=["eval", "acc", "G"]).to_string(index=False))
