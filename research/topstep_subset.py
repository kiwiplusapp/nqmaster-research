import itertools, numpy as np, pandas as pd
exec(open("topstep_calc.py").read().split("for R in (250,):")[0])
tr = sized(TR, 250)
mods = sorted(tr["mod"].unique())
def daily(sub, lo, hi):
    s = tr[tr["mod"].isin(sub) & (tr.date >= lo) & (tr.date <= hi)]
    days = days_all[(days_all >= lo) & (days_all <= hi)]
    return s.groupby("date").usd.sum().reindex(days, fill_value=0.0)
def comb_stats(d):
    res = combine(d); ok = [r for r in res if r]; p = [r[1] for r in ok if r[0] == "pass"]; b = [r for r in ok if r[0] == "bust"]
    return 100 * len(p) / len(res), 100 * len(b) / len(res), (np.median(p) if p else np.nan)
def funded(d, cushion=2000):
    starts = [i for i in range(0, len(d) - 60, 21)]; surv = 0; cash = []
    x = d.to_numpy()
    for st in starts:
        bal = 0; peak = 0; mll = -2000; wins = 0; paid = 0; alive = True
        for k in range(st, min(len(x), st + 126)):
            bal += x[k]
            if bal <= mll: alive = False; break
            peak = max(peak, bal); mll = min(0.0, max(mll, peak - 2000))
            if x[k] >= 150: wins += 1
            if wins >= 5 and bal > cushion:
                req = min(0.5 * bal, 5000, bal - cushion)
                if req > 0: bal -= req; paid += 0.9 * req; wins = 0
        surv += alive; cash.append(paid)
    return 100 * surv / len(starts), np.mean(cash)
# choose subsets using 2024-2025 only (Sharpe of daily P&L), evaluate on 2026
rows = []
for r in range(3, 8):
    for sub in itertools.combinations(mods, r):
        d = daily(sub, 20240201, 20251231)
        sh = d.mean() / d.std() * np.sqrt(252); dd = (d.cumsum().cummax() - d.cumsum()).max()
        rows.append((sh, dd, sub))
rows.sort(reverse=True)
print("Top subsets by 2024-25 Sharpe, then tested on 2026:")
for sh, dd, sub in rows[:8]:
    d26 = daily(sub, 20260101, 20261231); dall = daily(sub, 20240201, 20261231)
    s26 = tr[tr["mod"].isin(sub) & (tr.date >= 20260101)]
    p, b, md = comb_stats(dall); p26, b26, md26 = comb_stats(d26); fs, fc = funded(dall)
    print(f"{'+'.join(sub)}\n   24-25 Sharpe {sh:.2f} DD ${dd:,.0f} | 2026: net ${d26.sum():,.0f} PF {pf(s26.usd):.2f} WR {100*(s26.usd>0).mean():.0f}% DD ${(d26.cumsum().cummax()-d26.cumsum()).max():,.0f} Sharpe {d26.mean()/d26.std()*np.sqrt(252):.2f}"
          f"\n   Combine pass/bust 24-26 {p:.0f}/{b:.0f} (median {md:.0f}d) | 2026 {p26:.0f}/{b26:.0f} (median {md26:.0f}d) | funded 6-month survival {fs:.0f}%, avg cash 6 months ${fc:,.0f}")
