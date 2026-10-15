"""Batch 7 selection (2026-10-16): applies the protocol fixed BEFORE looking at the results of run_mine_db.py
(MINE_TAG=b7, MINE_KEEP_N=60 -> results_b7.csv, trades_b7.pkl; families7.py).
  a) T1 (CSV, real 2020-01..2023-12): n >= 60, PF >= 1.3
  b) T2 (real 2024-01..): PF >= 1.2, n >= 40; +4 ticks stress (-$3 per trade) T2 PF >= 1.1
  c) plateau: >= half of the grid neighbours one step away (one NUMERIC parameter moved to the adjacent grid value;
     categorical parameters in families7.CATEGORICAL are not steps) have T1 PF >= 1.15 (missing PF counts as a fail)
  d) null check: P(T2 PF >= 1.2) over ALL configs vs P(T2 PF >= 1.2 | stage a)
  e) survivors (max 10 by T1 Sharpe, six_lib window 2020-10-15..2023-12) -> six_lib.add_test at weight 1:
     Ultra Sharpe up in T1 AND T2, 6y max DD not worse by > 5%, worst month not worse by > 5%;
     final check: standalone stats recomputed with six_lib.tstats (T1 from 2020-10-15) must still pass a) and b).
  f) median PF per family (T1, T2), share of configs with PF > 1.
-> b7_select.json"""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)


def pf(u):
    u = np.asarray(u, float); l = -u[u <= 0].sum()
    return round(float(u[u > 0].sum() / l), 3) if l > 0 else None


def neighbours(row, R, fam_grid, cat):
    p = ast.literal_eval(row.params); keys = list(fam_grid[0])
    vals = {k: list(dict.fromkeys(g[k] for g in fam_grid)) for k in keys}       # grid order
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
    from families7 import FAMILIES7, CATEGORICAL
    R = pd.read_csv(os.path.join(HERE, "results_b7.csv"))
    T = pickle.load(open(os.path.join(HERE, "trades_b7.pkl"), "rb"))
    nerr = int(R["err"].notna().sum()) if "err" in R else 0
    if "err" in R: R = R[R["err"].isna()].copy()
    R = R.sort_values(["fam", "j"]).reset_index(drop=True)
    OUT = {"configs": int(len(R)), "errors": nerr, "families": {}}

    sa = (R.T1_n >= 60) & (R.T1_pf >= 1.3)
    t2ok = (R.T2_pf >= 1.2).fillna(False)
    # +4 ticks T2 PF (trades available for every stage-a config: run_mine_db keeps T1_n >= 60 & T1_pf >= 1.25)
    pf4 = pd.Series(np.nan, index=R.index)
    for i in R.index[sa]:
        k = (R.fam[i], int(R.j[i]))
        if k in T:
            tr = T[k]["real"]; u = tr.usd[tr.date >= 20240101].to_numpy() - 3.0
            pf4[i] = pf(u) if len(u) else np.nan
    R["T2_pf_4t"] = pf4
    sb = sa & t2ok & (R.T2_n >= 40) & (R.T2_pf_4t >= 1.1).fillna(False)
    # plateau
    plat = pd.Series(np.nan, index=R.index); nnb = pd.Series(0, index=R.index)
    for i in R.index[sa]:
        fam = R.fam[i]; G = FAMILIES7[fam][1]
        nb = neighbours(R.loc[i], R, G, CATEGORICAL)
        sub = R[(R.fam == fam) & (R.j.isin(nb))]
        nnb[i] = len(nb)
        plat[i] = float((sub.T1_pf >= 1.15).sum()) / len(nb) if nb else np.nan
    R["plateau"] = plat; R["n_neigh"] = nnb
    sc = sb & (R.plateau >= 0.5).fillna(False)
    R["stage_a"] = sa; R["stage_b"] = sb; R["stage_c"] = sc

    for fam, g in list(R.groupby("fam")) + [("ALL", R)]:
        a = sa[g.index]
        OUT["families"][fam] = dict(
            configs=int(len(g)),
            median_pf_T1=round(float(g.T1_pf.median()), 3), median_pf_T2=round(float(g.T2_pf.median()), 3),
            share_pf_gt1_T1=round(float((g.T1_pf > 1).mean()), 3), share_pf_gt1_T2=round(float((g.T2_pf > 1).mean()), 3),
            median_pf_A_norm=round(float(g.A_pf.median()), 3), median_pf_B_norm=round(float(g.B_pf.median()), 3),
            stage_a=int(a.sum()), stage_b=int(sb[g.index].sum()), stage_c=int(sc[g.index].sum()),
            base_rate_T2pf_ge_1_2=round(float(t2ok[g.index].mean()), 4),
            base_rate_T2pf_ge_1_2_n40=round(float((t2ok & (R.T2_n >= 40))[g.index].mean()), 4),
            rate_T2pf_ge_1_2_given_a=round(float(t2ok[g.index][a].mean()), 4) if a.any() else None,
            rate_stage_b_given_a=round(float(sb[g.index][a].mean()), 4) if a.any() else None)

    # stage-a table (for the report)
    cols = ["fam", "j", "params", "T1_n", "T1_wr", "T1_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf_4t", "A_pf", "B_pf", "plateau", "n_neigh", "stage_b", "stage_c"]
    OUT["stage_a_configs"] = R[sa][cols].sort_values("T1_pf", ascending=False).head(60).to_dict("records")

    # e) survivors -> portfolio test
    S = R[sc].copy(); rows = []
    for i in S.index:
        k = (S.fam[i], int(S.j[i])); tr = T[k]["real"]
        d = six_lib.daily(tr, col_pnl="usd")
        S.loc[i, "T1_sharpe_six"] = six_lib.metr(d)["T1"]["sharpe"]
    S = S.sort_values("T1_sharpe_six", ascending=False).head(10)
    for i in S.index:
        k = (S.fam[i], int(S.j[i])); tr = T[k]["real"]; nm = T[k]["norm"]
        d = six_lib.daily(tr, col_pnl="usd")
        ts = six_lib.tstats(tr.usd, tr.date); ts4 = six_lib.tstats(tr.usd - 3.0, tr.date)
        at = six_lib.add_test(d, w=1.0)
        b, c = at["base"], at["comb"]
        dS1 = c["T1"]["sharpe"] - b["T1"]["sharpe"]; dS2 = c["T2"]["sharpe"] - b["T2"]["sharpe"]
        dd_ok = c["all"]["maxdd"] <= 1.05 * b["all"]["maxdd"]; wm_ok = c["all"]["worst_month"] >= 1.05 * b["all"]["worst_month"]
        fin = ts["T1"]["n"] >= 60 and (ts["T1"]["pf"] or 0) >= 1.3 and (ts["T2"]["pf"] or 0) >= 1.2 and ts["T2"]["n"] >= 40 and (ts4["T2"]["pf"] or 0) >= 1.1
        acc = bool(dS1 > 0 and dS2 > 0 and dd_ok and wm_ok and fin)
        nA = nm[(nm.date >= 20100601) & (nm.date < 20150101)].usd; nB = nm[(nm.date >= 20150101) & (nm.date < 20200101)].usd
        rows.append(dict(fam=S.fam[i], j=int(S.j[i]), params=S.params[i],
                         csv=dict(T1=dict(n=int(S.T1_n[i]), wr=S.T1_wr[i], pf=S.T1_pf[i]), T2=dict(n=int(S.T2_n[i]), wr=S.T2_wr[i], pf=S.T2_pf[i]),
                                  T2_pf_4t=S.T2_pf_4t[i], A_norm_pf=S.A_pf[i], B_norm_pf=S.B_pf[i], A_n=int(S.A_n[i]), B_n=int(S.B_n[i])),
                         six=ts, six_plus4t=ts4, T1_sharpe_standalone=S.T1_sharpe_six[i],
                         per_month=dict(T1=round(float(d[(d.index < 20240101)].mean() * 21)), T2=round(float(d[d.index >= 20240101].mean() * 21))),
                         plateau=round(float(S.plateau[i]), 3), n_neigh=int(S.n_neigh[i]),
                         corr=at["corr"], ultra=b, ultra_plus=c, dSharpe_T1=round(dS1, 3), dSharpe_T2=round(dS2, 3),
                         maxdd_ok=bool(dd_ok), worst_month_ok=bool(wm_ok), final_check_six=bool(fin), accepted=acc))
    OUT["survivors"] = rows
    OUT["accepted"] = [r for r in rows if r["accepted"]]
    OUT["stage_c_configs"] = R[sc][cols].to_dict("records")

    # correlation of the candidate daily $ with each Ultra module's daily $ (top 4)
    U = six_lib.base(); U = U[U.date >= six_lib.START]
    MODD = {m: (g.w * g.u).groupby(g.date).sum() for m, g in U.groupby("mod")}
    def overlap(tr):
        d = six_lib.daily(tr, col_pnl="usd"); o = {}
        for m, x in MODD.items():
            x = x.reindex(d.index, fill_value=0.0)
            if x.std() > 0 and d.std() > 0: o[m] = round(float(np.corrcoef(d, x)[0, 1]), 3)
        return dict(sorted(o.items(), key=lambda kv: -abs(kv[1]))[:4])
    for r in rows: r["corr_with_ultra_modules"] = overlap(T[(r["fam"], r["j"])]["real"])

    # SUPPLEMENTARY (outside the protocol's top-10 rule, still chosen on T1 only): best stage-c config per family by T1 Sharpe
    sup = []
    Sall = R[sc].copy()
    for i in Sall.index:
        tr = T[(Sall.fam[i], int(Sall.j[i]))]["real"]; Sall.loc[i, "T1_sharpe_six"] = six_lib.metr(six_lib.daily(tr, col_pnl="usd"))["T1"]["sharpe"]
    for fam, g in Sall.groupby("fam"):
        i = g.T1_sharpe_six.idxmax(); k = (fam, int(Sall.j[i])); tr = T[k]["real"]
        d = six_lib.daily(tr, col_pnl="usd"); at = six_lib.add_test(d, w=1.0); b, c = at["base"], at["comb"]
        ts = six_lib.tstats(tr.usd, tr.date); ts4 = six_lib.tstats(tr.usd - 3.0, tr.date)
        sup.append(dict(fam=fam, j=k[1], params=Sall.params[i], n_stage_c_in_family=int(len(g)), six=ts, six_plus4t=ts4,
                        A_norm_pf=Sall.A_pf[i], B_norm_pf=Sall.B_pf[i], plateau=round(float(Sall.plateau[i]), 3), corr=at["corr"],
                        dSharpe_T1=round(c["T1"]["sharpe"] - b["T1"]["sharpe"], 3), dSharpe_T2=round(c["T2"]["sharpe"] - b["T2"]["sharpe"], 3),
                        maxdd=(b["all"]["maxdd"], c["all"]["maxdd"]), worst_month=(b["all"]["worst_month"], c["all"]["worst_month"]),
                        per_month=dict(T1=round(float(d[(d.index < 20240101)].mean() * 21)), T2=round(float(d[d.index >= 20240101].mean() * 21))),
                        corr_with_ultra_modules=overlap(tr)))
    # same for ER_PERSIST per checkpoint T (the protocol's top 10 are all 10:30 configs)
    Sall["grp"] = [f + (":" + str(ast.literal_eval(p)["T"]) if f == "ER_PERSIST" else "") for f, p in zip(Sall.fam, Sall.params)]
    for grp, g in Sall[Sall.fam == "ER_PERSIST"].groupby("grp"):
        i = g.T1_sharpe_six.idxmax(); fam = Sall.fam[i]
        if any(r["fam"] == fam and r["j"] == int(Sall.j[i]) for r in sup): continue
        k = (fam, int(Sall.j[i])); tr = T[k]["real"]
        d = six_lib.daily(tr, col_pnl="usd"); at = six_lib.add_test(d, w=1.0); b, c = at["base"], at["comb"]
        ts = six_lib.tstats(tr.usd, tr.date); ts4 = six_lib.tstats(tr.usd - 3.0, tr.date)
        sup.append(dict(fam=grp, j=k[1], params=Sall.params[i], n_stage_c_in_family=int(len(g)), six=ts, six_plus4t=ts4,
                        A_norm_pf=Sall.A_pf[i], B_norm_pf=Sall.B_pf[i], plateau=round(float(Sall.plateau[i]), 3), corr=at["corr"],
                        dSharpe_T1=round(c["T1"]["sharpe"] - b["T1"]["sharpe"], 3), dSharpe_T2=round(c["T2"]["sharpe"] - b["T2"]["sharpe"], 3),
                        maxdd=(b["all"]["maxdd"], c["all"]["maxdd"]), worst_month=(b["all"]["worst_month"], c["all"]["worst_month"]),
                        per_month=dict(T1=round(float(d[(d.index < 20240101)].mean() * 21)), T2=round(float(d[d.index >= 20240101].mean() * 21))),
                        corr_with_ultra_modules=overlap(tr)))
    OUT["supplementary_best_per_family"] = sup
    for r in sup: print("SUPP", r)
    json.dump(OUT, open(os.path.join(HERE, "b7_select.json"), "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(json.dumps(OUT["families"], indent=1))
    for r in rows:
        print(r["fam"], r["j"], r["params"], r["csv"], "six", r["six"], "corr", r["corr"], "dS", r["dSharpe_T1"], r["dSharpe_T2"],
              "dd", r["ultra"]["all"]["maxdd"], "->", r["ultra_plus"]["all"]["maxdd"], "wm", r["ultra"]["all"]["worst_month"], "->",
              r["ultra_plus"]["all"]["worst_month"], "plateau", r["plateau"], "ACCEPT" if r["accepted"] else "reject")


if __name__ == "__main__":
    main()
