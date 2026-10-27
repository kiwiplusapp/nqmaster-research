"""r4_seat_probe.py: asiento L150 sobre los MISMOS caminos bootstrap del exp04 (guardados por r4_rerun.py) con la fondeada instrumentada:
saldo que queda en la cuenta al 5.o retiro (fin de ciclo, no se cobra) y saldo abierto al fin del horizonte, por X. Verifica el neto contra NET."""
import os, sys, pickle, numpy as np
M_DIR = "/home/user/nqmaster-research/research/mine"; os.chdir(M_DIR); sys.path.insert(0, M_DIR)
SP = "/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad"; sys.path.insert(1, SP)
import prop_wf as P, objective as O, exp04_payout_x as X4
from r4_fund_probe_lib import fund_probe
D = pickle.load(open(os.path.join(SP, "r4_net.pkl"), "rb")); NET = D["NET"]; PATHS = D["PATHS"]; H = 252
days, M, FU, PER = O.setup()
for hc in (0.0, 0.35):
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per in ("T1", "T2"):
        paths = PATHS[("seat", hc, per)]; row = []
        for X in X4.XS:
            A = X4.args_x(FU, hc, X, Hm); LO, CL, _ = M[A["mix"]]; FL, FC, fp = A["tiers"]; ep = A["ep"]; fee = A["fee"]
            net = np.zeros(len(paths)); lost5 = np.zeros(len(paths)); openend = np.zeros(len(paths)); ncyc5 = np.zeros(len(paths))
            for b, bi in enumerate(paths):
                i = 0; cash = 0.0; fees = 0.0
                while i < H:
                    fees += fee; r, j = P.race(LO, CL, A["Hh"], bi, i, H, ep)
                    if r != 1: i = j + 1; continue
                    rec = np.zeros(6); pays = np.zeros((8, 7)); fund_probe(FL, FC, fp, bi, j + 1, H, rec, pays)
                    cash += rec[1]
                    if rec[3] >= 5: lost5[b] += rec[5]; ncyc5[b] += 1
                    elif rec[2] < 0: openend[b] += rec[5]
                    i = int(rec[4]) + 1
                net[b] = (cash - fees) / 12.0
            ok = np.allclose(net, NET[("seat", X, hc, per)], atol=1e-6)
            row.append(f"X{X}: neto==exp04 {ok} | med $/mes {np.median(net):5.0f} | ciclos de 5 retiros/anio {ncyc5.mean():.2f} saldo perdido al 5.o retiro $/mes {lost5.mean()/12:5.0f} | saldo abierto al fin $/mes {openend.mean()/12:5.0f}")
        print(f"--- asiento L150 hc{hc} {per} (1.000 caminos del exp04)"); print("\n".join(row))
