"""Federico 2026-10-08: 'can I remove the consistency rule at Lucid?'. LucidFlex has no option to remove it (support article
2026-08-26: largest day / profit <= 50% to pass); LucidPro has NO consistency in the evaluation (proea.app 2026-10-03, pipback,
tradetanto). LucidPro 50K: target 3,000, EOD trailing 2,000 locking at +100, eval DLL 1,200 soft (optional add-on), max 40 micros.
Funded Pro: full size, buffer 2,100 (payout needs balance >= start + 2,600), min request 500, caps 2,000 then 2,500, 40% consistency
per payout cycle (largest day <= 40% of the cycle profit), 90% split, no DLL with the add-on.
Part 1 (eval only, every start day with >= 150 trading days left, also ATR < 1.15 starts):
  Flex (50% consistency, account profit stop 1,400) vs Pro (no consistency, no profit stop, optional DLL 1,200) for fixed sizes and
  for the 1-contract Estable cushion gating (gate_final 'A-oro2' C1200). -> lucidpro_eval.csv
Part 2 (lifecycle $/month per slot, 12-month slots, history / +1 tick / 1,000 bootstrap years): Flex recommended 2c/2c vs Pro eval
k x funded k x payout request size. -> lucidpro_life.csv"""
import sys, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib  # noqa: F401
import lc_lib as L
from acct_life import CFG
from acct_policy import vec, hiatr
from acct_size import fu_g
from final_verify_lib import exits
from eval20 import stats

NIGHT = ["N:NF05", "N:LF06", "N:LF0430"]
EU = L.define("P50_EU", CFG["UA_FULL_GR"] + NIGHT)                       # Ultra (ampliado + night) + GoldMaster Robust
FU = tuple(L.define("P50_U" + x, CFG[x] + NIGHT) for x in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"))
EW = L.define("P50_EW", CFG["WR_FULL_GW"] + NIGHT)                       # WR70Plus + night + GoldMaster WinRate
PERS = ("IS", "C24", "REAL")
FEE_FLEX, FEE_PRO = 105.2, 152.0     # Flex 50K list $146 with the usual ~28% coupon; Pro 50K list $192 + no-DLL add-on $20, same coupon


@njit(cache=True)
def ev_c(LO, CL, k0, kdd, c1, cons, s, n):
    eq = 0.0; pk = 0.0; best = -1e9; d = s
    while d < n:
        thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        k = kdd if eq - thr < c1 else k0
        if eq + LO[k, d] <= thr: return -1, d
        c = CL[k, d]; eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= 3000.0 and (cons <= 0.0 or best <= cons * eq): return 1, d
        d += 1
    return 0, n


@njit(cache=True)
def fu_pro(lo, cl, k, c1, c2, start, n, Xw, cap1, cap2, cons, npmax, mindays):
    """LucidPro funded 50K: EOD trailing 2,000 locking at +100, payout when balance - 2,100 >= max(500, Xw) (amount capped),
    cycle profit >= 500, largest day of the cycle <= cons x cycle profit, >= mindays trading days in the cycle."""
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; cyc0 = 0.0; best = -1e9; nd = 0; d = start
    while d < n:
        thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        cu = bal - thr; j = 0 if cu < c1 else (1 if cu < c2 else 2)
        if bal + k * lo[j, d] <= thr: return cash, m, -1, d
        c = k * cl[j, d]; bal += c; nd += 1
        if bal > pk: pk = bal
        if c > best: best = c
        prof = bal - cyc0; cap = cap1 if m == 0 else cap2; amt = min(cap, bal - 2100.0)
        if nd >= mindays and prof >= 500.0 and amt >= max(500.0, min(Xw, cap)) and best <= cons * prof:
            bal -= amt; cash += 0.9 * amt; m += 1; cyc0 = bal; best = -1e9; nd = 0
            if m == npmax: return cash, m, 1, d
        d += 1
    return cash, m, 0, n


@njit(cache=True)
def life2(LO, CL, k0, kdd, c1, econs, flo, fcl, fk, firm, X, npmax, fee, H, step, out):
    nd = LO.shape[1]; r = 0
    for s in range(0, nd - H, step):
        end = s + H; i = s; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0; dtp = 0.0
        while i < end:
            fees += fee; nev += 1
            res, j = ev_c(LO, CL, k0, kdd, c1, econs, i, end)
            if res != 1: i = j + 1; continue
            npass += 1; dtp += j - i + 1
            if firm == 0: c, m, st, j2 = fu_g(flo, fcl, fk, 750.0, 1500.0, j + 1, end, X, 2000.0, 150.0, 2000.0)
            else: c, m, st, j2 = fu_pro(flo, fcl, fk, 750.0, 1500.0, j + 1, end, X, 2000.0, 2500.0, 0.4, npmax, 3)
            cash += c; npay += m; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb; out[r, 4] = npay; out[r, 5] = dtp / max(npass, 1); r += 1
    return r


def mats(per, cfg, DL, G, cost=False):
    nd = len(vec(per, cfg, 0.0, 0.0)[0]); LO = np.zeros((5, nd)); CL = np.zeros((5, nd)); ce = exits(per, cfg) if cost else 0.0
    for k in (1, 2, 3, 4):
        lo, cl = vec(per, cfg, DL / k if DL > 0 else 0.0, G / k if G > 0 else 0.0); LO[k] = k * (lo - ce); CL[k] = k * (cl - ce)
    return LO, CL


def esumm(o, mask=None):
    if mask is not None: o = o[mask]
    ps = o[:, 0] == 1
    return dict(aprueba=100 * ps.mean(), p10=100 * (ps & (o[:, 1] <= 10)).mean(), p15=100 * (ps & (o[:, 1] <= 15)).mean(),
                p20=100 * (ps & (o[:, 1] <= 20)).mean(), mediana=float(np.median(o[ps, 1])) if ps.any() else np.nan, quema=100 * (o[:, 0] == -1).mean())


def part1():
    import fast1c as F
    from gate_final import combo, UA, GW, EST
    from gate84 import gated
    rows = []
    for per in PERS:
        atr = hiatr(per)
        for (pn, cfg), k in itertools.product((("Ultra+noche+oro Robust", EU), ("WR70Plus+noche+oro WinRate", EW)), (1, 2, 3, 4)):
            for firm, cons, G, DL in (("Flex", 0.5, 1400.0, 0.0), ("Pro", 0.0, 0.0, 0.0), ("Pro DLL1200", 0.0, 0.0, 1200.0)):
                LO, CL = mats(per, cfg, DL, G)
                o = stats(LO, CL, 3000.0, 2000.0, cons, 400, k, k, 0.0, 999, k, 0.0, 150); m = len(o)
                for st, mask in (("todos", None), ("ATR<1.15", atr[:m] < 1.15)):
                    rows.append(dict(per=per, cuenta=firm, plan=f"{pn}, {k} contrato" + ("s" if k > 1 else ""), arranque=st, **esumm(o, mask)))
        # 1-contract Estable gating (HI = Ultra+night, LO = Estable, gold WinRate x2, gate at cushion 1,200) at k contracts
        for k, C in ((1, 1200.0), (2, 1200.0), (2, 1800.0)):
            (lH, cH), (lL, cL) = combo(UA, GW, 2, per), combo(EST, GW, 2, per)
            for firm, cons in (("Flex", 0.5), ("Pro", 0.0)):
                o = gated_c(k * lH, k * cH, k * lL, k * cL, C, 150, cons); m = len(o)
                for st, mask in (("todos", None), ("ATR<1.15", atr[:m] < 1.15)):
                    rows.append(dict(per=per, cuenta=firm, plan=f"Estable C{C:.0f} (Ultra/Estable + oro WR x2), {k} contrato" + ("s" if k > 1 else ""), arranque=st, **esumm(o, mask)))
        print(per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("lucidpro_eval.csv", index=False); return R


@njit(cache=True)
def gated_c(lH, cH, lL, cL, C, nmin, cons):
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
            if eq >= 3000.0 and (cons <= 0.0 or best <= cons * eq): r = 1; break
            d += 1
        out[s, 0] = r; out[s, 1] = d - s + 1
    return out


FUNDED_G = ()
def part2(nmc=1000):
    # (name, firm, eval cfg, eval k, eval DL, eval profit stop G, eval consistency, funded k, payout X, payouts to graduate, fee)
    C = [("Flex: eval 2c / fondeada 2c, retiro a $4k (recomendado hoy)", 0, EU, 2, 0.0, 1400.0, 0.5, 2, 4000.0, 5, FEE_FLEX),
         ("Flex: eval 1c / fondeada 2c", 0, EU, 1, 0.0, 1400.0, 0.5, 2, 4000.0, 5, FEE_FLEX)]
    for ek, fk, X in itertools.product((1, 2, 3, 4), (2, 3), (500.0, 2000.0)):
        C.append((f"Pro: eval {ek}c / fondeada {fk}c, retiro {'apenas se puede' if X == 500 else 'al tope'}", 1, EU, ek, 0.0, 0.0, 0.0, fk, X, 5, FEE_PRO))
    for ek in (2, 3):
        C.append((f"Pro: eval {ek}c con DLL $1.200 / fondeada 2c, retiro al tope", 1, EU, ek, 1200.0, 0.0, 0.0, 2, 2000.0, 5, FEE_PRO))
    if FUNDED_G:      # funded daily profit stop (account $) for the 40% cycle consistency
        C = [c for c in C if c[0].startswith("Flex: eval 2c") or c[0] in ("Pro: eval 4c / fondeada 2c, retiro apenas se puede", "Pro: eval 3c / fondeada 2c, retiro al tope")]
        for ek, Gf in itertools.product((3, 4), FUNDED_G):
            C.append((f"Pro: eval {ek}c / fondeada 2c con stop de ganancia diario ${Gf:.0f}, retiro apenas se puede", 1, EU, ek, 0.0, 0.0, 0.0, 2, 500.0, 5, FEE_PRO, Gf))
    rows = []
    for per in PERS:
        fv = [vec(per, c, 0.0, 0.0) for c in FU]; cf = np.array([exits(per, c) for c in FU])
        MM = {}
        for cc in C:
            nm, firm, ecfg, ek, DL, G, cons, fk, X, npm, fee = cc[:11]; Gf = cc[11] if len(cc) > 11 else 0.0
            if Gf > 0:
                fvg = [vec(per, c, 0.0, Gf / fk) for c in FU]; F0 = np.array([v[0] for v in fvg]); F1 = np.array([v[1] for v in fvg])
            else:
                F0 = np.array([v[0] for v in fv]); F1 = np.array([v[1] for v in fv])
            for test in ("historia", "costo +1 tick", "Monte Carlo"):
                cost = test == "costo +1 tick"; key = (ecfg, DL, G, cost)
                if key not in MM: MM[key] = mats(per, ecfg, DL, G, cost)
                LO, CL = MM[key]; nd = LO.shape[1]
                f0 = fk * (F0 - (cf if cost else 0)); f1 = fk * (F1 - (cf if cost else 0))
                args = (ek, ek, 0.0, cons)
                if test != "Monte Carlo":
                    out = np.zeros((1000, 6)); mm = life2(LO, CL, *args, f0, f1, 1.0, firm, X, npm, fee, 252, 3, out); Lr = out[:mm]
                else:
                    o1 = np.zeros((2, 6)); Lr = []
                    for q in range(nmc):
                        idx = np.concatenate([np.arange(s, s + 10) % nd for s in np.random.default_rng(31 + q).integers(0, nd, 27)])[:253]
                        life2(LO[:, idx].copy(), CL[:, idx].copy(), *args, f0[:, idx].copy(), f1[:, idx].copy(), 1.0, firm, X, npm, fee, 252, 252, o1); Lr.append(o1[0].copy())
                    Lr = np.array(Lr)
                rows.append(dict(per=per, caso=nm, test=test, mo=Lr[:, 0].mean() / 12, p10=np.percentile(Lr[:, 0], 10) / 12, ploss=100 * (Lr[:, 0] < 0).mean(),
                                 evals=Lr[:, 1].mean(), fondeadas=Lr[:, 2].mean(), quemas_fondeada=Lr[:, 3].mean(), pagos=Lr[:, 4].mean(), dias_aprobar=Lr[:, 5].mean()))
        print(per, flush=True)
    R = pd.DataFrame(rows); R.to_csv(("lucidpro_life_fg2.csv" if 300.0 in FUNDED_G else "lucidpro_life_fg.csv") if FUNDED_G else "lucidpro_life.csv", index=False); return R


if __name__ == "__main__":
    pd.set_option("display.width", 280); pd.set_option("display.max_colwidth", 80); pd.set_option("display.max_rows", 300)
    if "life" not in sys.argv:
        E = part1()
        P = E.pivot_table(index=["plan", "arranque", "cuenta"], columns="per", values=["aprueba", "p20", "mediana"]).round(1)
        print(P.to_string())
    if "eval" not in sys.argv:
        if "fg" in sys.argv: FUNDED_G = (600.0, 800.0, 1000.0, 1300.0)
        if "fg2" in sys.argv: FUNDED_G = (300.0, 400.0, 500.0, 600.0, 700.0)
        R = part2()
        S = R.groupby("caso").agg(mes_por_cuenta=("mo", "mean"), peor_de_9=("mo", "min"), p_anio_neg=("ploss", "max"), evals=("evals", "mean"),
                                  fondeadas=("fondeadas", "mean"), quemas_fond=("quemas_fondeada", "mean"), pagos=("pagos", "mean"), dias=("dias_aprobar", "mean"))
        print(S.round(1).sort_values("mes_por_cuenta", ascending=False).to_string())
