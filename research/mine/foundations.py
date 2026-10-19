"""foundations.py (2026-10-19): audit of the GLOBAL foundations shared by every module of the 2027 NQMaster default
(Ultra + SO04 / RV11 / ORFAIL / CAM3 = nt_compare --set ultra_d4), on real Databento NQ 2010-06..2026-10.
The per-module parameters were perturbed in perturb_lab.py; here the things every module inherits are varied one at a time:
  F1 daily trend filter   base: sign(prior complete RTH close - SMA20 of RTH closes)
                          alternatives: SMA 10/15/25/30/50, EMA20, close vs close N days ago (5/10/20), SMA20 & SMA50 agreement,
                          and the control 'none' (= union of the set built with trend = +1 everywhere and with trend = -1 everywhere:
                          every trend-filtered module trades both directions; ORB breaks either side with the pullback condition in
                          the breakout direction).
  F2 daily ATR            base: Wilder ATR(14) of the RTH-session true range (prior close = prior RTH close), shifted one day
                          alternatives: windows 7/10/20/30; full Globex-session range instead of the RTH range (14);
                          MinATR guard 150 -> 100/200/250 (real view only; no rebuild, assembly filter).
  F3 ORB pullback-day     base: prior-day move with the trend < 0.44 ATR; alternatives 0.30/0.35/0.50/0.60/none (ORB60, ORB90 and the
                          MSEQS gate rebuilt).
  F4 flat time            base 15:55 for the day modules; alternatives 15:45/15:50/15:58/16:00 (first bar at or after 16:00, i.e. the
                          cash close) / 16:14 (last bar before the 16:15 Globex halt). LON keeps its own 09:30 exit.
Implementation: perturb_lib's rebuild pipeline (reproduces the committed set row for row) with the foundations patched at the exact
points where the original signal code computes them: ict.day_levels (core.Data, tmom, ict_fix, london), crt.ATRD/TREND, wr60 up20,
nt_v2_replica.daily_stats (ORB direction, cap and pullback PR), wrq_lib.time_exit / fills_core / core.run_events (flat), MIN_ATR.
`python3 foundations.py check` asserts that the default configuration reproduces every original array exactly.
Views: A 2010-14 / B 2015-19 cost-normalised (0.345 % ATR, P&L in % ATR), T1 2020-23 / T2 2024-26 real $ per MNQ ($1.90 + 1 tick).

PRE-REGISTERED ACCEPTANCE (written before any result was looked at):
  decide on T1 + A + B: an alternative is a candidate only if its portfolio Sharpe is higher than the base in ALL three of A, B, T1;
  confirm on T2: T2 Sharpe not lower, T2 PF not lower, T2 WR not lower, T2 maxDD not higher by more than 5 %, trade count (T1 and T2)
  not lower by more than 5 %;
  plateau: the adjacent levels of the candidate (previous / next value of the same knob) must not be worse than the base by more than
  0.10 Sharpe in T1, and at least one adjacent level must also beat the base in T1 (a candidate that only wins at one isolated value is
  a spike and is rejected).
  Plateau verdict for the CURRENT choice of each knob: 'plateau' if every adjacent level is within 0.15 Sharpe (T1) and 0.15 (T2) of
  the base and within 0.03 PF; 'edge' if the base is at one end of the tested range and only the inner neighbour qualifies;
  'spike' if an adjacent level loses more than 0.15 Sharpe in T1 or T2.
Run:  cd research/mine && python3 foundations.py check            (reproduction asserts)
      python3 foundations.py cell <name>                            (one configuration -> <scratch>/found/<name>.pkl + .json)
      python3 foundations.py run                                    (every cell, 2 processes, in the background via xargs)
      python3 foundations.py report                                 (foundations.json + foundations_report.md)"""
import os, sys, json, time, pickle, importlib, subprocess, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.dirname(HERE)
for p in (HERE, RES):
    if p not in sys.path: sys.path.insert(0, p)
SCR = os.environ.get("FOUND_SCRATCH", "/tmp/claude-0/-home-user-nqmaster-research/176a42ca-c215-52e2-84dc-57e214e477d4/scratchpad")
OUT = os.path.join(SCR, "found"); os.makedirs(OUT, exist_ok=True)

DEFAULT = dict(trend=("sma", 20), atr=(14, "rth"), min_atr=150.0, pb=0.44, flat=1555)
CFG = dict(DEFAULT)
CELLS = {
    "base": {},
    "trend_sma10": dict(trend=("sma", 10)), "trend_sma15": dict(trend=("sma", 15)), "trend_sma25": dict(trend=("sma", 25)),
    "trend_sma30": dict(trend=("sma", 30)), "trend_sma50": dict(trend=("sma", 50)),
    "trend_ema20": dict(trend=("ema", 20)),
    "trend_mom5": dict(trend=("mom", 5)), "trend_mom10": dict(trend=("mom", 10)), "trend_mom20": dict(trend=("mom", 20)),
    "trend_both20_50": dict(trend=("both", 20, 50)),
    "trend_up": dict(trend=("const", 1)), "trend_dn": dict(trend=("const", -1)),
    "atr_7": dict(atr=(7, "rth")), "atr_10": dict(atr=(10, "rth")), "atr_20": dict(atr=(20, "rth")), "atr_30": dict(atr=(30, "rth")),
    "atr_full14": dict(atr=(14, "full")),
    "flat_1545": dict(flat=1545), "flat_1550": dict(flat=1550), "flat_1558": dict(flat=1558), "flat_1600": dict(flat=1600), "flat_1614": dict(flat=1614),
}
PB_LEVELS = [0.30, 0.35, 0.44, 0.50, 0.60, 99.0]
MINATR_LEVELS = [100.0, 150.0, 200.0, 250.0]
PERS = ["A", "B", "T1", "T2"]
_ORIG = {}


# ------------------------------------------------------------------------------------------------ foundations
def daily_table(d):
    """per Globex session (dayid): RTH h / l / last close, full-session h / l; NaN where the session has no RTH bars."""
    om, day = np.asarray(d["om"]), np.asarray(d["dayid"]); nd = int(day.max()) + 1
    df = pd.DataFrame(dict(day=day, om=om, h=np.asarray(d["h"]), l=np.asarray(d["l"]), c=np.asarray(d["c"])))
    rth = df[(df.om >= 570) & (df.om < 960)].groupby("day").agg(h=("h", "max"), l=("l", "min"), c=("c", "last")).reindex(range(nd))
    full = df.groupby("day").agg(fh=("h", "max"), fl=("l", "min")).reindex(range(nd))
    return rth.join(full)


def true_range(tab, first_plain=False, pc_ffill=False):
    n, rng = CFG["atr"]; pc = (tab.c.ffill() if pc_ffill else tab.c).shift(1)
    if rng == "rth": h, l = tab.h, tab.l
    else: h, l = tab.fh.where(tab.c.notna()), tab.fl.where(tab.c.notna())
    tr = np.maximum(h - l, np.maximum((h - pc).abs(), (l - pc).abs()))
    if first_plain: tr = tr.where(pc.notna(), h - l)
    return tr


def trend_series(c):
    """trend per row of a daily close series c (prior close vs reference), as float with NaN -> 0 later."""
    spec = CFG["trend"]; kind = spec[0]; pc = c.shift(1)
    if kind == "sma": ref = c.rolling(spec[1], min_periods=spec[1]).mean().shift(1); t = np.sign(pc - ref)
    elif kind == "ema": ref = c.ewm(span=spec[1], adjust=False, ignore_na=True).mean().shift(1); t = np.sign(pc - ref)
    elif kind == "mom": ref = c.shift(1 + spec[1]); t = np.sign(pc - ref)
    elif kind == "both":
        t1 = np.sign(pc - c.rolling(spec[1], min_periods=spec[1]).mean().shift(1)); t2 = np.sign(pc - c.rolling(spec[2], min_periods=spec[2]).mean().shift(1))
        t = t1.where(t1 == t2, 0.0)
    elif kind == "const": t = pd.Series(float(spec[1]), index=c.index)
    else: raise ValueError(spec)
    return t.fillna(0).astype(np.int64)


def ict_style(tab):
    """= ict.day_levels convention: series indexed by dayid WITH NaN holes (sessions without RTH)."""
    n = CFG["atr"][0]; tr = true_range(tab)
    atr = tr.ewm(alpha=1 / n, adjust=False, ignore_na=True).mean().shift(1).fillna(0).to_numpy()
    return atr, trend_series(tab.c).to_numpy()


def compact_style(tab):
    """= crt.daily_trend_atr / wr60.daily_info convention: computed on RTH days only, then reindexed to every dayid (0 where missing)."""
    n = CFG["atr"][0]; ok = tab.c.notna(); t2 = tab[ok]
    tr = true_range(t2)
    atr = tr.ewm(alpha=1 / n, adjust=False).mean().shift(1)
    tr_ = trend_series(t2.c)
    return atr.reindex(tab.index).fillna(0).to_numpy(), tr_.reindex(tab.index).fillna(0).to_numpy().astype(np.int64)


def day_levels_cfg(d):
    """replacement of ict.day_levels: same levels, ATR / trend per CFG."""
    om, day, h, l, c = d["om"], d["dayid"], d["h"], d["l"], d["c"]
    nd = int(day.max()) + 1
    df = pd.DataFrame(dict(day=day, om=om, h=h, l=l, c=c))
    rth = df[(df.om >= 570) & (df.om < 960)].groupby("day").agg(h=("h", "max"), l=("l", "min"), c=("c", "last")).reindex(range(nd))
    on = df[(df.om >= 1080) | (df.om < 570)].groupby("day").agg(h=("h", "max"), l=("l", "min")).reindex(range(nd))
    lon = df[(df.om >= 120) & (df.om < 300)].groupby("day").agg(h=("h", "max"), l=("l", "min")).reindex(range(nd))
    L = np.full((nd, 6), np.nan)
    L[:, 0] = rth.h.shift(1).to_numpy(); L[:, 3] = rth.l.shift(1).to_numpy()
    L[:, 1] = on.h.to_numpy(); L[:, 4] = on.l.to_numpy()
    L[:, 2] = lon.h.to_numpy(); L[:, 5] = lon.l.to_numpy()
    atr, trend = ict_style(daily_table(d))
    return L, atr, trend


def daily_stats_cfg(cx):
    """replacement of nt_v2_replica.daily_stats (ORB60 / ORB90 direction, ATR cap and pullback PR): NT-style ramped Wilder ATR with
    window n (ready after n complete RTH days); trend per CFG. For the SMA kind the original rule is kept (mean of the last <= n closes,
    at least min(15, n) closes); the other kinds use trend_series on the sequence of complete RTH closes."""
    n = CFG["atr"][0]; spec = CFG["trend"]; nd = cx.nd
    tab = daily_table(dict(om=cx.om, dayid=cx.dayid, h=cx.h, l=cx.l, c=cx.c))
    tr = true_range(tab, first_plain=True, pc_ffill=True).to_numpy(); cv = tab.c.to_numpy(); valid = ~np.isnan(cv)
    A = np.full(nd, np.nan); T = np.zeros(nd, np.int64); ready = np.zeros(nd, bool)
    if spec[0] != "sma":
        talt = trend_series(tab.c[valid]).reindex(tab.index).fillna(0).to_numpy().astype(np.int64)
    atr = np.nan; cnt = 0; closes = []; prev_tr = np.nan; prev_c = np.nan
    for d in range(nd):
        if not valid[d]: continue
        if not np.isnan(prev_tr):
            cnt += 1; k = min(cnt, n); atr = prev_tr if np.isnan(atr) else ((k - 1) * atr + prev_tr) / k
            closes.append(prev_c); closes = closes[-max(spec[1] if spec[0] == "sma" else 1, 1):]
        A[d] = atr; ready[d] = cnt >= n
        if spec[0] == "sma":
            if len(closes) >= min(15, spec[1]) and not np.isnan(prev_c):
                s = np.mean(closes); T[d] = 1 if prev_c > s else (-1 if prev_c < s else 0)
        else: T[d] = talt[d]
        prev_tr = tr[d]; prev_c = cv[d]
    return A, T, ready


# ------------------------------------------------------------------------------------------------ patching + init
def apply_cfg(cfg):
    CFG.clear(); CFG.update(DEFAULT); CFG.update(cfg)


def install():
    """patch every entry point BEFORE perturb_lib.init(); returns perturb_lib."""
    os.environ["NQ_DATA"] = "nqdb.npz"
    import ict, core, ict_fix, london, nt_v2_replica
    from core import S
    from wrq_lib import SLIP
    import perturb_lib as P
    if not _ORIG:
        _ORIG["day_levels"] = ict.day_levels; _ORIG["daily_stats"] = nt_v2_replica.daily_stats
        _ORIG["time_exit"] = P.time_exit; _ORIG["fills_core"] = P.fills_core; _ORIG["run_events"] = P.run_events
    for m in list(sys.modules.values()):
        try:
            if getattr(m, "day_levels", None) is _ORIG["day_levels"]: m.day_levels = day_levels_cfg
            if getattr(m, "daily_stats", None) is _ORIG["daily_stats"]: m.daily_stats = daily_stats_cfg
        except Exception: pass
    ict_fix.day_levels = day_levels_cfg                     # ict_fix has its OWN copy of day_levels (not imported from ict)
    te, fc, re_ = _ORIG["time_exit"], _ORIG["fills_core"], _ORIG["run_events"]

    def time_exit_cfg(D, fi, hold, flat_hhmm=1555): return te(D, fi, hold, CFG["flat"] if flat_hhmm == 1555 else flat_hhmm)

    def fills_core_cfg(D, ev, flat=955, maxday=1, slip=SLIP): return fc(D, ev, S(CFG["flat"]) if flat == 955 else flat, maxday, slip)

    def run_events_cfg(D, ev, flat=955, **kw): return re_(D, ev, flat=S(CFG["flat"]) if flat == 955 else flat, **kw)
    P.time_exit = time_exit_cfg; P.fills_core = fills_core_cfg; P.run_events = run_events_cfg
    P.MIN_ATR = CFG["min_atr"]
    for m in ("ORB60", "ORB90"): P.SPEC[m]["base"]["pb"] = CFG["pb"]
    return P


def post_init(P):
    """things perturb_lib.init computed from reloaded modules: wr60 up20, crt ATRD / TREND, the real day list."""
    import ict, core, ict_fix, london, tmom, nt_v2_replica
    for m in (ict, core, ict_fix, london, tmom): assert m.day_levels is day_levels_cfg, m.__name__
    assert nt_v2_replica.daily_stats is daily_stats_cfg and P.G["r3"].daily_stats is daily_stats_cfg
    G = P.G; tab = daily_table(G["Dr"]); atr_c, tr_c = compact_style(tab)
    dates = G["Dr"]["date"]; last = pd.Series(np.arange(len(dates))).groupby(G["Dr"]["dayid"]).last()
    ddate = pd.Series(dates[last.to_numpy()], index=last.index)                       # dayid -> date
    tr_by_date = pd.Series(tr_c, index=ddate.reindex(range(len(tr_c))).to_numpy())
    B = G["B5"]; B["up20"] = (pd.Series(B["date"]).map(tr_by_date).fillna(0).to_numpy() > 0)
    G["crt"].ATRD = atr_c.astype(np.float64); G["crt"].TREND = tr_c.astype(np.int64)
    set_minatr(P, CFG["min_atr"])


def set_minatr(P, v):
    G = P.G; D = G["D"]; P.MIN_ATR = float(v)
    dd = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); dd = dd[~np.isin(dd, list(G["fomc"]))]
    atr_d = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(dd).to_numpy()
    G["days_real"] = dd[(atr_d >= P.MIN_ATR) & (dd >= 20180101)]


def init_cfg(cfg):
    apply_cfg(cfg); P = install(); P.init(); post_init(P); return P


def build_parts(P, mods=None):
    return {m: P.compact(P.sim_module(m, P.SPEC[m]["base"])) for m in (mods or P.MODS)}


def rebuild_orb(P, pb):
    for m in ("ORB60", "ORB90"): P.SPEC[m]["base"]["pb"] = pb
    P.G["base_orb60"] = P.e_orb("ORB60", P.SPEC["ORB60"]["base"])
    return build_parts(P, ["ORB60", "ORB90", "MSEQS"])


def mod_pf(parts, P):
    return {m: {per: (v["pf"], v["n"]) for per, v in P.module_metrics(tr).items()} for m, tr in parts.items()}


# ------------------------------------------------------------------------------------------------ modes
def check():
    """default CFG must reproduce the original arrays and the base portfolio."""
    os.environ["NQ_DATA"] = "nqdb.npz"
    import ict, nt_v2_replica, wrq_build as WB
    apply_cfg({}); Dr = WB.raw("nqdb.npz")
    L0, a0, t0 = _ORIG.get("day_levels", ict.day_levels)(Dr); L1, a1, t1 = day_levels_cfg(Dr)
    assert np.allclose(np.nan_to_num(L0), np.nan_to_num(L1)) and np.allclose(a0, a1) and (t0 == t1).all(), "ict.day_levels mismatch"
    print("ict.day_levels reproduced", flush=True)
    cwd = os.getcwd(); os.chdir(RES)
    try:
        import common; cx = common.Ctx()
    finally: os.chdir(cwd)
    A0, T0, r0 = nt_v2_replica.daily_stats(cx); A1, T1, r1 = daily_stats_cfg(cx)
    assert np.allclose(np.nan_to_num(A0), np.nan_to_num(A1)) and (T0 == T1).all() and (r0 == r1).all(), "daily_stats mismatch"
    print("nt_v2_replica.daily_stats reproduced", flush=True)
    P = init_cfg({})
    crt = P.G["crt"]; a_c, t_c = compact_style(daily_table(Dr))
    orig_a, orig_t = crt.daily_trend_atr()
    assert np.allclose(orig_a, a_c) and (orig_t == t_c).all(), "crt ATRD/TREND mismatch"
    print("crt.ATRD / TREND reproduced", flush=True)
    w = P.G["wr60"]; B0 = w.build(5)
    assert (B0["up20"] == P.G["B5"]["up20"]).all(), "wr60 up20 mismatch"
    print("wr60 up20 reproduced", flush=True)
    parts = build_parts(P); M = P.port_metrics(parts)
    print({k: (v["n"], v["sharpe"]) for k, v in M.items()})
    ref = {"A": (5545, 0.62), "B": (6011, 1.30), "T1": (4804, 3.68), "T2": (3420, 4.07)}
    for k, (n, s) in ref.items(): assert M[k]["n"] == n and abs(M[k]["sharpe"] - s) < 0.0101, (k, M[k])
    print("base portfolio reproduced (perturb_report base row)", flush=True)


def cell(name):
    t0 = time.time(); P = init_cfg(CELLS[name]); parts = build_parts(P)
    res = dict(name=name, cfg={k: (list(v) if isinstance(v, tuple) else v) for k, v in CFG.items()}, port=P.port_metrics(parts), mods=mod_pf(parts, P))
    if name == "base":
        res["minatr"] = {}
        for v in MINATR_LEVELS:
            set_minatr(P, v); res["minatr"][str(v)] = P.port_metrics(parts)
        set_minatr(P, DEFAULT["min_atr"])
        res["pb"] = {}
        for pb in PB_LEVELS:
            q = dict(parts); q.update(rebuild_orb(P, pb)); res["pb"][str(pb)] = dict(port=P.port_metrics(q), mods=mod_pf({m: q[m] for m in ("ORB60", "ORB90", "MSEQS")}, P))
        rebuild_orb(P, DEFAULT["pb"])
    pickle.dump(parts, open(os.path.join(OUT, name + ".pkl"), "wb"))
    json.dump(res, open(os.path.join(OUT, name + ".json"), "w"), indent=1, default=float)
    print(name, "done", round(time.time() - t0), "s", {k: (v["n"], v["sharpe"]) for k, v in res["port"].items()}, flush=True)


def run_all(procs=2):
    names = [n for n in CELLS if not os.path.exists(os.path.join(OUT, n + ".json"))]
    print("cells to run", len(names), flush=True)
    lst = "\n".join(names) + "\n"
    cmd = f"cd {HERE} && xargs -P {procs} -I{{}} sh -c 'python3 foundations.py cell {{}} > {OUT}/log_{{}}.txt 2>&1'"
    subprocess.run(cmd, shell=True, input=lst.encode())


def _none_control(P):
    """control 'none': union of the trend = +1 and trend = -1 builds (dedupe on module, fi, d)."""
    up = pickle.load(open(os.path.join(OUT, "trend_up.pkl"), "rb")); dn = pickle.load(open(os.path.join(OUT, "trend_dn.pkl"), "rb"))
    parts = {}
    for m in up:
        pair = []
        for i in (0, 1):
            X = pd.concat([up[m][i], dn[m][i]], ignore_index=True).drop_duplicates(["mod", "fi", "d"]).sort_values("fi", kind="stable").reset_index(drop=True)
            pair.append(X)
        parts[m] = tuple(pair)
    return dict(name="trend_none", port=P.port_metrics(parts), mods=mod_pf(parts, P))


def report():
    R = {n: json.load(open(os.path.join(OUT, n + ".json"))) for n in CELLS if os.path.exists(os.path.join(OUT, n + ".json"))}
    P = init_cfg({})
    if "trend_up" in R and "trend_dn" in R: R["trend_none"] = _none_control(P)
    base = R["base"]["port"]
    rows = {}
    for n, r in R.items():
        if n in ("trend_up", "trend_dn"): continue
        rows[n] = r["port"]
    for v, r in R["base"]["minatr"].items(): rows[f"minatr_{int(float(v))}"] = r
    # MinATR with a FIXED day index (every non-FOMC day >= 2018; days below the guard count as flat): perturb_lib's own metrics drop
    # the guarded days from the Sharpe denominator, which flatters a higher guard.
    parts = pickle.load(open(os.path.join(OUT, "base.pkl"), "rb")); set_minatr(P, 0.0); full = P.G["days_real"].copy()
    for v in MINATR_LEVELS:
        set_minatr(P, v); X = P.assemble(parts, "real"); P.G["days_real"] = full
        rows[f"minatrF_{int(v)}"] = dict(base["A"] if False else {}, **{p: (P.metrics(X, p) if p in ("T1", "T2") else base[p]) for p in PERS})
    set_minatr(P, DEFAULT["min_atr"])
    for v, r in R["base"]["pb"].items(): rows[f"pb_{v}"] = r["port"]
    out = dict(protocol=__doc__, base=base, rows=rows, verdict=verdicts(rows, base), mods={n: R[n]["mods"] for n in R if "mods" in R[n]},
               pb_mods={v: r["mods"] for v, r in R["base"]["pb"].items()})
    json.dump(out, open(os.path.join(HERE, "foundations.json"), "w"), indent=1, default=float)
    open(os.path.join(HERE, "foundations_report.md"), "w").write(md_report(out))
    print("written foundations.json / foundations_report.md", flush=True)


KNOBS = {
    "F1 trend": ["trend_sma10", "trend_sma15", "base", "trend_sma25", "trend_sma30", "trend_sma50", "trend_ema20", "trend_mom5", "trend_mom10", "trend_mom20", "trend_both20_50", "trend_none"],
    "F2 ATR window": ["atr_7", "atr_10", "base", "atr_20", "atr_30", "atr_full14"],
    "F2 MinATR": ["minatr_100", "base", "minatr_200", "minatr_250"],
    "F2 MinATR, fixed day index (flat days = 0; A / B unchanged)": ["minatrF_100", "minatrF_150", "minatrF_200", "minatrF_250"],
    "F3 pullback": ["pb_0.3", "pb_0.35", "base", "pb_0.5", "pb_0.6", "pb_99.0"],
    "F4 flat": ["flat_1545", "flat_1550", "base", "flat_1558", "flat_1600", "flat_1614"],
}
ORDERED = {"F1 trend": ["trend_sma10", "trend_sma15", "base", "trend_sma25", "trend_sma30", "trend_sma50"], "F1 mom": ["trend_mom5", "trend_mom10", "trend_mom20"],
           "F2 ATR window": ["atr_7", "atr_10", "base", "atr_20", "atr_30"], "F2 MinATR": ["minatr_100", "base", "minatr_200", "minatr_250"], "F2 MinATR fixed": ["minatrF_100", "minatrF_150", "minatrF_200", "minatrF_250"],
           "F3 pullback": ["pb_0.3", "pb_0.35", "base", "pb_0.5", "pb_0.6", "pb_99.0"], "F4 flat": ["flat_1545", "flat_1550", "base", "flat_1558", "flat_1600", "flat_1614"]}
LABEL = {"minatrF_150": "MinATR 150 (= base, fixed day index)", "base": "BASE (SMA20 / ATR14 RTH / MinATR 150 / pb 0.44 / flat 15:55)", "trend_none": "no trend filter (union +1 / -1)", "trend_both20_50": "SMA20 & SMA50 agree",
         "trend_ema20": "EMA20", "atr_full14": "ATR14 of the full Globex range", "pb_99.0": "no pullback filter", "flat_1600": "flat 16:00 (first bar >= 16:00)", "flat_1614": "flat 16:14 (last bar before the halt)"}


CONCLUSIONS = """
## Plateau verdicts and conclusions

Reading of the tables (base Sharpe A / B / T1 / T2 = 0.63 / 1.30 / 3.68 / 4.06; T2 is the only period never used to choose anything).

* **F1 daily trend filter.** Removing it (control 'none') costs 0.95 / 1.12 Sharpe in T1 / T2, 0.22 PF, 3.4 WR points and +68 % maxDD, and
  0.66 / 0.31 in 2010-14 / 2015-19: the filter is the single most valuable foundation of the system (ON07, LON, VW13, LF0430, ORFAIL go to
  PF ~1 without it). Its exact form is NOT finely tuned but the base sits on a shallow ridge, not a flat plateau: SMA15 / SMA25 / SMA30 are
  within -0.03 / +0.08 / -0.12 Sharpe in T1 and -0.23 / -0.06 / -0.17 in T2 (PF within 0.05), SMA10 and SMA50 lose 0.4-0.9, EMA20 is
  equivalent (-0.05 / +0.03) but with +46 % T2 maxDD, momentum references (close vs N days ago) and the SMA20 & SMA50 agreement lose 0.2-0.6.
  By the pre-registered rule the current choice is labelled **'spike'** (an adjacent level loses more than 0.15 in T2); the honest wording is
  'local optimum selected on 2020-23 (T1), one step away costs 0.1-0.2 Sharpe out of sample, every neighbour 15-30 is still PF >= 1.45 in
  both real periods'. In 2010-19 (never used for any choice) SMA25 / SMA30 beat SMA20 by +0.05..+0.12, i.e. the old data prefers a slightly
  longer average; SMA25 is the only candidate that wins T1 + A + B, and it fails the T2 confirmation by 0.06 Sharpe / 0.019 PF (DD +0.5 %).
  That is inside noise and is NOT adopted: the rule was fixed in advance and T2 is the only clean out-of-sample period.
* **F2 daily ATR.** The RTH-range definition is a real choice: the full Globex-session range loses 0.55 / 0.81 Sharpe and 0.06 / 0.10 PF
  (stops and thresholds become too wide). The window 14 is again a local optimum: 10 and 20 lose 0.08-0.18 in T1 / T2 (PF -0.02) while
  gaining 0.04-0.08 in 2010-14; 7 and 30 lose 0.25-0.5. Labelled **'spike'** by the rule (worst neighbour -0.18); in practice every window
  7-30 keeps PF >= 1.44 and all four periods positive. **MinATR 150**: a plateau. With a fixed day index (days below the guard count as flat,
  which perturb_lib's own metric does not do and which flatters a higher guard), T1 Sharpe is 3.62 / 3.58 / 3.39 / 2.98 for 100 / 150 /
  200 / 250 and T2 4.06 / 4.06 / 4.01 / 3.80: a higher guard raises PF (fewer, better trades) and lowers the daily Sharpe; 100 adds 188
  trades in 2018-20 for +0.04 Sharpe. Rows of that table must be compared with each other, not with the base row above them.
* **F3 ORB pullback threshold 0.44 ATR.** A genuine **plateau**: 0.30 / 0.35 / 0.50 / 0.60 are within -0.08..-0.14 Sharpe in T1 and
  within 0.02 in T2, PF within 0.02; without the filter ORB loses 0.72 / 0.37 Sharpe and 0.10 / 0.07 PF. The filter matters, its value
  does not.
* **F4 flat time 15:55.** A **plateau**: 15:45 / 15:50 / 15:58 / 16:00 are within -0.06..+0.02 in T1 and -0.14..+0.03 in T2 with
  identical trade counts; holding to 16:14 costs 0.20 / 0.10 Sharpe and +7 % maxDD. 15:50 wins T1 + A + B by 0.02-0.15 and loses T2 by
  0.13 (WR -0.5): noise. 15:58 is +0.03 T2 / -0.01 T1: noise. No reason to move; the live FlattenTime 15:56 sits inside this plateau.

**Accepted changes: none.** No NQMaster property changes from this audit. The foundations were set in 2026-09 on CFD 2020-23 data; on the
16-year real futures data none of the 34 alternatives beats them under the pre-registered rule, the two T1 + A + B candidates (SMA25,
flat 15:50) fail the 2024-26 confirmation by amounts inside noise, and the two controls (no trend filter, no pullback filter) show that
the filters themselves carry 0.4-1.1 Sharpe. What the audit does say is that SMA20 and ATR14 are the best values on the selection period
and only locally best elsewhere (a neighbour costs 0.1-0.2 Sharpe, the 2010-19 data would have picked SMA25 / ATR 7-20); treat them as
'chosen on 2020-23, robust to one step', not as plateau values, and do not re-tune them on 2024-26.

Audit note: the first run of this script left ICT at the base trend / ATR in every cell because `ict_fix.py` defines its own `day_levels`
(not imported from `ict`), so the identity-based patch missed it; the per-module table exposed it (ICT PF identical in every trend cell),
`install()` now patches `ict_fix` explicitly and `post_init()` asserts every patched entry point. The tables above are from the corrected run.
"""


def neighbours(name):
    for k, lst in ORDERED.items():
        if name in lst:
            i = lst.index(name); return [lst[j] for j in (i - 1, i + 1) if 0 <= j < len(lst)]
    return []


def verdicts(rows, base):
    V = {}
    for n, r in rows.items():
        if n == "base": continue
        dec = all(r[p]["sharpe"] > base[p]["sharpe"] for p in ("A", "B", "T1"))
        conf = (r["T2"]["sharpe"] >= base["T2"]["sharpe"] and r["T2"]["pf"] >= base["T2"]["pf"] and r["T2"]["wr"] >= base["T2"]["wr"]
                and r["T2"]["maxdd"] <= 1.05 * base["T2"]["maxdd"] and r["T2"]["n"] >= 0.95 * base["T2"]["n"] and r["T1"]["n"] >= 0.95 * base["T1"]["n"])
        nb = [m for m in neighbours(n) if m in rows]
        nbs = [rows[m]["T1"]["sharpe"] for m in nb]
        plat = (all(s >= base["T1"]["sharpe"] - 0.10 for s in nbs) and any(s > base["T1"]["sharpe"] for s in nbs)) if nb else None
        V[n] = dict(candidate=dec, confirmed=dec and conf, plateau=plat, accepted=bool(dec and conf and plat), needs_plateau_scan=bool(dec and conf and plat is None),
                    dS={p: round(r[p]["sharpe"] - base[p]["sharpe"], 3) for p in PERS}, dPF={p: round(r[p]["pf"] - base[p]["pf"], 4) for p in PERS},
                    dWR={p: round(r[p]["wr"] - base[p]["wr"], 2) for p in PERS}, dN={p: r[p]["n"] - base[p]["n"] for p in PERS}, dDD_T2=round(r["T2"]["maxdd"] / base["T2"]["maxdd"] - 1, 3))
    # plateau verdict of the current choice per knob
    cur = {}
    for k, lst in ORDERED.items():
        if "base" not in lst: continue
        i = lst.index("base"); nb = [lst[j] for j in (i - 1, i + 1) if 0 <= j < len(lst) and lst[j] in rows]
        worst = min(min(rows[m]["T1"]["sharpe"] - base["T1"]["sharpe"], rows[m]["T2"]["sharpe"] - base["T2"]["sharpe"]) for m in nb)
        dpf = max(abs(rows[m][p]["pf"] - base[p]["pf"]) for m in nb for p in ("T1", "T2"))
        cur[k] = dict(neighbours=nb, worst_dSharpe=round(worst, 3), max_dPF=round(dpf, 4),
                      verdict="spike" if worst < -0.15 else ("plateau" if (len(nb) == 2 and dpf <= 0.03) else ("edge" if len(nb) == 1 else "plateau (PF moves > 0.03)")))
    return dict(alternatives=V, current=cur)


def fmt(rows, names):
    H = "| configuration | trades (tr/day) A / B / T1 / T2 | WR % | PF | Sharpe | maxDD | worst month |\n|---|---|---|---|---|---|---|\n"
    L = []
    for n in names:
        if n not in rows: continue
        r = rows[n]; j = lambda k, f: " / ".join(f.format(r[p][k]) for p in PERS)
        L.append(f"| {LABEL.get(n, n)} | " + " / ".join(f"{r[p]['n']} ({r[p]['tpd']:.2f})" for p in PERS) + f" | {j('wr', '{:.1f}')} | {j('pf', '{:.3f}')} | {j('sharpe', '{:.2f}')} | {j('maxdd', '{:.0f}')} | {j('worst_month', '{:.0f}')} |")
    return H + "\n".join(L) + "\n"


def md_report(out):
    rows, base, V = out["rows"], out["base"], out["verdict"]
    s = ["# Global foundations audit of the 2027 NQMaster default (2026-10-19)\n",
         "Rebuilt with `perturb_lib.py` (reproduces `nt_compare --set ultra_d4` row for row) on real Databento NQ 2010-06..2026-10. "
         "Every module inherits the daily trend filter, the daily ATR (stops, thresholds, cost normalisation, MinATR guard), the ORB pullback threshold and the flat time; "
         "they were set in 2026-09 on CFD data and are varied here one at a time, the whole portfolio rebuilt for each value "
         "(conflict filter, agreement, confluence, context rules, MinATR 150, MOM1030 / CPI09 x4, ICT x2). "
         "A / B = 2010-14 / 2015-19 cost-normalised (0.345 % ATR, P&L in % ATR); T1 / T2 = 2020-23 / 2024-26 real $ per MNQ ($1.90 + 1 tick). "
         "`python3 foundations.py check` verified that the default configuration reproduces every original array (ict.day_levels, nt_v2_replica.daily_stats, crt ATRD/TREND, wr60 up20) and the base portfolio.\n",
         "## Protocol (pre-registered)\n", "```\n" + __doc__.split("PRE-REGISTERED ACCEPTANCE")[1].split("Run:")[0].strip() + "\n```\n",
         "## Base\n", fmt(rows, ["base"])]
    for k, names in KNOBS.items():
        s.append(f"## {k}\n"); s.append(fmt(rows, names))
        if k in V["current"]:
            c = V["current"][k]; s.append(f"Current choice: **{c['verdict']}** (neighbours {c['neighbours']}: worst dSharpe {c['worst_dSharpe']:+.2f}, max |dPF| {c['max_dPF']:.3f}).\n")
        s.append("| alternative | candidate (Sharpe up A, B, T1) | T2 confirmed | plateau | accepted | dSharpe A/B/T1/T2 | dPF T1/T2 | dWR T1/T2 | dN T1/T2 | dDD T2 |\n|---|---|---|---|---|---|---|---|---|---|")
        for n in names:
            if n not in V["alternatives"]: continue
            v = V["alternatives"][n]; y = lambda b: "n/a" if b is None else ("yes" if b else "no")
            s.append(f"| {LABEL.get(n, n)} | {y(v['candidate'])} | {y(v['confirmed'])} | {y(v['plateau'])} | **{y(v['accepted'])}** | " + " / ".join(f"{v['dS'][p]:+.2f}" for p in PERS)
                     + f" | {v['dPF']['T1']:+.3f} / {v['dPF']['T2']:+.3f} | {v['dWR']['T1']:+.1f} / {v['dWR']['T2']:+.1f} | {v['dN']['T1']:+d} / {v['dN']['T2']:+d} | {v['dDD_T2']:+.1%} |")
        s.append("")
    acc = [n for n, v in V["alternatives"].items() if v["accepted"]]
    s.append("## Accepted changes\n"); s.append(("- " + "\n- ".join(LABEL.get(n, n) for n in acc)) if acc else "None.")
    nps = [n for n, v in V["alternatives"].items() if v.get("needs_plateau_scan")]
    if nps: s.append("\nCandidates confirmed on T2 whose plateau is not testable with this grid (non-ordinal alternative; would need its own length scan before any adoption): " + ", ".join(LABEL.get(n, n) for n in nps))
    # module-level view of the trend alternatives (standalone PF T1 / T2)
    mods = out["mods"]
    if "base" in mods:
        s.append("\n## Module standalone PF (T1 / T2) under the trend alternatives\n")
        names = [n for n in ["base", "trend_sma10", "trend_sma50", "trend_ema20", "trend_mom10", "trend_both20_50", "trend_none"] if n in mods]
        s.append("| module | " + " | ".join(LABEL.get(n, n).split(" (")[0] for n in names) + " |\n|---|" + "---|" * len(names))
        for m in mods["base"]:
            s.append(f"| {m} | " + " | ".join(f"{mods[n][m]['T1'][0]:.2f} / {mods[n][m]['T2'][0]:.2f}" if m in mods[n] else "" for n in names) + " |")
    s.append(CONCLUSIONS)
    return "\n".join(s) + "\n"


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    if mode == "check": check()
    elif mode == "cell": cell(sys.argv[2])
    elif mode == "run": run_all(int(sys.argv[2]) if len(sys.argv) > 2 else 2)
    elif mode == "report": report()
