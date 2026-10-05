import numpy as np, pandas as pd
TR = pd.read_pickle("timeline_mnq_fut.pkl"); TR = TR[(TR.date >= 20240201) & (~TR.fomc)]
days = np.array(sorted(pd.read_pickle("timeline_mnq_fut.pkl").query("date>=20240201").date.unique()))
def pf(u): return u[u > 0].sum() / -u[u <= 0].sum()
def block(lo, hi, lab):
    s = TR[(TR.date >= lo) & (TR.date <= hi)]; dd = days[(days >= lo) & (days <= hi)]
    d = s.groupby("date").usd.sum().reindex(dd, fill_value=0.0)
    eq = d.cumsum(); mdd = (eq.cummax() - eq).max()
    print(f"\n### {lab}: {len(dd)} sessions | trades {len(s)} = {len(s)/len(dd):.2f}/day | WR {100*(s.usd>0).mean():.1f}% | PF {pf(s.usd):.2f} | net ${s.usd.sum():,.0f} | maxDD ${mdd:,.0f} | green days {100*(d[d!=0]>0).mean():.0f}% | best ${d.max():,.0f} worst ${d.min():,.0f}")
    return s, d
block(20240201, 20991231, "2024-02 -> 2026-09 (real MNQ + MGC, v8)")
s26, d26 = block(20260101, 20991231, "2026 YTD")
m = s26.assign(m=s26.date // 100).groupby("m").agg(trades=("usd", "size"), net=("usd", "sum"))
print("   2026 by month:", " | ".join(f"{k%100:02d}: {r.trades} tr ${r.net:,.0f}" for k, r in m.iterrows()))
sm, dm = block(20260828, 20260928, "LAST MONTH 28-Aug -> 28-Sep-2026")
print("   trades per module last month:", sm.groupby("mod").size().to_dict())
print("   trades per day last month:", " ".join(f"{str(k)[4:6]}/{str(k)[6:]}:{v}" for k, v in sm.groupby("date").size().reindex(days[(days>=20260828)&(days<=20260928)], fill_value=0).items()))
print("   module stats 2024-26:"); print(TR.groupby("mod").usd.agg(trades="size", per_day=lambda u: round(len(u)/len(days), 2), wr=lambda u: round(100*(u>0).mean(), 1), pf=pf, net="sum").round(2).to_string())
# ---- business simulation on Topstep 50K, 1 contract per module, sequential lifecycle over real 2024-26
x = TR.groupby("date").usd.sum().reindex(days, fill_value=0.0).to_numpy()
FEE_MONTH, ACTIVATION = 49.0, 149.0   # assumption: combine subscription per month and XFA activation fee
def lifecycle(start, scale=1.0):
    i = start; cash = 0.0; fees = 0.0; passes = 0; busts_xfa = 0; busts_eval = 0; payouts = 0
    while i < len(x):
        # combine
        eq = pk = best = 0.0; d0 = i; ok = None
        while i < len(x):
            v = x[i] * scale; eq += v; best = max(best, v); pk = max(pk, eq); i += 1
            if (i - d0) % 21 == 1: fees += FEE_MONTH
            if eq <= pk - 2000: ok = False; break
            if eq >= max(3000, 2 * best): ok = True; break
        if ok is None: break
        if not ok: busts_eval += 1; continue
        passes += 1; fees += ACTIVATION
        bal = pk = 0.0; mll = -2000.0; wins = 0
        while i < len(x):
            v = x[i] * scale; bal += v; i += 1
            if bal <= mll: busts_xfa += 1; break
            pk = max(pk, bal); mll = min(0.0, max(mll, pk - 2000))
            if v >= 150: wins += 1
            if wins >= 5 and bal > 2000:
                req = min(0.5 * bal, 5000, bal - 2000)
                if req > 0: bal -= req; cash += 0.9 * req; payouts += 1; wins = 0
    months = (len(x) - start) / 21
    return cash, fees, months, passes, busts_eval, busts_xfa, payouts
res = [lifecycle(s) for s in range(0, len(x) - 120, 5)]
cash = np.array([r[0] for r in res]); fees = np.array([r[1] for r in res]); months = np.array([r[2] for r in res])
net_m = (cash - fees) / months
print(f"\n### Topstep 50K lifecycle (1 contract/module, starting on different dates 2024-26): net to you per month: median ${np.median(net_m):,.0f}, 25% ${np.percentile(net_m,25):,.0f}, 75% ${np.percentile(net_m,75):,.0f}")
print(f"    avg evals passed {np.mean([r[3] for r in res]):.1f}, eval busts {np.mean([r[4] for r in res]):.1f}, funded busts {np.mean([r[5] for r in res]):.1f}, payouts {np.mean([r[6] for r in res]):.1f} over avg {months.mean():.0f} months")
