"""wrq_filters: one-feature / one-threshold entry filters per module (thresholds = IS terciles of that module's trades, or the
fixed value 0 for directional features, or one weekday), each with its CURRENT exits. A rule removes trades.
Selection on IS only: WR up >= 0.5 pt AND PF up >= 0.05 AND >= 60% of trades kept; best IS PF per module.
Checks: C24, REAL, L15 (2015-19 cost-normalised), REAL +4 ticks; generalisation of all rules (Spearman IS vs OOS change);
PBO (CSCV, S=16) of 'pick the best rule' per module on the daily P&L 2020-26 CFD.  -> wrq_filters.csv, wrq_filters_sel.csv"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_lib import getD, PER, SLIP, pbo
from wrq_exits import arrays, sim, st

SIGNED = ["tr10", "tr20", "tr50", "r5", "r20", "r60", "vw", "svw", "pdcd", "gap", "m30"]
FEATS = SIGNED + ["atrr", "risk", "onr", "pdr", "pdpos", "dpos", "rv60", "tso"]
EXITS = {}                                   # current exits (Ultra variant of every module)

def module_u(EN, FT, name, m, slip, norm):
    E = EN[name][EN[name]["mod"] == m]; F = FT[name].loc[E.index]
    A = arrays(E); D = getD(name)
    u, ok, out = sim(A, D, slip, EXITS.get(m, {}), norm)
    return E, F, u, ok

def rules_for(F_is):
    R = []
    for f in FEATS:
        x = F_is[f].dropna()
        if len(x) < 30 or x.nunique() < 5: continue
        q1, q2 = x.quantile([1 / 3, 2 / 3])
        R.append((f"{f}<{q1:.3g} out", f, "lt", q1)); R.append((f"{f}>{q2:.3g} out", f, "gt", q2))
        if f in SIGNED:
            R.append((f"{f}<0 out", f, "lt", 0.0)); R.append((f"{f}>0 out", f, "gt", 0.0))
    for k in range(5): R.append((f"dow{k} out", "dow", "eq", float(k)))
    return R

def keep_mask(F, f, op, thr):
    x = F[f].to_numpy()
    if op == "lt": drop = x < thr
    elif op == "gt": drop = x > thr
    else: drop = x == thr
    return ~np.nan_to_num(drop, nan=0).astype(bool)

if __name__ == "__main__":
    EN = pickle.load(open("wrq_entries.pkl", "rb")); FT = pickle.load(open("wrq_feats.pkl", "rb"))
    mods = sorted(EN["nq_1m.npz"]["mod"].unique())
    rows = []; daily = {}
    RUNS = [("IS", "nq_1m.npz", SLIP, False), ("C24", "nq_1m.npz", SLIP, False), ("REAL", "mnq_fut.npz", SLIP, False), ("L15", "nqhd_long.npz", 0.0, True),
            ("REAL+4", "mnq_fut.npz", SLIP * 5, False)]
    for m in mods:
        base = {}
        cache = {}
        for lab, name, slip, norm in RUNS:
            E, F, u, ok = module_u(EN, FT, name, m, slip, norm)
            per = lab.replace("+4", ""); _, lo, hi = PER[per]
            msk = ok & (E.date.to_numpy() >= lo) & (E.date.to_numpy() < hi) & ((~E.fomc.to_numpy()) if per != "L15" else True)
            cache[lab] = (E, F, u, msk)
        E, F, u, msk = cache["IS"]; R = rules_for(F[msk])
        for rn, f, op, thr in [("base", None, None, None)] + R:
            for lab, (E, F, u, msk) in cache.items():
                k = msk & (keep_mask(F, f, op, thr) if f else True)
                n, wr, pf_, ex, net = st(u[k])
                rows.append(dict(mod=m, rule=rn, per=lab, n=n, wr=wr, pf=pf_, exp=ex, net=net, frac=n / max(msk.sum(), 1)))
                if lab in ("IS", "C24"):
                    s = pd.Series(np.where(k, u, 0.0)[msk], index=E.date.to_numpy()[msk]).groupby(level=0).sum()
                    daily.setdefault((m, rn), []).append(s)
        print(m, len(R), flush=True)
    T = pd.DataFrame(rows); T.to_csv("wrq_filters.csv", index=False)
    # ---------------- selection on IS and out-of-sample check
    P = T.pivot_table(index=["mod", "rule"], columns="per", values=["wr", "pf", "exp", "frac", "n"])
    B = P.xs("base", level="rule")
    sel = []
    for m in mods:
        g = P.loc[m]; b = B.loc[m]
        c = g[(g.index != "base") & (g[("wr", "IS")] >= b[("wr", "IS")] + 0.5) & (g[("pf", "IS")] >= b[("pf", "IS")] + 0.05) & (g[("frac", "IS")] >= 0.6)]
        if len(c) == 0: sel.append(dict(mod=m, rule="none")); continue
        r = c.sort_values(("pf", "IS"), ascending=False).iloc[0]; rn = c.sort_values(("pf", "IS"), ascending=False).index[0]
        d = dict(mod=m, rule=rn, n_cands=len(c))
        for per in ("IS", "C24", "REAL", "L15", "REAL+4"):
            d[f"{per} wr"] = f"{b[('wr', per)]:.1f}->{r[('wr', per)]:.1f}"; d[f"{per} pf"] = f"{b[('pf', per)]:.3f}->{r[('pf', per)]:.3f}"
            d[f"{per} dpf"] = r[("pf", per)] - b[("pf", per)]; d[f"{per} dwr"] = r[("wr", per)] - b[("wr", per)]
        sel.append(d)
    S_ = pd.DataFrame(sel); S_.to_csv("wrq_filters_sel.csv", index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
    print(S_[["mod", "rule", "n_cands"] + [f"{p} {c}" for p in ("IS", "C24", "REAL", "L15", "REAL+4") for c in ("wr", "pf")]].to_string())
    ok = S_.dropna(subset=["C24 dpf"])
    print("IS-selected rules:", len(ok), " PF up in C24:", int((ok["C24 dpf"] > 0).sum()), " REAL:", int((ok["REAL dpf"] > 0).sum()), " L15:", int((ok["L15 dpf"] > 0).sum()),
          " all three:", int(((ok["C24 dpf"] > 0) & (ok["REAL dpf"] > 0) & (ok["L15 dpf"] > 0)).sum()))
    # ---------------- generalisation across all rules
    Dd = {}
    for c in ("pf", "wr", "exp"):
        for per in ("IS", "C24", "REAL", "L15"):
            Dd[(c, per)] = P[(c, per)] - B[(c, per)].reindex(P.index.get_level_values(0)).to_numpy()
    Dd = pd.DataFrame(Dd); Dd = Dd[Dd.index.get_level_values(1) != "base"]
    for c in ("pf", "wr", "exp"):
        print(c, "Spearman IS vs", {per: round(Dd[(c, "IS")].corr(Dd[(c, per)], method="spearman"), 3) for per in ("C24", "REAL", "L15")})
    # ---------------- PBO per module (daily P&L 2020-26 CFD, all rules incl. base)
    pr = []
    for m in mods:
        cols = {rn: pd.concat(v) for (mm, rn), v in daily.items() if mm == m}
        M = pd.DataFrame(cols).fillna(0.0).sort_index()
        r = pbo(M.to_numpy()); r["mod"] = m; pr.append(r)
    PB = pd.DataFrame(pr); print(PB.to_string()); PB.to_csv("wrq_filters_pbo.csv", index=False)
