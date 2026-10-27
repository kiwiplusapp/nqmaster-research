"""neg60 sobre caminos HISTORICOS CONTIGUOS de 252 dias (inicio cada 5 dias dentro del periodo) vs bootstrap en bloques de 21."""
import sys, json, numpy as np, time
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import objective as O, prop_wf as P
days, M, FU, PER = O.setup(); H = O.H; out = {}; t0 = time.time()

def wins(F, W=60, step=1):
    c = np.concatenate([np.zeros((len(F), 1)), np.cumsum(F, 1)], 1); w = c[:, W:] - c[:, :-W]; return w[:, ::step]

for hc in (0.0, 0.35):
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        starts = np.arange(ii[0], ii[-1] + 1 - H + 1, 5); NBc = len(starts)
        for name in ("L150 6c/3c", "MFFU 1x8"):
            A = O.seat_args(FU, hc, name, Hm)
            flows = np.zeros((NBc, H)); mtms = np.zeros((NBc, H)); evs = []; nev = []
            for b, s in enumerate(starts):
                bi = np.arange(s, s + H, dtype=np.int64); ev = np.zeros((O.MAXEV, 5)); k = O.run_seat(M, A, bi, 0, H, flows[b], mtms[b], ev); evs.append(ev); nev.append(k)
            r = O.metrics(flows, mtms, evs, nev)
            # ventanas de 60 dias historicas contiguas, sin solapamiento entre caminos: tomar solo las ventanas que empiezan en los primeros 5 dias de cada camino
            w1 = wins(flows); w5 = w1[:, :5]
            res = dict(n_caminos=NBc, med_mes=r["med_mes"], p10_mes=r["p10_mes"], P_anio_neg=r["P_anio_neg"], neg60=r["neg60"], neg60_mtm=r["neg60_mtm"], neg60_ventanas_unicas=100 * (w5 < 0).mean(),
                       P_mes21_neg=r["P_mes21_neg"], evals_perdidas_mes=r["evals_perdidas_mes"], cuentas_perdidas_mes=r["cuentas_perdidas_mes"], aprobacion=r["aprobacion"], dias_aprobar=r["dias_aprobar"])
            key = f"{name} | hc{hc} | {per} | contiguo"; out[key] = res
            print(f"{time.time()-t0:5.0f}s {key}", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in res.items()}, flush=True)
json.dump(out, open("/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/verify_contig.json", "w"), indent=1)
