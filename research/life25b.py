"""12-month lifecycle per account slot on minute paths (unrealized trailing): eval (policy E) -> PA (policy P) -> repeat.
Eval: target 1500, trailing 1500, max 21 trading days, $17.70 per attempt. PA: $90, trailing 1500 on open equity until
peak >= 26,600 then fixed threshold 25,100; payout at day end if >=5 days >= $100 since last payout, bal >= 26,600,
best day < 50% of cycle profit; amount min(1000, bal-26,100) >= 500; closed after 6 payouts.
PA sizing: mode 0 fixed k1 | 4: k2 when cushion (bal - threshold) >= C else k1."""
import pickle, numpy as np, pandas as pd
from numba import njit
from evalfast import run as eval_run
@njit(cache=True)
def pa_run(day, fav, adv, rel, ndays, start, end, mode, k1, k2, C, B):
    i = np.searchsorted(day, start)
    bal = 25000.0; pk = 25000.0; cash = 0.0; n = 0; cyc0 = bal; best = -1e9; qd = 0; d = start
    while d < end:
        thr = 25100.0 if pk >= 26600.0 else pk - 1500.0
        k = k1
        if mode == 4 and bal - thr >= C: k = k2
        last = 0.0
        while i < len(day) and day[i] == d:
            thr = 25100.0 if pk >= 26600.0 else pk - 1500.0
            if bal + k * adv[i] <= thr: return cash, n, -1, d
            b = bal + k * fav[i]
            if b > pk: pk = b
            last = rel[i]; i += 1
        dp = k * last; bal += dp
        if bal > pk: pk = bal
        if dp >= 100: qd += 1
        if dp > best: best = dp
        prof = bal - cyc0
        if qd >= 5 and bal >= 26600.0 + B and prof > 0 and best < 0.5 * prof:
            amt = min(1000.0, bal - 26100.0 - B) if B > 0 else min(1000.0, bal - 26100.0)
            if amt >= 500:
                bal -= amt; cash += amt; n += 1; cyc0 = bal; best = -1e9; qd = 0
                if n == 6: return cash, n, 1, d
        d += 1
    return cash, n, 0, end
def lifecycle(P, E, PAp, H=252, step=3):
    day, fav, adv, rel, nd = P["day"], P["fav"], P["adv"], P["rel"], P["ndays"]
    out = []
    for s in range(0, nd - H, step):
        i = s; cash = fees = 0.0; npa = nbust = pays = evals = 0; pa_days = 0
        while i < s + H:
            evals += 1; fees += 17.70
            r, used = eval_run(day, fav, adv, rel, nd, i, 1500.0, 1500.0, min(21, s + H - i), E.get("mode", 0), E.get("k1", 1), E.get("k2", 1), E.get("thr", 0.0), E.get("dl", 0.0), E.get("dg", 0.0))
            j = i + used
            if r != 1: i = j; continue
            fees += 90; npa += 1
            c, k, st, dend = pa_run(day, fav, adv, rel, nd, j, s + H, PAp.get("mode", 0), PAp.get("k1", 1), PAp.get("k2", 1), PAp.get("C", 1e9), PAp.get("B", 0.0))
            cash += c; pays += k; nbust += st == -1; pa_days += dend - j; i = dend + 1
        out.append((cash - fees, cash, fees, pays, evals, npa, nbust, pa_days))
    a = np.array(out)
    return dict(net_mo=round(a[:, 0].mean() / 12), p10_mo=round(np.percentile(a[:, 0], 10) / 12), worst_mo=round(a[:, 0].min() / 12), payouts_yr=round(a[:, 3].mean(), 1),
                evals_yr=round(a[:, 4].mean(), 1), PAs_yr=round(a[:, 5].mean(), 1), PA_busts_yr=round(a[:, 6].mean(), 1), PA_share=round(a[:, 7].mean() / H * 100))
