import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, S
import filt_feats
from port_test import conflict_filter, metrics
A = pickle.load(open("wr70_variants.pkl", "rb")); sel_rules = pickle.load(open("filt_sel.pkl", "rb"))
CANDS = {
 "MaxPlus (referencia)": {"ORB60": 0.6, "ORB90": 0.6, "MSEQ": 0.5, "CRT11": 2.0, "LON": 2.0, "ICT": 1.0, "MOM11": 0.3, "MOM13": 1.0, "MOM1030": 0.3, "ON07": 1.0, "REV06": 0.3, "MSEQS": 0.75},
 "WR70-A": {"CRT11": 2.0, "ICT": 1.0, "MOM11": 0.3, "MSEQ": 0.5, "MSEQS": 0.75, "ORB60": 0.75, "ORB90": 0.6, "REV06": 0.3, "VOLB_tf1": 0.5, "VW13": 0.5, "VW13b": 0.5},
 "WR70-B": {"CRT11": 2.0, "ICT": 1.0, "MOM1030": 0.3, "MOM11": 0.3, "MSEQ": 0.5, "MSEQS": 0.75, "ORB60": 0.75, "ORB90": 0.6, "VOLB_tf1": 0.5, "VW13": 0.5, "VW13b": 0.5},
 "WR70-C": {"CRT11": 2.0, "ICT": 1.0, "MOM11": 0.3, "MOM1030": 0.3, "MSEQ": 0.5, "MSEQS": 0.75, "ORB60": 0.75, "ORB90": 0.6, "REV06": 0.3, "VOLB_tf1": 0.5, "VW13": 0.5, "VW13b": 0.5},
}
LATE = ["CRT11", "MOM13", "MSEQ", "MSEQS"]
def build(tag, prof, rules):
    X = A[tag]; X = pd.concat([X[(X["mod"] == m) & (X["var"] == v)] for m, v in prof.items()], ignore_index=True)
    X = conflict_filter(X.sort_values(["date", "tin"]).reset_index(drop=True))
    if not rules: return X
    X = X.sort_values(["date", "tin"]).copy()
    m11 = X[X["mod"] == "MOM11"].groupby("date").d.first()
    on = X[X["mod"].isin(["ON07", "REV06", "LON"])].groupby("date").d.agg(lambda s: np.sign(s.sum()))
    X["A"] = X["mod"].isin(LATE) & (X.date.map(m11) * X.d == -1) & (X.date.map(on) * X.d == 1) & (X.tin > S(1100))
    D = Data(tag + ".npz"); X = filt_feats.feats(D, X)
    b = pd.Series(1.0, index=X.index); keep = pd.Series(True, index=X.index)
    for r, k in sel_rules:
        x = X[r["feat"]]; m = ((X["mod"] == r["mod"]) & ((x < r["hi"]) if r["bucket"].startswith("low") else (x >= r["lo"]))).fillna(False)
        if k == "boost": b[m] = 2.0
        else: keep &= ~m
    base_w = X.w.copy(); w = base_w * np.where(X.A, 2.0, 1.0) * b
    X["w"] = np.minimum(w, np.maximum(base_w, 2.0)); return X[keep]
rows = []
for nm, prof in CANDS.items():
    for rules in (False, True):
        for tag in ("nq_1m", "mnq_fut"):
            X = build(tag, prof, rules)
            parts = [("IS", (X.date >= 20200201) & (X.date < 20240101)), ("C24", X.date >= 20240101), ("C24 2026", X.date >= 20260101)] if tag == "nq_1m" else [("REAL", X.date >= 20240201), ("REAL 2026", X.date >= 20260101)]
            for lab, m in parts:
                Y = X[m]; days = np.array(sorted(A[tag][(A[tag].date >= (20200201 if lab == "IS" else (20260101 if "2026" in lab else 20240101)))].date.unique()))
                if lab == "IS": days = days[days < 20240101]
                r = metrics(Y, days); r.update(v=nm + (" + reglas" if rules else ""), per=lab); rows.append(r)
g = pd.DataFrame(rows); pd.set_option("display.width", 250)
for c in ("wr", "pf", "sharpe", "mo", "maxdd", "tpd"):
    print(c); print(g.pivot(index="v", columns="per", values=c)[["IS", "C24", "REAL", "C24 2026", "REAL 2026"]].to_string())
