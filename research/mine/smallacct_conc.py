"""1-contract study, step 10: cap on simultaneously OPEN contracts (module trades skipped when K contracts are already open), 25K / 50K evals,
UltraR trade list (cand16_trades.pkl).  P(funded <= 22 trading days) with serial restarts, T1 vs T2.  -> smallacct_conc.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from smallacct_eval import SETUPS
from smallacct_protocol import outcomes, protocol


def cap_open(X, K):
    keep = np.zeros(len(X), bool); X = X.reset_index(drop=True)
    for d, g in X.groupby("date"):
        g = g.sort_values(["tin", "tout"]); live = []
        for i, r in zip(g.index, g.itertuples()):
            live = [(to, w) for (to, w) in live if to > r.tin]
            if sum(w for _, w in live) + r.w <= K: keep[i] = True; live.append((r.tout, r.w))
    return X[keep]


if __name__ == "__main__":
    E = RB.setup(); days = pickle.load(open(os.path.join(SP, "robust2_paths.pkl"), "rb"))[0]; n = len(days)
    X0 = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["UltraR"][0]; X0 = X0[X0.date.isin(days)]
    X0 = RB.attach(X0, E)
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 50]
    OUT = {}
    for K in (3, 4, 5, 6, 8, 99):
        X = X0 if K == 99 else cap_open(X0, K)
        low, close, fin = full_paths(X, days); c = (X.w * 1.0).groupby(X.date).sum().reindex(days, fill_value=0.0).to_numpy()
        r = {}
        for name in ("Lucid Flex 25K", "Lucid Flex 50K", "Bulenox Opt2 25K"):
            T, D, cons, mind, dll, fee = SETUPS[name]; G = 0.9 * cons * T if cons > 0 else 0.0
            lo, cl = vectors(low - c[:, None], close - c[:, None], fin - c, G)
            if dll > 0:
                hit = lo <= -dll; cl = np.where(hit, -float(dll), cl); lo = np.where(hit, -float(dll), lo)
            EL = np.ascontiguousarray(np.array([lo, lo])); EC = np.ascontiguousarray(np.array([cl, cl]))
            res, dd = outcomes(EL, EC, -1e9, T, D, cons, mind, n)
            r[name] = dict(W22=(protocol(res, dd, s1, 22, 1, 0, fee)[0], protocol(res, dd, s2, 22, 1, 0, fee)[0]), W33=(protocol(res, dd, s1, 33, 1, 0, fee)[0], protocol(res, dd, s2, 33, 1, 0, fee)[0]))
        OUT[K] = dict(trades=int(len(X)), mu_day=round(float(fin.mean())), **r)
        print("K", K, "trades", len(X), "mean/day", round(float(fin.mean())), {k: v["W22"] for k, v in r.items()}, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "smallacct_conc.json"), "w"), indent=1)
