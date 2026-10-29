import os, sys, pickle, numpy as np, pandas as pd
os.chdir("/home/user/nqmaster-research/research/mine"); sys.path.insert(0, os.getcwd())
import robust2_build as RB
from wrq_lib import getD
D = getD(RB.NAME); print("data", RB.NAME, "pv", D.pv, "comm", D.comm)
X = pickle.load(open("cand16_trades.pkl", "rb"))["UltraR"][0]
E = pickle.load(open("wrq_entries_db.pkl", "rb"))
days = pickle.load(open(os.path.join(RB.SP, "acct2027_paths.pkl"), "rb"))[0]
X = X[X.date.isin(set(np.asarray(days).tolist()))]
k = E[["mod", "fi", "ent0", "et", "sl0", "tp0"]].drop_duplicates(["mod", "fi"])
X = X.merge(k, on=["mod", "fi"], how="left"); print("trades", len(X), "missing E", int(X.ent0.isna().sum()))
X = X.dropna(subset=["ent0"])
d = X.d.to_numpy(); xi = X.xi.to_numpy().astype(int); et = X.et.to_numpy()
e = X.ent0.to_numpy() + np.where(et == 0, d * 0.25, 0.0)
ex = e + d * (X.u.to_numpy() + D.comm) / D.pv
o, h, l, c = D.o[xi], D.h[xi], D.l[xi], D.c[xi]
time_ = np.isclose(ex, c - d * 0.25)
gapst = np.isclose(ex, o - d * 0.25) & ~time_
# target fill: long fills at max(o, tp) and needs h >= tp + tick; short fills at min(o, tp), needs l <= tp - tick; no slippage
tgt = np.where(d > 0, h >= ex + 0.25 - 1e-9, l <= ex - 0.25 + 1e-9) & ((ex - e) * d > 0) & ~time_ & ~gapst
stop = ~(time_ | gapst | tgt)
w = X.w.to_numpy()
print("exits (share of contract-trades): time", round((w * time_).sum() / w.sum(), 3), "gap stop", round((w * gapst).sum() / w.sum(), 3), "target (no slip)", round((w * tgt).sum() / w.sum(), 3), "stop (slip)", round((w * stop).sum() / w.sum(), 3))
print("entries limit (no slip) share of contract-trades", round((w * (et == 1)).sum() / w.sum(), 3))
sides_slip = (et == 0).astype(float) + (~tgt).astype(float)
print("ticks of slippage in u per round trip (weighted by contracts): mean", round((w * sides_slip).sum() / w.sum(), 3), "-> modeled $ per MNQ RT incl. cc tick:",
      round(D.comm + 0.5 * (w * sides_slip).sum() / w.sum() + 1.0, 2))
print(X.assign(tgt=tgt, lim=(et == 1)).groupby("mod")[["tgt", "lim"]].mean().round(2).to_string())
# refinement: exact target match against tp0 (kt = 1) = lower bound; heuristic above = upper bound; MOM1030 weighted x4 (mix (0,4))
tp0 = X.tp0.to_numpy()
tgt_lo = (np.isclose(ex, tp0) | ((d > 0) & (o > tp0) & np.isclose(ex, o)) | ((d < 0) & (o < tp0) & np.isclose(ex, o))) & ~time_
w2 = np.where(X["mod"].to_numpy() == "MOM1030", 4.0, w)
for lab, tg in (("target = tp0 exacto (cota baja)", tgt_lo), ("target heuristico (cota alta)", tgt)):
    ss = (et == 0).astype(float) + (~tg).astype(float); m = (w2 * ss).sum() / w2.sum()
    print(lab, "share target", round((w2 * tg).sum() / w2.sum(), 3), "slipped sides per RT", round(m, 3), "-> modeled $/MNQ RT", round(D.comm + 0.5 * m + 1.0, 2), "-> modeled slippage ticks per side", round((m + 2) / 2, 2))
