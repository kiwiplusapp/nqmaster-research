"""Quant-literature families (batch Q, 2026-10-08). Same contract as families*.py: gen(D, p) -> event dict for core.run_events,
except Q_NOISE which needs a trailing stop evaluated at clock marks and returns {'direct': trades array} (simulated here with
the core cost model: market fills at the bar open +1 tick, stops -1 tick, flat at the close of the first bar >= flat, $1.90 RT).
No look-ahead: every feature uses data up to the signal bar close (cross-day statistics use previous days only; calendar flags use
the exchange calendar, which is known in advance).

Families (literature source in brackets):
  Q_NOISE  intraday momentum out of the 'noise area' (Zarattini, Aziz & Barbon 2024, SFI WP 24-97): sigma(t) = mean |close(t)/open-1| at the
           same clock minute over the last L RTH days; UB = max(open, prior close)*(1+m*sigma), LB = min(...)*(1-m*sigma); checks at HH:00/HH:30
           (f=30) or HH:00 (f=60) from 10:00; trailing stop max(UB, VWAP) (trail=1) or UB (trail=0) checked at the marks; optional hard stop.
  Q_CAL    calendar long-only trades: turn of the month (Ariel 1987, McConnell & Xu 2008), pre-holiday (Ariel 1990), pre-FOMC drift
           (Lucca & Moench 2015; exit 13:55 before the 14:00 statement), FOMC eve (Boguth et al.), CPI / NFP announcement days (Savor & Wilson 2013),
           monthly option-expiration week / Friday.
  Q_REBAL  month-end rebalancing pressure (Harvey, Mazzoleni & Melone 2025, NBER w33554): last K trading days, fade (mode -1) or follow (+1)
           the month-to-date move (in daily ATRs) when |MTD| >= x.
  Q_SEASON intraday return periodicity (Heston, Korajczyk & Sadka 2010): trade an RTH slot in the sign of its mean return over the last N
           days (or N same weekdays) when |t-stat| >= th (mode 1 persistence, -1 reversal).
  Q_RELSTR NQ vs ES relative strength since the RTH open at time T, single NQ leg: RS = NQ move/ATR_NQ - ES move/ATR_ES; or ESLEAD (ES moved
           >= x ATR, NQ lagging at most half of it -> NQ catch-up).
  Q_XLEAD  minute-scale cross-asset lead-lag (ES, EURUSD, gold -> NQ): at 15-minute marks, asset W-minute return z >= th while NQ |z| < 1.
  Q_VR     variance-ratio regime switch (Lo & MacKinlay VR on 1m returns since the open): VR high -> momentum of the open-to-now move;
           VR low -> fade toward VWAP.
  Q_TSMOM  time-series momentum (Moskowitz, Ooi & Pedersen 2012) traded intraday with a volatility-managed filter (Moreira & Muir 2017):
           sign of the L-day return, skip days with ATR / 60-day median ATR > v.
  Q_GAPVOL opening gap fill / continuation conditioned on the volatility regime (ATR / 60-day median ATR)."""
import os, sys, datetime as dt, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import S, ev_from_lists, load, RES
from families import grid
sys.path.insert(0, RES)
from ict import day_levels
import news                                            # FOMC / CPI / NFP sets 2020-26 (module only builds sets)

FOMC_1519 = ["2015-01-28", "2015-03-18", "2015-04-29", "2015-06-17", "2015-07-29", "2015-09-17", "2015-10-28", "2015-12-16",
             "2016-01-27", "2016-03-16", "2016-04-27", "2016-06-15", "2016-07-27", "2016-09-21", "2016-11-02", "2016-12-14",
             "2017-02-01", "2017-03-15", "2017-05-03", "2017-06-14", "2017-07-26", "2017-09-20", "2017-11-01", "2017-12-13",
             "2018-01-31", "2018-03-21", "2018-05-02", "2018-06-13", "2018-08-01", "2018-09-26", "2018-11-08", "2018-12-19",
             "2019-01-30", "2019-03-20", "2019-05-01", "2019-06-19", "2019-07-31", "2019-09-18", "2019-10-30", "2019-12-11"]
FOMC = set(news.fomc) | {int(x.replace("-", "")) for x in FOMC_1519}
NFP = set(news.nfp)
for y in range(2015, 2020):                            # first-Friday approximation of NFP release days 2015-19
    for m in range(1, 13):
        d = dt.date(y, m, 1)
        while d.weekday() != 4: d += dt.timedelta(days=1)
        NFP.add(int(d.strftime("%Y%m%d")))
CPI = set(news.cpi)                                    # 2020-26 only (no 2015-19 list -> CPI events empty there)
ASSET_FILES = {"nq_1m.npz": {"ES": "es_hd.npz", "EUR": "eur_hd.npz", "XAU": "xau_hd.npz"},
               "mnq_fut.npz": {"ES": "es_hd.npz", "EUR": "eur_hd.npz", "XAU": "xau_hd.npz"},
               "nqhd_long.npz": {"ES": "es_long.npz", "EUR": "eur_hd.npz", "XAU": "xau_long.npz"}}


# ------------------------------------------------------------------ NYSE trading calendar (CME keeps partial sessions on most holidays)
from pandas.tseries.holiday import (AbstractHolidayCalendar, Holiday, nearest_workday, sunday_to_monday, USMartinLutherKingJr, USPresidentsDay,
                                    GoodFriday, USMemorialDay, USLaborDay, USThanksgivingDay)
class _NYSE(AbstractHolidayCalendar):
    rules = [Holiday("NY", month=1, day=1, observance=sunday_to_monday), USMartinLutherKingJr, USPresidentsDay, GoodFriday, USMemorialDay,
             Holiday("J19", month=6, day=19, start_date="2022-01-01", observance=nearest_workday), Holiday("J4", month=7, day=4, observance=nearest_workday),
             USLaborDay, USThanksgivingDay, Holiday("XM", month=12, day=25, observance=nearest_workday)]
NYSE_HOL = {int(x.strftime("%Y%m%d")) for x in _NYSE().holidays("2010-01-01", "2027-12-31")} | {20181205, 20250109}


# ------------------------------------------------------------------ shared per-dataset features (cached on D)
def _cache(D):
    if not hasattr(D, "_q"): D._q = {}
    return D._q

def tdays(D):
    """Globex day ids with an RTH session on an NYSE trading day (holiday half-sessions excluded)."""
    C = _cache(D)
    if "td" not in C:
        ok = (D.ro >= 0) & ~np.isin(D.daydate, list(NYSE_HOL)); C["td"] = np.nonzero(ok)[0]
        C["ro2"] = np.where(ok, D.ro, -1)
    return C["td"]

def rth_map(D):
    """idx[d, m+1] = bar index of the bar opening at 09:30 + m minutes (m = -1 .. 389), -1 if missing."""
    C = _cache(D)
    if "idx" in C: return C["idx"]
    idx = np.full((D.nd, 391), -1, np.int64)
    m = D.om - 570; ok = (m >= -1) & (m < 390)
    ii = np.nonzero(ok)[0]; idx[D.day[ii], m[ii] + 1] = ii
    C["idx"] = idx; return idx

def cal(D):
    """Per Globex day: RTH-day flag, month position from start / end, prior month-end RTH close, pre-holiday flag, opex flags, ATR ratio."""
    C = _cache(D)
    if "cal" in C: return C["cal"]
    nd = D.nd; rthd = tdays(D)
    dates = D.daydate[rthd]
    ts = pd.to_datetime(dates.astype(str), format="%Y%m%d")
    df = pd.DataFrame(dict(d=rthd, date=dates, ym=dates // 100, ts=ts))
    df["pos_s"] = df.groupby("ym").cumcount() + 1
    df["pos_e"] = df.groupby("ym").cumcount(ascending=False) * -1 - 1
    # RTH close of each day (complete sessions only) = pdc of the next Globex day
    rc = np.r_[D.pdc[1:], np.nan]
    df["rc"] = rc[df.d.to_numpy()]
    me = df.groupby("ym").rc.last()                         # last RTH close of each month
    prev_me = me.shift(1)
    df["pme"] = df.ym.map(prev_me)
    # pre-holiday: next RTH day is more than one weekday later
    nxt = df.ts.shift(-1)
    bd = np.busday_count(df.ts.to_numpy().astype("datetime64[D]"), nxt.fillna(df.ts).to_numpy().astype("datetime64[D]"))
    df["prehol"] = (bd > 1) & nxt.notna()
    # option expiration: third Friday of the month (week of it = Mon..Fri)
    first = df.ts.dt.to_period("M").dt.start_time
    third_fri = first + pd.to_timedelta((4 - first.dt.weekday) % 7 + 14, unit="D")
    df["opexf"] = df.ts == third_fri
    df["opexw"] = (df.ts >= third_fri - pd.to_timedelta(4, unit="D")) & (df.ts <= third_fri)
    df["fomc"] = df.date.isin(FOMC); df["cpi"] = df.date.isin(CPI); df["nfp"] = df.date.isin(NFP)
    df["fomceve"] = df.fomc.shift(-1, fill_value=False)
    a = pd.Series(D.atr[rthd]); df["atrr"] = (a / a.shift(1).rolling(60, min_periods=40).median()).to_numpy()
    out = {}
    for col in ("pos_s", "pos_e", "pme", "prehol", "opexf", "opexw", "fomc", "cpi", "nfp", "fomceve", "atrr"):
        arr = np.full(nd, np.nan); arr[df.d.to_numpy()] = df[col].to_numpy().astype(float); out[col] = arr
    out["rthd"] = rthd
    C["cal"] = out; return out

def aligned(D, asset):
    """Asset close aligned to D's bars (last asset bar with epoch <= bar epoch, at most 2 min old), the asset's daily ATR mapped by date,
    and sigma1 = 20-day mean of the std of 1-minute log returns (RTH, aligned series), previous days only."""
    C = _cache(D); key = "al_" + asset
    if key in C: return C[key]
    f = ASSET_FILES[D.name][asset]; B = load(f)
    ep = load(D.name)["epoch"].astype(np.int64); be = B["epoch"].astype(np.int64)
    j = np.searchsorted(be, ep, side="right") - 1; ok = (j >= 0) & (ep - be[np.maximum(j, 0)] <= 2)
    xc = np.where(ok, B["c"][np.maximum(j, 0)], np.nan).astype(np.float64)
    _, batr, _ = day_levels(B)
    bdd = pd.Series(B["date"]).groupby(B["dayid"]).last()
    amap = dict(zip(bdd.to_numpy(), batr[bdd.index.to_numpy()]))
    xatr = np.array([amap.get(x, np.nan) for x in D.daydate], np.float64)
    lr = np.r_[np.nan, np.diff(np.log(xc))]; lr[np.r_[True, D.day[1:] != D.day[:-1]]] = np.nan
    rth = (D.om >= 570) & (D.om < 960)
    s = pd.Series(np.where(rth, lr, np.nan)).groupby(D.day).std().reindex(range(D.nd))
    sig1 = s.rolling(20, min_periods=12).mean().shift(1).to_numpy()
    # NQ itself on the same footing
    nlr = np.r_[np.nan, np.diff(np.log(D.c))]; nlr[np.r_[True, D.day[1:] != D.day[:-1]]] = np.nan
    ns = pd.Series(np.where(rth, nlr, np.nan)).groupby(D.day).std().reindex(range(D.nd))
    nsig1 = ns.rolling(20, min_periods=12).mean().shift(1).to_numpy()
    C[key] = (xc, xatr, sig1, nsig1); return C[key]


# ------------------------------------------------------------------ Q_NOISE (direct simulation)
def noise_sigma(D, L):
    C = _cache(D); key = f"nsig{L}"
    if key in C: return C[key]
    idx = rth_map(D)[:, 1:]                                  # minutes 0..389
    rthd = tdays(D)
    O = D.o[D.ro[rthd]]
    I = idx[rthd]; cc = np.where(I >= 0, D.c[np.maximum(I, 0)], np.nan)
    mv = np.abs(cc / O[:, None] - 1.0)
    sg = pd.DataFrame(mv).rolling(L, min_periods=int(0.7 * L)).mean().shift(1).to_numpy()
    out = np.full((D.nd, 390), np.nan); out[rthd] = sg
    C[key] = out; return out

@njit(cache=True)
def _noise(o, h, l, c, om, ro, de, atr, trend, pdc, vwap, sig, mult, marks, trail, hs, tf, maxday, side, flat, SLIP, out):
    k = 0
    for d in range(len(ro)):
        a = ro[d]
        if a < 0 or atr[d] <= 0: continue
        O = o[a]; P = pdc[d]
        if np.isnan(P): P = O
        hiB = max(O, P); loB = min(O, P)
        pos = 0; ent = 0.0; fi = -1; hst = 0.0; cnt = 0; q = a
        while q <= de[d]:
            m = om[q] - 570
            if m < 0 or m >= 390: break
            ex = np.nan
            if marks[m] == 1 and q - 1 >= a and om[q - 1] == om[q] - 1 and not np.isnan(sig[d, m - 1]):
                s1 = sig[d, m - 1]; cc = c[q - 1]; UB = hiB * (1 + mult * s1); LB = loB * (1 - mult * s1)
                if pos == 1:
                    lvl = UB
                    if trail == 1 and not np.isnan(vwap[q - 1]): lvl = max(UB, vwap[q - 1])
                    if cc < lvl: ex = o[q] - SLIP
                elif pos == -1:
                    lvl = LB
                    if trail == 1 and not np.isnan(vwap[q - 1]): lvl = min(LB, vwap[q - 1])
                    if cc > lvl: ex = o[q] + SLIP
                if not np.isnan(ex):
                    out[k, 0] = pos * (ex - ent); out[k, 1] = fi; out[k, 2] = q; out[k, 3] = pos; out[k, 4] = abs(ent - hst); k += 1; pos = 0; ex = np.nan
                if pos == 0 and cnt < maxday and om[q] < flat:
                    sd = 0
                    if cc > UB: sd = 1
                    elif cc < LB: sd = -1
                    if side == 1 and sd == -1: sd = 0
                    if tf == 1 and sd != trend[d]: sd = 0
                    if sd != 0:
                        pos = sd; ent = o[q] + sd * SLIP; fi = q; hst = ent - sd * hs * atr[d]; cnt += 1
            if pos != 0:
                if pos == 1 and l[q] <= hst: ex = min(hst, o[q]) - SLIP
                elif pos == -1 and h[q] >= hst: ex = max(hst, o[q]) + SLIP
                elif om[q] >= flat or q == de[d]: ex = c[q] - pos * SLIP
                if not np.isnan(ex):
                    out[k, 0] = pos * (ex - ent); out[k, 1] = fi; out[k, 2] = q; out[k, 3] = pos; out[k, 4] = abs(ent - hst); k += 1; pos = 0
            q += 1
        if pos != 0:
            qq = q - 1
            out[k, 0] = pos * (c[qq] - pos * SLIP - ent); out[k, 1] = fi; out[k, 2] = qq; out[k, 3] = pos; out[k, 4] = abs(ent - hst); k += 1
    return k

def gen_noise(D, p, slip=0.25, flat=955):
    sig = noise_sigma(D, p["L"])
    marks = np.zeros(390, np.int64)
    for m in range(30, 390, p["f"]): marks[m] = 1
    out = np.zeros((D.nd * 8, 5))
    tdays(D)
    k = _noise(D.o, D.h, D.l, D.c, D.om, _cache(D)["ro2"], D.de, D.atr, D.trend, D.pdc, D.vwap, sig, p["m"], marks, p["trail"], p["hs"], p["tf"], p["maxday"], p["side"], flat, slip, out)
    return {"direct": out[:k]}
GRID_NOISE = grid(L=(10, 14, 20), m=(1.0, 1.25, 1.5), f=(30, 60), trail=(0, 1), hs=(99.0, 0.5), tf=(0, 1), maxday=(1, 3), side=(0,))


# ------------------------------------------------------------------ helpers for event families
def _ev(rows):
    return ev_from_lists(rows)

def prev_min(hhmm):
    """ET hhmm one minute earlier (0931 -> 0930, 1000 -> 0959, 1500 -> 1459)."""
    m = (hhmm // 100) * 60 + hhmm % 100 - 1
    return (m // 60) * 100 + m % 60

def _bar_at(D, d, hhmm):
    """index of the bar opening at ET hhmm in Globex day d (RTH clock only: 09:29 .. 15:59), -1 if missing."""
    m = (hhmm // 100) * 60 + hhmm % 100 - 570
    if m < -1 or m >= 390: return -1
    return rth_map(D)[d, m + 1]


# ------------------------------------------------------------------ Q_CAL
CAL_EVENTS = ("TOM", "TOMLAST", "TOMFIRST", "PREHOL", "FOMC", "FOMCEVE", "CPI", "NFP", "MACRO", "OPEXW", "OPEXF")
def cal_mask(D, ev):
    K = cal(D); ps, pe = K["pos_s"], K["pos_e"]
    if ev == "TOM": return (pe == -1) | ((ps >= 1) & (ps <= 3))
    if ev == "TOMLAST": return pe == -1
    if ev == "TOMFIRST": return (ps >= 1) & (ps <= 2)
    if ev == "PREHOL": return K["prehol"] == 1
    if ev == "FOMC": return K["fomc"] == 1
    if ev == "FOMCEVE": return K["fomceve"] == 1
    if ev == "CPI": return K["cpi"] == 1
    if ev == "NFP": return K["nfp"] == 1
    if ev == "MACRO": return (K["fomc"] == 1) | (K["cpi"] == 1) | (K["nfp"] == 1)
    if ev == "OPEXW": return K["opexw"] == 1
    if ev == "OPEXF": return K["opexf"] == 1

def gen_cal(D, p):
    msk = cal_mask(D, p["ev"]); rows = []
    for d in np.nonzero(msk)[0]:
        if D.atr[d] <= 0: continue
        if p["A"] == 1801:
            i = D.ds[d]
            if i < 0 or D.sm[i] > 5: continue
        else:
            i = _bar_at(D, d, prev_min(p["A"]))                            # signal bar = bar before A (entry at A)
            if i < 0: continue
        A = D.atr[d]; px = D.c[i]; s = 1
        rows.append([i, s, 0, px, px - s * p["k"] * A, px + s * p["R"] * p["k"] * A, i, 5000])
    return _ev(rows)
GRID_CAL = grid(ev=CAL_EVENTS, A=(1801, 931, 1000), X=(1355, 1555), k=(0.3, 0.6, 1.0), R=(99.0, 1.0))


# ------------------------------------------------------------------ Q_REBAL
def gen_rebal(D, p):
    K = cal(D); pe = K["pos_e"]; rows = []
    for d in np.nonzero((pe >= -p["K"]) & (pe <= -1))[0]:
        A = D.atr[d]
        if A <= 0 or np.isnan(K["pme"][d]) or np.isnan(D.pdc[d]): continue
        mtd = (D.pdc[d] - K["pme"][d]) / A
        if abs(mtd) < p["x"]: continue
        s = int(np.sign(mtd)) * p["mode"]
        i = _bar_at(D, d, prev_min(p["A"]))
        if i < 0: continue
        px = D.c[i]; rows.append([i, s, 0, px, px - s * p["k"] * A, px + s * p["R"] * p["k"] * A, i, 5000])
    return _ev(rows)
GRID_REBAL = grid(K=(1, 3, 5), x=(0.5, 1.5, 3.0), A=(931, 1500), mode=(-1, 1), k=(0.3, 0.6), R=(99.0, 1.0))


# ------------------------------------------------------------------ Q_SEASON
def season_stats(D, Ls, N, wd):
    C = _cache(D); key = f"sea{Ls}_{N}_{wd}"
    if key in C: return C[key]
    idx = rth_map(D); rthd = tdays(D); ns = 390 // Ls
    R = np.full((len(rthd), ns), np.nan); REF = np.full((len(rthd), ns), -1, np.int64)
    for j in range(ns):
        m0 = j * Ls; m1 = m0 + Ls - 1
        ia = idx[rthd, m0]; ib = idx[rthd, m1 + 1]          # bar before slot start (column m0 = minute m0-1) / last slot bar
        ok = (ia >= 0) & (ib >= 0) & (D.atr[rthd] > 0)
        R[ok, j] = (D.c[ib[ok]] - D.c[ia[ok]]) / D.atr[rthd[ok]]
        REF[:, j] = np.where(ok, ia, -1)
    df = pd.DataFrame(R)
    if wd == 0:
        mu = df.rolling(N, min_periods=int(0.8 * N)).mean().shift(1); sd = df.rolling(N, min_periods=int(0.8 * N)).std().shift(1)
    else:
        dow = pd.to_datetime(D.daydate[rthd].astype(str), format="%Y%m%d").dayofweek.to_numpy()
        mu = pd.DataFrame(np.nan, index=df.index, columns=df.columns); sd = mu.copy()
        for w in range(5):
            sel = dow == w; sub = df[sel]
            mu.loc[sel] = sub.rolling(N, min_periods=int(0.8 * N)).mean().shift(1).to_numpy(); sd.loc[sel] = sub.rolling(N, min_periods=int(0.8 * N)).std().shift(1).to_numpy()
    t = (mu / (sd / np.sqrt(N))).to_numpy()
    C[key] = (rthd, t, REF); return C[key]

def gen_season(D, p):
    rthd, t, REF = season_stats(D, p["Ls"], p["N"], p["wd"]); rows = []
    for r, d in enumerate(rthd):
        A = D.atr[d]
        if A <= 0: continue
        for j in range(t.shape[1]):
            if np.isnan(t[r, j]) or abs(t[r, j]) < p["th"] or REF[r, j] < 0: continue
            i = REF[r, j]; s = int(np.sign(t[r, j])) * p["mode"]; px = D.c[i]
            rows.append([i, s, 0, px, px - s * p["k"] * A, px + s * 99 * p["k"] * A, i, p["Ls"] - 1])
    return _ev(rows)
GRID_SEASON = grid(Ls=(30, 60), N=(10, 20, 40, 60), wd=(0, 1), th=(1.0, 1.5, 2.0), mode=(1, -1), k=(0.15, 0.3))


# ------------------------------------------------------------------ Q_RELSTR
def gen_relstr(D, p):
    xc, xatr, _, _ = aligned(D, "ES"); rows = []
    for d in tdays(D):
        A = D.atr[d]
        if A <= 0 or np.isnan(xatr[d]) or xatr[d] <= 0: continue
        ref = _bar_at(D, d, 929); i = _bar_at(D, d, prev_min(p["T"]))
        if ref < 0 or i < 0 or np.isnan(xc[ref]) or np.isnan(xc[i]): continue
        nm = (D.c[i] - D.c[ref]) / A; em = (xc[i] - xc[ref]) / xatr[d]
        if p["sig"] == "RS":
            rs = nm - em
            if abs(rs) < p["x"]: continue
            s = int(np.sign(rs)) * p["mode"]
        else:                                                     # ESLEAD
            if abs(em) < p["x"] or nm * np.sign(em) > 0.5 * abs(em): continue
            s = int(np.sign(em)) * p["mode"]
        if p["tf"] == 1 and s != D.trend[d]: continue
        px = D.c[i]; rows.append([i, s, 0, px, px - s * p["k"] * A, px + s * p["R"] * p["k"] * A, i, 5000])
    return _ev(rows)
GRID_RELSTR = grid(T=(1000, 1100, 1200, 1300), sig=("RS", "ESLEAD"), x=(0.1, 0.2, 0.35), mode=(1, -1), k=(0.2, 0.35), R=(0.5, 1.0, 99.0), tf=(0, 1))


# ------------------------------------------------------------------ Q_XLEAD
def gen_xlead(D, p):
    xc, _, sig1, nsig1 = aligned(D, p["asset"]); idx = rth_map(D); W = p["W"]; rows = []
    marks = [m for m in range(15, 375, 15)]                       # 09:45 .. 15:45 (decision on the bar closing at the mark)
    for d in tdays(D):
        A = D.atr[d]
        if A <= 0 or np.isnan(sig1[d]) or np.isnan(nsig1[d]) or sig1[d] <= 0 or nsig1[d] <= 0: continue
        for m in marks:
            i = idx[d, m]; i0 = i - W
            if i < 0 or i0 < 0 or D.day[i0] != d or np.isnan(xc[i]) or np.isnan(xc[i0]): continue
            zx = np.log(xc[i] / xc[i0]) / (sig1[d] * np.sqrt(W)); zn = np.log(D.c[i] / D.c[i0]) / (nsig1[d] * np.sqrt(W))
            if abs(zx) < p["th"] or abs(zn) >= 1.0: continue
            s = int(np.sign(zx)) * p["mode"]; px = D.c[i]
            rows.append([i, s, 0, px, px - s * p["k"] * A, px + s * 99 * p["k"] * A, i, p["H"]])
    return _ev(rows)
GRID_XLEAD = grid(asset=("ES", "EUR", "XAU"), W=(5, 15, 30), th=(2.0, 3.0), mode=(1, -1), H=(15, 30, 60), k=(0.15, 0.3))


# ------------------------------------------------------------------ Q_VR
def vr_values(D, T, q):
    C = _cache(D); key = f"vr{T}_{q}"
    if key in C: return C[key]
    out = np.full(D.nd, np.nan); I = np.full(D.nd, -1, np.int64)
    lc = np.log(D.c)
    for d in tdays(D):
        a = D.ro[d]; i = _bar_at(D, d, prev_min(T))
        if i < 0 or i - a < 4 * q: continue
        r = np.diff(lc[a - 1:i + 1]) if a - 1 >= D.ds[d] else np.diff(lc[a:i + 1])
        n = (len(r) // q) * q
        if n < 4 * q: continue
        r = r[len(r) - n:]; v1 = r.var()
        if v1 <= 0: continue
        out[d] = r.reshape(-1, q).sum(1).var() / (q * v1); I[d] = i
    C[key] = (out, I); return C[key]

def gen_vr(D, p):
    vr, I = vr_values(D, p["T"], p["q"]); hi, lo = ((1.25, 0.8), (1.5, 0.65))[p["thr"]]; rows = []
    for d in np.nonzero(I >= 0)[0]:
        A = D.atr[d]; i = I[d]
        if A <= 0: continue
        if p["reg"] == "MOM":
            if vr[d] < hi: continue
            mv = D.c[i] - D.o[D.ro[d]]
            if abs(mv) < p["x"] * A: continue
            s = int(np.sign(mv))
        else:
            if vr[d] > lo or np.isnan(D.vwap[i]): continue
            dv = D.vwap[i] - D.c[i]
            if abs(dv) < p["x"] * A: continue
            s = int(np.sign(dv))
        if p["tf"] == 1 and s != D.trend[d]: continue
        px = D.c[i]; rows.append([i, s, 0, px, px - s * p["k"] * A, px + s * p["R"] * p["k"] * A, i, 5000])
    return _ev(rows)
GRID_VR = grid(T=(1100, 1200, 1300), q=(5, 15), reg=("MOM", "REV"), thr=(0, 1), x=(0.1, 0.25), k=(0.2, 0.35), R=(0.5, 1.0, 99.0), tf=(0, 1))


# ------------------------------------------------------------------ Q_TSMOM
def gen_tsmom(D, p):
    K = cal(D); rthd = K["rthd"]; rows = []
    pdc = D.pdc
    for r, d in enumerate(rthd):
        if r < p["L"]: continue
        A = D.atr[d]; d0 = rthd[r - p["L"]]
        if A <= 0 or np.isnan(pdc[d]) or np.isnan(pdc[d0]): continue
        if not (K["atrr"][d] <= p["v"]): continue
        s = int(np.sign(pdc[d] - pdc[d0]))
        if s == 0 or (p["side"] == 1 and s == -1): continue
        if p["A"] == 1801:
            i = D.ds[d]
            if i < 0 or D.sm[i] > 5: continue
        else:
            i = _bar_at(D, d, 930)
            if i < 0: continue
        px = D.c[i]; rows.append([i, s, 0, px, px - s * p["k"] * A, px + s * p["R"] * p["k"] * A, i, 5000])
    return _ev(rows)
GRID_TSMOM = grid(L=(5, 20, 60, 120), A=(1801, 931), v=(9.0, 1.0, 1.2), k=(0.3, 0.5, 1.0), R=(1.0, 99.0), side=(0, 1))


# ------------------------------------------------------------------ Q_GAPVOL
def gen_gapvol(D, p):
    K = cal(D); rows = []
    for d in K["rthd"]:
        A = D.atr[d]; ar = K["atrr"][d]
        if A <= 0 or np.isnan(D.pdc[d]) or np.isnan(ar): continue
        reg = 0 if ar < 0.9 else (2 if ar > 1.1 else 1)
        if reg != p["reg"]: continue
        a = D.ro[d]; g = (D.o[a] - D.pdc[d]) / A
        if abs(g) < p["x"]: continue
        i = a; px = D.c[i]
        if p["mode"] == "FILL":
            s = -int(np.sign(g)); sl = px - s * p["k"] * A; tp = D.pdc[d]
            if (tp - px) * s <= 0.5: continue
        else:
            s = int(np.sign(g)); R = 1.0 if p["mode"] == "CONT1" else 2.0; sl = px - s * p["k"] * A; tp = px + s * R * p["k"] * A
        if p["tf"] == 1 and s != D.trend[d]: continue
        rows.append([i, s, 0, px, sl, tp, i, 5000])
    return _ev(rows)
GRID_GAPVOL = grid(x=(0.1, 0.2, 0.35), reg=(0, 1, 2), mode=("FILL", "CONT1", "CONT2"), k=(0.2, 0.35), tf=(0, 1))


# family: (gen, grid, maxday, flat_fn)  flat_fn(p) -> flat minute (om); default 955 (15:55)
QFAMILIES = {"Q_NOISE": (gen_noise, GRID_NOISE, 99, None), "Q_CAL": (gen_cal, GRID_CAL, 1, lambda p: 835 if p["X"] == 1355 else 955),
             "Q_REBAL": (gen_rebal, GRID_REBAL, 1, None), "Q_SEASON": (gen_season, GRID_SEASON, 13, None),
             "Q_RELSTR": (gen_relstr, GRID_RELSTR, 1, None), "Q_XLEAD": (gen_xlead, GRID_XLEAD, 5, None),
             "Q_VR": (gen_vr, GRID_VR, 1, None), "Q_TSMOM": (gen_tsmom, GRID_TSMOM, 1, None), "Q_GAPVOL": (gen_gapvol, GRID_GAPVOL, 1, None)}
