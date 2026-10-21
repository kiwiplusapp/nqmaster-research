"""Batch 11 (2026-10-21): the CLASSIC index-futures trading literature adapted to intraday NQ (every trade flat at MINE_FLAT = 15:55 ET).
Families never mined here (Williams / Raschke-Connors / Crabel / Connors / Taylor / Steidlmayer). Daily values come from the compact table
of RTH days (_daily): a feature at row k uses rows <= k-1 only (yesterday = the previous RTH day); intraday levels (opening ranges,
day extremes) use 1m bars <= the signal bar; all fills go through core.execute ($1.90 + 1 tick, stops -1 tick, limits need a 1-tick
trade-through). Two-sided (OCO) setups are resolved in the generator: the side whose level is touched first in the window is the only
event emitted (signal bar = the bar before the touch; a bar touching both sides cancels the day). Structural stops (sk = 0) use the day's
extreme so far / the setup's own extreme + 1 tick, floored at 0.10 ATR and skipped above 1.0 ATR; R = 0 means hold to the close.
  LW_OOPS        Williams 'Oops!': RTH open gaps >= g ATR below yesterday's low -> buy stop at yesterday's low (mirror above the high).
  LW_SMASH       Williams smash day: yesterday closed below the day-before's low (bear smash) -> buy stop at yesterday's high (+off ATR);
                 'hidden': yesterday closed below its open in the bottom 25% of its range -> same entry; mirror for sells.
  LW_INOUT       inside day -> OCO breakout of the inside day's high/low; outside day -> entry on the break of its extreme with ('cont')
                 or against ('rev') the outside day's close direction.
  RC_TSOUP       Raschke/Connors Turtle Soup Plus One ('ts1': yesterday made a new N-day low AND closed at/below the previous N-day low;
                 today, after price trades x ATR below yesterday's low, buy stop back at that low) and intraday Turtle Soup ('tsi': price
                 breaks the N-day low (days k-N..k-1) by x ATR today, buy stop back at the level); mirror for sells.
  RC_8020        Raschke/Connors 80-20s: yesterday opened in the top pct and closed in the bottom pct of a range >= 0.75 ATR; today, after
                 trading x ATR below yesterday's low, buy stop at yesterday's low; mirror.
  RC_PINBALL     Raschke momentum pinball: 3-period RSI of the 1-day ROC (daily closes, up to yesterday) < thr -> buy stop above the
                 opening-range (09:30-orl) high after the range; > 100-thr -> sell stop below its low.
  RC_HOLYGRAIL   Raschke/Connors Holy Grail on tf-minute bars: ADX(14) > thr and rising, +DI > -DI, first bar whose low touches EMA(ema)
                 -> buy stop above that bar's high valid nb bars; stop below its low (struct) or sk ATR; mirror.
  RC_ANTI        Raschke Anti on tf-minute bars: slow %K(kp, 3) hooks back in the direction of a rising / falling %D(10) after a
                 pullback -> stop above the hook bar's high valid nb bars; stop below the pullback low (struct) or sk ATR; mirror.
  CRABEL_NR      Crabel NR4 / ID-NR4 / 2-bar NR (narrowest 2-day range of 20) yesterday -> OCO breakout of the opening range (09:30-orl).
  CRABEL_STRETCH Crabel stretch: 10-day mean of min(open-low, high-open); OCO stops at open +- m x stretch, optional NR4 / ID-NR4 day.
  CN_DOUBLE7     Connors Double 7s: yesterday's close is the lowest close of N days (and above SMA200 with filt) -> long at the open
                 (market) or on a dip (limit open - 0.1 ATR); mirror for the highest close (below SMA200 with filt).
  CN_PCTB        Connors %b: Bollinger(20, 2) %b of yesterday's close < thr -> long; > 1 - thr -> short; same entries / SMA200 filter.
  CN_R3          Connors R3: RSI(2) of daily closes fell 3 days in a row from < 60 to < thr3 (above SMA200 with filt) -> long; mirror.
  TAYLOR         Taylor 3-day cycle anchored at the lowest low ('low') / highest high ('high') of the last 3 RTH days -> today is the Buy,
                 Sell or Short-Sale day; Buy day: long on a decline x ATR below yesterday's low (limit, 'viol') or on the failure of that
                 decline (stop back at the low after the violation, 'fail'), target yesterday's high ('prior') / R / hold; SS day: mirror
                 at yesterday's high; the Sell day has no new entry.
  STEID_OPEN     Steidlmayer open types from the first W minutes: open-drive (open within 15% of one extreme, close within 30% of the
                 other, range >= x ATR) -> trade the drive; open-test-drive (the first extreme is the test side, open 15-50% from it,
                 close within 20% of the far extreme) -> trade the drive, stop beyond the test; open-rejection-reverse (the first extreme
                 was the far side, the W-close is back on the other side of the open) -> trade the reversal, stop beyond the rejected
                 extreme; open-auction (range <= x ATR, open in the middle 40%) -> fade the W-range extremes with limits until 12:00."""
import numpy as np, pandas as pd
from numba import njit
from core import S, TICK, ev_from_lists
from families import grid

HOLD = 100000           # bars; every trade is flat at MINE_FLAT anyway
FAR = 30.0              # 'hold to close' target = entry +- 30 ATR (never reached)
RMIN, RMAX = 0.10, 1.0  # structural-stop floor / cap in ATR
CATEGORICAL11 = ("mode", "pat", "src", "cond", "ent", "anchor", "tgt", "days", "typ", "tf", "filt", "dtf", "orl", "t0", "exp", "W")


# ------------------------------------------------------------------------------------------------ daily table (RTH days)
def _daily(D):
    """Per session d (index 0..nd-1) the features known at 09:30 of day d, from previous RTH days only. Cached on D."""
    if hasattr(D, "_d11"): return D._d11
    rows = []
    for d in range(D.nd):
        r = D.ro[d]
        if r < 0 or D.sm[r] != S(930): continue
        e = D.de[d]; om = D.om[r:e + 1]; m = (om >= 570) & (om < 960)
        if m.sum() < 30: continue
        hh = D.h[r:e + 1][m]; ll = D.l[r:e + 1][m]; cc = D.c[r:e + 1][m]
        rows.append((d, D.o[r], hh.max(), ll.min(), cc[-1]))
    T = pd.DataFrame(rows, columns=["d", "O", "H", "L", "C"])
    O, H, L, C = T.O, T.H, T.L, T.C
    F = {}
    sh = lambda s, k=1: s.shift(k)
    F["pO"], F["pH"], F["pL"], F["pC"] = sh(O), sh(H), sh(L), sh(C)
    F["pH2"], F["pL2"], F["pC2"] = sh(H, 2), sh(L, 2), sh(C, 2)
    rng = H - L
    F["rng1"] = sh(rng)
    F["nr4"] = sh((rng < rng.shift(1)) & (rng < rng.shift(2)) & (rng < rng.shift(3)))
    F["id"] = sh((H < H.shift(1)) & (L > L.shift(1)))
    F["od"] = sh((H > H.shift(1)) & (L < L.shift(1)))
    r2 = np.maximum(H, H.shift(1)) - np.minimum(L, L.shift(1))                       # 2-day range ending at the row
    F["nr2"] = sh(r2 < r2.shift(2).rolling(18, min_periods=18).min())               # narrowest 2-day range vs the 18 non-overlapping-ending ones before
    F["posO"] = sh((O - L) / rng); F["posC"] = sh((C - L) / rng)
    for N in (10, 20):
        F[f"ll{N}x"] = sh(L.rolling(N, min_periods=N).min(), 2)                      # N-day low of days k-N-1..k-2 (before yesterday)
        F[f"hh{N}x"] = sh(H.rolling(N, min_periods=N).max(), 2)
        F[f"ll{N}"] = sh(L.rolling(N, min_periods=N).min())                          # N-day low of days k-N..k-1
        F[f"hh{N}"] = sh(H.rolling(N, min_periods=N).max())
    F["stretch"] = sh(np.minimum(O - L, H - O).rolling(10, min_periods=10).mean())
    for N in (5, 7, 10):
        F[f"cmin{N}"] = sh(C == C.rolling(N, min_periods=N).min()); F[f"cmax{N}"] = sh(C == C.rolling(N, min_periods=N).max())
    F["sma200"] = sh(C.rolling(200, min_periods=200).mean())
    m20 = C.rolling(20, min_periods=20).mean(); s20 = C.rolling(20, min_periods=20).std(ddof=0)
    F["pb"] = sh((C - (m20 - 2 * s20)) / (4 * s20))
    dc = C.diff(); up = dc.clip(lower=0); dn = (-dc).clip(lower=0)
    au = up.ewm(alpha=1 / 2, adjust=False).mean(); ad = dn.ewm(alpha=1 / 2, adjust=False).mean()
    rsi2 = 100 - 100 / (1 + au / ad.replace(0, np.nan)); rsi2 = rsi2.fillna(100.0).where(C.notna())
    F["rsi2_1"], F["rsi2_2"], F["rsi2_3"] = sh(rsi2), sh(rsi2, 2), sh(rsi2, 3)
    roc = dc; au3 = roc.clip(lower=0).ewm(alpha=1 / 3, adjust=False).mean(); ad3 = (-roc).clip(lower=0).ewm(alpha=1 / 3, adjust=False).mean()
    F["rsi3roc"] = sh(100 - 100 / (1 + au3 / ad3.replace(0, np.nan)))
    # Taylor cycle: position of the lowest low / highest high among the last 3 RTH days (1 = yesterday, 2, 3)
    l1, l2, l3 = L.shift(1), L.shift(2), L.shift(3); h1, h2, h3 = H.shift(1), H.shift(2), H.shift(3)
    F["tlow"] = pd.Series(np.where(l1.isna() | l2.isna() | l3.isna(), np.nan, np.argmin(np.c_[l1, l2, l3], axis=1) + 1))
    F["thigh"] = pd.Series(np.where(h1.isna() | h2.isna() | h3.isna(), np.nan, np.argmax(np.c_[h1, h2, h3], axis=1) + 1))
    out = {}
    for k, s in F.items():
        a = np.full(D.nd, np.nan); a[T.d.to_numpy()] = np.asarray(s, dtype=float); out[k] = a
    out["rows"] = T.d.to_numpy()
    D._d11 = out; return out


@njit(cache=True)
def _first_at(sm, ro, de, d, t):
    for j in range(ro[d], de[d] + 1):
        if sm[j] >= t: return j
    return de[d]


# ------------------------------------------------------------------------------------------------ generic one-level kernel
@njit(cache=True)
def _lvl(o, h, l, c, sm, ro, de, atr, trend, LV, DIR, TG, mode, g, x, etype, t0, t1, texp, sk, R, tf, lim_off):
    """One trade per day in direction DIR[d] at level LV[d]. mode 0: at t0 the RTH open must be on the near side of the level by >= g ATR;
    mode 1: price must trade x ATR beyond the level inside [t0, t1) first, the order is placed on that bar; mode 2: order placed at t0 if
    the level is still ahead of price (stop) / behind price (limit). etype 0 market (next bar open), 1 limit at LV -+ lim_off ATR, 2 stop at LV.
    Stop sk ATR (sk > 0) or structural (day extreme so far + 1 tick, floor RMIN, cap RMAX). R > 0 target R x risk, R == 0 hold, R < 0 target TG[d]."""
    nd = len(ro); out = np.zeros((nd, 8)); n = 0
    for d in range(nd):
        r = ro[d]; A = atr[d]; s = DIR[d]; L = LV[d]
        if r < 1 or A <= 0 or s == 0 or np.isnan(L): continue
        if tf == 1 and s != trend[d]: continue
        if tf == -1 and s != -trend[d]: continue
        i0 = _first_at(sm, ro, de, d, t0); iexp = _first_at(sm, ro, de, d, texp)
        sig = -1
        if mode == 0:
            if (s == 1 and o[r] <= L - g * A) or (s == -1 and o[r] >= L + g * A): sig = i0
        elif mode == 1:
            for j in range(i0, de[d] + 1):
                if sm[j] >= t1: break
                if (s == 1 and l[j] <= L - x * A) or (s == -1 and h[j] >= L + x * A):
                    sig = j; break
        else:
            sig = i0
        if sig < 0 or sig >= iexp: continue
        if etype == 2: px = L
        elif etype == 1: px = L - s * lim_off * A
        else: px = c[sig]
        if mode == 2 and etype == 2 and (px - c[sig]) * s <= 0: continue        # breakout already happened before the placement
        if mode == 2 and etype == 1 and (c[sig] - px) * s <= 0: continue        # limit would fill at once: not the setup
        if sk > 0: risk = sk * A
        else:
            ext = l[r] if s == 1 else h[r]
            for j in range(r, sig + 1):
                if s == 1 and l[j] < ext: ext = l[j]
                if s == -1 and h[j] > ext: ext = h[j]
            risk = (px - ext if s == 1 else ext - px) + TICK
            if risk < RMIN * A: risk = RMIN * A
            if risk > RMAX * A: continue
        sl = px - s * risk
        if R > 0: tp = px + s * R * risk
        elif R == 0: tp = px + s * FAR * A
        else:
            tp = TG[d]
            if np.isnan(tp) or (tp - px) * s < 2 * TICK: continue
        out[n, 0] = sig; out[n, 1] = s; out[n, 2] = etype; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = iexp; out[n, 7] = HOLD; n += 1
    return out[:n]


# ------------------------------------------------------------------------------------------------ two-sided breakout (OCO) kernel
@njit(cache=True)
def _oco(o, h, l, c, sm, ro, de, atr, trend, UP, DN, OK, t0, t1, texp, sk, R, tf, off, etype):
    """At t0: buy stop at UP + off ATR and sell stop at DN - off ATR (etype 2), or sell limit at UP / buy limit at DN (etype 1, fade).
    The first side touched in (t0, t1) is emitted with signal bar = touch bar - 1; a bar touching both sides cancels the day.
    Structural stop (sk = 0): the opposite level (stops) / the range beyond the level (limits). R < 0: target = the range midpoint."""
    nd = len(ro); out = np.zeros((nd, 8)); n = 0
    for d in range(nd):
        r = ro[d]; A = atr[d]
        if r < 1 or A <= 0 or OK[d] == 0 or np.isnan(UP[d]) or np.isnan(DN[d]): continue
        up = UP[d] + off * A; dn = DN[d] - off * A
        if up - dn < 2 * TICK: continue
        i0 = _first_at(sm, ro, de, d, t0); iexp = _first_at(sm, ro, de, d, texp)
        if not (c[i0] <= up and c[i0] >= dn): continue
        au = tf == 0 or trend[d] == 1; ad = tf == 0 or trend[d] == -1   # stops: the upside break is a long, the downside break a short
        if etype == 1:
            au = tf == 0 or trend[d] == -1; ad = tf == 0 or trend[d] == 1   # limits (fade): a touch of UP is a short, of DN a long
        for j in range(i0 + 1, de[d] + 1):
            if sm[j] >= t1 or j >= iexp: break
            if etype == 2: bu = h[j] >= up; bd = l[j] <= dn
            else: bu = h[j] >= up + TICK; bd = l[j] <= dn - TICK
            if bu and bd: break
            if not (bu or bd): continue
            if etype == 2:
                if bu and not au: break
                if bd and not ad: break
                s = 1 if bu else -1; px = up if bu else dn
                risk = sk * A if sk > 0 else (up - dn) + TICK
            else:
                if bu and not ad: break
                if bd and not au: break
                s = -1 if bu else 1; px = up if bu else dn
                risk = sk * A if sk > 0 else (up - dn) + TICK
            if sk <= 0:
                if risk < RMIN * A: risk = RMIN * A
                if risk > RMAX * A: break
            sl = px - s * risk
            if R > 0: tp = px + s * R * risk
            elif R == 0: tp = px + s * FAR * A
            else: tp = 0.5 * (up + dn)
            if (tp - px) * s < 2 * TICK: break
            out[n, 0] = j - 1; out[n, 1] = s; out[n, 2] = etype; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = iexp; out[n, 7] = HOLD; n += 1
            break
    return out[:n]


@njit(cache=True)
def _orange(o, h, l, c, sm, ro, de, t_end):
    """Opening range 09:30 .. t_end (exclusive) per day: high, low, close of the last bar, index of the first extreme (1 high first, -1 low first, 0 same bar)."""
    nd = len(ro); H = np.full(nd, np.nan); L = np.full(nd, np.nan); C = np.full(nd, np.nan); FE = np.zeros(nd, np.int64); OPN = np.full(nd, np.nan)
    for d in range(nd):
        r = ro[d]
        if r < 1: continue
        hi = -1e18; lo = 1e18; ih = -1; il = -1; last = -1
        for j in range(r, de[d] + 1):
            if sm[j] >= t_end: break
            if h[j] > hi: hi = h[j]; ih = j
            if l[j] < lo: lo = l[j]; il = j
            last = j
        if last < 0 or last - r < 5: continue
        H[d] = hi; L[d] = lo; C[d] = c[last]; OPN[d] = o[r]; FE[d] = 1 if ih < il else (-1 if il < ih else 0)
    return H, L, C, OPN, FE


# ------------------------------------------------------------------------------------------------ helpers
def _base(D):
    return (D.o, D.h, D.l, D.c, D.sm, D.ro, D.de, D.atr.astype(np.float64), D.trend)


def _ev(arr):
    return ev_from_lists(arr.tolist())


def _dir_lv(buy_cond, sell_cond, buy_lv, sell_lv, nd):
    DIR = np.zeros(nd, np.int64); LV = np.full(nd, np.nan)
    b = np.nan_to_num(buy_cond).astype(bool); s = np.nan_to_num(sell_cond).astype(bool) & ~b
    DIR[b] = 1; LV[b] = buy_lv[b]; DIR[s] = -1; LV[s] = sell_lv[s]
    return DIR, LV


def _nan(D):
    return np.full(D.nd, np.nan)


# ------------------------------------------------------------------------------------------------ 1. Larry Williams
def gen_oops(D, p):
    F = _daily(D); A = D.atr; opn = np.full(D.nd, np.nan); m = D.ro >= 0; opn[m] = D.o[D.ro[m]]
    DIR, LV = _dir_lv(opn <= F["pL"] - p["g"] * A, opn >= F["pH"] + p["g"] * A, F["pL"], F["pH"], D.nd)
    return _ev(_lvl(*_base(D), LV, DIR, _nan(D), 0, p["g"], 0.0, 2, S(930), S(930), S(p["exp"]), p["sk"], p["R"], p["tf"], 0.0))


GRID_OOPS = grid(g=(0.0, 0.05, 0.15), exp=(1100, 1300, 1500), sk=(0.0, 0.25, 0.5), R=(1.0, 2.0, 0.0), tf=(0, 1, -1))


def gen_smash(D, p):
    F = _daily(D); A = D.atr
    if p["mode"] == "smash": bc = F["pC"] < F["pL2"]; sc = F["pC"] > F["pH2"]
    else: bc = (F["pC"] < F["pO"]) & (F["posC"] <= 0.25); sc = (F["pC"] > F["pO"]) & (F["posC"] >= 0.75)
    DIR, LV = _dir_lv(bc, sc, F["pH"] + p["off"] * A, F["pL"] - p["off"] * A, D.nd)
    return _ev(_lvl(*_base(D), LV, DIR, _nan(D), 0, 0.0, 0.0, 2, S(930), S(930), S(p["exp"]), p["sk"], p["R"], p["tf"], 0.0))


GRID_SMASH = grid(mode=("smash", "hidden"), off=(0.0, 0.05), exp=(1100, 1300, 1500), sk=(0.0, 0.25, 0.5), R=(1.0, 2.0, 0.0), tf=(0, 1, -1))


def gen_inout(D, p):
    F = _daily(D)
    if p["pat"] == "in":
        OK = np.nan_to_num(F["id"]).astype(np.int64)
        return _ev(_oco(*_base(D), F["pH"], F["pL"], OK, S(930), S(p["exp"]), S(p["exp"]), p["sk"], p["R"], p["tf"], 0.0, 2))
    od = np.nan_to_num(F["od"]).astype(bool); upc = F["pC"] > F["pO"]; dnc = F["pC"] < F["pO"]
    if p["pat"] == "out_cont": DIR, LV = _dir_lv(od & upc, od & dnc, F["pH"], F["pL"], D.nd)
    else: DIR, LV = _dir_lv(od & dnc, od & upc, F["pH"], F["pL"], D.nd)
    return _ev(_lvl(*_base(D), LV, DIR, _nan(D), 0, 0.0, 0.0, 2, S(930), S(930), S(p["exp"]), p["sk"], p["R"], p["tf"], 0.0))


GRID_INOUT = grid(pat=("in", "out_cont", "out_rev"), sk=(0.0, 0.25, 0.5), R=(1.0, 2.0, 0.0), exp=(1100, 1300, 1500), tf=(0, 1))


# ------------------------------------------------------------------------------------------------ 2. Raschke / Connors
def gen_tsoup(D, p):
    F = _daily(D); N = p["N"]
    if p["src"] == "ts1":
        bc = (F["pL"] < F[f"ll{N}x"]) & (F["pC"] <= F[f"ll{N}x"]); sc = (F["pH"] > F[f"hh{N}x"]) & (F["pC"] >= F[f"hh{N}x"])
        DIR, LV = _dir_lv(bc, sc, F["pL"], F["pH"], D.nd)
        # both sides possible on the same day only if yesterday was both a new high and a new low (impossible); DIR picks the buy
    else:
        DIR = np.zeros(D.nd, np.int64); LV = np.full(D.nd, np.nan)
        return _ev(np.concatenate([
            _lvl(*_base(D), F[f"ll{N}"], np.where(np.isnan(F[f"ll{N}"]), 0, 1).astype(np.int64), _nan(D), 1, 0.0, p["x"], 2, S(930), S(p["exp"]), S(p["exp"]), p["sk"], p["R"], p["tf"], 0.0),
            _lvl(*_base(D), F[f"hh{N}"], np.where(np.isnan(F[f"hh{N}"]), 0, -1).astype(np.int64), _nan(D), 1, 0.0, p["x"], 2, S(930), S(p["exp"]), S(p["exp"]), p["sk"], p["R"], p["tf"], 0.0)]))
    return _ev(_lvl(*_base(D), LV, DIR, _nan(D), 1, 0.0, p["x"], 2, S(930), S(p["exp"]), S(p["exp"]), p["sk"], p["R"], p["tf"], 0.0))


GRID_TSOUP = grid(src=("ts1", "tsi"), N=(10, 20), x=(0.0, 0.05), sk=(0.0, 0.35), R=(1.0, 2.0, 0.0), exp=(1200, 1500), tf=(0, 1, -1))


def gen_8020(D, p):
    F = _daily(D); A = D.atr; q = p["pct"]; big = F["rng1"] >= 0.75 * A
    bc = big & (F["posO"] >= 1 - q) & (F["posC"] <= q); sc = big & (F["posO"] <= q) & (F["posC"] >= 1 - q)
    DIR, LV = _dir_lv(bc, sc, F["pL"], F["pH"], D.nd)
    return _ev(_lvl(*_base(D), LV, DIR, _nan(D), 1, 0.0, p["x"], 2, S(930), S(p["exp"]), S(p["exp"]), p["sk"], p["R"], p["tf"], 0.0))


GRID_8020 = grid(pct=(0.2, 0.3), x=(0.05, 0.1), sk=(0.0, 0.25, 0.5), R=(1.0, 2.0, 0.0), exp=(1200, 1500), tf=(0, 1, -1))


def gen_pinball(D, p):
    F = _daily(D); H, L, C, OPN, FE = _orange(D.o, D.h, D.l, D.c, D.sm, D.ro, D.de, S(p["orl"]))
    DIR, LV = _dir_lv(F["rsi3roc"] < p["thr"], F["rsi3roc"] > 100 - p["thr"], H, L, D.nd)
    return _ev(_lvl(*_base(D), LV, DIR, _nan(D), 2, 0.0, 0.0, 2, S(p["orl"]) - 1, S(p["orl"]) - 1, S(p["exp"]), p["sk"], p["R"], p["tf"], 0.0))


GRID_PINBALL = grid(thr=(30.0, 20.0), orl=(1030, 1000), sk=(0.0, 0.25, 0.5), R=(1.0, 2.0, 0.0), exp=(1300, 1500), tf=(0, 1))


@njit(cache=True)
def _adx(h, l, c, n):
    m = len(c); pdi = np.zeros(m); mdi = np.zeros(m); adx = np.zeros(m)
    tr_s = 0.0; pd_s = 0.0; md_s = 0.0; dx_s = 0.0; a = 1.0 / n
    for i in range(1, m):
        tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        up = h[i] - h[i - 1]; dn = l[i - 1] - l[i]
        pdm = up if (up > dn and up > 0) else 0.0; mdm = dn if (dn > up and dn > 0) else 0.0
        if i <= n: tr_s += tr; pd_s += pdm; md_s += mdm
        else:
            tr_s = tr_s - tr_s * a + tr; pd_s = pd_s - pd_s * a + pdm; md_s = md_s - md_s * a + mdm
        if tr_s > 0: pdi[i] = 100 * pd_s / tr_s; mdi[i] = 100 * md_s / tr_s
        den = pdi[i] + mdi[i]; dx = 100 * abs(pdi[i] - mdi[i]) / den if den > 0 else 0.0
        if i <= 2 * n: dx_s += dx; adx[i] = dx_s / max(1, i - n) if i > n else 0.0
        else: adx[i] = adx[i - 1] + a * (dx - adx[i - 1])
    return pdi, mdi, adx


@njit(cache=True)
def _ema(c, n):
    m = len(c); e = np.zeros(m); a = 2.0 / (n + 1); e[0] = c[0]
    for i in range(1, m): e[i] = e[i - 1] + a * (c[i] - e[i - 1])
    return e


@njit(cache=True)
def _stoch(h, l, c, kp, ks, dp):
    m = len(c); raw = np.zeros(m); K = np.zeros(m); Dl = np.zeros(m)
    for i in range(m):
        if i < kp - 1: continue
        hi = -1e18; lo = 1e18
        for q in range(i - kp + 1, i + 1):
            if h[q] > hi: hi = h[q]
            if l[q] < lo: lo = l[q]
        raw[i] = 100 * (c[i] - lo) / (hi - lo) if hi > lo else 50.0
    for i in range(m):
        if i < kp - 1 + ks - 1: continue
        s = 0.0
        for q in range(i - ks + 1, i + 1): s += raw[q]
        K[i] = s / ks
    for i in range(m):
        if i < kp - 1 + ks - 1 + dp - 1: continue
        s = 0.0
        for q in range(i - dp + 1, i + 1): s += K[q]
        Dl[i] = s / dp
    return K, Dl


@njit(cache=True)
def _tfsig(bh, bl, bc, blast, bday, bsme, SIG, ro, de, sm, atr, trend, t0, t1, nb, sk, R, dtf, lowref):
    """Bar signals SIG[b] in {-1, 0, 1} on tf bars -> stop entry beyond the signal bar's extreme, valid nb bars; stop beyond the bar's / the
    pullback's extreme (lowref bars back, struct) or sk ATR."""
    m = len(bc); out = np.zeros((m, 8)); n = 0; lastday = -1
    for b in range(2, m - 1):
        s = SIG[b]
        if s == 0: continue
        d = bday[b]
        if ro[d] < 1 or atr[d] <= 0 or d == lastday: continue
        if bsme[b] < t0 or bsme[b] >= t1: continue
        if dtf == 1 and s != trend[d]: continue
        A = atr[d]; i = blast[b]
        if i + 1 > de[d] or sm[i + 1] < sm[i]: continue
        be = b + nb if b + nb < m else m - 1
        iexp = blast[be]
        if bday[be] != d: iexp = de[d]
        px = bh[b] + TICK if s == 1 else bl[b] - TICK
        if sk > 0: risk = sk * A
        else:
            ext = bl[b] if s == 1 else bh[b]
            for q in range(max(0, b - lowref + 1), b + 1):
                if s == 1 and bl[q] < ext: ext = bl[q]
                if s == -1 and bh[q] > ext: ext = bh[q]
            risk = (px - ext if s == 1 else ext - px) + TICK
            if risk < RMIN * A: risk = RMIN * A
            if risk > RMAX * A: continue
        sl = px - s * risk; tp = px + s * (R * risk if R > 0 else FAR * A)
        out[n, 0] = i; out[n, 1] = s; out[n, 2] = 2; out[n, 3] = px; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = iexp; out[n, 7] = HOLD; n += 1
        lastday = d
    return out[:n]


def gen_holygrail(D, p):
    B = D.bars(p["tf"]); pdi, mdi, adx = _adx(B["h"], B["l"], B["c"], 14); ema = _ema(B["c"], p["ema"])
    h, l, c = B["h"], B["l"], B["c"]
    pa = np.r_[0.0, adx[:-1]]; touch_lo = l <= ema; touch_hi = h >= ema
    ptl = np.r_[False, touch_lo[:-1]]; pth = np.r_[False, touch_hi[:-1]]
    ok = (adx > p["adx"]) & (adx >= pa)
    buy = ok & (pdi > mdi) & touch_lo & ~ptl                           # first bar whose low touches the EMA
    sell = ok & (mdi > pdi) & touch_hi & ~pth
    SIG = np.where(buy, 1, np.where(sell, -1, 0)).astype(np.int64)
    return _ev(_tfsig(h, l, c, B["last"], B["day"], B["sme"], SIG, D.ro, D.de, D.sm, D.atr.astype(np.float64), D.trend, S(945), S(1500), p["nb"], p["sk"], p["R"], p["dtf"], 1))


GRID_HOLYGRAIL = grid(tf=(15, 60), adx=(25.0, 30.0), ema=(10, 20), sk=(0.0, 0.3), R=(1.0, 2.0, 0.0), nb=(2, 4), dtf=(0, 1))


def gen_anti(D, p):
    B = D.bars(p["tf"]); K, Dl = _stoch(B["h"], B["l"], B["c"], p["kp"], 3, 10)
    K1 = np.r_[0.0, K[:-1]]; K2 = np.r_[0.0, 0.0, K[:-2]]; D1 = np.r_[0.0, Dl[:-1]]
    buy = (Dl > D1) & (K1 < K2) & (K > K1) & (K < 75) & (Dl > 0)
    sell = (Dl < D1) & (K1 > K2) & (K < K1) & (K > 25) & (Dl > 0)
    SIG = np.where(buy, 1, np.where(sell, -1, 0)).astype(np.int64)
    return _ev(_tfsig(B["h"], B["l"], B["c"], B["last"], B["day"], B["sme"], SIG, D.ro, D.de, D.sm, D.atr.astype(np.float64), D.trend, S(945), S(1500), p["nb"], p["sk"], p["R"], p["dtf"], 3))


GRID_ANTI = grid(tf=(15, 30), kp=(7, 14), sk=(0.0, 0.3), R=(1.0, 2.0, 0.0), nb=(2, 4), dtf=(0, 1))


# ------------------------------------------------------------------------------------------------ 3. Crabel
def _cond(F, name):
    if name == "any": return np.ones(len(F["pH"]), np.int64)
    if name == "NR4": return np.nan_to_num(F["nr4"]).astype(np.int64)
    if name == "IDNR4": return (np.nan_to_num(F["nr4"]).astype(bool) & np.nan_to_num(F["id"]).astype(bool)).astype(np.int64)
    if name == "NR2": return np.nan_to_num(F["nr2"]).astype(np.int64)
    raise ValueError(name)


def gen_crabel_nr(D, p):
    F = _daily(D); H, L, C, OPN, FE = _orange(D.o, D.h, D.l, D.c, D.sm, D.ro, D.de, S(p["orl"]))
    return _ev(_oco(*_base(D), H, L, _cond(F, p["cond"]), S(p["orl"]) - 1, S(p["exp"]), S(p["exp"]), p["sk"], p["R"], p["tf"], 0.0, 2))


GRID_CRABEL_NR = grid(cond=("NR4", "IDNR4", "NR2"), orl=(945, 1000), sk=(0.0, 0.25, 0.5), R=(1.0, 2.0, 0.0), exp=(1200, 1400), tf=(0, 1))


def gen_stretch(D, p):
    F = _daily(D); opn = np.full(D.nd, np.nan); m = D.ro >= 0; opn[m] = D.o[D.ro[m]]
    UP = opn + p["m"] * F["stretch"]; DN = opn - p["m"] * F["stretch"]
    return _ev(_oco(*_base(D), UP, DN, _cond(F, p["cond"]), S(930), S(p["exp"]), S(p["exp"]), p["sk"], p["R"], p["tf"], 0.0, 2))


GRID_STRETCH = grid(m=(1.0, 1.5), cond=("any", "NR4", "IDNR4"), sk=(0.0, 0.5), R=(1.0, 2.0, 0.0), exp=(1100, 1300, 1500), tf=(0, 1))


# ------------------------------------------------------------------------------------------------ 4. Connors daily mean reversion, intraday hold
def _cn_entry(D, p, bc, sc):
    F = _daily(D); A = D.atr
    if p["filt"]: bc = bc & (F["pC"] > F["sma200"]); sc = sc & (F["pC"] < F["sma200"])
    opn = np.full(D.nd, np.nan); m = D.ro >= 0; opn[m] = D.o[D.ro[m]]
    DIR, _ = _dir_lv(bc, sc, opn, opn, D.nd)
    if p["ent"] == "open":
        # market at the first bar after t0 (signal bar = the bar before t0; at 09:30 that is the last pre-market bar)
        LV = opn.copy(); t0 = S(p["t0"]) - 1
        return _lvl(*_base(D), LV, DIR, _nan(D), 2, 0.0, 0.0, 0, t0, t0, S(1500), p["sk"], p["R"], 0, 0.0)
    LV = opn.copy()
    return _lvl(*_base(D), LV, DIR, _nan(D), 2, 0.0, 0.0, 1, S(p["t0"]), S(p["t0"]), S(1200), p["sk"], p["R"], 0, 0.1)


def gen_double7(D, p):
    F = _daily(D); N = p["N"]
    return _ev(_cn_entry(D, p, np.nan_to_num(F[f"cmin{N}"]).astype(bool), np.nan_to_num(F[f"cmax{N}"]).astype(bool)))


GRID_DOUBLE7 = grid(N=(5, 7, 10), filt=(0, 1), ent=("open", "dip"), sk=(0.5, 1.0), R=(1.0, 2.0, 0.0), t0=(930, 1000))


def gen_pctb(D, p):
    F = _daily(D)
    return _ev(_cn_entry(D, p, F["pb"] < p["thr"], F["pb"] > 1 - p["thr"]))


GRID_PCTB = grid(thr=(0.0, 0.2), filt=(0, 1), ent=("open", "dip"), sk=(0.5, 1.0), R=(1.0, 2.0, 0.0), t0=(930, 1000))


def gen_r3(D, p):
    F = _daily(D); r1, r2, r3 = F["rsi2_1"], F["rsi2_2"], F["rsi2_3"]
    bc = (r1 < r2) & (r2 < r3) & (r3 < 60) & (r1 < p["thr3"]); sc = (r1 > r2) & (r2 > r3) & (r3 > 40) & (r1 > 100 - p["thr3"])
    return _ev(_cn_entry(D, p, bc, sc))


GRID_R3 = grid(thr3=(10.0, 20.0), filt=(0, 1), ent=("open", "dip"), sk=(0.5, 1.0), R=(1.0, 2.0, 0.0), t0=(930, 1000))


# ------------------------------------------------------------------------------------------------ 5. Taylor + Steidlmayer
def gen_taylor(D, p):
    F = _daily(D); pos = F["tlow"] if p["anchor"] == "low" else F["thigh"]
    # lowest-low anchor: lowest at 3 -> today Buy day, 1 -> Sell day, 2 -> Short-sale day; highest-high anchor: highest at 3 -> SS day,
    # 1 -> Buy day, 2 -> Sell day
    if p["anchor"] == "low": buyday = pos == 3; ssday = pos == 2
    else: buyday = pos == 1; ssday = pos == 3
    bc = buyday if p["days"] in ("bs", "b") else np.zeros(D.nd, bool); sc = ssday if p["days"] in ("bs", "s") else np.zeros(D.nd, bool)
    DIR, LV = _dir_lv(bc, sc, F["pL"], F["pH"], D.nd)
    TG = np.where(DIR == 1, F["pH"], F["pL"]); R = -1.0 if p["tgt"] == "prior" else float(p["tgt"])
    if p["mode"] == "viol":   # limit x ATR beyond yesterday's extreme, placed at 09:30 if price is on the near side
        return _ev(_lvl(*_base(D), LV, DIR, TG, 2, 0.0, 0.0, 1, S(930), S(930), S(p["exp"]), p["sk"], R, 0, p["x"]))
    return _ev(_lvl(*_base(D), LV, DIR, TG, 1, 0.0, p["x"], 2, S(930), S(p["exp"]), S(p["exp"]), p["sk"], R, 0, 0.0))


GRID_TAYLOR = grid(anchor=("low", "high"), mode=("viol", "fail"), x=(0.05, 0.1), sk=(0.25, 0.5), tgt=("prior", 1.0, 0.0), days=("bs", "b", "s"), exp=(1100, 1300))


def gen_steid(D, p):
    A = D.atr; W = p["W"]; tend = S(930) + W
    H, L, C, OPN, FE = _orange(D.o, D.h, D.l, D.c, D.sm, D.ro, D.de, tend)
    rng = H - L
    with np.errstate(invalid="ignore", divide="ignore"):
        po = (OPN - L) / rng; pc = (C - L) / rng
    big = rng >= p["x"] * A
    if p["typ"] == "auction":
        OK = ((rng <= p["x"] * A) & (po >= 0.3) & (po <= 0.7)).astype(np.int64)
        R = -1.0 if p["ent"] == "mkt" else p["R"]          # 'mkt' slot = target the range midpoint, 'stop' slot = R x risk
        return _ev(_oco(*_base(D), H, L, OK, tend - 1, S(1200), S(1200), p["sk"], R, p["tf"], 0.0, 1))
    if p["typ"] == "drive":
        bc = big & (po <= 0.15) & (pc >= 0.7); sc = big & (po >= 0.85) & (pc <= 0.3)
        blv = np.where(p["ent"] == "stop", H, C); slv = np.where(p["ent"] == "stop", L, C); bst = OPN; sst = OPN
    elif p["typ"] == "test":
        bc = big & (FE == -1) & (po > 0.15) & (po <= 0.5) & (pc >= 0.8); sc = big & (FE == 1) & (po < 0.85) & (po >= 0.5) & (pc <= 0.2)
        blv = np.where(p["ent"] == "stop", H, C); slv = np.where(p["ent"] == "stop", L, C); bst = L; sst = H
    else:   # rejection-reverse: the first extreme was made on one side, the W close is back across the open
        bc = big & (FE == -1) & (C > OPN) & (pc >= 0.6); sc = big & (FE == 1) & (C < OPN) & (pc <= 0.4)
        blv = np.where(p["ent"] == "stop", H, C); slv = np.where(p["ent"] == "stop", L, C); bst = L; sst = H
    DIR, LV = _dir_lv(bc, sc, blv, slv, D.nd)
    et = 2 if p["ent"] == "stop" else 0
    out = _lvl(*_base(D), LV, DIR, _nan(D), 2, 0.0, 0.0, et, tend - 1, tend - 1, S(1300), p["sk"], p["R"], p["tf"], 0.0)
    if p["sk"] == 0:      # structural stop = the open (drive) / the test extreme (test, rejrev): recompute sl/tp from the setup levels
        keep = []
        for row in out:
            d = D.day[int(row[0])]; s = int(row[1]); px = row[3]; st = bst[d] if s == 1 else sst[d]
            risk = (px - st if s == 1 else st - px) + TICK
            if risk < RMIN * A[d]: risk = RMIN * A[d]
            if risk > RMAX * A[d]: continue
            row = row.copy(); row[4] = px - s * risk; row[5] = px + s * (p["R"] * risk if p["R"] > 0 else FAR * A[d]); keep.append(row)
        out = np.array(keep) if keep else np.zeros((0, 8))
    return _ev(out)


GRID_STEID = grid(typ=("drive", "test", "rejrev", "auction"), W=(30, 60), x=(0.15, 0.3), ent=("mkt", "stop"), sk=(0.0, 0.3), R=(1.0, 2.0, 0.0), tf=(0, 1))

FAMILIES11 = {"LW_OOPS": (gen_oops, GRID_OOPS, 1), "LW_SMASH": (gen_smash, GRID_SMASH, 1), "LW_INOUT": (gen_inout, GRID_INOUT, 1),
              "RC_TSOUP": (gen_tsoup, GRID_TSOUP, 1), "RC_8020": (gen_8020, GRID_8020, 1), "RC_PINBALL": (gen_pinball, GRID_PINBALL, 1),
              "RC_HOLYGRAIL": (gen_holygrail, GRID_HOLYGRAIL, 1), "RC_ANTI": (gen_anti, GRID_ANTI, 1),
              "CRABEL_NR": (gen_crabel_nr, GRID_CRABEL_NR, 1), "CRABEL_STRETCH": (gen_stretch, GRID_STRETCH, 1),
              "CN_DOUBLE7": (gen_double7, GRID_DOUBLE7, 1), "CN_PCTB": (gen_pctb, GRID_PCTB, 1), "CN_R3": (gen_r3, GRID_R3, 1),
              "TAYLOR": (gen_taylor, GRID_TAYLOR, 1), "STEID_OPEN": (gen_steid, GRID_STEID, 1)}

if __name__ == "__main__":
    print({k: len(v[1]) for k, v in FAMILIES11.items()}, sum(len(v[1]) for v in FAMILIES11.values()))
