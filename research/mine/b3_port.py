"""Batch 3 selection + marginal portfolio test.
1) Per family: configs with IS n>=80 and PF>=1.15 (selection on 2020-23 only), then the OOS view (C24 CFD 2024-26, REAL MNQ 2024-26).
2) Top IS candidates (one per distinct setup) are added to WR70Plus (WR70-A + rules) and Ultra-like (+VOLB R2) portfolios with the
   first-come conflict filter; report WR / PF / Sharpe / $/mo / trades/day for IS, C24, REAL and 2026-only."""
import os, sys, pickle, ast, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
exec(open("wr70_eval.py").read().split("rows = []")[0])
from news import NEWS
TAG = os.environ.get("B3TAG", "b3")
R = pd.read_csv(f"results_{TAG}.csv"); TR = pickle.load(open(f"trades_{TAG}.pkl", "rb"))
pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 160); pd.set_option("display.max_rows", 500)
R["ok_is"] = (R.IS_n >= 80) & (R.IS_pf >= 1.15)
print("configs:", len(R), "errors:", R.get("err", pd.Series(dtype=str)).notna().sum())
for fam, g in R.groupby("fam"):
    s = g[g.ok_is]
    print(f"\n=== {fam}: {len(g)} configs, IS-ok {len(s)}; of those C24 PF>1: {(s.C24_pf > 1).mean() * 100 if len(s) else 0:.0f}%, REAL PF>1: {(s.REAL_pf > 1).mean() * 100 if len(s) else 0:.0f}%")
    print("  share of ALL configs with IS PF>1:", round((g.IS_pf > 1).mean() * 100, 1), "% | C24 PF>1:", round((g.C24_pf > 1).mean() * 100, 1), "% | REAL PF>1:", round((g.REAL_pf > 1).mean() * 100, 1), "%")
    cols = ["j", "params", "IS_n", "IS_wr", "IS_pf", "C24_n", "C24_wr", "C24_pf", "REAL_n", "REAL_wr", "REAL_pf", "REAL_net"]
    print(s.sort_values("IS_pf", ascending=False).head(15)[cols].to_string(index=False))
    hw = s[s.IS_wr >= 65]
    if len(hw): print("  -- IS WR>=65:"); print(hw.sort_values("IS_pf", ascending=False).head(10)[cols].to_string(index=False))

def cand(tag, tr, name):
    df = tr["mnq" if tag == "mnq_fut" else "nq"]; df = df[~df.date.isin(NEWS["FOMC"])]
    return pd.DataFrame(dict(date=df.date, mod=name, var=0.0, usd=df.usd, tin=df.tin, tout=df.tout, d=df.d, u=df.usd - 0.9, w=1.0))
def evalport(extra, prof):
    out = {}
    for tag in ("nq_1m", "mnq_fut"):
        X = build(tag, prof, True)[["date", "mod", "var", "tin", "tout", "d", "u", "w"]]
        if extra:
            X = pd.concat([X] + [cand(tag, tr, nm)[X.columns] for nm, tr in extra], ignore_index=True)
            X = conflict_filter(X.sort_values(["date", "tin"]).reset_index(drop=True))
        parts = [("IS", (X.date >= 20200201) & (X.date < 20240101), 20200201, 20240101), ("C24", X.date >= 20240101, 20240101, 3e7)] if tag == "nq_1m" else \
                [("REAL", X.date >= 20240201, 20240201, 3e7), ("R2026", X.date >= 20260101, 20260101, 3e7)]
        for lab, m, lo, hi in parts:
            days = np.array(sorted(A[tag][(A[tag].date >= lo) & (A[tag].date < hi)].date.unique()))
            out[lab] = metrics(X[m], days)
    return out
_DD = {}
def gen_tr(fam, j, data=(("nq", "nq_1m.npz"), ("mnq", "mnq_fut.npz"))):
    from families3 import FAMILIES3
    from core import run_events
    gen, G, md = FAMILIES3[fam]; out = {}
    for key, nm in data:
        if nm not in _DD: _DD[nm] = Data(nm)
        D = _DD[nm]; df = run_events(D, gen(D, G[j]), flat=955, maxday=md)
        out[key] = pd.DataFrame(dict(date=df.date, usd=df.usd, tin=D.sm[df.fi.to_numpy().astype(int)], tout=D.sm[df.xi.to_numpy().astype(int)] + 1, d=df.d))
    return out
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "port":
    PICKS = [("ENGULF_4H", j) for j in (411, 385, 388, 408, 414, 253, 349, 1374)] + [("EMA9_VWAP", j) for j in (576, 721, 679, 678, 673)]
    picks = pd.concat([R[(R.fam == f) & (R.j == j)] for f, j in PICKS])
    rows = []
    for prof_nm, prof in (("WR70Plus", CANDS["WR70-A"]),):
        b = evalport([], prof); rows.append(dict(prof=prof_nm, cand="BASE", **{f"{p}_{k}": v for p, r in b.items() for k, v in r.items()}))
        for _, c in picks.iterrows():
            tr = gen_tr(c.fam, int(c.j))
            r = evalport([(c.fam, tr)], prof)
            rows.append(dict(prof=prof_nm, cand=f"{c.fam}#{c.j} {c.params}", **{f"{p}_{k}": v for p, r2 in r.items() for k, v in r2.items()}))
            print(rows[-1]["cand"][:120], {p: (r[p]["wr"], r[p]["pf"], r[p]["tpd"]) for p in r}, flush=True)
        for combo in ((("ENGULF_4H", 411), ("EMA9_VWAP", 721)), (("ENGULF_4H", 411), ("ENGULF_4H", 253), ("EMA9_VWAP", 721), ("EMA9_VWAP", 679))):
            r = evalport([(f"{f}#{j}", gen_tr(f, j)) for f, j in combo], prof)
            rows.append(dict(prof=prof_nm, cand="COMBO " + "+".join(f"{f}#{j}" for f, j in combo), **{f"{p}_{k}": v for p, r2 in r.items() for k, v in r2.items()}))
    G = pd.DataFrame(rows); G.to_csv(f"b3_port_{TAG}.csv", index=False)
    for p in ("IS", "C24", "REAL", "R2026"):
        print(p); print(G[["cand", f"{p}_tpd", f"{p}_wr", f"{p}_pf", f"{p}_sharpe", f"{p}_mo", f"{p}_maxdd"]].to_string(index=False))
