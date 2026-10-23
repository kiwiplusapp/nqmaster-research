"""flex50_choice.py (2026-10-23): Lucid Flex 50K purchase options (consistency 40% vs 50%, DLL OFF vs $1,200 soft) on the prop_wf
harness (NQ-only 2027 default, minute race, +1 tick). Eval sizes fix1x8 (Contracts 1 + EvalHighWrMultiplier 8) / fix2 (preset with Contracts 2).
Profit stop G = 0.9 x cons x 3000. Funded k2 c1000 X4000 (preset), DLL 0 / 1200 in the funded account. 12-month seat $/month median."""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_wf as P
days, M = P.build_mix(); n = len(days); idx = np.arange(n, dtype=np.int64)
s1 = np.nonzero(days < P.T1_END)[0]; s2 = np.nonzero((days >= P.T1_END) & (days < P.T2_END))[0]
FU = P.Fund(days, M); out = {}
for cons in (0.4, 0.5):
    F = dict(P.FIRMS["LucidFlex50K"]); F["cons"] = cons; F["G"] = 0.9 * cons * 3000; F["fee"] = 69.0
    for dll in (0, 1200):
        for pol in ("fix1x8", "fix2", "fix1"):
            p = P.eval_policies(F)[pol + " L0"]; ep = P.ep_of(F, p); ep[5] = float(dll)
            mix = (0, 8) if "x8" in pol else (0, 4); LO, CL, _ = M[mix]
            for hc in P.HC:
                H = P.haircut(days, M[mix][2], hc)
                res = np.zeros(n, np.int64); end = np.zeros(n, np.int64); P.race_all(LO, CL, H, idx, ep, res, end)
                # funded: k2 c1000 X4000 with/without the soft DLL, then a 12-month seat
                FL, FC, fp = FU.tiers(hc, "LucidFlex50K", (2, 1000, 0, 4000, 0))
                if dll:
                    rows = [FU.vec(hc, (300, 4), 2, 0, 0, float(dll)), FU.vec(hc, (0, 4), 2, 0, 0, float(dll))]
                    FL = np.ascontiguousarray(np.array([r[0] for r in rows])); FC = np.ascontiguousarray(np.array([r[1] for r in rows]))
                so = np.zeros((n, 7)); r = P.seat_all(LO, CL, H, ep, 69.0, FL, FC, fp, idx, 252, 1, so); so = so[:r]
                for per, st in (("T1", s1), ("T2", s2)):
                    m = P.eval_metrics(res, end, st, 69.0, n)
                    ss = so[[x for x in st if x < r and x + 252 <= n]]
                    key = f"c{int(cons*100)} dll{dll} {pol} hc{hc} {per}"
                    out[key] = dict(p22_1=round(m["p22_1"], 1), p22_3=round(m["p22_3"], 1), p120_1=round(m["p120_1"], 1),
                                    med_days=m["med_days22_3"], mo=round(float(np.median(ss[:, 0])) / 12, 0), evals_yr=round(float(ss[:, 1].mean()), 1))
                    print(key, out[key], flush=True)
json.dump(out, open("flex50_choice.json", "w"), indent=1)
