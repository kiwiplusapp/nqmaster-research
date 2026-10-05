import numpy as np, pandas as pd
import engine as en, evalkit as ev
from common import Ctx, SPLIT
from nt_v2_replica import run as run_v2
pd.set_option("display.width",250)
cx=Ctx(); o,h,l,c,v,om,dayid=cx.o,cx.h,cx.l,cx.c,cx.v,cx.om,cx.dayid; nd=cx.nd
atr_d=cx.atr_daily()
pcs=pd.Series(cx.prev_close); s50=pcs.rolling(50,min_periods=40).mean().to_numpy()
up50=np.where(np.nan_to_num(cx.prev_close-s50,nan=-1)>0,1,0).astype(np.int64)
ones=np.ones(nd,np.int64)
def sized(df,risk,cap):
    per=(df.risk+0.25)*2+1.0
    q=np.floor(risk/per); q=np.where((q<1)&(per<=cap),1,q); q=np.minimum(q,20)
    s=df.assign(qty=q,usd=q*(df.pnl_pts*2-1.0)); return s[s.qty>=1]
def modules(risk,cap):
    M={}
    v2=run_v2(cx,risk_usd=risk,one_lot_cap=cap,orb_rr=2.0,vw_rr=2.0)
    M["ORB+VWAP"]=v2[["date","usd"]]
    M["RTHlong"]=sized(ev.to_df(en.sim_window_hold(o,h,l,c,om,dayid,atr_d,ones,570,955,0.2,0.0,1),cx.d,"r"),risk,cap)[["date","usd"]]
    M["Night"]=sized(ev.to_df(en.sim_window_hold(o,h,l,c,om,dayid,atr_d,up50,1080,480,0.3,0.0,0),cx.d,"n"),risk,cap)[["date","usd"]]
    return M
def daily(M,keys):
    return pd.concat([M[k].groupby("date").usd.sum().rename(k) for k in keys],axis=1).reindex(cx.rth_days).fillna(0).sum(axis=1)
def mc_dd(d,n=10000,block=20,horizon=250,seed=1):
    rng=np.random.default_rng(seed); x=d.to_numpy(); L=len(x); dds=np.empty(n)
    for k in range(n):
        idx=np.concatenate([np.arange(s,s+block)%L for s in rng.integers(0,L,horizon//block+1)])[:horizon]
        eq=np.cumsum(x[idx]); dds[k]=np.max(np.maximum.accumulate(np.r_[0,eq])[1:]-eq)
    return np.percentile(dds,[50,95,99])
risk,cap=100,200
M=modules(risk,cap)
print(f"=== sizing: ${risk} per trade (1 MNQ min up to ${cap}) ===")
for keys in (["ORB+VWAP"],["ORB+VWAP","RTHlong"],["ORB+VWAP","RTHlong","Night"]):
    d=daily(M,keys); yr=d.groupby(d.index//10000).sum().round(0)
    sh=d.mean()/d.std()*np.sqrt(252); eq=d.cumsum(); dd=(eq.cummax()-eq).max()
    p50,p95,p99=mc_dd(d)
    print("+".join(keys))
    print(f"   $/day {d.mean():.1f} | $/year {d.mean()*252:.0f} | Sharpe {sh:.2f} | green days {(d>0).mean()*100:.0f}% | worst day {d.min():.0f} | hist maxDD {dd:.0f}")
    print(f"   Monte-Carlo 1-year maxDD: median {p50:.0f}, 95% {p95:.0f}, 99% {p99:.0f}")
    print(f"   by year: {yr.to_dict()}")
