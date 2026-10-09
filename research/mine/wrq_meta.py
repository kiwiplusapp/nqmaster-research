"""wrq_meta: walk-forward logistic-regression meta-label per module (cross-check of the one-feature filters).
Features (5, decided in advance): tr20, r5, atrr, rv60, and vw for RTH entries / svw for overnight entries. Label = trade wins.
CFD: train on all years < Y (expanding, standardised, L2 C=1.0), predict year Y for Y = 2022 .. 2026.
REAL: train on CFD years < Y, predict REAL year Y (2024, 2025, 2026). L15 (2015-19): train on CFD 2020-23, predict 2015-19
(backward regime test). Threshold fixed in advance: skip a trade when its predicted probability is below the 20th percentile
of the training-set fitted probabilities. Pooled model across modules with module one-hot added is also tested.
-> wrq_meta.csv"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from wrq_lib import getD, PER, SLIP
from wrq_exits import arrays, sim, st

def dataset(EN, FT, name, slip, norm):
    D = getD(name); parts = []
    for m, E in EN[name].groupby("mod"):
        A = arrays(E); u, ok, _ = sim(A, D, slip, {}, norm)
        F = FT[name].loc[E.index].copy()
        F["vwx"] = np.where(F.vw.notna(), F.vw, F.svw)
        F["u"] = u; F["ok"] = ok; F["date"] = E.date.to_numpy(); F["mod"] = m; F["fomc"] = E.fomc.to_numpy()
        parts.append(F)
    X = pd.concat(parts); X = X[X.ok & ~X.fomc.astype(bool)]
    X["y"] = (X.u > 0).astype(int); X["year"] = X.date // 10000
    return X

COLS = ["tr20", "r5", "atrr", "rv60", "vwx"]

def fit_pred(tr, te, pooled=False, mods=None):
    cols = list(COLS)
    a = tr[cols].copy(); b = te[cols].copy()
    med = a.median(); a = a.fillna(med); b = b.fillna(med)
    if pooled:
        for m in mods:
            a["m_" + m] = (tr["mod"] == m).astype(float); b["m_" + m] = (te["mod"] == m).astype(float)
    sc = StandardScaler().fit(a); lr = LogisticRegression(C=1.0, max_iter=500).fit(sc.transform(a), tr.y)
    pt = lr.predict_proba(sc.transform(a))[:, 1]; pe = lr.predict_proba(sc.transform(b))[:, 1]
    if pooled:   # per-module threshold: 20th percentile of that module's training predictions
        thr = pd.Series(pt, index=tr.index).groupby(tr["mod"]).quantile(0.2)
        return pe >= te["mod"].map(thr).to_numpy()
    return pe >= np.quantile(pt, 0.2)

if __name__ == "__main__":
    EN = pickle.load(open("wrq_entries.pkl", "rb")); FT = pickle.load(open("wrq_feats.pkl", "rb"))
    C = dataset(EN, FT, "nq_1m.npz", SLIP, False); R = dataset(EN, FT, "mnq_fut.npz", SLIP, False); L = dataset(EN, FT, "nqhd_long.npz", 0.0, True)
    C = C[C.date >= 20200201]; L = L[(L.date >= 20150201) & (L.date < 20200101)]; R = R[R.date >= 20240201]
    mods = sorted(C["mod"].unique()); rows = []
    for mode in ("per-module", "pooled"):
        keepC = pd.Series(False, index=C.index); keepR = pd.Series(False, index=R.index); keepL = pd.Series(False, index=L.index)
        keepC = keepC.reset_index(drop=True); C2 = C.reset_index(drop=True); R2 = R.reset_index(drop=True); L2 = L.reset_index(drop=True)
        kC = np.zeros(len(C2), bool); kR = np.zeros(len(R2), bool); kL = np.zeros(len(L2), bool); hasC = np.zeros(len(C2), bool)
        groups = [(m, C2["mod"] == m, R2["mod"] == m, L2["mod"] == m) for m in mods] if mode == "per-module" else [("ALL", C2["mod"].notna(), R2["mod"].notna(), L2["mod"].notna())]
        for m, gc, gr, gl in groups:
            for Y in range(2022, 2027):
                tr = C2[gc & (C2.year < Y)]; te = C2[gc & (C2.year == Y)]
                if len(tr) < 60 or len(te) == 0: continue
                kC[te.index] = fit_pred(tr, te, mode == "pooled", mods); hasC[te.index] = True
                if Y >= 2024:
                    ter = R2[gr & (R2.year == Y)]
                    if len(ter): kR[ter.index] = fit_pred(tr, ter, mode == "pooled", mods)
            tr = C2[gc & (C2.year < 2024)]; tel = L2[gl]
            if len(tr) >= 60 and len(tel): kL[tel.index] = fit_pred(tr, tel, mode == "pooled", mods)
        for m in mods + ["ALL"]:
            for lab, X, k, h in (("CFD 2022-23", C2, kC, hasC & (C2.year < 2024)), ("C24", C2, kC, hasC & (C2.year >= 2024)), ("REAL", R2, kR, np.ones(len(R2), bool)), ("L15", L2, kL, np.ones(len(L2), bool))):
                g = (X["mod"] == m) if m != "ALL" else np.ones(len(X), bool)
                b = st(X.u[g & h].to_numpy()); a = st(X.u[g & h & k].to_numpy())
                rows.append(dict(mode=mode, mod=m, per=lab, n0=b[0], wr0=b[1], pf0=b[2], n1=a[0], wr1=a[1], pf1=a[2], exp0=b[3], exp1=a[3]))
        print(mode, "done", flush=True)
    T = pd.DataFrame(rows); T.to_csv("wrq_meta.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    T["dwr"] = T.wr1 - T.wr0; T["dpf"] = T.pf1 - T.pf0
    print(T.pivot_table(index=["mode", "mod"], columns="per", values=["dwr", "dpf"]).round(3).to_string())
