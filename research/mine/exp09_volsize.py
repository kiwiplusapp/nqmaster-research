"""exp09_volsize.py (2026-10-29, experimento 09 / frente 5C): contratos de Lucid 150K segun la volatilidad (riesgo en dolares constante).
V1: contratos del dia = clip(round(base x ATR_ref / ATR_dia), min, max); eval base 6 en [3, 9], fondeada base 3 en [2, 4]; ATR_dia = Wilder 14
desplazado un dia (se conoce al abrir); ATR_ref = mediana del ATR en los dias de T1. MFFU sin cambios. Plan: docs/PLAN_2026-10-29_exp09.md.
Run (desde research/mine): python3 exp09_volsize.py selftest | python3 exp09_volsize.py [NB]"""
import os, sys, json, time, numpy as np, pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import prop_wf as P, objective as O, exp03_eval_size as E3
from wrq_lib import getD
fund_flow = O.fund_flow; H = O.H; L = H + 25; MAXEV = O.MAXEV; L150 = "L150 6c/3c"; MF = "MFFU 1x8"


@njit(cache=True)
def race_v(LO, CL, Hh, idx, s, n, ep, kv):
    """prop_wf.race con contratos por dia kv[t] (t = dia absoluto) para la eval de tamano fijo (ptype 0)"""
    T = ep[0]; D = ep[1]; cons = ep[2]; mind = int(ep[3]); G = ep[4]; Lx = ep[5]
    intra = ep[12] > 0; lock = ep[13]; hardL = ep[14]
    eq = 0.0; pk = 0.0; best = -1e9; d = s; nm = LO.shape[1]
    while d < n:
        t = idx[d]; thr = lock if pk >= D + lock else pk - D
        k = kv[t]
        h = Hh[t]; last = 0.0
        for j in range(nm):
            lo = k * (LO[t, j] - h)
            if eq + lo <= thr: return -1, d
            if hardL > 0.0 and lo <= -hardL: return -1, d
            c = k * (CL[t, j] - h); tot = eq + c
            if tot >= T and (cons <= 0.0 or max(best, c) <= cons * tot):
                e = s + int(mind) - 1
                return 1, (d if d > e else e)
            last = c
            if intra and tot > pk:
                pk = tot; thr = lock if pk >= D + lock else pk - D
            if Lx > 0.0 and c <= -Lx: break
            if G > 0.0 and c >= G: break
        eq += last
        if last > best: best = last
        if eq > pk: pk = eq
        d += 1
    return 0, n


@njit(cache=True)
def seat_flow_v(LO, CL, Hh, ep, fee, FL, FC, fp, idx, s0, end, flow, mtm, ev, act, kv):
    i = s0; k = 0; rec = np.zeros(5)
    while i < end:
        flow[i] -= fee; mtm[i] -= fee
        r, j = race_v(LO, CL, Hh, idx, i, end, ep, kv)
        jj = j if j < end else end - 1
        if k < ev.shape[0]:
            ev[k, 0] = i; ev[k, 1] = r; ev[k, 2] = jj if r != 0 else end - 1; ev[k, 3] = -1; ev[k, 4] = 0
        if r != 1:
            k += 1; i = j + 1; continue
        if act > 0.0: flow[jj] -= act; mtm[jj] -= act
        fund_flow(FL, FC, fp, idx, j + 1, end, rec, flow, mtm)
        if k < ev.shape[0]:
            ev[k, 3] = j + 1 + rec[2] if rec[2] >= 0 else -1; ev[k, 4] = rec[3]
        k += 1; i = int(rec[4]) + 1
    return k


@njit(cache=True)
def race_all_v(LO, CL, Hh, idx, ep, res, end, kv):
    n = len(idx)
    for s in range(n):
        r, e = race_v(LO, CL, Hh, idx, s, n, ep, kv); res[s] = r; end[s] = e


def atr_days(days):
    D = getD("nqdb.npz"); return pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(days).to_numpy()


def kvecs(days, atr, mode):
    if mode == "V0": return np.full(len(days), 6.0), np.full(len(days), 3.0)
    ref = float(np.median(atr[days < P.T1_END]))
    return np.clip(np.round(6.0 * ref / atr), 3, 9).astype(np.float64), np.clip(np.round(3.0 * ref / atr), 2, 4).astype(np.float64)


def l150_args(FU, hc, Hm, kf):
    F = P.FIRMS["LucidFlex150K"]; FL1, FC1, fp = FU.tiers(hc, "LucidFlex150K", (1, 1687, 0, 6000, 0))
    FL = np.ascontiguousarray(FL1 * kf[None, :]); FC = np.ascontiguousarray(FC1 * kf[None, :])
    return dict(ep=P.ep_of(F, (0, 6, 6, 0, 0, 0, 0)), mix=(0, 4), fee=215.0, tiers=(FL, FC, fp), act=0.0, Hh=Hm[(0, 4)])


def run_l150(M, A, bi, s0, Lp, f, mm, ev, ke):
    LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]
    return seat_flow_v(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, bi, s0, s0 + Lp, f, mm, ev, A["act"], ke)


def p22_v(days, M, A, ii, ke):
    LO, CL, _ = M[A["mix"]]; n = len(days); idx = np.arange(n, dtype=np.int64); res = np.zeros(n, np.int64); end = np.zeros(n, np.int64)
    race_all_v(LO, CL, A["Hh"], idx, A["ep"], res, end, ke); o = P.eval_metrics(res, end, ii, A["fee"], n); return o["p22_3"]


def selftest(NB=200):
    days, M, FU, PER = O.setup(); atr = atr_days(days); ke, kf = kvecs(days, atr, "V0"); rng = np.random.default_rng(9); bad = 0; tot = 0
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        A0 = O.seat_args(FU, hc, L150, Hm); A1 = l150_args(FU, hc, Hm, kf)
        for per, ii in PER.items():
            for _ in range(NB):
                bi = P.boot_idx(ii[0], ii[-1] + 1, H, rng)
                f0 = np.zeros(H); m0 = np.zeros(H); e0 = np.zeros((MAXEV, 5)); k0 = O.run_seat(M, A0, bi, 0, H, f0, m0, e0)
                f1 = np.zeros(H); m1 = np.zeros(H); e1 = np.zeros((MAXEV, 5)); k1 = run_l150(M, A1, bi, 0, H, f1, m1, e1, ke)
                tot += 1; bad += not (k0 == k1 and np.array_equal(f0, f1) and np.array_equal(m0, m1) and np.array_equal(e0[:k0], e1[:k1]))
    print(f"selftest: {tot} asientos L150 con contratos constantes 6 / 3, {bad} diferencias contra objective.run_seat (flujo, mtm y evals al bit)"); return bad


def plan_cell(M, AL, AM, paths, ke):
    NB = len(paths); flows = np.zeros((NB, L)); mtms = np.zeros((NB, L)); tot = np.zeros(NB); evs = []; nev = []
    for b, bi in enumerate(paths):
        ev_all = np.zeros((8 * MAXEV, 5)); kk = 0
        for s in range(3):
            f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); k = O.run_seat(M, AM, bi, 5 * s, H, f, mm, ev)
            flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + k] = ev[:k]; kk += k
        for s in range(5):
            f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); k = run_l150(M, AL, bi, 5 * s, H, f, mm, ev, ke)
            flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + k] = ev[:k]; kk += k
        evs.append(ev_all); nev.append(kk)
    return E3.plan_metrics(flows, mtms, evs, nev, tot), tot


def seat_cell(M, AL, paths, ke):
    NB = len(paths); flows = np.zeros((NB, H)); mtms = np.zeros((NB, H)); evs = []; nev = []
    for b, bi in enumerate(paths):
        ev = np.zeros((MAXEV, 5)); k = run_l150(M, AL, bi, 0, H, flows[b], mtms[b], ev, ke); evs.append(ev); nev.append(k)
    return O.metrics(flows, mtms, evs, nev)


def main(NB=1000):
    days, M, FU, PER = O.setup(); atr = atr_days(days); n = len(days); idx = np.arange(n, dtype=np.int64); t0 = time.time()
    OUT = {"NB": NB, "ATR_ref": float(np.median(atr[days < P.T1_END])), "celdas": {}, "pareado": {}}
    KV = {mo: kvecs(days, atr, mo) for mo in ("V0", "V1")}
    for mo, (ke, kf) in KV.items():
        for per, ii in PER.items():
            vals, cnt = np.unique(ke[ii], return_counts=True); OUT[f"dist_contratos_eval {mo} {per}"] = {str(int(v)): int(c) for v, c in zip(vals, cnt)}
    NET = {}; SEAT = {}
    rng_s = np.random.default_rng(20261021); rng_p = np.random.default_rng(4242); PS = {}; PP = {}
    for hc in P.HC:
        for per, ii in PER.items(): PS[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, H, rng_s) for _ in range(1000)][:NB]
    for hc in P.HC:
        for per, ii in PER.items(): PP[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, L, rng_p) for _ in range(1000)][:NB]
    for hc in (0.0, 0.35):
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}; AM = O.seat_args(FU, hc, MF, Hm)
        for mo, (ke, kf) in KV.items():
            AL = l150_args(FU, hc, Hm, kf)
            for per, ii in PER.items():
                st = np.arange(ii[0], ii[-1] + 2 - H, 5); stp = np.arange(ii[0], ii[-1] + 2 - L, 5)
                se_b = seat_cell(M, AL, PS[(hc, per)], ke); se_b["p22_3"] = p22_v(days, M, AL, ii, ke)
                se_c = seat_cell(M, AL, [idx[s0:s0 + H] for s0 in st], ke); se_c["p22_3"] = se_b["p22_3"]
                pl_b, tot = plan_cell(M, AL, AM, PP[(hc, per)], ke); NET[(mo, hc, per)] = tot
                pl_c, _ = plan_cell(M, AL, AM, [idx[s0:s0 + L] for s0 in stp], ke)
                for src, pl, se in (("bootstrap", pl_b, se_b), ("contiguo", pl_c, se_c)):
                    v = O.verdict_d1(pl, se); key = f"{mo} | {src} | hc{hc} | {per}"
                    OUT["celdas"][key] = dict(plan=pl, asiento_L150=se, cumple_d1=v, n_cumple=int(sum(v.values())))
                    print(f"{time.time()-t0:5.0f}s {mo} {src:9s} hc{hc:<4} {per} med {pl['med_mes']:7.0f} p10 {pl['p10_mes']:7.0f} neg60 {pl['neg60']:5.1f} P(fond<=22d) {se['p22_3']:5.1f} dias {se['dias_aprobar']:3.0f} evperd/mes {pl['evals_perdidas_mes']:5.2f} cumple {sum(v.values())}/5 " + " ".join(("+" if x else "-") + k for k, x in v.items()), flush=True)
    for (mo, hc, per), v in NET.items():
        if mo == "V1": OUT["pareado"][f"V1 vs V0 | hc{hc} | {per}"] = E3.paired(v, NET[("V0", hc, per)])
    OUT["regla"] = decide(OUT); print(OUT["regla"])
    json.dump(OUT, open(os.path.join(HERE, "exp09_volsize.json"), "w"), indent=1); return OUT


def decide(OUT):
    c = lambda mo, src, hc, per: OUT["celdas"][f"{mo} | {src} | hc{hc} | {per}"]
    score = {mo: sum(c(mo, s, hc, "T1")["n_cumple"] for s in ("bootstrap", "contiguo") for hc in (0.0, 0.35)) for mo in ("V0", "V1")}
    R = dict(puntaje_T1=score)
    g1 = OUT["pareado"]["V1 vs V0 | hc0.35 | T1"]
    elegido = score["V1"] > score["V0"] or (score["V1"] == score["V0"] and g1["P_gain"] >= 0.80)
    if not elegido: R["veredicto"] = "sin cambio: V1 no gana la eleccion en T1"; return R
    perd = [f"{s} hc{hc}: {m}" for s in ("bootstrap", "contiguo") for hc in (0.0, 0.35) for m, v in c("V0", s, hc, "T2")["cumple_d1"].items() if v and not c("V1", s, hc, "T2")["cumple_d1"][m]]
    ok_g = all(OUT["pareado"][f"V1 vs V0 | hc{hc} | T2"]["P_loss5"] <= 0.20 for hc in (0.0, 0.35))
    ok_c = all(c("V1", "contiguo", hc, "T2")["plan"]["neg60"] <= c("V0", "contiguo", hc, "T2")["plan"]["neg60"] + 2.0 for hc in (0.0, 0.35))
    R.update(condiciones_perdidas_T2=perd, ganancia_ok=ok_g, contiguo_ok=ok_c, confirma=(not perd) and ok_g and ok_c)
    R["veredicto"] = "V1 confirma en T2: contratos por volatilidad en Lucid 150K (falta el parche de NQMaster.cs con F5)" if R["confirma"] else "V1 gana en T1 pero no confirma en T2: sin cambio"
    return R


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest": sys.exit(1 if selftest() else 0)
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)
