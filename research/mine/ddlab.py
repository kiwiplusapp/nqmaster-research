"""ddlab: pre-registered PORTFOLIO DRAWDOWN LAB on the 2027 default trade set (nt_compare 'ultra_d4' = Ultra + durable six-year
modules SO04 / RV11 / ORFAIL / CAM3, real Databento NQ 2020-10-15..2026-10, $ per MNQ incl. $1.90 + 1 tick, w = lots).
Goal (Federico, 2026-10-19): lower max drawdown and worst month WITHOUT lowering PF, WR, trade count or net $, and without overfitting.
Protocol (fixed before running, see ddlab_report.md 'Pre-registration'): every rule family x parameter grid is run on T1
(2020-10-15..2023-12-31) and T2 (2024-01-01..); a cell is chosen on T1 only, then checked on T2 and on 2010-19 cost-normalised data.
Rule families: R1 stop tightening to k x ATR (re-simulated exits), R2 skip risk > k x ATR, R3 portfolio heat cap, R4 daily loss stop
in ATR units (a: block new entries, b: flatten + block), R5 direction exposure cap (lots / trades), R6 session kill after K
consecutive stop-outs, R8 weekly / monthly loss stops in ATR units, R9 combination of the best passing R1 / R3 / R4 cells.
Acceptance (fixed): T1 maxDD down >= 10% AND T2 maxDD down >= 5% AND worst month not worse (T1, T2) AND Sharpe not lower (T1, T2)
AND net $ not lower by > 5% (T1, T2) AND trades not lower by > 3% (R2 reported separately) AND WR not lower (T1, T2).
Usage:  python3 ddlab.py build    (per-trade specs -> scratchpad ddlab_specs.pkl, prints the reproduction check)
        python3 ddlab.py run      (grid on real T1/T2 + 2010-19 norm, bootstrap, MFFU lifecycle -> ddlab.json)
MINE_PROCS / threads <= 2. Import-safe (no work at import)."""
import os, sys, json, time, pickle, itertools, numpy as np, pandas as pd
os.environ.setdefault("NUMBA_NUM_THREADS", "2"); os.environ.setdefault("OMP_NUM_THREADS", "2"); os.environ.setdefault("MKL_NUM_THREADS", "2")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from numba import njit
from wrq_lib import getD, xsim, fills_core, time_exit, SLIP, NORM_COST, DEF
from wrq_port import conflict_filter
from core import S, TICK
SP = os.environ.get("DDLAB_SP", "/tmp/claude-0/-home-user-nqmaster-research/176a42ca-c215-52e2-84dc-57e214e477d4/scratchpad")
SPECS = os.path.join(SP, "ddlab_specs.pkl")
NAME = "nqdb.npz"; PV = 2.0; COMM = 1.9
START, MID = 20201015, 20240101
SIX = {"SO04": ("CLOCK_ANCHOR", 1527), "RV11": ("RVOL_DRIVE", 4226), "ORFAIL": ("OR_FAIL", 142), "CAM3": ("PIVOT_FADE", 365)}
CPI09 = dict(A=830, T=60, x=0.05, mode=-1, tf=0, k=0.35, stop=0, R=0.5, hold=60)
EXITP = {"VOLB": dict(be=0.75, beo=0.1)}                                      # Ultra: VOLB break-even after +0.75R (stop to +0.1R)
STRUCT = ["VOLB", "ORB60", "ORB90", "MSEQ", "MSEQS", "CRT11", "ICT", "LON", "ORFAIL"]   # R1 modules (structure stops)
PERS = {"T1": (START, MID), "T2": (MID, 20991231), "A": (20100601, 20150101), "B": (20150101, 20200101), "N": (20100601, 20200101)}


# ------------------------------------------------------------------------------------------------ data
def days_real(D, lo=20200101):
    from news import NEWS
    dd = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); dd = dd[dd >= lo]
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(dd).to_numpy()
    return dd[(atr >= 150) & ~np.isin(dd, list(NEWS["FOMC"]))]


def days_norm(D):
    from news import NEWS; from db_long import FOMC_1019
    dd = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); dd = dd[(dd >= 20100601) & (dd < 20200101)]
    return dd[~np.isin(dd, list(NEWS["FOMC"]) + FOMC_1019)]


def base_real():
    """nt_compare 'ultra_d4' with the original module names kept (VW13b / VW13 separate for the joins)."""
    X = pickle.load(open(os.path.join(HERE, "six_ultra6_trades.pkl"), "rb"))["Ultra6"][["date", "mod", "tin", "tout", "d", "u", "w"]].copy()
    X = X[~X["mod"].isin(["CA04V", "GD03", "ENG26", "LATEFH"])]
    X = conflict_filter(X.sort_values(["date", "tin"]).reset_index(drop=True))
    return X.sort_values(["date", "tin"]).reset_index(drop=True)


def six_specs(D, maxday_flat=955):
    """Entry specs of the four six-year modules and CPI09 regenerated from their family generators (fills_core = core.execute entries)."""
    from run_mine import FAMILIES as OLD
    from families5 import FAMILIES5
    from families_gold import gen_drive
    from news_hist import CPI_ALL
    from cpi_lab import keep_days
    F = {**OLD, **FAMILIES5}; out = []
    for nm, (fam, j) in SIX.items():
        gen, grid, maxday = F[fam]; ev = gen(D, grid[j]); Fl = fills_core(D, ev, flat=maxday_flat, maxday=maxday)
        Fl["mod"] = nm; out.append(Fl)
    ev = keep_days(gen_drive(D, CPI09), D, set(CPI_ALL)); Fl = fills_core(D, ev, flat=maxday_flat, maxday=1); Fl["mod"] = "CPI09"; out.append(Fl)
    Z = pd.concat(out, ignore_index=True)
    Z["tx"] = time_exit(D, Z.fi.to_numpy(), Z.hold.to_numpy(), 1555); Z["date"] = D.date[Z.fi.to_numpy()]; Z["tin"] = D.sm[Z.fi.to_numpy()]
    return Z[["mod", "date", "tin", "fi", "d", "ent0", "et", "sl0", "tp0", "tx"]]


def simulate(D, Z, p=None, slip=SLIP, norm=False, sl_override=None):
    """xsim on a spec frame Z (one module, sorted by fi). Returns u, xi, rs, risk_pts (arrays aligned with Z)."""
    q = dict(DEF); q.update(p or {}); Z = Z.sort_values("fi", kind="stable")
    sl = Z.sl0.to_numpy(float) if sl_override is None else np.asarray(sl_override, float)
    out = np.zeros((len(Z), 6))
    xsim(D.o, D.h, D.l, D.c, Z.fi.to_numpy(np.int64), Z.d.to_numpy(np.int64), Z.ent0.to_numpy(float), Z.et.to_numpy(np.int64), sl, Z.tp0.to_numpy(float),
         Z.tx.to_numpy(np.int64), float(slip), float(q["ks"]), float(q["kt"]), float(q["be"]), float(q["beo"]), float(q["tt"]), float(q["td"]), int(q["ts"]), float(q["tsc"]), out)
    pts = out[:, 0]
    if norm:
        a = D.atr[D.day[Z.fi.to_numpy()]]; u = np.where(a > 0, (pts - NORM_COST * a) / np.where(a > 0, a, 1) * 100, 0.0)
    else:
        u = pts * D.pv - D.comm
    return pd.Series(u, index=Z.index), pd.Series(out[:, 1].astype(np.int64), index=Z.index), pd.Series(out[:, 2].astype(np.int64), index=Z.index), pd.Series(out[:, 3], index=Z.index)


def attach(D, X, E, Z6, norm=False):
    """X: trade set with fi (real: from cand16 join; norm: cand16 norm view) -> add ent0/et/sl0/tp0/tx, re-simulated u_sim, xi, rs, risk."""
    ult = E[["mod", "fi", "ent0", "et", "sl0", "tp0", "tx"]].drop_duplicates(["mod", "fi"])
    spec = pd.concat([ult, Z6[["mod", "fi", "ent0", "et", "sl0", "tp0", "tx"]]], ignore_index=True)
    X = X.merge(spec, on=["mod", "fi"], how="left")
    miss = X.ent0.isna()
    if miss.any(): print("WARNING: no spec for", X.loc[miss, "mod"].value_counts().to_dict(), flush=True)
    X = X[~miss].copy()
    X["e"] = X.ent0 + np.where(X.et == 0, X.d * (0.0 if norm else SLIP), 0.0)
    X["atr"] = D.atr[D.day[X.fi.to_numpy()]]
    X["u_sim"] = np.nan; X["xi"] = -1; X["rs"] = -1; X["risk"] = np.nan
    for m, g in X.groupby("mod"):
        u, xi, rs, risk = simulate(D, g, EXITP.get(m), 0.0 if norm else SLIP, norm)
        X.loc[u.index, "u_sim"] = u; X.loc[xi.index, "xi"] = xi; X.loc[rs.index, "rs"] = rs; X.loc[risk.index, "risk"] = risk
    X["risk_atr"] = X.risk / X.atr
    return X


def build():
    t0 = time.time(); D = getD(NAME); print("data", round(time.time() - t0), "s", flush=True)
    E = pickle.load(open(os.path.join(HERE, "wrq_entries_db.pkl"), "rb"))
    Z6 = six_specs(D); print("six specs", len(Z6), Z6["mod"].value_counts().to_dict(), flush=True)
    C = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["UltraR"]
    TR = {}
    for f in ("trades_db_old.pkl", "trades_db_new.pkl"): TR.update(pickle.load(open(os.path.join(HERE, f), "rb")))
    # ---- real view: ultra_d4 trades + fi from cand16 UltraR (Ultra modules) / six_specs (six modules, CPI09)
    B = base_real(); key = ["date", "mod", "tin", "d"]
    cr = C[0][key + ["fi"]].drop_duplicates(key); z6 = Z6[key + ["fi"]].drop_duplicates(key)
    X = B.merge(pd.concat([cr, z6], ignore_index=True).drop_duplicates(key), on=key, how="left")
    print("real: rows", len(X), "without fi:", int(X.fi.isna().sum()), X[X.fi.isna()]["mod"].value_counts().to_dict(), flush=True)
    X = X[~X.fi.isna()].copy(); X["fi"] = X.fi.astype(np.int64)
    XR = attach(D, X, E, Z6, norm=False)
    diff = (XR.u_sim - XR.u).abs(); print("real: re-sim |du| > 0.01:", int((diff > 0.01).sum()), "of", len(XR), "max", round(diff.max(), 2),
                                           XR[diff > 0.01]["mod"].value_counts().to_dict(), flush=True)
    # ---- 2010-19 cost-normalised view: cand16 UltraR norm + CPI09 norm + six-year norm (MOM1030 / CPI09 x4), conflict-filtered
    N = C[1][["date", "mod", "tin", "tout", "d", "u", "w", "fi"]].copy()
    parts = [N]
    for nm, k in SIX.items():
        t = TR[k]["norm"]; xi = TR[k]["real"].set_index("fi").xi.reindex(t.fi).to_numpy(); xi = np.nan_to_num(xi, nan=0).astype(int)
        parts.append(pd.DataFrame(dict(date=t.date.to_numpy(), mod=nm, tin=D.sm[t.fi.to_numpy().astype(int)], tout=D.sm[xi] + 1, d=t.d.to_numpy(), u=t.usd.to_numpy(), w=1.0, fi=t.fi.to_numpy().astype(int))))
    zc = Z6[Z6["mod"] == "CPI09"]; uc, xic, _, _ = simulate(D, zc, None, 0.0, True)
    parts.append(pd.DataFrame(dict(date=zc.date.to_numpy(), mod="CPI09", tin=zc.tin.to_numpy(), tout=D.sm[xic.to_numpy()] + 1, d=zc.d.to_numpy(), u=uc.to_numpy(), w=1.0, fi=zc.fi.to_numpy())))
    XN = pd.concat(parts, ignore_index=True); XN.loc[XN["mod"].isin(["MOM1030", "CPI09"]), "w"] = 4.0
    XN = XN[(XN.date >= 20100601) & (XN.date < 20200101)].sort_values(["date", "tin"]).reset_index(drop=True)
    XN = conflict_filter(XN).sort_values(["date", "tin"]).reset_index(drop=True)
    XN = attach(D, XN, E, Z6, norm=True)
    diff = (XN.u_sim - XN.u).abs(); print("norm: re-sim |du| > 0.01:", int((diff > 0.01).sum()), "of", len(XN), "max", round(diff.max(), 2),
                                           XN[diff > 0.01]["mod"].value_counts().to_dict(), flush=True)
    days = {"real": days_real(D), "norm": days_norm(D)}
    pickle.dump(dict(real=XR, norm=XN, days=days), open(SPECS, "wb"))
    print("saved", SPECS, round(time.time() - t0), "s", flush=True)
    return XR, XN


# ------------------------------------------------------------------------------------------------ metrics
def daily_pnl(X, days):
    x = (X.u * X.w).groupby(X.date).sum()
    idx = np.union1d(days, x.index.to_numpy())
    return x.reindex(idx, fill_value=0.0)


def metr(X, days, lo, hi):
    """Trades and daily series restricted to [lo, hi): n, wr (per trade, unweighted), pf (w*u), net, sharpe (daily, 252), maxdd (closed daily equity), worst month."""
    s = X[(X.date >= lo) & (X.date < hi)]; x = s.u * s.w
    d = daily_pnl(s, days[(days >= lo) & (days < hi)]); d = d[(d.index >= lo) & (d.index < hi)]
    eq = d.cumsum(); mo = d.groupby(d.index // 100).sum(); l = -x[x <= 0].sum()
    return dict(n=int(len(s)), wr=float(100 * (s.u > 0).mean()) if len(s) else 0.0, pf=float(x[x > 0].sum() / l) if l > 0 else 99.0, net=float(x.sum()),
                sharpe=float(d.mean() / d.std() * np.sqrt(252)) if d.std() > 0 else 0.0, maxdd=float((eq.cummax() - eq).max()), worst_month=float(mo.min()),
                neg_months=int((mo < 0).sum()), months=int(len(mo)))


def passes(b, r, per, skip_ok=False):
    """Acceptance parts for one period (b = base, r = rule metrics). DD: T1 >= 10% down, T2 >= 5% down."""
    need = 0.10 if per == "T1" else 0.05
    c = dict(dd=r["maxdd"] <= b["maxdd"] * (1 - need), wm=r["worst_month"] >= b["worst_month"], sh=r["sharpe"] >= b["sharpe"] - 0.005,
             net=r["net"] >= b["net"] * 0.95, n=skip_ok or r["n"] >= b["n"] * 0.97, wr=r["wr"] >= b["wr"] - 0.05)
    c["all"] = all(c.values()); return c


# ------------------------------------------------------------------------------------------------ rules
def r1_tighten(D, X, k, norm=False):
    """R1: stop distance = min(structure stop, k x daily ATR), target unchanged; exits re-simulated for the STRUCT modules."""
    X = X.copy(); m = X["mod"].isin(STRUCT)
    for mod, g in X[m].groupby("mod"):
        r0 = (g.e - g.sl0).abs().to_numpy(); nd = np.minimum(r0, k * g.atr.to_numpy()); sl = g.e.to_numpy() - g.d.to_numpy() * nd
        u, xi, rs, risk = simulate(D, g, EXITP.get(mod), 0.0 if norm else SLIP, norm, sl_override=sl[np.argsort(g.fi.to_numpy(), kind="stable")])
        X.loc[u.index, "u"] = u; X.loc[xi.index, "xi"] = xi; X.loc[rs.index, "rs"] = rs; X.loc[risk.index, "risk"] = risk
    X["risk_atr"] = X.risk / X.atr; X["tout"] = D.sm[X.xi.to_numpy()] + 1
    return X


def r2_skip(X, k):
    return X[X.risk_atr <= k + 1e-12].copy()


def gate(D, X, rule, prm, unit=PV):
    """Sequential intraday gates on the taken-trade state. rule: R3 (heat H in ATR x lots), R4a / R4b (daily loss L x ATR x unit),
    R5lots / R5trades (direction cap N), R6 (K consecutive full stop-outs). Returns the kept trades (R4b: flattened u / xi)."""
    X = X.sort_values(["fi"], kind="stable"); keep = np.ones(len(X), bool)
    fi = X.fi.to_numpy(); xi = X.xi.to_numpy(); d = X.d.to_numpy(); w = X.w.to_numpy(); ra = X.risk_atr.to_numpy(); rs = X.rs.to_numpy()
    e = X.e.to_numpy(); u = X.u.to_numpy().copy(); xi2 = xi.copy(); atr = X.atr.to_numpy(); dayi = D.day[fi]
    slip = SLIP if unit == PV else 0.0; comm = COMM if unit == PV else 0.0
    for dy in np.unique(dayi):
        idx = np.nonzero(dayi == dy)[0]; ds, de = D.ds[dy], D.de[dy]; nb = de - ds + 1
        taken = []; latch = False
        if rule.startswith("R4"):
            eq = np.zeros(nb); thr = prm * (atr[idx[0]] * PV if unit == PV else 100.0)   # L x ATR x $2 (real) / L x 100 %ATR (norm)
            cl = D.c[ds:de + 1]
        for k in idx:
            if latch: keep[k] = False; continue
            f = fi[k]
            op = [j for j in taken if fi[j] <= f < xi2[j]]
            if rule == "R3":
                if sum(w[j] * ra[j] for j in op) > prm: keep[k] = False; continue
            elif rule == "R5lots":
                if sum(w[j] for j in op if d[j] == d[k]) >= prm: keep[k] = False; continue
            elif rule == "R5trades":
                if sum(1 for j in op if d[j] == d[k]) >= prm: keep[k] = False; continue
            elif rule == "R6":
                cl_ = sorted([j for j in taken if xi2[j] < f], key=lambda j: xi2[j]); c = 0
                for j in reversed(cl_):
                    if rs[j] == 0: c += 1
                    else: break
                if c >= prm: keep[k] = False; continue
            elif rule.startswith("R4"):
                if f - ds > 0 and eq[: f - ds].min() <= -thr: keep[k] = False; latch = True; continue
            taken.append(k)
            if rule.startswith("R4"):
                a, b = f - ds, xi2[k] - ds
                if unit == PV: mtm = w[k] * ((cl[a:b] - e[k]) * d[k] * PV - comm)
                else: mtm = w[k] * ((cl[a:b] - e[k]) * d[k] - NORM_COST * atr[k]) / atr[k] * 100
                eq[a:b] += mtm; eq[b:] += w[k] * u[k]
                if rule == "R4b":
                    br = np.nonzero(eq[a:] <= -thr)[0]
                    if len(br):
                        m = a + br[0]; latch = True
                        for j in taken:
                            if fi[j] - ds <= m < xi2[j] - ds:
                                pts = d[j] * (cl[m] - e[j]) - slip
                                u[j] = pts * PV - comm if unit == PV else (pts - NORM_COST * atr[j]) / atr[j] * 100; xi2[j] = ds + m
    Y = X[keep].copy(); Y["u"] = u[keep]; Y["xi"] = xi2[keep]; Y["tout"] = D.sm[Y.xi.to_numpy()] + 1
    return Y.sort_values(["date", "tin"], kind="stable")


def r8_period_stop(X, days, kind, L, unit=PV):
    """R8: skip the whole day when the week-to-date (kind 'W') / month-to-date ('M') realized P&L of the previous days <= -L x ATR x unit."""
    atr_d = X.groupby("date").atr.first(); x = (X.u * X.w).groupby(X.date).sum()
    dd = np.union1d(days, x.index.to_numpy()); dts = pd.to_datetime(pd.Series(dd).astype(str))
    pid = (dts.dt.isocalendar().year * 100 + dts.dt.isocalendar().week).to_numpy() if kind == "W" else (dd // 100)
    skip = set(); acc = 0.0; cur = None
    for i, day in enumerate(dd):
        if pid[i] != cur: cur = pid[i]; acc = 0.0
        a = atr_d.get(day, np.nan)
        if np.isfinite(a) and acc <= -L * (a * PV if unit == PV else 100.0): skip.add(day); continue
        acc += float(x.get(day, 0.0))
    return X[~X.date.isin(skip)].copy()


def cells():
    C = []
    for k in (0.15, 0.2, 0.25, 0.3, 0.35, 0.4): C.append(("R1", f"R1 stop<=k ATR k={k}", k))
    for k in (0.15, 0.2, 0.25, 0.3, 0.35, 0.4): C.append(("R2", f"R2 skip risk>k ATR k={k}", k))
    for H in (0.4, 0.6, 0.8, 1.0, 1.5): C.append(("R3", f"R3 heat cap H={H} ATR", H))
    for L in (0.5, 0.75, 1.0, 1.5): C.append(("R4a", f"R4a daily loss block L={L} ATR", L))
    for L in (0.5, 0.75, 1.0, 1.5): C.append(("R4b", f"R4b daily loss flatten L={L} ATR", L))
    for N in (2, 3, 4): C.append(("R5lots", f"R5 dir cap lots N={N}", N))
    for N in (2, 3, 4): C.append(("R5trades", f"R5 dir cap trades N={N}", N))
    for K in (2, 3, 4): C.append(("R6", f"R6 session kill K={K} stop-outs", K))
    for W in (2, 3, 4): C.append(("R8W", f"R8 weekly loss stop W={W} ATR", W))
    for M in (4, 6, 8): C.append(("R8M", f"R8 monthly loss stop M={M} ATR", M))
    return C


def apply_cell(D, X, days, fam, prm, norm=False):
    unit = 100.0 if norm else PV
    if fam == "R1": return r1_tighten(D, X, prm, norm)
    if fam == "R2": return r2_skip(X, prm)
    if fam in ("R3", "R4a", "R4b", "R5lots", "R5trades", "R6"): return gate(D, X, fam, prm, unit)
    if fam == "R8W": return r8_period_stop(X, days, "W", prm, unit)
    if fam == "R8M": return r8_period_stop(X, days, "M", prm, unit)
    raise ValueError(fam)


def apply_combo(D, X, days, parts, norm=False):
    for fam, prm in parts: X = apply_cell(D, X, days, fam, prm, norm)
    return X


# ------------------------------------------------------------------------------------------------ bootstrap
def block_boot(db, dr, nb=500, blk=21, seed=7):
    """Paired 21-day block bootstrap of base / rule daily P&L: distribution of maxDD change (%) and Sharpe change."""
    rng = np.random.default_rng(seed); n = len(db); b = np.asarray(db); r = np.asarray(dr); out = []
    for _ in range(nb):
        st = rng.integers(0, n - blk, size=n // blk + 1); ix = np.concatenate([np.arange(s, s + blk) for s in st])[:n]
        xb, xr = b[ix], r[ix]; eb, er = np.cumsum(xb), np.cumsum(xr)
        ddb = (np.maximum.accumulate(eb) - eb).max(); ddr = (np.maximum.accumulate(er) - er).max()
        out.append((100 * (ddr / ddb - 1) if ddb > 0 else 0.0, xr.mean() / xr.std() * np.sqrt(252) - xb.mean() / xb.std() * np.sqrt(252), xr.sum() - xb.sum()))
    o = np.array(out)
    return dict(dd_chg_med=float(np.median(o[:, 0])), dd_chg_p10=float(np.percentile(o[:, 0], 10)), dd_chg_p90=float(np.percentile(o[:, 0], 90)),
                p_dd_lower=float((o[:, 0] < 0).mean()), p_dd_lower_5pct=float((o[:, 0] < -5).mean()), dsharpe_med=float(np.median(o[:, 1])), p_sharpe_up=float((o[:, 1] >= 0).mean()),
                dnet_med=float(np.median(o[:, 2])))


# ------------------------------------------------------------------------------------------------ MFFU 50K 1-contract lifecycle (copy of robust2_life / mffu_rapid machinery)
@njit(cache=True)
def ev_m(EL, EC, C, T, Dd, cons, mind, idx, s, n):
    eq = 0.0; pk = 0.0; best = -1e9; d = s
    while d < n:
        t = idx[d]
        thr = 100.0 if pk >= Dd + 100.0 else pk - Dd
        g = 1 if eq - thr >= C else 0
        if eq + EL[g, t] <= thr: return -1, d
        c = EC[g, t]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= T and d - s + 1 >= mind and (cons <= 0.0 or best <= cons * eq): return 1, d
        d += 1
    return 0, n


@njit(cache=True)
def fu_m(FL, FC, c1, c2, idx, start, n, B, Dd, npmax):
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; d = start
    while d < n:
        t = idx[d]
        thr = 100.0 if pk >= Dd + 100.0 else pk - Dd
        cu = bal - thr; j = 0 if cu < c1 else (1 if cu < c2 else 2)
        if bal + FL[j, t] <= thr: return cash, m, -1, d
        bal += FC[j, t]
        if bal > pk: pk = bal
        if bal - B >= 500.0:
            amt = bal - B; bal -= amt; cash += 0.9 * amt; m += 1
            if npmax > 0 and m >= npmax: return cash, m, 1, d
        d += 1
    return cash, m, 0, n


@njit(cache=True)
def life_m(EL, EC, C, T, Dd, cons, mind, fee, FL, FC, c1, c2, B, npmax, idx, H, step, out):
    N = len(idx); r = 0
    for s in range(0, N - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0; dtp = 0.0; fdays = 0.0
        while i < end:
            fees += fee; nev += 1
            res, j = ev_m(EL, EC, C, T, Dd, cons, mind, idx, i, end)
            if res != 1:
                i = j + 1; continue
            npass += 1; dtp += j - i + 1
            c, m, st, j2 = fu_m(FL, FC, c1, c2, idx, j + 1, end, B, Dd, npmax)
            fdays += min(j2, end - 1) - j; cash += c; npay += m; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb; out[r, 4] = npay
        out[r, 5] = dtp / max(npass, 1); out[r, 6] = fdays; out[r, 7] = cash; r += 1
    return r


def full_paths(D, X, days):
    pos = {d: i for i, d in enumerate(days)}; nd = len(days)
    Rinc = np.zeros((nd, 1440)); OA = np.zeros((nd, 1440)); XA = np.zeros((nd, 1440)); OC = np.zeros((nd, 1440))
    for t in X.itertuples():
        r = pos.get(t.date)
        if r is None: continue
        s = t.d; w = t.w; q = np.arange(t.fi, t.xi); sm = D.sm[q]
        adv = ((D.l[q] - t.e) if s > 0 else (t.e - D.h[q])) * D.pv - D.comm
        cls = (D.c[q] - t.e) * s * D.pv - D.comm
        np.add.at(OA[r], sm, w * adv); np.add.at(OC[r], sm, w * cls)
        mx = D.sm[t.xi]; advx = ((D.l[t.xi] - t.e) if s > 0 else (t.e - D.h[t.xi])) * D.pv - D.comm
        Rinc[r, mx] += w * t.u; XA[r, mx] += w * min(advx, t.u)
    Rc = np.cumsum(Rinc, 1)
    return Rc - Rinc + OA + XA, Rc + OC, Rc[:, -1]


def vectors(low, close, fin, G):
    lo = low.min(1); cl = fin.copy()
    if G > 0:
        hit = close >= G; has = hit.any(1); t = hit.argmax(1)
        for d in np.nonzero(has)[0]: lo[d] = low[d, :t[d] + 1].min(); cl[d] = close[d, t[d]]
    return np.minimum(lo, cl), cl


def boot_ids(days, mask, seed, NB=1000, H=252, BLK=10):
    pos = np.nonzero(mask)[0]; rng = np.random.default_rng(seed); nb = H // BLK + 2
    st = rng.integers(0, len(pos) - BLK, size=(NB, nb))
    return [np.ascontiguousarray(np.concatenate([pos[s:s + BLK] for s in row])[:H + 1]) for row in st]


def mffu_life(D, X, days, IDS):
    """MFFU Rapid EOD 50K, 1 contract, fixed set in eval (daily profit stop $800, 30% consistency) and funded (keep $4,100): bootstrap years."""
    low, close, fin = full_paths(D, X, days)
    lo8, cl8 = vectors(low, close, fin, 800.0); lo0, cl0 = vectors(low, close, fin, 0.0)
    EL = np.ascontiguousarray(np.array([lo8, lo8])); EC = np.ascontiguousarray(np.array([cl8, cl8]))
    FL = np.ascontiguousarray(np.array([lo0, lo0, lo0])); FC = np.ascontiguousarray(np.array([cl0, cl0, cl0])); out = {}
    for per, ids in IDS.items():
        res = np.zeros((len(ids), 8))
        for k, ix in enumerate(ids):
            o = np.zeros((2, 8)); life_m(EL, EC, 0.0, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 0.0, 0.0, 4100.0, 0, ix, 252, 252, o); res[k] = o[0]
        out[per] = dict(per_month=float(res[:, 0].mean() / 12), p10_month=float(np.percentile(res[:, 0], 10) / 12), evals=float(res[:, 1].mean()), passes=float(res[:, 2].mean()),
                        funded_busts=float(res[:, 3].mean()), payouts=float(res[:, 4].mean()), accounts_lost=float((res[:, 1] - res[:, 2] + res[:, 3]).mean()),
                        p_neg_year=float(100 * (res[:, 0] < 0).mean()), funded_days=float(res[:, 6].mean()),
                        bust_per_funded_year=float(res[:, 3].sum() / max(res[:, 6].sum() / 252, 1e-9)))
    return out


# ------------------------------------------------------------------------------------------------ run
def run():
    t0 = time.time(); D = getD(NAME); P = pickle.load(open(SPECS, "rb")); XR, XN, days = P["real"], P["norm"], P["days"]
    dr, dn = days["real"], days["norm"]
    base = {per: metr(XR, dr, *PERS[per]) for per in ("T1", "T2")}; base.update({per: metr(XN, dn, *PERS[per]) for per in ("A", "B", "N")})
    print("base", {k: (v["n"], round(v["wr"], 1), round(v["pf"], 3), round(v["net"]), round(v["sharpe"], 2), round(v["maxdd"]), round(v["worst_month"])) for k, v in base.items()}, flush=True)
    IDS = {"T1": boot_ids(dr, (dr >= START) & (dr < MID), 11), "T2": boot_ids(dr, dr >= MID, 12)}
    base_life = mffu_life(D, XR, dr, IDS); print("base life", base_life, flush=True)
    db = {per: daily_pnl(XR[(XR.date >= PERS[per][0]) & (XR.date < PERS[per][1])], dr[(dr >= PERS[per][0]) & (dr < PERS[per][1])]) for per in ("T1", "T2")}
    rows = []; SETS = {}
    for fam, name, prm in cells():
        Y = apply_cell(D, XR, dr, fam, prm, False); YN = apply_cell(D, XN, dn, fam, prm, True)
        m = {per: metr(Y, dr, *PERS[per]) for per in ("T1", "T2")}; m.update({per: metr(YN, dn, *PERS[per]) for per in ("A", "B", "N")})
        p1 = passes(base["T1"], m["T1"], "T1", fam == "R2"); p2 = passes(base["T2"], m["T2"], "T2", fam == "R2")
        row = dict(fam=fam, cell=name, prm=prm, T1_pass=p1["all"], T2_pass=p2["all"], both=p1["all"] and p2["all"], T1_fail=[k for k, v in p1.items() if not v and k != "all"], T2_fail=[k for k, v in p2.items() if not v and k != "all"])
        for per in ("T1", "T2", "A", "B", "N"):
            for k in ("n", "wr", "pf", "net", "sharpe", "maxdd", "worst_month"): row[f"{per}_{k}"] = m[per][k]
            row[f"{per}_dd_chg"] = 100 * (m[per]["maxdd"] / base[per]["maxdd"] - 1); row[f"{per}_net_chg"] = 100 * (m[per]["net"] / base[per]["net"] - 1) if base[per]["net"] else 0.0
        if fam in ("R1", "R3", "R4a", "R4b"):
            row["life"] = mffu_life(D, Y, dr, IDS)
        rows.append(row); SETS[name] = (Y, YN)
        print(f"{name:38s} T1 DD {row['T1_dd_chg']:+6.1f}% Sh {m['T1']['sharpe']:.2f} net {row['T1_net_chg']:+5.1f}% n {m['T1']['n']} WR {m['T1']['wr']:.1f} | T2 DD {row['T2_dd_chg']:+6.1f}% Sh {m['T2']['sharpe']:.2f} net {row['T2_net_chg']:+5.1f}% n {m['T2']['n']} WR {m['T2']['wr']:.1f} | N DD {row['N_dd_chg']:+6.1f}% Sh {m['N']['sharpe']:.2f} | {'T1ok' if p1['all'] else 'T1 ' + ','.join(row['T1_fail'])} {'T2ok' if p2['all'] else 'T2 ' + ','.join(row['T2_fail'])} ({round(time.time() - t0)} s)", flush=True)
    R = pd.DataFrame(rows)
    # R9: combination of the best T1-passing cell (by T1 maxDD reduction) of R1 / R3 / R4 (chosen on T1 only)
    best = {}
    for fam in ("R1", "R3", "R4"):
        sub = R[(R.fam.str.startswith(fam)) & R.T1_pass]
        if len(sub): r = sub.sort_values("T1_maxdd").iloc[0]; best[fam] = (r.fam, float(r.prm), r.cell)
    combos = []
    if len(best) >= 2:
        for n in range(2, len(best) + 1):
            for cs in itertools.combinations(best.values(), n):
                parts = [(f, p) for f, p, _ in cs]; name = "R9 " + " + ".join(c for _, _, c in cs)
                Y = apply_combo(D, XR, dr, parts, False); YN = apply_combo(D, XN, dn, parts, True)
                m = {per: metr(Y, dr, *PERS[per]) for per in ("T1", "T2")}; m.update({per: metr(YN, dn, *PERS[per]) for per in ("A", "B", "N")})
                p1 = passes(base["T1"], m["T1"], "T1"); p2 = passes(base["T2"], m["T2"], "T2")
                row = dict(fam="R9", cell=name, prm=repr(parts), T1_pass=p1["all"], T2_pass=p2["all"], both=p1["all"] and p2["all"], T1_fail=[k for k, v in p1.items() if not v and k != "all"], T2_fail=[k for k, v in p2.items() if not v and k != "all"])
                for per in ("T1", "T2", "A", "B", "N"):
                    for k in ("n", "wr", "pf", "net", "sharpe", "maxdd", "worst_month"): row[f"{per}_{k}"] = m[per][k]
                    row[f"{per}_dd_chg"] = 100 * (m[per]["maxdd"] / base[per]["maxdd"] - 1); row[f"{per}_net_chg"] = 100 * (m[per]["net"] / base[per]["net"] - 1) if base[per]["net"] else 0.0
                row["life"] = mffu_life(D, Y, dr, IDS); rows.append(row); SETS[name] = (Y, YN); combos.append(row)
                print(f"{name[:60]:60s} T1 DD {row['T1_dd_chg']:+6.1f}% Sh {m['T1']['sharpe']:.2f} | T2 DD {row['T2_dd_chg']:+6.1f}% Sh {m['T2']['sharpe']:.2f} | {p1['all']} {p2['all']}", flush=True)
    R = pd.DataFrame(rows)
    # bootstrap of the DD change for every T1-passing cell (and the accepted ones)
    BOOT = {}
    for r in R[R.T1_pass].itertuples():
        Y = SETS[r.cell][0]; BOOT[r.cell] = {}
        for per in ("T1", "T2"):
            lo, hi = PERS[per]; dd_ = dr[(dr >= lo) & (dr < hi)]
            dy = daily_pnl(Y[(Y.date >= lo) & (Y.date < hi)], dd_).reindex(db[per].index, fill_value=0.0)
            BOOT[r.cell][per] = block_boot(db[per].to_numpy(), dy.to_numpy())
    n1 = int(R[R.fam != "R9"].T1_pass.sum()); n12 = int((R[R.fam != "R9"].T1_pass & R[R.fam != "R9"].T2_pass).sum())
    summ = dict(cells=int((R.fam != "R9").sum()), T1_pass=n1, both_pass=n12, p_T2_given_T1=(n12 / n1 if n1 else None), combos=len(combos),
                T2_pass_unconditional=int(R[R.fam != "R9"].T2_pass.sum()), base=base, base_life=base_life)
    R.to_csv(os.path.join(HERE, "ddlab_grid.csv"), index=False)
    json.dump(dict(summary=summ, grid=json.loads(R.to_json(orient="records")), boot=BOOT, best_single=best), open(os.path.join(HERE, "ddlab.json"), "w"), indent=1)
    print("done", round(time.time() - t0), "s", summ["cells"], "cells, T1 pass", n1, "both", n12, flush=True)


def supplement():
    """Post-hoc diagnostics (not selection): paired bootstrap of the DD change for the near-miss cells, days triggered by the period
    stops, DD-vs-net trade-off over the grid, lifecycle table. Appends 'supplement' to ddlab.json."""
    D = getD(NAME); P = pickle.load(open(SPECS, "rb")); XR, days = P["real"], P["days"]; dr = days["real"]
    J = json.load(open(os.path.join(HERE, "ddlab.json"))); G = pd.DataFrame(J["grid"]); base = J["summary"]["base"]
    db = {per: daily_pnl(XR[(XR.date >= PERS[per][0]) & (XR.date < PERS[per][1])], dr[(dr >= PERS[per][0]) & (dr < PERS[per][1])]) for per in ("T1", "T2")}
    near = [("R8W", 2, "R8 weekly loss stop W=2 ATR"), ("R4a", 1.0, "R4a daily loss block L=1.0 ATR"), ("R1", 0.3, "R1 stop<=k ATR k=0.3"), ("R3", 1.5, "R3 heat cap H=1.5 ATR"),
            ("R6", 4, "R6 session kill K=4 stop-outs"), ("R1", 0.2, "R1 stop<=k ATR k=0.2")]
    BOOT = {}; TRIG = {}
    for fam, prm, name in near:
        Y = apply_cell(D, XR, dr, fam, prm, False); BOOT[name] = {}
        for per in ("T1", "T2"):
            lo, hi = PERS[per]; dd_ = dr[(dr >= lo) & (dr < hi)]
            dy = daily_pnl(Y[(Y.date >= lo) & (Y.date < hi)], dd_).reindex(db[per].index, fill_value=0.0)
            BOOT[name][per] = block_boot(db[per].to_numpy(), dy.to_numpy())
            BOOT[name][per]["days_changed"] = int((dy.to_numpy() != db[per].to_numpy()).sum()); BOOT[name][per]["trades_dropped"] = int(base[per]["n"] - ((Y.date >= lo) & (Y.date < hi)).sum())
    G["eff_T1"] = G.T1_dd_chg - G.T1_net_chg; G["eff_T2"] = G.T2_dd_chg - G.T2_net_chg
    trade = dict(corr_dDD_dNet_T1=float(G.T1_dd_chg.corr(G.T1_net_chg)), corr_dDD_dNet_T2=float(G.T2_dd_chg.corr(G.T2_net_chg)),
                 cells_DD_down_more_than_net_both=[c for c in G[(G.eff_T1 < 0) & (G.eff_T2 < 0) & (G.T1_dd_chg < 0) & (G.T2_dd_chg < 0)].cell],
                 cells_DD_only_pass_both=[c for c in G[(G.T1_dd_chg <= -10) & (G.T2_dd_chg <= -5)].cell],
                 cells_DD_and_sharpe_T1=[c for c in G[(G.T1_dd_chg <= -10) & (G.T1_sharpe >= base["T1"]["sharpe"] - 0.005)].cell],
                 cells_DD_and_sharpe_T2=[c for c in G[(G.T2_dd_chg <= -5) & (G.T2_sharpe >= base["T2"]["sharpe"] - 0.005)].cell],
                 cells_worst_month_better_both=[c for c in G[(G.T1_worst_month > base["T1"]["worst_month"]) & (G.T2_worst_month > base["T2"]["worst_month"])].cell])
    J["supplement"] = dict(boot_near_miss=BOOT, tradeoff=trade)
    json.dump(J, open(os.path.join(HERE, "ddlab.json"), "w"), indent=1)
    for k, v in BOOT.items(): print(k, {p: (round(b["dd_chg_med"], 1), round(b["dd_chg_p10"], 1), round(b["dd_chg_p90"], 1), round(b["p_dd_lower_5pct"], 2), round(b["dsharpe_med"], 2), round(b["p_sharpe_up"], 2), b["days_changed"], b["trades_dropped"]) for p, b in v.items()})
    print(trade)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "build": build()
    elif cmd == "run": run()
    elif cmd == "supp": supplement()
