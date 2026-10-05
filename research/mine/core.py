"""Strategy miner core: data + features + one generic bar-by-bar executor.
Execution model (same as all earlier research): market entries at the next 1m bar open +1 tick, stop entries at
max(open, level) +1 tick, limit entries need a 1-tick trade-through (fill at min(open, limit)), stops -1 tick (gap: open),
targets need a 1-tick trade-through and are never filled on the entry bar, stop checked first inside a bar,
time exit / flat at bar close -1 tick. MNQ $2/pt, $1.90 round-trip commission. One position at a time per strategy.
Session minute sm = (ET minute - 18:00) mod 1440, monotonic inside a Globex session (dayid)."""
import os, sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ict import day_levels
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(name):
    z = np.load(os.path.join(RES, "data", name)); return {k: z[k] for k in z.files}
TICK, SLIP = 0.25, 0.25
def S(hhmm):                      # ET HHMM -> session minute
    return ((hhmm // 100) * 60 + hhmm % 100 - 1080) % 1440


class Data:
    def __init__(self, name):
        D = load(name); self.name = name
        self.pv = 4.0 if name.startswith(("xau", "mgc", "wti", "mcl")) else 2.0; self.comm = 1.9      # $ per research point (gold x2.5: tick 0.25 = $1 MGC)
        self.o, self.h, self.l, self.c = [np.ascontiguousarray(D[k], dtype=np.float64) for k in "ohlc"]
        self.v = np.maximum(np.asarray(D["v"], np.float64), 1e-9)
        self.om = D["om"].astype(np.int64); self.day = D["dayid"].astype(np.int64); self.date = D["date"].astype(np.int64)
        self.sm = (self.om - 1080) % 1440
        self.n = len(self.c); nd = int(self.day.max()) + 1; self.nd = nd
        idx = np.arange(self.n)
        self.ds = np.full(nd, -1, np.int64); self.de = np.full(nd, -1, np.int64)
        first = pd.Series(idx).groupby(self.day).first(); last = pd.Series(idx).groupby(self.day).last()
        self.ds[first.index] = first.values; self.de[last.index] = last.values
        L, atr, trend = day_levels(D)
        self.L = L; self.atr = atr.astype(np.float64); self.trend = trend.astype(np.int64)
        self.daydate = np.zeros(nd, np.int64); self.daydate[last.index] = self.date[last.values]
        df = pd.DataFrame(dict(day=self.day, om=self.om, o=self.o, h=self.h, l=self.l, c=self.c, v=self.v))
        rth = (df.om >= 570) & (df.om < 960)
        g = df[rth].groupby("day")
        self.ro = np.full(nd, -1, np.int64); r0 = pd.Series(idx[rth.values]).groupby(self.day[rth.values]).first(); self.ro[r0.index] = r0.values
        rc = g.c.last().reindex(range(nd)); rlast = g.om.last().reindex(range(nd))
        self.pdc = rc.where(rlast >= 959).shift(1).to_numpy().astype(np.float64)        # prior complete RTH close
        # RTH-anchored VWAP and volume-weighted sigma (NaN outside RTH)
        tp = (df.h + df.l + df.c) / 3
        pv = np.where(rth, tp * df.v, 0.0); vv = np.where(rth, df.v, 0.0); p2 = np.where(rth, tp * tp * df.v, 0.0)
        cpv = pd.Series(pv).groupby(self.day).cumsum().to_numpy(); cvv = pd.Series(vv).groupby(self.day).cumsum().to_numpy()
        cp2 = pd.Series(p2).groupby(self.day).cumsum().to_numpy()
        with np.errstate(invalid="ignore", divide="ignore"):
            vw = cpv / cvv; var = cp2 / cvv - vw * vw
        self.vwap = np.where(rth.values & (cvv > 0), vw, np.nan); self.vsd = np.sqrt(np.maximum(np.where(rth.values, var, np.nan), 0))
        # session (18:00-anchored) VWAP
        spv = pd.Series(tp * df.v).groupby(self.day).cumsum().to_numpy(); svv = pd.Series(df.v).groupby(self.day).cumsum().to_numpy()
        self.svwap = spv / svv
        # prior RTH value area (70%) and POC, 1-point bins on typical price
        self.pd_poc, self.pd_vah, self.pd_val = value_area(self, 0.70)

    def bars(self, tf):
        """Resampled tf-minute bars inside each session; 'last' = last 1m index (signal bar for next-bar entries)."""
        key = f"_b{tf}"
        if hasattr(self, key): return getattr(self, key)
        g = (self.sm // tf) + self.day * 10000
        df = pd.DataFrame(dict(g=g, o=self.o, h=self.h, l=self.l, c=self.c, v=self.v, i=np.arange(self.n)))
        a = df.groupby("g", sort=True).agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), v=("v", "sum"), first=("i", "first"), last=("i", "last"))
        B = dict(o=a.o.to_numpy(), h=a.h.to_numpy(), l=a.l.to_numpy(), c=a.c.to_numpy(), v=a.v.to_numpy(), first=a["first"].to_numpy(), last=a["last"].to_numpy())
        B["day"] = self.day[B["last"]]; B["sm"] = self.sm[B["first"]]; B["sme"] = self.sm[B["last"]]
        B["vwap"] = self.vwap[B["last"]]; B["vsd"] = self.vsd[B["last"]]
        setattr(self, key, B); return B


def value_area(D, frac):
    rth = (D.om >= 570) & (D.om < 960)
    tp = np.round((D.h + D.l + D.c) / 3)
    df = pd.DataFrame(dict(day=D.day[rth], p=tp[rth], v=D.v[rth]))
    poc = np.full(D.nd, np.nan); vah = np.full(D.nd, np.nan); val = np.full(D.nd, np.nan)
    for d, g in df.groupby("day"):
        s = g.groupby("p").v.sum().sort_index(); pr = s.index.to_numpy(); vol = s.to_numpy()
        k = int(np.argmax(vol)); lo = hi = k; tot = vol.sum(); acc = vol[k]
        while acc < frac * tot and (lo > 0 or hi < len(vol) - 1):
            up = vol[hi + 1] if hi < len(vol) - 1 else -1; dn = vol[lo - 1] if lo > 0 else -1
            if up >= dn: hi += 1; acc += vol[hi]
            else: lo -= 1; acc += vol[lo]
        poc[d] = pr[k]; vah[d] = pr[hi]; val[d] = pr[lo]
    sh = lambda a: np.r_[np.nan, a[:-1]]                       # value area of the PRIOR session
    return sh(poc), sh(vah), sh(val)


@njit(cache=True)
def execute(o, h, l, c, om, day, ev_i, ev_d, ev_t, ev_px, ev_sl, ev_tp, ev_exp, ev_hold, flat, maxday, out, SLIP):
    """ev_t: 0 market (next bar open), 1 limit at ev_px, 2 stop-entry at ev_px. Pending orders live until ev_exp (bar idx)."""
    n = len(c); k = 0; busy = -1; curday = -1; cnt = 0
    for e in range(len(ev_i)):
        si = ev_i[e]
        if si <= busy or si + 1 >= n: continue
        j0 = si + 1
        if day[j0] != day[si]: continue
        if day[si] != curday:
            curday = day[si]; cnt = 0
        if cnt >= maxday: continue
        d = ev_d[e]; sl = ev_sl[e]; tp = ev_tp[e]; fi = -1; ent = 0.0
        if ev_t[e] == 0:
            if om[j0] >= flat and om[j0] < 1080: continue
            fi = j0; ent = o[j0] + d * SLIP
        else:
            px = ev_px[e]; last = min(ev_exp[e], n - 1)
            for j in range(j0, last + 1):
                if day[j] != day[si] or (om[j] >= flat and om[j] < 1080): break
                if ev_t[e] == 1:
                    if (d == 1 and l[j] <= px - TICK) or (d == -1 and h[j] >= px + TICK):
                        fi = j; ent = min(px, o[j]) if d == 1 else max(px, o[j]); break
                    # target reached before the retest -> setup gone
                    if (d == 1 and h[j] >= tp) or (d == -1 and l[j] <= tp): break
                else:
                    if (d == 1 and h[j] >= px) or (d == -1 and l[j] <= px):
                        fi = j; ent = (max(px, o[j]) if d == 1 else min(px, o[j])) + d * SLIP; break
            if fi < 0: continue
        if (d == 1 and (ent <= sl or ent >= tp)) or (d == -1 and (ent >= sl or ent <= tp)): continue
        ex = np.nan; q = fi
        while q < n:
            if d == 1:
                if q > fi and o[q] <= sl: ex = o[q] - SLIP; break
                if l[q] <= sl: ex = sl - SLIP; break
                if q > fi and h[q] >= tp + TICK: ex = max(o[q], tp); break
            else:
                if q > fi and o[q] >= sl: ex = o[q] + SLIP; break
                if h[q] >= sl: ex = sl + SLIP; break
                if q > fi and l[q] <= tp - TICK: ex = min(o[q], tp); break
            if (q - fi >= ev_hold[e]) or (om[q] >= flat and om[q] < 1080) or q + 1 >= n or day[q + 1] != day[q]:
                ex = c[q] - d * SLIP; break
            q += 1
        out[k, 0] = d * (ex - ent); out[k, 1] = fi; out[k, 2] = q; out[k, 3] = d; out[k, 4] = abs(ent - sl); k += 1
        busy = q; cnt += 1
    return k


def run_events(D, ev, flat=955, maxday=1, slip=SLIP, norm_cost=None):
    """ev: dict of arrays (i, d, t, px, sl, tp, exp, hold). Returns trades DataFrame."""
    if len(ev["i"]) == 0: return pd.DataFrame(columns=["date", "usd", "fi", "xi", "d", "risk"])
    order = np.argsort(ev["i"], kind="stable")
    a = {k: np.ascontiguousarray(np.asarray(v)[order]) for k, v in ev.items()}
    out = np.zeros((len(a["i"]) + 1, 5))
    k = execute(D.o, D.h, D.l, D.c, D.om, D.day, a["i"].astype(np.int64), a["d"].astype(np.int64), a["t"].astype(np.int64), a["px"].astype(np.float64),
                a["sl"].astype(np.float64), a["tp"].astype(np.float64), a["exp"].astype(np.int64), a["hold"].astype(np.int64), flat, maxday, out, slip)
    o = out[:k]; fi = o[:, 1].astype(np.int64)
    df = pd.DataFrame(dict(date=D.date[fi], usd=o[:, 0] * D.pv - D.comm, fi=fi, xi=o[:, 2].astype(np.int64), d=o[:, 3], risk=o[:, 4]))
    if norm_cost is not None:            # cost-normalised P&L in daily-ATR units: gross points minus norm_cost * ATR
        A = D.atr[D.day[fi]]; df["usd"] = np.where(A > 0, (o[:, 0] - norm_cost * A) / np.where(A > 0, A, 1) * 100, 0.0)
    return df


def ev_from_lists(L):
    if not L: return dict(i=np.zeros(0, np.int64), d=np.zeros(0), t=np.zeros(0), px=np.zeros(0), sl=np.zeros(0), tp=np.zeros(0), exp=np.zeros(0), hold=np.zeros(0))
    A = np.array(L, dtype=np.float64)
    return dict(i=A[:, 0].astype(np.int64), d=A[:, 1], t=A[:, 2], px=A[:, 3], sl=A[:, 4], tp=A[:, 5], exp=A[:, 6].astype(np.int64), hold=A[:, 7].astype(np.int64))


def pf(u):
    u = np.asarray(u); l = -u[u <= 0].sum()
    return round(u[u > 0].sum() / l, 3) if l > 0 and len(u) >= 20 else np.nan


def split_stats(name, df):
    out = {}
    if name.startswith(("xau_long", "wti_long")):
        parts = (("G1", (df.date >= 20100201) & (df.date < 20150101)), ("G2", (df.date >= 20150101) & (df.date < 20200101)), ("T1", (df.date >= 20200101) & (df.date < 20240101)), ("T2", df.date >= 20240101))
    elif name.startswith("nqhd_long"):
        parts = (("TR", (df.date >= 20150201) & (df.date < 20200101)), ("T1", (df.date >= 20200101) & (df.date < 20240101)), ("T2", df.date >= 20240101))
    elif name.startswith(("nq_1m", "xau", "wti")):
        parts = (("IS", (df.date >= 20200201) & (df.date < 20240101)), ("C24", df.date >= 20240101))
    else:
        parts = (("REAL", df.date >= 20240201),)
    for lab, m in parts:
        u = df.usd[m].to_numpy()
        out[lab + "_n"] = len(u); out[lab + "_wr"] = round(100 * (u > 0).mean(), 1) if len(u) else np.nan
        out[lab + "_pf"] = pf(u); out[lab + "_net"] = round(u.sum())
    return out
