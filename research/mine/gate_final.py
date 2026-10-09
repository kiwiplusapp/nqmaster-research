"""Final candidates for Federico's 1-contract eval (Lucid Flex 50K), exact dense grids:
  HOY      = WR70Plus + night + gold WinRate, no gating (what he runs)
  A        = Ultra(ampliado)+night (HI) / ESTABLE NQ (LO) + gold WinRate, gate at cushion C
  A-oro2   = same with gold WinRate at 2 MGC
  B        = RAPIDO/ESTABLE (searched sets, gold switches with the gear)
History (every start / ATR<1.15 starts) + block bootstrap (20-day blocks, 2,000 synthetic 2-year paths per period, same paths for
every policy -> paired win probability vs HOY). -> gate_final.csv, gate_final_boot.csv"""
import sys, itertools, numpy as np, pandas as pd
sys.path.insert(0, ".")
import fast1c as F
import prof_grid_lib  # noqa: F401
from acct_life import CFG
from gate84 import vecs, gated, summ
from gate84b import SETS
from acct_policy import hiatr
PERS = F.PERS
NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]; GW = ["G:OD1030", "G:ENG0408", "G:SVWAP22"]
UA = [k.replace("U:ICT", "U:ICTF").replace("ICTFF", "ICTF") for k in CFG["UA_FULL"]] + NIGHT
EST = [k for k in SETS["ESTABLE"] if not k.startswith("G:")]
def wv(keys, w, per):
    l, c = vecs([k for k in keys if k in F.KEYS], per); return l, c
def combo(nq, gold, gw, per):
    l1, c1 = vecs([k for k in nq if k in F.KEYS], per)
    if not gold: return l1, c1
    Ls, Cs, nd = F.DATA[per]; L = np.zeros((nd, 1440), np.float32); c = np.zeros(nd)
    for k in nq:
        if k in F.KEYS: L += Ls[k]; c += Cs[k]
    for k in gold: L += gw * Ls[k]; c += gw * Cs[k]
    return L.min(1).astype(np.float64), c
POL = {"HOY (sin cambio)": (SETS["HOY"], [], SETS["HOY"], [], 1, 0),
       "A: Ultra+noche / Estable + oro WR, C1200": (UA, GW, EST, GW, 1, 1200), "A: ... C1500": (UA, GW, EST, GW, 1, 1500),
       "A-oro2: oro WR x2, C1200": (UA, GW, EST, GW, 2, 1200), "A-oro2: ... C1500": (UA, GW, EST, GW, 2, 1500),
       "B: Rapido/Estable (oro cambia), C1200": (SETS["RAPIDO"], [], SETS["ESTABLE"], [], 1, 1200)}
if __name__ == "__main__":      # analysis only when run directly (other scripts import the helpers)
    VEC = {}
    for nm, (hn, hg, ln, lg, gw, C) in POL.items():
        for per in PERS:
            VEC[(nm, per)] = (combo(hn, hg, gw, per), combo(ln, lg, gw, per), C)
    rows = []
    for nm in POL:
        for per in PERS:
            (lH, cH), (lL, cL), C = VEC[(nm, per)]
            o = gated(lH, cH, lL, cL, float(C), 120); m = len(o); atr = hiatr(per)[:m]
            for fn, mask in (("todos", np.ones(m, bool)), ("ATR<1.15", atr < 1.15)):
                rows.append(dict(politica=nm, per=per, arranque=fn, **summ(o[mask])))
    R = pd.DataFrame(rows); R.to_csv("gate_final.csv", index=False)
    pd.set_option("display.width", 260)
    print(R.pivot_table(index=["politica", "arranque"], columns="per", values=["aprueba", "mediana", "p30"]).round(1).to_string())
    # block bootstrap: synthetic 504-day paths from 20-day blocks of the period; every start of the synthetic path (>=120 days left)
    rng = np.random.default_rng(42); B = []
    for per in ("C24", "REAL"):
        nd = len(VEC[("HOY (sin cambio)", per)][0][0])
        for b in range(400):
            idx = np.concatenate([np.arange(s, s + 20) % nd for s in rng.integers(0, nd, 26)])[:504]
            res = {}
            for nm in POL:
                (lH, cH), (lL, cL), C = VEC[(nm, per)]
                o = gated(lH[idx].copy(), cH[idx].copy(), lL[idx].copy(), cL[idx].copy(), float(C), 120); s = summ(o); res[nm] = s
            for nm in POL: B.append(dict(per=per, b=b, politica=nm, aprueba=res[nm]["aprueba"], mediana=res[nm]["mediana"], gana_a_hoy=res[nm]["aprueba"] > res["HOY (sin cambio)"]["aprueba"]))
    BB = pd.DataFrame(B); BB.to_csv("gate_final_boot.csv", index=False)
    q = BB.groupby(["politica", "per"]).agg(aprueba_med=("aprueba", "median"), p10=("aprueba", lambda x: np.percentile(x, 10)), p90=("aprueba", lambda x: np.percentile(x, 90)),
                                             mediana_dias=("mediana", "median"), prob_gana_hoy=("gana_a_hoy", "mean")).round(2)
    print(q.to_string())
