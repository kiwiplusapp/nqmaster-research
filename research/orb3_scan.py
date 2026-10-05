"""ORB v3 scan on one instrument: more trades, rr <= 2, re-entries, retest entries."""
import itertools, sys, time
import numpy as np, pandas as pd
import engine as en, evalkit as ev
from common import Ctx, SPLIT
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200); pd.set_option("display.max_columns", 40)
cx = Ctx()
o, h, l, c, om, dayid = cx.o, cx.h, cx.l, cx.c, cx.om, cx.dayid; nd = cx.nd
atr_d = cx.atr_daily(); ok = np.ones(nd, np.bool_)
sma20 = pd.Series(cx.prev_close).rolling(20, min_periods=15).mean().to_numpy()
t20 = np.nan_to_num(np.sign(cx.prev_close - sma20)).astype(np.int64)
ndays_is = (cx.rth_days < SPLIT).sum(); ndays_oos = (cx.rth_days >= SPLIT).sum()
rows = []; t0 = time.time()
grid = itertools.product([(570, 15), (570, 30), (570, 60)], (720, 780, 900), (0, 1), (0, 1), (0, 1), (0.15, 0.2, 0.3),
                         (1.0, 1.5, 2.0), (0.0, 1.0), (1, 2, 3))
for (rs, rl_), le, dm, et, sm, cap, rr, be, mt in grid:
    if be > 0 and rr <= 1.0:
        continue
    if rs + rl_ >= le:
        continue
    r = en.sim_range(o, h, l, c, om, dayid, cx.open_idx, atr_d, rs, rl_, le, 955, t20, dm, et, sm, cap, rr, be, mt, 30, ok)
    df = ev.to_df(r, cx.d, "x")
    if len(df) < 200:
        continue
    a = df[df.date < SPLIT]; b = df[df.date >= SPLIT]; rec = df[df.date >= 20250101]
    sa = ev.stats(a); sb = ev.stats(b)
    yr = df.groupby("year").R.sum()
    rows.append(dict(rng=rl_, last=le, dir=["trend", "both"][dm], entry=["stop", "retest"][et], stop=["opp", "mid"][sm], cap=cap, rr=rr, be=be, maxtr=mt,
                     tpd=round(len(df) / len(cx.rth_days), 2), wr_is=sa["wr"], wr_oos=sb["wr"], pf_is=sa["pf"], pf_oos=sb["pf"],
                     Rday_is=round(a.R.sum() / ndays_is, 3), Rday_oos=round(b.R.sum() / ndays_oos, 3), avg_2526=round(rec.R.mean(), 3),
                     sh_is=sa["sharpe"], sh_oos=sb["sharpe"], dd_is=sa["maxdd"], pos_years=int((yr > 0).sum()), risk=round(df.risk.mean(), 1)))
out = pd.DataFrame(rows); import os; out.to_csv(os.environ.get("SCAN_OUT", "orb3_scan.csv"), index=False)
print("configs", len(out), "secs", round(time.time() - t0))
print("share OOS PF>1:", round((out.pf_oos > 1).mean(), 2))
for col in ["rng", "last", "dir", "entry", "stop", "cap", "rr", "be", "maxtr"]:
    print("median by", col, out.groupby(col)[["tpd", "wr_is", "pf_is", "pf_oos", "Rday_is", "Rday_oos", "avg_2526"]].median().round(3).to_dict("index"))
sel = out[(out.rr <= 2.0)].sort_values("sh_is", ascending=False).head(30)
print("\nTOP 30 by IN-SAMPLE Sharpe (rr<=2):"); print(sel.to_string(index=False))
