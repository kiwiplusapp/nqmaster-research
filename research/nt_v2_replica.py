"""Bar-by-bar Python replica of NYOpeningRangeTrend.cs v2 (ORB + VWAP pullback), NT-style daily stats,
real-time 2-loss day stop, $-sizing. Fills: stop entries at max(open, trigger)+1 tick, limits need a
1-tick trade-through, stops pay 1 tick, targets are never filled on the entry bar."""
import numpy as np, pandas as pd
from common import Ctx, SPLIT

TICK, SLIP, PV, COMM = 0.25, 0.25, 2.0, 1.0


def daily_stats(cx):
    o, h, l, c, om, dayid = cx.o, cx.h, cx.l, cx.c, cx.om, cx.dayid
    nd = cx.nd
    atr = np.nan; cnt = 0; pc = np.nan; closes = []; prev = np.nan
    A = np.full(nd, np.nan); T = np.zeros(nd, np.int64); ready = np.zeros(nd, bool)
    cur = -1; has = False; dh = dl = dc = np.nan
    for i in np.where((om >= 570) & (om < 960))[0]:
        d = dayid[i]
        if d != cur:
            if has:
                tr = dh - dl if np.isnan(pc) else max(dh - dl, abs(dh - pc), abs(dl - pc))
                cnt += 1; k = min(cnt, 14); atr = tr if np.isnan(atr) else ((k - 1) * atr + tr) / k
                pc = dc; prev = dc; closes.append(dc); closes = closes[-20:]
            cur = d; has = False
            A[d] = atr; ready[d] = cnt >= 14
            if len(closes) >= 15 and not np.isnan(prev):
                s = np.mean(closes); T[d] = 1 if prev > s else (-1 if prev < s else 0)
        if not has:
            dh, dl, has = h[i], l[i], True
        else:
            dh = max(dh, h[i]); dl = min(dl, l[i])
        dc = c[i]
    return A, T, ready


def run(cx, risk_usd=100.0, one_lot_cap=200.0, orb_cap=0.20, orb_rr=2.0, orb_max=2, vw_ext=0.10, vw_stop=0.20, vw_rr=2.0,
        use_orb=True, use_vwap=True, max_consec_losses=2, orb_last=780, vw_last=870, flat=955, max_qty=20, dll=0.0):
    o, h, l, c, v, om, dayid = cx.o, cx.h, cx.l, cx.c, cx.v, cx.om, cx.dayid
    A, T, ready = daily_stats(cx)
    trades = []

    def qty_for(stop_ticks):
        per = (stop_ticks + 1) * TICK * PV + COMM
        q = int(np.floor(risk_usd / per))
        if q < 1 and per <= one_lot_cap:
            q = 1
        return min(q, max_qty), per

    for dd in range(cx.nd):
        i0 = cx.open_idx[dd]
        if i0 < 0 or not ready[dd] or T[dd] == 0 or np.isnan(A[dd]):
            continue
        d = T[dd]; atr = A[dd]
        orh = -1e18; orl = 1e18; pv = vv = 0.0
        loss_streak = 0; halted = False; day_pnl = 0.0
        orb_armed = False; orb_trades = 0; orb_order = None; orb_pos = None
        vw_armed = False; vw_done = False; vw_order = None; vw_pos = None
        i = i0
        n = len(c)
        while i < n and dayid[i] == dayid[i0]:
            m = om[i]
            if m >= 960:
                break
            # ---- 1) orders / positions interact with this bar (they were placed at an earlier close) ----
            for which in ("orb", "vw"):
                pos = orb_pos if which == "orb" else vw_pos
                order = orb_order if which == "orb" else vw_order
                if pos is None and order is not None and order["bar"] < i:
                    if which == "orb":
                        trig = h[i] >= order["px"] if d == 1 else l[i] <= order["px"]
                        fill = (max(o[i], order["px"]) + SLIP) if d == 1 else (min(o[i], order["px"]) - SLIP)
                    else:
                        trig = l[i] <= order["px"] - TICK if d == 1 else h[i] >= order["px"] + TICK
                        fill = min(order["px"], o[i]) if d == 1 else max(order["px"], o[i])
                    if trig:
                        pos = dict(entry=fill, stop=fill - d * order["st"] * TICK, tgt=fill + d * order["tt"] * TICK,
                                   qty=order["q"], risk=order["risk"], bar=i, mod=which)
                        if which == "orb":
                            orb_pos, orb_order = pos, None; orb_trades += 1
                        else:
                            vw_pos, vw_order, vw_done = pos, None, True
                if pos is not None:
                    xp = None
                    if d == 1:
                        if i > pos["bar"] and o[i] <= pos["stop"]: xp = o[i] - SLIP
                        elif l[i] <= pos["stop"]: xp = pos["stop"] - SLIP
                        elif i > pos["bar"] and h[i] >= pos["tgt"] + TICK: xp = max(pos["tgt"], o[i]) if o[i] >= pos["tgt"] else pos["tgt"]
                    else:
                        if i > pos["bar"] and o[i] >= pos["stop"]: xp = o[i] + SLIP
                        elif h[i] >= pos["stop"]: xp = pos["stop"] + SLIP
                        elif i > pos["bar"] and l[i] <= pos["tgt"] - TICK: xp = min(pos["tgt"], o[i]) if o[i] <= pos["tgt"] else pos["tgt"]
                    if xp is None and m + 1 >= flat:
                        xp = c[i] - d * SLIP
                    if xp is not None:
                        pnl = pos["qty"] * ((xp - pos["entry"]) * d * PV - COMM)
                        trades.append(dict(date=cx.date[i0], mod=pos["mod"], dir=d, entry=pos["entry"], exit=xp, qty=pos["qty"],
                                           usd=pnl, risk_usd=pos["risk"], R=pnl / pos["risk"], entry_idx=pos["bar"], exit_idx=i))
                        loss_streak = loss_streak + 1 if pnl <= 0 else 0
                        day_pnl += pnl
                        if (max_consec_losses and loss_streak >= max_consec_losses) or (dll and day_pnl <= -dll):
                            halted = True; orb_order = None; vw_order = None
                        if which == "orb": orb_pos = None
                        else: vw_pos = None
            # ---- 2) bar close: update range / VWAP, then strategy logic (C# ManageOrb / ManageVwap) ----
            if m < 570 + 60:
                orh = max(orh, h[i]); orl = min(orl, l[i])
            pv += (h[i] + l[i] + c[i]) / 3.0 * max(v[i], 1e-9); vv += max(v[i], 1e-9); vwap = pv / vv
            close_min = m + 1
            if close_min >= flat:
                break
            if m == 570 + 60 - 1:
                orb_armed = True
            if m >= 570 + 60 - 1 and not halted:
                # ORB module
                if use_orb:
                    window = close_min < orb_last
                    if orb_order is not None and not window:
                        orb_order = None
                    if (not orb_armed and orb_pos is None and orb_order is None and 0 < orb_trades < orb_max
                            and orl < c[i] < orh):
                        orb_armed = True
                    if orb_armed and orb_pos is None and orb_order is None and orb_trades < orb_max and window:
                        entry = orh + TICK if d == 1 else orl - TICK
                        opp = orl - TICK if d == 1 else orh + TICK
                        dist = min(abs(entry - opp), orb_cap * atr)
                        st = max(2, int(round(dist / TICK))); tt = max(1, int(round(st * orb_rr)))
                        q, per = qty_for(st)
                        orb_armed = False
                        if q >= 1:
                            orb_order = dict(px=entry, st=st, tt=tt, q=q, risk=q * per, bar=i)
                # VWAP module
                if use_vwap and m >= 570 + 60:
                    window = close_min < vw_last
                    if vw_order is not None:
                        if not window:
                            vw_order = None; vw_done = True
                        else:
                            vw_order["px"] = vwap
                    elif not (vw_done or vw_pos is not None or vw_armed) and window:
                        ext = (c[i] > orh and c[i] >= vwap + vw_ext * atr) if d == 1 else (c[i] < orl and c[i] <= vwap - vw_ext * atr)
                        if ext:
                            st = max(2, int(round(vw_stop * atr / TICK))); tt = max(1, int(round(st * vw_rr)))
                            q, per = qty_for(st)
                            if q >= 1:
                                vw_order = dict(px=vwap, st=st, tt=tt, q=q, risk=q * per, bar=i); vw_armed = True
                            else:
                                vw_done = True
            i += 1
    return pd.DataFrame(trades)


if __name__ == "__main__":
    import evalkit as ev
    cx = Ctx()
    df = run(cx)
    df["year"] = df.date // 10000
    print("trades", len(df), "per week", round(len(df) / len(cx.rth_days) * 5, 2))
    for mod, g in df.groupby("mod"):
        print(mod, "n", len(g), "WR", round((g.usd > 0).mean() * 100, 1), "PF", round(g.usd[g.usd > 0].sum() / -g.usd[g.usd <= 0].sum(), 2))
    s = ev.stats(df.assign(R=df.R), cx.rth_days)
    print("ALL:", s)
    print("IS :", ev.stats(df[df.date < SPLIT])); print("OOS:", ev.stats(df[df.date >= SPLIT]))
    print(df.groupby("year").agg(n=("R", "size"), wr=("R", lambda x: round((x > 0).mean() * 100, 1)), R=("R", "sum"), usd=("usd", "sum")).round(1).to_string())
    df.to_pickle("nt_v2_trades.pkl")
