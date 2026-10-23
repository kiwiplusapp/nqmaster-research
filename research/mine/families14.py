"""Batch 14 (2026-10-23): 'Franklin' NY-open bias rule from a reel Federico sent. At ~09:25-09:30 ET: if New York is ABOVE the London
session and ABOVE the VWAP -> look only for longs; BELOW London and BELOW the VWAP -> only shorts ("two lines, one up, one down").
The reel gives no entry, stop or target, so the grid covers the natural readings; all fills through core.execute (market = next 1m
bar open + 1 tick; stop entries at max(level, open) + 1 tick; stops -1 tick; flat 15:55; 1 trade per day).
  lon   London session window (ET): 0200-0500, 0300-0800, 0200-0830
  cmp   'above London' = close of the 09:29 bar above the London HIGH ('hi'), above its MIDPOINT ('mid') or above the London
        session's last CLOSE ('cls'); mirror below
  vw    'sess' = also on the right side of the 18:00-session VWAP at 09:29; 'none' = London only
  tf    1 = only with the house daily trend (prior RTH close vs SMA20)
  ent   'mkt'  market at the 09:30 open
        'brk15' stop order beyond the first 15-minute candle (09:30-09:44) in the bias direction, placed at 09:45, valid to 11:00
        'brkpre' stop beyond the pre-NY high/low (08:00-09:29), placed at 09:30, valid to 11:00
  st    stop 0.15 / 0.25 / 0.40 x daily ATR, or 'struct' = the opposite side of the reference (London range for mkt, first 15-min
        candle for brk15, pre-NY range for brkpre); risk floored at 0.10 ATR, setups with risk > 1.0 ATR skipped
  R     target R x risk; 0 = hold to 15:55
Grid 3 x 3 x 2 x 2 x 3 x 4 x 3 = 1,296 cells."""
import numpy as np, pandas as pd
from core import S, ev_from_lists
from families import grid

LON = {"0200-0500": (200, 500), "0300-0800": (300, 800), "0200-0830": (200, 830)}
_C = {}


def _day_feats(D):
    key = id(D)
    if key in _C: return _C[key]
    sm = D.sm; day = D.day; n = D.n
    def idx_at(t):
        a = np.full(D.nd, -1, np.int64); w = np.nonzero(sm == S(t))[0]; a[day[w]] = w; return a
    def rng(t0, t1):
        m = (sm >= S(t0)) & (sm < S(t1)); g = pd.DataFrame({"d": day[m], "h": D.h[m], "l": D.l[m], "c": D.c[m]}).groupby("d")
        hi = np.full(D.nd, np.nan); lo = np.full(D.nd, np.nan); cl = np.full(D.nd, np.nan)
        a = g.agg(h=("h", "max"), l=("l", "min"), c=("c", "last")); ix = a.index.to_numpy()
        hi[ix] = a.h.to_numpy(); lo[ix] = a.l.to_numpy(); cl[ix] = a.c.to_numpy(); return hi, lo, cl
    F = dict(i929=idx_at(929), i944=idx_at(944), i1100=idx_at(1100), lon={k: rng(*v) for k, v in LON.items()},
             f15=rng(930, 945), pre=rng(800, 930))
    _C[key] = F; return F


def gen_franklin(D, p):
    F = _day_feats(D); i = F["i929"]; ok = i >= 0
    days = np.nonzero(ok)[0]; i = i[days]
    c = D.c[i]; A = D.atr[days]; hi, lo, lc = [x[days] for x in F["lon"][p["lon"]]]
    ref_up = {"hi": hi, "mid": (hi + lo) / 2, "cls": lc}[p["cmp"]]; ref_dn = {"hi": lo, "mid": (hi + lo) / 2, "cls": lc}[p["cmp"]]
    d = np.where(c > ref_up, 1, np.where(c < ref_dn, -1, 0))
    if p["vw"] == "sess":
        v = D.svwap[i]; d = np.where((d == 1) & (c > v), 1, np.where((d == -1) & (c < v), -1, 0))
    if p["tf"]: d = np.where(d == D.trend[days], d, 0)
    good = (d != 0) & (A > 0) & np.isfinite(hi) & np.isfinite(lo)
    L = []
    for k in np.nonzero(good)[0]:
        dd = int(d[k]); a = A[k]; dy = days[k]
        if p["ent"] == "mkt":
            si = int(i[k]); t = 0; px = c[k]; exp = si + 1; sref = lo[k] if dd == 1 else hi[k]
        elif p["ent"] == "brk15":
            si = int(F["i944"][dy]); fh, fl = F["f15"][0][dy], F["f15"][1][dy]
            if si < 0 or not np.isfinite(fh): continue
            t = 2; px = fh if dd == 1 else fl; exp = int(F["i1100"][dy]); sref = fl if dd == 1 else fh
        else:
            si = int(i[k]); ph, pl = F["pre"][0][dy], F["pre"][1][dy]
            if not np.isfinite(ph): continue
            t = 2; px = ph if dd == 1 else pl; exp = int(F["i1100"][dy]); sref = pl if dd == 1 else ph
        if exp < 0: exp = si + 90
        risk = abs(px - sref) if p["st"] == "struct" else float(p["st"]) * a
        risk = max(risk, 0.10 * a)
        if risk > 1.0 * a: continue
        sl = px - dd * risk; tp = px + dd * (p["R"] * risk if p["R"] > 0 else 30.0 * a)
        L.append((si, dd, t, px, sl, tp, exp, 100000))
    return ev_from_lists(L)


GRID_FRANKLIN = grid(lon=tuple(LON), cmp=("hi", "mid", "cls"), vw=("sess", "none"), tf=(0, 1), ent=("mkt", "brk15", "brkpre"),
                     st=(0.15, 0.25, 0.40, "struct"), R=(1.0, 2.0, 0.0))
FAMILIES14 = {"FRANKLIN": (gen_franklin, GRID_FRANKLIN, 1)}

if __name__ == "__main__":
    print(len(GRID_FRANKLIN))
