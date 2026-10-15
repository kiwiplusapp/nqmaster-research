"""2026-10-15 'Sniper' eval sizing (Federico: when a module that won >= 80% of its trades over the past year signals, trade a big size
to pass the eval fast). Walk-forward flag per trade: the module's win rate over its trades of the previous L calendar days (only trades
closed before that day), n >= nmin and WR >= thr -> the trade is a SNIPER trade and is sized k contracts; every other trade keeps its
normal size (rest=1) or is skipped (rest=0). Static variants: MOM1030 + CPI09 at k (the current NQMaster defaults use k=4 in every mode).
Trades = UltraR (cand16, after the 10-12 overhaul) + CPI09 (ultraq), real Databento NQ 2020-26, minute paths (intraday low incl. open
trades), +1 tick per side, firm rules as month80.py, daily profit stop 0.9 x consistency x target. Starts T1 2020-03..2023-10 (choose),
T2 2024-01.. (check). Metrics: single eval pass within 5 / 10 / 20 list days, bust %, serial restarts funded within 20 list days, evals
used; 35% edge haircut; max simultaneous micros (p99 / max of daily peaks) vs the firm's eval cap. -> sniper_eval.json, sniper_eval.csv"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from wrq_lib import getD
from month80 import SET, outcomes, serial_first
FL = [(0.80, 365, 20), (0.80, 365, 30), (0.75, 365, 30), (0.85, 365, 20), (0.80, 730, 30)]
KS = (1, 2, 4, 6, 8, 10, 15)


def wf_flag(X, thr, L, nmin):
    out = np.zeros(len(X), bool); dt = pd.to_datetime(X.date.astype(str)).to_numpy()
    for m, g in X.groupby("mod"):
        ii = g.index.to_numpy(); d = dt[ii]; w = (g.u.to_numpy() > 0).astype(float); cw = np.concatenate([[0], np.cumsum(w)])
        lo = np.searchsorted(d, d - np.timedelta64(L, "D"), "left"); hi = np.searchsorted(d, d, "left")        # trades of earlier days only
        n = hi - lo; wr = np.where(n > 0, (cw[hi] - cw[lo]) / np.maximum(n, 1), 0)
        out[ii] = (n >= nmin) & (wr >= thr)
    return out


def conc(X, days, D):
    """per-day peak of simultaneously open contracts (weights w)"""
    pos = {d: i for i, d in enumerate(days)}; A = np.zeros((len(days), 1441))
    for t in X.itertuples():
        r = pos.get(t.date)
        if r is None: continue
        A[r, D.sm[t.fi]] += t.w; A[r, min(1440, D.sm[t.xi])] -= t.w
    return np.cumsum(A, 1)[:, :1440]


if __name__ == "__main__":
    E = RB.setup(); D = getD(RB.NAME)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]; n = len(days)
    X = pickle.load(open("cand16_trades.pkl", "rb"))["UltraR"][0]
    C = pickle.load(open("ultraq_trades.pkl", "rb"))["UltraQ"][0]; C = C[C["mod"] == "CPI09"].copy()
    key = pd.Series(np.arange(len(D.o)), index=pd.MultiIndex.from_arrays([D.date, D.sm]))
    key = key[~key.index.duplicated()]
    C["fi"] = [key.get((a, b), -1) for a, b in zip(C.date, C.tin)]; C["xi"] = [key.get((a, b), -1) for a, b in zip(C.date, C.tout)]
    C = C[(C.fi >= 0) & (C.xi >= 0)].copy(); C["e"] = D.o[C.fi.to_numpy()]; C["atr"] = np.nan
    X = RB.attach(X, E)
    T = pd.concat([X[["date", "mod", "tin", "tout", "d", "u", "fi", "xi", "w", "e"]], C[["date", "mod", "tin", "tout", "d", "u", "fi", "xi", "w", "e"]]], ignore_index=True)
    T = T.dropna(subset=["e"]).sort_values(["date", "tin"]).reset_index(drop=True)
    print("trades", len(T), "CPI09", int((T["mod"] == "CPI09").sum()), flush=True)
    flags = {f"wf{int(100*a)}_L{b}_n{c}": wf_flag(T, a, b, c) for a, b, c in FL}
    flags["static_MOM1030_CPI09"] = T["mod"].isin(["MOM1030", "CPI09"]).to_numpy()
    T2 = T[T.date.isin(days)]
    info = {}
    for nm, f in flags.items():
        g = T[f & (T.date >= 20200101)]
        info[nm] = dict(n=int(len(g)), per_week=round(len(g) / (len(days) / 5), 2), wr=round(100 * float((g.u > 0).mean()), 1),
                        pf=round(float(g.u[g.u > 0].sum() / -g.u[g.u <= 0].sum()), 2), avg_loss=round(float(g.u[g.u <= 0].mean()), 1),
                        avg_win=round(float(g.u[g.u > 0].mean()), 1), worst=round(float(g.u.min()), 1),
                        mods=g["mod"].value_counts().head(8).to_dict())
        print(nm, info[nm], flush=True)
    P = {}
    rest_all = T2.copy()
    P["all"] = full_paths(rest_all, days); cA = rest_all.w.groupby(rest_all.date).sum().reindex(days, fill_value=0).to_numpy(); kA = conc(rest_all, days, D)
    for nm, f in flags.items():
        ff = f[T.date.isin(days).to_numpy()]
        R0 = T2[~ff]; S1 = T2[ff].assign(w=1.0)
        P[nm] = (full_paths(R0, days), full_paths(S1, days),
                 R0.w.groupby(R0.date).sum().reindex(days, fill_value=0).to_numpy(), S1.w.groupby(S1.date).sum().reindex(days, fill_value=0).to_numpy(),
                 conc(R0, days, D), conc(S1, days, D))
        print("paths", nm, flush=True)
    d24 = int(np.searchsorted(days, 20240101))
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 40]
    rows = []
    pols = [("baseline Ultra 1c", None, 1, 1)] + [(nm, nm, k, r) for nm in flags for k in KS if k > 1 for r in (1, 0)]
    for pname, fl, k, rest in pols:
        if fl is None: (lw, cl0, fn), cc, kk = P["all"], cA, kA
        else:
            (a, b, cr, cs, kr, ks) = P[fl]
            lw = rest * a[0] + k * b[0]; cl0 = rest * a[1] + k * b[1]; fn = rest * a[2] + k * b[2]; cc = rest * cr + k * cs; kk = (rest * kr + k * ks).max(1)
        if fl is None: kk = kk.max(1)
        pk99, pkmax = float(np.percentile(kk, 99)), float(kk.max())
        mu1 = float(fn[:d24].mean()); mu2 = float(fn[d24:].mean())
        for firm, (Tg, Dd, cons, mind, dll, fee, mx) in SET.items():
            G = 0.9 * cons * Tg if cons > 0 else 0.0
            rec = dict(policy=pname, k=k, rest=rest, firm=firm, peak99=pk99, peakmax=pkmax, cap=mx, fits=bool(pkmax <= mx))
            for hc in (0.0, 0.35):
                h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
                lo, cl = vectors(lw - cc[:, None] - h[:, None], cl0 - cc[:, None] - h[:, None], fn - cc - h, G)
                if dll > 0:
                    hit = lo <= -dll; cl = np.where(hit, -float(dll), cl); lo = np.where(hit, -float(dll), lo)
                res, dd = outcomes(lo, cl, Tg, Dd, cons, mind, n)
                sfx = "" if hc == 0 else "_h35"
                for tag, st in (("T1", s1), ("T2", s2)):
                    for w in (5, 10, 20): rec[f"{tag}_p{w}{sfx}"] = round(100 * float(np.mean([(res[s] == 1) and dd[s] < w for s in st])), 1)
                    rec[f"{tag}_bust{sfx}"] = round(100 * float(np.mean([res[s] == -1 for s in st])), 1)
                    se = [serial_first(res, dd, s, 20) for s in st]
                    rec[f"{tag}_serial20{sfx}"] = round(100 * float(np.mean([a for a, _ in se])), 1); rec[f"{tag}_evals{sfx}"] = round(float(np.mean([b for _, b in se])), 2)
            rows.append(rec)
        print(f"{pname:24s} k{k:2d} rest{rest} peak {pk99:4.0f}/{pkmax:4.0f} | " + " | ".join(
            f"{r['firm'][:14]} p10 {r['T1_p10']:.0f}/{r['T2_p10']:.0f} ser {r['T1_serial20']:.0f}/{r['T2_serial20']:.0f}" for r in rows[-len(SET):] if r["firm"] in ("Lucid Pro 25K", "Lucid Flex 50K", "Lucid Pro 50K")), flush=True)
    R = pd.DataFrame(rows); R.to_csv(os.path.join(HERE, "sniper_eval.csv"), index=False)
    OUT = dict(flags=info)
    for firm in SET:
        F = R[(R.firm == firm) & R.fits]; base = R[(R.firm == firm) & (R.policy == "baseline Ultra 1c")].iloc[0]
        best = {}
        for obj in ("p5", "p10", "serial20"):
            b = F.sort_values(f"T1_{obj}", ascending=False).iloc[0]
            best[obj] = {c: (b[c] if not isinstance(b[c], (np.floating, np.integer)) else float(b[c])) for c in R.columns}
        OUT[firm] = dict(baseline={c: (base[c] if not isinstance(base[c], (np.floating, np.integer)) else float(base[c])) for c in R.columns}, chosen_on_T1=best)
    json.dump(OUT, open(os.path.join(HERE, "sniper_eval.json"), "w"), indent=1, default=str)
