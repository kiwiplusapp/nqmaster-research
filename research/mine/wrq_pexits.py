"""wrq_pexits: portfolio-level effect (current Ultra and WR70Plus, rules + conflict filter) of the exit changes that survived
wrq_exits.py / wrq_fine.py, alone and combined, per period IS / C24 / REAL / L15 (2015-19 cost-normalised) and with +4 ticks
per side on every module. -> wrq_pexits.csv"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_port import build_profile, metrics, days_of
from wrq_lib import SLIP

CANDS = {
    "VOLB BE 0.75R->+0.1R": {"VOLB": (dict(be=0.75, beo=0.1), None)},
    "VOLB BE 0.5R->+0.05R": {"VOLB": (dict(be=0.5, beo=0.05), None)},
    "VOLB BE 1.0R->+0.1R": {"VOLB": (dict(be=1.0, beo=0.1), None)},
    "MSEQ stop 2.0x": {"MSEQ": (dict(ks=2.0 / 1.75), None)},
    "MOM11 stop x1.25": {"MOM11": (dict(ks=1.25), None)},
    "LATE15 target 0.33R": {"LATE15": (dict(kt=0.67), None)},
    "NF05 time stop 120m": {"NF05": (dict(ts=120), None)},
    "VOLB_tf1 BE 0.4R->+0.1R": {"VOLB_tf1": (dict(be=0.4, beo=0.1), None)},
}
CANDS["combo A (VOLB BE .75 + MSEQ 2.0x)"] = {**CANDS["VOLB BE 0.75R->+0.1R"], **CANDS["MSEQ stop 2.0x"]}
CANDS["combo B (A + MOM11 x1.25)"] = {**CANDS["combo A (VOLB BE .75 + MSEQ 2.0x)"], **CANDS["MOM11 stop x1.25"]}
CANDS["combo C (B + LATE15 .33R + NF05 120m)"] = {**CANDS["combo B (A + MOM11 x1.25)"], **CANDS["LATE15 target 0.33R"], **CANDS["NF05 time stop 120m"]}

if __name__ == "__main__":
    rows = []; cache = {}
    for prof, mods in (("Ultra", None), ("WR70Plus", None)):
        for per in ("IS", "C24", "REAL", "L15"):
            days = days_of(per)
            for slip, tag in ((SLIP, ""), (SLIP * 5, " +4t")):
                if per == "L15" and tag: continue
                for nm, over in [("base", None)] + list(CANDS.items()):
                    from wrq_port import PROFILES
                    if over and not any(m in PROFILES[prof] for m in over): continue
                    X = build_profile(per, prof, over, slip=slip, cache=cache)
                    m = metrics(X, days); m.update(prof=prof, per=per + tag, cand=nm); rows.append(m)
                print(prof, per, tag, flush=True)
    R = pd.DataFrame(rows); R.to_csv("wrq_pexits.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
    for prof in ("Ultra", "WR70Plus"):
        for c in ("wr", "pf", "sharpe", "mo", "maxdd", "tpd"):
            P = R[R.prof == prof].pivot_table(index="cand", columns="per", values=c, sort=False)
            print(f"==== {prof} {c}"); print(P.round(3 if c in ("pf", "sharpe") else 1).to_string())
