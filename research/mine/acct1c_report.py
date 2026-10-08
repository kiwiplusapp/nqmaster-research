"""acct1c: summary tables from acct1c_eval.csv and acct1c_life*.csv (no simulation)."""
import sys, glob, pandas as pd
pd.set_option("display.width", 320); pd.set_option("display.max_rows", 400); pd.set_option("display.max_colwidth", 45)

E = pd.read_csv("acct1c_eval.csv")
EVK = [("U/EST C1200 + oro WinRate x2", "Flex50", 1400.0), ("U/EST C1500 + oro WinRate x2", "Flex50", 1400.0),
       ("U/EST C1800 + oro WinRate x2", "Flex50", 1400.0), ("U fijo + oro Robust x1", "Flex50", 1400.0),
       ("W fijo + oro WinRate x1", "Flex50", 1400.0), ("U/EST C1200 + oro WinRate x2", "Pro50 DLL1200", 0.0),
       ("U fijo + oro Robust x1", "Pro50 DLL1200", 0.0), ("W fijo + oro WinRate x1", "Pro50 DLL1200", 0.0),
       ("U/EST C1800 + oro WinRate x2", "Flex100", 2800.0), ("U fijo + oro Robust x1", "Flex100", 2800.0)]
rows = []
for ev, firm, G in EVK:
    for st in ("todos", "ATR<1.15"):
        s = E[(E["eval"] == ev) & (E.firm == firm) & (E.G == G) & (E.start == st)]
        r = dict(eval=ev, firm=firm, start=st)
        for t, tn in (("historia", "H"), ("costo +1 tick", "T"), ("bootstrap", "B")):
            q = s[s.test == t].set_index("per")
            for p in ("IS", "C24", "REAL"):
                r[f"{tn}_{p}"] = round(q.loc[p, "pass_pct"], 1)
        h = s[s.test == "historia"]
        r["pass9_mean"] = round(s.pass_pct.mean(), 1); r["pass9_min"] = round(s.pass_pct.min(), 1)
        r["med_H"] = "/".join(f"{x:.0f}" for x in h.set_index("per").loc[["IS", "C24", "REAL"], "med_days"])
        r["med_B"] = "/".join(f"{x:.0f}" for x in s[s.test == "bootstrap"].set_index("per").loc[["IS", "C24", "REAL"], "med_days"])
        r["p22_H"] = round(h.p22.mean(), 1); r["p33_H"] = round(h.p33.mean(), 1); r["fund33_H"] = round(h.fund33.mean(), 1)
        rows.append(r)
T = pd.DataFrame(rows); print(T.to_string(index=False)); T.to_csv("acct1c_eval_table.csv", index=False)

for f in sorted(glob.glob("acct1c_life*_summary.csv")):
    S = pd.read_csv(f); print("\n", f)
    for acc in S.acc.unique():
        s = S[S.acc == acc]
        print(f"\n== {acc}: top 15 by mean of 9 tests")
        print(s.sort_values("mean9", ascending=False).head(15).to_string(index=False))
        for k in sorted(s.k.unique()):
            print(f"-- {acc} funded k={k}: best 5 by min of 9")
            print(s[s.k == k].sort_values("min9", ascending=False).head(5).to_string(index=False))
