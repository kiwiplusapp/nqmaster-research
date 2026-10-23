"""perturb_lib: parameter-perturbation engine for the 2027 default NQMaster set (Ultra + SO04/RV11/ORFAIL/CAM3), 2026-10-19.
Import-safe (no work at import; call init() once per process).

Every module of the 2027 default is re-simulated from its ORIGINAL signal code with perturbed parameters on real Databento NQ
(research/data/nqdb.npz, 2010-06..2026-10):
  tmom.py      MOM11 / MOM1030 / MOM13 / ON07 / REV06        (params: entry time t, lookback L, stop sk x ATR, target R, hold H)
  nt_v3_replica ORB60 / ORB90 (pullback days)                 (range_min, t1_r, orb_cap, pullback threshold 0.44)
  wr60.py      MSEQ (+ own MSEQS mirror)                      (N, R, stop_k, window start)
  crt2.py      CRT11                                          (candle boundary offset, R, max_risk)
  ict_fix.py   ICT                                            (window end, max_risk, R, limit life M)
  london.py    LON                                            (range end, break deadline, R, max_risk)
  families*    VW13(+b) / VOLB / LATE15 / NF05 / LF06 / LF0430 / SO04 / RV11 / ORFAIL / CAM3 / CPI09
The 19 'wrq' modules go through the same exit engine / filters as cand16.py (minstop 0.10 ATR on structure modules, ORB trigger
>= 0.1 ATR beyond the prior close, VOLB break-even, agreement MOM1030/MOM13, confluence A/B, pruned context rules, MinATR 150 in
the real view); the 5 mined modules (CPI09, SO04, RV11, ORFAIL, CAM3) go through core.run_events exactly as in six_build.py.
Views: real ($ per MNQ, $1.90 + 1 tick, T1 2020-23 / T2 2024-26) and norm (cost 0.345% ATR, P&L in % ATR, A 2010-14 / B 2015-19)."""
import os, sys, importlib, pickle, numpy as np, pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.dirname(HERE)
for p in (HERE, RES):
    if p not in sys.path: sys.path.insert(0, p)
from core import run_events, S
from wrq_lib import getD, time_exit, fills_core, SLIP, TICK
from wrq_exits import arrays, sim as xsim_run
NAME = "nqdb.npz"; BIG = 10 ** 7; MIN_ATR = 150.0; MINSTOP = 0.10; ORBT = 0.1
STRUCT = ["ORB60", "ORB90", "VOLB", "MSEQ", "MSEQS", "CRT11", "ICT", "LON"]
LATE = ["CRT11", "MOM13", "MSEQ", "MSEQS"]
EXIT_P = {"VOLB": dict(be=0.75, beo=0.1)}
BASE_W = {"ICT": 2.0}
X4 = ("MOM1030", "CPI09")
PERIODS = {"A": (20100601, 20150101, "norm"), "B": (20150101, 20200101, "norm"), "T1": (20200101, 20240101, "real"), "T2": (20240101, 20991231, "real")}
G = {}

# ------------------------------------------------------------------------------------------------ module specs
# perturbable parameters: kind 'pct' (x (1+e), e in +-20%), 'time' (+- minutes), 'int' (pct then rounded, min 1)
SPEC = {
    "MOM11": dict(kind="tmom", base=dict(t=660, L=-2, rev=0, sk=0.25, R=0.3, H=100000, tf=0), pert=dict(t="time", sk="pct", R="pct")),
    "MOM1030": dict(kind="tmom", base=dict(t=630, L=-2, rev=0, sk=0.2, R=0.3, H=60, tf=1), pert=dict(t="time", sk="pct", R="pct", H="int")),
    "MOM13": dict(kind="tmom", base=dict(t=780, L=-2, rev=0, sk=0.2, R=1.0, H=240, tf=1), pert=dict(t="time", sk="pct", R="pct", H="int")),
    "ON07": dict(kind="tmom", base=dict(t=420, L=30, rev=0, sk=0.2, R=1.0, H=60, tf=1), pert=dict(t="time", L="int", sk="pct", R="pct")),
    "REV06": dict(kind="tmom", base=dict(t=360, L=30, rev=1, sk=0.2, R=0.3, H=240, tf=1), pert=dict(t="time", L="int", sk="pct", R="pct")),
    "ORB60": dict(kind="orb", base=dict(rm=60, t1=0.6, cap=0.35, pb=0.44), pert=dict(rm="int", t1="pct", cap="pct", pb="pct")),
    "ORB90": dict(kind="orb", base=dict(rm=90, t1=0.6, cap=0.35, pb=0.44), pert=dict(rm="int", t1="pct", cap="pct", pb="pct")),
    "MSEQ": dict(kind="mseq", base=dict(N=5, R=0.5, sk=1.75, ws=630), pert=dict(N="int", R="pct", sk="pct", ws="time")),
    "MSEQS": dict(kind="mseqs", base=dict(N=5, R=0.75, sk=1.75, ws=630), pert=dict(N="int", R="pct", sk="pct", ws="time")),
    "CRT11": dict(kind="crt", base=dict(off=0, R=2.0, mr=0.5), pert=dict(off="time", R="pct", mr="pct")),
    "ICT": dict(kind="ict", base=dict(we=630, mr=0.25, R=1.0, M=20), pert=dict(we="time", mr="pct", R="pct", M="int")),
    "LON": dict(kind="lon", base=dict(re=180, we=360, R=2.0, mr=0.25), pert=dict(re="time", we="time", R="pct", mr="pct")),
    "VW13": dict(kind="vw13", base=dict(T=1300, x=1.0, s=0.15, R=0.5), pert=dict(T="time", x="pct", s="pct", R="pct")),      # x scales both lots (0.15 / 0.30)
    "VOLB": dict(kind="fam", fam="VOL_BREAK", base=dict(k=0.45, s=0.35, R=2.0, tf=0, w1=1500, hold=400, stop=0), pert=dict(k="pct", R="pct", w1="time", hold="int")),
    "LATE15": dict(kind="fam", fam="LATE_MOM", base=dict(T=1500, sig="RTH", x=0.5, tf=1, k=0.3, R=0.5), pert=dict(T="time", x="pct", k="pct", R="pct")),
    "NF05": dict(kind="fam", fam="G_DRIVE", base=dict(A=2000, T=540, x=0.35, mode=-1, tf=0, k=0.2, stop=0, R=2.0, hold=240), pert=dict(A="time", x="pct", k="pct", R="pct")),
    "LF06": dict(kind="fam", fam="G_DRIVE", base=dict(A=400, T=120, x=0.2, mode=-1, tf=0, k=0.2, stop=0, R=0.5, hold=240), pert=dict(A="time", x="pct", k="pct", R="pct")),
    "LF0430": dict(kind="fam", fam="G_DRIVE", base=dict(A=400, T=30, x=0.1, mode=-1, tf=1, k=0.35, stop=0, R=0.5, hold=240), pert=dict(A="time", x="pct", k="pct", R="pct")),
    "SO04": dict(kind="ev", fam="CLOCK_ANCHOR", maxday=1, base=dict(anc="SOPEN", T=400, x=0.35, mode=1, s=0.15, R=1.0, tg=0, tf=1, hold=330), pert=dict(T="time", x="pct", s="pct", R="pct")),
    "RV11": dict(kind="ev", fam="RVOL_DRIVE", maxday=1, base=dict(T=1100, lim=0.8, ref="pdc", x=0.25, dm=1, tf=0, k=0.15, R=1.0), pert=dict(T="time", lim="pct", x="pct", k="pct", R="pct")),
    "ORFAIL": dict(kind="ev", fam="OR_FAIL", maxday=1, base=dict(T=15, w1=1400, bk=0.1, tfb=5, tg="opp", tf=1), pert=dict(T="int", bk="pct", w1="time")),
    "CAM3": dict(kind="ev", fam="PIVOT_FADE", maxday=2, base=dict(piv="CAM3", camf=1.1 / 4, w0=1000, w1=1530, sweep=0.0, conf=10, tg=1, R=1.0, tf=1, hold=240), pert=dict(w0="time", w1="time", conf="int", camf="pct")),
    "CPI09": dict(kind="ev", fam="CPI", maxday=1, base=dict(A=830, T=60, x=0.05, mode=-1, tf=0, k=0.35, stop=0, R=0.5, hold=60), pert=dict(T="int", x="pct", k="pct", R="pct")),
}
MODS = list(SPEC)
WRQ = [m for m in MODS if SPEC[m]["kind"] != "ev"]


def add_minutes(hhmm, mins):
    t = (hhmm // 100) * 60 + hhmm % 100 + mins; t %= 1440
    return (t // 60) * 100 + t % 60


def perturbed(mod, eps):
    """eps: {param: e}; pct -> x(1+e); time -> + e minutes (hhmm clocks, or plain minutes for CRT off / ICT we / LON re,we / MSEQ ws);
    int -> round(x(1+e)) >= 1. Returns a full param dict."""
    sp = SPEC[mod]; p = dict(sp["base"])
    for k, e in eps.items():
        kind = sp["pert"][k]
        if kind == "pct": p[k] = p[k] * (1 + e)
        elif kind == "int": p[k] = max(1, int(round(p[k] * (1 + e))))
        elif kind == "time":
            if mod in ("CRT11",): p[k] = int(round(e))
            elif mod in ("ICT", "LON", "MSEQ", "MSEQS", "MOM11", "MOM1030", "MOM13", "ON07", "REV06"): p[k] = int(p[k] + round(e))      # om minutes
            else: p[k] = add_minutes(p[k], int(round(e)))                                                                              # hhmm
    return p


# ------------------------------------------------------------------------------------------------ init
def _reload(mod):
    os.environ["NQ_DATA"] = NAME; cwd = os.getcwd(); os.chdir(RES)
    try:
        m = importlib.import_module(mod); m = importlib.reload(m)
    finally:
        os.chdir(cwd)
    return m


def init():
    if G: return G
    import wrq_build as WB
    D = getD(NAME); Dr = WB.raw(NAME); G["D"] = D; G["Dr"] = Dr; G["WB"] = WB
    import ict, tmom
    G["tmom"] = tmom; G["X"] = ict.day_levels(Dr)
    om, c, o, h, l, v = Dr["om"], Dr["c"], Dr["o"], Dr["h"], Dr["l"], np.maximum(Dr["v"].astype(float), 1e-9)
    rth = (om >= 570) & (om < 660)
    g = pd.DataFrame(dict(date=Dr["date"][rth], o=o[rth], c=c[rth], tp=(h[rth] + l[rth] + c[rth]) / 3 * v[rth], v=v[rth]))
    a = g.groupby("date").agg(o=("o", "first"), c=("c", "last"), tp=("tp", "sum"), v=("v", "sum"))
    G["agree"] = (np.sign(a.c - a.tp / a.v) == np.sign(a.c - a.o))
    full_day = (D.om[D.de] >= 955) & (D.om[D.de] < 1080); G["full_day"] = full_day
    # ORB context
    os.environ["NQ_DATA"] = NAME; cwd = os.getcwd(); os.chdir(RES)
    try:
        import common; importlib.reload(common); import nt_v3_replica as r3; importlib.reload(r3)
        from nt_v2_replica import daily_stats
        cx = common.Ctx()
    finally:
        os.chdir(cwd)
    A, T, _ = daily_stats(cx)
    G["cx"] = cx; G["r3"] = r3
    G["PR"] = {cx.dates[dd]: (cx.prev_close[dd] - cx.prev_close[dd - 1]) / A[dd] * T[dd] for dd in range(2, cx.nd) if A[dd] > 0}
    # MSEQ
    w = _reload("wr60"); G["wr60"] = w; G["B5"] = w.build(5); G["f1"] = WB.first_1m_of_5m(Dr); assert len(G["f1"]) == len(G["B5"]["c"])
    # CRT
    crt = _reload("crt"); crt2 = _reload("crt2"); G["crt"] = crt; G["crt2"] = crt2
    et_off = ((crt.OM - (crt.EP % 1440)) % 1440); G["et_ep"] = crt.EP + np.where(et_off > 720, et_off - 1440, et_off)
    # ICT
    cwd = os.getcwd(); os.chdir(RES)
    try:
        import ict_fix
    finally:
        os.chdir(cwd)
    G["ictB"] = ict_fix.bars(Dr, 5); G["ictL"] = ict_fix.day_levels(Dr)
    # LON
    import london
    G["lonB"] = london.bars(Dr, 1); _, atl, trl = london.day_levels(Dr); G["lonA"] = (atl, trl)
    # families
    from families import FAMILIES, gen_clock
    from families2 import FAMILIES2, gen_volbreak, _lfade
    from families4 import gen_late
    from families5 import gen_rvol, gen_orfail
    from families_gold import gen_drive
    G["gens"] = dict(CLOCK_ANCHOR=gen_clock, VOL_BREAK=gen_volbreak, LATE_MOM=gen_late, G_DRIVE=gen_drive, RVOL_DRIVE=gen_rvol, OR_FAIL=gen_orfail, CPI=gen_drive)
    G["lfade"] = _lfade
    from news import NEWS
    from news_hist import CPI_ALL
    from db_long import FOMC_1019
    G["fomc"] = set(NEWS["FOMC"]) | set(FOMC_1019); G["cpi"] = set(CPI_ALL)
    dd = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); dd = dd[~np.isin(dd, list(G["fomc"]))]
    atr_d = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(dd).to_numpy()
    G["days_norm"] = dd; G["days_real"] = dd[(atr_d >= MIN_ATR) & (dd >= 20180101)]
    full = pickle.load(open(os.path.join(HERE, "filt_sel.pkl"), "rb"))
    G["sel"] = [(r, k) for r, k in full if (r["mod"], r["feat"]) not in (("ORB90", "vw"), ("ORB60", "atr"))]
    G["fcache"] = {}
    G["base_orb60"] = e_orb("ORB60", SPEC["ORB60"]["base"])      # MSEQS gate = base ORB60 short fills (fixed in every perturbation)
    return G


# ------------------------------------------------------------------------------------------------ entry builders (wrq style)
def mk(mod, fi, d, ent0, et, sl0, tp0, tx):
    D = G["D"]; fi = np.asarray(fi, np.int64)
    E = pd.DataFrame(dict(date=D.date[fi], mod=mod, fi=fi, d=np.asarray(d, np.int64), ent0=np.asarray(ent0, float), et=np.asarray(et, np.int64) * np.ones(len(fi), np.int64),
                          sl0=np.asarray(sl0, float), tp0=np.asarray(tp0, float), tx=np.asarray(tx, np.int64)))
    E["fomc"] = E.date.isin(G["fomc"]); E["tin"] = D.sm[fi]
    return E.sort_values("fi", kind="stable").reset_index(drop=True)


def e_tmom(mod, p):
    D, Dr, tm = G["D"], G["Dr"], G["tmom"]
    df = tm.run(Dr, G["X"], p["t"], p["L"], p["rev"], p["sk"], p["R"], p["H"], p["tf"])
    if mod == "MOM11":
        full = G["full_day"][D.day[df.bi.to_numpy()]]
        df = df[df.date.map(G["agree"]).fillna(False).astype(bool).to_numpy() & full]
    bi = df.bi.to_numpy(); dd = df.d.to_numpy().astype(np.int64); e = D.o[bi] + dd * SLIP; rk = df.risk.to_numpy()
    return mk(mod, bi, dd, D.o[bi], 0, e - dd * rk, e + dd * p["R"] * rk, time_exit(D, bi, p["H"], 1555))


def e_orb(mod, p):
    D, cx, r3 = G["D"], G["cx"], G["r3"]; rm = int(p["rm"])
    base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=p["cap"], vw_stop=0.35)
    df = r3.run(cx, t1_r=p["t1"], use_vwap=False, range_min=rm, entry_start=max(630, 570 + rm), **base)
    df = df[df.date.map(G["PR"]) < p["pb"]]
    fi = df.entry_idx.to_numpy(); dd = df.dir.to_numpy().astype(np.int64); e = df.entry.to_numpy(); rk = df.risk_pts.to_numpy()
    E = mk(mod, fi, dd, e - dd * SLIP, 0, e - dd * rk, e + dd * p["t1"] * rk, time_exit(D, fi, BIG, 1555)); E.attrs["rm"] = rm
    return E


def e_mseq(mod, p):
    D, w, B, f1 = G["D"], G["wr60"], G["B5"], G["f1"]; N = int(p["N"])
    if mod == "MSEQ":
        o5 = np.zeros((len(B["c"]) // 3, 4))
        k = w.sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], B["up20"], N, p["R"], p["sk"], 0.0, 0, int(p["ws"]), 945, 955, 0.0, o5)
        eb = o5[:k, 1].astype(np.int64); fi = f1[eb]; e = D.o[fi] + SLIP; rk = o5[:k, 2]
        return mk(mod, fi, np.ones(k), D.o[fi], 0, e - rk, e + p["R"] * rk, time_exit(D, fi, BIG, 1555))
    orb60 = G["base_orb60"]
    sh = orb60[orb60.d == -1].groupby("date").fi.min()
    last1 = np.r_[f1[1:] - 1, len(G["Dr"]["c"]) - 1]
    first_short = pd.Series(B["date"]).map(sh).to_numpy(dtype=float)
    allow = ~np.isnan(first_short) & (last1 >= np.nan_to_num(first_short, nan=1e18))
    o6 = np.zeros((len(B["c"]) // 3, 4))
    k = G["WB"].mseq_short_sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], allow, N, p["R"], p["sk"], int(p["ws"]), 945, 955, o6)
    eb = o6[:k, 1].astype(np.int64); fi = f1[eb]; e = D.o[fi] - SLIP; rk = o6[:k, 2]
    return mk(mod, fi, -np.ones(k), D.o[fi], 0, e + rk, e - p["R"] * rk, time_exit(D, fi, BIG, 1555))


def e_crt(mod, p):
    D, crt, crt2 = G["D"], G["crt"], G["crt2"]; off = int(p["off"])
    cid = (G["et_ep"] - off) // 60; mask = np.zeros(24, np.bool_); mask[(660 + off) // 60] = True; R = p["R"]
    o = np.zeros((len(crt.C) // 20 + 1000, 5))
    k = crt2.sim(crt.O, crt.H, crt.L, crt.C, crt.OM, crt.DAY, cid, crt.ATRD, crt.TREND, mask, 1, R, 0.0, p["mr"], 0.0, 0, 955, o)
    o = o[:k]; eb = o[:, 1].astype(np.int64); dd = o[:, 3].astype(np.int64); rk = o[:, 2]; e = D.o[eb] + dd * SLIP
    return mk(mod, eb, dd, D.o[eb], 0, e - dd * rk, e + dd * R * rk, time_exit(D, eb, BIG, 1555))


def e_ict(mod, p):
    D, B, f1 = G["D"], G["ictB"], G["f1"]; L, atr, trend = G["ictL"]; R = p["R"]
    out = np.zeros((len(B["c"]) // 10 + 1000, 8))
    k = G["WB"].ICT_SIM(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], L, np.ones(6, np.bool_), atr, trend, 570, int(p["we"]), 4, 2, R, 1, p["mr"], int(p["M"]), 3, 955, out)
    rows = []
    for r in out[:k]:
        eb = int(r[1]); dd = int(r[3]); plim = r[7]; sl = r[6]; a = f1[eb]; fi = -1
        for j in range(a, a + 5):
            if j >= len(D.c) or D.day[j] != D.day[a]: break
            if (dd == 1 and D.l[j] <= plim - TICK) or (dd == -1 and D.h[j] >= plim + TICK): fi = j; break
        if fi < 0: continue
        ent = min(plim, D.o[fi]) if dd == 1 else max(plim, D.o[fi]); rk = (ent - sl) * dd
        if rk <= 0: continue
        rows.append((fi, dd, ent, sl, ent + dd * R * rk))
    A = np.array(rows); fi = A[:, 0].astype(np.int64)
    return mk(mod, fi, A[:, 1], A[:, 2], 1, A[:, 3], A[:, 4], time_exit(D, fi, BIG, 1555))


def e_lon(mod, p):
    D, B = G["D"], G["lonB"]; atl, trl = G["lonA"]; R = p["R"]
    out = np.zeros((6000, 7))
    k = G["WB"].LON_SIM(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], atl, trl, 0, int(p["re"]), int(p["we"]), 480, 1, 2, R, p["mr"], 570, 1, out)
    o = out[:k]; eb = o[:, 1].astype(np.int64); dd = o[:, 3].astype(np.int64); e = o[:, 5]; sl = o[:, 6]; rk = (e - sl) * dd
    return mk(mod, eb, dd, e, 1, sl, e + dd * R * rk, time_exit(D, eb, BIG, 930))


def e_fam(mod, p, fam=None, maxday=1):
    D = G["D"]; gen = G["gens"][fam or SPEC[mod]["fam"]]
    F = fills_core(D, gen(D, p), flat=955, maxday=maxday)
    return mk(mod, F.fi, F.d, F.ent0, F.et, F.sl0, F.tp0, time_exit(D, F.fi.to_numpy(), F.hold.to_numpy(), 1555))


def e_vw13(mod, p):
    """two lots: VW13b at 0.15 x and VW13 at 0.30 x (both scaled by p['x'])."""
    q = dict(anc="VWAP", T=p["T"], x=0.30 * p["x"], mode=1, s=p["s"], R=p["R"], tg=0, tf=1, hold=120)
    a = e_fam("VW13", q, "CLOCK_ANCHOR"); q["x"] = 0.15 * p["x"]; b = e_fam("VW13b", q, "CLOCK_ANCHOR")
    return [a, b]


def entries(mod, p):
    kind = SPEC[mod]["kind"]
    if kind == "tmom": return e_tmom(mod, p)
    if kind == "orb": return e_orb(mod, p)
    if kind in ("mseq", "mseqs"): return e_mseq(mod, p)
    if kind == "crt": return e_crt(mod, p)
    if kind == "ict": return e_ict(mod, p)
    if kind == "lon": return e_lon(mod, p)
    if kind == "vw13": return e_vw13(mod, p)
    if kind == "fam": return e_fam(mod, p)
    raise ValueError(mod)


# ------------------------------------------------------------------------------------------------ exit engine + filters (= cand16 module_trades3)
def keep_mask(E, mod):
    D = G["D"]; fi = E.fi.to_numpy(); ok = np.ones(len(E), bool)
    if mod in STRUCT:
        ok &=((E.ent0 - E.sl0).abs().to_numpy() / D.atr[D.day[fi]] >= MINSTOP)
    if mod in ("ORB60", "ORB90"):
        rm = E.attrs.get("rm", 60 if mod == "ORB60" else 90)
        hi = np.full(D.nd, np.nan); lo = np.full(D.nd, np.nan); m = (D.om >= 570) & (D.om < 570 + rm)
        g = pd.DataFrame(dict(day=D.day[m], h=D.h[m], l=D.l[m])).groupby("day").agg(h=("h", "max"), l=("l", "min")); hi[g.index] = g.h; lo[g.index] = g.l
        day = D.day[fi]; s = E.d.to_numpy(); trig = np.where(s > 0, hi[day] + TICK, lo[day] - TICK); x = (trig - D.pdc[day]) * s / D.atr[day]
        ok &= ~np.nan_to_num(x < ORBT, nan=0).astype(bool)
    return ok


def wrq_trades(E, mod):
    """-> (real, norm) trade frames: date, mod, tin, tout, d, u, fi, atr, w"""
    D = G["D"]
    if len(E) == 0:
        empty = pd.DataFrame(dict(date=[], mod=[], tin=[], tout=[], d=[], u=[], fi=[], atr=[], w=[])); return empty, empty.copy()
    E = E[keep_mask(E, mod)]
    A = arrays(E); out = []
    for view in ("real", "norm"):
        u, ok, o = xsim_run(A, D, 0.0 if view == "norm" else G.get("slip", SLIP), EXIT_P.get(mod, {}), view == "norm")
        m = ok & (A["date"] >= 20100607) & (~A["fomc"])
        fi = A["fi"][m]; xi = o[m, 1].astype(np.int64)
        out.append(pd.DataFrame(dict(date=A["date"][m], mod=mod, tin=D.sm[fi], tout=D.sm[xi] + 1, d=A["d"][m], u=u[m], fi=fi, atr=D.atr[D.day[fi]], w=BASE_W.get(mod, 1.0))))
    return out


def ev_trades(mod, p):
    """mined modules through core.run_events (as six_build / ultra_q2): -> (real, norm)"""
    D = G["D"]; sp = SPEC[mod]; q = dict(p)
    if mod == "CAM3":
        H, L, C = D.L[:, 0], D.L[:, 3], D.pdc; LH, LL = C + (H - L) * q["camf"], C - (H - L) * q["camf"]
        from core import ev_from_lists
        ev = ev_from_lists(G["lfade"](D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, LH, LL, S(q["w0"]), S(q["w1"]), q["sweep"], int(q["conf"]), q["tg"], q["R"], q["tf"], q["hold"], D.vwap).tolist())
    elif mod == "RV11":
        q["cond"] = ("lo", q["lim"]); ev = G["gens"]["RVOL_DRIVE"](D, q)
    elif mod == "ORFAIL":
        q["T"] = int(q["T"]); ev = G["gens"]["OR_FAIL"](D, q)
    elif mod == "CPI09":
        q["T"] = int(q["T"]); ev = G["gens"]["G_DRIVE"](D, q)
        if len(ev["i"]):
            m = np.isin(D.date[ev["i"]], list(G["cpi"])); ev = {k: v[m] for k, v in ev.items()}
    else:
        ev = G["gens"][sp["fam"]](D, q)
    out = []
    for view in ("real", "norm"):
        df = run_events(D, ev, flat=955, maxday=sp["maxday"], slip=0.0 if view == "norm" else G.get("slip", SLIP), norm_cost=0.00345 if view == "norm" else None)
        if len(df) == 0:
            out.append(pd.DataFrame(dict(date=[], mod=[], tin=[], tout=[], d=[], u=[], fi=[], atr=[], w=[]))); continue
        fi = df.fi.to_numpy().astype(int); xi = df.xi.to_numpy().astype(int)
        T = pd.DataFrame(dict(date=df.date.to_numpy(), mod=mod, tin=D.sm[fi], tout=D.sm[xi] + 1, d=df.d.to_numpy().astype(np.int64), u=df.usd.to_numpy(), fi=fi, atr=D.atr[D.day[fi]], w=1.0))
        T = T[~T.date.isin(G["fomc"])]
        out.append(T.reset_index(drop=True))
    return out


def sim_module(mod, p):
    """-> (real, norm) trade frames of one module with parameter dict p."""
    if SPEC[mod]["kind"] == "ev": return ev_trades(mod, p)
    E = entries(mod, p)
    if isinstance(E, list):                       # VW13: two lots
        rs = [wrq_trades(e, e["mod"].iloc[0] if len(e) else "VW13") for e in E]
        return pd.concat([r[0] for r in rs], ignore_index=True), pd.concat([r[1] for r in rs], ignore_index=True)
    return wrq_trades(E, mod)


# ------------------------------------------------------------------------------------------------ portfolio assembly (= cand16 trades + six_build)
@njit(cache=True)
def _conflict(date, tin, tout, d):
    n = len(date); keep = np.zeros(n, np.bool_); ko = np.zeros(n, np.int64); kd = np.zeros(n, np.int64); i = 0
    while i < n:
        j = i
        while j < n and date[j] == date[i]: j += 1
        m = 0
        for a in range(i, j):
            blocked = False
            for b in range(m):
                if ko[b] > tin[a] and kd[b] == -d[a]: blocked = True; break
            if not blocked:
                keep[a] = True; ko[m] = tout[a]; kd[m] = d[a]; m += 1
        i = j
    return keep


@njit(cache=True)
def _nsame(date, tin, tout, d, mc):
    n = len(date); out = np.zeros(n, np.int64); i = 0
    while i < n:
        j = i
        while j < n and date[j] == date[i]: j += 1
        for a in range(i, j):
            cnt = 0
            for b in range(i, j):
                if b != a and tin[b] < tin[a] and tout[b] > tin[a] and mc[b] != mc[a] and d[b] == d[a]: cnt += 1
            out[a] = cnt
        i = j
    return out


def conflict_filter(X):
    X = X.sort_values(["date", "tin"], kind="stable").reset_index(drop=True)
    k = _conflict(X.date.to_numpy(np.int64), X.tin.to_numpy(np.int64), X.tout.to_numpy(np.int64), X.d.to_numpy(np.int64))
    return X[k].reset_index(drop=True)


def feats_for(X):
    """context features (filt_feats) for rows of X, cached by (date, tin, d)."""
    import filt_feats
    keys = list(zip(X.date.to_numpy(), X.tin.to_numpy(), X.d.to_numpy())); C = G["fcache"]
    miss = [i for i, k in enumerate(keys) if k not in C]
    if miss:
        F = filt_feats.feats(G["D"], X.iloc[miss][["date", "mod", "tin", "d"]].reset_index(drop=True))
        cols = ["vw", "open", "rng", "pos", "trend", "gap", "pdret", "m30", "ret5", "atr", "pd", "svw"]
        for k, row in zip([keys[i] for i in miss], F[cols].to_numpy()): C[k] = row
    cols = ["vw", "open", "rng", "pos", "trend", "gap", "pdret", "m30", "ret5", "atr", "pd", "svw"]
    return pd.DataFrame(np.array([C[k] for k in keys]).reshape(len(keys), 12), columns=cols, index=X.index)


def apply_rules(X):
    X = X.sort_values(["date", "tin"], kind="stable").reset_index(drop=True)
    m11 = X[X["mod"] == "MOM11"].groupby("date").d.first()
    on = X[X["mod"].isin(["ON07", "REV06", "LON"])].groupby("date").d.agg(lambda s: np.sign(s.sum()))
    A = X["mod"].isin(LATE) & (X.date.map(m11) * X.d == -1) & (X.date.map(on) * X.d == 1) & (X.tin > S(1100))
    lon = X[X["mod"] == "LON"].set_index("date"); lon_d = lon.d[~lon.index.duplicated()]; lon_t = lon.tin[~lon.index.duplicated()]
    Bskip = (X["mod"] == "REV06") & (X.date.map(lon_d) == X.d) & (X.date.map(lon_t) <= X.tin)
    b = pd.Series(1.0, index=X.index); keep = ~Bskip
    rmods = {r["mod"] for r, _ in G["sel"]}; sub = X[X["mod"].isin(rmods)]
    if len(sub):
        F = feats_for(sub)
        for r, k in G["sel"]:
            x = F[r["feat"]]; mm = ((sub["mod"] == r["mod"]) & ((x < r["hi"]) if r["bucket"].startswith("low") else (x >= r["lo"]))).fillna(False)
            idx = sub.index[mm.to_numpy()]
            if k == "boost": b[idx] = 2.0
            else: keep[idx] = False
    bw = X.w.copy(); w = bw * np.where(A, 2.0, 1.0) * b
    X["w"] = np.minimum(w, np.maximum(bw, 2.0))
    return X[keep].reset_index(drop=True)


def assemble(parts, view, drop=()):
    """parts: {mod: (real, norm)}; -> portfolio trade frame of one view (date, mod, tin, tout, d, u, w, fi, atr)."""
    vi = 0 if view == "real" else 1
    wp = [parts[m][vi] for m in WRQ if m in parts and m not in drop]
    X0 = conflict_filter(pd.concat(wp, ignore_index=True))
    mc = pd.factorize(X0["mod"])[0]
    ns = _nsame(X0.date.to_numpy(np.int64), X0.tin.to_numpy(np.int64), X0.tout.to_numpy(np.int64), X0.d.to_numpy(np.int64), mc)
    dropped = X0[(ns == 0) & X0["mod"].isin(["MOM1030", "MOM13"])]
    X = pd.concat(wp, ignore_index=True)
    if len(dropped):
        key = pd.MultiIndex.from_frame(X[["date", "mod", "tin"]]); dk = pd.MultiIndex.from_frame(dropped[["date", "mod", "tin"]])
        X = X[~key.isin(dk)]
    X = apply_rules(conflict_filter(X))
    if view == "real": X = X[X.atr >= MIN_ATR]
    ev = [parts[m][vi] for m in MODS if m in parts and SPEC[m]["kind"] == "ev" and m not in drop]
    if ev:
        E = pd.concat(ev, ignore_index=True)
        E = E[E.date.isin(G["days_real"] if view == "real" else G["days_norm"])]
        X = pd.concat([X, E], ignore_index=True)
    X = conflict_filter(X)
    X.loc[X["mod"].isin(X4), "w"] = 4.0
    return X


# ------------------------------------------------------------------------------------------------ metrics
def days_of(per):
    lo, hi, view = PERIODS[per]; dd = G["days_real"] if view == "real" else G["days_norm"]
    return dd[(dd >= lo) & (dd < hi)]


def metrics(X, per, weighted=True, extra=0.0):
    lo, hi, view = PERIODS[per]; s = X[(X.date >= lo) & (X.date < hi)]; dd = days_of(per)
    if len(s) == 0: return dict(n=0, tpd=0.0, wr=np.nan, pf=np.nan, sharpe=np.nan, maxdd=np.nan, net=0.0, worst_month=np.nan)
    w = s.w.to_numpy() if weighted else np.ones(len(s)); x = (s.u.to_numpy() - extra) * w
    d = pd.Series(x, index=s.date.to_numpy()).groupby(level=0).sum().reindex(dd, fill_value=0.0); eq = d.cumsum()
    mo = d.groupby(d.index // 100).sum(); lo_ = -x[x <= 0].sum()
    return dict(n=int(len(s)), tpd=round(len(s) / max(len(dd), 1), 3), wr=round(100 * float((s.u > 0).mean()), 2), pf=round(float(x[x > 0].sum() / lo_), 4) if lo_ > 0 else np.nan,
                sharpe=round(float(d.mean() / d.std() * np.sqrt(252)), 3) if d.std() > 0 else 0.0, maxdd=round(float((eq.cummax() - eq).max()), 1),
                net=round(float(x.sum()), 1), worst_month=round(float(mo.min()), 1))


def module_metrics(tr):
    """standalone, unweighted, per period (real frame for T1/T2, norm frame for A/B)."""
    real, norm = tr; out = {}
    for per, (lo, hi, view) in PERIODS.items():
        X = real if view == "real" else norm
        if view == "real": X = X[X.atr >= MIN_ATR]
        out[per] = metrics(X, per, weighted=False)
    return out


def port_metrics(parts, drop=(), extra=0.0):
    out = {}
    for view in ("real", "norm"):
        X = assemble(parts, view, drop)
        for per, (lo, hi, v) in PERIODS.items():
            if v == view: out[per] = metrics(X, per, extra=extra if view == "real" else 0.0)
    return out


def compact(tr):
    """store a (real, norm) pair compactly"""
    cols = ["date", "mod", "tin", "tout", "d", "u", "fi", "atr", "w"]
    return tuple(t[cols].reset_index(drop=True) for t in tr)
