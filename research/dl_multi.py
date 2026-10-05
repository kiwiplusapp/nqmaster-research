"""Adaptive, rate-limit-friendly Dukascopy downloader: newest days first, symbols interleaved."""
import datetime as dt, os, sys, time
import requests
ROOT = os.path.dirname(os.path.abspath(__file__))
SYMS = sys.argv[1].split(",")
START = dt.date(2020, 1, 1); END = dt.date(2026, 9, 26)
s = requests.Session(); s.headers["User-Agent"] = "Mozilla/5.0"
days = [END - dt.timedelta(d) for d in range((END - START).days + 1)]
days = [d for d in days if d.weekday() != 5]
delay = 0.4; ok = 0; t0 = time.time()
for day in days:
    for sym in SYMS:
        raw = os.path.join(ROOT, "data", "raw_" + sym); os.makedirs(raw, exist_ok=True)
        path = os.path.join(raw, day.strftime("%Y%m%d") + ".bi5")
        if os.path.exists(path):
            continue
        url = f"https://datafeed.dukascopy.com/datafeed/{sym}/{day.year}/{day.month-1:02d}/{day.day:02d}/BID_candles_min_1.bi5"
        while True:
            try:
                r = s.get(url, timeout=30)
            except Exception:
                time.sleep(5); continue
            if r.status_code == 200:
                open(path, "wb").write(r.content); ok += 1
                delay = max(0.25, delay * 0.97); break
            if r.status_code == 404:
                open(path, "wb").close(); break
            if r.status_code == 429:
                delay = min(10.0, delay * 1.3); time.sleep(8); continue
            time.sleep(3)
        time.sleep(delay)
    if ok and ok % 100 == 0:
        print(f"{day} ok={ok} delay={delay:.2f} rate={ok/(time.time()-t0):.2f}/s", flush=True)
print("DONE", ok, flush=True)
