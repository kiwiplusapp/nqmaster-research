"""Download histdata.com 1-minute ASCII bars (EST, no DST) for index CFDs and build a UTC pickle."""
import io, os, re, sys, time, zipfile, datetime as dt
import requests, pandas as pd
ROOT = os.path.dirname(os.path.abspath(__file__))
pair = sys.argv[1].lower(); out = sys.argv[2]
raw = os.path.join(ROOT, "data", "hd_" + pair + os.environ.get('HD_SUFFIX', '')); os.makedirs(raw, exist_ok=True)
s = requests.Session(); s.headers["User-Agent"] = "Mozilla/5.0"
base = "https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/"
Y0, Y1 = int(os.environ.get('HD_Y0', 2020)), int(os.environ.get('HD_Y1', 2026))
jobs = [(y, None) for y in range(Y0, min(Y1, 2026))] + ([(2026, m) for m in range(1, 10)] if Y1 >= 2026 else [])
for y, m in jobs:
    name = f"{pair}_{y}{'' if m is None else f'_{m:02d}'}.zip"
    path = os.path.join(raw, name)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        continue
    url = base + f"{pair}/{y}" + ("" if m is None else f"/{m}")
    page = s.get(url, timeout=60).text
    f = dict(re.findall(r'name="(tk|date|datemonth|platform|timeframe|fxpair)" id="[^"]*" value="([^"]*)"', page))
    if "tk" not in f:
        print("no form for", y, m); continue
    r = s.post("https://www.histdata.com/get.php", data=f, headers={"Referer": url}, timeout=120)
    if r.status_code == 200 and r.content[:2] == b"PK":
        open(path, "wb").write(r.content); print("ok", name, len(r.content), flush=True)
    else:
        print("fail", name, r.status_code, r.content[:80], flush=True)
    time.sleep(1.5)
frames = []
for fn in sorted(os.listdir(raw)):
    if not fn.endswith(".zip"): continue
    z = zipfile.ZipFile(os.path.join(raw, fn))
    for inner in z.namelist():
        if inner.lower().endswith(".csv"):
            df = pd.read_csv(z.open(inner), sep=";", header=None, names=["ts", "open", "high", "low", "close", "volume"])
            frames.append(df)
df = pd.concat(frames).drop_duplicates("ts").sort_values("ts")
# Verified against Dukascopy: timestamps are New York local time WITH daylight saving.
local = pd.to_datetime(df["ts"], format="%Y%m%d %H%M%S")
df["time_utc"] = local.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
df = df[df["time_utc"].notna()]
df["volume"] = 1.0
df = df.drop(columns="ts").reset_index(drop=True)
df.to_pickle(os.path.join(ROOT, "data", out))
print(df.shape, df.time_utc.min(), df.time_utc.max())
