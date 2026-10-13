"""1-contract study, step 12: eval-only module / boost removals, pre-registered from the 2026-10-05 mu/sigma^2 finding (x2 boosts, VOLB, LON have the lowest
edge per unit of variance). Variants of the UltraR trade list: no x2 boosts (w=1), no VOLB, no LON, no ICT, no VOLB+LON. Lucid Flex 25K / 50K and Bulenox 25K,
P(funded <= 22 trading days) with serial restarts, T1 vs T2.  Accept only if BOTH periods improve by >= 2 points.  -> smallacct_mods.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from smallacct_eval import SETUPS
from smallacct_protocol import outcomes, protocol
if __name__ == "__main__":
    E = RB.setup(); days = pickle.load(open(os.path.join(SP, "robust2_paths.pkl"), "rb"))[0]; n = len(days)
    X0 = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["UltraR"][0]; X0 = RB.attach(X0[X0.date.isin(days)], E)
    print(X0["mod"].value_counts().to_dict())
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 50]
    V = {"base": X0, "no x2 boosts": X0.assign(w=1.0), "no VOLB": X0[~X0["mod"].str.startswith("VOLB")], "no LON": X0[X0["mod"] != "LON"],
         "no ICT": X0[X0["mod"] != "ICT"], "no VOLB+LON": X0[~X0["mod"].str.startswith("VOLB") & (X0["mod"] != "LON")],
         "no boosts + no VOLB": X0[~X0["mod"].str.startswith("VOLB")].assign(w=1.0)}
    OUT = {}
    for lab, X in V.items():
        low, close, fin = full_paths(X, days); c = (X.w * 1.0).groupby(X.date).sum().reindex(days, fill_value=0.0).to_numpy(); r = {}
        for name in ("Lucid Flex 25K", "Lucid Flex 50K", "Bulenox Opt2 25K"):
            T, D, cons, mind, dll, fee = SETUPS[name]; G = 0.9 * cons * T if cons > 0 else 0.0
            lo, cl = vectors(low - c[:, None], close - c[:, None], fin - c, G)
            if dll > 0:
                hit = lo <= -dll; cl = np.where(hit, -float(dll), cl); lo = np.where(hit, -float(dll), lo)
            EL = np.ascontiguousarray(np.array([lo, lo])); EC = np.ascontiguousarray(np.array([cl, cl]))
            res, dd = outcomes(EL, EC, -1e9, T, D, cons, mind, n)
            r[name] = (protocol(res, dd, s1, 22, 1, 0, fee)[0], protocol(res, dd, s2, 22, 1, 0, fee)[0])
        OUT[lab] = dict(mu_day=round(float(fin.mean())), sd_day=round(float(fin.std())), **r)
        print(f"{lab:22s} mu {fin.mean():6.1f} sd {fin.std():6.1f}", r, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "smallacct_mods.json"), "w"), indent=1)
