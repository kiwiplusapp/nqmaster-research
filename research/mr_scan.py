import itertools, time, os
import numpy as np, pandas as pd
import engine as en, evalkit as ev
from common import Ctx, SPLIT
pd.set_option("display.width",260); pd.set_option("display.max_rows",300); pd.set_option("display.max_columns",40)
cx=Ctx(); o,h,l,c,v,om,dayid=cx.o,cx.h,cx.l,cx.c,cx.v,cx.om,cx.dayid; nd=cx.nd
atr_d=cx.atr_daily()
sma20=pd.Series(cx.prev_close).rolling(20,min_periods=15).mean().to_numpy()
t20=np.nan_to_num(np.sign(cx.prev_close-sma20)).astype(np.int64)
W={"NY 10:00-15:00":(570,600,900,955),"NY 10:30-14:30":(570,630,870,955),"Night 19:00-03:00":(1080,1140,180,240),"Night 20:00-08:00":(1080,1200,480,565)}
rows=[]; t0=time.time()
for (wn,(ss,fe,le,fl)),(am,rn),k,tf,sk,dm in itertools.product(W.items(),[(0,0),(1,60),(1,120)],(0.1,0.15,0.2,0.3),(0.5,1.0),(0.1,0.2,0.3),(0,1,2)):
    r=en.sim_meanrev(o,h,l,c,v,om,dayid,atr_d,t20,ss,fe,le,fl,am,max(rn,1),k,tf,sk,3,dm,True,5)
    df=ev.to_df(r,cx.d,"mr")
    if len(df)<150: continue
    a=ev.stats(df[df.date<SPLIT]); b=ev.stats(df[df.date>=SPLIT]); yr=df.groupby("year").R.sum()
    rows.append(dict(win=wn,anchor=["vwap","ma60","ma120"][0 if am==0 else (1 if rn==60 else 2)],k=k,tgt=tf,stop=sk,dir=["both","counter","with"][dm],
        tpd=round(len(df)/len(cx.rth_days),2),wr_is=a["wr"],wr_oos=b["wr"],avg_is=a["avg"],avg_oos=b["avg"],pf_is=a["pf"],pf_oos=b["pf"],pos_years=int((yr>0).sum()),risk=round(df.risk.mean(),1)))
out=pd.DataFrame(rows); out.to_csv("mr_scan.csv",index=False)
print("configs",len(out),"secs",round(time.time()-t0))
hi=out[(out.wr_is>=65)]
print("configs with IS WR>=65%:",len(hi),"| of those OOS PF>1:",int((hi.pf_oos>1).sum()),"| IS&OOS PF>1.1:",int(((hi.pf_is>1.1)&(hi.pf_oos>1.1)).sum()))
print("\nBest IS PF among WR>=65% (then check OOS):")
print(hi.sort_values("pf_is",ascending=False).head(25).to_string(index=False))
print("\nmedian PF by window/dir:"); print(out.groupby(["win","dir"])[["wr_is","pf_is","pf_oos"]].median().round(2).to_string())
