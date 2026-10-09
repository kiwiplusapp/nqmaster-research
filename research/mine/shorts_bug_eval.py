"""Blocked-shorts bug (NQMaster, 2026-10-07): NT Strategy Analyzer export vs research Ultra (same logic, no bug), before and after
2025-08-13. Lucid 50K evals on daily P&L, 2 contracts, EOD trailing $2,000, target $3,000, best day <= 50% of profit; every start day.
Usage (from research/mine): python shorts_bug_eval.py "<NT trades.csv>"
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, "..")
import nt_compare as C
csv = sys.argv[1]
R, _ = C.research_set("ultra"); N = C.nt_frame(csv, "America/Argentina/Buenos_Aires")
R["usd"] = R.u * R.w
days = sorted(set(R.date) | set(N.date))
def daily(df, col): return df.groupby("date")[col].sum().reindex(days, fill_value=0.0)
dn, dr = daily(N, "pnl"), daily(R, "usd")
def ev(pnl, k=2, T=3000.0, D=2000.0):
    x = k * pnl.to_numpy(); n = len(x); res = []
    for s in range(n):
        eq = pk = 0.0; best = -1e9; out = (0, n - s)
        for d in range(s, n):
            thr = 100.0 if pk >= D + 100 else pk - D
            eq += x[d]; best = max(best, x[d]); pk = max(pk, eq)
            if eq <= thr: out = (-1, d - s + 1); break
            if eq >= T and best <= 0.5 * eq: out = (1, d - s + 1); break
        res.append(out)
    return np.array(res)
def summ(name, pnl, lo, hi):
    idx = [i for i, d in enumerate(days) if lo <= d <= hi]
    r = ev(pnl)[idx[0]:idx[-1] + 1]
    fin = r[r[:, 0] != 0]; p = fin[:, 0] == 1
    print(f"{name:34s} starts {len(fin):4d} | pass {100*p.mean():5.1f}% | bust {100*(~p).mean():5.1f}% | median days to pass {np.median(fin[p,1]):4.0f} | <=15d {100*(p & (fin[:,1]<=15)).mean():5.1f}%")
for lbl, lo, hi in (("2024-01..2025-07 (shorts working)", 20240201, 20250731), ("2025-08-13..2026-09 (shorts blocked)", 20250813, 20260925)):
    print(lbl)
    summ("  NinjaTrader as run", dn, lo, hi)
    summ("  same logic without the bug", dr, lo, hi)
    for nm, x in (("NT", dn), ("research", dr)):
        sel = x[(x.index >= lo) & (x.index <= hi)]
        print(f"    {nm:9s} $/month (1 base contract) {sel.sum() / (len(sel) / 21):7.0f}")
print("\nWin rate / PF by period (per trade):")
for lbl, lo, hi in (("2024-02..2025-07", 20240201, 20250731), ("2025-08-13..2026-09", 20250813, 20260925)):
    for nm, df, col in (("NT", N, "u"), ("research", R, "u")):
        x = df[(df.date >= lo) & (df.date <= hi)][col].to_numpy()
        print(f"  {lbl} {nm:9s} n {len(x):4d} WR {100*(x>0).mean():5.1f}% PF {x[x>0].sum()/-x[x<=0].sum():.2f} shorts {(df[(df.date >= lo) & (df.date <= hi)].d == -1).sum()}")
