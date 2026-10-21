"""avg_entry: pre-registered ENTRY-AVERAGING LAB on the 2027 NQMaster default (Ultra + SO04 / RV11 / ORFAIL / CAM3 = nt_compare
'ultra_d4'), 2026-10-21.  Question (Federico): does splitting a module's position into several entries at different prices help?

Machinery: perturb_lib rebuilds every module from its ORIGINAL signal code on real Databento NQ 2010-06..2026-10 (research/data/nqdb.npz).
Per trade we take the module's entry spec (fill bar fi, side d, raw entry ent0, order type et, stop sl0, target tp0, forced time-exit
bar tx) and re-simulate the exits with a TWO-LEG version of wrq_lib.xsim (same bar order: stop first, target needs a 1-tick
trade-through and is never filled on the fill bar, time exit at the bar close - 1 tick, one position per module).  The base variant
(1 leg) reproduces the committed base trade set exactly (checked in `build`).  Costs: $1.90 commission per MNQ unit filled, 1 tick per
side on market / stop fills (limit fills pay no entry slippage), cost-normalised view = 0.345 % of daily ATR per unit, slippage 0.
Module total size = 1 base unit in every variant (0.5 + 0.5); ratio metrics are size-invariant, so the 2-lot (1 + 1) and 4-lot
(2 + 2) integer versions are the same trades x2 / x4 (reported in the json / report).

Variants (per module, ALL modules get the same geometry; k relative to the trade's own stop distance r0 = |entry - stop| or
target distance tdist = |target - entry|):
  V1 split-better  k .25/.5/.75  half at the module's entry, half as a LIMIT at entry - k x r0 (better price, i.e. an average
                                 into the pullback); same stop / target for both legs; the limit dies when the trade exits.
  V2 split-worse   k .25/.5      half at entry, half as a STOP order at entry + k x r0 (worse price; the second leg's risk is
                                 (1 + k) r0, so the total risk rises); same stop / target.
  V3 pyramid       k .25/.5 x {stop moved to the original entry for the whole position when leg 2 fills, stop unchanged}
                                 half at entry, half as a STOP order at entry + k x tdist.
  V4 all-limit     k .25/.5      100 % as a LIMIT at entry - k x r0, live until the time exit, cancelled if the target is touched
                                 first; fill rate reported (the 'limit entry' idea).
  V5 time-split    N 5/15        half at the signal, half at MARKET N bars later if the trade is still open (open not beyond the stop).
VOLB keeps its break-even rule (stop to entry + 0.1 R after +0.75 R, measured from leg 1).
Periods (Federico's split): CHOOSE on T1 = 2019-01-01..2022-12-31 (real $, days with ATR >= 150 as NQMaster's MinATR guard; and the
cost-normalised view T1n where 2019 counts in full) + A = 2010-14 + B = 2015-19 cost-normalised (regime control);
CHECK on T2 = 2023-01-01..2026-10 real $ (never used to choose).
Acceptance (fixed before looking): portfolio Sharpe (conflict filter, agreement, confluence, context rules, MinATR 150, x2 / x4
weights, all other modules unchanged) UP in T1, T1n, A and B; then T2 Sharpe not lower, T2 PF and WR not lower, T2 maxDD not
higher by more than 5 %.  Base rates P(T2 Sharpe up | T1 up) vs P(T2 up) are reported over all module x variant cells.
Global cells: every variant applied to ALL modules at once, to the structure modules only, and to the clock modules only.
Usage: python3 avg_entry.py build | run | report      (<= 2 processes; cells cached in <scratch>/avg/, resumable)
Outputs: avg_entry_cells.csv, avg_entry.json, avg_entry_report.md.  Import-safe (no work at import)."""
import os, sys, json, time, pickle, numpy as np, pandas as pd
os.environ.setdefault("NUMBA_NUM_THREADS", "2"); os.environ.setdefault("OMP_NUM_THREADS", "2"); os.environ.setdefault("MKL_NUM_THREADS", "2")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from numba import njit
import perturb_lib as P
from wrq_lib import fills_core, time_exit, SLIP, NORM_COST
from core import S, TICK
SCR = os.environ.get("AVG_SCRATCH", "/tmp/claude-0/-home-user-nqmaster-research/176a42ca-c215-52e2-84dc-57e214e477d4/scratchpad")
AV = os.path.join(SCR, "avg"); os.makedirs(AV, exist_ok=True)
SPECS = os.path.join(AV, "avg_specs.pkl"); BASEP = os.path.join(AV, "avg_base_parts.pkl")
PERIODS = {"A": (20100601, 20150101, "norm"), "B": (20150101, 20200101, "norm"), "T1n": (20190101, 20230101, "norm"),
           "T1": (20190101, 20230101, "real"), "T2": (20230101, 20991231, "real")}
CHOOSE = ["T1", "T1n", "A", "B"]
STRUCT = ["ORB60", "ORB90", "VOLB", "MSEQ", "MSEQS", "CRT11", "ICT", "LON", "ORFAIL", "CAM3"]
CLOCK = [m for m in P.MODS if m not in STRUCT]
VARIANTS = [("base", dict(mode=0, k=0.0, sm=0, N=0))]
VARIANTS += [(f"V1_k{k}", dict(mode=1, k=k, sm=0, N=0)) for k in (0.25, 0.5, 0.75)]
VARIANTS += [(f"V2_k{k}", dict(mode=2, k=k, sm=0, N=0)) for k in (0.25, 0.5)]
VARIANTS += [(f"V3_k{k}_sm{sm}", dict(mode=3, k=k, sm=sm, N=0)) for k in (0.25, 0.5) for sm in (1, 0)]
VARIANTS += [(f"V4_k{k}", dict(mode=4, k=k, sm=0, N=0)) for k in (0.25, 0.5)]
VARIANTS += [(f"V5_N{N}", dict(mode=5, k=0.0, sm=0, N=N)) for N in (5, 15)]
VNAMES = [v for v, _ in VARIANTS]; VPAR = dict(VARIANTS)
BASE = {}


# ------------------------------------------------------------------------------------------------ two-leg exit engine
@njit(cache=True)
def xsim2(o, h, l, c, fi, d, ent0, et, sl0, tp0, tx, slip, be, beo, mode, k, q1, q2, stopmove, N, out):
    """out[i]: 0 pts (sum over legs q_i x (exit - entry_i) x d), 1 exit bar, 2 reason (0 stop, 1 target, 2 time, 3 BE/moved stop,
    -1 skipped (busy / bad spec), -2 unfilled limit (V4)), 3 qty filled, 4 leg-2 filled (0/1), 5 leg-1 fill bar, 6 leg-2 fill bar."""
    n = len(fi); busy = -1
    for i in range(n):
        f = fi[i]; s = d[i]
        out[i, 0] = np.nan; out[i, 1] = -1; out[i, 2] = -1; out[i, 3] = 0.0; out[i, 4] = 0.0; out[i, 5] = f; out[i, 6] = -1
        if f <= busy: continue
        raw = ent0[i]; sl = sl0[i]; tp = tp0[i]; last = tx[i]
        e1 = raw + (s * slip if et[i] == 0 else 0.0)
        qa = q1
        if mode == 4:                                       # all-limit: wait for a pullback fill
            r0 = abs(raw - sl)
            if r0 <= 0 or (raw - sl) * s <= 0 or (tp - raw) * s <= 0: continue
            px = raw - s * k * r0; q = f; got = False
            while q <= last:
                if s == 1:
                    if l[q] <= px - TICK: e1 = min(px, o[q]); got = True; break
                    if h[q] >= tp: break
                else:
                    if h[q] >= px + TICK: e1 = max(px, o[q]); got = True; break
                    if l[q] <= tp: break
                q += 1
            if not got:
                out[i, 2] = -2; continue
            f = q; qa = 1.0
        r0 = abs(e1 - sl)
        if r0 <= 0 or (e1 - sl) * s <= 0: continue
        tdist = (tp - e1) * s
        if tdist <= 0: continue
        pend = mode == 1 or mode == 2 or mode == 3 or mode == 5
        px2 = 0.0
        if mode == 1: px2 = e1 - s * k * r0
        elif mode == 2: px2 = e1 + s * k * r0
        elif mode == 3: px2 = e1 + s * k * tdist
        e2 = 0.0; f2 = 0; best = e1; moved = False; ex = np.nan; rs = 2; q = f
        while True:
            # (a) time-split leg: market at the open of bar f + N
            if pend and mode == 5 and q == f + N and q < last and (o[q] - sl) * s > 0:
                e2 = o[q] + s * slip; f2 = 1; pend = False; out[i, 6] = q
            # (b) better-price limit leg: fills before the stop check (the limit sits between entry and stop)
            if pend and mode == 1:
                if s == 1:
                    if l[q] <= px2 - TICK: e2 = min(px2, o[q]); f2 = 1; pend = False; out[i, 6] = q
                else:
                    if h[q] >= px2 + TICK: e2 = max(px2, o[q]); f2 = 1; pend = False; out[i, 6] = q
            # (c) stop
            if s == 1:
                if q > f and o[q] <= sl: ex = o[q] - slip; rs = 3 if moved else 0; break
                if l[q] <= sl: ex = sl - slip; rs = 3 if moved else 0; break
            else:
                if q > f and o[q] >= sl: ex = o[q] + slip; rs = 3 if moved else 0; break
                if h[q] >= sl: ex = sl + slip; rs = 3 if moved else 0; break
            # (d) worse-price stop-order leg (V2 / V3)
            if pend and (mode == 2 or mode == 3):
                if s == 1:
                    if h[q] >= px2: e2 = max(px2, o[q]) + slip; f2 = 1; pend = False; out[i, 6] = q
                else:
                    if l[q] <= px2: e2 = min(px2, o[q]) - slip; f2 = 1; pend = False; out[i, 6] = q
                if f2 == 1 and mode == 3 and stopmove == 1:
                    if (e1 - sl) * s > 0: sl = e1; moved = True
            # (e) target (never on the fill bar)
            if s == 1:
                if q > f and h[q] >= tp + TICK: ex = max(o[q], tp); rs = 1; break
            else:
                if q > f and l[q] <= tp - TICK: ex = min(o[q], tp); rs = 1; break
            if s == 1: best = max(best, h[q])
            else: best = min(best, l[q])
            if q >= last: ex = c[q] - s * slip; rs = 2; break
            fav = (best - e1) * s
            if be > 0 and fav >= be * r0:
                ns = e1 + s * beo * r0
                if (ns - sl) * s > 0: sl = ns; moved = True
            q += 1
        pts = qa * (ex - e1) * s; qty = qa
        if f2 == 1: pts += q2 * (ex - e2) * s; qty += q2
        out[i, 0] = pts; out[i, 1] = q; out[i, 2] = rs; out[i, 3] = qty; out[i, 4] = f2; out[i, 5] = f
        busy = q
    return n


# ------------------------------------------------------------------------------------------------ specs
def ev_dict(mod, p):
    """event dict of a mined ('ev') module, exactly as perturb_lib.ev_trades builds it."""
    G = P.G; D = G["D"]; sp = P.SPEC[mod]; q = dict(p)
    if mod == "CAM3":
        H, L, C = D.L[:, 0], D.L[:, 3], D.pdc; LH, LL = C + (H - L) * q["camf"], C - (H - L) * q["camf"]
        from core import ev_from_lists
        return ev_from_lists(G["lfade"](D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, LH, LL, S(q["w0"]), S(q["w1"]), q["sweep"], int(q["conf"]), q["tg"], q["R"], q["tf"], q["hold"], D.vwap).tolist())
    if mod == "RV11":
        q["cond"] = ("lo", q["lim"]); return G["gens"]["RVOL_DRIVE"](D, q)
    if mod == "ORFAIL":
        q["T"] = int(q["T"]); return G["gens"]["OR_FAIL"](D, q)
    if mod == "CPI09":
        q["T"] = int(q["T"]); ev = G["gens"]["G_DRIVE"](D, q)
        if len(ev["i"]):
            m = np.isin(D.date[ev["i"]], list(G["cpi"])); ev = {k: v[m] for k, v in ev.items()}
        return ev
    return G["gens"][sp["fam"]](D, q)


def build_specs():
    """{mod: [spec frames]} (VW13 = two frames VW13 / VW13b), already through keep_mask (minstop, ORB trigger)."""
    G = P.init(); D = G["D"]; out = {}
    for mod in P.MODS:
        sp = P.SPEC[mod]; p = sp["base"]
        if sp["kind"] == "ev":
            F = fills_core(D, ev_dict(mod, p), flat=955, maxday=sp["maxday"])
            E = P.mk(mod, F.fi, F.d, F.ent0, F.et, F.sl0, F.tp0, time_exit(D, F.fi.to_numpy(), F.hold.to_numpy(), 1555))
            out[mod] = [E]
        else:
            E = P.entries(mod, p); Es = E if isinstance(E, list) else [E]
            out[mod] = [e[P.keep_mask(e, e["mod"].iloc[0])].reset_index(drop=True) for e in Es]
    return out


def sim_spec(E, mod, var, slip_real=SLIP):
    """one spec frame -> (real, norm, info) frames: date, mod, tin, tout, d, u, fi, atr, w (+ qty, f2, rs in info)."""
    G = P.G; D = G["D"]; v = VPAR[var]; name = E["mod"].iloc[0] if len(E) else mod
    cols = ["date", "mod", "tin", "tout", "d", "u", "fi", "atr", "w"]
    if len(E) == 0:
        e = pd.DataFrame({c: [] for c in cols}); return e, e.copy(), pd.DataFrame()
    E = E.sort_values("fi", kind="stable").reset_index(drop=True)
    fi = E.fi.to_numpy(np.int64); d = E.d.to_numpy(np.int64); ent0 = E.ent0.to_numpy(float); et = E.et.to_numpy(np.int64)
    sl0 = E.sl0.to_numpy(float); tp0 = E.tp0.to_numpy(float); tx = E.tx.to_numpy(np.int64); date = E.date.to_numpy(); fomc = E.fomc.to_numpy(bool)
    xp = P.EXIT_P.get(mod, {}); be = float(xp.get("be", 0.0)); beo = float(xp.get("beo", 0.0))
    q1, q2 = (1.0, 0.0) if v["mode"] in (0, 4) else (0.5, 0.5)
    res = []; info = None
    for view in ("real", "norm"):
        out = np.zeros((len(fi), 7))
        xsim2(D.o, D.h, D.l, D.c, fi, d, ent0, et, sl0, tp0, tx, 0.0 if view == "norm" else slip_real, be, beo, int(v["mode"]), float(v["k"]), q1, q2, int(v["sm"]), int(v["N"]), out)
        ok = ~np.isnan(out[:, 0]) & (date >= 20100607) & (~fomc)
        f1 = out[:, 5].astype(np.int64); xi = out[:, 1].astype(np.int64); qty = out[:, 3]; a = D.atr[D.day[fi]]
        if view == "norm": u = np.where(a > 0, (out[:, 0] - NORM_COST * a * qty) / np.where(a > 0, a, 1) * 100, 0.0)
        else: u = out[:, 0] * D.pv - D.comm * qty
        T = pd.DataFrame(dict(date=date[ok], mod=name, tin=D.sm[f1[ok]], tout=D.sm[xi[ok]] + 1, d=d[ok], u=u[ok], fi=f1[ok], atr=a[ok], w=P.BASE_W.get(mod, 1.0)))
        res.append(T.reset_index(drop=True))
        if view == "real":
            info = pd.DataFrame(dict(date=date, atr=a, ok=ok, unfilled=out[:, 2] == -2, f2=out[:, 4] > 0, qty=qty, rs=out[:, 2]))
    return res[0], res[1], info


def sim_module(mod, var):
    Es = SPECS_CACHE[mod]; rs = [sim_spec(E, mod, var) for E in Es]
    tr = (pd.concat([r[0] for r in rs], ignore_index=True), pd.concat([r[1] for r in rs], ignore_index=True))
    return P.compact(tr), pd.concat([r[2] for r in rs], ignore_index=True)


SPECS_CACHE = {}


def init_worker():
    P.init(); P.PERIODS.clear(); P.PERIODS.update(PERIODS)
    SPECS_CACHE.update(pickle.load(open(SPECS, "rb"))); BASE.update(pickle.load(open(BASEP, "rb")))


def flat(prefix, M):
    return {f"{prefix}{per}_{k}": v for per, m in M.items() for k, v in m.items()}


def fill_stats(info):
    """second-leg fill rate / unfilled share per period (real view periods on ATR >= 150 days, norm periods on all days)."""
    out = {}
    for per, (lo, hi, view) in PERIODS.items():
        m = (info.date >= lo) & (info.date < hi)
        if view == "real": m &= info.atr >= P.MIN_ATR
        s = info[m]; n = int(m.sum())
        out[f"f_{per}_sig"] = n
        out[f"f_{per}_unfilled"] = round(100 * float(s.unfilled.mean()), 1) if n else np.nan
        ok = s[s.ok]; out[f"f_{per}_leg2"] = round(100 * float(ok.f2.mean()), 1) if len(ok) else np.nan
    return out


def run_cell(task):
    kind, mod, var = task; t0 = time.time(); row = dict(kind=kind, mod=mod, var=var)
    try:
        f = os.path.join(AV, f"{kind}_{mod}_{var}.pkl")
        if kind == "cell":
            tr, info = sim_module(mod, var); parts = dict(BASE); parts[mod] = tr
            row.update(flat("m_", P.module_metrics(tr))); row.update(fill_stats(info)); row.update(flat("p_", P.port_metrics(parts)))
            pickle.dump(tr, open(f, "wb"))
        else:                                                   # global: kind = all / struct / clock
            scope = {"all": P.MODS, "struct": STRUCT, "clock": CLOCK}[kind]; parts = dict(BASE)
            for m in scope: parts[m] = pickle.load(open(os.path.join(AV, f"cell_{m}_{var}.pkl"), "rb"))
            row.update(flat("p_", P.port_metrics(parts)))
    except Exception as e:
        import traceback; row["err"] = repr(e)[:300]; traceback.print_exc()
    row["secs"] = round(time.time() - t0, 2)
    return row


# ------------------------------------------------------------------------------------------------ build / run / report
def build():
    t0 = time.time(); sp = build_specs(); pickle.dump(sp, open(SPECS, "wb")); SPECS_CACHE.update(sp)
    print("specs", {m: sum(len(e) for e in v) for m, v in sp.items()}, round(time.time() - t0), "s", flush=True)
    ref = pickle.load(open(os.path.join(SCR, "base_parts.pkl"), "rb")); parts = {}; bad = {}
    for mod in P.MODS:
        tr, _ = sim_module(mod, "base"); parts[mod] = tr
        for vi, view in enumerate(("real", "norm")):
            a = tr[vi].sort_values(["fi", "mod"]).reset_index(drop=True); b = ref[mod][vi].sort_values(["fi", "mod"]).reset_index(drop=True)
            if len(a) != len(b) or not np.array_equal(a.fi.to_numpy(), b.fi.to_numpy()):
                bad[(mod, view)] = f"rows {len(a)} vs {len(b)}"; continue
            du = np.abs(a.u.to_numpy() - b.u.to_numpy()); dt = np.abs(a.tout.to_numpy() - b.tout.to_numpy())
            if du.max() > 1e-6 or dt.max() > 0: bad[(mod, view)] = f"|du| max {du.max():.4f} n>1e-6 {int((du > 1e-6).sum())} dtout {int((dt > 0).sum())}"
    print("reproduction vs base_parts.pkl:", "EXACT for every module and view" if not bad else bad, flush=True)
    pickle.dump(parts, open(BASEP, "wb"))
    P.PERIODS.clear(); P.PERIODS.update(PERIODS)
    print("base portfolio", json.dumps(P.port_metrics(parts)), flush=True)
    json.dump(dict(repro_bad={f"{m}/{v}": s for (m, v), s in bad.items()}, base=P.port_metrics(parts)), open(os.path.join(AV, "build.json"), "w"), indent=1)


def run():
    from multiprocessing import Pool
    out = os.path.join(HERE, "avg_entry_cells.csv"); rows = []; done = set()
    if os.path.exists(out):
        R0 = pd.read_csv(out); rows = R0.to_dict("records"); done = set(zip(R0.kind, R0["mod"], R0["var"]))
    cells = [("cell", m, v) for m in P.MODS for v in VNAMES if ("cell", m, v) not in done]
    glob = [(k, "ALL", v) for v in VNAMES if v != "base" for k in ("all", "struct", "clock") if (k, "ALL", v) not in done]
    print("cells", len(cells), "global", len(glob), "done", len(done), flush=True); t0 = time.time()
    with Pool(int(os.environ.get("AVG_PROCS", "2")), initializer=init_worker) as pool:
        for stage in (cells, glob):
            for k, row in enumerate(pool.imap_unordered(run_cell, stage, chunksize=2)):
                rows.append(row)
                if k % 25 == 0:
                    pd.DataFrame(rows).to_csv(out, index=False); print(k, len(stage), round(time.time() - t0), "s", row["kind"], row["mod"], row["var"], row.get("err", ""), flush=True)
            pd.DataFrame(rows).to_csv(out, index=False)
    R = pd.DataFrame(rows); R.to_csv(out, index=False)
    print("done", len(R), round(time.time() - t0), "s; errors", int(R["err"].notna().sum()) if "err" in R else 0, flush=True)


def passes(r, b):
    """acceptance on a cell row r vs base row b (portfolio metrics)."""
    ch = all(r[f"p_{p}_sharpe"] > b[f"p_{p}_sharpe"] for p in CHOOSE)
    t2 = (r["p_T2_sharpe"] >= b["p_T2_sharpe"]) and (r["p_T2_pf"] >= b["p_T2_pf"]) and (r["p_T2_wr"] >= b["p_T2_wr"]) and (r["p_T2_maxdd"] <= 1.05 * b["p_T2_maxdd"])
    return ch, t2


def report():
    R = pd.read_csv(os.path.join(HERE, "avg_entry_cells.csv")); C = R[R.kind == "cell"].copy()
    b = C[C["var"] == "base"].iloc[0]                             # portfolio base = identical in every base row
    pm = [f"p_{p}_{k}" for p in PERIODS for k in ("sharpe", "pf", "wr", "maxdd", "net", "worst_month", "n")]
    base_port = {c: float(b[c]) for c in pm}
    V = C[C["var"] != "base"].copy()
    for p in list(PERIODS): V[f"d_{p}_sharpe"] = V[f"p_{p}_sharpe"] - b[f"p_{p}_sharpe"]
    V["choose_ok"] = [passes(r, b)[0] for _, r in V.iterrows()]; V["t2_ok"] = [passes(r, b)[1] for _, r in V.iterrows()]
    V["pass"] = V.choose_ok & V.t2_ok
    V["t1_up"] = V.d_T1_sharpe > 0; V["t2_up"] = V.d_T2_sharpe > 0
    V["t1n_up"] = V.d_T1n_sharpe > 0; V["ab_up"] = (V.d_A_sharpe > 0) & (V.d_B_sharpe > 0)
    br = dict(cells=int(len(V)), P_T2_up=round(float(V.t2_up.mean()), 3),
              P_T1_up=round(float(V.t1_up.mean()), 3), P_T2_up_given_T1_up=round(float(V[V.t1_up].t2_up.mean()), 3) if V.t1_up.any() else None,
              n_T1_up=int(V.t1_up.sum()), n_choose_ok=int(V.choose_ok.sum()),
              P_T2_up_given_choose_ok=round(float(V[V.choose_ok].t2_up.mean()), 3) if V.choose_ok.any() else None,
              P_T2_up_given_T1_and_T1n_up=round(float(V[V.t1_up & V.t1n_up].t2_up.mean()), 3) if (V.t1_up & V.t1n_up).any() else None,
              n_T1_and_T1n_up=int((V.t1_up & V.t1n_up).sum()), n_pass=int(V["pass"].sum()),
              P_T2_full_check_given_choose_ok=round(float(V[V.choose_ok].t2_ok.mean()), 3) if V.choose_ok.any() else None,
              P_T2_full_check_overall=round(float(V.t2_ok.mean()), 3))
    # module tables: standalone + portfolio deltas
    mod_tab = {}
    for m in P.MODS:
        rows = []
        for _, r in C[C["mod"] == m].sort_values("var", key=lambda s: s.map({v: i for i, v in enumerate(VNAMES)})).iterrows():
            rows.append({k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items() if k not in ("kind", "mod", "secs")})
        mod_tab[m] = rows
    G = R[R.kind != "cell"].copy()
    for p in list(PERIODS): G[f"d_{p}_sharpe"] = G[f"p_{p}_sharpe"] - b[f"p_{p}_sharpe"]
    G["choose_ok"] = [passes(r, b)[0] for _, r in G.iterrows()]; G["t2_ok"] = [passes(r, b)[1] for _, r in G.iterrows()]; G["pass"] = G.choose_ok & G.t2_ok
    # best variant on the choose set: most modules whose portfolio Sharpe rises in all 4 choose periods, tie-break mean T1 dSharpe
    per_var = V.groupby("var").agg(n_choose_ok=("choose_ok", "sum"), n_t1_up=("t1_up", "sum"), mean_dT1=("d_T1_sharpe", "mean"), mean_dT1n=("d_T1n_sharpe", "mean"),
                                   mean_dA=("d_A_sharpe", "mean"), mean_dB=("d_B_sharpe", "mean"), mean_dT2=("d_T2_sharpe", "mean"), n_t2_up=("t2_up", "sum"), n_pass=("pass", "sum"))
    per_var = per_var.sort_values(["n_choose_ok", "mean_dT1"], ascending=False)
    survivors = V[V["pass"]][["mod", "var"] + [f"d_{p}_sharpe" for p in PERIODS] + [f"p_{p}_{k}" for p in ("T1", "T2") for k in ("pf", "wr", "maxdd", "net")] + ["f_T1_leg2", "f_T2_leg2"]]
    # standalone effects per variant (module metrics vs the module's own base), structure vs clock
    bm = C[C["var"] == "base"].set_index("mod"); st_rows = []
    for (var, grp), g in V.assign(grp=V["mod"].map(lambda m: "struct" if m in STRUCT else "clock")).groupby(["var", "grp"]):
        bb = bm.loc[g["mod"]]; r = dict(var=var, grp=grp, n_mod=len(g))
        for p in ("T1", "T2"):
            r[f"{p}_dWR"] = round(float((g[f"m_{p}_wr"].to_numpy() - bb[f"m_{p}_wr"].to_numpy()).mean()), 2)
            r[f"{p}_dPF"] = round(float((g[f"m_{p}_pf"].to_numpy() - bb[f"m_{p}_pf"].to_numpy()).mean()), 3)
            r[f"{p}_net_pct"] = round(100 * float(g[f"m_{p}_net"].sum() / bb[f"m_{p}_net"].sum() - 1), 1)
            r[f"{p}_n_pct"] = round(100 * float(g[f"m_{p}_n"].sum() / bb[f"m_{p}_n"].sum() - 1), 1)
        v = VPAR[var]; r["avg_size_T2"] = round(float((1 - g.f_T2_unfilled / 100).mean()), 2) if v["mode"] == 4 else round(float((0.5 + 0.5 * g.f_T2_leg2 / 100).mean()), 2)
        st_rows.append(r)
    st_tab = pd.DataFrame(st_rows)
    # integer-lot view: the split variants need 2 lots per module; $ and DD scale linearly with size
    lots = []
    def lot_rows(label, net1, dd1, netv, ddv):
        x2 = lambda v: None if v is None else 2 * v; x4 = lambda v: None if v is None else 4 * v
        return dict(cell=label, base_1lot_net=net1, base_1lot_maxdd=dd1, base_2lot_net=x2(net1), base_2lot_maxdd=x2(dd1),
                    split_2lot_net=x2(netv), split_2lot_maxdd=x2(ddv), split_4lot_net=x4(netv), split_4lot_maxdd=x4(ddv), base_4lot_net=x4(net1))
    for _, r in V[V["pass"]].iterrows():
        bb = bm.loc[r["mod"]]
        lots.append(lot_rows(f"{r['mod']} {r['var']} (module alone, T2)", float(bb.m_T2_net), None, float(r.m_T2_net), None))
        lots.append(lot_rows(f"{r['mod']} {r['var']} (portfolio, T2)", float(b.p_T2_net), float(b.p_T2_maxdd), float(r.p_T2_net), float(r.p_T2_maxdd)))
    for _, r in G.iterrows():
        if r["var"] in ("V1_k0.25", "V5_N5") and r.kind == "all":
            lots.append(lot_rows(f"ALL {r['var']} (portfolio, T2)", float(b.p_T2_net), float(b.p_T2_maxdd), float(r.p_T2_net), float(r.p_T2_maxdd)))
            lots.append(lot_rows(f"ALL {r['var']} (portfolio, T1)", float(b.p_T1_net), float(b.p_T1_maxdd), float(r.p_T1_net), float(r.p_T1_maxdd)))
    out = dict(pre_registration=__doc__, base_portfolio=base_port, base_rates=br, per_variant=per_var.reset_index().to_dict("records"),
               standalone_by_group=st_tab.to_dict("records"), lots=lots,
               survivors=survivors.to_dict("records"), choose_ok_cells=V[V.choose_ok][["mod", "var"] + [f"d_{p}_sharpe" for p in PERIODS] + ["t2_ok"]].to_dict("records"),
               global_cells=G[["kind", "var"] + [f"p_{p}_{k}" for p in PERIODS for k in ("sharpe", "pf", "wr", "maxdd", "net", "worst_month")] + ["choose_ok", "t2_ok", "pass"]].to_dict("records"),
               modules=mod_tab, variants=VNAMES, periods={k: list(v) for k, v in PERIODS.items()})
    json.dump(out, open(os.path.join(HERE, "avg_entry.json"), "w"), indent=1, default=lambda x: None if (isinstance(x, float) and np.isnan(x)) else (x.item() if hasattr(x, "item") else str(x)))
    write_md(out, V, G, b, C)
    print(json.dumps(br, indent=1)); print(per_var.round(3).to_string()); print("survivors:", len(survivors))
    return out


def fmt(x, nd=2):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else (f"{x:,.{nd}f}" if isinstance(x, (float, np.floating)) else str(x))


def write_md(out, V, G, b, C):
    L = []; a = L.append
    a("# Entry-averaging lab (avg_entry.py) — 2027 default, real Databento NQ 2010-2026\n")
    a("Question: does averaging into entries (several entries at different prices per module) help?  Pre-registered; protocol fixed before looking at any result.\n")
    a("## Pre-registration\n"); a("```\n" + out["pre_registration"].strip() + "\n```\n")
    a("Interpretation note: the request's V2 'average down' reads 'entry + k x stop against the trade'. For a long, entry + k x stop is a WORSE price (above the market), "
      "so it can only be a stop order that fills once the trade is already k x stop in profit; its leg-2 risk is (1 + k) r0, which is why the request says 'total risk rises'. "
      "A true average-down (a limit between the entry and the stop) is V1. V3 differs from V2 by its distance unit (target instead of stop) and the stop-move option.\n")
    bp = out["base_portfolio"]
    a("## Base portfolio (unchanged 2027 default, 1 base unit per module, boosts x2 / x4 as coded)\n")
    a("| period | n | Sharpe | PF | WR % | maxDD | net | worst month |\n|---|---|---|---|---|---|---|---|")
    for p in PERIODS:
        a(f"| {p} | {int(bp[f'p_{p}_n'])} | {fmt(bp[f'p_{p}_sharpe'],3)} | {fmt(bp[f'p_{p}_pf'],3)} | {fmt(bp[f'p_{p}_wr'],1)} | {fmt(bp[f'p_{p}_maxdd'],0)} | {fmt(bp[f'p_{p}_net'],0)} | {fmt(bp[f'p_{p}_worst_month'],0)} |")
    a("\nT1 / T2 in $ per MNQ base unit (days with ATR >= 150, FOMC skipped); A / B / T1n in % of daily ATR units, cost 0.345 % ATR, no slippage. "
      "T1 real has few 2019 days (MinATR 150 guard), which is why the cost-normalised T1n (2019 in full) is a choose period too.\n")
    br = out["base_rates"]
    a("## Base rates (selection-bias check over all module x variant cells)\n")
    a(f"- cells: {br['cells']} ({len(P.MODS)} modules x {len(VNAMES) - 1} variants)")
    a(f"- P(T2 portfolio Sharpe up) overall: **{br['P_T2_up']:.0%}**; P(T1 up): {br['P_T1_up']:.0%} ({br['n_T1_up']} cells)")
    a(f"- P(T2 up | T1 real up): **{fmt(br['P_T2_up_given_T1_up'],3)}**; P(T2 up | T1 and T1n up): {fmt(br['P_T2_up_given_T1_and_T1n_up'],3)} ({br['n_T1_and_T1n_up']} cells)")
    a(f"- cells passing the whole choose set (T1, T1n, A, B all up): {br['n_choose_ok']}; of those, T2 Sharpe up: {fmt(br['P_T2_up_given_choose_ok'],3)}, full T2 check: {fmt(br['P_T2_full_check_given_choose_ok'],3)} (overall full-T2-check rate {br['P_T2_full_check_overall']:.0%})")
    a(f"- survivors (choose set + full T2 check): **{br['n_pass']}**\n")
    a("## Per-variant summary (portfolio Sharpe deltas vs base, mean over the 23 modules; n = modules)\n")
    a("| variant | n choose-ok | n T1 up | mean dT1 | mean dT1n | mean dA | mean dB | mean dT2 | n T2 up | n pass |\n|---|---|---|---|---|---|---|---|---|---|")
    for r in out["per_variant"]:
        a(f"| {r['var']} | {r['n_choose_ok']} | {r['n_t1_up']} | {r['mean_dT1']:+.3f} | {r['mean_dT1n']:+.3f} | {r['mean_dA']:+.3f} | {r['mean_dB']:+.3f} | {r['mean_dT2']:+.3f} | {r['n_t2_up']} | {r['n_pass']} |")
    a("\n## Global cells (one variant on every module of a scope; structure = " + ", ".join(STRUCT) + "; clock = the other " + str(len(CLOCK)) + ")\n")
    a("| scope | variant | dSharpe T1 | T1n | A | B | T2 | T2 PF | T2 WR | T2 maxDD | T2 net | choose ok | T2 ok |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in G.sort_values(["kind", "var"]).iterrows():
        a(f"| {r.kind} | {r['var']} | {r.d_T1_sharpe:+.3f} | {r.d_T1n_sharpe:+.3f} | {r.d_A_sharpe:+.3f} | {r.d_B_sharpe:+.3f} | {r.d_T2_sharpe:+.3f} | {r.p_T2_pf:.3f} | {r.p_T2_wr:.1f} | {r.p_T2_maxdd:,.0f} | {r.p_T2_net:,.0f} | {'yes' if r.choose_ok else 'no'} | {'yes' if r.t2_ok else 'no'} |")
    a(f"\nBase: T1 Sharpe {bp['p_T1_sharpe']:.3f}, T2 Sharpe {bp['p_T2_sharpe']:.3f}, T2 PF {bp['p_T2_pf']:.3f}, T2 WR {bp['p_T2_wr']:.1f}, T2 maxDD {bp['p_T2_maxdd']:,.0f}, T2 net {bp['p_T2_net']:,.0f}.\n")
    a("## Standalone module effects per variant (mean over modules of the group; vs each module's own base)\n")
    a("avg size = mean filled size per trade in T2 (base = 1.00); net % / trades % = change of the group's summed net $ / trade count; dWR / dPF = mean change in points.\n")
    a("| variant | group | n mod | T1 dWR | T1 dPF | T1 net % | T2 dWR | T2 dPF | T2 net % | T2 trades % | avg size T2 |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for r in out["standalone_by_group"]:
        a(f"| {r['var']} | {r['grp']} | {r['n_mod']} | {r['T1_dWR']:+.1f} | {r['T1_dPF']:+.3f} | {r['T1_net_pct']:+.1f} | {r['T2_dWR']:+.1f} | {r['T2_dPF']:+.3f} | {r['T2_net_pct']:+.1f} | {r['T2_n_pct']:+.1f} | {r['avg_size_T2']:.2f} |")
    a("\n## Integer-lot view (NQMaster trades whole MNQ contracts; a split needs 2 lots per module)\n")
    a("Ratio metrics (Sharpe, PF, WR) do not depend on size; $ and maxDD scale linearly. 'split 2-lot' = 1 + 1 contracts, 'split 4-lot' = 2 + 2.\n")
    a("| cell | base 1 lot net | base 1 lot maxDD | base 2 lots net | base 2 lots maxDD | split 2 lots net | split 2 lots maxDD | split 4 lots net | split 4 lots maxDD |\n|---|---|---|---|---|---|---|---|---|")
    for r in out["lots"]:
        a(f"| {r['cell']} | {fmt(r['base_1lot_net'],0)} | {fmt(r['base_1lot_maxdd'],0)} | {fmt(r['base_2lot_net'],0)} | {fmt(r['base_2lot_maxdd'],0)} | {fmt(r['split_2lot_net'],0)} | {fmt(r['split_2lot_maxdd'],0)} | {fmt(r['split_4lot_net'],0)} | {fmt(r['split_4lot_maxdd'],0)} |")
    a("")
    a("## Cells that pass the choose set (T1, T1n, A, B portfolio Sharpe all up) and their T2 check\n")
    ch = out["choose_ok_cells"]
    if not ch: a("None.\n")
    else:
        a("| module | variant | dT1 | dT1n | dA | dB | dT2 | T2 full check |\n|---|---|---|---|---|---|---|---|")
        for r in ch: a(f"| {r['mod']} | {r['var']} | {r['d_T1_sharpe']:+.3f} | {r['d_T1n_sharpe']:+.3f} | {r['d_A_sharpe']:+.3f} | {r['d_B_sharpe']:+.3f} | {r['d_T2_sharpe']:+.3f} | {'yes' if r['t2_ok'] else 'no'} |")
        a("")
    a("## Survivors\n")
    sv = out["survivors"]
    if not sv: a("None.\n")
    else:
        for r in sv: a(f"- {r['mod']} {r['var']}: dSharpe T1 {r['d_T1_sharpe']:+.3f} T1n {r['d_T1n_sharpe']:+.3f} A {r['d_A_sharpe']:+.3f} B {r['d_B_sharpe']:+.3f} T2 {r['d_T2_sharpe']:+.3f}; T2 PF {r['p_T2_pf']:.3f} WR {r['p_T2_wr']:.1f} maxDD {r['p_T2_maxdd']:,.0f} net {r['p_T2_net']:,.0f}; leg-2 fill T1/T2 {fmt(r['f_T1_leg2'],0)}/{fmt(r['f_T2_leg2'],0)} %")
        a("")
    a("## Per-module tables (standalone module metrics, unweighted; portfolio Sharpe delta; fill rates)\n")
    a("Columns: n / WR / PF / net of the module alone in T1 (real $) and T2 (real $), A and B (norm); leg2 = share of trades where the second leg filled (V4: unfilled = signals whose limit never filled); dSh = portfolio Sharpe delta vs base.\n")
    for m in P.MODS:
        rows = out["modules"][m]; bb = [r for r in rows if r["var"] == "base"][0]
        a(f"### {m} ({'structure' if m in STRUCT else 'clock'})\n")
        a("| variant | T1 n | T1 WR | T1 PF | T1 net | T2 n | T2 WR | T2 PF | T2 net | A PF | B PF | leg2 T1/T2 % | unfilled T1/T2 % | dSh T1 | dSh T1n | dSh A | dSh B | dSh T2 |")
        a("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            d = lambda p: (r[f"p_{p}_sharpe"] - bb[f"p_{p}_sharpe"]) if r["var"] != "base" else 0.0
            a(f"| {r['var']} | {fmt(r['m_T1_n'])} | {fmt(r['m_T1_wr'],1)} | {fmt(r['m_T1_pf'],2)} | {fmt(r['m_T1_net'],0)} | {fmt(r['m_T2_n'])} | {fmt(r['m_T2_wr'],1)} | {fmt(r['m_T2_pf'],2)} | {fmt(r['m_T2_net'],0)} | {fmt(r['m_A_pf'],2)} | {fmt(r['m_B_pf'],2)} | "
              f"{fmt(r['f_T1_leg2'],0)}/{fmt(r['f_T2_leg2'],0)} | {fmt(r['f_T1_unfilled'],0)}/{fmt(r['f_T2_unfilled'],0)} | {d('T1'):+.3f} | {d('T1n'):+.3f} | {d('A'):+.3f} | {d('B'):+.3f} | {d('T2'):+.3f} |")
        a("")
    L.insert(L.index("## Base rates (selection-bias check over all module x variant cells)\n"), verdict(out, V, G, b))
    open(os.path.join(HERE, "avg_entry_report.md"), "w").write("\n".join(L))


def verdict(out, V, G, b):
    br = out["base_rates"]; sv = out["survivors"]; bp = out["base_portfolio"]
    T = ["## Verdict (honest)\n"]
    T.append(f"**Averaging into entries does not help the 2027 default.** {br['cells']} module x variant cells and {len(G)} global cells were run; "
             f"{br['n_choose_ok']} cells raise the portfolio Sharpe in all four choose periods (T1 real, T1 cost-normalised, 2010-14, 2015-19) and "
             f"{br['n_pass']} of them also passes the full T2 check.")
    for r in sv:
        T.append(f"- The formal survivor **{r['mod']} {r['var']}** is a noise-level cell: portfolio Sharpe deltas T1 {r['d_T1_sharpe']:+.3f}, T1n {r['d_T1n_sharpe']:+.3f}, "
                 f"A {r['d_A_sharpe']:+.3f}, B {r['d_B_sharpe']:+.3f}, T2 {r['d_T2_sharpe']:+.3f} (it passes 'T2 not lower' by equality at 3 decimals); "
                 f"T2 net ${r['p_T2_net']:,.0f} vs base ${bp['p_T2_net']:,.0f} and T1 net ${r['p_T1_net']:,.0f} vs ${bp['p_T1_net']:,.0f} (both LOWER), "
                 f"T2 maxDD {r['p_T2_maxdd']:,.0f} vs {bp['p_T2_maxdd']:,.0f}. It is not worth two lots per MSEQ trade and a second order; NOT recommended for NQMaster.")
    T.append(f"- Selection bias: P(T2 Sharpe up | T1 up) = {fmt(br['P_T2_up_given_T1_up'],2)} vs P(T2 up) overall = {br['P_T2_up']:.2f}; choosing on T1 has no predictive value here "
             f"(among the {br['n_choose_ok']} choose-set passes, T2 Sharpe rises in {fmt(br['P_T2_up_given_choose_ok'],2)} and the full T2 check holds in {fmt(br['P_T2_full_check_given_choose_ok'],2)}).")
    T.append("- Mechanism (see the standalone tables): V1 (limit for the second half at a better price) raises WR by 1-3 points but the second leg fills on 35-70 % of trades and "
             "fills more often on losers (the pullback that fills the limit is the start of the stop-out) -> net $ down 10-45 % with the same risk per trade; V2 / V3 (adding on a "
             "stop order once in profit) lowers WR 1-2 points (clock) / 3-5 (structure) and net $ 16-55 %; moving the stop to the original entry on a pyramid (V3 sm1) is catastrophic "
             "(WR -16..-39 points: the add turns a normal winner into a scratch); V4 (all-limit) loses 25-58 % of the signals (adverse selection, worse on clock modules) and "
             "is the worst family on 2010-19; V5 (half now, half 5-15 min later) is the closest to neutral in ratios (fill 80-95 %, WR +-1) but still loses 5-20 % of net $ (second slippage, later entry).")
    T.append("- Global: no scope x variant passes the choose set. 'All modules V1 k0.25' has the best T2 ratios (Sharpe 3.68 vs 3.60, PF 1.47 vs 1.44, WR 66.6 vs 64.5, maxDD 4.1k vs 4.7k) "
             "but net $ -12 % with 0.82-0.86 average size, and it FAILS 2010-14 / 2015-19 (Sharpe 0.25 vs 0.62, 1.03 vs 1.31): the ratio gain is a 2019-26 artefact of smaller size on "
             "the runaway winners, not an entry edge.")
    T.append("- Integer lots: every split needs at least 2 MNQ per module (2 x the account exposure of the current 1-lot setup) and earns less than the plain 2-lot base; the 1-contract "
             "prop plan cannot use any of these variants. Earlier partial results (gerard.py scale-in on the 5-min ORB, Tradefather scale-in, runners, limit entries on clock modules) are confirmed system-wide.")
    T.append("- NQMaster implementation: NONE recommended. For the record, the formal survivor would be: MSEQ EnterLong(1 lot) at the signal as today, then 15 one-minute bars later, "
             "if the position is still open (not stopped, not at target), EnterLong(1 lot) at market (second signal name 'MSEQ-2'), both lots sharing the same stop / target prices "
             "(SetStopLoss / SetProfitTarget per signal name at the ORIGINAL prices, not re-centred on the average); the time exit flattens both. Expected effect: $0 +- noise.")
    T.append("- Do not re-run with other k / N: V1 k .25/.5/.75, V2 k .25/.5, V3 k .25/.5 x stop-move, V4 k .25/.5, V5 N 5/15 cover the plateau and every family degrades monotonically "
             "with k; a new ingredient (e.g. order-flow-conditioned adds) would be needed, and order-flow filters already failed out of sample (2026-10-09).\n")
    return "\n".join(T)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "build": build()
    elif mode == "run": run()
    elif mode == "report": report()
