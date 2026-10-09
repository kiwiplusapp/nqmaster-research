"""Federico 2026-10-09: 'why only 20% that live matches the backtest?'. Replace judgment numbers with a calculation.
For the recommended setups (final3y_acct.py vectors, REAL MNQ + MGC 2024-02..2026-09) run 600 resampled 12-month account
lifecycles for each edge haircut h (h x mean daily P&L removed from every day, eval and funded). Output per h:
P(year > 0), P(>= $1,200 / month), P(>= 80% of the backtest month), P(>= 50%), median and p10 / p90 of $ per month.
Then mix the h-scenarios with explicit weights (prior over how much of the edge survives) -> final3y_conf.json"""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import acct1c_lib as A
from final3y_acct import evarr, fuarr, FIRMS, BUF, nd, life_m

CASES = [("MyFundedFutures Rapid EOD 50K", "Ultra fixed", "Ultra 1c"),
         ("MyFundedFutures Rapid EOD 50K", "Ultra fixed", "Ultra 1c -> 2c from $3,000 cushion"),
         ("MyFundedFutures Rapid EOD 50K", "Ultra lean fixed", "Ultra lean 1c"),
         ("MyFundedFutures Rapid EOD 50K", "WR70Plus fixed", "WR70Plus 1c"),
         ("Lucid Flex 50K", "Ultra fixed", "Ultra 1c")]
HS = [0.0, 0.1, 0.2, 0.3, 0.35, 0.4, 0.5, 0.6, 0.75, 1.0]
# prior over the surviving edge (judgment, written down so it can be argued with): centred on the audit's 35% haircut
PRIOR = {0.0: 0.10, 0.2: 0.20, 0.35: 0.30, 0.5: 0.20, 0.75: 0.12, 1.0: 0.08}
NB = 600


def lifecycles(firm, ev, fn, h, IDX):
    F = FIRMS[firm]; t0, t1, t2, c1, c2 = F["funds"][fn]
    EL0, EC0, C = evarr(ev, F["G"], False); FL0, FC0 = fuarr((t0, t1, t2), F["news"], False)
    me = h * EC0.mean(1, keepdims=True); mf = h * FC0.mean(1, keepdims=True)
    EL = np.ascontiguousarray(EL0 - me); EC = np.ascontiguousarray(EC0 - me); FL = np.ascontiguousarray(FL0 - mf); FC = np.ascontiguousarray(FC0 - mf)
    okst = np.ones(nd, np.bool_); out = np.zeros((2, 9)); res = np.zeros(len(IDX))
    for q, idx in enumerate(IDX):
        if firm.startswith("Lucid"):
            A.life(EL, EC, C, 3000.0, 2000.0, F["cons"], okst, F["fee"], FL, FC, c1, c2, 0, 4000.0, 150.0, 2000.0, 2000.0, idx, 252, 252, out)
        else:
            life_m(EL, EC, C, 3000.0, 2000.0, F["cons"], 4, F["fee"], FL, FC, c1, c2, BUF[fn], 0, idx, 252, 252, out)
        res[q] = out[0, 0] / 12.0
    return res


if __name__ == "__main__":
    IDX = [A.boot_idx(nd, q, 253, 10, 31) for q in range(NB)]
    OUT = {"prior": {str(k): v for k, v in PRIOR.items()}, "cases": []}
    for firm, ev, fn in CASES:
        base = None; rows = []; dist = {}
        for h in HS:
            m = lifecycles(firm, ev, fn, h, IDX); dist[h] = m
            if h == 0.0: base = float(m.mean())
            rows.append(dict(h=h, mean=round(float(m.mean())), median=round(float(np.median(m))), p10=round(float(np.percentile(m, 10))),
                             p90=round(float(np.percentile(m, 90))), p_pos=round(100 * float((m > 0).mean()), 1),
                             p_1200=round(100 * float((m >= 1200).mean()), 1), p_80=round(100 * float((m >= 0.8 * base).mean()), 1),
                             p_50=round(100 * float((m >= 0.5 * base).mean()), 1)))
            print(firm[:5], ev, "|", fn, rows[-1], flush=True)
        mix = np.concatenate([np.random.default_rng(7).choice(dist[h], int(round(w * 6000))) for h, w in PRIOR.items()])
        comb = dict(mean=round(float(mix.mean())), median=round(float(np.median(mix))), p10=round(float(np.percentile(mix, 10))), p90=round(float(np.percentile(mix, 90))),
                    p_pos=round(100 * float((mix > 0).mean()), 1), p_1200=round(100 * float((mix >= 1200).mean()), 1),
                    p_80=round(100 * float((mix >= 0.8 * base).mean()), 1), p_50=round(100 * float((mix >= 0.5 * base).mean()), 1))
        print("  COMBINED", comb, flush=True)
        OUT["cases"].append(dict(firm=firm, eval=ev, funded=fn, backtest_month=round(base), rows=rows, combined=comb))
    json.dump(OUT, open("final3y_conf.json", "w"), indent=1)
