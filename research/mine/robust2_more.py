"""Robustness lab, step 1b: extra risk-cap variants (Ultra cap 150 / 250, WR70Plus cap 150 / 250) and +1 tick per side cost
versions of the key sets, appended to the scratchpad paths file (robust2_build.minute_paths)."""
import os, sys, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_build import minute_paths, SP
if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "robust2_paths.pkl"), "rb"))
    TR = pickle.load(open(os.path.join(HERE, "robust2_trades.pkl"), "rb"))
    for base in ("Ultra", "WR70Plus"):
        for cap in (150, 250):
            TR[f"{base}_cap{cap}"] = TR[base][TR[base].risk <= cap]
    for k in ("Ultra_cap150", "Ultra_cap250", "WR70Plus_cap150", "WR70Plus_cap250"):
        lo, cl, fin = minute_paths(TR[k], days); P[k] = (np.minimum(lo, cl), cl); print(k, len(TR[k]), flush=True)
    # +1 tick per side stress: -$1 per contract per trade (2 x 0.25 pt x $2) on every trade, applied to the day vectors
    for k in list(P):
        if k.endswith("_t1"): continue
        X = TR[k]; c = (X.w * 1.0).groupby(X.date).sum().reindex(days, fill_value=0.0).to_numpy()
        P[k + "_t1"] = (P[k][0] - c, P[k][1] - c)
    pickle.dump((days, P), open(os.path.join(SP, "robust2_paths.pkl"), "wb"))
    pickle.dump(TR, open(os.path.join(HERE, "robust2_trades.pkl"), "wb"))
