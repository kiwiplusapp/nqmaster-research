"""1-contract study, step 4: 12-month lifecycle per seat (buy eval -> pass -> funded -> payouts -> bust -> buy again), Lucid Flex 25K vs 50K,
Ultra (post-overhaul) 1 contract per module. Rules: Flex payouts (50% of profit up to the cap, min $500, 5 qualifying days, 5 payouts then live
review), funded EOD trailing, lock +100. Funded low gear = per-trade risk cap while the cushion is below c1 x DD.
Slots start every 5 trading days over T1 (2020-23) and T2 (2024-26); policy chosen on T1. Also +1 tick per side. -> smallacct_life.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from smallacct_eval import prep
from robust2_life import SP
import acct1c_lib as A

SETUPS = {"Lucid Flex 50K": dict(T=3000, D=2000, cons=0.5, fee=146.0, Q=150.0, cap=2000.0, Xs=(3000, 4000, 5000)),
          "Lucid Flex 25K": dict(T=1250, D=1000, cons=0.5, fee=89.0, Q=100.0, cap=1000.0, Xs=(1500, 2000, 2500))}
H = 252


def life(P, cfg, ecap, ef, fcap, ff, X, t1, idx, n):
    G = 0.9 * cfg["cons"] * cfg["T"]
    hi = prep(P, ("UltraR", 0), G, 0, t1); lo_e = prep(P, ("UltraR", ecap) if ecap else ("UltraR", 0), G, 0, t1)
    EL = np.ascontiguousarray(np.array([lo_e[0], hi[0]])); EC = np.ascontiguousarray(np.array([lo_e[1], hi[1]]))
    hf = prep(P, ("UltraR", 0), 0.0, 0, t1); lf = prep(P, ("UltraR", fcap), 0.0, 0, t1)
    FL = np.ascontiguousarray(np.array([lf[0], hf[0], hf[0]])); FC = np.ascontiguousarray(np.array([lf[1], hf[1], hf[1]]))
    okst = np.ones(n, np.bool_)
    out = np.zeros((n, 9))
    r = A.life(EL, EC, float(ef * cfg["D"] if ef > 0 else -1e9), cfg["T"], cfg["D"], cfg["cons"], okst, cfg["fee"], FL, FC,
               float(ff * cfg["D"]), float(ff * cfg["D"]), 0, float(X), cfg["Q"], cfg["cap"], cfg["cap"], idx, H, 5, out)
    o = out[:r]
    return o


if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb")); n = len(days); idx = np.arange(n, dtype=np.int64)
    m1 = days < 20240101
    OUT = {}
    for name, cfg in SETUPS.items():
        rows = []
        for ecap in (0, 150, 200, 300):
            for ef in (0.0, 0.5):
                for fcap in (150, 200, 300):
                    for ff in (0.5, 1.0, 1.5):
                        for X in cfg["Xs"]:
                            o = life(P, cfg, ecap, ef, fcap, ff, X, False, idx, n)
                            # slot s covers positions [5k, 5k+H): T1 slots end before 2024, T2 slots start from 2024
                            st = np.arange(len(o)) * 5
                            a = o[(st + H) < np.searchsorted(days, 20240101)]; b = o[st >= np.searchsorted(days, 20240101)]
                            if len(a) == 0 or len(b) == 0: continue
                            rows.append(dict(ecap=ecap, ef=ef, fcap=fcap, ff=ff, X=X, T1=round(float(a[:, 0].mean() / 12)), T2=round(float(b[:, 0].mean() / 12)),
                                             T1_lost=round(float((a[:, 1] - a[:, 2] + a[:, 3]).mean()), 2), T2_lost=round(float((b[:, 1] - b[:, 2] + b[:, 3]).mean()), 2),
                                             T2_negyr=round(100 * float((b[:, 0] < 0).mean()), 1)))
        best = max(rows, key=lambda r: r["T1"])
        # plus 1 tick stress for the T1-best policy
        o = life(P, cfg, best["ecap"], best["ef"], best["fcap"], best["ff"], best["X"], True, idx, n); st = np.arange(len(o)) * 5; d24 = np.searchsorted(days, 20240101)
        a = o[(st + H) < d24]; b = o[st >= d24]
        best["T1_plus1tick"] = round(float(a[:, 0].mean() / 12)); best["T2_plus1tick"] = round(float(b[:, 0].mean() / 12))
        OUT[name] = dict(best=best, grid=rows)
        print(name, "best on T1:", best, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "smallacct_life.json"), "w"), indent=1)
