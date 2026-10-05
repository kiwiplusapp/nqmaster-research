"""Stage 3: full reports for the robust candidates + a one-position-at-a-time portfolio."""
import numpy as np
import pandas as pd
import engine as en
import evalkit as ev
import propsim
from common import Ctx, SPLIT
from report import full_report

pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300); pd.set_option("display.max_columns", 40)

cx = Ctx()
o, h, l, c, v, om, dayid = cx.o, cx.h, cx.l, cx.c, cx.v, cx.om, cx.dayid
nd = cx.nd
atr_d = cx.atr_daily()
sma20 = pd.Series(cx.prev_close).rolling(20, min_periods=15).mean().to_numpy()
trend20 = np.nan_to_num(np.sign(cx.prev_close - sma20)).astype(np.int64)
all_true = np.ones(nd, np.bool_)

C = {}
C["ORB30 stop-order cap0.25 EOD"] = en.sim_orb2(o, h, l, c, om, dayid, cx.open_idx, atr_d, 30, 0, 3, 0.25, 0.0, 955, 720, cx.zero_dir, all_true, 0.0, 1, 0.0)
C["ORB30 stop-order cap0.25 EOD trend20"] = en.sim_orb2(o, h, l, c, om, dayid, cx.open_idx, atr_d, 30, 0, 3, 0.25, 0.0, 955, 720, trend20, all_true, 0.0, 1, 0.0)
C["ORB15 stop-order opp EOD trend20"] = en.sim_orb2(o, h, l, c, om, dayid, cx.open_idx, atr_d, 15, 0, 0, 0.0, 0.0, 955, 720, trend20, all_true, 0.0, 1, 0.0)
C["ORB15 stop-order cap0.15 rr3"] = en.sim_orb2(o, h, l, c, om, dayid, cx.open_idx, atr_d, 15, 0, 3, 0.15, 3.0, 955, 720, cx.zero_dir, all_true, 0.0, 1, 0.0)
C["FVG open 9:30-10 edge c1 rr3"] = en.sim_fvg_window(o, h, l, c, om, dayid, cx.open_idx, cx.atr, 570, 600, 0.3, 0, 0, 3.0, 955, 20, cx.zero_dir, 1)
sigma = cx.sigma()
C["NOISE chk30 hard0.5 vwap"] = en.sim_noise(o, h, l, c, v, om, cx.open_idx, cx.prev_close, sigma, 1.0, 30, 600, 930, 955, 0.5, 1, 0.0, cx.zero_dir)

dfs = {}
for name, res in C.items():
    df = ev.to_df(res, cx.d, name)
    dfs[name] = df
    full_report(name, df, cx, risks=(100, 200, 300))

# correlation of daily R between candidates
daily = pd.DataFrame({k: v.groupby("date").R.sum() for k, v in dfs.items()}).reindex(cx.rth_days).fillna(0)
print("\nDaily-R correlation")
print(daily.corr().round(2).to_string())
pd.to_pickle(dfs, "candidates.pkl")
