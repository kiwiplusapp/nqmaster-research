import numpy as np, pandas as pd
S = pd.read_pickle("pullday_streams.pkl")
exec(open("pullday.py").read().split("streams = {}")[0])
TH = 0.44
MODS = {"orb60": S["orb60_0.6"], "vw60": S["vw60_0.6"], "orb30": S["orb30_0.75"], "orb15": S["orb15_0.75"], "vw30": S["vw30_0.75"]}
parts = []
for k, df in MODS.items():
    f = df[df.date.map(PR) < TH].copy()
    f["t_in"] = cx.om[f.entry_idx.to_numpy()]; f["t_out"] = cx.om[f.exit_idx.to_numpy()] + 1; f["mod"] = k
    parts.append(f[["date", "usd", "t_in", "t_out", "mod"]])
m = pd.read_pickle("mseq_times.pkl"); m["mod"] = "mseq"; parts.append(m[["date", "usd", "t_in", "t_out", "mod"]])
P = pd.concat(parts).sort_values(["date", "t_in"]).reset_index(drop=True)
P.to_pickle("pullday_portfolio_trades.pkl")
days = np.array(cx.rth_days)

def apply_dll(scale, dll, maxpos=99):
    taken = []
    for d, g in P.groupby("date", sort=True):
        g = g.sort_values("t_in"); open_ = []; closed = []
        for r in g.itertuples():
            realized = sum(u for (t, u) in closed if t <= r.t_in) + sum(u for (t, u) in open_ if t <= r.t_in)
            if dll and realized <= -dll: continue
            if sum(1 for (t, u) in open_ if t > r.t_in) >= maxpos: continue
            open_.append((r.t_out, r.usd * scale)); taken.append((d, r.usd * scale, r.mod))
    return pd.DataFrame(taken, columns=["date", "usd", "mod"])

def evalsim(daily, target, dd, maxdays):
    x = daily.to_numpy(); ok_ = 0; bad = 0; dys = []
    N = len(x) - 5
    for s in range(N):
        eq = 0.0; peak = 0.0
        for k in range(s, min(len(x), s + maxdays)):
            eq += x[k]; peak = max(peak, eq)
            if eq >= target: ok_ += 1; dys.append(k - s + 1); break
            if eq <= peak - dd: bad += 1; break
    return 100 * ok_ / N, 100 * bad / N, (np.median(dys) if dys else np.nan)

for scale in (1, 2):
    for dll in (0, 500, 800):
        T_ = apply_dll(scale, dll)
        daily = T_.groupby("date").usd.sum().reindex(days, fill_value=0.0)
        eq = daily.cumsum(); mdd = (eq.cummax() - eq).max()
        wk = daily.groupby(pd.to_datetime(daily.index.astype(str)).to_period("W")).sum()
        u = T_.usd
        print(f"\nx{scale} DLL {dll or 'off'}: trades/wk {len(u)/350:.2f} WR {100*(u>0).mean():.1f}% PF {pf(u):.2f} | IS PF {pf(u[T_.date<20240101]):.2f} OOS PF {pf(u[T_.date>=20240101]):.2f} | net/yr ${daily.sum()/6.73:,.0f} avg wk ${wk.mean():,.0f} weeks>0 {100*(wk>0).mean():.0f}% maxDD ${mdd:,.0f} worst day ${daily.min():,.0f}")
        line = ""
        for nm, a, b in (("25K 1500/1500", 1500, 1500), ("50K 3000/2000", 3000, 2000), ("50K 3000/2500", 3000, 2500), ("100K 6000/3000", 6000, 3000)):
            for md in (20, 60):
                p, f, med = evalsim(daily, a, b, md)
                line += f"  {nm} {md}d: pass {p:.0f}% bust {f:.0f}% (med {med:.0f}d)\n"
        print(line, end="")
