"""r4_fund_probe_lib.py: solo la funcion fund_probe de r4_fund_probe.py (sin efectos al importar)."""
import numpy as np
from numba import njit


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


