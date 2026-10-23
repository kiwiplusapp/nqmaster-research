"""Batch 12 selection (2026-10-21), layer B of the delta round.  Protocol FIXED BEFORE running the miner (families12.py,
MINE_TAG=b12 MINE_PROCS=2 MINE_T1=20190101 MINE_T2=20230101 MINE_KEEP_N=60 python3 run_mine_db.py PX_* -> results_b12.csv, trades_b12.pkl):
  s1  T1 (real 2019-01..2022-12): n >= 60, PF >= 1.30                                   (the only stage used to choose)
  s2  T2 (real 2023-01..2026-10): PF >= 1.20
  s3  T2 with +4 ticks per side (usd - 3.0 per trade, from the trades pickle) PF >= 1.10
  s4  delta cell beats its own no-delta CONTROL (same params, dw = none / dcond = none / *_all / price / vol) by >= +0.15 PF in T1 AND T2
      and keeps >= 50% of the control's trades in both (controls themselves cannot pass s4)
  s5  plateau: >= half of the numeric one-step neighbours (T, sk, R, dthr, m, W, z, k, thr) have T1 PF >= 1.15
  regime control (reported, not required): cost-normalised PF 2010-14 (A) and 2015-18 (B)
  survivor = s1..s5 -> portfolio test vs nt_compare.research_set('ultra_d4') with wrq_port.conflict_filter on 2020-10-15..2026-10-08
  (choose 2020-10-15..2022-12, check 2023-01..): Sharpe up in both, max DD / worst month not worse by > 5%, daily corr < 0.3;
  21-day block bootstrap of the daily gain vs the control.  Base rates P(T2 pass | T1 pass) vs P(T2 pass), same for 'beats control'.
-> b12_select.json"""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from delta_orb import neighbours_of, port_test, block_boot, pf
S1 = dict(n=60, pf=1.30); S2 = dict(pf=1.20); S3 = dict(pf=1.10, cost=3.0); S4 = dict(dpf=0.15, keep=0.5); S5 = dict(frac=0.5, pf=1.15)
NUMERIC = ("T", "sk", "R", "dthr", "m", "W", "z", "k", "thr")
PORT1 = (20201015, 20230101); PORT2 = (20230101, 20261009)


def ctrl_params(fam, p):
    if fam == "PX_ORB": return dict(p, dw="none", dthr=0.0)
    if fam == "PX_ABS": return dict(p, dcond="none")
    if fam == "PX_DIV": return dict(p, mode="fade_all" if p["mode"] == "fade_div" else "follow_all")
    if fam == "PX_VFLIP": return dict(p, mode="price")
    return dict(p, src="vol")


_D = None
def ctrl_trades(fam, j, T, FAMILIES12):
    """control trades: from the miner's pickle when kept, else regenerated (same executor, flat 15:55, $1.90 + 1 tick)."""
    global _D
    if (fam, j) in T: return T[(fam, j)]["real"]
    from core import Data, run_events
    if _D is None: _D = Data("nqdb.npz")
    gen, grid, md = FAMILIES12[fam]; return run_events(_D, gen(_D, grid[j]), flat=955, maxday=md, slip=0.25)


def main():
    from families12 import FAMILIES12
    R = pd.read_csv(os.path.join(HERE, "results_b12.csv")); T = pickle.load(open(os.path.join(HERE, "trades_b12.pkl"), "rb"))
    nerr = int(R["err"].notna().sum()) if "err" in R else 0
    if "err" in R: R = R[R["err"].isna()].copy()
    R = R.sort_values(["fam", "j"]).reset_index(drop=True); P = [ast.literal_eval(s) for s in R.params]
    idx = {(R.fam[i], repr(P[i])): i for i in range(len(R))}
    cidx = np.array([idx.get((R.fam[i], repr(ctrl_params(R.fam[i], P[i]))), -1) for i in range(len(R))])
    R["is_ctrl"] = cidx == np.arange(len(R)); R["cidx"] = cidx
    for col in ("T1_pf", "T2_pf", "T1_n", "T2_n", "A_pf", "B_pf"): R["c_" + col] = np.where(cidx >= 0, R[col].to_numpy()[np.maximum(cidx, 0)], np.nan)
    pf4 = pd.Series(np.nan, index=R.index)
    for i in R.index:
        k = (R.fam[i], int(R.j[i]))
        if k in T:
            tr = T[k]["real"]; u = tr.usd[tr.date >= 20230101].to_numpy() - S3["cost"]; pf4[i] = pf(u) if len(u) >= 20 else np.nan
    R["T2_pf_4t"] = pf4
    s1 = ((R.T1_n >= S1["n"]) & (R.T1_pf >= S1["pf"])).fillna(False)
    s2 = s1 & (R.T2_pf >= S2["pf"]).fillna(False); s3 = s2 & (R.T2_pf_4t >= S3["pf"]).fillna(False)
    beat1 = ((R.T1_pf >= R.c_T1_pf + S4["dpf"]) & (R.T1_n >= S4["keep"] * R.c_T1_n)).fillna(False) & ~R.is_ctrl
    beat2 = ((R.T2_pf >= R.c_T2_pf + S4["dpf"]) & (R.T2_n >= S4["keep"] * R.c_T2_n)).fillna(False) & ~R.is_ctrl
    s4 = s3 & beat1 & beat2
    plat = pd.Series(np.nan, index=R.index); caches = {f: {} for f in FAMILIES12}
    for i in R.index[s1 & ~R.is_ctrl]:
        fam = R.fam[i]; G = FAMILIES12[fam][1]; nb = neighbours_of(G[int(R.j[i])], G, NUMERIC, caches[fam])
        sub = R[(R.fam == fam) & (R.j.isin(nb))]
        plat[i] = float((sub.T1_pf >= S5["pf"]).sum()) / len(nb) if nb else np.nan
    R["plateau"] = plat; s5 = s4 & (R.plateau >= S5["frac"]).fillna(False)
    i2 = (R.T2_pf >= S2["pf"]).fillna(False); i3 = (R.T2_pf_4t >= S3["pf"]).fillna(False); i4 = beat1 & beat2; i5 = (R.plateau >= S5["frac"]).fillna(False)
    R["stages_after_s1"] = (i2.astype(int) + i3.astype(int) + i4.astype(int) + i5.astype(int)).where(s1, -1)
    for c_, v in (("s1", s1), ("s2", s2), ("s3", s3), ("s4", s4), ("s5", s5), ("beat_T1", beat1), ("beat_T2", beat2)): R[c_] = v
    OUT = {"protocol": dict(S1=S1, S2=S2, S3=S3, S4=S4, S5=S5, split="T1 2019-2022 / T2 2023-2026-10 real $; A 2010-14 / B 2015-18 cost-normalised"),
           "configs": int(len(R)), "errors": nerr, "families": {}}
    nc = ~R.is_ctrl
    for fam, g in list(R.groupby("fam")) + [("ALL", R)]:
        ix = g.index; gc = g[g.is_ctrl]; gd = g[~g.is_ctrl]
        OUT["families"][fam] = dict(
            configs=int(len(g)), controls=int(len(gc)),
            median_pf=dict(T1=round(float(g.T1_pf.median()), 3), T2=round(float(g.T2_pf.median()), 3), A=round(float(g.A_pf.median()), 3), B=round(float(g.B_pf.median()), 3)),
            ctrl_median_pf=dict(T1=round(float(gc.T1_pf.median()), 3), T2=round(float(gc.T2_pf.median()), 3)) if len(gc) else None,
            delta_minus_ctrl_median=dict(T1=round(float((gd.T1_pf - gd.c_T1_pf).median()), 3), T2=round(float((gd.T2_pf - gd.c_T2_pf).median()), 3)) if len(gd) else None,
            s1=int(s1[ix].sum()), s2=int(s2[ix].sum()), s3=int(s3[ix].sum()), s4=int(s4[ix].sum()), s5=int(s5[ix].sum()),
            p_T2pass=round(float(i2[ix].mean()), 4), p_T2pass_given_T1pass=round(float(i2[ix][s1[ix]].mean()), 4) if s1[ix].any() else None,
            p_beat_T2=round(float(beat2[ix][nc[ix]].mean()), 4) if nc[ix].any() else None,
            p_beat_T2_given_beat_T1=round(float(beat2[ix][nc[ix] & beat1[ix]].mean()), 4) if (nc[ix] & beat1[ix]).any() else None, n_beat_T1=int((nc[ix] & beat1[ix]).sum()))
    # ORB by condition
    g = R[(R.fam == "PX_ORB") & nc].copy(); g["cond"] = [f"{p['dw']}>={p['dthr']}" for p in (P[i] for i in g.index)]
    OUT["orb_by_condition"] = [dict(cond=c, cells=int(len(h)), kept_T1=round(float((h.T1_n / h.c_T1_n).median()), 2), dpf_T1=round(float((h.T1_pf - h.c_T1_pf).median()), 3),
                                    dpf_T2=round(float((h.T2_pf - h.c_T2_pf).median()), 3), beat_both=int((h.beat_T1 & h.beat_T2).sum()), beat_T1=int(h.beat_T1.sum()), beat_T2=int(h.beat_T2.sum()))
                               for c, h in g.groupby("cond")]
    OUT["orb_by_proxy"] = [dict(px=px, dpf_T1=round(float((h.T1_pf - h.c_T1_pf).median()), 3), dpf_T2=round(float((h.T2_pf - h.c_T2_pf).median()), 3), beat_both=int((h.beat_T1 & h.beat_T2).sum()))
                           for px, h in g.groupby(g.params.map(lambda s: ast.literal_eval(s)["px"]))]
    cols = ["fam", "j", "params", "T1_n", "T1_wr", "T1_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf_4t", "A_pf", "B_pf", "c_T1_pf", "c_T2_pf", "plateau", "s2", "s3", "s4", "s5", "stages_after_s1"]
    OUT["s1_configs"] = R[s1][cols].sort_values(["stages_after_s1", "T2_pf"], ascending=False).head(60).to_dict("records")
    OUT["best_controls"] = R[R.is_ctrl].sort_values("T1_pf", ascending=False).head(10)[cols].to_dict("records")
    OUT["survivors"] = R[s5][cols].to_dict("records")
    if s5.any(): C = R[s5]; OUT["portfolio_set"] = "survivors"
    else: C = R[s1 & nc].sort_values(["stages_after_s1", "T2_pf"], ascending=False).head(3); OUT["portfolio_set"] = "near_survivors"
    rows = []
    for i in C.index:
        k = (R.fam[i], int(R.j[i]))
        if k not in T: rows.append(dict(fam=k[0], j=k[1], params=R.params[i], note="no trades kept")); continue
        tr = T[k]["real"]; cand = tr.rename(columns={"usd": "u"})
        pt = port_test(cand, PORT1, PORT2); bb = None
        if R.cidx[i] >= 0:
            ct = ctrl_trades(R.fam[i], int(R.j[R.cidx[i]]), T, FAMILIES12); days = np.array(sorted(set(tr.date) | set(ct.date))); days = days[days >= 20190101]
            g = (tr.usd.groupby(tr.date).sum().reindex(days, fill_value=0.0) - ct.usd.groupby(ct.date).sum().reindex(days, fill_value=0.0))
            bb = dict(all=block_boot(g.to_numpy()), T1=block_boot(g[g.index < 20230101].to_numpy()), T2=block_boot(g[g.index >= 20230101].to_numpy()))
        rows.append(dict(fam=k[0], j=k[1], params=R.params[i], survivor=bool(s5[i]), stages_after_s1=int(R.stages_after_s1[i]),
                         csv={c_: (None if pd.isna(R[c_][i]) else float(R[c_][i])) for c_ in ("T1_n", "T1_wr", "T1_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf_4t", "A_pf", "B_pf", "c_T1_pf", "c_T2_pf", "plateau")},
                         portfolio=pt, boot_gain_vs_control=bb))
    OUT["portfolio"] = rows
    json.dump(OUT, open(os.path.join(HERE, "b12_select.json"), "w"), indent=1, default=lambda x: None if (isinstance(x, float) and np.isnan(x)) else (x.item() if hasattr(x, "item") else str(x)))
    print("configs", len(R), "s1", int(s1.sum()), "s2", int(s2.sum()), "s3", int(s3.sum()), "s4", int(s4.sum()), "s5", int(s5.sum()), "portfolio", OUT["portfolio_set"])
    for f, v in OUT["families"].items(): print(f, {k: v[k] for k in ("configs", "median_pf", "s1", "s2", "s3", "s4", "s5", "p_T2pass", "p_T2pass_given_T1pass", "p_beat_T2", "p_beat_T2_given_beat_T1")})


if __name__ == "__main__":
    main()
