"""Robustness evaluation of the Q batch (q_mine.py output).
 1 robust filter: IS & C24 PF >= 1.2 (n >= 80 / 50), REAL PF >= 1.15 (n >= 40), 2015-19 cost-normalised PF >= 1.1
 2 +4 ticks per side (slip 1.25 pt/side) PF >= 1.1 in IS, C24, REAL
 3 plateau: neighbours (one parameter changed) -> share with IS/C24 >= 1.1 and REAL >= 1.05, median neighbour PFs
 4 IS-only selection per family (best IS daily Sharpe with IS n >= 80) -> out-of-sample PFs (the honest test of each family)
 5 PBO (CSCV, S=16) on daily P&L of every config (CFD 2020-26) per family and for the whole batch; DSR with N = batch size and 300k
 6 portfolio: daily P&L correlation with Ultra / WR70Plus (robust_trades.pkl) and daily Sharpe change when added at 1 contract
Writes q_eval.json and q_survivors.csv."""
import os, sys, json, glob, math, itertools, pickle, ast, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scipy.stats import norm, skew, kurtosis
from core import split_stats

def pbo(M, S=16):
    """CSCV probability of backtest overfitting (Bailey, Borwein, Lopez de Prado, Zhu); copy of robust_lab.pbo (that file runs at import)."""
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
                IS_sharpe_best=round(float(deg[:, 0].mean() * 252 ** .5), 2), OOS_sharpe_of_best=round(float(deg[:, 1].mean() * 252 ** .5), 2))

def dsr(d, N):
    sr = d.mean() / d.std(); n = len(d); g3 = skew(d); g4 = kurtosis(d, fisher=False); emc = 0.5772156649
    sr0 = (1 / n) ** .5 * ((1 - emc) * norm.ppf(1 - 1 / N) + emc * norm.ppf(1 - 1 / (N * math.e)))
    z = (sr - sr0) * (n - 1) ** .5 / (1 - g3 * sr + (g4 - 1) / 4 * sr * sr) ** .5
    return round(float(norm.cdf(z)), 4), round(float(sr0 * 252 ** .5), 2)

def sharpe(x): x = np.asarray(x, float); return float(x.mean() / x.std() * 252 ** .5) if x.std() > 0 else np.nan

if __name__ == "__main__":
    from q_mine import run_cfg, load_all
    from q_families import QFAMILIES
    R = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("q_results_Q_*.csv"))], ignore_index=True)
    R["P"] = R.params.map(ast.literal_eval)
    DLY = {f: np.load(f"q_daily_{f}.npz") for f in R.fam.unique()}
    cfd_days = DLY["Q_NOISE"]["cfd_days"]; real_days = DLY["Q_NOISE"]["real_days"]
    isd = cfd_days < 20240101
    J = {"tested": {f: int((R.fam == f).sum()) for f in R.fam.unique()}, "total_configs": int(len(R))}
    # ---- 1 robust filter
    f1 = (R.IS_n >= 80) & (R.IS_pf >= 1.2) & (R.C24_n >= 50) & (R.C24_pf >= 1.2) & (R.REAL_n >= 40) & (R.REAL_pf >= 1.15) & (R.TR_pf >= 1.1)
    R["f1"] = f1
    # ---- 2 +4 ticks on the filter survivors
    G = load_all()
    for k in ("IS", "C24", "REAL"): R[k + "_pf4"] = np.nan
    for ix in R.index[f1]:
        fam, p = R.at[ix, "fam"], R.at[ix, "P"]
        st = split_stats("nq_1m.npz", run_cfg(G["cfd"], fam, p, slip=1.25)); st.update(split_stats("mnq_fut.npz", run_cfg(G["real"], fam, p, slip=1.25)))
        for k in ("IS", "C24", "REAL"): R.at[ix, k + "_pf4"] = st[k + "_pf"]
    R["f2"] = R.f1 & (R.IS_pf4 >= 1.1) & (R.C24_pf4 >= 1.1) & (R.REAL_pf4 >= 1.1)
    # ---- 3 plateau
    R["nb_n"] = 0; R["nb_ok"] = np.nan; R["nb_IS"] = np.nan; R["nb_C24"] = np.nan; R["nb_REAL"] = np.nan; R["nb_TR"] = np.nan
    for ix in R.index[R.f2]:
        fam, p = R.at[ix, "fam"], R.at[ix, "P"]; sub = R[R.fam == fam]
        nb = [j for j, q in zip(sub.index, sub.P) if j != ix and sum(q[k] != p[k] for k in p) == 1]
        S_ = R.loc[nb]; ok = (S_.IS_pf >= 1.1) & (S_.C24_pf >= 1.1) & (S_.REAL_pf >= 1.05)
        R.at[ix, "nb_n"] = len(nb); R.at[ix, "nb_ok"] = round(float(ok.mean()), 2) if len(nb) else np.nan
        for k in ("IS", "C24", "REAL", "TR"): R.at[ix, "nb_" + k] = round(float(S_[k + "_pf"].median()), 3) if len(nb) else np.nan
    R["f3"] = R.f2 & (R.nb_ok >= 0.5) & (R[["nb_IS", "nb_C24", "nb_REAL"]].min(axis=1) >= 1.1)
    J["funnel"] = R.groupby("fam").agg(configs=("j", "size"), robust=("f1", "sum"), plus4ticks=("f2", "sum"), plateau=("f3", "sum")).astype(int).to_dict("index")
    J["median_pf"] = R.groupby("fam")[["IS_pf", "C24_pf", "REAL_pf", "TR_pf"]].median().round(3).to_dict("index")
    # ---- 4 IS-only selection per family
    sel = {}
    for fam in R.fam.unique():
        sub = R[(R.fam == fam) & (R.IS_n >= 80)]
        if not len(sub): continue
        M = DLY[fam]["cfd"][sub.j.to_numpy()][:, isd]; shs = M.mean(1) / np.maximum(M.std(1), 1e-9) * 252 ** .5
        b = sub.index[int(np.argmax(shs))]
        sel[fam] = {k: (R.at[b, k] if not isinstance(R.at[b, k], (np.floating, np.integer)) else float(R.at[b, k])) for k in
                    ("params", "IS_n", "IS_wr", "IS_pf", "C24_n", "C24_wr", "C24_pf", "REAL_n", "REAL_wr", "REAL_pf", "TR_n", "TR_wr", "TR_pf")}
        sel[fam]["IS_sharpe"] = round(float(shs.max()), 2)
    J["is_selected"] = sel
    # ---- 5 PBO / DSR
    J["pbo"] = {}
    for fam in R.fam.unique():
        J["pbo"][fam] = pbo(DLY[fam]["cfd"].T.astype(np.float64))
    allM = np.concatenate([DLY[f]["cfd"] for f in sorted(DLY)], axis=0).T.astype(np.float64)
    J["pbo"]["ALL"] = pbo(allM)
    # ---- 6 portfolio
    T = pickle.load(open("robust_trades.pkl", "rb"))
    def port_daily(prof, per):
        F, days = T[prof][per]; x = (F.u * F.w).groupby(F.date).sum().reindex(days, fill_value=0.0); return x
    PER = {"IS": ("cfd", lambda d: (d >= 20200201) & (d < 20240101)), "C24": ("cfd", lambda d: d >= 20240101), "REAL": ("real", lambda d: d >= 20240201)}
    surv = R[R.f3].copy(); rows = []
    for ix in surv.index:
        fam, j = R.at[ix, "fam"], int(R.at[ix, "j"]); row = {"fam": fam, "j": j, "params": R.at[ix, "params"]}
        for per, (src, fn) in PER.items():
            days = DLY[fam][src + "_days"]; s = pd.Series(DLY[fam][src][j].astype(float), index=days)
            for prof in ("Ultra", "WR70Plus"):
                P = port_daily(prof, per); x = s.reindex(P.index, fill_value=0.0)
                row[f"{prof}_{per}_corr"] = round(float(np.corrcoef(P, x)[0, 1]), 3)
                row[f"{prof}_{per}_sh0"] = round(sharpe(P), 2); row[f"{prof}_{per}_dsh"] = round(sharpe(P + x) - sharpe(P), 2)
            row[f"{per}_mo"] = round(float(s[fn(days)].mean() * 21), 0)
        d_all = np.r_[DLY[fam]["cfd"][j].astype(float)]
        row["DSR_cfd_N_batch"], row["SR0_batch"] = dsr(d_all, len(R)); row["DSR_cfd_N300k"], row["SR0_300k"] = dsr(d_all, 300000)
        row["DSR_real_N_batch"], _ = dsr(DLY[fam]["real"][j].astype(float), len(R))
        row["sharpe_cfd"] = round(sharpe(d_all), 2); row["sharpe_real"] = round(sharpe(DLY[fam]["real"][j]), 2)
        rows.append(row)
    PS = pd.DataFrame(rows)
    out = surv.drop(columns=["P"]).merge(PS, on=["fam", "j", "params"], how="left") if len(PS) else surv.drop(columns=["P"])
    out.to_csv("q_survivors.csv", index=False)
    R.drop(columns=["P"]).to_csv("q_results_all.csv", index=False)
    json.dump(J, open("q_eval.json", "w"), indent=1, default=str)
    print(json.dumps(J["funnel"], indent=0)); print(json.dumps(J["pbo"], indent=0))
    print(pd.DataFrame(J["is_selected"]).T.to_string())
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 80)
    print(out.to_string())
