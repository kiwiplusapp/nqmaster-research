import itertools, time
import numpy as np, pandas as pd
import engine as en
from y26 import *
pd.set_option("display.width",260); pd.set_option("display.max_rows",300); pd.set_option("display.max_columns",40)
o,h,l,c,om,dayid=cx.o,cx.h,cx.l,cx.c,cx.om,cx.dayid
L=np.load("data/levels.npy")
oi=cx.open_idx.copy(); oi[cx.dates<Y0]=-1          # only 2026 sessions
atr1=cx.atr
MASKS={"all":np.array([1,1,1,1,1,1,1,1],np.bool_),"PD":np.array([1,1,0,0,0,0,0,0],np.bool_),
       "ON":np.array([0,0,1,1,0,0,0,0],np.bool_),"PD+ON":np.array([1,1,1,1,0,0,0,0],np.bool_),
       "Lon+Asia":np.array([0,0,0,0,1,1,1,1],np.bool_)}
WIN={"9:30-11:00":(570,660),"9:30-12:00":(570,720),"10:00-11:30":(600,690),"9:30-10:30":(570,630)}
rows=[]; t0=time.time()
grid=itertools.product(WIN.items(),MASKS.items(),(15,30,60),(10,20,40),(0.0,0.5),(0.0,0.5),(0,1),(0,1),(1.0,1.5,2.0))
for (wn,(ws,we)),(mn,mk),slb,flb,mfa,bm,em,sm,rr in grid:
    r=en.sim_sweep_ifvg(o,h,l,c,om,dayid,oi,L,mk,atr1,ws,we,955,slb,flb,mfa,bm,em,15,sm,4 if sm==0 else 2,rr,60.0,0.0,2,0.0)
    df=t26(r)
    if len(df)<25: continue
    a=df[df.date<SPLIT]; b=df[df.date>=SPLIT]
    sa=stats(a); sb=stats(b)
    rows.append(dict(win=wn,lv=mn,slb=slb,flb=flb,mfa=mfa,body=bm,entry=["mkt","retest"][em],stop=["sweep","bar"][sm],rr=rr,
                     n_is=sa["n"],wr_is=sa["wr"],pf_is=sa["pf"],avg_is=sa["avg"],n_oos=sb["n"],wr_oos=sb["wr"],pf_oos=sb["pf"],avg_oos=sb["avg"],
                     stop_pts=round(df.risk.mean(),1)))
out=pd.DataFrame(rows); out.to_csv("scan26_ifvg.csv",index=False)
print("configs",len(out),"secs",round(time.time()-t0))
print("IS PF>1:",round((out.pf_is>1).mean(),2),"| OOS PF>1:",round((out.pf_oos>1).mean(),2),"| both>1:",round(((out.pf_is>1)&(out.pf_oos>1)).mean(),2))
print("WR>=70 IS:",int((out.wr_is>=70).sum()),"| WR>=70 both:",int(((out.wr_is>=70)&(out.wr_oos>=70)).sum()),"| WR>=70 both & PF>1 both:",int(((out.wr_is>=70)&(out.wr_oos>=70)&(out.pf_is>1)&(out.pf_oos>1)).sum()))
for col in ["win","lv","slb","flb","mfa","body","entry","stop","rr"]:
    print("median by",col,out.groupby(col)[["wr_is","pf_is","pf_oos","avg_oos"]].median().round(2).to_dict("index"))
print(out[out.n_is>=30].sort_values("pf_is",ascending=False).head(25).to_string(index=False))
