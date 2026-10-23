"""perturb_analysis (2026-10-19): fragility ranking + pre-registered walk-forward tests + whole-system sensitivity from
perturb_cells.csv (perturb_lab.py).  Decision rules (fixed before looking at any T2 number):
  frag_IS  = mean of [share of the 200 joint draws with module A PF < 1, with B PF < 1, with T1 PF < 1, and with the portfolio
             T1 Sharpe below the base by > 0.1]  -> ranking used for the drop test (k = 1, 2, 3 most fragile)
  frag_T2  = mean of [share draws module T2 PF < 1, share portfolio T2 Sharpe below base by > 0.1]  (reported only)
  plateau centre = cell of the 5^3 factorial (first 3 parameters, +-10 % / +-15 min steps) with the highest MINIMUM standalone
             T1 PF over its 3x3x3 neighbourhood (cells with T1 n < 20 count as -inf); candidates = cells with a full neighbourhood
  smoothing = the 3 best plateau centres of a module, 1/3 lot each
Acceptance of a change (fixed): T2 Sharpe >= base, T2 maxDD <= base x 1.05, T2 PF and WR >= base, trades >= 95 % of base.
-> perturb_lab.json, perturb_report.md"""
import os, sys, json, pickle, itertools, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import perturb_lib as P
from perturb_lab import SCR, PT, PCT, TIM, levels
PERS = ["A", "B", "T1", "T2"]


def lvl_index(mod, eps):
    sp = P.SPEC[mod]; keys = list(sp["pert"])[:3]; out = []
    for k in keys:
        e = eps.get(k, 0.0); step = 15.0 if sp["pert"][k] == "time" else 0.1
        out.append(int(round(e / step)) + 2)
    return tuple(out)


def accept(m, b):
    ok = (m["T2_sharpe"] >= b["T2_sharpe"]) and (m["T2_maxdd"] <= b["T2_maxdd"] * 1.05) and (m["T2_pf"] >= b["T2_pf"]) and (m["T2_wr"] >= b["T2_wr"]) and (m["T2_n"] >= 0.95 * b["T2_n"])
    return bool(ok)


def pm(row, prefix="p_"):
    return {f"{per}_{k}": row[f"{prefix}{per}_{k}"] for per in PERS for k in ("n", "tpd", "wr", "pf", "sharpe", "maxdd", "net", "worst_month")}


def load_tr(mod, kind, idx):
    return pickle.load(open(os.path.join(PT, f"{mod}_{kind}_{idx}.pkl"), "rb"))


def port(parts, drop=(), scale=None, extra=0.0):
    out = {}
    for view in ("real", "norm"):
        X = P.assemble(parts, view, drop)
        if scale:
            for m, s in scale.items(): X.loc[X["mod"].isin([m, m + "b"]), "w"] *= s
        for per, (lo, hi, v) in P.PERIODS.items():
            if v == view:
                mm = P.metrics(X, per, extra=extra if view == "real" else 0.0)
                for k, val in mm.items(): out[f"{per}_{k}"] = val
    return out


if __name__ == "__main__":
    R = pd.read_csv(os.path.join(HERE, "perturb_cells.csv"))
    R = R[R.get("err", pd.Series(index=R.index, dtype=object)).isna()] if "err" in R else R
    R["eps_d"] = R.eps.map(json.loads)
    base_rows = R[R.kind == "base"].set_index("mod"); B = pm(base_rows.iloc[0])
    OUT = {"base": B, "modules": {}, "ranking": [], "walk_forward": {}, "system": {}, "slippage": {}}
    print("BASE", {k: B[k] for k in ("T1_sharpe", "T2_sharpe", "T1_pf", "T2_pf", "T2_maxdd", "T2_n")}, flush=True)
    # ------------------------------------------------------------------ per module
    plateau = {}; top3 = {}
    for mod in P.MODS:
        rm = R[R["mod"] == mod]; b = base_rows.loc[mod]; D = rm[rm.kind == "draw"]
        rec = {"base": {per: dict(n=int(b[f"m_{per}_n"]), wr=b[f"m_{per}_wr"], pf=b[f"m_{per}_pf"], sharpe=b[f"m_{per}_sharpe"]) for per in PERS}, "n_draws": int(len(D))}
        # draws
        dr = {}
        for per in PERS:
            pf = D[f"m_{per}_pf"].to_numpy(float); bp = float(b[f"m_{per}_pf"])
            dr[per] = dict(share_pf_lt_1=round(float(np.nanmean(pf < 1.0)), 3), share_pf_lt_0p9base=round(float(np.nanmean(pf < 0.9 * bp)), 3),
                           pf_median=round(float(np.nanmedian(pf)), 3), pf_p10=round(float(np.nanpercentile(pf, 10)), 3), pf_min=round(float(np.nanmin(pf)), 3),
                           port_sharpe_drop_gt_0p1=round(float(np.mean(D[f"p_{per}_sharpe"] < B[f"{per}_sharpe"] - 0.1)), 3),
                           port_sharpe_median=round(float(D[f"p_{per}_sharpe"].median()), 3), port_sharpe_p10=round(float(D[f"p_{per}_sharpe"].quantile(0.1)), 3),
                           port_maxdd_p90=round(float(D[f"p_{per}_maxdd"].quantile(0.9)), 1))
        rec["draws"] = dr
        rec["frag_IS"] = round(float(np.mean([dr["A"]["share_pf_lt_1"], dr["B"]["share_pf_lt_1"], dr["T1"]["share_pf_lt_1"], dr["T1"]["port_sharpe_drop_gt_0p1"]])), 3)
        rec["frag_T2"] = round(float(np.mean([dr["T2"]["share_pf_lt_1"], dr["T2"]["port_sharpe_drop_gt_0p1"]])), 3)
        rec["frag_IS_rel"] = round(float(np.mean([dr[p]["share_pf_lt_0p9base"] for p in ("A", "B", "T1")] + [dr["T1"]["port_sharpe_drop_gt_0p1"]])), 3)
        # one-at-a-time (single non-zero eps)
        oat = []
        for _, r in rm[rm.kind.isin(["fact", "oat"])].iterrows():
            e = r.eps_d
            if len(e) != 1: continue
            (k, v), = e.items()
            oat.append(dict(param=k, level=v, **{f"{per}_pf": r[f"m_{per}_pf"] for per in PERS}, **{f"{per}_n": int(r[f"m_{per}_n"]) for per in PERS},
                            **{f"port_{per}_dsharpe": round(r[f"p_{per}_sharpe"] - B[f"{per}_sharpe"], 3) for per in PERS}))
        rec["oat"] = sorted(oat, key=lambda x: (x["param"], x["level"]))
        # plateau (factorial of the first 3 params; T1 only)
        F = rm[rm.kind.isin(["fact", "base"])].copy(); F["ix"] = F.eps_d.map(lambda e: lvl_index(mod, e))
        grid = {}
        for _, r in F.iterrows():
            grid[r.ix] = (float(r[f"m_T1_pf"]) if r[f"m_T1_n"] >= 20 else -np.inf, r.kind, int(r.idx), r.eps_d)
        nd = len(list(P.SPEC[mod]["pert"])[:3]); cand = []
        for c in itertools.product(*([(1, 2, 3)] * nd)):
            nb = [tuple(np.add(c, dlt)) for dlt in itertools.product(*([(-1, 0, 1)] * nd))]
            vals = [grid[x][0] for x in nb if x in grid]
            if len(vals) < 3 ** nd or not all(np.isfinite(vals)): continue
            cand.append((min(vals), float(np.mean(vals)), c))
        cand.sort(reverse=True)
        bc = tuple([2] * nd); base_nb = [tuple(np.add(bc, dlt)) for dlt in itertools.product(*([(-1, 0, 1)] * nd))]
        base_min = min(grid[x][0] for x in base_nb if x in grid)
        rec["plateau"] = dict(base_cell_min_T1_pf=round(float(base_min), 3), base_T1_pf=float(b["m_T1_pf"]), n_candidates=len(cand),
                              centre=None if not cand else dict(cell=list(cand[0][2]), eps=grid[cand[0][2]][3], min_T1_pf=round(cand[0][0], 3), mean_T1_pf=round(cand[0][1], 3),
                                                                 T1_pf=round(float(F[F.ix == cand[0][2]].iloc[0]["m_T1_pf"]), 3), T2_pf=round(float(F[F.ix == cand[0][2]].iloc[0]["m_T2_pf"]), 3),
                                                                 A_pf=round(float(F[F.ix == cand[0][2]].iloc[0]["m_A_pf"]), 3), B_pf=round(float(F[F.ix == cand[0][2]].iloc[0]["m_B_pf"]), 3),
                                                                 is_base=cand[0][2] == bc),
                              top3=[dict(cell=list(c), min_T1_pf=round(v, 3), eps=grid[c][3]) for v, _, c in cand[:3]],
                              base_rank=int([c for _, _, c in cand].index(bc)) + 1 if bc in [c for _, _, c in cand] else None,
                              grid_T1_pf_share_lt_1=round(float(np.mean([v[0] < 1 for v in grid.values() if np.isfinite(v[0])])), 3),
                              grid_T2_pf_share_lt_1=round(float((F["m_T2_pf"] < 1).mean()), 3))
        if cand:
            plateau[mod] = (grid[cand[0][2]][1], grid[cand[0][2]][2]); top3[mod] = [(grid[c][1], grid[c][2]) for _, _, c in cand[:3]]
        OUT["modules"][mod] = rec
        print(f"{mod:7s} fragIS {rec['frag_IS']:.3f} fragT2 {rec['frag_T2']:.3f} | T1 PF<1 {dr['T1']['share_pf_lt_1']:.2f} T2 {dr['T2']['share_pf_lt_1']:.2f} A {dr['A']['share_pf_lt_1']:.2f} B {dr['B']['share_pf_lt_1']:.2f} | "
              f"centre {rec['plateau']['centre']['eps'] if rec['plateau']['centre'] else None} base_rank {rec['plateau']['base_rank']}", flush=True)
    rank = sorted(P.MODS, key=lambda m: (-OUT["modules"][m]["frag_IS"], -OUT["modules"][m]["draws"]["T1"]["share_pf_lt_1"]))
    OUT["ranking"] = [dict(mod=m, frag_IS=OUT["modules"][m]["frag_IS"], frag_T2=OUT["modules"][m]["frag_T2"], frag_IS_rel=OUT["modules"][m]["frag_IS_rel"]) for m in rank]
    print("ranking (IS):", rank, flush=True)
    # ------------------------------------------------------------------ whole-system draws + slippage
    Sy = R[R.kind == "sys"]
    for per in PERS:
        OUT["system"][per] = {k: dict(base=B[f"{per}_{k}"], median=round(float(Sy[f"p_{per}_{k}"].median()), 3), p10=round(float(Sy[f"p_{per}_{k}"].quantile(0.1)), 3),
                                      p90=round(float(Sy[f"p_{per}_{k}"].quantile(0.9)), 3), min=round(float(Sy[f"p_{per}_{k}"].min()), 3), max=round(float(Sy[f"p_{per}_{k}"].max()), 3))
                              for k in ("sharpe", "maxdd", "pf", "wr", "n", "net", "worst_month")}
        OUT["system"][per]["share_sharpe_drop_gt_0p1"] = round(float((Sy[f"p_{per}_sharpe"] < B[f"{per}_sharpe"] - 0.1).mean()), 3)
        OUT["system"][per]["share_sharpe_below_base"] = round(float((Sy[f"p_{per}_sharpe"] < B[f"{per}_sharpe"]).mean()), 3)
        OUT["system"][per]["share_pf_lt_1"] = round(float((Sy[f"p_{per}_pf"] < 1.0).mean()), 3)
    OUT["system"]["n_draws"] = int(len(Sy))
    OUT["system"]["corr_T1_T2_sharpe_across_draws"] = round(float(np.corrcoef(Sy.p_T1_sharpe, Sy.p_T2_sharpe)[0, 1]), 3) if len(Sy) > 2 else None
    OUT["system"]["corr_T1_T2_pf_across_draws"] = round(float(np.corrcoef(Sy.p_T1_pf, Sy.p_T2_pf)[0, 1]), 3) if len(Sy) > 2 else None
    for _, r in R[R.kind == "slip"].iterrows(): OUT["slippage"][f"+{int(r.idx)} ticks"] = pm(r)
    print("system T2 sharpe median/p10", OUT["system"]["T2"]["sharpe"], flush=True)
    # ------------------------------------------------------------------ walk-forward tests (assembly needed)
    P.init(); BASE = pickle.load(open(os.path.join(SCR, "base_parts.pkl"), "rb"))
    WF = {"base": port(BASE)}
    for k in (1, 2, 3):
        drop = rank[:k]; m = port(BASE, drop=tuple(drop)); m["dropped"] = drop; m["accepted"] = accept(m, B); WF[f"drop_{k}"] = m
        print("drop", drop, {x: m[x] for x in ("T1_sharpe", "T2_sharpe", "T2_pf", "T2_wr", "T2_maxdd", "T2_n")}, flush=True)
    changed = [m for m in P.MODS if m in plateau and not OUT["modules"][m]["plateau"]["centre"]["is_base"]]
    WF["plateau_changed_modules"] = changed
    def parts_with(mods, chooser):
        parts = dict(BASE)
        for m in mods:
            kind, idx = chooser(m); parts[m] = load_tr(m, kind, idx)
        return parts
    for lab, mods in (("plateau_top3_fragile", [m for m in rank[:3] if m in changed]), ("plateau_all_changed", changed)):
        m = port(parts_with(mods, lambda x: plateau[x])); m["modules"] = mods; m["accepted"] = accept(m, B); WF[lab] = m
        print(lab, mods, {x: m[x] for x in ("T1_sharpe", "T2_sharpe", "T2_pf", "T2_wr", "T2_maxdd", "T2_n")}, flush=True)
    WF["plateau_each"] = {}
    for mod in changed:
        m = port(parts_with([mod], lambda x: plateau[x])); m["accepted"] = accept(m, B); WF["plateau_each"][mod] = m
    # smoothing: 3 best plateau centres, 1/3 lot each
    def smooth_parts(mods):
        parts = dict(BASE)
        for m in mods:
            trs = [load_tr(m, k, i) for k, i in top3[m]]
            parts[m] = tuple(pd.concat([t[v] for t in trs], ignore_index=True) for v in (0, 1))
        return parts
    for lab, mods in (("smooth_top3_fragile", [m for m in rank[:3] if m in top3]), ("smooth_all", [m for m in P.MODS if m in top3])):
        m = port(smooth_parts(mods), scale={x: 1 / 3 for x in mods}); m["modules"] = mods; m["accepted_ex_n"] = bool((m["T2_sharpe"] >= B["T2_sharpe"]) and (m["T2_maxdd"] <= B["T2_maxdd"] * 1.05) and (m["T2_pf"] >= B["T2_pf"]) and (m["T2_wr"] >= B["T2_wr"]))
        WF[lab] = m; print(lab, {x: m[x] for x in ("T1_sharpe", "T2_sharpe", "T2_pf", "T2_wr", "T2_maxdd", "T2_n")}, flush=True)
    OUT["walk_forward"] = WF
    json.dump(OUT, open(os.path.join(HERE, "perturb_lab.json"), "w"), indent=1, default=float)
    print("saved perturb_lab.json", flush=True)
