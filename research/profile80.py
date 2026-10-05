"""Market Profile '80% rule' (Dalton) on NQ 1-minute data.
Prior-day RTH volume profile (tick volume spread uniformly over each bar's range, 1-point bins) -> POC, VAH, VAL (70%).
Setup: RTH opens outside the prior value area, then price re-enters and is ACCEPTED (N consecutive 30-min periods close
inside VA). Trade toward the opposite side of the value area. Entry at the next bar open after acceptance.
Stop: beyond the VA edge that was re-entered (+buffer) or beyond the session extreme. Target: opposite VA edge (or POC)."""
import numpy as np, pandas as pd
from numba import njit
import engine as en
from common import Ctx

TICK, SLIP = 0.25, 0.25


def value_areas(cx, pct=0.70):
    h, l, v = cx.h, cx.l, cx.v
    nd = cx.nd
    VA = np.full((nd, 3), np.nan)       # POC, VAH, VAL of that day's RTH
    for dd in range(nd):
        i0, i1 = cx.open_idx[dd], cx.close_idx[dd]
        if i0 < 0 or i1 <= i0:
            continue
        lo = np.floor(l[i0:i1 + 1].min()); hi = np.ceil(h[i0:i1 + 1].max())
        nb = int(hi - lo) + 1
        if nb <= 2 or nb > 5000:
            continue
        prof = np.zeros(nb)
        for i in range(i0, i1 + 1):
            a = int(np.floor(l[i] - lo)); b = int(np.ceil(h[i] - lo))
            b = max(b, a + 1)
            prof[a:b] += (v[i] if v[i] > 0 else 1.0) / (b - a)
        poc = int(np.argmax(prof)); tot = prof.sum()
        lo_i = hi_i = poc; acc = prof[poc]
        while acc < pct * tot and (lo_i > 0 or hi_i < nb - 1):
            up = prof[hi_i + 1] if hi_i < nb - 1 else -1
            dn = prof[lo_i - 1] if lo_i > 0 else -1
            if up >= dn:
                hi_i += 1; acc += up
            else:
                lo_i -= 1; acc += dn
        VA[dd] = (lo + poc + 0.5, lo + hi_i + 1, lo + lo_i)
    return VA


@njit(cache=True)
def sim80(o, h, l, c, om, dayid, open_idx, prevVA, accept_periods, period_min, last_entry, flat_om, stop_mode, buf, tgt_mode, max_stop):
    nd = len(open_idx)
    E = np.zeros(nd, np.int64); X = np.zeros(nd, np.int64); D = np.zeros(nd, np.int64)
    EP = np.zeros(nd); XP = np.zeros(nd); RK = np.zeros(nd); RS = np.zeros(nd, np.int64)
    t = 0; n = len(c)
    for dd in range(nd):
        i0 = open_idx[dd]
        if i0 < 0 or np.isnan(prevVA[dd, 0]):
            continue
        poc, vah, val = prevVA[dd, 0], prevVA[dd, 1], prevVA[dd, 2]
        op = o[i0]
        if op > vah:
            d = -1
        elif op < val:
            d = 1
        else:
            continue
        inside_count = 0
        ext = h[i0] if d == -1 else l[i0]
        j = i0
        sig = -1
        while j < n and dayid[j] == dayid[i0] and om[j] < last_entry:
            ext = max(ext, h[j]) if d == -1 else min(ext, l[j])
            if (om[j] + 1 - 570) % period_min == 0:          # close of a 30-min period
                if val < c[j] < vah:
                    inside_count += 1
                else:
                    inside_count = 0
                if inside_count >= accept_periods:
                    sig = j
                    break
            j += 1
        if sig < 0 or sig + 1 >= n or dayid[sig + 1] != dayid[i0]:
            continue
        e = sig + 1
        entry = o[e] + d * SLIP
        if stop_mode == 0:
            stop = vah + buf if d == -1 else val - buf
        else:
            stop = ext + buf if d == -1 else ext - buf
        tgt = (val if d == -1 else vah) if tgt_mode == 0 else poc
        rk = (entry - stop) * d
        if rk <= TICK or rk > max_stop or (tgt - entry) * d <= TICK:
            continue
        xi, xp, rs = en.walk_exit(o, h, l, c, om, dayid, e, d, entry, stop, tgt, flat_om, True)
        E[t] = e; X[t] = xi; D[t] = d; EP[t] = entry; XP[t] = xp; RK[t] = rk; RS[t] = rs; t += 1
    return E[:t], X[:t], D[:t], EP[:t], XP[:t], RK[:t], RS[:t]


if __name__ == "__main__":
    import itertools
    import evalkit as ev
    pd.set_option("display.width", 250)
    cx = Ctx()
    VA = value_areas(cx)
    prevVA = np.full_like(VA, np.nan)
    last = np.full(3, np.nan)
    for dd in range(cx.nd):
        prevVA[dd] = last
        if not np.isnan(VA[dd, 0]):
            last = VA[dd]
    np.save("data/prevVA.npy", prevVA)
    rows = []
    for acc, per, (sm, buf), tm, le in itertools.product((1, 2), (30, 15), [(0, 5.0), (0, 15.0), (1, 2.0)], (0, 1), (720, 840)):
        r = sim80(cx.o, cx.h, cx.l, cx.c, cx.om, cx.dayid, cx.open_idx, prevVA, acc, per, le, 955, sm, buf, tm, 400.0)
        df = ev.to_df(r, cx.d, "80")
        if len(df) < 30:
            continue
        a = df[df.date < 20240101]; b = df[(df.date >= 20240101) & (df.date < 20260101)]; y = df[df.date >= 20260101]
        f = lambda x: (len(x), round((x.R > 0).mean() * 100, 1) if len(x) else np.nan,
                       round(x.R[x.R > 0].sum() / -x.R[x.R <= 0].sum(), 2) if len(x) and (x.R <= 0).any() else np.nan)
        rows.append(dict(accept=acc, period=per, stop=["VAedge", "extreme"][sm], buf=buf, target=["oppVA", "POC"][tm], last=le,
                         n_2020_23=f(a)[0], wr_2020_23=f(a)[1], pf_2020_23=f(a)[2], n_2024_25=f(b)[0], wr_2024_25=f(b)[1], pf_2024_25=f(b)[2],
                         n_2026=f(y)[0], wr_2026=f(y)[1], pf_2026=f(y)[2], avg_stop=round(df.risk.mean(), 1)))
    out = pd.DataFrame(rows)
    out.to_csv("profile80_scan.csv", index=False)
    print(out.sort_values("pf_2020_23", ascending=False).to_string(index=False))
