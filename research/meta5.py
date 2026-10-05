"""Meta-labeling on 5-minute NQ: 16 primary strategies generate signals; a gradient-boosting meta-model learns
which signals win in which context. Strict walk-forward: for test year Y, the probability threshold is chosen on
year Y-1 using a model trained on years < Y-1; the final model is trained on years < Y and applied to Y.
Entries at the next 1-minute open after the 5-minute bar close; exits simulated on 1-minute bars
(stop first if both touch in one minute), 1 tick slippage, $1 RT commission (MNQ)."""
import numpy as np, pandas as pd
from numba import njit
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
import engine as en
from common import Ctx
from levels import build_levels

TICK = 0.25; SLIP = 0.25; COMM_PTS = 0.5
SIG_NAMES = ["ORB30", "ORB60", "VWAPreclaim", "EMAcross", "EMApullback", "RSI2", "BBfade", "Donchian",
             "PDHbreak", "PDHsweepFade", "ONsweepFade", "IFVG5", "InsideBar", "OpenDrive", "GapFade", "VWAPfade"]


def resample5(cx):
    o, h, l, c, v, om, dayid, date = cx.o, cx.h, cx.l, cx.c, cx.v, cx.om, cx.dayid, cx.date
    key = dayid.astype(np.int64) * 10000 + (om // 5)
    brk = np.r_[0, np.where(np.diff(key) != 0)[0] + 1]
    end = np.r_[brk[1:], len(c)]
    return dict(o=o[brk], c=c[end - 1], h=np.maximum.reduceat(h, brk), l=np.minimum.reduceat(l, brk),
                v=np.add.reduceat(v, brk), om=(om[brk] // 5) * 5, dayid=dayid[brk], date=date[brk], i1=end)   # i1: 1-min index after the bar


def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().to_numpy()


def rsi(c, n):
    d = np.diff(c, prepend=c[0]); up = np.clip(d, 0, None); dn = np.clip(-d, 0, None)
    au = pd.Series(up).ewm(alpha=1 / n, adjust=False).mean(); ad = pd.Series(dn).ewm(alpha=1 / n, adjust=False).mean()
    return (100 - 100 / (1 + au / ad.replace(0, np.nan))).fillna(50).to_numpy()


@njit(cache=True)
def label(o1, h1, l1, c1, om1, day1, ent, dirs, stop_pts, rr, max_hold, flat_om):
    m = len(ent); R = np.full(m, np.nan); XI = np.zeros(m, np.int64)
    n = len(c1)
    for q in range(m):
        e = ent[q]; d = dirs[q]; sp = stop_pts[q]
        if e >= n or not (sp > 0):
            continue
        entry = o1[e] + d * SLIP; stop = entry - d * sp; tgt = entry + d * rr * sp
        xp = np.nan; xi = e; k = e
        while k < n and k < e + max_hold:
            if day1[k] != day1[e] or om1[k] >= flat_om:
                xp = o1[k] - d * SLIP; xi = k; break
            if d == 1:
                if k > e and o1[k] <= stop: xp = o1[k] - SLIP; xi = k; break
                if l1[k] <= stop: xp = stop - SLIP; xi = k; break
                if h1[k] >= tgt + TICK: xp = max(tgt, o1[k]) if k > e else tgt; xi = k; break
            else:
                if k > e and o1[k] >= stop: xp = o1[k] + SLIP; xi = k; break
                if h1[k] >= stop: xp = stop + SLIP; xi = k; break
                if l1[k] <= tgt - TICK: xp = min(tgt, o1[k]) if k > e else tgt; xi = k; break
            k += 1
        if np.isnan(xp):
            kk = min(k, n - 1); xp = c1[kk - 1] - d * SLIP; xi = kk - 1
        R[q] = ((xp - entry) * d - COMM_PTS) / sp; XI[q] = xi
    return R, XI


def build(cx, sk=1.5, rr=1.0, max_hold=60):
    B = resample5(cx)
    o, h, l, c, v, om, dayid, date, i1 = (B[k] for k in ("o", "h", "l", "c", "v", "om", "dayid", "date", "i1"))
    n = len(c)
    atr5 = en.atr_nt(h, l, c, 14)
    atr_d = cx.atr_daily(); A = atr_d[dayid]
    sma20 = pd.Series(cx.prev_close).rolling(20, min_periods=15).mean().to_numpy()
    sma50 = pd.Series(cx.prev_close).rolling(50, min_periods=40).mean().to_numpy()
    T = np.nan_to_num(np.sign(cx.prev_close - sma20))[dayid]
    rth = (om >= 570) & (om < 960)
    day_s = pd.Series(dayid)
    # session VWAP (RTH), day range, opening ranges
    tp = (h + l + c) / 3; vv = np.where(v > 0, v, 1.0)
    g = pd.Series(np.where(rth, dayid, -1))
    pv = pd.Series(np.where(rth, tp * vv, 0.0)).groupby(g).cumsum().to_numpy()
    vs = pd.Series(np.where(rth, vv, 0.0)).groupby(g).cumsum().to_numpy()
    vwap = np.where(vs > 0, pv / np.maximum(vs, 1e-9), np.nan)
    dhi = pd.Series(np.where(rth, h, -np.inf)).groupby(g).cummax().to_numpy()
    dlo = pd.Series(np.where(rth, l, np.inf)).groupby(g).cummin().to_numpy()
    def rng_levels(t0, t1):
        # running (partial) range up to the current bar -> no look-ahead before the range is complete
        m = (om >= t0) & (om < t1)
        hi = pd.Series(np.where(m, h, -np.inf)).groupby(day_s).cummax().to_numpy()
        lo = pd.Series(np.where(m, l, np.inf)).groupby(day_s).cummin().to_numpy()
        return np.where(np.isinf(hi), np.nan, hi), np.where(np.isinf(lo), np.nan, lo)
    or30h, or30l = rng_levels(570, 600); or60h, or60l = rng_levels(570, 630)
    L = build_levels(cx); PDH, PDL, ONH, ONL = L[dayid, 0], L[dayid, 1], L[dayid, 2], L[dayid, 3]
    open930 = pd.Series(np.where(om == 570, o, np.nan)).groupby(day_s).transform("max").to_numpy()
    prevc = cx.prev_close[dayid]
    e9, e21, e50 = ema(c, 9), ema(c, 21), ema(c, 50)
    r2, r14 = rsi(c, 2), rsi(c, 14)
    ma20 = pd.Series(c).rolling(20).mean().to_numpy(); sd20 = pd.Series(c).rolling(20).std().to_numpy()
    bbu, bbl = ma20 + 2 * sd20, ma20 - 2 * sd20
    don_h = pd.Series(h).shift(1).rolling(20).max().to_numpy(); don_l = pd.Series(l).shift(1).rolling(20).min().to_numpy()
    s5, ref5, *_ = en.ifvg_signals(o, h, l, c, atr5, 0.25, 0.5, 0.65, 0.05, 2, 500, 500, 1, 1.5, rr, 20, True, False, 1.5, 50)
    prev = lambda x: np.r_[np.nan, x[:-1]]
    cp, hp, lp = prev(c), prev(h), prev(l)
    vwp = prev(vwap)
    win = rth & (om + 5 >= 580) & (om + 5 <= 930)          # bar CLOSE between 09:40 and 15:30
    S = np.zeros((n, len(SIG_NAMES)), np.int8)
    S[:, 0] = np.where((om >= 600) & (c > or30h) & (cp <= or30h), 1, np.where((om >= 600) & (c < or30l) & (cp >= or30l), -1, 0))
    S[:, 1] = np.where((om >= 630) & (c > or60h) & (cp <= or60h), 1, np.where((om >= 630) & (c < or60l) & (cp >= or60l), -1, 0))
    S[:, 2] = np.where((om >= 600) & (T == 1) & (cp < vwp) & (c > vwap), 1, np.where((om >= 600) & (T == -1) & (cp > vwp) & (c < vwap), -1, 0))
    e9p, e21p = prev(e9), prev(e21)
    S[:, 3] = np.where((T == 1) & (e9p <= e21p) & (e9 > e21), 1, np.where((T == -1) & (e9p >= e21p) & (e9 < e21), -1, 0))
    S[:, 4] = np.where((T == 1) & (e21 > e50) & (l <= e21) & (c > e9), 1, np.where((T == -1) & (e21 < e50) & (h >= e21) & (c < e9), -1, 0))
    S[:, 5] = np.where((T == 1) & (r2 < 10), 1, np.where((T == -1) & (r2 > 90), -1, 0))
    S[:, 6] = np.where((cp < prev(bbl)) & (c > bbl), 1, np.where((cp > prev(bbu)) & (c < bbu), -1, 0))
    S[:, 7] = np.where((T == 1) & (c > don_h), 1, np.where((T == -1) & (c < don_l), -1, 0))
    S[:, 8] = np.where((c > PDH) & (cp <= PDH), 1, np.where((c < PDL) & (cp >= PDL), -1, 0))
    S[:, 9] = np.where((h > PDH) & (c < PDH) & (cp < PDH), -1, np.where((l < PDL) & (c > PDL) & (cp > PDL), 1, 0))
    S[:, 10] = np.where((h > ONH) & (c < ONH) & (cp < ONH), -1, np.where((l < ONL) & (c > ONL) & (cp > ONL), 1, 0))
    S[:, 11] = s5
    ib = (hp <= prev(hp)) & (lp >= prev(lp))
    S[:, 12] = np.where(ib & (c > hp), 1, np.where(ib & (c < lp), -1, 0))
    S[:, 13] = np.where((om == 595) & (c - open930 > 0.15 * A), 1, np.where((om == 595) & (open930 - c > 0.15 * A), -1, 0))
    gap = (open930 - prevc) / A
    S[:, 14] = np.where((om == 575) & (gap > 0.1) & (c < o), -1, np.where((om == 575) & (gap < -0.1) & (c > o), 1, 0))
    S[:, 15] = np.where((om >= 630) & (c - vwap > 0.25 * A) & (c < o), -1, np.where((om >= 630) & (vwap - c > 0.25 * A) & (c > o), 1, 0))
    S[~win] = 0
    S[np.isnan(atr5) | np.isnan(A)] = 0
    # ---- samples ----
    bars, types = np.nonzero(S)
    dirs = S[bars, types].astype(np.int64)
    ent = i1[bars]
    ok = (ent < len(cx.c)) & (cx.dayid[np.minimum(ent, len(cx.c) - 1)] == dayid[bars])
    bars, types, dirs, ent = bars[ok], types[ok], dirs[ok], ent[ok]
    stop_pts = sk * atr5[bars]
    Rv, XI = label(cx.o, cx.h, cx.l, cx.c, cx.om, cx.dayid, ent, dirs, stop_pts, rr, max_hold, 955)
    same = (S[bars] == dirs[:, None]).sum(1) - 1; opp = (S[bars] == -dirs[:, None]).sum(1)
    d = dirs.astype(float); Ab = A[bars]; cb = c[bars]
    def r_(k): return (cb - c[np.maximum(bars - k, 0)]) / Ab * d
    F = pd.DataFrame({
        "type": types, "dir": d, "confl_same": same, "confl_opp": opp, "tod": om[bars] + 5, "dow": cx.d["dow"][cx.open_idx[dayid[bars]].clip(0)],
        "r1": r_(1), "r3": r_(3), "r6": r_(6), "r12": r_(12), "r24": r_(24),
        "vwap_d": (cb - vwap[bars]) / Ab * d, "vwap_slope": (vwap[bars] - vwap[np.maximum(bars - 6, 0)]) / Ab * d,
        "pos_day": np.where(d > 0, (cb - dlo[bars]), (dhi[bars] - cb)) / np.maximum(dhi[bars] - dlo[bars], 1e-9),
        "day_rng": (dhi[bars] - dlo[bars]) / Ab,
        "or60h_d": (cb - or60h[bars]) / Ab * d, "or60l_d": (cb - or60l[bars]) / Ab * d,
        "pdh_d": (cb - PDH[bars]) / Ab * d, "pdl_d": (cb - PDL[bars]) / Ab * d, "onh_d": (cb - ONH[bars]) / Ab * d, "onl_d": (cb - ONL[bars]) / Ab * d,
        "gap": gap[bars] * d, "from_open": (cb - open930[bars]) / Ab * d,
        "trend20": (prevc[bars] - sma20[dayid[bars]]) / Ab * d, "trend50": (prevc[bars] - sma50[dayid[bars]]) / Ab * d,
        "atr_ratio": atr5[bars] / Ab, "atr_pct": Ab / cb, "rsi2": np.where(d > 0, r2[bars], 100 - r2[bars]), "rsi14": np.where(d > 0, r14[bars], 100 - r14[bars]),
        "bb_pos": (cb - ma20[bars]) / np.maximum(2 * sd20[bars], 1e-9) * d, "ema_slope": (e21[bars] - e21[np.maximum(bars - 3, 0)]) / Ab * d,
        "ema_stack": np.sign(e9[bars] - e21[bars]) * d + np.sign(e21[bars] - e50[bars]) * d,
        "vol_rel": v[bars] / np.maximum(pd.Series(v).rolling(78, min_periods=20).mean().to_numpy()[bars], 1e-9),
        "body": (c[bars] - o[bars]) / np.maximum(h[bars] - l[bars], TICK) * d,
    })
    meta = pd.DataFrame({"bar": bars, "ent": ent, "xi": XI, "date": date[bars], "year": date[bars] // 10000, "R": Rv, "type": types,
                         "dir": dirs, "stop_pts": stop_pts})
    keep = ~np.isnan(Rv)
    return F[keep].reset_index(drop=True), meta[keep].reset_index(drop=True)


def model_c(seed=0):
    return HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=150,
                                          l2_regularization=1.0, categorical_features=[0], random_state=seed)


def walk_forward(F, M, years=(2023, 2024, 2025, 2026), min_trades_cal=150):
    out = []
    y_all = (M.R > 0).astype(int)
    for Y in years:
        cal = (M.year == Y - 1).to_numpy(); pre = (M.year < Y - 1).to_numpy()
        m1 = model_c(); m1.fit(F[pre], y_all[pre])
        pc = m1.predict_proba(F[cal])[:, 1]
        # threshold on the calibration year: best avg R with at least min_trades_cal signals
        best_thr, best_val = 0.5, -9
        for thr in np.arange(0.40, 0.80, 0.01):
            sel = pc >= thr
            if sel.sum() < min_trades_cal:
                break
            val = M.R[cal][sel].mean()
            if val > best_val:
                best_val, best_thr = val, thr
        tr = (M.year < Y).to_numpy(); te = (M.year == Y).to_numpy()
        m2 = model_c(); m2.fit(F[tr], y_all[tr])
        p = M[te].copy(); p["p"] = m2.predict_proba(F[te])[:, 1]; p["thr"] = best_thr; p["cal_avgR"] = best_val
        out.append(p)
    return pd.concat(out).reset_index(drop=True)


def trade(P, max_pos=1):
    """Sequential: at each 5-min bar, among signals with p >= thr choose the highest p; one position at a time."""
    P = P[P.p >= P.thr].sort_values(["bar", "p"], ascending=[True, False])
    busy = -1; rows = []
    for r in P.itertuples():
        if r.ent <= busy:
            continue
        rows.append((r.date, r.year, r.type, r.dir, r.R, r.p, r.stop_pts, r.ent, r.xi))
        busy = r.xi
    return pd.DataFrame(rows, columns=["date", "year", "type", "dir", "R", "p", "stop_pts", "ent", "xi"])


if __name__ == "__main__":
    import sys, time
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
    sk = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
    rr = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    mh = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    t0 = time.time()
    cx = Ctx()
    F, M = build(cx, sk, rr, mh)
    print(f"samples {len(F)}  build {time.time()-t0:.0f}s  base WR {(M.R>0).mean()*100:.1f}%  base avgR {M.R.mean():.3f}")
    base = M.groupby("type").agg(n=("R", "size"), wr=("R", lambda x: (x > 0).mean() * 100), avgR=("R", "mean"))
    base.index = [SIG_NAMES[i] for i in base.index]
    print(base.round(3).to_string())
    P = walk_forward(F, M)
    P.to_pickle(f"meta5_preds_sk{sk}_rr{rr}.pkl")
    t = trade(P)
    g = t.groupby("year").agg(n=("R", "size"), wr=("R", lambda x: round((x > 0).mean() * 100, 1)), avgR=("R", "mean"),
                              pf=("R", lambda x: round(x[x > 0].sum() / -x[x <= 0].sum(), 2)), totR=("R", "sum"))
    print(f"\n=== META-MODEL walk-forward OOS (stop {sk}xATR5m, 1:{rr}) ===")
    print(g.round(3).to_string())
    print(f"ALL OOS: n {len(t)}  WR {(t.R>0).mean()*100:.1f}%  avgR {t.R.mean():.3f}  PF {t.R[t.R>0].sum()/-t.R[t.R<=0].sum():.2f}  trades/day {len(t)/t.date.nunique():.2f}")
    print("thresholds per year:", P.groupby("year").thr.first().round(2).to_dict())
    print(f"total {time.time()-t0:.0f}s")
