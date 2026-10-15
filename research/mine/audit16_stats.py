"""2026-10-16 phase B: adversarial statistical audit of the CURRENT system (Ultra after the 10-12 overhaul + CPI09, MOM1030 x4,
CPI09 x4 = the NQMaster defaults on 2026-10-16). Pre-registered (written before running):
  B1 multiple testing: Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014) with N = 1e3..3e5 trials and the cross-sectional
     variance of trial Sharpe ratios estimated from the 45,278-config 16-year mining (binary-outcome approximation from WR / PF / n);
     PBO by CSCV (16 blocks, 12,870 splits) on the 32 system variants that were actually compared when building NQMaster;
     Hansen SPA (stationary bootstrap, mean block 10 days, 2,000 draws) of the same variants vs zero, on 2010-19 cost-normalised
     and on 2020-26 real.
  B2 per-module empirical-Bayes shrinkage: per module and era, mean $ per trade minus 1 extra tick ($1 per contract round trip)
     with its standard error; normal-normal hierarchical prior across modules (method of moments); posterior P(edge > 0).
     Decision rule fixed in advance: KEEP if P >= 0.90 in 2020-26 real AND P >= 0.60 in 2010-19 norm; KEEP-SMALL (watch) if
     P >= 0.90 in 2020-26 only; OFF-candidate if P < 0.80 in 2020-26 real.
  B3 regime stress: daily P&L conditional on ATR tercile, trend vs range day (|RTH close - open| / RTH range >= 0.5 = trend),
     rolling 12-month P&L; distribution of the longest streak of losing months in 12 and 36 months (20-day block bootstrap,
     1,000 paths) at full edge and with 35% of the edge removed.
-> audit16_stats.json"""
import os, sys, json, pickle, itertools, numpy as np, pandas as pd
from scipy.stats import norm
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from wrq_lib import getD
from news import NEWS
DUR = ["NF05", "CRT11", "VOLB", "MSEQS", "ORB60", "ORB90"]
rng = np.random.default_rng(16)


def load():
    C = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb")); Q = pickle.load(open(os.path.join(HERE, "ultraq_trades.pkl"), "rb"))["UltraQ"]
    cpiR, cpiN = Q[0][Q[0]["mod"] == "CPI09"], Q[1][Q[1]["mod"] == "CPI09"]
    sets = {}
    for k in C: sets[k] = (C[k][0].copy(), C[k][1].copy())
    sets["UltraQ"] = (Q[0].copy(), Q[1].copy())
    base = (pd.concat([C["UltraR"][0], cpiR], ignore_index=True), pd.concat([C["UltraR"][1], cpiN], ignore_index=True))
    for m in (1, 2, 4, 6, 8):
        sets[f"UltraR+CPI x{m}"] = tuple(X.assign(w=np.where(X["mod"].isin(["MOM1030", "CPI09"]), float(m), X.w)) for X in base)
    cur = sets["UltraR+CPI x4"]
    sets["Durable"] = tuple(X[X["mod"].isin(DUR)] for X in cur)
    for md in sorted(cur[0]["mod"].unique()):
        sets[f"x4 -{md}"] = tuple(X[X["mod"] != md] for X in cur)
    return sets, cur


def daily(X, days):
    return (X.u * X.w).groupby(X.date).sum().reindex(days, fill_value=0.0).to_numpy()


def dsr(x, N, vsr_d):
    """Deflated Sharpe ratio of daily series x after N trials with cross-sectional variance vsr_d of daily trial Sharpe ratios"""
    sr = x.mean() / x.std(); T = len(x); g3 = pd.Series(x).skew(); g4 = pd.Series(x).kurt() + 3
    em = 0.5772156649
    sr0 = np.sqrt(vsr_d) * ((1 - em) * norm.ppf(1 - 1 / N) + em * norm.ppf(1 - 1 / (N * np.e)))
    z = (sr - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return float(norm.cdf(z)), float(sr0 * np.sqrt(252)), float(sr * np.sqrt(252))


def trial_sr_var():
    """annualised Sharpe of every mined config on 2020-23 from WR / PF / n with a binary-outcome approximation"""
    r = pd.read_csv(os.path.join(HERE, "results_db_old.csv"), usecols=["T1_n", "T1_wr", "T1_pf"]).dropna()
    r = r[(r.T1_n >= 30) & (r.T1_wr > 0) & (r.T1_wr < 100) & (r.T1_pf > 0)]
    wr = r.T1_wr / 100; W = r.T1_pf * (1 - wr) / wr
    mean = (1 - wr) * (r.T1_pf - 1); sd = (W + 1) * np.sqrt(wr * (1 - wr))
    sr_ann = mean / sd * np.sqrt(r.T1_n / 4.0)
    sr_ann = sr_ann[np.isfinite(sr_ann)]
    return float(sr_ann.var()), float(sr_ann.median()), int(len(sr_ann))


def cscv_pbo(M, S=16):
    """M: T x K daily returns; probability that the in-sample best variant is below the OOS median (Bailey et al. 2015)"""
    T, K = M.shape; blocks = np.array_split(np.arange(T), S); lam = []
    for comb in itertools.combinations(range(S), S // 2):
        ins = np.concatenate([blocks[i] for i in comb]); oos = np.concatenate([blocks[i] for i in range(S) if i not in comb])
        a = M[ins]; b = M[oos]
        sa = a.mean(0) / (a.std(0) + 1e-12); sb = b.mean(0) / (b.std(0) + 1e-12)
        best = int(np.argmax(sa)); rk = (sb < sb[best]).sum() + 0.5 * ((sb == sb[best]).sum() - 1)
        w = (rk + 0.5) / K; lam.append(np.log(w / (1 - w)))
    lam = np.array(lam)
    return float((lam <= 0).mean()), float(np.median(lam))


def stat_boot_idx(T, mean_block, B):
    p = 1.0 / mean_block; out = np.empty((B, T), dtype=np.int64)
    for b in range(B):
        i = rng.integers(T);
        for t in range(T):
            out[b, t] = i
            i = rng.integers(T) if rng.random() < p else (i + 1) % T
    return out


def spa(M, B=2000, mb=10):
    """Hansen (2005) SPA, studentised, benchmark = 0 (flat): H0 no variant has positive mean. returns consistent p-value"""
    T, K = M.shape; mu = M.mean(0); idx = stat_boot_idx(T, mb, B)
    bm = np.stack([M[ix].mean(0) for ix in idx])                     # B x K
    om = np.sqrt(T) * bm.std(0) + 1e-12
    tstat = np.max(np.sqrt(T) * mu / om)
    gc = np.where(np.sqrt(T) * mu / om <= -np.sqrt(2 * np.log(np.log(T))), mu, 0.0)     # Hansen g_c: keep only clearly negative means
    tb = np.max(np.sqrt(T) * (bm - mu + gc) / om, axis=1)
    return float((tb >= tstat).mean()), float(tstat)


def eb_shrink(m, se):
    """normal-normal empirical Bayes: theta_i ~ N(mu, tau^2), m_i ~ N(theta_i, se_i^2)"""
    w = 1 / se ** 2; mu = float((w * m).sum() / w.sum())
    tau2 = max(0.0, float(np.var(m, ddof=1) - np.mean(se ** 2)))
    B = se ** 2 / (se ** 2 + tau2) if tau2 > 0 else np.ones_like(se)
    post = B * mu + (1 - B) * m; psd = np.sqrt(np.where(tau2 > 0, (1 - B) * se ** 2, se ** 2 * 0 + 1e-12))
    return post, psd, mu, tau2


def longest_neg_run(v):
    best = cur = 0
    for x in v:
        cur = cur + 1 if x < 0 else 0; best = max(best, cur)
    return best


if __name__ == "__main__":
    D = getD("nqdb.npz")
    alld = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); alld = alld[~np.isin(alld, list(NEWS["FOMC"]))]
    dR = alld[alld >= 20200101]; dN = alld[(alld >= 20100701) & (alld < 20200101)]
    sets, cur = load(); names = list(sets)
    OUT = {"variants": names}
    # ---- B1 DSR
    vsr, med, ncfg = trial_sr_var(); vsr_d = vsr / 252.0
    xR = daily(cur[0], dR); xN = daily(cur[1], dN)
    OUT["dsr"] = {"trial_SR_var_annual": round(vsr, 3), "trial_SR_median": round(med, 3), "configs_used": ncfg}
    for N in (1e3, 1e4, 1e5, 3e5, 1e6):
        p1, sr0, sr = dsr(xR, N, vsr_d); p2, sr0b, srb = dsr(xN, N, vsr_d)
        OUT["dsr"][f"N={int(N)}"] = dict(real_2020_26=dict(SR=round(sr, 2), SR0=round(sr0, 2), DSR=round(p1, 4)),
                                         norm_2010_19=dict(SR=round(srb, 2), SR0=round(sr0b, 2), DSR=round(p2, 4)))
    print("DSR", json.dumps(OUT["dsr"]), flush=True)
    # ---- B1 PBO + SPA on the variant set
    MR = np.column_stack([daily(sets[k][0], dR) for k in names]); MN = np.column_stack([daily(sets[k][1], dN) for k in names])
    pbo, lam = cscv_pbo(MR); OUT["pbo_2020_26"] = dict(pbo=round(pbo, 3), median_logit=round(lam, 3), variants=len(names))
    pboN, lamN = cscv_pbo(MN); OUT["pbo_2010_19_norm"] = dict(pbo=round(pboN, 3), median_logit=round(lamN, 3))
    print("PBO", OUT["pbo_2020_26"], OUT["pbo_2010_19_norm"], flush=True)
    pR, tR = spa(MR); pN, tN = spa(MN)
    OUT["spa"] = dict(real_2020_26=dict(p=round(pR, 4), t=round(tR, 2)), norm_2010_19=dict(p=round(pN, 4), t=round(tN, 2)))
    print("SPA", OUT["spa"], flush=True)
    sr_by = {k: dict(SR_2020_26=round(float(MR[:, i].mean() / MR[:, i].std() * np.sqrt(252)), 2),
                     SR_2010_19n=round(float(MN[:, i].mean() / MN[:, i].std() * np.sqrt(252)), 2)) for i, k in enumerate(names)}
    OUT["variant_sharpe"] = sr_by
    # ---- B2 per-module shrinkage (per trade, minus 1 extra tick = $1 per contract round trip)
    rows = []
    for era, X, lo, hi in (("2010-19n", cur[1], 20100101, 20200101), ("2020-26", cur[0], 20200101, 20991231)):
        Y = X[(X.date >= lo) & (X.date < hi)]
        g = Y.groupby("mod").u.agg(["mean", "std", "count"])
        g["m"] = g["mean"] - 1.0; g["se"] = g["std"] / np.sqrt(g["count"])
        g = g[g["count"] >= 10]
        post, psd, mu, tau2 = eb_shrink(g.m.to_numpy(), g.se.to_numpy())
        for i, md in enumerate(g.index):
            rows.append(dict(era=era, module=md, n=int(g["count"].iloc[i]), raw_mean=round(float(g.m.iloc[i]), 2), se=round(float(g.se.iloc[i]), 2),
                             post_mean=round(float(post[i]), 2), post_sd=round(float(psd[i]), 2), P_pos=round(float(norm.cdf(post[i] / psd[i])), 3),
                             P_pos_h35=round(float(norm.cdf((0.65 * (post[i] + 1.0) - 1.0) / psd[i])), 3)))
    T = pd.DataFrame(rows); OUT["modules"] = rows
    pv = T.pivot(index="module", columns="era", values="P_pos")
    dec = {}
    for md, r in pv.iterrows():
        pr, po = r.get("2020-26", np.nan), r.get("2010-19n", np.nan)
        dec[md] = ("KEEP" if pr >= 0.90 and (po >= 0.60 or np.isnan(po)) else "KEEP-SMALL (watch)" if pr >= 0.90 else "OFF-candidate" if pr < 0.80 else "WATCH")
    OUT["module_decision"] = dec
    print(T.to_string(index=False)); print(dec, flush=True)
    # ---- B3 regime stress (2020-26 real, current system)
    rth = (D.om >= 570) & (D.om < 960)
    dd = pd.DataFrame(dict(day=D.date[rth], o=D.o[rth], c=D.c[rth], h=D.h[rth], l=D.l[rth])).groupby("day").agg(o=("o", "first"), c=("c", "last"), h=("h", "max"), l=("l", "min"))
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last()
    dfR = pd.DataFrame(dict(pnl=xR), index=dR)
    dfR["trend"] = ((dd.c - dd.o).abs() / (dd.h - dd.l)).reindex(dR).to_numpy() >= 0.5
    dfR["atr"] = atr.reindex(dR).to_numpy(); dfR["terc"] = pd.qcut(dfR.atr, 3, labels=["low", "mid", "high"])
    pf = lambda v: float(v[v > 0].sum() / -v[v < 0].sum()) if (v < 0).any() else np.nan
    OUT["regime"] = {"trend_days": dict(share=round(float(dfR.trend.mean()), 3), pf=round(pf(dfR.pnl[dfR.trend].to_numpy()), 2), mean=round(float(dfR.pnl[dfR.trend].mean()), 1)),
                     "range_days": dict(pf=round(pf(dfR.pnl[~dfR.trend].to_numpy()), 2), mean=round(float(dfR.pnl[~dfR.trend].mean()), 1)),
                     "atr_terciles": {str(t): dict(pf=round(pf(g.pnl.to_numpy()), 2), mean=round(float(g.pnl.mean()), 1)) for t, g in dfR.groupby("terc", observed=True)}}
    mon = dfR.pnl.groupby(dR // 100).sum(); roll = mon.rolling(12).sum().dropna()
    OUT["rolling_12m"] = dict(min=round(float(roll.min())), p10=round(float(roll.quantile(0.1))), neg_share=round(float((roll < 0).mean()), 3))
    OUT["monthly"] = dict(months=int(len(mon)), neg=int((mon < 0).sum()), worst=round(float(mon.min())), longest_neg_streak=longest_neg_run(mon.to_numpy()))
    res = {}
    for hc in (0.0, 0.35):
        x = xR - hc * xR.mean(); L12 = []; L36 = []; NM12 = []
        for _ in range(1000):
            st = rng.integers(0, len(x) - 20, 38); path = np.concatenate([x[s:s + 20] for s in st])[:756]
            m = path.reshape(36, 21).sum(1)
            L12.append(longest_neg_run(m[:12])); L36.append(longest_neg_run(m)); NM12.append(int((m[:12] < 0).sum()))
        res[f"edge-{int(hc*100)}%"] = dict(longest_losing_streak_12m_p50=float(np.median(L12)), p90_12m=float(np.percentile(L12, 90)),
                                           p90_36m=float(np.percentile(L36, 90)), losing_months_per_year_mean=round(float(np.mean(NM12)), 2),
                                           P_3plus_losing_in_row_12m=round(float(np.mean(np.array(L12) >= 3)), 3))
    OUT["losing_streaks"] = res
    print(json.dumps({k: OUT[k] for k in ("regime", "rolling_12m", "monthly", "losing_streaks")}, indent=1), flush=True)
    json.dump(OUT, open(os.path.join(HERE, "audit16_stats.json"), "w"), indent=1, default=float)
