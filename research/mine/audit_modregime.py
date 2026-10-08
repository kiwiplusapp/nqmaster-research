"""AUDIT step 6: module-level regime splits (daily ATR terciles computed on each sample, trend vs range day = |RTH close-open| / RTH range > 0.5,
descriptive only - the day type is not known in advance). PF of each module's trades as traded in its profile. -> audit_modregime.csv"""
import pickle, numpy as np, pandas as pd
A = pickle.load(open("audit_trades.pkl", "rb")); P = A["prof"]; FE = pickle.load(open("audit_dayfeats.pkl", "rb"))
def pfu(x): gl = -x[x <= 0].sum(); return round(float(x[x > 0].sum() / gl), 2) if gl > 0 and len(x) >= 15 else np.nan
rows = []
for prof in ("Ultra", "WR70N"):
    for lab, pers, key in (("CFD", ("IS", "C24"), "nq"), ("REAL", ("REAL",), "mnq")):
        F = pd.concat([P[prof][p][0] for p in pers]); D = np.concatenate([P[prof][p][1] for p in pers])
        fe = FE[key].reindex(D); q = fe.atr.quantile([1 / 3, 2 / 3]).to_numpy()
        atr_t = pd.Series(np.where(fe.atr < q[0], "ATR low", np.where(fe.atr < q[1], "ATR mid", "ATR high")), index=D)
        trend = pd.Series(np.where(fe.trendday.fillna(False).astype(bool), "trend", "range"), index=D)
        F = F.assign(x=F.u * F.w, atr_t=F.date.map(atr_t), td=F.date.map(trend))
        for m, g in F.groupby("mod"):
            r = dict(prof=prof, sample=lab, mod=m)
            for b in ("ATR low", "ATR mid", "ATR high"): r[b] = pfu(g.x[g.atr_t == b])
            for b in ("range", "trend"): r[b] = pfu(g.x[g.td == b])
            rows.append(r)
R = pd.DataFrame(rows); R.to_csv("audit_modregime.csv", index=False)
pd.set_option("display.width", 200); pd.set_option("display.max_rows", 200)
print(R.pivot_table(index=["prof", "mod"], columns="sample", values=["ATR low", "ATR mid", "ATR high", "range", "trend"]).round(2).to_string())
