"""Joint search of the cushion-gated eval policy (Lucid Flex 50K) on the exact dense grids, IS (CFD 2020-23) only:
HI set (cushion >= C1) and LO set (cushion < C1), each = per module group: off / one stream variant at weight 1 or 2.
Objective on IS: share passed within 25 trading days, with a penalty when the eventual pass rate drops below 97% (IS eventual
~97% corresponded to ~90% out of sample for the gated HOY/ESTABLE policy). Alternating coordinate ascent HI -> LO -> C1, 2 rounds,
from several starts. Then every finalist is scored on C24 (CFD 2024-26) and REAL (MNQ + MGC futures 2024-26). -> gate_joint.csv"""
import sys, random, numpy as np, pandas as pd
sys.path.insert(0, ".")
import fast1c as F
from gate84 import POOL, GROUPS, gated, summ
from gate84b import SETS
PERS = F.PERS
_VC = {}
def wvecs(sel, per):
    """sel: tuple of (key, weight)"""
    ck = (sel, per)
    if ck in _VC: return _VC[ck]
    Ls, Cs, nd = F.DATA[per]; L = np.zeros((nd, 1440), np.float32); c = np.zeros(nd)
    for k, w in sel:
        L += w * Ls[k]; c += w * Cs[k]
    out = (L.min(1).astype(np.float64), c)
    if len(_VC) > 6000: _VC.clear()
    _VC[ck] = out; return out
def tup(d): return tuple(sorted((k, w) for k, w in d.values() if k))
def stats(hi, lo, C1, per):
    lH, cH = wvecs(tup(hi), per); lL, cL = wvecs(tup(lo), per)
    o = gated(lH, cH, lL, cL, float(C1), 120); s = summ(o); ps = o[:, 0] == 1; s["p25"] = 100 * (ps & (o[:, 1] <= 25)).mean(); return s
def obj(s): return s["p25"] - 3.0 * max(0.0, 97.0 - s["aprueba"])
OPTS = {g: [(None, 0)] + [(k, w) for k in GROUPS[g] for w in (1, 2)] for g in GROUPS}
def from_keys(keys):
    d = {g: (None, 0) for g in GROUPS}
    for k in keys: d[F.base(k)] = (k, 1)
    return d
def ascend(sel, other, C1, which, rng):
    cur = obj(stats(sel, other, C1, "IS") if which == "hi" else stats(other, sel, C1, "IS")); imp = True
    while imp:
        imp = False
        for g in rng.sample(sorted(GROUPS), len(GROUPS)):
            bo = sel[g]
            for o in OPTS[g]:
                if o == sel[g]: continue
                t = dict(sel); t[g] = o
                v = obj(stats(t, other, C1, "IS") if which == "hi" else stats(other, t, C1, "IS"))
                if v > cur + 1e-9: cur = v; bo = o
            if bo != sel[g]: sel[g] = bo; imp = True
    return sel, cur

if __name__ == "__main__":
    rng = random.Random(7); finals = []
    STARTS = [("HOY", "ESTABLE"), ("RAPIDO", "ESTABLE"), ("HOY", "HOY"), ("RAPIDO", "HOY")]
    for hn, ln in STARTS:
        hi = from_keys(SETS[hn]); lo = from_keys(SETS[ln]); C1 = 1200
        for rnd in range(2):
            hi, v = ascend(hi, lo, C1, "hi", rng); print(hn, ln, "round", rnd, "HI", round(v, 1), flush=True)
            lo, v = ascend(lo, hi, C1, "lo", rng); print(hn, ln, "round", rnd, "LO", round(v, 1), flush=True)
            best = max(((obj(stats(hi, lo, c, "IS")), c) for c in (600, 900, 1200, 1500, 1800)))
            C1 = best[1]; print("  C1 ->", C1, round(best[0], 1), flush=True)
        finals.append((f"{hn}/{ln} optimizada", dict(hi), dict(lo), C1))
    finals += [("HOY/ESTABLE (gate84)", from_keys(SETS["HOY"]), from_keys(SETS["ESTABLE"]), 1200),
               ("RAPIDO/ESTABLE (gate84)", from_keys(SETS["RAPIDO"]), from_keys(SETS["ESTABLE"]), 1200),
               ("HOY sin cambio", from_keys(SETS["HOY"]), from_keys(SETS["HOY"]), 0)]
    rows = []
    for nm, hi, lo, C1 in finals:
        r = dict(politica=nm, C1=C1, hi=" ".join(f"{k}x{w}" for k, w in tup(hi)), lo=" ".join(f"{k}x{w}" for k, w in tup(lo)))
        for per in PERS:
            s = stats(hi, lo, C1, per); r.update({f"{per}_{a}": b for a, b in s.items()})
        rows.append(r)
    R = pd.DataFrame(rows); R.to_csv("gate_joint.csv", index=False)
    pd.set_option("display.width", 320); pd.set_option("display.max_colwidth", 400)
    cols = ["politica", "C1"] + [f"{p}_{a}" for a in ("aprueba", "mediana", "p20", "p30", "quema") for p in PERS]
    print(R[cols].round(1).to_string(index=False))
    for r in rows: print(r["politica"], "| HI:", r["hi"], "| LO:", r["lo"])
