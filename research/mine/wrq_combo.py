"""wrq_combo: portfolio test of the surviving ideas, alone and combined, for Ultra and WR70Plus (rules + conflict filter),
IS / C24 / REAL / L15 and +4 ticks per side:
  BE    VOLB (Ultra): stop to entry + 0.1R after +0.75R
  ORBc  ORB60 + ORB90: skip the breakout when price at the fill decision (close of the bar before the fill) is not at least
        0.1 ATR beyond the prior RTH close in the trade direction (IS-chosen on ORB60: 0.0988; ORB90 by analogy)
  ORBt  same idea decided at range completion: breakout trigger (range high + 1 tick / low - 1 tick) vs prior close >= 0.1 ATR
  ORB0  ORBt with threshold 0 (trigger on the trade side of the prior close)
  VTSO  VOLB_tf1 (WR70Plus): no entry later than 77 min after 09:30 (10:47)
  AGR   agreement: skip MOM1030 / MOM13 entries when no other NQ module is already open in the same direction
        (IS criterion: the 'alone' subset has PF < 1 in IS; LATE15 also met it in IS -> tested as AGR3)
-> wrq_combo.csv"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_lib import getD, SLIP, S
from wrq_port import build_profile, metrics, days_of, PROFILES, conflict_filter, apply_rules, module_trades, BASE_W, daily
from wrq_agree import n_same
HERE = os.path.dirname(os.path.abspath(__file__))
FT = pickle.load(open(os.path.join(HERE, "wrq_feats.pkl"), "rb"))
_RNG = {}

def orb_range(name, rm):
    if (name, rm) not in _RNG:
        D = getD(name); hi = np.full(D.nd, np.nan); lo = np.full(D.nd, np.nan)
        m = (D.om >= 570) & (D.om < 570 + rm)
        g = pd.DataFrame(dict(day=D.day[m], h=D.h[m], l=D.l[m])).groupby("day").agg(h=("h", "max"), l=("l", "min"))
        hi[g.index] = g.h; lo[g.index] = g.l; _RNG[(name, rm)] = (hi, lo)
    return _RNG[(name, rm)]

def k_pdcd(thr):
    def k(E, name):
        x = FT[name].loc[E.index, "pdcd"].to_numpy(); return ~np.nan_to_num(x < thr, nan=0).astype(bool)
    return k

def k_trig(thr, rm):
    def k(E, name):
        D = getD(name); hi, lo = orb_range(name, rm); day = D.day[E.fi.to_numpy()]; s = E.d.to_numpy(); A = D.atr[day]
        trig = np.where(s > 0, hi[day] + 0.25, lo[day] - 0.25); x = (trig - D.pdc[day]) * s / A
        return ~np.nan_to_num(x < thr, nan=0).astype(bool)
    return k

def k_tso(maxmin):
    def k(E, name):
        x = FT[name].loc[E.index, "tso"].to_numpy(); return ~(x > maxmin)
    return k

def build(per, prof, over=None, agr=(), slip=SLIP, cache=None):
    """build_profile + agreement rule: drop 'alone' trades of the modules in agr, then redo the conflict filter."""
    if not agr: return build_profile(per, prof, over, slip=slip, cache=cache)
    X0 = build_profile(per, prof, over, slip=slip, rules=False, cache=cache)        # conflict-filtered, no rules
    N = n_same(X0); drop = N["mod"].isin(agr) & (N.nsame == 0)
    dropped = set(map(tuple, N.loc[drop, ["date", "mod", "tin"]].to_numpy()))
    parts = []
    for mod, p in PROFILES[prof].items():
        q, kf = dict(p), None
        if over and mod in over:
            q2, kf = over[mod]; q.update(q2 or {})
        key = (per, mod, tuple(sorted(q.items())), slip, kf)
        T = cache[key] if cache is not None and key in cache else module_trades(per, mod, q, slip, kf)
        parts.append(T)
    X = pd.concat(parts, ignore_index=True)
    X = X[[(d, m, t) not in dropped for d, m, t in zip(X.date, X["mod"], X.tin)]]
    X = conflict_filter(X.sort_values(["date", "tin"], kind="stable").reset_index(drop=True))
    return apply_rules(X, per)

BE = {"VOLB": (dict(be=0.75, beo=0.1), None)}
ORBc = {"ORB60": ({}, k_pdcd(0.0988)), "ORB90": ({}, k_pdcd(0.0988))}
ORBt = {"ORB60": ({}, k_trig(0.1, 60)), "ORB90": ({}, k_trig(0.1, 90))}
ORB0 = {"ORB60": ({}, k_trig(0.0, 60)), "ORB90": ({}, k_trig(0.0, 90))}
VTSO = {"VOLB_tf1": ({}, k_tso(77))}
CANDS = {
    "Ultra": [("base", None, ()), ("BE", BE, ()), ("ORBc", ORBc, ()), ("ORBt", ORBt, ()), ("ORB0", ORB0, ()),
              ("AGR (MOM1030, MOM13)", None, ("MOM1030", "MOM13")), ("AGR3 (+LATE15)", None, ("MOM1030", "MOM13", "LATE15")),
              ("BE + ORBt", {**BE, **ORBt}, ()), ("BE + ORBt + AGR", {**BE, **ORBt}, ("MOM1030", "MOM13"))],
    "WR70Plus": [("base", None, ()), ("ORBc", ORBc, ()), ("ORBt", ORBt, ()), ("ORB0", ORB0, ()), ("VTSO", VTSO, ()),
                 ("ORBt + VTSO", {**ORBt, **VTSO}, ())],
}

if __name__ == "__main__":
    rows = []; cache = {}; DL = {}
    for prof, cands in CANDS.items():
        for per in ("IS", "C24", "REAL", "L15"):
            days = days_of(per)
            for slip, tag in ((SLIP, ""), (SLIP * 5, " +4t")):
                if per == "L15" and tag: continue
                for nm, over, agr in cands:
                    X = build(per, prof, over, agr, slip, cache); m = metrics(X, days); m.update(prof=prof, per=per + tag, cand=nm); rows.append(m)
                    if not tag: DL[(prof, nm, per)] = daily(X, days)
            print(prof, per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("wrq_combo.csv", index=False); pickle.dump(DL, open("wrq_combo_daily.pkl", "wb"))
    pd.set_option("display.width", 250)
    for prof in CANDS:
        for c in ("wr", "pf", "sharpe", "mo", "maxdd", "tpd"):
            P = R[R.prof == prof].pivot_table(index="cand", columns="per", values=c, sort=False)[["IS", "C24", "REAL", "L15", "IS +4t", "C24 +4t", "REAL +4t"]]
            print(f"=== {prof} {c}"); print(P.round(3 if c in ("pf", "sharpe", "tpd") else 1).to_string())
