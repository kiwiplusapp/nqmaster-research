"""Three-gear eval policy on the exact dense grids (Lucid Flex 50K: 3,000 target, 2,000 EOD trailing locking at +100, best day <= 50%).
cushion = equity - threshold at the start of the day
  cushion <  C1            -> LO set   (stable streams, 1 contract)
  C1 <= cushion < C2       -> HI set   (fast streams, 1 contract)
  cushion >= C2            -> HI set x K2 contracts (turbo: near/after the lock the account can afford it)
optional account daily stop DL (open equity, per base contract, scaled with size) on HI days and daily profit stop G (consistency).
Sets from gate84 (HOY / RAPIDO / ESTABLE). Choices are judged on IS; C24 and REAL are out of sample. -> gate84b.csv"""
import sys, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import fast1c as F
from gate84 import vecs
PERS = F.PERS
SETS = {}
for line in open("gate84_sets.txt"):
    nm, ks = line.split(":", 1); SETS[nm.split(" ")[0]] = ks.split()

@njit(cache=True)
def gear(lH, cH, lL, cL, lT, cT, C1, C2, G, nmin):
    n = len(lH); m = n - nmin; out = np.zeros((m, 2))
    for s in range(m):
        eq = 0.0; pk = 0.0; best = -1e9; r = 0; d = s
        while d < n:
            thr = 100.0 if pk >= 2100.0 else pk - 2000.0
            cu = eq - thr
            if cu >= C2: lo_ = lT[d]; c = cT[d]
            elif cu >= C1: lo_ = lH[d]; c = cH[d]
            else: lo_ = lL[d]; c = cL[d]
            if G > 0.0 and c > G: c = G                       # daily profit stop (approx: stop at G realized)
            if eq + lo_ <= thr: r = -1; break
            eq += c
            if c > best: best = c
            if eq > pk: pk = eq
            if eq >= 3000.0 and best <= 0.5 * eq: r = 1; break
            d += 1
        out[s, 0] = r; out[s, 1] = d - s + 1
    return out

def summ(o):
    ps = o[:, 0] == 1
    return dict(aprueba=100 * ps.mean(), p15=100 * (ps & (o[:, 1] <= 15)).mean(), p20=100 * (ps & (o[:, 1] <= 20)).mean(),
                p30=100 * (ps & (o[:, 1] <= 30)).mean(), mediana=float(np.median(o[ps, 1])) if ps.any() else np.nan, quema=100 * (o[:, 0] == -1).mean())

def run(hi, lo, C1, C2, K2, DL, G, per):
    lH, cH = vecs(hi, per, DL); lL, cL = vecs(lo, per, 0.0)
    lT0, cT0 = vecs(hi, per, DL / K2 if DL > 0 else 0.0) if K2 > 1 else (lH, cH)
    return summ(gear(lH, cH, lL, cL, K2 * lT0, K2 * cT0, float(C1), float(C2), float(G), 120))

if __name__ == "__main__":
    rows = []
    PAIRS = [("HOY/ESTABLE", SETS["HOY"], SETS["ESTABLE"]), ("RAPIDO/ESTABLE", SETS["RAPIDO"], SETS["ESTABLE"]), ("RAPIDO/HOY", SETS["RAPIDO"], SETS["HOY"])]
    grid = list(itertools.product(PAIRS, (900, 1200, 1500), (1800, 2100, 2400, 99999), (2, 3), (0, 700), (0, 1400)))
    for (nm, hi, lo), C1, C2, K2, DL, G in grid:
        if C2 == 99999 and K2 == 3: continue
        r = dict(par=nm, C1=C1, C2=C2, K2=K2 if C2 < 99999 else 1, DL=DL, G=G)
        for per in PERS:
            s = run(hi, lo, C1, C2, K2, DL, G, per); r.update({f"{per}_{a}": b for a, b in s.items()})
        rows.append(r)
    R = pd.DataFrame(rows).drop_duplicates(subset=["par", "C1", "C2", "K2", "DL", "G"])
    R.to_csv("gate84b.csv", index=False)
    pd.set_option("display.width", 320)
    cols = ["par", "C1", "C2", "K2", "DL", "G"] + [f"{p}_{a}" for a in ("aprueba", "mediana", "p20") for p in PERS]
    R["is_obj"] = R.IS_aprueba + R.IS_p20
    print(R.sort_values("is_obj", ascending=False)[cols].head(30).round(1).to_string(index=False))
    ok = R[(R[["IS_aprueba", "C24_aprueba", "REAL_aprueba"]].min(1) >= 84)]
    print("\nAll three periods >= 84% pass, fastest (mean median):")
    ok = ok.assign(med=ok[["IS_mediana", "C24_mediana", "REAL_mediana"]].mean(1)).sort_values("med")
    print(ok[cols].head(20).round(1).to_string(index=False))
