import numpy as np, pandas as pd, pickle, sys
exec(open("conflict.py").read().split("for tag, lo, split")[0])
ap = open("apex_policy.py").read(); exec(ap[ap.index("def sim("):ap.index("POL = {")])
VV = pickle.load(open("VV_plus2.pkl", "rb"))
R = {"ORB60": 0.6, "ORB90": 0.6, "ORB45": 0.6, "MSEQ": 0.5, "CRT11": 2.0, "LON": 2.0, "ICT": 1.0, "MOM11": 0.3, "MOM13": 1.0, "MOM1030": 0.3, "ON07": 1.0, "REV06": 0.3, "MOM1130": 0.3, "RSI2_0.15": 0.3}
def prof(s): return {m: R[m] for m in s.split(",")}
def arrays(F, days):
    tot = np.zeros(len(days)); mn = np.zeros(len(days)); mx = np.zeros(len(days)); idx = {d: i for i, d in enumerate(days)}
    for d, g in F.groupby("date"):
        c = np.cumsum(g.sort_values("tout").u.to_numpy()); i = idx[d]; tot[i] = c[-1]; mn[i] = min(0, c.min()); mx[i] = max(0, c.max())
    return tot, mn, mx
def evaluate(P, apex=True):
    out = []
    for tag, lo in (("nq_1m", 20200201), ("mnq_fut", 20240201)):
        V = VV[tag][VV[tag].date >= lo]
        F = conflict_filter(pick(V, P).reset_index(drop=True)); F = F.assign(u=F.usd - 0.9)
        parts = [("IS", lambda x: x[x.date < 20240101]), ("C24", lambda x: x[x.date >= 20240101])] if tag == "nq_1m" else [("REAL", lambda x: x)]
        for lab, f in parts:
            x = f(F); days = np.array(sorted(f(V).date.unique())); dser = x.groupby("date").u.sum().reindex(days, fill_value=0)
            u = x.u; r = dict(per=lab, tpd=round(len(x) / len(days), 2), wr=round(100 * (u > 0).mean(), 1), pf=round(u[u > 0].sum() / -u[u <= 0].sum(), 3),
                              sharpe=round(dser.mean() / dser.std() * np.sqrt(252), 2), usd_mo=round(dser.mean() * 21), maxdd=round((dser.cumsum().cummax() - dser.cumsum()).max()))
            if apex and lab != "IS":
                t, mn, mx = arrays(x, days)
                a = sim(t, mn, mx, lambda e, p: 2 if p - e < 800 else 1, maxd=22); b = sim(t, mn, mx, lambda e, p: 1, maxd=44)
                r.update(apex_ad30=f"{a[0]:.0f}/{a[1]:.0f}", apex_f1_60=f"{b[0]:.0f}/{b[1]:.0f}")
            out.append(r)
    return pd.DataFrame(out)
if __name__ == "__main__":
    C = {"MaxSharpe": "ORB60,MSEQ,CRT11,LON,ICT,MOM11,MOM13,MOM1030,ON07,REV06",
         "MaxTrades": "ORB60,MSEQ,CRT11,LON,ICT,MOM11,MOM13,MOM1030,ON07,REV06,MOM1130,RSI2_0.15",
         "ALL14": ",".join(R),
         "S_top3": "ORB60,ORB90,ORB45,MSEQ,CRT11,LON,ICT,MOM11,MOM13,MOM1030,ON07,REV06,RSI2_0.15",
         "MS+ORB90+ORB45": "ORB60,ORB90,ORB45,MSEQ,CRT11,LON,ICT,MOM11,MOM13,MOM1030,ON07,REV06",
         "MS+ORB90": "ORB60,ORB90,MSEQ,CRT11,LON,ICT,MOM11,MOM13,MOM1030,ON07,REV06"}
    for k, s in C.items():
        print("==", k); print(evaluate(prof(s)).to_string(index=False))
