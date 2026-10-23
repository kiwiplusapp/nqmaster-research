"""Batch 9 selection (2026-10-19, Federico: 'new modules with HIGH win rate and NEGATIVE reward-to-risk that hold in 2026-27').
Protocol FIXED BEFORE running the miner (MINE_TAG=b9 MINE_PROCS=3 python3 run_mine_db.py ROUND_NUM ONHL_TEST SETTLE TREND_SCALP
STRETCH_SNAP -> results_b9.csv, trades_b9.pkl; generators in families9.py). Not changed after seeing the results.
Every config has a target r x risk with r in {0.2, 0.3, 0.5} (break-even WR before costs 83 / 77 / 67%).
  s1  T1 (real 2020-01..2023-12): n >= 100, WR >= 70, PF >= 1.25                         (the only stage used to choose)
  s2  T2 (real 2024-01..2026-10): PF >= 1.15 and WR >= 68
  s3  B (2015-19 cost-normalised, 0.345% ATR) PF >= 1.05 and A (2010-14 cost-normalised) PF >= 0.95 (missing PF = fail)
  s4  plateau: >= half of the grid neighbours one NUMERIC step away (families9.CATEGORICAL9 are not steps) have T1 PF >= 1.10
      (a missing PF counts as a fail; a config with no numeric neighbour fails the stage)
  s5  stress: T2 with +4 ticks per side (usd - 3.0 per trade) PF >= 1.05
  survivor = s1..s5. Per family: median PF per period, share PF > 1, counts per stage, base rate P(T2 passes s2) vs
  P(T2 passes s2 | s1).
  portfolio: every survivor (or, if none, the 3 best near-survivors = s1 passers ranked by the number of later stages passed,
  then T2 PF; if there are no s1 passers, the 3 configs with the best T1 PF among n >= 100 and WR >= 70 whose trades were kept)
  -> six_lib.add_test(daily $ of the 'real' trades, w = 1): accepted only if Ultra Sharpe rises in T1 AND T2 and the 6-year
  max DD and worst month are not worse by more than 5%.
-> b9_select.json, results_b9_staged.csv"""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

S1 = dict(n=100, wr=70.0, pf=1.25); S2 = dict(pf=1.15, wr=68.0); S3 = dict(B=1.05, A=0.95); S4 = dict(frac=0.5, pf=1.10); S5 = dict(pf=1.05, cost=3.0)


def pf(u):
    u = np.asarray(u, float); l = -u[u <= 0].sum()
    return round(float(u[u > 0].sum() / l), 3) if l > 0 else None


def neighbours(params, fam_grid, cat):
    p = ast.literal_eval(params); keys = list(fam_grid[0])
    vals = {k: list(dict.fromkeys(g[k] for g in fam_grid)) for k in keys}
    idx = {repr(g): j for j, g in enumerate(fam_grid)}
    out = []
    for k in keys:
        if k in cat: continue
        v = vals[k]; i = v.index(p[k])
        for di in (-1, 1):
            if 0 <= i + di < len(v):
                q = dict(p); q[k] = v[i + di]; j = idx.get(repr(q))
                if j is not None: out.append(j)
    return out


def main():
    import six_lib
    from families9 import FAMILIES9, CATEGORICAL9
    R = pd.read_csv(os.path.join(HERE, "results_b9.csv"))
    T = pickle.load(open(os.path.join(HERE, "trades_b9.pkl"), "rb"))
    nerr = int(R["err"].notna().sum()) if "err" in R else 0
    if "err" in R: R = R[R["err"].isna()].copy()
    R = R.sort_values(["fam", "j"]).reset_index(drop=True)
    OUT = {"protocol": dict(S1=S1, S2=S2, S3=S3, S4=S4, S5=S5), "configs": int(len(R)), "errors": nerr, "families": {}}

    s1 = (R.T1_n >= S1["n"]) & (R.T1_wr >= S1["wr"]) & (R.T1_pf >= S1["pf"]).fillna(False)
    i2 = (R.T2_pf >= S2["pf"]).fillna(False) & (R.T2_wr >= S2["wr"]).fillna(False)
    s2 = s1 & i2
    i3 = (R.B_pf >= S3["B"]).fillna(False) & (R.A_pf >= S3["A"]).fillna(False)
    s3 = s2 & i3
    plat = pd.Series(np.nan, index=R.index); nnb = pd.Series(0, index=R.index)
    for i in R.index[s1]:
        fam = R.fam[i]; G = FAMILIES9[fam][1]
        nb = neighbours(R.params[i], G, CATEGORICAL9)
        sub = R[(R.fam == fam) & (R.j.isin(nb))]
        nnb[i] = len(nb); plat[i] = float((sub.T1_pf >= S4["pf"]).sum()) / len(nb) if nb else np.nan
    R["plateau"] = plat; R["n_neigh"] = nnb
    i4 = (R.plateau >= S4["frac"]).fillna(False)
    s4 = s3 & i4
    pf4 = pd.Series(np.nan, index=R.index)
    for i in R.index:
        k = (R.fam[i], int(R.j[i]))
        if k in T:
            tr = T[k]["real"]; u = tr.usd[tr.date >= 20240101].to_numpy() - S5["cost"]
            pf4[i] = pf(u) if len(u) else np.nan
    R["T2_pf_4t"] = pf4
    i5 = (R.T2_pf_4t >= S5["pf"]).fillna(False)
    s5 = s4 & i5
    R["stages_after_s1"] = (i2.astype(int) + i3.astype(int) + i4.astype(int) + i5.astype(int)).where(s1, -1)
    R["s1"] = s1; R["s2"] = s2; R["s3"] = s3; R["s4"] = s4; R["s5"] = s5

    for fam, g in list(R.groupby("fam")) + [("ALL", R)]:
        ix = g.index
        OUT["families"][fam] = dict(
            configs=int(len(g)),
            median_pf=dict(T1=round(float(g.T1_pf.median()), 3), T2=round(float(g.T2_pf.median()), 3),
                           A_norm=round(float(g.A_pf.median()), 3), B_norm=round(float(g.B_pf.median()), 3)),
            median_wr=dict(T1=round(float(g.T1_wr.median()), 1), T2=round(float(g.T2_wr.median()), 1)),
            median_n=dict(T1=round(float(g.T1_n.median())), T2=round(float(g.T2_n.median()))),
            share_pf_gt1=dict(T1=round(float((g.T1_pf > 1).mean()), 3), T2=round(float((g.T2_pf > 1).mean()), 3),
                              A=round(float((g.A_pf > 1).mean()), 3), B=round(float((g.B_pf > 1).mean()), 3)),
            share_T1_wr_ge70=round(float((g.T1_wr >= 70).mean()), 3),
            s1=int(s1[ix].sum()), s2=int(s2[ix].sum()), s3=int(s3[ix].sum()), s4=int(s4[ix].sum()), s5=int(s5[ix].sum()),
            base_rate_T2_s2=round(float(i2[ix].mean()), 4),
            rate_T2_s2_given_s1=round(float(i2[ix][s1[ix]].mean()), 4) if s1[ix].any() else None)

    cols = ["fam", "j", "params", "T1_n", "T1_wr", "T1_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf_4t", "A_n", "A_wr", "A_pf", "B_n", "B_wr", "B_pf",
            "plateau", "n_neigh", "s2", "s3", "s4", "s5", "stages_after_s1"]
    OUT["s1_configs"] = R[s1][cols].sort_values(["stages_after_s1", "T2_pf"], ascending=False).head(80).to_dict("records")
    OUT["survivors"] = R[s5][cols].to_dict("records")

    if s5.any():
        C = R[s5].copy(); OUT["portfolio_set"] = "survivors"
    elif s1.any():
        C = R[s1].sort_values(["stages_after_s1", "T2_pf"], ascending=False).head(3).copy(); OUT["portfolio_set"] = "near_survivors"
    else:
        kept = R.apply(lambda x: (x.fam, int(x.j)) in T, axis=1)
        C = R[kept & (R.T1_n >= S1["n"]) & (R.T1_wr >= S1["wr"])].sort_values("T1_pf", ascending=False).head(3).copy()
        OUT["portfolio_set"] = "best_T1_no_s1"
    rows = []
    for i in C.index:
        k = (C.fam[i], int(C.j[i]))
        if k not in T: rows.append(dict(fam=k[0], j=k[1], params=C.params[i], note="no trades kept")); continue
        tr = T[k]["real"]; nm = T[k]["norm"]
        d = six_lib.daily(tr, col_pnl="usd")
        ts = six_lib.tstats(tr.usd, tr.date); ts4 = six_lib.tstats(tr.usd - S5["cost"], tr.date)
        at = six_lib.add_test(d, w=1.0); b, c = at["base"], at["comb"]
        dS1 = c["T1"]["sharpe"] - b["T1"]["sharpe"]; dS2 = c["T2"]["sharpe"] - b["T2"]["sharpe"]
        dd_ok = c["all"]["maxdd"] <= 1.05 * b["all"]["maxdd"]; wm_ok = c["all"]["worst_month"] >= 1.05 * b["all"]["worst_month"]
        acc = bool(dS1 > 0 and dS2 > 0 and dd_ok and wm_ok)
        rows.append(dict(fam=k[0], j=k[1], params=C.params[i], survivor=bool(s5[i]), stages_after_s1=int(C.stages_after_s1[i]),
                         csv=dict(T1=dict(n=int(C.T1_n[i]), wr=C.T1_wr[i], pf=C.T1_pf[i]), T2=dict(n=int(C.T2_n[i]), wr=C.T2_wr[i], pf=C.T2_pf[i]),
                                  T2_pf_4t=C.T2_pf_4t[i], A=dict(n=int(C.A_n[i]), wr=C.A_wr[i], pf=C.A_pf[i]), B=dict(n=int(C.B_n[i]), wr=C.B_wr[i], pf=C.B_pf[i]),
                                  plateau=C.plateau[i], n_neigh=int(C.n_neigh[i])),
                         six=ts, six_plus4t=ts4,
                         per_month=dict(T1=round(float(d[d.index < 20240101].mean() * 21)), T2=round(float(d[d.index >= 20240101].mean() * 21))),
                         corr=at["corr"], ultra=b, ultra_plus=c, dSharpe_T1=round(dS1, 3), dSharpe_T2=round(dS2, 3),
                         maxdd_ok=bool(dd_ok), worst_month_ok=bool(wm_ok), portfolio_accepted=acc))
    OUT["portfolio"] = rows
    OUT["accepted"] = [r for r in rows if r.get("survivor") and r.get("portfolio_accepted")]
    json.dump(OUT, open(os.path.join(HERE, "b9_select.json"), "w"), indent=1, default=str)
    R.to_csv(os.path.join(HERE, "results_b9_staged.csv"), index=False)
    print(json.dumps({f: {k: v for k, v in x.items() if k not in ("median_n",)} for f, x in OUT["families"].items()}, indent=1))
    print("survivors:", len(OUT["survivors"]), "| portfolio set:", OUT["portfolio_set"])
    for r in rows:
        if "note" in r: print(r); continue
        print(r["fam"], r["j"], r["params"], "| surv", r["survivor"], "| csv", r["csv"]["T1"], r["csv"]["T2"], "4t", r["csv"]["T2_pf_4t"],
              "A", r["csv"]["A"], "B", r["csv"]["B"], "plat", r["csv"]["plateau"],
              "| dSharpe", r["dSharpe_T1"], r["dSharpe_T2"], "corr", r["corr"], "DDok", r["maxdd_ok"], "WMok", r["worst_month_ok"], "acc", r["portfolio_accepted"])


if __name__ == "__main__":
    main()
