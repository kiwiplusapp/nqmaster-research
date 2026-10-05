"""Apex lifecycle with general parameters (unrealized trailing on minute paths). 50K: target 3000, trailing 2500, safety net
start+2500+100 (threshold stops trailing at start+100 once peak >= safety net), payout caps 1500,2000,2500,2500,3000,3000,
min request 500, 5 days >= $200 since last payout, 50% consistency, 6 payouts max. Eval $19.70 per attempt, PA $90."""
import numpy as np, pandas as pd
from numba import njit
from evalfast import run as eval_run
@njit(cache=True)
def pa_gen(day, fav, adv, rel, start, end, k, DD, qday, caps):
    i = np.searchsorted(day, start)
    bal = 0.0; pk = 0.0; cash = 0.0; n = 0; cyc0 = 0.0; best = -1e9; qd = 0; d = start; safety = DD + 100.0
    while d < end:
        while i < len(day) and day[i] == d:
            thr = 100.0 if pk >= safety else pk - DD
            if bal + k * adv[i] <= thr: return cash, n, -1, d
            b = bal + k * fav[i]
            if b > pk: pk = b
            last = rel[i]; i += 1
        dp = 0.0
        # realized day pnl = k * last rel of the day (rel is cumulative within day)
        j = i - 1
        if j >= 0 and day[j] == d: dp = k * rel[j]
        bal += dp
        if bal > pk: pk = bal
        if dp >= qday: qd += 1
        if dp > best: best = dp
        prof = bal - cyc0
        if qd >= 5 and bal >= safety + 500 and prof > 0 and best < 0.5 * prof:
            amt = min(caps[min(n, len(caps) - 1)], bal - safety)
            if amt >= 500:
                bal -= amt; cash += amt; n += 1; cyc0 = bal; best = -1e9; qd = 0
                if n == 6: return cash, n, 1, d
        d += 1
    return cash, n, 0, end
def life(P, ek, pk_, T=3000.0, DD=2500.0, qday=200.0, caps=(1500., 2000., 2500., 2500., 3000., 3000.), fee=19.70, H=252, step=3, PP=None):
    PP = PP or P; nd = P["ndays"]; caps = np.array(caps); out = []
    for s in range(0, nd - H, step):
        i = s; cash = fees = 0.0; pays = npa = nb = 0
        while i < s + H:
            fees += fee
            r, used = eval_run(P["day"], P["fav"], P["adv"], P["rel"], nd, i, T, DD, min(21, s + H - i), 0, ek, 1, 0.0, 0.0, 0.0)
            j = i + used
            if r != 1: i = j; continue
            fees += 90; npa += 1
            c, k, st, dend = pa_gen(PP["day"], PP["fav"], PP["adv"], PP["rel"], j, s + H, pk_, DD, qday, caps)
            cash += c; pays += k; nb += st == -1; i = dend + 1
        out.append((cash - fees, pays, npa, nb))
    a = np.array(out)
    return dict(net_mo=round(a[:, 0].mean() / 12), p10_mo=round(np.percentile(a[:, 0], 10) / 12), payouts_yr=round(a[:, 1].mean(), 1), PAs_yr=round(a[:, 2].mean(), 1), PA_busts_yr=round(a[:, 3].mean(), 1))
