"""r3_indep.py: re-implementacion independiente del bucle de objective.baseline (orden L150 primero, luego MFFU, como la base) con ep de k.
Uso: python3 r3_indep.py SEED_SEAT SEED_PLAN NB OUT.npz [seats]"""
import sys, os, time, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine"); os.chdir("/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O, exp03_eval_size as E
ss, sp, NB, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]; do_seats = len(sys.argv) > 5
days, M, FU, PER = O.setup(); H = O.H; L = H + 25; KS = (1, 2, 3, 4, 5, 6); res = {}; t0 = time.time()
F = P.FIRMS["LucidFlex150K"]
def args(hc, k, Hm):
    A = dict(O.seat_args(FU, hc, "L150 6c/3c", Hm)); A["ep"] = P.ep_of(F, (0, k, k, 0, 0, 0, 0)); return A
# 1) chequeo: args_k de exp03 == seat_args de la base con ep cambiado
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for k in KS:
        a, b = E.args_k(FU, hc, k, Hm), args(hc, k, Hm)
        for q in a:
            va, vb = a[q], b[q]
            same = all(np.array_equal(x, y) for x, y in zip(va, vb)) if isinstance(va, tuple) and q == "tiers" else (np.array_equal(va, vb) if isinstance(va, np.ndarray) else va == vb)
            if not same: print("ARGS DIFF", hc, k, q, va, vb)
        if k != 6:
            e6 = args(hc, 6, Hm)["ep"]; ek = b["ep"]; dif = np.nonzero(e6 != ek)[0].tolist(); print(f"hc{hc} k{k}: ep difiere de k6 solo en posiciones {dif} (7=kA, 8=kB)") if hc == 0.0 else None
if do_seats:
    rng = np.random.default_rng(ss)
    for hc in P.HC:
        Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
        for per, ii in PER.items():
            paths = [P.boot_idx(ii[0], ii[-1] + 1, H, rng) for _ in range(NB)]
            for k in KS:
                A = args(hc, k, Hm); net = np.zeros(NB)
                for b, bi in enumerate(paths):
                    f = np.zeros(H); mm = np.zeros(H); ev = np.zeros((O.MAXEV, 5)); O.run_seat(M, A, bi, 0, H, f, mm, ev); net[b] = f.sum() / 12.0
                res[f"seat_k{k}_hc{hc}_{per}"] = net
        print(f"{time.time()-t0:.0f}s seats hc{hc}", flush=True)
rng = np.random.default_rng(sp)
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]
        if hc == 1.0: continue
        Amf = O.seat_args(FU, hc, "MFFU 1x8", Hm)
        for k in KS:
            A = args(hc, k, Hm); tot = np.zeros(NB); flows = np.zeros((NB, L)); mtms = np.zeros((NB, L)); evs = []; nev = []
            for b, bi in enumerate(paths):
                ev_all = np.zeros((8 * O.MAXEV, 5)); kk = 0
                for AA, cnt in ((A, 5), (Amf, 3)):
                    for s in range(cnt):
                        f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((O.MAXEV, 5)); q = O.run_seat(M, AA, bi, 5 * s, H, f, mm, ev)
                        flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + q] = ev[:q]; kk += q
                evs.append(ev_all); nev.append(kk)
            rw = O.metrics(flows, mtms, evs, nev, 20, H)
            r = dict(med_mes=float(np.median(tot)), p10_mes=float(np.percentile(tot, 10))); r.update({q: rw[q] for q in ("neg60", "evals_perdidas_mes", "aprobacion", "dias_aprobar", "dias_aprobar_p75", "evals_anio")})
            v = O.verdict(r); res[f"plan_k{k}_hc{hc}_{per}"] = tot
            res[f"plan_k{k}_hc{hc}_{per}_m"] = np.array([r[q] for q in ("med_mes", "p10_mes", "neg60", "evals_perdidas_mes", "aprobacion", "dias_aprobar", "dias_aprobar_p75", "evals_anio")] + [float(x) for x in v.values()])
            print(f"{time.time()-t0:.0f}s plan k{k} hc{hc} {per} med {r['med_mes']:.1f} p10 {r['p10_mes']:.1f} neg60 {r['neg60']:.2f} evp {r['evals_perdidas_mes']:.3f} apr {r['aprobacion']:.2f} dias {r['dias_aprobar']} cumple {sum(v.values())}", flush=True)
np.savez(out, **res)
