"""wrq_agree: 'agreement between modules already in trade' as an entry filter. In the current Ultra / WR70Plus portfolio (after
the conflict filter, so opposite positions never coexist), count for every trade the other NQ modules already open in the SAME
direction at its entry minute (n_same). Per module: WR / PF / expectancy with n_same = 0 vs >= 1, per period, and the
two rules 'skip if alone' / 'skip if others already in'. -> wrq_agree.csv"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_port import build_profile, days_of
from wrq_lib import stats

def n_same(X):
    out = np.zeros(len(X), int); X = X.reset_index(drop=True)
    for d, g in X.groupby("date"):
        tin = g.tin.to_numpy(); tout = g.tout.to_numpy(); dd = g.d.to_numpy(); md = g["mod"].to_numpy()
        for a, i in enumerate(g.index):
            live = (tin < tin[a]) & (tout > tin[a]) & (md != md[a])
            out[i] = int((live & (dd == dd[a])).sum())
    X["nsame"] = out; return X

if __name__ == "__main__":
    rows = []
    for prof in ("Ultra", "WR70Plus"):
        for per in ("IS", "C24", "REAL", "L15"):
            X = n_same(build_profile(per, prof, rules=False))
            for m, g in list(X.groupby("mod")) + [("ALL", X)]:
                for lab, k in (("alone", g.nsame == 0), ("with", g.nsame >= 1)):
                    s = stats(g.u[k]); s.update(prof=prof, per=per, mod=m, grp=lab, share=k.mean()); rows.append(s)
            print(prof, per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("wrq_agree.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    P = R.pivot_table(index=["prof", "mod", "grp"], columns="per", values=["share", "wr", "pf"])
    print(P.round(3).to_string())
