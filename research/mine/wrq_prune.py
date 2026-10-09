"""Joint test of the wrq_ trade-quality rules (already in NQMaster) with the audit_ pruning suggestions (2026-10-08):
Ultra final = VOLB break-even + ORB prior-close rule + MOM1030/MOM13 agreement, then minus ON07 / LATEFH / ENG10 / MOM13 / ORB90 and
ICT x1 instead of x2. WR70Plus final = ORB rule + VOLB 10:47 cutoff, then minus VOLB_tf1 / ORB90, ICT x1.
IS / C24 / REAL / 2015-19 (L15) and +4 ticks. -> wrq_prune.csv"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrq_port
from wrq_lib import SLIP
from wrq_port import metrics, days_of, ULTRA, WR70
from wrq_combo import build, BE, ORBt, VTSO
VAR = {
    "Ultra final": ("Ultra", {}, ()),
    "Ultra final -ON07": ("Ultra", {"drop": ["ON07"]}, ()),
    "Ultra final -ON07 -LATEFH -ENG10": ("Ultra", {"drop": ["ON07", "LATEFH", "ENG10"]}, ()),
    "Ultra final -ON07 -LATEFH -ENG10 -MOM13": ("Ultra", {"drop": ["ON07", "LATEFH", "ENG10", "MOM13"]}, ()),
    "Ultra final -ORB90": ("Ultra", {"drop": ["ORB90"]}, ()),
    "Ultra final ICT x1": ("Ultra", {"ict1": True}, ()),
    "WR70Plus final": ("WR70Plus", {}, ()),
    "WR70Plus final -VOLB_tf1": ("WR70Plus", {"drop": ["VOLB_tf1"]}, ()),
    "WR70Plus final -ORB90": ("WR70Plus", {"drop": ["ORB90"]}, ()),
    "WR70Plus final ICT x1": ("WR70Plus", {"ict1": True}, ()),
}
if __name__ == "__main__":
    rows = []
    for per, slip, tag in (("IS", SLIP, "IS"), ("C24", SLIP, "C24"), ("REAL", SLIP, "REAL"), ("L15", SLIP, "L15"), ("REAL", SLIP * 5, "REAL+4t")):
        days = days_of(per); cache = {}
        for nm, (base, opt, _) in VAR.items():
            src = ULTRA if base == "Ultra" else WR70
            prof = {k: v for k, v in src.items() if k not in opt.get("drop", [])}
            wrq_port.PROFILES["_tmp"] = prof
            wrq_port.BASE_W["ICT"] = 1.0 if opt.get("ict1") else 2.0
            over = {**BE, **ORBt} if base == "Ultra" else {**ORBt, **VTSO}
            over = {k: v for k, v in over.items() if k in prof}
            agr = tuple(m for m in ("MOM1030", "MOM13") if m in prof) if base == "Ultra" else ()
            X = build(per, "_tmp", over, agr, slip=slip, cache=None)
            r = metrics(X, days); r.update(variant=nm, per=tag); rows.append(r)
        wrq_port.BASE_W["ICT"] = 2.0
        print(tag, flush=True)
    R = pd.DataFrame(rows); R.to_csv("wrq_prune.csv", index=False)
    pd.set_option("display.width", 250)
    for c in ("wr", "pf", "sharpe", "mo", "maxdd", "tpd"):
        print("\n", c); print(R.pivot_table(index="variant", columns="per", values=c, sort=False).round(3 if c == "pf" else 2).to_string())
