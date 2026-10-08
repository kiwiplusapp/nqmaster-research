"""acct1c step 2: 12-month LIFECYCLE per account slot with the eval at ONE contract and the funded account at k = 1/2/3 contracts.
Slot: buy eval (fee) -> eval at 1 contract (policy below; optional ATR < 1.15 start filter, waiting is free) -> funded (k contracts,
cushion tiers SAFE / NO-BOOST / FULL or full always, payout request threshold X, LucidPro funded daily profit stop G) -> after a
funded bust or 5 payouts a new eval. Lucid Flex 50K (eval 50% consistency + account profit stop; funded no consistency, 50% of
balance up to $2,000 after 5 days >= $150) and LucidPro 50K (eval no consistency; funded buffer 2,100, caps 2,000 / 2,500,
40% per-cycle consistency); optional Flex 100K.
Tests: history (slot start every 3 days), +1 tick per side, 1,000 block-bootstrap years (10-day blocks) on IS / C24 / REAL.
Reports net $/month per slot (fees, eval time, busts and restarts included) and cash per funded-account month. -> acct1c_life.csv"""
import sys, time, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import acct1c_lib as A

FEE = {"Flex50": 105.2, "Pro50": 152.6, "Pro50D": 138.2, "Flex100": 215.0}
ACC = {"Flex50": (3000.0, 2000.0, 0.5, 150.0, 2000.0, 2000.0, 0), "Pro50": (3000.0, 2000.0, 0.0, 0.0, 2000.0, 2500.0, 1),
       "Pro50D": (3000.0, 2000.0, 0.0, 0.0, 2000.0, 2500.0, 1), "Flex100": (6000.0, 3000.0, 0.5, 200.0, 2500.0, 2500.0, 0)}
UE = (A.items(A.UA_FULL, A.GW, 2.0), A.items(A.EST, A.GW, 2.0))
# eval policies: name -> (account, hi items, lo items or None, C, G (account profit stop), DL, ATR filter)
EV = {
    "Flex U/EST C1200 oroWRx2 G1400 ATR": ("Flex50", UE[0], UE[1], 1200.0, 1400.0, 0.0, True),
    "Flex U/EST C1200 oroWRx2 G1400": ("Flex50", UE[0], UE[1], 1200.0, 1400.0, 0.0, False),
    "Flex U/EST C1500 oroWRx2 G1400 ATR": ("Flex50", UE[0], UE[1], 1500.0, 1400.0, 0.0, True),
    "Flex U fijo oroR G1400": ("Flex50", A.items(A.UA_FULL, A.GR, 1.0), None, 0.0, 1400.0, 0.0, False),
    "Flex W fijo oroWR G1400": ("Flex50", A.items(A.WR_FULL, A.GW, 1.0), None, 0.0, 1400.0, 0.0, False),
    "Pro U/EST C1200 oroWRx2 ATR DLL": ("Pro50D", UE[0], UE[1], 1200.0, 0.0, 1200.0, True),
    "Pro U fijo oroR DLL": ("Pro50D", A.items(A.UA_FULL, A.GR, 1.0), None, 0.0, 0.0, 1200.0, False),
    "Pro W fijo oroWR DLL": ("Pro50D", A.items(A.WR_FULL, A.GW, 1.0), None, 0.0, 0.0, 1200.0, False),
    "Flex100 U/EST C1800 oroWRx2 G2800 ATR": ("Flex100", UE[0], UE[1], 1800.0, 2800.0, 0.0, True),
    "Flex100 U fijo oroR G2800": ("Flex100", A.items(A.UA_FULL, A.GR, 1.0), None, 0.0, 2800.0, 0.0, False),
}
UT = (A.items(A.UA_SAFE, A.GR), A.items(A.UA_NOB, A.GR), A.items(A.UA_FULL, A.GR))
WT = (A.items(A.WR_SAFE, A.GW), A.items(A.WR_NOB, A.GW), A.items(A.WR_FULL, A.GW))
FP = {"U escalones": UT, "U completo": (UT[2],) * 3, "W escalones": WT, "W completo": (WT[2],) * 3}


def funded_grid(acc):
    out = []
    ks = (1, 2) if acc == "Flex50" else ((1, 2, 3) if acc.startswith("Pro") else (1, 2, 3))
    for k in ks:
        sc = 1.5 if acc == "Flex100" else 1.0
        for pn in FP:
            cuts = [(0.0, 0.0)] if "completo" in pn else ([(750.0 * sc, 1500.0 * sc)] + ([(1500.0 * sc, 3000.0 * sc)] if k >= 2 else []))
            for c1, c2 in cuts:
                if acc == "Flex50": Xs, Gs = (3000.0, 4000.0, 5000.0), (0.0,)
                elif acc == "Flex100": Xs, Gs = (5000.0, 6000.0), (0.0,)
                else: Xs, Gs = (500.0, 2000.0), {1: (0.0, 250.0, 350.0, 500.0), 2: (0.0, 400.0, 500.0, 700.0), 3: (0.0, 600.0, 750.0, 1000.0)}[k]
                for X, G in itertools.product(Xs, Gs):
                    out.append((pn, k, c1, c2, X, G))
    return out


def run(ev_names=None, nmc=1000):
    rows = []; t0 = time.time()
    ev_names = ev_names or list(EV)
    for per in A.PERS:
        nd = A.ndays(per); atr_ok = A.hiatr(per) < 1.15; allok = np.ones(nd, bool)
        IDX = [A.boot_idx(nd, q, 253, 10, 31) for q in range(nmc)]; hidx = np.arange(nd, dtype=np.int64)
        # funded vectors cache: (prof, k, G, cost) -> (FL, FC)
        FV = {}
        def fvec(pn, k, G, cost):
            key = (pn, k, G, cost)
            if key not in FV:
                L = []; Cc = []
                for it in FP[pn]:
                    lo, cl = A.dv(per, it, 0.0, G / k if G > 0 else 0.0); e = A.exits(per, it) if cost else 0.0
                    L.append(k * (lo - e)); Cc.append(k * (cl - e))
                FV[key] = (np.ascontiguousarray(np.array(L)), np.ascontiguousarray(np.array(Cc)))
            return FV[key]
        for en in ev_names:
            acc, hi, lo, C, Ge, DLe, useatr = EV[en]
            T, D, cons, Q, cap1, cap2, firm = ACC[acc]; fee = FEE[acc]; okst = atr_ok if useatr else allok
            EVV = {}
            for cost in (False, True):
                lH, cH = A.dv(per, hi, DLe, Ge); lL, cL = (lH, cH) if lo is None else A.dv(per, lo, DLe, Ge)
                eH = A.exits(per, hi) if cost else 0.0; eL = (A.exits(per, lo) if lo is not None else eH) if cost else 0.0
                EVV[cost] = (np.ascontiguousarray(np.array([lL - eL, lH - eH])), np.ascontiguousarray(np.array([cL - eL, cH - eH])))
            for pn, k, c1, c2, X, G in funded_grid(acc):
                for test in ("historia", "costo +1 tick", "Monte Carlo"):
                    cost = test == "costo +1 tick"; EL, EC = EVV[cost]; FL, FC = fvec(pn, k, G, cost)
                    if test != "Monte Carlo":
                        out = np.zeros((nd, 9)); m = A.life(EL, EC, C, T, D, cons, okst, fee, FL, FC, c1, c2, firm, X, Q, cap1, cap2, hidx, 252, 3, out); Lr = out[:m]
                    else:
                        Lr = np.zeros((nmc, 9)); o1 = np.zeros((2, 9))
                        for q, idx in enumerate(IDX):
                            A.life(EL, EC, C, T, D, cons, okst, fee, FL, FC, c1, c2, firm, X, Q, cap1, cap2, idx, 252, 252, o1); Lr[q] = o1[0]
                    fm = Lr[:, 6].sum() / 21.0
                    rows.append(dict(per=per, eval=en, acc=acc, fprof=pn, k=k, c1=c1, c2=c2, X=X, G=G, test=test,
                                     mo=Lr[:, 0].mean() / 12, p10=np.percentile(Lr[:, 0], 10) / 12, ploss=100 * (Lr[:, 0] < 0).mean(),
                                     evals=Lr[:, 1].mean(), passes=Lr[:, 2].mean(), fbust=Lr[:, 3].mean(), payouts=Lr[:, 4].mean(),
                                     eval_days=Lr[:, 5].mean(), funded_share=100 * Lr[:, 6].mean() / 252, cash_per_funded_month=Lr[:, 7].sum() / max(fm, 1e-9),
                                     wait_days=Lr[:, 8].mean()))
            print(per, en, round(time.time() - t0), flush=True)
    return pd.DataFrame(rows)


def summary(R):
    keys = ["eval", "acc", "fprof", "k", "c1", "c2", "X", "G"]
    S = R.groupby(keys).agg(mean9=("mo", "mean"), min9=("mo", "min"), p10=("p10", "mean"), ploss=("ploss", "max"),
                            cash_fm=("cash_per_funded_month", "mean"), cash_fm_min=("cash_per_funded_month", "min"),
                            fbust=("fbust", "mean"), payouts=("payouts", "mean"), evals=("evals", "mean"), passes=("passes", "mean"),
                            eval_days=("eval_days", "mean"), funded_share=("funded_share", "mean")).round(1).reset_index()
    return S


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if a in EV] or None
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else ""
    R = run(names); R.to_csv(f"acct1c_life{tag}.csv", index=False)
    S = summary(R); S.to_csv(f"acct1c_life{tag}_summary.csv", index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_rows", 300); pd.set_option("display.max_colwidth", 40)
    print(S.sort_values("mean9", ascending=False).head(60).to_string(index=False))
