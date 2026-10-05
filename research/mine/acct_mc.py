"""Robustness of the account protocols: (1) block-bootstrap Monte Carlo of 12-month lifecycles (blocks of 10 trading days resampled
jointly across configs from each period), (2) cost stress: +1 tick per side on every trade (MNQ $1, MGC $2 per round trip x weight).
Protocols (1 contract per module):
  HOY       : eval Ultra, funded Ultra, payout at $5,000
  APROBACION: eval SAFE < $900 <= FULL + daily stop $700 + start only if ATR < 1.15 x median; funded SAFE < $1,500 <= NO-BOOST, payout $6,000
  INGRESO   : eval FULLG (Ultra + gold WinRate + ASIA + ENG0206); funded SAFE < $750 <= FULLG, payout $4,000"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_life import life, CFG, stack, hiatr
from acct_lab import Z, META
T = pickle.load(open("robust_trades.pkl", "rb")); GC = pickle.load(open("gold_curated_trades.pkl", "rb"))
PROT = {"HOY": ((("ULTRA",) * 3, 0, 0, 0.0), (("ULTRA",) * 3, 0, 0, 0.0), 0.0, 5000.0),
        "APROBACION": ((("SAFE", "SAFE", "FULL"), 900, 900, 700.0), (("SAFE", "SAFE", "NOB"), 1500, 1500, 0.0), 1.15, 6000.0),
        "INGRESO": ((("FULLG",) * 3, 0, 0, 0.0), (("SAFE", "SAFE", "FULLG"), 750, 750, 0.0), 0.0, 4000.0),
        "EQUILIBRIO": ((("FULLG",) * 3, 0, 0, 0.0), (("SAFE", "SAFE", "FULL"), 750, 750, 0.0), 0.0, 5000.0),
        "EQ2": ((("FULLG",) * 3, 0, 0, 0.0), (("SAFE", "NOB", "FULL"), 750, 1500, 0.0), 0.0, 4000.0),
        "EQ3": ((("FULLG",) * 3, 0, 0, 0.0), (("SAFE", "FULL", "FULLG"), 750, 1500, 0.0), 0.0, 5000.0),
        "EQUILIBRIO+gating": ((("SAFE", "SAFE", "FULLG"), 600, 600, 1000.0), (("SAFE", "SAFE", "FULL"), 750, 750, 0.0), 0.0, 5000.0)}
# ---- daily trade-count (x weight) per config, for the cost stress
def counts(per, cfg):
    days = Z(per)["days"]; pos = {d: k for k, d in enumerate(days)}; out = np.zeros(len(days))
    for m in CFG[cfg]:
        src, name = m.split(":")
        if src in ("U", "U1"): F = T["Ultra"][per][0]; F = F[F["mod"] == name]; w = np.minimum(F.w, 1.0) if src == "U1" else F.w; extra = 1.0
        elif src == "W": F = T["WR70Plus"][per][0]; F = F[F["mod"] == name]; w = F.w; extra = 1.0
        elif src == "C": F = T["Core6"][per][0]; F = F[F["mod"] == name]; w = F.w; extra = 1.0
        elif src == "G": F = GC[name][per]; w = F.w; extra = 2.0
        else: F = T["Ultra"][per][0].iloc[:0]; w = F.w; extra = 1.0           # LATE15: ~0.17/day, ignored
        for d, ww in zip(F.date.to_numpy(), np.asarray(w)):
            if d in pos: out[pos[d]] += ww * extra
    return out
def arrays(per, spec, stress):
    cfgs, c1, c2, DL = spec; lo, cl = stack(per, cfgs, DL)
    if stress:
        cst = np.array([counts(per, c) for c in cfgs]); lo = lo - cst; cl = cl - cst
    return np.ascontiguousarray(lo), np.ascontiguousarray(cl), c1, c2
def run(per, name, stress=False, mc=0, H=252, rng=None):
    ev, fu, atr_max, X = PROT[name]
    elo, ecl, ec1, ec2 = arrays(per, ev, stress); flo, fcl, fc1, fc2 = arrays(per, fu, stress)
    ok = hiatr(per) < atr_max if atr_max > 0 else np.ones(elo.shape[1], bool)
    out = np.zeros((4000, 6))
    if mc == 0:
        n = life(elo, ecl, ec1, ec2, flo, fcl, fc1, fc2, X, ok, H, 3, 105.2, out); o = out[:n]
    else:
        nd = elo.shape[1]; res = []
        for b in range(mc):
            idx = np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, (H + 20) // 10 + 1)])[:H + 1]
            k = life(elo[:, idx].copy(), ecl[:, idx].copy(), ec1, ec2, flo[:, idx].copy(), fcl[:, idx].copy(), fc1, fc2, X, ok[idx].copy(), H, H, 105.2, out)
            res.append(out[0].copy())
        o = np.array(res)
    return dict(mo=round(o[:, 0].mean() / 12), p10=round(np.percentile(o[:, 0], 10) / 12), p50=round(np.median(o[:, 0]) / 12), P_loss=round(100 * (o[:, 0] < 0).mean(), 1),
                evals=round(o[:, 1].mean(), 2), passes=round(o[:, 2].mean(), 2), fbust=round(o[:, 3].mean(), 2), payouts=round(o[:, 4].mean(), 2))
if __name__ == "__main__" and os.environ.get("ONLY"):
    import sys as _s
    rng = np.random.default_rng(11); rows = []
    for per in ("IS", "C24", "REAL"):
        for name in os.environ["ONLY"].split(","):
            rows.append(dict(test="historia", per=per, prot=name, **run(per, name)))
            rows.append(dict(test="costo +1 tick/lado", per=per, prot=name, **run(per, name, stress=True)))
            rows.append(dict(test="Monte Carlo 2000 años", per=per, prot=name, **run(per, name, mc=2000, rng=rng)))
    pd.set_option("display.width", 250); D_ = pd.DataFrame(rows); D_.to_csv(os.environ.get("OUT", "acct_mc_only.csv"), index=False); print(D_.to_string(index=False)); _s.exit()
if __name__ == "__main__":
    rng = np.random.default_rng(11); pd.set_option("display.width", 250)
    rows = []
    for per in ("IS", "C24", "REAL"):
        for name in PROT:
            rows.append(dict(test="historia", per=per, prot=name, **run(per, name)))
            rows.append(dict(test="costo +1 tick/lado", per=per, prot=name, **run(per, name, stress=True)))
            rows.append(dict(test="Monte Carlo 2000 años", per=per, prot=name, **run(per, name, mc=2000, rng=rng)))
        print(per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("acct_mc.csv", index=False)
    print(R.to_string(index=False))
