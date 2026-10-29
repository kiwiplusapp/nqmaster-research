import os, sys, numpy as np, pandas as pd
M = "/home/user/nqmaster-research/research/mine"; sys.path.insert(0, M); sys.path.insert(0, os.path.dirname(M)); os.chdir(M)
from wrq_lib import getD
D = getD("nqdb.npz")
for a in ("atr", "daydate", "day", "ro", "date", "om"):
    v = getattr(D, a, None); print(a, None if v is None else (np.shape(v), v[:3]))
