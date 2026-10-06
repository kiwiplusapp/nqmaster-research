"""mined(key, per, name): trades of a mined module (trades_b3 / trades_b4) for one period, FOMC days excluded (from ultra_plus.py)."""
import pickle, pandas as pd
TR = {}
for f in ("trades_b3.pkl", "trades_b4.pkl"): TR.update(pickle.load(open(f, "rb")))
def mined(key, per, name):
    df = TR[key]["mnq" if per == "REAL" else "nq"]
    lo, hi = (20240201, 3e7) if per == "REAL" else ((20200201, 20240101) if per == "IS" else (20240101, 3e7))
    from news import NEWS
    df = df[(df.date >= lo) & (df.date < hi) & ~df.date.isin(NEWS["FOMC"])]
    return pd.DataFrame(dict(date=df.date.to_numpy(), mod=name, tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df.usd.to_numpy(), w=1.0))
