import numpy as np, pandas as pd
S = pd.read_pickle("pullday_streams.pkl")
exec(open("pullday.py").read().split("streams = {}")[0])
mseq = pd.read_pickle("wr60_A.pkl"); mseq["usd"] = mseq.pts * 2.0 - 1.0
TH = 0.44
parts = []
for k, (df) in {"orb60": S["orb60_0.6"], "vw60": S["vw60_0.6"], "orb30": S["orb30_0.75"], "orb15": S["orb15_0.75"], "vw30": S["vw30_0.75"]}.items():
    f = df[df.date.map(PR) < TH][["date", "usd", "exit_idx"]].copy(); parts.append(f)
m = mseq[["date", "usd"]].copy(); m["exit_idx"] = 10**12; parts.append(m)
P = pd.concat(parts).sort_values(["date", "exit_idx"])
days = np.array(cx.rth_days)

def day_pnl(scale, dll):
    out = {}
    for d, g in P.groupby("date"):
        run = 0.0
        for u in g.usd.to_numpy() * scale:
            if dll and run <= -dll: break
            run += u
        out[d] = run
    return pd.Series(out).reindex(days, fill_value=0.0)

def evalsim(daily, target, dd, maxdays):
    x = daily.to_numpy(); res = []; dys = []
    for s in range(len(x) - 5):
        eq = 0.0; peak = 0.0; ok = None
        for k in range(s, min(len(x), s + maxdays)):
            eq += x[k]; peak = max(peak, eq)
            if eq >= target: ok = True; dys.append(k - s + 1); break
            if eq <= peak - dd: ok = False; break
        res.append(ok)
    r = np.array([1 if v is True else (0 if v is False else -1) for v in res])
    return (r == 1).mean() * 100, (r == 0).mean() * 100, (np.median(dys) if dys else np.nan)

for scale in (1, 2):
    for dll in (0, 600, 1000):
        daily = day_pnl(scale, dll)
        eq = daily.cumsum(); mdd = (eq.cummax() - eq).max()
        wk = daily.groupby(pd.to_datetime(daily.index.astype(str)).to_period("W")).sum()
        line = f"x{scale} MNQ/module DLL {dll or 'off':>4} | net/yr ${daily.sum()/6.73:,.0f} | avg week ${wk.mean():,.0f} | weeks>0 {100*(wk>0).mean():.0f}% | maxDD ${mdd:,.0f}"
        for nm, T_, D_ in (("25K 1500/1500", 1500, 1500), ("50K 3000/2000", 3000, 2000), ("50K 3000/2500", 3000, 2500)):
            for md in (20, 60):
                p, f, med = evalsim(daily, T_, D_, md)
                line += f" | {nm} {md}d pass {p:.0f}% fail {f:.0f}% med {med:.0f}d"
        print(line)
