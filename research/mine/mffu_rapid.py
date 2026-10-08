"""MyFundedFutures (MFFU) Rapid EOD 50K, the best-paying bot-friendly account found by the 2026-10-08 prop-firm survey
(help.myfundedfutures.com, Aug-Sep 2026): $157 one-time eval, target 3,000, 2,000 EOD trailing drawdown that locks at start + 100,
no daily loss limit, 30% consistency (best day <= 30% of total profit, soft: keep trading), minimum 4 trading days, 30 micros.
Funded: 2,000 EOD trailing locking at +100 once the EOD high reaches 2,100, no consistency, no DLL, daily payouts of everything above
the 2,100 buffer (min 500, NO cap), 90% split, no payout limit (live transfer is discretionary or on a $10k day; not modelled),
max 3 Rapid accounts. News: flat and no orders +-2 min around T1 releases (FOMC is skipped already; CPI/NFP 08:30 not modelled here).
Policy studied: keep a buffer B above start (withdraw only the excess over B, >= 500), cushion tiers, 1 or 2 contracts.
Exact dense grids via acct1c_lib (9 tests: history / +1 tick / 1,000 bootstrap years x IS / C24 / REAL). -> mffu_rapid.csv"""
import sys, time, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import acct1c_lib as A
from acct1c_life import UE, UT, WT

FEE = 157.0


@njit(cache=True)
def ev_m(EL, EC, C, T, D, cons, mind, idx, s, n):
    eq = 0.0; pk = 0.0; best = -1e9; d = s
    while d < n:
        t = idx[d]
        thr = 100.0 if pk >= D + 100.0 else pk - D
        g = 1 if eq - thr >= C else 0
        if eq + EL[g, t] <= thr: return -1, d
        c = EC[g, t]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= T and d - s + 1 >= mind and (cons <= 0.0 or best <= cons * eq): return 1, d
        d += 1
    return 0, n


@njit(cache=True)
def fu_m(FL, FC, c1, c2, idx, start, n, B, D, npmax):
    """MFFU Rapid funded: withdraw bal - B whenever >= 500 (B >= 2,100 buffer), 90% split; returns (cash, payouts, status, last pos)"""
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; d = start
    while d < n:
        t = idx[d]
        thr = 100.0 if pk >= D + 100.0 else pk - D
        cu = bal - thr; j = 0 if cu < c1 else (1 if cu < c2 else 2)
        if bal + FL[j, t] <= thr: return cash, m, -1, d
        bal += FC[j, t]
        if bal > pk: pk = bal
        if bal - B >= 500.0:
            amt = bal - B; bal -= amt; cash += 0.9 * amt; m += 1
            if npmax > 0 and m >= npmax: return cash, m, 1, d
        d += 1
    return cash, m, 0, n


@njit(cache=True)
def life_m(EL, EC, C, T, D, cons, mind, fee, FL, FC, c1, c2, B, npmax, idx, H, step, out):
    N = len(idx); r = 0
    for s in range(0, N - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0; dtp = 0.0; fdays = 0.0
        while i < end:
            fees += fee; nev += 1
            res, j = ev_m(EL, EC, C, T, D, cons, mind, idx, i, end)
            if res != 1:
                i = j + 1; continue
            npass += 1; dtp += j - i + 1
            c, m, st, j2 = fu_m(FL, FC, c1, c2, idx, j + 1, end, B, D, npmax)
            fdays += min(j2, end - 1) - j; cash += c; npay += m; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb; out[r, 4] = npay
        out[r, 5] = dtp / max(npass, 1); out[r, 6] = fdays; out[r, 7] = cash; r += 1
    return r


@njit(cache=True)
def eval_stats(EL, EC, C, T, D, cons, mind, idx, nmin, out):
    N = len(idx); m = N - nmin
    for s in range(m):
        r, j = ev_m(EL, EC, C, T, D, cons, mind, idx, s, N); out[s, 0] = r; out[s, 1] = j - s + 1
    return m


EV = {  # name: (hi items, lo items or None, C, account daily profit stop G)
    "Estable C1200 (Ultra/Estable + oro WR x2) 1c": (UE[0], UE[1], 1200.0, 800.0),
    "Estable C1200 1c, sin stop": (UE[0], UE[1], 1200.0, 0.0),
    "Ultra fijo 1c + oro Robust": (A.items(A.UA_FULL, A.GR), None, 0.0, 800.0),
    "WR70Plus fijo 1c + oro WinRate": (A.items(A.WR_FULL, A.GW), None, 0.0, 800.0),
}
S_, N_, F_ = UT; WS, WN, WF = WT
FUND = {
    "1c Ultra": (((F_, 1), (F_, 1), (F_, 1)), 0.0, 0.0),
    "1c Ultra escalones 750/1500": (((S_, 1), (N_, 1), (F_, 1)), 750.0, 1500.0),
    "1c WR70Plus": (((WF, 1), (WF, 1), (WF, 1)), 0.0, 0.0),
    "2c Ultra": (((F_, 2), (F_, 2), (F_, 2)), 0.0, 0.0),
    "2c Ultra escalones 750/1500": (((S_, 2), (N_, 2), (F_, 2)), 750.0, 1500.0),
    "Ultra 1c -> 2c desde colchon 3000": (((F_, 1), (F_, 1), (F_, 2)), 0.0, 3000.0),
    "Ultra 1c -> 2c desde colchon 4000": (((F_, 1), (F_, 1), (F_, 2)), 0.0, 4000.0),
}
BUF = (2100.0, 3100.0, 4100.0, 5100.0, 6100.0)


def run(nmc=1000):
    rows = []; erows = []; t0 = time.time()
    for per in A.PERS:
        nd = A.ndays(per); IDX = [A.boot_idx(nd, q, 253, 10, 31) for q in range(nmc)]; hidx = np.arange(nd, dtype=np.int64)
        FV = {}
        for fn, (tiers, c1, c2) in FUND.items():
            for cost in (False, True):
                L = []; Cc = []
                for it, k in tiers:
                    lo, cl = A.dv(per, it); e = A.exits(per, it) if cost else 0.0
                    L.append(k * (lo - e)); Cc.append(k * (cl - e))
                FV[(fn, cost)] = (np.ascontiguousarray(np.array(L)), np.ascontiguousarray(np.array(Cc)))
        for en, (hi, lo, C, G) in EV.items():
            EVV = {}
            for cost in (False, True):
                lH, cH = A.dv(per, hi, 0.0, G); lL, cL = (lH, cH) if lo is None else A.dv(per, lo, 0.0, G)
                eH = A.exits(per, hi) if cost else 0.0; eL = (A.exits(per, lo) if lo is not None else eH) if cost else 0.0
                EVV[cost] = (np.ascontiguousarray(np.array([lL - eL, lH - eH])), np.ascontiguousarray(np.array([cL - eL, cH - eH])))
            for test in ("historia", "costo +1 tick"):
                EL, EC = EVV[test != "historia"]; o = np.zeros((nd, 2)); m = eval_stats(EL, EC, C, 3000.0, 2000.0, 0.3, 4, hidx, 60, o)
                erows.append(dict(per=per, eval=en, test=test, **A.esumm(o[:m])))
            EL, EC = EVV[False]; bs = []
            for idx in IDX[:300]:
                o = np.zeros((253, 2)); m = eval_stats(EL, EC, C, 3000.0, 2000.0, 0.3, 4, idx, 60, o); bs.append(A.esumm(o[:m])["pass_pct"])
            erows.append(dict(per=per, eval=en, test="bootstrap", pass_pct=float(np.mean(bs))))
            for (fn, (tiers, c1, c2)), B in itertools.product(FUND.items(), BUF):
                for test in ("historia", "costo +1 tick", "Monte Carlo"):
                    cost = test == "costo +1 tick"; EL, EC = EVV[cost]; FL, FC = FV[(fn, cost)]
                    if test != "Monte Carlo":
                        out = np.zeros((nd, 8)); m = life_m(EL, EC, C, 3000.0, 2000.0, 0.3, 4, FEE, FL, FC, c1, c2, B, 0, hidx, 252, 3, out); Lr = out[:m]
                    else:
                        Lr = np.zeros((nmc, 8)); o1 = np.zeros((2, 8))
                        for q, idx in enumerate(IDX):
                            life_m(EL, EC, C, 3000.0, 2000.0, 0.3, 4, FEE, FL, FC, c1, c2, B, 0, idx, 252, 252, o1); Lr[q] = o1[0]
                    fm = Lr[:, 6].sum() / 21.0
                    rows.append(dict(per=per, eval=en, fprof=fn, B=B, test=test, mo=Lr[:, 0].mean() / 12, ploss=100 * (Lr[:, 0] < 0).mean(),
                                     evals=Lr[:, 1].mean(), passes=Lr[:, 2].mean(), fbust=Lr[:, 3].mean(), payouts=Lr[:, 4].mean(),
                                     eval_days=Lr[:, 5].mean(), funded_share=100 * Lr[:, 6].mean() / 252, cash_fm=Lr[:, 7].sum() / max(fm, 1e-9)))
            print(per, en, round(time.time() - t0), flush=True)
    return pd.DataFrame(rows), pd.DataFrame(erows)


if __name__ == "__main__":
    R, E = run(); R.to_csv("mffu_rapid.csv", index=False); E.to_csv("mffu_rapid_eval.csv", index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 50)
    print(E.pivot_table(index=["eval", "test"], columns="per", values=["pass_pct", "med_days", "p22", "p33"]).round(0).to_string())
    S = R.groupby(["eval", "fprof", "B"]).agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), cash_fm=("cash_fm", "mean"),
                                              cash_fm_min=("cash_fm", "min"), fbust=("fbust", "mean"), payouts=("payouts", "mean"),
                                              evals=("evals", "mean"), funded_share=("funded_share", "mean")).round(0).reset_index()
    S.to_csv("mffu_rapid_summary.csv", index=False)
    for ev in S["eval"].unique():
        print("\n##", ev); print(S[S["eval"] == ev].sort_values("mean9", ascending=False).head(12).drop(columns=["eval"]).to_string(index=False))
