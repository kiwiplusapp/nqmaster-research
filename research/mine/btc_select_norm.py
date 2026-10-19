"""Supplementary selection (pre-stated after seeing that real-cost T1 2020-23 is a 4 %-of-ATR cost regime, BEFORE looking at T2
results of this variant): choose on T1 with TODAY's cost (cost-normalised 1.47 % of ATR columns T1n of results_btc.csv:
n >= 100, WR >= 55, PF >= 1.3, plateau on T1n PF >= 1.15), confirm on T2 REAL $ (PF >= 1.2, n >= 30), A 2017-19 normalised
PF >= 1.0, +4 ticks T2 PF >= 1.1, then the same portfolio test vs ultra_d4. -> btc_select_norm.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from btc_select import st1, st2, plateau, base_daily, metr, sharpe, block_boot, START, MID, TICK4

if __name__ == "__main__":
    R = pd.read_csv(os.path.join(HERE, "results_btc.csv")); T = pickle.load(open(os.path.join(HERE, "trades_btc.pkl"), "rb"))
    if "err" in R: R = R[R.err.isna()].copy()
    R2 = R.copy(); R2["T1_pf"] = R.T1n_pf; R2["T1_wr"] = R.T1n_wr            # T1 judged at today's cost level
    s1 = st1(R2); s2 = st2(R2)
    pf4 = pd.Series(np.nan, index=R.index)
    for i in R.index[s1]:
        k = (R.fam[i], int(R.j[i]))
        if k in T:
            u = T[k]["real"]; u = u[u.date >= MID].usd.to_numpy() - TICK4
            pf4[i] = u[u > 0].sum() / -u[u <= 0].sum() if (u <= 0).any() else np.nan
    R2["T2_pf_4t"] = pf4; R2["plateau"] = plateau(R2); s3 = (R2.T2_pf_4t >= 1.10) & R2.plateau
    t2ok = (R.T2_n >= 30) & (R.T2_pf >= 1.2)
    OUT = dict(stage1_T1norm=int(s1.sum()), stage1_and_2=int((s1 & s2).sum()), final=int((s1 & s2 & s3).sum()),
               p_T2pf12_given_stage1=round(float(t2ok[s1].mean()), 4) if s1.any() else None, p_T2pf12_all=round(float(t2ok.mean()), 4),
               p_T2pf12_given_T1n_1_12=round(float(t2ok[(R.T1_n >= 100) & (R.T1n_pf >= 1.0) & (R.T1n_pf < 1.2)].mean()), 4),
               kept_trades_missing=int(sum((R.fam[i], int(R.j[i])) not in T for i in R.index[s1])),
               stage1_by_family=R[s1].fam.value_counts().to_dict(), stage12_by_family=R[s1 & s2].fam.value_counts().to_dict(), final_by_family=R[s1 & s2 & s3].fam.value_counts().to_dict())
    print(json.dumps({k: v for k, v in OUT.items() if not isinstance(v, dict)}, indent=1)); print(OUT["stage1_by_family"]); print(OUT["stage12_by_family"]); print(OUT["final_by_family"])
    B = base_daily(); days = B.index.to_numpy(); rows = []
    for i in R.index[s1 & s2]:
        f = R2.loc[i]; k = (f.fam, int(f.j))
        if k not in T: continue
        tr = T[k]["real"]; tr = tr[tr.date >= START]; x = tr.groupby("date").usd.sum(); idx = np.union1d(days, x.index.to_numpy())
        b = B.reindex(idx, fill_value=0.0); c = x.reindex(idx, fill_value=0.0)
        rec = dict(fam=f.fam, j=int(f.j), params=f.params, T1n_n=int(f.T1_n), T1n_wr=f.T1_wr, T1n_pf=f.T1_pf, T1_real_pf=R.T1_pf[i], T2_n=int(f.T2_n), T2_wr=f.T2_wr, T2_pf=f.T2_pf,
                   A_pf=f.A_pf, T2_pf_4t=round(float(f.T2_pf_4t), 3), plateau=bool(f.plateau), final=bool(s3[i]))
        for lab, m in (("T1", idx < MID), ("T2", idx >= MID)):
            mb, mc = metr(b[m], idx[m]), metr(b[m] + c[m], idx[m])
            rec[f"{lab}_corr"] = round(float(np.corrcoef(b[m], c[m])[0, 1]), 3) if c[m].std() > 0 else 0.0
            rec[f"{lab}_dsh"] = round(mc["sharpe"] - mb["sharpe"], 3); rec[f"{lab}_dd"] = (mb["maxdd"], mc["maxdd"]); rec[f"{lab}_wm"] = (mb["worst_month"], mc["worst_month"])
            rec[f"{lab}_cand_per_month"] = round(float(c[m].mean() * 21)); rec[f"{lab}_boot"] = block_boot(b[m].to_numpy(), c[m].to_numpy())
        rec["accept"] = bool(rec["final"] and rec["T1_dsh"] > 0 and rec["T2_dsh"] > 0 and rec["T1_corr"] < 0.3 and rec["T2_corr"] < 0.3
                             and all(rec[f"{l}_dd"][1] <= 1.05 * rec[f"{l}_dd"][0] and rec[f"{l}_wm"][1] >= 1.05 * rec[f"{l}_wm"][0] for l in ("T1", "T2")))
        rows.append(rec)
    FF = pd.DataFrame(rows)
    if len(FF):
        FF = FF.sort_values("T2_dsh", ascending=False); pd.set_option("display.width", 250)
        print(FF[["fam", "j", "T1n_n", "T1n_wr", "T1n_pf", "T1_real_pf", "T2_n", "T2_wr", "T2_pf", "A_pf", "T2_pf_4t", "plateau", "T1_corr", "T2_corr", "T1_dsh", "T2_dsh", "T2_cand_per_month", "accept"]].to_string())
        OUT["finalists"] = FF.to_dict("records"); OUT["accepted"] = int(FF.accept.sum())
    json.dump(OUT, open(os.path.join(HERE, "btc_select_norm.json"), "w"), indent=1, default=str)
