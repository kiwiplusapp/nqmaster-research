"""diag_sync_seats.py (2026-10-27, frente 5B, diagnostico): sincronizacion de las plazas del plan sobre los caminos de la base (rng 4242, 300 caminos).
Dos plazas que arrancan una eval el mismo dia quedan identicas desde ahi (mismo camino, mismas reglas): "pares fusionados".
Plazas efectivas = n^2 / suma de la matriz de correlacion de la caja + saldo mensual (dias 20..251). Run desde research/mine. -> diag_sync_seats.json"""
import sys, json, os, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O
days, M, FU, PER = O.setup(); H = O.H; L = H + 25; NB = 300; RES = {}
rng = np.random.default_rng(4242)
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        paths = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(1000)][:NB]
        out = []
        for name, cnt in (("L150 6c/3c", 5), ("MFFU 1x8", 3)):
            A = O.seat_args(FU, hc, name, Hm); merged = 0; pairs = 0; mday = []; frac_same = []; eff = []
            for bi in paths:
                S = []; MT = []
                for s in range(cnt):
                    f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((O.MAXEV, 5)); k = O.run_seat(M, A, bi, 5 * s, H, f, mm, ev)
                    S.append(set(ev[:k, 0].astype(int).tolist())); MT.append(mm)
                for a in range(cnt):
                    for b in range(a + 1, cnt):
                        pairs += 1; common = sorted(S[a] & S[b])
                        # merged: they start an eval on the same day at least once -> identical from there on (same path, same rules, same state)
                        if common: merged += 1; mday.append(common[0])
                MT = np.array(MT)[:, 20:251].reshape(cnt, -1, 21).sum(2)
                c = np.corrcoef(MT); eff.append(cnt ** 2 / np.nansum(c) if np.isfinite(c).all() else np.nan)
            out.append(f"{name}: pares fusionados {100*merged/pairs:.0f} % (dia mediano de fusion {np.median(mday) if mday else float('nan'):.0f}), plazas efectivas (caja + saldo mensual) {np.nanmedian(eff):.1f} de {cnt}")
        print(f"hc{hc} {per}: " + " | ".join(out), flush=True); RES[f"hc{hc} | {per}"] = out
json.dump(RES, open(os.path.join("/home/user/nqmaster-research/research/mine", "diag_sync_seats.json"), "w"), indent=1, ensure_ascii=False)
