"""Walk-forward machine-learning study on NQ 1-minute data.

Decision points: every 5 minutes (bar closes 09:40 ... 15:00 ET). At each point we could open a LONG or SHORT
bracket at the next 1-minute open: stop = SK x ATR(5-min, 14), target = RR x stop, max hold 60 minutes.
Labels = realized R of each bracket (1-minute path, stop assumed first when both touch in one bar,
1 tick slippage on entry/stop/time exits, $1 RT commission).
Features use ONLY information available at the decision bar close.
Model: HistGradientBoostingRegressor predicting R_long and R_short. Expanding-window walk-forward by year.
"""
import numpy as np, pandas as pd
from numba import njit
from sklearn.ensemble import HistGradientBoostingRegressor
from common import Ctx
from levels import build_levels

TICK = 0.25; SLIP = 0.25; COMM_PTS = 0.5


@njit(cache=True)
def label_brackets(o, h, l, c, om, dayid, idx, stop_pts, rr, max_hold, flat_om):
    n = len(c); m = len(idx)
    RL = np.full(m, np.nan); RSs = np.full(m, np.nan); XL = np.zeros(m, np.int64); XS = np.zeros(m, np.int64)
    for q in range(m):
        i = idx[q]; e = i + 1
        if e >= n or dayid[e] != dayid[i]:
            continue
        sp = stop_pts[q]
        if not (sp > 0):
            continue
        for d in (1, -1):
            entry = o[e] + d * SLIP
            stop = entry - d * sp; tgt = entry + d * rr * sp
            xp = np.nan; xi = e
            k = e
            while k < n and k < e + max_hold:
                if dayid[k] != dayid[e] or om[k] >= flat_om:
                    xp = o[k] - d * SLIP; xi = k; break
                if d == 1:
                    if k > e and o[k] <= stop: xp = o[k] - SLIP; xi = k; break
                    if l[k] <= stop: xp = stop - SLIP; xi = k; break
                    if h[k] >= tgt + TICK:
                        xp = max(tgt, o[k]) if k > e else tgt; xi = k; break
                else:
                    if k > e and o[k] >= stop: xp = o[k] + SLIP; xi = k; break
                    if h[k] >= stop: xp = stop + SLIP; xi = k; break
                    if l[k] <= tgt - TICK:
                        xp = min(tgt, o[k]) if k > e else tgt; xi = k; break
                k += 1
            if np.isnan(xp):
                kk = min(k, n - 1)
                xp = c[kk - 1] - d * SLIP if kk > e else c[e] - d * SLIP; xi = kk
            r = ((xp - entry) * d - COMM_PTS) / sp
            if d == 1:
                RL[q] = r; XL[q] = xi
            else:
                RSs[q] = r; XS[q] = xi
    return RL, RSs, XL, XS


def build_dataset(cx, sk=1.5, rr=1.0, max_hold=60):
    o, h, l, c, v, om, dayid = cx.o, cx.h, cx.l, cx.c, cx.v, cx.om, cx.dayid
    n = len(c)
    s = pd.DataFrame({"o": o, "h": h, "l": l, "c": c, "v": v, "om": om, "day": dayid})
    # ---- 5-minute ATR from 1-minute data (rolling 5-bar high/low ranges, averaged over 14 x 5 bars) ----
    hh5 = s.h.rolling(5).max(); ll5 = s.l.rolling(5).min()
    tr5 = (hh5 - ll5).to_numpy()
    atr5 = pd.Series(tr5).rolling(70, min_periods=35).mean().to_numpy()
    atr_d = cx.atr_daily()
    A = atr_d[dayid]
    # ---- session VWAP, day high/low, OR60 (RTH) ----
    rth = (om >= 570) & (om < 960)
    tp = (h + l + c) / 3.0
    vv = np.where(v > 0, v, 1.0)
    grp = pd.Series(np.where(rth, dayid, -1))
    pv = pd.Series(np.where(rth, tp * vv, 0.0)).groupby(grp).cumsum().to_numpy()
    vs = pd.Series(np.where(rth, vv, 0.0)).groupby(grp).cumsum().to_numpy()
    vwap = np.where(vs > 0, pv / np.maximum(vs, 1e-9), np.nan)
    dhi = pd.Series(np.where(rth, h, -np.inf)).groupby(grp).cummax().to_numpy()
    dlo = pd.Series(np.where(rth, l, np.inf)).groupby(grp).cummin().to_numpy()
    or_mask = (om >= 570) & (om < 630)
    or_h = pd.Series(np.where(or_mask, h, -np.inf)).groupby(pd.Series(dayid)).cummax().to_numpy()
    or_l = pd.Series(np.where(or_mask, l, np.inf)).groupby(pd.Series(dayid)).cummin().to_numpy()
    L = build_levels(cx)                                   # PDH PDL ONH ONL LonH LonL AsiaH AsiaL
    open930 = np.full(cx.nd, np.nan); m = cx.open_idx >= 0; open930[m] = o[cx.open_idx[m]]
    sma20 = pd.Series(cx.prev_close).rolling(20, min_periods=15).mean().to_numpy()
    sma50 = pd.Series(cx.prev_close).rolling(50, min_periods=40).mean().to_numpy()
    # ---- decision points: 1-minute bars whose CLOSE is on a 5-minute boundary, 09:40..15:00 ----
    close_min = om + 1
    dec = np.where(rth & (close_min >= 580) & (close_min <= 900) & (close_min % 5 == 0))[0]
    dec = dec[(dec > 200) & (dec < n - 2)]
    dec = dec[~np.isnan(atr5[dec]) & ~np.isnan(A[dec])]
    stop_pts = sk * atr5[dec]
    RL, RS, XL, XS = label_brackets(o, h, l, c, om, dayid, dec, stop_pts, rr, max_hold, 955)
    ci = c[dec]; d = dayid[dec]; Ad = A[dec]
    def ret(k):
        return (ci - c[dec - k]) / Ad
    # running swept flags (price beyond level at any time today up to i)
    sweptH = np.zeros((len(dec), 4)); sweptL = np.zeros((len(dec), 4))
    for j, (kh, kl) in enumerate([(0, 1), (2, 3), (4, 5), (6, 7)]):
        lvh = L[d, kh]; lvl = L[d, kl]
        sweptH[:, j] = (dhi[dec] > lvh).astype(float)
        sweptL[:, j] = (dlo[dec] < lvl).astype(float)
    # recent FVG / inversion counts in the last 30 bars
    bullfvg = np.r_[False, False, l[2:] > h[:-2]]
    bearfvg = np.r_[False, False, h[2:] < l[:-2]]
    bf30 = pd.Series(bullfvg.astype(float)).rolling(30).sum().to_numpy()
    sf30 = pd.Series(bearfvg.astype(float)).rolling(30).sum().to_numpy()
    vol_rel = (pd.Series(v).rolling(5).mean() / pd.Series(v).rolling(390, min_periods=100).mean()).to_numpy()
    X = pd.DataFrame({
        "tod": close_min[dec], "dow": cx.d["dow"][dec],
        "r1": ret(1), "r5": ret(5), "r15": ret(15), "r30": ret(30), "r60": ret(60), "r120": ret(120),
        "vwap_d": (ci - vwap[dec]) / Ad,
        "vwap_slope": (vwap[dec] - vwap[dec - 15]) / Ad,
        "pos_day": (ci - dlo[dec]) / np.maximum(dhi[dec] - dlo[dec], 1e-9),
        "day_rng": (dhi[dec] - dlo[dec]) / Ad,
        "or_h_d": (ci - or_h[dec]) / Ad, "or_l_d": (ci - or_l[dec]) / Ad,
        "pdh_d": (ci - L[d, 0]) / Ad, "pdl_d": (ci - L[d, 1]) / Ad, "onh_d": (ci - L[d, 2]) / Ad, "onl_d": (ci - L[d, 3]) / Ad,
        "swH_pd": sweptH[:, 0], "swL_pd": sweptL[:, 0], "swH_on": sweptH[:, 1], "swL_on": sweptL[:, 1],
        "swH_lon": sweptH[:, 2], "swL_lon": sweptL[:, 2],
        "gap": (open930[d] - cx.prev_close[d]) / Ad,
        "from_open": (ci - open930[d]) / Ad,
        "trend20": (cx.prev_close[d] - sma20[d]) / Ad, "trend50": (cx.prev_close[d] - sma50[d]) / Ad,
        "atr_ratio": atr5[dec] / Ad, "atr_pct": Ad / ci,
        "bull_fvg30": bf30[dec], "bear_fvg30": sf30[dec], "vol_rel": vol_rel[dec],
        "body1": (c[dec] - o[dec]) / np.maximum(h[dec] - l[dec], TICK),
    })
    meta = pd.DataFrame({"i": dec, "date": cx.date[dec], "year": cx.date[dec] // 10000, "RL": RL, "RS": RS, "XL": XL, "XS": XS,
                         "stop_pts": stop_pts})
    ok = ~np.isnan(RL) & ~np.isnan(RS)
    return X[ok].reset_index(drop=True), meta[ok].reset_index(drop=True)


def walk_forward(X, meta, test_years=(2023, 2024, 2025, 2026), seed=0):
    preds = []
    for y in test_years:
        tr = (meta.year < y).to_numpy()
        te = (meta.year == y).to_numpy()
        Xtr, Xte = X[tr], X[te]
        mL = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=200,
                                           l2_regularization=1.0, random_state=seed)
        mS = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=200,
                                           l2_regularization=1.0, random_state=seed)
        mL.fit(Xtr, meta.RL[tr].clip(-1.5, 3)); mS.fit(Xtr, meta.RS[tr].clip(-1.5, 3))
        pL_tr = mL.predict(Xtr); pS_tr = mS.predict(Xtr)
        p = meta[te].copy(); p["pL"] = mL.predict(Xte); p["pS"] = mS.predict(Xte)
        # thresholds fixed from the TRAINING period (top quantiles of predicted edge)
        best_tr = np.maximum(pL_tr, pS_tr)
        p["thr90"] = np.quantile(best_tr, 0.90); p["thr95"] = np.quantile(best_tr, 0.95); p["thr98"] = np.quantile(best_tr, 0.98)
        preds.append(p)
    return pd.concat(preds).reset_index(drop=True)


def trade_sim(p, thr_col, one_at_a_time=True):
    """Sequential: at each decision point, if flat and best prediction > threshold, take that side."""
    p = p.sort_values("i").reset_index(drop=True)
    busy_until = -1; rows = []
    for r in p.itertuples():
        if r.i <= busy_until:
            continue
        thr = getattr(r, thr_col)
        if max(r.pL, r.pS) <= thr or max(r.pL, r.pS) <= 0:
            continue
        if r.pL >= r.pS:
            R, xi, side = r.RL, r.XL, 1
        else:
            R, xi, side = r.RS, r.XS, -1
        rows.append((r.date, r.year, side, R, r.stop_pts))
        if one_at_a_time:
            busy_until = xi
    return pd.DataFrame(rows, columns=["date", "year", "side", "R", "stop_pts"])


if __name__ == "__main__":
    import sys, time
    pd.set_option("display.width", 250)
    sk = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
    rr = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    t0 = time.time()
    cx = Ctx()
    X, meta = build_dataset(cx, sk=sk, rr=rr)
    print(f"samples {len(X)}  features {X.shape[1]}  build {time.time()-t0:.0f}s  | base WR long {(meta.RL>0).mean():.3f} short {(meta.RS>0).mean():.3f}  meanR L {meta.RL.mean():.3f} S {meta.RS.mean():.3f}")
    P = walk_forward(X, meta)
    P.to_pickle(f"ml_preds_sk{sk}_rr{rr}.pkl")
    for thr in ("thr90", "thr95", "thr98"):
        t = trade_sim(P, thr)
        if len(t) == 0:
            continue
        g = t.groupby("year").agg(n=("R", "size"), wr=("R", lambda x: round((x > 0).mean() * 100, 1)), avgR=("R", "mean"),
                                  pf=("R", lambda x: round(x[x > 0].sum() / -x[x <= 0].sum(), 2)), totR=("R", "sum"))
        print(f"\n=== OOS walk-forward, threshold {thr} (bracket stop {sk}xATR5, 1:{rr}) ===")
        print(g.round(3).to_string())
        print(f"ALL OOS: n {len(t)}  WR {(t.R>0).mean()*100:.1f}%  avgR {t.R.mean():.3f}  PF {t.R[t.R>0].sum()/-t.R[t.R<=0].sum():.2f}  trades/day {len(t)/t.date.nunique():.2f}")
    print(f"total {time.time()-t0:.0f}s")
