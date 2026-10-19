"""Selection on the gold 16-year real-futures mining (run_mine_db.py on mgcdb.npz, MINE_FLAT=1010, MINE_NORM=0.0096 ->
results_gold16_new.csv / results_gold16_old.csv + trades_gold16_*.pkl), 2026-10-19.
Protocol fixed BEFORE looking (gold16_report.md section 0):
  1 T1 real 2020-23: n >= 80, PF >= 1.30, WR >= 50       2 T2 real 2024-26: PF >= 1.20 (n >= 30)
  3 A 2010-14 norm PF >= 1.00, B 2015-19 norm PF >= 1.00 (n >= 30)     4 +4 ticks ($4 per MGC trade) T2 PF >= 1.10
  5 plateau: 1-step grid neighbours (T1 n >= 30) median T1 PF >= 1.15 and <= 1/3 below 1.00
  6 one representative per signal (family + idea parameters; risk/exit parameters are variants), best T1 PF
  7 portfolio: gold Robust + candidate Sharpe up in T1 AND T2 with maxDD <= +5 %; NQ ultra_d4 + gold Robust + candidate Sharpe up in T1 AND T2
Also runs the current GoldMaster modules (gold_db.MODS) through the same table.
-> results_gold16.csv, gold16_select.json, gold16_survivors_trades.pkl"""
import os, sys, ast, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from core import Data, run_events
from run_mine_db import FAMILIES, NORM as _NQNORM
from news import NEWS
from db_long import FOMC_1019
NORM = 0.0096; FLAT = 1010; EXTRA4 = 4.0                                     # $4 per MGC trade = 2 extra ticks per side
FOMC = set(NEWS["FOMC"]) | set(FOMC_1019)
MODS = {   # current GoldMaster Robust set (gold_db.py / gold_curated.py)
    "OD1030": ("OPEN_DRIVE", "{'T': 60, 'x': 0.3, 'stop': 0, 'R': 0.5, 'tf': 1, 'hold': 400}"),
    "ENG0408": ("ENGULF_4H", "{'eng': '0408v0004@0930', 'ent': 2, 'R': 0.5, 'stop': 2, 'trend': 0, 'w1': 1500, 'body': 2}"),
    "SVWAP22": ("CLOCK_ANCHOR", "{'anc': 'SVWAP', 'T': 2200, 'x': 0.3, 'mode': -1, 's': 0.25, 'R': 0.5, 'tg': 0, 'tf': 0, 'hold': 120}"),
    "ASIA1R": ("G_ORB", "{'A': 2000, 'T': 240, 'W': 360, 'cap': 0.6, 'R': 1.0, 'tf': 1, 'hold': 600}"),
    "ENG0206": ("ENGULF_4H", "{'eng': '0206v2202@0930', 'ent': 2, 'R': 0.5, 'stop': 2, 'trend': 0, 'w1': 1500, 'body': 2}"),
}
VARIANT_KEYS = {"R", "x", "k", "s", "cap", "hold", "stop", "body", "bk", "conf", "sweep", "exp", "off", "extra", "N", "wick", "rng", "wmax", "wmin",
                "f", "tgt", "K", "bias", "rsi", "tf5", "maxday", "vwf", "sg", "w0", "w1", "st", "em", "m", "nb", "nf", "ex", "lb", "tfb", "dm", "ent", "tf", "tg"}
PARTS_R = (("T1", 20200101, 20240101), ("T2", 20240101, 20991231))
PARTS_N = (("A", 20100601, 20150101), ("B", 20150101, 20200101))


def pf(u):
    u = np.asarray(u, float); l = -u[u <= 0].sum()
    return float(u[u > 0].sum() / l) if l > 0 and len(u) >= 20 else np.nan


def sharpe(x):
    x = np.asarray(x, float); return float(x.mean() / x.std() * np.sqrt(252)) if len(x) > 1 and x.std() > 0 else 0.0


def maxdd(x):
    eq = np.cumsum(np.asarray(x, float)); return float((np.maximum.accumulate(eq) - eq).max()) if len(eq) else 0.0


def gate1(R): return (R.T1_n >= 80) & (R.T1_pf >= 1.30) & (R.T1_wr >= 50)
def gate2(R): return (R.T2_n >= 30) & (R.T2_pf >= 1.20)
def gate3(R): return (R.A_n >= 30) & (R.A_pf >= 1.00) & (R.B_n >= 30) & (R.B_pf >= 1.00)


def load_results():
    R = []
    for tag in ("gold16_new", "gold16_old"):
        p = os.path.join(HERE, f"results_{tag}.csv")
        if os.path.exists(p):
            r = pd.read_csv(p); r["tag"] = tag; R.append(r)
    R = pd.concat(R, ignore_index=True)
    if "err" not in R: R["err"] = np.nan
    R.to_csv(os.path.join(HERE, "results_gold16.csv"), index=False)
    return R


def load_trades():
    T = {}
    for tag in ("gold16_new", "gold16_old"):
        p = os.path.join(HERE, f"trades_{tag}.pkl")
        if os.path.exists(p): T.update(pickle.load(open(p, "rb")))
    return T


def plus4_pf(tr, lo=20240101):
    u = tr.usd[tr.date >= lo].to_numpy() - EXTRA4; return pf(u)


def neighbours(R, fam, p):
    """1-step grid neighbours inside the family (exactly one parameter different), T1 n >= 30."""
    sub = R[(R.fam == fam) & (R.T1_n >= 30)]
    out = []
    for _, r in sub.iterrows():
        q = r._pd
        if q == p: continue
        diff = [k for k in p if k in q and q[k] != p[k]] + [k for k in q if k not in p]
        if len(diff) == 1: out.append(float(r.T1_pf))
    out = np.array([v for v in out if np.isfinite(v)])
    return dict(n=int(len(out)), median=round(float(np.median(out)), 3) if len(out) else None, below1=round(float((out < 1.0).mean()), 2) if len(out) else None,
                ok=bool(len(out) >= 2 and np.median(out) >= 1.15 and (out < 1.0).mean() <= 1 / 3))


def signal_key(fam, p):
    return fam + "|" + ",".join(f"{k}={p[k]}" for k in sorted(p) if k not in VARIANT_KEYS)


def row_from_trades(r, nm):
    out = {}
    for lab, lo, hi in PARTS_R:
        u = r.usd[(r.date >= lo) & (r.date < hi)].to_numpy()
        out[lab + "_n"] = len(u); out[lab + "_wr"] = round(100 * (u > 0).mean(), 1) if len(u) else np.nan; out[lab + "_pf"] = round(pf(u), 3)
    for lab, lo, hi in PARTS_N:
        u = nm.usd[(nm.date >= lo) & (nm.date < hi)].to_numpy()
        out[lab + "_n"] = len(u); out[lab + "_wr"] = round(100 * (u > 0).mean(), 1) if len(u) else np.nan; out[lab + "_pf"] = round(pf(u), 3)
    return out


def gen_trades(D, fam, p):
    gen, grid, md = FAMILIES[fam]; ev = gen(D, p)
    r = run_events(D, ev, flat=FLAT, maxday=md, slip=0.25)
    nm = run_events(D, ev, flat=FLAT, maxday=md, slip=0.0, norm_cost=NORM)
    for df in (r, nm):
        df["tin"] = D.sm[df.fi.to_numpy().astype(int)] if len(df) else []; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1 if len(df) else []
    return r, nm


def conflict_filter(T):             # copy of gold_port.conflict_filter (importing gold_port loads two datasets)
    keep = []
    for d, g in T.groupby("date", sort=False):
        openpos = []
        for r in g.sort_values("tin", kind="stable").itertuples():
            if any(to > r.tin and dd == -r.d for to, dd in openpos): continue
            openpos.append((r.tout, r.d)); keep.append(r.Index)
    return T.loc[keep]


def frame(tr, name, w=1.0):
    tr = tr[~tr.date.isin(FOMC)]
    return pd.DataFrame(dict(date=tr.date.to_numpy(), mod=name, tin=tr.tin.to_numpy(), tout=tr.tout.to_numpy(), d=tr.d.to_numpy(), u=tr.usd.to_numpy(), w=w))


def daily(F, days):
    return (F.u * F.w).groupby(F.date).sum().reindex(days, fill_value=0.0)


def per_metrics(d, lo, hi):
    x = d[(d.index >= lo) & (d.index < hi)]
    return dict(sharpe=round(sharpe(x), 3), maxdd=round(maxdd(x)), per_month=round(float(x.mean() * 21)), net=round(float(x.sum())))


def block_boot(b, c, lo, hi, n=1000, L=21, seed=7):
    """21-day block bootstrap of Sharpe(c) - Sharpe(b) on a period."""
    m = (b.index >= lo) & (b.index < hi); bb = b[m].to_numpy(); cc = c[m].to_numpy(); N = len(bb)
    if N < 2 * L: return None
    rng = np.random.default_rng(seed); nb = int(np.ceil(N / L)); out = np.empty(n)
    for i in range(n):
        st = rng.integers(0, N - L + 1, nb); idx = (st[:, None] + np.arange(L)[None, :]).ravel()[:N]
        out[i] = sharpe(cc[idx]) - sharpe(bb[idx])
    return dict(median=round(float(np.median(out)), 3), p5=round(float(np.percentile(out, 5)), 3), p95=round(float(np.percentile(out, 95)), 3), p_gain=round(float((out > 0).mean()), 3))


def nq_daily():
    cache = os.path.join(HERE, "gold16_nq_daily.pkl")
    if os.path.exists(cache): return pickle.load(open(cache, "rb"))
    from nt_compare import research_set
    X, _ = research_set("ultra_d4"); d = (X.w * X.u).groupby(X.date).sum()
    pickle.dump(d, open(cache, "wb")); return d


if __name__ == "__main__":
    R = load_results(); R = R[R.err.isna()].copy(); R["_pd"] = R.params.map(ast.literal_eval)
    OUT = {"configs": int(len(R)), "by_family": R.fam.value_counts().to_dict()}
    g1 = gate1(R); g2 = gate2(R); g3 = gate3(R)
    base_pool = (R.T1_n >= 80) & (R.T2_n >= 30)
    OUT["gate1_T1"] = int(g1.sum()); OUT["gate12"] = int((g1 & g2).sum()); OUT["gate123"] = int((g1 & g2 & g3).sum())
    OUT["P_T2_given_T1"] = round(float(g2[g1].mean()), 4) if g1.any() else None
    OUT["P_T2_all_n80"] = round(float(g2[base_pool].mean()), 4)
    OUT["P_T2_T1pf_1.0_1.2"] = round(float(g2[base_pool & (R.T1_pf >= 1.0) & (R.T1_pf < 1.2)].mean()), 4)
    OUT["P_AB_given_T1T2"] = round(float(g3[g1 & g2].mean()), 4) if (g1 & g2).any() else None
    OUT["P_AB_all_n80"] = round(float(g3[base_pool].mean()), 4)
    fam_rows = []
    for fam, sub in R.groupby("fam"):
        s1 = gate1(sub); s2 = gate2(sub); pool = (sub.T1_n >= 80) & (sub.T2_n >= 30)
        fam_rows.append(dict(fam=fam, configs=len(sub), medT1=round(float(sub.T1_pf.median()), 3), medT2=round(float(sub.T2_pf.median()), 3),
                             medA=round(float(sub.A_pf.median()), 3), medB=round(float(sub.B_pf.median()), 3),
                             g1=int(s1.sum()), g12=int((s1 & s2).sum()), g123=int((s1 & s2 & gate3(sub)).sum()),
                             P_T2_given_T1=round(float(s2[s1].mean()), 3) if s1.any() else None, P_T2_all=round(float(s2[pool].mean()), 3) if pool.any() else None))
    FAM = pd.DataFrame(fam_rows).sort_values("g123", ascending=False); OUT["families"] = FAM.to_dict("records")
    print(json.dumps({k: OUT[k] for k in OUT if k not in ("by_family", "families")}, indent=1), flush=True)
    print(FAM.to_string(index=False), flush=True)

    # ---- gates 4-6 on the trades
    T = load_trades(); D = Data("mgcdb.npz")
    C = R[g1 & g2 & g3].copy(); rows = []
    for _, r in C.iterrows():
        k = (r.fam, int(r.j)); tr = T[k]["real"] if k in T else None
        p4 = plus4_pf(tr) if tr is not None else np.nan
        nb = neighbours(R, r.fam, r._pd)
        rows.append(dict(fam=r.fam, j=int(r.j), params=r.params, T1=f"{int(r.T1_n)} tr WR {r.T1_wr} PF {r.T1_pf}", T2=f"{int(r.T2_n)} tr WR {r.T2_wr} PF {r.T2_pf}",
                         A=f"PF {r.A_pf} ({int(r.A_n)})", B=f"PF {r.B_pf} ({int(r.B_n)})", T1_pf=float(r.T1_pf), T2_plus4=round(p4, 3), g4=bool(p4 >= 1.10),
                         nb_n=nb["n"], nb_median=nb["median"], nb_below1=nb["below1"], g5=nb["ok"], signal=signal_key(r.fam, r._pd)))
    G = pd.DataFrame(rows)
    OUT["gate1234"] = int(G.g4.sum()) if len(G) else 0; OUT["gate12345"] = int((G.g4 & G.g5).sum()) if len(G) else 0
    if len(G):
        G = G.sort_values("T1_pf", ascending=False)
        S = G[G.g4 & G.g5].drop_duplicates("signal", keep="first").copy()
        OUT["gate123456"] = int(len(S)); OUT["gate1_5_rows"] = G.to_dict("records")
        print("gates 1-5:\n", G[["fam", "j", "T1", "T2", "A", "B", "T2_plus4", "nb_n", "nb_median", "nb_below1", "g4", "g5"]].to_string(index=False), flush=True)
    else:
        S = G; OUT["gate123456"] = 0

    # ---- current GoldMaster modules through the same table
    days_all = np.array(sorted(set(D.daydate[D.daydate > 0]))); days = days_all[(days_all >= 20200101) & ~np.isin(days_all, list(FOMC))]
    cur = {}; cur_rows = []
    for nm, (fam, ps) in MODS.items():
        p = ast.literal_eval(ps); r, nmm = gen_trades(D, fam, p); st = row_from_trades(r, nmm); cur[nm] = r
        hit = R[(R.fam == fam) & R._pd.map(lambda q: q == p)]
        nb = neighbours(R, fam, p)
        rec = dict(mod=nm, fam=fam, params=ps, **st, T2_plus4=round(plus4_pf(r), 3), nb_n=nb["n"], nb_median=nb["median"], nb_below1=nb["below1"], in_grid=bool(len(hit)))
        rec["g1"] = bool(st["T1_n"] >= 80 and st["T1_pf"] >= 1.30 and st["T1_wr"] >= 50); rec["g2"] = bool(st["T2_n"] >= 30 and st["T2_pf"] >= 1.20)
        rec["g3"] = bool(st["A_n"] >= 30 and st["A_pf"] >= 1.0 and st["B_n"] >= 30 and st["B_pf"] >= 1.0); rec["g4"] = bool(rec["T2_plus4"] >= 1.10); rec["g5"] = nb["ok"]
        cur_rows.append(rec)
    CUR = pd.DataFrame(cur_rows); OUT["current_modules"] = CUR.to_dict("records")
    print("current GoldMaster modules:\n", CUR.drop(columns=["params"]).to_string(index=False), flush=True)

    # ---- portfolio tests
    base_mods = [frame(cur[m], m) for m in MODS]
    Fb = conflict_filter(pd.concat(base_mods, ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)); gb = daily(Fb, days)
    NQ = nq_daily(); nq_days = np.array(sorted(set(days[days >= 20201015]) | set(NQ.index[NQ.index >= 20201015]))); nq_days = nq_days[~np.isin(nq_days, list(FOMC))]
    nqd = NQ.reindex(nq_days, fill_value=0.0); gbn = gb.reindex(nq_days, fill_value=0.0)
    PER_G = (("T1", 20200101, 20240101), ("T2", 20240101, 20991231)); PER_N = (("T1", 20201015, 20240101), ("T2", 20240101, 20991231))
    OUT["gold_robust"] = {lab: per_metrics(gb, lo, hi) for lab, lo, hi in PER_G}
    OUT["nq_ultra_d4"] = {lab: per_metrics(nqd, lo, hi) for lab, lo, hi in PER_N}
    OUT["nq_plus_gold"] = {lab: per_metrics(nqd + gbn, lo, hi) for lab, lo, hi in PER_N}
    OUT["corr_nq_gold"] = {lab: round(float(np.corrcoef(nqd[(nqd.index >= lo) & (nqd.index < hi)], gbn[(gbn.index >= lo) & (gbn.index < hi)])[0, 1]), 3) for lab, lo, hi in PER_N}
    print("gold Robust", OUT["gold_robust"], "\nNQ", OUT["nq_ultra_d4"], "\nNQ+gold", OUT["nq_plus_gold"], "corr", OUT["corr_nq_gold"], flush=True)

    def port_test(tr, name):
        cand = frame(tr, name)
        Fc = conflict_filter(pd.concat(base_mods + [cand], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)); gc = daily(Fc, days)
        gcn = gc.reindex(nq_days, fill_value=0.0); rec = {"gold": {}, "nq": {}, "boot_gold": {}, "boot_nq": {}}
        for lab, lo, hi in PER_G:
            b = per_metrics(gb, lo, hi); c = per_metrics(gc, lo, hi)
            rec["gold"][lab] = dict(base=b, plus=c, dSharpe=round(c["sharpe"] - b["sharpe"], 3), dd_ratio=round(c["maxdd"] / b["maxdd"], 3) if b["maxdd"] > 0 else None)
            rec["boot_gold"][lab] = block_boot(gb, gc, lo, hi)
        for lab, lo, hi in PER_N:
            b = per_metrics(nqd + gbn, lo, hi); c = per_metrics(nqd + gcn, lo, hi)
            rec["nq"][lab] = dict(base=b, plus=c, dSharpe=round(c["sharpe"] - b["sharpe"], 3), dd_ratio=round(c["maxdd"] / b["maxdd"], 3) if b["maxdd"] > 0 else None)
            rec["boot_nq"][lab] = block_boot(nqd + gbn, nqd + gcn, lo, hi)
        x = cand.u.to_numpy(); cg = daily(cand, days)
        rec["standalone"] = dict(n=int(len(cand)), wr=round(100 * float((x > 0).mean()), 1), pf=round(pf(x), 3), per_month_T2=round(float(cg[cg.index >= 20240101].mean() * 21)),
                                 corr_gold_T1=round(float(np.corrcoef(cg[cg.index < 20240101], gb[gb.index < 20240101])[0, 1]), 3), corr_gold_T2=round(float(np.corrcoef(cg[cg.index >= 20240101], gb[gb.index >= 20240101])[0, 1]), 3))
        rec["pass_gold"] = bool(all(rec["gold"][l]["dSharpe"] > 0 and (rec["gold"][l]["dd_ratio"] or 0) <= 1.05 for l in ("T1", "T2")))
        rec["pass_nq"] = bool(all(rec["nq"][l]["dSharpe"] > 0 for l in ("T1", "T2")))
        return rec

    surv = {}; keep_tr = {}
    for _, s in S.iterrows():
        k = (s.fam, int(s.j)); tr = T[k]["real"]; name = f"{s.fam}#{s.j}"
        surv[name] = dict(params=s.params, T1=s.T1, T2=s.T2, A=s.A, B=s.B, T2_plus4=s.T2_plus4, plateau=dict(n=s.nb_n, median=s.nb_median, below1=s.nb_below1), **port_test(tr, name))
        keep_tr[name] = tr
        print(name, s.params, "\n  gold", {l: (v["dSharpe"], v["dd_ratio"]) for l, v in surv[name]["gold"].items()}, "nq", {l: v["dSharpe"] for l, v in surv[name]["nq"].items()},
              "pass_gold", surv[name]["pass_gold"], "pass_nq", surv[name]["pass_nq"], "\n  boot nq", surv[name]["boot_nq"], flush=True)
    OUT["survivors"] = surv; OUT["final"] = [n for n, v in surv.items() if v["pass_gold"] and v["pass_nq"]]
    # leave-one-out of the current modules (same test, for the reader)
    loo = {}
    for m in MODS:
        Fm = conflict_filter(pd.concat([f for f in base_mods if f["mod"].iloc[0] != m], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True)); gm = daily(Fm, days)
        gmn = gm.reindex(nq_days, fill_value=0.0)
        loo[m] = {"gold": {lab: round(per_metrics(gm, lo, hi)["sharpe"] - per_metrics(gb, lo, hi)["sharpe"], 3) for lab, lo, hi in PER_G},
                  "nq": {lab: round(per_metrics(nqd + gmn, lo, hi)["sharpe"] - per_metrics(nqd + gbn, lo, hi)["sharpe"], 3) for lab, lo, hi in PER_N}}
    OUT["loo_current_dSharpe_when_removed"] = loo; print("LOO (dSharpe when removed)", loo, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "gold16_select.json"), "w"), indent=1, default=str)
    pickle.dump(dict(survivors=keep_tr, current={m: cur[m] for m in MODS}), open(os.path.join(HERE, "gold16_survivors_trades.pkl"), "wb"))
    print("final:", OUT["final"], flush=True)
