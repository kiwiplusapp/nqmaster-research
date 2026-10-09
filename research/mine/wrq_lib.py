"""wrq_lib: per-module ENTRY SPECS + generic 1-minute EXIT ENGINE for the WR/PF-per-trade study (agent prefix wrq_).
Import-safe (no work at import).

Entry spec (one row per filled trade of a module, as the module's own research sim takes it):
  date, mod, fi (1m fill bar index in the dataset), d (+1/-1), ent0 (fill price WITHOUT slippage), et (0 = market/stop fill that
  pays slippage, 1 = limit fill), sl0 / tp0 (initial stop / target prices), tx (1m bar whose close is the forced time exit:
  max hold / 15:55 flat / LON 09:30 / end of session), u0 (P&L of the module's own sim, $ per MNQ, $1.90 RT + 1 tick).
Exit engine xsim(): bar-by-bar on 1m bars from the fill bar, stop checked first (gap at open -> open), target needs a 1-tick
trade-through and is never filled on the fill bar, time exit at bar close -1 tick, one position at a time per module (a later
entry whose fill bar is <= the previous exit bar is skipped).  Variants: stop distance x ks, target distance x kt (kt <= 0: no
target), break-even after +be R (stop to entry + beo R), trailing after +tt R at td R behind the best extreme (updated at
bar close, effective from the next bar), time stop after ts minutes (unconditional, or only if open P&L < tsc R)."""
import os, sys, importlib, math, itertools, numpy as np, pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.dirname(HERE)
for p in (HERE, RES):
    if p not in sys.path: sys.path.insert(0, p)
from core import Data, S, TICK
SLIP = 0.25
PER = {"IS": ("nq_1m.npz", 20200201, 20240101), "C24": ("nq_1m.npz", 20240101, 30000000),
       "REAL": ("mnq_fut.npz", 20240201, 30000000), "L15": ("nqhd_long.npz", 20150201, 20200101)}
NORM_COST = 0.00345                    # 2015-19 regime test: cost = 0.345% of daily ATR, no slippage, P&L in % of ATR
_D = {}
def getD(name):
    if name not in _D: _D[name] = Data(name)
    return _D[name]


# ------------------------------------------------------------------------------------------------ exit engine
@njit(cache=True)
def xsim(o, h, l, c, fi, d, ent0, et, sl0, tp0, tx, slip, ks, kt, be, beo, tt, td, ts, tsc, out):
    """out[k]: 0 pts (gross, incl. slippage), 1 exit bar, 2 reason (0 stop, 1 target, 2 time, 3 BE/trail stop, 4 time stop,
    -1 skipped), 3 risk pts (new stop distance), 4 MFE in R, 5 MAE in R."""
    n = len(fi); busy = -1
    for k in range(n):
        f = fi[k]; s = d[k]
        out[k, 0] = np.nan; out[k, 2] = -1
        if f <= busy: continue
        e = ent0[k] + (s * slip if et[k] == 0 else 0.0)
        r0 = abs(e - sl0[k]); sd = ks * r0
        if sd <= 0 or (e - sl0[k]) * s <= 0: continue
        sl = e - s * sd
        if kt > 0:
            tdist = kt * (tp0[k] - e) * s
            if tdist <= 0: continue
            tp = e + s * tdist
        else:
            tp = e + s * 1e9
        best = e; worst = e; moved = False; ex = np.nan; rs = 2; q = f
        last = tx[k]
        while True:
            if s == 1:
                if q > f and o[q] <= sl: ex = o[q] - slip; rs = 3 if moved else 0; break
                if l[q] <= sl: ex = sl - slip; rs = 3 if moved else 0; break
                if q > f and h[q] >= tp + TICK: ex = max(o[q], tp); rs = 1; break
            else:
                if q > f and o[q] >= sl: ex = o[q] + slip; rs = 3 if moved else 0; break
                if h[q] >= sl: ex = sl + slip; rs = 3 if moved else 0; break
                if q > f and l[q] <= tp - TICK: ex = min(o[q], tp); rs = 1; break
            if s == 1:
                best = max(best, h[q]); worst = min(worst, l[q])
            else:
                best = min(best, l[q]); worst = max(worst, h[q])
            if q >= last: ex = c[q] - s * slip; rs = 2; break
            if ts > 0 and q - f >= ts:
                if tsc < -50 or (c[q] - e) * s < tsc * sd:
                    ex = c[q] - s * slip; rs = 4; break
            fav = (best - e) * s
            if be > 0 and fav >= be * sd:
                ns = e + s * beo * sd
                if (ns - sl) * s > 0: sl = ns; moved = True
            if tt > 0 and fav >= tt * sd:
                ns = best - s * td * sd
                if (ns - sl) * s > 0: sl = ns; moved = True
            q += 1
        out[k, 0] = s * (ex - e); out[k, 1] = q; out[k, 2] = rs; out[k, 3] = sd
        out[k, 4] = (best - e) * s / sd; out[k, 5] = (worst - e) * s / sd
        busy = q
    return n


DEF = dict(ks=1.0, kt=1.0, be=0.0, beo=0.0, tt=0.0, td=0.0, ts=0, tsc=-99.0)
def run_exit(E, D, slip=SLIP, norm=False, **kw):
    """E: entry specs of ONE module on dataset D (sorted by fi). Returns copy with u ($/MNQ, or %ATR if norm), xi, rs, risk, mfe, mae."""
    p = dict(DEF); p.update(kw)
    E = E.sort_values("fi", kind="stable")
    out = np.zeros((len(E), 6))
    xsim(D.o, D.h, D.l, D.c, E.fi.to_numpy(np.int64), E.d.to_numpy(np.int64), E.ent0.to_numpy(np.float64), E.et.to_numpy(np.int64),
         E.sl0.to_numpy(np.float64), E.tp0.to_numpy(np.float64), E.tx.to_numpy(np.int64), float(slip), float(p["ks"]), float(p["kt"]),
         float(p["be"]), float(p["beo"]), float(p["tt"]), float(p["td"]), int(p["ts"]), float(p["tsc"]), out)
    X = E.copy(); ok = ~np.isnan(out[:, 0])
    pts = out[:, 0]
    if norm:
        A = D.atr[D.day[X.fi.to_numpy()]]
        X["u"] = np.where(A > 0, (pts - NORM_COST * A) / np.where(A > 0, A, 1) * 100, 0.0)
    else:
        X["u"] = pts * D.pv - D.comm
    X["xi"] = out[:, 1].astype(np.int64); X["rs"] = out[:, 2].astype(np.int64); X["risk"] = out[:, 3]; X["mfe"] = out[:, 4]; X["mae"] = out[:, 5]
    X = X[ok].copy(); X["tout"] = D.sm[X.xi.to_numpy()] + 1
    return X


# ------------------------------------------------------------------------------------------------ helpers
def time_exit(D, fi, hold, flat_hhmm=1555):
    """Forced exit bar: first bar q >= fi of the same session with q - fi >= hold or sm >= S(flat), else last bar of the session."""
    fi = np.asarray(fi, np.int64); hold = np.broadcast_to(np.asarray(hold, np.int64), fi.shape)
    sf = S(flat_hhmm); out = np.empty(len(fi), np.int64)
    for k in range(len(fi)):
        f = fi[k]; dd = D.day[f]; e = D.de[dd]; q = f
        lim = min(e, f + hold[k])
        while q < lim and D.sm[q] < sf: q += 1
        out[k] = q
    return out


def fills_core(D, ev, flat=955, maxday=1, slip=SLIP):
    """Entry part of core.execute (same order of events, busy/maxday logic with the ORIGINAL exits) -> fills + original pts."""
    if len(ev["i"]) == 0: return None
    order = np.argsort(ev["i"], kind="stable"); a = {k: np.ascontiguousarray(np.asarray(v)[order]) for k, v in ev.items()}
    out = np.zeros((len(a["i"]) + 1, 9))
    k = _fills(D.o, D.h, D.l, D.c, D.om, D.day, a["i"].astype(np.int64), a["d"].astype(np.int64), a["t"].astype(np.int64), a["px"].astype(np.float64),
               a["sl"].astype(np.float64), a["tp"].astype(np.float64), a["exp"].astype(np.int64), a["hold"].astype(np.int64), flat, maxday, out, slip)
    o = out[:k]
    return pd.DataFrame(dict(fi=o[:, 0].astype(np.int64), d=o[:, 1].astype(np.int64), ent0=o[:, 2], et=o[:, 3].astype(np.int64), sl0=o[:, 4], tp0=o[:, 5],
                             hold=o[:, 6].astype(np.int64), pts=o[:, 7], xi0=o[:, 8].astype(np.int64)))


@njit(cache=True)
def _fills(o, h, l, c, om, day, ev_i, ev_d, ev_t, ev_px, ev_sl, ev_tp, ev_exp, ev_hold, flat, maxday, out, SLIP):
    n = len(c); k = 0; busy = -1; curday = -1; cnt = 0
    for e in range(len(ev_i)):
        si = ev_i[e]
        if si <= busy or si + 1 >= n: continue
        j0 = si + 1
        if day[j0] != day[si]: continue
        if day[si] != curday:
            curday = day[si]; cnt = 0
        if cnt >= maxday: continue
        d = ev_d[e]; sl = ev_sl[e]; tp = ev_tp[e]; fi = -1; ent = 0.0; raw = 0.0; et = 0
        if ev_t[e] == 0:
            if om[j0] >= flat and om[j0] < 1080: continue
            fi = j0; raw = o[j0]; ent = raw + d * SLIP
        else:
            px = ev_px[e]; last = min(ev_exp[e], n - 1)
            for j in range(j0, last + 1):
                if day[j] != day[si] or (om[j] >= flat and om[j] < 1080): break
                if ev_t[e] == 1:
                    if (d == 1 and l[j] <= px - TICK) or (d == -1 and h[j] >= px + TICK):
                        fi = j; raw = min(px, o[j]) if d == 1 else max(px, o[j]); ent = raw; et = 1; break
                    if (d == 1 and h[j] >= tp) or (d == -1 and l[j] <= tp): break
                else:
                    if (d == 1 and h[j] >= px) or (d == -1 and l[j] <= px):
                        fi = j; raw = max(px, o[j]) if d == 1 else min(px, o[j]); ent = raw + d * SLIP; break
            if fi < 0: continue
        if (d == 1 and (ent <= sl or ent >= tp)) or (d == -1 and (ent >= sl or ent <= tp)): continue
        ex = np.nan; q = fi
        while q < n:
            if d == 1:
                if q > fi and o[q] <= sl: ex = o[q] - SLIP; break
                if l[q] <= sl: ex = sl - SLIP; break
                if q > fi and h[q] >= tp + TICK: ex = max(o[q], tp); break
            else:
                if q > fi and o[q] >= sl: ex = o[q] + SLIP; break
                if h[q] >= sl: ex = sl + SLIP; break
                if q > fi and l[q] <= tp - TICK: ex = min(o[q], tp); break
            if (q - fi >= ev_hold[e]) or (om[q] >= flat and om[q] < 1080) or q + 1 >= n or day[q + 1] != day[q]:
                ex = c[q] - d * SLIP; break
            q += 1
        out[k, 0] = fi; out[k, 1] = d; out[k, 2] = raw; out[k, 3] = et; out[k, 4] = sl; out[k, 5] = tp; out[k, 6] = ev_hold[e]
        out[k, 7] = d * (ex - ent); out[k, 8] = q; k += 1
        busy = q; cnt += 1
    return k


def pf(u):
    u = np.asarray(u, float); lo = -u[u <= 0].sum()
    return u[u > 0].sum() / lo if lo > 0 else np.nan


def stats(u):
    u = np.asarray(u, float)
    if len(u) == 0: return dict(n=0, wr=np.nan, pf=np.nan, exp=np.nan, net=0.0)
    return dict(n=len(u), wr=100 * (u > 0).mean(), pf=pf(u), exp=u.mean(), net=u.sum())


def per_slice(X, per):
    _, lo, hi = PER[per]
    return X[(X.date >= lo) & (X.date < hi)]


# ------------------------------------------------------------------------------------------------ overfitting tools (copied from robust_lab.py, which runs work at import)
def dsr(d, N):
    from scipy.stats import skew, kurtosis, norm
    d = np.asarray(d, float); sr = d.mean() / d.std(); n = len(d); g3 = skew(d); g4 = kurtosis(d, fisher=False); emc = 0.5772156649
    sr0 = (1 / n) ** .5 * ((1 - emc) * norm.ppf(1 - 1 / N) + emc * norm.ppf(1 - 1 / (N * math.e)))
    z = (sr - sr0) * (n - 1) ** .5 / (1 - g3 * sr + (g4 - 1) / 4 * sr * sr) ** .5
    return float(norm.cdf(z)), float(sr0 * 252 ** .5)


def pbo(M, S=16):
    """CSCV probability of backtest overfitting. M: T x N matrix of per-period (daily) returns of N candidate configurations."""
    M = np.asarray(M, float); n, N = M.shape; b = np.array_split(np.arange(n), S)
    s1 = np.array([M[ix].sum(0) for ix in b]); s2 = np.array([(M[ix] ** 2).sum(0) for ix in b]); cnt = np.array([len(ix) for ix in b])
    lam = []; deg = []
    for comb in itertools.combinations(range(S), S // 2):
        cm = np.zeros(S, bool); cm[list(comb)] = True
        def sh(mask):
            m = s1[mask].sum(0) / cnt[mask].sum(); v = s2[mask].sum(0) / cnt[mask].sum() - m * m; return m / np.sqrt(np.maximum(v, 1e-12))
        a = sh(cm); oo = sh(~cm); k = int(np.argmax(a))
        rk = (oo < oo[k]).mean() + 0.5 * (oo == oo[k]).mean(); rk = min(max(rk, 1 / N), 1 - 1 / N)
        lam.append(math.log(rk / (1 - rk))); deg.append((a[k], oo[k]))
    lam = np.array(lam); deg = np.array(deg)
    return dict(PBO=round(float((lam <= 0).mean()), 3), median_logit=round(float(np.median(lam)), 2), N=N, combos=len(lam),
                IS_best_sharpe_ann=round(float(deg[:, 0].mean() * 252 ** .5), 2), OOS_sharpe_of_IS_best_ann=round(float(deg[:, 1].mean() * 252 ** .5), 2))
