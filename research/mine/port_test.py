"""Marginal portfolio test: MaxPlus (+confluence A+B, ICT x2) + candidate module(s), first-come conflict filter (no opposite
positions), per period IS (CFD 2020-23) / C24 (CFD 2024-26) / REAL (MNQ 2024-26). Costs: $1.90 RT, 1-tick slippage."""
import os, sys, pickle, numpy as np, pandas as pd
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, RES)
cwd = os.getcwd(); os.chdir(RES)
exec(open(os.path.join(RES, "conflict.py")).read().split("for tag, lo, split")[0])
T = pickle.load(open(os.path.join(RES, "feat_trades2.pkl"), "rb"))
os.chdir(cwd)
from news import NEWS
def base(per):
    F, days = T[per]; F = F.copy()
    F["w"] = F.base_w * np.where(F.rev_bucket, 2.0, 1.0) * np.where((F["mod"] == "REV06") & F.lon_same, 0.0, 1.0)
    return F[F.w > 0][["date", "mod", "tin", "tout", "d", "u", "w"]], np.array(days)
def cand_trades(tr, per, name, w=1.0):
    df = tr["mnq" if per == "REAL" else "nq"].copy()
    if per == "IS": df = df[(df.date >= 20200201) & (df.date < 20240101)]
    elif per == "C24": df = df[df.date >= 20240101]
    else: df = df[df.date >= 20240201]
    df = df[~df.date.isin(NEWS["FOMC"])]
    return pd.DataFrame(dict(date=df.date, mod=name, tin=df.tin, tout=df.tout, d=df.d, u=df.usd, w=w))
def metrics(F, days):
    x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0); eq = d.cumsum()
    return dict(n=len(F), tpd=round(len(F) / len(days), 2), wr=round(100 * (F.u > 0).mean(), 2), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3),
                sharpe=round(d.mean() / d.std() * np.sqrt(252), 2), mo=round(d.mean() * 21), maxdd=round((eq.cummax() - eq).max()))
def combine(per, cands):
    B, days = base(per)
    if not cands: return metrics(B, days)
    A = pd.concat([B] + [cand_trades(tr, per, nm, w) for nm, tr, w in cands], ignore_index=True)
    A = conflict_filter(A.sort_values(["date", "tin"]).reset_index(drop=True))
    return metrics(A, days)
if __name__ == "__main__":
    R = pd.read_csv("results_all.csv"); TR = pickle.load(open("trades_all.pkl", "rb"))
    picks = [("CLOCK_ANCHOR", "{'anc': 'SOPEN', 'T': 800, 'x': 0.35, 'mode': 1, 's': 0.25, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 330}"),
             ("CLOCK_ANCHOR", "{'anc': 'VWAP', 'T': 1300, 'x': 0.15, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}"),
             ("CLOCK_ANCHOR", "{'anc': 'VWAP', 'T': 1300, 'x': 0.15, 'mode': 1, 's': 0.25, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}"),
             ("HOD_RETEST", "{'w0': 1030, 'w1': 1400, 'bk': 0.02, 's': 0.2, 'R': 0.5, 'tf': 1, 'exp': 90, 'hold': 240}"),
             ("OPEN_DRIVE", "{'T': 60, 'x': 0.3, 'stop': 1, 'R': 0.5, 'tf': 1, 'hold': 400}"),
             ("OPEN_DRIVE", "{'T': 60, 'x': 0.3, 'stop': 1, 'R': 1.0, 'tf': 1, 'hold': 400}"),
             ("VWAP_PULLBACK", "{'w0': 1100, 'w1': 1300, 'x': 0.15, 's': 0.2, 'R': 2.0, 'tf': 0, 'exp': 60, 'hold': 240, 'off': 0.0}"),
             ("CLOCK_ANCHOR", "{'anc': 'PDC', 'T': 1100, 'x': 0.2, 'mode': 1, 's': 0.25, 'R': 1.0, 'tg': 1, 'tf': 1, 'hold': 240}")]
    rows = []
    for per in ("IS", "C24", "REAL"):
        r = combine(per, []); r.update(per=per, cand="BASE MaxPlus+conf"); rows.append(r)
        for fam, ps in picks:
            j = int(R[(R.fam == fam) & (R.params == ps)].j.iloc[0]); tr = TR[(fam, j)]
            r = combine(per, [(fam, tr, 1.0)]); r.update(per=per, cand=f"{fam} {ps[:70]}"); rows.append(r)
    g = pd.DataFrame(rows); pd.set_option("display.width", 250)
    for c in ("wr", "pf", "sharpe", "mo", "tpd"):
        print(c); print(g.pivot(index="cand", columns="per", values=c)[["IS", "C24", "REAL"]].to_string())
