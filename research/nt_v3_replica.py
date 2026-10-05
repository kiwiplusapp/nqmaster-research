"""Bar-by-bar replica of NQTrendDayPro.cs (v3): ORB + VWAP-pullback in the daily-trend direction, with
two-leg exits (TP1 partial -> stop to breakeven -> TP2), hard max trades/day, daily loss limit that FLATTENS and
halts the day, optional daily profit target, entry window and flatten time.
Fills: stop entries at max(open, trigger)+1 tick, VWAP limits need a 1-tick trade-through, stops pay 1 tick,
targets need a 1-tick trade-through and are never filled on the entry bar. Stop assumed before target inside a bar.
Costs: $1.00 round turn per MNQ contract (0.5 pt) + 1 tick slippage on market/stop fills."""
import numpy as np, pandas as pd
from nt_v2_replica import daily_stats

TICK, SLIP, PV, COMM = 0.25, 0.25, 2.0, 1.0


def run(cx, contracts=2, orb_cap=0.20, orb_max=2, vw_ext=0.10, vw_stop=0.20, t1_r=1.0, t1_frac=0.5, t2_r=2.0,
        be_after_t1=True, be_off_ticks=1, max_consec_losses=2, max_trades_day=10, dll=0.0, dpt=0.0,
        entry_start=630, orb_last=780, vw_last=870, flat=955, use_orb=True, use_vwap=True, range_min=60):
    o, h, l, c, v, om, dayid = cx.o, cx.h, cx.l, cx.c, cx.v, cx.om, cx.dayid
    A, T, ready = daily_stats(cx)
    n = len(c)
    out = []
    frac1 = t1_frac if t1_frac > 0 else 0.0

    def close_pos(pos, px, i, reason):
        # realize every open leg at px
        for lg in pos["legs"]:
            if lg["open"]:
                lg["open"] = False
                pos["pts"] += lg["frac"] * (px - pos["entry"]) * pos["d"]
        pnl_pts = pos["pts"]
        usd = contracts * (pnl_pts * PV - COMM)
        R = (pnl_pts - COMM / PV) / pos["risk_pts"]
        return dict(date=pos["date"], mod=pos["mod"], dir=pos["d"], entry=pos["entry"], R=R, usd=usd,
                    risk_pts=pos["risk_pts"], entry_idx=pos["bar"], exit_idx=i, reason=reason, t1_hit=pos["t1_hit"])

    for dd in range(cx.nd):
        i0 = cx.open_idx[dd]
        if i0 < 0 or not ready[dd] or T[dd] == 0 or np.isnan(A[dd]):
            continue
        d = int(T[dd]); atr = A[dd]
        orh = -1e18; orl = 1e18; pv = vv = 0.0
        streak = 0; halted = False; day_pnl = 0.0; entries = 0
        orb_armed = False; orb_trades = 0; orb_order = None
        vw_armed = False; vw_done = False; vw_order = None
        pos = {"orb": None, "vw": None}
        i = i0
        while i < n and dayid[i] == dayid[i0]:
            m = om[i]
            if m >= 960:
                break
            # ---------- 1) fills & exits on this bar ----------
            for which in ("orb", "vw"):
                order = orb_order if which == "orb" else vw_order
                if pos[which] is None and order is not None and order["bar"] < i and not halted:
                    if which == "orb":
                        trig = h[i] >= order["px"] if d == 1 else l[i] <= order["px"]
                        fill = (max(o[i], order["px"]) + SLIP) if d == 1 else (min(o[i], order["px"]) - SLIP)
                    else:
                        trig = l[i] <= order["px"] - TICK if d == 1 else h[i] >= order["px"] + TICK
                        fill = min(order["px"], o[i]) if d == 1 else max(order["px"], o[i])
                    if trig and entries < max_trades_day:
                        rk = order["st"] * TICK
                        legs = []
                        if frac1 > 0:
                            legs.append(dict(frac=frac1, tgt=fill + d * t1_r * rk, open=True, t1=True))
                        if frac1 < 1:
                            legs.append(dict(frac=1 - frac1, tgt=fill + d * t2_r * rk, open=True, t1=False))
                        pos[which] = dict(entry=fill, stop=fill - d * rk, legs=legs, bar=i, risk_pts=rk, d=d, pts=0.0,
                                          mod=which, date=cx.date[i0], t1_hit=False)
                        entries += 1
                        if which == "orb":
                            orb_order = None; orb_trades += 1
                        else:
                            vw_order = None; vw_done = True
                p = pos[which]
                if p is None:
                    continue
                done = None
                # stop first (conservative)
                if d == 1:
                    if i > p["bar"] and o[i] <= p["stop"]:
                        done = close_pos(p, o[i] - SLIP, i, "stop")
                    elif l[i] <= p["stop"]:
                        done = close_pos(p, p["stop"] - SLIP, i, "stop")
                else:
                    if i > p["bar"] and o[i] >= p["stop"]:
                        done = close_pos(p, o[i] + SLIP, i, "stop")
                    elif h[i] >= p["stop"]:
                        done = close_pos(p, p["stop"] + SLIP, i, "stop")
                if done is None and i > p["bar"]:
                    for lg in p["legs"]:
                        if lg["open"] and ((d == 1 and h[i] >= lg["tgt"] + TICK) or (d == -1 and l[i] <= lg["tgt"] - TICK)):
                            px = lg["tgt"]
                            if (d == 1 and o[i] >= lg["tgt"]) or (d == -1 and o[i] <= lg["tgt"]):
                                px = o[i]
                            lg["open"] = False
                            p["pts"] += lg["frac"] * (px - p["entry"]) * d
                            if lg["t1"]:
                                p["t1_hit"] = True
                                if be_after_t1:
                                    p["stop"] = p["entry"] + d * be_off_ticks * TICK
                    if not any(lg["open"] for lg in p["legs"]):
                        done = close_pos(p, c[i], i, "target")
                if done is None and m + 1 >= flat:
                    done = close_pos(p, c[i] - d * SLIP, i, "time")
                if done is not None:
                    out.append(done)
                    pos[which] = None
                    day_pnl += done["usd"]
                    streak = streak + 1 if done["usd"] <= 0 else 0
                    if max_consec_losses and streak >= max_consec_losses:
                        halted = True
                    if dpt and day_pnl >= dpt:
                        halted = True
            # daily loss limit on realized + open P&L at the bar close -> flatten everything, halt the day
            if dll and not halted:
                unreal = 0.0
                for which in ("orb", "vw"):
                    p = pos[which]
                    if p is not None:
                        open_frac = sum(lg["frac"] for lg in p["legs"] if lg["open"])
                        unreal += contracts * (p["pts"] + open_frac * (c[i] - p["entry"]) * d) * PV
                if day_pnl + unreal <= -dll:
                    for which in ("orb", "vw"):
                        p = pos[which]
                        if p is not None:
                            done = close_pos(p, c[i] - d * SLIP, i, "daily_loss")
                            out.append(done); day_pnl += done["usd"]; pos[which] = None
                    halted = True
            if halted:
                orb_order = None; vw_order = None
            # ---------- 2) bar close logic ----------
            if m < 570 + range_min:
                orh = max(orh, h[i]); orl = min(orl, l[i])
            pv += (h[i] + l[i] + c[i]) / 3.0 * max(v[i], 1e-9); vv += max(v[i], 1e-9); vwap = pv / vv
            close_min = m + 1
            if close_min >= flat:
                break
            if m == 570 + range_min - 1:
                orb_armed = True
            if halted or close_min < entry_start or entries >= max_trades_day:
                i += 1
                continue
            if use_orb and m >= 570 + range_min - 1:
                window = close_min < orb_last
                if orb_order is not None and not window:
                    orb_order = None
                if (not orb_armed and pos["orb"] is None and orb_order is None and 0 < orb_trades < orb_max and orl < c[i] < orh):
                    orb_armed = True
                if orb_armed and pos["orb"] is None and orb_order is None and orb_trades < orb_max and window:
                    entry = orh + TICK if d == 1 else orl - TICK
                    opp = orl - TICK if d == 1 else orh + TICK
                    dist = min(abs(entry - opp), orb_cap * atr)
                    st = max(8, int(round(dist / TICK)))
                    orb_armed = False
                    orb_order = dict(px=entry, st=st, bar=i)
            if use_vwap and m >= 570 + range_min:
                window = close_min < vw_last
                if vw_order is not None:
                    if not window:
                        vw_order = None; vw_done = True
                    else:
                        vw_order["px"] = vwap
                elif not (vw_done or pos["vw"] is not None or vw_armed) and window:
                    ext = (c[i] > orh and c[i] >= vwap + vw_ext * atr) if d == 1 else (c[i] < orl and c[i] <= vwap - vw_ext * atr)
                    if ext:
                        st = max(8, int(round(vw_stop * atr / TICK)))
                        vw_order = dict(px=vwap, st=st, bar=i); vw_armed = True
            i += 1
    return pd.DataFrame(out)


def metrics(df, days):
    if len(df) == 0:
        return {}
    r = df.R; u = df.usd
    daily = df.groupby("date").usd.sum().reindex(days, fill_value=0.0)
    eq = daily.cumsum(); dd = float((eq.cummax() - eq).max())
    wins = u[u > 0].sum(); loss = -u[u <= 0].sum()
    return dict(trades=len(df), trades_per_day=round(len(df) / len(days), 2), winrate=round((u > 0).mean() * 100, 1),
                pf=round(wins / loss, 2) if loss > 0 else np.inf, expectancy_R=round(r.mean(), 3), expectancy_usd=round(u.mean(), 1),
                net_usd=round(u.sum(), 0), max_dd_usd=round(dd, 0), worst_day=round(daily.min(), 0), best_day=round(daily.max(), 0),
                green_days_pct=round((daily[daily != 0] > 0).mean() * 100, 1))
