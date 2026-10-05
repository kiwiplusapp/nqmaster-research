import itertools, numpy as np, pandas as pd
from y26 import *
pd.set_option("display.width",250); pd.set_option("display.max_rows",100)
lib=pd.read_pickle("lib26.pkl")
R=pd.DataFrame({k:v.groupby("date").R.sum() for k,v in lib.items()}).reindex(DAYS).fillna(0.0)
names=list(R.columns); X=R.to_numpy()
def run_meta(L,K,score,reb=5,start=None):
    n=len(DAYS); out=np.zeros(n); picks=[]
    first=max(L,start or L)
    for t in range(first,n,reb):
        past=X[t-L:t]
        if score=="sum": s=past.sum(0)
        else:
            sd=past.std(0); s=np.where(sd>0,past.mean(0)/sd,0)
        order=np.argsort(-s); sel=[i for i in order[:K] if s[i]>0]
        picks.append((DAYS[t],[names[i] for i in sel]))
        if sel: out[t:t+reb]=X[t:t+reb][:,sel].sum(1)
    return pd.Series(out,index=DAYS), picks, first
rows=[]
for L,K,sc in itertools.product((10,20,40,60),(1,3,5,10),("sum","sharpe")):
    s,p,first=run_meta(L,K,sc,start=60)          # common OOS start (day 60 ~ late March) for fair comparison
    live=s.iloc[60:]
    eq=live.cumsum(); dd=(eq.cummax()-eq).max()
    rows.append(dict(L=L,K=K,score=sc,totR=round(live.sum(),1),R_per_day=round(live.mean(),3),sharpe=round(live.mean()/live.std()*np.sqrt(252),2) if live.std()>0 else 0,maxdd_R=round(dd,1),green=round((live>0).mean()*100)))
out=pd.DataFrame(rows)
print("OOS window:",DAYS[60],"->",DAYS[-1],f"({len(DAYS)-60} days)")
print(out.sort_values("sharpe",ascending=False).to_string(index=False))
live_all=R.iloc[60:].mean(1)*10
print("\nbenchmark equal-weight all 93 streams (scaled x10): Sharpe",round(live_all.mean()/live_all.std()*np.sqrt(252),2),"totR",round(live_all.sum(),1))
print("share of meta configs with positive OOS:",round((out.totR>0).mean(),2),"| median Sharpe:",out.sharpe.median())
