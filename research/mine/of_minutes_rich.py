"""Keep the paid Databento NQ trades (2026-04-01 -> 2026-10-08, 52M prints) as a rich per-minute order-flow table, so the raw 820 MB
never has to be bought again: per 1-minute bar (UTC minute of the print) buy / sell volume (aggressor B / A), trade counts, volume
in prints of size >= 5 / 10 / 20 / 50 per side, largest print per side, volume-weighted buy and sell price.
-> of_minutes_rich.pkl (DataFrame indexed by epoch minute)."""
import os, sys, glob, pickle, numpy as np, pandas as pd, databento as db
RAW = sys.argv[1]
parts = []
for f in sorted(glob.glob(os.path.join(RAW, "**", "*.dbn.zst"), recursive=True)):
    for ch in db.DBNStore.from_file(f).to_df(count=4_000_000):
        ch = ch.reset_index()
        ep = pd.to_datetime(ch.ts_event, utc=True).dt.tz_convert(None).values.astype("datetime64[m]").astype("int64")
        sz = ch["size"].to_numpy(float); px = ch["price"].to_numpy(float); sd = ch["side"].astype(str).to_numpy()
        isb = sd == "B"; isa = sd == "A"
        g = dict(ep=ep, buy=np.where(isb, sz, 0.0), sell=np.where(isa, sz, 0.0), nbuy=isb.astype(float), nsell=isa.astype(float),
                 pvb=np.where(isb, px * sz, 0.0), pva=np.where(isa, px * sz, 0.0))
        for k in (5, 10, 20, 50):
            g[f"buy{k}"] = np.where(isb & (sz >= k), sz, 0.0); g[f"sell{k}"] = np.where(isa & (sz >= k), sz, 0.0)
        df = pd.DataFrame(g); agg = df.groupby("ep").sum()
        mx = pd.DataFrame(dict(ep=ep, mb=np.where(isb, sz, 0.0), ma=np.where(isa, sz, 0.0))).groupby("ep").max()
        parts.append(agg.join(mx)); print(os.path.basename(f), len(ch), flush=True)
M = pd.concat(parts); s = [c for c in M.columns if c not in ("mb", "ma")]
M = M.groupby(level=0).agg({**{c: "sum" for c in s}, "mb": "max", "ma": "max"}).sort_index()
M["vwap_buy"] = M.pvb / M.buy.where(M.buy > 0); M["vwap_sell"] = M.pva / M.sell.where(M.sell > 0); M = M.drop(columns=["pvb", "pva"])
M = M.astype({c: "float32" for c in M.columns})
pickle.dump(M, open("of_minutes_rich.pkl", "wb")); print("minutes", len(M), "cols", list(M.columns))
