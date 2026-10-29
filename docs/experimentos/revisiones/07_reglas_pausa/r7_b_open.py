"""Saldo abierto al pausar: modulo exp07_open_balance.open_bal contra (i) suma acumulada de (mtm - flujo) hasta p-1 en la corrida con fin p+1
y (ii) un fund en Python puro (firmas 0 flex y 2 mffu) que devuelve el saldo al cierre de p-1."""
import numpy as np
from r7_common import *
import exp07_open_balance as OB

days, M, FU, PER, n, CONST, ARc, ARs, paths = load()

def ob_cum(AR, idx, p):
    tot = 0.0
    for name, cnt in X.PLAN:
        A = AR["A"][name]; LO, CL, _ = AR["M"][A["mix"]]; FL, FC, fp = A["tiers"]
        for s in range(cnt):
            s0 = 5 * s
            if p >= s0 + H or p <= s0: continue
            f = np.zeros(L + 1); mm = np.zeros(L + 1); ev = np.zeros((X.MAXEV, 5))
            O.seat_flow(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, idx, s0, min(p + 1, s0 + H), f, mm, ev, A["act"])
            tot += max(0.0, float((mm[:p] - f[:p]).sum()))
    return tot

def fund_py(FL, FC, fp, idx, s, n_, stop):
    """prop_wf.fund en Python para firmas 0 y 2; devuelve (estado, saldo al cierre del dia stop-1 si sigue viva, ultimo dia)"""
    firm = int(fp[0]); c1 = fp[1]; X_ = fp[2]; cap1 = fp[5]; Q = fp[7]; npmax = int(fp[8]); D = fp[9]
    bal = 0.0; pk = 0.0; m = 0; cyc0 = 0.0; qd = 0; locked = False; d = s
    while d < n_:
        t = idx[d]; thr = 100.0 if (locked or pk >= D + 100.0) else pk - D; cu = bal - thr; g = 0 if cu < c1 else 1
        if bal + FL[g, t] <= thr: return "bust", 0.0, d
        c = FC[g, t]; bal += c; pk = max(pk, bal); amt = 0.0
        if firm == 0:
            if c >= Q: qd += 1
            if qd >= 5 and bal - cyc0 > 0 and bal >= X_:
                a = min(cap1, 0.5 * bal)
                if a >= 500.0: amt = a; qd = 0; locked = True
        elif firm == 2:
            if bal - X_ >= 500.0: amt = bal - X_
        if amt > 0:
            bal -= amt; m += 1; cyc0 = bal
            if npmax > 0 and m >= npmax: return "end5", 0.0, d
        if d == stop - 1: return "open", bal, d
        d += 1
    return "horizon", 0.0, n_

def ob_py(AR, idx, p):
    tot = 0.0
    for name, cnt in X.PLAN:
        A = AR["A"][name]; LO, CL, _ = AR["M"][A["mix"]]; FL, FC, fp = A["tiers"]
        for s in range(cnt):
            s0 = 5 * s; end = s0 + H
            if p >= end or p <= s0: continue
            i = s0
            while i < p:                                   # recorrido sin pausa hasta p-1 (las decisiones hasta p-1 no dependen del fin)
                r, j = P.race(LO, CL, A["Hh"], idx, i, end, A["ep"])
                if r != 1: i = j + 1; continue
                if j + 1 > p - 1: break                    # fondeada empieza en p o despues: no hay saldo en p-1
                st, bal, dlast = fund_py(FL, FC, fp, idx, j + 1, end, p)
                if st == "open": tot += max(0.0, bal); break
                i = dlast + 1 if st != "horizon" else end
    return tot

for sc, AR, hc, S, rule, per in (("completo", ARc["completo"], 0.0, None, "R1", "T2"), ("-35%", ARc["-35%"], 0.35, None, "R4", "T1"),
                                   ("cero", ARc["cero"], 1.0, None, "R1", "T1"), ("muere63", ARs, 0.0, 63, "R4", "T2")):
    a = []; b = []; c = []
    for bi in paths[(hc, per)]:
        b2 = bi if S is None else sw(bi, n, S); p = X.pause_day(AR["x"][b2], rule)
        if p >= L: continue
        a.append(OB.open_bal(AR, b2, p)); b.append(ob_cum(AR, b2, p)); c.append(ob_py(AR, b2, p))
    a, b, c = map(np.array, (a, b, c))
    print(f"{sc:8s} {per} {rule}: {len(a)} pausados | media modulo {a.mean():8.1f} | cum(mtm-flujo) {b.mean():8.1f} max|dif| {np.abs(a-b).max():.2e} | fund python {c.mean():8.1f} max|dif| {np.abs(a-c).max():.2e} | frac con saldo > 0 {(a>0).mean():.2f}")
