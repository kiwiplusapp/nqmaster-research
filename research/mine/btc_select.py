"""Selection on the Bitcoin mining run (run_mine_btc.py -> results_btc.csv, trades_btc.pkl), 2026-10-19.
Protocol fixed BEFORE looking at T2 (task brief):
  1. chosen on T1 only (real $ per MBT 2020-23): n >= 100, WR >= 55 %, PF >= 1.30
  2. out of sample, nothing re-fitted: T2 real 2024-26 PF >= 1.20 (n >= 30);  A 2017-08..2019 cost-normalised PF >= 1.00 (n >= 30);
     +4 ticks per round trip ($2 extra per trade) T2 PF >= 1.10;  plateau: every neighbouring parameter cell (one grid step in
     one parameter) has T1 PF >= 1.15 (a missing / undefined neighbour counts as a fail; at least one neighbour must exist)
  3. luck check: P(stage 2 | stage 1) vs P(stage 2) over all configs
  4. portfolio value: daily $ per MBT added to the 2027 NQ default (nt_compare 'ultra_d4', 1 base contract); accepted only if the
     portfolio Sharpe rises in T1 AND T2, max DD and worst month are not worse by > 5 %, and daily P&L correlation < 0.3;
     block bootstrap (21-day blocks) of the Sharpe gain.
-> btc_select.json, btc_finalists.csv"""
import os, sys, ast, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
START, MID = 20201015, 20240101            # portfolio window = six_lib window (base set starts 2020-10-15)
TICK4 = 4 * 0.25 * 2.0                      # +4 ticks per round trip = $2 per MBT


def st1(R): return (R.T1_n >= 100) & (R.T1_wr >= 55) & (R.T1_pf >= 1.30)
def st2(R): return (R.T2_n >= 30) & (R.T2_pf >= 1.20) & (R.A_n >= 30) & (R.A_pf >= 1.00)


def sharpe(x):
    x = np.asarray(x, float); return float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else 0.0


def metr(x, idx):
    x = pd.Series(np.asarray(x, float), index=idx); eq = x.cumsum()
    mo = x.groupby(pd.to_datetime(x.index.astype(str)).to_period("M")).sum()
    return dict(sharpe=round(sharpe(x), 3), net=round(float(x.sum())), maxdd=round(float((eq.cummax() - eq).max())), worst_month=round(float(mo.min())))


def plateau(R):
    """True when every one-step neighbour (same family, one parameter moved one grid step) has T1 PF >= 1.15."""
    ok = pd.Series(False, index=R.index); P = {i: ast.literal_eval(p) for i, p in R.params.items()}
    for fam, g in R.groupby("fam"):
        keys = list(P[g.index[0]]); vals = {k: sorted({P[i][k] for i in g.index if isinstance(P[i][k], (int, float)) and not isinstance(P[i][k], bool)}) for k in keys}
        index = {tuple(P[i][k] for k in keys): i for i in g.index}
        for i in g.index:
            if not st1(R.loc[[i]]).iloc[0]: continue
            p = P[i]; nb = []
            for k in keys:
                v = vals.get(k, [])
                if not isinstance(p[k], (int, float)) or isinstance(p[k], bool) or len(v) < 2: continue
                j = v.index(p[k])
                for jj in (j - 1, j + 1):
                    if 0 <= jj < len(v):
                        q = dict(p); q[k] = v[jj]; t = tuple(q[kk] for kk in keys)
                        nb.append(index.get(t))
            if not nb: continue
            pfs = [R.T1_pf.get(x, np.nan) if x is not None else np.nan for x in nb]
            ok[i] = all((not np.isnan(z)) and z >= 1.15 for z in pfs)
    return ok


def base_daily():
    import nt_compare
    X, _ = nt_compare.research_set("ultra_d4")
    pnl = (X.u * X.w).groupby(X.date).sum(); pnl = pnl[pnl.index >= START]
    return pnl


def block_boot(b, c, nrep=1000, blk=21, seed=1):
    """Sharpe(base + cand) - Sharpe(base) under a 21-day block bootstrap of the joint daily rows."""
    rng = np.random.default_rng(seed); n = len(b); nb = int(np.ceil(n / blk)); gains = np.empty(nrep)
    b = np.asarray(b, float); c = np.asarray(c, float)
    for r in range(nrep):
        st = rng.integers(0, max(1, n - blk + 1), nb); idx = np.concatenate([np.arange(s, s + blk) for s in st])[:n]
        gains[r] = sharpe(b[idx] + c[idx]) - sharpe(b[idx])
    return dict(median=round(float(np.median(gains)), 3), p05=round(float(np.percentile(gains, 5)), 3), p95=round(float(np.percentile(gains, 95)), 3), p_gain_pos=round(float((gains > 0).mean()), 3))


if __name__ == "__main__":
    R = pd.read_csv(os.path.join(HERE, "results_btc.csv")); T = pickle.load(open(os.path.join(HERE, "trades_btc.pkl"), "rb"))
    if "err" in R: R = R[R.err.isna()].copy()
    s1 = st1(R); s2 = st2(R)
    # +4 ticks on T2 and plateau need the kept trades / the grid
    pf4 = pd.Series(np.nan, index=R.index)
    for i in R.index[s1]:
        k = (R.fam[i], int(R.j[i]))
        if k in T:
            u = T[k]["real"]; u = u[u.date >= MID].usd.to_numpy() - TICK4
            pf4[i] = u[u > 0].sum() / -u[u <= 0].sum() if (u <= 0).any() else np.nan
    R["T2_pf_4t"] = pf4; R["plateau"] = plateau(R)
    s3 = (R.T2_pf_4t >= 1.10) & R.plateau
    OUT = dict(configs=int(len(R)), families=int(R.fam.nunique()), stage1=int(s1.sum()), stage1_and_2=int((s1 & s2).sum()), stage1_2_3=int((s1 & s2 & s3).sum()),
               p_stage2_given_stage1=round(float(s2[s1].mean()), 4) if s1.any() else None, p_stage2_all=round(float(s2.mean()), 4),
               p_stage2_all_with_T2n30=round(float(s2[R.T2_n >= 30].mean()), 4),
               p_T2pf12_given_stage1=round(float(((R.T2_n >= 30) & (R.T2_pf >= 1.2))[s1].mean()), 4) if s1.any() else None,
               p_T2pf12_all=round(float(((R.T2_n >= 30) & (R.T2_pf >= 1.2)).mean()), 4),
               p_T2pf12_given_T1pf_1_12=round(float(((R.T2_n >= 30) & (R.T2_pf >= 1.2))[(R.T1_n >= 100) & (R.T1_pf >= 1.0) & (R.T1_pf < 1.2)].mean()), 4),
               median_pf=dict(A=round(float(R.A_pf.median()), 3), T1=round(float(R.T1_pf.median()), 3), T2=round(float(R.T2_pf.median()), 3), T1n=round(float(R.T1n_pf.median()), 3), T2n=round(float(R.T2n_pf.median()), 3)),
               stage1_by_family=R[s1].fam.value_counts().to_dict(), stage12_by_family=R[s1 & s2].fam.value_counts().to_dict(), final_by_family=R[s1 & s2 & s3].fam.value_counts().to_dict(),
               loose_T1_T2_only=int((s1 & (R.T2_n >= 30) & (R.T2_pf >= 1.2)).sum()))
    print(json.dumps({k: v for k, v in OUT.items() if not isinstance(v, dict)}, indent=1), flush=True)
    print("median PF", OUT["median_pf"]); print("stage1 by family", OUT["stage1_by_family"]); print("stage1&2", OUT["stage12_by_family"]); print("final", OUT["final_by_family"], flush=True)

    # ---- portfolio value vs the 2027 NQ default (ultra_d4)
    B = base_daily(); days = B.index.to_numpy()
    cols = ["fam", "j", "params", "T1_n", "T1_wr", "T1_pf", "T1_avg", "T2_n", "T2_wr", "T2_pf", "T2_avg", "A_n", "A_wr", "A_pf", "T2_pf_4t", "plateau"]
    F = R[s1 & s2].copy()                                   # everything that passed T1 + T2 + A; the 4-tick / plateau flags are reported
    rows = []
    for i, f in F.iterrows():
        k = (f.fam, int(f.j))
        if k not in T: continue
        tr = T[k]["real"]; tr = tr[tr.date >= START]
        x = tr.groupby("date").usd.sum(); idx = np.union1d(days, x.index.to_numpy())
        b = B.reindex(idx, fill_value=0.0); c = x.reindex(idx, fill_value=0.0)
        rec = {c_: f[c_] for c_ in cols}; rec["final"] = bool(s3[i])
        for lab, m in (("T1", idx < MID), ("T2", idx >= MID)):
            mb, mc = metr(b[m], idx[m]), metr(b[m] + c[m], idx[m])
            rec[f"{lab}_corr"] = round(float(np.corrcoef(b[m], c[m])[0, 1]), 3) if c[m].std() > 0 else 0.0
            rec[f"{lab}_sh_base"] = mb["sharpe"]; rec[f"{lab}_sh_plus"] = mc["sharpe"]; rec[f"{lab}_dsh"] = round(mc["sharpe"] - mb["sharpe"], 3)
            rec[f"{lab}_dd_base"] = mb["maxdd"]; rec[f"{lab}_dd_plus"] = mc["maxdd"]; rec[f"{lab}_wm_base"] = mb["worst_month"]; rec[f"{lab}_wm_plus"] = mc["worst_month"]
            rec[f"{lab}_cand_per_month"] = round(float(c[m].mean() * 21)); rec[f"{lab}_cand_sharpe"] = round(sharpe(c[m]), 3)
            rec[f"{lab}_boot"] = block_boot(b[m].to_numpy(), c[m].to_numpy())
        rec["accept"] = bool(rec["final"] and rec["T1_dsh"] > 0 and rec["T2_dsh"] > 0 and rec["T1_corr"] < 0.3 and rec["T2_corr"] < 0.3
                             and all(rec[f"{l}_dd_plus"] <= 1.05 * rec[f"{l}_dd_base"] and rec[f"{l}_wm_plus"] >= 1.05 * rec[f"{l}_wm_base"] for l in ("T1", "T2")))
        rows.append(rec)
    FF = pd.DataFrame(rows)
    OUT["portfolio_base"] = {lab: metr(B[m], days[m]) for lab, m in (("T1", days < MID), ("T2", days >= MID))}
    if len(FF):
        FF = FF.sort_values("T2_dsh", ascending=False); FF.to_csv(os.path.join(HERE, "btc_finalists.csv"), index=False)
        show = ["fam", "j", "T1_n", "T1_wr", "T1_pf", "T2_n", "T2_wr", "T2_pf", "A_pf", "T2_pf_4t", "plateau", "T1_corr", "T2_corr", "T1_dsh", "T2_dsh", "T2_cand_per_month", "accept"]
        print(FF[show].head(40).to_string(), flush=True)
        OUT["finalists"] = FF.head(60).to_dict("records"); OUT["accepted"] = int(FF.accept.sum()); OUT["adds_sharpe_both"] = int(((FF.T1_dsh > 0) & (FF.T2_dsh > 0)).sum())
        # the whole final survivor set as one BTC book (sum of the configs that passed every stage)
        G = FF[FF.final]
        if len(G):
            tr = pd.concat([T[(g.fam, int(g.j))]["real"] for _, g in G.iterrows()], ignore_index=True); tr = tr[tr.date >= START]
            x = tr.groupby("date").usd.sum(); idx = np.union1d(days, x.index.to_numpy()); b = B.reindex(idx, fill_value=0.0); c = x.reindex(idx, fill_value=0.0)
            S = dict(configs=int(len(G)))
            for lab, m in (("T1", idx < MID), ("T2", idx >= MID)):
                u = tr[((tr.date < MID) if lab == "T1" else (tr.date >= MID))].usd.to_numpy(); nd = int(m.sum())
                S[lab] = dict(n=int(len(u)), wr=round(100 * float((u > 0).mean()), 1), pf=round(float(u[u > 0].sum() / -u[u <= 0].sum()), 3) if (u <= 0).any() else None,
                              trades_per_day=round(len(u) / nd, 2), net=round(float(u.sum())), per_month=round(float(u.sum()) / nd * 21), maxdd=metr(c[m], idx[m])["maxdd"],
                              sharpe=round(sharpe(c[m]), 3), corr=round(float(np.corrcoef(b[m], c[m])[0, 1]), 3), base=metr(b[m], idx[m]), plus=metr(b[m] + c[m], idx[m]),
                              boot=block_boot(b[m].to_numpy(), c[m].to_numpy()))
            OUT["survivor_set"] = S; print("survivor set", json.dumps(S, indent=1))
    else:
        print("no config passed stage 1 + 2")
    # nearest misses: best T1 configs and what they did in T2 / A
    NM = R[s1].sort_values("T1_pf", ascending=False).head(25)[["fam", "j", "params", "T1_n", "T1_wr", "T1_pf", "T2_n", "T2_wr", "T2_pf", "A_n", "A_pf", "T2_pf_4t", "plateau"]]
    OUT["top_T1_configs"] = NM.to_dict("records"); print("top T1 configs\n", NM.to_string())
    json.dump(OUT, open(os.path.join(HERE, "btc_select.json"), "w"), indent=1, default=str)
