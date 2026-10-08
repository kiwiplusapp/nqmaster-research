"""wrq_final: accepted changes - module before/after per period, portfolio per year, deflated Sharpe and portfolio-level PBO.
Accepted (see wrq_combo.py):
  Ultra    : BE (VOLB stop to entry + 0.1R after +0.75R) + ORBt (ORB60/ORB90 breakout trigger >= 0.1 ATR beyond the prior RTH
             close in the trade direction) + AGR (MOM1030 / MOM13 only when another NQ module is already open the same way)
  WR70Plus : ORBt + VTSO (VOLB_tf1: no entry after 10:47 ET)
-> wrq_final_modules.csv, wrq_final_years.csv, wrq_final_dsr.csv, wrq_final_pbo.csv"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_lib import SLIP, stats, dsr, pbo
from wrq_port import build_profile, module_trades, days_of
from wrq_agree import n_same
from wrq_combo import k_trig, k_tso

PERS = [("IS", SLIP), ("C24", SLIP), ("REAL", SLIP), ("L15", SLIP), ("REAL+4t", SLIP * 5), ("C24+4t", SLIP * 5)]

def row(lab, mod, ver, per, u):
    s = stats(u); s.update(change=lab, mod=mod, ver=ver, per=per); return s

if __name__ == "__main__":
    rows = []
    for per_t, slip in PERS:
        per = per_t.replace("+4t", "")
        a = module_trades(per, "VOLB", {}, slip); b = module_trades(per, "VOLB", dict(be=0.75, beo=0.1), slip)
        rows += [row("BE", "VOLB", "before", per_t, a.u), row("BE", "VOLB", "after", per_t, b.u)]
        for mod, rm in (("ORB60", 60), ("ORB90", 90)):
            a = module_trades(per, mod, {}, slip); b = module_trades(per, mod, {}, slip, k_trig(0.1, rm))
            rows += [row("ORBt", mod, "before", per_t, a.u), row("ORBt", mod, "after", per_t, b.u)]
            a = module_trades(per, mod, {"kt": 1.25} if mod == "ORB60" else {}, slip); b = module_trades(per, mod, {"kt": 1.25} if mod == "ORB60" else {}, slip, k_trig(0.1, rm))
            rows += [row("ORBt (WR70Plus exits)", mod, "before", per_t, a.u), row("ORBt (WR70Plus exits)", mod, "after", per_t, b.u)]
        a = module_trades(per, "VOLB_tf1", {}, slip); b = module_trades(per, "VOLB_tf1", {}, slip, k_tso(77))
        rows += [row("VTSO", "VOLB_tf1", "before", per_t, a.u), row("VTSO", "VOLB_tf1", "after", per_t, b.u)]
        X = n_same(build_profile(per, "Ultra", {"VOLB": (dict(be=0.75, beo=0.1), None)}, slip=slip, rules=False))
        for mod in ("MOM1030", "MOM13"):
            g = X[X["mod"] == mod]
            rows += [row("AGR", mod, "before", per_t, g.u), row("AGR", mod, "after", per_t, g.u[g.nsame >= 1])]
        print(per_t, flush=True)
    M = pd.DataFrame(rows); M.to_csv("wrq_final_modules.csv", index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_rows", 200)
    M["s"] = M.apply(lambda r: f"{r.n:d} {r.wr:.1f}% {r.pf:.2f} {r.exp:+.1f}", axis=1)
    print(M.pivot_table(index=["change", "mod", "ver"], columns="per", values="s", aggfunc="first", sort=False)[[p for p, _ in PERS]].to_string())
    # ------------- portfolio per year, DSR, PBO (daily series from wrq_combo.py)
    DL = pickle.load(open("wrq_combo_daily.pkl", "rb"))
    FINAL = {"Ultra": "BE + ORBt + AGR", "WR70Plus": "ORBt + VTSO"}
    yrows = []
    for prof, fin in FINAL.items():
        for per in ("L15", "IS", "C24", "REAL"):
            for ver in ("base", fin):
                d = DL[(prof, ver, per)]
                for y, g in d.groupby(d.index // 10000):
                    yrows.append(dict(prof=prof, per=per, year=y, ver="final" if ver == fin else "base", sharpe=g.mean() / g.std() * 252 ** .5, mo=g.mean() * 21))
    Y = pd.DataFrame(yrows); Y.to_csv("wrq_final_years.csv", index=False)
    print(Y.pivot_table(index=["prof", "per", "year"], columns="ver", values=["sharpe", "mo"]).round(2).to_string())
    drows = []
    for prof, fin in FINAL.items():
        for ver in ("base", fin):
            for smp, pers in (("CFD 2020-26", ("IS", "C24")), ("REAL 2024-26", ("REAL",))):
                d = np.concatenate([DL[(prof, ver, p)].to_numpy() for p in pers])
                r = dict(prof=prof, ver=ver, sample=smp, days=len(d), sharpe=round(d.mean() / d.std() * 252 ** .5, 3))
                for N in (10, 100, 3000, 10000, 300000):
                    p, sr0 = dsr(d, N); r[f"DSR N={N}"] = round(p, 4); r[f"SR0 N={N}"] = round(sr0, 2)
                drows.append(r)
    DS = pd.DataFrame(drows); DS.to_csv("wrq_final_dsr.csv", index=False); print(DS.to_string())
    prow = []
    for prof in FINAL:
        cands = sorted({k[1] for k in DL if k[0] == prof})
        for smp, pers in (("CFD 2020-26", ("IS", "C24")), ("REAL 2024-26", ("REAL",))):
            Mx = pd.DataFrame({c: pd.concat([DL[(prof, c, p)] for p in pers]) for c in cands}).fillna(0.0)
            r = pbo(Mx.to_numpy()); r.update(prof=prof, sample=smp, cands=", ".join(cands)); prow.append(r)
    PB = pd.DataFrame(prow); PB.to_csv("wrq_final_pbo.csv", index=False); print(PB.drop(columns="cands").to_string())
