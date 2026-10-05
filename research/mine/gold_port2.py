"""High-win-rate gold portfolio, selected ONLY on CFD 2020-23 (IS); CFD 2024-26 and MGC 2024-26 are out of sample;
2010-14 / 2015-19 shown as an extra regime check (cost-normalised to today's cost/ATR ratio: PF only).
Candidates: IS n >= 60, IS WR >= 63%, IS PF >= 1.2 (real $ costs, flat 16:50). Greedy: maximise IS PF of the combined
portfolio (conflict filter) while the combined IS WR stays >= 66%; a module must add >= 0.02 PF and keep tpd growing."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from gold_port import conflict_filter, metrics, DAYS, FOMC
R = pd.read_csv("results_goldlong.csv"); TR = pickle.load(open("trades_goldlong.pkl", "rb"))
RN = pd.read_csv("results_goldlongnorm.csv").set_index(["fam", "j"])
TN = pickle.load(open("trades_goldlongnorm.pkl", "rb"))
PER = {"IS": ("nq", 20200201, 20240101), "C24": ("nq", 20240101, 30000000), "REAL": ("mnq", 20240201, 30000000)}
def trades(k, per):
    key, lo, hi = PER[per]; df = TR[k][key]; df = df[(df.date >= lo) & (df.date < hi) & ~df.date.isin(FOMC)]
    return pd.DataFrame(dict(date=df.date.to_numpy(), mod=f"{k[0]}#{k[1]}", tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df.usd.to_numpy(), w=1.0))
def combo(mods, per): return conflict_filter(pd.concat([trades(k, per) for k in mods], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
def longpf(mods):
    out = {}
    for lab, lo, hi in (("2010-14", 20100201, 20150101), ("2015-19", 20150101, 20200101)):
        parts = []
        for k in mods:
            if k not in TN: return {"2010-14": np.nan, "2015-19": np.nan}
            df = TN[k]["nq"]; df = df[(df.date >= lo) & (df.date < hi) & ~df.date.isin(FOMC)]
            parts.append(pd.DataFrame(dict(date=df.date.to_numpy(), mod=f"{k}", tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df.usd.to_numpy(), w=1.0)))
        F = conflict_filter(pd.concat(parts, ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)); x = F.u
        out[lab] = round(float(x[x > 0].sum() / -x[x <= 0].sum()), 3)
    return out
cand = R[(R.T1_n >= 60) & (R.T1_wr >= 63) & (R.T1_pf >= 1.2)]
pool = [(r.fam, r.j) for r in cand.itertuples() if (r.fam, r.j) in TR]
print("pool", len(pool), flush=True)
sel = []; cur = None
for step in range(12):
    best = None
    for k in pool:
        if k in sel: continue
        m = metrics(combo(sel + [k], "IS"), DAYS["IS"])
        if m["wr"] < 66: continue
        if cur is not None and (m["pf"] < cur["pf"] + 0.02 and m["tpd"] <= cur["tpd"]): continue
        score = m["pf"] * np.sqrt(m["tpd"])               # quality x frequency
        if best is None or score > best[0]: best = (score, k, m)
    if best is None or (cur is not None and best[0] <= cur["pf"] * np.sqrt(cur["tpd"]) + 0.01): break
    sel.append(best[1]); cur = best[2]
    oos = {per: metrics(combo(sel, per), DAYS[per]) for per in ("C24", "REAL")}
    print(f"+ {best[1]} {R[(R.fam == best[1][0]) & (R.j == best[1][1])].params.iat[0]}")
    print(f"   IS  tpd {cur['tpd']} WR {cur['wr']} PF {cur['pf']} Sh {cur['sharpe']} $/mo {cur['mo']} | " +
          " | ".join(f"{p} tpd {m['tpd']} WR {m['wr']} PF {m['pf']} Sh {m['sharpe']} $/mo {m['mo']} DD {m['maxdd']}" for p, m in oos.items()) + f" | long {longpf(sel)}", flush=True)
pickle.dump(sel, open("gold_port2_sel.pkl", "wb"))
