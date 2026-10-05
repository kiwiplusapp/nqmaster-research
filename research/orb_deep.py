"""Stage 2: ORB deep-dive. Selection is done on IN-SAMPLE only (2020-2023); OOS (2024-2026) is reported
for the IS-selected configs so we can measure honest degradation."""
import itertools
import time
import numpy as np
import pandas as pd
import engine as en
import evalkit as ev
from common import Ctx, SPLIT

pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300); pd.set_option("display.max_columns", 40)

cx = Ctx()
o, h, l, c, om, dayid = cx.o, cx.h, cx.l, cx.c, cx.om, cx.dayid
nd = cx.nd
atr_d = cx.atr_daily()

# ---- daily features known at 09:30 ----
open930 = np.full(nd, np.nan)
m = cx.open_idx >= 0
open930[m] = o[cx.open_idx[m]]
prev_open = np.roll(open930, 1); prev_open[0] = np.nan
sess_open = np.full(nd, np.nan)
first = np.r_[0, np.where(np.diff(dayid) != 0)[0] + 1]
sess_open[dayid[first]] = o[first]
closes = pd.Series(cx.prev_close)            # prev_close[dd] = close of day dd-1
sma20 = closes.rolling(20, min_periods=15).mean().to_numpy()

def sgn(x):
    return np.nan_to_num(np.sign(x)).astype(np.int64)

BIAS = {
    "none": cx.zero_dir,
    "trend20": sgn(cx.prev_close - sma20),
    "gap": sgn(open930 - cx.prev_close),
    "overnight": sgn(open930 - sess_open),
    "prevday": sgn(cx.prev_close - prev_open),
}

def or_range(or_len):
    r = np.full(nd, np.nan)
    for dd in range(nd):
        i0 = cx.open_idx[dd]
        if i0 < 0 or i0 + or_len >= len(c):
            continue
        r[dd] = h[i0:i0 + or_len].max() - l[i0:i0 + or_len].min()
    return r

ORR = {k: or_range(k) for k in (5, 15, 30)}
all_true = np.ones(nd, np.bool_)

rows = []
t0 = time.time()
grid = itertools.product((5, 15, 30), (0, 1), [(0, 0.0), (1, 0.0), (3, 0.15), (3, 0.25), (2, 0.2)],
                         (1.5, 2.0, 3.0, 0.0), (0.0, 1.0), tuple(BIAS), ("all", "or<=0.5"))
for or_len, em, (sm, sk), rr, be, bias, osz in grid:
    ok = all_true if osz == "all" else np.nan_to_num(ORR[or_len] / atr_d, nan=9.0) <= 0.5
    res = en.sim_orb2(o, h, l, c, om, dayid, cx.open_idx, atr_d, or_len, em, sm, sk, rr, 955, 720,
                      BIAS[bias], ok, be, 1, 0.0)
    df = ev.to_df(res, cx.d, "ORB")
    a = ev.stats(df[df.date < SPLIT]); b = ev.stats(df[df.date >= SPLIT])
    rows.append(dict(or_len=or_len, entry=["stop", "close"][em], stop=f"{['opp', 'mid', 'atr', 'cap'][sm]}{sk if sk else ''}",
                     rr=rr if rr else "EOD", be=be, bias=bias, orsz=osz,
                     n_is=a.get("n", 0), wr_is=a.get("wr"), avg_is=a.get("avg"), pf_is=a.get("pf"), tot_is=a.get("total"), dd_is=a.get("maxdd"), sh_is=a.get("sharpe"),
                     n_oos=b.get("n", 0), wr_oos=b.get("wr"), avg_oos=b.get("avg"), pf_oos=b.get("pf"), tot_oos=b.get("total"), dd_oos=b.get("maxdd"), sh_oos=b.get("sharpe"),
                     risk=round(df.risk.mean(), 1)))
print("configs", len(rows), "time", round(time.time() - t0, 1))
out = pd.DataFrame(rows)
out.to_csv("orb_deep.csv", index=False)

cand = out[(out.n_is >= 300)].copy()
cand["score_is"] = cand.sh_is
top = cand.sort_values("score_is", ascending=False).head(40)
print("\nTOP 40 BY IN-SAMPLE SHARPE (daily R), with their OUT-OF-SAMPLE results")
print(top.drop(columns=["score_is"]).to_string(index=False))
print("\nOOS summary of IS top-40: median PF", top.pf_oos.median(), "share OOS PF>1:", (top.pf_oos > 1).mean())
print("OOS summary of ALL configs: median PF", out.pf_oos.median(), "share OOS PF>1:", (out.pf_oos > 1).mean())
for col in ["or_len", "entry", "stop", "rr", "be", "bias", "orsz"]:
    g = out.groupby(col)[["pf_is", "pf_oos", "sh_is", "sh_oos"]].median().round(2)
    print("\nmedian by", col); print(g.to_string())
