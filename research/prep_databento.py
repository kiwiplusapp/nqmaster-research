"""Convert Databento GLBX.MDP3 ohlcv-1m continuous futures (NQ.v.0 / GC.v.0, 2010-06 -> 2026-10) into the research npz format
(same keys as prep_nt.py: bar OPEN time, ET session date = ET + 6 h, 17:00-18:00 ET and weekend bars dropped).
Rolls: the volume-based continuous symbol switches contract at a session boundary; prices from each switch on are shifted
(additive FORWARD adjustment: 2010 prices stay raw, later ones move down by the cumulative carry, ~5,000 NQ points by 2026, so
nothing turns negative) by the spread between the new and the old contract measured on the ohlcv-1d bars of the day before
the switch (v.1 close - v.0 close), so intraday point moves stay exact and cross-day levels (prior close, SMA20, ATR) have no
roll gaps.  Gold: prices x 2.5 (research convention: tick 0.25 = one MGC tick, $4 per research point).
Usage (from research/): python3 -I prep_databento.py <ohlcv-1m.dbn.zst> <ohlcv-1d v0v1.dbn.zst> <out name> [scale]"""
import sys, numpy as np, pandas as pd, databento as db

src, daily, dst = sys.argv[1], sys.argv[2], sys.argv[3]
scale = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
m = db.DBNStore.from_file(src).to_df().reset_index()
m = m.sort_values("ts_event").reset_index(drop=True)
d = db.DBNStore.from_file(daily).to_df().reset_index()
d["day"] = d.ts_event.dt.tz_convert(None).dt.normalize()

# ---- roll spreads
iid = m.instrument_id.to_numpy(); sw = np.nonzero(iid[1:] != iid[:-1])[0] + 1
adj = np.zeros(len(m)); rolls = []
for k in sw[::-1]:
    old, new = iid[k - 1], iid[k]; t = m.ts_event.iat[k].tz_convert(None)
    a = d[(d.instrument_id == old) & (d.day < t.normalize())][["day", "close"]]
    b = d[(d.instrument_id == new) & (d.day < t.normalize())][["day", "close"]]
    j = a.merge(b, on="day", suffixes=("_o", "_n"))
    if len(j): sp = float(j.close_n.iat[-1] - j.close_o.iat[-1]); how = "daily"
    else: sp = float(m.open.iat[k] - m.close.iat[k - 1]); how = "gap"
    adj[k:] -= sp; rolls.append((str(t), int(old), int(new), round(sp, 2), how))
for c in ("open", "high", "low", "close"): m[c] = (m[c] + adj) * scale
print("rolls", len(rolls), "| by daily spread", sum(r[4] == "daily" for r in rolls), "| last 3", rolls[:3])
print("min price after adjustment", round(float(m.low.min()), 2))

# ---- research format (as prep_nt.py)
ts = m.ts_event
et = ts.dt.tz_convert("America/New_York")
om = (et.dt.hour * 60 + et.dt.minute).to_numpy().astype(np.int32)
sess = et + pd.Timedelta(hours=6)
date = sess.dt.strftime("%Y%m%d").astype(np.int32).to_numpy(); dow = sess.dt.dayofweek.to_numpy().astype(np.int32)
keep = ~((om >= 17 * 60) & (om < 18 * 60)) & (dow < 5)
m = m[keep].reset_index(drop=True); om = om[keep]; date = date[keep]; dow = dow[keep]; ts = ts[keep].reset_index(drop=True)
uniq, dayid = np.unique(date, return_inverse=True)
ep = ts.dt.tz_convert(None).values.astype("datetime64[s]").astype("int64") // 60
np.savez("data/" + dst, o=m.open.to_numpy(float), h=m.high.to_numpy(float), l=m.low.to_numpy(float), c=m.close.to_numpy(float),
         v=m.volume.to_numpy(float), om=om, dayid=dayid.astype(np.int32), date=date, dates=uniq.astype(np.int32), dow=dow, epoch=ep)
pd.DataFrame(rolls, columns=["switch_utc", "old_id", "new_id", "spread", "method"]).to_csv("data/" + dst.replace(".npz", "_rolls.csv"), index=False)
print(dst, "bars", len(m), "days", len(uniq), uniq[0], "->", uniq[-1])
