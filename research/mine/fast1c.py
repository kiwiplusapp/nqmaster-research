"""Federico 2026-10-08: pass ~84% at ONE contract per module, but faster than ~6 weeks.
Lever: with 1 contract the pass odds are set by theta = 2 mu / sigma^2 and the speed by mu. Adding streams that raise mu without
lowering theta speeds the eval up at the same pass rate. This search chooses, per module, which dense stream to run (off / Ultra
version with boosts / no-boost version / WR70Plus version / gold / night ...) to maximise the share of evals passed within 30
trading days on IS (CFD 2020-23); the winners are then checked on C24 (CFD 2024-26) and REAL (MNQ + MGC futures 2024-26).
Exact dense minute grids (intraday adverse equity), Lucid Flex 50K: target 3,000, MLL 2,000 EOD trailing locking at +100,
best day <= 50% of profit. -> fast1c.csv"""
import sys, random, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
from acct_lab import META, Z

def base(m):
    b = m.split(":")[1]
    if b.startswith("VOLB"): return "VOLB"
    return "ICT" if b in ("ICT", "ICTF") else b
PERS = ("IS", "C24", "REAL")
KEYS = sorted(set(META["IS"]) & set(META["C24"]) & set(META["REAL"]))
KEYS = [k for k in KEYS if not k.startswith("U:ICT") or k == "U:ICTF"]     # biased ICT sim out; corrected ICTF in
KEYS = [k for k in KEYS if k not in ("U:ICT", "U1:ICT", "WR:ICT", "WR1:ICT", "C6:ICT", "C61:ICT")]
GROUPS = {}
for k in KEYS: GROUPS.setdefault(base(k), []).append(k)
DATA = {}
for per in PERS:
    z = Z(per); Ls = {}; Cs = {}
    for k in KEYS:
        Ls[k] = np.asarray(z[k + "|L"], np.float32); Cs[k] = np.asarray(z[k + "|R"][:, -1], np.float64)
    DATA[per] = (Ls, Cs, len(z["days"])); print(per, len(z["days"]), "days", len(KEYS), "streams", flush=True)

@njit(cache=True)
def runs(low, close, nmin):
    """every start with >= nmin days left: result (1 pass / -1 bust / 0 open) and days used"""
    n = len(low); m = n - nmin; out = np.zeros((m, 2))
    for s in range(m):
        eq = 0.0; pk = 0.0; best = -1e9; r = 0; d = s
        while d < n:
            thr = 100.0 if pk >= 2100.0 else pk - 2000.0
            if eq + low[d] <= thr: r = -1; break
            c = close[d]; eq += c
            if c > best: best = c
            if eq > pk: pk = eq
            if eq >= 3000.0 and best <= 0.5 * eq: r = 1; break
            d += 1
        out[s, 0] = r; out[s, 1] = d - s + 1
    return out

def stats_of(low, close):
    o = runs(low, close, 120); ps = o[:, 0] == 1
    return dict(aprueba=100 * ps.mean(), quema=100 * (o[:, 0] == -1).mean(), p20=100 * (ps & (o[:, 1] <= 20)).mean(),
                p30=100 * (ps & (o[:, 1] <= 30)).mean(), mediana=float(np.median(o[ps, 1])) if ps.any() else np.nan,
                mu=close.mean(), sd=close.std())

def evaluate(sel, per):
    Ls, Cs, nd = DATA[per]; L = np.zeros((nd, 1440), np.float32); c = np.zeros(nd)
    for g, k in sel.items():
        if k is not None: L += Ls[k]; c += Cs[k]
    return stats_of(L.min(1).astype(np.float64), c)

class Inc:
    """incremental sums for coordinate ascent on one period"""
    def __init__(self, sel, per):
        self.per = per; Ls, Cs, nd = DATA[per]; self.L = np.zeros((nd, 1440), np.float32); self.c = np.zeros(nd); self.sel = dict(sel)
        for g, k in sel.items():
            if k is not None: self.L += Ls[k]; self.c += Cs[k]
    def score_swap(self, g, k, obj):
        Ls, Cs, _ = DATA[self.per]; old = self.sel.get(g)
        L = self.L; c = self.c
        if old is not None: L = L - Ls[old]; c = c - Cs[old]
        if k is not None: L = L + Ls[k]; c = c + Cs[k]
        return obj(stats_of(L.min(1).astype(np.float64), c))
    def apply(self, g, k):
        Ls, Cs, _ = DATA[self.per]; old = self.sel.get(g)
        if old is not None: self.L -= Ls[old]; self.c -= Cs[old]
        if k is not None: self.L += Ls[k]; self.c += Cs[k]
        self.sel[g] = k

def obj(s): return s["p30"]

WRN_GW = {base(k): k for k in ["WR:" + m for m in ("CRT11", "MOM11", "MSEQ", "MSEQS", "ORB60", "ORB90", "REV06", "VOLB_tf1", "VW13", "VW13b")]
          + ["U:ICTF", "N:LATE15", "N:NF05", "N:LF06", "N:LF0430", "G:OD1030", "G:ENG0408", "G:SVWAP22"]}

if __name__ == "__main__":
    rows = []
    def report(name, sel):
        r = dict(mezcla=name, mods=" ".join(sorted(k for k in sel.values() if k)))
        for per in PERS:
            s = evaluate(sel, per); r.update({f"{per}_{a}": b for a, b in s.items()})
        rows.append(r)
        print(name, {k: round(v, 1) for k, v in r.items() if isinstance(v, float)}, flush=True)
    report("WR70Plus+noche+oro WinRate (hoy, 1 contrato)", WRN_GW)
    random.seed(5); found = []
    starts = [dict(WRN_GW)] + [{g: random.choice(GROUPS[g] + [None, None]) for g in GROUPS} for _ in range(11)]
    for i, st in enumerate(starts):
        sel = {g: st.get(g) for g in GROUPS}; inc = Inc(sel, "IS"); imp = True
        while imp:
            imp = False
            for g in random.sample(sorted(GROUPS), len(GROUPS)):
                cur = inc.score_swap(g, inc.sel[g], obj); bk = inc.sel[g]
                for k in GROUPS[g] + [None]:
                    if k == inc.sel[g]: continue
                    o = inc.score_swap(g, k, obj)
                    if o > cur + 1e-9: cur = o; bk = k
                if bk != inc.sel[g]: inc.apply(g, bk); imp = True
        key = " ".join(sorted(k for k in inc.sel.values() if k))
        found.append((obj(evaluate(inc.sel, "IS")), key, dict(inc.sel))); print("start", i, round(found[-1][0], 1), flush=True)
    found.sort(key=lambda x: -x[0]); seen = set()
    for o, key, sel in found:
        if key in seen: continue
        seen.add(key); report(f"busqueda IS p30={o:.1f}", sel)
        if len(seen) >= 6: break
    R = pd.DataFrame(rows); R.to_csv("fast1c.csv", index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 250)
    for a in ("aprueba", "p30", "p20", "mediana", "quema"):
        print(a); print(R[["mezcla"] + [f"{p}_{a}" for p in PERS]].round(1).to_string(index=False))
    print(R[["mezcla", "mods"]].to_string(index=False))
