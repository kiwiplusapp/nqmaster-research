"""Batch 11 selection (2026-10-21, Federico: 'new strategies never tested here, chosen on 2019-2023 and compared on 2023-2026').
Mine: MINE_TAG=b11 MINE_PROCS=2 MINE_T1=20190101 MINE_T2=20230101 python3 run_mine_db.py <15 families of families11.py>
  -> results_b11.csv (real $ per MNQ: T1 = 2019-01..2022-12, T2 = 2023-01..2026-10; cost-normalised 0.345% ATR: A 2010-14, B 2015-18,
     T1n 2019-22, T2n 2023-26), trades_b11.pkl (configs with T1 n >= 80 and PF >= 1.25).
PROTOCOL, fixed before looking at results_b11.csv (same stages as b9 / more_trades, periods as asked):
  s1  choose: T1 real n >= 80, PF >= 1.30, WR >= 50.0, and T1n (cost-normalised) PF >= 1.15        (the only stage used to choose)
  s2  T2 real PF >= 1.20
  s3  A norm PF >= 1.00 and B norm PF >= 1.00 (missing PF = fail)
  s4  stress: T2 with +4 ticks per side ($3.00 per trade) PF >= 1.10
  s5  plateau: >= 2/3 of the one-step NUMERIC neighbours (CATEGORICAL11 axes are not steps; >= 2 neighbours needed) have T1 PF >= 1.15
  s6  one representative per signal (fam + signal params; exits sk / R / exp / nb / t0 / dtf and the daily trend filter are not a signal):
      the survivor with the best T1 PF
  portfolio (s6 representatives, each alone, then all together as information): candidate trades on NQMaster days (ATR >= 150, no FOMC)
      added to the RAW 2027 default set (nt_compare ultra_d4 before its conflict filter) and run through wrq_port.conflict_filter;
      T1p = 2020-10-15..2022-12 (base start), T2p = 2023-01..: Sharpe up in BOTH, max DD and worst month not worse by > 5% in either,
      daily-P&L correlation with the base < 0.3; 21-day block bootstrap (1000 draws) of the Sharpe gain per period (median, p5, p95, P > 0).
  base rates: P(T2 PF >= 1.2) over all cells vs P(T2 PF >= 1.2 | s1) per family and overall.
-> b11_select.json, results_b11_staged.csv, b11_report.md"""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))

S1 = dict(n=80, wr=50.0, pf=1.30, pfn=1.15); S2 = dict(pf=1.20); S3 = dict(A=1.00, B=1.00); S4 = dict(pf=1.10, cost=3.0); S5 = dict(frac=2 / 3, pf=1.15, min_nb=2)
PORT = dict(maxdd_pct=5.0, worst_month_pct=5.0, corr=0.3, boot=1000, block=21)
T1, T2 = 20190101, 20230101
START_P, MID_P = 20201015, 20230101          # portfolio periods (base set starts 2020-10-15)
EXIT_KEYS = {"sk", "R", "exp", "nb", "t0", "dtf"}


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


def signal_key(fam, params):
    p = ast.literal_eval(params); ex = set(EXIT_KEYS)
    if fam not in ("RC_HOLYGRAIL", "RC_ANTI"): ex.add("tf")
    return fam + ":" + repr({k: v for k, v in p.items() if k not in ex})


# ------------------------------------------------------------------------------------------------ portfolio helpers (periods of this batch)
def sharpe(d):
    return round(float(d.mean() / d.std() * np.sqrt(252)), 3) if d.std() > 0 else 0.0


def pmetrics(T, lo, hi, days):
    T = T[(T.date >= lo) & (T.date < hi)]; dd = days[(days >= lo) & (days < hi)]
    x = (T.u * T.w); d = x.groupby(T.date).sum().reindex(dd, fill_value=0.0); eq = d.cumsum()
    mo = d.groupby(pd.to_datetime(d.index.astype(str)).to_period("M")).sum() if len(d) else pd.Series([0.0])
    w = x[x > 0].sum(); l = -x[x <= 0].sum()
    return dict(n=int(len(T)), tpd=round(len(T) / max(1, len(dd)), 3), wr=round(100 * float((T.u > 0).mean()), 2) if len(T) else None,
                pf=round(float(w / l), 3) if l > 0 else None, sharpe=sharpe(d), net=round(float(x.sum())), maxdd=round(float((eq.cummax() - eq).max())),
                worst_month=round(float(mo.min())), avg=round(float(x.mean()), 2) if len(T) else None)


def block_boot(bd, cd, lo, hi, n=1000, block=21, seed=11):
    """Sharpe gain (comb - base) under a joint 21-day block bootstrap of the daily P&L."""
    m = (bd.index >= lo) & (bd.index < hi); b = bd[m].to_numpy(); c = cd[m].to_numpy(); L = len(b)
    if L < 2 * block: return None
    rng = np.random.default_rng(seed); nb = int(np.ceil(L / block)); gains = np.zeros(n)
    for k in range(n):
        st = rng.integers(0, L - block + 1, size=nb); ix = np.concatenate([np.arange(s, s + block) for s in st])[:L]
        bb = b[ix]; cc = c[ix]
        sb = bb.mean() / bb.std() * np.sqrt(252) if bb.std() > 0 else 0.0; sc = cc.mean() / cc.std() * np.sqrt(252) if cc.std() > 0 else 0.0
        gains[k] = sc - sb
    return dict(median=round(float(np.median(gains)), 3), p5=round(float(np.percentile(gains, 5)), 3), p95=round(float(np.percentile(gains, 95)), 3), p_gt0=round(float((gains > 0).mean()), 3))


def portfolio_test(cands, label):
    from more_trades import load_base, ok_days
    from wrq_port import conflict_filter
    raw, base = load_base(); days = np.array(sorted(base.date.unique()))
    C = pd.concat([c[["date", "mod", "tin", "tout", "d", "u", "w"]] for c in cands], ignore_index=True)
    C = C[(C.date >= START_P) & C.date.isin(ok_days())]
    comb = conflict_filter(pd.concat([raw, C], ignore_index=True).sort_values(["date", "tin"], kind="stable").reset_index(drop=True))
    out = {"label": label, "cand_n": int(len(C)), "cand_kept": int(comb["mod"].isin(C["mod"].unique()).sum()), "base": {}, "comb": {}, "delta": {}, "boot": {}}
    ds = lambda T: (T.u * T.w).groupby(T.date).sum().reindex(days, fill_value=0.0)
    cd = ds(C); bd = ds(base); cbd = ds(comb)
    out["corr"] = round(float(np.corrcoef(bd, cd)[0, 1]), 3) if cd.std() > 0 else 0.0
    for lab, lo, hi in (("T1p", START_P, MID_P), ("T2p", MID_P, 20991231)):
        m = (days >= lo) & (days < hi)
        out["corr_" + lab] = round(float(np.corrcoef(bd[m], cd[m])[0, 1]), 3) if cd[m].std() > 0 else 0.0
        b = pmetrics(base, lo, hi, days); c = pmetrics(comb, lo, hi, days); out["base"][lab] = b; out["comb"][lab] = c
        out["delta"][lab] = dict(sharpe=round(c["sharpe"] - b["sharpe"], 3), wr=round((c["wr"] or 0) - (b["wr"] or 0), 2), pf=round((c["pf"] or 0) - (b["pf"] or 0), 3),
                                 maxdd_pct=round(100 * (c["maxdd"] / b["maxdd"] - 1), 1) if b["maxdd"] else 0.0,
                                 worst_month_pct=round(100 * (c["worst_month"] / b["worst_month"] - 1), 1) if b["worst_month"] else 0.0,
                                 net=c["net"] - b["net"], tpd=round(c["tpd"] - b["tpd"], 3), n=c["n"] - b["n"])
        out["boot"][lab] = block_boot(bd, cbd, lo, hi, PORT["boot"], PORT["block"])
    out["base_blocked"] = int(len(base) - comb[~comb["mod"].isin(C["mod"].unique())].shape[0])
    dl = out["delta"]
    chk = dict(sharpe_up=all(dl[l]["sharpe"] > 0 for l in ("T1p", "T2p")), maxdd=all(dl[l]["maxdd_pct"] <= PORT["maxdd_pct"] for l in ("T1p", "T2p")),
               worst_month=all(dl[l]["worst_month_pct"] <= PORT["worst_month_pct"] for l in ("T1p", "T2p")), corr=out["corr"] < PORT["corr"])
    out["checks"] = chk; out["pass"] = all(chk.values())
    return out


def cand_frame(tr, name):
    return pd.DataFrame(dict(date=tr.date.to_numpy(), mod=name, tin=tr.tin.to_numpy(), tout=tr.tout.to_numpy(), d=tr.d.to_numpy(), u=tr.usd.to_numpy(), w=1.0))


# ------------------------------------------------------------------------------------------------ main
def main():
    from families11 import FAMILIES11, CATEGORICAL11
    R = pd.read_csv(os.path.join(HERE, "results_b11.csv"))
    T = pickle.load(open(os.path.join(HERE, "trades_b11.pkl"), "rb"))
    nerr = int(R["err"].notna().sum()) if "err" in R else 0
    if "err" in R: R = R[R["err"].isna()].copy()
    R = R.sort_values(["fam", "j"]).reset_index(drop=True)
    OUT = {"protocol": dict(S1=S1, S2=S2, S3=S3, S4=S4, S5=S5, PORT=PORT, T1=T1, T2=T2, START_P=START_P, MID_P=MID_P, EXIT_KEYS=sorted(EXIT_KEYS)),
           "configs": int(len(R)), "errors": nerr, "families": {}}
    try: OUT["lookahead"] = json.load(open(os.path.join(HERE, "b11_lookahead.json")))["_total"]
    except Exception: OUT["lookahead"] = None

    s1 = ((R.T1_n >= S1["n"]) & (R.T1_wr >= S1["wr"]) & (R.T1_pf >= S1["pf"]) & (R.T1n_pf >= S1["pfn"])).fillna(False)
    i2 = (R.T2_pf >= S2["pf"]).fillna(False); s2 = s1 & i2
    i3 = (R.A_pf >= S3["A"]).fillna(False) & (R.B_pf >= S3["B"]).fillna(False); s3 = s2 & i3
    pf4 = pd.Series(np.nan, index=R.index)
    for i in R.index:
        k = (R.fam[i], int(R.j[i]))
        if k in T:
            tr = T[k]["real"]; u = tr.usd[tr.date >= T2].to_numpy() - S4["cost"]
            pf4[i] = pf(u) if len(u) >= 20 else np.nan
    R["T2_pf_4t"] = pf4; i4 = (R.T2_pf_4t >= S4["pf"]).fillna(False); s4 = s3 & i4
    plat = pd.Series(np.nan, index=R.index); nnb = pd.Series(0, index=R.index)
    for i in R.index[s1]:
        fam = R.fam[i]; G = FAMILIES11[fam][1]; nb = neighbours(R.params[i], G, CATEGORICAL11)
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
        OUT["families"][fam] = dict(
            configs=int(len(g)),
            median_pf=dict(T1=round(float(g.T1_pf.median()), 3), T2=round(float(g.T2_pf.median()), 3), T1n=round(float(g.T1n_pf.median()), 3),
                           A=round(float(g.A_pf.median()), 3), B=round(float(g.B_pf.median()), 3)),
            median_wr=dict(T1=round(float(g.T1_wr.median()), 1), T2=round(float(g.T2_wr.median()), 1)),
            median_n=dict(T1=round(float(g.T1_n.median())), T2=round(float(g.T2_n.median()))),
            share_pf_gt1=dict(T1=round(float((g.T1_pf > 1).mean()), 3), T2=round(float((g.T2_pf > 1).mean()), 3), A=round(float((g.A_pf > 1).mean()), 3), B=round(float((g.B_pf > 1).mean()), 3)),
            best=dict(T1_pf=round(float(g.T1_pf.max()), 3) if g.T1_pf.notna().any() else None, T2_pf=round(float(g.T2_pf.max()), 3) if g.T2_pf.notna().any() else None),
            s1=int(s1[ix].sum()), s2=int(s2[ix].sum()), s3=int(s3[ix].sum()), s4=int(s4[ix].sum()), s5=int(s5[ix].sum()), s6=int(s6[ix].sum()),
            signals=int(g.signal.nunique()),
            base_rate_T2=round(float(i2[ix].mean()), 4), rate_T2_given_s1=round(float(i2[ix][s1[ix]].mean()), 4) if s1[ix].any() else None,
            rate_T2_AB_given_s1=round(float((i2 & i3)[ix][s1[ix]].mean()), 4) if s1[ix].any() else None)
    cols = ["fam", "j", "params", "signal", "T1_n", "T1_wr", "T1_pf", "T1n_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf_4t", "A_n", "A_pf", "B_n", "B_pf", "T2n_pf",
            "plateau", "n_neigh", "s2", "s3", "s4", "s5", "s6", "stages_after_s1"]
    OUT["s1_configs"] = R[s1][cols].sort_values(["stages_after_s1", "T2_pf"], ascending=False).head(100).to_dict("records")
    OUT["survivors"] = R[s5][cols].to_dict("records")
    OUT["representatives"] = R[s6][cols].to_dict("records")

    # portfolio: survivors' representatives; if none, information only on the 3 best near-survivors (ranked by stages passed, then T2 PF)
    if s6.any(): C = R[s6].copy(); OUT["portfolio_set"] = "survivor_representatives"
    elif s1.any(): C = R[s1].sort_values(["stages_after_s1", "T2_pf"], ascending=False).head(3).copy(); OUT["portfolio_set"] = "near_survivors_info_only"
    else:
        kept = R.apply(lambda x: (x.fam, int(x.j)) in T, axis=1)
        C = R[kept].sort_values("T1_pf", ascending=False).head(3).copy(); OUT["portfolio_set"] = "best_T1_info_only"
    rows = []; frames = []
    for i in C.index:
        k = (C.fam[i], int(C.j[i]))
        if k not in T: rows.append(dict(fam=k[0], j=k[1], params=C.params[i], note="no trades kept")); continue
        tr = T[k]["real"]; name = f"{k[0]}#{k[1]}"; cf = cand_frame(tr, name); frames.append(cf)
        pt = portfolio_test([cf], name)
        u = tr.usd.to_numpy(); dt = tr.date.to_numpy()
        per = {}
        for lab, lo, hi in (("T1", T1, T2), ("T2", T2, 20991231)):
            x = u[(dt >= lo) & (dt < hi)]; per[lab] = dict(n=int(len(x)), wr=round(100 * float((x > 0).mean()), 1) if len(x) else None, pf=pf(x), net=round(float(x.sum())),
                                                            per_month=round(float(x.sum()) / max(1, (hi - lo) // 10000 * 12 if hi < 20991231 else 46)))
        rows.append(dict(fam=k[0], j=k[1], params=C.params[i], survivor=bool(s5[i]), representative=bool(s6[i]), stages_after_s1=int(C.stages_after_s1[i]),
                         csv=dict(T1=dict(n=int(C.T1_n[i]), wr=C.T1_wr[i], pf=C.T1_pf[i]), T1n_pf=C.T1n_pf[i], T2=dict(n=int(C.T2_n[i]), wr=C.T2_wr[i], pf=C.T2_pf[i]),
                                  T2_pf_4t=C.T2_pf_4t[i], A_pf=C.A_pf[i], B_pf=C.B_pf[i], plateau=C.plateau[i], n_neigh=int(C.n_neigh[i])),
                         standalone=per, portfolio=pt, portfolio_accepted=bool(pt["pass"])))
    OUT["portfolio"] = rows
    if len(frames) > 1: OUT["portfolio_all_together"] = portfolio_test(frames, "all representatives together (information only)")
    OUT["accepted"] = [r for r in rows if r.get("survivor") and r.get("portfolio_accepted")]
    json.dump(OUT, open(os.path.join(HERE, "b11_select.json"), "w"), indent=1, default=str)
    R.to_csv(os.path.join(HERE, "results_b11_staged.csv"), index=False)
    for f, x in OUT["families"].items():
        print(f, x["configs"], "medPF", x["median_pf"], "s1..s6", x["s1"], x["s2"], x["s3"], x["s4"], x["s5"], x["s6"], "base", x["base_rate_T2"], "given s1", x["rate_T2_given_s1"])
    print("survivors:", len(OUT["survivors"]), "representatives:", len(OUT["representatives"]), "| portfolio set:", OUT["portfolio_set"])
    for r in rows:
        if "note" in r: print(r); continue
        pt = r["portfolio"]
        print(r["fam"], r["j"], r["params"], "| surv", r["survivor"], "| T1", r["csv"]["T1"], "T2", r["csv"]["T2"], "4t", r["csv"]["T2_pf_4t"], "A", r["csv"]["A_pf"], "B", r["csv"]["B_pf"],
              "plat", r["csv"]["plateau"], "| dSharpe", pt["delta"]["T1p"]["sharpe"], pt["delta"]["T2p"]["sharpe"], "corr", pt["corr"], "DD%", pt["delta"]["T1p"]["maxdd_pct"], pt["delta"]["T2p"]["maxdd_pct"],
              "WM%", pt["delta"]["T1p"]["worst_month_pct"], pt["delta"]["T2p"]["worst_month_pct"], "boot", pt["boot"], "acc", r["portfolio_accepted"])


if __name__ == "__main__":
    main()
