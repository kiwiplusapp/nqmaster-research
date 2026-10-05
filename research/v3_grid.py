import itertools, numpy as np, pandas as pd
from common import Ctx
from nt_v3_replica import run, metrics
pd.set_option("display.width",260); pd.set_option("display.max_rows",200); pd.set_option("display.max_columns",30)
cx=Ctx(); D=cx.rth_days
IS=D[(D>=20240925)&(D<20260126)]; OOS=D[(D>=20260126)&(D<=20260925)]
print("IS days",len(IS),IS[0],IS[-1],"| OOS days",len(OOS),OOS[0],OOS[-1])
rows=[]
exits=[("single 2R",dict(t1_frac=0.0,t2_r=2.0)),("single 1R",dict(t1_frac=0.0,t2_r=1.0)),("single 0.5R",dict(t1_frac=0.0,t2_r=0.5))]
for t1,t2 in itertools.product((0.5,0.75,1.0),(1.5,2.0,3.0)):
    exits.append((f"50% @{t1}R +BE, 50% @{t2}R",dict(t1_r=t1,t1_frac=0.5,t2_r=t2)))
for (ename,ep),cap,rm in itertools.product(exits,(0.15,0.20,0.25),(45,60)):
    df=run(cx,orb_cap=cap,vw_stop=cap,range_min=rm,**ep)
    a=metrics(df[df.date.isin(IS)],IS); b=metrics(df[df.date.isin(OOS)],OOS)
    rows.append(dict(exit=ename,stop_cap=cap,range_min=rm,**{f"IS_{k}":v for k,v in a.items() if k in("trades","winrate","pf","expectancy_R","max_dd_usd")},
                     **{f"OOS_{k}":v for k,v in b.items() if k in("trades","winrate","pf","expectancy_R","max_dd_usd")}))
out=pd.DataFrame(rows); out.to_csv("v3_grid.csv",index=False)
print(out.sort_values("IS_pf",ascending=False).to_string(index=False))
