import itertools, numpy as np, pandas as pd
import engine as en, evalkit as ev
from common import Ctx
from nt_v2_replica import run as run_v2
from y26 import eval_prop
pd.set_option("display.width",260); pd.set_option("display.max_rows",300)
cx=Ctx(); o,h,l,c,v,om,dayid=cx.o,cx.h,cx.l,cx.c,cx.v,cx.om,cx.dayid; nd=cx.nd
atr_d=cx.atr_daily(); ones=np.ones(nd,np.int64)
pcs=pd.Series(cx.prev_close); s50=pcs.rolling(50,min_periods=40).mean().to_numpy()
up50=np.where(np.nan_to_num(cx.prev_close-s50,nan=-1)>0,1,0).astype(np.int64)
ALL=cx.rth_days; Y26=ALL[ALL>=20260101]
def sized(df,risk,cap):
    per=(df.risk+0.25)*2+1.0; q=np.floor(risk/per); q=np.where((q<1)&(per<=cap),1,q); q=np.minimum(q,40)
    s=df.assign(qty=q,usd=q*(df.pnl_pts*2-1.0)); return s[s.qty>=1][["date","exit_idx","usd"]]
def daily_caps(tr,loss_cap,profit_cap):
    if not loss_cap and not profit_cap: return tr
    tr=tr.sort_values(["date","exit_idx"]); keep=[]; cur=None; p=0; stop=False
    for d,u in zip(tr.date,tr.usd):
        if d!=cur: cur=d; p=0; stop=False
        if stop: keep.append(False); continue
        keep.append(True); p+=u
        if (loss_cap and p<=-loss_cap) or (profit_cap and p>=profit_cap): stop=True
    return tr[np.array(keep)]
rows=[]
for risk,cap in [(100,200),(150,250),(200,300),(300,400)]:
    v2=run_v2(cx,risk_usd=risk,one_lot_cap=cap,orb_rr=2.0,vw_rr=2.0)[["date","exit_idx","usd"]]
    drift=pd.concat([sized(ev.to_df(en.sim_window_hold(o,h,l,c,om,dayid,atr_d,ones,570,955,0.2,0.0,1),cx.d,"r"),risk,cap),
                     sized(ev.to_df(en.sim_window_hold(o,h,l,c,om,dayid,atr_d,up50,1080,480,0.3,0.0,0),cx.d,"n"),risk,cap)])
    for name,tr in [("ORB+VWAP",v2),("Portfolio",pd.concat([v2,drift]))]:
        for lc,pc in [(0,0),(400,0),(0,600),(400,600),(300,400)]:
            t=daily_caps(tr,lc,pc)
            for dd in (1200,1500):
                a=eval_prop(t,ALL,1500,dd,20); b=eval_prop(t,Y26,1500,dd,20)
                rows.append(dict(system=name,risk=risk,day_loss_cap=lc,day_profit_cap=pc,DD=dd,
                                 pass_2020_26=a["pass_"],fail_2020_26=a["fail"],pass_2026=b["pass_"],fail_2026=b["fail"],days_2026=b["days"]))
out=pd.DataFrame(rows); out.to_csv("eval25.csv",index=False)
print(out[out.DD==1200].sort_values("pass_2020_26",ascending=False).head(25).to_string(index=False))
print("\nDD=1500 best:"); print(out[out.DD==1500].sort_values("pass_2020_26",ascending=False).head(10).to_string(index=False))
