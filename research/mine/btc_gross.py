"""Zero-cost view of the Bitcoin mining run (run_mine_btc.py with MINE_NORM=0 -> results_btc_gross.csv): the *n columns are
gross P&L in % of the daily ATR (no commission, no slippage). Answers 'is it the cost or is there no pattern at all?'.
Also re-prices the real $ columns at the actual cost levels of a prop firm (MFFU $3.50 RT + 1 tick per side) for the
stage-1 configs. -> btc_gross.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    G = pd.read_csv(os.path.join(HERE, "results_btc_gross.csv")); R = pd.read_csv(os.path.join(HERE, "results_btc.csv"))
    out = {"configs": int(len(G))}
    for lab in ("A", "T1n", "T2n"):
        pfc = G[lab + "_pf"]; n = G[lab.rstrip("n") + "_n"] if lab != "A" else G["A_n"]
        out[lab] = dict(median_gross_pf=round(float(pfc.median()), 3), share_pf_ge_1=round(float((pfc >= 1.0).mean()), 3),
                        share_pf_ge_1_3_n100=round(float(((pfc >= 1.3) & (n >= 100)).mean()), 4), n_pf_ge_1_3_n100=int(((pfc >= 1.3) & (n >= 100)).sum()))
    g_all = (G.T1n_pf >= 1.3) & (G.T1_n >= 100) & (G.T2n_pf >= 1.2) & (G.T2_n >= 30) & (G.A_pf >= 1.0) & (G.A_n >= 30)
    out["gross_pass_T1_T2_A"] = int(g_all.sum()); out["gross_pass_by_family"] = G[g_all].fam.value_counts().to_dict()
    g1 = (G.T1n_pf >= 1.3) & (G.T1_n >= 100); g2 = (G.T2n_pf >= 1.2) & (G.T2_n >= 30)
    out["gross_p_T2_given_T1"] = round(float(g2[g1].mean()), 4) if g1.any() else None; out["gross_p_T2_all"] = round(float(g2[G.T2_n >= 30].mean()), 4)
    # NQ comparison: same statistic on the NQ real-futures run (results_db_old.csv, cost-normalised 0.345 % columns are net, so use real T1/T2)
    p = os.path.join(HERE, "results_db_old.csv")
    if os.path.exists(p):
        N = pd.read_csv(p); out["nq_reference"] = dict(configs=int(len(N)), median_pf_T1=round(float(N.T1_pf.median()), 3), median_pf_T2=round(float(N.T2_pf.median()), 3),
                                                      share_T1_pf_ge_1_3_n100=round(float(((N.T1_pf >= 1.3) & (N.T1_n >= 100)).mean()), 4))
    out["btc_net_reference"] = dict(median_pf_T1=round(float(R.T1_pf.median()), 3), median_pf_T2=round(float(R.T2_pf.median()), 3),
                                    share_T1_pf_ge_1_3_n100=round(float(((R.T1_pf >= 1.3) & (R.T1_n >= 100)).mean()), 4))
    print(json.dumps(out, indent=1)); json.dump(out, open(os.path.join(HERE, "btc_gross.json"), "w"), indent=1)
