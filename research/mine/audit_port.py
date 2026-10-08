"""AUDIT step 5: portfolio-level tests on audit_trades.pkl (1 base contract, weights as coded).
 1 walk-forward of the composition (anchored, yearly): module enters year Y only if, on CFD data up to Y-1,
   rule A: PF >= 1.1 in EVERY prior calendar year with >= 20 trades;  rule B: cumulative PF >= 1.1;  rule C: cumulative PF >= 1.0.
   Year Y is traded on CFD (2021-26) and on REAL (2024-26). Compared with the fixed profile.  (Approximation: removed modules do not
   free trades the conflict filter had blocked; modules were discovered with data to 2026, so this tests composition only.)
 2 leave-one-out and joint removals of flagged modules: Sharpe / WR / PF / $ per month per period, 2015-19 normalised PF of the set.
 3 Monte Carlo: stationary block bootstrap (mean block 20 days) of daily P&L -> 1-year P&L, max drawdown, P(losing 3/6/12-month
   window); plus the historical rolling windows. With and without a forward haircut.
 4 haircut scenarios: +1 tick/side, edge x0.75 and x0.5 (constant deduction per trade) -> WR, PF, Sharpe, $/month.
Output: audit_wf.csv, audit_loo.csv, audit_mc.csv, audit_haircut.csv"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
A = pickle.load(open("audit_trades.pkl", "rb")); P = A["prof"]; L = A["L1519"]
rng = np.random.default_rng(11)
def daily(F, days, extra=0.0): return ((F.u - extra) * F.w).groupby(F.date).sum().reindex(days, fill_value=0.0)
def st(F, days, extra=0.0):
    x = (F.u - extra) * F.w; d = daily(F, days, extra); eq = d.cumsum(); gl = -x[x <= 0].sum()
    return dict(n=len(F), tpd=round(len(F) / max(len(days), 1), 2), wr=round(100 * ((F.u - extra) > 0).mean(), 1) if len(F) else np.nan, pf=round(x[x > 0].sum() / gl, 3) if gl > 0 else np.nan,
                sharpe=round(d.mean() / d.std() * 252 ** .5, 2) if d.std() > 0 else np.nan, mo=round(d.mean() * 21), maxdd=round((eq.cummax() - eq).max()))
def pfu(u): u = np.asarray(u); gl = -u[u <= 0].sum(); return round(u[u > 0].sum() / gl, 3) if gl > 0 else np.nan
L1519MAP = {"Ultra": {"VOLB": "VOLB_U", "VW13": "VW13b", "ORB60": "ORB60"}, "WR70N": {"VOLB": "VOLB_W", "VW13": "VW13b", "ORB60": "ORB60_075"}}
def pf1519(prof, mods):
    """2015-19 cost-normalised PF of a module set (sum of module trades, no conflict filter; ORB90 / MSEQS absent)."""
    u = np.concatenate([L[L1519MAP[prof].get(m, m)].u.to_numpy() for m in mods if L1519MAP[prof].get(m, m) in L])
    return pfu(u)
def boot_idx(n, B, Lb=20):
    idx = np.empty((B, n), np.int64)
    for b in range(B):
        i = 0; p = rng.integers(n)
        while i < n:
            idx[b, i] = p; i += 1
            p = rng.integers(n) if rng.random() < 1 / Lb else (p + 1) % n
    return idx
if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 30)
    # ------------------------------------------------------------------ 1 walk-forward composition
    wf = []
    for prof in ("Ultra", "WR70N"):
        CF = pd.concat([P[prof]["IS"][0], P[prof]["C24"][0]]); CD = np.concatenate([P[prof]["IS"][1], P[prof]["C24"][1]])
        RF, RD = P[prof]["REAL"]; mods = sorted(CF["mod"].unique()); x = CF.assign(y=CF.date // 10000, v=CF.u * CF.w)
        ypf = x.groupby(["mod", "y"]).agg(n=("v", "size"), gp=("v", lambda s: s[s > 0].sum()), gl=("v", lambda s: -s[s <= 0].sum()))
        for Y in range(2021, 2027):
            sel = {}
            for rule in ("A", "B", "C"):
                keep = []
                for m in mods:
                    h = ypf.loc[m] if m in ypf.index.get_level_values(0) else None
                    if h is None: continue
                    h = h[h.index < Y]
                    if len(h) == 0 or h.n.sum() < 20: continue                    # no history yet -> not traded
                    if rule == "A": ok = all((r.gp / r.gl if r.gl > 0 else 9) >= 1.1 for _, r in h[h.n >= 20].iterrows()) and (h.n >= 20).any()
                    else: ok = (h.gp.sum() / h.gl.sum()) >= (1.1 if rule == "B" else 1.0)
                    if ok: keep.append(m)
                sel[rule] = keep
            for src, F, D in (("CFD", CF, CD), ("REAL", RF, RD)):
                if src == "REAL" and Y < 2024: continue
                Fy = F[F.date // 10000 == Y]; Dy = D[D // 10000 == Y]
                if len(Dy) == 0: continue
                r = dict(prof=prof, year=Y, src=src, set="fixed", nmods=len(mods), **st(Fy, Dy)); wf.append(r)
                for rule, keep in sel.items():
                    r = dict(prof=prof, year=Y, src=src, set=f"WF rule {rule}", nmods=len(keep), dropped=",".join(sorted(set(mods) - set(keep))), **st(Fy[Fy["mod"].isin(keep)], Dy)); wf.append(r)
    WF = pd.DataFrame(wf); WF.to_csv("audit_wf.csv", index=False)
    print(WF[["prof", "year", "src", "set", "nmods", "n", "wr", "pf", "sharpe", "mo", "dropped"]].to_string(index=False))
    # aggregate WF vs fixed (2021-26 CFD, 2024-26 REAL)
    agg = []
    for prof in ("Ultra", "WR70N"):
        for src, pers, y0 in (("CFD 2021-26", ("IS", "C24"), 2021), ("REAL 2024-26", ("REAL",), 2024)):
            F = pd.concat([P[prof][p][0] for p in pers]); D = np.concatenate([P[prof][p][1] for p in pers]); F = F[F.date >= y0 * 10000]; D = D[D >= y0 * 10000]
            agg.append(dict(prof=prof, sample=src, set="fixed", **st(F, D)))
            for rule in ("A", "B", "C"):
                parts = []
                for Y in range(y0, 2027):
                    w = WF[(WF.prof == prof) & (WF.year == Y) & (WF.src == src.split()[0]) & (WF.set == f"WF rule {rule}")]
                    if len(w) == 0: continue
                    keep = set(F["mod"].unique()) - set(str(w.dropped.iat[0]).split(",")) if isinstance(w.dropped.iat[0], str) and w.dropped.iat[0] else set(F["mod"].unique())
                    parts.append(F[(F.date // 10000 == Y) & F["mod"].isin(keep)])
                agg.append(dict(prof=prof, sample=src, set=f"WF rule {rule}", **st(pd.concat(parts), D)))
    AG = pd.DataFrame(agg); AG.to_csv("audit_wf_agg.csv", index=False); print(AG.to_string(index=False), flush=True)
    # ------------------------------------------------------------------ 2 leave-one-out and joint removals
    loo = []
    JOINT = {"Ultra": {"-MOM1030": ["MOM1030"], "-ON07": ["ON07"], "-MOM1030-ON07": ["MOM1030", "ON07"], "-MOM1030-ON07-MOM13": ["MOM1030", "ON07", "MOM13"],
                       "-MOM1030-ON07-REV06": ["MOM1030", "ON07", "REV06"], "-fail2015-19 (MOM1030,MOM11,MOM13,ON07,REV06,VW13)": ["MOM1030", "MOM11", "MOM13", "ON07", "REV06", "VW13"],
                       "-recent weak (ENG10,LATEFH)": ["ENG10", "LATEFH"], "-MOM1030-ON07-ENG10-LATEFH": ["MOM1030", "ON07", "ENG10", "LATEFH"]},
             "WR70N": {"-REV06": ["REV06"], "-REV06-VW13": ["REV06", "VW13"], "-fail2015-19 (MOM11,REV06,VW13,VOLB)": ["MOM11", "REV06", "VW13", "VOLB"], "-REV06-VOLB": ["REV06", "VOLB"]}}
    for prof in ("Ultra", "WR70N"):
        mods = sorted(P[prof]["REAL"][0]["mod"].unique())
        sets = {"full": []} | {"-" + m: [m] for m in mods} | JOINT[prof]
        for nm, rem in sets.items():
            r = dict(prof=prof, set=nm)
            for per in ("IS", "C24", "REAL"):
                F, D = P[prof][per]; s = st(F[~F["mod"].isin(rem)], D)
                for k in ("tpd", "wr", "pf", "sharpe", "mo", "maxdd"): r[f"{per}_{k}"] = s[k]
                F6 = F[(F.date >= 20260401) & ~F["mod"].isin(rem)]; D6 = D[D >= 20260401]
                if per != "IS": r[f"{per}_L6_pf"] = st(F6, D6)["pf"]; r[f"{per}_L6_mo"] = st(F6, D6)["mo"]
            r["L1519_pf_set"] = pf1519(prof, [m for m in mods if m not in rem]); loo.append(r)
    LO = pd.DataFrame(loo)
    for prof in ("Ultra", "WR70N"):
        b = LO[(LO.prof == prof) & (LO.set == "full")].iloc[0]
        for per in ("IS", "C24", "REAL"): LO.loc[LO.prof == prof, f"{per}_dSh"] = (LO.loc[LO.prof == prof, f"{per}_sharpe"] - b[f"{per}_sharpe"]).round(2)
    LO.to_csv("audit_loo.csv", index=False)
    print(LO[["prof", "set", "IS_sharpe", "C24_sharpe", "REAL_sharpe", "IS_dSh", "C24_dSh", "REAL_dSh", "IS_wr", "REAL_wr", "IS_pf", "C24_pf", "REAL_pf", "REAL_mo", "REAL_maxdd", "REAL_L6_pf", "L1519_pf_set"]].to_string(index=False), flush=True)
    # ------------------------------------------------------------------ 4 haircut scenarios (constant deduction per weighted trade)
    hc = []
    for prof in ("Ultra", "WR70N", "Ultra+GoldRB", "WR70N+GoldWR"):
        for per in ("C24", "REAL"):
            F, D = P[prof][per]; tick = np.where(F["mod"].astype(str).str.startswith("G:"), 2.0, 1.0)
            mean_tr = float(((F.u - tick) * F.w).sum() / F.w.sum())
            for nm, extra_t, keep in (("history", 0, 1.0), ("+1 tick/side", 1, 1.0), ("+1 tick, edge x0.75", 1, 0.75), ("+1 tick, edge x0.5", 1, 0.5), ("+2 ticks, edge x0.5", 2, 0.5)):
                c = extra_t * tick + (1 - keep) * mean_tr
                s = st(F.assign(u=F.u - c), D); s6 = st(F[F.date >= 20260401].assign(u=(F.u - c)[F.date >= 20260401]), D[D >= 20260401])
                hc.append(dict(prof=prof, per=per, scenario=nm, **s, L6_pf=s6["pf"], L6_mo=s6["mo"]))
    HC = pd.DataFrame(hc); HC.to_csv("audit_haircut.csv", index=False); print(HC.to_string(index=False), flush=True)
    # ------------------------------------------------------------------ 3 Monte Carlo (1 year = 252 days) + historical windows
    mc = []
    for prof in ("Ultra", "WR70N", "Ultra+GoldRB", "WR70N+GoldWR"):
        for lab, pers in (("CFD 2020-26", ("IS", "C24")), ("REAL 2024-26", ("REAL",))):
            F = pd.concat([P[prof][p][0] for p in pers]); D = np.concatenate([P[prof][p][1] for p in pers]); d = daily(F, D).to_numpy()
            tick = np.where(F["mod"].astype(str).str.startswith("G:"), 2.0, 1.0); mean_tr = float(((F.u - tick) * F.w).sum() / F.w.sum())
            dh = daily(F.assign(u=F.u - tick - 0.5 * mean_tr), D).to_numpy()          # haircut: +1 tick and half the edge
            for hn, dd in (("history", d), ("haircut +1t x0.5", dh)):
                I = boot_idx(len(dd), 3000)[:, :252]; Pm = dd[I]; eq = Pm.cumsum(1); mdd = (np.maximum.accumulate(np.maximum(eq, 0), 1) - eq).max(1)
                r = dict(prof=prof, sample=lab, version=hn, mean_mo=round(dd.mean() * 21), yr_p5=round(np.percentile(eq[:, -1], 5)), yr_p50=round(np.percentile(eq[:, -1], 50)), yr_p95=round(np.percentile(eq[:, -1], 95)),
                         P_year_loss=round(float((eq[:, -1] < 0).mean()), 4), maxdd_p50=round(np.percentile(mdd, 50)), maxdd_p95=round(np.percentile(mdd, 95)), maxdd_p99=round(np.percentile(mdd, 99)))
                for w, nm in ((63, "3m"), (126, "6m"), (252, "12m")):
                    if w < 252:
                        cs = np.concatenate([np.zeros((Pm.shape[0], 1)), eq], 1); win = cs[:, w:] - cs[:, :-w]
                        r[f"P_window_loss_{nm}"] = round(float((win < 0).mean()), 4); r[f"P_any_{nm}_loss_in_year"] = round(float((win < 0).any(1).mean()), 3)
                    hcs = np.concatenate([[0], np.cumsum(dd)]); hw = hcs[w:] - hcs[:-w]; r[f"hist_window_loss_{nm}"] = round(float((hw < 0).mean()), 4) if len(hw) else np.nan
                mc.append(r)
    MC = pd.DataFrame(mc); MC.to_csv("audit_mc.csv", index=False); print(MC.to_string(index=False))
    # ------------------------------------------------------------------ 5 module correlation / effective number of bets
    cr = []
    for prof in ("Ultra", "WR70N"):
        for lab, pers in (("CFD 2020-26", ("IS", "C24")), ("REAL 2024-26", ("REAL",))):
            F = pd.concat([P[prof][p][0] for p in pers]); D = np.concatenate([P[prof][p][1] for p in pers])
            Mx = F.assign(x=F.u * F.w).pivot_table(index="date", columns="mod", values="x", aggfunc="sum").reindex(D, fill_value=0.0).fillna(0.0)
            C = Mx.corr().to_numpy(); ev = np.linalg.eigvalsh(C); iu = np.triu_indices_from(C, 1); k = np.unravel_index(np.argmax(np.where(np.triu(np.ones_like(C), 1) > 0, C, -9)), C.shape)
            cr.append(dict(prof=prof, sample=lab, n_mods=C.shape[0], mean_pair_corr=round(float(C[iu].mean()), 3), max_pair=f"{Mx.columns[k[0]]}/{Mx.columns[k[1]]} {C[k]:.2f}",
                           eff_bets=round(float(ev.sum() ** 2 / (ev ** 2).sum()), 1)))
    print(pd.DataFrame(cr).to_string(index=False)); pd.DataFrame(cr).to_csv("audit_corr.csv", index=False)
