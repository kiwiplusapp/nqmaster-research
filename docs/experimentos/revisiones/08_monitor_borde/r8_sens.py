"""r8: sensitivity of exp08's verdict. run2 = copy of exp08.run with options (start date, review-set mode, CUSUM reset at 2020, drop ATR<150 days 2020+)."""
import os, sys, json, numpy as np, pandas as pd
M = "/home/user/nqmaster-research/research/mine"; sys.path.insert(0, M); sys.path.insert(0, os.path.dirname(M)); os.chdir(M)
SP = "/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad"
import exp08_monitor as E
from os_adapt import review_set, stats, DUR
NQTAB = {2020: "LF0430 LF06 MOM11 MOM13 ON07 ORB60 ORB90 REV06 VW13", 2021: "LF0430 LF06 MOM11 MOM13 ON07 VW13", 2022: "LF0430 LF06 ON07 VW13",
         2023: "LF06 ON07", 2024: "LF06 VW13", 2025: "", 2026: "", 2027: "REV06"}
def nqtable(y): return NQTAB[max(2020, min(y, 2027))].split()

def run2(days, atr, mods, Mv, N, post, pol, k, h, hw, start=0, review="alarm", reset2020=False, keep=None):
    n = len(days); out = np.zeros(n); s = 0.0; until = -1; fb = None; alarms = []; warns = []; off = 0; half = 0; warned = False; halfdays = []
    col = {m: i for i, m in enumerate(mods)}; allm = list(range(len(mods))); fbsets = []
    for t in range(n):
        if reset2020 and days[t] == days[days >= 20200101][0]: s = 0.0; warned = False; until = min(until, t)
        if t < until: act = fb; off += 1
        else: act = allm
        scale = 0.5 if (pol == "WH" and t >= until and s > hw) else 1.0
        half += scale < 1.0
        if scale < 1: halfdays.append(int(days[t]))
        out[t] = scale * (Mv[t, act].sum() if len(act) else 0.0)
        if days[t] < start or (keep is not None and not keep[t]): continue        # monitor not running / day not counted (NQMaster: ATR < MinAtrPoints)
        if t >= until:
            z = E.zday(Mv[t, act].sum(), t, atr, post, "corregido")
            s = max(0.0, s + k - z)
            if s <= 0: warned = False
            if not warned and s > hw: warned = True; warns.append(int(days[t]))
            if s > h:
                alarms.append(int(days[t])); s = 0.0; warned = False
                if pol.startswith("P"): fb = []; until = t + 1 + int(pol[1:])
                elif pol in ("W252", "WH"):
                    if review == "alarm": rs = review_set(N, mods, int(days[t]))
                    elif review == "jan": rs = review_set(N, mods, int(days[t]) // 10000 * 10000 + 101)
                    else: rs = [m for m in mods if m not in nqtable(int(days[t]) // 10000)]
                    fb = [col[m] for m in rs]; until = t + 1 + 252; fbsets.append((int(days[t]), sorted(set(mods) - set(rs))))
                elif pol == "D252": fb = [col[m] for m in DUR if m in col]; until = t + 1 + 252
    return out, alarms, warns, off, half, fbsets, halfdays

def table(days, OUTP):
    return {p: {q: stats(x[(days >= lo) & (days < hi)]) for q, (lo, hi) in E.PER.items()} for p, x in OUTP.items()}

def decide(T):
    inc = T["W252"]; ok = []
    for p, r in T.items():
        if p in ("W252", "D252"): continue
        c1 = r["2013-19 norm"]["sharpe"] > inc["2013-19 norm"]["sharpe"] and r["2013-19 norm"]["net"] >= inc["2013-19 norm"]["net"]
        c2 = all(r[q]["net"] >= 0.95 * inc[q]["net"] and r[q]["sharpe"] >= inc[q]["sharpe"] - 0.05 for q in ("2020-23 real", "2024-26 real"))
        if c1 and c2: ok.append(p)
    return max(ok, key=lambda p: T[p]["2013-19 norm"]["sharpe"]) if ok else "W252"

days, atr, mods, Mv, N, post = E.build(with_new=True)
keep150 = ~((days >= 20200101) & (atr < 150))
# 0) run2 default == exp08.run
for pol in ("A", "W252", "WH", "P252"):
    a = E.run(days, atr, mods, Mv, N, post, pol, E.K, E.Hh, E.HW); b = run2(days, atr, mods, Mv, N, post, pol, E.K, E.Hh, E.HW)
    assert np.allclose(a[0], b[0]) and a[1] == b[1], pol
print("run2 default reproduces exp08.run")
POLS = ("A", "W252", "P63", "P126", "P252", "D252", "WH")
cases = [("base (exp08)", dict()),
         ("k/h recal2 0.085/24.44/9.12", dict(k=0.085, h=24.44, hw=9.12)),
         ("k/h os_adapt 0.0758/18.57 (hw 0.37h)", dict(k=0.0758, h=18.57, hw=0.37 * 18.57)),
         ("h x0.9", dict(h=0.9 * E.Hh)), ("h x1.1", dict(h=1.1 * E.Hh)),
         ("start 2011-01-01", dict(start=20110101)), ("start 2011-07-01", dict(start=20110701)), ("start 2012-01-01", dict(start=20120101)),
         ("start 2013-01-01", dict(start=20130101)), ("start 2014-01-01", dict(start=20140101)),
         ("review = 1 Jan of alarm year", dict(review="jan")), ("review = NQMaster table literal", dict(review="nqtable")),
         ("CUSUM reset 2020-01-01", dict(reset2020=True)), ("no ATR<150 days 2020+ (NQMaster)", dict(keep=keep150)),
         ("reset 2020 + no ATR<150", dict(reset2020=True, keep=keep150))]
RES = {}
for name, o in cases:
    k = o.pop("k", E.K); h = o.pop("h", E.Hh); hw = o.pop("hw", E.HW); OUTP = {}; info = {}
    for pol in POLS:
        x, al, wa, off, half, fbs, hd = run2(days, atr, mods, Mv, N, post, pol, k, h, hw, **o); OUTP[pol] = x
        info[pol] = dict(alarms=al, warns=wa, half=half, fb=fbs, half2020=sum(d >= 20200101 for d in hd))
    T = table(days, OUTP); g = decide(T)
    dW = T["W252"]["2013-19 norm"]; dA = T["A"]["2013-19 norm"]
    best = max((p for p in POLS if p != "D252"), key=lambda p: T[p]["2013-19 norm"]["sharpe"])
    print(f"\n== {name}: ganador regla = {g} | best Sharpe 2013-19 (sin D252) = {best}")
    for p in POLS:
        r = T[p]; print(f"   {p:5s} al {info[p]['alarms']} | 13-19 {r['2013-19 norm']['net']:>6} Sh {r['2013-19 norm']['sharpe']:.2f} DD {r['2013-19 norm']['maxdd']:>5} | 20-23 {r['2020-23 real']['net']:>6} Sh {r['2020-23 real']['sharpe']:.2f} | 24-26 {r['2024-26 real']['net']:>6} Sh {r['2024-26 real']['sharpe']:.2f}"
                     + (f" | half {info[p]['half']} (2020+: {info[p]['half2020']}) warns {info[p]['warns']}" if p in ("A", "WH") else "") + (f" | off-sets {info[p]['fb']}" if p == "W252" else ""))
    RES[name] = dict(ganador=g, T=T, info={p: {kk: vv for kk, vv in info[p].items()} for p in POLS})
json.dump(RES, open(f"{SP}/r8_sens.json", "w"), indent=1, default=str)
