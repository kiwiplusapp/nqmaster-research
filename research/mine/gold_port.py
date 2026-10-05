"""Gold portfolio from the mined candidates (results_gold / results_goldfam). Selection ONLY on CFD 2020-23 (IS):
greedy forward selection on IS daily Sharpe with the first-come conflict filter (no opposite positions), max 10 modules,
each added module must raise IS Sharpe by >= 0.05. C24 (CFD 2024-26) and REAL (MGC 2024-26) are out of sample.
Costs: $1.90 RT + 1 tick per side (MGC: $4 per research point). FOMC days skipped."""
import os, sys, pickle, ast, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data
from news import NEWS
FOMC = set(NEWS["FOMC"])
def conflict_filter(T):
    keep = []
    for d, g in T.groupby("date", sort=False):
        openpos = []
        for r in g.sort_values("tin").itertuples():
            if any(to > r.tin and dd == -r.d for to, dd in openpos): continue
            openpos.append((r.tout, r.d)); keep.append(r.Index)
    return T.loc[keep]
def days_of(name, lo, hi):
    D = Data(name); rth = (D.om >= 570) & (D.om < 960); d = np.unique(D.date[rth]); d = d[(d >= lo) & (d < hi)]
    return np.array([x for x in d if x not in FOMC])
PER = {"IS": ("nq", 20200201, 20240101), "C24": ("nq", 20240101, 30000000), "REAL": ("mnq", 20240201, 30000000)}
DAYS = {"IS": days_of("xau_hd.npz", 20200201, 20240101), "C24": days_of("xau_hd.npz", 20240101, 30000000), "REAL": days_of("mgc_fut.npz", 20240201, 30000000)}
def trades(tr, per, name, w=1.0):
    key, lo, hi = PER[per]; df = tr[key]; df = df[(df.date >= lo) & (df.date < hi) & ~df.date.isin(FOMC)]
    return pd.DataFrame(dict(date=df.date.to_numpy(), mod=name, tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df.usd.to_numpy(), w=w))
def metrics(F, days):
    x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0.0); eq = d.cumsum()
    return dict(n=len(F), tpd=round(len(F) / len(days), 2), wr=round(100 * (F.u > 0).mean(), 1), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3) if (x <= 0).any() else np.nan,
                sharpe=round(d.mean() / d.std() * np.sqrt(252), 2), mo=round(d.mean() * 21), maxdd=round((eq.cummax() - eq).max()))
def combo(mods, per):
    F = pd.concat([trades(TR[k], per, f"{k[0]}#{k[1]}") for k in mods], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)
    return conflict_filter(F)
if __name__ == "__main__":
    R = pd.concat([pd.read_csv("results_gold.csv"), pd.read_csv("results_goldfam.csv")], ignore_index=True)
    TR = {}
    for f in ("trades_gold.pkl", "trades_goldfam.pkl"): TR.update(pickle.load(open(f, "rb")))
    pool = R[(R.IS_n >= 80) & (R.IS_pf >= 1.15)]
    pool = [(r.fam, r.j) for r in pool.itertuples() if (r.fam, r.j) in TR]
    print("pool:", len(pool), flush=True)
    # precompute IS daily series per candidate (no conflict) to speed the first screen
    sel = []; best = -9
    for step in range(10):
        scores = []
        for k in pool:
            if k in sel: continue
            F = combo(sel + [k], "IS"); m = metrics(F, DAYS["IS"]); scores.append((m["sharpe"], k))
        scores.sort(reverse=True); s, k = scores[0]
        if s < best + 0.05: break
        sel.append(k); best = s
        row = {per: metrics(combo(sel, per), DAYS[per]) for per in PER}
        print(f"+ {k} {R[(R.fam == k[0]) & (R.j == k[1])].params.iat[0]}")
        print("   ", " | ".join(f"{per}: tpd {m['tpd']} WR {m['wr']} PF {m['pf']} Sh {m['sharpe']} $/mo {m['mo']} DD {m['maxdd']}" for per, m in row.items()), flush=True)
    pickle.dump(dict(sel=sel), open("gold_port_sel.pkl", "wb"))
