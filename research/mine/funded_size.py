"""Funded sizing by cushion (Lucid 50K, payouts capped at min($2,000, 50%), 5 payouts): does trading 3 contracts once the cushion over
the EOD-trailing threshold is large reach payouts faster without more busts? Tiers by cushion: < c1 -> row0, < c2 -> row1, else row2.
Eval = final (UA+GR fixed 2). -> funded_size.csv"""
import sys; sys.path.insert(0, ".")
import pandas as pd
import lc_lib as L
E = "UA_FULL_GR"; S, N, F = "UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"
runs = {"final (SAFE<750<=NOB<1500<=FULL, 2c)": dict(fc=(S, N, F), fk=2.0, c1=750.0, c2=1500.0)}
for c2 in (2500.0, 3500.0, 5000.0):
    runs[f"SAFE 2c <750<= FULL 2c <{c2:.0f}<= FULL 3c"] = dict(fc=(S, F, F), fk=(2.0, 2.0, 3.0), c1=750.0, c2=c2)
    runs[f"SAFE 2c <1500<= FULL 2c <{c2:.0f}<= FULL 3c"] = dict(fc=(S, F, F), fk=(2.0, 2.0, 3.0), c1=1500.0, c2=c2)
runs["SAFE 1c <750<= NOB 2c <1500<= FULL 2c"] = dict(fc=(S, N, F), fk=(1.0, 2.0, 2.0), c1=750.0, c2=1500.0)
runs["SAFE 1c <1000<= FULL 2c <3500<= FULL 3c"] = dict(fc=(S, F, F), fk=(1.0, 2.0, 3.0), c1=1000.0, c2=3500.0)
out = []
for nm, p in runs.items():
    R, _ = L.run({nm: (E, p["fc"], L.FIXED2)}, fk=p["fk"], c1=p["c1"], c2=p["c2"]); out.append(R); print(nm, round(R.mo.mean()), round(R.mo.min()), flush=True)
R = pd.concat(out); R.to_csv("funded_size.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
print(R.pivot_table(index="cand", columns=["per", "test"], values="mo").round(0).to_string())
print(R.groupby("cand").agg(mean9=("mo", "mean"), min9=("mo", "min"), ploss=("ploss", "max"), fbust=("fbust", "mean"), payouts=("payouts", "mean")).round(2).sort_values("mean9", ascending=False).to_string())
