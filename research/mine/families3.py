"""Batch 3 (user ideas, Oct 2026):
CISD_TRITON - Triton Trades style: H1 orderblock / H1 FVG / liquidity sweep (PDH/PDL, ONH/ONL, London) -> CISD on
              1/3/5-min bars -> entry market / LTF FVG limit / CISD retest limit; stop beyond the sweep extreme;
              target fixed R or the nearest opposite liquidity (PDL/ONL/London low, session low) with min/max R.
EMA9_VWAP   - 9 EMA + VWAP: pullback to EMA9 on the VWAP side, EMA9/VWAP cross, VWAP bounce with EMA9 on side.
ENGULF_4H   - Omar 'Engulfing Bar Play': last closed 4H candle engulfs the previous one -> direction; entry at the
              NY open (market / 15m breakout / break of the 4H candle / opening-15m-range break), target R (2:1 default)."""
import numpy as np
from numba import njit
from core import S, TICK, ev_from_lists
from families import grid

# ============================================================== H1 context zones (FVG / orderblock), no look-ahead
@njit(cache=True)
def _h1_zones(o, h, l, c, last, life):
    n = len(c); top = np.zeros(4 * n); bot = np.zeros(4 * n); frm = np.zeros(4 * n, np.int64); to = np.zeros(4 * n, np.int64)
    zd = np.zeros(4 * n, np.int64); zk = np.zeros(4 * n, np.int64); k = 0
    for b in range(2, n):
        for kind in range(2):
            for s in (-1, 1):
                ok = False; tp_ = 0.0; bt = 0.0
                if kind == 0:                                     # FVG
                    if s == -1 and h[b] < l[b - 2]: ok = True; bt = h[b]; tp_ = l[b - 2]
                    if s == 1 and l[b] > h[b - 2]: ok = True; bt = h[b - 2]; tp_ = l[b]
                else:                                             # orderblock: last opposite candle before a displacement close
                    body = abs(c[b] - o[b]); pb = abs(c[b - 1] - o[b - 1])
                    if s == -1 and c[b - 1] > o[b - 1] and c[b] < l[b - 1] and body > pb: ok = True; bt = l[b - 1]; tp_ = h[b - 1]
                    if s == 1 and c[b - 1] < o[b - 1] and c[b] > h[b - 1] and body > pb: ok = True; bt = l[b - 1]; tp_ = h[b - 1]
                if not ok: continue
                e = min(n - 1, b + life)
                for q in range(b + 1, min(n, b + life + 1)):
                    if (s == -1 and c[q] > tp_) or (s == 1 and c[q] < bt): e = q; break
                top[k] = tp_; bot[k] = bt; frm[k] = last[b]; to[k] = last[e]; zd[k] = s; zk[k] = kind; k += 1
    return top[:k], bot[:k], frm[:k], to[:k], zd[:k], zk[:k]

@njit(cache=True)
def _zone_mark(top, bot, frm, to, zd, zk, bf, bl, bh, blo, tol, out):
    """out[i, 0..3]: bar high inside active bearish FVG / bearish OB, bar low inside active bullish FVG / bullish OB."""
    for z in range(len(top)):
        a = np.searchsorted(bf, frm[z] + 1); b = np.searchsorted(bl, to[z] + 1)
        for i in range(a, b):
            if zd[z] == -1:
                if bh[i] >= bot[z] and bh[i] <= top[z] + tol[i]: out[i, zk[z]] = True
            else:
                if blo[i] <= top[z] and blo[i] >= bot[z] - tol[i]: out[i, 2 + zk[z]] = True

def _bars(D, tf):
    if tf == 1:
        return dict(o=D.o, h=D.h, l=D.l, c=D.c, sm=D.sm, sme=D.sm, first=np.arange(D.n), last=np.arange(D.n), day=D.day, vwap=D.vwap)
    return D.bars(tf)

def _ctx(D, tf):
    key = f"_ctx{tf}"
    if hasattr(D, key): return getattr(D, key)
    if not hasattr(D, "_h1z"):
        H = D.bars(60); D._h1z = _h1_zones(H["o"], H["h"], H["l"], H["c"], H["last"], 48)
    B = _bars(D, tf); out = np.zeros((len(B["c"]), 4), np.bool_)
    tol = 0.1 * D.atr[B["day"]]
    _zone_mark(*D._h1z, B["first"].astype(np.int64), B["last"].astype(np.int64), B["h"], B["l"], tol, out)
    setattr(D, key, out); return out

# ============================================================== CISD (Triton)
@njit(cache=True)
def _cisd(o, h, l, c, smf, last, day, L, mask, atr, trend, ctx, w0, w1, K, emode, tmode, R, rmin, rmax, bias, src, zreq, max_risk, M):
    """src 0: liquidity-level sweeps only; 1: H1-zone touch only (no level needed).  zreq: 0 none, 1 FVG, 2 OB, 3 either
    (for src 0 the sweep extreme must sit inside that H1 zone; for src 1 it defines which zones activate)."""
    n = len(c); out = np.zeros((n // 4 + 10, 8)); k = 0
    cur = -1; taken = np.zeros(6, np.bool_); act = np.zeros(2, np.bool_); ext = np.zeros(2); exti = np.zeros(2, np.int64)
    slo = 0.0; shi = 0.0
    for i in range(2, n - 1):
        d = day[i]
        if d != cur:
            cur = d; act[:] = False; slo = 1e18; shi = -1e18
            for q in range(6): taken[q] = (not mask[q]) or np.isnan(L[d, q])
        m = smf[i]; inwin = m >= w0 and m < w1
        for q in range(6):
            if not taken[q] and not inwin:
                if q < 3 and h[i] > L[d, q]: taken[q] = True
                elif q >= 3 and l[i] < L[d, q]: taken[q] = True
        if not inwin:
            act[:] = False; slo = min(slo, l[i]); shi = max(shi, h[i]); continue
        zb = (zreq == 1 and ctx[i, 0]) or (zreq == 2 and ctx[i, 1]) or (zreq == 3 and (ctx[i, 0] or ctx[i, 1]))
        zu = (zreq == 1 and ctx[i, 2]) or (zreq == 2 and ctx[i, 3]) or (zreq == 3 and (ctx[i, 2] or ctx[i, 3]))
        if src == 0:
            for q in range(6):
                if taken[q]: continue
                if q < 3 and h[i] > L[d, q]:
                    taken[q] = True
                    if not act[0] or h[i] > ext[0]: act[0] = True; ext[0] = h[i]; exti[0] = i
                elif q >= 3 and l[i] < L[d, q]:
                    taken[q] = True
                    if not act[1] or l[i] < ext[1]: act[1] = True; ext[1] = l[i]; exti[1] = i
        else:
            if zb and (not act[0] or h[i] > ext[0]): act[0] = True; ext[0] = h[i]; exti[0] = i
            if zu and (not act[1] or l[i] < ext[1]): act[1] = True; ext[1] = l[i]; exti[1] = i
        for s in range(2):
            if not act[s]: continue
            dirn = -1 if s == 0 else 1
            if s == 0 and h[i] > ext[0]: ext[0] = h[i]; exti[0] = i
            if s == 1 and l[i] < ext[1]: ext[1] = l[i]; exti[1] = i
            if i - exti[s] > K: act[s] = False; continue
            if i <= exti[s]: continue
            j = exti[s]
            if s == 0:
                if c[j] <= o[j]: j -= 1
                while j > 0 and day[j] == d and c[j] > o[j] and c[j - 1] > o[j - 1]: j -= 1
            else:
                if c[j] >= o[j]: j -= 1
                while j > 0 and day[j] == d and c[j] < o[j] and c[j - 1] < o[j - 1]: j -= 1
            cisd = o[j]
            if not ((s == 0 and c[i] < cisd) or (s == 1 and c[i] > cisd)): continue
            act[s] = False
            je = exti[s]
            if src == 0 and zreq > 0:
                inz = (ctx[je, 0] or ctx[je, 1]) if s == 0 else (ctx[je, 2] or ctx[je, 3])
                if zreq == 1: inz = ctx[je, 0] if s == 0 else ctx[je, 2]
                if zreq == 2: inz = ctx[je, 1] if s == 0 else ctx[je, 3]
                if not inz: continue
            if bias == 1 and dirn != trend[d]: continue
            a = atr[d]
            if a <= 0: continue
            stop = ext[s] + TICK if s == 0 else ext[s] - TICK
            t = 0; px = c[i]
            if emode == 1:
                lim = np.nan; b = i
                while b >= exti[s] + 2:
                    if s == 0 and h[b] < l[b - 2]: lim = h[b]; break
                    if s == 1 and l[b] > h[b - 2]: lim = l[b]; break
                    b -= 1
                if np.isnan(lim) or (s == 0 and lim <= c[i]) or (s == 1 and lim >= c[i]): continue
                px = lim; t = 1
            elif emode == 2:
                if (s == 0 and cisd <= c[i]) or (s == 1 and cisd >= c[i]): continue
                px = cisd; t = 1
            risk = (stop - px) * (-dirn)
            if risk <= 0.015 * a or risk > max_risk * a: continue
            if tmode == 0:
                tp = px + dirn * R * risk
            else:
                best = 1e18
                for q in range(6):
                    lv = L[d, q]
                    if np.isnan(lv): continue
                    if (dirn == -1 and q >= 3) or (dirn == 1 and q < 3):
                        dist = (px - lv) * (-dirn) * -1 if False else (lv - px) * dirn
                        if dist >= rmin * risk and dist < best: best = dist
                sx = slo if dirn == -1 else shi                       # session extreme before the window = resting liquidity
                if sx < 1e17 and sx > -1e17:
                    dist = (sx - px) * dirn
                    if dist >= rmin * risk and dist < best: best = dist
                if best > 1e17: best = rmin * risk
                tp = px + dirn * min(best, rmax * risk)
            out[k, 0] = last[i]; out[k, 1] = dirn; out[k, 2] = t; out[k, 3] = px; out[k, 4] = stop; out[k, 5] = tp
            out[k, 6] = last[min(n - 1, i + M)]; out[k, 7] = 400; k += 1
    return out[:k]

SETUPS = {"all": ("all", 0, 0), "PD": ("PD", 0, 0), "ON": ("ON", 0, 0), "LON": ("LON", 0, 0), "all&FVG": ("all", 0, 1), "all&OB": ("all", 0, 2),
          "all&ANY": ("all", 0, 3), "zFVG": ("none", 1, 1), "zOB": ("none", 1, 2), "zANY": ("none", 1, 3)}
TGTS = {"R0.5": (0, 0.5, 0, 0), "R1": (0, 1.0, 0, 0), "R1.5": (0, 1.5, 0, 0), "R2": (0, 2.0, 0, 0), "R3": (0, 3.0, 0, 0),
        "liq0.75-2": (1, 0, 0.75, 2.0), "liq1-2": (1, 0, 1.0, 2.0), "liq1.5-3": (1, 0, 1.5, 3.0)}
def gen_cisd(D, p):
    B = _bars(D, p["tf"]); ctx = _ctx(D, p["tf"])
    lv, src, zreq = SETUPS[p["setup"]]; tm, R, rmin, rmax = TGTS[p["tgt"]]
    mask = np.array([lv in ("all", "PD"), lv in ("all", "ON"), lv in ("all", "LON")] * 2, np.bool_)
    w0, w1 = p["win"]
    return ev_from_lists(_cisd(B["o"], B["h"], B["l"], B["c"], B["sm"].astype(np.int64), B["last"].astype(np.int64), B["day"].astype(np.int64), D.L, mask,
                               D.atr, D.trend, ctx, S(w0), S(w1), p["K"], p["em"], tm, R, rmin, rmax, p["bias"], src, zreq, 0.3, 20).tolist())
GRID_CISD = grid(tf=(1, 3, 5), win=((830, 1100), (930, 1100), (930, 1030), (900, 1130), (930, 1200)), setup=list(SETUPS), K=(3, 8),
                 em=(0, 1, 2), tgt=list(TGTS), bias=(0, 1))

# ============================================================== 9 EMA + VWAP
@njit(cache=True)
def _ema9vw(kind, o, h, l, c, sme, last, day, atr, trend, vwap, w0, w1, R, stopm, s_k, tfl, maxday):
    n = len(c); out = np.zeros((n // 3 + 10, 8)); k = 0; cur = -1; cnt = 0
    e = np.zeros(n); al = 2.0 / 10.0; e[0] = c[0]
    for i in range(1, n): e[i] = al * c[i] + (1 - al) * e[i - 1]
    for i in range(6, n):
        d = day[i]
        if d != cur: cur = d; cnt = 0
        if sme[i] < w0 or sme[i] >= w1 or cnt >= maxday or np.isnan(vwap[i]) or np.isnan(vwap[i - 1]): continue
        a = atr[d]
        if a <= 0 or day[i - 5] != d: continue
        s = 0
        if kind == 0:      # pullback to EMA9 with EMA9 and close on the VWAP side
            if e[i] > vwap[i] and c[i] > vwap[i] and l[i] <= e[i] and c[i] > e[i] and c[i] > o[i]: s = 1
            elif e[i] < vwap[i] and c[i] < vwap[i] and h[i] >= e[i] and c[i] < e[i] and c[i] < o[i]: s = -1
        elif kind == 1:    # EMA9 crosses VWAP
            if e[i] > vwap[i] and e[i - 1] <= vwap[i - 1] and c[i] > vwap[i]: s = 1
            elif e[i] < vwap[i] and e[i - 1] >= vwap[i - 1] and c[i] < vwap[i]: s = -1
        else:              # VWAP bounce while EMA9 stays on the trend side
            if e[i] > vwap[i] and l[i] <= vwap[i] and c[i] > vwap[i] and c[i] > o[i]: s = 1
            elif e[i] < vwap[i] and h[i] >= vwap[i] and c[i] < vwap[i] and c[i] < o[i]: s = -1
        if s == 0: continue
        if tfl == 1 and s != trend[d]: continue
        if stopm == 0:
            lo = 1e18; hi = -1e18
            for j in range(i - 4, i + 1): lo = min(lo, l[j]); hi = max(hi, h[j])
            sl = lo - 0.02 * a if s == 1 else hi + 0.02 * a
        elif stopm == 1:
            sl = c[i] - s * s_k * a
        else:
            sl = (min(vwap[i], l[i]) - 0.03 * a) if s == 1 else (max(vwap[i], h[i]) + 0.03 * a)
        risk = (c[i] - sl) * s
        if risk <= 0.015 * a or risk > 0.4 * a: continue
        out[k, 0] = last[i]; out[k, 1] = s; out[k, 2] = 0; out[k, 3] = c[i]; out[k, 4] = sl; out[k, 5] = c[i] + s * R * risk; out[k, 6] = last[i]; out[k, 7] = 120
        k += 1; cnt += 1
    return out[:k]

def gen_ema9vw(D, p):
    B = _bars(D, p["tfb"])
    return ev_from_lists(_ema9vw(p["kind"], B["o"], B["h"], B["l"], B["c"], B["sme"].astype(np.int64), B["last"].astype(np.int64), B["day"].astype(np.int64),
                                 D.atr, D.trend, B["vwap"], S(p["w0"]), S(p["w1"]), p["R"], p["stop"], 0.15, p["trend"], 3).tolist())
GRID_EMA9 = grid(kind=(0, 1, 2), tfb=(1, 2, 3, 5), w0=(945, 1000), w1=(1130, 1530), R=(0.5, 1.0, 1.5, 2.0), stop=(0, 1, 2), trend=(0, 1))

# ============================================================== Omar 4H engulfing + 15m entry at the NY open
@njit(cache=True)
def _engulf(o, h, l, c, sm, ds, de, atr, trend, ev_t, a_start, b_start, ent, R, stopm, tfl, w1, body):
    out = np.zeros((len(ds), 8)); k = 0
    for d in range(len(ds)):
        if ds[d] < 0 or atr[d] <= 0: continue
        a = atr[d]
        ao = -1.0; ac = 0.0; ah = -1e18; al_ = 1e18; bo = -1.0; bc = 0.0; bh = -1e18; bl = 1e18; ie = -1
        for i in range(ds[d], de[d] + 1):
            m = sm[i]
            if m >= a_start and m < a_start + 240:
                if ao < 0: ao = o[i]
                ac = c[i]; ah = max(ah, h[i]); al_ = min(al_, l[i])
            if m >= b_start and m < b_start + 240:
                if bo < 0: bo = o[i]
                bc = c[i]; bh = max(bh, h[i]); bl = min(bl, l[i])
            if m >= ev_t and ie < 0: ie = i
        if ao < 0 or bo < 0 or ie <= ds[d]: continue
        s = 0
        if body == 1:      # body engulfing with opposite colours
            if bc > bo and ac < ao and bc >= ao and bo <= ac: s = 1
            elif bc < bo and ac > ao and bc <= ao and bo >= ac: s = -1
        elif body == 0:    # range engulfing, close in its direction
            if bh >= ah and bl <= al_: s = 1 if bc > bo else (-1 if bc < bo else 0)
        else:              # close beyond the previous candle's extreme
            if bc > bo and bc > ah: s = 1
            elif bc < bo and bc < al_: s = -1
        if s == 0: continue
        if tfl == 1 and s != trend[d]: continue
        si = -1; px = 0.0; t = 0; ex = 0
        if ent == 0:
            si = ie - 1; px = c[ie - 1]; ex = ie
        elif ent == 1:     # first 15m close beyond the previous 15m candle's extreme
            ph = -1e18; pl = 1e18; hh = -1e18; ll = 1e18; st = sm[ie]
            for i in range(ie, de[d] + 1):
                if sm[i] >= w1: break
                hh = max(hh, h[i]); ll = min(ll, l[i])
                if (sm[i] - st + 1) % 15 == 0:
                    if ph > -1e17 and ((s == 1 and c[i] > ph) or (s == -1 and c[i] < pl)): si = i; break
                    ph = hh; pl = ll; hh = -1e18; ll = 1e18
            if si < 0 or si + 1 > de[d]: continue
            px = c[si]; ex = si
        elif ent == 2:     # break of the engulfing 4H candle's extreme
            si = ie - 1; px = bh + TICK if s == 1 else bl - TICK; t = 2
            if (s == 1 and c[si] >= px) or (s == -1 and c[si] <= px): continue
        else:              # opening-15m-range break in the engulfing direction
            hh = -1e18; ll = 1e18; q = ie
            while q <= de[d] and sm[q] < sm[ie] + 15:
                hh = max(hh, h[q]); ll = min(ll, l[q]); q += 1
            if q > de[d]: continue
            si = q - 1; px = hh + TICK if s == 1 else ll - TICK; t = 2
            if (s == 1 and c[si] >= px) or (s == -1 and c[si] <= px): continue
        if t == 2:
            ex = si
            while ex + 1 <= de[d] and sm[ex + 1] < w1: ex += 1
        if stopm == 0: sl = px - s * 0.25 * a
        elif stopm == 1: sl = px - s * 0.5 * (bh - bl)
        elif stopm == 2: sl = (bl - TICK) if s == 1 else (bh + TICK)
        else: sl = px - s * 0.15 * a
        risk = (px - sl) * s
        if risk <= 0.02 * a or risk > 0.6 * a: continue
        out[k, 0] = si; out[k, 1] = s; out[k, 2] = t; out[k, 3] = px; out[k, 4] = sl; out[k, 5] = px + s * R * risk; out[k, 6] = ex; out[k, 7] = 400; k += 1
    return out[:k]

ENG = {"0206v2202@0930": (930, 2200, 200), "0610v0206@1000": (1000, 200, 600), "0408v0004@0930": (930, 0, 400)}
def gen_engulf(D, p):
    ev_t, a_s, b_s = ENG[p["eng"]]
    return ev_from_lists(_engulf(D.o, D.h, D.l, D.c, D.sm, D.ds, D.de, D.atr, D.trend, S(ev_t), S(a_s), S(b_s), p["ent"], p["R"], p["stop"], p["trend"],
                                 S(p["w1"]), p["body"]).tolist())
GRID_ENGULF = grid(eng=list(ENG), ent=(0, 1, 2, 3), R=(0.5, 1.0, 1.5, 2.0), stop=(0, 1, 2, 3), trend=(0, 1), w1=(1130, 1500), body=(0, 1, 2))

FAMILIES3 = {"CISD_TRITON": (gen_cisd, GRID_CISD, 3), "EMA9_VWAP": (gen_ema9vw, GRID_EMA9, 3), "ENGULF_4H": (gen_engulf, GRID_ENGULF, 1)}
