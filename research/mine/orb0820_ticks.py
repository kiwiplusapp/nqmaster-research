"""TICK-LEVEL backtest of the 08:20 range breakout (Federico 2026-10-09: 'test it with the news blackout off so it trades').
The 1-minute research sim gave WR 70% / PF 1.6 (2020-26) but cannot see what happens inside the 08:30 news minute.
Here every NQ trade print is used (Databento GLBX.MDP3 NQ.v.0 'trades', 2025-05-01 -> 2026-10-08, ~17 months; raw files in the
session scratchpad) and, as a check of the micro contract, MNQ.v.0 prints for 2025-09.
Rules (research config G_ORB A=820 T=10 W=60 cap 0.25 R 0.5): range = high / low of the prints 08:20:00-08:29:59 ET;
buy stop 1 tick above, sell stop 1 tick below, live 08:30:00-09:29:59, first one triggered wins (OCO); stop = level -/+
min(range + 2 ticks, 0.25 daily ATR); target = level +/- 0.5 x that risk (resting limit, filled only on a 1-tick trade-through);
exit after 240 min or 15:55 at the print price.  Stop orders (entry and stop-loss) fill at the first print at least `lat`
after the triggering print: lat 0 = the triggering print itself (best case), 50 ms, 250 ms (server-held stops).
If the entry fill is already beyond the target or the stop, the bracket fires at once (exit at the next print).
$ per MNQ contract ($2 per point, $1.90 commission).  News days (CPI / NFP at 08:30) reported separately.
-> orb0820_ticks.json, orb0820_ticks_trades.csv"""
import os, sys, glob, json, numpy as np, pandas as pd
from multiprocessing import Pool
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
RAW = "/tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad/databento_raw"
NS = 1_000_000_000; M = 60 * NS
T820, T830, T930, T1555 = (8 * 60 + 20) * M, (8 * 60 + 30) * M, (9 * 60 + 30) * M, (15 * 60 + 55) * M
LATS = (0, 50_000_000, 250_000_000)
G = {}


@njit(cache=True)
def first_after(tod, start, t):
    for q in range(start, len(tod)):
        if tod[q] >= t: return q
    return -1


@njit(cache=True)
def sim_day(tod, p, atr, lat):
    """returns (side, level, fill, exit, reason, trig_tod, both) ; reason 1 target 2 stop 3 time 4 instant; side 0 = no trade."""
    n = len(tod); rh = -1e18; rl = 1e18; k0 = -1
    for q in range(n):
        if tod[q] >= T830: k0 = q; break
        if tod[q] >= T820: rh = max(rh, p[q]); rl = min(rl, p[q])
    if k0 < 0 or rh < 0 or atr <= 0: return 0, 0.0, 0.0, 0.0, 0, 0, 0
    up = rh + 0.25; dn = rl - 0.25; risk = min(rh - rl + 0.5, 0.25 * atr)
    k = -1; s = 0
    for q in range(k0, n):
        if tod[q] >= T930: break
        if p[q] >= up: k = q; s = 1; break
        if p[q] <= dn: k = q; s = -1; break
    if k < 0: return 0, 0.0, 0.0, 0.0, 0, 0, 0
    lvl = up if s == 1 else dn
    j = first_after(tod, k, tod[k] + lat)
    if j < 0: return 0, 0.0, 0.0, 0.0, 0, 0, 0
    fill = p[j]; sl = lvl - s * risk; tp = lvl + s * 0.5 * risk
    both = 0
    for q in range(j, n):                       # did the other side also trade inside the window (whipsaw day)?
        if tod[q] >= T930: break
        if (s == 1 and p[q] <= dn) or (s == -1 and p[q] >= up): both = 1; break
    if (fill - tp) * s >= 0 or (fill - sl) * s <= 0:
        e = min(j + 1, n - 1); return s, lvl, fill, p[e], 4, tod[k], both
    tend = min(tod[j] + 240 * M, T1555)
    for q in range(j + 1, n):
        if tod[q] >= tend: return s, lvl, fill, p[q], 3, tod[k], both
        if (s == 1 and p[q] <= sl) or (s == -1 and p[q] >= sl):
            e = first_after(tod, q, tod[q] + lat)
            if e < 0: e = q
            return s, lvl, fill, p[e], 2, tod[k], both
        if (s == 1 and p[q] >= tp + 0.25) or (s == -1 and p[q] <= tp - 0.25):
            return s, lvl, tp, tp, 1, tod[k], both           # 'fill' slot reused below: exit at tp
    return s, lvl, fill, p[n - 1], 3, tod[k], both


def init(atr_map): G["atr"] = atr_map


def month(f):
    import databento as db
    parts = []
    for ch in db.DBNStore.from_file(f).to_df(count=5_000_000):
        idx = pd.DatetimeIndex(ch.index).tz_convert("America/New_York").tz_localize(None)
        ns = idx.asi8; day = (ns // (86400 * NS)) * (86400 * NS); tod = ns - day
        m = (tod >= T820) & (tod < T1555 + M)
        if not m.any(): continue
        dd = pd.DatetimeIndex(day[m]); parts.append(pd.DataFrame(dict(date=dd.year * 10000 + dd.month * 100 + dd.day, tod=tod[m], p=ch["price"].to_numpy(float)[m])))
    if not parts: return []
    X = pd.concat(parts, ignore_index=True); out = []
    for date, g in X.groupby("date", sort=True):
        if pd.Timestamp(str(date)).dayofweek >= 5: continue
        atr = G["atr"].get(int(date), 0.0); tod = g.tod.to_numpy(np.int64); p = g.p.to_numpy(np.float64)
        for lat in LATS:
            s, lvl, fill, ex, why, tt, both = sim_day(tod, p, atr, lat)
            if s == 0: continue
            entry = fill if why != 1 else None
            out.append(dict(date=int(date), lat_ms=lat // 1_000_000, side=int(s), level=lvl, entry=float(fill) if why != 1 else np.nan,
                            exit=float(ex), reason=int(why), trig_sec=round((tt - T830) / NS, 3), both=int(both), atr=atr))
    # entries for target exits: rerun to recover the entry fill (sim_day reuses the slot)
    for r in out:
        if r["reason"] == 1:
            g = X[X.date == r["date"]]
            tod = g.tod.to_numpy(np.int64); p = g.p.to_numpy(np.float64)
            k = np.where((tod >= T830) & (tod < T930) & ((p >= r["level"]) if r["side"] == 1 else (p <= r["level"])))[0][0]
            j = max(k, np.searchsorted(tod, tod[k] + r["lat_ms"] * 1_000_000)); r["entry"] = float(p[min(j, len(p) - 1)])
    print(os.path.basename(f), len(out) // len(LATS), "days", flush=True)
    return out


def pf(u):
    u = np.asarray(u); l = -u[u <= 0].sum(); return round(float(u[u > 0].sum() / l), 3) if l > 0 else None


def summary(T):
    u = T.usd.to_numpy()
    return dict(trades=int(len(T)), wr=round(100 * float((u > 0).mean()), 1) if len(u) else None, pf=pf(u), avg=round(float(u.mean()), 2) if len(u) else None,
                net=round(float(u.sum())), entry_slip_ticks_avg=round(float(T.slip_ticks.mean()), 2) if len(T) else None,
                entry_slip_ticks_p90=round(float(T.slip_ticks.quantile(0.9)), 1) if len(T) else None)


if __name__ == "__main__":
    from core import Data, run_events
    from families_gold import gen_orb
    from news import NEWS
    D = Data("nqdb.npz")
    atr_map = {int(D.daydate[d]): float(D.atr[d]) for d in range(D.nd) if D.daydate[d] > 0}
    files = sorted(glob.glob(os.path.join(RAW, "nq_trades_2025", "**", "*.trades.dbn.zst"), recursive=True)) + \
            sorted(glob.glob(os.path.join(RAW, "nq_trades_2026", "**", "*.trades.dbn.zst"), recursive=True))
    mnq = sorted(glob.glob(os.path.join(RAW, "mnq_trades_2025_09", "**", "*.trades.dbn.zst"), recursive=True))
    with Pool(4, initializer=init, initargs=(atr_map,)) as pool:
        res = pool.map(month, files + mnq, chunksize=1)
    rows = []
    for f, r in zip(files + mnq, res):
        for x in r: x["feed"] = "MNQ" if "mnq_" in f else "NQ"; rows.append(x)
    T = pd.DataFrame(rows)
    T["usd"] = (T.exit - T.entry) * T.side * 2.0 - 1.9
    T["slip_ticks"] = (T.entry - T.level) * T.side / 0.25
    news = set(NEWS["CPI"]) | set(NEWS["NFP"]); T["news"] = T.date.isin(news)
    T.to_csv(os.path.join(HERE, "orb0820_ticks_trades.csv"), index=False)
    OUT = {}
    for lat in sorted(T.lat_ms.unique()):
        S = T[(T.feed == "NQ") & (T.lat_ms == lat)]
        OUT[f"NQ_lat{lat}ms"] = dict(all=summary(S), news_days=summary(S[S.news]), other_days=summary(S[~S.news]),
                                     other_side_also_broke_before_0930=summary(S[S.both == 1]), triggered_in_first_second=summary(S[S.trig_sec < 1.0]))
        print(f"lat {lat} ms", json.dumps(OUT[f"NQ_lat{lat}ms"]), flush=True)
    # same days on the 1-minute research sim
    tr = run_events(D, gen_orb(D, dict(A=820, T=10, W=60, cap=0.25, R=0.5, tf=0, hold=240)), flat=955, maxday=1, slip=0.25)
    lo, hi = int(T.date.min()), int(T.date.max())
    b = tr[(tr.date >= lo) & (tr.date <= hi)].usd.to_numpy()
    OUT["minute_sim_same_period"] = dict(trades=int(len(b)), wr=round(100 * float((b > 0).mean()), 1), pf=pf(b), net=round(float(b.sum())))
    print("1-minute research sim, same period:", OUT["minute_sim_same_period"], flush=True)
    # MNQ vs NQ in September 2025
    for feed in ("NQ", "MNQ"):
        S = T[(T.feed == feed) & (T.date >= 20250901) & (T.date < 20251001) & (T.lat_ms == 50)]
        OUT[f"sep2025_{feed}_lat50"] = summary(S); print("Sep 2025", feed, OUT[f"sep2025_{feed}_lat50"], flush=True)
    OUT["by_month_NQ_lat50"] = {str(m): summary(g) for m, g in T[(T.feed == "NQ") & (T.lat_ms == 50)].groupby(T.date // 100)}
    json.dump(OUT, open(os.path.join(HERE, "orb0820_ticks.json"), "w"), indent=1, default=float)
