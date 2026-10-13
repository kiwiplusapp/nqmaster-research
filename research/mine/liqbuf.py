"""Audit item M8 (2026-10-12): intraday liquidation buffer for prop accounts. In realtime, if account equity (cash + open P&L) falls
to the firm's threshold + buffer, flatten and stop for the day (only when the day started with a cushion above the buffer).
NEW Ultra default (UltraR + $300 per-contract risk cap below $1,200 eval / $2,000 funded cushion), MFFU Rapid EOD 50K lifecycle,
1 contract, 1,000 resampled 12-month paths per period (paired), +1 tick; extra exit slippage of $20 when the buffer triggers.
Day model: the day's intraday low of equity (incl. open trades' adverse excursion) and close; when the buffer triggers the day ends
at threshold + buffer - $20. -> liqbuf.json"""
import os, sys, json, pickle, numpy as np
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, vectors, boot, SP


@njit(cache=True)
def day(EL, EC, g, t, eq, thr, buf):
    lo = EL[g, t]; c = EC[g, t]
    if buf > 0 and eq - thr > buf and eq + lo <= thr + buf: return thr + buf - 20.0 - eq, False
    if eq + lo <= thr: return 0.0, True
    return c, False


@njit(cache=True)
def ev(EL, EC, C, idx, s, n, buf):
    eq = 0.0; pk = 0.0; best = -1e9; d = s
    while d < n:
        t = idx[d]; thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        g = 1 if eq - thr >= C else 0
        c, bust = day(EL, EC, g, t, eq, thr, buf)
        if bust: return -1, d
        eq += c
        if c > best: best = c
        if eq > pk: pk = eq
        if eq >= 3000.0 and d - s + 1 >= 4 and best <= 0.3 * eq: return 1, d
        d += 1
    return 0, n


@njit(cache=True)
def fu(FL, FC, c1, idx, start, n, buf):
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; d = start
    while d < n:
        t = idx[d]; thr = 100.0 if pk >= 2100.0 else pk - 2000.0
        g = 0 if bal - thr < c1 else 1
        c, bust = day(FL, FC, g, t, bal, thr, buf)
        if bust: return cash, m, -1, d
        bal += c
        if bal > pk: pk = bal
        if bal - 4100.0 >= 500.0:
            amt = bal - 4100.0; bal -= amt; cash += 0.9 * amt; m += 1
        d += 1
    return cash, m, 0, n


@njit(cache=True)
def life(EL, EC, FL, FC, ids, H, buf, out):
    for r in range(len(ids)):
        idx = ids[r]; i = 0; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0
        while i < H:
            fees += 157.0; nev += 1
            res, j = ev(EL, EC, 1200.0, idx, i, H, buf)
            if res != 1: i = j + 1; continue
            npass += 1
            c, m, st, j2 = fu(FL, FC, 2000.0, idx, j + 1, H, buf)
            cash += c; nb += st == -1; i = j2 + 1
        out[r, 0] = cash - fees; out[r, 1] = nev; out[r, 2] = npass; out[r, 3] = nb


if __name__ == "__main__":
    E = RB.setup(); TRD = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))
    days = pickle.load(open(os.path.join(SP, "robust2_paths.pkl"), "rb"))[0]
    X = RB.attach(TRD["UltraR"][0][TRD["UltraR"][0].date.isin(days)], E); V = {}
    for cap, XX in ((0, X), (300, X[X.risk <= 300])):
        low, close, fin = full_paths(XX, days); c = (XX.w * 1.0).groupby(XX.date).sum().reindex(days, fill_value=0.0).to_numpy()
        for G in (0.0, 800.0):
            V[(cap, G, 0)] = vectors(low, close, fin, G); V[(cap, G, 1)] = vectors(low - c[:, None], close - c[:, None], fin - c, G)
    IDS = {"2020-23": boot(days, (days >= 20200101) & (days < 20240101), 11), "2024-26": boot(days, days >= 20240101, 12)}
    OUT = {}
    for buf in (0.0, 100.0, 150.0, 250.0, 400.0):
        rec = {}
        for per, ids in IDS.items():
            ids = np.ascontiguousarray(np.array(ids))
            for t1 in (0, 1):
                EL = np.ascontiguousarray(np.array([V[(300, 800.0, t1)][0], V[(0, 800.0, t1)][0]])); EC = np.ascontiguousarray(np.array([V[(300, 800.0, t1)][1], V[(0, 800.0, t1)][1]]))
                FL = np.ascontiguousarray(np.array([V[(300, 0.0, t1)][0], V[(0, 0.0, t1)][0]])); FC = np.ascontiguousarray(np.array([V[(300, 0.0, t1)][1], V[(0, 0.0, t1)][1]]))
                o = np.zeros((len(ids), 4)); life(EL, EC, FL, FC, ids, 252, buf, o)
                rec[per + (" +1tick" if t1 else "")] = dict(per_month=round(float(o[:, 0].mean() / 12)), p10=round(float(np.percentile(o[:, 0], 10) / 12)),
                                                           evals=round(float(o[:, 1].mean()), 2), passes=round(float(o[:, 2].mean()), 2), funded_busts=round(float(o[:, 3].mean()), 2),
                                                           accounts_lost=round(float((o[:, 1] - o[:, 2] + o[:, 3]).mean()), 2))
        OUT[f"buffer {int(buf)}"] = rec; print(int(buf), json.dumps(rec), flush=True)
    json.dump(OUT, open(os.path.join(HERE, "liqbuf.json"), "w"), indent=1)
