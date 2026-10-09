"""wrq_exits: exit engineering per module, re-simulated on 1-minute bars (wrq_lib.xsim) from the modules' own fills.
Families of variants around the current exit (1 contract, no scale-out):
  TS  target x kt (0 = no target) and stop x ks       (kt in .5,.67,.8,1,1.25,1.5,2,0 ; ks in .6,.8,1,1.25,1.5)
  BE  break-even after +be R, stop to entry + beo R     (be .25,.5,.75,1 ; beo 0, .1)
  TR  trailing after +tt R at td R behind the best extreme (tt .5,1 ; td .5,1)
  TM  time stop after ts minutes, unconditional or only if the trade is losing (ts 15,30,60,120)
Periods: IS (CFD 2020-23, selection), C24 (CFD 2024-26), REAL (MNQ 2024-26), L15 (2015-19 cost-normalised, %ATR units),
plus +4 ticks per side on IS / C24 / REAL. FOMC days excluded (2020+). -> wrq_exits.csv, wrq_exits_daily.pkl"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_lib import xsim, getD, PER, NORM_COST, SLIP, DEF

def variants():
    V = [("base", {})]
    for kt in (0.5, 0.67, 0.8, 1.0, 1.25, 1.5, 2.0, 0.0):
        for ks in (0.6, 0.8, 1.0, 1.25, 1.5):
            if kt == 1.0 and ks == 1.0: continue
            V.append((f"TS kt{kt} ks{ks}", dict(kt=kt, ks=ks)))
    for be in (0.25, 0.5, 0.75, 1.0):
        for beo in (0.0, 0.1):
            V.append((f"BE be{be} beo{beo}", dict(be=be, beo=beo)))
    for tt in (0.5, 1.0):
        for td in (0.5, 1.0):
            V.append((f"TR tt{tt} td{td}", dict(tt=tt, td=td)))
    for ts in (15, 30, 60, 120):
        for tsc in (-99.0, 0.0):
            V.append((f"TM ts{ts} {'all' if tsc < -50 else 'losing'}", dict(ts=ts, tsc=tsc)))
    return V

def arrays(E):
    E = E.sort_values("fi", kind="stable")
    return dict(fi=E.fi.to_numpy(np.int64), d=E.d.to_numpy(np.int64), ent0=E.ent0.to_numpy(float), et=E.et.to_numpy(np.int64), sl0=E.sl0.to_numpy(float),
                tp0=E.tp0.to_numpy(float), tx=E.tx.to_numpy(np.int64), date=E.date.to_numpy(), fomc=E.fomc.to_numpy(bool))

def sim(A, D, slip, p, norm=False):
    q = dict(DEF); q.update(p); out = np.zeros((len(A["fi"]), 6))
    xsim(D.o, D.h, D.l, D.c, A["fi"], A["d"], A["ent0"], A["et"], A["sl0"], A["tp0"], A["tx"], float(slip), float(q["ks"]), float(q["kt"]), float(q["be"]),
         float(q["beo"]), float(q["tt"]), float(q["td"]), int(q["ts"]), float(q["tsc"]), out)
    pts = out[:, 0]; ok = ~np.isnan(pts)
    if norm:
        a = D.atr[D.day[A["fi"]]]; u = np.where(a > 0, (pts - NORM_COST * a) / np.where(a > 0, a, 1) * 100, 0.0)
    else:
        u = pts * D.pv - D.comm
    return u, ok, out

def st(u):
    if len(u) == 0: return 0, np.nan, np.nan, np.nan, 0.0
    lo = -u[u <= 0].sum()
    return len(u), 100 * (u > 0).mean(), (u[u > 0].sum() / lo if lo > 0 else np.nan), u.mean(), u.sum()

RUNS = [("IS", "nq_1m.npz", SLIP, False), ("C24", "nq_1m.npz", SLIP, False), ("REAL", "mnq_fut.npz", SLIP, False), ("L15", "nqhd_long.npz", 0.0, True),
        ("IS+4", "nq_1m.npz", SLIP * 5, False), ("C24+4", "nq_1m.npz", SLIP * 5, False), ("REAL+4", "mnq_fut.npz", SLIP * 5, False)]

if __name__ == "__main__":
    EN = pickle.load(open("wrq_entries.pkl", "rb"))
    V = variants(); rows = []; daily = {}
    mods = sorted(EN["nq_1m.npz"]["mod"].unique())
    for name in ("nq_1m.npz", "mnq_fut.npz", "nqhd_long.npz"):
        D = getD(name)
        for m in mods:
            A = arrays(EN[name][EN[name]["mod"] == m])
            for lab, nm, slip, norm in RUNS:
                if nm != name or (lab.endswith("+4") and lab[:-2] not in ("IS", "C24", "REAL")): continue
                per = lab.replace("+4", ""); _, lo, hi = PER[per]
                msk = (A["date"] >= lo) & (A["date"] < hi) & (~A["fomc"] if per != "L15" else True)
                for vn, p in V:
                    if lab.endswith("+4") and vn != "base" and not vn.startswith(("TS", "BE", "TR", "TM")): continue
                    u, ok, out = sim(A, D, slip, p, norm)
                    k = ok & msk; n, wr, pff, ex, net = st(u[k])
                    rows.append(dict(mod=m, var=vn, per=lab, n=n, wr=wr, pf=pff, exp=ex, net=net,
                                     tgt=100 * (out[k, 2] == 1).mean() if n else np.nan, stop=100 * np.isin(out[k, 2], (0, 3)).mean() if n else np.nan))
                    if not lab.endswith("+4"):
                        daily[(m, vn, per)] = pd.Series(u[k], index=A["date"][k]).groupby(level=0).sum()
            print(name, m, flush=True)
    R = pd.DataFrame(rows); R.to_csv("wrq_exits.csv", index=False)
    pickle.dump(daily, open("wrq_exits_daily.pkl", "wb"))
    print(len(R), "rows")
