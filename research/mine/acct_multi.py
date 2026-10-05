"""N account slots run in parallel on the SAME market path (same strategy -> correlated), started 0/5/10/15/20 trading days apart.
Block-bootstrap paths (10-day blocks) from each period; EQUILIBRIO vs HOY. Annual income for the whole set of accounts."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_mc import PROT, arrays
from acct_life import life
from acct_policy import hiatr
rng = np.random.default_rng(5); pd.set_option("display.width", 250)
rows = []
for per in ("IS", "C24", "REAL"):
    for name in ("HOY", "EQUILIBRIO"):
        ev, fu, atr_max, X = PROT[name]
        elo, ecl, ec1, ec2 = arrays(per, ev, False); flo, fcl, fc1, fc2 = arrays(per, fu, False)
        okall = np.ones(elo.shape[1], bool); nd = elo.shape[1]; H = 252; out = np.zeros((10, 6))
        tot = {1: [], 3: [], 5: []}
        for b in range(1500):
            idx = np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, (H + 40) // 10 + 1)])[:H + 41]
            E0, E1, F0, F1, OK = elo[:, idx], ecl[:, idx], flo[:, idx], fcl[:, idx], okall[idx]
            slot = []
            for off in (0, 5, 10, 15, 20):
                life(E0[:, off:off + H + 1].copy(), E1[:, off:off + H + 1].copy(), ec1, ec2, F0[:, off:off + H + 1].copy(), F1[:, off:off + H + 1].copy(), fc1, fc2, X, OK[off:off + H + 1].copy(), H, H, 105.2, out)
                slot.append(out[0, 0])
            for n in (1, 3, 5): tot[n].append(sum(slot[:n]))
        for n in (1, 3, 5):
            a = np.array(tot[n]); rows.append(dict(per=per, prot=name, cuentas=n, mes_prom=round(a.mean() / 12), mes_p10=round(np.percentile(a, 10) / 12), mes_p90=round(np.percentile(a, 90) / 12), P_año_negativo=round(100 * (a < 0).mean(), 1)))
    print(per, flush=True)
R = pd.DataFrame(rows); R.to_csv("acct_multi.csv", index=False); print(R.to_string(index=False))
