"""Batch 7 (2026-10-16, six-year round on real Databento NQ futures): five families never mined before.
  SQZ_BOX     time-of-day-normalised volatility squeeze: range of the last N minutes (box) vs the median range of the SAME
              clock slot over the prior 20 sessions; ratio <= q -> OCO stop orders 1 tick beyond the box for E minutes
              (when both sides are hit inside one 1m bar the side nearer the bar open is taken = the order a real OCO
              would most likely fill; the stop is checked inside that same bar by core.execute). Up to 2 setups a day.
  PD_ACCEPT   prior-day structure acceptance: K consecutive 5-minute RTH closes beyond the prior complete RTH high / low
              (+bk ATR), with the RTH open inside / outside that level -> continuation (market at the next bar).
  ER_PERSIST  intraday trend-strength persistence: at a checkpoint T, Kaufman efficiency ratio of the RTH path so far
              (|close - RTH open| / sum |5m close changes|); high ER -> continuation, low ER -> reversion.
  ON_POS      overnight-range position: where price sits at 09:29 / 09:44 / 09:59 inside the 18:00-09:29 range;
              near one end -> trade toward the far end (fade) or out of the range (continuation).
  PERIOD_OPEN weekly / monthly open price (open of the first Globex session of the week / month): first RTH touch ->
              resting limit bounce, or stop-entry break through the level.
All signals use bars up to the signal bar; entries from the next bar (core.execute, $1.90 + 1 tick per side)."""
import numpy as np, pandas as pd
from numba import njit
from core import S, TICK, ev_from_lists
from families import grid, idx_at
from families5 import _daily

STEP = 15                        # squeeze slot step (minutes)


# ---------------------------------------------------------------- SQZ_BOX
@njit(cache=True)
def _boxes(h, l, sm, ds, de, N, step):
    nd = len(ds); ns = 1440 // step
    BH = np.full((nd, ns), np.nan); BL = np.full((nd, ns), np.nan); BE = np.full((nd, ns), -1)
    for d in range(nd):
        if ds[d] < 0: continue
        i0 = ds[d]
        for k in range(ns):
            t = k * step
            if t - N < 0: continue
            while i0 <= de[d] and sm[i0] < t - N: i0 += 1
            hi = -1e18; lo = 1e18; cnt = 0; i = i0
            while i <= de[d] and sm[i] < t:
                if h[i] > hi: hi = h[i]
                if l[i] < lo: lo = l[i]
                cnt += 1; i += 1
            if cnt < 0.8 * N: continue
            if i > de[d] or sm[i] >= t + step: continue          # need the bar at t (first bar after the box)
            BH[d, k] = hi; BL[d, k] = lo; BE[d, k] = i
    return BH, BL, BE


def _sqz_feat(D, N):
    key = f"_sqz{N}"
    if hasattr(D, key): return getattr(D, key)
    BH, BL, BE = _boxes(D.h, D.l, D.sm, D.ds, D.de, N, STEP)
    R = BH - BL
    med = pd.DataFrame(R).rolling(20, min_periods=10).median().shift(1).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = R / med
    out = (BH, BL, BE, np.where(np.isfinite(ratio), ratio, np.inf))
    setattr(D, key, out); return out


@njit(cache=True)
def _sqz(o, h, l, c, sm, de, atr, trend, BH, BL, BE, ratio, k0, k1, q, stopm, R, tf, E, cap, step):
    nd = BH.shape[0]; out = np.zeros((nd * 2, 8)); n = 0
    for d in range(nd):
        A = atr[d]
        if A <= 0: continue
        if tf == 1 and trend[d] == 0: continue
        k = k0; cnt = 0
        while k <= k1 and cnt < 2:
            if not (ratio[d, k] <= q) or BE[d, k] < 0:
                k += 1; continue
            hi = BH[d, k]; lo = BL[d, k]; e = BE[d, k]
            pl = hi + TICK; ps = lo - TICK
            j_end = e
            while j_end + 1 <= de[d] and sm[j_end + 1] < sm[e] + E: j_end += 1
            fj = -1; fd = 0
            for j in range(e, j_end + 1):
                ul = h[j] >= pl and (tf == 0 or trend[d] == 1)
                us = l[j] <= ps and (tf == 0 or trend[d] == -1)
                if ul and us:
                    fd = 1 if (pl - o[j]) <= (o[j] - ps) else -1
                elif ul: fd = 1
                elif us: fd = -1
                if fd != 0:
                    fj = j; break
            if fj < 0:
                k = sm[j_end] // step + 1; continue
            px = pl if fd == 1 else ps
            if stopm == 0: sl = (lo - TICK) if fd == 1 else (hi + TICK)
            elif stopm == 1: sl = (hi + lo) / 2
            else: sl = px - fd * 0.2 * A
            risk = (px - sl) * fd
            if risk > cap * A or risk < 0.03 * A or fj - 1 < 0:
                k = sm[fj] // step + 1; continue
            out[n, 0] = fj - 1; out[n, 1] = fd; out[n, 2] = 2; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = px + fd * R * risk
            out[n, 6] = fj; out[n, 7] = 240; n += 1; cnt += 1
            k = sm[fj] // step + 1
    return out[:n]


SQZ_WIN = {"night": (1900, 700), "am": (1000, 1200), "pm": (1200, 1500)}


def gen_sqz(D, p):
    BH, BL, BE, ratio = _sqz_feat(D, p["N"]); w0, w1 = SQZ_WIN[p["win"]]
    ev = _sqz(D.o, D.h, D.l, D.c, D.sm, D.de, D.atr, D.trend, BH, BL, BE, ratio, S(w0) // STEP, S(w1) // STEP, p["q"], p["stop"],
              p["R"], p["tf"], p["E"], 0.5, STEP)
    return ev_from_lists(ev.tolist())


GRID_SQZ = grid(N=(30, 60, 120), q=(0.5, 0.65, 0.8), win=tuple(SQZ_WIN), stop=(0, 1, 2), R=(0.5, 1.0, 2.0), tf=(0, 1), E=(30, 90))


# ---------------------------------------------------------------- PD_ACCEPT
@njit(cache=True)
def _pdacc(o, c, sm, ro, de, atr, trend, H1, L1, oloc, K, bk, w1, stopm, R, tf):
    nd = len(ro); out = np.zeros((nd, 8)); n = 0
    for d in range(nd):
        r = ro[d]; A = atr[d]
        if r < 0 or A <= 0 or np.isnan(H1[d]) or np.isnan(L1[d]): continue
        op = o[r]; up = H1[d] + bk * A; dn = L1[d] - bk * A
        okL = oloc == 0 or (oloc == 1 and op <= H1[d]) or (oloc == 2 and op > H1[d])
        okS = oloc == 0 or (oloc == 1 and op >= L1[d]) or (oloc == 2 and op < L1[d])
        if tf == 1:
            okL = okL and trend[d] == 1; okS = okS and trend[d] == -1
        if not (okL or okS): continue
        cu = 0; cd = 0
        for j in range(r, de[d] + 1):
            if sm[j] >= w1: break
            if (sm[j] - sm[r]) % 5 != 4: continue                  # 5-minute closes
            cu = cu + 1 if c[j] > up else 0
            cd = cd + 1 if c[j] < dn else 0
            s = 0
            if cu >= K and okL: s = 1
            elif cd >= K and okS: s = -1
            if s == 0: continue
            lvl = H1[d] if s == 1 else L1[d]
            sl = (lvl - s * 0.1 * A) if stopm == 0 else (c[j] - s * 0.25 * A)
            risk = (c[j] - sl) * s
            if risk > 0.4 * A or risk < 0.03 * A: break
            out[n, 0] = j; out[n, 1] = s; out[n, 2] = 0; out[n, 3] = c[j]; out[n, 4] = sl; out[n, 5] = c[j] + s * R * risk
            out[n, 6] = j; out[n, 7] = 400; n += 1
            break
    return out[:n]


def gen_pdacc(D, p):
    dl = _daily(D)
    return ev_from_lists(_pdacc(D.o, D.c, D.sm, D.ro, D.de, D.atr, D.trend, dl["H1"], dl["L1"], p["oloc"], p["K"], p["bk"], S(p["w1"]),
                                p["stop"], p["R"], p["tf"]).tolist())


GRID_PDACC = grid(oloc=(0, 1, 2), K=(2, 3, 6), bk=(0.0, 0.1), w1=(1000, 1030, 1130, 1300), stop=(0, 1), R=(0.5, 1.0, 2.0, 99.0), tf=(0, 1))


# ---------------------------------------------------------------- ER_PERSIST
@njit(cache=True)
def _er(o, c, sm, ro, eT, atr, trend, mode, th, x, k, R, tf):
    nd = len(ro); out = np.zeros((nd, 8)); n = 0
    for d in range(nd):
        r = ro[d]; e = eT[d]; A = atr[d]
        if r < 0 or e < 0 or A <= 0 or e - 1 <= r: continue
        i = e - 1; op = o[r]; prev = op; path = 0.0
        for j in range(r, i + 1):
            if (sm[j] - sm[r]) % 5 == 4 or j == i:
                path += abs(c[j] - prev); prev = c[j]
        mv = c[i] - op
        if path <= 0 or mv == 0: continue
        er = abs(mv) / path
        if abs(mv) < x * A: continue
        if mode == 1:
            if er < th: continue
            s = 1 if mv > 0 else -1
        else:
            if er > th: continue
            s = -1 if mv > 0 else 1
        if tf == 1 and s != trend[d]: continue
        sl = c[i] - s * k * A
        out[n, 0] = i; out[n, 1] = s; out[n, 2] = 0; out[n, 3] = c[i]; out[n, 4] = sl; out[n, 5] = c[i] + s * R * k * A
        out[n, 6] = i; out[n, 7] = 400; n += 1
    return out[:n]


ER_COND = {"hi30": (1, 0.30), "hi45": (1, 0.45), "hi60": (1, 0.60), "lo10": (-1, 0.10), "lo20": (-1, 0.20)}


def gen_er(D, p):
    eT = idx_at(D.sm, D.ds, D.de, S(p["T"])); mode, th = ER_COND[p["cond"]]
    return ev_from_lists(_er(D.o, D.c, D.sm, D.ro, eT, D.atr, D.trend, mode, th, p["x"], p["k"], p["R"], p["tf"]).tolist())


GRID_ER = grid(T=(1030, 1130, 1230, 1330, 1430), cond=tuple(ER_COND), x=(0.0, 0.15, 0.3), k=(0.15, 0.3), R=(0.5, 1.0, 2.0, 99.0), tf=(0, 1))


# ---------------------------------------------------------------- ON_POS
@njit(cache=True)
def _onpos(c, eT, atr, trend, ONH, ONL, z, ins, mode, stopm, tg, tf):
    nd = len(eT); out = np.zeros((nd, 8)); n = 0
    for d in range(nd):
        e = eT[d]; A = atr[d]
        if e < 1 or A <= 0 or np.isnan(ONH[d]) or np.isnan(ONL[d]): continue
        w = ONH[d] - ONL[d]
        if w <= 0.05 * A: continue
        i = e - 1; px = c[i]; pos = (px - ONL[d]) / w
        if ins == 1 and (pos < 0 or pos > 1): continue
        s = 0
        if pos <= z: s = 1 if mode == 1 else -1
        elif pos >= 1 - z: s = -1 if mode == 1 else 1
        if s == 0: continue
        if tf == 1 and s != trend[d]: continue
        if stopm == 0: sl = px - s * 0.2 * A
        elif stopm == 1: sl = px - s * 0.35 * A
        else:
            if mode == 1:                                           # beyond the near ON extreme
                ne = ONL[d] if s == 1 else ONH[d]
                sl = (min(ne, px) - 0.1 * A) if s == 1 else (max(ne, px) + 0.1 * A)
            else:
                sl = (ONH[d] + ONL[d]) / 2                         # continuation: back to the ON midpoint
        risk = (px - sl) * s
        if risk < 0.05 * A or risk > 0.6 * A: continue
        if tg == 0:
            if mode == 1: tp = ONH[d] if s == 1 else ONL[d]
            else: tp = px + s * w
            if (tp - px) * s < 0.05 * A: continue
        else:
            tp = px + s * (0.5 if tg == 1 else (1.0 if tg == 2 else 2.0)) * risk
        out[n, 0] = i; out[n, 1] = s; out[n, 2] = 0; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = i; out[n, 7] = 400; n += 1
    return out[:n]


def gen_onpos(D, p):
    eT = idx_at(D.sm, D.ds, D.de, S(p["T"]))
    return ev_from_lists(_onpos(D.c, eT, D.atr, D.trend, D.L[:, 1], D.L[:, 4], p["z"], p["ins"], p["mode"], p["stop"], p["tg"], p["tf"]).tolist())


GRID_ONPOS = grid(z=(0.15, 0.25, 0.35), ins=(0, 1), mode=(1, -1), T=(930, 945, 1000), stop=(0, 1, 2), tg=(0, 1, 2, 3), tf=(0, 1))


# ---------------------------------------------------------------- PERIOD_OPEN
def _period_opens(D):
    if hasattr(D, "_popen"): return D._popen
    nd = D.nd; WO = np.full(nd, np.nan); MO = np.full(nd, np.nan)
    valid = np.where(D.ds >= 0)[0]
    dt = pd.to_datetime(D.daydate[valid].astype(str), format="%Y%m%d", errors="coerce")
    iso = dt.isocalendar()
    wk = (iso.year.to_numpy() * 100 + iso.week.to_numpy()); mo = dt.year.to_numpy() * 100 + dt.month.to_numpy()
    cw = cm = None; wo = mo_ = np.nan
    for k, d in enumerate(valid):
        if wk[k] != cw: cw = wk[k]; wo = D.o[D.ds[d]]
        if mo[k] != cm: cm = mo[k]; mo_ = D.o[D.ds[d]]
        WO[d] = wo; MO[d] = mo_
    D._popen = (WO, MO); return D._popen


@njit(cache=True)
def _popen(o, h, l, c, sm, de, atr, trend, st, en, LV, nl, mode, dmin, s_k, R, tf):
    nd = len(st); out = np.zeros((nd * 2, 8)); n = 0
    for d in range(nd):
        a = st[d]; b = en[d]; A = atr[d]
        if a < 1 or b <= a or A <= 0: continue
        for q in range(nl):
            lv = LV[d, q]
            if np.isnan(lv): continue
            side = 1 if c[a - 1] > lv else (-1 if c[a - 1] < lv else 0)
            if side == 0 or abs(c[a - 1] - lv) < dmin * A: continue
            if mode == 0:                                           # bounce: resting limit at the level
                s = side
                if tf == 1 and s != trend[d]: continue
                fj = -1
                for j in range(a, b + 1):
                    if (side == 1 and l[j] <= lv) or (side == -1 and h[j] >= lv):
                        fj = j; break
                if fj < 0: continue
                sl = lv - s * s_k * A
                out[n, 0] = fj - 1; out[n, 1] = s; out[n, 2] = 1; out[n, 3] = lv; out[n, 4] = sl; out[n, 5] = lv + s * R * s_k * A
                out[n, 6] = b; out[n, 7] = 240; n += 1
            else:                                                   # break: stop entry 0.05 ATR through the level
                s = -side
                if tf == 1 and s != trend[d]: continue
                px = lv + s * 0.05 * A; sl = lv - s * s_k * A; risk = (px - sl) * s
                out[n, 0] = a - 1; out[n, 1] = s; out[n, 2] = 2; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = px + s * R * risk
                out[n, 6] = b; out[n, 7] = 240; n += 1
    return out[:n]


def gen_popen(D, p):
    WO, MO = _period_opens(D)
    LV = {"WO": np.column_stack([WO]), "MO": np.column_stack([MO]), "BOTH": np.column_stack([WO, MO])}[p["lvl"]]
    st = idx_at(D.sm, D.ds, D.de, S(p["w0"])); en = idx_at(D.sm, D.ds, D.de, S(p["w1"]))
    return ev_from_lists(_popen(D.o, D.h, D.l, D.c, D.sm, D.de, D.atr, D.trend, st, en, np.ascontiguousarray(LV), LV.shape[1],
                                p["mode"], p["dmin"], p["s"], p["R"], p["tf"]).tolist())


GRID_POPEN = grid(lvl=("WO", "MO", "BOTH"), mode=(0, 1), w0=(930, 1000), w1=(1200, 1530), dmin=(0.0, 0.2), s=(0.1, 0.2), R=(0.5, 1.0, 2.0), tf=(0, 1))

FAMILIES7 = {"SQZ_BOX": (gen_sqz, GRID_SQZ, 2), "PD_ACCEPT": (gen_pdacc, GRID_PDACC, 1), "ER_PERSIST": (gen_er, GRID_ER, 1),
             "ON_POS": (gen_onpos, GRID_ONPOS, 1), "PERIOD_OPEN": (gen_popen, GRID_POPEN, 2)}
# categorical parameters (excluded from the plateau neighbourhood: they define different strategies, not a step)
CATEGORICAL = {"win", "stop", "tf", "oloc", "cond", "ins", "mode", "lvl", "tg"}
