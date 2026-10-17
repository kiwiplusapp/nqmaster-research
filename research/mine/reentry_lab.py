"""reentry_lab (2026-10-17): SECOND ATTEMPT (re-entry) after a stop-out for the NQMaster Ultra modules, real Databento NQ 2020-10-15..2026-10
(six_lib protocol: T1 2020-10-15..2023 choose, T2 2024.. check; $1.90 + 1 tick per side, +4 ticks stress = u - 3).
Base portfolio = six_trades.pkl 'Ultra' (= cand16 UltraR rows + CPI09); the base rows carry fi / xi (cand16_trades.pkl), the exit reason is
recomputed here with the same exit engine (wrq_exits.sim, VOLB break-even, 0.10 ATR minimum stop) and checked against the stored exit bar.
What exists today (research = NQMaster.cs): ORB60/ORB90 up to 2 trades per day (re-armed when price closes back inside the range), MSEQ
any number of sequences per day, ICT up to 3 (but only 1 per day survives in the final set), VOLB / CRT11 / LON / time modules once per day.
Candidates built here (all derived from a base trade that exited by STOP LOSS, same session, same rules, w = 1):
  gen_check   : core-family generators (VOLB, VW13, VW13b, NF05, LF06, LF0430, LATE15, ENG10) re-run with maxday 2 / 3 -> extra events per day
  ORB3        : nt_v3_replica with orb_max 3 (the third ORB trade of the day; first two identical to the base), ORBt trigger + minstop filters
  VOLB_RE     : VOL_BREAK re-armed from the bar after the stop-out: next break of the same levels (RTH open +/- 0.45 x prior range), stop at the
                RTH open, 2R, break-even rule, entries before 15:00, either side (VOLB_RE_E) or the same side only (VOLB_RE_S)
  LON_RE      : London breakout re-armed from the bar after the stop-out: new close beyond the 00:00-03:00 range before 06:00 (with the daily
                trend, as the module), limit at the first FVG until 08:00, stop at the opposite range side (<= 0.25 ATR), 2R, exit 09:30
  NAIVE_S/_O  : every module: market re-entry at the open of the bar after the stop-out, same (S) or opposite (O) direction, same stop
                distance, same target distance, same deadline (hold / flat) and exit rule
  Existing second attempts (ORB rank 2, MSEQ rank 2+) are split by the exit reason of the first trade, and removing them is tested too.
Portfolio effect with six_lib.add_test; NinjaTrader feasibility = no opposite base position open at the re-entry minute (DirectionAllowed),
plus the base entries that an open re-entry would block. Usage: cd research/mine && python3 reentry_lab.py -> reentry_lab.json, reentry_report.md"""
import os, sys, json, pickle, importlib, numpy as np, pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.dirname(HERE)
for p in (HERE, RES):
    if p not in sys.path: sys.path.insert(0, p)
import six_lib as SL
from wrq_lib import getD, S, SLIP, TICK, time_exit, fills_core, NORM_COST
from wrq_exits import arrays, sim as exit_sim
NAME = "nqdb.npz"; BIG = 10 ** 7
SP = os.environ.get("REENTRY_SP", os.path.join(RES, "tmp", "reentry")); os.makedirs(SP, exist_ok=True)
PARAMS = {"VOLB": dict(be=0.75, beo=0.1)}                      # Ultra exit params (cand16: VOLB break-even after +0.75R to entry + 0.1R)
STRUCT = ["ORB60", "ORB90", "VOLB", "VOLB_tf1", "MSEQ", "MSEQS", "CRT11", "ICT", "LON", "ENG10"]; MINSTOP = 0.10
FLAT = S(1555)


# ------------------------------------------------------------------------------------------------ base trades with exit reasons
def base_rows():
    X = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["UltraR"][0]
    return X[X.date >= SL.START].sort_values(["date", "tin"]).reset_index(drop=True)


def entries():
    return pickle.load(open(os.path.join(HERE, "wrq_entries_db.pkl"), "rb"))


def module_exits(D, E, mod, slip=SLIP, norm=False):
    """Exit engine on every entry of a module (Ultra params + 0.10 ATR minimum stop for structure modules)."""
    Em = E[E["mod"] == mod].sort_values("fi", kind="stable")
    if mod in STRUCT:
        Em = Em[((Em.ent0 - Em.sl0).abs() / D.atr[D.day[Em.fi.to_numpy()]] >= MINSTOP).to_numpy()]
    A = arrays(Em); u, ok, out = exit_sim(A, D, slip, PARAMS.get(mod, {}), norm)
    R = pd.DataFrame(dict(mod=mod, fi=A["fi"], xi=out[:, 1].astype(np.int64), rs=out[:, 2].astype(np.int64), risk=out[:, 3], u_chk=u,
                          ent0=A["ent0"], et=A["et"], sl0=A["sl0"], tp0=A["tp0"], tx=A["tx"], d=A["d"]))
    return R[ok]


def base_with_reason(D, E):
    X = base_rows(); parts = []
    for mod in sorted(X["mod"].unique()):
        parts.append(module_exits(D, E, mod))
    R = pd.concat(parts, ignore_index=True)
    B = X.merge(R.drop(columns=["d"]), on=["mod", "fi"], how="left", suffixes=("", "_r"))
    chk = dict(rows=int(len(B)), matched=int(B.rs.notna().sum()), xi_equal=int((B.xi == B.xi_r).sum()), u_close=int((np.abs(B.u - B.u_chk) < 0.05).sum()))
    B["rank"] = B.groupby(["date", "mod"]).cumcount()
    return B, chk


# ------------------------------------------------------------------------------------------------ 1) core-family generator check
def gen_check(D):
    import wrq_build as WB
    out = {}
    for nm, (fam, p) in WB.FAM.items():
        if nm == "VOLB_tf1": continue
        gen, grid, md = WB.ALLF[fam]
        if isinstance(p, int): p = grid[p]
        ev = gen(D, p); n = len(ev["i"]); cnt = pd.Series(D.day[ev["i"]]).value_counts() if n else pd.Series(dtype=int)
        rec = dict(events=int(n), days=int(len(cnt)), max_events_per_day=int(cnt.max()) if n else 0)
        for k in (1, 2, 3):
            F = fills_core(D, ev, flat=955, maxday=k)
            rec[f"fills_maxday{k}"] = int(len(F)) if F is not None else 0
        out[nm] = rec
    return out


# ------------------------------------------------------------------------------------------------ 2a) ORB with orb_max 3
def orb_max3(D):
    cache = os.path.join(SP, "orb_max3.pkl")
    if os.path.exists(cache): return pickle.load(open(cache, "rb"))
    import wrq_build as WB
    from wrq_combo import k_trig
    os.environ["NQ_DATA"] = NAME; cwd = os.getcwd(); os.chdir(RES)
    try:
        import common; importlib.reload(common); import nt_v3_replica as r3
        from nt_v2_replica import daily_stats
        cx = common.Ctx()
    finally:
        os.chdir(cwd)
    A, T, _ = daily_stats(cx)
    PR = {cx.dates[dd]: (cx.prev_close[dd] - cx.prev_close[dd - 1]) / A[dd] * T[dd] for dd in range(2, cx.nd) if A[dd] > 0}
    base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=0.35, vw_stop=0.35)
    out = {}
    for nm, rm, t1 in (("ORB60", 60, 0.6), ("ORB90", 90, 0.6)):
        df = r3.run(cx, t1_r=t1, use_vwap=False, range_min=rm, entry_start=max(630, 570 + rm), orb_max=3, **base)
        df = df[df.date.map(PR) < 0.44]
        fi = df.entry_idx.to_numpy(); dd = df.dir.to_numpy(); e = df.entry.to_numpy(); rk = df.risk_pts.to_numpy()
        pts = (df.usd.to_numpy() + 1.0) / 2.0
        Em = WB.mk(D, nm, fi, dd, e - dd * SLIP, 0, e - dd * rk, e + dd * t1 * rk, time_exit(D, fi, BIG, 1555), pts * 2 - 1.9)
        Em["fomc"] = False
        Em = Em[k_trig(0.1, rm)(Em, NAME)]
        Em = Em[((Em.ent0 - Em.sl0).abs() / D.atr[D.day[Em.fi.to_numpy()]] >= MINSTOP).to_numpy()]
        Am = arrays(Em); u, ok, o = exit_sim(Am, D, SLIP, {}, False)
        R = pd.DataFrame(dict(date=Am["date"], mod=nm, fi=Am["fi"], xi=o[:, 1].astype(np.int64), rs=o[:, 2].astype(np.int64), d=Am["d"], u=u))[ok]
        R["rank"] = R.groupby("date").cumcount(); out[nm] = R.reset_index(drop=True)
        print(nm, "orb_max3 run:", len(R), R["rank"].value_counts().to_dict(), flush=True)
    pickle.dump(out, open(cache, "wb")); return out


# ------------------------------------------------------------------------------------------------ 2b) VOLB re-arm
@njit(cache=True)
def _volb_re(o, h, l, c, sm, de, atr, ro, pdh, pdl, days, starts, dfirst, k_, R, w1, hold, same_only, out):
    kk = 0
    for n in range(len(days)):
        d = days[n]; r = ro[d]
        if r < 0 or atr[d] <= 0 or np.isnan(pdh[d]): continue
        rng = pdh[d] - pdl[d]; up = o[r] + k_ * rng; dn = o[r] - k_ * rng
        for i in range(starts[n], de[d] + 1):
            if sm[i] >= w1: break
            s = 0
            if h[i] >= up: s = 1
            elif l[i] <= dn: s = -1
            if s == 0: continue
            if same_only == 1 and s != dfirst[n]: continue
            px = up if s == 1 else dn; sl = o[r]
            if (px - sl) * s <= 0: break
            tp = px + s * R * abs(px - sl)
            out[kk, 0] = i - 1; out[kk, 1] = s; out[kk, 2] = 2; out[kk, 3] = px; out[kk, 4] = sl; out[kk, 5] = tp; out[kk, 6] = i; out[kk, 7] = hold
            out[kk, 8] = n; kk += 1
            break
    return kk


def volb_rearm(D, B, same_only, k_=0.45, R=2.0, w1=1500, hold=400, slip=SLIP, norm=False, stops=None):
    st = B[(B["mod"] == "VOLB") & (B.rs == 0)] if stops is None else stops
    days = D.day[st.xi.to_numpy()]; starts = st.xi.to_numpy() + 1; dfirst = st.d.to_numpy().astype(np.int64)
    out = np.zeros((len(st), 9))
    k = _volb_re(D.o, D.h, D.l, D.c, D.sm, D.de, D.atr, D.ro, D.L[:, 0], D.L[:, 3], days.astype(np.int64), starts.astype(np.int64), dfirst, k_, R, S(w1), hold, int(same_only), out)
    o = out[:k]
    if k == 0: return None
    ev = dict(i=o[:, 0].astype(np.int64), d=o[:, 1], t=o[:, 2], px=o[:, 3], sl=o[:, 4], tp=o[:, 5], exp=o[:, 6].astype(np.int64), hold=o[:, 7].astype(np.int64))
    F = fills_core(D, ev, flat=955, maxday=1)
    if F is None or len(F) == 0: return None
    import wrq_build as WB
    Em = WB.mk(D, "VOLB", F.fi, F.d, F.ent0, F.et, F.sl0, F.tp0, time_exit(D, F.fi.to_numpy(), F.hold.to_numpy(), 1555), F.pts * 2 - 1.9); Em["fomc"] = False
    Em = Em[((Em.ent0 - Em.sl0).abs() / D.atr[D.day[Em.fi.to_numpy()]] >= MINSTOP).to_numpy()]
    return finish(D, Em, "VOLB", PARAMS["VOLB"], slip, norm, st)


# ------------------------------------------------------------------------------------------------ 2c) LON re-arm
@njit(cache=True)
def _lon_re(o, h, l, c, om, day, ds, de, atr, trend, days, starts, bias, R, max_risk, out):
    kk = 0
    for n in range(len(days)):
        d = days[n]; a = atr[d]
        if ds[d] < 0 or a <= 0: continue
        rh = -1e18; rl = 1e18; q = ds[d]
        while q <= de[d]:
            m = om[q]
            if m >= 0 and m < 180: rh = max(rh, h[q]); rl = min(rl, l[q])
            elif m >= 180 and m < 1080: break
            q += 1
        if rh < -1e17 or rl > 1e17: continue
        q = starts[n]; dirn = 0; bq = -1
        while q <= de[d]:
            m = om[q]
            if m >= 360 and m < 1080: break
            if c[q] > rh: dirn = 1; bq = q; break
            if c[q] < rl: dirn = -1; bq = q; break
            q += 1
        if dirn == 0 or (bias == 1 and dirn != trend[d]): continue
        lim = np.nan; entry = np.nan; eb = -1; q = bq
        while q <= de[d]:
            m = om[q]
            if m >= 480 and m < 1080: break
            if np.isnan(lim) and q >= 2:
                if dirn == 1 and l[q] > h[q - 2]: lim = l[q]
                if dirn == -1 and h[q] < l[q - 2]: lim = h[q]
                q += 1; continue
            if not np.isnan(lim):
                if (dirn == 1 and l[q] <= lim - TICK) or (dirn == -1 and h[q] >= lim + TICK):
                    eb = q; entry = min(lim, o[q]) if dirn == 1 else max(lim, o[q]); break
            q += 1
        if eb < 0 or np.isnan(entry): continue
        stop = rl if dirn == 1 else rh; risk = (entry - stop) * dirn
        if risk <= 0 or risk > max_risk * a: continue
        out[kk, 0] = eb; out[kk, 1] = dirn; out[kk, 2] = entry; out[kk, 3] = stop; out[kk, 4] = entry + dirn * R * risk; out[kk, 5] = n; kk += 1
    return kk


def lon_rearm(D, B, bias=1, R=2.0, max_risk=0.25, slip=SLIP, norm=False, stops=None):
    st = B[(B["mod"] == "LON") & (B.rs == 0)] if stops is None else stops
    days = D.day[st.xi.to_numpy()].astype(np.int64); starts = (st.xi.to_numpy() + 1).astype(np.int64)
    out = np.zeros((len(st), 6)); k = _lon_re(D.o, D.h, D.l, D.c, D.om, D.day, D.ds, D.de, D.atr, D.trend, days, starts, int(bias), R, max_risk, out)
    if k == 0: return None
    o = out[:k]; fi = o[:, 0].astype(np.int64); dd = o[:, 1].astype(np.int64)
    import wrq_build as WB
    Em = WB.mk(D, "LON", fi, dd, o[:, 2], 1, o[:, 3], o[:, 4], time_exit(D, fi, BIG, 930), np.zeros(k)); Em["fomc"] = False
    Em = Em[((Em.ent0 - Em.sl0).abs() / D.atr[D.day[Em.fi.to_numpy()]] >= MINSTOP).to_numpy()]
    return finish(D, Em, "LON", {}, slip, norm, st)


# ------------------------------------------------------------------------------------------------ 2d) naive re-entry at the bar after the stop
def naive(D, B, sign, mods=None, slip=SLIP, norm=False):
    st = B[B.rs == 0]
    if mods is not None: st = st[st["mod"].isin(mods)]
    parts = []
    for mod, g in st.groupby("mod"):
        xi = g.xi.to_numpy(); fi = xi + 1; d0 = g.d.to_numpy().astype(np.int64); d1 = sign * d0
        ok = (fi < D.n) & (D.day[np.minimum(fi, D.n - 1)] == D.day[xi]) & (fi < g.tx.to_numpy()) & (D.sm[np.minimum(fi, D.n - 1)] < FLAT)
        if not ok.any(): continue
        g = g[ok]; fi = fi[ok]; d0 = d0[ok]; d1 = d1[ok]
        e1 = g.ent0.to_numpy() + np.where(g.et.to_numpy() == 0, d0 * SLIP, 0.0); risk = np.abs(e1 - g.sl0.to_numpy()); tgt = np.abs(g.tp0.to_numpy() - e1)
        e2 = D.o[fi] + d1 * SLIP
        import wrq_build as WB
        Em = WB.mk(D, mod, fi, d1, D.o[fi], 0, e2 - d1 * risk, e2 + d1 * tgt, g.tx.to_numpy(), np.zeros(len(fi))); Em["fomc"] = False
        parts.append(finish(D, Em, mod, PARAMS.get(mod, {}), slip, norm, g))
    return pd.concat([p for p in parts if p is not None], ignore_index=True) if parts else None


def finish(D, Em, mod, p, slip, norm, st):
    """Exit engine on candidate entries -> trade table (date, mod, tin, tout, d, u, w, fi, xi, rs, same, d0)."""
    if Em is None or len(Em) == 0: return None
    Em = Em.sort_values("fi", kind="stable"); A = arrays(Em); u, ok, o = exit_sim(A, D, slip, p, norm)
    T = pd.DataFrame(dict(date=A["date"], mod=mod, fi=A["fi"], xi=o[:, 1].astype(np.int64), rs=o[:, 2].astype(np.int64), d=A["d"], u=u))[ok].copy()
    T["tin"] = D.sm[T.fi.to_numpy()]; T["tout"] = D.sm[T.xi.to_numpy()] + 1; T["w"] = 1.0
    d0 = st.groupby("date").d.first() if "date" in st else None
    T["d0"] = T.date.map(d0).to_numpy() if d0 is not None else np.nan
    T["same"] = (T.d == T.d0)
    return T.reset_index(drop=True)


# ------------------------------------------------------------------------------------------------ 3) evaluation
def overlap(T, base):
    """For each candidate trade: is a base position open at its entry minute (any / opposite), and how many base entries would it block."""
    anyo = np.zeros(len(T), bool); oppo = np.zeros(len(T), bool); blocked = np.zeros(len(T), int); blocked_u = np.zeros(len(T))
    bg = {d: g for d, g in base.groupby("date")}
    for k, r in enumerate(T.itertuples()):
        g = bg.get(r.date)
        if g is None: continue
        live = (g.tin.to_numpy() <= r.tin) & (g.tout.to_numpy() > r.tin) & ~((g["mod"].to_numpy() == r.mod) & (g.tin.to_numpy() == r.tin))
        anyo[k] = live.any(); oppo[k] = (live & (g.d.to_numpy() == -r.d)).any()
        later = (g.tin.to_numpy() > r.tin) & (g.tin.to_numpy() < r.tout) & (g.d.to_numpy() == -r.d)
        blocked[k] = int(later.sum()); blocked_u[k] = float((g.u.to_numpy() * g.w.to_numpy())[later].sum())
    T = T.copy(); T["open_any"] = anyo; T["open_opp"] = oppo; T["blocks"] = blocked; T["blocks_u"] = blocked_u
    return T


def tst(T, extra=0.0):
    return SL.tstats(T.u.to_numpy() - extra, T.date.to_numpy())


def accept(st, st4, port):
    t1, t2 = st["T1"], st["T2"]; b, c = port["base"], port["comb"]
    ok = dict(T1_n60_pf13=bool(t1["n"] >= 60 and (t1["pf"] or 0) >= 1.3), T2_pf12=bool((t2["pf"] or 0) >= 1.2), T2_plus4t_pf11=bool((st4["T2"]["pf"] or 0) >= 1.1),
              sharpe_up_T1=bool(c["T1"]["sharpe"] > b["T1"]["sharpe"]), sharpe_up_T2=bool(c["T2"]["sharpe"] > b["T2"]["sharpe"]),
              maxdd_ok=bool(c["all"]["maxdd"] <= 1.05 * b["all"]["maxdd"]), worst_month_ok=bool(c["all"]["worst_month"] >= 1.05 * b["all"]["worst_month"]))
    ok["pass"] = all(ok.values()); return ok


def evaluate(T, base, label):
    T = overlap(T, base); rec = dict(label=label, n=int(len(T)), by_mod=T.groupby("mod").size().to_dict())
    rec["standalone"] = tst(T); rec["plus4t"] = tst(T, 3.0)
    rec["avg_usd"] = {k: round(float(T[(T.date < SL.MID) if k == "T1" else (T.date >= SL.MID)].u.mean()), 1) if len(T) else None for k in ("T1", "T2")}
    rec["exit_reasons"] = {int(k): int(v) for k, v in T.rs.value_counts().items()}
    rec["years"] = {int(y): dict(n=int(len(g)), wr=round(100 * float((g.u > 0).mean()), 1), pf=round(float(g.u[g.u > 0].sum() / -g.u[g.u <= 0].sum()), 2) if (g.u <= 0).any() else None, net=round(float(g.u.sum())))
                    for y, g in T.groupby(T.date // 10000)}
    for nm, m in (("same_dir", T.same.to_numpy()), ("opp_dir", ~T.same.to_numpy())):
        if m.any(): rec[nm] = tst(T[m])
    rec["overlap"] = dict(open_any_pct=round(100 * float(T.open_any.mean()), 1), open_opp_pct=round(100 * float(T.open_opp.mean()), 1),
                          base_entries_blocked=int(T.blocks.sum()), blocked_base_usd=round(float(T.blocks_u.sum())))
    rec["portfolio"] = SL.add_test(SL.daily(T)); rec["accept"] = accept(rec["standalone"], rec["plus4t"], rec["portfolio"])
    F = T[~T.open_opp]
    if len(F) and len(F) < len(T):
        rec["nt_feasible"] = dict(n=int(len(F)), standalone=tst(F), portfolio=SL.add_test(SL.daily(F)))
        rec["nt_feasible"]["accept"] = accept(rec["nt_feasible"]["standalone"], tst(F, 3.0), rec["nt_feasible"]["portfolio"])
    return rec, T


def existing_split(B, mod):
    """Existing 2nd+ attempts of a module in the base, split by the exit reason of the previous trade; and the portfolio without them."""
    g = B[B["mod"] == mod].copy(); g["prev_rs"] = g.groupby("date").rs.shift(1)
    sec = g[g["rank"] >= 1]; out = dict(n_first=int((g["rank"] == 0).sum()), n_second_plus=int(len(sec)))
    for nm, m in (("after_stop", sec.prev_rs == 0), ("after_target", sec.prev_rs == 1), ("after_other", ~sec.prev_rs.isin([0, 1]))):
        if m.any(): out[nm] = tst(sec[m])
    out["all_second"] = tst(sec); out["all_second_plus4t"] = tst(sec, 3.0)
    if len(sec): out["portfolio_without_second"] = SL.add_test(SL.daily(sec), w=-1.0)
    return out


def norm_1519(D, E, B_fn):
    """2015-19 cost-normalised view (P&L in % of daily ATR, cost 0.345% ATR, no slippage) of the same re-entry rules."""
    out = {}
    stops = {}
    for mod in ("VOLB", "LON"):
        R = module_exits(D, E, mod, slip=0.0, norm=True); R["date"] = D.date[R.fi.to_numpy()]
        stops[mod] = R[(R.date >= 20150101) & (R.date < 20200101) & (R.rs == 0)]
        out[mod + "_base_norm"] = _nst(R[(R.date >= 20150101) & (R.date < 20200101)].u_chk)
    for lab, T in (("VOLB_RE_E", volb_rearm(D, None, 0, slip=0.0, norm=True, stops=stops["VOLB"])), ("VOLB_RE_S", volb_rearm(D, None, 1, slip=0.0, norm=True, stops=stops["VOLB"])),
                   ("VOLB_RE_E_k60", volb_rearm(D, None, 0, k_=0.6, slip=0.0, norm=True, stops=stops["VOLB"])), ("LON_RE", lon_rearm(D, None, 1, slip=0.0, norm=True, stops=stops["LON"]))):
        out[lab] = _nst(T.u) if T is not None else None
    return out


def _nst(u):
    u = np.asarray(u, float); lo = -u[u <= 0].sum()
    return dict(n=int(len(u)), wr=round(100 * float((u > 0).mean()), 1) if len(u) else None, pf=round(float(u[u > 0].sum() / lo), 3) if lo > 0 else None, mean_pct_atr=round(float(u.mean()), 3) if len(u) else None)


def fmt_st(s):
    return " / ".join(f"{k}: n {v['n']} WR {v['wr']} PF {v['pf']} ${v['net']:,}" for k, v in s.items())


def report(OUT):
    L = ["# Re-entry (second attempt) after a stop-out — NQMaster Ultra, real NQ 2020-10..2026-10", "",
         "Protocol: six_lib (T1 2020-10-15..2023 choose, T2 2024.. check; T1 n>=60 & PF>=1.3, T2 PF>=1.2, +4 ticks T2 PF>=1.1, Sharpe up in T1 and T2, maxDD / worst month not worse by >5%).",
         "All candidates start after a base trade that exited by stop loss, same session, same rules, 1 contract, $1.90 + 1 tick per side.", "",
         "## What exists today (research = NQMaster.cs)", "",
         "| Module | Trades/day allowed | Re-arm rule |", "|---|---|---|",
         "| ORB60 / ORB90 | 2 | after any exit, when a close is back inside the range (nt_v3_replica orb_max 2 = NQMaster o.Trades < 2) |",
         "| MSEQ / MSEQS | unlimited | next valid 5-candle sequence (wr60.sim; NQMaster has no per-day flag) |",
         "| ICT | 3 | another sweep of a different level (max_day 3 / ictTrades < 3); only 1 per day survives in the final set |",
         "| VOLB, CRT11, LON, time modules | 1 | none (volbDone, crt.Done, m.Done) |", ""]
    c = OUT["base_check"]; L += [f"Base check: {c['rows']} base rows, {c['matched']} matched to recomputed exits, exit bar equal {c['xi_equal']}, P&L equal {c['u_close']}.", ""]
    L += ["## 1. Core-family generators with maxday 2 / 3", "", "| Module | events | days | max events/day | fills maxday 1 / 2 / 3 |", "|---|---|---|---|---|"]
    for k, v in OUT["gen_check"].items():
        L.append(f"| {k} | {v['events']} | {v['days']} | {v['max_events_per_day']} | {v['fills_maxday1']} / {v['fills_maxday2']} / {v['fills_maxday3']} |")
    L += ["", "Every core-family generator emits at most one event per day (the first break / the clock bar), so maxday > 1 adds nothing; a re-entry needs a re-armed generator (VOLB_RE below).", ""]
    L += ["## 2. Existing second attempts in the base (ORB rank 2, MSEQ rank 2+), by the exit of the previous trade", ""]
    for mod, v in OUT["existing"].items():
        L.append(f"**{mod}**: first trades {v['n_first']}, second+ {v['n_second_plus']}")
        for k in ("after_stop", "after_target", "after_other", "all_second", "all_second_plus4t"):
            if k in v: L.append(f"- {k}: {fmt_st(v[k])}")
        if "portfolio_without_second" in v:
            p = v["portfolio_without_second"]; L.append(f"- portfolio WITHOUT them: Sharpe T1 {p['base']['T1']['sharpe']} -> {p['comb']['T1']['sharpe']}, T2 {p['base']['T2']['sharpe']} -> {p['comb']['T2']['sharpe']}, maxDD {p['base']['all']['maxdd']} -> {p['comb']['all']['maxdd']}")
        L.append("")
    L += [f"Unfiltered orb_max 3 run (2020-10..): ORB60 first-trade stop-outs {OUT['ORB60_run_first_stops']}, second trades by previous exit (0 stop / 1 target / 2 time) {OUT['ORB60_run_second_prev_rs']}; ORB90 {OUT['ORB90_run_first_stops']} / {OUT['ORB90_run_second_prev_rs']}. After a stop the price sits beyond the opposite side of the range, so a close back inside the range plus a new break of the trend side before 13:00 almost never happens: the ORB second attempt after a stop-out is a non-event; the existing second trades follow targets.", ""]
    L += ["## 3. New second-attempt candidates", "", "| Candidate | n | T1 n / WR / PF / $ | T2 n / WR / PF / $ | +4t T2 PF | avg $ T1 / T2 | Sharpe T1 base->comb | Sharpe T2 base->comb | maxDD base->comb | worst mo base->comb | corr | open opp % | base entries blocked ($) | pass |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for lab, r in OUT["candidates"].items():
        s, s4, p = r["standalone"], r["plus4t"], r["portfolio"]; b, cm = p["base"], p["comb"]
        L.append(f"| {lab} | {r['n']} | {s['T1']['n']} / {s['T1']['wr']} / {s['T1']['pf']} / {s['T1']['net']:,} | {s['T2']['n']} / {s['T2']['wr']} / {s['T2']['pf']} / {s['T2']['net']:,} | {s4['T2']['pf']} | {r['avg_usd']['T1']} / {r['avg_usd']['T2']} | {b['T1']['sharpe']} -> {cm['T1']['sharpe']} | {b['T2']['sharpe']} -> {cm['T2']['sharpe']} | {b['all']['maxdd']:,} -> {cm['all']['maxdd']:,} | {b['all']['worst_month']:,} -> {cm['all']['worst_month']:,} | {p['corr']} | {r['overlap']['open_opp_pct']} | {r['overlap']['base_entries_blocked']} ({r['overlap']['blocked_base_usd']:,}) | {'YES' if r['accept']['pass'] else 'no'} |")
    L += ["", "Direction split (same = same direction as the stopped trade):", ""]
    for lab, r in OUT["candidates"].items():
        parts = [f"{k}: {fmt_st(r[k])}" for k in ("same_dir", "opp_dir") if k in r]
        L.append(f"- {lab}: " + " | ".join(parts) + f" | exits {r['exit_reasons']}")
        if "nt_feasible" in r:
            f = r["nt_feasible"]; L.append(f"  - NT-feasible subset (no opposite base position open): n {f['n']}, {fmt_st(f['standalone'])}, Sharpe T1 {f['portfolio']['base']['T1']['sharpe']} -> {f['portfolio']['comb']['T1']['sharpe']}, T2 {f['portfolio']['base']['T2']['sharpe']} -> {f['portfolio']['comb']['T2']['sharpe']}, pass {'YES' if f['accept']['pass'] else 'no'}")
    L += ["", "VOLB re-arm plateau (first trade unchanged; re-armed break level k x prior range, target R; T1 -> T2 as n / WR / PF / $):", ""]
    for k, v in OUT["VOLB_RE_plateau"].items():
        if v: L.append(f"- {k}: T1 {v['T1']['n']} / {v['T1']['wr']} / {v['T1']['pf']} / {v['T1']['net']:,} -> T2 {v['T2']['n']} / {v['T2']['wr']} / {v['T2']['pf']} / {v['T2']['net']:,}")
    L += ["", "Yearly (n / WR / PF / $) of the main candidates:", ""]
    for lab in ("VOLB_RE_E", "VOLB_RE_E_k60", "NAIVE_O_struct", "NAIVE_S_all"):
        if lab in OUT["candidates"]: L.append(f"- {lab}: " + ", ".join(f"{y}: {v['n']}/{v['wr']}/{v['pf']}/{v['net']:,}" for y, v in OUT["candidates"][lab]["years"].items()))
    L += ["", "Per-module naive re-entry (same direction, market at the bar after the stop):", "", "| Module | T1 n / WR / PF / $ | T2 n / WR / PF / $ |", "|---|---|---|"]
    for mod, s in OUT["naive_same_by_mod"].items():
        L.append(f"| {mod} | {s['T1']['n']} / {s['T1']['wr']} / {s['T1']['pf']} / {s['T1']['net']:,} | {s['T2']['n']} / {s['T2']['wr']} / {s['T2']['pf']} / {s['T2']['net']:,} |")
    L += ["", "Per-module naive re-entry (opposite direction, stop-and-reverse):", "", "| Module | T1 n / WR / PF / $ | T2 n / WR / PF / $ |", "|---|---|---|"]
    for mod, s in OUT["naive_opp_by_mod"].items():
        L.append(f"| {mod} | {s['T1']['n']} / {s['T1']['wr']} / {s['T1']['pf']} / {s['T1']['net']:,} | {s['T2']['n']} / {s['T2']['wr']} / {s['T2']['pf']} / {s['T2']['net']:,} |")
    if OUT.get("norm_1519"):
        L += ["", "## 4. 2015-19 cost-normalised check (P&L in % of daily ATR, cost 0.345% ATR, no slippage)", ""]
        for k, v in OUT["norm_1519"].items(): L.append(f"- {k}: {v}")
    if OUT.get("dd_window"):
        L += ["", "Drawdown windows (base max-DD window and the candidate's $ inside it):", ""]
        for k, v in OUT["dd_window"].items(): L.append(f"- {k}: {v}")
    L += ["", "## 5. Verdict", ""] + OUT["verdict"] + ["", "Conclusions:", ""] + OUT["conclusions"]
    open(os.path.join(HERE, "reentry_report.md"), "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    D = getD(NAME); E = entries(); base = SL.base()
    B, chk = base_with_reason(D, E); print("base check", chk, flush=True)
    OUT = {"base_check": chk, "base_stops_by_mod": B[B.rs == 0].groupby("mod").size().to_dict()}
    OUT["gen_check"] = gen_check(D); print("gen_check", OUT["gen_check"], flush=True)
    OUT["existing"] = {m: existing_split(B, m) for m in ("ORB60", "ORB90", "MSEQ")}
    print("existing", json.dumps(OUT["existing"], default=float)[:1500], flush=True)
    C = {}; TT = {}
    # ORB third attempt
    O3 = orb_max3(D)
    for nm in ("ORB60", "ORB90"):
        R = O3[nm]; chk3 = dict(base_n=int((B["mod"] == nm).sum()), run_rank01_n=int((R["rank"] <= 1).sum()), base_fi_in_run=int(B[B["mod"] == nm].fi.isin(R.fi).sum()))
        third = R[(R["rank"] == 2) & (R.date >= SL.START) & R.date.isin(set(B.date))].copy()
        prev = R[R["rank"] == 1].set_index("date").rs
        third["prev_rs"] = third.date.map(prev); OUT[f"{nm}_orb_max3_check"] = chk3; OUT[f"{nm}_third_prev_rs"] = {int(k): int(v) for k, v in third.prev_rs.value_counts().items()}
        third["tin"] = D.sm[third.fi.to_numpy()]; third["tout"] = D.sm[third.xi.to_numpy()] + 1; third["w"] = 1.0; third["d0"] = third.d; third["same"] = True
        if len(third): C[nm + "_3RD"] = third
    C["VOLB_RE_E"] = volb_rearm(D, B, 0); C["VOLB_RE_S"] = volb_rearm(D, B, 1)
    # plateau of the re-armed break around the module's own cell (k 0.45, R 2): neighbouring k and R, first trade unchanged
    OUT["VOLB_RE_plateau"] = {}
    for k_ in (0.3, 0.45, 0.6, 0.75, 0.9):
        for R in (1.0, 2.0):
            Tp = volb_rearm(D, B, 0, k_=k_, R=R); Tp = Tp[Tp.date >= SL.START] if Tp is not None else None
            OUT["VOLB_RE_plateau"][f"k{k_}_R{R}"] = tst(Tp) if Tp is not None and len(Tp) else None
    C["VOLB_RE_E_k60"] = volb_rearm(D, B, 0, k_=0.6)            # T1-best cell of that grid (a parameter choice, reported separately)
    for nm in ("ORB60", "ORB90"):                                  # unfiltered orb_max3 run: how often does the 2nd ORB trade follow a stop?
        R = O3[nm]; R = R[R.date >= SL.START]; prv = R.groupby("date").rs.shift(1); sec = R[R["rank"] == 1]
        OUT[f"{nm}_run_second_prev_rs"] = {str(int(k)) if k == k else "nan": int(v) for k, v in prv[sec.index].value_counts(dropna=False).items()}
        OUT[f"{nm}_run_first_stops"] = int(((R["rank"] == 0) & (R.rs == 0)).sum())
    C["LON_RE"] = lon_rearm(D, B, 1); C["LON_RE_anydir"] = lon_rearm(D, B, 0)
    NS = naive(D, B, +1); NO = naive(D, B, -1)
    for mods, lab in ((STRUCT, "struct"), (None, "all")):
        s = NS if mods is None else NS[NS["mod"].isin(mods)]; o = NO if mods is None else NO[NO["mod"].isin(mods)]
        C[f"NAIVE_S_{lab}"] = s; C[f"NAIVE_O_{lab}"] = o
    OUT["naive_same_by_mod"] = {m: tst(g) for m, g in NS.groupby("mod")}; OUT["naive_opp_by_mod"] = {m: tst(g) for m, g in NO.groupby("mod")}
    OUT["candidates"] = {}
    for lab, T in C.items():
        if T is None or len(T) == 0: print(lab, "no trades"); continue
        T = T[T.date >= SL.START]
        rec, Tx = evaluate(T, base, lab); OUT["candidates"][lab] = rec; TT[lab] = Tx[["date", "mod", "tin", "tout", "d", "u", "w", "rs", "same", "open_any", "open_opp", "blocks", "blocks_u"]]
        s = rec["standalone"]; print(f"{lab:16s} n {rec['n']:4d} | {fmt_st(s)} | +4t T2 PF {rec['plus4t']['T2']['pf']} | Sharpe T1 {rec['portfolio']['base']['T1']['sharpe']}->{rec['portfolio']['comb']['T1']['sharpe']} T2 {rec['portfolio']['base']['T2']['sharpe']}->{rec['portfolio']['comb']['T2']['sharpe']} | opp-open {rec['overlap']['open_opp_pct']}% | pass {rec['accept']['pass']}", flush=True)
    try:
        OUT["norm_1519"] = norm_1519(D, E, None); print("norm 2015-19", OUT["norm_1519"], flush=True)
    except Exception as ex:
        OUT["norm_1519"] = None; print("norm_1519 failed:", repr(ex))
    # where the extra drawdown comes from (base max-DD window, positional)
    OUT["dd_window"] = {}
    b = SL.daily(base)
    for lab in ("VOLB_RE_E", "VOLB_RE_E_k60"):
        if lab not in TT: continue
        c = SL.daily(TT[lab]).reindex(b.index, fill_value=0.0); rec = {}
        for nm, d in (("base", b), ("comb", b + c)):
            eq = d.cumsum().to_numpy(); dd = np.maximum.accumulate(eq) - eq; i = int(np.argmax(dd)); pk = int(np.argmax(eq[:i + 1]))
            rec[nm] = dict(maxdd=round(float(dd[i])), peak=int(d.index[pk]), trough=int(d.index[i]), cand_in_window=round(float(c.to_numpy()[pk + 1:i + 1].sum())))
        cs = c.cumsum().to_numpy(); rec["cand_standalone_maxdd"] = round(float((np.maximum.accumulate(cs) - cs).max()))
        OUT["dd_window"][lab] = rec
    V = []
    for lab, r in OUT["candidates"].items():
        a = r["accept"]; fails = [k for k, v in a.items() if k != "pass" and not v]
        V.append(f"- {lab}: {'PASSES' if a['pass'] else 'fails ' + ', '.join(fails)}")
    OUT["verdict"] = V
    c = OUT["candidates"]; e = OUT["existing"]
    def pp(lab): r = c[lab]; s = r["standalone"]; p = r["portfolio"]; return f"T1 n {s['T1']['n']} PF {s['T1']['pf']} / T2 n {s['T2']['n']} PF {s['T2']['pf']}, +4t T2 {r['plus4t']['T2']['pf']}, Sharpe {p['base']['T1']['sharpe']}->{p['comb']['T1']['sharpe']} / {p['base']['T2']['sharpe']}->{p['comb']['T2']['sharpe']}, net 6y {p['comb']['all']['net'] - p['base']['all']['net']:+,}, maxDD {p['base']['all']['maxdd']:,}->{p['comb']['all']['maxdd']:,} ({100 * (p['comb']['all']['maxdd'] / p['base']['all']['maxdd'] - 1):+.1f}%)"
    OUT["conclusions"] = [
        f"- ORB60/ORB90: a second attempt after a STOP almost never exists ({OUT['ORB60_run_first_stops']} ORB60 stop-outs, {OUT['ORB60_run_second_prev_rs'].get('0', 0)} re-entries after them in 6 years; ORB90 {OUT['ORB90_run_first_stops']} / {OUT['ORB90_run_second_prev_rs'].get('0', 0)}). The existing second trades (after a target) are good (ORB60 {e['ORB60']['all_second']['T1']['pf']} / {e['ORB60']['all_second']['T2']['pf']}, ORB90 n {e['ORB90']['n_second_plus']}) and removing them lowers Sharpe -> keep the 2-per-day rule as it is. A third trade per day: {c['ORB60_3RD']['n'] if 'ORB60_3RD' in c else 0} trade(s) in 6 years -> nothing to gain.",
        f"- MSEQ: re-entries already allowed; only {e['MSEQ'].get('after_stop', {}).get('T1', {}).get('n', 0) + e['MSEQ'].get('after_stop', {}).get('T2', {}).get('n', 0)} second sequences after a stop in 6 years (the sequence needs 5 rising candles above the main low, which a stop-out destroys); second sequences after a target: T1 PF {e['MSEQ']['after_target']['T1']['pf']} / T2 {e['MSEQ']['after_target']['T2']['pf']} (n {e['MSEQ']['after_target']['T1']['n']} / {e['MSEQ']['after_target']['T2']['n']}); removing all second+ sequences changes Sharpe by {e['MSEQ']['portfolio_without_second']['comb']['T1']['sharpe'] - e['MSEQ']['portfolio_without_second']['base']['T1']['sharpe']:+.3f} / {e['MSEQ']['portfolio_without_second']['comb']['T2']['sharpe'] - e['MSEQ']['portfolio_without_second']['base']['T2']['sharpe']:+.3f} -> leave as is.",
        f"- VOLB re-arm, same rules (either side, k 0.45, stop at the RTH open, 2R, BE): {pp('VOLB_RE_E')}; 2015-19 cost-normalised PF {OUT['norm_1519']['VOLB_RE_E']['pf'] if OUT.get('norm_1519') else 'n/a'} (base VOLB {OUT['norm_1519']['VOLB_base_norm']['pf'] if OUT.get('norm_1519') else 'n/a'}); opposite-open conflicts {c['VOLB_RE_E']['overlap']['open_opp_pct']}%. Passes every rule except max DD (+6%, limit +5%): the extra trades lose in the 2023 drawdown window. Same-side-only re-arm fails T2 (PF {c['VOLB_RE_S']['standalone']['T2']['pf']}).",
        f"- VOLB re-arm with a wider second level (k 0.6, T1-best of the k grid, every year 2020-26 positive): {pp('VOLB_RE_E_k60')}; 2015-19 norm PF {OUT['norm_1519'].get('VOLB_RE_E_k60', {}).get('pf') if OUT.get('norm_1519') else 'n/a'}. Also fails only the max-DD rule (+7.7%). It is a parameter choice on a 5x2 grid (plateau OK: all k cells T1 PF >= 1.35).",
        f"- LON re-arm (trend side, FVG limit): {c['LON_RE']['n']} trades in 6 years -> non-event; allowing the counter-trend side after the stop: T1 PF {c['LON_RE_anydir']['standalone']['T1']['pf']} / T2 {c['LON_RE_anydir']['standalone']['T2']['pf']} -> fails T1, and {c['LON_RE_anydir']['overlap']['open_opp_pct']}% would be blocked by an opposite open position.",
        f"- CRT11 / ICT / time modules: no second trigger exists in the same session (CRT11 one candle pair, ICT other levels are already allowed but ~never fire, clock modules fire once). Naive same-direction re-entry at the bar after the stop loses everywhere (structure modules T1 PF {c['NAIVE_S_struct']['standalone']['T1']['pf']} / T2 {c['NAIVE_S_struct']['standalone']['T2']['pf']}; all modules {c['NAIVE_S_all']['standalone']['T1']['pf']} / {c['NAIVE_S_all']['standalone']['T2']['pf']}, Sharpe down 0.2-0.5): the stop carries information. Stop-and-reverse (opposite): structure T1 {c['NAIVE_O_struct']['standalone']['T1']['pf']} / T2 {c['NAIVE_O_struct']['standalone']['T2']['pf']}, all {c['NAIVE_O_all']['standalone']['T1']['pf']} / {c['NAIVE_O_all']['standalone']['T2']['pf']}: positive only in T2 (T1 fails), {c['NAIVE_O_struct']['overlap']['open_opp_pct']}% / {c['NAIVE_O_all']['overlap']['open_opp_pct']}% conflict with open positions and it would block {c['NAIVE_O_all']['overlap']['base_entries_blocked']} base entries -> rejected.",
        "- Nothing passes the six_lib protocol. The only candidate worth a note is the VOLB re-arm (either side), +$58-110 per month per contract with a slightly deeper max DD; it could be re-checked after a year of new data, not added now.",
    ]
    pickle.dump(TT, open(os.path.join(HERE, "reentry_trades.pkl"), "wb"))
    json.dump(OUT, open(os.path.join(HERE, "reentry_lab.json"), "w"), indent=1, default=float)
    report(OUT); print("\n".join(V))
