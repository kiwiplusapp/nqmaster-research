import numpy as np, pandas as pd
from ict import load, day_levels
import timefill as tfm
def pf(s): return s[s>0].sum()/-s[s<=0].sum() if (s<=0).any() else 9
out={}
for n in ("nq_1m.npz","mnq_fut.npz"):
    d=load(n); L,atr,trend=day_levels(d); df=tfm.run(d,L,atr,trend,660,1,0.25,0.3,0)
    om=d["om"]; day=d["dayid"]; c=d["c"]; o=d["o"]; h=d["h"]; l=d["l"]; v=d["v"]
    rth=(om>=570)&(om<660)
    g=pd.DataFrame(dict(day=day[rth],o=o[rth],c=c[rth],h=h[rth],l=l[rth],tp=(h[rth]+l[rth]+c[rth])/3*np.maximum(v[rth],1e-9),v=np.maximum(v[rth],1e-9),date=d["date"][rth]))
    a=g.groupby("date").agg(o=("o","first"),c=("c","last"),h=("h","max"),l=("l","min"),tp=("tp","sum"),v=("v","sum"),day=("day","first"))
    a["vwap"]=a.tp/a.v; a["atr"]=atr[a.day]; a["trend"]=trend[a.day]
    a["move"]=(a.c-a.o)/a.atr; a["rng"]=(a.h-a.l)/a.atr; a["dir"]=np.sign(a.c-a.o)
    a["vw_agree"]=np.sign(a.c-a.vwap)==a.dir; a["with_trend"]=a.dir==a.trend
    a["pos_in_rng"]=np.where(a.dir>0,(a.c-a.l)/(a.h-a.l),(a.h-a.c)/(a.h-a.l))
    x=df.join(a,on="date",rsuffix="_f"); x["absmove"]=x.move.abs()
    out[n]=x
for f in ["absmove","rng","pos_in_rng"]:
    q=out["nq_1m.npz"].query("date<20240101")[f].quantile([.2,.4,.6,.8]).to_numpy()
    line=f"{f} q={np.round(q,2)}"
    for n,x in out.items():
        for nm,s in ((("IS",x[x.date<20240101]),("C24",x[x.date>=20240101])) if n=="nq_1m.npz" else (("FUT",x),)):
            b=np.digitize(s[f],q); line+=f" | {nm}: "+" ".join(f"{pf(s.usd[b==k]):.2f}" for k in range(5))
    print(line)
for f in ["vw_agree","with_trend"]:
    line=f
    for n,x in out.items():
        for nm,s in ((("IS",x[x.date<20240101]),("C24",x[x.date>=20240101])) if n=="nq_1m.npz" else (("FUT",x),)):
            line+=f" | {nm}: F {pf(s.usd[~s[f].astype(bool)]):.2f} T {pf(s.usd[s[f].astype(bool)]):.2f}"
    print(line)

print()
for n,x in out.items():
    for nm,s in ((("IS",x[x.date<20240101]),("C24",x[x.date>=20240101])) if n=="nq_1m.npz" else (("FUT",x),)):
        a=s[s.vw_agree.astype(bool)]
        print(f"{nm}: MOM11 all n{len(s)} wr{100*(s.usd>0).mean():.1f} pf{pf(s.usd):.2f} | vw_agree n{len(a)} ({100*len(a)/len(s):.0f}% days) wr{100*(a.usd>0).mean():.1f} pf{pf(a.usd):.2f} | by yr "+" ".join(f"{pf(g.usd):.2f}" for _,g in a.groupby(a.date//10000)))
