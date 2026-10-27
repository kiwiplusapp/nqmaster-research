"""Cuanto de neg60_mtm viene del castigo del saldo al 5.o retiro y al fin de horizonte: variante del nucleo que NO castiga (mantiene el saldo
como riqueza) y variante que solo castiga el quiebre. Mismos caminos (rng 20261021), L150 coupon hc0 / 0.35, 300 caminos (los primeros 300 de cada tanda)."""
import sys, json, numpy as np, time
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import objective as O, prop_wf as P
from numba import njit
race = P.race

@njit(cache=False)
def fund_flow2(FL, FC, fp, idx, s, n, rec, flow, mtm, wo5, woH):
    firm = int(fp[0]); c1 = fp[1]; X = fp[2]; S = fp[3]; K = int(fp[4]); cap1 = fp[5]; cap2 = fp[6]; Q = fp[7]; npmax = int(fp[8]); D = fp[9]
    lock = 100.0; bal = 0.0; pk = 0.0; cash = 0.0; m = 0; cyc0 = 0.0; nd = 0; qd = 0; locked = False; d = s
    rec[0] = -1.0; rec[2] = -1.0
    while d < n:
        t = idx[d]; v0 = cash + bal
        thr = lock if (locked or pk >= D + lock) else pk - D
        cu = bal - thr
        g = 0 if cu < c1 else 1
        if bal + FL[g, t] <= thr:
            mtm[d] += cash - v0
            rec[1] = cash; rec[2] = d - s; rec[3] = m; rec[4] = d; return
        c = FC[g, t]; bal += c; nd += 1
        if bal > pk: pk = bal
        amt = 0.0
        if firm == 0:
            if c >= Q: qd += 1
            if qd >= 5 and bal - cyc0 > 0 and bal >= X:
                a = min(cap1, 0.5 * bal)
                if a >= 500.0: amt = a; qd = 0; locked = True
        else:
            if bal - X >= 500.0: amt = bal - X
        if amt > 0.0:
            bal -= amt; pay = 0.9 * amt; cash += pay; flow[d] += pay; m += 1; cyc0 = bal
            if rec[0] < 0: rec[0] = d - s
            if npmax > 0 and m >= npmax:
                if wo5: mtm[d] += cash - v0
                else: mtm[d] += cash + bal - v0
                rec[1] = cash; rec[3] = m; rec[4] = d; return
        mtm[d] += cash + bal - v0
        d += 1
    if woH: mtm[n - 1] += -bal
    rec[1] = cash; rec[3] = m; rec[4] = n

@njit(cache=False)
def seat_flow2(LO, CL, Hh, ep, fee, FL, FC, fp, idx, s0, end, flow, mtm, wo5, woH):
    i = s0; k = 0; rec = np.zeros(5)
    while i < end:
        flow[i] -= fee; mtm[i] -= fee
        r, j = race(LO, CL, Hh, idx, i, end, ep)
        if r != 1:
            k += 1; i = j + 1; continue
        fund_flow2(FL, FC, fp, idx, j + 1, end, rec, flow, mtm, wo5, woH)
        k += 1; i = int(rec[4]) + 1
    return k

def wins(F, W=60):
    c = np.concatenate([np.zeros((len(F), 1)), np.cumsum(F, 1)], 1); return c[:, W:] - c[:, :-W]

days, M, FU, PER = O.setup(); NB = 1000; NU = 300; H = O.H; out = {}; t0 = time.time()
rng = np.random.default_rng(20261021)
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, H, rng) for _ in range(NB)][:NU]
        if hc == 1.0: continue
        A = O.seat_args(FU, hc, "L150 6c/3c", Hm); LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]
        res = {}
        for lab, wo5, woH in (("como objective (castiga 5o retiro y fin)", True, True), ("sin castigo al 5o retiro", False, True), ("sin castigo al 5o retiro ni al fin", False, False)):
            flows = np.zeros((NU, H)); mtms = np.zeros((NU, H))
            for b, bi in enumerate(paths): seat_flow2(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, bi, 0, H, flows[b], mtms[b], wo5, woH)
            res[lab] = dict(neg60=100 * float((wins(flows) < 0).mean()), neg60_mtm=100 * float((wins(mtms) < 0).mean()), suma_mtm_menos_caja_media=float((mtms.sum(1) - flows.sum(1)).mean()))
        key = f"L150 | hc{hc} | {per} | {NU} caminos"; out[key] = res
        print(f"{time.time()-t0:5.0f}s {key}"); [print("   ", l, {k: round(v, 2) for k, v in r.items()}) for l, r in res.items()]
json.dump(out, open("/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/verify_mtm.json", "w"), indent=1)
