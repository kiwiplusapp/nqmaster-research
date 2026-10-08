"""Deep checks on the Q-batch finalists: per-year PF (2015-19 cost-normalised, CFD 2020-26, REAL), long/short split, block-bootstrap
CI of the portfolio Sharpe change (Ultra / WR70Plus), the two finalists together, and which Ultra modules the NOISE family overlaps.
Writes q_deep.json."""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import pf

FIN = {"REBAL48": ("Q_REBAL", {'K': 3, 'x': 0.5, 'A': 931, 'mode': -1, 'k': 0.3, 'R': 99.0}),
       "REBAL49": ("Q_REBAL", {'K': 3, 'x': 0.5, 'A': 931, 'mode': -1, 'k': 0.3, 'R': 1.0}),
       "VR394": ("Q_VR", {'T': 1300, 'q': 5, 'reg': 'MOM', 'thr': 0, 'x': 0.1, 'k': 0.35, 'R': 99.0, 'tf': 0}),
       "XLEAD_ISbest": ("Q_XLEAD", {'asset': 'ES', 'W': 30, 'th': 2.0, 'mode': 1, 'H': 60, 'k': 0.3}),
       "NOISE_ISbest": ("Q_NOISE", {'L': 10, 'm': 1.0, 'f': 60, 'trail': 1, 'hs': 99.0, 'tf': 0, 'maxday': 3, 'side': 0}),
       "NOISE259": ("Q_NOISE", {'L': 20, 'm': 1.5, 'f': 30, 'trail': 0, 'hs': 99.0, 'tf': 1, 'maxday': 3, 'side': 0})}
rng = np.random.default_rng(11)
def boot_idx(n, B, L=10):
    idx = np.empty((B, n), np.int64)
    for b in range(B):
        i = 0; p = rng.integers(n)
        while i < n:
            idx[b, i] = p; i += 1
            p = rng.integers(n) if rng.random() < 1 / L else (p + 1) % n
    return idx
def sh(x): return x.mean(-1) / x.std(-1) * 252 ** .5

if __name__ == "__main__":
    from q_mine import run_cfg, load_all, NORM
    G = load_all(); J = {}; TR = {}
    T = pickle.load(open("robust_trades.pkl", "rb"))
    PER = {"IS": ("cfd", 20200201, 20240101), "C24": ("cfd", 20240101, 99999999), "REAL": ("real", 20240201, 99999999)}
    for name, (fam, p) in FIN.items():
        t = {k: run_cfg(G[k], fam, p) for k in ("cfd", "real")}; t["long"] = run_cfg(G["long"], fam, p, slip=0.0, norm_cost=NORM)
        TR[name] = t; r = {}
        yl = t["long"][t["long"].date < 20200101]; yc = t["cfd"]; yr = t["real"][t["real"].date >= 20240201]
        r["by_year"] = {**{f"{y} (15-19 norm)": [len(g), round(100 * (g.usd > 0).mean(), 1), pf(g.usd)] for y, g in yl.groupby(yl.date // 10000)},
                        **{f"{y} CFD": [len(g), round(100 * (g.usd > 0).mean(), 1), pf(g.usd), round(g.usd.sum())] for y, g in yc.groupby(yc.date // 10000)},
                        **{f"{y} REAL": [len(g), round(100 * (g.usd > 0).mean(), 1), pf(g.usd), round(g.usd.sum())] for y, g in yr.groupby(yr.date // 10000)}}
        r["side"] = {}
        for lab, df in (("IS", yc[yc.date < 20240101]), ("C24", yc[yc.date >= 20240101]), ("REAL", yr), ("2015-19", yl)):
            r["side"][lab] = {("long" if s > 0 else "short"): [int(len(g)), round(100 * (g.usd > 0).mean(), 1), pf(g.usd)] for s, g in df.groupby(np.sign(df.d))}
        J[name] = r
    # bootstrap CI of the Sharpe change, finalists alone and together
    combos = {"REBAL48": ["REBAL48"], "VR394": ["VR394"], "REBAL48+VR394": ["REBAL48", "VR394"], "REBAL49+VR394": ["REBAL49", "VR394"], "NOISE259": ["NOISE259"]}
    J["boot_dsharpe"] = {}
    for cname, members in combos.items():
        out = {}
        for per, (src, a, b) in PER.items():
            for prof in ("Ultra", "WR70Plus"):
                F, days = T[prof][per]; P = (F.u * F.w).groupby(F.date).sum().reindex(days, fill_value=0.0)
                X = sum(TR[m][src][(TR[m][src].date >= a) & (TR[m][src].date < b)].groupby("date").usd.sum().reindex(days, fill_value=0.0) for m in members)
                p_ = P.to_numpy(); x_ = X.to_numpy(); I = boot_idx(len(p_), 2000)
                d = sh(p_[I] + x_[I]) - sh(p_[I])
                out[f"{prof}_{per}"] = dict(dsh=round(float(sh(p_ + x_) - sh(p_)), 3), ci90=[round(float(np.percentile(d, 5)), 3), round(float(np.percentile(d, 95)), 3)],
                                             P_gt0=round(float((d > 0).mean()), 3), add_mo=round(float(x_.mean() * 21)))
        J["boot_dsharpe"][cname] = out
    # NOISE overlap with Ultra modules (daily P&L correlation per module, REAL)
    F, days = T["Ultra"]["REAL"]; x = TR["NOISE_ISbest"]["real"]; x = x[x.date >= 20240201].groupby("date").usd.sum().reindex(days, fill_value=0.0)
    J["noise_vs_ultra_modules_REAL"] = {m: round(float(np.corrcoef((g.u * g.w).groupby(g.date).sum().reindex(days, fill_value=0.0), x)[0, 1]), 3) for m, g in F.groupby("mod")}
    json.dump(J, open("q_deep.json", "w"), indent=1, default=str)
    for k in ("REBAL48", "REBAL49", "VR394", "XLEAD_ISbest"):
        print(k); [print("  ", a, b) for a, b in J[k]["by_year"].items()]; print("  side", J[k]["side"])
    print(json.dumps(J["boot_dsharpe"], indent=0)); print(J["noise_vs_ultra_modules_REAL"])
