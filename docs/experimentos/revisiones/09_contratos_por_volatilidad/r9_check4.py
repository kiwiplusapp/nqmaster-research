"""r9_check4: P&L por punto de ATR por tercil (diario, normalizado) con error estandar y t del tercil bajo vs medio+alto; mismo para alto vs medio."""
import os, sys, numpy as np
MINE = "/home/user/nqmaster-research/research/mine"; os.chdir(MINE); sys.path.insert(0, MINE)
import prop_wf as P, objective as O, exp09_volsize as X
days, M, FU, PER = O.setup(); atr = X.atr_days(days); FIN = M[(0, 4)][2]
for lab, m in (("2020-26", days < P.T2_END), ("T1", days < P.T1_END), ("T2", (days >= P.T1_END) & (days < P.T2_END))):
    a = atr[m]; y = FIN[m] / a * 100; b = np.digitize(a, np.quantile(a, [1/3, 2/3]))
    st = [(y[b == t].mean(), y[b == t].std(ddof=1) / np.sqrt((b == t).sum())) for t in range(3)]
    lo, hi = y[b == 0], y[b >= 1]; t_lo = (hi.mean() - lo.mean()) / np.sqrt(hi.var(ddof=1)/len(hi) + lo.var(ddof=1)/len(lo))
    h2, m2 = y[b == 2], y[b == 1]; t_hi = (h2.mean() - m2.mean()) / np.sqrt(h2.var(ddof=1)/len(h2) + m2.var(ddof=1)/len(m2))
    print(f"{lab}: P&L/ATR x100 por tercil bajo/medio/alto " + " / ".join(f"{u:.1f} (ee {e:.1f})" for u, e in st) + f" | t(medio+alto - bajo) {t_lo:.2f} | t(alto - medio) {t_hi:.2f}")
