"""Daily profit lock (stop trading for the day once realized day P&L >= G per contract) in eval and/or funded, k = 1 and 2.
Base = EQ2-style: eval UA+GR (Ultra ampliado + gold Robust), funded UA gating (SAFE<750<=NOB<1500<=FULL) + gold WinRate, payout $4k."""
import sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import prof_grid_lib as PG          # CFG entries for the profile configs
from acct_policy import vec
from acct_size import life_g
EV = "UA_FULL_GR"; FU = ("UA_SAFE_GW", "UA_NOB_GW", "UA_FULL_GW")
T, D, Q, CAP, FEE = 3000.0, 2000.0, 150.0, 2000.0, 105.2; rows = []
for per in ("IS", "C24", "REAL"):
    rng = np.random.default_rng(9); nd = len(vec(per, EV, 0.0, 0.0)[0])
    IDX = [np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, 27)])[:253] for _ in range(400)]
    for k, Ge, Gf in itertools.product((1.0, 2.0), (0.0, 700.0, 1000.0, 1400.0), (0.0, 600.0, 1000.0, 1500.0)):
        ev = vec(per, EV, 0.0, Ge / k if Ge > 0 else 0.0); E = (np.array([ev[0]] * 3), np.array([ev[1]] * 3))
        fv = [vec(per, c, 0.0, Gf / k if Gf > 0 else 0.0) for c in FU]; F = (np.array([v[0] for v in fv]), np.array([v[1] for v in fv]))
        out = np.zeros((1000, 6)); m = life_g(E[0], E[1], k, 0.0, 0.0, F[0], F[1], k, 750.0, 1500.0, 4000.0, T, D, Q, CAP, FEE, 252, 3, out); L = out[:m]
        mc = []; o1 = np.zeros((2, 6))
        for idx in IDX:
            life_g(E[0][:, idx].copy(), E[1][:, idx].copy(), k, 0.0, 0.0, F[0][:, idx].copy(), F[1][:, idx].copy(), k, 750.0, 1500.0, 4000.0, T, D, Q, CAP, FEE, 252, 252, o1); mc.append(o1[0, 0])
        mc = np.array(mc)
        rows.append(dict(per=per, k=int(k), G_eval=Ge, G_fund=Gf, hist=round(L[:, 0].mean() / 12), mc=round(mc.mean() / 12), mc_p10=round(np.percentile(mc, 10) / 12)))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("profit_lock.csv", index=False); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
P = R.pivot_table(index=["k", "G_eval", "G_fund"], columns="per", values=["hist", "mc"], aggfunc="first")
P["worst"] = P.min(axis=1); print(P.sort_values("worst", ascending=False).head(20).to_string()); print(P.loc[(slice(None), 0.0, 0.0), :].to_string())
