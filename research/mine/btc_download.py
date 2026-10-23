"""Download Binance spot BTCUSDT 1-minute klines (monthly zips, 2017-08 -> 2026-09, daily zips for the current month)
into an empty scratch directory (untrusted data; read later with btc_prep.py).
Usage: python3 btc_download.py <out_dir> [first YYYY-MM] [last YYYY-MM]"""
import os, sys, time, urllib.request

BASE_M = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-{y}-{m:02d}.zip"
BASE_D = "https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1m/BTCUSDT-1m-{y}-{m:02d}-{d:02d}.zip"


def fetch(url, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 1000: return "cached"
    for k in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(dst + ".part", "wb") as f:
                f.write(r.read())
            os.replace(dst + ".part", dst); return "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404: return "404"
            time.sleep(3 * (k + 1))
        except Exception:
            time.sleep(3 * (k + 1))
    return "fail"


if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    y0, m0 = (int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "2017-08").split("-"))
    y1, m1 = (int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "2026-09").split("-"))
    y, m = y0, m0; n = 0
    while (y, m) <= (y1, m1):
        st = fetch(BASE_M.format(y=y, m=m), os.path.join(out, f"BTCUSDT-1m-{y}-{m:02d}.zip"))
        print(y, m, st, flush=True); n += st in ("ok", "cached")
        m += 1
        if m > 12: m, y = 1, y + 1
    # current month: daily files (stop at the first 404)
    yd, md = y1, m1 + 1
    if md > 12: yd, md = y1 + 1, 1
    for d in range(1, 32):
        st = fetch(BASE_D.format(y=yd, m=md, d=d), os.path.join(out, f"BTCUSDT-1m-{yd}-{md:02d}-{d:02d}.zip"))
        if st == "404": break
        print(yd, md, d, st, flush=True)
    print("monthly files ok:", n)
