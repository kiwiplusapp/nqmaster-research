"""2026-10-14 Ultra per-trade win rate / profit factor levers, screened on 4 periods (A 2010-14 and B 2015-19 cost-normalised, T1 2020-23
and T2 2024-26 real $ per MNQ) on the UltraR trade lists of cand16.py. Pre-registered levers (list fixed before looking at results):
drop REV06 / ON07 / VW13b (2nd VW13 lot) / MOM11 / LON / ICT, CPI-morning skip (no entries before 10:00 ET on CPI days), CPI-day skip,
NFP-morning skip, + CPI09 module (cpi_lab.py: at 09:30 fade the 08:30->09:29 move if >= 0.05 ATR, stop 0.35 ATR, 0.5R, 60 min).
Pass = WR and PF both up (>= 0) in all four periods. Screen only: removals ignore conflict-filter interactions (rebuilt later). -> ultra_q2.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import Data, run_events
from families_gold import gen_drive
from news_hist import CPI_ALL, NFP_ALL
from cpi_lab import keep_days, NORM
PER = (("A", 20100601, 20150101, 1), ("B", 20150101, 20200101, 1), ("T1", 20200101, 20240101, 0), ("T2", 20240101, 20991231, 0))
CPI09 = dict(A=830, T=60, x=0.05, mode=-1, tf=0, k=0.35, stop=0, R=0.5, hold=60)


def cpi09_trades(D):
    ev = keep_days(gen_drive(D, CPI09), D, set(CPI_ALL)); out = []
    for norm in (0, 1):
        df = run_events(D, ev, flat=955, maxday=1, slip=0.0 if norm else 0.25, norm_cost=NORM if norm else None)
        out.append(pd.DataFrame(dict(date=df.date, mod="CPI09", tin=D.sm[df.fi.to_numpy().astype(int)], tout=D.sm[df.xi.to_numpy().astype(int)] + 1,
                                     d=df.d, u=df.usd, w=1.0)))
    return out


def stats(X, lo, hi):
    s = X[(X.date >= lo) & (X.date < hi)]; x = s.u * s.w
    d = x.groupby(s.date).sum()
    return dict(n=len(s), wr=100 * float((s.u > 0).mean()), pf=float(x[x > 0].sum() / -x[x <= 0].sum()), net=float(x.sum()), sh=float(d.mean() / d.std() * np.sqrt(252)))


if __name__ == "__main__":
    R, N = pickle.load(open("cand16_trades.pkl", "rb"))["UltraR"]
    cr, cn = cpi09_trades(Data("nqdb.npz"))
    cpi = set(CPI_ALL); nfp = set(NFP_ALL); et = lambda X: (X.tin + 1080) % 1440
    LEV = {"base": lambda X: X,
           "-REV06": lambda X: X[X["mod"] != "REV06"], "-ON07": lambda X: X[X["mod"] != "ON07"], "-VW13b": lambda X: X[X["mod"] != "VW13b"],
           "-MOM11": lambda X: X[X["mod"] != "MOM11"], "-LON": lambda X: X[X["mod"] != "LON"], "-ICT": lambda X: X[X["mod"] != "ICT"],
           "CPI morning skip": lambda X: X[~(X.date.isin(cpi) & (et(X) < 600))], "CPI day skip": lambda X: X[~X.date.isin(cpi)],
           "NFP morning skip": lambda X: X[~(X.date.isin(nfp) & (et(X) < 600))]}
    out = {}
    for name, f in list(LEV.items()) + [("+CPI09", None)]:
        rec = {}
        for lab, lo, hi, norm in PER:
            X = N if norm else R
            Y = pd.concat([X, cn if norm else cr], ignore_index=True) if f is None else f(X)
            rec[lab] = stats(Y, lo, hi)
        out[name] = rec
    base = out["base"]; rows = []
    for name, rec in out.items():
        dwr = {k: rec[k]["wr"] - base[k]["wr"] for k in rec}; dpf = {k: rec[k]["pf"] - base[k]["pf"] for k in rec}
        rows.append(dict(lever=name, **{f"{k}_wr": round(rec[k]["wr"], 2) for k in rec}, **{f"{k}_pf": round(rec[k]["pf"], 3) for k in rec},
                         **{f"d{k}_sh": round(rec[k]["sh"] - base[k]["sh"], 2) for k in rec}, net_T2_pct=round(100 * (rec["T2"]["net"] / base["T2"]["net"] - 1), 1),
                         passes=all(v >= 0 for v in dwr.values()) and all(v >= 0 for v in dpf.values()), pf_up_all=all(v > 0 for v in dpf.values())))
    T = pd.DataFrame(rows); pd.set_option("display.width", 260); print(T.to_string(index=False))
    json.dump(dict(table=T.to_dict("records"), raw=out), open("ultra_q2.json", "w"), indent=1)
