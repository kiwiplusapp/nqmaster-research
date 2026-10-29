"""r8: where does WH lose in 2020-26? half-size days and P&L cost per year; CUSUM level at 2020-01-02."""
import os, sys, numpy as np
M = "/home/user/nqmaster-research/research/mine"; sys.path.insert(0, M); sys.path.insert(0, os.path.dirname(M)); os.chdir(M)
import exp08_monitor as E
days, atr, mods, Mv, N, post = E.build(with_new=True)
def path(reset2020):
    n = len(days); s = 0.0; until = -1; S = np.zeros(n); half = np.zeros(n, bool); allm = list(range(len(mods))); col = {m: i for i, m in enumerate(mods)}
    for t in range(n):
        if reset2020 and days[t] == days[days >= 20200101][0]: s = 0.0
        act = fb if t < until else allm
        half[t] = t >= until and s > E.HW; S[t] = s
        if t >= until:
            s = max(0.0, s + E.K - E.zday(Mv[t, act].sum(), t, atr, post, "corregido"))
            if s > E.Hh:
                s = 0.0; fb = [col[m] for m in E.review_set(N, mods, int(days[t]))]; until = t + 1 + 252
    return S, half
for r in (False, True):
    S, half = path(r); full = Mv.sum(1)
    print(f"reset2020={r}: CUSUM at first 2020 day {S[days >= 20200101][0]:.2f} (aviso {E.HW}, alarma {E.Hh})")
    for y in range(2018, 2027):
        m = (days // 10000) == y; print(f"   {y}: half days {half[m].sum():3d}  cost {-(0.5 * full[m & half]).sum():8.0f}")
