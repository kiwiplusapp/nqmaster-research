"""fill_gap.py (2026-10-26, experiment 01 / frente 5A, docs/PLAN_2026-10-26.md H1-H3).
Compares two NinjaTrader Strategy Analyzer trade exports of the SAME strategy, settings and period that differ only in the fill
model (A = FillSeries Off, Standard 1-minute OHLC fills; B = FillSeries Tick1 / Second1, intrabar fills) trade by trade, and
optionally both against the research trade list (nt_compare.research_set). Per module x order type x ET time band:
  n matched, only in A, only in B, entry fill difference in ticks (B - A, signed, + = worse for the trade), exit fill difference,
  $ per trade difference (B - A) with a 95% CI, share of trades whose outcome flips (winner <-> loser), $ totals on the matched
  trades, a crosstab of exit kinds (stop / target / time), and fills outside the 1-minute bar that contains them (impossible fills,
  checked against research/data/<bars>.npz when it is there).
Usage (from research/mine):
  python3 fill_gap.py <A_standard.csv> <B_tick.csv> [--tz America/Argentina/Buenos_Aires] [--tol 3] [--research ultra_d4]
                      [--bars mnq_fut.npz] [--out fill_gap_<tag>]
Self-test: A = B must give 100% matched and every difference 0 (python3 fill_gap.py x.csv x.csv --out /tmp/selftest).
Writes <out>.md, <out>_pairs.csv (matched pairs with the deltas) and <out>_unmatched.csv."""
import os, sys, argparse, datetime, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from nt_trades import load_nt

TICK = 0.25
STOP_MODS = {"ORB60", "ORB90", "VOLB", "ENG10"}          # stop-market entries (ORB enters at market when the close is already through)
LIMIT_MODS = {"LON", "ICT"}                               # limit entries
BANDS = [(0, 570, "noche <09:30"), (570, 630, "09:30-10:30"), (630, 720, "10:30-12:00"), (720, 840, "12:00-14:00"), (840, 1080, "14:00-18:00"), (1080, 1441, "noche >=18:00")]


def otype(mod): return "stop" if mod in STOP_MODS else ("limit" if mod in LIMIT_MODS else "market")
def band(minute_of_day):
    for lo, hi, name in BANDS:
        if lo <= minute_of_day < hi: return name
    return "?"
def xkind(name):
    n = str(name).lower()
    return "stop" if n.startswith("stop") else ("target" if n.startswith(("profit", "target")) else "time/flat")   # 'Stop loss' / 'StopX', 'Profit target' / 'TargetX'


def bar_open(ts, tick_stamped=None):
    """ET timestamp of a fill -> open time of the 1-minute bar it belongs to. A 1-minute-series fill is stamped with the bar CLOSE
    (minus one minute). A fill on a tick / second series is stamped with the tick time: floor to the minute, ALSO when the seconds are
    :00 (a market order sent at the bar close fills on the first tick of the next minute, stamped HH:MM:00 = that bar's open). Whether
    an export is tick-stamped is decided per export (tick_stamped), by default when > 20% of its fills carry seconds."""
    if tick_stamped is None: tick_stamped = (ts.dt.second > 0).mean() > 0.2
    if tick_stamped: return ts.dt.floor("min")
    return ts - pd.Timedelta(minutes=1)


def frame(path, tz, tag, tick_stamped=None, slip_ticks=0, slip_scope="all"):
    """slip_ticks: synthetic slippage added to this export's fills (+ = adverse) on market / stop-market entries and, with slip_scope
    'all', on stop-loss and time / flat exits: NinjaTrader's Slippage setting is not applied to fills on a secondary (tick) series
    (measured 2026-10-26: Tick1 entries exactly 1 tick better than Standard), so the Tick1 export gets the 1 tick Standard charges."""
    t = load_nt(path)
    if "Strategy" in t.columns and (t["Strategy"].str.strip() != "NQMaster").any():
        n0 = len(t); t = t[t["Strategy"].str.strip() == "NQMaster"]; print(f"{tag}: {n0 - len(t)} rows of other strategies dropped")
    et = lambda s: s.dt.tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("America/New_York").dt.tz_localize(None)
    tin_et, tout_et = et(t.tin), et(t.tout)
    ts_flag = tick_stamped if tick_stamped is not None else bool(((tin_et.dt.second > 0) | (tout_et.dt.second > 0)).mean() > 0.2)
    op = bar_open(tin_et, ts_flag); xo = bar_open(tout_et, ts_flag)
    print(f"{tag}: {len(t)} trades, fill stamps read as {'tick time' if ts_flag else 'bar close'}" + (f", synthetic slippage {slip_ticks} tick(s) on {slip_scope}" if slip_ticks else ""))
    mods = t["mod"].str.strip(); d = t["d"].values.astype(float); epx = t.epx.values.astype(float); xpx = t.xpx.values.astype(float); u = (t.pnl / t.qty).values.astype(float)
    if slip_ticks:
        ent = mods.map(lambda m: otype(m) != "limit").values
        epx = epx + np.where(ent, d * slip_ticks * TICK, 0.0); u = u - np.where(ent, slip_ticks * TICK * 2.0, 0.0)          # MNQ $2 per point
        if slip_scope == "all":
            ex = t.xname.map(lambda n: xkind(n) != "target").values
            xpx = xpx - np.where(ex, d * slip_ticks * TICK, 0.0); u = u - np.where(ex, slip_ticks * TICK * 2.0, 0.0)
    f = pd.DataFrame(dict(date=((op + pd.Timedelta(hours=6)).dt.normalize().dt.strftime("%Y%m%d").astype(int)),
                          mod=mods.values, d=t["d"].values, qty=t.qty.values, u=u, pnl=t.pnl.values,
                          epx=epx, xpx=xpx, xname=t.xname.values, bars=t.bars.values,
                          tin=((op.dt.hour * 60 + op.dt.minute - 1080) % 1440).astype(int), tout=((xo.dt.hour * 60 + xo.dt.minute - 1080) % 1440).astype(int),
                          mod_et=(op.dt.hour * 60 + op.dt.minute).astype(int), tin_ts=tin_et.values, tout_ts=tout_et.values))
    f["otype"] = f["mod"].map(otype); f["band"] = f["mod_et"].map(band); f["xkind"] = f["xname"].map(xkind)
    f["hold"] = (f.tout - f.tin) % 1440
    return f.sort_values(["date", "tin"]).reset_index(drop=True)


def match(A, B, tol):
    """Greedy nearest-entry-minute pairing inside (date, module, direction). Returns A, B with column k (partner index, -1 = none)."""
    A = A.copy(); B = B.copy(); A["k"] = -1; B["k"] = -1
    for (dt, md, d), g in A.groupby(["date", "mod", "d"]):
        cand = B[(B.date == dt) & (B["mod"] == md) & (B.d == d)]
        if not len(cand): continue
        tl = 300 if md == "LON" else tol
        for i, r in g.iterrows():
            c = cand[(B.loc[cand.index, "k"] < 0) & ((cand.tin - r.tin).abs() <= tl)]
            if len(c):
                j = (c.tin - r.tin).abs().idxmin(); A.at[i, "k"] = j; B.at[j, "k"] = i
    return A, B


def pairs(A, B):
    m = A[A.k >= 0]; b = B.loc[m.k.values]
    P = pd.DataFrame(dict(date=m.date.values, mod=m["mod"].values, d=m.d.values, otype=m.otype.values, band=m.band.values,
                          tin_a=m.tin.values, tin_b=b.tin.values, epx_a=m.epx.values, epx_b=b.epx.values, xpx_a=m.xpx.values, xpx_b=b.xpx.values,
                          xkind_a=m.xkind.values, xkind_b=b.xkind.values, hold_a=m.hold.values, hold_b=b.hold.values, u_a=m.u.values, u_b=b.u.values, qty_a=m.qty.values, qty_b=b.qty.values))
    P["d_entry_ticks"] = ((P.epx_b - P.epx_a) * P.d / TICK).round(2)        # + = B entered worse
    P["d_exit_ticks"] = ((P.xpx_a - P.xpx_b) * P.d / TICK).round(2)         # + = B exited worse
    P["d_usd"] = (P.u_b - P.u_a).round(2)
    P["flip"] = np.sign(P.u_a) != np.sign(P.u_b)
    P["d_tin"] = ((P.tin_b - P.tin_a + 720) % 1440) - 720
    P["d_hold"] = P.hold_b - P.hold_a
    return P


def ci95(x):
    x = np.asarray(x, float); n = len(x)
    if n < 2: return (np.nan, np.nan)
    se = x.std(ddof=1) / np.sqrt(n); return (x.mean() - 1.96 * se, x.mean() + 1.96 * se)


def summary(P, keys):
    rows = []
    for key, g in (P.groupby(keys) if keys else [((), P)]):
        key = key if isinstance(key, tuple) else (key,)
        lo, hi = ci95(g.d_usd)
        rows.append(dict(**{k: v for k, v in zip(keys, key)}, n=len(g), d_entry_ticks=round(g.d_entry_ticks.mean(), 2), d_entry_med=round(g.d_entry_ticks.median(), 2),
                         d_exit_ticks=round(g.d_exit_ticks.mean(), 2), d_usd=round(g.d_usd.mean(), 2), ci_lo=round(lo, 2), ci_hi=round(hi, 2),
                         flips_pct=round(100 * g.flip.mean(), 1), usd_a=round(g.u_a.sum()), usd_b=round(g.u_b.sum()), d_usd_total=round(g.d_usd.sum()),
                         d_tin_mean=round(g.d_tin.mean(), 2), d_hold_mean=round(g.d_hold.mean(), 2)))
    return pd.DataFrame(rows)


def impossible_fills(F, bars_name, tag):
    """Fills outside [low - 1 tick, high + 1 tick] of the 1-minute bar they belong to (bar = trade date + session minute). A fill more
    than 10 points (40 ticks) outside that range is a price-level mismatch between the NT feed and the research data (seen on
    2025-07-15 and 2025-08-19 with mnq_fut.npz, 135-350 points), counted apart as feed_offset, not as an impossible fill."""
    p = os.path.join(os.path.dirname(HERE), "data", bars_name)
    if not os.path.exists(p): return None, f"{bars_name} not found: impossible-fill check skipped"
    z = np.load(p); date = z["date"].astype(np.int64); sm = (z["om"].astype(np.int64) - 1080) % 1440
    key = date * 1440 + sm; order = np.argsort(key, kind="stable"); ks = key[order]
    h = z["h"][order]; l = z["l"][order]
    def look(dates, mins):
        q = dates.astype(np.int64) * 1440 + mins.astype(np.int64); i = np.searchsorted(ks, q)
        ok = (i < len(ks)) & (ks[np.minimum(i, len(ks) - 1)] == q); return i, ok
    out = []
    for col, mcol, what in (("epx", "tin", "entry"), ("xpx", "tout", "exit")):
        i, ok = look(F.date.values, F[mcol].values)
        px = F[col].values
        j = np.minimum(i, len(ks) - 1)
        dist = np.maximum(np.maximum(l[j] - px, px - h[j]), 0.0)               # points outside the bar's range (0 = inside)
        off = ok & (dist > 10.0)                                                # >= 40 ticks outside: the two feeds are not on the same price level
        bad = ok & ~off & (dist > TICK + 1e-9)                                  # 1 tick of slippage beyond the range is allowed
        out.append(dict(side=tag, what=what, checked=int(ok.sum()), no_bar=int((~ok).sum()), feed_offset=int(off.sum()), outside=int(bad.sum())))
        F.loc[bad, f"bad_{what}"] = True
    return pd.DataFrame(out), None


def series_check(F, tag):
    """Which series filled the orders (review 2026-10-26): a fill on the tick / second series is stamped with the tick time (seconds != 0),
    a fill on the 1-minute series with the bar close (seconds == 0). In a Tick1 run every kind should be ~100% 'seconds != 0'; stops /
    targets at 0% mean the Set* orders stayed on the 1-minute series (plan B of the patch). Also counts exits NinjaTrader made on its own
    (session close) and exits at/after 15:58 ET, which would mean the whole-position exit on the fill series was ignored."""
    rows = []
    for what, ts, grp in (("entry", F.tin_ts, F.otype), ("exit", F.tout_ts, F.xkind)):
        sec = pd.Series(pd.DatetimeIndex(ts).second != 0, index=F.index)
        for g, m in grp.groupby(grp):
            rows.append(dict(side=tag, what=what, kind=g, n=int(len(m)), seconds_nonzero_pct=round(100 * float(sec[m.index].mean()), 1)))
    T = pd.DataFrame(rows)
    xt = pd.DatetimeIndex(F.tout_ts); mins = xt.hour * 60 + xt.minute                  # the 15:56 flatten fills on the next bar, stamped 15:57:00
    late = int(((mins >= 15 * 60 + 58) & (mins < 18 * 60)).sum())
    own = int(F.xname.str.lower().str.contains("session|exit on", regex=True).sum())
    return T, f"{tag}: exits at/after 15:58 ET {late} (flatten fills are stamped 15:57:00), exits named by NinjaTrader itself (session close) {own}"


def research_gap(F, set_name, tol, tag):
    """$ per trade NT vs research on matched trades, per module (H3): + = NT better than research."""
    from nt_compare import research_set, match as rmatch
    from parity_check import TOL_MOD
    R, _ = research_set(set_name)
    lo, hi = max(R.date.min(), F.date.min()), min(R.date.max(), F.date.max())
    R = R[(R.date >= lo) & (R.date <= hi)].drop_duplicates(["date", "mod", "tin", "d"]).reset_index(drop=True); N = F[(F.date >= lo) & (F.date <= hi)].reset_index(drop=True)
    rows = []
    for md in sorted(set(R["mod"]) | set(N["mod"])):
        r = R[R["mod"] == md].reset_index(drop=True); n = N[N["mod"] == md].reset_index(drop=True)
        if not len(r) or not len(n): rows.append(dict(side=tag, module=md, research=len(r), nt=len(n), matched=0)); continue
        r, n = rmatch(r, n, TOL_MOD.get(md, tol)); m = r[r.k >= 0]
        g = n.loc[m.k.values, "u"].to_numpy() - m.u.to_numpy() if len(m) else np.array([])
        se = g.std(ddof=1) / np.sqrt(len(g)) if len(g) > 1 else np.nan
        rows.append(dict(side=tag, module=md, research=len(r), nt=len(n), matched=len(m), pct=round(100 * len(m) / len(r), 1),
                         nt_minus_research_usd=round(float(g.mean()), 2) if len(g) else np.nan, t=round(float(g.mean() / se), 2) if len(g) > 1 and se > 0 else np.nan,
                         research_usd=round(float(m.u.sum())), nt_usd=round(float(n.loc[m.k.values, "u"].sum())) if len(m) else 0))
    return pd.DataFrame(rows), lo, hi


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--tz", default="America/Argentina/Buenos_Aires"); ap.add_argument("--tol", type=int, default=3)
    ap.add_argument("--research", default=None, help="research set for the H3 table (e.g. ultra_d4); off by default")
    ap.add_argument("--bars", default="mnq_fut.npz", help="1-minute bars in research/data for the impossible-fill check")
    ap.add_argument("--out", default=None); ap.add_argument("--label-a", default="A (Standard)"); ap.add_argument("--label-b", default="B (Tick1)")
    ap.add_argument("--slip-b", type=int, default=0, help="synthetic slippage (ticks) added to B's market / stop fills; NinjaTrader does not apply Slippage on a tick series")
    ap.add_argument("--slip-b-scope", default="all", choices=["all", "entries"], help="'entries' when B's stop / target exits are still on the 1-minute series (they already carry the slippage)")
    ap.add_argument("--stamps-b", default="auto", choices=["auto", "tick", "close"], help="how B's fill timestamps are read (auto = tick time when > 20%% carry seconds)")
    ap.add_argument("--exclude-dates", default="", help="comma list of trade dates (yyyymmdd) left out of both sides, e.g. days with TICK GAP minutes in the Tick1 run")
    a = ap.parse_args(); out = a.out or os.path.join(HERE, f"fill_gap_{datetime.date.today():%Y%m%d}")
    A = frame(a.a, a.tz, "A"); B = frame(a.b, a.tz, "B", None if a.stamps_b == "auto" else a.stamps_b == "tick", a.slip_b, a.slip_b_scope)
    lo, hi = max(A.date.min(), B.date.min()), min(A.date.max(), B.date.max())
    A = A[(A.date >= lo) & (A.date <= hi)].reset_index(drop=True); B = B[(B.date >= lo) & (B.date <= hi)].reset_index(drop=True)
    excl = [int(x) for x in a.exclude_dates.split(",") if x.strip()]
    if excl:
        nA, nB = int(A.date.isin(excl).sum()), int(B.date.isin(excl).sum())
        A = A[~A.date.isin(excl)].reset_index(drop=True); B = B[~B.date.isin(excl)].reset_index(drop=True); print(f"excluded dates {excl}: {nA} trades of A, {nB} of B")
    A, B = match(A, B, a.tol); P = pairs(A, B)
    pd.set_option("display.width", 250)
    L = [f"# Fill gap: {a.label_a} vs {a.label_b} ({lo}-{hi})" + (f" | B + {a.slip_b} tick(s) synthetic slippage on {a.slip_b_scope}" if a.slip_b else ""), ""]
    tot = summary(P, []).iloc[0] if len(P) else None
    if tot is None: L.append("- No matched trades."); print("\n".join(L)); sys.exit(1)
    pct_a = 100 * (A.k >= 0).mean(); pct_b = 100 * (B.k >= 0).mean()
    rel = 100 * tot.d_usd_total / tot.usd_a if tot.usd_a else np.nan
    L.append(f"- Trades: A {len(A)}, B {len(B)}, matched {len(P)} ({pct_a:.1f}% of A, {pct_b:.1f}% of B); tolerance {a.tol} min inside (date, module, direction)." + (f" Dates excluded: {excl}." if excl else ""))
    L.append(f"- $ per contract on the matched trades: A {tot.usd_a:,.0f}, B {tot.usd_b:,.0f}, B - A {tot.d_usd_total:+,.0f} ({rel:+.1f}% of A); "
             f"per trade {tot.d_usd:+.2f} (95% CI {tot.ci_lo:+.2f} .. {tot.ci_hi:+.2f}); outcome flips {tot.flips_pct:.1f}%.")
    L.append(f"- Entry fill B - A: mean {tot.d_entry_ticks:+.2f} ticks (median {tot.d_entry_med:+.2f}); exit fill B - A: mean {tot.d_exit_ticks:+.2f} ticks; "
             f"entry minute B - A {tot.d_tin_mean:+.2f}, hold B - A {tot.d_hold_mean:+.2f} min. (+ = worse for the trade in B).")
    L.append(f"- Unmatched $: only A {A[A.k < 0].u.sum():,.0f} ({int((A.k < 0).sum())} trades), only B {B[B.k < 0].u.sum():,.0f} ({int((B.k < 0).sum())} trades).")
    L += ["", "## Slippage: how it is counted (once)",
          "- A (Standard, 1-minute fills): NinjaTrader's Slippage = 1 tick is inside the export: market and stop-market entries +1 tick, stop-loss and market exits -1 tick, limit fills 0.",
          f"- B (fills on the tick series): NinjaTrader applies no slippage on a secondary series (measured 2026-10-26), so this report adds {a.slip_b} tick(s) to B's market / stop-market fills" + (" (entries only: B's stop / target exits are still 1-minute fills that already carry it)" if a.slip_b_scope == "entries" else " on entries, stop-loss exits and market exits") + ", 0 on limit fills. B - A is therefore the price path alone (H1 / H2), with the same 1-tick assumption on both sides." if a.slip_b else
          "- B: NO synthetic slippage added (--slip-b 0): if B is a tick-series run, its market / stop fills are 1 tick better than Standard by construction and B - A overstates B.",
          "- Real slippage (H5, slip_model.py) is measured against the order level in live / sim exports and replaces the 1-tick assumption only per cell with n >= 15; it is never added on top of this table."]
    L += ["", "## By order type", "```", summary(P, ["otype"]).to_string(index=False), "```", "", "## By module", "```", summary(P, ["mod"]).to_string(index=False), "```",
          "", "## By order type and ET band (entry bar)", "```", summary(P, ["otype", "band"]).to_string(index=False), "```",
          "", "## Exit kind A (rows) vs B (columns)", "```", pd.crosstab(P.xkind_a, P.xkind_b).to_string(), "```"]
    chk = []
    for F, tag in ((A, "A"), (B, "B")):
        t, msg = impossible_fills(F, a.bars, tag)
        if t is None: chk.append(msg)
        else: chk.append(t.to_string(index=False))
    L += ["", f"## Fills outside the 1-minute bar (+/- 1 tick), bars = research/data/{a.bars}", "```"] + chk + ["```"]
    sc = []
    for F, tag in ((A, "A"), (B, "B")):
        T, line = series_check(F, tag); sc += [T.to_string(index=False), line]
    L += ["", "## Which series filled the orders (seconds != 0 = tick / second series; a Tick1 run needs ~100% in every kind, stops and targets included)", "```"] + sc + ["```"]
    if a.research:
        parts = []
        for F, tag in ((A, a.label_a), (B, a.label_b)):
            G, rlo, rhi = research_gap(F, a.research, a.tol, tag); parts.append(G)
        G = pd.concat(parts, ignore_index=True)
        L += ["", f"## NT vs research ({a.research}, {rlo}-{rhi}): $ per trade NT - research on matched trades (H3; + = NT better)", "```", G.to_string(index=False), "```"]
    txt = "\n".join(L) + "\n"
    open(out + ".md", "w", encoding="utf-8").write(txt); P.to_csv(out + "_pairs.csv", index=False)
    um = pd.concat([A[A.k < 0].assign(side="only A"), B[B.k < 0].assign(side="only B")])[["side", "date", "mod", "d", "tin", "epx", "xpx", "xname", "u"]]
    um["hora_ET"] = ((um.tin + 1080) % 1440).map(lambda x: f"{x // 60:02d}:{x % 60:02d}"); um.sort_values(["date", "tin"]).to_csv(out + "_unmatched.csv", index=False)
    print(txt); print("->", out + ".md")
