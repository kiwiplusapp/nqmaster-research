import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_life import stack, ev_run
from acct_policy3 import run_apex3
pd.set_option("display.width", 250); rows = []
for nm, (cfgs, c1, c2, DL) in {"Ultra (hoy)": (("ULTRA",) * 3, 0, 0, 0.0), "FULLG (Ultra + oro Robust)": (("FULLG",) * 3, 0, 0, 0.0),
                                "SAFE<600<=FULLG DL1000": (("SAFE", "SAFE", "FULLG"), 600, 600, 1000.0), "SAFE<900<=FULLG DL700": (("SAFE", "SAFE", "FULLG"), 900, 900, 700.0)}.items():
    for per in ("IS", "C24", "REAL"):
        lo, cl = stack(per, cfgs, DL); nd = lo.shape[1]
        r = np.array([ev_run(lo, cl, c1, c2, s, nd) for s in range(nd - 120)]); res = r[:, 0]; days = r[:, 1] - np.arange(nd - 120) + 1
        ok = res == 1; done = res != 0; a = np.array([run_apex3(lo, cl, c1, c2, s, 21) for s in range(nd - 21)])
        rows.append(dict(set=nm, per=per, pass_=round(100 * ok.sum() / done.sum(), 1), bust=round(100 * (res == -1).sum() / done.sum(), 1), p21=round(100 * (ok & (days <= 21)).mean(), 1),
                         days=float(np.median(days[ok])), apex30=round(100 * (a[:, 0] == 1).mean(), 1)))
print(pd.DataFrame(rows).pivot_table(index="set", columns="per", values=["pass_", "bust", "days", "p21", "apex30"], aggfunc="first").to_string())
