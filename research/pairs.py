"""Intraday statistical arbitrage MNQ vs MES (RTH). Signals at bar close, fills at next bar open (1 tick slip per leg per side)."""
import itertools, numpy as np, pandas as pd
from numba import njit
from prep import load
pd.set_option("display.width",250); pd.set_option("display.max_rows",200)

nq=load("nq_hd.npz"); es=load("es_hd.npz")
def frame(z):
    return pd.DataFrame({"o":z["o"],"c":z["c"],"om":z["om"],"date":z["date"],"ep":z["epoch"]}).set_index("ep")
a=frame(nq); b=frame(es)
j=a.join(b,lsuffix="_nq",rsuffix="_es",how="inner")
j=j[(j.om_nq>=570)&(j.om_nq<960)]
j=j[j.date_nq==j.date_es]
print("aligned RTH bars", len(j))
onq=j.o_nq.to_numpy(); cnq=j.c_nq.to_numpy(); oes=j.o_es.to_numpy(); ces=j.c_es.to_numpy()
om=j.om_nq.to_numpy().astype(np.int64); date=j.date_nq.to_numpy().astype(np.int64)

@njit(cache=True)
def sim(onq,cnq,oes,ces,om,date,N,k_in,k_out,k_stop,max_hold,first_m,last_m,flat_m):
    n=len(cnq)
    out_pnl=np.zeros(n//5+10); out_date=np.zeros(n//5+10,np.int64); out_dir=np.zeros(n//5+10,np.int64); t=0
    pos=0; ei=0; qes=0.0; e_nq=0.0; e_es=0.0
    s=np.log(cnq)-np.log(ces)
    for i in range(N,n-1):
        if date[i]!=date[i-N]:
            if pos!=0 and date[i]!=date[ei]:
                pos=0
            continue
        w=s[i-N+1:i+1]
        mu=w.mean(); sd=w.std()
        if sd<=0: continue
        z=(s[i]-mu)/sd
        nxt=i+1
        if pos!=0:
            exit_now = (pos==1 and z>=-k_out) or (pos==-1 and z<=k_out) or abs(z)>=k_stop or (i-ei)>=max_hold or om[i]+1>=flat_m or date[nxt]!=date[i]
            if exit_now:
                x_nq=onq[nxt]; x_es=oes[nxt]
                if date[nxt]!=date[i]:
                    x_nq=cnq[i]; x_es=ces[i]
                # pos=+1: long spread = long NQ, short ES
                pnl = pos*((x_nq-e_nq)*2.0) - pos*((x_es-e_es)*5.0*qes)
                pnl -= (1.0 + 1.0*qes)           # commissions
                pnl -= 2*(0.25*2.0) + 2*(0.25*5.0*qes)   # 1 tick slippage per leg per side
                out_pnl[t]=pnl; out_date[t]=date[i]; out_dir[t]=pos; t+=1
                pos=0
            continue
        if om[i]+1<first_m or om[i]+1>last_m or date[nxt]!=date[i]:
            continue
        if z>=k_in: pos=-1
        elif z<=-k_in: pos=1
        if pos!=0:
            ei=nxt; e_nq=onq[nxt]; e_es=oes[nxt]
            qes=(e_nq*2.0)/(e_es*5.0)      # dollar-neutral hedge ratio (MES per 1 MNQ)
    return out_pnl[:t],out_date[:t],out_dir[:t]

rows=[]
for N,kin,kout,kst,mh in itertools.product((30,60,120),(2.0,2.5,3.0),(0.0,0.5),(4.0,5.0),(30,90)):
    p,d,_=sim(onq,cnq,oes,ces,om,date,N,kin,kout,kst,mh,600,930,955)
    if len(p)<200: continue
    df=pd.DataFrame({"pnl":p,"date":d})
    ins=df[df.date<20240101]; oos=df[df.date>=20240101]
    pf=lambda x: round(x[x>0].sum()/-x[x<0].sum(),2) if (x<0).any() else np.inf
    yr=df.groupby(df.date//10000).pnl.sum()
    rows.append(dict(N=N,k_in=kin,k_out=kout,k_stop=kst,max_hold=mh,n=len(df),tpd=round(len(df)/df.date.nunique(),1),wr=round((df.pnl>0).mean()*100,1),
                     avg_usd=round(df.pnl.mean(),2),pf_is=pf(ins.pnl),pf_oos=pf(oos.pnl),pos_years=int((yr>0).sum())))
out=pd.DataFrame(rows); out.to_csv("pairs_scan.csv",index=False)
print("configs",len(out),"| OOS PF>1:",round((out.pf_oos>1).mean(),2),"| WR>=65%:",int((out.wr>=65).sum()))
print(out.sort_values("pf_is",ascending=False).head(20).to_string(index=False))
