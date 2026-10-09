"""gate84b with the turbo gear only AFTER the Lucid lock (peak >= 2,100 -> threshold fixed at +100): there a $2,000+ loss is needed
to fail, so trading K2 contracts only shortens the last stretch. Plus LO/HI gating on the cushion as before. -> gate84c.csv"""
import sys, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import fast1c as F
from gate84 import vecs
from gate84b import SETS, summ
PERS = F.PERS
@njit(cache=True)
def gear(lH, cH, lL, cL, lT, cT, C1, G, nmin):
    n = len(lH); m = n - nmin; out = np.zeros((m, 2))
    for s in range(m):
        eq = 0.0; pk = 0.0; best = -1e9; r = 0; d = s
        while d < n:
            thr = 100.0 if pk >= 2100.0 else pk - 2000.0
            cu = eq - thr
            if pk >= 2100.0 and cu >= 2000.0: lo_ = lT[d]; c = cT[d]
            elif cu >= C1: lo_ = lH[d]; c = cH[d]
            else: lo_ = lL[d]; c = cL[d]
            if G > 0.0 and c > G: c = G
            if eq + lo_ <= thr: r = -1; break
            eq += c
            if c > best: best = c
            if eq > pk: pk = eq
            if eq >= 3000.0 and best <= 0.5 * eq: r = 1; break
            d += 1
        out[s, 0] = r; out[s, 1] = d - s + 1
    return out
def run(hi, lo, C1, K2, DL, G, per, turbo=None):
    turbo = turbo or hi
    lH, cH = vecs(hi, per, DL); lL, cL = vecs(lo, per, 0.0); lT, cT = vecs(turbo, per, DL / K2 if DL > 0 else 0.0)
    return summ(gear(lH, cH, lL, cL, K2 * lT, K2 * cT, float(C1), float(G), 120))
if __name__ == "__main__":
    rows = []
    PAIRS = [("HOY/ESTABLE", SETS["HOY"], SETS["ESTABLE"]), ("RAPIDO/ESTABLE", SETS["RAPIDO"], SETS["ESTABLE"])]
    for (nm, hi, lo), C1, K2, DL, G in itertools.product(PAIRS, (900, 1200), (1, 2, 3), (0, 700), (0, 1400)):
        r = dict(par=nm, C1=C1, K2=K2, DL=DL, G=G)
        for per in PERS:
            s = run(hi, lo, C1, K2, DL, G, per); r.update({f"{per}_{a}": b for a, b in s.items()})
        rows.append(r)
    R = pd.DataFrame(rows); R.to_csv("gate84c.csv", index=False); pd.set_option("display.width", 320)
    cols = ["par", "C1", "K2", "DL", "G"] + [f"{p}_{a}" for a in ("aprueba", "mediana", "p20", "p30") for p in PERS]
    print(R[cols].round(1).to_string(index=False))
