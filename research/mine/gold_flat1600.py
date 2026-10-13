"""Audit C1 (2026-10-12): GoldMaster now flattens at 16:00 ET (MFFU auto-close 16:10, Lucid 16:45) instead of 16:50.
Same research engine as gold_curated.py (MGC $4/pt, $1.90 RT, 1 tick per side, FOMC skipped, conflict filter), flat 16:50 vs 16:00,
profiles WinRate (OD1030 + ENG0408 + SVWAP22) and Robust (+ ASIA1R + ENG0206). -> gold_flat1600.json"""
import os, sys, ast, json, numpy as np, pandas as pd
sys.path.insert(0, ".")
from core import Data, run_events
from run_mine import FAMILIES
from gold_port import conflict_filter, metrics, DAYS, FOMC
MODS = {
    "ENG0408": ("ENGULF_4H", "{'eng': '0408v0004@0930', 'ent': 2, 'R': 0.5, 'stop': 2, 'trend': 0, 'w1': 1500, 'body': 2}"),
    "SVWAP22": ("CLOCK_ANCHOR", "{'anc': 'SVWAP', 'T': 2200, 'x': 0.3, 'mode': -1, 's': 0.25, 'R': 0.5, 'tg': 0, 'tf': 0, 'hold': 120}"),
    "OD1030": ("OPEN_DRIVE", "{'T': 60, 'x': 0.3, 'stop': 0, 'R': 0.5, 'tf': 1, 'hold': 400}"),
    "ASIA1R": ("G_ORB", "{'A': 2000, 'T': 240, 'W': 360, 'cap': 0.6, 'R': 1.0, 'tf': 1, 'hold': 600}"),
    "ENG0206": ("ENGULF_4H", "{'eng': '0206v2202@0930', 'ent': 2, 'R': 0.5, 'stop': 2, 'trend': 0, 'w1': 1500, 'body': 2}"),
}
PROF = {"WinRate": ["OD1030", "ENG0408", "SVWAP22"], "Robust": ["OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206"]}
if __name__ == "__main__":
    DL, DM = Data("xau_long.npz"), Data("mgc_fut.npz")
    def tr(D, fam, ps, flat):
        gen, grid, md = FAMILIES[fam]; p = ast.literal_eval(ps)
        df = run_events(D, gen(D, p), flat=flat, maxday=md, slip=0.25)
        df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
        return df[~df.date.isin(FOMC)]
    def frame(df, name, lo, hi):
        df = df[(df.date >= lo) & (df.date < hi)]
        return pd.DataFrame(dict(date=df.date.to_numpy(), mod=name, tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df.usd.to_numpy(), w=1.0))
    OUT = {}
    for flat, lab in ((1010, "flat 16:50 (old)"), (960, "flat 16:00 (new)")):
        T = {}
        for nm, (fam, ps) in MODS.items():
            a = tr(DL, fam, ps, flat); b = tr(DM, fam, ps, flat)
            T[nm] = {"IS": frame(a, nm, 20200201, 20240101), "C24": frame(a, nm, 20240101, 30000000), "REAL": frame(b, nm, 20240201, 30000000)}
        for pn, mods in PROF.items():
            r = {}
            for per in ("IS", "C24", "REAL"):
                F = conflict_filter(pd.concat([T[m][per] for m in mods], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
                m = metrics(F, DAYS[per]); r[per] = {k: m[k] for k in ("tpd", "wr", "pf", "sharpe", "mo", "maxdd")}
            OUT[f"{pn} | {lab}"] = r; print(pn, lab, json.dumps(r), flush=True)
    json.dump(OUT, open("gold_flat1600.json", "w"), indent=1, default=float)
