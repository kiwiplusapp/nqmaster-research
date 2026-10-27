"""r4_rerun.py: re-corre la logica de exp04_payout_x.main SIN escribir nada en el repo; guarda NET por camino en el scratchpad
y compara contra exp04_payout_x.json. Ademas verifica que los argumentos de los 7 candidatos difieren solo en fp[2]."""
import os, sys, json, time, pickle, numpy as np
M_DIR = "/home/user/nqmaster-research/research/mine"; os.chdir(M_DIR); sys.path.insert(0, M_DIR)
import prop_wf as P, objective as O, exp03_eval_size as E3, exp04_payout_x as X4
SP = os.path.dirname(os.path.abspath(__file__)); NB = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
XS, INC, H = X4.XS, X4.INC, X4.H
days, M, FU, PER = O.setup(); t0 = time.time()

# (1) los argumentos difieren solo en X
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    A0 = X4.args_x(FU, hc, INC, Hm); Ak = E3.args_k(FU, hc, 6, Hm)
    for X in XS:
        A = X4.args_x(FU, hc, X, Hm); FL, FC, fp = A["tiers"]; FL0, FC0, fp0 = A0["tiers"]
        dif = [i for i in range(len(fp)) if fp[i] != fp0[i]]
        same = np.array_equal(A["ep"], A0["ep"]) and np.array_equal(FL, FL0) and np.array_equal(FC, FC0) and A["Hh"] is A0["Hh"] and A["fee"] == A0["fee"] and A["act"] == A0["act"] and A["mix"] == A0["mix"]
        assert same, (hc, X)
        assert dif == ([] if X == INC else [2]) and fp[2] == X, (hc, X, dif, fp)
    FLk, FCk, fpk = Ak["tiers"]; FL0, FC0, fp0 = A0["tiers"]
    assert np.array_equal(Ak["ep"], A0["ep"]) and np.array_equal(FLk, FL0) and np.array_equal(FCk, FC0) and np.array_equal(fpk, fp0)
print("args: los 7 candidatos comparten ep, FL, FC, Hh, fee, act, mix; fp difiere solo en el indice 2 (= X); X6000 == exp03 k6 == objective SEATS. fp(hc0) =", X4.args_x(FU, 0.0, 6000, {m: P.haircut(days, M[m][2], 0.0) for m in ((0, 4), (0, 8))})["tiers"][2])

OUT = {"asiento": {}, "plan": {}, "asiento_contiguo": {}, "plan_contiguo": {}, "pareado": {}}; NET = {}; PATHS = {}
rng = np.random.default_rng(20261021)
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, H, rng) for _ in range(NB)]; PATHS[("seat", hc, per)] = np.array(paths)
        for X in XS:
            A = X4.args_x(FU, hc, X, Hm); flows, mtms, evs, nev = E3.seat_cell(M, A, paths); r = O.metrics(flows, mtms, evs, nev); r["cumple"] = O.verdict(r)
            OUT["asiento"][f"L150 X{X} | hc{hc} | {per}"] = r; NET[("seat", X, hc, per)] = flows.sum(1) / 12.0
            NET[("seatF", X, hc, per)] = flows; NET[("seatE", X, hc, per)] = (evs, nev)
print(f"{time.time()-t0:.0f}s asientos")
rng = np.random.default_rng(4242); L = H + 25
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(NB)]; PATHS[("plan", hc, per)] = np.array(paths); mf = E3.mffu_cell(M, FU, hc, Hm, paths)
        NET[("mffu", hc, per)] = mf[4]
        for X in XS:
            flows, mtms, evs, nev, tot = X4.plan_cell(M, X4.args_x(FU, hc, X, Hm), paths, mf); r = E3.plan_metrics(flows, mtms, evs, nev, tot)
            OUT["plan"][f"plan X{X} | hc{hc} | {per}"] = r; NET[("plan", X, hc, per)] = tot; NET[("planF", X, hc, per)] = flows
print(f"{time.time()-t0:.0f}s planes")
for (u, X, hc, per), v in [(k, v) for k, v in NET.items() if k[0] in ("seat", "plan")]:
    if X != INC: OUT["pareado"][f"{u} X{X} vs X{INC} | hc{hc} | {per}"] = E3.paired(v, NET[(u, INC, hc, per)])
n = len(days); idx = np.arange(n, dtype=np.int64)
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        st = np.arange(ii[0], ii[-1] + 2 - H, 5); stp = np.arange(ii[0], ii[-1] + 2 - L, 5)
        pp = [idx[s0:s0 + L] for s0 in stp]; mfp = E3.mffu_cell(M, FU, hc, Hm, pp)
        for X in XS:
            A = X4.args_x(FU, hc, X, Hm); flows, mtms, evs, nev = E3.seat_cell(M, A, [idx[s0:s0 + H] for s0 in st]); r = O.metrics(flows, mtms, evs, nev); r["cumple"] = O.verdict(r)
            OUT["asiento_contiguo"][f"L150 X{X} | hc{hc} | {per}"] = r
            flows, mtms, evs, nev, tot = X4.plan_cell(M, A, pp, mfp); r = E3.plan_metrics(flows, mtms, evs, nev, tot); OUT["plan_contiguo"][f"plan X{X} | hc{hc} | {per}"] = r
            NET[("pcont", X, hc, per)] = tot; NET[("pcontF", X, hc, per)] = flows
print(f"{time.time()-t0:.0f}s contiguo")
OUT["regla"] = X4.decide(OUT)

# comparar contra el JSON publicado
J = json.load(open(os.path.join(M_DIR, "exp04_payout_x.json"))); nd = 0; nk = 0
for sec in ("asiento", "plan", "asiento_contiguo", "plan_contiguo", "pareado"):
    for k, r in OUT[sec].items():
        for q, v in r.items():
            nk += 1; w = J[sec][k][q]
            if isinstance(v, dict): ok = v == w
            elif isinstance(v, list): ok = np.allclose(v, w, rtol=0, atol=1e-9)
            else: ok = (v == w) or (np.isnan(v) and np.isnan(w))
            if not ok: nd += 1; print("DIFF", sec, k, q, v, w) if nd < 10 else None
print(f"re-corrida NB={NB}: {nk} valores, {nd} distintos del JSON publicado; regla igual: {OUT['regla'] == J['regla']}")
pickle.dump(dict(NET={k: v for k, v in NET.items() if k[0] in ('seat', 'plan', 'pcont', 'mffu', 'pcontF')}, PATHS=PATHS), open(os.path.join(SP, "r4_net.pkl"), "wb"), protocol=4)
print("guardado", os.path.join(SP, "r4_net.pkl"))
