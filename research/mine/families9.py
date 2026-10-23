"""Batch 9 (2026-10-19, real Databento NQ futures 2010-26): HIGH win rate / NEGATIVE reward-to-risk families never mined here.
Every config targets r x risk with r in {0.2, 0.3, 0.5} and a WIDE stop (k x daily ATR or day structure), so the WR is high by
construction; the question is whether the WR clears the break-even 1/(1+r) (83 / 77 / 67% before costs) out of sample.
  ROUND_NUM    first RTH touch (09:35-12:00 or 09:35-15:30) of a round number of the RAW contract price (steps 50 / 100 / 250 NQ
               points; nqdb is forward roll-adjusted, so raw = adjusted + cumulative roll carry of the session) after an approach
               of >= x ATR over the last 60 minutes; bounce (fade the approach) with a resting limit at the level ('bl') or at
               the next bar open after the touch ('bm'). Levels considered: raw multiples within RTH open +- 2.5 ATR.
  ONHL_TEST    first RTH test (09:35-11:00 / 12:00) of the overnight high / low (18:00-09:29 bars only, complete by 09:30);
               price must have been >= x ATR away from the level since 09:30. Bounce limit ('bl'), bounce at market after the
               touch ('bm') or continuation stop entry 1 tick through the level ('br').
  SETTLE       first RTH touch of the prior session's 16:00 ET settlement (close of the last RTH bar of the prior COMPLETE
               session, core.Data.pdc) after being >= x ATR away since 09:30; bl / bm / br as above.
  TREND_SCALP  trend-day-so-far: at T (10:30 / 11:00 / 12:00) the RTH move >= x ATR and the last close on the same side of the RTH
               VWAP; then buy (sell) the pullback to the 5-minute EMA9 (last COMPLETED 5m bar) or to the VWAP with a 1-bar limit
               re-issued on every 1m bar that closes 0..0.05 ATR on the trend side of the reference; stop k ATR or 1 tick beyond
               the day's opposite RTH extreme so far (risk 0.1-1.0 ATR); first fill only; until 15:00 (entries).
  STRETCH_SNAP 11:00-14:30 lull, 5m bars: dev = close - mean of the previous M closes (M 6 / 12 = 30 / 60 min), sigma = std of the
               previous 24 five-minute changes; |dev| >= z sigma AND >= 75% of dev made in the last q (2 / 3) bars -> fade at the
               next 1m bar; re-armed after |dev| < 1 sigma; stop k ATR, target r x risk, hold 30 / 60 min; max 2 a day.
Level families: levels and approach conditions use bars up to the arming / touch bar only; a resting limit ('bl') is placed on
a bar that does NOT touch the level and that closes within 0.5 x target of it (so the order is live; core.execute cancels it if
the target is reached first), valid E = 30 min; one setup per level per day (the first touch consumes the level; a touch
before the window start consumes it too). All entries go through core.execute ($1.90 + 1 tick per side)."""
import os, numpy as np, pandas as pd
from numba import njit
from core import S, TICK, ev_from_lists
from families import grid, idx_at

HERE = os.path.dirname(os.path.abspath(__file__))
MODE = {"bl": 0, "bm": 1, "br": 2}


def _carry(D):
    """Per session: cumulative roll carry (raw = adjusted + carry). Rolls switch at 00:00 UTC = inside the session whose ET+6h
    date equals the switch date, before 09:30 -> constant over RTH."""
    if hasattr(D, "_car"): return D._car
    rolls = pd.read_csv(os.path.join(os.path.dirname(HERE), "data", "nqdb_rolls.csv"), parse_dates=["switch_utc"]).sort_values("switch_utc")
    rd = rolls.switch_utc.dt.strftime("%Y%m%d").astype(int).to_numpy(); cum = np.cumsum(rolls.spread.to_numpy())
    k = np.searchsorted(rd, D.daydate, side="right") - 1
    D._car = np.where(k >= 0, cum[np.maximum(k, 0)], 0.0).astype(np.float64); return D._car


def _round_levels(D, step):
    key = f"_rl{step}"
    if hasattr(D, key): return getattr(D, key)
    car = _carry(D); rows = []; K = 1
    for d in range(D.nd):
        r = D.ro[d]; A = D.atr[d]
        if r < 0 or A <= 0: rows.append(np.zeros(0)); continue
        op = D.o[r] + car[d]                                           # RTH open (09:30 bar open), raw price
        lo = np.ceil((op - 2.5 * A) / step) * step; hi = np.floor((op + 2.5 * A) / step) * step
        lv = np.arange(lo, hi + step / 2, step) - car[d] if hi >= lo else np.zeros(0)
        rows.append(lv); K = max(K, len(lv))
    LV = np.full((D.nd, K), np.nan)
    for d, lv in enumerate(rows): LV[d, :len(lv)] = lv
    setattr(D, key, LV); return LV


def _on_levels(D):
    if hasattr(D, "_onl"): return D._onl
    LV = np.full((D.nd, 2), np.nan); s930 = S(930)
    for d in range(D.nd):
        a, r = D.ds[d], D.ro[d]
        if a < 0 or r < 0: continue
        m = D.sm[a:r] < s930
        if m.sum() < 500: continue                                    # need a real overnight session
        LV[d, 0] = D.h[a:r][m].max(); LV[d, 1] = D.l[a:r][m].min()
    D._onl = LV; return LV


def _settle_levels(D):
    return np.ascontiguousarray(D.pdc.reshape(-1, 1))


@njit(cache=True)
def _lvl(o, h, l, c, sm, ds, ro, de, atr, trend, LV, w0, w1, x, W, mode, tf, k, r, E, hold):
    nd, K = LV.shape; cap = 100; out = np.zeros((nd * cap, 8)); n = 0; over = 0
    alive = np.zeros(K, np.bool_); armed = np.zeros(K, np.bool_)
    for d in range(nd):
        r0 = ro[d]; A = atr[d]
        if r0 < 1 or A <= 0: continue
        risk = k * A; tgt = r * risk; band = 0.5 * tgt; nday = 0
        for m in range(K):
            alive[m] = not np.isnan(LV[d, m]); armed[m] = True
        for j in range(r0, de[d] + 1):
            if sm[j] >= w1: break
            for m in range(K):
                if not alive[m]: continue
                L = LV[d, m]
                touch = (l[j] <= L) and (h[j] >= L)
                if sm[j] < w0:
                    if touch: alive[m] = False
                    continue
                if touch:
                    alive[m] = False
                    if mode != 1: continue
                    sb = 1 if c[j - 1] > L else -1                    # side before the touch
                    st = r0 if W == 0 else max(j - W, ds[d])
                    far = 0.0
                    for q in range(st, j):
                        f = (h[q] - L) if sb == 1 else (L - l[q])
                        if f > far: far = f
                    if far < x * A: continue
                    s = sb
                    if tf == 1 and s != trend[d]: continue
                    px = c[j]; sl = px - s * risk; tp = px + s * tgt; t = 0; ex = j
                else:
                    if mode == 1: continue
                    sb = 1 if c[j] > L else -1
                    dist = (c[j] - L) * sb
                    if dist > band:
                        armed[m] = True; continue
                    if not armed[m]: continue
                    armed[m] = False
                    st = r0 if W == 0 else max(j - W + 1, ds[d])
                    far = 0.0
                    for q in range(st, j + 1):
                        f = (h[q] - L) if sb == 1 else (L - l[q])
                        if f > far: far = f
                    if far < x * A: continue
                    if mode == 0:
                        s = sb; px = L; sl = L - s * risk; tp = L + s * tgt; t = 1
                    else:
                        s = -sb; px = L + s * TICK; sl = px - s * risk; tp = px + s * tgt; t = 2
                    if tf == 1 and s != trend[d]: continue
                    ex = j + E
                if nday >= cap: over += 1; continue
                out[n, 0] = j; out[n, 1] = s; out[n, 2] = t; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = ex; out[n, 7] = hold
                n += 1; nday += 1
    return out[:n], over


def _lvl_events(D, LV, p, w1, x, W):
    o, over = _lvl(D.o, D.h, D.l, D.c, D.sm, D.ds, D.ro, D.de, D.atr, D.trend, np.ascontiguousarray(LV), S(935), S(w1), x, W,
                   MODE[p["mode"]], p["tf"], p["k"], p["r"], 30, 120)
    if over > 0: raise RuntimeError(f"event cap hit {over}")
    return ev_from_lists(o.tolist())


# ---------------------------------------------------------------- ROUND_NUM
def gen_round(D, p):
    return _lvl_events(D, _round_levels(D, p["step"]), p, p["win"], p["x"], 60)


GRID_ROUND = grid(step=(50, 100, 250), mode=("bl", "bm"), x=(0.15, 0.3, 0.5), tf=(0, 1), k=(0.25, 0.4, 0.6), r=(0.2, 0.3, 0.5), win=(1200, 1530))


# ---------------------------------------------------------------- ONHL_TEST
def gen_onhl(D, p):
    return _lvl_events(D, _on_levels(D), p, p["win"], p["x"], 0)


GRID_ONHL = grid(mode=("bl", "bm", "br"), x=(0.0, 0.15, 0.3), tf=(0, 1), k=(0.25, 0.4, 0.6), r=(0.2, 0.3, 0.5), win=(1100, 1200))


# ---------------------------------------------------------------- SETTLE
def gen_settle(D, p):
    return _lvl_events(D, _settle_levels(D), p, p["win"], p["x"], 0)


GRID_SETTLE = grid(mode=("bl", "bm", "br"), x=(0.1, 0.25, 0.4), tf=(0, 1), k=(0.25, 0.4, 0.6), r=(0.2, 0.3, 0.5), win=(1200, 1530))


# ---------------------------------------------------------------- TREND_SCALP
def _ema9_1m(D):
    """EMA9 of 5-minute closes, as known at each 1m bar: value of the last 5m bar COMPLETED at or before that 1m bar."""
    if hasattr(D, "_e9"): return D._e9
    B = D.bars(5)
    e = pd.Series(B["c"]).ewm(span=9, adjust=False).mean().to_numpy()
    pos = np.searchsorted(B["last"], np.arange(D.n), side="right") - 1
    out = np.where(pos >= 0, e[np.maximum(pos, 0)], np.nan)
    D._e9 = np.ascontiguousarray(out); return D._e9


@njit(cache=True)
def _tscalp(o, h, l, c, sm, ro, de, atr, trend, vwap, ref, eT, x, tf, stopm, k, r, band, wend, hold):
    nd = len(ro); cap = 80; out = np.zeros((nd * cap, 8)); n = 0
    for d in range(nd):
        r0 = ro[d]; e = eT[d]; A = atr[d]
        if r0 < 0 or e < 0 or A <= 0 or e - 1 <= r0: continue
        i = e - 1; mv = c[i] - o[r0]
        if abs(mv) < x * A: continue
        s = 1 if mv > 0 else -1
        if np.isnan(vwap[i]) or (c[i] - vwap[i]) * s <= 0: continue
        if tf == 1 and s != trend[d]: continue
        lo = 1e18; hi = -1e18
        for q in range(r0, i + 1):
            if l[q] < lo: lo = l[q]
            if h[q] > hi: hi = h[q]
        cnt = 0
        for j in range(e, de[d] + 1):
            if sm[j] >= wend or cnt >= cap: break
            if l[j] < lo: lo = l[j]
            if h[j] > hi: hi = h[j]
            rf = ref[j]
            if np.isnan(rf): continue
            dd = (c[j] - rf) * s
            if dd < 0 or dd > band * A: continue
            px = np.floor(rf / TICK + 0.5) * TICK
            if stopm == 0: sl = px - s * k * A
            else: sl = (lo - TICK) if s == 1 else (hi + TICK)
            risk = (px - sl) * s
            if risk < 0.1 * A or risk > 1.0 * A: continue
            tp = px + s * r * risk
            out[n, 0] = j; out[n, 1] = s; out[n, 2] = 1; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = j + 1; out[n, 7] = hold
            n += 1; cnt += 1
    return out[:n]


TS_STOP = {"k0.25": (0, 0.25), "k0.4": (0, 0.4), "ext": (1, 0.0)}


def gen_tscalp(D, p):
    ref = _ema9_1m(D) if p["ref"] == "ema9" else np.ascontiguousarray(D.vwap)
    eT = idx_at(D.sm, D.ds, D.de, S(p["T"])); stopm, k = TS_STOP[p["stop"]]
    return ev_from_lists(_tscalp(D.o, D.h, D.l, D.c, D.sm, D.ro, D.de, D.atr, D.trend, D.vwap, ref, eT, p["x"], p["tf"], stopm, k, p["r"],
                                 0.05, S(1500), 400).tolist())


GRID_TSCALP = grid(T=(1030, 1100, 1200), x=(0.3, 0.5, 0.75), ref=("ema9", "vwap"), tf=(0, 1), stop=tuple(TS_STOP), r=(0.2, 0.3, 0.5))


# ---------------------------------------------------------------- STRETCH_SNAP
def _stretch_feat(D, M):
    key = f"_st{M}"
    if hasattr(D, key): return getattr(D, key)
    B = D.bars(5); cs = pd.Series(B["c"])
    mean = cs.rolling(M, min_periods=M).mean().shift(1).to_numpy(float)
    sig = cs.diff().rolling(24, min_periods=24).std(ddof=0).shift(1).to_numpy(float)
    out = (np.ascontiguousarray(mean), np.ascontiguousarray(sig)); setattr(D, key, out); return out


@njit(cache=True)
def _stretch(c5, sme, day5, last5, atr, trend, mean5, sig5, w0, w1, zt, q, tf, k, r, hold):
    nb = len(c5); nd = day5[-1] + 1; out = np.zeros((nd * 4 + 10, 8)); n = 0
    cur = -1; armed = True; cnt = 0
    for b in range(nb):
        d = day5[b]
        if d != cur: cur = d; armed = True; cnt = 0
        if sme[b] < w0 or sme[b] >= w1: continue
        sg = sig5[b]; mu = mean5[b]
        if not (sg > 0) or np.isnan(mu): continue
        dev = c5[b] - mu; z = dev / sg
        if abs(z) < 1.0: armed = True; continue
        if abs(z) < zt or not armed: continue
        if b - q < 0 or day5[b - q] != d: continue
        sd = 1.0 if dev > 0 else -1.0
        if (c5[b] - c5[b - q]) * sd < 0.75 * abs(dev): continue
        armed = False
        A = atr[d]
        if A <= 0 or cnt >= 2: continue
        s = -int(sd)
        if tf == 1 and s != trend[d]: continue
        px = c5[b]; sl = px - s * k * A; tp = px + s * r * k * A
        out[n, 0] = last5[b]; out[n, 1] = s; out[n, 2] = 0; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = last5[b]; out[n, 7] = hold
        n += 1; cnt += 1
    return out[:n]


def gen_stretch(D, p):
    B = D.bars(5); mean, sig = _stretch_feat(D, p["M"])
    return ev_from_lists(_stretch(B["c"], B["sme"], B["day"], B["last"], D.atr, D.trend, mean, sig, S(1100), S(1430), p["z"], p["q"], p["tf"],
                                  p["k"], p["r"], p["hold"]).tolist())


GRID_STRETCH = grid(M=(6, 12), z=(2.0, 2.5, 3.0, 3.5), q=(2, 3), tf=(0, 1), k=(0.2, 0.3, 0.45), r=(0.2, 0.3, 0.5), hold=(30, 60))

FAMILIES9 = {"ROUND_NUM": (gen_round, GRID_ROUND, 2), "ONHL_TEST": (gen_onhl, GRID_ONHL, 2), "SETTLE": (gen_settle, GRID_SETTLE, 1),
             "TREND_SCALP": (gen_tscalp, GRID_TSCALP, 1), "STRETCH_SNAP": (gen_stretch, GRID_STRETCH, 2)}
# categorical parameters (not a "step" for the plateau test)
CATEGORICAL9 = {"mode", "tf", "win", "ref", "stop"}
