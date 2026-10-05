"""Coordinate descent over module variants for a fixed 1-contract prop account, selected on IS (CFD 2020-23) only.
Each group takes one variant or none. Objective (eval): P(pass Lucid within 42 sessions) + 0.5 * P(pass within 21) - 0.3 * funded bust.
C24 (CFD 2024-26) and REAL (MNQ/MGC 2024-26) are out of sample."""
import os, sys, json, numpy as np, pandas as pd
sys.path.insert(0, ".")
from acct_lab import stats_for, META
GROUPS = {
    "ORB60": ["U:ORB60", "U1:ORB60", "W:ORB60"], "ORB90": ["U:ORB90", "U1:ORB90"], "MSEQ": ["U:MSEQ", "U1:MSEQ", "W:MSEQ"],
    "CRT11": ["U:CRT11", "U1:CRT11", "W:CRT11"], "ICT": ["U:ICT", "U1:ICT"], "MOM13": ["U:MOM13", "U1:MOM13"], "MSEQS": ["U:MSEQS"],
    "VOLB": ["U:VOLB", "C:VOLB_tf0", "W:VOLB_tf1"], "REV06": ["U:REV06", "W:REV06"], "VW13": ["U:VW13", "W:VW13b"], "LON": ["U:LON"],
    "MOM1030": ["U:MOM1030"], "MOM11": ["U:MOM11"], "ON07": ["U:ON07"], "LATE15": ["N:LATE15"], "ASIA": ["G:ASIA1R", "G:ASIA05"],
    "ENG0408": ["G:ENG0408"], "ENG0206": ["G:ENG0206"], "ENG0610": ["G:ENG0610"], "OD1030": ["G:OD1030"], "SVWAP22": ["G:SVWAP22"],
    "DRIVE11": ["G:DRIVE11"], "LATE1430": ["G:LATE1430"]}
START = {g: (v[0] if v[0].startswith("U:") else None) for g, v in GROUPS.items()}
def J(s): return s["L_p42"] + 0.5 * s["L_p21"] - 0.3 * s["F_bust"]
def mods_of(cfg): return [m for m in cfg.values() if m]
if __name__ == "__main__":
    cfg = dict(START); best = stats_for(mods_of(cfg), "IS"); bj = J(best)
    print("start", round(bj, 2), best, flush=True)
    for it in range(4):
        improved = False
        for g, opts in GROUPS.items():
            for o in [None] + opts:
                if o == cfg[g]: continue
                c2 = dict(cfg); c2[g] = o; s = stats_for(mods_of(c2), "IS"); j = J(s)
                if j > bj + 0.2: cfg, best, bj, improved = c2, s, j, True; print(f"  it{it} {g} -> {o}: J {bj:.2f}", {k: best[k] for k in ("L_pass", "L_p21", "L_p42", "L_days", "F_bust", "mo")}, flush=True)
        if not improved: break
    sel = mods_of(cfg); json.dump(sel, open("acct_opt_sel.json", "w"))
    print("SELECTED:", sel)
    ULTRA = [m for m in META["IS"] if m.startswith("U:")]
    rows = []
    for nm, mods in (("Ultra actual", ULTRA), ("Óptimo 1 contrato", sel)):
        for per in ("IS", "C24", "REAL"): rows.append(dict(set=nm, per=per, **stats_for(mods, per)))
    pd.set_option("display.width", 250); print(pd.DataFrame(rows).to_string(index=False))
