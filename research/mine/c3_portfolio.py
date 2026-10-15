"""2026-10-16 C3: portfolio construction WITHOUT estimating means. Pre-registered universe (8 configs) and acceptance rule:
  methods: inverse-volatility risk parity (RP) and Hierarchical Risk Parity (HRP, Lopez de Prado 2016, single linkage on the
  correlation distance) with Ledoit-Wolf shrunk covariance; trailing window 126 or 252 trading days; monthly rebalance;
  weights scaled so the average module weight is 1 (same gross budget as today's 1 base contract per module); applied as a
  multiplier on each module's current daily P&L (current defaults: MOM1030 / CPI09 x4, ICT x2, context x2 included).
  Two versions: continuous weights and integer contracts (round, clip 0..4) -- only the integer one is implementable.
  Accept only if Sharpe AND worst month improve vs fixed contracts in all four periods (2010-14 / 2015-19 cost-normalised,
  2020-23 / 2024-26 real) and max drawdown is not more than 5% worse.
Plus redundancy check: module pairs with daily correlation > 0.30 (2020-26) and the effect of switching off the lower-Sharpe one.
-> c3_portfolio.json"""
import os, sys, json, numpy as np, pandas as pd
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from wrq_lib import getD
from news import NEWS
from audit16_stats import load
from sklearn.covariance import LedoitWolf

PER = {"2010-14n": (20100701, 20150101, 1), "2015-19n": (20150101, 20200101, 1), "2020-23": (20200101, 20240101, 0), "2024-26": (20240101, 20991231, 0)}


def hrp(cov):
    sd = np.sqrt(np.diag(cov)); corr = cov / np.outer(sd, sd); corr = np.clip(corr, -1, 1)
    dist = np.sqrt(np.clip((1 - corr) / 2, 0, None)); np.fill_diagonal(dist, 0)
    order = leaves_list(linkage(squareform(dist, checks=False), "single"))
    w = np.ones(len(cov)); clusters = [list(order)]
    while clusters:
        new = []
        for c in clusters:
            if len(c) <= 1: continue
            a, b = c[:len(c) // 2], c[len(c) // 2:]
            va = ivp_var(cov, a); vb = ivp_var(cov, b); al = 1 - va / (va + vb)
            w[a] *= al; w[b] *= 1 - al; new += [a, b]
        clusters = new
    return w


def ivp_var(cov, idx):
    c = cov[np.ix_(idx, idx)]; iv = 1 / np.diag(c); iv /= iv.sum(); return float(iv @ c @ iv)


def stats(x, days):
    mon = pd.Series(x, index=days).groupby(days // 100).sum(); eq = np.cumsum(x)
    return dict(sharpe=round(float(x.mean() / x.std() * np.sqrt(252)), 3), worst_month=round(float(mon.min())), maxdd=round(float((np.maximum.accumulate(eq) - eq).max())), net=round(float(x.sum())))


if __name__ == "__main__":
    D = getD("nqdb.npz")
    days = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); days = days[(days >= 20100701) & ~np.isin(days, list(NEWS["FOMC"]))]
    sets, cur = load()
    mods = sorted(set(cur[0]["mod"]) | set(cur[1]["mod"]))
    def mat(X): return X.assign(x=X.u * X.w).pivot_table(index="date", columns="mod", values="x", aggfunc="sum").reindex(index=days, columns=mods).fillna(0.0)
    MN = mat(cur[1]); MR = mat(cur[0]); M = MN.copy(); M.loc[days >= 20200101] = MR.loc[days >= 20200101]
    X = M.to_numpy(); n, K = X.shape; mon_key = days // 100
    W = {}
    for meth in ("RP", "HRP"):
        for win in (126, 252):
            w = np.full((n, K), np.nan); last = None
            for t in range(win, n):
                if last is None or mon_key[t] != mon_key[t - 1]:
                    S = X[t - win:t]; act = S.std(0) > 0
                    cov = LedoitWolf().fit(S[:, act]).covariance_
                    ww = np.zeros(K)
                    if meth == "RP": ww[act] = 1 / np.sqrt(np.diag(cov))
                    else: ww[act] = hrp(cov)
                    ww = ww / ww[act].mean() if act.any() else ww; last = ww
                w[t] = last
            W[(meth, win)] = w
    OUT = {"configs": 8, "periods": {}}
    base = X.sum(1)
    for nm, (lo, hi, _) in PER.items():
        m = (days >= lo) & (days < hi); rec = {"fixed (today)": stats(base[m], days[m])}
        for (meth, win), w in W.items():
            ok = m & ~np.isnan(w[:, 0])
            rec[f"{meth}{win} cont"] = stats((X * np.nan_to_num(w))[ok].sum(1), days[ok])
            wi = np.clip(np.rint(np.nan_to_num(w)), 0, 4)
            rec[f"{meth}{win} int"] = stats((X * wi)[ok].sum(1), days[ok])
            rec[f"fixed same days {meth}{win}"] = stats(base[ok], days[ok])
        OUT["periods"][nm] = rec
        print(nm, json.dumps(rec), flush=True)
    verdict = {}
    for (meth, win) in W:
        for kind in ("cont", "int"):
            good = all(OUT["periods"][p][f"{meth}{win} {kind}"]["sharpe"] > OUT["periods"][p][f"fixed same days {meth}{win}"]["sharpe"]
                       and OUT["periods"][p][f"{meth}{win} {kind}"]["worst_month"] > OUT["periods"][p][f"fixed same days {meth}{win}"]["worst_month"]
                       and OUT["periods"][p][f"{meth}{win} {kind}"]["maxdd"] <= 1.05 * OUT["periods"][p][f"fixed same days {meth}{win}"]["maxdd"] for p in PER)
            verdict[f"{meth}{win} {kind}"] = "passes all 4 periods" if good else "fails"
    OUT["verdict"] = verdict; print(verdict)
    # redundancy
    R = MR.loc[days >= 20200101]; C = R.corr(); pairs = []
    for i in range(K):
        for j in range(i + 1, K):
            if C.iloc[i, j] > 0.30: pairs.append((mods[i], mods[j], round(float(C.iloc[i, j]), 3)))
    OUT["corr_pairs_gt_0.30"] = pairs; print("pairs", pairs)
    shp = lambda v: float(v.mean() / v.std() * np.sqrt(252)) if v.std() > 0 else 0.0
    eff = {}
    for a, b, c in pairs:
        T1 = (days >= 20200101) & (days < 20240101)
        weaker = a if shp(M[a].to_numpy()[T1]) < shp(M[b].to_numpy()[T1]) else b
        res = {}
        for nm, (lo, hi, _) in PER.items():
            m = (days >= lo) & (days < hi); x0 = base[m]; x1 = x0 - M[weaker].to_numpy()[m]
            res[nm] = dict(dSharpe=round(shp(x1) - shp(x0), 3), dWorstMonth=round(stats(x1, days[m])["worst_month"] - stats(x0, days[m])["worst_month"]))
        eff[f"off {weaker} (pair {a}/{b} corr {c})"] = res
    OUT["redundancy_off_weaker"] = eff; print(json.dumps(eff, indent=1))
    json.dump(OUT, open(os.path.join(HERE, "c3_portfolio.json"), "w"), indent=1)
