"""final3y step 2: Lucid Flex 50K and MyFundedFutures Rapid EOD 50K on the CURRENT NQMaster logic (final3y.py paths, REAL MNQ +
MGC 2024-02..2026-09). Eval at 1 contract (Estable gating / Ultra / Ultra lean / WR70Plus), funded 1c or 1c -> 2c; lifecycle per
account slot (12-month windows: eval fees, eval time, busts and restarts included); history, +1 tick per side, 600 bootstrap years.
MFFU funded uses the Tier-1 news blackout (NQ trades flat at 08:28 / 13:58 on CPI, NFP and FOMC-minutes days). -> final3y_acct.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import acct1c_lib as A
from final3y import day_vectors
from mffu_rapid import ev_m, fu_m, life_m, eval_stats
from numba import njit

PATHS, GL, GX = pickle.load(open("/tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad/final3y_paths.pkl", "rb"))
nd = len(GL["Robust"][0]); NMC = 600
VEC = {"U": ("Ultra", "Robust"), "UL": ("UltraLean", "Robust"), "W": ("WR70Plus", "WinRate"), "UH": ("Ultra", "WinRate x2"), "EL": ("Estable", "WinRate x2")}
_C = {}
def vec(key, G=0.0, news=False, cost=False):
    ck = (key, G, news, cost)
    if ck not in _C:
        prof, g = VEC[key]; low, close, fin, ex = PATHS[(prof, news)]; gL, gR = GL[g]
        lo, cl = day_vectors(low, close, fin, gL.astype(np.float64), gR.astype(np.float64), G)
        if cost: c = ex * 1.0 + GX[g]; lo = lo - c; cl = cl - c
        _C[ck] = (lo, cl)
    return _C[ck]


@njit(cache=True)
def funded_within_m(EL, EC, C, idx, W, out):
    N = len(idx); m = N - W
    for s in range(m):
        i = s; ok = 0.0; att = 0
        while i < s + W:
            att += 1; r, j = ev_m(EL, EC, C, 3000.0, 2000.0, 0.3, 4, idx, i, s + W)
            if r == 1: ok = 1.0; break
            if r == 0: break
            i = j + 1
        out[s, 0] = ok; out[s, 1] = att
    return m


EVALS = {"Estable (Ultra / Estable gear, C1200)": ("UH", "EL", 1200.0), "Ultra fixed": ("U", None, 0.0), "Ultra lean fixed": ("UL", None, 0.0),
         "WR70Plus fixed": ("W", None, 0.0)}
FUNDS = {"Ultra 1c": (("U", 1), ("U", 1), ("U", 1), 0.0, 0.0), "Ultra lean 1c": (("UL", 1), ("UL", 1), ("UL", 1), 0.0, 0.0),
         "WR70Plus 1c": (("W", 1), ("W", 1), ("W", 1), 0.0, 0.0)}
FUNDS_L = dict(FUNDS); FUNDS_L["Ultra 1c -> 2c from $1,500 cushion"] = (("U", 1), ("U", 1), ("U", 2), 0.0, 1500.0)
FUNDS_M = dict(FUNDS); FUNDS_M["Ultra 1c -> 2c from $3,000 cushion"] = (("U", 1), ("U", 1), ("U", 2), 0.0, 3000.0)
FIRMS = {"Lucid Flex 50K": dict(G=1400.0, fee=105.2, cons=0.5, news=False, funds=FUNDS_L),
         "MyFundedFutures Rapid EOD 50K": dict(G=800.0, fee=157.0, cons=0.3, news=True, funds=FUNDS_M)}
BUF = {"Ultra 1c": 4100.0, "Ultra lean 1c": 4100.0, "WR70Plus 1c": 4100.0, "Ultra 1c -> 2c from $3,000 cushion": 6100.0}


def evarr(ev, G, cost):
    hi, lo, C = EVALS[ev]; lH, cH = vec(hi, G, False, cost); lL, cL = (lH, cH) if lo is None else vec(lo, G, False, cost)
    return np.ascontiguousarray(np.array([lL, lH])), np.ascontiguousarray(np.array([cL, cH])), C


def fuarr(tiers, news, cost):
    L = []; Cc = []
    for key, k in tiers:
        lo, cl = vec(key, 0.0, news, cost); L.append(k * lo); Cc.append(k * cl)
    return np.ascontiguousarray(np.array(L)), np.ascontiguousarray(np.array(Cc))


if __name__ == "__main__":
    hidx = np.arange(nd, dtype=np.int64); IDX = [A.boot_idx(nd, q, 253, 10, 31) for q in range(NMC)]
    OUT = {}
    for firm, F in FIRMS.items():
        res = {"evals": {}, "life": {}}
        for ev in EVALS:
            r = {}
            for test, cost in (("history", False), ("+1 tick", True)):
                EL, EC, C = evarr(ev, F["G"], cost); o = np.zeros((nd, 2))
                if firm.startswith("Lucid"): m = A.eval_all(EL, EC, C, 3000.0, 2000.0, F["cons"], hidx, 60, o)
                else: m = eval_stats(EL, EC, C, 3000.0, 2000.0, F["cons"], 4, hidx, 60, o)
                s = A.esumm(o[:m]); r[test] = {k: round(v, 1) for k, v in s.items()}
                if test == "history":
                    fw = np.zeros((nd, 4)) if firm.startswith("Lucid") else np.zeros((nd, 2))
                    if firm.startswith("Lucid"): mm = A.funded_within(EL, EC, C, 3000.0, 2000.0, F["cons"], hidx, 33, fw); r["funded_within_33d"] = round(100 * fw[:mm, 1].mean(), 1); r["evals_used_33d"] = round(fw[:mm, 2].mean(), 2)
                    else: mm = funded_within_m(EL, EC, C, hidx, 33, fw); r["funded_within_33d"] = round(100 * fw[:mm, 0].mean(), 1); r["evals_used_33d"] = round(fw[:mm, 1].mean(), 2)
            EL, EC, C = evarr(ev, F["G"], False); bs = []
            for idx in IDX[:300]:
                o = np.zeros((253, 2))
                m = A.eval_all(EL, EC, C, 3000.0, 2000.0, F["cons"], idx, 60, o) if firm.startswith("Lucid") else eval_stats(EL, EC, C, 3000.0, 2000.0, F["cons"], 4, idx, 60, o)
                bs.append(A.esumm(o[:m])["pass_pct"])
            r["bootstrap_pass"] = round(float(np.mean(bs)), 1); r["bootstrap_pass_p10"] = round(float(np.percentile(bs, 10)), 1)
            res["evals"][ev] = r
            print(firm, ev, r["history"]["pass_pct"], r["history"]["med_days"], flush=True)
            for fn, (t0, t1, t2, c1, c2) in F["funds"].items():
                rows = []
                for test in ("history", "+1 tick", "bootstrap"):
                    cost = test == "+1 tick"; EL, EC, C = evarr(ev, F["G"], cost); FL, FC = fuarr((t0, t1, t2), F["news"], cost)
                    okst = np.ones(nd, np.bool_)
                    def run(idx, step, out):
                        if firm.startswith("Lucid"):
                            return A.life(EL, EC, C, 3000.0, 2000.0, F["cons"], okst, F["fee"], FL, FC, c1, c2, 0, 4000.0, 150.0, 2000.0, 2000.0, idx, 252, step, out)
                        return life_m(EL, EC, C, 3000.0, 2000.0, F["cons"], 4, F["fee"], FL, FC, c1, c2, BUF[fn], 0, idx, 252, step, out)
                    if test != "bootstrap":
                        out = np.zeros((nd, 9)); m = run(hidx, 3, out); Lr = out[:m]
                    else:
                        Lr = np.zeros((NMC, 9)); o1 = np.zeros((2, 9))
                        for q, idx in enumerate(IDX): run(idx, 252, o1); Lr[q] = o1[0]
                    fcol = 6; fm = Lr[:, fcol].sum() / 21.0; gross = Lr[:, 7]
                    rows.append(dict(test=test, per_month=round(Lr[:, 0].mean() / 12), p10_month=round(np.percentile(Lr[:, 0], 10) / 12),
                                     p_neg_year=round(100 * (Lr[:, 0] < 0).mean(), 1), evals_per_year=round(Lr[:, 1].mean(), 1),
                                     passes_per_year=round(Lr[:, 2].mean(), 2), funded_busts_per_year=round(Lr[:, 3].mean(), 2),
                                     payouts_per_year=round(Lr[:, 4].mean(), 1), cash_per_funded_month=round(gross.sum() / max(fm, 1e-9)),
                                     funded_share=round(100 * Lr[:, fcol].mean() / 252)))
                res["life"][f"{ev} | {fn}"] = rows
        OUT[firm] = res
    json.dump(OUT, open("final3y_acct.json", "w"), indent=1)
    for firm, res in OUT.items():
        print("\n##", firm)
        for k, rows in res["life"].items():
            print(f"{k:75s}", " | ".join(f"{r['test']}: {r['per_month']} (p10 {r['p10_month']}, neg {r['p_neg_year']}%, cashFM {r['cash_per_funded_month']})" for r in rows))
