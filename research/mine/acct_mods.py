"""Per-module daily statistics for fixed 1-contract accounts. The ruin / race odds of a drifting process depend on mu/sigma^2,
so for each module: daily mean, sd, worst-day, mu/sigma^2 (x1000), and the effect of REMOVING it from Ultra on the Ultra ratio.
Also mu/sigma^2 of Ultra by daily-ATR tercile (per-contract $ risk grows with ATR)."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_lab import Z, META, sums
from core import Data
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
ULTRA = [m for m in META["IS"] if m.startswith("U:")]
rows = []
for per in ("IS", "C24", "REAL"):
    z = Z(per); base = sum(z[m + "|R"][:, -1].astype(float) for m in ULTRA); bm, bv = base.mean(), base.var()
    for m in META[per]:
        c = z[m + "|R"][:, -1].astype(float); lo = z[m + "|L"].min(1).astype(float)
        rest = base - c if m in ULTRA else base + c
        rows.append(dict(per=per, mod=m, mo=round(c.mean() * 21), sd=round(c.std()), ratio=round(1000 * c.mean() / c.var(), 2) if c.var() > 0 else np.nan,
                         worst=round(lo.min()), corr=round(np.corrcoef(c, base)[0, 1], 2),
                         ultra_ratio_change=round(1000 * (rest.mean() / rest.var() - bm / bv), 3)))
M = pd.DataFrame(rows)
print("Ultra ratio x1000:", {per: round(1000 * sum(Z(per)[m + "|R"][:, -1].astype(float) for m in ULTRA).mean() / sum(Z(per)[m + "|R"][:, -1].astype(float) for m in ULTRA).var(), 3) for per in ("IS", "C24", "REAL")})
print(M.pivot(index="mod", columns="per", values=["mo", "sd", "ratio", "ultra_ratio_change"]).to_string())
# ATR terciles (Ultra)
for per, nm in (("IS", "nq_1m.npz"), ("C24", "nq_1m.npz"), ("REAL", "mnq_fut.npz")):
    D = Data(nm); days = Z(per)["days"]; atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(days).to_numpy()
    base = sum(Z(per)[m + "|R"][:, -1].astype(float) for m in ULTRA); q = np.nanquantile(atr, [1 / 3, 2 / 3])
    out = []
    for lab, msk in (("bajo", atr < q[0]), ("medio", (atr >= q[0]) & (atr < q[1])), ("alto", atr >= q[1])):
        x = base[msk]; out.append(f"{lab}: ATR<{q[0]:.0f}/{q[1]:.0f} $/día {x.mean():.0f} sd {x.std():.0f} ratio {1000 * x.mean() / x.var():.3f}")
    print(per, " | ".join(out))
M.to_csv("acct_mods.csv", index=False)
