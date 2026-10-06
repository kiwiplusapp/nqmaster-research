"""Dense grids for the WR70Plus and Core profiles (module by module, corrected ICT), as-is weights and capped at 1 (no x2).
Keys: WR:<mod>, WR1:<mod>, C6:<mod>, C61:<mod>. Appended to research/tmp/dense/<per>.npz and meta.pkl."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from dense_build import dense
from ict_redo import ictf
from gold_port import conflict_filter
T = pickle.load(open("robust_trades.pkl", "rb")); RES = os.path.dirname(os.getcwd()); DN = os.path.join(RES, "tmp", "dense")
meta = pickle.load(open(os.path.join(DN, "meta.pkl"), "rb"))
for per in ("IS", "C24", "REAL"):
    z = dict(np.load(os.path.join(DN, f"{per}.npz"))); days = z["days"]; new = []
    for prof, tag in (("WR70Plus", "WR"), ("Core6", "C6")):
        F = T[prof][per][0][["date", "mod", "tin", "tout", "d", "u", "w"]]
        F = conflict_filter(pd.concat([F[F["mod"] != "ICT"], ictf(per, 2.0)], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
        for m, g in F.groupby("mod"):
            for key, gg in ((f"{tag}:{m}", g), (f"{tag}1:{m}", g.assign(w=np.minimum(g.w, 1.0)))):
                L, R = dense(gg, "nq", per, days); z[key + "|L"] = L; z[key + "|R"] = R; new.append(key)
    np.savez(os.path.join(DN, f"{per}.npz"), **z); meta[per] = sorted(set(meta[per]) | set(new)); print(per, len(new), "keys", flush=True)
pickle.dump(meta, open(os.path.join(DN, "meta.pkl"), "wb")); print(sorted(k for k in meta["REAL"] if k.startswith(("WR", "C6"))))
