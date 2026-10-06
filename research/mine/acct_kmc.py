"""Robustness of the contract-size candidates: history, +1 tick per side cost stress, 2,000 block-bootstrap years."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_size import life_g
from acct_life import stack
from acct_mc import counts
pd.set_option("display.width", 250)
T, D, Q, CAP, FEE = 3000.0, 2000.0, 150.0, 2000.0, 105.2
CAND = {"EQ2 1/1 $4k": (1, 1, 4000.0, 750, 1500), "2/2 $4k": (2, 2, 4000.0, 750, 1500), "2/2 $5k": (2, 2, 5000.0, 750, 1500),
        "2/1 $4k": (2, 1, 4000.0, 750, 1500), "1/2 $4k": (1, 2, 4000.0, 750, 1500), "2/2 $4k colchón 1500/3000": (2, 2, 4000.0, 1500, 3000)}
rng = np.random.default_rng(21); rows = []
for per in ("IS", "C24", "REAL"):
    E = stack(per, ("FULLG",) * 3, 0.0); F = stack(per, ("SAFE", "NOB", "FULL"), 0.0)
    cE = np.array([counts(per, "FULLG")] * 3); cF = np.array([counts(per, c) for c in ("SAFE", "NOB", "FULL")])
    for nm, (ek, fk, X, c1, c2) in CAND.items():
        for test in ("historia", "costo +1 tick", "Monte Carlo"):
            elo, ecl = E; flo, fcl = F
            if test == "costo +1 tick": elo, ecl, flo, fcl = elo - cE, ecl - cE, flo - cF, fcl - cF
            out = np.zeros((4000, 6))
            if test != "Monte Carlo":
                m = life_g(np.ascontiguousarray(elo), np.ascontiguousarray(ecl), float(ek), 0.0, 0.0, np.ascontiguousarray(flo), np.ascontiguousarray(fcl), float(fk), float(c1), float(c2), X, T, D, Q, CAP, FEE, 252, 3, out); L = out[:m, 0]
            else:
                nd = elo.shape[1]; L = []
                for b in range(2000):
                    idx = np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, 27)])[:253]
                    life_g(elo[:, idx].copy(), ecl[:, idx].copy(), float(ek), 0.0, 0.0, flo[:, idx].copy(), fcl[:, idx].copy(), float(fk), float(c1), float(c2), X, T, D, Q, CAP, FEE, 252, 252, out); L.append(out[0, 0])
                L = np.array(L)
            rows.append(dict(per=per, cand=nm, test=test, mo=round(L.mean() / 12), p10=round(np.percentile(L, 10) / 12), P_loss=round(100 * (L < 0).mean(), 1)))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("acct_kmc.csv", index=False)
print(R.pivot_table(index=["cand"], columns=["per", "test"], values="mo").to_string())
print(R.pivot_table(index=["cand"], columns=["per", "test"], values="p10").to_string())
print(R[R.test == "Monte Carlo"].pivot_table(index="cand", columns="per", values="P_loss").to_string())
