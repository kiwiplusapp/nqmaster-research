"""Reproduce los caminos de integ_paired (rng 20261021, mismo orden) para L150 coupon en hc 0 / 0.35 y chequea:
pay62, neg60 paso 1 vs paso 21, ventanas exactamente 0, dias de fee = inicios de eval, ev vs race directo, censura de evals abiertas."""
import sys, json, numpy as np, time
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import objective as O, prop_wf as P
days, M, FU, PER = O.setup(); NB = 1000; H = O.H
rng = np.random.default_rng(20261021); out = {}; t0 = time.time()

def wins(F, W=60, step=1):
    c = np.concatenate([np.zeros((len(F), 1)), np.cumsum(F, 1)], 1); w = c[:, W:] - c[:, :-W]; return w[:, ::step]

for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, H, rng) for _ in range(NB)]
        if hc == 1.0: continue
        for name in ("L150 6c/3c", "MFFU 1x8"):
            if name == "MFFU 1x8" and hc != 0.0: continue
            A = O.seat_args(FU, hc, name, Hm); LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]
            flows = np.zeros((NB, H)); mtms = np.zeros((NB, H)); evs = []; nev = []
            for b, bi in enumerate(paths):
                ev = np.zeros((O.MAXEV, 5)); k = O.run_seat(M, A, bi, 0, H, flows[b], mtms[b], ev); evs.append(ev); nev.append(k)
            r = O.metrics(flows, mtms, evs, nev)
            first = np.array([(np.nonzero(f > 0)[0][0] if (f > 0).any() else -1) for f in flows])
            w1 = wins(flows); w21 = wins(flows, step=21); wm = wins(mtms)
            # ventanas de 21 dias (los 12 cortes) con 0 exacto
            b21 = flows.reshape(NB, 12, 21).sum(2)
            # checks de timing
            fee = A["fee"]; bad_fee = 0; bad_neg = 0; bad_race = 0; bad_bust = 0; nchk = 0; rec = np.zeros(5)
            for b in range(NB):
                E = evs[b][:nev[b]]; st = E[:, 0].astype(int)
                if not np.all(np.isclose(flows[b][st], -fee)): bad_fee += 1
                if (flows[b] < 0).sum() != nev[b]: bad_neg += 1
                if b < 200:
                    for q in range(nev[b]):
                        rr, j = P.race(LO, CL, A["Hh"], paths[b], st[q], H, A["ep"]); nchk += 1
                        if rr != E[q, 1] or (rr != 0 and j != E[q, 2]) or (rr == 0 and E[q, 2] != H - 1): bad_race += 1
                        if rr == 1:
                            P.fund(FL, FC, fp, paths[b], j + 1, H, rec)
                            bd = j + 1 + rec[2] if rec[2] >= 0 else -1
                            if bd != E[q, 3] or rec[3] != E[q, 4]: bad_bust += 1
            E = np.concatenate([e[:k] for k, e in zip(nev, evs)]); done = E[E[:, 1] != 0]; dur = done[:, 2] - done[:, 0] + 1
            # censura: aprobacion por tramo de inicio
            def apr(mask):
                d = E[mask & (E[:, 1] != 0)]; return 100 * (d[:, 1] == 1).mean(), int(len(d)), int((E[mask][:, 1] == 0).sum())
            a_all = apr(np.ones(len(E), bool)); a_early = apr(E[:, 0] < 126); a_late = apr(E[:, 0] >= 126)
            # evals abiertas al final: duracion ya transcurrida
            op = E[E[:, 1] == 0]; op_dur = (H - op[:, 0]) if len(op) else np.array([0.0])
            # ventanas con 0 exacto / <= 0
            res = dict(med_mes=r["med_mes"], p10_mes=r["p10_mes"], pay62=100 * ((first >= 0) & (first < 62)).mean(),
                       neg60_json=r["neg60"], neg60_step1=100 * (w1 < 0).mean(), neg60_step21=100 * (w21 < 0).mean(), n_w21=int(w21.shape[1]),
                       zero60=100 * (w1 == 0).mean(), nonpos60=100 * (w1 <= 0).mean(), neg60_mtm=100 * (wm < 0).mean(),
                       P_mes21_neg=100 * (b21 < 0).mean(), P_mes21_zero=100 * (b21 == 0).mean(),
                       neg60_last_window_mtm=100 * (wm[:, -1] < 0).mean(), neg60_first_window=100 * (w1[:, 0] < 0).mean(),
                       bad_fee_days=bad_fee, bad_negdays=bad_neg, race_checked=nchk, bad_race=bad_race, bad_bust=bad_bust,
                       aprob_all=a_all, aprob_start_lt126=a_early, aprob_start_ge126=a_late,
                       dur_done_p50=float(np.median(dur)), dur_done_p90=float(np.percentile(dur, 90)), dur_done_p99=float(np.percentile(dur, 99)), dur_done_max=float(dur.max()),
                       open_frac=100 * (E[:, 1] == 0).mean(), open_dur_p50=float(np.median(op_dur)), open_dur_p90=float(np.percentile(op_dur, 90)),
                       dias_aprobar=r["dias_aprobar"], dias_p75=r["dias_aprobar_p75"])
            key = f"{name} | hc{hc} | {per}"; out[key] = res
            print(f"{time.time()-t0:5.0f}s {key}"); print("   ", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in res.items()}, flush=True)
json.dump(out, open("/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/verify_seats.json", "w"), indent=1)
