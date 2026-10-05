"""Per-session liquidity levels known before the NY open: PDH, PDL, ONH, ONL, London H/L, Asia H/L."""
import numpy as np


def build_levels(cx):
    o, h, l, c, om, dayid = cx.o, cx.h, cx.l, cx.c, cx.om, cx.dayid
    nd = cx.nd
    L = np.full((nd, 8), np.nan)
    # previous RTH high/low
    rth_h = np.full(nd, np.nan); rth_l = np.full(nd, np.nan)
    for dd in range(nd):
        i0, i1 = cx.open_idx[dd], cx.close_idx[dd]
        if i0 >= 0 and i1 > i0:
            rth_h[dd] = h[i0:i1 + 1].max(); rth_l[dd] = l[i0:i1 + 1].min()
    last_h = np.nan; last_l = np.nan
    for dd in range(nd):
        L[dd, 0] = last_h; L[dd, 1] = last_l
        if not np.isnan(rth_h[dd]):
            last_h, last_l = rth_h[dd], rth_l[dd]
    # overnight / London / Asia within the session (bars before the 09:30 open)
    first = np.r_[0, np.where(np.diff(dayid) != 0)[0] + 1]
    for dd in range(nd):
        i0 = cx.open_idx[dd]
        if i0 < 0:
            continue
        s = first[np.searchsorted(first, i0, side="right") - 1]
        if s >= i0:
            continue
        seg = slice(s, i0)
        hh, ll, mm = h[seg], l[seg], om[seg]
        L[dd, 2] = hh.max(); L[dd, 3] = ll.min()
        lon = (mm >= 120) & (mm < 300)
        if lon.any():
            L[dd, 4] = hh[lon].max(); L[dd, 5] = ll[lon].min()
        asia = (mm >= 1080) | (mm < 60)
        if asia.any():
            L[dd, 6] = hh[asia].max(); L[dd, 7] = ll[asia].min()
    return L
