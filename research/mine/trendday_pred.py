"""Can a trend day (|RTH close - open| / range > 0.5) be predicted with information available at 10:30 ET?
Features (all known at 10:30): opening-range 15/30/60 size / ATR, move 09:30->10:30 / ATR, efficiency of that move, gap / ATR,
overnight range / ATR, prior-day type and prior-day close location, ATR ratio (ATR / 60-day median), day of week.
Model: logistic regression fitted on CFD 2020-23; AUC out of sample on CFD 2024-26 and MNQ real 2024-26.
Then: Ultra trades entering after 10:30 bucketed by predicted probability (terciles from IS) -> PF per bucket."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, S
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
def day_table(D):
    rows = []
    for d in range(D.nd):
        a = D.ro[d]
        if a < 0 or D.atr[d] <= 0 or np.isnan(D.pdc[d]): continue
        e = D.de[d]; sm = D.sm[a:e + 1]
        if sm[-1] < S(1555): continue
        i1030 = a + np.searchsorted(sm, S(1030)) - 1; i945 = a + np.searchsorted(sm, S(945)) - 1; i1000 = a + np.searchsorted(sm, S(1000)) - 1
        if i1030 <= a or i945 < a or i1000 < a: continue
        A = D.atr[d]; o = D.o[a]
        rth_c = D.c[e if sm[-1] < S(1600) else a + np.searchsorted(sm, S(1600)) - 1]
        hi = D.h[a:e + 1].max(); lo = D.l[a:e + 1].min()
        on_lo = D.l[D.ds[d]:a].min() if a > D.ds[d] else np.nan; on_hi = D.h[D.ds[d]:a].max() if a > D.ds[d] else np.nan
        seg = D.c[a:i1030 + 1]; path = np.abs(np.diff(np.r_[o, seg])).sum()
        rows.append(dict(day=d, date=int(D.daydate[d]), A=A,
            or15=(D.h[a:i945 + 1].max() - D.l[a:i945 + 1].min()) / A, or30=(D.h[a:i1000 + 1].max() - D.l[a:i1000 + 1].min()) / A,
            or60=(D.h[a:i1030 + 1].max() - D.l[a:i1030 + 1].min()) / A, mv60=abs(D.c[i1030] - o) / A, er60=abs(D.c[i1030] - o) / path if path > 0 else 0,
            gap=abs(o - D.pdc[d]) / A, onr=(on_hi - on_lo) / A, trend_align=np.sign(D.c[i1030] - o) * D.trend[d],
            trendday=float(abs(rth_c - o) / (hi - lo) > 0.5) if hi > lo else 0.0))
    T = pd.DataFrame(rows)
    T["prev_td"] = T.trendday.shift(1); T["atr_ratio"] = T.A / T.A.rolling(60, min_periods=20).median().shift(1); T["dow"] = pd.to_datetime(T.date.astype(str)).dt.dayofweek
    return T.dropna()
FEATS = ["or15", "or30", "or60", "mv60", "er60", "gap", "onr", "trend_align", "prev_td", "atr_ratio"]
DN = Data("nq_1m.npz"); DM = Data("mnq_fut.npz")
TN = day_table(DN); TM = day_table(DM)
IS = TN[(TN.date >= 20200201) & (TN.date < 20240101)]; C24 = TN[TN.date >= 20240101]; RE = TM[TM.date >= 20240201]
mu = IS[FEATS].mean(); sd = IS[FEATS].std()
Z = lambda X: ((X[FEATS] - mu) / sd).to_numpy()
m = LogisticRegression(C=1.0, max_iter=2000).fit(Z(IS), IS.trendday)
for nm, X in (("IS", IS), ("C24", C24), ("REAL", RE)):
    p = m.predict_proba(Z(X))[:, 1]; print(nm, "days", len(X), "trend-day rate %.3f" % X.trendday.mean(), "AUC %.3f" % roc_auc_score(X.trendday, p))
print("coef:", dict(zip(FEATS, np.round(m.coef_[0], 3))))
# single-feature AUCs (sign-free)
for f in FEATS:
    a = [roc_auc_score(X.trendday, X[f]) for X in (IS, C24, RE)]; print(f, np.round(a, 3))
# bucket Ultra trades after 10:30 by predicted probability
T = pickle.load(open("robust_trades.pkl", "rb"))
q = np.quantile(m.predict_proba(Z(IS))[:, 1], [1 / 3, 2 / 3])
for per, X in (("IS", IS), ("C24", C24), ("REAL", RE)):
    F = T["Ultra"][per][0]; F = F[F.tin > S(1030)].copy()
    pmap = pd.Series(m.predict_proba(Z(X))[:, 1], index=X.date.to_numpy())
    F["p"] = F.date.map(pmap); F = F.dropna(subset=["p"]); F["b"] = np.digitize(F.p, q); F["x"] = F.u * F.w
    g = F.groupby("b").x.agg(n="size", net="sum", pf=lambda x: x[x > 0].sum() / -x[x <= 0].sum())
    print(per, "Ultra trades after 10:30 by predicted trend-day prob (low/mid/high):"); print(g.round(2).to_string())
# ---- sizing test: boost trades after 10:30 on predicted trend days (weights chosen from a small fixed menu, judged on all periods)
def met(F, days, w):
    x = F.u * w; d = x.groupby(F.date).sum().reindex(days, fill_value=0.0); eq = d.cumsum()
    return dict(pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3), sharpe=round(d.mean() / d.std() * 252 ** .5, 2), mo=round(d.mean() * 21), dd=round((eq.cummax() - eq).max()))
rows = []
for prof in ("Ultra", "WR70Plus"):
    for nm, fac in (("base", (1, 1, 1)), ("alto x1.5", (1, 1, 1.5)), ("alto x2", (1, 1, 2)), ("bajo x0.5", (0.5, 1, 1)), ("bajo x0.5 alto x1.5", (0.5, 1, 1.5)), ("medio+alto x1.5", (1, 1.5, 1.5)), ("prob lineal", None)):
        r = dict(prof=prof, rule=nm)
        for per, X in (("IS", IS), ("C24", C24), ("REAL", RE)):
            F, days = T[prof][per]; F = F.copy()
            pmap = pd.Series(m.predict_proba(Z(X))[:, 1], index=X.date.to_numpy()); F["p"] = F.date.map(pmap)
            late = (F.tin > S(1030)) & F.p.notna()
            b = np.digitize(F.p.fillna(0.5), q)
            if fac is None: f = np.where(late, np.clip(F.p.fillna(0.5) / 0.5, 0.5, 1.5), 1.0)
            else: f = np.where(late, np.array(fac)[b], 1.0)
            mm = met(F, days, F.w * f); r.update({f"{per}_{k}": v for k, v in mm.items()})
        rows.append(r)
G = pd.DataFrame(rows); pd.set_option("display.width", 250)
for k in ("sharpe", "pf", "mo", "dd"):
    print(k); print(G[["prof", "rule"] + [f"{p}_{k}" for p in ("IS", "C24", "REAL")]].to_string(index=False))
pickle.dump(dict(mu=mu, sd=sd, coef=m.coef_[0], intercept=m.intercept_[0], q=q, feats=FEATS), open("trendday_model.pkl", "wb"))
