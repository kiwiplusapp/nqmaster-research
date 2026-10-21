"""Batch 11 lookahead check (2026-10-21). For a sample of events of every families11 generator (3 configs per family, up to 12 events each,
seeded), the data AFTER the signal bar is perturbed (all later bars: prices +137 points, ranges +-25 wider, volume x3) and the generator is
re-run on the perturbed data: the event at the same signal bar must exist with the same direction, type, price, stop, target and expiry.
Anything computed from bars after the signal bar (the rest of the day, later days) would change the event -> violation.
Two-sided OCO setups (inside-day breakout, Crabel NR / stretch, Steidlmayer auction) resolve the first touch in the generator, so their
signal bar is the bar before the touch: there the touch bar is left as it is, the bars between the order placement bar and the signal bar
are collapsed to their close (a collapsed bar touches no level it did not touch before) and everything after the touch bar is shifted;
the event must be unchanged (levels from bars <= the placement bar only).  -> b11_lookahead.json"""
import os, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from core import Data, S
from ict import day_levels
import families11 as F11


class Light:
    bars = Data.bars


def perturb(D, i, i0=None):
    X = Light()
    for k in ("om", "day", "date", "sm", "n", "nd", "ds", "de", "ro", "vwap", "vsd", "pv", "comm", "name", "daydate"): setattr(X, k, getattr(D, k))
    o, h, l, c, v = D.o.copy(), D.h.copy(), D.l.copy(), D.c.copy(), D.v.copy()
    if i0 is not None:                                   # OCO: keep the touch bar i + 1, collapse the bars between placement and signal
        if i > i0:
            sl_ = slice(i0 + 1, i + 1); o[sl_] = c[sl_]; h[sl_] = c[sl_]; l[sl_] = c[sl_]; v[sl_] *= 3
        start = i + 2
    else:
        start = i + 1
    o[start:] += 137.0; c[start:] += 137.0; h[start:] += 162.0; l[start:] += 112.0; v[start:] *= 3
    X.o, X.h, X.l, X.c, X.v = o, h, l, c, v
    L, atr, trend = day_levels(dict(om=D.om, dayid=D.day, h=h, l=l, c=c)); X.L = L; X.atr = atr.astype(np.float64); X.trend = trend.astype(np.int64)
    return X


def placement_bar(D, fam, p, i):
    """Order placement bar of an OCO setup (its signal bar is the bar before the first touch)."""
    d = D.day[i]
    if fam == "LW_INOUT": t0 = S(930)
    elif fam == "CRABEL_NR": t0 = S(p["orl"]) - 1
    elif fam == "CRABEL_STRETCH": t0 = S(930)
    elif fam == "STEID_OPEN": t0 = S(930) + p["W"] - 1
    else: return None
    return int(F11._first_at(D.sm, D.ro, D.de, d, t0))


def is_oco(fam, p):
    return fam in ("CRABEL_NR", "CRABEL_STRETCH") or (fam == "LW_INOUT" and p["pat"] == "in") or (fam == "STEID_OPEN" and p["typ"] == "auction")


def main(only=None):
    D = Data("nqdb.npz"); rng = np.random.default_rng(11); OUT = json.load(open(os.path.join(HERE, "b11_lookahead.json"))) if only else {}; tot = 0; viol_tot = 0
    for fam, (gen, grid, maxday) in F11.FAMILIES11.items():
        if only and fam not in only: continue
        rec = dict(configs=[], events=0, violations=0, max_diff=0.0, missing=0, details=[])
        picks = sorted({0, len(grid) // 2, len(grid) - 1})
        if fam in ("LW_INOUT", "STEID_OPEN"):           # make sure both the OCO and the one-sided variants are covered
            picks = sorted(set(picks) | {j for j in range(len(grid)) if (j % 97 == 3)})[:5]
        for j in picks:
            p = grid[j]; ev = gen(D, p); n = len(ev["i"])
            rec["configs"].append(dict(j=j, params=repr(p), n_events=int(n)))
            if n == 0: continue
            sel = rng.choice(n, size=min(12, n), replace=False)
            for e in sel:
                i = int(ev["i"][e]); i0 = placement_bar(D, fam, p, i) if is_oco(fam, p) else None
                X = perturb(D, i, i0); ev2 = gen(X, p)
                m = np.where(ev2["i"] == i)[0]
                rec["events"] += 1; tot += 1
                if len(m) == 0:
                    rec["violations"] += 1; rec["missing"] += 1; viol_tot += 1
                    rec["details"].append(dict(j=j, i=i, date=int(D.date[i]), kind="missing")); continue
                k = int(m[0]); diffs = {}
                for key in ("d", "t", "px", "sl", "tp", "exp"):
                    a, b = float(ev[key][e]), float(ev2[key][k]); dd = abs(a - b)
                    if dd > 1e-6: diffs[key] = (a, b)
                    rec["max_diff"] = max(rec["max_diff"], dd)
                if diffs:
                    rec["violations"] += 1; viol_tot += 1
                    rec["details"].append(dict(j=j, i=i, date=int(D.date[i]), kind="changed", diffs=diffs))
        OUT[fam] = rec
        print(fam, "events", rec["events"], "violations", rec["violations"], "max_diff", rec["max_diff"], flush=True)
    OUT["_total"] = dict(events=sum(v["events"] for k, v in OUT.items() if not k.startswith("_")), violations=sum(v["violations"] for k, v in OUT.items() if not k.startswith("_")))
    json.dump(OUT, open(os.path.join(HERE, "b11_lookahead.json"), "w"), indent=1)
    print("TOTAL events", tot, "violations", viol_tot)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
