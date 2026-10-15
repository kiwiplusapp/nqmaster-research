"""2026-10-14 'CPI method': can the US CPI release (08:30 ET, ~12 days a year) be traded robustly on NQ?
Real Databento NQ 1-minute 2010-06..2026-10 (nqdb.npz). CPI calendar: news.NEWS (2020-26) + news_hist.CPI_1019 (BLS archive).
Families (generators reused from families_gold.py, CPI days only):
  CPI_DRIVE : move from the 08:30 bar open to 08:30+T (T = 1..60 min, i.e. entry 08:31..09:30) >= x ATR -> continuation (mode 1) or
              fade (-1), market entry, stop k ATR or beyond the post-release extreme (capped), target R, hold limit
  CPI_ORB   : range 08:30..08:30+T, first breakout within W minutes (stop entry), stop at the other side capped, target R
  OPEN_DRIVE on CPI days: anchor 09:30 (first RTH minutes) for comparison
Costs: real $ per MNQ ($1.90 + 1 tick per side; STRESS = 4 ticks per side) for T1 2020-23 / T2 2024-26; cost-normalised (0.345% ATR)
for A 2010-14 / B 2015-19. Protocol fixed before looking: chosen on T1 only (n >= 25, PF >= 1.3); must hold T2 PF >= 1.2 (real and
stress), A and B PF >= 1.0. Same families on NON-news days are reported as the control. -> cpi_lab.csv, cpi_lab.json"""
import os, sys, json, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import Data, run_events
from families import grid
from families_gold import gen_drive, gen_orb
from news import NEWS
from news_hist import CPI_ALL, NFP_ALL
from db_long import FOMC_1019
NORM = 0.00345
PARTS = (("A", 20100601, 20150101, "n"), ("B", 20150101, 20200101, "n"), ("T1", 20200101, 20240101, "r"), ("T2", 20240101, 20991231, "r"))
G_DRV = grid(A=(830,), T=(1, 2, 5, 10, 15, 30, 60), x=(0.0, 0.05, 0.1, 0.2), mode=(1, -1), tf=(0, 1), k=(0.1, 0.2, 0.35), stop=(0, 1), R=(0.5, 1.0, 2.0), hold=(60, 240))
G_ORB = grid(A=(830,), T=(1, 5, 15, 30, 60), W=(30, 90), cap=(0.15, 0.25, 0.4), R=(0.5, 1.0, 2.0), tf=(0, 1), hold=(60, 240))
G_OPEN = grid(A=(930,), T=(5, 15, 30, 60), x=(0.05, 0.1, 0.2), mode=(1, -1), tf=(0, 1), k=(0.2, 0.35), stop=(0, 1), R=(0.5, 1.0, 2.0), hold=(240,))


def keep_days(ev, D, days):
    if len(ev["i"]) == 0: return ev
    m = np.isin(D.date[ev["i"]], list(days))
    return {k: v[m] for k, v in ev.items()}


def st(df, lo, hi):
    u = df.usd[(df.date >= lo) & (df.date < hi)].to_numpy(); l = -u[u <= 0].sum()
    return len(u), (round(100 * (u > 0).mean(), 1) if len(u) else np.nan), (round(u[u > 0].sum() / l, 3) if l > 0 and len(u) >= 10 else np.nan), (round(float(u.sum()), 1) if len(u) else 0.0)


if __name__ == "__main__":
    D = Data("nqdb.npz")
    cpi = set(CPI_ALL); news = cpi | set(NFP_ALL) | set(NEWS["FOMC"]) | set(FOMC_1019)
    alld = set(D.daydate[D.daydate > 0]); ctrl = alld - news
    rows = []
    for fam, gen, G in (("CPI_DRIVE", gen_drive, G_DRV), ("CPI_ORB", gen_orb, G_ORB), ("OPEN_DRIVE", gen_drive, G_OPEN)):
        for j, p in enumerate(G):
            ev = gen(D, p)
            for tag, days in (("cpi", cpi), ("ctrl", ctrl)):
                e = keep_days(ev, D, days); row = dict(fam=fam, j=j, days=tag, params=repr(p))
                r = run_events(D, e, flat=955, maxday=1, slip=0.25); s = run_events(D, e, flat=955, maxday=1, slip=1.0)
                nm = run_events(D, e, flat=955, maxday=1, slip=0.0, norm_cost=NORM)
                for lab, lo, hi, kind in PARTS:
                    n, wr, pf, net = st(nm if kind == "n" else r, lo, hi)
                    row.update({f"{lab}_n": n, f"{lab}_wr": wr, f"{lab}_pf": pf, f"{lab}_net": net})
                    if kind == "r": row[f"{lab}_pf_stress"] = st(s, lo, hi)[2]
                rows.append(row)
        print(fam, len(G), flush=True)
    R = pd.DataFrame(rows); R.to_csv("cpi_lab.csv", index=False)
    C = R[R.days == "cpi"]
    sel = C[(C.T1_n >= 25) & (C.T1_pf >= 1.3)]
    ok = sel[(sel.T2_pf >= 1.2) & (sel.T2_pf_stress >= 1.2) & (sel.A_pf >= 1.0) & (sel.B_pf >= 1.0)]
    out = dict(configs=int(len(C)), median_pf={lab: float(C[f"{lab}_pf"].median()) for lab, *_ in PARTS},
               median_pf_ctrl={lab: float(R[R.days == 'ctrl'][f"{lab}_pf"].median()) for lab, *_ in PARTS},
               t1_pass=int(len(sel)), all_pass=int(len(ok)), base_rate_t2=float((C.T2_pf >= 1.2).mean()),
               t2_given_t1=float((sel.T2_pf >= 1.2).mean()) if len(sel) else None,
               survivors=ok.sort_values("T1_pf", ascending=False).head(30).to_dict("records"))
    json.dump(out, open("cpi_lab.json", "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in out.items() if k != "survivors"}, indent=1))
    pd.set_option("display.width", 250)
    if len(ok): print(ok.sort_values("T1_pf", ascending=False).head(30)[["fam", "params", "A_n", "A_pf", "B_pf", "T1_n", "T1_wr", "T1_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf_stress"]].to_string())
