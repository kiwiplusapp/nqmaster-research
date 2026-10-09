"""Federico 2026-10-09: 16 years of REAL NQ futures (Databento GLBX.MDP3 ohlcv-1m NQ.v.0, 2010-06 -> 2026-10, back-adjusted,
research/data/nqdb.npz from research/prep_databento.py) to test the CURRENT NQMaster profiles (final3y.PROFILES: Ultra with the
2026-10-08 rules, Ultra lean, WR70Plus) on years the system never saw (2010-2019) and on real futures for 2020-2023.
Two views:
  real  : $ per MNQ contract ($1.90 + 1 tick per side), NQMaster's MinAtrPoints 150 guard (no trading when the daily ATR < 150)
  norm  : the same trades with cost = 0.345% of the daily ATR and P&L in % of ATR (removes the price-level effect: NQ was ~2,000
          in 2010 with ~1.5% daily range, so fixed tick costs were 4x larger relative to the moves than today)
Entries are rebuilt with wrq_build.build (same module code as every other study) -> wrq_entries_db.pkl.
FOMC days 2010-2019 added from the Fed's published meeting calendar (2020+ from news.py).
-> db_long.json (per profile, per year, both views), db_long_trades.pkl"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import wrq_lib, wrq_port, wrq_combo
import final3y as F3
from wrq_lib import PER, getD, SLIP
from wrq_exits import arrays, sim
from wrq_port import BASE_W

NAME = "nqdb.npz"
FOMC_1019 = [20100127, 20100316, 20100428, 20100623, 20100810, 20100921, 20101103, 20101214,
             20110126, 20110315, 20110427, 20110622, 20110809, 20110921, 20111102, 20111213,
             20120125, 20120313, 20120425, 20120620, 20120801, 20120913, 20121024, 20121212,
             20130130, 20130320, 20130501, 20130619, 20130731, 20130918, 20131030, 20131218,
             20140129, 20140319, 20140430, 20140618, 20140730, 20140917, 20141029, 20141217,
             20150128, 20150318, 20150429, 20150617, 20150729, 20150917, 20151028, 20151216,
             20160127, 20160316, 20160427, 20160615, 20160727, 20160921, 20161102, 20161214,
             20170201, 20170315, 20170503, 20170614, 20170726, 20170920, 20171101, 20171213,
             20180131, 20180321, 20180502, 20180613, 20180801, 20180926, 20181108, 20181219,
             20190130, 20190320, 20190501, 20190619, 20190731, 20190918, 20191030, 20191211]
PER["DB"] = (NAME, 20100607, 20261010); PER["DB_N"] = (NAME, 20100607, 20261010)
MIN_ATR = 150.0


def entries_db():
    p = os.path.join(HERE, "wrq_entries_db.pkl")
    if os.path.exists(p): return pickle.load(open(p, "rb"))
    import wrq_build
    from news import NEWS
    E = wrq_build.build(NAME); E["fomc"] = E.date.isin(set(NEWS["FOMC"]) | set(FOMC_1019))
    pickle.dump(E, open(p, "wb")); return E


def module_trades3(per, mod, p=None, slip=SLIP, keep=None):
    name, lo, hi = PER[per]; D = getD(name); E = wrq_port.entries()[name]; E = E[E["mod"] == mod].sort_values("fi", kind="stable")
    if keep is not None: E = E[keep(E, name)]
    norm = per.endswith("_N"); A = arrays(E)
    u, ok, out = sim(A, D, 0.0 if norm else slip, p or {}, norm)
    m = ok & (A["date"] >= lo) & (A["date"] < hi) & (~A["fomc"])
    fi = A["fi"][m]; xi = out[m, 1].astype(np.int64)
    return pd.DataFrame(dict(date=A["date"][m], mod=mod, tin=D.sm[fi], tout=D.sm[xi] + 1, d=A["d"][m], u=u[m], fi=fi, xi=xi,
                             atr=D.atr[D.day[fi]], w=BASE_W.get(mod, 1.0)))


wrq_port.module_trades = module_trades3; wrq_combo.module_trades = module_trades3


def trades(prof, per):
    mods, over, agr, boosts = F3.PROFILES[prof]
    wrq_port.PROFILES["_f"] = mods
    X = wrq_combo.build(per, "_f", {k: v for k, v in over.items() if k in mods}, tuple(a for a in agr if a in mods))
    if not boosts: X["w"] = 1.0
    return X.sort_values(["date", "tin"]).reset_index(drop=True)


def stats(X, days, norm=False):
    x = (X.u * X.w).to_numpy(); d = pd.Series(x, index=X.date.to_numpy()).groupby(level=0).sum().reindex(days, fill_value=0.0)
    eq = d.cumsum(); w = x[x > 0].sum(); l = -x[x <= 0].sum()
    r = dict(trades=int(len(X)), tpd=round(len(X) / max(len(days), 1), 2), wr=round(100 * float((X.u > 0).mean()), 1) if len(X) else None,
             pf=round(w / l, 2) if l > 0 else None, sharpe=round(float(d.mean() / d.std() * np.sqrt(252)), 2) if d.std() > 0 else None)
    if norm: r.update(mean_trade_pct_atr=round(float(x.mean()), 3) if len(x) else None)
    else: r.update(per_month=round(float(d.mean() * 21)), net=round(float(x.sum())), max_dd=round(float((eq.cummax() - eq).max())),
                   days_traded_pct=round(100 * X.date.nunique() / max(len(days), 1), 1))
    return r


if __name__ == "__main__":
    E = entries_db(); wrq_port.entries()[NAME] = E
    print("entries", len(E), E.groupby("mod").size().to_dict(), flush=True)
    D = getD(NAME)
    alld = np.array(sorted(set(D.daydate[(D.ro >= 0)])))
    alld = alld[(alld >= 20100607) & ~np.isin(alld, list(set(FOMC_1019)))]
    sys.path.insert(0, os.path.dirname(HERE)); from news import NEWS
    alld = alld[~np.isin(alld, list(NEWS["FOMC"]))]
    atr_day = pd.Series(D.atr, index=D.daydate).groupby(level=0).last()
    OUT = {"days": int(len(alld)), "atr_days_ge_150_pct_by_year": {}, "profiles": {}}
    for y in range(2010, 2027):
        dd = alld[alld // 10000 == y]; OUT["atr_days_ge_150_pct_by_year"][y] = round(100 * float((atr_day.reindex(dd) >= MIN_ATR).mean()), 1)
    TR = {}
    for prof in ("Ultra", "UltraLean", "WR70Plus"):
        Xr = trades(prof, "DB"); Xn = trades(prof, "DB_N"); TR[prof] = (Xr, Xn)
        Xg = Xr[Xr.atr >= MIN_ATR]                                     # NQMaster as coded: MinAtrPoints 150
        rec = {"years": {}}
        for y in range(2010, 2027):
            dd = alld[alld // 10000 == y]
            rec["years"][y] = dict(real_min_atr=stats(Xg[Xg.date // 10000 == y], dd), real_no_filter=stats(Xr[Xr.date // 10000 == y], dd),
                                   norm=stats(Xn[Xn.date // 10000 == y], dd, True))
        for lab, lo, hi in (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019), ("2020-2023", 2020, 2023), ("2024-2026", 2024, 2026), ("2010-2026", 2010, 2026)):
            dd = alld[(alld // 10000 >= lo) & (alld // 10000 <= hi)]
            k = lambda X: X[(X.date // 10000 >= lo) & (X.date // 10000 <= hi)]
            rec[lab] = dict(real_min_atr=stats(k(Xg), dd), real_no_filter=stats(k(Xr), dd), norm=stats(k(Xn), dd, True))
        dd = alld[alld >= 20240201]; k = Xr[(Xr.date >= 20240201) & (Xr.date <= 20260925)]
        rec["check_vs_mnq_fut_2024_02_2026_09"] = stats(k, dd[dd <= 20260925])
        OUT["profiles"][prof] = rec
        print(prof, json.dumps({k: rec[k] for k in ("2010-2014", "2015-2019", "2020-2023", "2024-2026", "check_vs_mnq_fut_2024_02_2026_09")}), flush=True)
    pickle.dump(TR, open("db_long_trades.pkl", "wb"))
    json.dump(OUT, open("db_long.json", "w"), indent=1, default=float)
