"""Convert BarExporterUTC CSV (UTC bar-CLOSE timestamps) into the research npz format."""
import sys, numpy as np, pandas as pd
src, dst = sys.argv[1], sys.argv[2]
f = pd.read_csv(src, sep=";", header=None, names=["t", "o", "h", "l", "c", "v"])
ts = pd.to_datetime(f.t, format="%Y%m%d %H%M%S") - pd.Timedelta(minutes=1)     # bar OPEN, UTC
ts = ts.dt.tz_localize("UTC")
et = ts.dt.tz_convert("America/New_York")
om = (et.dt.hour * 60 + et.dt.minute).to_numpy().astype(np.int32)
sess = et + pd.Timedelta(hours=6)
date = sess.dt.strftime("%Y%m%d").astype(np.int32).to_numpy(); dow = sess.dt.dayofweek.to_numpy().astype(np.int32)
keep = ~((om >= 17 * 60) & (om < 18 * 60)) & (dow < 5)
f = f[keep].reset_index(drop=True); om = om[keep]; date = date[keep]; dow = dow[keep]; ts = ts[keep].reset_index(drop=True)
uniq, dayid = np.unique(date, return_inverse=True)
ep = ts.dt.tz_convert(None).values.astype("datetime64[s]").astype("int64") // 60
np.savez("data/" + dst, o=f.o.to_numpy(float), h=f.h.to_numpy(float), l=f.l.to_numpy(float), c=f.c.to_numpy(float), v=f.v.to_numpy(float),
         om=om, dayid=dayid.astype(np.int32), date=date, dates=uniq.astype(np.int32), dow=dow, epoch=ep)
print(dst, "bars", len(f), "days", len(uniq), uniq[0], "->", uniq[-1])
