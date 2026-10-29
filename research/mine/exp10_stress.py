"""exp10_stress.py (2026-10-29, experimento 10 / frente 5D): estres de la campana por costos de ejecucion (x ticks extra por lado = x $ por
contrato-trade) y por edge (completo, -35 %, regimen 2015-19 = -68 %, cero). Plan pre-registrado: docs/PLAN_2026-10-29_exp10.md.
Run (desde research/mine): python3 exp10_stress.py selftest | python3 exp10_stress.py [NB]"""
import os, sys, json, time, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import prop_wf as P, objective as O, exp03_eval_size as E3
H = O.H; L = H + 25; MAXEV = O.MAXEV; MIXES = ((0, 4), (0, 8), (300, 4)); XS = (0, 1, 2, 3); HCS = (0.0, 0.35, 0.68, 1.0)
L150 = "L150 6c/3c"; MF = "MFFU 1x8"


def mixes_x(Mb, x):
    """mezclas con x $ extra por contrato-trade restados por dia (cc = ca + m cb del acct2027_paths)"""
    _, Pp = pickle.load(open(P.SRC, "rb")); out = {}
    for cap, m in MIXES:
        a, b, ca, cb = Pp[cap]; cc = ca + m * cb; LO, CL, FIN = Mb[(cap, m)]
        out[(cap, m)] = (np.ascontiguousarray(LO - x * cc[:, None]), np.ascontiguousarray(CL - x * cc[:, None]), FIN - x * cc)
    return out


def fund_x(days, Mb, Mx):
    """prop_wf.Fund sobre las mezclas con costo extra, con el recorte calculado sobre la mezcla base"""
    FU = P.Fund(days, Mx)
    for hc in HCS:
        for mix in MIXES: FU.H[(hc, mix)] = P.haircut(days, Mb[mix][2], hc)
    return FU


def args(FU, hc, Mb, days):
    Hm = {m: P.haircut(days, Mb[m][2], hc) for m in MIXES}
    return O.seat_args(FU, hc, L150, Hm), O.seat_args(FU, hc, MF, Hm)


def plan_cell(M, AL, AM, paths):
    NB = len(paths); flows = np.zeros((NB, L)); mtms = np.zeros((NB, L)); tot = np.zeros(NB); evs = []; nev = []
    for b, bi in enumerate(paths):
        ev_all = np.zeros((8 * MAXEV, 5)); kk = 0
        for A, cnt in ((AL, 5), (AM, 3)):
            for s in range(cnt):
                f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); k = O.run_seat(M, A, bi, 5 * s, H, f, mm, ev)
                flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + k] = ev[:k]; kk += k
        evs.append(ev_all); nev.append(kk)
    r = E3.plan_metrics(flows, mtms, evs, nev, tot); r["media_mes"] = float(tot.mean()); return r, tot


def seat_cell(M, A, paths):
    NB = len(paths); flows = np.zeros((NB, H)); mtms = np.zeros((NB, H)); evs = []; nev = []
    for b, bi in enumerate(paths):
        ev = np.zeros((MAXEV, 5)); k = O.run_seat(M, A, bi, 0, H, flows[b], mtms[b], ev); evs.append(ev); nev.append(k)
    return O.metrics(flows, mtms, evs, nev)


def setup_paths(NB):
    days, Mb, FU0, PER = O.setup(); rng_p = np.random.default_rng(4242); rng_s = np.random.default_rng(20261021); PP = {}; PS = {}
    for hc in P.HC:
        for per, ii in PER.items(): PS[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, H, rng_s) for _ in range(1000)][:NB]
    for hc in P.HC:
        for per, ii in PER.items(): PP[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, L, rng_p) for _ in range(1000)][:NB]
    return days, Mb, PER, {per: PP[(0.0, per)] for per in PER}, {per: PS[(0.0, per)] for per in PER}


def selftest():
    days, Mb, PER, PP, PS = setup_paths(1000); Mx = mixes_x(Mb, 0); FU = fund_x(days, Mb, Mx); AL, AM = args(FU, 0.0, Mb, days)
    base = json.load(open(os.path.join(HERE, "integ_port.json"))); bad = 0
    for per in PER:
        r, _ = plan_cell(Mx, AL, AM, PP[per]); ref = base[f"hc0.0 | {per} | coupon | rot"]
        d = (round(r["med_mes"]) - ref["med"], round(r["p10_mes"]) - ref["p10"]); bad += any(d)
        print(f"selftest x0 completo {per}: med {r['med_mes']:.0f} p10 {r['p10_mes']:.0f} vs integ_port {ref['med']} {ref['p10']} -> dif {d}", flush=True)
    print("selftest:", "OK" if not bad else f"{bad} diferencias"); return bad


def main(NB=1000):
    days, Mb, PER, PP, PS = setup_paths(NB); t0 = time.time(); n = len(days); idx = np.arange(n, dtype=np.int64)
    OUT = {"NB": NB, "XS": XS, "HCS": HCS, "celdas": {}}
    for x in XS:
        Mx = mixes_x(Mb, x); FU = fund_x(days, Mb, Mx)
        for hc in HCS:
            AL, AM = args(FU, hc, Mb, days)
            for per, ii in PER.items():
                pl_b, _ = plan_cell(Mx, AL, AM, PP[per]); se_b = seat_cell(Mx, AL, PS[per]); se_b["p22_3"] = E3.p22(days, Mx, AL, ii)["p22_3"]
                stp = np.arange(ii[0], ii[-1] + 2 - L, 5); st = np.arange(ii[0], ii[-1] + 2 - H, 5)
                pl_c, _ = plan_cell(Mx, AL, AM, [idx[s0:s0 + L] for s0 in stp]); se_c = seat_cell(Mx, AL, [idx[s0:s0 + H] for s0 in st]); se_c["p22_3"] = se_b["p22_3"]
                for src, pl, se in (("bootstrap", pl_b, se_b), ("contiguo", pl_c, se_c)):
                    v = O.verdict_d1(pl, se); OUT["celdas"][f"x{x} | hc{hc} | {per} | {src}"] = dict(plan=pl, asiento_L150=se, cumple_d1=v, n_cumple=int(sum(v.values())))
                print(f"{time.time()-t0:5.0f}s x+{x} hc{hc:<4} {per} boot med {pl_b['med_mes']:7.0f} media {pl_b['media_mes']:7.0f} p10 {pl_b['p10_mes']:7.0f} Pneg {pl_b['P_anio_neg']:5.1f} neg60 {pl_b['neg60']:5.1f} p22 {se_b['p22_3']:5.1f} | contig med {pl_c['med_mes']:7.0f} p10 {pl_c['p10_mes']:7.0f} neg60 {pl_c['neg60']:5.1f}", flush=True)
    OUT["salidas"] = salidas(OUT); print(OUT["salidas"])
    json.dump(OUT, open(os.path.join(HERE, "exp10_stress.json"), "w"), indent=1); return OUT


def salidas(OUT):
    c = lambda x, hc, per, src="bootstrap": OUT["celdas"][f"x{x} | hc{hc} | {per} | {src}"]
    R = {}
    for hc in (0.0, 0.35):
        best = None                                                    # mayor x tal que todos los x' <= x cumplen M1 en T1 y T2 (bootstrap)
        for x in XS:
            if all(c(x, hc, per)["cumple_d1"]["med_mes"] and c(x, hc, per)["cumple_d1"]["p10_mes"] for per in ("T1", "T2")): best = x
            else: break
        R[f"presupuesto_costos_M1_hc{hc}"] = best
    for hc in HCS:
        for per in ("T1", "T2"):
            med = [c(x, hc, per)["plan"]["med_mes"] for x in XS]
            cero = None
            for i in range(1, len(XS)):
                if med[i - 1] > 0 >= med[i]: cero = XS[i - 1] + med[i - 1] / (med[i - 1] - med[i]) * (XS[i] - XS[i - 1])
            if med[0] <= 0: cero = 0.0
            R[f"costo_extra_mediana_cero hc{hc} {per}"] = cero
    return R


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest": sys.exit(1 if selftest() else 0)
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)
