"""Final 1-contract protocols vs today's setup, with block-bootstrap 90% intervals of the pass-rate gain (blocks of 20 start days).
Eval (Lucid Flex 50K and Apex 50K EOD 30 days):
  BASE  : NQMaster Ultra, start any day
  E1    : NQMaster Ultra + gold WinRate, start only when NQ daily ATR < 1.15 x its 60-day median
  E2    : cushion gating (SAFE below $900 of cushion, FULL above) + own daily stop $700, start when ATR < 1.15 x median
Funded (Lucid, 12 months): BASE Ultra X=5000 vs F1 = SAFE always, request payout at >= $6,000."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_policy import hiatr
from acct_policy3 import arrays, run_lucid3, run_apex3, run_funded3
rng = np.random.default_rng(3); pd.set_option("display.width", 250)
EV = {"BASE Ultra (hoy)": (("ULTRA",) * 3, 0, 0, 0.0, False), "E1 Ultra+oro, ATR<1.15": (("FULL",) * 3, 0, 0, 0.0, True),
      "E2 gating+DL700, ATR<1.15": (("SAFE", "SAFE", "FULL"), 900, 900, 700.0, True)}
rows = []; RAW = {}
for per in ("IS", "C24", "REAL"):
    a = hiatr(per)
    for nm, (cfgs, C1, C2, DL, filt) in EV.items():
        lo, cl = arrays(per, cfgs, DL, 0.0); nd = lo.shape[1]; st = np.arange(60, nd - 120)
        r = np.array([run_lucid3(lo, cl, C1, C2, s) for s in st]); ap = np.array([run_apex3(lo, cl, C1, C2, s, 21) for s in st])
        m = (a[st] < 1.15) if filt else np.ones(len(st), bool)
        ok = (r[:, 0] == 1); RAW[(per, nm)] = (ok, r[:, 0] == -1, r[:, 1], ap[:, 0] == 1, m)
        rows.append(dict(per=per, prot=nm, starts=round(100 * m.mean()), L_pass=round(100 * ok[m].mean(), 1), L_bust=round(100 * (r[:, 0] == -1)[m].mean(), 1),
                         L_p21=round(100 * (ok & (r[:, 1] <= 21))[m].mean(), 1), L_days=float(np.median(r[m & ok, 1])), A_pass=round(100 * (ap[:, 0] == 1)[m].mean(), 1)))
R = pd.DataFrame(rows); print(R.to_string(index=False))
# bootstrap the pass-rate gain vs BASE (block resampling of start days)
print("\n90% interval of the Lucid pass-rate gain vs BASE (block bootstrap):")
for per in ("IS", "C24", "REAL"):
    okb, _, _, _, mb = RAW[(per, "BASE Ultra (hoy)")]; n = len(okb); nb = n // 20
    for nm in list(EV)[1:]:
        ok, _, _, _, m = RAW[(per, nm)]; g = []
        for _ in range(2000):
            idx = np.concatenate([np.arange(s, min(s + 20, n)) for s in rng.integers(0, n, nb)])
            g.append(100 * (ok[idx][m[idx]].mean() - okb[idx].mean()))
        print(f"  {per:4s} {nm:28s} gain {np.mean(g):+5.1f} pts  [{np.percentile(g, 5):+5.1f}, {np.percentile(g, 95):+5.1f}]")
# funded
FU = {"BASE Ultra, cobro a $5k": (("ULTRA",) * 3, 0, 0, 5000.0), "F1 SAFE, cobro a $6k": (("SAFE",) * 3, 0, 0, 6000.0), "F2 SAFE<1500<=NOB, cobro a $6k": (("SAFE", "NOB", "NOB"), 1500, 1500, 6000.0)}
rows = []
for per in ("IS", "C24", "REAL"):
    for nm, (cfgs, C1, C2, X) in FU.items():
        lo, cl = arrays(per, cfgs, 0.0, 0.0); nd = lo.shape[1]
        f = np.array([run_funded3(lo, cl, C1, C2, s, s + 252, X) for s in range(nd - 252)])
        rows.append(dict(per=per, prot=nm, bust=round(100 * (f[:, 2] == -1).mean(), 1), cash=round(f[:, 0].mean()), payouts=round(f[:, 1].mean(), 2), all5=round(100 * (f[:, 1] == 5).mean(), 1)))
print(); print(pd.DataFrame(rows).to_string(index=False))
R.to_csv("acct_final_eval.csv", index=False); pd.DataFrame(rows).to_csv("acct_final_funded.csv", index=False)
