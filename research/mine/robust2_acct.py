"""Robustness lab, step 2: MyFundedFutures Rapid EOD 50K (eval: target 3,000, EOD trailing 2,000 locking at +100, 30% consistency,
4 days min; funded: withdraw everything above start + 4,100 = keep a $4,000 cushion, 90% split) at 1 contract, on REAL NQ
2020-01..2026-10 day vectors from robust2_build.py (intraday low incl. open adverse excursion).
Policies switch the traded set by CUSHION (balance minus liquidation threshold) - 'gears': eval 2 gears (below / above C),
funded 3 gears (below c1 / c1..c2 / above c2). Every start day of each period, 12-month horizon (funded) / to the end (eval).
Chosen on 2020-23, confirmed on 2024-26. -> robust2_acct.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mffu_rapid import ev_m, fu_m, life_m
SP = "/tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad"
days, P = pickle.load(open(os.path.join(SP, "robust2_paths.pkl"), "rb"))
N = len(days); idx = np.arange(N)
PERIODS = {"2020-23": (days >= 20200101) & (days < 20240101), "2024-26": days >= 20240101}


def arr(keys):
    return (np.ascontiguousarray(np.array([P[k][0] for k in keys])), np.ascontiguousarray(np.array([P[k][1] for k in keys])))


def funded(gears, c1, c2, B=4100.0, H=252):
    FL, FC = arr(gears); out = {}
    for lab, m in PERIODS.items():
        st = np.nonzero(m)[0]; st = st[st + 60 < N]
        res = np.array([fu_m(FL, FC, c1, c2, idx, s, min(s + H, N), B, 2000.0, 0) for s in st])
        span = np.array([min(s + H, N) - s for s in st])
        out[lab] = dict(bust=round(100 * float((res[:, 2] == -1).mean()), 1), cash=round(float((res[:, 0] / span * 21).mean())),
                        payouts=round(float(res[:, 1].mean()), 1), bust_first_60d=round(100 * float(((res[:, 2] == -1) & (res[:, 3] - st < 60)).mean()), 1))
    return out


def evals(gears, C):
    EL, EC = arr(gears if len(gears) == 2 else gears * 2); out = {}
    for lab, m in PERIODS.items():
        st = np.nonzero(m)[0]; st = st[st + 40 < N]
        r = np.array([ev_m(EL, EC, C, 3000.0, 2000.0, 0.3, 4, idx, s, N) for s in st])
        ok = r[:, 0] == 1; dd = (r[:, 1] - st + 1)[ok]
        out[lab] = dict(passed=round(100 * float(ok.mean()), 1), median_days=float(np.median(dd)) if ok.any() else None,
                        within_22d=round(100 * float((ok & ((r[:, 1] - st + 1) <= 22)).mean()), 1))
    return out


def life(eg, C, fg, c1, c2, B=4100.0, fee=157.0, H=252, step=3):
    EL, EC = arr(eg if len(eg) == 2 else eg * 2); FL, FC = arr(fg); out = {}
    for lab, m in PERIODS.items():
        st = np.nonzero(m)[0]; s0, s1 = st[0], st[-1]
        sub = np.arange(s0, min(s1 + 1, N)); o = np.zeros((len(sub), 8))
        r = life_m(EL, EC, C, 3000.0, 2000.0, 0.3, 4, fee, FL, FC, c1, c2, B, 0, sub, min(H, len(sub) - 1), step, o); o = o[:r]
        out[lab] = dict(per_month=round(float(o[:, 0].mean() / 12)), worst_year=round(float(o[:, 0].min())), evals=round(float(o[:, 1].mean()), 1),
                        funded_busts=round(float(o[:, 3].mean()), 2), payouts=round(float(o[:, 4].mean()), 1), p_neg_year=round(100 * float((o[:, 0] < 0).mean()), 1))
    return out


if __name__ == "__main__":
    OUT = {"funded": {}, "eval": {}, "life": {}}
    F = {"Ultra 1c (today)": (["Ultra"] * 3, 0, 0), "WR70Plus 1c": (["WR70Plus"] * 3, 0, 0), "UltraLean 1c": (["UltraLean"] * 3, 0, 0),
         "Ultra cap400 always": (["Ultra_cap400"] * 3, 0, 0), "Ultra cap300 always": (["Ultra_cap300"] * 3, 0, 0)}
    for c1 in (1000, 1500, 2000, 2500, 3000):
        F[f"cap300 < {c1} <= Ultra"] = (["Ultra_cap300", "Ultra", "Ultra"], c1, c1)
        F[f"cap200 < {c1} <= Ultra"] = (["Ultra_cap200", "Ultra", "Ultra"], c1, c1)
        F[f"Estable < {c1} <= Ultra"] = (["Estable", "Ultra", "Ultra"], c1, c1)
        F[f"WR70Plus < {c1} <= Ultra"] = (["WR70Plus", "Ultra", "Ultra"], c1, c1)
        F[f"WR70Plus_cap300 < {c1} <= WR70Plus"] = (["WR70Plus_cap300", "WR70Plus", "WR70Plus"], c1, c1)
    F["cap200 < 1000 <= cap300 < 2500 <= Ultra"] = (["Ultra_cap200", "Ultra_cap300", "Ultra"], 1000, 2500)
    F["Estable < 1000 <= cap300 < 2500 <= Ultra"] = (["Estable", "Ultra_cap300", "Ultra"], 1000, 2500)
    for k, (g, c1, c2) in F.items():
        OUT["funded"][k] = funded(g, c1, c2); print("FUNDED", f"{k:42s}", OUT["funded"][k], flush=True)
    E = {"Ultra fixed": (["Ultra", "Ultra"], 0.0), "Estable < 1200 <= Ultra (today's Estable gear)": (["Estable", "Ultra"], 1200.0),
         "WR70Plus fixed": (["WR70Plus", "WR70Plus"], 0.0)}
    for C in (800, 1200, 1600, 2000):
        E[f"cap300 < {C} <= Ultra"] = (["Ultra_cap300", "Ultra"], float(C)); E[f"cap200 < {C} <= Ultra"] = (["Ultra_cap200", "Ultra"], float(C))
        E[f"WR70Plus_cap300 < {C} <= WR70Plus"] = (["WR70Plus_cap300", "WR70Plus"], float(C))
    for k, (g, C) in E.items():
        OUT["eval"][k] = evals(g, C); print("EVAL", f"{k:42s}", OUT["eval"][k], flush=True)
    json.dump(OUT, open(os.path.join(HERE, "robust2_acct.json"), "w"), indent=1)
