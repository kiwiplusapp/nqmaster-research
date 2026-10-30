"""Revision adversarial diag 11: variantes de diag_partition.py (no toca el repo; corre desde research/mine)."""
import os, sys, json, pickle, numpy as np, pandas as pd
MINE = "/home/user/nqmaster-research/research/mine"
sys.path.insert(0, MINE); os.chdir(MINE)
import diag_partition as P
from wrq_port import conflict_filter

SEED = P.SEED


def daily(excl=("CA04V", "GD03", "ENG26"), cf=False):
    T = pickle.load(open(os.path.join(MINE, "six_ultra6_trades.pkl"), "rb"))["Ultra6"]
    T = T[~T["mod"].isin(list(excl))].copy()
    if cf: T = conflict_filter(T.sort_values(["date", "tin"]).reset_index(drop=True))
    T["pnl"] = T.u * T.w
    return T.pivot_table(index="date", columns="mod", values="pnl", aggfunc="sum").fillna(0.0)


def partitions(D, t1):
    mods = list(D.columns); m1 = D[t1].mean(); order = m1.sort_values(ascending=False).index.tolist()
    alt = (order[0::2], order[1::2])
    rng = np.random.default_rng(SEED); tot = m1.sum(); best, bc = None, 9.0
    for _ in range(2000):
        msk = rng.random(len(mods)) < 0.5; A = [m for m, k in zip(mods, msk) if k]; B = [m for m, k in zip(mods, msk) if not k]
        if not A or not B or abs(m1[A].sum() - tot / 2) > 0.1 * tot / 2: continue
        c = np.corrcoef(D.loc[t1, A].sum(axis=1), D.loc[t1, B].sum(axis=1))[0, 1]
        if c < bc: bc, best = c, (A, B)
    return alt, best


def coinc(da, db, W=5, wrap=True):
    near = np.zeros_like(db)
    for k in range(-W, W + 1):
        if wrap: near |= np.roll(db, k, axis=1)
        else:
            s = np.zeros_like(db)
            if k >= 0: s[:, k:] = db[:, :db.shape[1] - k]
            else: s[:, :k] = db[:, -k:]
            near |= s
    return (da & near).sum() / max(1, da.sum())


def ph(a, b, idx, thr):
    ca, da = P.renewal(np.ascontiguousarray(a[idx]), thr); cb, db = P.renewal(np.ascontiguousarray(b[idx]), thr)
    return dict(par=float(ca.mean() + cb.mean()), qa=float(ca.mean()), qb=float(cb.mean()),
                co_ab=100 * coinc(da, db), co_ba=100 * coinc(db, da), co_ab_nowrap=100 * coinc(da, db, wrap=False),
                co_ba_nowrap=100 * coinc(db, da, wrap=False),
                p90_par=float(np.percentile(ca + cb, 90)))


def run(label, D, t1cut, thrs=(1500.0, 2000.0), hcs=(0.0,), seeds=(SEED,)):
    t1 = D.index < t1cut; alt, best = partitions(D, t1); out = {}
    for per, msk in (("T1", t1), ("T2", ~t1)):
        X = D[msk]
        for sd in seeds:
            idx = P.boot_idx(len(X), np.random.default_rng(sd))
            for hc in hcs:
                full = X.sum(axis=1).to_numpy()
                for nm, (A, B) in (("alterna", alt), ("favorable", best)):
                    a = 2 * X[A].sum(axis=1).to_numpy(); b = 2 * X[B].sum(axis=1).to_numpy()
                    f2, a2, b2 = full - hc * full.mean(), a - hc * a.mean(), b - hc * b.mean()
                    for thr in thrs:
                        r0 = ph(f2, f2, idx, thr); r1 = ph(a2, b2, idx, thr)
                        out[(per, sd, hc, nm, thr)] = (r0, r1)
    return out, alt, best


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    res = {}
    if what in ("all", "repro"):
        D = daily(); o, alt, best = run("repro", D, 20230101)
        print("REPRO (set del script, T1<2023): base par -> particion par | coincidencia A->B / B->A / A->B sin wrap / B->A sin wrap")
        for k, (r0, r1) in o.items():
            print(" ", k, "%.2f -> %.2f (x%.2f) | %.1f / %.1f / %.1f / %.1f | p90 par base %.0f part %.0f" % (r0["par"], r1["par"], r1["par"] / max(r0["par"], 1e-9), r1["co_ab"], r1["co_ba"], r1["co_ab_nowrap"], r1["co_ba_nowrap"], r0["p90_par"], r1["p90_par"]))
    if what in ("all", "d4"):
        D = daily(excl=("CA04V", "GD03", "ENG26", "LATEFH"), cf=True); print("ultra_d4 exacto: modulos", len(D.columns), "dias", len(D))
        o, alt, best = run("d4", D, 20230101, hcs=(0.0, 0.35, 1.0))
        print("ULTRA_D4 (sin LATEFH, con conflict_filter), T1<2023")
        print("  favorable A:", best[0]); print("  favorable B:", best[1])
        for k, (r0, r1) in o.items():
            print(" ", k, "%.2f -> %.2f (x%.2f) | coinc A->B %.1f B->A %.1f" % (r0["par"], r1["par"], r1["par"] / max(r0["par"], 1e-9), r1["co_ab"], r1["co_ba"]))
    if what in ("all", "t2024"):
        D = daily(); o, alt, best = run("t2024", D, 20240101)
        print("T1<2024 (pre-registro literal: T1 2020-23, T2 2024-26)")
        for k, (r0, r1) in o.items():
            print(" ", k, "%.2f -> %.2f (x%.2f) | coinc A->B %.1f B->A %.1f" % (r0["par"], r1["par"], r1["par"] / max(r0["par"], 1e-9), r1["co_ab"], r1["co_ba"]))
    if what in ("all", "thr"):
        D = daily(); o, alt, best = run("thr", D, 20230101, thrs=(500.0, 750.0, 1000.0, 1500.0, 3000.0, 4500.0, 6000.0), hcs=(0.0, 0.35, 1.0))
        print("BARRIDO DE UMBRAL (favorable y alterna)")
        for k, (r0, r1) in o.items():
            print(" ", k, "%.2f -> %.2f (x%.2f) | coinc A->B %.1f B->A %.1f" % (r0["par"], r1["par"], r1["par"] / max(r0["par"], 1e-9), r1["co_ab"], r1["co_ba"]))
    if what in ("all", "seeds"):
        D = daily(); o, alt, best = run("seeds", D, 20230101, seeds=(1, 2, 3, 4, 5))
        print("SEMILLAS DE BOOTSTRAP 1-5")
        for k, (r0, r1) in o.items():
            print(" ", k, "%.2f -> %.2f (x%.2f)" % (r0["par"], r1["par"], r1["par"] / max(r0["par"], 1e-9)))
