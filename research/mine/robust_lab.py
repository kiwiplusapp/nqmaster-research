"""Robustness lab, step 2: every test in the 'what it took' checklist, on robust_trades.pkl. Writes robust_lab.json.
 1 costs      : extra slippage ticks/side (1 tick/side = $1.00 RT per MNQ) -> PF/Sharpe/$; breakeven ticks.
 2 bootstrap  : stationary block bootstrap of days (mean block 10) -> 5-95% bands of Sharpe, PF, $/mo; P(PF>1).
 3 evidence   : trades vs independent days, daily autocorrelation, block vs iid standard error.
 4 DSR        : deflated Sharpe ratio (Bailey & Lopez de Prado) for N = 10 ... 50,000 trials.
 5 PBO        : CSCV probability of backtest overfitting for (a) 'pick the best mined config' (b) 'pick the best variant per module'.
 6 regimes    : PF and $/day by year, ATR tercile, trend/range day, VIX tercile.
 7 correlation: module daily P&L correlation, effective number of independent bets.
 8 plateaus   : PF across target variants per module (C24 / REAL).
 9 Monte Carlo: 1-year bootstrap paths (1 lot) -> P&L and max-drawdown percentiles, P(losing year).
10 monitor    : one-sided CUSUM on ATR-normalised daily P&L: false-alarm run length on live-like data and detection delay
                when the edge is gone; replay on 2020-26 and on 2015-19 (edge eaten by costs)."""
import os, sys, json, pickle, itertools, math, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data
from scipy.stats import norm, skew, kurtosis
T = pickle.load(open("robust_trades.pkl", "rb")); J = {}
rng = np.random.default_rng(7)
def daily(F, days, extra=0.0):
    x = (F.u - extra) * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0.0)
    gp = x.clip(lower=0).groupby(F.date).sum().reindex(days, fill_value=0.0); gl = (-x.clip(upper=0)).groupby(F.date).sum().reindex(days, fill_value=0.0)
    return d.to_numpy(), gp.to_numpy(), gl.to_numpy()
def stat(d, gp, gl): return dict(pf=gp.sum() / gl.sum(), sharpe=d.mean() / d.std() * 252 ** .5, mo=d.mean() * 21)
def boot_idx(n, B, L=10):
    idx = np.empty((B, n), np.int64)
    for b in range(B):
        i = 0; p = rng.integers(n)
        while i < n:
            idx[b, i] = p; i += 1
            p = rng.integers(n) if rng.random() < 1 / L else (p + 1) % n
    return idx
# ------------------------------------------------------------------ 1-3, 9
for prof, PP in T.items():
    for per, (F, days) in PP.items():
        r = {}
        r["costs"] = {s: {k: round(v, 3) for k, v in stat(*daily(F, days, s)).items()} for s in (0.0, 1.0, 2.0, 3.0, 4.0)}
        r["breakeven_ticks_per_side"] = round(float((F.u * F.w).sum() / F.w.sum()), 2)
        d, gp, gl = daily(F, days); n = len(d); I = boot_idx(n, 2000)
        sh = d[I].mean(1) / d[I].std(1) * 252 ** .5; pf = gp[I].sum(1) / gl[I].sum(1); mo = d[I].mean(1) * 21
        r["boot"] = dict(sharpe=[round(float(np.percentile(sh, q)), 2) for q in (5, 50, 95)], pf=[round(float(np.percentile(pf, q)), 3) for q in (5, 50, 95)],
                         mo=[round(float(np.percentile(mo, q))) for q in (5, 50, 95)], P_pf_gt1=round(float((pf > 1).mean()), 4), P_sharpe_gt1=round(float((sh > 1).mean()), 4))
        ac = [float(pd.Series(d).autocorr(l)) for l in (1, 2, 5)]
        se_iid = d.std() / n ** .5; se_blk = float(d[I].mean(1).std())
        r["evidence"] = dict(trades=len(F), days=n, days_with_trades=int((F.groupby("date").size() > 0).sum()), autocorr_1_2_5=[round(a, 3) for a in ac],
                             se_ratio_block_vs_iid=round(se_blk / se_iid, 2), eff_days=round(n * (se_iid / se_blk) ** 2))
        # 1-year Monte Carlo (252 days) from this period's days
        I2 = boot_idx(n, 4000)[:, :252] if n >= 252 else None
        if I2 is not None:
            P = d[I2]; eq = P.cumsum(1); dd = (np.maximum.accumulate(np.maximum(eq, 0), 1) - eq).max(1); yr = eq[:, -1]
            m21 = np.array([P[:, i:i + 21].sum(1) for i in range(0, 252 - 20, 21)]).T
            r["mc_year"] = dict(pnl=[round(float(np.percentile(yr, q))) for q in (5, 25, 50, 75, 95)], maxdd=[round(float(np.percentile(dd, q))) for q in (50, 75, 95, 99)],
                                P_year_loss=round(float((yr < 0).mean()), 4), P_month_loss=round(float((m21 < 0).mean()), 3), worst_month_p5=round(float(np.percentile(m21.min(1), 5))))
        J.setdefault(prof, {})[per] = r
    print(prof, "1-3,9 done", flush=True)
# ------------------------------------------------------------------ 4 DSR on daily returns
def dsr(d, N):
    sr = d.mean() / d.std(); n = len(d); g3 = skew(d); g4 = kurtosis(d, fisher=False); emc = 0.5772156649
    sr0 = (1 / n) ** .5 * ((1 - emc) * norm.ppf(1 - 1 / N) + emc * norm.ppf(1 - 1 / (N * math.e)))
    z = (sr - sr0) * (n - 1) ** .5 / (1 - g3 * sr + (g4 - 1) / 4 * sr * sr) ** .5
    return float(norm.cdf(z)), float(sr0 * 252 ** .5)
for prof, PP in T.items():
    for lab, pers in (("CFD 2020-26", ("IS", "C24")), ("REAL 2024-26", ("REAL",))):
        d = np.concatenate([daily(*PP[p])[0] for p in pers])
        J[prof].setdefault("dsr", {})[lab] = {str(N): [round(v, 4) for v in dsr(d, N)] for N in (10, 100, 1000, 10000, 50000)} | {"sharpe": round(float(d.mean() / d.std() * 252 ** .5), 2), "days": len(d)}
print("DSR done", flush=True)
# ------------------------------------------------------------------ 5 PBO (CSCV, S=16)
def pbo(M, S=16):
    n, N = M.shape; b = np.array_split(np.arange(n), S)
    s1 = np.array([M[ix].sum(0) for ix in b]); s2 = np.array([(M[ix] ** 2).sum(0) for ix in b]); cnt = np.array([len(ix) for ix in b])
    lam = []; deg = []
    for comb in itertools.combinations(range(S), S // 2):
        c = np.zeros(S, bool); c[list(comb)] = True
        def sh(mask):
            m = s1[mask].sum(0) / cnt[mask].sum(); v = s2[mask].sum(0) / cnt[mask].sum() - m * m; return m / np.sqrt(np.maximum(v, 1e-12))
        a = sh(c); o = sh(~c); k = int(np.argmax(a))
        rk = (o < o[k]).mean() + 0.5 * (o == o[k]).mean(); rk = min(max(rk, 1 / N), 1 - 1 / N)
        lam.append(math.log(rk / (1 - rk))); deg.append((a[k], o[k]))
    lam = np.array(lam); deg = np.array(deg)
    return dict(PBO=round(float((lam <= 0).mean()), 3), median_logit=round(float(np.median(lam)), 2), N=N, combos=len(lam),
                IS_best_sharpe_ann=round(float(deg[:, 0].mean() * 252 ** .5), 2), OOS_sharpe_of_IS_best_ann=round(float(deg[:, 1].mean() * 252 ** .5), 2),
                P_OOS_loss=round(float((deg[:, 1] < 0).mean()), 3))
nqd = None
TR = {}
for tag in ("b1", "b2", "b3"):
    try: TR.update(pickle.load(open(f"trades_{tag}.pkl", "rb")))
    except FileNotFoundError: pass
cols = {}
for key, v in TR.items():
    df = v["nq"]; df = df[(df.date >= 20200201)]
    if len(df) >= 150: cols[key] = df.groupby("date").usd.sum()
M = pd.DataFrame(cols).fillna(0.0); M = M.reindex(sorted(set(M.index)), fill_value=0.0)
alld = np.array(sorted(set(np.concatenate([T["Ultra"]["IS"][1], T["Ultra"]["C24"][1]])))); M = M.reindex(alld, fill_value=0.0)
J["pbo_miner"] = pbo(M.to_numpy())
V = pd.read_pickle(os.path.join(RES, "variants_ext_nq_1m.pkl")); V = V[(V["mod"] != "GOLD") & (V.date >= 20200201)]
per_mod = {}
for m, g in V.groupby("mod"):
    if g["var"].nunique() < 3: continue
    Mm = g.pivot_table(index="date", columns="var", values="usd", aggfunc="sum").reindex(alld, fill_value=0.0).fillna(0.0)
    per_mod[m] = pbo(Mm.to_numpy())
J["pbo_variants"] = per_mod
print("PBO done", J["pbo_miner"], flush=True)
# ------------------------------------------------------------------ 6 regimes
DD = {"nq": Data("nq_1m.npz"), "mnq": Data("mnq_fut.npz")}
def day_feats(D):
    rth = (D.om >= 570) & (D.om < 960)
    df = pd.DataFrame(dict(date=D.date[rth], o=D.o[rth], h=D.h[rth], l=D.l[rth], c=D.c[rth], day=D.day[rth]))
    g = df.groupby("date").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), day=("day", "first"))
    g["atr"] = D.atr[g.day.to_numpy()]; g["trendday"] = (g.c - g.o).abs() / (g.h - g.l).replace(0, np.nan) > 0.5
    return g
FE = {k: day_feats(D) for k, D in DD.items()}
vix = pd.read_csv(os.path.join(RES, "vix.csv")); vix.columns = [c.lower() for c in vix.columns]
vcol = [c for c in vix.columns if c != "date" and "date" not in c][0]; dcol = [c for c in vix.columns if "date" in c][0]
vix["date"] = pd.to_datetime(vix[dcol]).dt.strftime("%Y%m%d").astype(int); vix = vix.set_index("date")[vcol].apply(pd.to_numeric, errors="coerce").shift(1)
for prof, PP in T.items():
    R = {}
    for lab, pers, key in (("CFD 2020-26", ("IS", "C24"), "nq"), ("REAL 2024-26", ("REAL",), "mnq")):
        F = pd.concat([PP[p][0] for p in pers]); days = np.concatenate([PP[p][1] for p in pers])
        d, gp, gl = daily(F, days); X = pd.DataFrame(dict(date=days, d=d, gp=gp, gl=gl)).set_index("date")
        fe = FE[key].reindex(X.index); X["year"] = X.index // 10000; X["atr"] = fe.atr; X["trend"] = fe.trendday; X["vix"] = vix.reindex(X.index).ffill().to_numpy()
        X["atr_t"] = pd.qcut(X.atr, 3, labels=["ATR bajo", "ATR medio", "ATR alto"]); X["vix_t"] = pd.qcut(X.vix, 3, labels=["VIX bajo", "VIX medio", "VIX alto"])
        out = {}
        for col in ("year", "atr_t", "trend", "vix_t"):
            g = X.groupby(col, observed=True).agg(gp=("gp", "sum"), gl=("gl", "sum"), d=("d", "mean"), n=("d", "size"))
            out[col] = {str(k): dict(pf=round(float(r.gp / r.gl), 3), per_day=round(float(r.d), 1), days=int(r.n)) for k, r in g.iterrows()}
        out["atr_terciles_pts"] = [round(float(q)) for q in X.atr.quantile([1 / 3, 2 / 3])]
        R[lab] = out
    J[prof]["regimes"] = R
print("regimes done", flush=True)
# ------------------------------------------------------------------ 7 correlation
for prof, PP in T.items():
    for lab, pers in (("CFD 2020-26", ("IS", "C24")), ("REAL 2024-26", ("REAL",))):
        F = pd.concat([PP[p][0] for p in pers]); days = np.concatenate([PP[p][1] for p in pers])
        Mx = (F.assign(x=F.u * F.w).pivot_table(index="date", columns="mod", values="x", aggfunc="sum").reindex(days, fill_value=0.0).fillna(0.0))
        C = Mx.corr().to_numpy(); ev = np.linalg.eigvalsh(C); iu = np.triu_indices_from(C, 1)
        J[prof].setdefault("corr", {})[lab] = dict(mods=list(Mx.columns), mean_pair_corr=round(float(C[iu].mean()), 3), max_pair_corr=round(float(C[iu].max()), 3),
                                                   eff_bets=round(float(ev.sum() ** 2 / (ev ** 2).sum()), 2), n_mods=len(Mx.columns),
                                                   matrix=[[round(float(v), 2) for v in row] for row in C])
print("corr done", flush=True)
# ------------------------------------------------------------------ 8 plateaus (target variants)
pl = {}
for tag, lab, lo in (("nq_1m", "C24", 20240101), ("nq_1m", "IS", 20200201), ("mnq_fut", "REAL", 20240201)):
    E = pd.read_pickle(os.path.join(RES, f"variants_ext_{tag}.pkl")); E = E[(E["mod"] != "GOLD") & (E.date >= lo)]
    if lab == "IS": E = E[E.date < 20240101]
    for (m, v), g in E.groupby(["mod", "var"]):
        u = g.usd; pl.setdefault(m, {}).setdefault(str(v), {})[lab] = dict(pf=round(float(u[u > 0].sum() / -u[u <= 0].sum()), 3), wr=round(float(100 * (u > 0).mean()), 1), n=len(u))
J["plateaus"] = pl
# ------------------------------------------------------------------ 10 CUSUM edge monitor (ATR-normalised daily P&L, 1 lot)
@njit(cache=True)
def cusum_first(x, k, h):
    s = 0.0
    for t in range(len(x)):
        s = max(0.0, s + k - x[t])
        if s > h: return t + 1
    return -1
def norm_daily(F, days, key):
    d = daily(F, days)[0]; a = FE[key].reindex(days).atr.to_numpy(); return d / (2 * a)          # P&L in units of (ATR points x $2)
mon = {}
for prof in ("Ultra", "WR70Plus", "Core6"):
    PP = T[prof]
    z = np.concatenate([norm_daily(*PP["IS"], "nq"), norm_daily(*PP["C24"], "nq")]); zr = norm_daily(*PP["REAL"], "mnq")
    mu = float(z.mean()); k = mu / 2; res = {"mu_norm": mu, "k": k}
    n = len(z); B = 600; I = boot_idx(n, B, 10); H = 3000
    long_idx = np.concatenate([I, boot_idx(n, B, 10), boot_idx(n, B, 10)], axis=1)[:, :H] if n < H else I[:, :H]
    table = []
    for h_mult in (4, 6, 8, 10, 12, 15, 20):
        h = h_mult * float(z.std())
        arl0 = []; arl_dead = []; arl_half = []
        for b in range(B):
            seq = z[long_idx[b]]
            t0 = cusum_first(seq, k, h); arl0.append(t0 if t0 > 0 else H)
            t1 = cusum_first(seq - mu, k, h); arl_dead.append(t1 if t1 > 0 else H)
            t2 = cusum_first(seq - 0.5 * mu, k, h); arl_half.append(t2 if t2 > 0 else H)
        arl0 = np.array(arl0); arl_dead = np.array(arl_dead); arl_half = np.array(arl_half)
        table.append(dict(h_sd=h_mult, h=h, P_false_alarm_1y=round(float((arl0 <= 252).mean()), 3), P_false_alarm_3y=round(float((arl0 <= 756).mean()), 3),
                          median_days_detect_dead=float(np.median(arl_dead)), p90_days_detect_dead=float(np.percentile(arl_dead, 90)), median_days_detect_half=float(np.median(arl_half))))
    res["table"] = table
    # replays with the chosen h (first with P_false_alarm_3y <= 10%)
    ch = next((t for t in table if t["P_false_alarm_3y"] <= 0.10), table[-1]); res["chosen"] = ch
    res["replay_2020_26_alarm_day"] = cusum_first(z, k, ch["h"]); res["replay_REAL_alarm_day"] = cusum_first(zr, k, ch["h"])
    mon[prof] = res
# 2015-19 replay: robust-module set as traded then (real costs of the era), normalised by that era's ATR
L = pd.read_pickle(os.path.join(RES, "variants_nqhd_long.pkl"))
core = {"ICT": 1.0, "MSEQ": 0.5, "CRT11": 2.0, "LON": 2.0, "ORB60": 0.6}
L = pd.concat([L[(L["mod"] == m) & (L["var"] == v)] for m, v in core.items()]); L = L[~L.fomc]
DL = Data("nqhd_long.npz"); fl = day_feats(DL)
Ld = L.groupby("date").usd.sum(); alld_l = np.array(sorted(fl.index)); Ld = Ld.reindex(alld_l, fill_value=0.0)
zl = (Ld / (2 * fl.atr.reindex(alld_l))).to_numpy()
y = alld_l // 10000; m1519 = (y >= 2015) & (y <= 2019)
k6 = mon["Core6"]["k"]; h6 = mon["Core6"]["chosen"]["h"]
first = cusum_first(zl[m1519], k6, h6)
mon["replay_2015_19_core"] = dict(alarm_day=first, alarm_date=int(alld_l[m1519][first - 1]) if first > 0 else None, days=int(m1519.sum()),
                                  pf_2015_19=round(float(L[(L.date >= 20150101) & (L.date < 20200101)].usd.pipe(lambda u: u[u > 0].sum() / -u[u <= 0].sum())), 3),
                                  share_days_atr_ge150=round(float((fl.atr.reindex(alld_l[m1519]) >= 150).mean()), 3))
J["monitor"] = mon
json.dump(J, open("robust_lab.json", "w"), indent=1, default=float)
print("ALL DONE")
