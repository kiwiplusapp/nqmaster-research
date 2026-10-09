"""Order-flow test with real aggressor data (Databento NQ.v.0 trades 2026-04-01 -> 2026-10-09; side B = buyer lifted the offer,
A = seller hit the bid).  Per 1-minute bar: buy / sell volume, trade count, big-trade (>= BIG contracts) buy / sell volume.
For every NQMaster Ultra trade in the window (db_long_trades.pkl, real NQ futures, current rules) features known BEFORE the fill
bar opens, oriented with the trade direction:
  dl5 / dl15 / dl30   (buy - sell) / (buy + sell) over the last 5 / 15 / 30 minutes
  cvd                 session cumulative delta (since 18:00 ET) / session volume
  div15               price move of the last 15 minutes (in ATR) x sign, minus... -> agreement flag: +1 when price and delta of the
                      last 15 min point the same way as the trade, -1 when price agrees but delta disagrees (absorption against)
  big15               (big buys - big sells) / (big buys + big sells) over the last 15 minutes
Only ~6 months (~650 trades): IS = Apr-Jun 2026 (quintile edges), OOS = Jul-Oct 2026.  Exploratory: a rule is worth anything only if
the worst IS quintile is also clearly worst OOS.  -> of_trades.json, of_minutes.pkl (per-minute order flow, reusable)."""
import os, sys, glob, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from wrq_lib import getD

RAW = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad/databento_raw/nq_trades_2026"
BIG = 10


def minutes():
    p = os.path.join(HERE, "of_minutes.pkl")
    if os.path.exists(p): return pickle.load(open(p, "rb"))
    import databento as db
    parts = []
    for f in sorted(glob.glob(os.path.join(RAW, "**", "*.dbn.zst"), recursive=True)):
        for ch in db.DBNStore.from_file(f).to_df(count=4_000_000):
            ch = ch.reset_index()
            ep = pd.to_datetime(ch.ts_event, utc=True).dt.tz_convert(None).values.astype("datetime64[m]").astype("int64")
            sz = ch["size"].to_numpy(float); sd = ch["side"].astype(str).to_numpy()
            b = np.where(sd == "B", sz, 0.0); a = np.where(sd == "A", sz, 0.0); big = sz >= BIG
            g = pd.DataFrame(dict(ep=ep, buy=b, sell=a, n=1, bbuy=np.where(big, b, 0.0), bsell=np.where(big, a, 0.0))).groupby("ep").sum()
            parts.append(g); print(os.path.basename(f), len(ch), flush=True)
    M = pd.concat(parts).groupby(level=0).sum().sort_index()
    pickle.dump(M, open(p, "wb")); return M


def pf(x):
    x = np.asarray(x); l = -x[x <= 0].sum()
    return round(float(x[x > 0].sum() / l), 3) if l > 0 else None


if __name__ == "__main__":
    M = minutes(); print("minutes with trades", len(M), M.index.min(), M.index.max(), flush=True)
    D = getD("nqdb.npz"); ep_all = np.load(os.path.join(os.path.dirname(HERE), "data", "nqdb.npz"))["epoch"]
    # per-bar series aligned with nqdb bars (bar open minute = epoch)
    S = M.reindex(ep_all).fillna(0.0); buy, sell, bb, bs = (S[c].to_numpy() for c in ("buy", "sell", "bbuy", "bsell"))
    cb, cs, cbb, cbs = (np.cumsum(np.r_[0, x]) for x in (buy, sell, bb, bs))
    first = D.ds[D.day]                                                    # first bar of each bar's session
    Xr, _ = pickle.load(open("db_long_trades.pkl", "rb"))["Ultra"]
    X = Xr[(Xr.atr >= 150) & (Xr.date >= 20260401)].copy()
    i = X.fi.to_numpy(); d = X.d.to_numpy()                                # features use bars < fi (known at the fill bar open)
    def win(k):
        lo = np.maximum(i - k, first[i]); B = cb[i] - cb[lo]; A = cs[i] - cs[lo]
        return np.where(B + A > 0, (B - A) / np.maximum(B + A, 1), np.nan)
    for k in (5, 15, 30): X[f"dl{k}"] = win(k) * d
    B = cb[i] - cb[first[i]]; A = cs[i] - cs[first[i]]; X["cvd"] = np.where(B + A > 0, (B - A) / np.maximum(B + A, 1), np.nan) * d
    lo = np.maximum(i - 15, first[i]); pm = (D.c[i - 1] - D.o[lo]) * d
    X["div15"] = np.where(pm > 0, np.sign(X["dl15"]), np.nan)               # price moved the trade's way: does delta agree (+1) or not (-1)?
    BB = cbb[i] - cbb[lo]; BS = cbs[i] - cbs[lo]; X["big15"] = np.where(BB + BS > 0, (BB - BS) / np.maximum(BB + BS, 1), np.nan) * d
    X = X[ep_all[i] - 30 >= M.index.min()]                                  # full 30-minute look-back inside the order-flow data
    IS = X.date < 20260701; OOS = ~IS
    print("trades", len(X), "IS", int(IS.sum()), "OOS", int(OOS.sum()), flush=True)
    OUT = {"n": int(len(X)), "features": {}}
    for ft in ("dl5", "dl15", "dl30", "cvd", "big15", "div15"):
        if ft == "div15":
            rows = {}
            for v in (-1.0, 1.0):
                r = {}
                for lab, m in (("IS", IS), ("OOS", OOS)):
                    s = X[m & (X[ft] == v)]; x = (s.u * s.w).to_numpy()
                    r[lab] = dict(n=int(len(s)), wr=round(100 * float((s.u > 0).mean()), 1) if len(s) else None, pf=pf(x))
                rows["delta agrees" if v > 0 else "delta against"] = r
            OUT["features"][ft] = rows; print(ft, rows, flush=True); continue
        q = np.nanquantile(X.loc[IS, ft], [0.2, 0.4, 0.6, 0.8]); b = np.where(X[ft].isna(), -1, np.digitize(X[ft], q))
        rows = {}
        for k in range(5):
            r = {}
            for lab, m in (("IS", IS), ("OOS", OOS)):
                s = X[m & (b == k)]; x = (s.u * s.w).to_numpy()
                r[lab] = dict(n=int(len(s)), wr=round(100 * float((s.u > 0).mean()), 1) if len(s) else None, pf=pf(x))
            rows[f"Q{k + 1}"] = r
        OUT["features"][ft] = rows
        print(ft, {k: (v["IS"]["pf"], v["OOS"]["pf"]) for k, v in rows.items()}, flush=True)
    base = {lab: dict(n=int(m.sum()), wr=round(100 * float((X[m].u > 0).mean()), 1), pf=pf((X[m].u * X[m].w).to_numpy())) for lab, m in (("IS", IS), ("OOS", OOS))}
    OUT["base"] = base; print("base", base)
    json.dump(OUT, open("of_trades.json", "w"), indent=1, default=float)
