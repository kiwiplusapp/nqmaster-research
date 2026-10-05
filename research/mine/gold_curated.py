"""All subsets (size 1-6) of the strongest gold modules. Real $ costs (MGC: $4/pt, $1.90 RT, 1 tick per side), flat 16:50,
FOMC skipped, conflict filter (no opposite positions). Periods: IS = CFD 2020-23, C24 = CFD 2024-26, REAL = MGC 2024-26,
plus 2010-14 / 2015-19 cost-normalised to today's cost/ATR ratio (0.96% ATR)."""
import os, sys, ast, itertools, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from core import Data, run_events
from run_mine import FAMILIES
from gold_port import conflict_filter, metrics, DAYS, FOMC, days_of
MODS = {
    "ENG0408": ("ENGULF_4H", "{'eng': '0408v0004@0930', 'ent': 2, 'R': 0.5, 'stop': 2, 'trend': 0, 'w1': 1500, 'body': 2}"),
    "DRIVE11": ("G_DRIVE", "{'A': 930, 'T': 90, 'x': 0.2, 'mode': 1, 'tf': 1, 'k': 0.35, 'stop': 0, 'R': 0.5, 'hold': 600}"),
    "SVWAP22": ("CLOCK_ANCHOR", "{'anc': 'SVWAP', 'T': 2200, 'x': 0.3, 'mode': -1, 's': 0.25, 'R': 0.5, 'tg': 0, 'tf': 0, 'hold': 120}"),
    "OD1030": ("OPEN_DRIVE", "{'T': 60, 'x': 0.3, 'stop': 0, 'R': 0.5, 'tf': 1, 'hold': 400}"),
    "ASIA1R": ("G_ORB", "{'A': 2000, 'T': 240, 'W': 360, 'cap': 0.6, 'R': 1.0, 'tf': 1, 'hold': 600}"),
    "ASIA05": ("G_ORB", "{'A': 2000, 'T': 240, 'W': 360, 'cap': 0.6, 'R': 0.5, 'tf': 1, 'hold': 600}"),
    "LATE1430": ("LATE_MOM", "{'T': 1430, 'sig': 'DAY', 'x': 0.5, 'tf': 1, 'k': 1.0, 'R': 1.0}"),
    "ENG0206": ("ENGULF_4H", "{'eng': '0206v2202@0930', 'ent': 2, 'R': 0.5, 'stop': 2, 'trend': 0, 'w1': 1500, 'body': 2}"),
    "ENG0610": ("ENGULF_4H", "{'eng': '0610v0206@1000', 'ent': 2, 'R': 0.5, 'stop': 1, 'trend': 0, 'w1': 1500, 'body': 0}"),
}
DL, DM = Data("xau_long.npz"), Data("mgc_fut.npz")
def tr(D, fam, ps, norm=None):
    gen, grid, md = FAMILIES[fam]; p = ast.literal_eval(ps)
    df = run_events(D, gen(D, p), flat=1010, maxday=md, slip=0.0 if norm else 0.25, norm_cost=norm)
    df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
    return df[~df.date.isin(FOMC)]
def frame(df, name, lo, hi):
    df = df[(df.date >= lo) & (df.date < hi)]
    return pd.DataFrame(dict(date=df.date.to_numpy(), mod=name, tin=df.tin.to_numpy(), tout=df.tout.to_numpy(), d=df.d.to_numpy(), u=df.usd.to_numpy(), w=1.0))
T = {}
for nm, (fam, ps) in MODS.items():
    a = tr(DL, fam, ps); b = tr(DM, fam, ps); c = tr(DL, fam, ps, norm=0.0096)
    T[nm] = {"IS": frame(a, nm, 20200201, 20240101), "C24": frame(a, nm, 20240101, 30000000), "REAL": frame(b, nm, 20240201, 30000000),
             "2010-14": frame(c, nm, 20100201, 20150101), "2015-19": frame(c, nm, 20150101, 20200101)}
    print(nm, {p: (len(f), round(100 * (f.u > 0).mean(), 1), round(f.u[f.u > 0].sum() / -f.u[f.u <= 0].sum(), 2)) for p, f in T[nm].items()}, flush=True)
pickle.dump(T, open("gold_curated_trades.pkl", "wb"))
def pfwr(F): x = F.u; return round(float(x[x > 0].sum() / -x[x <= 0].sum()), 3), round(100 * float((x > 0).mean()), 1)
rows = []
names = list(MODS)
for r in range(1, 7):
    for sub in itertools.combinations(names, r):
        if "ASIA1R" in sub and "ASIA05" in sub: continue
        row = dict(mods="+".join(sub), k=len(sub))
        for per in ("IS", "C24", "REAL"):
            F = conflict_filter(pd.concat([T[m][per] for m in sub], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
            m = metrics(F, DAYS[per]); row.update({f"{per}_{k}": m[k] for k in ("tpd", "wr", "pf", "sharpe", "mo", "maxdd")})
        for per in ("2010-14", "2015-19"):
            F = conflict_filter(pd.concat([T[m][per] for m in sub], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
            row[f"{per}_pf"], row[f"{per}_wr"] = pfwr(F)
        rows.append(row)
G = pd.DataFrame(rows); G.to_csv("gold_curated.csv", index=False)
G["minpf"] = G[["IS_pf", "C24_pf", "REAL_pf"]].min(axis=1); G["minwr"] = G[["IS_wr", "C24_wr", "REAL_wr"]].min(axis=1)
pd.set_option("display.width", 320); pd.set_option("display.max_rows", 200)
cols = ["mods", "IS_tpd", "IS_wr", "IS_pf", "IS_sharpe", "C24_wr", "C24_pf", "REAL_tpd", "REAL_wr", "REAL_pf", "REAL_sharpe", "REAL_mo", "REAL_maxdd", "2010-14_pf", "2015-19_pf", "2015-19_wr"]
print("\n== WR >= 66% and PF >= 1.4 in IS, C24 and REAL"); print(G[(G.minwr >= 66) & (G.minpf >= 1.4)].sort_values("REAL_tpd", ascending=False)[cols].head(40).to_string(index=False))
print("\n== best min-PF with WR >= 64% everywhere and >= 0.5 trades/day"); print(G[(G.minwr >= 64) & (G.REAL_tpd >= 0.5)].sort_values("minpf", ascending=False)[cols].head(25).to_string(index=False))
print("\n== 16-year robust (2010-14 and 2015-19 PF >= 1.05)"); print(G[(G["2010-14_pf"] >= 1.05) & (G["2015-19_pf"] >= 1.05)].sort_values("minpf", ascending=False)[cols].head(25).to_string(index=False))
