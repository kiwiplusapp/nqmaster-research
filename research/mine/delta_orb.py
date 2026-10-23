"""Layer A of the volume / delta / order-flow round (2026-10-21): TRUE aggressor delta (Databento NQ trades, per-minute buy / sell
volume in of_minutes_2025.pkl 2025-05-01..2026-03-31 and of_minutes.pkl / of_minutes_rich.pkl 2026-04-01..2026-10-08, index = epoch
minute = nqdb bar-open minute) on real NQ 1-minute bars (research/data/nqdb.npz).  Import-safe: the shared pieces (flow features,
ORB kernel, A2 signal generators, portfolio test) are reused by families12.py (layer B, bar-delta proxy on 2010-26).

PRE-REGISTERED (fixed before running):
  window 2025-05-01..2026-10-08; CHOOSE = 2025-05-01..2025-12-31, CHECK = 2026-01-01..2026-10-08.  $ per MNQ, $1.90 RT + 1 tick.
  A1 ORB + delta confirmation: opening range 09:30 + T (5/15/30/60 min); breakout = stop order 1 tick beyond the edge (fills in the
     first bar that touches it; delta features use bars <= b-1) or first 1-min CLOSE beyond the edge (market at the next open; features
     use bars <= b, the complete breakout minute); breakouts until 14:00; stop at the opposite edge (floor 0.10 ATR, skip > 1.0 ATR)
     or 0.2 / 0.35 ATR; target 1 / 1.5 / 2 R or the range width ('rng'); flat 15:55; max 1 or 2 trades / day (one event per side);
     with / without the daily trend filter (prior RTH close vs SMA20).  CONTROL = the same cell with no delta condition.  Delta
     conditions (oriented with the break): dl1 / dl5 / dl15 = (buy - sell) / (buy + sell) of the last 1 / 5 / 15 min >= 0 / .03 / .06 / .10;
     cum = session delta since 09:30 >= 0 / .01 / .02 / .04; q5 / q15 = raw delta of the last 5 / 15 min >= the 0.5 / 0.75 / 0.9 quantile
     of |the previous 12 windows of the same length|; big15 = (buy50 - sell50) / (buy50 + sell50) over 15 min >= 0 / .10 (prints >= 50
     contracts, only from 2026-04-01 -> information only, no choose period).  The delta version is the control's event set masked by
     the condition (a dropped first break lets the other side's break trade, as it would live).
  A2 delta patterns, market at the next open, window 09:35-15:30, flat 15:55, max 2 / day, stop 0.2 / 0.35 ATR, target 0.5 / 1 / 2 R:
     ABS   absorption: volume >= m x the previous 20-min mean (m 2 / 3), body <= 0.25 x range, at the RTH high / low so far or within
           0.05 ATR of the ORB30 edge (after 10:00) -> fade; dcond none (control) / 'with' (minute delta pushes into the extreme) / 'against'.
     DIV   new W-min high (W 15 / 30, window inside RTH) with session CVD below its W-min max -> fade (control: fade every new high);
           CVD at a new max too -> follow (control: follow every new high); mirror for lows.
     VFLIP price within 0.05 ATR of the RTH VWAP, 5-min delta ratio flips sign with |dl5| >= .05 / .10 -> follow the new delta sign;
           control: the 5-min price change flips sign -> follow it.
     CLIMAX |minute delta| >= z x the std of the previous 60 minutes (z 3 / 4) -> fade or follow; control: volume >= mean + z std of the
           previous 60 minutes, direction = sign(close - open).
  Every feature at bar t uses bars <= t (entry at t+1 open) or <= b-1 for resting stop orders: no lookahead.
  ACCEPTANCE (a cell survives only if ALL hold): n >= 60 in CHOOSE; PF >= 1.3 CHOOSE; PF >= 1.2 CHECK; CHECK PF with +4 ticks per side
     (extra $3 per trade over the base 1 tick) >= 1.1; delta cell PF >= control PF + 0.15 in BOTH periods and n >= 50% of the control's
     in both; plateau: >= half of the numeric one-step neighbours (T, stop, R, threshold / m / W / z) have CHOOSE PF >= 1.15.
     Survivors then go to the portfolio test vs nt_compare.research_set('ultra_d4') with wrq_port.conflict_filter: Sharpe up in both
     periods, max DD / worst month not worse by > 5%, daily correlation < 0.3; 21-day block bootstrap of the daily gain vs control.
  Base rates: P(CHECK PF >= 1.2 | CHOOSE PF >= 1.3) vs P(CHECK PF >= 1.2); P(beats control in CHECK | beats in CHOOSE) vs overall.
Earlier findings NOT re-tested: session-CVD-with-trade x2 boost failed OOS (of_validate), dl5/15/30 quintile orderings flip between
samples, top-of-book imbalance skip rules fail OOS (of_bbo).
-> delta_orb.json (tables), delta_orb_trades.pkl (trades of the cells that reach the portfolio stage)"""
import os, sys, json, pickle, itertools, numpy as np, pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.dirname(HERE)
for p in (HERE, RES):
    if p not in sys.path: sys.path.insert(0, p)
from core import S, TICK, run_events, ev_from_lists

HOLD = 100000; FLAT = 955; BRK_END = S(1400); RMIN, RMAX = 0.10, 1.0
CH = (20250501, 20260101); CK = (20260101, 20261009)
COST4 = 3.0                                              # +4 ticks per side = $3 more than the base 1 tick per trade (b8 convention)


def pf(u):
    u = np.asarray(u, float); l = -u[u <= 0].sum()
    return round(float(u[u > 0].sum() / l), 3) if l > 0 and len(u) else None


# ------------------------------------------------------------------------------------------------ flow features
class Flow:
    """delta / volume per 1m bar + cumulative sums; have[i] = the bar lies inside the flow data."""
    def __init__(self, delta, vol, have, b50=None, s50=None, have50=None):
        self.delta = np.asarray(delta, float); self.vol = np.asarray(vol, float); self.have = have
        self.cd = np.cumsum(np.r_[0.0, self.delta]); self.cv = np.cumsum(np.r_[0.0, self.vol])
        self.b50 = b50; self.s50 = s50; self.have50 = have50
        if b50 is not None: self.cb50 = np.cumsum(np.r_[0.0, b50]); self.cs50 = np.cumsum(np.r_[0.0, s50])

    def ratio(self, k, w, floor):
        lo = np.maximum(k - w + 1, floor); sd = self.cd[k + 1] - self.cd[lo]; sv = self.cv[k + 1] - self.cv[lo]
        return np.where(sv > 0, sd / np.maximum(sv, 1e-9), 0.0)

    def raw(self, k, w):
        lo = np.maximum(k - w + 1, 0); return self.cd[k + 1] - self.cd[lo]

    def qref(self, k, w, q):
        ref = np.stack([np.abs(self.raw(k - j * w, w)) for j in range(1, 13)]); return np.quantile(ref, q, axis=0)

    def big(self, k, w, floor):
        if self.b50 is None: return np.full(len(k), np.nan)
        lo = np.maximum(k - w + 1, floor); B = self.cb50[k + 1] - self.cb50[lo]; A = self.cs50[k + 1] - self.cs50[lo]
        r = np.where(B + A > 0, (B - A) / np.maximum(B + A, 1e-9), 0.0); return np.where(self.have50[k], r, np.nan)

    def feats(self, k, s, floor_sess, floor_rth):
        """event features oriented with the trade side s, from bars <= k."""
        F = {}
        for w in (1, 5, 15): F[f"dl{w}"] = self.ratio(k, w, floor_sess) * s
        F["cum"] = self.ratio(k, k - floor_rth + 1, floor_rth) * s
        for w in (5, 15):
            cur = self.raw(k, w) * s
            for q in (0.5, 0.75, 0.9): F[f"q{w}_{q}"] = cur - self.qref(k, w, q)
        F["big15"] = self.big(k, 15, floor_sess) * s
        return F


CONDS = [("none", 0.0)] + [(f"dl{w}", t) for w in (1, 5, 15) for t in (0.0, 0.03, 0.06, 0.10)] + [("cum", t) for t in (0.0, 0.01, 0.02, 0.04)] + \
        [(f"q{w}", q) for w in (5, 15) for q in (0.5, 0.75, 0.9)] + [("big15", t) for t in (0.0, 0.10)]


def cond_mask(F, cw, thr):
    if cw == "none": return np.ones(len(F["dl1"]), bool)
    if cw.startswith("q"): return F[f"{cw}_{thr}"] >= 0
    x = F[cw]; return np.where(np.isnan(x), False, x >= thr)


def true_flow(D):
    """true aggressor delta aligned with nqdb bars (epoch minutes)."""
    ep = np.load(os.path.join(RES, "data", "nqdb.npz"))["epoch"]
    M = pd.concat([pickle.load(open(os.path.join(HERE, "of_minutes_2025.pkl"), "rb"))[["buy", "sell"]],
                   pickle.load(open(os.path.join(HERE, "of_minutes.pkl"), "rb"))[["buy", "sell"]]]).sort_index()
    Sx = M.reindex(ep).fillna(0.0); have = (ep >= M.index.min()) & (ep <= M.index.max())
    R = pickle.load(open(os.path.join(HERE, "of_minutes_rich.pkl"), "rb"))[["buy50", "sell50"]].reindex(ep).fillna(0.0)
    buy, sell = Sx.buy.to_numpy(), Sx.sell.to_numpy()
    return Flow(buy - sell, buy + sell, have, R.buy50.to_numpy(), R.sell50.to_numpy(), ep >= 29583360), have


def proxy_delta(D, kind):
    """bar-delta proxy: 'cl' = volume x (2 (close - low) / (high - low) - 1); 'tr' = sign(close - open) x volume."""
    if kind == "cl":
        rng = D.h - D.l; return np.where(rng > 0, D.v * (2.0 * (D.c - D.l) / np.where(rng > 0, rng, 1.0) - 1.0), 0.0)
    return np.sign(D.c - D.o) * D.v


def proxy_flow(D, kind):
    if not hasattr(D, "_pflow"): D._pflow = {}
    if kind not in D._pflow: D._pflow[kind] = Flow(proxy_delta(D, kind), D.v, np.ones(D.n, bool))
    return D._pflow[kind]


# ------------------------------------------------------------------------------------------------ A1: opening-range breakouts
@njit(cache=True)
def _orbx(h, l, c, sm, ro, ds, de, atr, T, mode, brk_end):
    """per day: first up-break and first down-break of the range [09:30, 09:30 + T): rows (b, s, rh, rl, d); mode 0 stop (touch), 1 close."""
    out = np.zeros((2 * len(ds), 5)); n = 0; A = 570 - 1080 + 1440
    for d in range(len(ds)):
        a = ro[d]
        if a < 0 or atr[d] <= 0 or sm[a] != A: continue
        e = -1
        for q in range(a, de[d] + 1):
            if sm[q] >= A + T: e = q; break
        if e < 0: continue
        rh = h[a]; rl = l[a]
        for q in range(a, e):
            rh = max(rh, h[q]); rl = min(rl, l[q])
        bu = -1; bd = -1
        for q in range(e, de[d] + 1):
            if sm[q] >= brk_end: break
            if mode == 0:
                up = h[q] >= rh + 0.25; dn = l[q] <= rl - 0.25
            else:
                up = c[q] > rh; dn = c[q] < rl
            if up and dn and bu < 0 and bd < 0: bu = -2; break
            if up and bu < 0: bu = q
            if dn and bd < 0: bd = q
            if bu >= 0 and bd >= 0: break
        if bu == -2: continue
        if bu >= 0: out[n, 0] = bu; out[n, 1] = 1; out[n, 2] = rh; out[n, 3] = rl; out[n, 4] = d; n += 1
        if bd >= 0: out[n, 0] = bd; out[n, 1] = -1; out[n, 2] = rh; out[n, 3] = rl; out[n, 4] = d; n += 1
    return out[:n]


def orb_breaks(D, T, ent):
    key = ("_orbx", T, ent)
    if not hasattr(D, "_orbc"): D._orbc = {}
    if key not in D._orbc:
        X = _orbx(D.h, D.l, D.c, D.sm, D.ro, D.ds, D.de, D.atr, T, 0 if ent == "stop" else 1, BRK_END)
        o = np.argsort(X[:, 0], kind="stable"); D._orbc[key] = X[o]
    return D._orbc[key]


def orb_events(D, T, ent, sk, R, tf):
    """events (core format) + the feature bar k per event + day. sk 'opp' or ATR fraction; R number or 'rng'."""
    X = orb_breaks(D, T, ent)
    b = X[:, 0].astype(np.int64); s = X[:, 1].astype(np.int64); rh = X[:, 2]; rl = X[:, 3]; d = X[:, 4].astype(np.int64)
    A = D.atr[d]
    if ent == "stop": ref = np.where(s == 1, rh + TICK, rl - TICK); i = b - 1; t = np.full(len(b), 2.0); px = ref; exp = b; k = b - 1
    else: ref = D.c[b]; i = b; t = np.zeros(len(b)); px = ref; exp = b; k = b
    if sk == "opp": risk = np.maximum(np.where(s == 1, ref - (rl - TICK), (rh + TICK) - ref), RMIN * A)
    else: risk = sk * A
    tgt = ref + s * (risk * R if R != "rng" else (rh - rl))
    ok = (risk <= RMAX * A) & (A > 0) & (k >= 1) & ((s == D.trend[d]) if tf else True)
    ev = dict(i=i, d=s.astype(float), t=t, px=px, sl=ref - s * risk, tp=tgt, exp=exp, hold=np.full(len(b), HOLD))
    return {kk: v[ok] for kk, v in ev.items()}, k[ok], d[ok]


# ------------------------------------------------------------------------------------------------ A2: delta patterns
def _roll(x, w, fn):
    return getattr(pd.Series(x).rolling(w), fn)().shift(1).to_numpy()


def a2_base(D, F, lo, hi):
    """per-bar context on the slice [lo, hi): everything at bar t uses bars <= t."""
    key = ("_a2", lo, hi, id(F))
    if not hasattr(D, "_a2c"): D._a2c = {}
    if key in D._a2c: return D._a2c[key]
    sl_ = slice(lo, hi); o, h, l, c, v, sm, day, om = D.o[sl_], D.h[sl_], D.l[sl_], D.c[sl_], D.v[sl_], D.sm[sl_], D.day[sl_], D.om[sl_]
    delta = F.delta[sl_]; atr = D.atr[day]; rth = (om >= 570) & (om < 960)
    B = dict(o=o, h=h, l=l, c=c, v=v, sm=sm, day=day, atr=atr, delta=delta, idx=np.arange(lo, hi))
    B["win"] = (sm >= S(935)) & (sm <= S(1530)) & (atr > 0)
    B["v20"] = _roll(v, 20, "mean")
    B["v60m"] = _roll(v, 60, "mean"); B["v60s"] = _roll(v, 60, "std"); B["d60s"] = _roll(delta, 60, "std")
    hh = pd.Series(np.where(rth, h, np.nan)); ll = pd.Series(np.where(rth, l, np.nan))
    B["hmax"] = hh.groupby(day).cummax().to_numpy(); B["lmin"] = ll.groupby(day).cummin().to_numpy()
    cvd = pd.Series(np.where(rth, delta, 0.0)).groupby(day).cumsum().to_numpy(); B["cvd"] = cvd
    for W in (15, 30):
        B[f"hmax{W}"] = _roll(h, W, "max"); B[f"lmin{W}"] = _roll(l, W, "min"); B[f"cmax{W}"] = _roll(cvd, W, "max"); B[f"cmin{W}"] = _roll(cvd, W, "min")
    # ORB30 edges (per day) after 10:00
    e30 = pd.DataFrame(dict(day=day, h=np.where((om >= 570) & (om < 600), h, np.nan), l=np.where((om >= 570) & (om < 600), l, np.nan))).groupby("day").agg(h=("h", "max"), l=("l", "min"))
    B["o30h"] = e30.h.reindex(day).to_numpy(); B["o30l"] = e30.l.reindex(day).to_numpy()
    k = np.arange(lo, hi); floor = D.ds[day]
    B["dl5"] = F.ratio(k, 5, floor); B["dl5p"] = F.ratio(np.maximum(k - 5, 0), 5, floor)
    B["r5"] = c - np.r_[np.full(5, np.nan), c[:-5]]; B["r5p"] = np.r_[np.full(5, np.nan), B["r5"][:-5]]
    B["vwap"] = D.vwap[sl_]
    D._a2c[key] = B; return B


def a2_signals(B, fam, p):
    """returns (t, s) arrays of signal bars (slice-relative) for family fam with params p."""
    w = B["win"]; c, h, l, o, v, delta, atr = B["c"], B["h"], B["l"], B["o"], B["v"], B["delta"], B["atr"]
    if fam == "ABS":
        rng = h - l; big = (v >= p["m"] * B["v20"]) & (rng > 0) & (np.abs(c - o) <= 0.25 * rng)
        if p["loc"] == "sess": ext = np.where(h >= B["hmax"], 1, np.where(l <= B["lmin"], -1, 0))
        else:
            after = B["sm"] >= S(1000)
            ext = np.where(after & (np.abs(h - B["o30h"]) <= 0.05 * atr), 1, np.where(after & (np.abs(l - B["o30l"]) <= 0.05 * atr), -1, 0))
        m = w & big & (ext != 0)
        if p["dcond"] == "with": m &= delta * ext >= 0
        elif p["dcond"] == "against": m &= delta * ext < 0
        return np.flatnonzero(m), -ext[m]
    if fam == "DIV":
        W = p["W"]; inside = B["sm"] - W >= S(930)
        nh = w & inside & (h > B[f"hmax{W}"]); nl = w & inside & (l < B[f"lmin{W}"])
        if p["mode"] == "fade_div": nh &= B["cvd"] < B[f"cmax{W}"]; nl &= B["cvd"] > B[f"cmin{W}"]; sh, sl2 = -1, 1
        elif p["mode"] == "fade_all": sh, sl2 = -1, 1
        elif p["mode"] == "follow_conf": nh &= B["cvd"] >= B[f"cmax{W}"]; nl &= B["cvd"] <= B[f"cmin{W}"]; sh, sl2 = 1, -1
        else: sh, sl2 = 1, -1
        t = np.r_[np.flatnonzero(nh), np.flatnonzero(nl)]; s = np.r_[np.full(nh.sum(), sh), np.full(nl.sum(), sl2)]
        o_ = np.argsort(t, kind="stable"); return t[o_], s[o_]
    if fam == "VFLIP":
        near = w & (np.abs(c - B["vwap"]) <= 0.05 * atr)
        if p["mode"] == "delta":
            x, xp = B["dl5"], B["dl5p"]; m = near & (np.sign(x) * np.sign(xp) < 0) & (np.abs(x) >= p["thr"])
        else:
            x, xp = B["r5"], B["r5p"]; m = near & (np.sign(x) * np.sign(xp) < 0) & (np.abs(x) >= TICK)
        m &= ~np.isnan(x) & ~np.isnan(xp); return np.flatnonzero(m), np.sign(x[m]).astype(int)
    if fam == "CLIMAX":
        if p["src"] == "delta": m = w & (np.abs(delta) >= p["z"] * B["d60s"]) & (B["d60s"] > 0); dr = np.sign(delta)
        else: m = w & (v >= B["v60m"] + p["z"] * B["v60s"]) & (B["v60s"] > 0); dr = np.sign(c - o)
        m &= dr != 0; s = dr[m].astype(int); return np.flatnonzero(m), (-s if p["dir"] == "fade" else s)
    raise ValueError(fam)


def a2_events(D, B, fam, p):
    t, s = a2_signals(B, fam, p)
    if len(t) == 0: return ev_from_lists([])
    i = B["idx"][t]; c = B["c"][t]; risk = p["k"] * B["atr"][t]; s = s.astype(float)
    return dict(i=i, d=s, t=np.zeros(len(i)), px=c, sl=c - s * risk, tp=c + s * p["R"] * risk, exp=i, hold=np.full(len(i), HOLD))


# ------------------------------------------------------------------------------------------------ stats / tests
def period_stats(tr, per, cost=0.0):
    u = tr.usd[(tr.date >= per[0]) & (tr.date < per[1])].to_numpy() - cost
    return dict(n=int(len(u)), wr=round(100 * float((u > 0).mean()), 1) if len(u) else None, pf=pf(u), avg=round(float(u.mean()), 1) if len(u) else None, net=round(float(u.sum())))


def daily(tr, days):
    return tr.usd.groupby(tr.date).sum().reindex(days, fill_value=0.0)


def block_boot(g, blk=21, reps=2000, seed=0):
    """21-day block bootstrap of the mean of a daily series g (gain delta - control)."""
    x = np.asarray(g, float); n = len(x); nb = int(np.ceil(n / blk)); rng = np.random.default_rng(seed)
    starts = rng.integers(0, max(n - blk, 1), size=(reps, nb)); idx = (starts[:, :, None] + np.arange(blk)[None, None, :]).reshape(reps, -1)[:, :n]
    m = x[idx].mean(axis=1)
    return dict(mean_per_day=round(float(x.mean()), 2), p_gt0=round(float((m > 0).mean()), 3), ci90=[round(float(np.quantile(m, 0.05)), 2), round(float(np.quantile(m, 0.95)), 2)], days=n)


def port_test(cand, per1, per2, days_filter=None):
    """cand: trades (date, tin, tout, d, u). Ultra (ultra_d4) + cand with the first-come conflict filter, per period Sharpe / DD / worst month."""
    from nt_compare import research_set
    from wrq_port import conflict_filter
    U, _ = research_set("ultra_d4"); lo, hi = per1[0], per2[1]; U = U[(U.date >= lo) & (U.date < hi)].copy()
    days = np.array(sorted(set(U.date.unique())))
    C = cand[(cand.date >= lo) & (cand.date < hi)][["date", "tin", "tout", "d", "u"]].copy(); C["mod"] = "CAND"; C["w"] = 1.0
    X = conflict_filter(pd.concat([U, C], ignore_index=True).sort_values(["date", "tin"], kind="stable").reset_index(drop=True))
    b = (U.u * U.w).groupby(U.date).sum().reindex(days, fill_value=0.0); comb = (X.u * X.w).groupby(X.date).sum().reindex(days, fill_value=0.0)
    cd = (C.u).groupby(C.date).sum().reindex(days, fill_value=0.0)
    def metr(x):
        eq = x.cumsum(); mo = x.groupby(pd.to_datetime(x.index.astype(str)).to_period("M")).sum()
        return dict(sharpe=round(float(x.mean() / x.std() * np.sqrt(252)), 3) if x.std() > 0 else 0.0, net=round(float(x.sum())), maxdd=round(float((eq.cummax() - eq).max())), worst_month=round(float(mo.min())))
    out = {"corr": round(float(np.corrcoef(b, cd)[0, 1]), 3) if cd.std() > 0 else 0.0, "cand_kept": int((X["mod"] == "CAND").sum()), "cand_n": int(len(C))}
    ok = True
    for lab, per in (("choose", per1), ("check", per2), ("all", (lo, hi))):
        m = (b.index >= per[0]) & (b.index < per[1]); mb, mc = metr(b[m]), metr(comb[m]); out[lab] = dict(base=mb, comb=mc, dSharpe=round(mc["sharpe"] - mb["sharpe"], 3))
        if lab != "all": ok &= mc["sharpe"] > mb["sharpe"]
        else: ok &= (mc["maxdd"] <= 1.05 * mb["maxdd"]) and (mc["worst_month"] >= 1.05 * mb["worst_month"])
    out["accepted"] = bool(ok and out["corr"] < 0.3); return out


def neighbours_of(cfg, grid, numeric, cache):
    """indices of grid configs one numeric step away from cfg (per numeric key, both directions), every other key equal."""
    key = lambda g, k: repr(sorted((kk, v) for kk, v in g.items() if kk != k))
    if "idx" not in cache: cache["idx"] = {repr(sorted(g.items())): j for j, g in enumerate(grid)}
    out = []
    for k in numeric:
        if k not in cfg or isinstance(cfg[k], str): continue
        if k not in cache:
            m = {}
            for g in grid:
                if not isinstance(g[k], str): m.setdefault(key(g, k), set()).add(g[k])
            cache[k] = m
        vals = sorted(cache[k].get(key(cfg, k), ()))
        if cfg[k] not in vals: continue
        i = vals.index(cfg[k])
        for di in (-1, 1):
            if 0 <= i + di < len(vals):
                q = dict(cfg); q[k] = vals[i + di]; j = cache["idx"].get(repr(sorted(q.items())))
                if j is not None: out.append(j)
    return out


# ------------------------------------------------------------------------------------------------ main (layer A)
def layer_a():
    from wrq_lib import getD
    D = getD("nqdb.npz"); F, have = true_flow(D)
    lo = int(np.argmax(have)); hi = int(len(have) - np.argmax(have[::-1]))
    dates = D.date; days = np.array(sorted(set(dates[lo:hi][(D.om[lo:hi] >= 570) & (D.om[lo:hi] < 960)])))
    print("flow bars", lo, hi, dates[lo], dates[hi - 1], "RTH days", len(days), flush=True)
    OUT = {"window": [int(dates[lo]), int(dates[hi - 1])], "choose": CH, "check": CK, "days": int(len(days)), "A1": {}, "A2": {}}
    rows = []; TR = {}
    # ---- A1
    ctrl_grid = [dict(T=T, ent=e, sk=sk, R=R, tf=tf, md=md) for T in (5, 15, 30, 60) for e in ("stop", "close") for sk in ("opp", 0.2, 0.35) for R in (1.0, 1.5, 2.0, "rng") for tf in (0, 1) for md in (1, 2)]
    for ci, cfg in enumerate(ctrl_grid):
        ev, k, d = orb_events(D, cfg["T"], cfg["ent"], cfg["sk"], cfg["R"], cfg["tf"])
        inw = have[k] & have[D.ds[d]] & (k - 200 >= lo); ev = {kk: v[inw] for kk, v in ev.items()}; k = k[inw]; d = d[inw]
        Fe = F.feats(k, ev["d"], D.ds[d], D.ro[d])
        for cw, thr in CONDS:
            m = cond_mask(Fe, cw, thr); e2 = {kk: v[m] for kk, v in ev.items()}
            tr = run_events(D, e2, flat=FLAT, maxday=cfg["md"], slip=0.25)
            r = dict(fam="ORB", ci=ci, **cfg, cw=cw, thr=thr, ch=period_stats(tr, CH), ck=period_stats(tr, CK), ck4=period_stats(tr, CK, COST4)["pf"])
            rows.append(r); TR[("ORB", ci, cw, thr)] = tr[["date", "usd", "fi", "xi", "d"]]
        if ci % 50 == 0: print("A1", ci, len(ctrl_grid), flush=True)
    # ---- A2
    B = a2_base(D, F, lo, hi)
    a2grid = {"ABS": [dict(loc=loc, m=m, dcond=dc, k=k, R=R) for loc in ("sess", "orb30") for m in (2.0, 3.0) for dc in ("none", "with", "against") for k in (0.2, 0.35) for R in (0.5, 1.0, 2.0)],
              "DIV": [dict(W=W, mode=md, k=k, R=R) for W in (15, 30) for md in ("fade_div", "fade_all", "follow_conf", "follow_all") for k in (0.2, 0.35) for R in (0.5, 1.0, 2.0)],
              "VFLIP": [dict(thr=t, mode=md, k=k, R=R) for t in (0.05, 0.10) for md in ("delta", "price") for k in (0.2, 0.35) for R in (0.5, 1.0, 2.0)],
              "CLIMAX": [dict(z=z, dir=dr, src=src, k=k, R=R) for z in (3.0, 4.0) for dr in ("fade", "follow") for src in ("delta", "vol") for k in (0.2, 0.35) for R in (0.5, 1.0, 2.0)]}
    for fam, G in a2grid.items():
        for ci, cfg in enumerate(G):
            ev = a2_events(D, B, fam, cfg); tr = run_events(D, ev, flat=FLAT, maxday=2, slip=0.25)
            rows.append(dict(fam=fam, ci=ci, **cfg, ch=period_stats(tr, CH), ck=period_stats(tr, CK), ck4=period_stats(tr, CK, COST4)["pf"]))
            TR[(fam, ci)] = tr[["date", "usd", "fi", "xi", "d"]]
        print("A2", fam, len(G), flush=True)
    R = pd.DataFrame([dict(fam=r["fam"], ci=r["ci"], cw=r.get("cw", ""), thr=r.get("thr", 0.0), ch_n=r["ch"]["n"], ch_wr=r["ch"]["wr"], ch_pf=r["ch"]["pf"], ch_net=r["ch"]["net"],
                            ck_n=r["ck"]["n"], ck_wr=r["ck"]["wr"], ck_pf=r["ck"]["pf"], ck_net=r["ck"]["net"], ck4_pf=r["ck4"],
                            params=repr({kk: v for kk, v in r.items() if kk not in ("fam", "ci", "cw", "thr", "ch", "ck", "ck4")})) for r in rows])
    for col in ("ch_pf", "ck_pf", "ck4_pf", "ch_wr", "ck_wr"): R[col] = pd.to_numeric(R[col])
    # control pairing
    def ctrl_key(r):
        if r.fam == "ORB": return (r.fam, r.ci, "none", 0.0)
        p = eval(r.params)
        if r.fam == "ABS": return ("ABS", repr(dict(p, dcond="none")))
        if r.fam == "DIV": return ("DIV", repr(dict(p, mode="fade_all" if p["mode"] == "fade_div" else "follow_all")))
        if r.fam == "VFLIP": return ("VFLIP", repr(dict(p, mode="price")))
        return ("CLIMAX", repr(dict(p, src="vol")))
    def self_key(r):
        if r.fam == "ORB": return (r.fam, r.ci, r.cw, r.thr)
        return (r.fam, r.params)
    keys = {self_key(r): i for i, r in enumerate(R.itertuples())}
    is_ctrl = []; cidx = []
    for r in R.itertuples():
        ck_ = ctrl_key(r); j = keys.get(ck_); cidx.append(j if j is not None else -1); is_ctrl.append(self_key(r) == ck_)
    R["is_ctrl"] = is_ctrl; R["cidx"] = cidx
    for col in ("ch_pf", "ck_pf", "ch_n", "ck_n"): R["c_" + col] = R[col].to_numpy()[np.array(cidx)].astype(float); R.loc[R.cidx < 0, "c_" + col] = np.nan
    R["beat_ch"] = (R.ch_pf >= R.c_ch_pf + 0.15) & (R.ch_n >= 0.5 * R.c_ch_n); R["beat_ck"] = (R.ck_pf >= R.c_ck_pf + 0.15) & (R.ck_n >= 0.5 * R.c_ck_n)
    s1 = (R.ch_n >= 60) & (R.ch_pf >= 1.3); s2 = s1 & (R.ck_pf >= 1.2); s3 = s2 & (R.ck4_pf >= 1.1); s4 = s3 & R.beat_ch & R.beat_ck & ~R.is_ctrl
    # plateau (numeric one-step neighbours with CHOOSE PF >= 1.15)
    plat = np.full(len(R), np.nan)
    allgrid = {"ORB": [dict(**ctrl_grid[r.ci], cw=r.cw, thr=r.thr) for r in R[R.fam == "ORB"].itertuples()]}
    for fam, G in a2grid.items(): allgrid[fam] = G
    famidx = {fam: R.index[R.fam == fam].to_numpy() for fam in allgrid}; caches = {fam: {} for fam in allgrid}
    for i in R.index[s1 & ~R.is_ctrl]:
        fam = R.fam[i]; G = allgrid[fam]; pos = int(np.where(famidx[fam] == i)[0][0])
        nb = neighbours_of(G[pos], G, ("T", "sk", "R", "thr", "m", "W", "z", "k"), caches[fam])
        if nb: plat[i] = float(np.mean([np.nan_to_num(R.ch_pf.iloc[famidx[fam][j]], nan=0.0) >= 1.15 for j in nb]))
    R["plateau"] = plat; s5 = s4 & (R.plateau >= 0.5).fillna(False)
    R["s1"], R["s2"], R["s3"], R["s4"], R["s5"] = s1, s2, s3, s4, s5
    nc = ~R.is_ctrl
    OUT["counts"] = {fam: dict(cells=int((R.fam == fam).sum()), controls=int(((R.fam == fam) & R.is_ctrl).sum()), s1=int((s1 & (R.fam == fam)).sum()), s2=int((s2 & (R.fam == fam)).sum()),
                               s3=int((s3 & (R.fam == fam)).sum()), s4_beats_control=int((s4 & (R.fam == fam)).sum()), s5_plateau=int((s5 & (R.fam == fam)).sum()),
                               median_pf=dict(choose=round(float(R.ch_pf[R.fam == fam].median()), 3), check=round(float(R.ck_pf[R.fam == fam].median()), 3)),
                               ctrl_median_pf=dict(choose=round(float(R.ch_pf[(R.fam == fam) & R.is_ctrl].median()), 3), check=round(float(R.ck_pf[(R.fam == fam) & R.is_ctrl].median()), 3)))
                     for fam in allgrid}
    ok1 = (R.ch_pf >= 1.3) & (R.ch_n >= 60); ok2 = (R.ck_pf >= 1.2) & (R.ck_n >= 30)
    OUT["base_rates"] = dict(p_check_pass=round(float(ok2.mean()), 4), p_check_pass_given_choose_pass=round(float(ok2[ok1].mean()), 4) if ok1.any() else None, n_choose_pass=int(ok1.sum()),
                             p_beat_check=round(float(R.beat_ck[nc].mean()), 4), p_beat_check_given_beat_choose=round(float(R.beat_ck[nc & R.beat_ch].mean()), 4) if (nc & R.beat_ch).any() else None,
                             n_beat_choose=int((nc & R.beat_ch).sum()), delta_minus_control_pf=dict(choose_median=round(float((R.ch_pf - R.c_ch_pf)[nc].median()), 3), check_median=round(float((R.ck_pf - R.c_ck_pf)[nc].median()), 3),
                             corr_choose_check=round(float(pd.concat([(R.ch_pf - R.c_ch_pf)[nc], (R.ck_pf - R.c_ck_pf)[nc]], axis=1).corr().iloc[0, 1]), 3)))
    # per condition (ORB): how often the delta cell beats its control, median gain
    cond_rows = []
    for (cw, thr), g in R[(R.fam == "ORB") & nc].groupby(["cw", "thr"]):
        cond_rows.append(dict(cond=f"{cw}>={thr}", cells=int(len(g)), kept_choose=round(float((g.ch_n / g.c_ch_n).median()), 2), dpf_choose=round(float((g.ch_pf - g.c_ch_pf).median()), 3),
                              dpf_check=round(float((g.ck_pf - g.c_ck_pf).median()), 3), beat_both=int((g.beat_ch & g.beat_ck).sum()), beat_choose=int(g.beat_ch.sum()), beat_check=int(g.beat_ck.sum())))
    OUT["A1"]["by_condition"] = cond_rows
    OUT["A1"]["best_controls"] = R[(R.fam == "ORB") & R.is_ctrl].sort_values("ch_pf", ascending=False).head(10)[["params", "ch_n", "ch_wr", "ch_pf", "ck_n", "ck_wr", "ck_pf", "ck4_pf"]].to_dict("records")
    cols = ["fam", "params", "cw", "thr", "ch_n", "ch_wr", "ch_pf", "ck_n", "ck_wr", "ck_pf", "ck4_pf", "c_ch_pf", "c_ck_pf", "c_ch_n", "c_ck_n", "plateau", "s2", "s3", "s4", "s5"]
    OUT["A1"]["top_delta_cells"] = R[(R.fam == "ORB") & nc & s1].sort_values(["s5", "s4", "s3", "s2", "ck_pf"], ascending=False).head(25)[cols].to_dict("records")
    for fam in a2grid:
        OUT["A2"][fam] = dict(top=R[(R.fam == fam)].sort_values(["s5", "s4", "s3", "s2", "ch_pf"], ascending=False).head(10)[cols].to_dict("records"))
    OUT["survivors"] = R[s5][cols].to_dict("records")
    # portfolio + bootstrap for survivors (or the 3 best near-survivors: s1 non-control cells ranked by stages then check PF)
    stages = s2.astype(int) + s3.astype(int) + s4.astype(int) + s5.astype(int)
    C = R[s5] if s5.any() else R[s1 & nc].assign(st=stages[s1 & nc]).sort_values(["st", "ck_pf"], ascending=False).head(3)
    OUT["portfolio_set"] = "survivors" if s5.any() else "near_survivors"; prow = []; keep = {}
    for i in C.index:
        r = R.loc[i]
        k_ = (r.fam, int(R.ci[i]), r.cw, r.thr) if r.fam == "ORB" else (r.fam, int(R.ci[i])); tr = TR[k_]; keep[str(k_)] = tr
        ctr = TR[("ORB", int(R.ci[i]), "none", 0.0)] if r.fam == "ORB" else TR[(r.fam, int(R.cidx[i]))] if R.cidx[i] >= 0 else None
        cand = tr.assign(tin=D.sm[tr.fi.to_numpy()], tout=D.sm[tr.xi.to_numpy()] + 1, u=tr.usd)
        pt = port_test(cand, CH, CK)
        bb = block_boot((daily(tr, days) - daily(ctr, days)).to_numpy()) if ctr is not None else None
        prow.append(dict(fam=r.fam, params=r.params, cond=f"{r.cw}>={r.thr}" if r.fam == "ORB" else "", choose=dict(n=int(r.ch_n), wr=r.ch_wr, pf=r.ch_pf), check=dict(n=int(r.ck_n), wr=r.ck_wr, pf=r.ck_pf, pf_4t=r.ck4_pf),
                         control=dict(ch_pf=r.c_ch_pf, ck_pf=r.c_ck_pf), stages=int(stages[i]), portfolio=pt, boot_gain_vs_control=bb))
    OUT["portfolio"] = prow
    R.to_csv(os.path.join(HERE, "delta_orb_cells.csv"), index=False)
    json.dump(OUT, open(os.path.join(HERE, "delta_orb.json"), "w"), indent=1, default=lambda x: None if (isinstance(x, float) and np.isnan(x)) else (x.item() if hasattr(x, "item") else str(x)))
    pickle.dump(keep, open(os.path.join(HERE, "delta_orb_trades.pkl"), "wb"))
    print("cells", len(R), "s1", int(s1.sum()), "s2", int(s2.sum()), "s3", int(s3.sum()), "s4", int(s4.sum()), "s5", int(s5.sum()), flush=True)
    return OUT


def proxy_validation():
    """correlation of the bar-delta proxies with the true aggressor delta on the overlap (per minute and per 15-min sum, all hours / RTH)."""
    from wrq_lib import getD
    D = getD("nqdb.npz"); F, have = true_flow(D); out = {}
    for kind in ("cl", "tr"):
        P = proxy_delta(D, kind); rth = (D.om >= 570) & (D.om < 960)
        for lab, m in (("all", have), ("rth", have & rth)):
            a, b = F.delta[m], P[m]; r1 = float(np.corrcoef(a, b)[0, 1]); sg = float((np.sign(a) == np.sign(b))[(a != 0) & (b != 0)].mean())
            k = len(a) // 15; a15 = a[: k * 15].reshape(k, 15).sum(1); b15 = b[: k * 15].reshape(k, 15).sum(1); r15 = float(np.corrcoef(a15, b15)[0, 1])
            # session cumulative delta ratio correlation (per RTH day): cum since 09:30 at 11:00
            out[f"{kind}_{lab}"] = dict(minutes=int(m.sum()), corr_1m=round(r1, 3), sign_agree_1m=round(sg, 3), corr_15m_sum=round(r15, 3))
        ro = D.ro[(D.ro >= 0)]; ro = ro[have[ro] & (ro + 90 < D.n)]
        ct = np.array([F.delta[r:r + 90].sum() / max(F.vol[r:r + 90].sum(), 1) for r in ro]); cp = np.array([P[r:r + 90].sum() / max(D.v[r:r + 90].sum(), 1) for r in ro])
        out[f"{kind}_cum90_0930"] = dict(days=int(len(ro)), corr=round(float(np.corrcoef(ct, cp)[0, 1]), 3), sign_agree=round(float((np.sign(ct) == np.sign(cp)).mean()), 3))
    json.dump(out, open(os.path.join(HERE, "proxy_validation.json"), "w"), indent=1); print(json.dumps(out, indent=1)); return out


HOUSE_CONDS = [("cum", 0.0), ("cum", 0.01), ("cum", 0.02), ("q5", 0.5), ("q5", 0.75), ("dl15", 0.03), ("q15", 0.75)]


def house_orb():
    """the same delta conditions as a FILTER on the house ORB60 / ORB90 trades of ultra_d4 (features from bars <= fill bar - 1):
    true delta on 2025-05..2026-10 (choose / check as layer A) and the tick-rule proxy on 2020-10..2026-10 (T1 < 2023 / T2 >= 2023).
    Same acceptance: filtered PF >= unfiltered PF + 0.15 in both periods, keeping >= 50% of the trades."""
    from wrq_lib import getD
    from nt_compare import research_set
    D = getD("nqdb.npz"); U, _ = research_set("ultra_d4"); X = U[U["mod"].isin(["ORB60", "ORB90"])].copy()
    code = D.date.astype(np.int64) * 10000 + D.sm; lut = pd.Series(np.arange(D.n), index=code); lut = lut[~lut.index.duplicated()]
    X["fi"] = lut.reindex((X.date * 10000 + X.tin).to_numpy()).to_numpy(); X = X[X.fi.notna()].copy(); X["fi"] = X.fi.astype(int)
    out = {"n_house_trades": int(len(X)), "conds": [f"{c}>={t}" for c, t in HOUSE_CONDS], "rows": []}
    Ft, have = true_flow(D); Fp = proxy_flow(D, "tr")
    for src, F, pers in (("true", Ft, (CH, CK)), ("proxy_tr", Fp, ((20201015, 20230101), (20230101, 20261009)))):
        Y = X[(X.date >= pers[0][0]) & (X.date < pers[1][1])].copy(); k = Y.fi.to_numpy() - 1; d = D.day[k]
        okk = (k - 200 >= 0) & (F.have[k] if src == "true" else True) & (F.have[D.ds[d]] if src == "true" else True); Y = Y[okk]; k = k[okk]; d = d[okk]
        Fe = F.feats(k, Y.d.to_numpy(), D.ds[d], D.ro[d]); u = (Y.u * Y.w).to_numpy()
        for mod in ("ORB60", "ORB90", "both"):
            mm = np.ones(len(Y), bool) if mod == "both" else (Y["mod"] == mod).to_numpy()
            base = {}
            for lab, per in (("p1", pers[0]), ("p2", pers[1])):
                pm = mm & (Y.date >= per[0]).to_numpy() & (Y.date < per[1]).to_numpy(); base[lab] = dict(n=int(pm.sum()), pf=pf(u[pm]), wr=round(100 * float((u[pm] > 0).mean()), 1) if pm.any() else None)
            for cw, thr in HOUSE_CONDS:
                m = cond_mask(Fe, cw, thr); r = dict(src=src, mod=mod, cond=f"{cw}>={thr}", base=base)
                for lab, per in (("p1", pers[0]), ("p2", pers[1])):
                    pm = mm & (Y.date >= per[0]).to_numpy() & (Y.date < per[1]).to_numpy(); km = pm & m; dm = pm & ~m
                    r[lab] = dict(n=int(km.sum()), keep=round(float(km.sum() / max(pm.sum(), 1)), 2), pf=pf(u[km]), wr=round(100 * float((u[km] > 0).mean()), 1) if km.any() else None,
                                  dropped_pf=pf(u[dm]), dropped_net=round(float(u[dm].sum())), dpf=round(float((pf(u[km]) or 0) - (base[lab]["pf"] or 0)), 3))
                r["beats_both"] = bool(r["p1"]["dpf"] >= 0.15 and r["p2"]["dpf"] >= 0.15 and r["p1"]["keep"] >= 0.5 and r["p2"]["keep"] >= 0.5)
                out["rows"].append(r)
    json.dump(out, open(os.path.join(HERE, "delta_house.json"), "w"), indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x))
    for r in out["rows"]:
        print(r["src"], r["mod"], r["cond"], "base", r["base"]["p1"], r["base"]["p2"], "| kept p1", r["p1"]["n"], r["p1"]["keep"], r["p1"]["pf"], "dropped", r["p1"]["dropped_pf"], "| p2", r["p2"]["n"], r["p2"]["keep"], r["p2"]["pf"], "dropped", r["p2"]["dropped_pf"], "BEATS" if r["beats_both"] else "")
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "proxy": proxy_validation()
    elif len(sys.argv) > 1 and sys.argv[1] == "house": house_orb()
    else: layer_a()
