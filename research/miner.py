"""Robert Miner - Dual Time Frame Momentum strategy (High Probability Trading Strategies), tested on NQ.

DT oscillator = Stochastic RSI:  RSI(r) -> stochastic over s -> %K = SMA(k), %D = SMA(d). OB 75 / OS 25.
Direction: trade only with the HIGHER time-frame momentum (%K > %D bullish, %K < %D bearish) unless it is
overbought (no new longs) / oversold (no new shorts).
Setup: LOWER time-frame DT bullish crossover (K crosses above D) coming from the oversold zone (bearish mirror).
Entry: Tr-1BH/L - buy stop 1 tick above the signal bar high, trailed down to each new completed bar high for up
to `trail_bars` bars; cancelled if the lower-TF momentum turns back.
Initial stop: 1 tick beyond the swing low of the last `swing_lb` lower-TF bars.
Exits (simulated on 1-minute bars): 'r1' fixed 1R, 'r2' fixed 2R, 'units' 50% at 1R then stop to breakeven and
trail the rest 1 tick beyond the prior completed lower-TF bar low (Miner's two-unit management), 'trail' trailing only.
"""
import itertools, numpy as np, pandas as pd
from numba import njit
from common import Ctx

TICK = 0.25; SLIP = 0.25; COMM_PTS = 0.5
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 400)


def resample(cx, tf):
    o, h, l, c, om, dayid, date, ep = cx.o, cx.h, cx.l, cx.c, cx.om, cx.dayid, cx.date, cx.d["epoch"]
    key = dayid.astype(np.int64) * 10000 + (om // tf)
    brk = np.r_[0, np.where(np.diff(key) != 0)[0] + 1]
    end = np.r_[brk[1:], len(c)]
    return dict(o=o[brk], c=c[end - 1], h=np.maximum.reduceat(h, brk), l=np.minimum.reduceat(l, brk),
                om=(om[brk] // tf) * tf, dayid=dayid[brk], date=date[brk], i0=brk, i1=end, end_ep=ep[end - 1] + 1)


def dt_osc(c, r, s, k, d):
    dlt = np.diff(c, prepend=c[0]); up = np.clip(dlt, 0, None); dn = np.clip(-dlt, 0, None)
    au = pd.Series(up).ewm(alpha=1 / r, adjust=False).mean(); ad = pd.Series(dn).ewm(alpha=1 / r, adjust=False).mean()
    rsi = (100 - 100 / (1 + au / ad.replace(0, np.nan))).fillna(50)
    lo = rsi.rolling(s).min(); hi = rsi.rolling(s).max()
    st = ((rsi - lo) / (hi - lo).replace(0, np.nan) * 100).fillna(50)
    K = st.rolling(k).mean(); D = K.rolling(d).mean()
    return K.to_numpy(), D.to_numpy()


@njit(cache=True)
def run_trades(o1, h1, l1, c1, om1, day1, sig_bar, sig_dir, lh, ll, li1, lK, lD, swing_lb, trail_bars, exit_mode, flat_om):
    """sig_bar: lower-TF bar index of each signal. li1[b] = first 1-minute index AFTER lower-TF bar b."""
    m = len(sig_bar)
    R = np.full(m, np.nan); XI = np.zeros(m, np.int64); EI = np.zeros(m, np.int64); RKs = np.full(m, np.nan)
    n1 = len(c1); nl = len(lh)
    busy = -1
    for q in range(m):
        b = sig_bar[q]; d = sig_dir[q]
        if li1[b] <= busy:
            continue
        # swing stop
        s0 = max(0, b - swing_lb + 1)
        stop = -1e18 if d == -1 else 1e18
        for k in range(s0, b + 1):
            if d == 1:
                stop = min(stop, ll[k])
            else:
                stop = max(stop, lh[k])
        stop = stop - TICK if d == 1 else stop + TICK
        # trailing one-bar entry
        trig = lh[b] + TICK if d == 1 else ll[b] - TICK
        filled = False; entry = 0.0; e = -1
        bb = b
        while bb < nl - 1 and bb <= b + trail_bars and not filled:
            j0 = li1[bb]; j1 = li1[bb + 1] if bb + 1 < nl else n1
            if day1[j0] != day1[li1[b]] or om1[j0] >= flat_om:
                break
            for j in range(j0, j1):
                if d == 1 and h1[j] >= trig:
                    entry = max(o1[j], trig) + SLIP; e = j; filled = True; break
                if d == -1 and l1[j] <= trig:
                    entry = min(o1[j], trig) - SLIP; e = j; filled = True; break
            if filled:
                break
            nb = bb + 1
            if nb >= nl:
                break
            # cancel if lower-TF momentum turns back against the trade
            if (d == 1 and lK[nb] < lD[nb]) or (d == -1 and lK[nb] > lD[nb]):
                break
            nt = lh[nb] + TICK if d == 1 else ll[nb] - TICK
            trig = min(trig, nt) if d == 1 else max(trig, nt)
            bb = nb
        if not filled:
            continue
        rk = (entry - stop) * d
        if rk <= 2 * TICK:
            continue
        # ---- manage on 1-minute bars ----
        t1 = entry + d * rk; t2 = entry + d * 2 * rk
        half_done = False; half_pnl = 0.0
        cur_stop = stop
        j = e; xp = np.nan; xi = e
        # lower-TF bar that contains e
        lb = b
        while lb + 1 < nl and li1[lb + 1] <= e:
            lb += 1
        while j < n1:
            if j > e and (day1[j] != day1[e] or om1[j] >= flat_om):
                xp = o1[j] - d * SLIP; xi = j; break
            # trail update at each completed lower-TF bar (units / trail modes)
            if (exit_mode == 2 and half_done) or exit_mode == 3:
                while lb + 1 < nl and li1[lb + 1] <= j:
                    lb += 1
                    if d == 1:
                        cur_stop = max(cur_stop, ll[lb] - TICK)
                    else:
                        cur_stop = min(cur_stop, lh[lb] + TICK)
            if d == 1:
                if j > e and o1[j] <= cur_stop:
                    xp = o1[j] - SLIP; xi = j; break
                if l1[j] <= cur_stop:
                    xp = cur_stop - SLIP; xi = j; break
            else:
                if j > e and o1[j] >= cur_stop:
                    xp = o1[j] + SLIP; xi = j; break
                if h1[j] >= cur_stop:
                    xp = cur_stop + SLIP; xi = j; break
            if j > e:
                if exit_mode == 0 and ((d == 1 and h1[j] >= t1 + TICK) or (d == -1 and l1[j] <= t1 - TICK)):
                    xp = t1; xi = j; break
                if exit_mode == 1 and ((d == 1 and h1[j] >= t2 + TICK) or (d == -1 and l1[j] <= t2 - TICK)):
                    xp = t2; xi = j; break
                if exit_mode == 2 and not half_done and ((d == 1 and h1[j] >= t1 + TICK) or (d == -1 and l1[j] <= t1 - TICK)):
                    half_done = True; half_pnl = rk
                    cur_stop = entry if d == 1 else entry
                    while lb + 1 < nl and li1[lb + 1] <= j:
                        lb += 1
            j += 1
        if np.isnan(xp):
            xp = c1[n1 - 1]; xi = n1 - 1
        runner = (xp - entry) * d
        if exit_mode == 2:
            pnl = (half_pnl + runner) / 2.0 if half_done else runner
        else:
            pnl = runner
        R[q] = (pnl - COMM_PTS) / rk
        XI[q] = xi; EI[q] = e; RKs[q] = rk
        busy = xi
    return R, XI, EI, RKs


def study():
    cx = Ctx()
    o1, h1, l1, c1, om1, day1 = cx.o, cx.h, cx.l, cx.c, cx.om, cx.dayid
    rows = []
    for (ltf, htf) in [(5, 60), (5, 15), (15, 60)]:
        Lb = resample(cx, ltf); Hb = resample(cx, htf)
        for (r, s, k, d) in [(8, 5, 3, 3), (13, 8, 5, 5)]:
            lK, lD = dt_osc(Lb["c"], r, s, k, d)
            hK, hD = dt_osc(Hb["c"], r, s, k, d)
            # higher-TF value known at each lower-TF bar close (last COMPLETED higher-TF bar)
            pos = np.searchsorted(Hb["end_ep"], Lb["end_ep"], side="right") - 1
            HK = np.where(pos >= 0, hK[np.maximum(pos, 0)], np.nan); HD = np.where(pos >= 0, hD[np.maximum(pos, 0)], np.nan)
            pK, pD = np.r_[np.nan, lK[:-1]], np.r_[np.nan, lD[:-1]]
            bull_x = (pK <= pD) & (lK > lD); bear_x = (pK >= pD) & (lK < lD)
            for os_req, (ws, we, fl, wn) in itertools.product((True, False), [(570, 690, 720, "2h 9:30-11:30"), (570, 900, 955, "RTH")]):
                close_m = Lb["om"] + ltf
                inwin = (close_m > ws) & (close_m <= we)
                longs = bull_x & (HK > HD) & (HK < 75) & inwin
                shorts = bear_x & (HK < HD) & (HK > 25) & inwin
                if os_req:
                    longs &= (np.minimum(pK, pD) < 25)
                    shorts &= (np.maximum(pK, pD) > 75)
                sb = np.r_[np.where(longs)[0], np.where(shorts)[0]]
                sd = np.r_[np.ones(longs.sum(), np.int64), -np.ones(shorts.sum(), np.int64)]
                order = np.argsort(sb, kind="stable"); sb, sd = sb[order], sd[order]
                for em, en_ in enumerate(["1R", "2R", "2 units (Miner)", "trail only"]):
                    for slb in (3, 6):
                        R, XI, EI, _ = run_trades(o1, h1, l1, c1, om1, day1, sb.astype(np.int64), sd, Lb["h"], Lb["l"], Lb["i1"], lK, lD, slb, 3, em, fl)
                        ok = ~np.isnan(R)
                        Rv = R[ok]; dt = Lb["date"][sb[ok]]
                        def st(msk):
                            x = Rv[msk]
                            if len(x) == 0:
                                return (0, np.nan, np.nan)
                            ls = -x[x <= 0].sum()
                            return (len(x), round((x > 0).mean() * 100, 1), round(x[x > 0].sum() / ls, 2) if ls > 0 else np.nan)
                        a = st(dt < 20240101); b_ = st((dt >= 20240101) & (dt < 20260101)); y = st(dt >= 20260101)
                        rows.append(dict(tf=f"{ltf}m/{htf}m", dt=f"{r},{s},{k},{d}", os_zone=os_req, session=wn, exit=en_, swing_lb=slb,
                                         n_20_23=a[0], wr_20_23=a[1], pf_20_23=a[2], n_24_25=b_[0], wr_24_25=b_[1], pf_24_25=b_[2],
                                         n_2026=y[0], wr_2026=y[1], pf_2026=y[2]))
    out = pd.DataFrame(rows)
    out.to_csv("miner_scan.csv", index=False)
    return out


if __name__ == "__main__":
    out = study()
    print("configs", len(out))
    print("PF>1 in all 3 periods:", int(((out.pf_20_23 > 1) & (out.pf_24_25 > 1) & (out.pf_2026 > 1)).sum()),
          "| WR>=60 in all 3:", int(((out.wr_20_23 >= 60) & (out.wr_24_25 >= 60) & (out.wr_2026 >= 60)).sum()))
    for col in ["tf", "dt", "os_zone", "session", "exit", "swing_lb"]:
        print("median by", col, out.groupby(col)[["wr_20_23", "pf_20_23", "pf_24_25", "pf_2026"]].median().round(2).to_dict("index"))
    print(out.sort_values("pf_20_23", ascending=False).head(25).to_string(index=False))
