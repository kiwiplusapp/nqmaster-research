"""Federico 2026-10-08: ~84% pass at ONE contract, faster than ~6 weeks. Cushion-gated module sets on the exact dense grids.
HI set (fast, high mu) while the cushion over the Lucid threshold is >= C; LO set (stable, high theta = 2 mu / sigma^2) below C;
optional account daily stop DL (flatten at -DL open equity) on HI days. Only streams implemented in NQMaster / GoldMaster.
Step 1: per-stream mu, sigma, theta per period.  Step 2: HI = best p30 mix (IS search), LO = best eventual-pass mix given HI and C
(IS search).  Step 3: grid C x DL for several HI/LO pairs, all periods.  Choices on IS only; C24 / REAL are out of sample.
-> gate84_streams.csv, gate84.csv"""
import sys, random, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import fast1c as F
PERS = F.PERS
NOT_IMPL = {"N:NM22", "G:DRIVE11", "G:ASIA05"}
POOL = [k for k in F.KEYS if k not in NOT_IMPL]
GROUPS = {}
for k in POOL: GROUPS.setdefault(F.base(k), []).append(k)

_VC = {}
def vecs(keys, per, DL=0.0):
    ck = (tuple(sorted(keys)), per, DL)
    if ck in _VC: return _VC[ck]
    out = _vecs(keys, per, DL)
    if len(_VC) > 20000: _VC.clear()
    _VC[ck] = out; return out
def _vecs(keys, per, DL=0.0):
    Ls, Cs, nd = F.DATA[per]; L = np.zeros((nd, 1440), np.float32); c = np.zeros(nd)
    for k in keys: L += Ls[k]; c += Cs[k]
    low = L.min(1).astype(np.float64)
    if DL > 0:
        hit = L <= -DL; has = hit.any(1); t = hit.argmax(1)
        for d in np.nonzero(has)[0]: low[d] = L[d, :t[d] + 1].min(); c[d] = L[d, t[d]]
    return low, c

@njit(cache=True)
def gated(lH, cH, lL, cL, C, nmin):
    n = len(lH); m = n - nmin; out = np.zeros((m, 2))
    for s in range(m):
        eq = 0.0; pk = 0.0; best = -1e9; r = 0; d = s
        while d < n:
            thr = 100.0 if pk >= 2100.0 else pk - 2000.0
            hi = (eq - thr) >= C
            lo_ = lH[d] if hi else lL[d]; c = cH[d] if hi else cL[d]
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
    return dict(aprueba=100 * ps.mean(), p20=100 * (ps & (o[:, 1] <= 20)).mean(), p30=100 * (ps & (o[:, 1] <= 30)).mean(),
                mediana=float(np.median(o[ps, 1])) if ps.any() else np.nan, quema=100 * (o[:, 0] == -1).mean())

def run(hi, lo, C, DL, per):
    lH, cH = vecs(hi, per, DL); lL, cL = vecs(lo, per, 0.0)
    return summ(gated(lH, cH, lL, cL, float(C), 120))

def search(obj, start_sets, groups, fixed_eval, n_starts=8, seed=1):
    """coordinate ascent over one module set; fixed_eval(keys) -> stats on IS"""
    random.seed(seed); found = []
    for st in start_sets[:n_starts]:
        sel = {g: st.get(g) for g in groups}; imp = True
        cur = obj(fixed_eval([k for k in sel.values() if k]))
        while imp:
            imp = False
            for g in random.sample(sorted(groups), len(groups)):
                bk = sel[g]
                for k in groups[g] + [None]:
                    if k == sel[g]: continue
                    trial = dict(sel); trial[g] = k
                    o = obj(fixed_eval([x for x in trial.values() if x]))
                    if o > cur + 1e-9: cur = o; bk = k
                if bk != sel[g]: sel[g] = bk; imp = True
        found.append((cur, sorted(k for k in sel.values() if k)))
    found.sort(key=lambda x: -x[0]); return found

if __name__ == "__main__":
    pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 250); pd.set_option("display.max_rows", 200)
    # step 1: streams
    rows = []
    cur = sorted(F.WRN_GW.values())
    for per in PERS:
        _, cc = vecs(cur, per)
        for k in POOL:
            c = F.DATA[per][1][k]; sd = c.std()
            rows.append(dict(per=per, key=k, mu=c.mean(), sd=sd, theta=2000 * c.mean() / sd ** 2 if sd > 0 else np.nan, corr_cur=np.corrcoef(c, cc)[0, 1] if sd > 0 else np.nan))
    S = pd.DataFrame(rows); S.to_csv("gate84_streams.csv", index=False)
    P = S.pivot_table(index="key", columns="per", values=["mu", "theta", "corr_cur"]).round(3)
    print(P.sort_values(("theta", "IS"), ascending=False).to_string())
    # step 2a: HI = max p30 on IS (no gating) over the implementable pool
    starts = [dict(F.WRN_GW)] + [{g: random.choice(GROUPS[g] + [None, None]) for g in GROUPS} for _ in range(7)]
    his = search(lambda s: s["p30"], starts, GROUPS, lambda keys: run(keys, keys, 0, 0, "IS"), n_starts=8, seed=2)
    print("HI candidates (IS p30):", [(round(o, 1), len(k)) for o, k in his[:3]], flush=True)
    HI = his[0][1]
    # step 2b: LO = max eventual pass on IS with HI fixed and C = 1000
    lstarts = [dict(F.WRN_GW), {g: None for g in GROUPS}] + [{g: random.choice(GROUPS[g] + [None, None, None]) for g in GROUPS} for _ in range(4)]
    los = search(lambda s: s["aprueba"] + 0.2 * s["p30"], lstarts, GROUPS, lambda keys: run(HI, keys if keys else ["G:OD1030"], 1000, 0, "IS"), n_starts=6, seed=3)
    print("LO candidates:", [(round(o, 1), len(k)) for o, k in los[:3]], flush=True)
    LO = los[0][1]
    SETS = {"HOY (WR70Plus+noche+oro WR)": cur, "RAPIDO (busqueda)": HI, "ESTABLE (busqueda)": LO}
    for nm, ks in SETS.items(): print(nm, " ".join(ks))
    # step 3: grid
    res = []
    PAIRS = [("HOY", cur, cur), ("RAPIDO", HI, HI), ("ESTABLE", LO, LO), ("RAPIDO/ESTABLE", HI, LO), ("RAPIDO/HOY", HI, cur), ("HOY/ESTABLE", cur, LO)]
    for (nm, hi, lo), C, DL in itertools.product(PAIRS, (0, 300, 600, 900, 1200, 1500, 2000), (0, 500, 700, 900)):
        if hi is lo and C > 0: continue
        r = dict(par=nm, C=C, DL=DL)
        for per in PERS:
            s = run(hi, lo, C, DL, per); r.update({f"{per}_{a}": b for a, b in s.items()})
        res.append(r)
    R = pd.DataFrame(res)
    for a in ("aprueba", "p30", "mediana"): R[f"oos_{a}"] = R[[f"C24_{a}", f"REAL_{a}"]].mean(1)
    R.to_csv("gate84.csv", index=False)
    cols = ["par", "C", "DL", "IS_aprueba", "C24_aprueba", "REAL_aprueba", "IS_p30", "C24_p30", "REAL_p30", "IS_mediana", "C24_mediana", "REAL_mediana"]
    print("\nTop by IS (aprueba + 0.5 p30):")
    R["is_obj"] = R.IS_aprueba + 0.5 * R.IS_p30
    print(R.sort_values("is_obj", ascending=False)[cols].head(25).round(1).to_string(index=False))
    print("\nBaselines:"); print(R[(R.C == 0) & (R.DL == 0)][cols].round(1).to_string(index=False))
    with open("gate84_sets.txt", "w") as f:
        for nm, ks in SETS.items(): f.write(nm + ": " + " ".join(ks) + "\n")
