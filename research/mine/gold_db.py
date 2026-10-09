"""GoldMaster (Robust = OD1030 + ENG0408 + SVWAP22 + ASIA1R + ENG0206; WinRate = first three) on 16 years of REAL gold futures
(Databento GLBX.MDP3 ohlcv-1m GC.v.0 2010-06 -> 2026-10, back-adjusted, prices x2.5 -> research/data/mgcdb.npz).
Real view: $ per MGC ($1.90 + 1 tick), flat 16:50, FOMC skipped, conflict filter.  Norm view: cost 0.96% of daily ATR (today's
MGC cost/ATR ratio), P&L in % of ATR.  Per year and per block. -> gold_db.json"""
import os, sys, ast, json, numpy as np, pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, "..")
from core import Data, run_events
from run_mine import FAMILIES
from gold_port import conflict_filter
MODS = {   # copied from gold_curated.py (importing it would re-run its whole study and overwrite gold_curated_trades.pkl)
    "ENG0408": ("ENGULF_4H", "{'eng': '0408v0004@0930', 'ent': 2, 'R': 0.5, 'stop': 2, 'trend': 0, 'w1': 1500, 'body': 2}"),
    "SVWAP22": ("CLOCK_ANCHOR", "{'anc': 'SVWAP', 'T': 2200, 'x': 0.3, 'mode': -1, 's': 0.25, 'R': 0.5, 'tg': 0, 'tf': 0, 'hold': 120}"),
    "OD1030": ("OPEN_DRIVE", "{'T': 60, 'x': 0.3, 'stop': 0, 'R': 0.5, 'tf': 1, 'hold': 400}"),
    "ASIA1R": ("G_ORB", "{'A': 2000, 'T': 240, 'W': 360, 'cap': 0.6, 'R': 1.0, 'tf': 1, 'hold': 600}"),
    "ENG0206": ("ENGULF_4H", "{'eng': '0206v2202@0930', 'ent': 2, 'R': 0.5, 'stop': 2, 'trend': 0, 'w1': 1500, 'body': 2}"),
}
from db_long import FOMC_1019
from news import NEWS


def tr(D, fam, ps, norm=None):
    gen, grid, md = FAMILIES[fam]; p = ast.literal_eval(ps)
    df = run_events(D, gen(D, p), flat=1010, maxday=md, slip=0.0 if norm else 0.25, norm_cost=norm)
    df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
    return df[~df.date.isin(set(NEWS["FOMC"]) | set(FOMC_1019))]


def st(F, days, norm):
    x = F.u.to_numpy(); d = pd.Series(x, index=F.date.to_numpy()).groupby(level=0).sum().reindex(days, fill_value=0.0)
    w, l = x[x > 0].sum(), -x[x <= 0].sum()
    r = dict(trades=int(len(F)), wr=round(100 * float((x > 0).mean()), 1) if len(x) else None, pf=round(float(w / l), 2) if l > 0 else None,
             sharpe=round(float(d.mean() / d.std() * np.sqrt(252)), 2) if d.std() > 0 else None)
    if not norm: r["per_month"] = round(float(d.mean() * 21))
    return r


if __name__ == "__main__":
    D = Data("mgcdb.npz")
    days = np.array(sorted(set(D.daydate[D.daydate > 0]))); days = days[days >= 20100701]
    SETS = {"Robust": ["OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206"], "WinRate": ["OD1030", "ENG0408", "SVWAP22"]}
    OUT = {}
    for norm in (None, 0.0096):
        T = {}
        for nm in set(SETS["Robust"]):
            fam, ps = MODS[nm]; df = tr(D, fam, ps, norm)
            T[nm] = pd.DataFrame(dict(date=df.date.to_numpy(), mod=nm, tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df.usd.to_numpy(), w=1.0))
        for sname, mods in SETS.items():
            F = conflict_filter(pd.concat([T[m] for m in mods], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
            key = f"{sname} {'norm' if norm else 'real'}"; rec = {}
            for y in range(2010, 2027): rec[y] = st(F[F.date // 10000 == y], days[days // 10000 == y], norm)
            for lab, lo, hi in (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019), ("2020-2023", 2020, 2023), ("2024-2026", 2024, 2026)):
                rec[lab] = st(F[(F.date // 10000 >= lo) & (F.date // 10000 <= hi)], days[(days // 10000 >= lo) & (days // 10000 <= hi)], norm)
            OUT[key] = rec; print(key, {k: rec[k] for k in ("2010-2014", "2015-2019", "2020-2023", "2024-2026")}, flush=True)
    json.dump(OUT, open("gold_db.json", "w"), indent=1, default=float)
