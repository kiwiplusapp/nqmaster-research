"""Eval-specific position sizing policies (same strategies, same market). Block-bootstrap of daily portfolio P&L
(per 1 MNQ per module). Policy chosen on CFD 2020-26, checked on REAL MNQ 2024-26."""
import itertools, numpy as np, pandas as pd
from numba import njit
MC, MF, mods = pd.read_pickle("daily_mats.pkl")
w = pd.Series({"MOM11a": 1, "MOM11d": 1, "ORB60": 1, "VWP60": 1, "MSEQ": 1, "CRT11": 1, "ORB30": 0, "ORB15": 0, "VWP30": 0})
XC = (MC[w.index] * w).sum(axis=1).to_numpy(); XF = (MF[w.index] * w).sum(axis=1).to_numpy()

def paths(x, n=20000, L=20, block=5, seed=1):
    rng = np.random.default_rng(seed); out = np.empty((n, L))
    for i in range(n):
        p = []
        while len(p) < L:
            s = rng.integers(0, len(x) - block); p.extend(x[s:s + block])
        out[i] = p[:L]
    return out

@njit(cache=True)
def run(P, T, D, khi, klo, c1, near, klast):
    n, L = P.shape; ok = 0; bust = 0; dsum = 0.0
    for i in range(n):
        eq = 0.0; pk = 0.0
        for t in range(L):
            cushion = eq - (pk - D)
            k = khi if cushion > c1 * D else klo
            if near > 0 and (T - eq) < near * T: k = min(k, klast)
            eq += k * P[i, t]; pk = max(pk, eq)
            if eq >= T: ok += 1; dsum += t + 1; break
            if eq <= pk - D: bust += 1; break
    return ok / n, bust / n, dsum / max(ok, 1)

if __name__ == "__main__":
    PC20 = paths(XC); PF20 = paths(XF, seed=2)
    rows = []
    for acc, T, D in (("25K", 1500, 1500), ("50K", 3000, 2500)):
        for khi, klo, c1, near, klast in itertools.product((2, 3, 4, 5, 6, 8), (1, 2, 3), (0.0, 0.3, 0.5, 0.7), (0.0, 0.25, 0.5), (1, 2, 3)):
            if klo > khi or (near == 0 and klast != 1): continue
            a = run(PC20, T, D, khi, klo, c1, near, klast); b = run(PF20, T, D, khi, klo, c1, near, klast)
            rows.append(dict(acc=acc, khi=khi, klo=klo, c1=c1, near=near, klast=klast, cfd_pass=round(a[0]*100,1), cfd_bust=round(a[1]*100,1), cfd_days=round(a[2],1),
                             real_pass=round(b[0]*100,1), real_bust=round(b[1]*100,1), real_days=round(b[2],1)))
    g = pd.DataFrame(rows); g.to_csv("sizing.csv", index=False)
    for acc in ("25K", "50K"):
        s = g[g.acc == acc]
        print(f"\n== {acc}: fixed-size baseline (c1=0, near=0)")
        print(s[(s.c1 == 0) & (s.near == 0) & (s.klo == 1)][["khi", "cfd_pass", "cfd_bust", "cfd_days", "real_pass", "real_bust", "real_days"]].to_string(index=False))
        print(f"== {acc}: best dynamic policies by CFD pass rate (<=20 days)")
        print(s.sort_values("cfd_pass", ascending=False).head(12).to_string(index=False))
