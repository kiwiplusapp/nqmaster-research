"""Shared helpers for the 2026-10-16 six-year round (Federico: 'backtest de los últimos 6 años, mejorar todo y añadir nuevas').
Window: real Databento NQ 2020-10-15 .. end. T1 = 2020-10-15..2023-12-31 (choose), T2 = 2024-01-01..end (check, never used to choose).
Base portfolio = current Ultra (six_trades.pkl 'Ultra': UltraR + CPI09, MOM1030/CPI09 x4), P&L per row = w * u ($ per MNQ incl. $1.90 + 1 tick).
Acceptance for ANY addition / change (fixed before looking at T2):
  T1: n >= 60 (standalone) and PF >= 1.3;  T2: PF >= 1.2;  +4 ticks (extra $3 per contract round trip) T2 PF >= 1.1;
  portfolio: Ultra Sharpe up in T1 AND T2, max DD (6y) not worse by > 5%, worst month not worse by > 5%;
  plateau: the neighbouring parameter cells must also have T1 PF >= 1.15."""
import os, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
START, MID = 20201015, 20240101
_P = None


def base(name="Ultra"):
    global _P
    if _P is None: _P = pickle.load(open(os.path.join(HERE, "six_trades.pkl"), "rb"))
    return _P[name]


def days():
    T = base(); return np.array(sorted(T.date.unique()))


def daily(T, col_pnl=None, extra=0.0):
    """T needs date + (w,u) or a 'usd' column ($ per row). Returns daily $ Series over the base trading-day index (0 on no-trade days)."""
    pnl = T[col_pnl] if col_pnl else T.w * (T.u - extra)
    if col_pnl and extra: pnl = pnl - extra * (T.w if "w" in T else 1.0)
    d = pnl.groupby(T.date).sum()
    idx = np.union1d(days(), d.index.to_numpy()); idx = idx[idx >= START]
    return d.reindex(idx, fill_value=0.0)


def metr(d):
    d = d[d.index >= START]; out = {}
    for lab, m in (("T1", d.index < MID), ("T2", d.index >= MID), ("all", np.ones(len(d), bool))):
        x = d[m]; eq = x.cumsum(); mo = x.groupby(pd.to_datetime(x.index.astype(str)).to_period("M")).sum()
        out[lab] = dict(sharpe=round(float(x.mean() / x.std() * np.sqrt(252)), 3) if x.std() > 0 else 0.0, net=round(float(x.sum())),
                        maxdd=round(float((eq.cummax() - eq).max())), worst_month=round(float(mo.min())))
    return out


def tstats(usd, dates):
    usd = np.asarray(usd); dates = np.asarray(dates); out = {}
    for lab, m in (("T1", (dates >= START) & (dates < MID)), ("T2", dates >= MID)):
        u = usd[m]; l = -u[u <= 0].sum()
        out[lab] = dict(n=int(len(u)), wr=round(100 * float((u > 0).mean()), 1) if len(u) else None, pf=round(float(u[u > 0].sum() / l), 3) if l > 0 else None,
                        net=round(float(u.sum())))
    return out


def add_test(cand_daily, w=1.0, name="Ultra"):
    """Ultra + w x candidate daily $; returns base metrics, combined metrics and correlation of daily P&L."""
    b = daily(base(name)); c = cand_daily.reindex(b.index.union(cand_daily.index), fill_value=0.0)
    b = b.reindex(c.index, fill_value=0.0); comb = b + w * c
    return dict(base=metr(b), comb=metr(comb), corr=round(float(np.corrcoef(b, c)[0, 1]), 3) if c.std() > 0 else 0.0)
