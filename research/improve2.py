import pickle, numpy as np, pandas as pd
from improve1 import perf
D = pickle.load(open("feat_trades.pkl", "rb"))
LATE = ["CRT11", "MOM13", "MSEQ", "MSEQS"]
def tag(F):
    F = F.sort_values(["date", "tin"]).copy()
    m11 = F[F["mod"] == "MOM11"].groupby("date").d.first()
    on = F[F["mod"].isin(["ON07", "REV06", "LON"])].groupby("date").d.agg(lambda s: np.sign(s.sum()))
    lon = F[F["mod"] == "LON"].groupby("date").d.first()
    F["m11"] = F.date.map(m11) * F.d; F["on"] = F.date.map(on) * F.d; F["lon_same"] = (F.date.map(lon) == F.d) & (F.tin > F.date.map(F[F["mod"] == "LON"].groupby("date").tin.first()))
    F["rev_bucket"] = F["mod"].isin(LATE) & (F.m11 == -1) & (F.on == 1) & (F.tin > (660 - 1080) % 1440)
    return F
RULES = {"MaxPlus actual": lambda F: F.base_w,
         "A: x2 tardío contra MOM11 + a favor overnight": lambda F: F.base_w * np.where(F.rev_bucket, 2.0, 1.0),
         "B: saltar REV06 si LON ya entró igual": lambda F: F.base_w * np.where((F["mod"] == "REV06") & F.lon_same, 0.0, 1.0),
         "A + B": lambda F: F.base_w * np.where(F.rev_bucket, 2.0, 1.0) * np.where((F["mod"] == "REV06") & F.lon_same, 0.0, 1.0)}
if __name__ == "__main__":
    T = {p: (tag(F), days) for p, (F, days) in D.items()}
    pickle.dump(T, open("feat_trades2.pkl", "wb"))
    for p, (F, days) in T.items():
        print(p, "REV06 w/ LON same:", int(((F["mod"] == "REV06") & F.lon_same).sum()), "| rev_bucket trades:", int(F.rev_bucket.sum()))
    rows = []
    for nm, fn in RULES.items():
        for p, (F, days) in T.items():
            r = perf(F, days, fn(F)); r.update(rule=nm, per=p); rows.append(r)
    g = pd.DataFrame(rows)
    for c in ("pf", "sharpe", "mo", "maxdd", "ret_dd"):
        print(c); print(g.pivot(index="rule", columns="per", values=c).reindex(list(RULES))[["IS", "C24", "REAL"]].to_string())
