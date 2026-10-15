"""2026-10-16 six-year round, step 2: re-select the 54k configs already mined on real NQ (results_db_old/new, results_nga) under the
six-year protocol of six_lib (2010-19 NOT required any more). T1 from the CSV (2020-01..2023-12) n >= 80, PF >= 1.3 -> T2 PF >= 1.2, n >= 40
-> +4 ticks T2 PF >= 1.1 -> plateau (>= half of one-step grid neighbours T1 PF >= 1.15) -> portfolio add_test (T1 from 2020-10-15).
Null: P(T2 PF >= 1.2) over all configs vs given T1 pass. -> six_reselect.json"""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import six_lib as S

if __name__ == "__main__":
    R = pd.concat([pd.read_csv(os.path.join(HERE, f)).assign(src=f) for f in ("results_db_old.csv", "results_db_new.csv", "results_nga.csv")], ignore_index=True)
    R = R[R.err.isna()] if "err" in R else R
    OUT = dict(n_configs=int(len(R)))
    ok2 = (R.T2_pf >= 1.2) & (R.T2_n >= 40)
    t1 = (R.T1_n >= 80) & (R.T1_pf >= 1.3)
    OUT["base_rate_T2"] = round(100 * float(ok2.mean()), 2); OUT["T1_pass"] = int(t1.sum()); OUT["T2_given_T1"] = round(100 * float(ok2[t1].mean()), 2)
    OUT["per_family"] = {f: dict(n=int(len(g)), med_T1=round(float(g.T1_pf.median()), 3), med_T2=round(float(g.T2_pf.median()), 3), T1_pass=int(((g.T1_n >= 80) & (g.T1_pf >= 1.3)).sum()),
                                 T2_given_T1=round(100 * float(((g.T2_pf >= 1.2) & (g.T2_n >= 40))[(g.T1_n >= 80) & (g.T1_pf >= 1.3)].mean()), 1) if ((g.T1_n >= 80) & (g.T1_pf >= 1.3)).any() else None)
                         for f, g in R.groupby("fam")}
    C = R[t1 & ok2].copy()
    print("configs", len(R), "T1 pass", int(t1.sum()), "T1&T2", len(C), "base rate", OUT["base_rate_T2"], "given T1", OUT["T2_given_T1"], flush=True)
    TR = {}
    for f in ("trades_db_old.pkl", "trades_db_new.pkl", "trades_nga.pkl"):
        TR.update(pickle.load(open(os.path.join(HERE, f), "rb")))
    # plateau: neighbours = same family, params differ in exactly one key
    R["p"] = R.params.apply(ast.literal_eval)
    fam_rows = {f: g for f, g in R.groupby("fam")}
    rows = []
    for _, c in C.iterrows():
        key = (c.fam, int(c.j)); tr = TR.get(key)
        if tr is None: continue
        t = tr["real"]; t = t[t.date >= S.START]
        ts = S.tstats(t.usd.to_numpy(), t.date.to_numpy()); ts4 = S.tstats(t.usd.to_numpy() - 3.0, t.date.to_numpy())
        if ts4["T2"]["pf"] is None or ts4["T2"]["pf"] < 1.1: continue
        p = ast.literal_eval(c.params); g = fam_rows[c.fam]
        nb = [r for r in g.itertuples() if sum(r.p.get(k) != v for k, v in p.items()) == 1]
        plat = float(np.mean([(x.T1_pf or 0) >= 1.15 for x in nb])) if nb else 0.0
        if plat < 0.5: continue
        cd = t.usd.groupby(t.date).sum(); a = S.add_test(cd)
        b, m = a["base"], a["comb"]
        acc = (m["T1"]["sharpe"] > b["T1"]["sharpe"]) and (m["T2"]["sharpe"] > b["T2"]["sharpe"]) and (m["all"]["maxdd"] <= 1.05 * b["all"]["maxdd"]) and (m["all"]["worst_month"] >= 1.05 * b["all"]["worst_month"])
        rows.append(dict(fam=c.fam, j=int(c.j), params=c.params, T1=ts["T1"], T2=ts["T2"], T2_plus4_pf=ts4["T2"]["pf"], A_pf=c.A_pf, B_pf=c.B_pf, plateau=round(plat, 2),
                         corr=a["corr"], dSR_T1=round(m["T1"]["sharpe"] - b["T1"]["sharpe"], 3), dSR_T2=round(m["T2"]["sharpe"] - b["T2"]["sharpe"], 3),
                         dDD=m["all"]["maxdd"] - b["all"]["maxdd"], dWorstMo=m["all"]["worst_month"] - b["all"]["worst_month"], accepted=bool(acc)))
    D = pd.DataFrame(rows)
    print("after +4 ticks & plateau:", len(D), "accepted:", int(D.accepted.sum()) if len(D) else 0)
    if len(D):
        D = D.sort_values(["accepted", "dSR_T1"], ascending=False)
        with pd.option_context("display.width", 250, "display.max_colwidth", 90):
            print(D.drop(columns=["T1", "T2"]).assign(T1pf=[x["pf"] for x in D.T1], T1n=[x["n"] for x in D.T1], T2pf=[x["pf"] for x in D.T2], T2n=[x["n"] for x in D.T2], T2wr=[x["wr"] for x in D.T2]).head(40).to_string(index=False))
    OUT["candidates"] = D.to_dict("records")
    json.dump(OUT, open(os.path.join(HERE, "six_reselect.json"), "w"), indent=1, default=str)
