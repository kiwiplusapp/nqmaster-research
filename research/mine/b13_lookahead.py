"""Batch 13 lookahead check (2026-10-21). For a sample of events of every families13 generator (5 configs per family, up to 12 events each,
seeded) the data AFTER the signal bar is perturbed (prices +137 points, ranges widened, volume x3) and the generator re-run on the perturbed
data: the event at the same signal bar must exist with the same direction, type, price, stop, target and expiry.
Pivots: a pivot needs k tf bars after it, so the setup is armed only after the last 1m bar of tf bar p2+k; anything that read later bars
(the pivot's right side not yet complete, the sweep extreme, the rest of the day) would change or remove the event.
Touch-resolved events (DT_CONT stop entries, DT_REV limit entries, IB_FADE limits, IB_BREAK OCO): the signal bar is the bar before the
touch, i.e. a resting order that exists from the arming bar; there the touch bar i+1 is kept and everything from i+2 on is perturbed.
VWAP / session VWAP / ATR / daily trend / tf-bar SMA200 are recomputed from the perturbed data. -> b13_lookahead.json"""
import os, sys, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from core import Data
from ict import day_levels
import families13 as F13


class Light:
    bars = Data.bars


def vwaps(X):
    df = pd.DataFrame(dict(day=X.day, om=X.om, h=X.h, l=X.l, c=X.c, v=X.v)); rth = ((df.om >= 570) & (df.om < 960)).values
    tp = (df.h + df.l + df.c) / 3
    cpv = pd.Series(np.where(rth, tp * df.v, 0.0)).groupby(X.day).cumsum().to_numpy(); cvv = pd.Series(np.where(rth, df.v, 0.0)).groupby(X.day).cumsum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"): vw = cpv / cvv
    X.vwap = np.where(rth & (cvv > 0), vw, np.nan)
    X.svwap = pd.Series(tp * df.v).groupby(X.day).cumsum().to_numpy() / pd.Series(df.v).groupby(X.day).cumsum().to_numpy()


def perturb(D, start):
    X = Light()
    for k in ("om", "day", "date", "sm", "n", "nd", "ds", "de", "ro", "pv", "comm", "name", "daydate", "vsd"): setattr(X, k, getattr(D, k))
    o, h, l, c, v = D.o.copy(), D.h.copy(), D.l.copy(), D.c.copy(), D.v.copy()
    o[start:] += 137.0; c[start:] += 137.0; h[start:] += 162.0; l[start:] += 112.0; v[start:] *= 3
    X.o, X.h, X.l, X.c, X.v = o, h, l, c, v
    L, atr, trend = day_levels(dict(om=D.om, dayid=D.day, h=h, l=l, c=c)); X.L = L; X.atr = atr.astype(np.float64); X.trend = trend.astype(np.int64)
    vwaps(X); return X


def touch_resolved(fam, p):
    return fam in ("DT_CONT", "IB_BREAK") or (fam == "DT_REV" and p["ent"] == "lim") or (fam == "IB_FADE" and p["ent"] == "lim")


def main():
    D = Data("nqdb.npz"); rng = np.random.default_rng(13); OUT = {}; tot = viol = 0
    for fam, (gen, grid, maxday) in F13.FAMILIES13.items():
        rec = dict(configs=[], events=0, violations=0, max_diff=0.0, missing=0, details=[])
        picks = sorted(set(int(x) for x in rng.choice(len(grid), size=min(5, len(grid)), replace=False)) | {0})
        for j in picks:
            p = grid[j]; ev = gen(D, p); n = len(ev["i"]); rec["configs"].append(dict(j=j, params=repr(p), n_events=int(n)))
            if n == 0: continue
            for e in rng.choice(n, size=min(12, n), replace=False):
                i = int(ev["i"][e]); X = perturb(D, i + 2 if touch_resolved(fam, p) else i + 1); ev2 = gen(X, p)
                m = np.where(ev2["i"] == i)[0]; rec["events"] += 1; tot += 1
                if len(m) == 0:
                    rec["violations"] += 1; rec["missing"] += 1; viol += 1; rec["details"].append(dict(j=j, i=i, date=int(D.date[i]), kind="missing")); continue
                best = None
                for k in m:                                  # several setups can share a signal bar: match the closest one
                    diffs = {key: (float(ev[key][e]), float(ev2[key][k])) for key in ("d", "t", "px", "sl", "tp", "exp") if abs(float(ev[key][e]) - float(ev2[key][k])) > 1e-6}
                    if best is None or len(diffs) < len(best): best = diffs
                    if not diffs: break
                if best:
                    rec["violations"] += 1; viol += 1; rec["details"].append(dict(j=j, i=i, date=int(D.date[i]), kind="changed", diffs=best))
                    rec["max_diff"] = max(rec["max_diff"], max(abs(a - b) for a, b in best.values()))
        OUT[fam] = rec; print(fam, "events", rec["events"], "violations", rec["violations"], flush=True)
    OUT["_total"] = dict(events=tot, violations=viol)
    json.dump(OUT, open(os.path.join(HERE, "b13_lookahead.json"), "w"), indent=1); print("TOTAL events", tot, "violations", viol)


if __name__ == "__main__":
    main()
