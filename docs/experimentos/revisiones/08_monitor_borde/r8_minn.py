"""r8: plan wording 'PF > 1.05 con >= 20 trades' read strictly (modules with < 20 trades OFF) vs code (unknown modules stay ON)."""
import os, sys, numpy as np
M = "/home/user/nqmaster-research/research/mine"; sys.path.insert(0, M); sys.path.insert(0, os.path.dirname(M)); os.chdir(M)
import exp08_monitor as E, os_adapt as O
days, atr, mods, Mv, N, post = E.build(with_new=True)
for d in (20120925, 20150519):
    lo = d - 50000; T = N[(N.date >= lo) & (N.date < d)]
    few = [m for m in mods if (T["mod"] == m).sum() < 20]; print(d, "modules with < 20 trades in the window (kept ON by the code):", few, "| window starts", max(lo, int(N.date.min())))
def strict(N_, mods_, d):
    lo = d - 50000; T = N_[(N_.date >= lo) & (N_.date < d)]
    return [m for m in mods_ if len(T[T["mod"] == m]) >= 20 and O.pf(T[T["mod"] == m].x.to_numpy()) > 1.05]
E.review_set = strict
x, al, *_ = E.run(days, atr, mods, Mv, N, post, "W252", E.K, E.Hh, E.HW)
print("W252 strict reading:", al, {q: O.stats(x[(days >= lo) & (days < hi)]) for q, (lo, hi) in E.PER.items()})
