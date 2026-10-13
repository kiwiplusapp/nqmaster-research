"""1-contract study, step 8: realistic income per seat. 12-month lifecycle (eval with serial restarts -> funded -> payouts -> bust -> new eval) for
Lucid Flex / Pro 25K and 50K with 0 / 35 / 60 % of the edge removed (+1 tick cost always), policy fixed from smallacct_life.py (eval always full profile,
funded low gear = $150 or $300 risk cap while cushion < 0.5 x DD).  Net cash per month = payouts x 90% - eval fees.  -> smallacct_life2.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_life import vectors, SP
import acct1c_lib as A
H = 252
CFG = {"Lucid Flex 25K": dict(firm=0, T=1250, D=1000, cons=0.5, fee=89.0, Q=100.0, cap1=1000.0, cap2=1000.0, X=1500.0, fcap=150),
       "Lucid Flex 50K": dict(firm=0, T=3000, D=2000, cons=0.5, fee=146.0, Q=150.0, cap1=2000.0, cap2=2000.0, X=4000.0, fcap=300),
       "Lucid Pro 25K": dict(firm=1, T=1250, D=1000, cons=0.0, fee=123.0, Q=100.0, cap1=1000.0, cap2=1500.0, X=1000.0, fcap=150),
       "Lucid Pro 50K": dict(firm=1, T=3000, D=2000, cons=0.0, fee=192.0, Q=150.0, cap1=2000.0, cap2=2500.0, X=2000.0, fcap=300)}
if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb")); n = len(days); idx = np.arange(n, dtype=np.int64)
    d24 = int(np.searchsorted(days, 20240101)); mu1 = float(P[("UltraR", 0)][2][:d24].mean()); mu2 = float(P[("UltraR", 0)][2][d24:].mean())
    OUT = {}
    for name, c in CFG.items():
        G = 0.9 * c["cons"] * c["T"] if c["cons"] > 0 else 0.0; r = {}
        for hc in (0.0, 0.35, 0.60):
            h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2); res = {}
            def vec(key, g):
                low, close, fin = P[key]; cc = P[key + ("cost",)]
                return vectors(low - cc[:, None] - h[:, None], close - cc[:, None] - h[:, None], fin - cc - h, g)
            hi = vec(("UltraR", 0), G); EL = np.ascontiguousarray(np.array([hi[0], hi[0]])); EC = np.ascontiguousarray(np.array([hi[1], hi[1]]))
            hf = vec(("UltraR", 0), 0.0); lf = vec(("UltraR", c["fcap"]), 0.0)
            FL = np.ascontiguousarray(np.array([lf[0], hf[0], hf[0]])); FC = np.ascontiguousarray(np.array([lf[1], hf[1], hf[1]]))
            out = np.zeros((n, 9)); k = A.life(EL, EC, -1e9, c["T"], c["D"], c["cons"], np.ones(n, np.bool_), c["fee"], FL, FC, 0.5 * c["D"], 0.5 * c["D"],
                                               c["firm"], c["X"], c["Q"], c["cap1"], c["cap2"], idx, H, 5, out)
            o = out[:k]; st = np.arange(k) * 5
            a = o[(st + H) < d24]; b = o[st >= d24]
            res = {p: dict(per_month=round(float(x[:, 0].mean() / 12)), p10_month=round(float(np.percentile(x[:, 0], 10) / 12)), accounts_lost_per_year=round(float((x[:, 1] - x[:, 2] + x[:, 3]).mean()), 2),
                           funded_busts=round(float(x[:, 3].mean()), 2), payouts=round(float(x[:, 4].mean()), 1), neg_year_pct=round(100 * float((x[:, 0] < 0).mean()), 1)) for p, x in (("T1", a), ("T2", b))}
            r[f"edge-{int(hc*100)}%"] = res
        OUT[name] = r
        print(name, {k: (v["T1"]["per_month"], v["T2"]["per_month"], v["T2"]["accounts_lost_per_year"], v["T2"]["neg_year_pct"]) for k, v in r.items()}, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "smallacct_life2.json"), "w"), indent=1)
