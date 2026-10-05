"""When to START an evaluation. Daily P&L of the strategy has positive autocorrelation at weekly horizons (lag-5 0.10-0.14 on
2024-26). Condition the eval start on information known that morning: trailing N-day P&L of the strategy itself (sim account),
and the NQ daily-ATR regime (ATR / its 60-day median). Lucid Flex 50K, 1 contract; FULL (Ultra + gold WinRate) and the
cushion-gated policy (SAFE < 900 <= FULL, DL 700)."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_policy import vec, hiatr
from acct_policy3 import arrays, run_lucid3
pd.set_option("display.width", 250)
rows = []
for nm, cfgs, C1, C2, DL in (("FULL fijo", ("FULL", "FULL", "FULL"), 0, 0, 0.0), ("Ultra fijo", ("ULTRA", "ULTRA", "ULTRA"), 0, 0, 0.0), ("Gating 900 DL700", ("SAFE", "SAFE", "FULL"), 900, 900, 700.0)):
    for per in ("IS", "C24", "REAL"):
        lo, cl = arrays(per, cfgs, DL, 0.0); nd = lo.shape[1]
        daily = vec(per, "FULL", 0.0, 0.0)[1]                      # the strategy's own daily P&L (known up to yesterday)
        st = np.arange(60, nd - 120)
        res = np.array([run_lucid3(lo, cl, C1, C2, s) for s in st]); ok = res[:, 0] == 1; done = res[:, 0] != 0; days = res[:, 1]
        cs = np.r_[0, np.cumsum(daily)]
        ar = hiatr(per)
        for N in (5, 10, 20, 40):
            trail = cs[st] - cs[st - N]
            for lab, m in (("todas", np.ones(len(st), bool)), (f"últimos {N}d > 0", trail > 0), (f"últimos {N}d <= 0", trail <= 0)):
                if lab == "todas" and N != 5: continue
                rows.append(dict(pol=nm, per=per, cond=lab, n=int(m.sum()), pass_=round(100 * ok[m].sum() / max(done[m].sum(), 1), 1),
                                 p21=round(100 * (ok & (days <= 21))[m].mean(), 1), days=float(np.median(days[m & ok])) if (m & ok).any() else np.nan))
        a = ar[st]
        for lab, m in (("ATR bajo (<0.9 mediana)", a < 0.9), ("ATR normal", (a >= 0.9) & (a < 1.15)), ("ATR alto (>=1.15)", a >= 1.15)):
            rows.append(dict(pol=nm, per=per, cond=lab, n=int(m.sum()), pass_=round(100 * ok[m].sum() / max(done[m].sum(), 1), 1),
                             p21=round(100 * (ok & (days <= 21))[m].mean(), 1), days=float(np.median(days[m & ok])) if (m & ok).any() else np.nan))
R = pd.DataFrame(rows); R.to_csv("acct_timing.csv", index=False)
print(R.pivot_table(index=["pol", "cond"], columns="per", values=["pass_", "p21", "days"], aggfunc="first").to_string())
