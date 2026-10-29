"""diag_neg60_calendar.py (2026-10-29, frente 5C, diagnostico): en que trimestres calendario caen las ventanas de 60 dias con caja negativa del plan
(5 L150 + 3 MFFU) sobre historia contigua, y el P&L del sistema por contrato base de los 60 dias previos en esos trimestres. Run desde research/mine."""
import sys, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O
days, M, FU, PER = O.setup(); H = O.H; L = H + 25; n = len(days); idx = np.arange(n, dtype=np.int64)
for hc in (0.0, 0.35):
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    AL, AM = O.seat_args(FU, hc, "L150 6c/3c", Hm), O.seat_args(FU, hc, "MFFU 1x8", Hm)
    neg = np.zeros(n); cnt = np.zeros(n)
    for ii in PER.values():
        for s0 in np.arange(ii[0], ii[-1] + 2 - L, 5):
            F = np.zeros(n)
            for A, k in ((AM, 3), (AL, 5)):
                for s in range(k):
                    f = np.zeros(n); mm = np.zeros(n); ev = np.zeros((O.MAXEV, 5)); O.run_seat(M, A, idx, int(s0) + 5 * s, H, f, mm, ev); F += f
            c = np.concatenate([[0.0], np.cumsum(F[s0 + 20:s0 + H])]); w = c[60:] - c[:-60]
            ends = np.arange(s0 + 20 + 59, s0 + H)                     # calendar day where each window ends
            neg[ends] += (w < 0); cnt[ends] += 1
    # system P&L per base contract (full mix) over the trailing 60 days, as a regime proxy
    fin = M[(0, 4)][2] - Hm[(0, 4)]; r60 = np.concatenate([[np.nan] * 59, np.convolve(fin, np.ones(60), "valid")])
    print(f"== edge hc{hc}: fraccion de planes con ventana de 60 d negativa, por trimestre calendario (fin de ventana) | P&L del sistema 60 d por contrato (media del trimestre)")
    q = (days // 10000) * 10 + ((days // 100) % 100 - 1) // 3 + 1
    for qq in np.unique(q):
        m = (q == qq) & (cnt > 0)
        if m.sum() == 0: continue
        print(f"  {qq // 10}T{qq % 10}: {100 * neg[m].sum() / cnt[m].sum():5.1f} % de ventanas negativas (n {int(cnt[m].sum()):5d})  P&L sistema 60 d {np.nanmean(r60[m]):7.0f}")
