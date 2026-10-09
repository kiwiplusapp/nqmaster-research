"""Out-of-sample check of NQMaster's order-flow boost (UseOrderFlowBoost) on order-flow data it never saw.
Second free Databento credit (2026-10-09, $116.61 of $125): NQ.v.0 trades 2025-05-01 -> 2026-03-31 (11 months, before the
Apr-Oct 2026 sample where the 0.015 threshold was read) and MNQ.v.0 trades 2025-09 (1 month, to compare MNQ's own flow - what an
MNQ chart sees in NinjaTrader - with NQ's).
Rule tested exactly as coded (pre-registered, nothing re-fitted): session cumulative delta (aggressor buy - sell since 18:00 ET /
volume, bars before the fill bar), oriented with the trade, >= 0.015 -> x2 ('cap' = never above 2x base, NQMaster default;
'stack' = x2 on top).  Trades: Ultra on real NQ futures (db_long_trades.pkl, current rules, MinATR 150), $ per MNQ contract.
-> of_minutes_2025.pkl, of_minutes_mnq_2025_09.pkl, of_validate.json"""
import os, sys, glob, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from wrq_lib import getD

RAW = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad/databento_raw"
THR = 0.015


def minutes(sub, out):
    p = os.path.join(HERE, out)
    if os.path.exists(p): return pickle.load(open(p, "rb"))
    import databento as db
    parts = []
    for f in sorted(glob.glob(os.path.join(RAW, sub, "**", "*.dbn.zst"), recursive=True)):
        for ch in db.DBNStore.from_file(f).to_df(count=4_000_000):
            ch = ch.reset_index()
            ep = pd.to_datetime(ch.ts_event, utc=True).dt.tz_convert(None).values.astype("datetime64[m]").astype("int64")
            sz = ch["size"].to_numpy(float); sd = ch["side"].astype(str).to_numpy()
            g = pd.DataFrame(dict(ep=ep, buy=np.where(sd == "B", sz, 0.0), sell=np.where(sd == "A", sz, 0.0), n=1)).groupby("ep").sum()
            parts.append(g)
        print(os.path.basename(f), flush=True)
    M = pd.concat(parts).groupby(level=0).sum().sort_index()
    pickle.dump(M, open(p, "wb")); return M


def pf(x):
    x = np.asarray(x, float); l = -x[x <= 0].sum()
    return round(float(x[x > 0].sum() / l), 3) if l > 0 else None


def block(s, hit):
    x0 = s.u * s.w; xc = s.u * np.where(hit, np.maximum(s.w, 2), s.w); xs = s.u * s.w * np.where(hit, 2, 1)
    def dd(x):
        e = x.groupby(s.date.to_numpy()).sum().cumsum(); return round(float((e.cummax() - e).max()))
    b = s[hit]; nb = s[~hit]
    return dict(n=int(len(s)), boosted_pct=round(100 * float(hit.mean()), 1),
                boosted=dict(n=int(len(b)), wr=round(100 * float((b.u > 0).mean()), 1) if len(b) else None, pf=pf(b.u * b.w), avg=round(float((b.u * b.w).mean()), 1) if len(b) else None),
                rest=dict(n=int(len(nb)), wr=round(100 * float((nb.u > 0).mean()), 1) if len(nb) else None, pf=pf(nb.u * nb.w), avg=round(float((nb.u * nb.w).mean()), 1) if len(nb) else None),
                off=dict(net=round(float(x0.sum())), pf=pf(x0), dd=dd(x0)), cap=dict(net=round(float(xc.sum())), pf=pf(xc), dd=dd(xc)),
                stack=dict(net=round(float(xs.sum())), pf=pf(xs), dd=dd(xs)))


def cvd_feature(M, D, ep_all, X):
    S = M.reindex(ep_all).fillna(0.0); cb, cs = np.cumsum(np.r_[0, S.buy.to_numpy()]), np.cumsum(np.r_[0, S.sell.to_numpy()])
    first = D.ds[D.day]; i = X.fi.to_numpy(); B = cb[i] - cb[first[i]]; A = cs[i] - cs[first[i]]
    ok = ep_all[first[i]] >= M.index.min()                                   # the whole session is inside the order-flow data
    return np.where(ok & (B + A > 0), (B - A) / np.maximum(B + A, 1), np.nan) * X.d.to_numpy()


if __name__ == "__main__":
    from scipy.stats import spearmanr
    D = getD("nqdb.npz"); ep_all = np.load(os.path.join(os.path.dirname(HERE), "data", "nqdb.npz"))["epoch"]
    M_new = minutes("nq_trades_2025", "of_minutes_2025.pkl"); M_old = pickle.load(open(os.path.join(HERE, "of_minutes.pkl"), "rb"))
    print("new NQ minutes", len(M_new), M_new.index.min(), M_new.index.max(), flush=True)
    Xr, _ = pickle.load(open(os.path.join(HERE, "db_long_trades.pkl"), "rb"))["Ultra"]
    X = Xr[(Xr.atr >= 150) & (Xr.date >= 20250501)].copy()
    X["cvd"] = np.nan
    for M, lo, hi in ((M_new, 20250501, 20260401), (M_old, 20260401, 20261010)):
        m = ((X.date >= lo) & (X.date < hi)).to_numpy(); X.loc[m, "cvd"] = cvd_feature(M, D, ep_all, X[m])
    X = X[X.cvd.notna()]
    NEW = (X.date < 20260401).to_numpy(); OLD = ~NEW
    OUT = {"rule": f"session delta with the trade >= {THR} -> x2", "new_oos_2025_05_2026_03": block(X[NEW], (X[NEW].cvd >= THR).to_numpy()),
           "original_2026_04_10": block(X[OLD], (X[OLD].cvd >= THR).to_numpy()), "all": block(X, (X.cvd >= THR).to_numpy())}
    for lab, m in (("new", NEW), ("original", OLD), ("all", np.ones(len(X), bool))):
        r = spearmanr(X[m].cvd, X[m].u * X[m].w); OUT[f"spearman_{lab}"] = dict(rho=round(float(r[0]), 3), p=round(float(r[1]), 4), n=int(m.sum()))
    q = np.nanquantile(X[OLD].cvd, [0.2, 0.4, 0.6, 0.8]); b = np.digitize(X.cvd, q)          # quintile edges from the ORIGINAL sample
    OUT["quintiles_new_with_original_edges"] = {f"Q{k + 1}": dict(n=int(((b == k) & NEW).sum()), pf=pf((X.u * X.w)[(b == k) & NEW]),
                                                                    avg=round(float((X.u * X.w)[(b == k) & NEW].mean()), 1)) for k in range(5)}
    OUT["edges_original"] = [round(float(v), 4) for v in q]
    X["hit"] = X.cvd >= THR; X["mo"] = X.date // 100
    OUT["by_month"] = {str(mo): dict(n=int(len(g)), boosted=int(g.hit.sum()), avg_boosted=round(float((g.u * g.w)[g.hit].mean()), 1) if g.hit.any() else None,
                                     avg_rest=round(float((g.u * g.w)[~g.hit].mean()), 1), cap_gain=round(float((g.u * np.where(g.hit, np.maximum(g.w, 2), g.w)).sum() - (g.u * g.w).sum())))
                       for mo, g in X.groupby("mo")}
    OUT["by_module_new"] = {md: dict(n=int(len(g)), boosted=int(g.hit.sum()), avg_boosted=round(float((g.u * g.w)[g.hit].mean()), 1) if g.hit.any() else None,
                                     avg_rest=round(float((g.u * g.w)[~g.hit].mean()), 1) if (~g.hit).any() else None)
                            for md, g in X[NEW].groupby("mod")}
    # ---- MNQ's own flow vs NQ's (September 2025)
    Mm = minutes("mnq_trades_2025_09", "of_minutes_mnq_2025_09.pkl")
    if len(Mm):
        sep = X[(X.date >= 20250901) & (X.date < 20251001)].copy()
        sep["cvd_mnq"] = cvd_feature(Mm, D, ep_all, sep); sep = sep[sep.cvd_mnq.notna()]
        a, bq = sep.cvd >= THR, sep.cvd_mnq >= THR
        # per-minute session delta of the two contracts through the month
        idx = M_new.index[(M_new.index >= Mm.index.min()) & (M_new.index <= Mm.index.max())]
        sess = pd.Series(D.daydate[np.searchsorted(ep_all, idx.to_numpy()).clip(0, len(ep_all) - 1)], index=idx)
        nq = M_new.reindex(idx).fillna(0); mn = Mm.reindex(idx).fillna(0)
        cn = (nq.buy - nq.sell).groupby(sess.values).cumsum() / (nq.buy + nq.sell).groupby(sess.values).cumsum().replace(0, np.nan)
        cm = (mn.buy - mn.sell).groupby(sess.values).cumsum() / (mn.buy + mn.sell).groupby(sess.values).cumsum().replace(0, np.nan)
        OUT["mnq_vs_nq_sep2025"] = dict(
            trades=int(len(sep)), corr_cvd_at_trades=round(float(np.corrcoef(sep.cvd, sep.cvd_mnq)[0, 1]), 3),
            corr_session_delta_per_minute=round(float(pd.concat([cn, cm], axis=1).dropna().corr().iloc[0, 1]), 3),
            same_boost_decision_pct=round(100 * float((a == bq).mean()), 1), boosted_nq=int(a.sum()), boosted_mnq=int(bq.sum()), boosted_both=int((a & bq).sum()),
            mnq_volume_share_pct=round(100 * float((mn.buy + mn.sell).sum() / ((nq.buy + nq.sell).sum() + (mn.buy + mn.sell).sum())), 1),
            avg_trade_boosted_by_nq=round(float((sep.u * sep.w)[a].mean()), 1) if a.any() else None,
            avg_trade_boosted_by_mnq=round(float((sep.u * sep.w)[bq].mean()), 1) if bq.any() else None,
            avg_trade_rest_mnq=round(float((sep.u * sep.w)[~bq].mean()), 1))
    json.dump(OUT, open(os.path.join(HERE, "of_validate.json"), "w"), indent=1, default=float)
    for k in ("new_oos_2025_05_2026_03", "original_2026_04_10", "all", "spearman_new", "spearman_original", "spearman_all", "quintiles_new_with_original_edges", "mnq_vs_nq_sep2025"):
        print(k, json.dumps(OUT.get(k)), flush=True)
    print("by_month", json.dumps(OUT["by_month"]), flush=True)
