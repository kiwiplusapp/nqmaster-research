import sys, numpy as np, pandas as pd
import engine as en, evalkit as ev
from common import Ctx, SPLIT
pd.set_option("display.width",250)
cx=Ctx(); o,h,l,c,om,dayid=cx.o,cx.h,cx.l,cx.c,cx.om,cx.dayid; nd=cx.nd
atr_d=cx.atr_daily(); ok=np.ones(nd,np.bool_)
sma20=pd.Series(cx.prev_close).rolling(20,min_periods=15).mean().to_numpy()
t20=np.nan_to_num(np.sign(cx.prev_close-sma20)).astype(np.int64)
open930=np.full(nd,np.nan); m=cx.open_idx>=0; open930[m]=o[cx.open_idx[m]]
gapw=(np.nan_to_num(np.sign(open930-cx.prev_close)).astype(np.int64)==t20)
cfgs={"A: OR60 cap0.2 rr4 1/day (v1)":(0.2,4.0,1,ok),"B: OR60 cap0.2 rr2 2/day":(0.2,2.0,2,ok),"C: OR60 cap0.3 rr1.5 2/day":(0.3,1.5,2,ok),
      "D: C + gap-with-trend":(0.3,1.5,2,gapw),"E: B + gap-with-trend":(0.2,2.0,2,gapw)}
for k,(cap,rr,mt,f) in cfgs.items():
    r=en.sim_range(o,h,l,c,om,dayid,cx.open_idx,atr_d,570,60,780,955,t20,0,0,0,cap,rr,0.0,mt,30,f.astype(np.bool_))
    df=ev.to_df(r,cx.d,k); a=ev.stats(df[df.date<SPLIT]); b=ev.stats(df[df.date>=SPLIT]); yr=df.groupby("year").R.sum().round(1)
    print(f"{k:34s} n={len(df):4d} WR {ev.stats(df)['wr']}% PF {ev.stats(df)['pf']} | IS PF {a['pf']} OOS PF {b['pf']} | years {yr.to_dict()}")
