"""SMC 'sniper' confluence model on NQ 1-minute bars (bar-by-bar, no look-ahead).

Bearish setup (bullish is the mirror):
  1 SWEEP  : inside [sweep_s, sweep_e) a bar trades above an untaken buy-side level (PDH, ONH, London high, Asia high).
             ref = most recent CONFIRMED swing low at the sweep bar (start of the final up-leg).
             HTF PDA (pda_mode): 1 premium (sweep above prior-day equilibrium), 2 sweep bar inside an active 60-min
             bearish FVG, 3 both.
  2 MSS    : within `setup_bars` bars a bar CLOSES below ref. Optional filters on that bar: displacement
             (body >= body_min*range and range >= disp_k*ATR1m) and volume influx (volume >= vol_k * 20-bar average).
             If a filter fails, the setup is dropped.
  3 IFVG   : a bullish FVG formed between ref and the MSS bar whose bottom is above the close (inverted), at the MSS bar or
             within `ifvg_bars` bars after it.
  4 MACRO  : (use_macro) the inversion bar must close inside an ICT macro window.
  5 ENTRY  : 0 market at next open; 1 limit at the inverted FVG edge for `retest_bars` bars.
  6 STOP   : beyond the sweep extreme + stop_buf ticks (skip if > max_stop points).
  7 TARGET : tgt_mode 0: rr*R.  tgt_mode 1: nearest opposing liquidity (PDL, ONL, London low, Asia low, session low)
             that gives at least min_rr*R ("clear target"); the setup is skipped if none exists.
"""
import numpy as np
from numba import njit
from engine import TICK, SLIP, walk_exit


@njit(cache=True)
def confirmed_pivots(h, l, k):
    """Most recent swing high/low CONFIRMED at or before each bar (a pivot at j is confirmed at j+k)."""
    n = len(h)
    sl_p = np.full(n, np.nan); sl_b = np.full(n, -1, np.int64)
    sh_p = np.full(n, np.nan); sh_b = np.full(n, -1, np.int64)
    cur_lp = np.nan; cur_lb = -1; cur_hp = np.nan; cur_hb = -1
    for i in range(n):
        j = i - k
        if j - k >= 0:
            isl = True; ish = True
            for q in range(j - k, j + k + 1):
                if l[q] < l[j]:
                    isl = False
                if h[q] > h[j]:
                    ish = False
            if isl:
                cur_lp = l[j]; cur_lb = j
            if ish:
                cur_hp = h[j]; cur_hb = j
        sl_p[i] = cur_lp; sl_b[i] = cur_lb; sh_p[i] = cur_hp; sh_b[i] = cur_hb
    return sl_p, sl_b, sh_p, sh_b


@njit(cache=True)
def htf_pda_flags(h1, l1, ep_end1, Hh, Hl, Hend):
    """Per 1-minute bar: does it trade into an ACTIVE higher-TF bullish / bearish FVG? Zones are built only from
    COMPLETED higher-TF bars; a bullish zone dies when a HTF bar trades below its bottom (mirror for bearish)."""
    n = len(h1); nH = len(Hh)
    cap = 400
    zt = np.zeros(cap); zb = np.zeros(cap); zd = np.zeros(cap, np.int64); cnt = 0
    inBull = np.zeros(n, np.bool_); inBear = np.zeros(n, np.bool_)
    p = 0
    for i in range(n):
        while p < nH and Hend[p] <= ep_end1[i]:
            q = 0
            while q < cnt:
                dead = (zd[q] == 1 and Hl[p] < zb[q]) or (zd[q] == -1 and Hh[p] > zt[q])
                if dead:
                    for r in range(q, cnt - 1):
                        zt[r] = zt[r + 1]; zb[r] = zb[r + 1]; zd[r] = zd[r + 1]
                    cnt -= 1
                else:
                    q += 1
            if p >= 2:
                if Hl[p] > Hh[p - 2] and cnt < cap:
                    zb[cnt] = Hh[p - 2]; zt[cnt] = Hl[p]; zd[cnt] = 1; cnt += 1
                elif Hh[p] < Hl[p - 2] and cnt < cap:
                    zb[cnt] = Hh[p]; zt[cnt] = Hl[p - 2]; zd[cnt] = -1; cnt += 1
            p += 1
        for q in range(cnt):
            if l1[i] <= zt[q] and h1[i] >= zb[q]:
                if zd[q] == 1:
                    inBull[i] = True
                else:
                    inBear[i] = True
    return inBull, inBear


@njit(cache=True)
def sim_smc(o, h, l, c, v, om, dayid, open_idx, levels, atr1, avgv, sl_p, sl_b, sh_p, sh_b, inBull, inBear,
            macro, sweep_s, sweep_e, entry_e, flat_om, setup_bars, ifvg_bars,
            use_disp, disp_k, body_min, use_vol, vol_k, use_macro, pda_mode, entry_mode, retest_bars,
            tgt_mode, rr, min_rr, stop_buf, max_stop, max_trades, atr_day, max_stop_atr, swing_liq, swing_age):
    nd = len(open_idx)
    maxT = nd * max(1, max_trades) + 10
    E = np.zeros(maxT, np.int64); X = np.zeros(maxT, np.int64); D = np.zeros(maxT, np.int64)
    EP = np.zeros(maxT); XP = np.zeros(maxT); RK = np.zeros(maxT); RS = np.zeros(maxT, np.int64)
    t = 0; n = len(c)
    for dd in range(nd):
        i0 = open_idx[dd]
        if i0 < 0:
            continue
        s0 = i0
        while s0 - 1 >= 0 and dayid[s0 - 1] == dayid[i0]:
            s0 -= 1
        PDH = levels[dd, 0]; PDL = levels[dd, 1]
        eq = (PDH + PDL) / 2.0 if not (np.isnan(PDH) or np.isnan(PDL)) else np.nan
        taken = np.zeros(8, np.bool_)
        trades = 0
        b_on = False; b_sbar = -1; b_ext = 0.0; b_ref = 0.0; b_refbar = -1; b_mss = -1
        s_on = False; s_sbar = -1; s_ext = 0.0; s_ref = 0.0; s_refbar = -1; s_mss = -1
        sess_hi = -1e18; sess_lo = 1e18
        last_sh_used = -1; last_sl_used = -1
        j = s0
        while j < n and dayid[j] == dayid[i0] and trades < max_trades:
            if om[j] >= flat_om and om[j] < 1080:
                break
            in_sweep = om[j] >= sweep_s and om[j] < sweep_e
            if not in_sweep and (om[j] < sweep_s or om[j] >= 1080):
                # levels already traded through before the window are not fresh liquidity
                for k in range(8):
                    lv = levels[dd, k]
                    if not taken[k] and not np.isnan(lv):
                        if (k % 2 == 0 and h[j] > lv) or (k % 2 == 1 and l[j] < lv):
                            taken[k] = True
            if in_sweep:
                for k in range(8):
                    lv = levels[dd, k]
                    if taken[k] or np.isnan(lv):
                        continue
                    if k % 2 == 0 and h[j] > lv:
                        taken[k] = True
                        pda_ok = True
                        if pda_mode == 1 or pda_mode == 3:
                            pda_ok = (not np.isnan(eq)) and h[j] > eq
                        if pda_ok and (pda_mode == 2 or pda_mode == 3):
                            pda_ok = inBear[j]
                        if pda_ok and not np.isnan(sl_p[j]):
                            b_on = True; b_sbar = j; b_ext = h[j]; b_ref = sl_p[j]; b_refbar = sl_b[j]; b_mss = -1
                    elif k % 2 == 1 and l[j] < lv:
                        taken[k] = True
                        pda_ok = True
                        if pda_mode == 1 or pda_mode == 3:
                            pda_ok = (not np.isnan(eq)) and l[j] < eq
                        if pda_ok and (pda_mode == 2 or pda_mode == 3):
                            pda_ok = inBull[j]
                        if pda_ok and not np.isnan(sh_p[j]):
                            s_on = True; s_sbar = j; s_ext = l[j]; s_ref = sh_p[j]; s_refbar = sh_b[j]; s_mss = -1
            if in_sweep and swing_liq and j >= 1:
                if not b_on and sh_b[j - 1] >= 0 and sh_b[j - 1] != last_sh_used and j - sh_b[j - 1] <= swing_age and h[j] > sh_p[j - 1]:
                    last_sh_used = sh_b[j - 1]
                    pda_ok = True
                    if pda_mode == 1 or pda_mode == 3:
                        pda_ok = (not np.isnan(eq)) and h[j] > eq
                    if pda_ok and (pda_mode == 2 or pda_mode == 3):
                        pda_ok = inBear[j]
                    if pda_ok and not np.isnan(sl_p[j]):
                        b_on = True; b_sbar = j; b_ext = h[j]; b_ref = sl_p[j]; b_refbar = sl_b[j]; b_mss = -1
                if not s_on and sl_b[j - 1] >= 0 and sl_b[j - 1] != last_sl_used and j - sl_b[j - 1] <= swing_age and l[j] < sl_p[j - 1]:
                    last_sl_used = sl_b[j - 1]
                    pda_ok = True
                    if pda_mode == 1 or pda_mode == 3:
                        pda_ok = (not np.isnan(eq)) and l[j] < eq
                    if pda_ok and (pda_mode == 2 or pda_mode == 3):
                        pda_ok = inBull[j]
                    if pda_ok and not np.isnan(sh_p[j]):
                        s_on = True; s_sbar = j; s_ext = l[j]; s_ref = sh_p[j]; s_refbar = sh_b[j]; s_mss = -1
            d = 0; edge = 0.0; ext = 0.0
            if b_on:
                b_ext = max(b_ext, h[j])
                if b_mss < 0:
                    if j - b_sbar > setup_bars:
                        b_on = False
                    elif c[j] < b_ref:
                        rng = max(h[j] - l[j], TICK)
                        ok = True
                        if use_disp and not ((o[j] - c[j]) >= body_min * rng and rng >= disp_k * atr1[j]):
                            ok = False
                        if use_vol and not (v[j] >= vol_k * avgv[j]):
                            ok = False
                        if ok:
                            b_mss = j
                        else:
                            b_on = False
                if b_on and b_mss >= 0:
                    if j - b_mss > ifvg_bars:
                        b_on = False
                    else:
                        lo_k = max(b_refbar, 2)
                        for k in range(b_mss, lo_k - 1, -1):
                            if l[k] > h[k - 2]:
                                if c[j] < h[k - 2] and ((not use_macro) or macro[j]):
                                    d = -1; edge = h[k - 2]; ext = b_ext
                                break
            if d == 0 and s_on:
                s_ext = min(s_ext, l[j])
                if s_mss < 0:
                    if j - s_sbar > setup_bars:
                        s_on = False
                    elif c[j] > s_ref:
                        rng = max(h[j] - l[j], TICK)
                        ok = True
                        if use_disp and not ((c[j] - o[j]) >= body_min * rng and rng >= disp_k * atr1[j]):
                            ok = False
                        if use_vol and not (v[j] >= vol_k * avgv[j]):
                            ok = False
                        if ok:
                            s_mss = j
                        else:
                            s_on = False
                if s_on and s_mss >= 0:
                    if j - s_mss > ifvg_bars:
                        s_on = False
                    else:
                        lo_k = max(s_refbar, 2)
                        for k in range(s_mss, lo_k - 1, -1):
                            if h[k] < l[k - 2]:
                                if c[j] > l[k - 2] and ((not use_macro) or macro[j]):
                                    d = 1; edge = l[k - 2]; ext = s_ext
                                break
            # session extremes include the current bar only AFTER sweep/MSS logic (known at its close)
            sess_hi = max(sess_hi, h[j]); sess_lo = min(sess_lo, l[j])
            if d == 0 or om[j] >= entry_e:
                j += 1
                continue
            if d == -1:
                b_on = False
            else:
                s_on = False
            stop = ext + stop_buf * TICK if d == -1 else ext - stop_buf * TICK
            e = -1; entry = 0.0
            if entry_mode == 0:
                if j + 1 < n and dayid[j + 1] == dayid[i0]:
                    e = j + 1; entry = o[e] + d * SLIP
            else:
                for q in range(j + 1, min(n, j + 1 + retest_bars)):
                    if dayid[q] != dayid[i0] or (om[q] >= flat_om and om[q] < 1080):
                        break
                    if (d == -1 and h[q] >= edge + TICK) or (d == 1 and l[q] <= edge - TICK):
                        e = q
                        entry = max(edge, o[q]) if d == -1 else min(edge, o[q])
                        break
            if e < 0:
                j += 1
                continue
            rk = (entry - stop) * d
            if rk <= 2 * TICK or rk > max_stop or (max_stop_atr > 0 and rk > max_stop_atr * atr_day[dd]):
                j += 1
                continue
            if tgt_mode == 0:
                tgt = entry + d * rr * rk
            else:
                best = np.nan
                for k in range(8):
                    if (d == -1 and k % 2 == 1) or (d == 1 and k % 2 == 0):
                        lv = levels[dd, k]
                        if np.isnan(lv):
                            continue
                        dist = (lv - entry) * d
                        if dist >= min_rr * rk and (np.isnan(best) or dist < (best - entry) * d):
                            best = lv
                sx = sess_lo if d == -1 else sess_hi
                dist = (sx - entry) * d
                if dist >= min_rr * rk and (np.isnan(best) or dist < (best - entry) * d):
                    best = sx
                if np.isnan(best):
                    j += 1
                    continue
                tgt = best - d * TICK
            xi, xp, rs_ = walk_exit(o, h, l, c, om, dayid, e, d, entry, stop, tgt, flat_om, entry_mode == 0)
            E[t] = e; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs_; t += 1
            trades += 1
            j = xi + 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]
