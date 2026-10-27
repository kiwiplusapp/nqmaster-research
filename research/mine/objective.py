"""objective.py (2026-10-27, experimento 02 / frente 5B): linea de base de la FUNCION OBJETIVO del programa sobre los caminos de campana.

Reusa los nucleos pre-registrados de prop_wf.py (race = eval a resolucion de minuto, fund = cuenta fondeada diaria) sin cambiar una
regla: seat_flow / fund_flow son copias de prop_wf.seat / prop_wf.fund que ademas escriben el FLUJO DE CAJA DIARIO del asiento
(fee al comprar la eval, activacion al aprobar, 90 % de cada retiro el dia que se pide) y un registro por eval (inicio, resultado,
fin, quiebre de la fondeada, retiros). selftest() exige 0 diferencias contra prop_wf.seat en neto, evals, aprobadas, quiebres,
retiros y primer retiro.

Definiciones pre-registradas (docs/PLAN_2026-10-27.md), por asiento y por plan, sobre NB caminos bootstrap de 252 dias habiles
(bloques de 21 dias; mismas semillas y mismo orden de sorteo que integ_paired.py / integ_port.py, asi los asientos reproducen
integ_paired.json e integ_port.json):
  M1 med_mes / p10_mes   mediana y p10 entre caminos del neto de 12 meses / 12 (la definicion de integ_summ; cupon).
     med_mes21 / p10_mes21: distribucion de los 12 cortes de 21 dias de cada camino (caja por 'mes'; muestra lo grumoso del flujo).
  M2 neg60               fraccion de ventanas moviles de 60 dias habiles (paso 1 dia, 193 por camino) con flujo de caja negativo;
     neg60_mtm: lo mismo sobre caja + saldo de la fondeada (el saldo se pierde al quebrar; la equity de una eval no es nuestra).
  M3 evals_perdidas_mes  evals quebradas por camino / 12.  cuentas_perdidas_mes: fondeadas quebradas / 12.
  M4 aprobacion          aprobadas / (aprobadas + quebradas) sobre las evals terminadas de todos los caminos (las abiertas al final
     del camino no cuentan).  p22_3: P(fondeado en <= 22 dias habiles con hasta 3 evals seriadas) sobre los inicios reales del
     periodo (metrica primaria pre-registrada de prop_wf, sin bootstrap).
  M5 dias_aprobar        mediana (y p75) de los dias habiles desde la compra hasta la aprobacion, sobre las evals aprobadas.
Umbrales de la consigna del programa (interpretados sobre el asiento Lucid Flex 150K 6c/3c, la unidad cuyas magnitudes coinciden):
  med_mes > 2.759 sin p10_mes < 1.600 | neg60 < 10 % | evals_perdidas_mes < 0,12 | aprobacion >= 65 % | dias_aprobar <= 10.
Run (desde research/mine): python3 objective.py [NB]   -> objective_baseline.json + objective_baseline.md ; python3 objective.py selftest
"""
import os, sys, json, time, numpy as np
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import prop_wf as P
race = P.race
P.FIRMS["LucidFlex150K"] = dict(T=9000.0, D=4500.0, cons=0.5, mind=1, G=4050.0, fee=285.0, kmax=6, fund="flex", Q=250.0, cap1=3000.0, npmax=5)
# name: firm, eval policy, mix, funded policy, fee coupon, fee list   (incumbentes del runbook; integ_paired.py CFG)
SEATS = {"L150 6c/3c": ("LucidFlex150K", (0, 6, 6, 0, 0, 0, 0), (0, 4), (3, 1687, 0, 6000, 0), 215.0, 285.0),
         "MFFU 1x8":   ("MFFU50K", (0, 1, 1, 0, 0, 0, 0), (0, 8), (1, 2000, 0, 4100, 0), 157.0, 157.0)}
PLAN = (("L150 6c/3c", 5), ("MFFU 1x8", 3))          # 5 Lucid 150K + 3 MFFU, arranques cada 5 dias (integ_port.py)
H = 252; W60 = 60; MAXEV = 400
THR = dict(med_mes=2759.0, p10_mes=1600.0, neg60=10.0, evals_perdidas_mes=0.12, aprobacion=65.0, dias_aprobar=10.0)


@njit(cache=True)
def fund_flow(FL, FC, fp, idx, s, n, rec, flow, mtm):
    """prop_wf.fund + flujo de caja: flow[d] += 0.9 * retiro el dia d; mtm[d] += variacion diaria de (caja + saldo fondeado), el saldo
    vale 0 al quebrar. rec como en prop_wf.fund: 0 primer retiro (offset, -1), 1 caja, 2 quiebre (offset, -1), 3 retiros, 4 ultima posicion."""
    firm = int(fp[0]); c1 = fp[1]; X = fp[2]; S = fp[3]; K = int(fp[4]); cap1 = fp[5]; cap2 = fp[6]; Q = fp[7]; npmax = int(fp[8]); D = fp[9]
    lock = 100.0; lop = 0.0; B = 0.0; frac = 1.0; minreq = 500.0; minprof = 0.0; pc = 0.0; nq = 0.0; qthr = 0.0; md = 0.0; split = 0.9
    if firm == 4:
        lock = fp[10]; lop = fp[11]; B = fp[12]; frac = fp[13]; minreq = fp[14]; minprof = fp[15]; pc = fp[16]; nq = fp[17]; qthr = fp[18]; md = fp[19]; split = fp[20]
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; cyc0 = 0.0; best = -1e9; nd = 0; qd = 0; locked = False; d = s
    rec[0] = -1.0; rec[2] = -1.0
    while d < n:
        t = idx[d]; v0 = cash + bal
        thr = lock if (locked or pk >= D + lock) else pk - D
        cu = bal - thr
        if firm == 3:
            k = 1 + int(cu / S)
            if k > K: k = K
            g = 0 if (k == 1 and cu < c1) else k
        else: g = 0 if cu < c1 else 1
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
        elif firm == 1:
            if c > best: best = c
            prof = bal - cyc0; cap = cap1 if m == 0 else cap2; a = min(cap, bal - (D + 100.0))
            if nd >= 3 and prof >= 500.0 and a >= max(500.0, min(X, cap)) and best <= 0.4 * prof:
                amt = a; best = -1e9; nd = 0
        elif firm == 4:
            if c > best: best = c
            if c >= qthr and qthr > 0: qd += 1
            prof = bal - cyc0; cap = cap1 if m == 0 else cap2; a = min(cap, min(bal - B, frac * bal))
            if (a >= max(minreq, min(X, cap)) and prof >= minprof and (pc <= 0.0 or best <= pc * prof) and qd >= nq and nd >= md):
                amt = a; best = -1e9; nd = 0; qd = 0
                if lop > 0: locked = True
        else:
            if bal - X >= 500.0: amt = bal - X
        if amt > 0.0:
            bal -= amt; pay = (split if firm == 4 else 0.9) * amt; cash += pay; flow[d] += pay; m += 1; cyc0 = bal
            if rec[0] < 0: rec[0] = d - s
            if npmax > 0 and m >= npmax:
                mtm[d] += cash - v0            # el ciclo termina con el 5.o retiro: el saldo que queda no se cobra (como prop_wf.fund)
                rec[1] = cash; rec[3] = m; rec[4] = d; return
        mtm[d] += cash + bal - v0
        d += 1
    mtm[n - 1] += -bal                        # fin del horizonte: el saldo abierto no es caja (prop_wf.fund tampoco lo cuenta)
    rec[1] = cash; rec[3] = m; rec[4] = n


@njit(cache=True)
def seat_flow(LO, CL, Hh, ep, fee, FL, FC, fp, idx, s0, end, flow, mtm, ev, act):
    """prop_wf.seat con flujo diario y registro por eval. ev[k]: 0 inicio, 1 resultado (1 aprobada / -1 quebrada / 0 abierta al final),
    2 ultimo dia de la eval, 3 quiebre de la fondeada (dia absoluto, -1), 4 retiros del ciclo. Devuelve el numero de evals."""
    i = s0; k = 0; rec = np.zeros(5)
    while i < end:
        flow[i] -= fee; mtm[i] -= fee
        r, j = race(LO, CL, Hh, idx, i, end, ep)
        if k < ev.shape[0]:
            ev[k, 0] = i; ev[k, 1] = r; ev[k, 2] = j if r != 0 else end - 1; ev[k, 3] = -1; ev[k, 4] = 0
        if r != 1:
            k += 1; i = j + 1; continue
        if act > 0.0: flow[j] -= act; mtm[j] -= act
        fund_flow(FL, FC, fp, idx, j + 1, end, rec, flow, mtm)
        if k < ev.shape[0]:
            ev[k, 3] = j + 1 + rec[2] if rec[2] >= 0 else -1; ev[k, 4] = rec[3]
        k += 1; i = int(rec[4]) + 1
    return k


def setup():
    days, M = P.build_mix(); FU = P.Fund(days, M)
    i1 = np.nonzero(days < P.T1_END)[0]; i2 = np.nonzero((days >= P.T1_END) & (days < P.T2_END))[0]
    return days, M, FU, {"T1": i1, "T2": i2}


def seat_args(FU, hc, name, Hm):
    firm, pe, mix, pf, fc, fl = SEATS[name]; F = P.FIRMS[firm]
    return dict(ep=P.ep_of(F, pe), mix=mix, fee=fc, fee_list=fl, tiers=FU.tiers(hc, firm, pf), act=float(F.get("act", 0.0)), Hh=Hm[mix])


def run_seat(M, A, bi, s0, L, flow, mtm, ev, fee=None):
    LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]
    return seat_flow(LO, CL, A["Hh"], A["ep"], A["fee"] if fee is None else fee, FL, FC, fp, bi, s0, s0 + L, flow, mtm, ev, A["act"])


def neg_windows(flow, lo, hi, W=W60):
    c = np.concatenate([[0.0], np.cumsum(flow[lo:hi])]); w = c[W:] - c[:-W]
    return float((w < 0).mean()), len(w)


def metrics(flows, mtms, evs, nev, lo=0, hi=H):
    """flows / mtms: (NB, L); evs: list of (k, ev) por camino."""
    net = flows[:, lo:hi].sum(1) / 12.0
    buckets = flows[:, lo:hi].reshape(len(flows), -1, 21).sum(2).ravel() if (hi - lo) % 21 == 0 else flows[:, lo:lo + 21 * ((hi - lo) // 21)].reshape(len(flows), -1, 21).sum(2).ravel()
    n60 = np.array([neg_windows(f, lo, hi)[0] for f in flows]); n60m = np.array([neg_windows(f, lo, hi)[0] for f in mtms])
    E = np.concatenate([e[:k] for k, e in zip(nev, evs)]) if evs is not None else None
    r = dict(med_mes=float(np.median(net)), p10_mes=float(np.percentile(net, 10)), p90_mes=float(np.percentile(net, 90)), P_anio_neg=100 * float((net < 0).mean()),
             med_mes21=float(np.median(buckets)), p10_mes21=float(np.percentile(buckets, 10)), P_mes21_neg=100 * float((buckets < 0).mean()),
             neg60=100 * float(n60.mean()), neg60_mtm=100 * float(n60m.mean()), neg60_p90_camino=100 * float(np.percentile(n60, 90)))
    if E is not None:
        done = E[E[:, 1] != 0]; passed = E[E[:, 1] == 1]; days_ok = passed[:, 2] - passed[:, 0] + 1
        r.update(evals_anio=float(np.mean(nev)), evals_perdidas_mes=float((E[:, 1] == -1).sum() / len(flows) / 12.0),
                 cuentas_perdidas_mes=float((E[:, 3] >= 0).sum() / len(flows) / 12.0), retiros_anio=float(E[:, 4].sum() / len(flows)),
                 aprobacion=100 * float((done[:, 1] == 1).mean()) if len(done) else float("nan"),
                 dias_aprobar=float(np.median(days_ok)) if len(days_ok) else float("nan"), dias_aprobar_p75=float(np.percentile(days_ok, 75)) if len(days_ok) else float("nan"),
                 evals_abiertas_fin=float((E[:, 1] == 0).sum() / len(flows)))
    return r


def p22_3(days, M, FU, hc, name, per_idx, Hm):
    A = seat_args(FU, hc, name, Hm); LO, CL, _ = M[A["mix"]]; n = len(days); idx = np.arange(n, dtype=np.int64)
    res = np.zeros(n, np.int64); end = np.zeros(n, np.int64); P.race_all(LO, CL, A["Hh"], idx, A["ep"], res, end)
    o = P.eval_metrics(res, end, per_idx, A["fee"], n); return dict(p22_3=o["p22_3"], p10_3=o["p10_3"], p22_1=o["p22_1"], med_days22_3=o["med_days22_3"])


def verdict(r):
    return {"med_mes": r["med_mes"] > THR["med_mes"], "p10_mes": r["p10_mes"] >= THR["p10_mes"], "neg60": r["neg60"] < THR["neg60"],
            "evals_perdidas_mes": r["evals_perdidas_mes"] < THR["evals_perdidas_mes"], "aprobacion": r["aprobacion"] >= THR["aprobacion"], "dias_aprobar": r["dias_aprobar"] <= THR["dias_aprobar"]}


def baseline(NB=1000):
    days, M, FU, PER = setup(); OUT = {"NB": NB, "umbrales": THR, "asientos": {}, "plan": {}}; t0 = time.time()
    rng = np.random.default_rng(20261021)                       # integ_paired.py: mismo orden de sorteo -> mismos caminos
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            paths = [P.boot_idx(ii[0], ii[-1] + 1, H, rng) for _ in range(NB)]
            for name in SEATS:
                A = seat_args(FU, hc, name, Hm)
                for fee_s in ("coupon", "list"):
                    fee = A["fee"] if fee_s == "coupon" else A["fee_list"]
                    if fee_s == "list" and fee == A["fee"]: continue
                    flows = np.zeros((NB, H)); mtms = np.zeros((NB, H)); evs = []; nev = []
                    for b, bi in enumerate(paths):
                        ev = np.zeros((MAXEV, 5)); k = run_seat(M, A, bi, 0, H, flows[b], mtms[b], ev, fee); evs.append(ev); nev.append(k)
                    r = metrics(flows, mtms, evs, nev)
                    if fee_s == "coupon": r.update(p22_3(days, M, FU, hc, name, ii, Hm)); r["cumple"] = verdict(r)
                    OUT["asientos"][f"{name} | hc{hc} | {per} | {fee_s}"] = r
                    print(f"{time.time()-t0:6.0f}s {name:11s} hc{hc:<4} {per} {fee_s:6s} med {r['med_mes']:7.0f} p10 {r['p10_mes']:7.0f} neg60 {r['neg60']:5.1f} mtm {r['neg60_mtm']:5.1f} "
                          f"evperd/mes {r['evals_perdidas_mes']:.3f} ctas/mes {r['cuentas_perdidas_mes']:.3f} aprob {r['aprobacion']:5.1f} dias {r['dias_aprobar']:4.0f} (p75 {r['dias_aprobar_p75']:4.0f})"
                          + (f" p22_3 {r['p22_3']:5.1f}" if fee_s == "coupon" else ""), flush=True)
    rng = np.random.default_rng(4242)                           # integ_port.py: mismos caminos del plan (252 + 25 dias)
    L = H + 25; lo, hi = 20, H                                  # ventana con los 8 asientos activos (arranques 0..20, fines 252..272)
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]
            flows = np.zeros((NB, L)); mtms = np.zeros((NB, L)); tot = np.zeros(NB); nev = []; evs = []
            for b, bi in enumerate(paths):
                ev_all = np.zeros((MAXEV, 5)); kk = 0
                for name, cnt in PLAN:
                    A = seat_args(FU, hc, name, Hm)
                    for s in range(cnt):
                        f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); k = run_seat(M, A, bi, 5 * s, H, f, mm, ev)
                        flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0
                        if name == "L150 6c/3c":
                            take = min(k, MAXEV - kk); ev_all[kk:kk + take] = ev[:take]; kk += take
                evs.append(ev_all); nev.append(kk)
            r = dict(med_mes=float(np.median(tot)), p10_mes=float(np.percentile(tot, 10)), p90_mes=float(np.percentile(tot, 90)), P_anio_neg=100 * float((tot < 0).mean()))
            rw = metrics(flows, mtms, None, None, lo, hi)
            r.update(neg60=rw["neg60"], neg60_mtm=rw["neg60_mtm"], neg60_p90_camino=rw["neg60_p90_camino"], med_mes21=rw["med_mes21"], p10_mes21=rw["p10_mes21"], P_mes21_neg=rw["P_mes21_neg"], ventana_neg60=[lo, hi])
            E = np.concatenate([e[:k] for k, e in zip(nev, evs)]); r["evals_perdidas_mes_L150x5"] = float((E[:, 1] == -1).sum() / NB / 12.0); r["cuentas_perdidas_mes_L150x5"] = float((E[:, 3] >= 0).sum() / NB / 12.0)
            OUT["plan"][f"5 L150 + 3 MFFU | hc{hc} | {per} | coupon"] = r
            print(f"{time.time()-t0:6.0f}s PLAN hc{hc:<4} {per} med {r['med_mes']:7.0f} p10 {r['p10_mes']:7.0f} neg60 {r['neg60']:5.1f} mtm {r['neg60_mtm']:5.1f} mes21 med {r['med_mes21']:7.0f} p10 {r['p10_mes21']:7.0f} Pneg {r['P_mes21_neg']:4.1f}", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "objective_baseline.json"), "w"), indent=1)
    write_md(OUT); return OUT


def write_md(OUT):
    L = ["# Linea de base de la funcion objetivo (objective.py, %d caminos)\n" % OUT["NB"], "Umbrales: " + ", ".join(f"{k} {v}" for k, v in OUT["umbrales"].items()) + "\n",
         "| asiento | edge | periodo | fee | med $/mes | p10 | P(anio<0) % | mes21 med / p10 / P<0 | neg60 % (mtm) | evals/anio | evals perd./mes | ctas perd./mes | aprob. % | p22_3 % | dias aprobar (p75) | cumple |", "|" + "---|" * 17]
    for k, r in OUT["asientos"].items():
        nm, hc, per, fee = [x.strip() for x in k.split("|")]
        c = r.get("cumple"); cs = "" if c is None else " ".join(("+" if v else "-") + n for n, v in c.items())
        L.append(f"| {nm} | {hc} | {per} | {fee} | {r['med_mes']:.0f} | {r['p10_mes']:.0f} | {r['P_anio_neg']:.1f} | {r['med_mes21']:.0f} / {r['p10_mes21']:.0f} / {r['P_mes21_neg']:.0f} | {r['neg60']:.1f} ({r['neg60_mtm']:.1f}) | {r['evals_anio']:.1f} | {r['evals_perdidas_mes']:.3f} | {r['cuentas_perdidas_mes']:.3f} | {r['aprobacion']:.1f} | {r.get('p22_3', float('nan')):.1f} | {r['dias_aprobar']:.0f} ({r['dias_aprobar_p75']:.0f}) | {cs} |")
    L += ["", "| plan | edge | periodo | med $/mes | p10 | p90 | P(anio<0) % | mes21 med / p10 / P<0 | neg60 % (mtm) [dias] | evals perd./mes 5 L150 | ctas perd./mes 5 L150 |", "|" + "---|" * 11]
    for k, r in OUT["plan"].items():
        nm, hc, per, fee = [x.strip() for x in k.split("|")]
        L.append(f"| {nm} | {hc} | {per} | {r['med_mes']:.0f} | {r['p10_mes']:.0f} | {r['p90_mes']:.0f} | {r['P_anio_neg']:.1f} | {r['med_mes21']:.0f} / {r['p10_mes21']:.0f} / {r['P_mes21_neg']:.0f} | {r['neg60']:.1f} ({r['neg60_mtm']:.1f}) {r['ventana_neg60']} | {r['evals_perdidas_mes_L150x5']:.3f} | {r['cuentas_perdidas_mes_L150x5']:.3f} |")
    open(os.path.join(HERE, "objective_baseline.md"), "w").write("\n".join(L) + "\n")


def selftest(NB=200):
    """seat_flow debe reproducir prop_wf.seat exactamente (neto, evals, aprobadas, quiebres, retiros, primer retiro) y la suma del flujo = neto."""
    days, M, FU, PER = setup(); rng = np.random.default_rng(7); bad = 0; tot = 0
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            for name in SEATS:
                A = seat_args(FU, hc, name, Hm); LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]
                for _ in range(NB):
                    bi = P.boot_idx(ii[0], ii[-1] + 1, H, rng); o = np.zeros(7); P.seat(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, bi, 0, H, o, A["act"])
                    f = np.zeros(H); mm = np.zeros(H); ev = np.zeros((MAXEV, 5)); k = run_seat(M, A, bi, 0, H, f, mm, ev)
                    E = ev[:k]; first = -1.0
                    pays = np.nonzero(f > 0)[0]
                    if len(pays): first = float(pays[0])
                    got = (round(f.sum(), 6), k, int((E[:, 1] == 1).sum()), int((E[:, 3] >= 0).sum()), int(E[:, 4].sum()), first, round(f.sum() - mm.sum(), 6))
                    exp = (round(o[0], 6), int(o[1]), int(o[2]), int(o[3]), int(o[4]), o[5], 0.0)
                    tot += 1
                    if got[:6] != exp[:6] or abs(mm.sum() - f.sum()) > 1e-6: bad += 1; print("DIFF", name, hc, per, got, exp) if bad <= 5 else None
    print(f"selftest: {tot} asientos, {bad} diferencias contra prop_wf.seat (neto, evals, aprobadas, quiebres, retiros, primer retiro; caja = mtm al final)")
    return bad


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest": sys.exit(1 if selftest() else 0)
    baseline(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)
