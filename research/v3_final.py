import itertools, numpy as np, pandas as pd
from common import Ctx
from nt_v3_replica import run, metrics
pd.set_option("display.width",250); pd.set_option("display.max_columns",30)
cx=Ctx(); D=cx.rth_days
W2=D[(D>=20240925)&(D<=20260925)]; IS=W2[W2<20260126]; OOS=W2[W2>=20260126]
# ---- chosen default: stable across IS/OOS, partial exits ----
cfg=dict(orb_cap=0.25,vw_stop=0.25,range_min=60,t1_r=1.0,t1_frac=0.5,t2_r=2.0,contracts=2,dll=600.0,dpt=0.0,max_trades_day=10,max_consec_losses=2)
df=run(cx,**cfg); df=df[df.date.isin(W2)]
for lab,days in (("IN-SAMPLE Sep24-Jan26",IS),("OUT-OF-SAMPLE Feb26-Sep26",OOS),("FULL 2 YEARS",W2)):
    print(lab, metrics(df[df.date.isin(days)],days))
m=df.assign(month=df.date//100).groupby("month").agg(trades=("usd","size"),winrate=("usd",lambda x: round((x>0).mean()*100,1)),net_usd=("usd","sum"))
print(m.round(0).T.to_string())
print("by module:",df.groupby("mod").agg(n=("usd","size"),wr=("usd",lambda x: round((x>0).mean()*100,1)),pf=("usd",lambda x: round(x[x>0].sum()/-x[x<=0].sum(),2))).to_dict("index"))
print("exit reasons:",df.reason.value_counts().to_dict(),"| TP1 hit rate:",round(df.t1_hit.mean()*100,1))
df.to_pickle("v3_final_trades.pkl")
# ---- walk-forward: every 4 months pick the best of the 72-config grid by trailing-12-month PF, trade the next 4 months ----
grid=[]
exits=[("2R",dict(t1_frac=0.0,t2_r=2.0)),("1R",dict(t1_frac=0.0,t2_r=1.0)),("0.5R",dict(t1_frac=0.0,t2_r=0.5))]+[(f"{a}/{b}",dict(t1_r=a,t1_frac=0.5,t2_r=b)) for a,b in itertools.product((0.5,0.75,1.0),(1.5,2.0,3.0))]
for (en,ep),cap,rm in itertools.product(exits,(0.15,0.20,0.25),(45,60)):
    t=run(cx,orb_cap=cap,vw_stop=cap,range_min=rm,contracts=2,**ep); grid.append(((en,cap,rm),t))
starts=[20250126,20250526,20250926,20260126,20260526]
ends=[20250526,20250926,20260126,20260526,20260926]
wf=[]
for s,e in zip(starts,ends):
    trainD=D[(D>=s-10000)&(D<s)]; testD=D[(D>=s)&(D<e)]
    best=None;bp=-1
    for key,t in grid:
        tt=t[t.date.isin(trainD)]; loss=-tt.usd[tt.usd<=0].sum()
        pf=tt.usd[tt.usd>0].sum()/loss if loss>0 else 0
        if pf>bp: bp=pf;best=(key,t)
    key,t=best; tt=t[t.date.isin(testD)]
    wf.append(tt); print(f"WF test {s}-{e}: chosen {key} (train PF {bp:.2f}) -> test",metrics(tt,testD))
allwf=pd.concat(wf); print("WALK-FORWARD combined (Jan25-Sep26):",metrics(allwf,D[(D>=20250126)&(D<20260926)]))
