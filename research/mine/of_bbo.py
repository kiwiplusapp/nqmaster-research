"""Order-book pressure test (Databento NQ.v.0 bbo-1m 2020-01 -> 2026-10, best bid/ask price and size sampled every minute).
For every NQMaster Ultra trade on real NQ futures 2020-2026 (db_long_trades.pkl, current rules, as coded with the Min ATR guard)
compute book features known BEFORE the fill bar opens (snapshots up to the start of the fill minute), oriented with the trade:
  imb0   (bid size - ask size) / (bid size + ask size) at the last snapshot, x direction
  imb5 / imb15   mean of that over the last 5 / 15 snapshots
  spr    spread in ticks at the last snapshot
  depth  bid + ask size at the last snapshot / its median at the same minute of day over the prior 20 sessions
Protocol: quintile edges from IS = 2020-2023 trades; PF / WR / $ per quintile in IS and OOS = 2024-2026; a skip rule is kept only
if the worst IS quintile is also clearly worst OOS and removing it raises portfolio Sharpe in BOTH periods.
-> of_bbo.json, of_bbo_feats.pkl.  Raw bbo file is read from the session scratchpad (python -I not needed: own download)."""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from wrq_lib import getD

RAW = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad/databento_raw/nq_bbo1m_2020_2026.dbn.zst"
FEATS = ["imb0", "imb5", "imb15", "spr", "depth"]


def load_bbo():
    import databento as db
    b = db.DBNStore.from_file(RAW).to_df().reset_index()
    tcol = "ts_recv" if "ts_recv" in b.columns else b.columns[0]
    t = pd.to_datetime(b[tcol], utc=True).dt.tz_convert(None).dt.ceil("min")          # snapshot time -> minute boundary it describes
    ep = (t.values.astype("datetime64[s]").astype("int64") // 60)
    bs, as_ = b["bid_sz_00"].to_numpy(float), b["ask_sz_00"].to_numpy(float)
    bp, ap = b["bid_px_00"].to_numpy(float), b["ask_px_00"].to_numpy(float)
    f = pd.DataFrame(dict(ep=ep, bs=bs, as_=as_, spr=(ap - bp) / 0.25)).groupby("ep").last()
    f = f[(f.bs > 0) & (f.as_ > 0) & (f.spr > 0) & (f.spr < 40)]
    f["imb"] = (f.bs - f.as_) / (f.bs + f.as_); f["dep"] = f.bs + f.as_
    return f


def features(X, D, f):
    """book state at the START of the fill bar (bar open epoch) = last snapshot with ep <= bar-open minute."""
    ep_open = D_epoch[X.fi.to_numpy()]
    idx = np.searchsorted(f.index.to_numpy(), ep_open, side="right") - 1
    ok = (idx >= 15) & (ep_open - f.index.to_numpy()[np.clip(idx, 0, None)] <= 3)
    imb = f.imb.to_numpy(); spr = f.spr.to_numpy(); dep = f.dep.to_numpy()
    c = np.cumsum(np.r_[0, imb])
    i = np.clip(idx, 15, None)
    out = pd.DataFrame(index=X.index)
    d = X.d.to_numpy()
    out["imb0"] = np.where(ok, imb[np.clip(idx, 0, None)] * d, np.nan)
    out["imb5"] = np.where(ok, (c[i + 1] - c[i - 4]) / 5 * d, np.nan)
    out["imb15"] = np.where(ok, (c[i + 1] - c[i - 14]) / 15 * d, np.nan)
    out["spr"] = np.where(ok, spr[np.clip(idx, 0, None)], np.nan)
    # depth relative to the same minute-of-day median of the prior 20 sessions
    mod = (f.index.to_numpy() % 1440); dd = pd.DataFrame(dict(mod=mod, dep=dep, day=f.index.to_numpy() // 1440))
    dd["med"] = dd.groupby("mod").dep.transform(lambda s: s.shift(1).rolling(20, min_periods=10).median())
    med = dd.med.to_numpy()
    out["depth"] = np.where(ok, dep[np.clip(idx, 0, None)] / med[np.clip(idx, 0, None)], np.nan)
    return out


def pf(x):
    x = np.asarray(x); l = -x[x <= 0].sum()
    return round(float(x[x > 0].sum() / l), 3) if l > 0 else None


def sharpe(X, days):
    d = (X.u * X.w).groupby(X.date).sum().reindex(days, fill_value=0.0)
    return round(float(d.mean() / d.std() * np.sqrt(252)), 3), round(float(d.mean() * 21))


if __name__ == "__main__":
    D = getD("nqdb.npz"); D_epoch = np.load(os.path.join(os.path.dirname(HERE), "data", "nqdb.npz"))["epoch"]
    f = load_bbo(); print("bbo snapshots", len(f), flush=True)
    Xr, _ = pickle.load(open("db_long_trades.pkl", "rb"))["Ultra"]
    X = Xr[(Xr.atr >= 150) & (Xr.date >= 20200101)].copy()
    F = features(X, D, f); X = X.join(F)
    print("trades", len(X), "with book features", int(X.imb0.notna().sum()), flush=True)
    pickle.dump(X, open("of_bbo_feats.pkl", "wb"))
    IS = X.date < 20240101; OOS = ~IS
    days_all = np.array(sorted(set(D.daydate[(D.ro >= 0)])))
    dIS = days_all[(days_all >= 20200101) & (days_all < 20240101)]; dOOS = days_all[(days_all >= 20240101) & (days_all <= 20261009)]
    OUT = {"n_trades": int(len(X)), "base": {"IS": sharpe(X[IS], dIS), "OOS": sharpe(X[OOS], dOOS)}, "features": {}}
    for ft in FEATS:
        q = np.nanquantile(X.loc[IS, ft], [0.2, 0.4, 0.6, 0.8]); b = np.digitize(X[ft], q); b = np.where(X[ft].isna(), -1, b)
        rows = {}
        for k in range(5):
            r = {}
            for lab, m in (("IS", IS), ("OOS", OOS)):
                s = X[m & (b == k)]; x = (s.u * s.w).to_numpy()
                r[lab] = dict(n=int(len(s)), wr=round(100 * float((s.u > 0).mean()), 1) if len(s) else None, pf=pf(x), avg=round(float(x.mean()), 1) if len(x) else None)
            rows[f"Q{k + 1}"] = r
        worst = min(range(5), key=lambda k: rows[f"Q{k + 1}"]["IS"]["avg"] if rows[f"Q{k + 1}"]["IS"]["avg"] is not None else 1e9)
        keep = b != worst
        rule = dict(skip_quintile=f"Q{worst + 1}", edges=[round(float(v), 4) for v in q],
                    IS=sharpe(X[IS & keep], dIS), OOS=sharpe(X[OOS & keep], dOOS),
                    IS_pf=pf((X[IS & keep].u * X[IS & keep].w)), OOS_pf=pf((X[OOS & keep].u * X[OOS & keep].w)),
                    IS_wr=round(100 * float((X[IS & keep].u > 0).mean()), 1), OOS_wr=round(100 * float((X[OOS & keep].u > 0).mean()), 1))
        OUT["features"][ft] = dict(quintiles=rows, rule=rule)
        print(ft, {k: (v["IS"]["pf"], v["OOS"]["pf"]) for k, v in rows.items()}, "| skip", rule["skip_quintile"], "Sharpe/mo IS", OUT["base"]["IS"], "->", rule["IS"],
              "OOS", OUT["base"]["OOS"], "->", rule["OOS"], flush=True)
    json.dump(OUT, open("of_bbo.json", "w"), indent=1, default=float)
