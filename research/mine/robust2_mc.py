"""Robustness lab, step 3: the funded / eval results of robust2_acct.py depend on a handful of drawdown episodes, so every policy is
re-run on 2,000 resampled years per period (10-day blocks of real days, the SAME resampled paths for every policy = paired).
MyFundedFutures Rapid EOD 50K, 1 contract: funded keeps $4,100 (withdraw above), eval 3,000 / 2,000 EOD / 30% consistency.
Chosen on 2020-23 resamples, confirmed on 2024-26 resamples. -> robust2_mc.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mffu_rapid import ev_m, fu_m
from robust2_acct import P, days, arr
NB = 2000; H = 252; BLK = 10


def boot(mask, seed):
    pos = np.nonzero(mask)[0]; rng = np.random.default_rng(seed); nb = H // BLK + 1
    st = rng.integers(0, len(pos) - BLK, size=(NB, nb))
    return [np.concatenate([pos[s:s + BLK] for s in row])[:H] for row in st]


IDX = {"2020-23": boot((days >= 20200101) & (days < 20240101), 7), "2024-26": boot(days >= 20240101, 8)}


def funded(gears, c1, c2, B=4100.0):
    FL, FC = arr(gears); out = {}
    for lab, ids in IDX.items():
        r = np.array([fu_m(FL, FC, c1, c2, ix, 0, H, B, 2000.0, 0) for ix in ids])
        out[lab] = dict(bust=round(100 * float((r[:, 2] == -1).mean()), 1), cash_mo=round(float(r[:, 0].mean() / 12)),
                        bust_60d=round(100 * float(((r[:, 2] == -1) & (r[:, 3] < 60)).mean()), 1))
    return out


def evals(gears, C):
    EL, EC = arr(gears); out = {}
    for lab, ids in IDX.items():
        r = np.array([ev_m(EL, EC, C, 3000.0, 2000.0, 0.3, 4, ix, 0, H) for ix in ids])
        ok = r[:, 0] == 1
        out[lab] = dict(passed=round(100 * float(ok.mean()), 1), median_days=float(np.median(r[ok, 1] + 1)) if ok.any() else None,
                        busted=round(100 * float((r[:, 0] == -1).mean()), 1))
    return out


if __name__ == "__main__":
    OUT = {"funded": {}, "eval": {}}
    F = {"Ultra 1c (today)": (["Ultra"] * 3, 0, 0), "WR70Plus 1c": (["WR70Plus"] * 3, 0, 0), "UltraLean 1c": (["UltraLean"] * 3, 0, 0)}
    for c1 in (1000, 1500, 2000, 2500, 3000):
        for low in ("Ultra_cap300", "Ultra_cap200", "Ultra_cap400", "Estable", "WR70Plus"):
            F[f"{low} < {c1} <= Ultra"] = ([low, "Ultra", "Ultra"], c1, c1)
    for c1, c2 in ((1000, 2000), (1000, 2500), (1500, 3000)):
        F[f"Estable < {c1} <= cap300 < {c2} <= Ultra"] = (["Estable", "Ultra_cap300", "Ultra"], c1, c2)
        F[f"cap200 < {c1} <= cap300 < {c2} <= Ultra"] = (["Ultra_cap200", "Ultra_cap300", "Ultra"], c1, c2)
        F[f"Estable < {c1} <= WR70Plus < {c2} <= Ultra"] = (["Estable", "WR70Plus", "Ultra"], c1, c2)
    for k, (g, c1, c2) in F.items():
        OUT["funded"][k] = funded(g, c1, c2); print("FUNDED", f"{k:44s}", OUT["funded"][k], flush=True)
    E = {"Ultra fixed": (["Ultra", "Ultra"], 0.0), "WR70Plus fixed": (["WR70Plus", "WR70Plus"], 0.0)}
    for C in (800, 1200, 1600, 2000):
        for low in ("Estable", "Ultra_cap300", "Ultra_cap200", "WR70Plus"):
            E[f"{low} < {C} <= Ultra"] = ([low, "Ultra"], float(C))
    for k, (g, C) in E.items():
        OUT["eval"][k] = evals(g, C); print("EVAL", f"{k:44s}", OUT["eval"][k], flush=True)
    json.dump(OUT, open(os.path.join(HERE, "robust2_mc.json"), "w"), indent=1)
