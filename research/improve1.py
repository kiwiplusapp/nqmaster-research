import pickle, numpy as np, pandas as pd
from news import NEWS
M = pickle.load(open("modpnl.pkl", "rb"))
def sets():
    P, F = M["nq_1m"]; Pr, Fr = M["mnq_fut"]
    yield "IS", F[F.date < 20240101].copy(), P.index[P.index < 20240101]
    yield "C24", F[F.date >= 20240101].copy(), P.index[P.index >= 20240101]
    yield "REAL", Fr.copy(), Pr.index
def feats(F):
    F = F.sort_values(["date", "tin"]).copy(); F["base_w"] = np.where(F["mod"] == "ICT", 2.0, 1.0)
    same = []; opp = []; orb_same = []
    for d, g in F.groupby("date", sort=False):
        prev = []
        for r in g.itertuples():
            earlier = [(m, dd) for (m, dd, t) in prev if t < r.tin]
            same.append(sum(1 for m, dd in earlier if dd == r.d)); opp.append(sum(1 for m, dd in earlier if dd == -r.d))
            orb_same.append(int(any(m in ("ORB60", "ORB90") and dd == r.d for m, dd in earlier)))
            prev.append((r.mod, r.d, r.tin))
    F["same"] = same; F["opp"] = opp; F["orb_same"] = orb_same
    F["cpi"] = F.date.isin(NEWS["CPI"]); F["nfp"] = F.date.isin(NEWS["NFP"])
    return F
def perf(F, days, w):
    x = F.u * w; d = x.groupby(F.date).sum().reindex(days, fill_value=0); eq = d.cumsum()
    xx = x[w > 0]
    return dict(sharpe=round(d.mean() / d.std() * np.sqrt(252), 2), pf=round(xx[xx > 0].sum() / -xx[xx <= 0].sum(), 3), mo=round(d.mean() * 21),
                maxdd=round((eq.cummax() - eq).max()), ret_dd=round(d.sum() / (eq.cummax() - eq).max(), 2), tpd=round((w > 0).sum() / len(days), 2))
def pf(u): return round(u[u > 0].sum() / -u[u <= 0].sum(), 2) if (u <= 0).any() and len(u) >= 15 else np.nan
if __name__ == "__main__":
    D = {per: (feats(F), days) for per, F, days in sets()}
    pickle.dump(D, open("feat_trades.pkl", "wb"))
    print("== PF by bucket (IS / C24 / REAL)")
    for lab, fn in (("no prior entries", lambda F: (F.same == 0) & (F.opp == 0)), ("prior SAME dir only", lambda F: (F.same > 0) & (F.opp == 0)),
                    ("prior OPP dir only", lambda F: (F.same == 0) & (F.opp > 0)), ("both", lambda F: (F.same > 0) & (F.opp > 0)),
                    ("after ORB same dir", lambda F: F.orb_same == 1), ("CPI day", lambda F: F.cpi), ("NFP day", lambda F: F.nfp)):
        s = " | ".join(f"{p}: n{fn(F).sum():4d} PF {pf(F.u[fn(F)])} WR {100*(F.u[fn(F)]>0).mean():.0f}%" for p, (F, days) in D.items())
        print(f"{lab:22s} {s}")
    print("\n== per module: PF prior SAME vs prior OPP vs none (IS/C24/REAL)")
    for m in sorted(D["IS"][0]["mod"].unique()):
        s = []
        for p, (F, days) in D.items():
            G = F[F["mod"] == m]
            s.append(f"{p} same {pf(G.u[(G.same>0)&(G.opp==0)])} opp {pf(G.u[(G.opp>0)&(G.same==0)])} none {pf(G.u[(G.same==0)&(G.opp==0)])}")
        print(f"{m:8s} " + " | ".join(s))
