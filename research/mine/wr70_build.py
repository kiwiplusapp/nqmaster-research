import os, sys, pickle, ast, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, run_events
from families import FAMILIES
from families2 import FAMILIES2
os.chdir(RES)
from news import NEWS
VV3 = pickle.load(open("VV_plus3.pkl", "rb"))
out = {}
for tag, key in (("nq_1m", "nq"), ("mnq_fut", "mnq")):
    E = pd.read_pickle(f"variants_ext_{tag}.pkl"); E = E[E["mod"] != "GOLD"].copy(); E["u"] = E.usd - 0.9
    X = VV3[tag]; X = X[X["mod"].isin(["MSEQS", "MOM1130", "RSI2_0.15"])].copy(); X["u"] = X.usd - 0.9
    D = Data(tag + ".npz"); extra = []
    for fam, nm, ps in (("CLOCK_ANCHOR", "VW13", "{'anc': 'VWAP', 'T': 1300, 'x': 0.3, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}"),
                        ("CLOCK_ANCHOR", "VW13b", "{'anc': 'VWAP', 'T': 1300, 'x': 0.15, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}")) + tuple(
                        ("VOL_BREAK", f"VOLB_tf{tf}", f"{{'k': 0.45, 's': 0.35, 'R': {R}, 'tf': {tf}, 'w1': 1500, 'hold': 400, 'stop': 0}}") for tf in (0, 1) for R in (0.5, 0.75, 1.0, 2.0)):
        gen, grid, md = {**FAMILIES, **FAMILIES2}[fam]; p = ast.literal_eval(ps)
        df = run_events(D, gen(D, p), flat=955, maxday=md)
        df = pd.DataFrame(dict(date=df.date, mod=nm, var=p["R"], usd=df.usd, tin=D.sm[df.fi.to_numpy().astype(int)], tout=D.sm[df.xi.to_numpy().astype(int)] + 1, d=df.d, u=df.usd))
        extra.append(df)
    A = pd.concat([E, X] + extra, ignore_index=True); A["fomc"] = A.date.isin(NEWS["FOMC"]); A = A[~A.fomc]
    A["w"] = np.where(A["mod"] == "ICT", 2.0, 1.0)
    out[tag] = A; print(tag, A.groupby(["mod"]).size().to_dict(), flush=True)
pickle.dump(out, open("mine/wr70_variants.pkl", "wb"))
