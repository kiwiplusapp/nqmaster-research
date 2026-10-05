"""Numba backtest engine for MNQ intraday research on 1-minute bars.

Conventions
- Bars are indexed by OPEN time; `om` = ET minute-of-day of the bar open.
- Market / stop fills pay 1 tick slippage. Limit fills require a trade-through by 1 tick and get no slippage.
- When stop and target are both inside the same bar, the STOP is assumed first (conservative).
- Every trade returns: entry_idx, exit_idx, dir, entry_px, exit_px, risk_pts, reason (1 target, -1 stop, 0 time/rule).
"""
import numpy as np
from numba import njit

TICK = 0.25
SLIP = 0.25
import os
COMM_PTS = float(os.environ.get("COMM_PTS", "0.5"))   # $1.00 RT per contract in points (MNQ 0.5, MES 0.2, MYM 2.0)
REOPEN = 18 * 60


@njit(cache=True)
def atr_nt(h, l, c, n):
    out = np.empty(len(c))
    out[0] = h[0] - l[0]
    for i in range(1, len(c)):
        tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        k = min(i + 1, n)
        out[i] = ((k - 1) * out[i - 1] + tr) / k
    return out


@njit(cache=True)
def walk_exit(o, h, l, c, om, dayid, i0, d, entry, stop, target, flat_om, target_on_entry_bar):
    """Walk from entry bar i0 until stop / target / flatten. Returns (exit_idx, exit_px, reason)."""
    n = len(c)
    day = dayid[i0]
    i = i0
    while i < n:
        if i > i0 and (dayid[i] != day or (om[i] >= flat_om and om[i] < REOPEN)):
            return i, o[i] - d * SLIP, 0
        if d == 1:
            if i > i0 and o[i] <= stop:
                return i, o[i] - SLIP, -1
            if l[i] <= stop:
                return i, stop - SLIP, -1
            if target > 0 and (i > i0 or target_on_entry_bar) and h[i] >= target + TICK:
                if i > i0 and o[i] >= target:
                    return i, o[i], 1
                return i, target, 1
        else:
            if i > i0 and o[i] >= stop:
                return i, o[i] + SLIP, -1
            if h[i] >= stop:
                return i, stop + SLIP, -1
            if target > 0 and (i > i0 or target_on_entry_bar) and l[i] <= target - TICK:
                if i > i0 and o[i] <= target:
                    return i, o[i], 1
                return i, target, 1
        # Flatten at the close of the last bar before the flatten time.
        if i + 1 < n and (dayid[i + 1] != day or (om[i + 1] >= flat_om and om[i + 1] < REOPEN)):
            return i, c[i] - d * SLIP, 0
        i += 1
    return n - 1, c[n - 1], 0


# ---------------------------------------------------------------------------
# 1) IFVG engine (exact port of the Pine indicator's hidden-FVG memory + inversion)
# ---------------------------------------------------------------------------
@njit(cache=True)
def ifvg_signals(o, h, l, c, atr, min_gap_atr, min_body, min_range_atr, break_atr,
                 line_mode, max_mem, max_age, entry_ref_mode, sl_mult, rr,
                 room_lb, vol_guard, adaptive, adapt_mult, adapt_lb):
    n = len(c)
    cap = max_mem + 3
    tops = np.zeros(cap); bots = np.zeros(cap); dirs = np.zeros(cap, np.int64); ages = np.zeros(cap, np.int64)
    ga = np.zeros(cap); br = np.zeros(cap); ra = np.zeros(cap)
    cnt = 0
    hist = np.zeros(adapt_lb + 3); hcnt = 0

    sig = np.zeros(n, np.int8)
    ref = np.full(n, np.nan)
    line = np.full(n, np.nan)
    ztop = np.full(n, np.nan)
    zbot = np.full(n, np.nan)
    risk = np.full(n, np.nan)
    g_vol = np.zeros(n, np.bool_)
    g_room = np.zeros(n, np.bool_)
    g_path = np.zeros(n, np.bool_)

    for i in range(2, n):
        safe = atr[i] if atr[i] > 0 else TICK
        # age + expiry
        j = cnt - 1
        while j >= 0:
            ages[j] += 1
            if ages[j] > max_age:
                for k in range(j, cnt - 1):
                    tops[k] = tops[k + 1]; bots[k] = bots[k + 1]; dirs[k] = dirs[k + 1]; ages[k] = ages[k + 1]
                    ga[k] = ga[k + 1]; br[k] = br[k + 1]; ra[k] = ra[k + 1]
                cnt -= 1
            j -= 1

        rng = max(h[i] - l[i], TICK)
        body = abs(c[i] - o[i]) / rng
        rng_atr = rng / safe

        if l[i] > h[i - 2]:
            g = (l[i] - h[i - 2]) / safe
            tops[cnt] = l[i]; bots[cnt] = h[i - 2]; dirs[cnt] = 1; ages[cnt] = 0
            ga[cnt] = g; br[cnt] = body; ra[cnt] = rng_atr; cnt += 1
            hist[hcnt] = g; hcnt += 1
        if h[i] < l[i - 2]:
            g = (l[i - 2] - h[i]) / safe
            tops[cnt] = l[i - 2]; bots[cnt] = h[i]; dirs[cnt] = -1; ages[cnt] = 0
            ga[cnt] = g; br[cnt] = body; ra[cnt] = rng_atr; cnt += 1
            hist[hcnt] = g; hcnt += 1
        while hcnt > adapt_lb:
            for k in range(hcnt - 1):
                hist[k] = hist[k + 1]
            hcnt -= 1
        while cnt > max_mem:
            for k in range(cnt - 1):
                tops[k] = tops[k + 1]; bots[k] = bots[k + 1]; dirs[k] = dirs[k + 1]; ages[k] = ages[k + 1]
                ga[k] = ga[k + 1]; br[k] = br[k + 1]; ra[k] = ra[k + 1]
            cnt -= 1

        buf = safe * break_atr
        found = 0
        ftop = 0.0; fbot = 0.0
        j = cnt - 1
        while j >= 0:
            bull = dirs[j] == -1 and c[i] > tops[j] + buf
            bear = dirs[j] == 1 and c[i] < bots[j] - buf
            if bull or bear:
                if adaptive:
                    s = 0.0
                    for k in range(hcnt):
                        s += hist[k]
                    avg = s / hcnt if hcnt > 0 else 0.0
                    gap_ok = ga[j] >= avg * adapt_mult
                else:
                    gap_ok = ga[j] >= min_gap_atr
                if gap_ok and br[j] >= min_body and ra[j] >= min_range_atr:
                    found = 1 if bull else -1
                    ftop = tops[j]; fbot = bots[j]
                for k in range(j, cnt - 1):
                    tops[k] = tops[k + 1]; bots[k] = bots[k + 1]; dirs[k] = dirs[k + 1]; ages[k] = ages[k + 1]
                    ga[k] = ga[k + 1]; br[k] = br[k + 1]; ra[k] = ra[k + 1]
                cnt -= 1
                break
            j -= 1

        if found == 0:
            continue

        if line_mode == 0:
            lp = ftop if found == 1 else fbot
        elif line_mode == 1:
            lp = c[i]
        else:
            lp = (ftop + fbot) / 2.0
        e = c[i] if entry_ref_mode == 1 else lp
        rk = atr[i] * sl_mult
        tp = e + found * rk * rr

        sig[i] = found; ref[i] = e; line[i] = lp; ztop[i] = ftop; zbot[i] = fbot; risk[i] = rk
        g_vol[i] = (not vol_guard) or (rng / safe <= 3.0)

        room_ok = True
        if i > room_lb:
            if found == 1:
                obs = -1e18
                for k in range(i - room_lb, i):
                    obs = max(obs, h[k])
                room_ok = obs >= tp or obs <= e
            else:
                obs = 1e18
                for k in range(i - room_lb, i):
                    obs = min(obs, l[k])
                room_ok = obs <= tp or obs >= e
        g_room[i] = room_ok

        blocked = False
        for k in range(cnt):
            if found == 1 and dirs[k] == -1 and bots[k] > e and bots[k] < tp:
                blocked = True
            if found == -1 and dirs[k] == 1 and tops[k] < e and tops[k] > tp:
                blocked = True
        g_path[i] = not blocked

    return sig, ref, line, ztop, zbot, risk, g_vol, g_room, g_path


@njit(cache=True)
def sim_ifvg(o, h, l, c, om, dayid, sig, ref, risk, gate, rr, mode, win_s, win_e, flat_om,
             limit_expiry, cancel_on_tp, min_risk, max_risk):
    """mode 0 = Pine virtual (assumes fill at ref on the signal close),
       mode 1 = market at next bar open, mode 2 = limit at ref (IFVG line)."""
    n = len(c)
    maxT = n // 20 + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    i = 0
    busy_until = -1
    while i < n - 1:
        if sig[i] == 0 or not gate[i] or i <= busy_until:
            i += 1
            continue
        if not (om[i] >= win_s and om[i] < win_e):
            i += 1
            continue
        d = int(sig[i])
        rk = max(risk[i], min_risk)
        if max_risk > 0 and rk > max_risk:
            i += 1
            continue
        if mode == 0:
            entry = ref[i]
            stop = entry - d * risk[i]
            tgt = entry + d * risk[i] * rr
            # Pine checks from the next bar, SL first, no flatten, no slippage.
            j = i + 1
            res = 0
            while j < n:
                hs = l[j] <= stop if d == 1 else h[j] >= stop
                ht = h[j] >= tgt if d == 1 else l[j] <= tgt
                if hs:
                    res = -1
                    break
                if ht:
                    res = 1
                    break
                j += 1
            if j >= n:
                break
            E[t] = i; X[t] = j; D[t] = d; EP[t] = entry; XP[t] = stop if res == -1 else tgt
            RK[t] = risk[i]; RS[t] = res; t += 1
            busy_until = j - 1   # Pine can arm a new trade on the same bar a trade closes? No: engine runs first.
            busy_until = j
            i += 1
            continue
        if mode == 1:
            j = i + 1
            if dayid[j] != dayid[i] or (om[j] >= flat_om and om[j] < REOPEN):
                i += 1
                continue
            entry = o[j] + d * SLIP
            stop = entry - d * rk
            tgt = entry + d * rk * rr
            xi, xp, rs = walk_exit(o, h, l, c, om, dayid, j, d, entry, stop, tgt, flat_om, True)
            E[t] = j; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
            busy_until = xi
            i += 1
            continue
        # mode 2: limit at ref
        lim = ref[i]
        stop = lim - d * rk
        tgt = lim + d * rk * rr
        filled = -1
        j = i + 1
        while j < n and j <= i + limit_expiry:
            if dayid[j] != dayid[i] or (om[j] >= flat_om and om[j] < REOPEN):
                break
            if d == 1 and l[j] <= lim - TICK:
                filled = j
                break
            if d == -1 and h[j] >= lim + TICK:
                filled = j
                break
            if cancel_on_tp and ((d == 1 and h[j] >= tgt) or (d == -1 and l[j] <= tgt)):
                break
            j += 1
        if filled < 0:
            busy_until = j
            i += 1
            continue
        entry = min(lim, o[filled]) if d == 1 else max(lim, o[filled])
        stop = entry - d * rk
        tgt = entry + d * rk * rr
        xi, xp, rs = walk_exit(o, h, l, c, om, dayid, filled, d, entry, stop, tgt, flat_om, False)
        E[t] = filled; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
        busy_until = xi
        i += 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 2) Opening Range Breakout
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_orb(o, h, l, c, om, dayid, open_idx, atr, or_len, mode, stop_mode, stop_param, rr,
            flat_om, last_entry_om, min_or_atr, max_or_atr, dir_filter, max_trades_day):
    """mode 0: Zarattini ORB - trade in the direction of the opening-range candle at the next bar open.
       mode 1: stop-order breakout of the OR high/low (first side hit).
       stop_mode 0: opposite OR extreme; 1: fraction of OR range from entry; 2: ATR(1m) multiple; 3: OR midpoint.
       dir_filter: per-day allowed direction array (0 = both)."""
    nd = len(open_idx)
    maxT = nd * max(1, max_trades_day) + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    n = len(c)
    for dd in range(nd):
        i0 = open_idx[dd]
        if i0 < 0:
            continue
        ie = i0 + or_len - 1
        if ie + 1 >= n or dayid[ie] != dayid[i0] or om[ie] != 570 + or_len - 1:
            continue
        orh = -1e18; orl = 1e18
        for k in range(i0, ie + 1):
            orh = max(orh, h[k]); orl = min(orl, l[k])
        rng = orh - orl
        a = atr[ie] * np.sqrt(or_len)
        if a <= 0 or rng / a < min_or_atr or (max_or_atr > 0 and rng / a > max_or_atr):
            continue
        allowed = dir_filter[dd]
        trades_today = 0
        j = ie + 1
        while j < n and dayid[j] == dayid[i0] and om[j] < last_entry_om and trades_today < max_trades_day:
            d = 0
            entry = 0.0
            if mode == 0:
                if trades_today > 0:
                    break
                d = 1 if c[ie] > o[i0] else (-1 if c[ie] < o[i0] else 0)
                if d == 0:
                    break
                entry = o[j] + d * SLIP
            else:
                up = h[j] >= orh + TICK
                dn = l[j] <= orl - TICK
                if up and dn:
                    break
                if up:
                    d = 1
                    entry = max(o[j], orh + TICK) + SLIP
                elif dn:
                    d = -1
                    entry = min(o[j], orl - TICK) - SLIP
                else:
                    j += 1
                    continue
            if allowed != 0 and d != allowed:
                if mode == 0:
                    break
                j += 1
                continue
            if stop_mode == 0:
                stop = orl if d == 1 else orh
            elif stop_mode == 1:
                stop = entry - d * stop_param * rng
            elif stop_mode == 2:
                stop = entry - d * stop_param * atr[j - 1]
            else:
                stop = (orh + orl) / 2.0
            rk = (entry - stop) * d
            if rk <= TICK:
                break
            tgt = entry + d * rk * rr if rr > 0 else -1.0
            xi, xp, rs = walk_exit(o, h, l, c, om, dayid, j, d, entry, stop, tgt, flat_om, mode == 0)
            E[t] = j; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
            trades_today += 1
            j = xi + 1
            if mode == 1:
                # After a stop-out only allow the opposite side (classic ORB re-entry).
                pass
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 3) Intraday momentum / noise area (Zarattini, Aziz & Barbon 2024)
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_noise(o, h, l, c, v, om, open_idx, prev_close, sigma, band_mult, check_every, first_entry_min,
              last_entry_min, flat_om, hard_stop_mult, use_vwap, rr_cap, dir_filter):
    """sigma[d, k]: average |close/open - 1| at minute k over the prior 14 days.
       Entries only at decision times (every `check_every` minutes on the half hour grid).
       Trailing stop = max(UB, VWAP) for longs (min(LB, VWAP) for shorts), checked at decision times.
       Hard stop = hard_stop_mult * band half-width (in price) from entry, checked intrabar."""
    nd = len(open_idx)
    maxT = nd * 8 + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    n = len(c)
    for dd in range(1, nd):
        i0 = open_idx[dd]
        if i0 < 0 or np.isnan(prev_close[dd]) or np.isnan(sigma[dd, 30]):
            continue
        op = o[i0]
        hi_ref = max(op, prev_close[dd]); lo_ref = min(op, prev_close[dd])
        pv = 0.0; vv = 0.0
        pos = 0; entry = 0.0; hard = 0.0; rk = 0.0; ei = -1
        allowed = dir_filter[dd]
        for k in range(390):
            i = i0 + k
            if i >= n or om[i] != 570 + k:
                break
            vol = v[i] if use_vwap == 1 else 1.0
            pv += (h[i] + l[i] + c[i]) / 3.0 * vol
            vv += vol
            vwap = pv / vv if vv > 0 else c[i]
            s = sigma[dd, k] * band_mult
            ub = hi_ref * (1 + s); lb = lo_ref * (1 - s)
            tclose = 570 + k + 1
            # intrabar hard stop
            if pos != 0 and i > ei:
                if pos == 1 and l[i] <= hard:
                    xp = min(o[i], hard) - SLIP
                    E[t] = ei; X[t] = i; D[t] = 1; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = -1; t += 1
                    pos = 0
                elif pos == -1 and h[i] >= hard:
                    xp = max(o[i], hard) + SLIP
                    E[t] = ei; X[t] = i; D[t] = -1; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = -1; t += 1
                    pos = 0
                elif rr_cap > 0 and pos == 1 and h[i] >= entry + rr_cap * rk + TICK:
                    E[t] = ei; X[t] = i; D[t] = 1; EP[t] = entry; XP[t] = entry + rr_cap * rk; RK[t] = rk; RS[t] = 1; t += 1
                    pos = 0
                elif rr_cap > 0 and pos == -1 and l[i] <= entry - rr_cap * rk - TICK:
                    E[t] = ei; X[t] = i; D[t] = -1; EP[t] = entry; XP[t] = entry - rr_cap * rk; RK[t] = rk; RS[t] = 1; t += 1
                    pos = 0
            if tclose >= flat_om:
                if pos != 0:
                    xp = c[i] - pos * SLIP
                    E[t] = ei; X[t] = i; D[t] = pos; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = 0; t += 1
                    pos = 0
                break
            decision = (tclose - 570) % check_every == 0
            if not decision:
                continue
            if pos == 1:
                trail = max(ub, vwap) if use_vwap >= 0 else ub
                if c[i] < trail:
                    xp = o[i + 1] - SLIP
                    E[t] = ei; X[t] = i + 1; D[t] = 1; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = 0; t += 1
                    pos = 0
            elif pos == -1:
                trail = min(lb, vwap) if use_vwap >= 0 else lb
                if c[i] > trail:
                    xp = o[i + 1] + SLIP
                    E[t] = ei; X[t] = i + 1; D[t] = -1; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = 0; t += 1
                    pos = 0
            if pos == 0 and tclose >= first_entry_min and tclose <= last_entry_min and (tclose - 570) % 30 == 0:
                d = 0
                if c[i] > ub and (allowed == 0 or allowed == 1):
                    d = 1
                elif c[i] < lb and (allowed == 0 or allowed == -1):
                    d = -1
                if d != 0 and i + 1 < n:
                    entry = o[i + 1] + d * SLIP
                    half = (ub - lb) / 2.0
                    rk = hard_stop_mult * half
                    hard = entry - d * rk
                    pos = d
                    ei = i + 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 4) ICT Silver Bullet style FVG retrace
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_fvg_window(o, h, l, c, om, dayid, open_idx, atr, win_s, win_e, min_gap_atr, entry_mode,
                   stop_mode, rr, flat_om, expiry_bars, dir_filter, max_trades_day):
    """FVG formed inside [win_s, win_e) ET (bar-open minutes). Limit entry on retrace into the gap.
       entry_mode 0: near edge, 1: midpoint. stop_mode 0: beyond candle-1 extreme, 1: beyond candle-2 extreme."""
    nd = len(open_idx)
    maxT = nd * max(1, max_trades_day) + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    n = len(c)
    for dd in range(nd):
        i0 = open_idx[dd]
        if i0 < 0:
            continue
        allowed = dir_filter[dd]
        trades = 0
        i = i0 + (win_s - 570)
        while i < n and trades < max_trades_day:
            if dayid[i] != dayid[i0] or om[i] >= win_e:
                break
            if i - 2 < i0:
                i += 1
                continue
            d = 0
            if l[i] > h[i - 2] and (l[i] - h[i - 2]) >= min_gap_atr * atr[i]:
                d = 1
            elif h[i] < l[i - 2] and (l[i - 2] - h[i]) >= min_gap_atr * atr[i]:
                d = -1
            if d == 0 or (allowed != 0 and d != allowed):
                i += 1
                continue
            if d == 1:
                top = l[i]; bot = h[i - 2]
                lim = top if entry_mode == 0 else (top + bot) / 2.0
                stop = l[i - 2] - TICK if stop_mode == 0 else l[i - 1] - TICK
            else:
                top = l[i - 2]; bot = h[i]
                lim = bot if entry_mode == 0 else (top + bot) / 2.0
                stop = h[i - 2] + TICK if stop_mode == 0 else h[i - 1] + TICK
            rk = (lim - stop) * d
            if rk <= TICK:
                i += 1
                continue
            tgt = lim + d * rr * rk
            filled = -1
            j = i + 1
            while j < n and j <= i + expiry_bars:
                if dayid[j] != dayid[i] or om[j] >= flat_om:
                    break
                if d == 1 and l[j] <= lim - TICK:
                    filled = j
                    break
                if d == -1 and h[j] >= lim + TICK:
                    filled = j
                    break
                if (d == 1 and h[j] >= tgt) or (d == -1 and l[j] <= tgt):
                    break
                j += 1
            if filled < 0:
                i += 1
                continue
            entry = min(lim, o[filled]) if d == 1 else max(lim, o[filled])
            rk = (entry - stop) * d
            tgt = entry + d * rr * rk
            xi, xp, rs = walk_exit(o, h, l, c, om, dayid, filled, d, entry, stop, tgt, flat_om, False)
            E[t] = filled; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
            trades += 1
            i = xi + 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 5) Overnight-range liquidity sweep reversal (Judas swing / turtle soup)
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_sweep(o, h, l, c, om, dayid, open_idx, win_end, rr, stop_buf_ticks, flat_om, min_sweep_ticks, dir_filter):
    """Overnight range = 18:00-09:29 ET. After 09:30, if price trades above ONH and a bar then CLOSES back
    below ONH (before win_end), short at the next open; stop above the sweep extreme; target rr*R.
    Mirror for ONL. One trade per day, first trigger wins."""
    nd = len(open_idx)
    maxT = nd + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    n = len(c)
    for dd in range(nd):
        i0 = open_idx[dd]
        if i0 < 0:
            continue
        # overnight range: walk back while same session day
        k = i0 - 1
        onh = -1e18; onl = 1e18
        while k >= 0 and dayid[k] == dayid[i0]:
            onh = max(onh, h[k]); onl = min(onl, l[k])
            k -= 1
        if onh < 0 or onl > 1e17:
            continue
        allowed = dir_filter[dd]
        hi_ext = -1e18; lo_ext = 1e18
        swept_hi = False; swept_lo = False
        j = i0
        while j + 1 < n and dayid[j] == dayid[i0] and om[j] < win_end:
            hi_ext = max(hi_ext, h[j]); lo_ext = min(lo_ext, l[j])
            if h[j] >= onh + min_sweep_ticks * TICK:
                swept_hi = True
            if l[j] <= onl - min_sweep_ticks * TICK:
                swept_lo = True
            d = 0
            if swept_hi and c[j] < onh and (allowed == 0 or allowed == -1):
                d = -1
            elif swept_lo and c[j] > onl and (allowed == 0 or allowed == 1):
                d = 1
            if d != 0:
                e_i = j + 1
                entry = o[e_i] + d * SLIP
                stop = hi_ext + stop_buf_ticks * TICK if d == -1 else lo_ext - stop_buf_ticks * TICK
                rk = (entry - stop) * d
                if rk > TICK:
                    tgt = entry + d * rr * rk
                    xi, xp, rs = walk_exit(o, h, l, c, om, dayid, e_i, d, entry, stop, tgt, flat_om, True)
                    E[t] = e_i; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
                break
            j += 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 6) Opening gap fade toward the prior RTH close
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_gap(o, h, l, c, om, dayid, open_idx, prev_close, atr_day, min_gap, max_gap, stop_mult, fill_frac, delay, flat_om):
    """Gap = RTH open - prior RTH close, measured in daily-ATR units (atr_day per day).
    Fade: enter at the open of bar 09:30+delay against the gap, target = fill_frac of the gap,
    stop = stop_mult * gap beyond the entry."""
    nd = len(open_idx)
    maxT = nd + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    n = len(c)
    for dd in range(1, nd):
        i0 = open_idx[dd]
        if i0 < 0 or np.isnan(prev_close[dd]) or np.isnan(atr_day[dd]) or atr_day[dd] <= 0:
            continue
        gap = o[i0] - prev_close[dd]
        g = abs(gap) / atr_day[dd]
        if g < min_gap or g > max_gap:
            continue
        e_i = i0 + delay
        if e_i >= n or dayid[e_i] != dayid[i0]:
            continue
        d = -1 if gap > 0 else 1
        entry = o[e_i] + d * SLIP
        tgt = o[i0] - gap * fill_frac
        if (tgt - entry) * d <= TICK:
            continue
        rk = stop_mult * abs(gap)
        stop = entry - d * rk
        xi, xp, rs = walk_exit(o, h, l, c, om, dayid, e_i, d, entry, stop, tgt, flat_om, True)
        E[t] = e_i; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 2b) ORB v2 - confirmation entries, capped stops, breakeven, per-day filters
# ---------------------------------------------------------------------------
@njit(cache=True)
def walk_exit_be(o, h, l, c, om, dayid, i0, d, entry, stop, target, flat_om, target_on_entry_bar, be_r, be_off):
    """walk_exit with an optional breakeven move once price has traveled be_r * R (checked on bar close)."""
    n = len(c)
    day = dayid[i0]
    rk = (entry - stop) * d
    moved = False
    i = i0
    while i < n:
        if i > i0 and (dayid[i] != day or (om[i] >= flat_om and om[i] < REOPEN)):
            return i, o[i] - d * SLIP, 0
        if d == 1:
            if i > i0 and o[i] <= stop:
                return i, o[i] - SLIP, (0 if moved else -1)
            if l[i] <= stop:
                return i, stop - SLIP, (0 if moved else -1)
            if target > 0 and (i > i0 or target_on_entry_bar) and h[i] >= target + TICK:
                if i > i0 and o[i] >= target:
                    return i, o[i], 1
                return i, target, 1
            if be_r > 0 and not moved and c[i] >= entry + be_r * rk:
                stop = entry + be_off
                moved = True
        else:
            if i > i0 and o[i] >= stop:
                return i, o[i] + SLIP, (0 if moved else -1)
            if h[i] >= stop:
                return i, stop + SLIP, (0 if moved else -1)
            if target > 0 and (i > i0 or target_on_entry_bar) and l[i] <= target - TICK:
                if i > i0 and o[i] <= target:
                    return i, o[i], 1
                return i, target, 1
            if be_r > 0 and not moved and c[i] <= entry - be_r * rk:
                stop = entry - be_off
                moved = True
        if i + 1 < n and (dayid[i + 1] != day or (om[i + 1] >= flat_om and om[i + 1] < REOPEN)):
            return i, c[i] - d * SLIP, 0
        i += 1
    return n - 1, c[n - 1], 0


@njit(cache=True)
def sim_orb2(o, h, l, c, om, dayid, open_idx, atr_day, or_len, entry_mode, stop_mode, stop_k, rr,
             flat_om, last_entry_om, day_dir, day_ok, be_r, max_trades_day, max_stop_pts, or_start=570):
    """entry_mode 0: stop order at OR high/low (+1 tick). 1: bar CLOSE beyond OR -> next bar open.
       stop_mode 0: opposite OR extreme; 1: OR midpoint; 2: k * daily ATR from entry; 3: min(opposite, k*ATRd).
       day_dir: allowed direction per day (0 both). day_ok: day filter. max_stop_pts>0 skips wider stops."""
    nd = len(open_idx)
    maxT = nd * max(1, max_trades_day) + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    n = len(c)
    for dd in range(nd):
        i0 = open_idx[dd]
        if i0 < 0 or not day_ok[dd] or np.isnan(atr_day[dd]):
            continue
        ie = i0 + or_len - 1
        if ie + 1 >= n or dayid[ie] != dayid[i0] or om[ie] != (or_start + or_len - 1) % 1440:
            continue
        orh = -1e18; orl = 1e18
        for k in range(i0, ie + 1):
            orh = max(orh, h[k]); orl = min(orl, l[k])
        mid = (orh + orl) / 2.0
        allowed = day_dir[dd]
        trades = 0
        last_dir = 0
        j = ie + 1
        while j < n and dayid[j] == dayid[i0] and om[j] < last_entry_om and trades < max_trades_day:
            d = 0
            entry = 0.0
            ei = j
            if entry_mode == 0:
                up = h[j] >= orh + TICK
                dn = l[j] <= orl - TICK
                if up and dn:
                    break
                if up and last_dir != 1:
                    d = 1; entry = max(o[j], orh + TICK) + SLIP
                elif dn and last_dir != -1:
                    d = -1; entry = min(o[j], orl - TICK) - SLIP
            else:
                if c[j] > orh and last_dir != 1:
                    d = 1
                elif c[j] < orl and last_dir != -1:
                    d = -1
                if d != 0:
                    ei = j + 1
                    if ei >= n or dayid[ei] != dayid[i0] or om[ei] >= flat_om:
                        break
                    entry = o[ei] + d * SLIP
            if d == 0:
                j += 1
                continue
            if allowed != 0 and d != allowed:
                j += 1
                continue
            if stop_mode == 0:
                stop = orl - TICK if d == 1 else orh + TICK
            elif stop_mode == 1:
                stop = mid
            elif stop_mode == 2:
                stop = entry - d * stop_k * atr_day[dd]
            else:
                s_opp = orl - TICK if d == 1 else orh + TICK
                s_atr = entry - d * stop_k * atr_day[dd]
                stop = max(s_opp, s_atr) if d == 1 else min(s_opp, s_atr)
            rk = (entry - stop) * d
            if rk <= 2 * TICK or (max_stop_pts > 0 and rk > max_stop_pts):
                j += 1
                if entry_mode == 1:
                    j = ei
                last_dir = d
                continue
            tgt = entry + d * rk * rr if rr > 0 else -1.0
            xi, xp, rs = walk_exit_be(o, h, l, c, om, dayid, ei, d, entry, stop, tgt, flat_om, entry_mode == 1, be_r, TICK)
            E[t] = ei; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
            trades += 1
            last_dir = d
            j = xi + 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 7) NY-open FVG with an exactly implementable order policy (bar-by-bar state machine)
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_open_fvg(o, h, l, c, om, dayid, open_idx, atr, win_s, win_e, min_gap_atr, rr, flat_om,
                 expiry, policy, max_trades_day, dir_filter, max_stop_pts):
    """Processed bar by bar exactly like the NinjaScript (Calculate.OnBarClose):
       - at the close of bar i inside [win_s+2, win_e) a new FVG (bull: l[i] > h[i-2]) with gap >= min_gap_atr*ATR
         arms a limit at the FVG near edge (bull: l[i], bear: h[i]); stop beyond candle-1 extreme; target rr*R.
       - policy 0: the newest FVG replaces an unfilled pending limit. policy 1: keep the first pending limit.
       - pending limit: fills on a trade-through from the next bar; cancelled after `expiry` bars or when price
         reaches the target first; never fills at/after flat_om.
       - one position at a time, max_trades_day fills per day."""
    nd = len(open_idx)
    maxT = nd * max(1, max_trades_day) + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    n = len(c)
    for dd in range(nd):
        i0 = open_idx[dd]
        if i0 < 0:
            continue
        allowed = dir_filter[dd]
        trades = 0
        pend = 0; lim = 0.0; stp = 0.0; tgt = 0.0; pbar = -1
        j = i0 + 2
        while j < n and dayid[j] == dayid[i0] and om[j] < flat_om:
            # 1) pending order interacts with bar j (order was placed at the close of an earlier bar)
            if pend != 0 and j > pbar:
                filled = False
                if pend == 1 and l[j] <= lim - TICK:
                    filled = True
                elif pend == -1 and h[j] >= lim + TICK:
                    filled = True
                if filled:
                    d = pend
                    entry = min(lim, o[j]) if d == 1 else max(lim, o[j])
                    rk = (entry - stp) * d
                    target = entry + d * rr * rk
                    xi, xp, rs = walk_exit(o, h, l, c, om, dayid, j, d, entry, stp, target, flat_om, False)
                    E[t] = j; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
                    trades += 1
                    pend = 0
                    if trades >= max_trades_day:
                        break
                    j = xi + 1
                    continue
                if (pend == 1 and h[j] >= tgt) or (pend == -1 and l[j] <= tgt) or j - pbar >= expiry:
                    pend = 0
            # 2) signal at the close of bar j
            if om[j] >= win_s + 2 and om[j] < win_e and j - 2 >= i0:
                d = 0
                a = atr[j]
                if l[j] > h[j - 2] and (l[j] - h[j - 2]) >= min_gap_atr * a:
                    d = 1
                elif h[j] < l[j - 2] and (l[j - 2] - h[j]) >= min_gap_atr * a:
                    d = -1
                if d != 0 and (allowed == 0 or allowed == d) and (pend == 0 or policy == 0):
                    nl = l[j] if d == 1 else h[j]
                    ns = l[j - 2] - TICK if d == 1 else h[j - 2] + TICK
                    rk = (nl - ns) * d
                    if rk > 2 * TICK and (max_stop_pts <= 0 or rk <= max_stop_pts):
                        pend = d; lim = nl; stp = ns; tgt = nl + d * rr * rk; pbar = j
            j += 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]



# ---------------------------------------------------------------------------
# 8) Last-half-hour intraday momentum (Gao, Han, Li & Zhou 2018)
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_lasthalf(o, h, l, c, om, dayid, open_idx, prev_close, atr_day, sig_end_om, entry_om, stop_k, flat_om, min_ret_atr):
    """Sign of the return from the prior RTH close to the close of bar `sig_end_om` decides the direction;
    enter at the open of bar `entry_om`, stop = stop_k * daily ATR, exit at flat_om."""
    nd = len(open_idx)
    E = np.zeros(nd + 10, np.int64); X = np.zeros(nd + 10, np.int64); D = np.zeros(nd + 10, np.int64)
    EP = np.zeros(nd + 10); XP = np.zeros(nd + 10); RK = np.zeros(nd + 10); RS = np.zeros(nd + 10, np.int64)
    t = 0
    n = len(c)
    for dd in range(1, nd):
        i0 = open_idx[dd]
        if i0 < 0 or np.isnan(prev_close[dd]) or np.isnan(atr_day[dd]):
            continue
        si = i0 + (sig_end_om - 570)
        ei = i0 + (entry_om - 570)
        if ei >= n or om[si] != sig_end_om or om[ei] != entry_om:
            continue
        r = c[si] - prev_close[dd]
        if abs(r) < min_ret_atr * atr_day[dd]:
            continue
        d = 1 if r > 0 else -1
        entry = o[ei] + d * SLIP
        rk = stop_k * atr_day[dd]
        xi, xp, rs = walk_exit(o, h, l, c, om, dayid, ei, d, entry, entry - d * rk, -1.0, flat_om, True)
        E[t] = ei; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 9) Generic range-breakout state machine (NinjaScript-implementable)
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_range(o, h, l, c, om, dayid, start_idx, atr_day, rs, rlen, le, flat_om, day_dir, dir_mode,
              entry_type, stop_mode, stop_cap, rr, be_r, max_trades, retest_bars, day_ok):
    """Range = bars opening in [rs, rs+rlen). After it completes, until `le` (bar-open minute):
       entry_type 0: stop order 1 tick beyond the range (both sides if dir_mode==1, trend side if 0).
       entry_type 1: breakout-retest: after a bar CLOSES beyond the range, a limit at the broken edge
                     waits `retest_bars` bars; cancelled if the target is reached first.
       stop_mode 0: opposite side capped at stop_cap*ATRd; 1: range midpoint capped; 2: stop_cap*ATRd flat.
       Re-entry (max_trades>1): only after price CLOSES back inside the range (re-arms from the next bar)."""
    nd = len(start_idx)
    maxT = nd * max(1, max_trades) + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    n = len(c)
    for dd in range(nd):
        i0 = start_idx[dd]
        if i0 < 0 or not day_ok[dd] or np.isnan(atr_day[dd]):
            continue
        ie = i0 + rlen - 1
        if ie + 1 >= n or dayid[ie] != dayid[i0] or om[ie] != (rs + rlen - 1) % 1440:
            continue
        rh = -1e18; rl = 1e18
        for k in range(i0, ie + 1):
            rh = max(rh, h[k]); rl = min(rl, l[k])
        mid = (rh + rl) / 2.0
        tdir = day_dir[dd]
        if dir_mode == 0 and tdir == 0:
            continue
        long_ok = dir_mode == 1 or tdir == 1
        short_ok = dir_mode == 1 or tdir == -1
        cap = stop_cap * atr_day[dd]
        trades = 0
        armed = True
        pend = 0; plim = 0.0; pbar = -1; pstop = 0.0
        j = ie + 1
        while j < n and dayid[j] == dayid[i0] and om[j] < flat_om and trades < max_trades:
            if om[j] >= le and pend == 0:
                break
            d = 0; entry = 0.0; stop = 0.0
            if entry_type == 0:
                if armed and om[j] < le:
                    up = long_ok and h[j] >= rh + TICK
                    dn = short_ok and l[j] <= rl - TICK
                    if up and dn:
                        up = abs(o[j] - rh) <= abs(o[j] - rl)
                        dn = not up
                    if up:
                        d = 1; entry = max(o[j], rh + TICK) + SLIP
                    elif dn:
                        d = -1; entry = min(o[j], rl - TICK) - SLIP
                    if d != 0:
                        if stop_mode == 0:
                            s0 = rl - TICK if d == 1 else rh + TICK
                        elif stop_mode == 1:
                            s0 = mid
                        else:
                            s0 = entry - d * cap
                        dist = min((entry - s0) * d, cap)
                        stop = entry - d * dist
                ei = j
            else:
                ei = j
                if pend != 0 and j > pbar:
                    if (pend == 1 and l[j] <= plim - TICK) or (pend == -1 and h[j] >= plim + TICK):
                        d = pend
                        entry = min(plim, o[j]) if d == 1 else max(plim, o[j])
                        stop = pstop
                        pend = 0
                    else:
                        dist0 = (plim - pstop) * pend
                        tgt0 = plim + pend * rr * dist0
                        if (pend == 1 and h[j] >= tgt0) or (pend == -1 and l[j] <= tgt0) or j - pbar >= retest_bars:
                            pend = 0
                if d == 0 and pend == 0 and armed and om[j] < le:
                    bd = 0
                    if long_ok and c[j] > rh:
                        bd = 1
                    elif short_ok and c[j] < rl:
                        bd = -1
                    if bd != 0:
                        edge = rh if bd == 1 else rl
                        if stop_mode == 0:
                            s0 = rl - TICK if bd == 1 else rh + TICK
                        elif stop_mode == 1:
                            s0 = mid
                        else:
                            s0 = edge - bd * cap
                        dist = min((edge - s0) * bd, cap)
                        pend = bd; plim = edge; pstop = edge - bd * dist; pbar = j
                        armed = False
            if d != 0:
                rk = (entry - stop) * d
                if rk > 2 * TICK:
                    tgt = entry + d * rr * rk if rr > 0 else -1.0
                    xi, xp, rs_ = walk_exit_be(o, h, l, c, om, dayid, ei, d, entry, stop, tgt, flat_om,
                                                entry_type == 1 and False, be_r, TICK)
                    E[t] = ei; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs_; t += 1
                    trades += 1
                    armed = False
                    j = xi + 1
                    continue
                armed = False
            # re-arm after price closes back inside the range
            if not armed and pend == 0 and trades < max_trades and c[j] < rh and c[j] > rl:
                armed = True
            j += 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 10) Trend-day VWAP pullback (after the opening range breaks in the trend direction)
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_vwap_pullback(o, h, l, c, v, om, dayid, open_idx, atr_day, day_dir, rlen, start_om, last_om, flat_om,
                      ext_k, stop_k, rr, max_trades, use_vol):
    """Long days (day_dir=+1): once a bar CLOSES above the opening-range high and at least ext_k*ATRd above VWAP,
       rest a buy limit at the previous bar's VWAP. Stop = stop_k*ATRd below entry, target rr*R.
       After each exit the setup must re-extend before a new limit is placed. Mirror for shorts."""
    nd = len(open_idx)
    maxT = nd * max(1, max_trades) + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    n = len(c)
    for dd in range(nd):
        i0 = open_idx[dd]
        d = day_dir[dd]
        if i0 < 0 or d == 0 or np.isnan(atr_day[dd]):
            continue
        a = atr_day[dd]
        orh = -1e18; orl = 1e18
        pv = 0.0; vv = 0.0
        trades = 0
        armed = False
        vw_prev = 0.0
        j = i0
        while j < n and dayid[j] == dayid[i0] and om[j] < flat_om and trades < max_trades:
            if om[j] < 570 + rlen:
                orh = max(orh, h[j]); orl = min(orl, l[j])
            # pending limit at previous VWAP
            if armed and om[j] < last_om and j > i0:
                lim = vw_prev
                hit = (d == 1 and l[j] <= lim - TICK) or (d == -1 and h[j] >= lim + TICK)
                if hit:
                    entry = min(lim, o[j]) if d == 1 else max(lim, o[j])
                    rk = stop_k * a
                    xi, xp, rs = walk_exit(o, h, l, c, om, dayid, j, d, entry, entry - d * rk, entry + d * rr * rk, flat_om, False)
                    E[t] = j; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
                    trades += 1
                    armed = False
                    # rebuild VWAP through the exit bar
                    for k in range(j, xi + 1):
                        w = v[k] if use_vol else 1.0
                        pv += (h[k] + l[k] + c[k]) / 3.0 * w; vv += w
                    vw_prev = pv / vv
                    j = xi + 1
                    continue
            w = v[j] if use_vol else 1.0
            pv += (h[j] + l[j] + c[j]) / 3.0 * w; vv += w
            vw = pv / vv
            if om[j] >= start_om and om[j] < last_om and not armed:
                if d == 1 and c[j] > orh and c[j] >= vw + ext_k * a:
                    armed = True
                elif d == -1 and c[j] < orl and c[j] <= vw - ext_k * a:
                    armed = True
            vw_prev = vw
            j += 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 11) Mean reversion (high win-rate family): fade deviations from an anchor back toward it
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_meanrev(o, h, l, c, v, om, dayid, atr_day, day_dir, sess_start, first_entry, last_entry, flat_om,
                anchor_mode, roll_n, k_dev, tgt_frac, stop_k, max_trades, dir_mode, use_vol, cooldown):
    """Anchor: 0 = session VWAP from `sess_start` (bar-open minute, may be >= 18:00 for Globex),
               1 = rolling mean of the last roll_n closes; deviation measured in units of daily ATR.
       Signal at bar close when |close - anchor| >= k_dev * ATRd -> market entry next open toward the anchor.
       Target = entry moves tgt_frac of the deviation back (1.0 = anchor). Stop = stop_k * ATRd.
       dir_mode: 0 both, 1 only against the daily bias (counter-trend fades), 2 only with the bias
       (fade pullbacks = buy dips in uptrend). Session minutes are handled on a 18:00-based clock."""
    n = len(c)
    maxT = n // 50 + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    cur_day = -1
    pv = 0.0; vv = 0.0; trades = 0; last_exit = -100000
    ssum = 0.0
    i = 1
    while i < n - 1:
        dd = dayid[i]
        # minutes on an 18:00-based clock so Globex windows are monotonic
        m = (om[i] - 1080) % 1440
        s0 = (sess_start - 1080) % 1440
        fe = (first_entry - 1080) % 1440
        le = (last_entry - 1080) % 1440
        fl = (flat_om - 1080) % 1440
        if dd != cur_day:
            cur_day = dd; pv = 0.0; vv = 0.0; trades = 0
        a = atr_day[dd]
        if np.isnan(a) or a <= 0 or m < s0:
            i += 1
            continue
        w = v[i] if use_vol else 1.0
        pv += (h[i] + l[i] + c[i]) / 3.0 * w; vv += w
        if anchor_mode == 0:
            anc = pv / vv
        else:
            if i < roll_n:
                i += 1
                continue
            s = 0.0
            for k in range(i - roll_n + 1, i + 1):
                s += c[k]
            anc = s / roll_n
        if m + 1 < fe or m + 1 > le or trades >= max_trades or i - last_exit < cooldown:
            i += 1
            continue
        dev = c[i] - anc
        d = 0
        if dev >= k_dev * a:
            d = -1
        elif dev <= -k_dev * a:
            d = 1
        if d != 0:
            bias = day_dir[dd]
            if dir_mode == 1 and not (bias != 0 and d == -bias):
                d = 0
            elif dir_mode == 2 and not (bias != 0 and d == bias):
                d = 0
        if d == 0:
            i += 1
            continue
        j = i + 1
        if dayid[j] != dd:
            i += 1
            continue
        entry = o[j] + d * SLIP
        tgt = entry + d * tgt_frac * abs(dev)
        rk = stop_k * a
        stop = entry - d * rk
        if (tgt - entry) * d <= TICK:
            i += 1
            continue
        # walk with a flatten on the 18:00 clock
        xi = j; xp = 0.0; rs = 0
        k = j
        while True:
            mk = (om[k] - 1080) % 1440
            if k > j and (dayid[k] != dd or mk >= fl):
                xi = k; xp = o[k] - d * SLIP; rs = 0
                break
            if d == 1:
                if k > j and o[k] <= stop:
                    xi = k; xp = o[k] - SLIP; rs = -1; break
                if l[k] <= stop:
                    xi = k; xp = stop - SLIP; rs = -1; break
                if h[k] >= tgt + TICK:
                    xi = k; xp = max(tgt, o[k]) if (k > j and o[k] >= tgt) else tgt; rs = 1; break
            else:
                if k > j and o[k] >= stop:
                    xi = k; xp = o[k] + SLIP; rs = -1; break
                if h[k] >= stop:
                    xi = k; xp = stop + SLIP; rs = -1; break
                if l[k] <= tgt - TICK:
                    xi = k; xp = min(tgt, o[k]) if (k > j and o[k] <= tgt) else tgt; rs = 1; break
            if k + 1 >= n:
                xi = k; xp = c[k]; rs = 0; break
            k += 1
        E[t] = j; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
        trades += 1
        last_exit = xi
        # rebuild the VWAP through the exit bar
        if anchor_mode == 0:
            for q in range(i + 1, xi + 1):
                if dayid[q] != dd:
                    break
                w = v[q] if use_vol else 1.0
                pv += (h[q] + l[q] + c[q]) / 3.0 * w; vv += w
        i = xi + 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 12) Time-window hold (session drift): enter at a clock time, exit at a later clock time (same Globex session)
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_window_hold(o, h, l, c, om, dayid, atr_day, day_dir, entry_om, exit_om, stop_k, tgt_k, dir_mode):
    """Clock times on the 18:00-based session clock. dir_mode: 1 always long, -1 always short, 0 follow day_dir.
       Stop = stop_k * ATRd, optional target tgt_k * ATRd (0 = none). One trade per session."""
    n = len(c)
    maxT = dayid[-1] + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    em = (entry_om - 1080) % 1440; xm = (exit_om - 1080) % 1440
    done_day = -1
    i = 0
    while i < n:
        dd = dayid[i]
        m = (om[i] - 1080) % 1440
        if dd == done_day or m < em or m >= xm:
            i += 1
            continue
        done_day = dd
        a = atr_day[dd]
        d = dir_mode if dir_mode != 0 else day_dir[dd]
        if d == 0 or np.isnan(a) or a <= 0:
            i += 1
            continue
        entry = o[i] + d * SLIP
        rk = stop_k * a
        stop = entry - d * rk
        tgt = entry + d * tgt_k * a if tgt_k > 0 else -1.0
        k = i
        xi = i; xp = c[i]; rs = 0
        while k < n:
            mk = (om[k] - 1080) % 1440
            if k > i and (dayid[k] != dd or mk >= xm):
                xi = k; xp = o[k] - d * SLIP; rs = 0; break
            if d == 1:
                if k > i and o[k] <= stop: xi = k; xp = o[k] - SLIP; rs = -1; break
                if l[k] <= stop: xi = k; xp = stop - SLIP; rs = -1; break
                if tgt > 0 and k > i and h[k] >= tgt + TICK: xi = k; xp = tgt; rs = 1; break
            else:
                if k > i and o[k] >= stop: xi = k; xp = o[k] + SLIP; rs = -1; break
                if h[k] >= stop: xi = k; xp = stop + SLIP; rs = -1; break
                if tgt > 0 and k > i and l[k] <= tgt - TICK: xi = k; xp = tgt; rs = 1; break
            k += 1
        if k >= n:
            break
        E[t] = i; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
        i = xi + 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 13) ICT model: liquidity sweep -> inversion of an FVG (IFVG) -> entry (bar-by-bar state machine)
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_sweep_ifvg(o, h, l, c, om, dayid, open_idx, levels, lvl_mask, atr1, win_s, win_e, flat_om,
                   sweep_lb, fvg_lb, min_fvg_atr, body_min, entry_mode, retest_bars, stop_mode, stop_buf,
                   rr, max_stop, min_stop, max_trades, be_r):
    """levels[dd, k]: liquidity levels known before the session window (k even = buy-side/high, k odd = sell-side/low).
       lvl_mask[k]: use level k.  A BUY-side level is 'swept' when a bar's high trades above it (inside the window).
       Bearish setup: within `sweep_lb` bars after a buy-side sweep, a bar CLOSES below the bottom of a bullish FVG
       that formed within the last `fvg_lb` bars (the inversion) -> short. Mirror for sell-side sweeps.
       entry_mode 0: market at next open; 1: limit at the inverted FVG edge (retest) for `retest_bars`.
       stop_mode 0: beyond the sweep extreme (+stop_buf ticks); 1: beyond the inversion bar extreme; 2: 1.0*atr1*stop_buf.
       Stops outside [min_stop, max_stop] points are skipped (min_stop 0 = no floor)."""
    nd = len(open_idx)
    maxT = nd * max(1, max_trades) + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0
    n = len(c)
    nl = levels.shape[1]
    for dd in range(nd):
        i0 = open_idx[dd]
        if i0 < 0:
            continue
        swept = np.zeros(nl, np.bool_)
        # most recent sweep per side: bar index and running extreme
        bsl_bar = -1; bsl_ext = -1e18
        ssl_bar = -1; ssl_ext = 1e18
        trades = 0
        pend = 0; plim = 0.0; pstop = 0.0; pbar = -1
        j = i0 + (win_s - 570)
        if j < i0 + 2:
            j = i0 + 2
        while j < n and dayid[j] == dayid[i0] and om[j] < flat_om and trades < max_trades:
            if om[j] >= win_e and pend == 0:
                break
            # ---- pending retest limit ----
            if pend != 0 and j > pbar:
                filled = (pend == 1 and l[j] <= plim - TICK) or (pend == -1 and h[j] >= plim + TICK)
                if filled:
                    d = pend
                    entry = min(plim, o[j]) if d == 1 else max(plim, o[j])
                    rk = (entry - pstop) * d
                    pend = 0
                    if rk > TICK:
                        tgt = entry + d * rr * rk
                        xi, xp, rs_ = walk_exit_be(o, h, l, c, om, dayid, j, d, entry, pstop, tgt, flat_om, False, be_r, TICK)
                        E[t] = j; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs_; t += 1
                        trades += 1
                        bsl_bar = -1; ssl_bar = -1
                        j = xi + 1
                        continue
                elif j - pbar >= retest_bars:
                    pend = 0
            # ---- sweeps (inside the window) ----
            if om[j] < win_e:
                for k in range(nl):
                    if not lvl_mask[k] or swept[k]:
                        continue
                    lv = levels[dd, k]
                    if np.isnan(lv):
                        continue
                    if k % 2 == 0 and h[j] > lv:
                        swept[k] = True
                        bsl_bar = j; bsl_ext = h[j]
                    elif k % 2 == 1 and l[j] < lv:
                        swept[k] = True
                        ssl_bar = j; ssl_ext = l[j]
            if bsl_bar >= 0:
                bsl_ext = max(bsl_ext, h[j])
                if j - bsl_bar > sweep_lb:
                    bsl_bar = -1
            if ssl_bar >= 0:
                ssl_ext = min(ssl_ext, l[j])
                if j - ssl_bar > sweep_lb:
                    ssl_bar = -1
            if pend != 0 or om[j] >= win_e:
                j += 1
                continue
            rng = max(h[j] - l[j], TICK)
            body_ok = abs(c[j] - o[j]) / rng >= body_min
            a = atr1[j]
            d = 0; edge = 0.0; ext = 0.0
            # bearish inversion after a buy-side sweep
            if bsl_bar >= 0 and body_ok and c[j] < o[j]:
                for k in range(j - 1, max(i0 + 1, j - fvg_lb) - 1, -1):
                    if k - 2 < 0:
                        break
                    if l[k] > h[k - 2] and (l[k] - h[k - 2]) >= min_fvg_atr * a:
                        bot = h[k - 2]
                        if c[j] < bot and c[j - 1] >= bot:
                            d = -1; edge = bot; ext = bsl_ext
                        break
            if d == 0 and ssl_bar >= 0 and body_ok and c[j] > o[j]:
                for k in range(j - 1, max(i0 + 1, j - fvg_lb) - 1, -1):
                    if k - 2 < 0:
                        break
                    if h[k] < l[k - 2] and (l[k - 2] - h[k]) >= min_fvg_atr * a:
                        top = l[k - 2]
                        if c[j] > top and c[j - 1] <= top:
                            d = 1; edge = top; ext = ssl_ext
                        break
            if d == 0:
                j += 1
                continue
            if stop_mode == 0:
                stop = ext + stop_buf * TICK if d == -1 else ext - stop_buf * TICK
            elif stop_mode == 1:
                stop = h[j] + stop_buf * TICK if d == -1 else l[j] - stop_buf * TICK
            else:
                stop = c[j] - d * stop_buf * a
            if entry_mode == 0:
                if j + 1 >= n or dayid[j + 1] != dayid[i0]:
                    break
                entry = o[j + 1] + d * SLIP
                rk = (entry - stop) * d
                if rk <= TICK or rk > max_stop or rk < min_stop:
                    j += 1
                    continue
                tgt = entry + d * rr * rk
                xi, xp, rs_ = walk_exit_be(o, h, l, c, om, dayid, j + 1, d, entry, stop, tgt, flat_om, True, be_r, TICK)
                E[t] = j + 1; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs_; t += 1
                trades += 1
                bsl_bar = -1; ssl_bar = -1
                j = xi + 1
                continue
            else:
                rk = (edge - stop) * d
                if rk <= TICK or rk > max_stop or rk < min_stop:
                    j += 1
                    continue
                pend = d; plim = edge; pstop = stop; pbar = j
                if d == -1:
                    bsl_bar = -1
                else:
                    ssl_bar = -1
            j += 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


# ---------------------------------------------------------------------------
# 14) ICT Power of Three (AMD) - generic bar-by-bar state machine
# ---------------------------------------------------------------------------
@njit(cache=True)
def sim_po3(o, h, l, c, om, dayid, ref_up, ref_dn, atr_day, bias, man_s, man_e, ent_e, flat_om,
            k_man, trigger, stop_buf, max_stop_atr, min_stop_atr, rr, tgt_up, tgt_dn):
    """All clock arguments are bar-OPEN minutes on the 18:00-based session clock ((om-1080) % 1440).
    ref_up/ref_dn[dd]: level whose break DOWN (ref_dn) is the bullish manipulation and break UP (ref_up) the bearish one.
      (open-based variants: ref_up = ref_dn = the open; range-based variants: range high / range low)
    bias[dd]: +1 longs only, -1 shorts only, 0 both.
    Manipulation (long): inside [man_s, man_e) price trades below ref_dn - k_man*ATRd.
    Distribution trigger (long), evaluated at bar close inside [man_s, ent_e):
      0: close back above ref_dn;  1: close back above ref_dn with body >= 60% of range (displacement);
      2: bullish FVG (low[i] > high[i-2]) whose bottom is above the manipulation low and close > ref_dn.
    Entry at next bar open. Stop = manipulation extreme -/+ stop_buf ticks. Skip if stop outside [min,max]*ATRd.
    Target: rr*R if rr > 0; rr == 0 -> opposite liquidity (tgt_up/tgt_dn[dd]); rr < 0 -> hold to flat."""
    n = len(c)
    nd = atr_day.shape[0]
    E = np.zeros(nd + 10, np.int64); X = np.zeros(nd + 10, np.int64); D = np.zeros(nd + 10, np.int64)
    EP = np.zeros(nd + 10); XP = np.zeros(nd + 10); RK = np.zeros(nd + 10); RS = np.zeros(nd + 10, np.int64)
    t = 0
    fl = (flat_om - 1080) % 1440
    i = 0
    while i < n:
        dd = dayid[i]
        a = atr_day[dd]
        # skip to next day quickly if unusable
        if np.isnan(a) or a <= 0 or np.isnan(ref_up[dd]) or np.isnan(ref_dn[dd]):
            while i < n and dayid[i] == dd:
                i += 1
            continue
        man_long = False; man_short = False
        lo_ext = 1e18; hi_ext = -1e18
        done = False
        while i < n and dayid[i] == dd:
            m = (om[i] - 1080) % 1440
            if done or m >= ent_e:
                i += 1
                continue
            if m >= man_s:
                if bias[dd] >= 0 and l[i] < ref_dn[dd] - k_man * a:
                    man_long = True
                if bias[dd] <= 0 and h[i] > ref_up[dd] + k_man * a:
                    man_short = True
                if man_long:
                    lo_ext = min(lo_ext, l[i])
                if man_short:
                    hi_ext = max(hi_ext, h[i])
                d = 0
                rng = max(h[i] - l[i], TICK)
                if man_long and c[i] > ref_dn[dd]:
                    if trigger == 0:
                        d = 1
                    elif trigger == 1 and (c[i] - o[i]) >= 0.6 * rng:
                        d = 1
                    elif trigger == 2 and i >= 2 and l[i] > h[i - 2] and h[i - 2] > lo_ext:
                        d = 1
                if d == 0 and man_short and c[i] < ref_up[dd]:
                    if trigger == 0:
                        d = -1
                    elif trigger == 1 and (o[i] - c[i]) >= 0.6 * rng:
                        d = -1
                    elif trigger == 2 and i >= 2 and h[i] < l[i - 2] and l[i - 2] < hi_ext:
                        d = -1
                if d != 0 and i + 1 < n and dayid[i + 1] == dd:
                    e = i + 1
                    entry = o[e] + d * SLIP
                    stop = lo_ext - stop_buf * TICK if d == 1 else hi_ext + stop_buf * TICK
                    rk = (entry - stop) * d
                    done = True
                    if rk > TICK and rk <= max_stop_atr * a and rk >= min_stop_atr * a:
                        if rr > 0:
                            tgt = entry + d * rr * rk
                        elif rr == 0:
                            tgt = tgt_up[dd] if d == 1 else tgt_dn[dd]
                            if np.isnan(tgt) or (tgt - entry) * d <= TICK:
                                tgt = entry + d * 2.0 * rk
                        else:
                            tgt = -1.0
                        # walk with a flatten on the 18:00 clock
                        k = e; xp = c[e]; xi = e; rs = 0
                        while k < n:
                            mk = (om[k] - 1080) % 1440
                            if k > e and (dayid[k] != dd or mk >= fl):
                                xp = o[k] - d * SLIP; xi = k; rs = 0; break
                            if d == 1:
                                if k > e and o[k] <= stop: xp = o[k] - SLIP; xi = k; rs = -1; break
                                if l[k] <= stop: xp = stop - SLIP; xi = k; rs = -1; break
                                if tgt > 0 and k > e and h[k] >= tgt + TICK: xp = tgt; xi = k; rs = 1; break
                            else:
                                if k > e and o[k] >= stop: xp = o[k] + SLIP; xi = k; rs = -1; break
                                if h[k] >= stop: xp = stop + SLIP; xi = k; rs = -1; break
                                if tgt > 0 and k > e and l[k] <= tgt - TICK: xp = tgt; xi = k; rs = 1; break
                            k += 1
                        if k < n:
                            E[t] = e; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
            i += 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]
