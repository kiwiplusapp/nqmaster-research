import os, sys, numpy as np
M = "/home/user/nqmaster-research/research/mine"; sys.path.insert(0, M); sys.path.insert(0, os.path.dirname(M)); os.chdir(M)
import exp08_monitor as E
days, atr, mods, Mv, N, post = E.build(with_new=True)
for lo, hi in ((20100701, 20150101), (20150101, 20180101), (20180101, 20200101)):
    m = (days >= lo) & (days < hi); print(lo, hi, "median 100/(2*ATR) =", round(float(np.median(100 / (2 * atr[m]))), 2))
