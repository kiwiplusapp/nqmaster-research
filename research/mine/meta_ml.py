"""Meta-labeling with walk-forward: P(win) per base trade from entry-time context; train on years < Y (CFD), test on Y
(CFD) and on real MNQ for Y >= 2024. Rules derived from TRAIN quantiles only: skip bottom q of lift, x2 top q of lift."""
import os, sys, pickle, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import S
B = pickle.load(open("base_feats.pkl", "rb"))
vix = pd.read_csv(os.path.join(os.path.dirname(os.getcwd()), "vix.csv"))
vix["d"] = vix.observation_date.str.replace("-", "").astype(int); vix = vix.set_index("d").VIXCLS.replace(".", np.nan).astype(float).ffill()
def prep(F):
    F = F.copy()
    F = F[F["mod"] != "LON"]                                    # LON entry times are not exact -> excluded from the model
    pre = F.tin < S(930)
    for c in ("gap", "open", "rng", "vw"): F.loc[pre, c] = np.nan
    F["hour"] = (F.tin + 1080) % 1440 / 60.0
    dd = pd.to_datetime(F.date.astype(str), format="%Y%m%d"); F["dow"] = dd.dt.dayofweek
    vi = vix.reindex(sorted(set(vix.index) | set(F.date))).ffill().shift(1)       # prior-day VIX
    F["vix"] = F.date.map(vi)
    # outcomes of the same day's trades that closed before this entry
    F = F.sort_values(["date", "tin"]); wins = []; losses = []; net = []
    for d, g in F.groupby("date", sort=False):
        rows = list(zip(g.tin, g.tout, g.u * g.w))
        for i, (ti, to, u) in enumerate(rows):
            prev = [x for (a, b, x) in rows[:i] if b <= ti]
            wins.append(sum(1 for x in prev if x > 0)); losses.append(sum(1 for x in prev if x <= 0)); net.append(sum(prev))
    F["pw"] = wins; F["pl"] = losses; F["pnet"] = net
    for m in sorted(F["mod"].unique()): F["m_" + m] = (F["mod"] == m).astype(int)
    F["y"] = F.date // 10000; F["win"] = (F.u > 0).astype(int)
    return F
FE = ["vw", "open", "rng", "pos", "trend", "gap", "pdret", "m30", "ret5", "atr", "pd", "svw", "hour", "dow", "vix", "pw", "pl", "pnet", "same", "opp", "d"]
C = prep(B["IS"][0]); C = pd.concat([C, prep(B["C24"][0])]); R = prep(B["REAL"][0])
MODS = [c for c in C.columns if c.startswith("m_")]
for m in MODS:
    if m not in R: R[m] = 0
X = FE + MODS
def metrics(F, days):
    x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0); eq = d.cumsum()
    return dict(n=len(F), wr=round(100 * (F.u > 0).mean(), 2), pf=round(x[x > 0].sum() / -x[x <= 0].sum(), 3), sharpe=round(d.mean() / d.std() * np.sqrt(252), 2), mo=round(d.mean() * 21))
res = []; allt = {"CFD": [], "REAL": []}
for Y in (2022, 2023, 2024, 2025, 2026):
    tr = C[C.y < Y]
    clf = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.04, max_iter=250, min_samples_leaf=60, l2_regularization=1.0, random_state=0)
    clf.fit(tr[X], tr.win)
    base_rate = tr.groupby("mod").win.mean()
    lift_tr = clf.predict_proba(tr[X])[:, 1] - tr["mod"].map(base_rate).to_numpy()
    lo_q, hi_q = np.quantile(lift_tr, 0.15), np.quantile(lift_tr, 0.85)
    for src, T in (("CFD", C[C.y == Y]), ("REAL", R[R.y == Y])):
        if not len(T): continue
        lift = clf.predict_proba(T[X])[:, 1] - T["mod"].map(base_rate).to_numpy()
        T = T.assign(lift=lift); allt[src].append(T.assign(lo=lo_q, hi=hi_q))
        days = np.array(sorted(T.date.unique()))
        b = metrics(T, days); s = metrics(T[T.lift >= lo_q], days); bo = metrics(T[T.lift >= lo_q].assign(w=lambda z: np.where(z.lift >= hi_q, np.minimum(z.w * 2, np.maximum(z.w, 2)), z.w)), days)
        res.append(dict(Y=Y, src=src, base=b, skip15=s, skip15_boost15=bo))
for r in res: print(r["Y"], r["src"], "| base", r["base"], "\n            skip", r["skip15"], "\n      skip+boost", r["skip15_boost15"])
for src in ("CFD", "REAL"):
    T = pd.concat(allt[src]); days = np.array(sorted(T.date.unique()))
    print("\nALL TEST YEARS", src, "base", metrics(T, days))
    print("   skip bottom15", metrics(T[T.lift >= T.lo], days))
    print("   skip15+boost15", metrics(T[T.lift >= T.lo].assign(w=lambda z: np.where(z.lift >= z.hi, np.minimum(z.w * 2, np.maximum(z.w, 2)), z.w)), days))
    # calibration: realized WR / PF by lift decile
    T["q"] = pd.qcut(T.lift, 5, labels=False)
    print("   by lift quintile:", T.groupby("q").apply(lambda g: (round(100 * (g.u > 0).mean(), 1), round((g.u[g.u > 0].sum()) / -(g.u[g.u <= 0].sum()), 2), len(g))).to_dict())
pickle.dump(allt, open("meta_ml_test.pkl", "wb"))
