"""2026-10-15 follow-up of sniper_eval.py: is 'big size only on the 80%-WR trades' better than simply trading more contracts on every
trade? Same frame (UltraR + CPI09, real NQ 2020-26 minute paths, +1 tick, firm rules of month80.py, starts T1 2020-03..2023-10 / T2 2024..):
policies = base contracts b (1-4) on every trade, and the high-WR group sized m x b (m = 1, 2, 4, 6, 8):
  static: MOM1030 + CPI09 (what NQMaster does: tq = multiplier x Qty())
  wf80  : walk-forward trailing-year WR >= 80% (n >= 20) of the module.
Only settings whose peak simultaneous micros fit the firm's eval cap. -> sniper_uniform.csv / sniper_uniform.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from wrq_lib import getD
from month80 import SET, outcomes, serial_first
from sniper_eval import wf_flag, conc
from sniper_life import build

if __name__ == "__main__":
    E = RB.setup(); D = getD(RB.NAME)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]; n = len(days)
    T = build(E, D); flags = {"static": T["mod"].isin(["MOM1030", "CPI09"]).to_numpy(), "wf80": wf_flag(T, 0.80, 365, 20)}
    inday = T.date.isin(days).to_numpy(); T2 = T[inday]
    P = {}
    for nm, f in flags.items():
        ff = f[inday]; R0 = T2[~ff]; S1 = T2[ff].assign(w=1.0)
        P[nm] = (full_paths(R0, days), full_paths(S1, days), R0.w.groupby(R0.date).sum().reindex(days, fill_value=0).to_numpy(),
                 S1.w.groupby(S1.date).sum().reindex(days, fill_value=0).to_numpy(), conc(R0, days, D), conc(S1, days, D))
        print("paths", nm, flush=True)
    d24 = int(np.searchsorted(days, 20240101))
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 40]
    rows = []
    for grp in ("static", "wf80"):
        a, b, ca, cb, ka, kb = P[grp]
        for kb_ in (1, 2, 3, 4):
            for m in (1, 2, 4, 6, 8):
                if grp == "wf80" and m == 1: continue
                k = kb_ * m
                lw = kb_ * a[0] + k * b[0]; cl0 = kb_ * a[1] + k * b[1]; fn = kb_ * a[2] + k * b[2]; cc = kb_ * ca + k * cb; pk = (kb_ * ka + k * kb).max(1)
                mu1 = float(fn[:d24].mean()); mu2 = float(fn[d24:].mean())
                for firm, (Tg, Dd, cons, mind, dll, fee, mx) in SET.items():
                    if pk.max() > mx: continue
                    G = 0.9 * cons * Tg if cons > 0 else 0.0
                    rec = dict(group=grp, base=kb_, mult=m, firm=firm, peakmax=float(pk.max()), cap=mx)
                    for hc in (0.0, 0.35):
                        h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
                        lo, cl = vectors(lw - cc[:, None] - h[:, None], cl0 - cc[:, None] - h[:, None], fn - cc - h, G)
                        if dll > 0:
                            hit = lo <= -dll; cl = np.where(hit, -float(dll), cl); lo = np.where(hit, -float(dll), lo)
                        res, dd = outcomes(lo, cl, Tg, Dd, cons, mind, n); sfx = "" if hc == 0 else "_h35"
                        for tag, st in (("T1", s1), ("T2", s2)):
                            for w in (5, 10, 20): rec[f"{tag}_p{w}{sfx}"] = round(100 * float(np.mean([(res[s] == 1) and dd[s] < w for s in st])), 1)
                            rec[f"{tag}_bust{sfx}"] = round(100 * float(np.mean([res[s] == -1 for s in st])), 1)
                            se = [serial_first(res, dd, s, 20) for s in st]
                            rec[f"{tag}_serial20{sfx}"] = round(100 * float(np.mean([x for x, _ in se])), 1); rec[f"{tag}_evals{sfx}"] = round(float(np.mean([y for _, y in se])), 2)
                    rows.append(rec)
                print(grp, kb_, m, flush=True)
    R = pd.DataFrame(rows); R.to_csv(os.path.join(HERE, "sniper_uniform.csv"), index=False)
    OUT = {}
    for firm in SET:
        F = R[R.firm == firm]
        if not len(F): continue
        F = F.assign(score=F[["T1_p20", "T1_serial20"]].mean(1))
        b = F.sort_values("score", ascending=False).iloc[0]
        OUT[firm] = dict(chosen_on_T1=b.to_dict(), table=F.drop(columns="score").to_dict("records"))
        print(firm, "best on T1:", b.group, b.base, b.mult, "| p20", b.T1_p20, b.T2_p20, "| serial", b.T1_serial20, b.T2_serial20, "| h35", b.T2_p20_h35, b.T2_serial20_h35, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "sniper_uniform.json"), "w"), indent=1, default=float)
