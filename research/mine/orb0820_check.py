"""Stress test of the best near-miss of the 16-year mining (G_ORB A=820 T=10 W=60 cap 0.25 R 0.5 tf 0: range 08:20-08:30 ET,
first break of it by a stop order within 08:30-09:30, stop min(range, 0.25 ATR), target 0.5R).  Real NQ futures 2010-26, $ per MNQ.
Its sim skips days whose first breakout bar crosses BOTH sides (typical 08:30 news spike) - with two resting stop orders one of
them fills and the other side is usually hit in the same minute: here those days are counted as full-risk losses.
Fills inside the 08:30 news minute also get extra slippage (stop orders become market orders in a fast market).
-> orb0820_check.json"""
import os, sys, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from core import Data, run_events, S
from families_gold import gen_orb

P = dict(A=820, T=10, W=60, cap=0.25, R=0.5, tf=0, hold=240)


def pf(u):
    u = np.asarray(u); l = -u[u <= 0].sum(); return round(float(u[u > 0].sum() / l), 3) if l > 0 else None


if __name__ == "__main__":
    D = Data("nqdb.npz")
    tr = run_events(D, gen_orb(D, P), flat=955, maxday=1, slip=0.25)
    tr["tin"] = D.sm[tr.fi.to_numpy()]
    news_bar = tr.tin.isin([S(830), S(831)]).to_numpy()
    # whipsaw days skipped by the sim
    A0, T0, W0 = S(820), 10, 60; rows = []
    for d in range(D.nd):
        if D.ds[d] < 0 or D.atr[d] <= 0: continue
        sm = D.sm[D.ds[d]:D.de[d] + 1]; base = D.ds[d]
        a = np.searchsorted(sm, A0); e = np.searchsorted(sm, A0 + T0)
        if a >= len(sm) or e >= len(sm) or sm[a] > A0 + 5: continue
        rh = D.h[base + a:base + e].max(); rl = D.l[base + a:base + e].min()
        for q in range(e, len(sm)):
            if sm[q] >= A0 + T0 + W0: break
            up = D.h[base + q] >= rh + 0.25; dn = D.l[base + q] <= rl - 0.25
            if up and dn:
                risk = min(rh - rl + 0.5, 0.25 * D.atr[d])
                rows.append(dict(date=D.daydate[d], usd=-(risk + 0.25) * 2.0 - 1.9, sm=sm[q]))
            if up or dn: break
    W = pd.DataFrame(rows)
    OUT = {"params": P}
    for lab, lo, hi in (("2010-14", 20100601, 20150101), ("2015-19", 20150101, 20200101), ("2020-23", 20200101, 20240101), ("2024-26", 20240101, 20991231)):
        m = ((tr.date >= lo) & (tr.date < hi)).to_numpy(); u = tr.usd.to_numpy()[m]; nb = news_bar[m]
        w = W[(W.date >= lo) & (W.date < hi)].usd.to_numpy() if len(W) else np.zeros(0)
        r = dict(trades=int(m.sum()), wr=round(100 * float((u > 0).mean()), 1), pf=pf(u), per_trade=round(float(u.mean()), 2),
                 fills_in_0830_minute_pct=round(100 * float(nb.mean()), 1), whipsaw_days_skipped=int(len(w)))
        uw = np.r_[u, w]
        r["with_whipsaw_losses"] = dict(wr=round(100 * float((uw > 0).mean()), 1), pf=pf(uw), per_trade=round(float(uw.mean()), 2))
        for xt in (2, 4, 8):                                   # extra ticks per side on the 08:30-minute fills (entry + exit)
            ux = np.where(nb, u - xt * 0.25 * 2.0 * 2, u); uxw = np.r_[ux, w - xt * 0.25 * 2.0 * 2]
            r[f"whipsaw_plus_{xt}ticks_news_fills"] = dict(wr=round(100 * float((uxw > 0).mean()), 1), pf=pf(uxw))
        r["no_0830_minute_fills"] = dict(trades=int((~nb).sum()), wr=round(100 * float((u[~nb] > 0).mean()), 1), pf=pf(u[~nb]))
        OUT[lab] = r; print(lab, json.dumps(r), flush=True)
    json.dump(OUT, open(os.path.join(HERE, "orb0820_check.json"), "w"), indent=1, default=float)
