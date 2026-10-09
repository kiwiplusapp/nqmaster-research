"""AUDIT step 4 (original modules: clock modules MOM11 / MOM13 / MOM1030 / ON07 / REV06, LON, ICT (corrected), CRT11, MSEQ, ORB60/90).
 a) PBO (CSCV, S=16, CFD 2020-26 daily P&L) of the search each module was picked from, re-run in full:
      time-of-day map (tmom grid, ~8.5k configs) for the clock modules, London grid (3,456) for LON, ICT-fix 5-min grid (3,840) for ICT;
    plus IS -> OOS (top IS configs -> C24 / REAL PF) and the chosen config's percentile; and target-variant PBO (variants_ext) per module.
 b) one-parameter neighbours of the chosen config (re-run directly: CFD IS / C24, MNQ REAL, 2015-19 cost-normalised) for the
    clock modules, LON and ICT; from the existing grids for CRT11 (crt2.csv) and MSEQ (wr60_focus.csv); target variants for ORB.
Costs: these research sims charge $1.00 RT -> $0.90 is subtracted per trade here ($1.90 RT + 1 tick per side).
Output: audit_oldmods.json, audit_neighbours_old.csv"""
import os, sys, json, itertools, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
import tmom, london, ict_fix
from ict import day_levels as ict_levels
from news import NEWS
from audit_family import pbo
FOMC = set(NEWS["FOMC"])
def load(n):
    z = np.load(os.path.join(RES, "data", n)); return {k: z[k] for k in z.files}
def pfu(u):
    u = np.asarray(u); gl = -u[u <= 0].sum(); return float(u[u > 0].sum() / gl) if gl > 0 and len(u) >= 20 else np.nan
def clean(df, lo=20200201, hi=3e7):
    return df[(df.date >= lo) & (df.date < hi) & ~df.date.isin(FOMC)]
D = {k: load(n) for k, n in (("cfd", "nq_1m.npz"), ("real", "mnq_fut.npz"), ("long", "nqhd_long.npz"))}
X = {k: ict_levels(v) for k, v in D.items()}                 # (levels, atr, trend) per day id
ATRL = pd.Series(X["long"][1], index=None)
dd_long = pd.DataFrame(dict(day=D["long"]["dayid"], date=D["long"]["date"])).groupby("day").date.last()
ATR_BY_DATE = pd.Series(X["long"][1][dd_long.index.to_numpy()], index=dd_long.to_numpy()); ATR_BY_DATE = ATR_BY_DATE[~ATR_BY_DATE.index.duplicated()]
def norm1519(df):
    df = clean(df, 20150201, 20200101); a = df.date.map(ATR_BY_DATE).to_numpy(); return (df.pts.to_numpy() + 0.5 - 0.00345 * a) / a * 100
def three(fn):
    """fn(key) -> trades df with pts, usd ($1 RT), date. Returns IS / C24 / REAL PF ($1.90) + 2015-19 normalised PF."""
    a = clean(fn("cfd")); b = clean(fn("real"), 20240201); l = fn("long")
    ua = a.usd - 0.9; return dict(IS_n=int((a.date < 20240101).sum()), IS_pf=pfu(ua[a.date < 20240101]), C24_pf=pfu(ua[a.date >= 20240101]), REAL_n=len(b), REAL_pf=pfu(b.usd - 0.9),
                                   L1519_pf=pfu(norm1519(l)), L1519_n=int(((l.date >= 20150201) & (l.date < 20200101)).sum()))
def degrade(stats, chosen_key):
    ok = stats[(stats.IS_n >= 100) & stats.IS_pf.notna()]; rk = ok.sort_values("IS_pf", ascending=False); r = {}
    for top in (1, 10, 50):
        t = rk.head(top); r[f"top{top}"] = dict(IS=round(float(t.IS_pf.median()), 3), C24=round(float(t.C24_pf.median()), 3), REAL=round(float(t.REAL_pf.median()), 3))
    r["family_median"] = dict(IS=round(float(ok.IS_pf.median()), 3), C24=round(float(ok.C24_pf.median()), 3), REAL=round(float(ok.REAL_pf.median()), 3))
    r["spearman_IS_REAL"] = round(float(ok[["IS_pf", "REAL_pf"]].corr(method="spearman").iloc[0, 1]), 3)
    if chosen_key is not None and chosen_key in stats.index:
        c = stats.loc[chosen_key]; r["chosen"] = dict(IS=round(float(c.IS_pf), 3), C24=round(float(c.C24_pf), 3), REAL=round(float(c.REAL_pf), 3))
        r["chosen_IS_pct"] = round(float((ok.IS_pf < c.IS_pf).mean()), 3); r["chosen_REAL_pct"] = round(float((ok.REAL_pf < c.REAL_pf).mean()), 3)
    return r
CACHE = os.path.join(os.environ.get("AUDIT_TMP", "/tmp"), "audit_oldmods_cache.pkl")
def family(name, configs, runner, chosen=None):
    """configs: list of param tuples; runner(key, cfg) -> df(date, usd). PBO on CFD 2020-26 daily ($1.90), IS->OOS stats."""
    import pickle
    cache = pickle.load(open(CACHE, "rb")) if os.path.exists(CACHE) else {}
    if name in cache:
        r, S = cache[name]; print(name, "(cached)", r, flush=True); return r, S
    cols = {}; st = []
    alld = np.array(sorted(set(D["cfd"]["date"][D["cfd"]["date"] >= 20200201]) - FOMC))
    for c in configs:
        a = clean(runner("cfd", c)); b = clean(runner("real", c), 20240201); ua = a.usd - 0.9
        st.append(dict(key=str(c), IS_n=int((a.date < 20240101).sum()), IS_pf=pfu(ua[a.date < 20240101]), C24_pf=pfu(ua[a.date >= 20240101]), REAL_pf=pfu(b.usd - 0.9)))
        if len(a) >= 100: cols[str(c)] = (a.assign(u=ua)).groupby("date").u.sum()
    S = pd.DataFrame(st).set_index("key"); M = pd.DataFrame(cols).reindex(alld, fill_value=0.0).fillna(0.0)
    r = dict(configs=len(configs), pbo=pbo(M.to_numpy()), **degrade(S, None if chosen is None else str(chosen))); print(name, r, flush=True)
    cache[name] = (r, S); pickle.dump(cache, open(CACHE, "wb")); return r, S
J = {}; NB = []
if __name__ == "__main__":
    # ---------------------------------------------------------------- clock modules (tmom)
    def tm(key, c): t, L, rev, sk, R, H, tf = c; return tmom.run(D[key], X[key], t, L, rev, sk, R, H, tf)
    grid = [c for c in itertools.product(tmom.TIMES, (30, 60, 120, -1, -2), (0, 1), (0.1, 0.2), (0.3, 0.5, 1.0), (60, 240, 100000), (0, 1)) if not (c[1] == -2 and not (570 < c[0] < 960))]
    CL = {"MOM11": (660, -2, 0, 0.25, 0.3, 100000, 0), "MOM13": (780, -2, 0, 0.2, 1.0, 240, 1), "MOM1030": (630, -2, 0, 0.2, 0.3, 60, 1),
          "ON07": (420, 30, 0, 0.2, 1.0, 60, 1), "REV06": (360, 30, 1, 0.2, 0.3, 240, 1)}
    r, S = family("time map", grid, tm, None)
    J["time_map"] = r
    for m, c in CL.items():
        cg = str(c) if str(c) in S.index else str((c[0], c[1], c[2], 0.2, c[4], c[5], c[6]))
        J.setdefault(m, {})["family"] = "time map (tmom)"; J[m]["chosen_in_map"] = dict(key=str(cg), **{k: (round(float(v), 3) if pd.notna(v) else None) for k, v in S.loc[[cg]].iloc[0].items()})
        J[m]["chosen_IS_pct"] = round(float((S[S.IS_n >= 100].IS_pf < S.loc[[cg]].IS_pf.iloc[0]).mean()), 3)
        J[m]["chosen_REAL_pct"] = round(float((S[S.IS_n >= 100].REAL_pf < S.loc[[cg]].REAL_pf.iloc[0]).mean()), 3)
        # neighbours (exact chosen params, incl. sk 0.25 for MOM11)
        t, L, rev, sk, R, H, tf = c; nbs = []
        for dt in (-30, -15, 15, 30):
            tt = t + dt; nbs.append(("t", tt, (tt, L, rev, sk, R, H, tf)))
        for v in {30: (60,), 60: (30, 120), 120: (60,), -1: (-2,), -2: (-1, 30)}[L]: nbs.append(("L", v, (t, v, rev, sk, R, H, tf)))
        for v in (round(sk * 0.75, 3), round(sk * 1.25, 3)): nbs.append(("sk", v, (t, L, rev, v, R, H, tf)))
        for v in ((0.2, 0.4) if R == 0.3 else (0.75, 1.5)): nbs.append(("R", v, (t, L, rev, sk, v, H, tf)))
        for v in {60: (30, 120), 240: (120, 480), 100000: (240,)}[H]: nbs.append(("H", v, (t, L, rev, sk, R, v, tf)))
        nbs.append(("tfil", 1 - tf, (t, L, rev, sk, R, H, 1 - tf)))
        ch = three(lambda k: tm(k, c)); J[m]["chosen_unfiltered"] = ch
        for p, v, cc in nbs:
            s = three(lambda k: tm(k, cc)); NB.append(dict(module=m, param=p, value=v, **s))
        print(m, "neighbours done", flush=True)
    # ---------------------------------------------------------------- LON
    BL = {k: london.bars(v, 1) for k, v in D.items()}; LL = {k: london.day_levels(v) for k, v in D.items()}
    def lo(key, c):
        rs, we, ee, em, sm, R, mx, xo, bias = c; _, at, tr = LL[key]
        return london.run(BL[key], at, tr, rs, 180, we, ee, em, sm, R, mx, xo, bias)        # range end fixed at 03:00 (as london.py grid)
    lgrid = [(rs, we, ee, em, sm, R, mx, xo, bias) for rs, (we, ee), em, sm, R, mx, xo, bias in itertools.product((1080, 1200, 0, 120), ((300, 360), (360, 480), (480, 540)), (0, 1), (0, 1, 2), (1.0, 1.5, 2.0, 3.0), (0.1, 0.25), (570, 660, 955), (0, 1))]
    chosen = (0, 360, 480, 1, 2, 2.0, 0.25, 570, 1)
    r, S = family("LON grid", lgrid, lo, chosen); J["LON"] = dict(family="London grid", **r)
    ch = three(lambda k: lo(k, chosen)); J["LON"]["chosen_check"] = ch
    names = {0: "rs", 1: "we/ee", 3: "em", 4: "sm", 5: "R", 6: "mx", 7: "exit", 8: "bias"}
    alts = {0: (1200, 120), 1: ((300, 360), (480, 540)), 3: (0,), 4: (0, 1), 5: (1.5, 3.0), 6: (0.1, 0.5), 7: (480, 660), 8: (0,)}
    for i, vs in alts.items():
        for v in vs:
            c = list(chosen)
            if i == 1: c[1], c[2] = v
            else: c[i] = v
            c = tuple(c); s = three(lambda k: lo(k, c)); NB.append(dict(module="LON", param=names[i], value=str(v), **s))
    print("LON neighbours done", flush=True)
    # ---------------------------------------------------------------- ICT (corrected fill)
    BI = {k: ict_fix.bars(v, 5) for k, v in D.items()}; LI = {k: ict_fix.day_levels(v) for k, v in D.items()}
    LEV = ict_fix.LEVELS; WIN = ict_fix.WINS
    def ic(key, c):
        lv, win, K, em, R, bias, mx = c; L_, at, tr = LI[key]
        df = ict_fix.run(BI[key], L_, at, tr, np.array(LEV[lv], np.bool_), win, K, em, R, bias, mx); return df
    igrid = list(itertools.product(LEV, [WIN[w] for w in WIN], (4, 8), (0, 1, 2, 3), (1.0, 1.5, 2.0, 3.0), (0, 1, -1), (0.1, 0.25)))
    ichosen = ("all", (570, 630), 4, 2, 1.0, 1, 0.25)
    r, S = family("ICT grid", igrid, ic, ichosen); J["ICT"] = dict(family="ICT-fix 5m grid", **r)
    J["ICT"]["chosen_check"] = three(lambda k: ic(k, ichosen))
    for p, v, c in [("K", 2, ("all", (570, 630), 2, 2, 1.0, 1, 0.25)), ("K", 8, ("all", (570, 630), 8, 2, 1.0, 1, 0.25)), ("em", 1, ("all", (570, 630), 4, 1, 1.0, 1, 0.25)),
                    ("em", 3, ("all", (570, 630), 4, 3, 1.0, 1, 0.25)), ("em", 0, ("all", (570, 630), 4, 0, 1.0, 1, 0.25)), ("R", 0.75, ("all", (570, 630), 4, 2, 0.75, 1, 0.25)),
                    ("R", 1.5, ("all", (570, 630), 4, 2, 1.5, 1, 0.25)), ("bias", 0, ("all", (570, 630), 4, 2, 1.0, 0, 0.25)), ("mx", 0.15, ("all", (570, 630), 4, 2, 1.0, 1, 0.15)),
                    ("mx", 0.35, ("all", (570, 630), 4, 2, 1.0, 1, 0.35)), ("win", "0930-1100", ("all", (570, 660), 4, 2, 1.0, 1, 0.25)), ("win", "0930-1130", ("all", (570, 690), 4, 2, 1.0, 1, 0.25)),
                    ("lv", "pd_on", ("pd_on", (570, 630), 4, 2, 1.0, 1, 0.25)), ("lv", "on_lon", ("on_lon", (570, 630), 4, 2, 1.0, 1, 0.25))]:
        s = three(lambda k: ic(k, c)); NB.append(dict(module="ICT", param=p, value=str(v), **s))
    print("ICT neighbours done", flush=True)
    # ---------------------------------------------------------------- CRT11 / MSEQ from existing grids (IS = CFD 2020-23, OOS = CFD 2024-26; $1 RT there)
    C = pd.read_csv(os.path.join(RES, "crt2.csv")); C = C[C.p == 60]
    base = dict(hours="11", bias=1, R=2.0, min_rng=0.0, max_risk=0.5, mcf=0.0, emode=0)
    sel = C[np.logical_and.reduce([C[k] == v for k, v in base.items()])]; J["CRT11"] = dict(family="CRT grid (crt2.csv, 4,608 configs)", chosen=sel[["is_n", "is_pf", "oos_pf", "minyr"]].to_dict("records"))
    for k, vs in dict(hours=("10", "9-10", "12-15"), bias=(0,), R=(1.5, 2.5, 3.0), min_rng=(0.1,), max_risk=(0.25,), mcf=(0.25,), emode=(1, 2)).items():
        for v in vs:
            b = dict(base); b[k] = v; s = C[np.logical_and.reduce([C[kk] == vv for kk, vv in b.items()])]
            if len(s): NB.append(dict(module="CRT11", param=k, value=str(v), IS_n=int(s.is_n.iloc[0]), IS_pf=float(s.is_pf.iloc[0]), C24_pf=float(s.oos_pf.iloc[0]), REAL_pf=np.nan, L1519_pf=np.nan))
    ok = C[C.is_n >= 60]; J["CRT11"]["grid_median_IS_OOS"] = [round(float(ok.is_pf.median()), 3), round(float(ok.oos_pf.median()), 3)]
    t = ok.sort_values("is_pf", ascending=False).head(10); J["CRT11"]["top10_IS_OOS"] = [round(float(t.is_pf.median()), 3), round(float(t.oos_pf.median()), 3)]
    W = pd.read_csv(os.path.join(RES, "wr60_focus.csv")); base = dict(filt="up20", sess="rth_1030", N=5, R=0.5, sk=1.75)
    sel = W[np.logical_and.reduce([W[k] == v for k, v in base.items()])]; J["MSEQ"] = dict(family="MSEQ focus grid (wr60_focus.csv, 216; ~22k searched)", chosen=sel[["n", "is_pf", "oos_pf", "minyr"]].to_dict("records"))
    for k, vs in dict(filt=("up20_vwap",), sess=("rth", "to14"), N=(4, 6), R=(0.6,), sk=(2.0,)).items():
        for v in vs:
            b = dict(base); b[k] = v; s = W[np.logical_and.reduce([W[kk] == vv for kk, vv in b.items()])]
            if len(s): NB.append(dict(module="MSEQ", param=k, value=str(v), IS_n=int(s.n.iloc[0]), IS_pf=float(s.is_pf.iloc[0]), C24_pf=float(s.oos_pf.iloc[0]), REAL_pf=np.nan, L1519_pf=np.nan))
    # ---------------------------------------------------------------- target-variant PBO and plateaus (variants_ext)
    alld = np.array(sorted(set(D["cfd"]["date"][D["cfd"]["date"] >= 20200201]) - FOMC))
    V = pd.read_pickle(os.path.join(RES, "variants_ext_nq_1m.pkl")); V = V[(V["mod"] != "GOLD") & (V.date >= 20200201) & ~V.fomc]
    VR = pd.read_pickle(os.path.join(RES, "variants_ext_mnq_fut.pkl")); VR = VR[(VR["mod"] != "GOLD") & (VR.date >= 20240201) & ~VR.fomc]
    VL = pd.read_pickle(os.path.join(RES, "variants_nqhd_long.pkl")); VL = VL[~VL.fomc & (VL.date >= 20150201) & (VL.date < 20200101)]
    tv = {}
    for m, g in V.groupby("mod"):
        rows = {}
        for v, gg in g.groupby("var"):
            u = gg.usd - 0.9; ur = VR[(VR["mod"] == m) & (VR["var"] == v)].usd - 0.9; gl = VL[(VL["mod"] == m) & (VL["var"] == v)]
            a = gl.date.map(ATR_BY_DATE).to_numpy(); ul = ((gl.usd + 1) / 2 + 0.5 - 0.00345 * a) / a * 100
            rows[str(v)] = dict(IS=round(pfu(u[gg.date < 20240101]), 3), C24=round(pfu(u[gg.date >= 20240101]), 3), REAL=round(pfu(ur), 3), L1519=round(pfu(ul), 3) if len(ul) >= 20 else None,
                                WR_REAL=round(float(100 * (ur > 0).mean()), 1) if len(ur) else None)
        r = dict(variants=rows)
        if g["var"].nunique() >= 3:
            Mm = g.assign(u=g.usd - 0.9).pivot_table(index="date", columns="var", values="u", aggfunc="sum").reindex(alld, fill_value=0.0).fillna(0.0); r["pbo"] = pbo(Mm.to_numpy())
        tv[m] = r
    J["target_variants"] = tv
    json.dump(J, open("audit_oldmods.json", "w"), indent=1, default=float)
    N = pd.DataFrame(NB); N.to_csv("audit_neighbours_old.csv", index=False)
    pd.set_option("display.width", 220); pd.set_option("display.max_rows", 300)
    print(N.round(3).to_string(index=False))
    print(json.dumps({m: J[m].get("chosen_unfiltered", J[m].get("chosen_check", J[m].get("chosen"))) for m in J if m not in ("time_map", "target_variants")}, indent=0, default=float))
