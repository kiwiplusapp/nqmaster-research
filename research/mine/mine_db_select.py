"""Selection on the 16-year real-futures mining runs (run_mine_db.py -> results_db_old.csv, results_db_new.csv), 2026-10-09.
Protocol fixed BEFORE looking at the results (Federico: 'high win rate AND high PF'):
  1. chosen on T1 only (real 2020-23): n >= 100, WR >= 60%, PF >= 1.40
  2. out of sample, nothing re-fitted:  T2 real 2024-26 n >= 40, PF >= 1.30, WR >= 58%
                                        B  2015-19 cost-normalised PF >= 1.10 (n >= 30)
                                        A  2010-14 cost-normalised PF >= 1.00 (n >= 30)
  3. luck check: share of stage-1 configs passing stage 2 vs the share of ALL configs passing stage 2 on their own
  4. value for the portfolio: daily P&L added to Ultra (db_long_trades.pkl, real, MinATR 150) -> Sharpe change in T1 and T2,
     correlation with Ultra, and +4 ticks per side stress on T2.
-> mine_db_select.json, mine_db_finalists.csv"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))


def load():
    R, T = [], {}
    for tag in ("db_old", "db_new"):
        p = os.path.join(HERE, f"results_{tag}.csv")
        if os.path.exists(p):
            r = pd.read_csv(p); r["tag"] = tag; R.append(r)
            T.update(pickle.load(open(os.path.join(HERE, f"trades_{tag}.pkl"), "rb")))
    return pd.concat(R, ignore_index=True), T


def st1(R): return (R.T1_n >= 100) & (R.T1_wr >= 60) & (R.T1_pf >= 1.40)
def st2(R): return (R.T2_n >= 40) & (R.T2_pf >= 1.30) & (R.T2_wr >= 58) & (R.B_n >= 30) & (R.B_pf >= 1.10) & (R.A_n >= 30) & (R.A_pf >= 1.00)


def sharpe(x): return float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else np.nan


if __name__ == "__main__":
    R, T = load()
    R = R[R.get("err", pd.Series(np.nan, index=R.index)).isna()].copy()
    s1 = st1(R); s2 = st2(R)
    OUT = {"configs": int(len(R)), "by_tag": R.tag.value_counts().to_dict(), "stage1": int(s1.sum()), "stage1_and_2": int((s1 & s2).sum()),
           "stage2_rate_given_stage1": round(float(s2[s1].mean()), 4) if s1.any() else None,
           "stage2_rate_all_configs": round(float(s2.mean()), 4),
           "stage2_rate_configs_T1pf_1.0_1.2": round(float(s2[(R.T1_pf >= 1.0) & (R.T1_pf < 1.2) & (R.T1_n >= 100)].mean()), 4)}
    OUT["stage1_by_family"] = R[s1].fam.value_counts().to_dict()
    OUT["final_by_family"] = R[s1 & s2].fam.value_counts().to_dict()
    print(json.dumps({k: OUT[k] for k in list(OUT)[:7]}, indent=1), flush=True)
    print("stage 1 by family", OUT["stage1_by_family"], flush=True)
    print("final by family", OUT["final_by_family"], flush=True)

    # ---- portfolio value vs Ultra
    TR = pickle.load(open(os.path.join(HERE, "db_long_trades.pkl"), "rb"))
    Xr = TR["Ultra"][0]; Xr = Xr[Xr.atr >= 150]
    from wrq_lib import getD
    D = getD("nqdb.npz")
    days = np.array(sorted(set(D.daydate[D.ro >= 0]))); atr_d = pd.Series(D.atr, index=D.daydate).groupby(level=0).last()
    days = days[(days >= 20200101) & (atr_d.reindex(days).to_numpy() >= 150)]
    U = (Xr.u * Xr.w).groupby(Xr.date).sum().reindex(days, fill_value=0.0)
    F = R[s1 & s2].copy()
    rows = []
    for _, f in F.iterrows():
        k = (f.fam, int(f.j))
        if k not in T: continue
        tr = T[k]["real"]; tr = tr[tr.date.isin(days)]
        x = tr.groupby("date").usd.sum().reindex(days, fill_value=0.0)
        x4 = (tr.usd - 6 * 0.25 * 2.0).groupby(tr.date).sum().reindex(days, fill_value=0.0)          # +3 ticks per side more
        rec = dict(fam=f.fam, j=int(f.j), params=f.params, tag=f.tag,
                   T1=f"{int(f.T1_n)} tr WR {f.T1_wr} PF {f.T1_pf}", T2=f"{int(f.T2_n)} tr WR {f.T2_wr} PF {f.T2_pf}",
                   B=f"PF {f.B_pf} ({int(f.B_n)})", A=f"PF {f.A_pf} ({int(f.A_n)})")
        for lab, lo, hi in (("T1", 20200101, 20240101), ("T2", 20240101, 20991231)):
            m = (days >= lo) & (days < hi)
            u, xx, xx4 = U[m], x[m], x4[m]
            rec[f"{lab}_corr"] = round(float(np.corrcoef(u, xx)[0, 1]), 3)
            rec[f"{lab}_sh_ultra"] = round(sharpe(u), 2); rec[f"{lab}_sh_plus"] = round(sharpe(u + xx), 2)
            rec[f"{lab}_per_month"] = round(float(xx.mean() * 21))
            if lab == "T2":
                w = tr[(tr.date >= lo)].usd - 6 * 0.25 * 2.0
                rec["T2_pf_plus3ticks"] = round(float(w[w > 0].sum() / -w[w <= 0].sum()), 2) if (w <= 0).any() else None
        rec["dSharpe_T1"] = round(rec["T1_sh_plus"] - rec["T1_sh_ultra"], 3); rec["dSharpe_T2"] = round(rec["T2_sh_plus"] - rec["T2_sh_ultra"], 3)
        rows.append(rec)
    FF = pd.DataFrame(rows)
    if len(FF):
        FF = FF.sort_values(["dSharpe_T2"], ascending=False)
        FF.to_csv(os.path.join(HERE, "mine_db_finalists.csv"), index=False)
        cols = ["fam", "j", "T1", "T2", "B", "A", "T2_pf_plus3ticks", "T1_corr", "T2_corr", "dSharpe_T1", "dSharpe_T2", "T2_per_month"]
        print(FF[cols].head(40).to_string(), flush=True)
        OUT["finalists"] = FF.head(60).to_dict("records")
        OUT["adds_sharpe_both"] = int(((FF.dSharpe_T1 > 0) & (FF.dSharpe_T2 > 0)).sum())
    json.dump(OUT, open(os.path.join(HERE, "mine_db_select.json"), "w"), indent=1, default=str)
