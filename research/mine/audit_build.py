"""AUDIT step 1: trade sets of the CURRENT profiles (as coded in NQMaster.cs / GoldMaster.cs on 2026-10-08), 1 base contract.
  Ultra   = robust_trades Ultra (MaxPlus2 + confluence/context weights + VOLB 2R) with ICT -> corrected ICT x2 (ict_fix),
            VW13 wide (VW13 0.30 + VW13b 0.15 rows -> 2 lots at >= 0.30, as the code's DoubleDist), + LATE15, ENG10, LATEFH,
            + night NF05, LF06, LF0430. First-come conflict filter (no opposite positions).
  WR70N   = robust_trades WR70Plus with corrected ICT x2 + LATE15 + NF05 + LF06 + LF0430 (NightOnWr70 = true).
  GoldWR  = GoldMaster WinRate (OD1030, ENG0408, SVWAP22);  GoldRB = Robust (+ ASIA1R, ENG0206).
Periods IS (CFD 2020-02..2023), C24 (CFD 2024-26), REAL (MNQ / MGC futures 2024-02..2026-09). FOMC days skipped.
Fix applied: ict_fix_trades.pkl was built with $1.00 commission (ict.py COMM) -> charge the missing $0.90 per contract.
2015-19 regime test per module (cost-normalised: P&L in % of daily ATR, cost 0.345% ATR as today):
  old modules from ../variants_nqhd_long.pkl (pts + 2 ticks added back, as overnight.py), ICT re-run with ict_fix on nqhd_long,
  mined / night modules re-run with core.run_events(norm_cost=0.00345, slip=0). ORB90 / MSEQS: not available.
Output: audit_trades.pkl = {"prof": {prof: {per: (F, days)}}, "L1519": {mod: DataFrame(date, u, d)}, "days1519": array}"""
import os, sys, ast, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, run_events
from families_gold import gen_drive
from families2 import FAMILIES2
from families import FAMILIES
from families3 import FAMILIES3
from families4 import FAMILIES4
from gold_port import conflict_filter
from news import NEWS
import ict_fix
FOMC = set(NEWS["FOMC"]); COLS = ["date", "mod", "tin", "tout", "d", "u", "w"]
LO = {"IS": (20200201, 20240101), "C24": (20240101, 3e7), "REAL": (20240201, 3e7)}
T = pickle.load(open("robust_trades.pkl", "rb")); K = pd.read_pickle("ict_fix_trades.pkl"); GC = pickle.load(open("gold_curated_trades.pkl", "rb"))
# ------------------------------------------------------------------ module definitions (mined / night)
MINED = {"LATE15": (FAMILIES4["LATE_MOM"], FAMILIES4["LATE_MOM"][1][762]), "LATEFH": (FAMILIES4["LATE_MOM"], FAMILIES4["LATE_MOM"][1][1107]),
         "ENG10": (FAMILIES3["ENGULF_4H"], FAMILIES3["ENGULF_4H"][1][1172])}
NIGHT = {"NF05": dict(A=2000, T=540, x=0.35, mode=-1, tf=0, k=0.2, stop=0, R=2.0, hold=240),
         "LF06": dict(A=400, T=120, x=0.2, mode=-1, tf=0, k=0.2, stop=0, R=0.5, hold=240),
         "LF0430": dict(A=400, T=30, x=0.1, mode=-1, tf=1, k=0.35, stop=0, R=0.5, hold=240)}
OTHER = {"VOLB_U": (FAMILIES2["VOL_BREAK"], {'k': 0.45, 's': 0.35, 'R': 2.0, 'tf': 0, 'w1': 1500, 'hold': 400, 'stop': 0}),
         "VOLB_W": (FAMILIES2["VOL_BREAK"], {'k': 0.45, 's': 0.35, 'R': 0.5, 'tf': 1, 'w1': 1500, 'hold': 400, 'stop': 0}),
         "VW13a": (FAMILIES["CLOCK_ANCHOR"], {'anc': 'VWAP', 'T': 1300, 'x': 0.3, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}),
         "VW13b": (FAMILIES["CLOCK_ANCHOR"], {'anc': 'VWAP', 'T': 1300, 'x': 0.15, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120})}
def run(D, gen, p, md, nc=None):
    df = run_events(D, gen(D, p), flat=955, maxday=md, slip=0.0 if nc else 0.25, norm_cost=nc)
    if len(df): df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
    return df
def frame(df, name, per, w=1.0, ucol="usd"):
    lo, hi = LO[per]; df = df[(df.date >= lo) & (df.date < hi) & ~df.date.isin(FOMC)]
    return pd.DataFrame(dict(date=df.date.to_numpy(), mod=name, tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df[ucol].to_numpy(), w=w))
def ictf(per, w):
    df = K[("mnq_fut.npz" if per == "REAL" else "nq_1m.npz", "corregido", 1.0)].copy(); df["usd"] = df.usd - 0.9
    return frame(df, "ICT", per, w)
if __name__ == "__main__":
    Dn, Dr = Data("nq_1m.npz"), Data("mnq_fut.npz")
    NEW = {}
    for nm, ((gen, grid, md), p) in MINED.items():
        a, b = run(Dn, gen, p, md), run(Dr, gen, p, md); NEW[nm] = {"IS": frame(a, nm, "IS"), "C24": frame(a, nm, "C24"), "REAL": frame(b, nm, "REAL")}
    for nm, p in NIGHT.items():
        a, b = run(Dn, gen_drive, p, 1), run(Dr, gen_drive, p, 1); NEW[nm] = {"IS": frame(a, nm, "IS"), "C24": frame(a, nm, "C24"), "REAL": frame(b, nm, "REAL")}
    print({k: {p: len(v) for p, v in d.items()} for k, d in NEW.items()}, flush=True)
    PROF = {}
    for per in ("IS", "C24", "REAL"):
        days = np.array(T["Ultra"][per][1])
        U = T["Ultra"][per][0][COLS]; W = T["WR70Plus"][per][0][COLS]
        ul = pd.concat([U[U["mod"] != "ICT"], W[W["mod"] == "VW13b"].assign(mod="VW13"), ictf(per, 2.0)] + [NEW[m][per] for m in ("LATE15", "ENG10", "LATEFH", "NF05", "LF06", "LF0430")], ignore_index=True)
        ul = conflict_filter(ul.sort_values(["date", "tin"]).reset_index(drop=True)).reset_index(drop=True)
        wr = pd.concat([W[W["mod"] != "ICT"].replace({"mod": {"VOLB_tf1": "VOLB", "VW13b": "VW13"}}), ictf(per, 2.0)] + [NEW[m][per] for m in ("LATE15", "NF05", "LF06", "LF0430")], ignore_index=True)
        wr = conflict_filter(wr.sort_values(["date", "tin"]).reset_index(drop=True)).reset_index(drop=True)
        gw = conflict_filter(pd.concat([GC[m][per] for m in ("OD1030", "ENG0408", "SVWAP22")], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)).reset_index(drop=True)
        gr = conflict_filter(pd.concat([GC[m][per] for m in ("OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206")], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)).reset_index(drop=True)
        gw = gw[~gw.date.isin(FOMC) & gw.date.isin(days)]; gr = gr[~gr.date.isin(FOMC) & gr.date.isin(days)]
        for nm, F in (("Ultra", ul), ("WR70N", wr), ("GoldWR", gw), ("GoldRB", gr)):
            PROF.setdefault(nm, {})[per] = (F[COLS].reset_index(drop=True), days)
        PROF.setdefault("Ultra+GoldRB", {})[per] = (pd.concat([ul, gr.assign(mod="G:" + gr["mod"])], ignore_index=True)[COLS], days)
        PROF.setdefault("WR70N+GoldWR", {})[per] = (pd.concat([wr, gw.assign(mod="G:" + gw["mod"])], ignore_index=True)[COLS], days)
        for nm in PROF:
            F, dd = PROF[nm][per]; x = F.u * F.w; s = x.groupby(F.date).sum().reindex(dd, fill_value=0.0)
            print(per, nm, len(F), "tpd", round(len(F) / len(dd), 2), "WR", round(100 * (F.u > 0).mean(), 1), "PF", round(x[x > 0].sum() / -x[x <= 0].sum(), 3),
                  "Sh", round(s.mean() / s.std() * 252 ** .5, 2), "$/mo", round(s.mean() * 21), flush=True)
    # ------------------------------------------------------------------ 2015-19 cost-normalised (% of daily ATR)
    DL = Data("nqhd_long.npz"); atr_by_date = pd.Series(DL.atr, index=DL.daydate); atr_by_date = atr_by_date[atr_by_date.index > 0]
    atr_by_date = atr_by_date[~atr_by_date.index.duplicated()]
    def keep(df): return df[(df.date >= 20150201) & (df.date < 20200101) & ~df.date.isin(FOMC)]
    L = {}
    V = pd.read_pickle(os.path.join(RES, "variants_nqhd_long.pkl")); V = V[~V.fomc]
    for m, var in (("CRT11", 2.0), ("LON", 2.0), ("MOM1030", 0.3), ("MOM11", 0.3), ("MOM13", 1.0), ("MSEQ", 0.5), ("ON07", 1.0), ("ORB60", 0.6), ("ORB60_075", 0.75), ("REV06", 0.3)):
        g = keep(V[(V["mod"] == m.split("_")[0]) & (V["var"] == var)]).copy(); a = g.date.map(atr_by_date).to_numpy()
        g["u"] = ((g.usd + 1) / 2 + 0.5 - 0.00345 * a) / a * 100; L[m] = g[["date", "u", "d"]].reset_index(drop=True)
    z = dict(np.load(os.path.join(RES, "data", "nqhd_long.npz"))); Bi = ict_fix.bars(z, 5); Lv, at, tr = ict_fix.day_levels(z)
    di = ict_fix.run(Bi, Lv, at, tr, np.array([1] * 6, np.bool_), (570, 630), 4, 2, 1.0, 1, 0.25); di = keep(di).copy(); a = di.date.map(atr_by_date).to_numpy()
    di["u"] = (di.pts + 0.5 - 0.00345 * a) / a * 100; L["ICT"] = di[["date", "u", "d"]].reset_index(drop=True)
    for nm, ((gen, grid, md), p) in list(MINED.items()) + [(k, (v[0], v[1])) for k, v in OTHER.items()]:
        df = keep(run(DL, gen, p, md, nc=0.00345)); L[nm] = df.rename(columns={"usd": "u"})[["date", "u", "d"]].reset_index(drop=True)
    for nm, p in NIGHT.items():
        df = keep(run(DL, gen_drive, p, 1, nc=0.00345)); L[nm] = df.rename(columns={"usd": "u"})[["date", "u", "d"]].reset_index(drop=True)
    for m in ("OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206"):
        g = GC[m]["2015-19"]; L["G:" + m] = g.rename(columns={})[["date", "u", "d"]].reset_index(drop=True)      # gold: cost 0.96% ATR (gold_curated)
    rth = (DL.om >= 570) & (DL.om < 960); d1519 = np.unique(DL.date[rth]); d1519 = np.array([d for d in d1519 if 20150201 <= d < 20200101 and d not in FOMC])
    for m, g in L.items():
        u = g.u; print("2015-19", m, len(g), "WR", round(100 * (u > 0).mean(), 1), "PF", round(u[u > 0].sum() / -u[u <= 0].sum(), 3), flush=True)
    pickle.dump({"prof": PROF, "L1519": L, "days1519": d1519, "new": NEW}, open("audit_trades.pkl", "wb"))
    print("saved audit_trades.pkl")
