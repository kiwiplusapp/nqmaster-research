"""r4_fund_probe.py: replica instrumentada de prop_wf.fund (rama firma 0) para verificar (a) que reproduce prop_wf.fund, (b) el piso trabado
al primer retiro con X >= 4.600, (c) el saldo real al pedir y el colchon tras el retiro, (d) el saldo perdido al 5.o retiro y al fin del horizonte."""
import os, sys, numpy as np
from numba import njit
M_DIR = "/home/user/nqmaster-research/research/mine"; os.chdir(M_DIR); sys.path.insert(0, M_DIR)
import prop_wf as P, objective as O, exp04_payout_x as X4
XS = X4.XS; H = 252


@njit(cache=False)
def fund_probe(FL, FC, fp, idx, s, n, rec, pays):
    """copia literal de prop_wf.fund firma 0 + registro por retiro: pays[m] = (dia, bal antes, monto, pk, thr al inicio del dia, thr del dia siguiente, qd al pedir)."""
    firm = int(fp[0]); c1 = fp[1]; X = fp[2]; cap1 = fp[5]; Q = fp[7]; npmax = int(fp[8]); D = fp[9]
    lock = 100.0; bal = 0.0; pk = 0.0; cash = 0.0; m = 0; cyc0 = 0.0; qd = 0; locked = False; d = s
    rec[0] = -1.0; rec[2] = -1.0; rec[5] = 0.0
    while d < n:
        t = idx[d]
        thr = lock if (locked or pk >= D + lock) else pk - D
        cu = bal - thr
        g = 0 if cu < c1 else 1
        if bal + FL[g, t] <= thr:
            rec[1] = cash; rec[2] = d - s; rec[3] = m; rec[4] = d; rec[5] = bal; return
        c = FC[g, t]; bal += c
        if bal > pk: pk = bal
        amt = 0.0
        if c >= Q: qd += 1
        q_at = qd
        if qd >= 5 and bal - cyc0 > 0 and bal >= X:
            a = min(cap1, 0.5 * bal)
            if a >= 500.0: amt = a; qd = 0; locked = True
        if amt > 0.0:
            b0 = bal; bal -= amt; cash += 0.9 * amt; m += 1; cyc0 = bal
            thr_next = lock if (locked or pk >= D + lock) else pk - D
            pays[m - 1, 0] = d - s; pays[m - 1, 1] = b0; pays[m - 1, 2] = amt; pays[m - 1, 3] = pk; pays[m - 1, 4] = thr; pays[m - 1, 5] = thr_next; pays[m - 1, 6] = q_at
            if rec[0] < 0: rec[0] = d - s
            if npmax > 0 and m >= npmax:
                rec[1] = cash; rec[3] = m; rec[4] = d; rec[5] = bal; return
        d += 1
    rec[1] = cash; rec[3] = m; rec[4] = n; rec[5] = bal


days, M, FU, PER = O.setup(); n = len(days); idx = np.arange(n, dtype=np.int64)
print("dias:", days[0], "->", days[-1], "n", n)
for hc in (0.0, 0.35):
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        print(f"--- hc{hc} {per}: fondeada sola desde cada dia del periodo, horizonte {H} dias")
        for X in XS:
            A = X4.args_x(FU, hc, X, Hm); FL, FC, fp = A["tiers"]
            mism = 0; lockbad = 0; b_first = []; cush_first = []; amt_first = []; lost5 = []; open_end = []; busts = 0; ncyc = 0; cash = []; npay = []; b_all = []
            for s in ii:
                e = min(n, s + H); rec = np.zeros(6); pays = np.zeros((8, 7)); fund_probe(FL, FC, fp, idx, s, e, rec, pays)
                r2 = np.zeros(5); P.fund(FL, FC, fp, idx, s, e, r2)
                if not np.allclose(rec[:5], r2): mism += 1
                m = int(rec[3]); ncyc += 1; cash.append(rec[1]); npay.append(m)
                if rec[2] >= 0: busts += 1
                for k in range(m):
                    if pays[k, 3] < 4600 or pays[k, 5] != 100.0: lockbad += 1
                    b_all.append(pays[k, 1])
                if m >= 1: b_first.append(pays[0, 1]); amt_first.append(pays[0, 2]); cush_first.append(pays[0, 1] - pays[0, 2] - 100.0)
                if m >= 5: lost5.append(rec[5])
                elif rec[2] < 0: open_end.append(rec[5])
            b_first = np.array(b_first); b_all = np.array(b_all)
            print(f"X{X:<5} fund==prop_wf.fund: {len(ii)-mism}/{len(ii)} | retiros con piso NO trabado: {lockbad} | 1er retiro: n {len(b_first)} saldo med {np.median(b_first):6.0f} (p25 {np.percentile(b_first,25):6.0f} p75 {np.percentile(b_first,75):6.0f}) "
                  f"monto med {np.median(amt_first):5.0f} colchon tras retiro med {np.median(cush_first):5.0f} | saldo al pedir (todos) en [X, X+1000): {100*np.mean(b_all < X + 1000):4.1f}% | "
                  f"quiebres {100*busts/ncyc:4.1f}% | ciclos con 5 retiros {100*len(lost5)/ncyc:4.1f}% saldo perdido med {np.median(lost5) if lost5 else 0:6.0f} | abiertos al fin {100*len(open_end)/ncyc:4.1f}% saldo med {np.median(open_end) if open_end else 0:6.0f} | caja media {np.mean(cash):6.0f}")
