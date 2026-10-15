"""2026-10-15 CME NQ options open interest (what the QuikStrike OI heatmap shows) as a trading input. Databento GLBX.MDP3 NQ.OPT
definition + statistics (open interest, stat_type 9), 2024-01..2026-10 (free credit). Levels for trading day D use only OI
published before D (no lookahead). Levels: per strike, OI summed over calls+puts of every NQ option expiring within the next
7 calendar days ("near" walls) and of all expiries ("all"). Tests (fixed before looking), each on 2024-25 and on 2026 separately:
 1 Magnet: on days when a near expiry settles, does the RTH close end nearer to the largest-OI strike than the 09:30 open?
   Control = same test with a strike shifted by +-3 strikes (100-250 pts away from the big one, same distance class).
 2 Level reaction: first RTH touch (after 10:00) of a top-3 OI strike: 30-min move against the approach (rejection) vs touches of
   ordinary 100-pt round numbers that are not top-OI strikes.
 3 NQMaster trade filter: Ultra trades (cand16 UltraR real) with a top-3 OI strike between entry and target vs without.
-> oi_lab.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
import databento as db
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from core import Data
OI = "/tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad/oi"


def load():
    import glob
    defs = []
    for f in sorted(glob.glob(os.path.join(OI, "chunks", "def_*.dbn.zst"))) + [os.path.join(OI, "nq_opt_definition.dbn.zst")]:
        try: defs.append(db.DBNStore.from_file(f).to_df().reset_index())
        except Exception as e: print("skip", f, e)
    d = pd.concat(defs, ignore_index=True)
    d = d[d.instrument_class.isin(["C", "P"])].drop_duplicates("instrument_id", keep="last")[["instrument_id", "instrument_class", "strike_price", "expiration", "underlying"]]
    st = []
    for f in sorted(glob.glob(os.path.join(OI, "chunks", "stat_*.dbn.zst"))):
        x = db.DBNStore.from_file(f).to_df().reset_index(); st.append(x[x.stat_type == 9][["ts_ref", "ts_event", "instrument_id", "quantity"]])
    s = pd.concat(st, ignore_index=True)
    s["day"] = pd.to_datetime(s.ts_ref, utc=True).dt.tz_convert("America/New_York").dt.date
    s = s.sort_values("ts_event").drop_duplicates(["instrument_id", "day"], keep="last")
    n0 = len(s); s = s.merge(d, on="instrument_id"); print("OI rows with a definition", len(s), "of", n0)
    s["exp"] = pd.to_datetime(s.expiration, utc=True).dt.tz_convert("America/New_York").dt.date
    return s


def levels(s, days):
    """for each trading day D: OI by strike as published on the last OI day before D"""
    oid = np.array(sorted(s.day.unique())); out = {}
    for D in days:
        dd = pd.Timestamp(str(D)).date(); k = np.searchsorted(oid, dd) - 1
        if k < 0: continue
        snap = s[s.day == oid[k]]
        near = snap[(pd.to_datetime(snap.exp) >= pd.Timestamp(dd)) & (pd.to_datetime(snap.exp) <= pd.Timestamp(dd) + pd.Timedelta(days=7))]
        out[D] = dict(near=near.groupby("strike_price").quantity.sum(), all=snap[pd.to_datetime(snap.exp) >= pd.Timestamp(dd)].groupby("strike_price").quantity.sum(),
                      expday=bool((snap.exp == dd).any()))
    return out


if __name__ == "__main__":
    s = load(); print("OI rows", len(s), "days", s.day.nunique(), "first", s.day.min(), "last", s.day.max(), flush=True)
    D = Data("nqdb.npz")
    # nqdb is forward-adjusted (later prices moved DOWN by the cumulative roll carry): raw = adjusted + carry of the rolls so far
    rolls = pd.read_csv(os.path.join(os.path.dirname(HERE), "data", "nqdb_rolls.csv"), parse_dates=["switch_utc"]).sort_values("switch_utc")
    rd = rolls.switch_utc.dt.strftime("%Y%m%d").astype(int).to_numpy(); cum = np.cumsum(rolls.spread.to_numpy())
    def carry(d):
        k = np.searchsorted(rd, d, side="right") - 1
        return float(cum[k]) if k >= 0 else 0.0
    off = {d: carry(d) for d in np.unique(D.daydate[D.daydate >= 20231201])}
    for a in ("o", "h", "l", "c"):
        arr = getattr(D, a).copy(); m = D.date >= 20231201
        arr[m] = arr[m] + np.vectorize(lambda d: off.get(d, carry(d)))(D.date[m]); setattr(D, a, arr)
    rth = (D.om >= 570) & (D.om < 960); days = np.array(sorted(set(D.daydate[(D.daydate >= 20240102)])))
    L = levels(s, days); print("days with levels", len(L), flush=True)
    res = {"meta": dict(oi_days=int(s.day.nunique()), level_days=len(L))}
    rows = []
    for d, lv in L.items():
        idx = np.nonzero((D.date == d) & rth)[0]
        if len(idx) < 300: continue
        o, c = D.o[idx[0]], D.c[idx[-1]]; hi, lo = D.h[idx], D.l[idx]; om = D.om[idx]
        for kind in ("near", "all"):
            ser = lv[kind]
            if ser is None or len(ser) == 0 or ser.sum() <= 0: continue
            win = ser[(ser.index > o * 0.97) & (ser.index < o * 1.03)]
            if len(win) < 5: continue
            top = win.sort_values(ascending=False).index[:3].to_numpy(); K = top[0]
            strikes = np.sort(win.index.to_numpy()); j = np.searchsorted(strikes, K)
            ctrl = [strikes[x] for x in (j - 3, j + 3) if 0 <= x < len(strikes)]
            rows.append(dict(date=d, kind=kind, exp=lv["expday"], K=K, magnet=abs(c - K) < abs(o - K), dK=abs(o - K),
                             ctrl=np.mean([abs(c - k2) < abs(o - k2) for k2 in ctrl]) if ctrl else np.nan))
            # level reaction: first touch after 10:00 of each top-3 strike / of non-OI 100-pt rounds
            for lvl, typ in [(k, "oi") for k in top] + [(r, "round") for r in np.arange(np.ceil(lo.min() / 100) * 100, hi.max(), 100) if not np.any(np.abs(top - r) < 1)]:
                t = np.nonzero((om >= 600) & (om < 930) & (lo <= lvl) & (hi >= lvl))[0]
                if len(t) == 0 or t[0] == 0: continue
                t = t[0]; appr = 1 if D.c[idx[t - 1]] < lvl else -1; t30 = min(t + 30, len(idx) - 1)
                rows.append(dict(date=d, kind=kind + "_touch_" + typ, rej=float((lvl - D.c[idx[t30]]) * appr)))
    R = pd.DataFrame(rows)
    for per, m in (("2024-25", R.date < 20260101), ("2026", R.date >= 20260101)):
        X = R[m]; out = {}
        for kind in ("near", "all"):
            a = X[X.kind == kind]; e = a[a.exp]
            out[kind] = dict(days=int(len(a)), magnet_all=round(float(a.magnet.mean()), 3), ctrl_all=round(float(a.ctrl.mean()), 3),
                             exp_days=int(len(e)), magnet_exp=round(float(e.magnet.mean()), 3) if len(e) else None, ctrl_exp=round(float(e.ctrl.mean()), 3) if len(e) else None)
            for typ in ("oi", "round"):
                t = X[X.kind == f"{kind}_touch_{typ}"].rej
                out[kind][f"touch_{typ}"] = dict(n=int(len(t)), mean_rejection_pts=round(float(t.mean()), 2), p_reject=round(float((t > 0).mean()), 3))
        res[per] = out; print(per, json.dumps(out), flush=True)
    # 3 NQMaster trade filter
    X = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["UltraR"][0]; X = X[X.date >= 20240102].copy()
    ent = D.o[X.fi.to_numpy().astype(int)]
    pf = lambda u: float(u[u > 0].sum() / -u[u <= 0].sum())
    flag = []
    for (d, e, dd), u in zip(X[["date"]].assign(e=ent, dd=X.d).itertuples(index=False), X.u):
        lv = L.get(d)
        if lv is None or lv["near"] is None or len(lv["near"]) == 0: flag.append(np.nan); continue
        win = lv["near"][(lv["near"].index > e * 0.97) & (lv["near"].index < e * 1.03)]
        top = win.sort_values(ascending=False).index[:3].to_numpy()
        flag.append(float(np.any((top - e) * dd > 0) and np.any(np.abs(top - e) < 0.004 * e)))
    X["wall_ahead"] = flag
    for per, m in (("2024-25", X.date < 20260101), ("2026", X.date >= 20260101)):
        Y = X[m & X.wall_ahead.notna()]
        res[per]["ultra_filter"] = {str(k): dict(n=int(len(g)), wr=round(100 * float((g.u > 0).mean()), 1), pf=round(pf(g.u * g.w), 3)) for k, g in Y.groupby("wall_ahead")}
        print(per, "Ultra trades with a big near-expiry OI strike ahead (within 0.4%):", res[per]["ultra_filter"], flush=True)
    json.dump(res, open(os.path.join(HERE, "oi_lab.json"), "w"), indent=1, default=str)
