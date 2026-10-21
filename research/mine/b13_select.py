"""Batch 13 selection (2026-10-21, Federico's two video strategies: double top / bottom liquidity sweep and IB to VWAP).
Mine: MINE_TAG=b13 MINE_PROCS=2 MINE_T1=20190101 MINE_T2=20230101 MINE_KEEP_N=60 python3 run_mine_db.py DT_CONT DT_REV IB_FADE IB_BREAK IB_RECLAIM
  -> results_b13.csv (real $ per MNQ: T1 2019-01..2022-12, T2 2023-01..2026-10; cost-normalised 0.345% ATR: A 2010-14, B 2015-18,
     T1n, T2n), trades_b13.pkl (configs with T1 n >= 60 and PF >= 1.25).
PROTOCOL, fixed before looking at results_b13.csv (identical to batch 11, b11_select.py):
  s1  choose: T1 real n >= 80, PF >= 1.30, WR >= 50.0, and T1n PF >= 1.15          (the only stage used to choose)
  s2  T2 real PF >= 1.20
  s3  A norm PF >= 1.00 and B norm PF >= 1.00 (missing PF = fail)
  s4  T2 with +4 ticks per side ($3.00 per trade) PF >= 1.10
  s5  plateau: >= 2/3 of the one-step NUMERIC neighbours (>= 2 neighbours; CATEGORICAL13 axes are not steps) have T1 PF >= 1.15
  s6  one representative per signal (exits st / R / tgt / sk / tg / wait and the context filters filt / ctx / tf are not a signal):
      the survivor with the best T1 PF
  portfolio: as b11 (raw ultra_d4 + candidate on NQMaster days -> wrq_port.conflict_filter; T1p 2020-10-15..2022-12, T2p 2023-01..;
      Sharpe up in both, max DD / worst month <= +5%, corr < 0.3, 21-day block bootstrap of the Sharpe gain).
  extra (information): base rates per family, F1 continuation vs reversal, filter none / vwap / sma200 / trend with vs without, and the
      ultra_d4 base on days with a double top / bottom sweep vs other days.
-> b13_select.json, results_b13_staged.csv"""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from b11_select import pf, neighbours, pmetrics, sharpe, portfolio_test, cand_frame, S1, S2, S3, S4, S5, PORT, START_P, MID_P

T1, T2 = 20190101, 20230101
EXIT_KEYS = {"st", "R", "tgt", "sk", "tg", "wait", "filt", "ctx", "tf"}


def signal_key(fam, params):
    p = ast.literal_eval(params); return fam + ":" + repr({k: v for k, v in p.items() if k not in EXIT_KEYS})


def med(s):
    s = s.dropna(); return round(float(s.median()), 3) if len(s) else None


def group_table(R, i2, s1, keys):
    rows = []
    for k, g in R.groupby(keys):
        ix = g.index
        rows.append(dict(key=k if isinstance(k, tuple) else (k,), configs=int(len(g)), med_T1=med(g.T1_pf), med_T2=med(g.T2_pf), med_A=med(g.A_pf), med_B=med(g.B_pf),
                         med_wr_T1=med(g.T1_wr), med_wr_T2=med(g.T2_wr), med_n_T1=med(g.T1_n), share_T2_gt1=round(float((g.T2_pf > 1).mean()), 3),
                         s1=int(s1[ix].sum()), s5=int(g.s5.sum()), p_T2=round(float(i2[ix].mean()), 3),
                         p_T2_given_s1=round(float(i2[ix][s1[ix]].mean()), 3) if s1[ix].any() else None))
    return rows


def sweep_days():
    """Days with a double top / bottom sweep in RTH (canonical cell: 5m and 15m bars, k 2, tol 0.05 ATR, sweep 1 tick, no filter)."""
    from core import Data
    from families13 import gen_dt_cont
    D = Data("nqdb.npz"); out = {}
    for bar in (5, 15):
        ev = gen_dt_cont(D, dict(bar=bar, k=2, tol=0.05, win="rth", filt="none", b=0.0, st=0.25, R=1.0))
        out[bar] = set(D.date[ev["i"]].tolist())
    return out


def base_by_sweep(SD):
    from more_trades import load_base, ok_days
    raw, base = load_base(); days = np.array(sorted(d for d in ok_days() if d >= START_P))
    dP = (base.u * base.w).groupby(base.date).sum().reindex(days, fill_value=0.0)
    res = {}
    for bar, sd in SD.items():
        for lab, lo, hi in (("T1p", START_P, MID_P), ("T2p", MID_P, 20991231)):
            for nm, m in (("sweep", np.isin(days, list(sd))), ("other", ~np.isin(days, list(sd)))):
                mm = m & (days >= lo) & (days < hi); dd = set(days[mm].tolist()); T = base[base.date.isin(dd)]; x = T.u * T.w
                res[f"{bar}m_{lab}_{nm}"] = dict(days=int(mm.sum()), trades=int(len(T)), wr=round(100 * float((T.u > 0).mean()), 1) if len(T) else None,
                                                 pf=pf(x), usd_per_day=round(float(dP[mm].mean()), 1), share_days=round(float(mm.sum() / max(1, ((days >= lo) & (days < hi)).sum())), 3))
    return res


def main():
    from families13 import FAMILIES13, CATEGORICAL13
    R = pd.read_csv(os.path.join(HERE, "results_b13.csv")); T = pickle.load(open(os.path.join(HERE, "trades_b13.pkl"), "rb"))
    nerr = int(R["err"].notna().sum()) if "err" in R else 0
    if "err" in R: R = R[R["err"].isna()].copy()
    R = R.sort_values(["fam", "j"]).reset_index(drop=True)
    P = [ast.literal_eval(p) for p in R.params]
    for key in ("bar", "win", "filt", "ent", "ctx", "tf", "ib"): R[key] = [str(p.get(key, "")) for p in P]
    OUT = {"protocol": dict(S1=S1, S2=S2, S3=S3, S4=S4, S5=S5, PORT=PORT, T1=T1, T2=T2, START_P=START_P, MID_P=MID_P, EXIT_KEYS=sorted(EXIT_KEYS)),
           "configs": int(len(R)), "errors": nerr, "families": {}}
    try: OUT["lookahead"] = json.load(open(os.path.join(HERE, "b13_lookahead.json")))["_total"]
    except Exception: OUT["lookahead"] = None
    s1 = ((R.T1_n >= S1["n"]) & (R.T1_wr >= S1["wr"]) & (R.T1_pf >= S1["pf"]) & (R.T1n_pf >= S1["pfn"])).fillna(False)
    i2 = (R.T2_pf >= S2["pf"]).fillna(False); s2 = s1 & i2
    i3 = (R.A_pf >= S3["A"]).fillna(False) & (R.B_pf >= S3["B"]).fillna(False); s3 = s2 & i3
    pf4 = pd.Series(np.nan, index=R.index)
    for i in R.index:
        k = (R.fam[i], int(R.j[i]))
        if k in T:
            tr = T[k]["real"]; u = tr.usd[tr.date >= T2].to_numpy() - S4["cost"]; pf4[i] = pf(u) if len(u) >= 20 else np.nan
    R["T2_pf_4t"] = pf4; i4 = (R.T2_pf_4t >= S4["pf"]).fillna(False); s4 = s3 & i4
    plat = pd.Series(np.nan, index=R.index); nnb = pd.Series(0, index=R.index)
    for i in R.index[s1]:
        fam = R.fam[i]; G = FAMILIES13[fam][1]; nb = neighbours(R.params[i], G, CATEGORICAL13)
        sub = R[(R.fam == fam) & (R.j.isin(nb))]; nnb[i] = len(nb)
        plat[i] = float((sub.T1_pf >= S5["pf"]).sum()) / len(nb) if nb else np.nan
    R["plateau"] = plat; R["n_neigh"] = nnb
    i5 = ((R.plateau >= S5["frac"] - 1e-9) & (R.n_neigh >= S5["min_nb"])).fillna(False); s5 = s4 & i5
    R["signal"] = [signal_key(f, p) for f, p in zip(R.fam, R.params)]
    s6 = pd.Series(False, index=R.index)
    for sig, g in R[s5].groupby("signal"): s6[g.T1_pf.idxmax()] = True
    R["stages_after_s1"] = (i2.astype(int) + i3.astype(int) + i4.astype(int) + i5.astype(int)).where(s1, -1)
    for nm, s in (("s1", s1), ("s2", s2), ("s3", s3), ("s4", s4), ("s5", s5), ("s6", s6)): R[nm] = s
    for fam, g in list(R.groupby("fam")) + [("ALL", R)]:
        ix = g.index
        OUT["families"][fam] = dict(configs=int(len(g)), median_pf=dict(T1=med(g.T1_pf), T2=med(g.T2_pf), T1n=med(g.T1n_pf), A=med(g.A_pf), B=med(g.B_pf)),
                                    median_wr=dict(T1=med(g.T1_wr), T2=med(g.T2_wr)), median_n=dict(T1=med(g.T1_n), T2=med(g.T2_n)),
                                    share_pf_gt1=dict(T1=round(float((g.T1_pf > 1).mean()), 3), T2=round(float((g.T2_pf > 1).mean()), 3), A=round(float((g.A_pf > 1).mean()), 3), B=round(float((g.B_pf > 1).mean()), 3)),
                                    best=dict(T1_pf=med(g.T1_pf.nlargest(1)), T2_pf=med(g.T2_pf.nlargest(1))),
                                    s1=int(s1[ix].sum()), s2=int(s2[ix].sum()), s3=int(s3[ix].sum()), s4=int(s4[ix].sum()), s5=int(s5[ix].sum()), s6=int(s6[ix].sum()),
                                    signals=int(g.signal.nunique()), base_rate_T2=round(float(i2[ix].mean()), 4),
                                    rate_T2_given_s1=round(float(i2[ix][s1[ix]].mean()), 4) if s1[ix].any() else None,
                                    rate_T2_AB_given_s1=round(float((i2 & i3)[ix][s1[ix]].mean()), 4) if s1[ix].any() else None)
    DT = R[R.fam.isin(["DT_CONT", "DT_REV"])]
    OUT["tables"] = dict(dt_fam_win=group_table(DT, i2, s1, ["fam", "win"]), dt_fam_filt=group_table(DT, i2, s1, ["fam", "filt"]),
                         dt_fam_bar=group_table(DT, i2, s1, ["fam", "bar"]), dt_fam_win_filt=group_table(DT, i2, s1, ["fam", "win", "filt"]),
                         dtrev_ent=group_table(R[R.fam == "DT_REV"], i2, s1, ["ent"]), ib_fade_tf=group_table(R[R.fam == "IB_FADE"], i2, s1, ["tf", "ent"]),
                         ib_break_ctx=group_table(R[R.fam == "IB_BREAK"], i2, s1, ["ctx"]), ib_reclaim_tf=group_table(R[R.fam == "IB_RECLAIM"], i2, s1, ["tf"]))
    cols = ["fam", "j", "params", "signal", "T1_n", "T1_wr", "T1_pf", "T1n_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf_4t", "A_n", "A_pf", "B_n", "B_pf", "T2n_pf",
            "plateau", "n_neigh", "s2", "s3", "s4", "s5", "s6", "stages_after_s1"]
    OUT["s1_configs"] = R[s1][cols].sort_values(["stages_after_s1", "T2_pf"], ascending=False).head(60).to_dict("records")
    OUT["survivors"] = R[s5][cols].to_dict("records"); OUT["representatives"] = R[s6][cols].to_dict("records")
    if s6.any(): C = R[s6].copy(); OUT["portfolio_set"] = "survivor_representatives"
    elif s1.any(): C = R[s1].sort_values(["stages_after_s1", "T2_pf"], ascending=False).head(3).copy(); OUT["portfolio_set"] = "near_survivors_info_only"
    else:
        kept = R.apply(lambda x: (x.fam, int(x.j)) in T, axis=1); C = R[kept].sort_values("T1_pf", ascending=False).head(3).copy(); OUT["portfolio_set"] = "best_T1_info_only"
    rows = []; frames = []
    for i in C.index:
        k = (C.fam[i], int(C.j[i]))
        if k not in T: rows.append(dict(fam=k[0], j=k[1], params=C.params[i], note="no trades kept")); continue
        tr = T[k]["real"]; name = f"{k[0]}#{k[1]}"; cf = cand_frame(tr, name); frames.append(cf); pt = portfolio_test([cf], name)
        yr = tr.assign(y=tr.date // 10000).groupby("y").usd.agg(lambda u: pf(u.to_numpy())).to_dict()
        rows.append(dict(fam=k[0], j=k[1], params=C.params[i], survivor=bool(s5[i]), representative=bool(s6[i]), stages_after_s1=int(C.stages_after_s1[i]),
                         csv=dict(T1=dict(n=int(C.T1_n[i]), wr=C.T1_wr[i], pf=C.T1_pf[i]), T1n_pf=C.T1n_pf[i], T2=dict(n=int(C.T2_n[i]), wr=C.T2_wr[i], pf=C.T2_pf[i]),
                                  T2_pf_4t=C.T2_pf_4t[i], A_pf=C.A_pf[i], B_pf=C.B_pf[i], plateau=C.plateau[i], n_neigh=int(C.n_neigh[i])),
                         pf_by_year=yr, portfolio=pt, portfolio_accepted=bool(pt["pass"])))
    OUT["portfolio"] = rows
    if len(frames) > 1: OUT["portfolio_all_together"] = portfolio_test(frames, "all together (information only)")
    OUT["accepted"] = [r for r in rows if r.get("survivor") and r.get("portfolio_accepted")]
    OUT["base_on_sweep_days"] = base_by_sweep(sweep_days())
    json.dump(OUT, open(os.path.join(HERE, "b13_select.json"), "w"), indent=1, default=str)
    R.to_csv(os.path.join(HERE, "results_b13_staged.csv"), index=False)
    for f, x in OUT["families"].items():
        print(f, x["configs"], "medPF", x["median_pf"], "WR", x["median_wr"], "s1..s6", x["s1"], x["s2"], x["s3"], x["s4"], x["s5"], x["s6"], "base", x["base_rate_T2"], "given s1", x["rate_T2_given_s1"], x["rate_T2_AB_given_s1"])
    for t, rws in OUT["tables"].items():
        print("--", t)
        for r in rws: print("  ", r)
    print("survivors:", len(OUT["survivors"]), "representatives:", len(OUT["representatives"]), "| portfolio set:", OUT["portfolio_set"])
    for r in rows:
        if "note" in r: print(r); continue
        pt = r["portfolio"]
        print(r["fam"], r["j"], r["params"], "| surv", r["survivor"], "| T1", r["csv"]["T1"], "T2", r["csv"]["T2"], "4t", r["csv"]["T2_pf_4t"], "A", r["csv"]["A_pf"], "B", r["csv"]["B_pf"],
              "plat", r["csv"]["plateau"], "| dSharpe", pt["delta"]["T1p"]["sharpe"], pt["delta"]["T2p"]["sharpe"], "corr", pt["corr"], "DD%", pt["delta"]["T1p"]["maxdd_pct"], pt["delta"]["T2p"]["maxdd_pct"],
              "WM%", pt["delta"]["T1p"]["worst_month_pct"], pt["delta"]["T2p"]["worst_month_pct"], "boot", pt["boot"], "acc", r["portfolio_accepted"], "yr", r["pf_by_year"])
    if "portfolio_all_together" in OUT: print("ALL", OUT["portfolio_all_together"]["delta"], OUT["portfolio_all_together"]["corr"])
    print("base on sweep days", json.dumps(OUT["base_on_sweep_days"]))


if __name__ == "__main__":
    main()
