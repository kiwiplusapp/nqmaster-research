"""2026-10-14 16-year robustness table for the NQMaster profiles + the yearly module review rule.
Years 2013-2019: cost-normalised P&L (0.345% of ATR per trade, removes the price-level effect); 2020-2026: real $ per MNQ.
Profiles: Ultra (cand16 UltraR + CPI09), UltraQ (ultraq_build.py), Durable (NF05 CRT11 VOLB MSEQS ORB60 ORB90, composition chosen on
2010-26 -> its old years are in-sample), WF = Ultra with the yearly review rule (each January switch off a module whose last-5-year
cost-normalised PF <= 1.05; uses only past data). -> robust16.json"""
import json, pickle, numpy as np, pandas as pd
DUR = ["NF05", "CRT11", "VOLB", "MSEQS", "ORB60", "ORB90"]
pf = lambda x: float(x[x > 0].sum() / -x[x <= 0].sum()) if (x <= 0).any() else np.nan

if __name__ == "__main__":
    C = pickle.load(open("cand16_trades.pkl", "rb")); Q = pickle.load(open("ultraq_trades.pkl", "rb"))["UltraQ"]
    R, N = C["UltraR"]; R = pd.concat([R, Q[0][Q[0]["mod"] == "CPI09"]], ignore_index=True); N = pd.concat([N, Q[1][Q[1]["mod"] == "CPI09"]], ignore_index=True)
    for X in (R, N, Q[0], Q[1]): X["y"] = X.date // 10000; X["x"] = X.u * X.w
    mods = sorted(N["mod"].unique()); sel = {}
    for y in range(2013, 2028):
        T = N[(N.y >= y - 5) & (N.y < y)]; sel[y] = [m for m in mods if (T["mod"] == m).sum() >= 20 and pf(T[T["mod"] == m].x) > 1.05]
    out = {"review_off_next_year_2027": [m for m in mods if m not in sel[2027]], "years": {}}
    for y in range(2013, 2027):
        rec = {}
        for nm, X in (("Ultra", N if y < 2020 else R), ("UltraQ", Q[1] if y < 2020 else Q[0]), ("Durable", N if y < 2020 else R), ("WF", N if y < 2020 else R)):
            s = X[X.y == y]
            if nm == "Durable": s = s[s["mod"].isin(DUR)]
            if nm == "WF": s = s[s["mod"].isin(sel[y])]
            rec[nm] = dict(pf=round(pf(s.x), 2), wr=round(100 * float((s.u > 0).mean()), 1), n=int(len(s)), net=round(float(s.x.sum())) if y >= 2020 else None)
        out["years"][y] = rec
        print(y, " | ".join(f"{k} PF {v['pf']:.2f} WR {v['wr']:.0f}" + (f" ${v['net']:,}" if v['net'] is not None else "") for k, v in rec.items()))
    print("review rule, switch off in 2027:", out["review_off_next_year_2027"])
    json.dump(out, open("robust16.json", "w"), indent=1, default=str)
