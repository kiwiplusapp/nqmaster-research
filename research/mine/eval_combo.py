"""NQMaster (MNQ) + GoldMaster (MGC) in the same prop account. Minute-level combined equity path (open P&L from bar high/low,
realized at exit), per period: IS = CFD 2020-23, C24 = CFD 2024-26, REAL = MNQ + MGC futures 2024-26.
Gold size g = MGC per gold module for each MNQ unit (k scales both). Accounts:
  Lucid Flex 50K : target 3,000, EOD trailing 2,000 (locks +100), 50% consistency, no time limit (lucid.py)
  Apex 50K 2026  : target 3,000, DD 2,000, 21 sessions, EOD+DLL1000 policy 2->3 @12 <1500 DL600 (eod_eval.py)
Lifecycle (12 months per account slot, fees included) as lucid.py."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from lucid import lucid_eval, lucid_funded, life_lucid, life_apex, summarize
from eod_eval import run_eval
T = pickle.load(open("robust_trades.pkl", "rb")); G = pickle.load(open("gold_final_trades.pkl", "rb"))
DATA = {("nq", "IS"): ("nq_1m.npz", 2.0), ("nq", "C24"): ("nq_1m.npz", 2.0), ("nq", "REAL"): ("mnq_fut.npz", 2.0),
        ("gold", "IS"): ("xau_long.npz", 4.0), ("gold", "C24"): ("xau_long.npz", 4.0), ("gold", "REAL"): ("mgc_fut.npz", 4.0)}
_L = {}
def load(name):
    if name not in _L:
        z = np.load(os.path.join(RES, "data", name)); _L[name] = {k: z[k] for k in ("o", "h", "l", "om", "date")}
    return _L[name]
def grids(F, name, pv):
    Z = load(name); date = Z["date"]; smm = (Z["om"].astype(np.int64) - 1080) % 1440; o, h, l = Z["o"], Z["h"], Z["l"]
    idx = pd.Series(np.arange(len(date))).groupby(date); first = idx.first(); last = idx.last()
    out = {}
    for d, g in F.groupby("date"):
        if d not in first.index: continue
        a, b = first[d], last[d] + 1; mm = smm[a:b]; n = b - a
        fav = np.zeros(1440); adv = np.zeros(1440); rel = np.zeros(1440)
        for r in g.itertuples():
            q = r.w
            if q == 0: continue
            i0 = min(np.searchsorted(mm, r.tin), n - 1); i1 = min(max(np.searchsorted(mm, r.tout - 1), i0), n - 1)
            e = o[a + i0] + 0.25 * r.d
            if i1 > i0:
                seg = slice(a + i0, a + i1); gm = mm[i0:i1]
                fv = (h[seg] - e) * pv if r.d == 1 else (e - l[seg]) * pv; av = (l[seg] - e) * pv if r.d == 1 else (e - h[seg]) * pv
                np.add.at(fav, gm, q * fv); np.add.at(adv, gm, q * av)
            rel[mm[i1]:] += q * r.u
        out[d] = (fav, adv, rel)
    return out
def combine(parts, days):
    di, fv, av, rl = [], [], [], []
    for k, d in enumerate(days):
        fav = np.zeros(1440); adv = np.zeros(1440); rel = np.zeros(1440); has = False
        for P, w in parts:
            if d in P: f, a, r = P[d]; fav += w * f; adv += w * a; rel += w * r; has = True
        if not has: continue
        nz = np.nonzero((fav != 0) | (adv != 0) | (np.diff(np.r_[0.0, rel]) != 0))[0]
        di.append(np.full(len(nz), k)); fv.append(rel[nz] + fav[nz]); av.append(rel[nz] + adv[nz]); rl.append(rel[nz])
    return dict(day=np.concatenate(di), fav=np.concatenate(fv), adv=np.concatenate(av), rel=np.concatenate(rl), ndays=len(days), dates=days)
PER = ("IS", "C24", "REAL")
PATHS = {}
for per in PER:
    nqg = {p: grids(T[p][per][0], *DATA[("nq", per)]) for p in ("Ultra", "WR70Plus")}
    gg = {p: grids(G[(p, per)], *DATA[("gold", per)]) for p in ("WinRate", "Robust")}
    days = np.array(sorted(T["Ultra"][per][1]))
    for nqp in ("Ultra", "WR70Plus"):
        PATHS[(nqp, "solo NQ", per)] = combine([(nqg[nqp], 1.0)], days)
        PATHS[(nqp, "+ oro WinRate", per)] = combine([(nqg[nqp], 1.0), (gg["WinRate"], 1.0)], days)
        PATHS[(nqp, "+ oro WinRate x2", per)] = combine([(nqg[nqp], 1.0), (gg["WinRate"], 2.0)], days)
        PATHS[(nqp, "+ oro Robust", per)] = combine([(nqg[nqp], 1.0), (gg["Robust"], 1.0)], days)
    print(per, "paths built", flush=True)
pickle.dump(PATHS, open("combo_paths.pkl", "wb"))
rows = []
for nqp, gl in dict.fromkeys((a, b) for a, b, _ in PATHS):
    r = dict(nq=nqp, oro=gl)
    for per in PER:
        P = PATHS[(nqp, gl, per)]; nd = P["ndays"]
        last = pd.Series(P["rel"]).groupby(P["day"]).last().reindex(range(nd), fill_value=0.0).to_numpy(); eq = last.cumsum()
        r[f"{per}_mo"] = round(last.mean() * 21); r[f"{per}_sharpe"] = round(last.mean() / last.std() * 252 ** .5, 2); r[f"{per}_dd"] = round((np.maximum.accumulate(eq) - eq).max())
        for k in (1, 2, 3):
            res = np.array([lucid_eval(P["day"], P["fav"], P["adv"], P["rel"], nd, s, k, 0.0, 400) for s in range(nd - 120)])
            ok = res[:, 0] == 1; done = res[:, 0] != 0
            r[f"{per}_L{k}_pass"] = round(100 * ok.sum() / max(done.sum(), 1), 1); r[f"{per}_L{k}_p21"] = round(100 * (ok & (res[:, 1] <= 21)).mean(), 1)
            r[f"{per}_L{k}_days"] = float(np.median(res[ok, 1])) if ok.any() else np.nan
        res = np.array([run_eval(P["day"], P["fav"], P["adv"], P["rel"], nd, s, 3000.0, 2000.0, 21, True, 1000.0, False, 2, 12, 1500.0, 3, 600.0) for s in range(nd - 21)])
        r[f"{per}_AE_pass"] = round(100 * (res[:, 0] == 1).mean(), 1); r[f"{per}_AE_bust"] = round(100 * (res[:, 0] == -1).mean(), 1)
        a = np.array([lucid_funded(P["day"], P["fav"], P["adv"], P["rel"], s, s + 252, 1, 5000.0, 600.0) for s in range(nd - 252)])
        r[f"{per}_LF_cash"] = round(a[:, 0].mean()); r[f"{per}_LF_bust"] = round(100 * (a[:, 2] == -1).mean(), 1)
        out = np.zeros((2000, 7))
        n = life_lucid(P["day"], P["fav"], P["adv"], P["rel"], nd, 252, 3, 3, 0.0, 1, 5000.0, 600.0, 105.2, out); s = summarize(out, n)
        r[f"{per}_LIFE_L"] = round(s["net_mo"]); r[f"{per}_LIFE_L_p10"] = round(s["p10_mo"])
    rows.append(r); print(nqp, gl, "done", flush=True)
R = pd.DataFrame(rows); R.to_csv("eval_combo.csv", index=False)
pd.set_option("display.width", 320); pd.set_option("display.max_columns", 200)
for blk in (["mo", "sharpe", "dd"], ["L1_pass", "L1_days", "L2_pass", "L2_days", "L3_pass", "L3_p21", "L3_days"], ["AE_pass", "AE_bust"], ["LF_cash", "LF_bust", "LIFE_L", "LIFE_L_p10"]):
    print(R[["nq", "oro"] + [f"{p}_{b}" for b in blk for p in PER]].to_string(index=False))
