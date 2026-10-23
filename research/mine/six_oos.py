"""2026-10-19 'que funcione en 2026-2027': out-of-sample check of the six-year modules (chosen on 2020-10..2023, gated on 2024-26) on
2010-2019 real NQ futures cost-normalised (0.345% of ATR per trade, P&L in % of ATR; data never used to choose them).
Per module: PF in A 2010-14 / B 2015-19 (norm) and T1 / T2 (real). Portfolio (Ultra as coded, MOM1030 x4; norm view for 2010-19,
real $ for 2020-26; opposite-position conflicts removed): Ultra vs + all six-year modules + LATEFH vs + the 'durable' subset
(rule fixed before looking at the portfolio: A PF >= 1.0 and B PF >= 1.05 -> ORFAIL, CAM3, SO04, RV11). -> six_oos.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from wrq_port import conflict_filter
from wrq_lib import getD
NEW = {"CA04V": ("CLOCK_ANCHOR", 916), "SO04": ("CLOCK_ANCHOR", 1527), "GD03": ("G_DRIVE", 3922), "RV11": ("RVOL_DRIVE", 4226),
       "ENG26": ("ENGULF_4H", 25), "ORFAIL": ("OR_FAIL", 142), "CAM3": ("PIVOT_FADE", 365)}
BLOCKS = (("A 2010-14", 20100101, 20150101), ("B 2015-19", 20150101, 20200101), ("T1 2020-23", 20200101, 20240101), ("T2 2024-26", 20240101, 20991231))


def stats(T, lo, hi, days):
    T = T[(T.date >= lo) & (T.date < hi)]; dd = days[(days >= lo) & (days < hi)]
    x = (T.u * T.w).to_numpy(); d = pd.Series(x, index=T.date.to_numpy()).groupby(level=0).sum().reindex(dd, fill_value=0.0)
    w = x[x > 0].sum(); l = -x[x <= 0].sum(); eq = d.cumsum()
    return dict(n=int(len(T)), wr=round(100 * float((T.u > 0).mean()), 1) if len(T) else None, pf=round(float(w / l), 3) if l > 0 else None,
                sharpe=round(float(d.mean() / d.std() * np.sqrt(252)), 2) if d.std() > 0 else 0.0, net=round(float(x.sum()), 1), maxdd=round(float((eq.cummax() - eq).max()), 1))


if __name__ == "__main__":
    D = getD("nqdb.npz"); TR = {}
    for f in ("trades_db_old.pkl", "trades_db_new.pkl"): TR.update(pickle.load(open(os.path.join(HERE, f), "rb")))
    U = pickle.load(open(os.path.join(HERE, "db_long_trades.pkl"), "rb"))["Ultra"]
    real, norm = U[0].copy(), U[1].copy()
    for X in (real, norm): X.loc[X["mod"] == "MOM1030", "w"] = 4.0
    days = np.array(sorted(real.date.unique()))
    mods = {}
    for nm, key in NEW.items():
        for view, src in (("real", "real"), ("norm", "norm")):
            t = TR[key][src]
            tin = D.sm[t.fi.to_numpy().astype(int)]
            xi = TR[key]["real"].set_index("fi").xi.reindex(t.fi).to_numpy() if view == "norm" else t.xi.to_numpy()
            tout = D.sm[np.nan_to_num(xi, nan=0).astype(int)] + 1
            mods[(nm, view)] = pd.DataFrame(dict(date=t.date.to_numpy(), mod=nm, tin=tin, tout=tout, d=t.d.to_numpy(), u=t.usd.to_numpy(), w=1.0))
    late = {"real": real[real["mod"] == "LATEFH"], "norm": norm[norm["mod"] == "LATEFH"]}
    OUT = {"modules": {}, "portfolios": {}}
    for nm in list(NEW) + ["LATEFH"]:
        OUT["modules"][nm] = {}
        for lab, lo, hi in BLOCKS:
            view = "norm" if lab[0] in "AB" else "real"
            T = late[view] if nm == "LATEFH" else mods[(nm, view)]
            OUT["modules"][nm][lab] = stats(T, lo, hi, days)
    durable = [m for m in NEW if OUT["modules"][m]["A 2010-14"]["pf"] >= 1.0 and OUT["modules"][m]["B 2015-19"]["pf"] >= 1.05]
    print("durable by rule:", durable, flush=True)
    base_nolate = lambda X: X[X["mod"] != "LATEFH"]     # Ultra as coded has LATEFH off; six-year switch turns it on
    SETS = {"Ultra": [], "Ultra + six (all) + LATEFH": list(NEW) + ["LATEFH"], "Ultra + durable": durable}
    for sname, extra in SETS.items():
        OUT["portfolios"][sname] = {}
        for lab, lo, hi in BLOCKS:
            view = "norm" if lab[0] in "AB" else "real"
            B = base_nolate(norm if view == "norm" else real)
            parts = [B] + [late[view] if m == "LATEFH" else mods[(m, view)] for m in extra]
            A = pd.concat(parts, ignore_index=True)
            A = A[(A.date >= lo) & (A.date < hi)].sort_values(["date", "tin"]).reset_index(drop=True)
            A = conflict_filter(A)
            OUT["portfolios"][sname][lab] = stats(A, lo, hi, days)
        print(sname, {k: (v["pf"], v["sharpe"], v["net"], v["maxdd"]) for k, v in OUT["portfolios"][sname].items()}, flush=True)
    for nm, v in OUT["modules"].items(): print(f"{nm:7s}", {k: (x["n"], x["pf"]) for k, x in v.items()})
    OUT["durable"] = durable
    json.dump(OUT, open(os.path.join(HERE, "six_oos.json"), "w"), indent=1)
