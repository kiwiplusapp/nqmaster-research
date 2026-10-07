"""Scaling limit: how big are the household's simultaneous orders compared with the market's volume at each module's entry minute?
Volume of MNQ + NQ (in MNQ equivalents: NQ x10) in the entry minute, from the real futures exports (2024-26). Order size per signal =
contracts per account x module weight (x2 boosts) x number of accounts. Reports the median minute volume per module and the share of it
that 5 / 10 / 25 accounts would take (eval sizes: Lucid 6, Apex 5 -> ~5.6 average). -> liquidity.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, "..")
import nt_compare as C
RES = "../data/"
def vol_map(name, mult):
    z = np.load(RES + name); sm = ((z["om"].astype(np.int64) - 1080) % 1440)
    return pd.Series(z["v"] * mult, index=pd.MultiIndex.from_arrays([z["date"], sm])).groupby(level=[0, 1]).sum()
V = vol_map("mnq_fut.npz", 1.0).add(vol_map("nq_fut.npz", 10.0), fill_value=0.0)
R, _ = C.research_set("ultra")
R["vol"] = V.reindex(pd.MultiIndex.from_arrays([R.date.values, R.tin.values])).values
rows = []
for m, g in R.groupby("mod"):
    v = g.vol.dropna(); w = g.w.median()
    if len(v) == 0: continue
    med = np.median(v); p10 = np.percentile(v, 10)
    row = dict(modulo=m, hora_ET=f"{((int(g.tin.median()) + 1080) % 1440) // 60:02d}:{((int(g.tin.median()) + 1080) % 1440) % 60:02d}", trades=len(g),
               vol_minuto_mediana=round(med), vol_minuto_p10=round(p10), peso=w)
    for n in (5, 10, 25):
        q = 5.6 * w * n; row[f"orden_{n}cuentas"] = round(q); row[f"pct_vol_{n}"] = round(100 * q / med, 1); row[f"pct_vol_{n}_p10"] = round(100 * q / max(p10, 1), 1)
    rows.append(row)
O = pd.DataFrame(rows).sort_values("vol_minuto_mediana"); O.to_csv("liquidity.csv", index=False); pd.set_option("display.width", 250); print(O.to_string(index=False))
