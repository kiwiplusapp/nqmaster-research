import itertools, time, numpy as np, pandas as pd
import evalkit as ev
from common import Ctx
from smc import confirmed_pivots, htf_pda_flags, sim_smc
from miner import resample
pd.set_option("display.width",260); pd.set_option("display.max_rows",300); pd.set_option("display.max_columns",40)
cx=Ctx(); o,h,l,c,v,om,dayid=cx.o,cx.h,cx.l,cx.c,cx.v,cx.om,cx.dayid
L=np.load("data/levels.npy")
sl_p,sl_b,sh_p,sh_b=confirmed_pivots(h,l,3)
H=resample(cx,60)
inBull,inBear=htf_pda_flags(h,l,cx.d["epoch"]+1,H["h"],H["l"],H["end_ep"])
cm=om+1
def win(a,b): return (cm>=a)&(cm<=b)
macro=win(530,550)|win(590,610)|win(650,670)|win(710,730)|win(790,820)|win(890,910)
ATRD=cx.atr_daily()
avgv=pd.Series(v).shift(1).rolling(20,min_periods=10).mean().to_numpy()
def run(**p):
    q=dict(sweep_s=570,sweep_e=900,entry_e=910,setup_bars=30,ifvg_bars=10,use_disp=False,disp_k=1.0,body_min=0.5,use_vol=False,vol_k=1.5,
           use_macro=False,pda_mode=0,entry_mode=0,retest_bars=10,tgt_mode=0,rr=2.0,min_rr=2.0,stop_buf=4,max_stop=1e9,max_trades=2,max_stop_atr=0.2,swing_liq=True,swing_age=60)
    q.update(p)
    r=sim_smc(o,h,l,c,v,om,dayid,cx.open_idx,L,cx.atr,avgv,sl_p,sl_b,sh_p,sh_b,inBull,inBear,macro,q["sweep_s"],q["sweep_e"],q["entry_e"],955,
              q["setup_bars"],q["ifvg_bars"],q["use_disp"],q["disp_k"],q["body_min"],q["use_vol"],q["vol_k"],q["use_macro"],q["pda_mode"],
              q["entry_mode"],q["retest_bars"],q["tgt_mode"],q["rr"],q["min_rr"],q["stop_buf"],q["max_stop"],q["max_trades"],ATRD,q["max_stop_atr"],q["swing_liq"],q["swing_age"])
    return ev.to_df(r,cx.d,"smc")
def st(df):
    out={}
    for lab,m in (("20-23",df.date<20240101),("24-25",(df.date>=20240101)&(df.date<20260101)),("2026",df.date>=20260101)):
        x=df.R[m]; ls=-x[x<=0].sum()
        out[f"n_{lab}"]=len(x); out[f"wr_{lab}"]=round((x>0).mean()*100,1) if len(x) else np.nan
        out[f"pf_{lab}"]=round(x[x>0].sum()/ls,2) if ls>0 else np.nan
    return out
if __name__=="__main__":
    t0=time.time()
    STEPS=[("1 base: sweep+MSS+IFVG",{}),
           ("2 +displacement",dict(use_disp=True)),
           ("3 +volume influx",dict(use_disp=True,use_vol=True)),
           ("4 +macro window",dict(use_disp=True,use_vol=True,use_macro=True)),
           ("5 +premium/discount",dict(use_disp=True,use_vol=True,use_macro=True,pda_mode=1)),
           ("6 +HTF 60m FVG (PDA)",dict(use_disp=True,use_vol=True,use_macro=True,pda_mode=3)),
           ("7 +clear targets (>=2R liq)",dict(use_disp=True,use_vol=True,use_macro=True,pda_mode=3,tgt_mode=1,min_rr=2.0))]
    rows=[]
    for (name,p),em in itertools.product(STEPS,(0,1)):
        df=run(entry_mode=em,**p); rows.append(dict(step=name,entry=["market","retest"][em],**st(df)))
    # single-filter ablation vs base (each filter alone)
    for (name,p),em in itertools.product([("only displacement",dict(use_disp=True)),("only volume",dict(use_vol=True)),("only macro",dict(use_macro=True)),
                                          ("only prem/disc",dict(pda_mode=1)),("only HTF FVG",dict(pda_mode=2)),("only clear targets",dict(tgt_mode=1))],(0,1)):
        df=run(entry_mode=em,**p); rows.append(dict(step=name,entry=["market","retest"][em],**st(df)))
    out=pd.DataFrame(rows); out.to_csv("smc_ablation.csv",index=False)
    print(out.to_string(index=False)); print("secs",round(time.time()-t0))
