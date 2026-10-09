"""wrq_build: entry specs for every NQMaster NQ module (Ultra / WR70Plus) on nq_1m (IS + C24), mnq_fut (REAL) and
nqhd_long (2015-19 regime test), re-using the ORIGINAL research simulators for the signal logic:
  tmom.py (MOM11 + VWAP-agree, MOM1030, MOM13, ON07, REV06), nt_v3_replica.py (ORB60 / ORB90 on pullback days < 0.44),
  wr60.py (MSEQ, 5m), own mirror of wr60 (MSEQS, only after an ORB60 short), crt2.py (CRT11), ict_fix.py (ICT, corrected,
  patched to also return entry / stop / limit), london.py (LON, patched to return entry / stop), core families
  (VW13 x0.30, VW13b x0.15, VOLB tf0 R2, VOLB_tf1 R0.5, LATE15, LATEFH, ENG10, NF05, LF06, LF0430).
5-minute modules (MSEQ, MSEQS, ICT) are mapped to the 1-minute fill bar so all exits are re-simulated on 1m bars.
Output: wrq_entries.pkl {dataset: DataFrame}.  Run: cd research/mine && python3 wrq_build.py"""
import os, sys, ast, importlib, pickle, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_lib import RES, getD, time_exit, fills_core, SLIP, TICK, S
from families import FAMILIES
from families2 import FAMILIES2
from families3 import FAMILIES3
from families4 import FAMILIES4
from families_gold import gen_drive
BIG = 10 ** 7


def _reload(mod, data):
    os.environ["NQ_DATA"] = data; cwd = os.getcwd(); os.chdir(RES)
    try:
        m = importlib.import_module(mod); m = importlib.reload(m)
    finally:
        os.chdir(cwd)
    return m


def raw(name):
    z = np.load(os.path.join(RES, "data", name)); return {k: z[k] for k in z.files}


def patched(path, reps, extra_ns):
    src = open(os.path.join(RES, path)).read()
    a = src.index("@njit(cache=True)\ndef sim("); b = src.index("\ndef ", a + 30)
    f = src[a:b].replace("@njit(cache=True)", "@njit")
    for x, y in reps:
        assert x in f, (path, x); f = f.replace(x, y)
    ns = dict(np=np, njit=njit, TICK=0.25, SLIP=0.25); ns.update(extra_ns); exec(f, ns); return ns["sim"]


ICT_SIM = patched("ict_fix.py", [("out[k, 4] = i; k += 1; pos = 0", "out[k, 4] = i; out[k, 5] = entry; out[k, 6] = sl; out[k, 7] = plim; k += 1; pos = 0")], {})
LON_SIM = patched("london.py", [("out[k, 4] = min(q, nxt - 1); k += 1", "out[k, 4] = min(q, nxt - 1); out[k, 5] = entry; out[k, 6] = stop; k += 1")], {})


def first_1m_of_5m(Dr):
    g = Dr["epoch"] // 5
    df = pd.DataFrame(dict(day=Dr["dayid"], g=g, i=np.arange(len(g))))
    return df.groupby(["day", "g"], sort=True).i.first().to_numpy()


def mk(D, mod, fi, d, ent0, et, sl0, tp0, tx, u0):
    fi = np.asarray(fi, np.int64)
    return pd.DataFrame(dict(date=D.date[fi], mod=mod, fi=fi, d=np.asarray(d, np.int64), ent0=np.asarray(ent0, float), et=np.asarray(et, np.int64) * np.ones(len(fi), np.int64),
                             sl0=np.asarray(sl0, float), tp0=np.asarray(tp0, float), tx=np.asarray(tx, np.int64), u0=np.asarray(u0, float)))


# ---------------------------------------------------------------------------------------------- per-module builders
def b_tmom(name, D, Dr):
    import tmom, ict
    X = ict.day_levels(Dr); out = []
    spec = {"MOM11": (660, -2, 0, 0.25, 0.3, 100000, 0), "MOM1030": (630, -2, 0, 0.2, 0.3, 60, 1), "MOM13": (780, -2, 0, 0.2, 1.0, 240, 1),
            "ON07": (420, 30, 0, 0.2, 1.0, 60, 1), "REV06": (360, 30, 1, 0.2, 0.3, 240, 1)}
    # MOM11 VWAP agreement (mom11_feat.py): sign(close 10:59 - VWAP 09:30-10:59) == sign(close 10:59 - open 09:30)
    om, c, o, h, l, v = Dr["om"], Dr["c"], Dr["o"], Dr["h"], Dr["l"], np.maximum(Dr["v"].astype(float), 1e-9)
    rth = (om >= 570) & (om < 660)
    g = pd.DataFrame(dict(date=Dr["date"][rth], o=o[rth], c=c[rth], tp=(h[rth] + l[rth] + c[rth]) / 3 * v[rth], v=v[rth]))
    a = g.groupby("date").agg(o=("o", "first"), c=("c", "last"), tp=("tp", "sum"), v=("v", "sum"))
    agree = (np.sign(a.c - a.tp / a.v) == np.sign(a.c - a.o))
    for nm, (t, L, rev, sk, R, H, tf) in spec.items():
        df = tmom.run(Dr, X, t, L, rev, sk, R, H, tf)
        if nm == "MOM11":             # VWAP agreement + full session (timefill.py skipped early-close / holiday sessions)
            full = np.array([D.om[D.de[D.day[b]]] >= 955 and D.om[D.de[D.day[b]]] < 1080 for b in df.bi.to_numpy()], bool)
            df = df[df.date.map(agree).fillna(False).astype(bool).to_numpy() & full]
        bi = df.bi.to_numpy(); dd = df.d.to_numpy(); e = D.o[bi] + dd * SLIP; rk = df.risk.to_numpy()
        out.append(mk(D, nm, bi, dd, D.o[bi], 0, e - dd * rk, e + dd * R * rk, time_exit(D, bi, H, 1555), df.pts * 2 - 1.9))
    return out


def b_orb(name, D, Dr):
    os.environ["NQ_DATA"] = name
    cwd = os.getcwd(); os.chdir(RES)
    try:
        import common; importlib.reload(common); import nt_v3_replica as r3
        from nt_v2_replica import daily_stats
        cx = common.Ctx()
    finally:
        os.chdir(cwd)
    A, T, _ = daily_stats(cx)
    PR = {cx.dates[dd]: (cx.prev_close[dd] - cx.prev_close[dd - 1]) / A[dd] * T[dd] for dd in range(2, cx.nd) if A[dd] > 0}
    base = dict(contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=0.35, vw_stop=0.35)
    out = []
    for nm, rm, t1 in (("ORB60", 60, 0.6), ("ORB90", 90, 0.6)):
        df = r3.run(cx, t1_r=t1, use_vwap=False, range_min=rm, entry_start=max(630, 570 + rm), **base)
        df = df[df.date.map(PR) < 0.44]
        fi = df.entry_idx.to_numpy(); dd = df.dir.to_numpy(); e = df.entry.to_numpy(); rk = df.risk_pts.to_numpy()
        pts = (df.usd.to_numpy() + 1.0) / 2.0
        out.append(mk(D, nm, fi, dd, e - dd * SLIP, 0, e - dd * rk, e + dd * t1 * rk, time_exit(D, fi, BIG, 1555), pts * 2 - 1.9))
    return out


@njit(cache=True)
def mseq_short_sim(o, h, l, c, om, day, allow, N, R, stop_k, win_s, win_e, flat, out):
    """Mirror of wr60.sim for shorts (bull main candle + N falling bear candles below its high)."""
    n = len(c); pos = 0; k = 0; entry = 0.0; sl = 0.0; tp = 0.0; eb = 0; pend = False; psl = 0.0; risk = 0.0
    for i in range(N + 1, n):
        if pend:
            pend = False
            if day[i] == day[i - 1] and om[i] < flat:
                entry = o[i] - 0.25; risk = psl - entry
                if risk > 0:
                    pos = -1; sl = psl; tp = entry - R * risk; eb = i
        if pos == -1:
            ex = 0.0; done = False
            if o[i] >= sl and i > eb: ex = o[i] + 0.25; done = True
            elif h[i] >= sl: ex = sl + 0.25; done = True
            elif i > eb and l[i] <= tp - 0.25: ex = min(o[i], tp); done = True
            elif day[i] != day[eb] or om[i] >= flat: ex = c[i] + 0.25; done = True
            if done:
                out[k, 0] = entry - ex; out[k, 1] = eb; out[k, 2] = risk; out[k, 3] = i; k += 1; pos = 0
        if pos == 0 and not pend and allow[i] and om[i] >= win_s and om[i] < win_e:
            m = i - N
            if c[m] > o[m] and day[m] == day[i]:
                ok = True
                for j in range(N):
                    b = i - j
                    if c[b] >= o[b] or h[b] >= h[m]:
                        ok = False; break
                    if j < N - 1 and c[b] >= c[b - 1]:
                        ok = False; break
                if ok:
                    dist = (h[m] - c[i]) * stop_k
                    if dist > 0:
                        pend = True; psl = c[i] + dist
    return k


def b_mseq(name, D, Dr, orb60):
    w = _reload("wr60", name)
    B = w.build(5); f1 = first_1m_of_5m(Dr); assert len(f1) == len(B["c"])
    out = []
    o5 = np.zeros((len(B["c"]) // 3, 4))
    k = w.sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], B["up20"], 5, 0.5, 1.75, 0.0, 0, 630, 945, 955, 0.0, o5)
    eb = o5[:k, 1].astype(np.int64); fi = f1[eb]; e = D.o[fi] + SLIP; rk = o5[:k, 2]
    out.append(mk(D, "MSEQ", fi, np.ones(k), D.o[fi], 0, e - rk, e + 0.5 * rk, time_exit(D, fi, BIG, 1555), o5[:k, 0] * 2 - 1.9))
    # MSEQS: allowed on 5m bars whose last 1m bar is at/after an ORB60 SHORT fill of the same day
    sh = orb60[orb60.d == -1].groupby("date").fi.min()
    last1 = np.r_[f1[1:] - 1, len(Dr["c"]) - 1]
    first_short = pd.Series(B["date"]).map(sh).to_numpy(dtype=float)
    allow = ~np.isnan(first_short) & (last1 >= np.nan_to_num(first_short, nan=1e18))
    o6 = np.zeros((len(B["c"]) // 3, 4))
    k = mseq_short_sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], allow, 5, 0.75, 1.75, 630, 945, 955, o6)
    eb = o6[:k, 1].astype(np.int64); fi = f1[eb]; e = D.o[fi] - SLIP; rk = o6[:k, 2]
    out.append(mk(D, "MSEQS", fi, -np.ones(k), D.o[fi], 0, e + rk, e - 0.75 * rk, time_exit(D, fi, BIG, 1555), o6[:k, 0] * 2 - 1.9))
    return out


def b_crt(name, D, Dr):
    crt = _reload("crt", name); crt2 = _reload("crt2", name)
    cid, _ = crt.candle_ids(60); mask = np.zeros(24, np.bool_); mask[11] = True; R = 2.0
    o = np.zeros((len(crt.C) // 20 + 1000, 5))
    k = crt2.sim(crt.O, crt.H, crt.L, crt.C, crt.OM, crt.DAY, cid, crt.ATRD, crt.TREND, mask, 1, R, 0.0, 0.5, 0.0, 0, 955, o)
    o = o[:k]; eb = o[:, 1].astype(np.int64); dd = o[:, 3].astype(np.int64); rk = o[:, 2]; e = D.o[eb] + dd * SLIP
    return [mk(D, "CRT11", eb, dd, D.o[eb], 0, e - dd * rk, e + dd * R * rk, time_exit(D, eb, BIG, 1555), o[:, 0] * 2 - 1.9)]


def b_ict(name, D, Dr):
    os.chdir(RES)
    import ict_fix
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    B = ict_fix.bars(Dr, 5); L, atr, trend = ict_fix.day_levels(Dr); f1 = first_1m_of_5m(Dr); assert len(f1) == len(B["c"])
    R = 1.0; out = np.zeros((len(B["c"]) // 10 + 1000, 8))
    k = ICT_SIM(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], L, np.ones(6, np.bool_), atr, trend, 570, 630, 4, 2, R, 1, 0.25, 20, 3, 955, out)
    o = out[:k]; rows = []
    for r in o:
        eb = int(r[1]); dd = int(r[3]); plim = r[7]; sl = r[6]; a = f1[eb]; fi = -1
        for j in range(a, a + 5):
            if j >= len(D.c) or D.day[j] != D.day[a]: break
            if (dd == 1 and D.l[j] <= plim - TICK) or (dd == -1 and D.h[j] >= plim + TICK): fi = j; break
        if fi < 0: continue
        ent = min(plim, D.o[fi]) if dd == 1 else max(plim, D.o[fi]); rk = (ent - sl) * dd
        if rk <= 0: continue
        rows.append((fi, dd, ent, sl, ent + dd * R * rk, r[0] * 2 - 1.9))
    A = np.array(rows); fi = A[:, 0].astype(np.int64)
    return [mk(D, "ICT", fi, A[:, 1], A[:, 2], 1, A[:, 3], A[:, 4], time_exit(D, fi, BIG, 1555), A[:, 5])]


def b_lon(name, D, Dr):
    import london
    B = london.bars(Dr, 1); _, atl, trl = london.day_levels(Dr); R = 2.0
    out = np.zeros((4000, 7))
    k = LON_SIM(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], atl, trl, 0, 180, 360, 480, 1, 2, R, 0.25, 570, 1, out)
    o = out[:k]; eb = o[:, 1].astype(np.int64); dd = o[:, 3].astype(np.int64); e = o[:, 5]; sl = o[:, 6]; rk = (e - sl) * dd
    return [mk(D, "LON", eb, dd, e, 1, sl, e + dd * R * rk, time_exit(D, eb, BIG, 930), o[:, 0] * 2 - 1.9)]


FAM = {"VW13": ("CLOCK_ANCHOR", dict(anc="VWAP", T=1300, x=0.3, mode=1, s=0.15, R=0.5, tg=0, tf=1, hold=120)),
       "VW13b": ("CLOCK_ANCHOR", dict(anc="VWAP", T=1300, x=0.15, mode=1, s=0.15, R=0.5, tg=0, tf=1, hold=120)),
       "VOLB": ("VOL_BREAK", dict(k=0.45, s=0.35, R=2.0, tf=0, w1=1500, hold=400, stop=0)),
       "VOLB_tf1": ("VOL_BREAK", dict(k=0.45, s=0.35, R=0.5, tf=1, w1=1500, hold=400, stop=0)),
       "LATE15": ("LATE_MOM", 762), "LATEFH": ("LATE_MOM", 1107), "ENG10": ("ENGULF_4H", 1172),
       "NF05": ("G_DRIVE", dict(A=2000, T=540, x=0.35, mode=-1, tf=0, k=0.2, stop=0, R=2.0, hold=240)),
       "LF06": ("G_DRIVE", dict(A=400, T=120, x=0.2, mode=-1, tf=0, k=0.2, stop=0, R=0.5, hold=240)),
       "LF0430": ("G_DRIVE", dict(A=400, T=30, x=0.1, mode=-1, tf=1, k=0.35, stop=0, R=0.5, hold=240))}
ALLF = {**FAMILIES, **FAMILIES2, **FAMILIES3, **FAMILIES4, "G_DRIVE": (gen_drive, None, 1)}


def b_fam(name, D, Dr):
    out = []
    for nm, (fam, p) in FAM.items():
        gen, grid, md = ALLF[fam]
        if isinstance(p, int): p = grid[p]
        F = fills_core(D, gen(D, p), flat=955, maxday=md)
        out.append(mk(D, nm, F.fi, F.d, F.ent0, F.et, F.sl0, F.tp0, time_exit(D, F.fi.to_numpy(), F.hold.to_numpy(), 1555), F.pts * 2 - 1.9))
    return out


def build(name):
    D = getD(name); Dr = raw(name); parts = []
    for f in (b_tmom, b_orb, b_crt, b_ict, b_lon, b_fam):
        parts += f(name, D, Dr); print(name, f.__name__, "done", flush=True)
    orb60 = [p for p in parts if (p["mod"] == "ORB60").all()][0]
    parts += b_mseq(name, D, Dr, orb60); print(name, "mseq done", flush=True)
    E = pd.concat(parts, ignore_index=True)
    sys.path.insert(0, RES); from news import NEWS
    E["fomc"] = E.date.isin(NEWS["FOMC"]); E["tin"] = D.sm[E.fi.to_numpy()]
    return E.sort_values(["mod", "fi"]).reset_index(drop=True)


if __name__ == "__main__":
    OUT = {}
    for name in ("nq_1m.npz", "mnq_fut.npz", "nqhd_long.npz"):
        OUT[name] = build(name); print(name, OUT[name].groupby("mod").size().to_dict(), flush=True)
    pickle.dump(OUT, open("wrq_entries.pkl", "wb"))
