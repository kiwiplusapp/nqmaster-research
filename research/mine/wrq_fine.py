"""wrq_fine: fine parameter grids around the exit changes that improved WR and PF in every period of wrq_exits.py
(plateau check): NF05 time stop, VOLB break-even, MOM11 / MSEQ / MOM1030 / REV06 stop width, LATE15 target. -> wrq_fine.csv"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_lib import getD, PER, SLIP
from wrq_exits import arrays, sim, st, RUNS

GRIDS = {
    "NF05": [dict(ts=t) for t in (60, 75, 90, 105, 120, 135, 150, 165, 180, 210, 240)],
    "VOLB": [dict(be=b, beo=o) for b in (0.4, 0.5, 0.6, 0.75, 0.9, 1.0, 1.25, 1.5) for o in (0.0, 0.05, 0.1, 0.2, 0.3)],
    "VOLB_tf1": [dict(be=b, beo=o) for b in (0.25, 0.3, 0.4, 0.5) for o in (0.0, 0.05, 0.1)],
    "MOM11": [dict(ks=k) for k in (1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.5, 1.75, 2.0)] + [dict(ks=k, kt=0.9) for k in (1.25, 1.5)] + [dict(ks=k, kt=1.1) for k in (1.25, 1.5)],
    "MOM1030": [dict(ks=k) for k in (1.0, 1.1, 1.25, 1.4, 1.5, 1.75, 2.0)],
    "REV06": [dict(ks=k) for k in (1.0, 1.1, 1.25, 1.4, 1.5, 1.75, 2.0)],
    "MSEQ": [dict(ks=k, kt=t) for k in (1.0, 1.1, 1.2, 1.25, 1.3, 1.4, 1.5) for t in (0.9, 1.0, 1.1, 1.25)],
    "LATE15": [dict(kt=t, ks=k) for t in (0.5, 0.6, 0.67, 0.75, 0.8, 0.9, 1.0) for k in (0.9, 1.0, 1.1)],
}

if __name__ == "__main__":
    EN = pickle.load(open("wrq_entries.pkl", "rb")); rows = []
    for name in ("nq_1m.npz", "mnq_fut.npz", "nqhd_long.npz"):
        D = getD(name)
        for m, G in GRIDS.items():
            A = arrays(EN[name][EN[name]["mod"] == m])
            for lab, nm, slip, norm in RUNS:
                if nm != name: continue
                per = lab.replace("+4", ""); _, lo, hi = PER[per]
                msk = (A["date"] >= lo) & (A["date"] < hi) & (~A["fomc"] if per != "L15" else True)
                for p in [{}] + G:
                    u, ok, out = sim(A, D, slip, p, norm); k = ok & msk; n, wr, pff, ex, net = st(u[k])
                    rows.append(dict(mod=m, var=" ".join(f"{a}{b}" for a, b in p.items()) or "base", per=lab, n=n, wr=wr, pf=pff, exp=ex, net=net))
        print(name, flush=True)
    R = pd.DataFrame(rows); R.to_csv("wrq_fine.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
    for m in GRIDS:
        P = R[R["mod"] == m].pivot_table(index="var", columns="per", values=["wr", "pf"], sort=False)
        print("----", m); print(P[[("wr", "IS"), ("pf", "IS"), ("wr", "C24"), ("pf", "C24"), ("wr", "REAL"), ("pf", "REAL"), ("wr", "L15"), ("pf", "L15"), ("pf", "REAL+4"), ("pf", "C24+4")]].round(3).to_string())
