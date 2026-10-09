"""acct1c step 1: the EVALUATION at ONE contract (1 MNQ per module, gold 1-2 MGC) on Lucid Flex 50K / LucidPro 50K / Flex 100K.
Eval policies (gear 1 = fast set while cushion >= C, gear 0 = stable set below; C = 0 -> fixed set):
  U fixed       : Ultra(ampliado)+night + gold Robust x1  (or gold WinRate x2)
  W fixed       : WR70Plus+night(+LATE15) + gold WinRate x1 (or x2)
  U/EST Cxxxx   : Ultra+night above C, Estable below (NQMaster EvalSafeSet=Estable), gold WinRate x2 / Robust x1 / WinRate x1
  W/WEST Cxxxx  : WR70Plus above C, WR70Plus-Estable below (CRT11, ORB90, MSEQ, REV06, VOLB trend 0.5R, VW13), gold WinRate x2
Firms: Flex 50K (target 3,000, EOD trailing 2,000 locking +100, best day <= 50%, account profit stop G 0/700/1000/1400),
       Pro 50K (no consistency; soft DLL 1,200 or none), Flex 100K (6,000 / 3,000, 50%).
Tests: history (every start with >= 150 days left), +1 tick per side, block bootstrap (200 synthetic 504-day paths of 10-day
blocks, all starts pooled); starts: all days / ATR < 1.15 days. -> acct1c_eval.csv"""
import sys, time, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import acct1c_lib as A

EVALS = {
    "U fijo + oro Robust x1": (A.items(A.UA_FULL, A.GR, 1.0), None, 0.0),
    "U fijo + oro WinRate x2": (A.items(A.UA_FULL, A.GW, 2.0), None, 0.0),
    "W fijo + oro WinRate x1": (A.items(A.WR_FULL, A.GW, 1.0), None, 0.0),
    "W fijo + oro WinRate x2": (A.items(A.WR_FULL, A.GW, 2.0), None, 0.0),
    "EST siempre + oro WinRate x2": (A.items(A.EST, A.GW, 2.0), None, 0.0),
}
for C in (900.0, 1200.0, 1500.0, 1800.0):
    EVALS[f"U/EST C{C:.0f} + oro WinRate x2"] = (A.items(A.UA_FULL, A.GW, 2.0), A.items(A.EST, A.GW, 2.0), C)
for C in (1200.0, 1500.0):
    EVALS[f"U/EST C{C:.0f} + oro Robust x1"] = (A.items(A.UA_FULL, A.GR, 1.0), A.items(A.EST, A.GR, 1.0), C)
    EVALS[f"U/EST C{C:.0f} + oro WinRate x1"] = (A.items(A.UA_FULL, A.GW, 1.0), A.items(A.EST, A.GW, 1.0), C)
    EVALS[f"W/WEST C{C:.0f} + oro WinRate x2"] = (A.items(A.WR_FULL, A.GW, 2.0), A.items(A.WEST, A.GW, 2.0), C)
# (firm, T, D, cons, G, DL)
FIRMS = [("Flex50", 3000.0, 2000.0, 0.5, G, 0.0) for G in (0.0, 700.0, 1000.0, 1400.0)] + \
        [("Pro50", 3000.0, 2000.0, 0.0, 0.0, 0.0), ("Pro50 DLL1200", 3000.0, 2000.0, 0.0, 0.0, 1200.0)] + \
        [("Flex100", 6000.0, 3000.0, 0.5, G, 0.0) for G in (0.0, 2800.0)]
NB = 200


def gears(per, hi, lo, G, DL, cost):
    lH, cH = A.dv(per, hi, DL, G)
    if lo is None: lL, cL = lH, cH
    else: lL, cL = A.dv(per, lo, DL, G)
    EL = np.array([lL, lH]); EC = np.array([cL, cH])
    if cost:
        eH = A.exits(per, hi); eL = eH if lo is None else A.exits(per, lo)
        EL = EL - np.array([eL, eH]); EC = EC - np.array([eL, eH])
    return np.ascontiguousarray(EL), np.ascontiguousarray(EC)


def run():
    rows = []; t0 = time.time()
    for per in A.PERS:
        nd = A.ndays(per); atr_ok = A.hiatr(per) < 1.15
        IDX = [A.boot_idx(nd, q, 504, 10, 77) for q in range(NB)]
        for en, (hi, lo, C) in EVALS.items():
            for firm, T, D, cons, G, DL in FIRMS:
                if firm == "Flex100" and not (en.startswith("U fijo") or en.startswith("W fijo") or en.startswith("U/EST C1200 + oro WinRate x2") or en.startswith("U/EST C1800 + oro WinRate x2")): continue
                Ce = C * (1.5 if firm == "Flex100" else 1.0)
                for test in ("historia", "costo +1 tick", "bootstrap"):
                    EL, EC = gears(per, hi, lo, G, DL, test == "costo +1 tick")
                    if test != "bootstrap":
                        idx = np.arange(nd, dtype=np.int64); out = np.zeros((nd, 2)); m = A.eval_all(EL, EC, Ce, T, D, cons, idx, 150, out); o = out[:m]
                        fo = np.zeros((nd, 4)); fm = A.funded_within(EL, EC, Ce, T, D, cons, idx, 33, fo); f33 = 100 * fo[:fm, 1].mean()
                        fo2 = np.zeros((nd, 4)); fm2 = A.funded_within(EL, EC, Ce, T, D, cons, idx, 22, fo2); f22 = 100 * fo2[:fm2, 1].mean()
                        for st, mask in (("todos", None), ("ATR<1.15", atr_ok[:m])):
                            rows.append(dict(per=per, eval=en, firm=firm, G=G, test=test, start=st, fund22=f22, fund33=f33, **A.esumm(o, mask)))
                    else:
                        O = []; MK = []
                        for idx in IDX:
                            out = np.zeros((504, 2)); m = A.eval_all(EL, EC, Ce, T, D, cons, idx, 150, out); O.append(out[:m].copy()); MK.append(atr_ok[idx[:m]])
                        O = np.concatenate(O); MK = np.concatenate(MK)
                        for st, mask in (("todos", None), ("ATR<1.15", MK)):
                            rows.append(dict(per=per, eval=en, firm=firm, G=G, test=test, start=st, fund22=np.nan, fund33=np.nan, **A.esumm(O, mask)))
            print(per, en, round(time.time() - t0), flush=True)
    R = pd.DataFrame(rows); R.to_csv("acct1c_eval.csv", index=False); return R


if __name__ == "__main__":
    R = run()
    pd.set_option("display.width", 300); pd.set_option("display.max_rows", 500); pd.set_option("display.max_colwidth", 40)
    S = R.groupby(["eval", "firm", "G", "start"]).agg(pass_mean=("pass_pct", "mean"), pass_min=("pass_pct", "min"), med=("med_days", "mean"),
                                                      med_max=("med_days", "max"), p33=("p33", "mean"), p22=("p22", "mean"), f33=("fund33", "mean")).round(1).reset_index()
    print(S.sort_values("pass_min", ascending=False).to_string(index=False))
