"""Dense per-module minute equity grids for prop-account research.
For each period (IS = CFD 2020-23, C24 = CFD 2024-26, REAL = MNQ/MGC futures 2024-26) and each module:
  L[d, t] = realized-so-far + open P&L at the bar's ADVERSE extreme (worst equity in minute t), $ per 1 contract (with module weight)
  R[d, t] = realized-so-far (step function)        t = session minute (18:00 = 0)
Modules: U:* Ultra (NQMaster rules, boosts x2 / ICT x2), U1:* same with every weight capped at 1, W:* WR70Plus variants,
C:VOLB_tf0 (Core), N:LATE15, G:* gold modules. Output: research/tmp/dense/<per>.npz (+ meta.pkl)."""
import os, sys, pickle, ast, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, run_events
from families4 import FAMILIES4
from news import NEWS
FOMC = set(NEWS["FOMC"]); OUT = os.path.join(RES, "tmp", "dense"); os.makedirs(OUT, exist_ok=True)
T = pickle.load(open("robust_trades.pkl", "rb")); GC = pickle.load(open("gold_curated_trades.pkl", "rb"))
SRC = {("nq", "IS"): "nq_1m.npz", ("nq", "C24"): "nq_1m.npz", ("nq", "REAL"): "mnq_fut.npz", ("gold", "IS"): "xau_long.npz", ("gold", "C24"): "xau_long.npz", ("gold", "REAL"): "mgc_fut.npz"}
PV = {"nq": 2.0, "gold": 4.0}
_L = {}
def raw(name):
    if name not in _L:
        z = np.load(os.path.join(RES, "data", name)); date = z["date"]; idx = pd.Series(np.arange(len(date))).groupby(date)
        _L[name] = dict(o=z["o"], h=z["h"], l=z["l"], sm=((z["om"].astype(np.int64) - 1080) % 1440), first=idx.first(), last=idx.last())
    return _L[name]
def dense(F, inst, per, days):
    Z = raw(SRC[(inst, per)]); pv = PV[inst]; pos = {d: k for k, d in enumerate(days)}
    L = np.zeros((len(days), 1440), np.float32); R = np.zeros((len(days), 1440), np.float32)
    for d, g in F.groupby("date"):
        if d not in pos or d not in Z["first"].index: continue
        k = pos[d]; a, b = Z["first"][d], Z["last"][d] + 1; mm = Z["sm"][a:b]; n = b - a
        adv = np.zeros(1440); rel = np.zeros(1440)
        for r in g.itertuples():
            q = r.w
            if q == 0: continue
            i0 = min(np.searchsorted(mm, r.tin), n - 1); i1 = min(max(np.searchsorted(mm, r.tout - 1), i0), n - 1)
            e = Z["o"][a + i0] + 0.25 * r.d
            if i1 > i0:
                seg = slice(a + i0, a + i1)
                av = (Z["l"][seg] - e) * pv if r.d == 1 else (e - Z["h"][seg]) * pv
                np.add.at(adv, mm[i0:i1], q * av)
            rel[mm[i1]:] += q * r.u
        L[k] = rel + adv; R[k] = rel
    return L, R
def late15(per):
    gen, G, md = FAMILIES4["LATE_MOM"]; p = G[762]; D = Data("mnq_fut.npz" if per == "REAL" else "nq_1m.npz")
    df = run_events(D, gen(D, p), flat=955, maxday=md); df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
    return pd.DataFrame(dict(date=df.date, mod="LATE15", tin=df.tin, tout=df.tout, d=df.d, u=df.usd, w=1.0))
meta = {}
for per in ("IS", "C24", "REAL"):
    days = np.array(sorted(T["Ultra"][per][1])); lo, hi = days.min(), days.max(); arrs = {}
    U = T["Ultra"][per][0]; W = T["WR70Plus"][per][0]; C = T["Core6"][per][0]
    mods = {}
    for m, g in U.groupby("mod"):
        mods["U:" + m] = ("nq", g)
        if (g.w != 1).any(): mods["U1:" + m] = ("nq", g.assign(w=np.minimum(g.w, 1.0)))
    for m, g in W.groupby("mod"):
        if m in ("ORB60", "VOLB_tf1", "VW13b", "REV06", "CRT11", "MSEQ"): mods["W:" + m] = ("nq", g)
    mods["C:VOLB_tf0"] = ("nq", C[C["mod"] == "VOLB_tf0"])
    L15 = late15(per); mods["N:LATE15"] = ("nq", L15[(L15.date >= lo) & (L15.date <= hi) & ~L15.date.isin(FOMC)])
    for m, P in GC.items():
        g = P[per]; mods["G:" + m] = ("gold", g[(g.date >= lo) & (g.date <= hi)])
    for k, (inst, F) in mods.items():
        L, R = dense(F, inst, per, days); arrs[k + "|L"] = L; arrs[k + "|R"] = R
    np.savez(os.path.join(OUT, f"{per}.npz"), days=days, **arrs)
    meta[per] = sorted(mods); print(per, len(days), "days", len(mods), "modules", flush=True)
pickle.dump(meta, open(os.path.join(OUT, "meta.pkl"), "wb"))
print(meta["REAL"])
