import numpy as np, pandas as pd
exec(open("pullday.py").read().split("streams = {}")[0])   # reuse cx, PR, pf, summ
S = pd.read_pickle("pullday_streams.pkl")
mseq = pd.read_pickle("wr60_A.pkl"); mseq["usd"] = mseq.pts * 2.0 - 1.0; mseq["mod"] = "mseq"
TH = 0.44
pick = {"orb60": S["orb60_0.6"], "vw60": S["vw60_0.6"], "orb30": S["orb30_0.75"], "orb15": S["orb15_0.75"], "vw30": S["vw30_0.75"]}
parts = []
for k, df in pick.items():
    f = df[df.date.map(PR) < TH][["date", "usd"]].copy(); f["mod"] = k; parts.append(f)
core = pd.concat(parts)
m2 = mseq[["date", "usd", "mod"]]
m2f = m2[m2.date.map(PR) < TH]
summ(m2, "mseq (no pullday filter)"); summ(m2f, "mseq (pullday filter)")
for name, P in (("CORE 5 modules", core), ("CORE + MSEQ", pd.concat([core, m2])), ("CORE + MSEQ(filtered)", pd.concat([core, m2f]))):
    print(); summ(P, name)
    daily = P.groupby("date").usd.sum().reindex(cx.rth_days, fill_value=0.0)
    eq = daily.cumsum(); dd = (eq.cummax() - eq).max()
    tdays = (daily != 0)
    print(f"   net ${P.usd.sum():,.0f}  maxDD ${dd:,.0f}  worst day ${daily.min():,.0f}  best day ${daily.max():,.0f}  days traded {tdays.mean()*100:.0f}%  green days {100*(daily[tdays]>0).mean():.0f}%")
    for y in range(2020, 2027):
        s = P[P.date // 10000 == y].usd
        print(f"   {y}: n {len(s):4d}  wr {100*(s>0).mean():.1f}%  pf {pf(s):.2f}  net ${s.sum():,.0f}")
    pd.to_pickle(P, f"port_{name.replace(' ','_').replace('+','p').replace('(','').replace(')','')}.pkl")
