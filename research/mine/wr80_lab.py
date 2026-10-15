"""2026-10-15 'A+ setups': can we know BEFORE the entry that a trade belongs to a group with >= 80% win rate, and trade 4 contracts
there? Every Ultra (cand16 UltraR) trade on real Databento NQ 2010-2026 gets 19 decision-time features (wrq_feats: trend, prior-day
range/position, ATR regime, stop size, VWAP distance, gap, overnight range, session position, 30-min move, volatility, time, weekday;
only information known before the fill). Candidate setups = module x one feature x one side of a quantile threshold (20/33/50/67/80%,
thresholds computed on 2020-23 only).
Protocol fixed before looking:
  chosen on T1 (2020-23 real): n >= 30, WR >= 80%, PF >= 1.5
  must hold on T2 (2024-26 real): n >= 15, WR >= 80%, PF >= 1.3
  and on 2010-14 + 2015-19 (cost-normalised, pooled): n >= 30, WR >= 75%, PF >= 1.1
Null check: the whole search repeated 20 times with the feature values shuffled within each module (how many 'setups' pass by luck).
Then: survivors traded at 4 contracts (others 1) -> Sharpe / PF / $ / max drawdown per period. -> wr80_lab.json, wr80_lab.csv"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from wrq_lib import getD
from wrq_feats import feats
FEATS = ["tr10", "tr20", "tr50", "r5", "r20", "r60", "atrr", "risk", "vw", "svw", "pdcd", "gap", "pdr", "pdpos", "onr", "dpos", "rv60", "m30", "dow"]
QS = (0.2, 0.33, 0.5, 0.67, 0.8)
pf = lambda u: float(u[u > 0].sum() / -u[u <= 0].sum()) if (u <= 0).any() and (u > 0).any() else (np.inf if (u > 0).any() else 0.0)


def stat(u):
    u = np.asarray(u); return len(u), (100 * float((u > 0).mean()) if len(u) else np.nan), pf(u) if len(u) else np.nan


def search(R, N, F):
    """R real trades (T1/T2), N norm trades (A/B); F feature frame keyed like R/N (column 'k')"""
    out = []
    T1 = R[(R.date >= 20200101) & (R.date < 20240101)]; T2 = R[R.date >= 20240101]; AB = N[N.date < 20200101]
    for m in sorted(R["mod"].unique()):
        t1, t2, ab = T1[T1["mod"] == m], T2[T2["mod"] == m], AB[AB["mod"] == m]
        for f in FEATS:
            v1 = t1[f].to_numpy(); ok = ~np.isnan(v1)
            if ok.sum() < 60: continue
            for q in QS:
                th = float(np.quantile(v1[ok], q))
                for side in (1, -1):
                    sel = lambda X: X[(X[f] >= th) if side == 1 else (X[f] < th)]
                    a = sel(t1)
                    n1, w1, p1 = stat(a.u)
                    if n1 < 30 or w1 < 80 or p1 < 1.5: continue
                    b = sel(t2); c = sel(ab); n2, w2, p2 = stat(b.u); n3, w3, p3 = stat(c.u)
                    out.append(dict(mod=m, feat=f, q=q, side=side, th=round(th, 4), T1_n=n1, T1_wr=round(w1, 1), T1_pf=round(p1, 2),
                                    T2_n=n2, T2_wr=round(w2, 1), T2_pf=round(p2, 2), AB_n=n3, AB_wr=round(w3, 1), AB_pf=round(p3, 2),
                                    ok=bool(n2 >= 15 and w2 >= 80 and p2 >= 1.3 and n3 >= 30 and w3 >= 75 and p3 >= 1.1)))
    return pd.DataFrame(out)


if __name__ == "__main__":
    E = RB.setup(); D = getD(RB.NAME)
    R, N = pickle.load(open("cand16_trades.pkl", "rb"))["UltraR"]
    U = pd.concat([R[["mod", "fi", "d", "date"]], N[["mod", "fi", "d", "date"]]]).drop_duplicates(["mod", "fi", "d"]).reset_index(drop=True)
    U = RB.attach(U.assign(w=1.0), E).dropna(subset=["ent0", "sl0"]).reset_index(drop=True)
    F = feats(D, U); F = pd.concat([U[["mod", "fi", "d"]], F], axis=1)
    R = R.merge(F, on=["mod", "fi", "d"], how="left"); N = N.merge(F, on=["mod", "fi", "d"], how="left")
    S = search(R, N, F); S.to_csv("wr80_lab.csv", index=False)
    print("candidates passing 2020-23:", len(S), " | also 2024-26 and 2010-19:", int(S.ok.sum()) if len(S) else 0, flush=True)
    rng = np.random.default_rng(3); null = []
    for b in range(20):
        Rs, Ns = R.copy(), N.copy()
        for X in (Rs, Ns):
            for m, g in X.groupby("mod"):
                perm = rng.permutation(g.index.to_numpy())
                X.loc[g.index, FEATS] = X.loc[perm, FEATS].to_numpy()
        Sn = search(Rs, Ns, F); null.append((len(Sn), int(Sn.ok.sum()) if len(Sn) else 0))
    print("null (shuffled features), 20 runs: T1 passes mean", np.mean([a for a, _ in null]), "all-period passes mean", np.mean([b for _, b in null]),
          "max", max(b for _, b in null), flush=True)
    pd.set_option("display.width", 250)
    surv = S[S.ok] if len(S) else S
    if len(surv): print(surv.sort_values("T2_wr", ascending=False).to_string(index=False))
    res = dict(t1_pass=int(len(S)), all_pass=int(len(surv)), null=null, survivors=surv.to_dict("records"))
    # sizing: survivors (union of their trades) at 4 contracts
    if len(surv):
        def mark(X):
            k = np.zeros(len(X), bool)
            for r in surv.itertuples():
                k |= ((X["mod"] == r.mod) & ((X[r.feat] >= r.th) if r.side == 1 else (X[r.feat] < r.th))).to_numpy()
            return k
        for nm, X, lo, hi in (("A", N, 20100601, 20150101), ("B", N, 20150101, 20200101), ("T1", R, 20200101, 20240101), ("T2", R, 20240101, 20991231)):
            s = X[(X.date >= lo) & (X.date < hi)].reset_index(drop=True); k = mark(s)
            for mult in (1, 2, 4):
                x = s.u * s.w * np.where(k, mult, 1.0); d = x.groupby(s.date).sum(); eq = d.cumsum()
                res.setdefault("sizing", {}).setdefault(nm, {})[f"x{mult}"] = dict(flagged=int(k.sum()), flagged_wr=round(100 * float((s.u[k] > 0).mean()), 1) if k.any() else None,
                    pf=round(pf(x.to_numpy()), 3), sharpe=round(float(d.mean() / d.std() * np.sqrt(252)), 2), net=round(float(x.sum())), maxdd=round(float((eq.cummax() - eq).max())))
            print(nm, res["sizing"][nm], flush=True)
    json.dump(res, open("wr80_lab.json", "w"), indent=1, default=str)
