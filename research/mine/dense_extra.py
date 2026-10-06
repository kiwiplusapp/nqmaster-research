"""Dense grids for the Ultra-ampliado extras that the account simulations referenced but that were never built (silently skipped by
acct_policy.sums): N:ENG0610 (ENGULF_4H 1172 on NQ = NQMaster ENG10) and N:LATEFH (LATE_MOM 1107). Weight 1, FOMC days excluded."""
import os, sys, pickle, numpy as np
sys.path.insert(0, ".")
from dense_build import dense
from ultra_plus_lib import mined
RES = os.path.dirname(os.getcwd()); DN = os.path.join(RES, "tmp", "dense")
meta = pickle.load(open(os.path.join(DN, "meta.pkl"), "rb"))
for per in ("IS", "C24", "REAL"):
    z = dict(np.load(os.path.join(DN, f"{per}.npz"))); new = []
    for key, (src, nm) in {"N:ENG0610": (("ENGULF_4H", 1172), "ENG10"), "N:LATEFH": (("LATE_MOM", 1107), "LATEFH")}.items():
        F = mined(src, per, nm); L, R = dense(F, "nq", per, z["days"]); z[key + "|L"] = L; z[key + "|R"] = R; new.append(key)
        print(per, key, len(F), "trades, $", round(float(R[:, -1].sum())), flush=True)
    np.savez(os.path.join(DN, f"{per}.npz"), **z); meta[per] = sorted(set(meta[per]) | set(new))
pickle.dump(meta, open(os.path.join(DN, "meta.pkl"), "wb")); print("done")
