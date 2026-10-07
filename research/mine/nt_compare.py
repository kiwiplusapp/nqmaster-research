"""Compare a NinjaTrader Strategy Analyzer trade export with the research trades, module by module (port validation).

Usage (from research/mine):
  python nt_compare.py "<NT trades.csv>" --set ultra      [--tz America/Argentina/Buenos_Aires] [--out nt_compare_ultra]
  python nt_compare.py "<NT trades.csv>" --set gold_robust | gold_winrate | wr70plus

NT export: Strategy Analyzer -> Trades tab -> right click -> Export (CSV, ';' separated, '1.234,56 $' numbers, local PC time).
Run NT with Contracts = 1 on real MNQ / MGC 1-minute data; P&L is compared per contract (NT profit / qty).
Research reference = the REAL (MNQ/MGC futures 2024-26) trade lists with the conflict filter, FOMC days excluded.
A trade matches when date, module and direction agree and the entry minute differs by <= 3 minutes.
Writes <out>.md (summary) and <out>_mismatch.csv (unmatched trades of both sides)."""
import os, sys, argparse, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, "..")
from nt_trades import load_nt
from gold_port import conflict_filter

def research_set(name):
    if name in ("ultra", "wr70plus"):
        from ict_redo import ictf
        from ultra_plus_lib import mined
        T = pickle.load(open("robust_trades.pkl", "rb"))
        if name == "ultra":
            F = T["Ultra"]["REAL"][0]; W = T["WR70Plus"]["REAL"][0]
            parts = [F[(F["mod"] != "ICT") & (F["mod"] != "VW13")], ictf("REAL", 2.0), W[W["mod"] == "VW13b"].assign(mod="VW13"),
                     mined(("LATE_MOM", 762), "REAL", "LATE15"), mined(("ENGULF_4H", 1172), "REAL", "ENG10"), mined(("LATE_MOM", 1107), "REAL", "LATEFH")]
        else:
            F = T["WR70Plus"]["REAL"][0]
            parts = [F[F["mod"] != "ICT"], ictf("REAL", 2.0), mined(("LATE_MOM", 762), "REAL", "LATE15")]
        X = pd.concat([p[["date", "mod", "tin", "tout", "d", "u", "w"]] for p in parts], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)
        X["mod"] = X["mod"].replace({"VW13b": "VW13", "VOLB_tf1": "VOLB", "VOLB_tf0": "VOLB"})
        return conflict_filter(X), "nq"
    GC = pickle.load(open("gold_curated_trades.pkl", "rb"))
    mods = ["OD1030", "ENG0408", "SVWAP22"] + (["ASIA1R", "ENG0206"] if name == "gold_robust" else [])
    X = pd.concat([GC[m]["REAL"][["date", "mod", "tin", "tout", "d", "u", "w"]] for m in mods], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)
    X["mod"] = X["mod"].replace({"ASIA1R": "ASIA"})
    return conflict_filter(X), "gold"

def nt_frame(path, tz):
    t = load_nt(path)
    loc = t.tin.dt.tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("America/New_York").dt.tz_localize(None)
    op = loc - pd.Timedelta(minutes=1)                         # NT stamps the fill with the bar CLOSE time; research uses the bar OPEN
    trade_day = (op + pd.Timedelta(hours=6)).dt.normalize()       # 18:00 ET belongs to the next trade date
    t["date"] = trade_day.dt.strftime("%Y%m%d").astype(int)
    t["tin"] = ((op.dt.hour * 60 + op.dt.minute - 1080) % 1440).astype(int)
    t["d"] = np.where(t["Market pos."].str.lower().str.startswith(("long", "larg")), 1, -1)
    t["u"] = t.pnl / t.qty
    t["mod"] = t["mod"].replace({"GC_ORB30": "ORB30"})
    return t[["date", "mod", "tin", "d", "u", "qty", "pnl"]].reset_index(drop=True)

def match(R, N, tol=3):
    R = R.copy(); N = N.copy(); R["k"] = -1; N["k"] = -1
    for (dt, md), g in R.groupby(["date", "mod"]):
        cand = N[(N.date == dt) & (N["mod"] == md) & (N.k < 0)]
        for i, r in g.iterrows():
            tl = 300 if md == "LON" else tol                        # research stores LON at 05:00 (limit fill time not kept)
            c = cand[(cand.d == r.d) & ((cand.tin - r.tin).abs() <= tl) & (N.loc[cand.index, "k"] < 0)]
            if len(c):
                j = (c.tin - r.tin).abs().idxmin(); R.at[i, "k"] = j; N.at[j, "k"] = i
    return R, N

def stats(u):
    u = np.asarray(u, float)
    if len(u) == 0: return dict(n=0, wr=np.nan, pf=np.nan, net=0.0)
    gl = -u[u <= 0].sum()
    return dict(n=len(u), wr=round(100 * (u > 0).mean(), 1), pf=round(u[u > 0].sum() / gl, 2) if gl > 0 else np.nan, net=round(u.sum()))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--set", default="ultra", choices=["ultra", "wr70plus", "gold_robust", "gold_winrate"])
    ap.add_argument("--tz", default="America/Argentina/Buenos_Aires"); ap.add_argument("--out", default=None); ap.add_argument("--tol", type=int, default=3)
    a = ap.parse_args(); out = a.out or "nt_compare_" + a.set
    R, inst = research_set(a.set); N = nt_frame(a.csv, a.tz)
    lo, hi = max(R.date.min(), N.date.min()), min(R.date.max(), N.date.max())
    R = R[(R.date >= lo) & (R.date <= hi)].reset_index(drop=True); N = N[(N.date >= lo) & (N.date <= hi)].reset_index(drop=True)
    R["u1"] = R.u                                                # research $ per contract (weights x2 compared per contract)
    R, N = match(R, N, a.tol)
    rows = []
    for md in sorted(set(R["mod"]) | set(N["mod"])):
        r = R[R["mod"] == md]; n = N[N["mod"] == md]; mr = r[r.k >= 0]
        sr, sn = stats(r.u1), stats(n.u)
        mu = n.loc[mr.k.values, "u"].values if len(mr) else np.array([])
        rows.append(dict(module=md, res_n=sr["n"], nt_n=sn["n"], matched=len(mr), only_res=int((r.k < 0).sum()), only_nt=int((n.k < 0).sum()),
                         res_wr=sr["wr"], nt_wr=sn["wr"], res_pf=sr["pf"], nt_pf=sn["pf"], res_net=sr["net"], nt_net=sn["net"],
                         matched_res=round(mr.u1.sum()), matched_nt=round(mu.sum()) if len(mu) else 0,
                         corr=round(np.corrcoef(mr.u1.values, mu)[0, 1], 3) if len(mu) > 2 else np.nan))
    S = pd.DataFrame(rows)
    tot = dict(module="TOTAL", **{c: S[c].sum() for c in ["res_n", "nt_n", "matched", "only_res", "only_nt", "res_net", "nt_net", "matched_res", "matched_nt"]})
    tot.update(res_wr=stats(R.u1)["wr"], nt_wr=stats(N.u)["wr"], res_pf=stats(R.u1)["pf"], nt_pf=stats(N.u)["pf"])
    S = pd.concat([S, pd.DataFrame([tot])], ignore_index=True)
    dr = R.groupby("date").u1.sum(); dn = N.groupby("date").u.sum(); idx = dr.index.union(dn.index)
    dcorr = np.corrcoef(dr.reindex(idx, fill_value=0), dn.reindex(idx, fill_value=0))[0, 1]
    mm = pd.concat([R[R.k < 0].assign(side="solo investigacion")[["side", "date", "mod", "tin", "d", "u1"]].rename(columns={"u1": "u"}),
                    N[N.k < 0].assign(side="solo NinjaTrader")[["side", "date", "mod", "tin", "d", "u"]]]).sort_values(["date", "tin"])
    mm["hora_ET"] = ((mm.tin + 1080) % 1440).map(lambda x: f"{x // 60:02d}:{x % 60:02d}")
    mm.to_csv(out + "_mismatch.csv", index=False)
    pd.set_option("display.width", 250)
    txt = (f"# NinjaTrader vs investigación ({a.set}, {lo}-{hi})\n\n"
           f"- Trades: investigación {len(R)}, NinjaTrader {len(N)}, coinciden {int((R.k >= 0).sum())} ({100 * (R.k >= 0).mean():.1f}% de la investigación).\n"
           f"- $ por contrato: investigación {R.u1.sum():,.0f}, NinjaTrader {N.u.sum():,.0f}. Correlación diaria {dcorr:.3f}.\n"
           f"- En los trades que coinciden: investigación {R[R.k >= 0].u1.sum():,.0f}, NinjaTrader {N[N.k >= 0].u.sum():,.0f}.\n\n"
           "```\n" + S.to_string(index=False) + "\n```\n\nTrades sin pareja: " + out + "_mismatch.csv\n")
    open(out + ".md", "w", encoding="utf-8").write(txt); print(txt)
