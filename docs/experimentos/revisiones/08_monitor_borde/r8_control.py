"""r8: (1) re-run exp08 control with current lists, (2) re-run os_adapt.py's own run() with the 13-oct cand16 list -> does it reproduce os_adapt.json?"""
import os, sys, json, pickle, numpy as np, pandas as pd
M = "/home/user/nqmaster-research/research/mine"; sys.path.insert(0, M); sys.path.insert(0, os.path.dirname(M)); os.chdir(M)
SP = "/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad"
import exp08_monitor as E
import os_adapt as O
from wrq_lib import getD
from news import NEWS
ref = json.load(open("os_adapt.json"))
PER = E.PER

def build_osadapt(cpath):
    C = pickle.load(open(cpath, "rb")); Q = pickle.load(open("ultraq_trades.pkl", "rb"))["UltraQ"]
    R, N = C["UltraR"]; R = pd.concat([R, Q[0][Q[0]["mod"] == "CPI09"]], ignore_index=True); N = pd.concat([N, Q[1][Q[1]["mod"] == "CPI09"]], ignore_index=True)
    for X in (R, N): X["x"] = X.u * X.w
    D = getD("nqdb.npz")
    days = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); days = days[(days >= 20100701) & ~np.isin(days, list(NEWS["FOMC"]))]
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(days).to_numpy()
    mods = sorted(set(N["mod"]) | set(R["mod"]))
    Mn = N.pivot_table(index="date", columns="mod", values="x", aggfunc="sum").reindex(index=days, columns=mods, fill_value=0.0).fillna(0.0)
    Mr = R.pivot_table(index="date", columns="mod", values="x", aggfunc="sum").reindex(index=days, columns=mods, fill_value=0.0).fillna(0.0)
    Mmix = Mn.copy(); Mmix.loc[days >= 20200101] = Mr.loc[days >= 20200101]
    return days, atr, mods, Mmix, N, R

res = {}
for tag, cp in (("actual(27-oct)", "cand16_trades.pkl"), ("13-oct", f"{SP}/old/cand16_trades_1013.pkl"), ("27-oct 01:23", f"{SP}/old/cand16_trades_1027a.pkl")):
    days, atr, mods, Mmix, N, R = build_osadapt(cp)
    for pol, L in (("A", 0), ("W", 252), ("P", 252), ("D", 252)):
        x, al, off = O.run(Mmix, Mmix, atr, days, mods, N, pol, L)
        key = pol + (str(L) if L else "")
        rec = {q: O.stats(x[(days >= lo) & (days < hi)]) for q, (lo, hi) in PER.items()}
        r = ref[key]
        print(f"[{tag}] os_adapt.run {key}: alarms {al} (json {r['alarms']}) | " + " | ".join(f"{q}: {rec[q]['net']} Sh {rec[q]['sharpe']} (json {r[q]['net']} Sh {r[q]['sharpe']})" for q in PER))
    # exp08.run on same inputs (zmode os_adapt, old k/h)
    post = days >= 20200101
    for pol in ("A", "W252"):
        x, al, wa, off, half = E.run(days, atr, mods, Mmix.to_numpy(), N, post, pol, 0.0758, 18.57, 1e18, zmode="os_adapt")
        rec = {q: O.stats(x[(days >= lo) & (days < hi)]) for q, (lo, hi) in PER.items()}
        print(f"[{tag}] exp08.run control {pol}: alarms {len(al)} {al} | " + " | ".join(f"{q}: {rec[q]['net']} Sh {rec[q]['sharpe']}" for q in PER))
    # module diffs
    if tag != "actual(27-oct)":
        C0 = pickle.load(open(cp, "rb"))["UltraR"]; C1 = pickle.load(open("cand16_trades.pkl", "rb"))["UltraR"]
        for i, era in ((1, "norm"), (0, "real")):
            a = (C0[i].u * C0[i].w).groupby(C0[i]["mod"]).agg(["size", "sum"]); b = (C1[i].u * C1[i].w).groupby(C1[i]["mod"]).agg(["size", "sum"])
            d = a.join(b, lsuffix="_old", rsuffix="_new", how="outer"); d["dsum"] = d.sum_new - d.sum_old
            print(f"   {era}: per-module old->new (only changed):"); print(d[(d.dsum.abs() > 1) | (d.size_old != d.size_new)].round(0).to_string())
            wa = C0[i].groupby("mod").w.mean(); wb = C1[i].groupby("mod").w.mean(); print("   mean w old/new differs:", {m: (round(wa[m],2), round(wb[m],2)) for m in wa.index if m in wb.index and abs(wa[m]-wb[m])>1e-9})
