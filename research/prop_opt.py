import numpy as np, pandas as pd
import engine as en, evalkit as ev
from common import Ctx, SPLIT
pd.set_option("display.width",250); pd.set_option("display.max_rows",200)
cx=Ctx(); o,h,l,c,om,dayid=cx.o,cx.h,cx.l,cx.c,cx.om,cx.dayid; nd=cx.nd
atr_d=cx.atr_daily(); ok=np.ones(nd,np.bool_)
sma20=pd.Series(cx.prev_close).rolling(20,min_periods=15).mean().to_numpy()
t20=np.nan_to_num(np.sign(cx.prev_close-sma20)).astype(np.int64)
open930=np.full(nd,np.nan); m=cx.open_idx>=0; open930[m]=o[cx.open_idx[m]]
gapw=(np.nan_to_num(np.sign(open930-cx.prev_close)).astype(np.int64)==t20)
def eval_window(s, days, target=3000, dd=2000, max_days=60):
    dates=np.asarray(days); td=s.date.to_numpy(); v=s.usd.to_numpy(); fi=np.searchsorted(td,dates)
    res=[]
    for si,sd in enumerate(dates[:-max_days]):
        k=fi[si]; eq=0; pk=0; out="timeout"; end=dates[si+max_days-1]
        while k<len(v) and td[k]<=end:
            eq+=v[k]; pk=max(pk,eq); fl=min(max(-dd,pk-dd),0)
            if eq<=fl: out="fail"; break
            if eq>=target: out="pass"; break
            k+=1
        res.append(out)
    r=pd.Series(res); return round((r=="pass").mean()*100,1), round((r=="fail").mean()*100,1)
cfgs={"A rr4 cap.2 1/d":(0.2,4.0,1,ok),"B rr2 cap.2 2/d":(0.2,2.0,2,ok),"C rr1.5 cap.3 2/d":(0.3,1.5,2,ok),"D C+gap":(0.3,1.5,2,gapw),"E B+gap":(0.2,2.0,2,gapw)}
rows=[]
for k,(cap,rr,mt,f) in cfgs.items():
    r=en.sim_range(o,h,l,c,om,dayid,cx.open_idx,atr_d,570,60,780,955,t20,0,0,0,cap,rr,0.0,mt,30,f.astype(np.bool_))
    df=ev.to_df(r,cx.d,k); per=(df.risk+0.25)*2+1.0
    for risk in (100,200,300,400,500):
        q=np.floor(risk/per); q=np.where((q<1)&(per<=risk*2),1,q); q=np.minimum(q,20)
        s=df.assign(qty=q,usd=q*(df.pnl_pts*2-1.0)); s=s[s.qty>=1]
        p_all,f_all=eval_window(s,cx.rth_days)
        p_oos,f_oos=eval_window(s[s.date>=SPLIT],cx.rth_days[cx.rth_days>=SPLIT])
        p_rec,f_rec=eval_window(s[s.date>=20250101],cx.rth_days[cx.rth_days>=20250101])
        rows.append(dict(cfg=k,risk=risk,wr=round((df.R>0).mean()*100,1),trades_per_week=round(len(s)/len(cx.rth_days)*5,1),
                         pass60_all=p_all,fail60_all=f_all,pass60_2024_26=p_oos,fail60_2024_26=f_oos,pass60_2025_26=p_rec,fail60_2025_26=f_rec))
t=pd.DataFrame(rows); print(t.to_string(index=False)); t.to_csv("prop_opt.csv",index=False)
