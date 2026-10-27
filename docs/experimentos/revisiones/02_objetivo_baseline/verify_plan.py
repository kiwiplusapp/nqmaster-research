"""Plan: rng 4242 (mismo orden que objective.baseline / integ_port). Para hc1.0 (peor caso) cuenta las evals L150 por camino (truncado en MAXEV=400?).
Para hc0 T1 reproduce el plan completo y compara med/p10 con integ_port.json; chequea la ventana [20,252) y los buckets de 21."""
import sys, json, numpy as np, time
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import objective as O, prop_wf as P
days, M, FU, PER = O.setup(); NB = 1000; H = O.H; L = H + 25; out = {}; t0 = time.time()
rng = np.random.default_rng(4242)
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]
        if hc == 1.0:
            kk = np.zeros(NB, int); kmax_seat = 0
            A = O.seat_args(FU, hc, "L150 6c/3c", Hm)
            for b, bi in enumerate(paths):
                for s in range(5):
                    f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((O.MAXEV, 5)); k = O.run_seat(M, A, bi, 5 * s, H, f, mm, ev); kk[b] += k; kmax_seat = max(kmax_seat, k)
            out[f"plan hc1.0 {per} evals L150 por camino"] = dict(mean=float(kk.mean()), p99=float(np.percentile(kk, 99)), max=int(kk.max()), n_truncados=int((kk > O.MAXEV).sum()), max_por_asiento=int(kmax_seat))
            print(f"{time.time()-t0:5.0f}s", list(out.items())[-1], flush=True)
        if hc == 0.0 and per == "T1":
            flows = np.zeros((NB, L)); mtms = np.zeros((NB, L)); tot = np.zeros(NB); act_days = np.zeros(L)
            for b, bi in enumerate(paths):
                for name, cnt in O.PLAN:
                    A = O.seat_args(FU, hc, name, Hm)
                    for s in range(cnt):
                        f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((O.MAXEV, 5)); k = O.run_seat(M, A, bi, 5 * s, H, f, mm, ev)
                        flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0
                        if b == 0: act_days[5 * s:5 * s + H] += 1
            rw = O.metrics(flows, mtms, None, None, 20, H)
            # alternativas: ventana completa 0..272 (todos los dias con algun asiento) y 0..252
            r_all = O.metrics(flows, mtms, None, None, 0, 272); r_0 = O.metrics(flows, mtms, None, None, 0, H)
            out["plan hc0.0 T1"] = dict(med=float(np.median(tot)), p10=float(np.percentile(tot, 10)), neg60_20_252=rw["neg60"], neg60_mtm_20_252=rw["neg60_mtm"], buckets21_en_20_252=int((H - 20) // 21),
                                        neg60_0_272=r_all["neg60"], neg60_0_252=r_0["neg60"], dias_con_8_asientos=int((act_days == 8).sum()), primer_dia_8=int(np.nonzero(act_days == 8)[0][0]), ultimo_dia_8=int(np.nonzero(act_days == 8)[0][-1]),
                                        P_mes21_neg_20_252=rw["P_mes21_neg"], med_mes21=rw["med_mes21"])
            print(f"{time.time()-t0:5.0f}s", out["plan hc0.0 T1"], flush=True)
json.dump(out, open("/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/verify_plan.json", "w"), indent=1)
