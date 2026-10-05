"""2026-only research harness: in-sample Jan-May 2026, out-of-sample Jun-Sep 2026, 25K prop-eval simulator."""
import numpy as np
import pandas as pd
import engine as en
import evalkit as ev
from common import Ctx

Y0 = 20260101
SPLIT = 20260601            # IS: Jan-May 2026 | OOS: Jun-Sep 2026
TICK, PV, COMM = 0.25, 2.0, 1.0

cx = Ctx()                  # full history is loaded only so indicators are warm on Jan 2 2026
DAYS = cx.rth_days[cx.rth_days >= Y0]
DAYS_IS = DAYS[DAYS < SPLIT]
DAYS_OOS = DAYS[DAYS >= SPLIT]


def t26(res, name="x"):
    df = ev.to_df(res, cx.d, name)
    return df[df.date >= Y0].reset_index(drop=True)


def size(df, risk_usd, one_lot_cap=None, max_qty=20):
    """MNQ contracts = floor(risk / (stop + 1 tick + $1 commission)); 1 lot allowed up to one_lot_cap."""
    per = (df.risk + TICK) * PV + COMM
    q = np.floor(risk_usd / per)
    if one_lot_cap is not None:
        q = np.where((q < 1) & (per <= one_lot_cap), 1, q)
    q = np.minimum(q, max_qty)
    out = df.assign(qty=q, usd=q * (df.pnl_pts * PV - COMM), risk_usd=q * per)
    return out[out.qty >= 1].reset_index(drop=True)


def stats(df, col="R"):
    if len(df) == 0:
        return dict(n=0, wr=np.nan, pf=np.nan, avg=np.nan, tot=0.0)
    r = df[col]
    loss = -r[r <= 0].sum()
    return dict(n=len(df), wr=round((r > 0).mean() * 100, 1), pf=round(r[r > 0].sum() / loss, 2) if loss > 0 else np.inf,
                avg=round(r.mean(), 3), tot=round(r.sum(), 1))


def eval_prop(tr, days, target=1500.0, max_dd=1200.0, horizon=20, dll=0.0):
    """Rolling-start evaluation over `days`: replay trades (chronological, realized equity) for `horizon` trading
    days; trailing drawdown from the realized peak, locked at the starting balance. Optional daily loss limit that
    ends the DAY (not the account). Returns pass%, fail%, timeout%, median days to pass."""
    tr = tr.sort_values(["date", "exit_idx"])
    td = tr.date.to_numpy(); v = tr.usd.to_numpy()
    days = np.asarray(days)
    first = np.searchsorted(td, days)
    res = []; dpass = []
    for s in range(len(days) - horizon + 1):
        end = days[s + horizon - 1]
        k = first[s]; eq = 0.0; pk = 0.0; out = "timeout"; cur = None; dpnl = 0.0; blocked = False
        while k < len(v) and td[k] <= end:
            if td[k] != cur:
                cur = td[k]; dpnl = 0.0; blocked = False
            if blocked:
                k += 1; continue
            eq += v[k]; dpnl += v[k]
            pk = max(pk, eq)
            floor = min(pk - max_dd, 0.0)
            if eq <= floor:
                out = "fail"; break
            if eq >= target:
                out = "pass"; dpass.append(int(np.searchsorted(days, cur) - s + 1)); break
            if dll and dpnl <= -dll:
                blocked = True
            k += 1
        res.append(out)
    r = pd.Series(res)
    return dict(starts=len(r), pass_=round((r == "pass").mean() * 100, 1), fail=round((r == "fail").mean() * 100, 1),
                timeout=round((r == "timeout").mean() * 100, 1), days=float(np.median(dpass)) if dpass else np.nan)


def weekly(tr, days):
    d = tr.groupby("date").usd.sum().reindex(days, fill_value=0.0)
    wk = pd.to_datetime(pd.Series(days).astype(str)).dt.to_period("W").values
    w = d.groupby(wk).sum()
    return dict(avg_week=round(w.mean(), 0), pct_weeks_ge400=round((w >= 400).mean() * 100, 0), worst_week=round(w.min(), 0),
                maxdd=round(float((d.cumsum().cummax() - d.cumsum()).max()), 0))
