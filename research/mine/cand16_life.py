"""Candidate profiles (cand16.py) through the account lifecycle with the new cushion risk cap (robust2_life.py machinery):
MyFundedFutures Rapid EOD 50K and Lucid Flex 50K, 1 contract, 1,000 resampled 12-month paths per period (paired), +1 tick stress.
Policies per candidate: no cap (fixed profile) and 'cap300' = trades risking > $300 per contract skipped while the eval cushion
< $1,200 and the funded cushion < $1,500 / $2,000. -> cand16_life.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, vectors, boot, run_life, SP

if __name__ == "__main__":
    E = RB.setup(); TRD = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))
    days = pickle.load(open(os.path.join(SP, "robust2_paths.pkl"), "rb"))[0]
    V = {}; ST = {}
    for name in TRD:
        X = RB.attach(TRD[name][0][TRD[name][0].date.isin(days)], E)
        for sfx, XX in (("", X), ("_cap300", X[X.risk <= 300])):
            low, close, fin = full_paths(XX, days)
            c = (XX.w * 1.0).groupby(XX.date).sum().reindex(days, fill_value=0.0).to_numpy()
            for G in (0.0, 800.0, 1400.0):
                V[(name + sfx, G)] = vectors(low, close, fin, G); V[(name + sfx + "_t1", G)] = vectors(low - c[:, None], close - c[:, None], fin - c, G)
        print("paths", name, flush=True)
    IDS = {"2020-23": boot(days, (days >= 20200101) & (days < 20240101), 11), "2024-26": boot(days, days >= 20240101, 12)}
    OUT = {}
    for firm in ("MFFU", "Lucid"):
        for name in TRD:
            for pol, (le, Ce, lf, c1) in {"fixed": (name, 0, name, 0), "cap300 e1200 f1500": (name + "_cap300", 1200, name + "_cap300", 1500),
                                          "cap300 e1200 f2000": (name + "_cap300", 1200, name + "_cap300", 2000)}.items():
                # run_life uses 'Ultra' as the high gear: map it to this candidate
                VV = dict(V); 
                for G in (0.0, 800.0, 1400.0):
                    VV[("Ultra", G)] = V[(name, G)]; VV[("Ultra_t1", G)] = V[(name + "_t1", G)]
                r = {}
                for per, ids in IDS.items():
                    r[per] = run_life(VV, firm, le, Ce, lf, c1, ids, False); r[per + " +1tick"] = run_life(VV, firm, le, Ce, lf, c1, ids, True)
                OUT[f"{firm} | {name} | {pol}"] = r
                print(firm, f"{name:10s} {pol:20s}", {p: (v["per_month"], v["funded_busts"], v["accounts_lost"], v["p_neg_year"]) for p, v in r.items()}, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "cand16_life.json"), "w"), indent=1)
