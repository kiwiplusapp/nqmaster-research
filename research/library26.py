"""Build a library of ~100 trade streams (2026 only) for walk-forward strategy rotation."""
import itertools, numpy as np, pandas as pd
import engine as en
from y26 import *
o,h,l,c,v,om,dayid=cx.o,cx.h,cx.l,cx.c,cx.v,cx.om,cx.dayid; nd=cx.nd
atr_d=cx.atr_daily(); ok=np.ones(nd,np.bool_); ones=np.ones(nd,np.int64)
sma20=pd.Series(cx.prev_close).rolling(20,min_periods=15).mean().to_numpy()
t20=np.nan_to_num(np.sign(cx.prev_close-sma20)).astype(np.int64)
L=np.load("data/levels.npy"); oi=cx.open_idx.copy(); oi[cx.dates<Y0]=-1
lib={}
for rl,dm,cap,rr in itertools.product((15,30,60),(0,1),(0.1,0.2),(1.0,2.0)):
    lib[f"ORB{rl} {['trend','both'][dm]} cap{cap} {rr}R"]=t26(en.sim_range(o,h,l,c,om,dayid,cx.open_idx,atr_d,570,rl,780,955,t20,dm,0,0,cap,rr,0.0,2,30,ok))
for ext,sk,rr in itertools.product((0.05,0.1),(0.1,0.2),(1.0,2.0)):
    lib[f"VWAPpb ext{ext} stop{sk} {rr}R"]=t26(en.sim_vwap_pullback(o,h,l,c,v,om,dayid,cx.open_idx,atr_d,t20,60,630,870,955,ext,sk,rr,1,True))
for (wn,ss,fe,le),k,tf,sk in itertools.product([("NY",570,600,900),("Mid",570,690,840)],(0.1,0.15,0.2),(0.5,1.0),(0.1,0.2)):
    lib[f"MR {wn} k{k} tgt{tf} stop{sk}"]=t26(en.sim_meanrev(o,h,l,c,v,om,dayid,atr_d,t20,ss,fe,le,955,0,1,k,tf,sk,3,0,True,5))
MK={"PD+ON":np.array([1,1,1,1,0,0,0,0],np.bool_),"all":np.ones(8,np.bool_),"Lon+Asia":np.array([0,0,0,0,1,1,1,1],np.bool_)}
for (mn,mk),em,rr,(ws,we) in itertools.product(MK.items(),(0,1),(1.0,2.0),[(570,660),(570,720)]):
    lib[f"SweepIFVG {mn} {['mkt','retest'][em]} {rr}R {ws}-{we}"]=t26(en.sim_sweep_ifvg(o,h,l,c,om,dayid,oi,L,mk,cx.atr,ws,we,955,30,20,0.0,0.5,em,15,0,4,rr,60.0,0.0,2,0.0))
for rr,mode,(ws,we) in itertools.product((1.0,2.0),(1,2),[(570,930),(570,690)]):
    s,ref,line,zt,zb,risk,gv,gr,gp=en.ifvg_signals(o,h,l,c,cx.atr,0.25,0.5,0.65,0.05,2,500,500,0 if mode==2 else 1,1.5,rr,20,True,False,1.5,50)
    lib[f"PineIFVG {['','mkt','limit'][mode]} {rr}R {ws}-{we}"]=t26(en.sim_ifvg(o,h,l,c,om,dayid,s,ref,risk,gv&gr&gp,rr,mode,ws,we,955,15,True,0.0,0.0))
lib["RTH long"]=t26(en.sim_window_hold(o,h,l,c,om,dayid,atr_d,ones,570,955,0.2,0.0,1))
lib["RTH short"]=t26(en.sim_window_hold(o,h,l,c,om,dayid,atr_d,ones,570,955,0.2,0.0,-1))
lib["RTH trend"]=t26(en.sim_window_hold(o,h,l,c,om,dayid,atr_d,t20,570,955,0.2,0.0,0))
lib["Night long"]=t26(en.sim_window_hold(o,h,l,c,om,dayid,atr_d,ones,1080,480,0.3,0.0,1))
sigma=cx.sigma()
for hs in (0.5,1.0):
    lib[f"Noise hard{hs}"]=t26(en.sim_noise(o,h,l,c,v,om,cx.open_idx,cx.prev_close,sigma,1.0,30,600,930,955,hs,1,0.0,cx.zero_dir))
lib={k:v for k,v in lib.items() if len(v)>=15}
pd.to_pickle(lib,"lib26.pkl")
print("streams:",len(lib))
