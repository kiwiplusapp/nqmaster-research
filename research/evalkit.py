"""Metrics, $-sizing and prop-firm evaluation simulation for research trade lists."""
import numpy as np
import pandas as pd
from engine import COMM_PTS, SLIP

POINT_VALUE = 2.0          # MNQ $ per point
COMM_USD = 1.00            # round turn per contract


def to_df(res, data, name):
    E, X, D, EP, XP, RK, RS = res
    pnl = (XP - EP) * D
    return pd.DataFrame(dict(
        strategy=name, date=data["date"][E], entry_idx=E, exit_idx=X, dir=D, entry=EP, exit=XP,
        risk=RK, pnl_pts=pnl, R=(pnl - COMM_PTS) / RK, reason=RS, om=data["om"][E],
        year=data["date"][E] // 10000,
    ))


def size_dollars(df, risk_usd=100.0, max_qty=15, min_qty_fallback=False):
    """Contracts = floor(risk / (stop + 1 tick slippage + commission)); trades that cannot be sized are dropped."""
    per_contract = (df["risk"] + SLIP) * POINT_VALUE + COMM_USD
    qty = np.floor(risk_usd / per_contract).clip(upper=max_qty)
    if min_qty_fallback:
        qty = qty.clip(lower=1)
    out = df.assign(qty=qty, usd=qty * (df["pnl_pts"] * POINT_VALUE - COMM_USD))
    return out[out["qty"] >= 1].copy()


def apply_daily_rules(df, max_losses=3, daily_stop=300.0, daily_target=0.0, max_trades=0, col="usd"):
    """Sequential per-day halts, identical to the NinjaTrader risk layer."""
    keep = np.zeros(len(df), bool)
    vals = df[col].to_numpy(); dates = df["date"].to_numpy()
    cur = None; pnl = 0.0; streak = 0; cnt = 0; halted = False
    for k in range(len(df)):
        if dates[k] != cur:
            cur = dates[k]; pnl = 0.0; streak = 0; cnt = 0; halted = False
        if halted or (max_trades and cnt >= max_trades):
            continue
        keep[k] = True
        cnt += 1
        pnl += vals[k]
        streak = streak + 1 if vals[k] <= 0 else 0
        if (max_losses and streak >= max_losses) or (daily_stop and pnl <= -daily_stop) or (daily_target and pnl >= daily_target):
            halted = True
    return df[keep].copy()


def stats(df, all_dates=None, col="R"):
    if len(df) == 0:
        return dict(n=0)
    r = df[col]
    wins = r[r > 0].sum(); losses = -r[r < 0].sum()
    eq = r.cumsum().to_numpy()
    dd = float(np.max(np.maximum.accumulate(eq) - eq)) if len(eq) else 0.0
    daily = df.groupby("date")[col].sum()
    if all_dates is not None:
        daily = daily.reindex(all_dates, fill_value=0.0)
    sharpe = daily.mean() / daily.std() * np.sqrt(252) if daily.std() > 0 else 0.0
    monthly = df.assign(m=df["date"] // 100).groupby("m")[col].sum()
    return dict(
        n=len(df), wr=round(100 * (r > 0).mean(), 1), avg=round(r.mean(), 3), pf=round(wins / losses, 2) if losses > 0 else np.inf,
        total=round(r.sum(), 1), maxdd=round(dd, 1), sharpe=round(sharpe, 2),
        pos_months=round(100 * (monthly > 0).mean(), 0), per_day=round(len(df) / max(1, df["date"].nunique()), 2),
    )


def by_year(df, col="R"):
    rows = []
    for y, g in df.groupby("year"):
        s = stats(g, col=col)
        s["year"] = y
        rows.append(s)
    return pd.DataFrame(rows).set_index("year")[["n", "wr", "avg", "pf", "total", "maxdd"]]


def prop_eval(df, all_dates, target=3000.0, max_dd=2000.0, dll=0.0, lock_at_start=True, col="usd"):
    """Rolling-start evaluation: for every start day, replay trades until target or trailing drawdown is hit.
    Trailing DD follows the peak of closed-trade equity (intraday), like Apex/Topstep on realized P&L."""
    dates = np.asarray(all_dates)
    tdates = df["date"].to_numpy(); vals = df[col].to_numpy()
    first_idx = np.searchsorted(tdates, dates)
    results = []
    for s_i, sd in enumerate(dates[:-20]):
        k = first_idx[s_i]
        eq = 0.0; peak = 0.0; floor = -max_dd; outcome = None; day_pnl = 0.0; cur = None; best_day = 0.0
        days_used = 0
        while k < len(vals):
            if tdates[k] != cur:
                if cur is not None:
                    best_day = max(best_day, day_pnl)
                cur = tdates[k]; day_pnl = 0.0
                days_used = int(np.searchsorted(dates, cur) - s_i + 1)
            if dll and day_pnl <= -dll:
                k += 1
                continue
            eq += vals[k]; day_pnl += vals[k]
            peak = max(peak, eq)
            floor = max(floor, peak - max_dd)
            if lock_at_start:
                floor = min(floor, 0.0)
            if eq <= floor:
                outcome = "fail"; break
            if eq >= target:
                best_day = max(best_day, day_pnl)
                outcome = "pass"; break
            k += 1
        results.append((sd, outcome or "open", days_used, best_day / target if outcome == "pass" else np.nan))
    r = pd.DataFrame(results, columns=["start", "outcome", "days", "best_day_share"])
    done = r[r.outcome != "open"]
    return dict(
        starts=len(r), pass_rate=round(100 * (done.outcome == "pass").mean(), 1) if len(done) else np.nan,
        median_days_pass=float(done[done.outcome == "pass"].days.median()) if (done.outcome == "pass").any() else np.nan,
        median_days_fail=float(done[done.outcome == "fail"].days.median()) if (done.outcome == "fail").any() else np.nan,
        consistency_ok=round(100 * (done[done.outcome == "pass"].best_day_share < 0.5).mean(), 1) if (done.outcome == "pass").any() else np.nan,
    )
