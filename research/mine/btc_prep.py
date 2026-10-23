"""Binance spot BTCUSDT 1-minute klines (monthly/daily zips from data.binance.vision, UTC open-time stamps) -> research npz
(same keys as prep_databento.py / prep_nt.py: bar OPEN time, ET session date = ET + 6 h, 17:00-18:00 ET and weekend bars dropped,
session dates not present in nqdb.npz (CME holidays) dropped so the session calendar matches NQ).
Price scale: BTC price / 20, so one research tick (0.25) = $5 of BTC price = one MBT tick ($0.50 per contract) and one research
point = $20 of BTC price = $2.00 per MBT (pv 2.0 like MNQ).  Volume = base volume (BTC).
Usage: python3 -I btc_prep.py <zip_dir> <out name e.g. btc_1m.npz>   (run from research/mine; reads ../data/nqdb.npz for the calendar)"""
import sys, os, io, glob, zipfile, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(os.path.dirname(HERE), "data")
SCALE = 1.0 / 20.0
COLS = ["t", "o", "h", "l", "c", "v", "tc", "qv", "n", "tb", "tq", "ig"]


def read_zip(path):
    with zipfile.ZipFile(path) as z:
        name = [n for n in z.namelist() if n.endswith(".csv")][0]
        raw = z.read(name)
    df = pd.read_csv(io.BytesIO(raw), header=None, names=COLS, usecols=["t", "o", "h", "l", "c", "v"], dtype=str)
    df = df[pd.to_numeric(df.t, errors="coerce").notna()]                        # drop a header line if present
    df = df.astype({"t": np.int64, "o": float, "h": float, "l": float, "c": float, "v": float})
    df["t"] = np.where(df.t > 10**14, df.t // 1000, df.t)                        # microseconds (2025+) -> milliseconds
    return df


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    files = sorted(glob.glob(os.path.join(src, "BTCUSDT-1m-*.zip")))
    parts = []
    for f in files:
        try: parts.append(read_zip(f))
        except Exception as e: print("skip", os.path.basename(f), repr(e)[:80])
    m = pd.concat(parts, ignore_index=True).drop_duplicates("t").sort_values("t").reset_index(drop=True)
    print("raw bars", len(m), "files", len(files))
    bad = (m.h < m.l) | (m.o <= 0) | (m.c <= 0) | (m.h < m[["o", "c"]].max(axis=1)) | (m.l > m[["o", "c"]].min(axis=1))
    print("bad OHLC rows dropped", int(bad.sum())); m = m[~bad].reset_index(drop=True)
    ts = pd.to_datetime(m.t, unit="ms", utc=True)
    et = ts.dt.tz_convert("America/New_York")
    om = (et.dt.hour * 60 + et.dt.minute).to_numpy().astype(np.int32)
    sess = et + pd.Timedelta(hours=6)
    date = sess.dt.strftime("%Y%m%d").astype(np.int32).to_numpy(); dow = sess.dt.dayofweek.to_numpy().astype(np.int32)
    keep = ~((om >= 17 * 60) & (om < 18 * 60)) & (dow < 5)
    nq = np.load(os.path.join(DATA, "nqdb.npz"))["dates"]
    cal = np.isin(date, nq) | (date > int(nq.max()))                               # CME calendar (holidays off); keep days after nqdb ends
    print("weekday bars", int(keep.sum()), "| dropped by CME calendar", int((keep & ~cal).sum()), "bars,", len(np.unique(date[keep & ~cal])), "days")
    keep &= cal
    m = m[keep].reset_index(drop=True); om = om[keep]; date = date[keep]; dow = dow[keep]; ts = ts[keep].reset_index(drop=True)
    uniq, dayid = np.unique(date, return_inverse=True)
    ep = ts.dt.tz_convert(None).values.astype("datetime64[s]").astype("int64") // 60
    out = os.path.join(DATA, dst)
    np.savez(out, o=m.o.to_numpy(float) * SCALE, h=m.h.to_numpy(float) * SCALE, l=m.l.to_numpy(float) * SCALE, c=m.c.to_numpy(float) * SCALE,
             v=m.v.to_numpy(float), om=om, dayid=dayid.astype(np.int32), date=date, dates=uniq.astype(np.int32), dow=dow, epoch=ep)
    print(dst, "bars", len(m), "days", len(uniq), uniq[0], "->", uniq[-1], "| MB", round(os.path.getsize(out) / 1e6, 1))
    # per-year coverage
    yr = date // 10000
    print(pd.Series(yr).value_counts().sort_index().to_string())
