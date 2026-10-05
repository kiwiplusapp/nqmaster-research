import numpy as np, pandas as pd
TR = pd.read_pickle("trades_real_all.pkl")
def pf(s): return s[s > 0].sum() / -s[s <= 0].sum()
def sized(tr, risk_usd, minc=1, maxc=50):
    n = np.floor(risk_usd / (tr.risk * 2.0)).clip(lower=minc, upper=maxc)
    return tr.assign(n=n, usd=n * (tr.pts * 2.0 - 1.0))
days_all = np.array(sorted(pd.read_pickle("daily_mats2.pkl")[1].index))
def summary(tr, lo, hi, label):
    s = tr[(tr.date >= lo) & (tr.date <= hi)]
    days = days_all[(days_all >= lo) & (days_all <= hi)]
    daily = s.groupby("date").usd.sum().reindex(days, fill_value=0.0)
    eq = daily.cumsum(); dd = (eq.cummax() - eq).max()
    print(f"\n### {label}: {len(days)} trading days | trades {len(s)} ({len(s)/len(days):.1f}/day) | WR {100*(s.usd>0).mean():.1f}% | PF {pf(s.usd):.2f} | NET ${s.usd.sum():,.0f} | max DD ${dd:,.0f} | best day ${daily.max():,.0f} | worst day ${daily.min():,.0f} | green days {100*(daily[daily!=0]>0).mean():.0f}% | avg contracts {s.n.mean():.1f}")
    return daily
def combine(daily, T=3000, D=2000, maxdays=400):
    x = daily.to_numpy(); res = []
    for st in range(len(x)):
        eq = 0.0; pk = 0.0; best = 0.0; r = None
        for k in range(st, min(len(x), st + maxdays)):
            eq += x[k]; best = max(best, x[k]); pk = max(pk, eq)
            if eq <= pk - D: r = ("bust", k - st + 1); break
            if eq >= max(T, 2 * best): r = ("pass", k - st + 1); break
        res.append(r)
    return res
for R in (250,):
    tr = sized(TR, R)
    d26 = summary(tr, 20260101, 20261231, f"2026 YTD, risk ${R}/trade (0.5% of 50K)")
    m = tr[tr.date >= 20260101].assign(m=lambda z: z.date // 100).groupby("m").usd.sum().round(0)
    print("   monthly:", " | ".join(f"{k%100:02d}: ${v:,.0f}" for k, v in m.items()))
    print("   by module 2026:"); s = tr[tr.date >= 20260101]
    print(s.groupby("mod").usd.agg(trades="size", wr=lambda u: round(100 * (u > 0).mean(), 1), pf=pf, net="sum").round(2).to_string())
    dm = summary(tr, 20260828, 20260928, "LAST MONTH (28-Aug -> 28-Sep 2026)")
    print("   daily:", " ".join(f"{str(k)[4:6]}/{str(k)[6:]}:{v:+.0f}" for k, v in dm.items()))
    for lab, lo in (("2026", 20260101), ("2024-2026", 20240201)):
        dd_ = tr[tr.date >= lo].groupby("date").usd.sum().reindex(days_all[days_all >= lo], fill_value=0.0)
        res = combine(dd_)
        ok = [r for r in res if r]; p = [r[1] for r in ok if r[0] == "pass"]; b = [r for r in ok if r[0] == "bust"]
        print(f"\n   Topstep 50K Combine started each day of {lab}: PASS {100*len(p)/len(res):.0f}% | BUST {100*len(b)/len(res):.0f}% | unfinished {100*(len(res)-len(ok))/len(res):.0f}% | days to pass median {np.median(p):.0f} (25%: {np.percentile(p,25):.0f}, 75%: {np.percentile(p,75):.0f})")

print("\n==== Combine speed vs risk per trade (starts in 2026 / 2024-26) ====")
for R in (250, 375, 500, 750):
    tr = sized(TR, R); line = f"risk ${R}:"
    for lab, lo in (("2026", 20260101), ("24-26", 20240201)):
        dd_ = tr[tr.date >= lo].groupby("date").usd.sum().reindex(days_all[days_all >= lo], fill_value=0.0)
        res = combine(dd_); ok = [r for r in res if r]; p = [r[1] for r in ok if r[0] == "pass"]; b = [r for r in ok if r[0] == "bust"]
        p20 = sum(1 for r in ok if r[0] == "pass" and r[1] <= 20)
        line += f" | {lab}: pass {100*len(p)/len(res):.0f}% bust {100*len(b)/len(res):.0f}% median {np.median(p):.0f}d, pass<=20d {100*p20/len(res):.0f}%"
    print(line)

print("\n==== Funded XFA 2026 simulation (start 02-Jan, risk $250, MLL $2,000 EOD trailing, locks at 0) ====")
tr = sized(TR, 250)
d = tr[tr.date >= 20260101].groupby("date").usd.sum().reindex(days_all[days_all >= 20260101], fill_value=0.0)
bal = 0.0; peak = 0.0; mll = -2000.0; wins = 0; paid = 0.0; npay = 0; alive = True
for dt, x in d.items():
    bal += x
    if bal <= mll: alive = False; print("  BUSTED on", dt); break
    peak = max(peak, bal); mll = min(0.0, max(mll, peak - 2000.0))
    if x >= 150: wins += 1
    if wins >= 5 and bal > 0:
        req = min(0.5 * bal, 5000.0); bal -= req; paid += 0.9 * req; npay += 1; wins = 0
        peak = bal
print(f"  alive={alive} | payouts {npay} | cash to trader ${paid:,.0f} | remaining balance ${bal:,.0f}")
