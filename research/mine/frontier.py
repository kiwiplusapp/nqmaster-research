"""Efficient frontier: max PF (IS) subject to WR >= w and trades/day >= t, over module x variant x size(1,2) choices;
then out-of-sample WR/PF/tpd of the IS-optimal mix. Uses the wr70_money daily matrices."""
import pickle, numpy as np, pandas as pd, random
exec(open("wr70_money.py").read().split("def obj(sel):")[0])
def solve(wmin, tmin, starts=120, seed=3):
    random.seed(seed); best = None
    def obj(sel):
        r = evalsel(sel, "IS")
        return r["pf"] - (max(0, wmin - r["wr"]) * 1.0 + max(0, tmin - r["tpd"]) * 2.0) * 10
    for _ in range(starts):
        sel = {m: random.choice(CHOICES[m]) for m in MODS}; imp = True
        while imp:
            imp = False
            for m in random.sample(MODS, len(MODS)):
                cur = obj(sel); bc = sel[m]
                for c in CHOICES[m]:
                    sel[m] = c; o = obj(sel)
                    if o > cur + 1e-9: cur = o; bc = c; imp = True
                sel[m] = bc
        o = obj(sel)
        if best is None or o > best[0]: best = (o, dict(sel))
    return best[1]
rows = []
for wmin, tmin in ((65, 4), (70, 4), (70, 3), (75, 4), (75, 3), (75, 2), (80, 4), (80, 2), (80, 1), (60, 1), (70, 1)):
    sel = solve(wmin, tmin)
    r = dict(cond=f"WR>={wmin}, trades/dia>={tmin}")
    for p in ("IS", "C24", "REAL"):
        e = evalsel(sel, p); r.update({f"{p}_wr": round(e["wr"], 1), f"{p}_pf": round(e["pf"], 2), f"{p}_tpd": round(e["tpd"], 2)})
    r["mods"] = " ".join(f"{m}:{c[0]}x{c[1]}" for m, c in sorted(sel.items()) if c is not None)
    rows.append(r); print(r, flush=True)
pd.DataFrame(rows).to_csv("frontier.csv", index=False)
