"""2026-10-21 NEW EVENT TYPES on NQ: mega-cap earnings releases (NVDA AAPL MSFT AMZN GOOGL META TSLA AVGO NFLX, all after the close) and
Nasdaq-100 index events (quarterly rebalance / annual reconstitution / quad witching at the close of the third Friday of Mar/Jun/Sep/Dec +
the 2011 and 2023 special rebalances). Date lists: earn_dates_build.py -> research/news_dates_earn_<ticker>.csv, news_dates_ndx_rebal.csv.
Data: real Databento NQ 1-minute 2010-06..2026-10 (nqdb.npz, $2/pt per MNQ, $1.90 + 1 tick per side; stress 4 ticks).
PERIODS (Federico, fixed before looking): choose on T1 = 2019-01..2022-12 (real $ AND cost-normalised 0.345% ATR), check on T2 = 2023-01..2026-10,
A = 2010-06..2018-12 cost-normalised as the regime control. The same cells on ORDINARY days (no earnings, index, CPI, NFP, FOMC) are the control:
an event rule must NOT work there.
VALIDATION of each date list (step 1): next session after the release, |09:29 close - prior RTH close| / ATR vs the median of control days of
the same year (median ratio, share > 1); plus the 16:00-16:59 range of the release day / ATR vs control (the reaction itself). A ticker list is
'validated' when the 2019+ median gap ratio >= 1.25 and the share of next-days above the control median >= 0.60; others are flagged.
PRE-REGISTERED HYPOTHESES (cells enumerated below, nothing added after seeing results):
 (a) GAP   next session, entry 09:30 (signal = 09:29 close): follow (+1) or fade (-1) the overnight move since the 18:00 open (GAP18) or since
           the prior RTH close (GAPC) when |move| >= x ATR (x 0.05/0.1/0.2/0.35), fixed stop k ATR (0.25/0.35/0.5), target R (0.5/1/2),
           hold 30/60/120/240 min, flat 15:55. Sets: union of the 9 tickers' next-days, validated-ticker union, core-6 union (NVDA AAPL MSFT
           AMZN GOOGL META), each ticker, rebalance next-day, cluster weeks, control.
 (a-pre) release day before the close: at 15:00 follow/fade the RTH move 09:30->14:59 >= x ATR (0.1/0.2/0.35), stop 0.2/0.35 ATR, R 0.5/1/2, flat 15:55.
 (b) ORB60 next session (range 09:30-10:29, stop entry, W 120/300 min, stop cap 0.25/0.4 ATR, R 0.5/1/2) filtered WITH the gap, AGAINST the gap,
           ANY, or the standard daily-trend filter (reference).
 (c) FIRST-HOUR REVERSAL: at 10:00 (30-min) or 10:30 (60-min) fade (or follow, reference) the move since the 09:30 open >= x ATR (0.1/0.2/0.35),
           stop 0.25/0.35/0.5 ATR, R 0.5/1/2, hold 60/120/240. Sets: next-days, release days, rebalance days, cluster weeks, control.
 (d) the 2027 default (nt_compare.research_set('ultra_d4'), 2020-10..2026-10) per module on event days vs other days, and the portfolio with
           those days skipped (x0) or boosted (x2): T1 (2020-10..2022) and T2 (2023+) Sharpe, maxDD, worst month, 21-day block bootstrap.
 (e) INDEX REBALANCE day: at 15:30 follow/fade the RTH move 09:30->15:29 (x 0.1/0.2/0.35) or the 15:00->15:29 move (x 0.03/0.05/0.1), stop 0.1/0.2
           ATR, target 0.5/1 R or hold to the 15:59 close; NEXT DAY at 09:30 fade/follow the last-30-minute move of the rebalance day
           (x 0.03/0.05/0.1 ATR, stop 0.25/0.35/0.5, R 0.5/1/2, hold 30/60/120); plus the (a) and (c) cells on rebalance (next-)days.
 (f) EARNINGS CLUSTER WEEK (Mon-Fri week with >= 4 of the 9 reports) as a regime: (d)-style per-module table and skip/boost, and the (a)/(c) cells.
PROTOCOL per cell (fixed): T1 n >= 20, T1 real PF >= 1.3, T1 cost-normalised PF >= 1.2 -> must hold T2 PF >= 1.2, T2 stress (4 ticks) >= 1.1,
event-specific (event PF exceeds the same cell on control days by >= 0.2 in T1 and T2), plateau (>= half of the one-parameter neighbours have
T1 PF >= 1.2 and T2 PF >= 1.0); 'robust' adds A (2010-18 normalised) PF >= 1.0. Base rates: P(T2 ok | T1 ok) vs P(T2 ok) over all event cells.
Two pre-registered single tests: the CPI09 cell (x 0.05, fade, stop 0.35 ATR, 0.5R, hold 60) on GAPC next-days (fade) and its follow version.
Portfolio test (survivors + the two single tests): added to ultra_d4 with wrq_port.conflict_filter; accepted only if Sharpe rises in T1 and T2
and maxDD / worst month do not worsen by more than 5%; 21-day block bootstrap of the Sharpe gain.
Outputs: earn_lab_cells.csv (every cell x set), earn_lab.json, report earn_lab_report.md (by hand). <= 2 processes. Run from research/mine."""
import os, sys, json, numpy as np, pandas as pd
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
from core import Data, run_events, ev_from_lists, S
from families import grid
from families_gold import gen_orb
from cpi_lab import keep_days, st
from news_fade import block_boot, port_metrics
from news import NEWS
from news_hist import CPI_ALL, NFP_ALL
from db_long import FOMC_1019

NORM = 0.00345
PARTS = (("A", 20100601, 20190101, "n"), ("T1", 20190101, 20230101, "r"), ("T2", 20230101, 20991231, "r"))
PPARTS = (("T1", 20200101, 20230101), ("T2", 20230101, 20991231))                   # portfolio periods (ultra_d4 starts 2020-10-15)
TICKERS = ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "NFLX"]
CORE6 = ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META"]
CPI09 = dict(x=0.05, mode=-1, k=0.35, R=0.5, hold=60)
_D = None; _F = None


def getD():
    global _D
    if _D is None: _D = Data("nqdb.npz")
    return _D


def feats(D):
    """Per Globex day: bar indices at ET minutes and the price features of the pre-registered signals."""
    global _F
    if _F is not None: return _F
    nd = D.nd; pos = np.full((nd, 1440), -1, np.int64); pos[D.day[::-1], D.sm[::-1]] = np.arange(D.n)[::-1]
    def bar(om):
        s = S(om); out = np.full(nd, -1, np.int64)
        for k in range(6):
            cand = pos[:, (s + k) % 1440]; out = np.where((out < 0) & (cand >= 0), cand, out)
        return out
    def close_before(e):             # close of the bar before e, same day
        i = e - 1; ok = (e > 0) & (i >= 0) & (D.day[np.maximum(i, 0)] == D.day[np.maximum(e, 0)])
        return np.where(ok, D.c[np.maximum(i, 0)], np.nan), np.where(ok, i, -1)
    F = dict(pos=pos)
    for om in (930, 1000, 1030, 1500, 1530):
        e = bar(om); F[f"e{om}"] = e; F[f"c{om}"], F[f"i{om}"] = close_before(e)      # c930 = 09:29 close, i930 = its bar index
    o18 = np.full(nd, np.nan); ok = D.ds >= 0; o18[ok] = D.o[D.ds[ok]]; o18[ok & (D.sm[np.maximum(D.ds, 0)] > 5)] = np.nan; F["o18"] = o18
    o930 = np.full(nd, np.nan); ok = D.ro >= 0; o930[ok] = D.o[D.ro[ok]]; F["o930"] = o930
    last = np.full(nd, -1, np.int64)                                               # last RTH bar (om < 960)
    for k in range(10):
        cand = pos[:, S(1559 - k) if k < 1 else (S(1559) - k) % 1440]; last = np.where((last < 0) & (cand >= 0), cand, last)
    c1559 = np.where(last >= 0, D.c[np.maximum(last, 0)], np.nan); F["c1559"] = c1559
    A = D.atr
    F["gap18"] = F["c930"] - o18; F["gapc"] = F["c930"] - D.pdc; F["fh30"] = F["c1000"] - o930; F["fh60"] = F["c1030"] - o930
    F["rth1459"] = F["c1500"] - o930; F["rth1529"] = F["c1530"] - o930; F["m1500"] = F["c1530"] - F["c1500"]; last30 = c1559 - F["c1530"]
    prv = np.full(nd, -1, np.int64); p = -1
    for d in range(nd):
        prv[d] = p
        if D.ro[d] >= 0: p = d
    F["prevlast30"] = np.where(prv >= 0, last30[np.maximum(prv, 0)], np.nan)
    # validation features: |gap|/ATR and the 16:00-16:59 range of the day (reaction window of an after-close release)
    with np.errstate(invalid="ignore", divide="ignore"):
        F["gapc_r"] = np.abs(F["gapc"]) / A; F["gap18_r"] = np.abs(F["gap18"]) / A
    pc = (D.om >= 960) & (D.om < 1020)
    hi = pd.Series(np.where(pc, D.h, -np.inf)).groupby(D.day).max(); lo = pd.Series(np.where(pc, D.l, np.inf)).groupby(D.day).min()
    r = np.full(nd, np.nan); r[hi.index] = (hi.values - lo.values); r[~np.isfinite(r)] = np.nan
    with np.errstate(invalid="ignore", divide="ignore"): F["postclose_r"] = r / A
    rh = pd.Series(np.where((D.om >= 570) & (D.om < 960), D.h, -np.inf)).groupby(D.day).max(); rl = pd.Series(np.where((D.om >= 570) & (D.om < 960), D.l, np.inf)).groupby(D.day).min()
    rr = np.full(nd, np.nan); rr[rh.index] = rh.values - rl.values; rr[~np.isfinite(rr)] = np.nan
    with np.errstate(invalid="ignore", divide="ignore"): F["rthrange_r"] = rr / A
    _F = F; return F


def drive_events(D, F, sig, entry, x, mode, k, R, hold):
    mv = F[sig]; A = D.atr; i = F[f"i{entry}"]; rows = []
    for d in np.nonzero((D.ro >= 0) & (A > 0) & np.isfinite(mv) & (i >= 0))[0]:
        if abs(mv[d]) < x * A[d] or mv[d] == 0: continue
        s = (1 if mv[d] > 0 else -1) * mode; px = D.c[i[d]]; risk = k * A[d]
        rows.append([i[d], s, 0, px, px - s * risk, px + s * R * risk, i[d], hold])
    return ev_from_lists(rows)


def orb_events(D, F, W, cap, R, filt):
    ev = gen_orb(D, dict(A=930, T=60, W=W, cap=cap, R=R, tf=1 if filt == "trend" else 0, hold=300))
    if len(ev["i"]) == 0 or filt in ("any", "trend"): return ev
    g = np.sign(F["gapc"][D.day[ev["i"]]]); m = (g * ev["d"] == (1 if filt == "with" else -1))
    return {k: v[m] for k, v in ev.items()}


def cells():
    C = []
    for sig in ("gap18", "gapc"):
        C += [dict(h="a", sig=sig, entry=930, flat=955, **p) for p in grid(x=(0.05, 0.1, 0.2, 0.35), mode=(1, -1), k=(0.25, 0.35, 0.5), R=(0.5, 1.0, 2.0), hold=(30, 60, 120, 240))]
    C += [dict(h="apre", sig="rth1459", entry=1500, flat=955, hold=60, **p) for p in grid(x=(0.1, 0.2, 0.35), mode=(1, -1), k=(0.2, 0.35), R=(0.5, 1.0, 2.0))]
    C += [dict(h="b", sig="orb", **p) for p in grid(W=(120, 300), cap=(0.25, 0.4), R=(0.5, 1.0, 2.0), filt=("with", "against", "any", "trend"))]
    for sig, entry in (("fh30", 1000), ("fh60", 1030)):
        C += [dict(h="c", sig=sig, entry=entry, flat=955, **p) for p in grid(x=(0.1, 0.2, 0.35), mode=(-1, 1), k=(0.25, 0.35, 0.5), R=(0.5, 1.0, 2.0), hold=(60, 120, 240))]
    C += [dict(h="e_drift", sig="rth1529", entry=1530, flat=959, hold=30, **p) for p in grid(x=(0.1, 0.2, 0.35), mode=(1, -1), k=(0.1, 0.2), R=(0.5, 1.0, 99.0))]
    C += [dict(h="e_drift", sig="m1500", entry=1530, flat=959, hold=30, **p) for p in grid(x=(0.03, 0.05, 0.1), mode=(1, -1), k=(0.1, 0.2), R=(0.5, 1.0, 99.0))]
    C += [dict(h="e_next", sig="prevlast30", entry=930, flat=955, **p) for p in grid(x=(0.03, 0.05, 0.1), mode=(-1, 1), k=(0.25, 0.35, 0.5), R=(0.5, 1.0, 2.0), hold=(30, 60, 120))]
    for j, c in enumerate(C): c["j"] = j
    return C


SETS_FOR = {"a": ["next_all", "next_val", "next_core6", "rebal_next", "cluster", "ctrl"] + [f"next_{t}" for t in TICKERS],
            "apre": ["rel_all", "rel_val", "ctrl"] + [f"rel_{t}" for t in TICKERS],
            "b": ["next_all", "next_val", "rebal_next", "ctrl"],
            "c": ["next_all", "next_val", "rel_all", "rebal", "cluster", "ctrl"],
            "e_drift": ["rebal", "rel_all", "ctrl"], "e_next": ["rebal_next", "ctrl"]}


def evaluate(D, ev, days, flat):
    e = keep_days(ev, D, days); row = {}
    r = run_events(D, e, flat=flat, maxday=1, slip=0.25); s = run_events(D, e, flat=flat, maxday=1, slip=1.0)
    nm = run_events(D, e, flat=flat, maxday=1, slip=0.0, norm_cost=NORM)
    for lab, lo, hi, kind in PARTS:
        n, wr, pf, net = st(nm if kind == "n" else r, lo, hi)
        row.update({f"{lab}_n": n, f"{lab}_wr": wr, f"{lab}_pf": pf, f"{lab}_net": net})
        if kind == "r": row[f"{lab}_pf_stress"] = st(s, lo, hi)[2]
    row["T1n_pf"] = st(nm, 20190101, 20230101)[2]
    return row


def cell_events(D, F, c):
    if c["sig"] == "orb": return orb_events(D, F, c["W"], c["cap"], c["R"], c["filt"]), 955
    return drive_events(D, F, c["sig"], c["entry"], c["x"], c["mode"], c["k"], c["R"], c["hold"]), c["flat"]


def run_chunk(args):
    C, sets = args; D = getD(); F = feats(D); rows = []
    for c in C:
        ev, flat = cell_events(D, F, c)
        for sname in SETS_FOR[c["h"]]:
            rows.append(dict(j=c["j"], h=c["h"], sig=c["sig"], set=sname, params=repr({k: v for k, v in c.items() if k not in ("j", "h", "sig", "flat", "entry")}), **evaluate(D, ev, sets[sname], flat)))
    return rows


def passes(C, K):
    """C: event-set rows (index j); K: control rows (index j) of the same cells."""
    C = C.copy(); kt1 = K.T1_pf.reindex(C.index); kt2 = K.T2_pf.reindex(C.index)
    C["ctrl_T1_pf"] = kt1; C["ctrl_T2_pf"] = kt2
    C["t1_ok"] = (C.T1_n >= 20) & (C.T1_pf >= 1.3) & (C.T1n_pf >= 1.2)
    C["t2_ok"] = (C.T2_pf >= 1.2) & (C.T2_pf_stress >= 1.1)
    C["specific"] = ((C.T1_pf - kt1.fillna(9)) >= 0.2) & ((C.T2_pf - kt2.fillna(9)) >= 0.2)
    C["regime_ok"] = C.A_pf >= 1.0
    P = C.params.map(eval); plat = []
    for i, r in C.iterrows():
        p = P[i]; keys = list(p); nb = [jj for jj, q in P.items() if jj != i and sum(q[kk] != p[kk] for kk in keys) == 1]
        plat.append(bool(((C.loc[nb].T1_pf >= 1.2) & (C.loc[nb].T2_pf >= 1.0)).mean() >= 0.5) if nb else False)
    C["plateau"] = plat
    C["survivor"] = C.t1_ok & C.t2_ok & C.specific & C.plateau; C["robust"] = C.survivor & C.regime_ok
    return C


def validation(D, F, sets, ctrl_dates):
    out = {}; dd = pd.Series(D.daydate); yr = dd // 10000
    def ratio(feat, dates, same_day=True):
        v = pd.Series(F[feat]); cm = dd.isin(ctrl_dates) & v.notna()
        base = v[cm].groupby(yr[cm]).median(); m = dd.isin(dates) & v.notna()
        r = (v[m] / yr[m].map(base)).dropna(); r.index = dd[m].to_numpy()[: len(r)] if len(r) == m.sum() else r.index
        rr = r.to_numpy(); d8 = dd[m].to_numpy()
        res = dict(n=int(len(rr)), median_ratio=float(np.median(rr)) if len(rr) else None, share_gt1=float((rr > 1).mean()) if len(rr) else None)
        m19 = d8 >= 20190101
        res["median_ratio_2019plus"] = float(np.median(rr[m19])) if m19.any() else None; res["share_gt1_2019plus"] = float((rr[m19] > 1).mean()) if m19.any() else None
        res["median_ratio_pre2019"] = float(np.median(rr[~m19])) if (~m19).any() else None
        return res
    for t in TICKERS:
        out[t] = dict(n_dates=len(sets[f"rel_{t}"]), gapc=ratio("gapc_r", sets[f"next_{t}"]), gap18=ratio("gap18_r", sets[f"next_{t}"]),
                      postclose=ratio("postclose_r", sets[f"rel_{t}"]), rthrange_next=ratio("rthrange_r", sets[f"next_{t}"]))
        g = out[t]["gapc"]; out[t]["validated"] = bool(g["median_ratio_2019plus"] is not None and g["median_ratio_2019plus"] >= 1.25 and g["share_gt1_2019plus"] >= 0.6)
    out["ALL_next"] = dict(gapc=ratio("gapc_r", sets["next_all"]), postclose=ratio("postclose_r", sets["rel_all"]), rthrange_next=ratio("rthrange_r", sets["next_all"]))
    out["REBAL"] = dict(rthrange=ratio("rthrange_r", sets["rebal"]), gapc_next=ratio("gapc_r", sets["rebal_next"]), rthrange_next=ratio("rthrange_r", sets["rebal_next"]))
    out["CLUSTER"] = dict(rthrange=ratio("rthrange_r", sets["cluster"]), gapc=ratio("gapc_r", sets["cluster"]))
    return out


def build_sets(D):
    alld = np.array(sorted(set(D.daydate[D.ro >= 0]))); allset = set(alld.tolist())
    def nxt(dates):
        return {int(alld[np.searchsorted(alld, d, side="right")]) for d in dates if np.searchsorted(alld, d, side="right") < len(alld)}
    sets = {}; rel = {}
    for t in TICKERS:
        dts = set(pd.read_csv(os.path.join(ROOT, f"news_dates_earn_{t.lower()}.csv")).date.astype(int)) & allset
        rel[t] = dts; sets[f"rel_{t}"] = dts; sets[f"next_{t}"] = nxt(dts)
    sets["rel_all"] = set().union(*rel.values()); sets["next_all"] = nxt(sets["rel_all"])
    sets["rel_core6"] = set().union(*[rel[t] for t in CORE6]); sets["next_core6"] = nxt(sets["rel_core6"])
    rb = pd.read_csv(os.path.join(ROOT, "news_dates_ndx_rebal.csv")); sets["rebal"] = set(rb.date.astype(int)) & allset; sets["rebal_next"] = nxt(sets["rebal"])
    # cluster weeks: Mon-Fri weeks with >= 4 of the 9 reports
    ts = pd.to_datetime(pd.Series(sorted(sets["rel_all"])).astype(str)); wk = ts.dt.to_period("W-SUN")
    cnt = {}
    for t in TICKERS:
        for w in set(pd.to_datetime(pd.Series(sorted(rel[t])).astype(str)).dt.to_period("W-SUN")): cnt[w] = cnt.get(w, 0) + 1
    cw = {w for w, c in cnt.items() if c >= 4}
    aw = pd.to_datetime(pd.Series(alld).astype(str)).dt.to_period("W-SUN")
    sets["cluster"] = set(alld[aw.isin(cw).to_numpy()].tolist()); sets["n_cluster_weeks"] = len(cw)
    macro = set(CPI_ALL) | set(NFP_ALL) | set(NEWS["FOMC"]) | set(FOMC_1019)
    sets["ctrl"] = allset - sets["rel_all"] - sets["next_all"] - sets["rebal"] - sets["rebal_next"] - macro
    return sets, alld


def module_table(X0, flags):
    out = {}
    for fname, dates in flags.items():
        m = X0.date.isin(dates); rows = []
        for mod, g in X0.groupby("mod"):
            r = dict(mod=mod)
            for lab, lo, hi in PPARTS:
                for tag, mm in (("ev", m), ("other", ~m)):
                    u = (g.u * g.w)[mm.loc[g.index] & (g.date >= lo) & (g.date < hi)]
                    n, wr, pf, net = st(pd.DataFrame(dict(usd=u.to_numpy(), date=g.date[u.index].to_numpy())), lo, hi)
                    r[f"{lab}_{tag}_n"] = n; r[f"{lab}_{tag}_wr"] = wr; r[f"{lab}_{tag}_pf"] = pf; r[f"{lab}_{tag}_avg"] = round(float(u.mean()), 1) if len(u) else None
            rows.append(r)
        tot = dict(mod="ALL")
        for lab, lo, hi in PPARTS:
            for tag, mm in (("ev", m), ("other", ~m)):
                u = (X0.u * X0.w)[mm & (X0.date >= lo) & (X0.date < hi)]
                n, wr, pf, net = st(pd.DataFrame(dict(usd=u.to_numpy(), date=X0.date[u.index].to_numpy())), lo, hi)
                tot[f"{lab}_{tag}_n"] = n; tot[f"{lab}_{tag}_wr"] = wr; tot[f"{lab}_{tag}_pf"] = pf; tot[f"{lab}_{tag}_avg"] = round(float(u.mean()), 1) if len(u) else None
        out[fname] = dict(n_days={lab: int(len([d for d in dates if lo <= d < hi])) for lab, lo, hi in PPARTS}, modules=rows + [tot])
    return out


def pmetrics(X, days):
    return port_metrics(X, days)


def skip_boost(X0, flags, days):
    out = {}
    for fname, dates in flags.items():
        for mult in (0.0, 2.0):
            X1 = X0.copy(); X1.loc[X1.date.isin(dates), "w"] = X1.w[X1.date.isin(dates)] * mult; rec = {}
            for lab, lo, hi in PPARTS:
                dd = days[(days >= lo) & (days < hi)]
                m0 = pmetrics(X0[(X0.date >= lo) & (X0.date < hi)], dd); m1 = pmetrics(X1[(X1.date >= lo) & (X1.date < hi)], dd)
                d0 = (X0.u * X0.w).groupby(X0.date).sum().reindex(dd, fill_value=0.0); d1 = (X1.u * X1.w).groupby(X1.date).sum().reindex(dd, fill_value=0.0)
                rec[lab] = dict(base=m0, variant=m1, boot=block_boot(d0, d1, B=500))
            out[f"{fname}_x{int(mult)}"] = rec
    return out


def cell_trades(D, F, c, dates, mod):
    ev, flat = cell_events(D, F, c); df = run_events(D, keep_days(ev, D, dates), flat=flat, maxday=1, slip=0.25)
    if len(df) == 0: return pd.DataFrame(columns=["date", "mod", "tin", "tout", "d", "u", "w"])
    return pd.DataFrame(dict(date=df.date, mod=mod, tin=D.sm[df.fi.to_numpy().astype(int)], tout=D.sm[df.xi.to_numpy().astype(int)] + 1, d=df.d, u=df.usd, w=1.0))


def portfolio(X0, days, adds):
    from wrq_port import conflict_filter
    out = {}
    for name, T in adds.items():
        X1 = pd.concat([X0, T[T.date.isin(days)]], ignore_index=True).sort_values(["date", "tin"], kind="stable").reset_index(drop=True); X1 = conflict_filter(X1); rec = {}
        for lab, lo, hi in PPARTS:
            dd = days[(days >= lo) & (days < hi)]
            m0 = pmetrics(X0[(X0.date >= lo) & (X0.date < hi)], dd); m1 = pmetrics(X1[(X1.date >= lo) & (X1.date < hi)], dd)
            d0 = (X0.u * X0.w).groupby(X0.date).sum().reindex(dd, fill_value=0.0); d1 = (X1.u * X1.w).groupby(X1.date).sum().reindex(dd, fill_value=0.0)
            rec[lab] = dict(without=m0, with_=m1, added_kept=int((X1["mod"] == name).sum()), boot=block_boot(d0, d1))
        ok = all(rec[l]["with_"]["sharpe"] > rec[l]["without"]["sharpe"] and rec[l]["with_"]["maxdd"] <= 1.05 * rec[l]["without"]["maxdd"]
                 and rec[l]["with_"]["worst_month"] >= 1.05 * rec[l]["without"]["worst_month"] for l in ("T1", "T2"))
        rec["accepted"] = bool(ok); out[name] = rec
    return out


if __name__ == "__main__":
    D = getD(); F = feats(D); sets, alld = build_sets(D)
    print({k: (len(v) if isinstance(v, set) else v) for k, v in sets.items()}, flush=True)
    val = validation(D, F, sets, sets["ctrl"])
    for t in TICKERS:
        g = val[t]["gapc"]; p = val[t]["postclose"]
        print(f"valid {t:5s} n {val[t]['n_dates']:3d} gapc ratio all/pre19/2019+ {g['median_ratio']:.2f}/{g['median_ratio_pre2019'] or 0:.2f}/{g['median_ratio_2019plus']:.2f} share>1 {g['share_gt1_2019plus']:.2f} | post-close range ratio {p['median_ratio']:.2f} (2019+ {p['median_ratio_2019plus']:.2f}) | validated {val[t]['validated']}", flush=True)
    validated = [t for t in TICKERS if val[t]["validated"]]
    sets["next_val"] = set().union(*[sets[f"next_{t}"] for t in validated]) if validated else set(); sets["rel_val"] = set().union(*[sets[f"rel_{t}"] for t in validated]) if validated else set()
    print("validated:", validated, "next_val", len(sets["next_val"]), flush=True)
    C = cells(); print("cells", len(C), flush=True)
    chunks = [C[0::2], C[1::2]]
    with Pool(2) as pool: res = pool.map(run_chunk, [(ch, {k: v for k, v in sets.items() if isinstance(v, set)}) for ch in chunks])
    R = pd.DataFrame([r for rr in res for r in rr]); R.to_csv(os.path.join(HERE, "earn_lab_cells.csv"), index=False)
    # protocol per hypothesis x set
    summary = {}; allC = []
    for h in sorted(set(R.h)):
        K = R[(R.h == h) & (R.set == "ctrl")].set_index("j")
        for sname in [s for s in SETS_FOR[h] if s != "ctrl"]:
            Cs = R[(R.h == h) & (R.set == sname)].set_index("j")
            if not len(Cs): continue
            P = passes(Cs, K); P["h"] = h; P["set"] = sname; allC.append(P)
            sel = P[P.t1_ok]; surv = P[P.survivor]
            summary[f"{h}|{sname}"] = dict(n_cells=int(len(P)), n_days={lab: int(len([d for d in sets[sname] if lo <= d < hi])) for lab, lo, hi, _ in PARTS},
                                         median_pf={lab: float(P[f"{lab}_pf"].median()) for lab, *_ in PARTS}, median_pf_ctrl={lab: float(K[f"{lab}_pf"].median()) for lab, *_ in PARTS},
                                         median_wr={lab: float(P[f"{lab}_wr"].median()) for lab, *_ in PARTS},
                                         t1_pass=int(len(sel)), base_rate_t2=float(P.t2_ok.mean()), t2_given_t1=float(sel.t2_ok.mean()) if len(sel) else None,
                                         survivors=int(len(surv)), robust=int(P.robust.sum()),
                                         best_t1=P.sort_values("T1_pf", ascending=False).head(3)[["params", "T1_n", "T1_wr", "T1_pf", "T1n_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf_stress", "A_pf", "ctrl_T1_pf", "ctrl_T2_pf", "plateau"]].to_dict("records"),
                                         survivor_rows=surv[["params", "A_n", "A_pf", "T1_n", "T1_wr", "T1_pf", "T1n_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf_stress", "ctrl_T1_pf", "ctrl_T2_pf", "regime_ok"]].to_dict("records"))
            s = summary[f"{h}|{sname}"]
            print(f"{h:7s} {sname:11s} cells {s['n_cells']:3d} days T1/T2 {s['n_days']['T1']}/{s['n_days']['T2']} medPF A/T1/T2 {s['median_pf']['A']:.2f}/{s['median_pf']['T1']:.2f}/{s['median_pf']['T2']:.2f} ctrl {s['median_pf_ctrl']['T1']:.2f}/{s['median_pf_ctrl']['T2']:.2f} T1 pass {s['t1_pass']} P(T2|T1) {s['t2_given_t1']} base {s['base_rate_t2']:.2f} surv {s['survivors']} robust {s['robust']}", flush=True)
    ALL = pd.concat(allC); ALL.to_csv(os.path.join(HERE, "earn_lab_protocol.csv"))
    ev_rows = ALL[~ALL.set.str.startswith(("next_", "rel_")) | ALL.set.isin(["next_all", "rel_all", "next_val", "rel_val", "next_core6"])]
    base = dict(n_cells=int(len(ALL)), t1_pass=int(ALL.t1_ok.sum()), p_t2=float(ALL.t2_ok.mean()), p_t2_given_t1=float(ALL[ALL.t1_ok].t2_ok.mean()) if ALL.t1_ok.any() else None,
                survivors=int(ALL.survivor.sum()), robust=int(ALL.robust.sum()),
                pooled_sets=dict(n_cells=int(len(ev_rows)), t1_pass=int(ev_rows.t1_ok.sum()), p_t2=float(ev_rows.t2_ok.mean()), p_t2_given_t1=float(ev_rows[ev_rows.t1_ok].t2_ok.mean()) if ev_rows.t1_ok.any() else None, survivors=int(ev_rows.survivor.sum()), robust=int(ev_rows.robust.sum())))
    print("base rates", base, flush=True)
    # two pre-registered single tests (CPI09 cell transplanted to the earnings gap)
    single = {}
    for name, mode in (("GAPC_fade_cpi09", -1), ("GAPC_follow_cpi09", 1)):
        c = dict(h="a", sig="gapc", entry=930, flat=955, x=0.05, mode=mode, k=0.35, R=0.5, hold=60, j=-1)
        ev, flat = cell_events(D, F, c); single[name] = {s: evaluate(D, ev, sets[s], flat) for s in ("next_all", "next_val", "next_core6", "rebal_next", "ctrl")}
        for s, v in single[name].items(): print(f"single {name} {s:10s} n A/T1/T2 {v['A_n']}/{v['T1_n']}/{v['T2_n']} PF {v['A_pf']}/{v['T1_pf']}/{v['T2_pf']} stress {v['T2_pf_stress']} WR {v['T1_wr']}/{v['T2_wr']}", flush=True)
    # (d)/(f): the 2027 default on event days
    from nt_compare import research_set
    X0, _ = research_set("ultra_d4")
    fomc = set(NEWS["FOMC"]) | set(FOMC_1019)
    days = alld[(alld >= X0.date.min()) & (alld <= X0.date.max()) & ~np.isin(alld, list(fomc))]
    flags = {k: sets[k] for k in ("next_all", "rel_all", "next_core6", "rebal", "rebal_next", "cluster")}
    if validated: flags["next_val"] = sets["next_val"]
    mt = module_table(X0, flags); sb = skip_boost(X0, flags, days)
    for k, v in sb.items():
        print(f"skip/boost {k:16s} T1 Sharpe {v['T1']['base']['sharpe']:.2f}->{v['T1']['variant']['sharpe']:.2f} $/mo {v['T1']['base']['usd_mo']:.0f}->{v['T1']['variant']['usd_mo']:.0f} | T2 {v['T2']['base']['sharpe']:.2f}->{v['T2']['variant']['sharpe']:.2f} $/mo {v['T2']['base']['usd_mo']:.0f}->{v['T2']['variant']['usd_mo']:.0f} P(gain) {v['T1']['boot']['p_gain']:.2f}/{v['T2']['boot']['p_gain']:.2f}", flush=True)
    for fname in flags:
        tot = mt[fname]["modules"][-1]
        print(f"default on {fname:10s}: T1 ev n {tot['T1_ev_n']} WR {tot['T1_ev_wr']} PF {tot['T1_ev_pf']} avg {tot['T1_ev_avg']} | other PF {tot['T1_other_pf']} avg {tot['T1_other_avg']} || T2 ev n {tot['T2_ev_n']} WR {tot['T2_ev_wr']} PF {tot['T2_ev_pf']} avg {tot['T2_ev_avg']} | other PF {tot['T2_other_pf']} avg {tot['T2_other_avg']}", flush=True)
    # portfolio test: survivors (pooled sets only) + the two single tests
    adds = {}; cmap = {c["j"]: c for c in C}
    surv_rows = ev_rows[ev_rows.survivor]
    for (j, sname), r in surv_rows.groupby([surv_rows.index, "set"]).first().iterrows():
        adds[f"E{j}_{sname}"] = cell_trades(D, F, cmap[j], sets[sname], f"E{j}_{sname}")
    for name, mode in (("GAPC_fade_cpi09", -1), ("GAPC_follow_cpi09", 1)):
        adds[name] = cell_trades(D, F, dict(h="a", sig="gapc", entry=930, flat=955, x=0.05, mode=mode, k=0.35, R=0.5, hold=60, j=-1), sets["next_all"], name)
    port = portfolio(X0, days, adds)
    for k, v in port.items():
        print(f"portfolio +{k:22s} T1 Sharpe {v['T1']['without']['sharpe']:.2f}->{v['T1']['with_']['sharpe']:.2f} DD {v['T1']['without']['maxdd']:.0f}->{v['T1']['with_']['maxdd']:.0f} | T2 {v['T2']['without']['sharpe']:.2f}->{v['T2']['with_']['sharpe']:.2f} DD {v['T2']['without']['maxdd']:.0f}->{v['T2']['with_']['maxdd']:.0f} boot p50 {v['T1']['boot']['p50']:.2f}/{v['T2']['boot']['p50']:.2f} accepted {v['accepted']}", flush=True)
    out = dict(sets={k: (len(v) if isinstance(v, set) else v) for k, v in sets.items()}, validation=val, validated=validated, n_cells=len(C), summary=summary, base_rates=base,
               single=single, module_table=mt, skip_boost=sb, portfolio=port, cells_examined=int(len(R)))
    json.dump(out, open(os.path.join(HERE, "earn_lab.json"), "w"), indent=1, default=str)
    print("done", flush=True)
