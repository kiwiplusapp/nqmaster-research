import itertools, time, numpy as np, pandas as pd
import engine as en, evalkit as ev
from common import Ctx
pd.set_option("display.width",260); pd.set_option("display.max_rows",300); pd.set_option("display.max_columns",40)
cx=Ctx(); o,h,l,c,om,dayid=cx.o,cx.h,cx.l,cx.c,cx.om,cx.dayid; nd=cx.nd
atr_d=cx.atr_daily()
L=np.load("data/levels.npy"); PDH,PDL=L[:,0],L[:,1]
def open_at(minute):
    a=np.full(nd,np.nan); w=np.where(om==minute)[0]; a[dayid[w]]=o[w]; return a
def rng(m0,m1):
    hi=np.full(nd,np.nan); lo=np.full(nd,np.nan)
    msk=(om>=m0)&(om<m1); s=pd.DataFrame({"d":dayid[msk],"h":h[msk],"l":l[msk]}).groupby("d").agg(h=("h","max"),l=("l","min"))
    hi[s.index.to_numpy()]=s.h.to_numpy(); lo[s.index.to_numpy()]=s.l.to_numpy(); return hi,lo
mid=open_at(0); o830=open_at(510); o930=open_at(570)
asia_hi,asia_lo=rng(1200,1440); lon_hi,lon_lo=rng(120,300)
sma20=pd.Series(cx.prev_close).rolling(20,min_periods=15).mean().to_numpy()
t20=np.nan_to_num(np.sign(cx.prev_close-sma20)).astype(np.int64)
prev_open=np.roll(o930,1); pdir=np.nan_to_num(np.sign(cx.prev_close-prev_open)).astype(np.int64)
BIAS={"none":np.zeros(nd,np.int64),"trend20":t20,"prevday":pdir}
S=lambda hhmm: ((hhmm//100)*60+hhmm%100-1080)%1440      # ET clock -> 18:00 session clock
VAR=[]
for ms in (200,700,930):
    for ee in (1100,1200): VAR.append(("Midnight open",mid,mid,PDH,PDL,ms,ee))
for ee in (1030,1130): VAR.append(("09:30 open",o930,o930,PDH,PDL,930,ee))
for ee in (1030,1130): VAR.append(("08:30 open",o830,o830,PDH,PDL,830,ee))
for ms in (200,700,930):
    for ee in (1100,1200): VAR.append(("Asia range",asia_hi,asia_lo,asia_hi,asia_lo,ms,ee))
for ms in (700,930):
    for ee in (1100,1200): VAR.append(("London range",lon_hi,lon_lo,lon_hi,lon_lo,ms,ee))
rows=[]; t0=time.time()
for (name,ru,rd,tu,tdn,ms,ee),km,trig,(bn,bias),rr in itertools.product(VAR,(0.0,0.05),(0,1,2),BIAS.items(),(1.0,2.0,0.0,-1.0)):
    r=en.sim_po3(o,h,l,c,om,dayid,ru,rd,atr_d,bias,S(ms),S(ee),S(ee),955,km,trig,2,0.3,0.02,rr,tu,tdn)
    df=ev.to_df(r,cx.d,"po3")
    if len(df)<60: continue
    def st(m):
        x=df.R[m]
        if len(x)==0: return (0,np.nan,np.nan)
        ls=-x[x<=0].sum(); return (len(x),round((x>0).mean()*100,1),round(x[x>0].sum()/ls,2) if ls>0 else np.nan)
    a=st(df.date<20240101); b=st((df.date>=20240101)&(df.date<20260101)); y=st(df.date>=20260101)
    rows.append(dict(variant=name,manip_from=ms,entry_until=ee,k_man=km,trigger=["reclaim","displacement","FVG"][trig],bias=bn,
                     target={1.0:"1R",2.0:"2R",0.0:"opp.liquidity",-1.0:"EOD"}[rr],n_20_23=a[0],wr_20_23=a[1],pf_20_23=a[2],
                     n_24_25=b[0],wr_24_25=b[1],pf_24_25=b[2],n_2026=y[0],wr_2026=y[1],pf_2026=y[2],stop=round(df.risk.mean(),1)))
out=pd.DataFrame(rows); out.to_csv("po3_scan.csv",index=False)
print("configs",len(out),"secs",round(time.time()-t0))
allpos=(out.pf_20_23>1)&(out.pf_24_25>1)&(out.pf_2026>1)
print("PF>1 in all 3 periods:",int(allpos.sum()),f"({allpos.mean()*100:.1f}%) | WR>=60 in all 3:",int(((out.wr_20_23>=60)&(out.wr_24_25>=60)&(out.wr_2026>=60)).sum()),
      "| WR>=60 & PF>1 all 3:",int((allpos&(out.wr_20_23>=60)&(out.wr_24_25>=60)&(out.wr_2026>=60)).sum()))
for col in ["variant","trigger","bias","target","k_man","manip_from"]:
    print("median by",col,out.groupby(col)[["wr_20_23","pf_20_23","pf_24_25","pf_2026"]].median().round(2).to_dict("index"))
print("\nTop by 2020-23 PF (then check later periods):")
print(out.sort_values("pf_20_23",ascending=False).head(20).to_string(index=False))
print("\nConfigs positive in all 3 periods:")
print(out[allpos].sort_values("pf_24_25",ascending=False).head(20).to_string(index=False))
