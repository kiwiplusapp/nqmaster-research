"""Batch 10 (2026-10-19, 'more trades at the same quality' round):
VWAP_BAND2 : NEW ingredient. Session (18:00-anchored) VWAP +- m x sigma, sigma = sqrt(volume-weighted variance of the typical price),
             both computed from the bars BEFORE the signal bar (bands at bar t use bars <= t-1 only; see lookahead_check()).
             mode 'fade2' / 'fade3': close beyond the 2nd / 3rd band -> fade toward the VWAP (tg 0 = VWAP target, tg 1 = R x stop);
             mode 'mom1': close crosses from inside the 1st band to outside it -> momentum in that direction, target R x stop.
             Stop s x daily ATR, daily-trend filter tf (1 with, 0 any, -1 against), window w0-w1 ET, hold minutes, max 2 signals per day,
             30 minutes between signals.
OR_FAIL_X  : the failed opening-range breakout family (families5._orfail) on 5- and 10-minute opening ranges (the mined grid had 15/30/60).
PIVOT_FADE_X: the Camarilla fade (families2 pivots) at the L2/H2 (1.1/6) and L4/H4 (1.1/2) levels (the mined grid had CAM3 = 1.1/4 only)."""
import numpy as np
from numba import njit
from core import S, TICK, ev_from_lists
from families import grid, _lfade
from families5 import _orfail, TG

MODES = {"fade2": (0, 2.0), "fade3": (0, 3.0), "mom1": (1, 1.0)}


@njit(cache=True)
def _vwb2(o, h, l, c, v, sm, ds, de, atr, trend, w0, w1, mode, m, s_k, tg, R, tf, hold, maxn, dbg):
    out = np.zeros((maxn * len(ds), 8)); k = 0
    for d in range(len(ds)):
        if ds[d] < 0 or atr[d] <= 0: continue
        a = atr[d]; spv = 0.0; svv = 0.0; sp2 = 0.0; nn = 0; last = -100; prev_in = False; have_prev = False
        for i in range(ds[d], de[d] + 1):
            # bands from the bars before i (sums exclude bar i)
            vw = np.nan; sd = np.nan
            if svv > 0:
                vw = spv / svv; var = sp2 / svv - vw * vw
                sd = np.sqrt(var) if var > 0 else 0.0
            inside = False
            if not np.isnan(vw) and sd > 0:
                inside = abs(c[i] - vw) < 1.0 * sd
            fire = False; side = 0
            if sm[i] >= w0 and sm[i] < w1 and nn < maxn and i - last >= 30 and not np.isnan(vw) and sd > 0:
                if mode == 0:
                    if c[i] > vw + m * sd: side = -1
                    elif c[i] < vw - m * sd: side = 1
                else:
                    if have_prev and prev_in:
                        if c[i] > vw + m * sd: side = 1
                        elif c[i] < vw - m * sd: side = -1
                if side != 0:
                    if tf == 1 and side != trend[d]: side = 0
                    elif tf == -1 and side == trend[d]: side = 0
                if side != 0:
                    sl = c[i] - side * s_k * a
                    if mode == 0 and tg == 0: tp = vw
                    else: tp = c[i] + side * R * s_k * a
                    if (tp - c[i]) * side > TICK:
                        out[k, 0] = i; out[k, 1] = side; out[k, 2] = 0; out[k, 3] = c[i]; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = i; out[k, 7] = hold
                        dbg[k, 0] = vw; dbg[k, 1] = sd; k += 1; nn += 1; last = i; fire = True
            # now add bar i to the session sums
            tp_i = (h[i] + l[i] + c[i]) / 3.0
            spv += tp_i * v[i]; svv += v[i]; sp2 += tp_i * tp_i * v[i]
            prev_in = inside; have_prev = not np.isnan(vw) and sd > 0
    return out[:k], dbg[:k]


def vwb2_raw(D, p):
    mode, m = MODES[p["mode"]]
    dbg = np.zeros((2 * D.nd, 2))
    return _vwb2(D.o, D.h, D.l, D.c, D.v, D.sm, D.ds, D.de, D.atr.astype(np.float64), D.trend, S(p["w0"]), S(p["w1"]), mode, m, p["s"], p["tg"], p["R"], p["tf"], p["hold"], 2, dbg)


def gen_vwb2(D, p):
    ev, _ = vwb2_raw(D, p)
    return ev_from_lists(ev.tolist())


def lookahead_check(D, p):
    """Recompute the session VWAP / sigma at every signal bar from the bars strictly before it (numpy, cumulative sums shifted by one bar) and
    compare with the values the generator used. Returns (n_events, max_abs_diff_vwap, max_abs_diff_sigma, n_violations)."""
    ev, dbg = vwb2_raw(D, p)
    if len(ev) == 0: return 0, 0.0, 0.0, 0
    i = ev[:, 0].astype(np.int64)
    tp = (D.h + D.l + D.c) / 3.0
    import pandas as pd
    g = pd.Series(D.day)
    cpv = (tp * D.v); cvv = D.v.copy(); cp2 = (tp * tp * D.v)
    cpv = pd.Series(cpv).groupby(g).cumsum().shift(1).to_numpy().copy(); cvv = pd.Series(cvv).groupby(g).cumsum().shift(1).to_numpy().copy(); cp2 = pd.Series(cp2).groupby(g).cumsum().shift(1).to_numpy().copy()
    first = (D.ds[D.day] == np.arange(D.n)); cpv[first] = 0.0; cvv[first] = 0.0; cp2[first] = 0.0
    vw = cpv[i] / cvv[i]; var = cp2[i] / cvv[i] - vw * vw; sd = np.sqrt(np.maximum(var, 0))
    dv = np.abs(vw - dbg[:, 0]); dsd = np.abs(sd - dbg[:, 1])
    # perturbation test: changing the signal bar's own volume and prices must not change the bands the generator used
    D2 = type("X", (), {})();
    for kname in ("o", "h", "l", "c", "v", "sm", "ds", "de", "atr", "trend", "nd"): setattr(D2, kname, getattr(D, kname))
    D2.v = D.v.copy(); D2.v[i] = D.v[i] * 7.0 + 123.0; D2.h = D.h.copy(); D2.h[i] = D.h[i] + 50.0
    ev2, dbg2 = vwb2_raw(D2, p)
    # the perturbed bar changes the sums AFTER it, so later signals of the same day may legitimately move; the signal bar itself must keep
    # its bands (and must still fire): compare on the common bars, which must include every first signal of a day
    m2 = {int(b): (dbg2[j, 0], dbg2[j, 1]) for j, b in enumerate(ev2[:, 0])}
    firstday = np.r_[True, D.day[i[1:]] != D.day[i[:-1]]]
    missing = int(sum(1 for j, b in enumerate(i) if firstday[j] and int(b) not in m2))
    bad = int(sum(1 for j, b in enumerate(i) if firstday[j] and int(b) in m2 and (abs(m2[int(b)][0] - dbg[j, 0]) > 1e-6 or abs(m2[int(b)][1] - dbg[j, 1]) > 1e-6)))
    viol = int((dv > 1e-6).sum() + (dsd > 1e-6).sum()) + missing + bad
    return int(len(ev)), float(dv.max()), float(dsd.max()), viol


GRID_VWB2 = ([dict(mode=md, w0=w0, w1=w1, s=s, tg=0, R=1.0, tf=tf, hold=hd) for md in ("fade2", "fade3") for w0 in (1000, 1100) for w1 in (1300, 1500)
              for s in (0.15, 0.25) for tf in (0, 1, -1) for hd in (120, 240)] +
             [dict(mode=md, w0=w0, w1=w1, s=s, tg=1, R=R, tf=tf, hold=hd) for md in ("fade2", "fade3", "mom1") for w0 in (1000, 1100) for w1 in (1300, 1500)
              for s in (0.15, 0.25) for R in (0.5, 1.0, 2.0) for tf in (0, 1, -1) for hd in (120, 240)])


def gen_orfail_x(D, p):
    return ev_from_lists(_orfail(D.o, D.h, D.l, D.c, D.sm, D.ro, D.de, D.atr, D.trend, p["T"], S(p["w1"]), p["bk"], p["tfb"], TG[p["tg"]], p["tf"]).tolist())


GRID_ORFAIL_X = grid(T=(5, 10), w1=(1200, 1400), bk=(0.0, 0.05, 0.1), tfb=(1, 5), tg=tuple(TG), tf=(0, 1, -1))


def pivots_x(D, kind):
    H, L, C = D.L[:, 0], D.L[:, 3], D.pdc
    if kind == "CAM2": return C + (H - L) * 1.1 / 6, C - (H - L) * 1.1 / 6
    if kind == "CAM4": return C + (H - L) * 1.1 / 2, C - (H - L) * 1.1 / 2
    raise ValueError(kind)


def gen_pivfade_x(D, p):
    LH, LL = pivots_x(D, p["piv"])
    return ev_from_lists(_lfade(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, LH, LL, S(p["w0"]), S(p["w1"]), p["sweep"], p["conf"], p["tg"], p["R"], p["tf"], p["hold"], D.vwap).tolist())


GRID_PIVFADE_X = grid(piv=("CAM2", "CAM4"), w0=(930, 1000), w1=(1300, 1530), sweep=(0.0, 0.03), conf=(3, 10), tg=(0, 1), R=(1.0, 2.0), tf=(0, 1), hold=(240,))

FAMILIES10 = {"VWAP_BAND2": (gen_vwb2, GRID_VWB2, 2), "OR_FAIL_X": (gen_orfail_x, GRID_ORFAIL_X, 1), "PIVOT_FADE_X": (gen_pivfade_x, GRID_PIVFADE_X, 2)}
