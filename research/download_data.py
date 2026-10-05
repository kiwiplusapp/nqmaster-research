"""Download Nasdaq-100 (USATECHIDXUSD) 1-minute BID candles from Dukascopy's public datafeed.
Output: research/data/nq_1m_utc.pkl with columns [time_utc, open, high, low, close, volume]."""
import datetime as dt, lzma, struct, os, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
SYM = sys.argv[1] if len(sys.argv) > 1 else "USATECHIDXUSD"
OUT = sys.argv[2] if len(sys.argv) > 2 else "nq_1m_utc.pkl"
RAW = os.path.join(ROOT, "data", "raw" if SYM == "USATECHIDXUSD" else "raw_" + SYM)
os.makedirs(RAW, exist_ok=True)
START = dt.date.fromisoformat(os.environ.get('DL_START', '2020-01-01'))
END = dt.date.fromisoformat(os.environ.get('DL_END', '2026-09-26'))

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0"

def fetch(day):
    path = os.path.join(RAW, day.strftime("%Y%m%d") + ".bi5")
    if os.path.exists(path):
        return day, "cached"
    url = f"https://datafeed.dukascopy.com/datafeed/{SYM}/{day.year}/{day.month-1:02d}/{day.day:02d}/BID_candles_min_1.bi5"
    for attempt in range(40):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
                time.sleep(0.15)
                return day, "ok"
            if r.status_code == 404:
                open(path, "wb").close()
                return day, "404"
            if r.status_code == 429:
                time.sleep(20 + attempt * 5)
                continue
        except Exception as e:
            time.sleep(2 + attempt * 2)
    return day, "fail"

days = [START + dt.timedelta(d) for d in range((END - START).days + 1)]
days = [d for d in days if d.weekday() != 5]  # no Saturday session
with ThreadPoolExecutor(int(os.environ.get('DL_THREADS', '3'))) as ex:
    res = list(ex.map(fetch, days))
fails = [d for d, s in res if s == "fail"]
print("downloaded", len(res), "fails", len(fails), fails[:10])

rows = []
for day in days:
    path = os.path.join(RAW, day.strftime("%Y%m%d") + ".bi5")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        continue
    raw = lzma.decompress(open(path, "rb").read())
    base = int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp())
    for i in range(len(raw) // 24):
        t, o, c, l, h, v = struct.unpack(">iiiiif", raw[i * 24:(i + 1) * 24])
        rows.append((base + t, o / 1000.0, h / 1000.0, l / 1000.0, c / 1000.0, v))

df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
df["time_utc"] = pd.to_datetime(df["ts"], unit="s", utc=True)
df = df.drop(columns="ts")
# Drop closed-market placeholder candles (no ticks).
df = df[df["volume"] > 0].reset_index(drop=True)
df.to_pickle(os.path.join(ROOT, "data", OUT))
print(df.shape, df["time_utc"].min(), df["time_utc"].max())
