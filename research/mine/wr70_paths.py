import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
exec(open("wr70_eval.py").read().split("rows = []")[0])
os.chdir(RES)
from pa_subsets import build as bpath
def paths(prof, rules=True):
    out = {}
    for tag, lo in (("nq_1m", 20200201), ("mnq_fut", 20240201)):
        X = build(tag, prof, rules); X = X[X.date >= lo]
        alld = np.array(sorted(A[tag][(A[tag].date >= lo)].date.unique()))
        for per, m, days in ((("IS", X.date < 20240101, alld[alld < 20240101]), ("C24", X.date >= 20240101, alld[alld >= 20240101])) if tag == "nq_1m" else (("REAL", X.date >= 0, alld),)):
            out[per] = bpath(tag, X[m], days)
    return out
if __name__ == "__main__":
    P = paths(CANDS["WR70-A"]); pickle.dump(P, open(os.path.join(RES, "mine", "wr70plus_paths.pkl"), "wb"))
    from evalfast import stats
    rows = []
    for acct, T, D in (("Apex 25K", 1500.0, 1500.0), ("Apex 50K", 3000.0, 2500.0)):
        for k in (1, 2, 3, 4, 6):
            for per in ("IS", "C24", "REAL"):
                s = stats(P[per], T=T, D=D, k1=k, maxd=21)
                rows.append(dict(acct=acct, k=k, per=per, pass30=s["pass_"], bust30=s["bust"], timeout=s["timeout"], med_days=s["med_days"], evals_per_funded=s["evals_per_PA"], days_to_funded=s["days_to_PA"]))
    g = pd.DataFrame(rows); pd.set_option("display.width", 250)
    for c in ("pass30", "bust30", "med_days", "days_to_funded", "evals_per_funded"):
        print(c); print(g.pivot_table(index=["acct", "k"], columns="per", values=c)[["IS", "C24", "REAL"]].to_string())
