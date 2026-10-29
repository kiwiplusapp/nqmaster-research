import os, sys, json, time, numpy as np
os.chdir("/home/user/nqmaster-research/research/mine"); sys.path.insert(0, os.getcwd())
import pickle, prop_wf as P, objective as O, exp10_stress as X10, exp03_eval_size as E3
H, L = X10.H, X10.L
days, Mb, FU0, PER = O.setup()
rng_p = np.random.default_rng(4242); PP = {}
for hc in P.HC:
    for per, ii in PER.items(): PP[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, L, rng_p) for _ in range(1000)]
_, Pp = pickle.load(open(P.SRC, "rb"))
def mixes_eod(x):
    out = {}
    for cap, m in X10.MIXES:
        a, b, ca, cb = Pp[cap]; cc = ca + m * cb; LO, CL, FIN = Mb[(cap, m)]
        LO2 = LO.copy(); CL2 = CL.copy(); LO2[:, -1] -= x * cc; CL2[:, -1] -= x * cc
        out[(cap, m)] = (np.ascontiguousarray(LO2), np.ascontiguousarray(CL2), FIN - x * cc)
    return out
t0 = time.time()
for x in (1, 3):
    Mf = X10.mixes_x(Mb, x); Me = mixes_eod(x)
    for hc in (0.0, 0.35):
        for lab, M in (("dia entero desde el min 0 (exp10)", Mf), ("todo al cierre (cota optimista)", Me)):
            FU = X10.fund_x(days, Mb, M); AL, AM = X10.args(FU, hc, Mb, days)
            s = []
            for per, ii in PER.items():
                r, tot = X10.plan_cell(M, AL, AM, PP[(0.0, per)]); p22 = E3.p22(days, M, AL, ii)["p22_3"]
                s.append(f"{per} med {r['med_mes']:.0f} p10 {r['p10_mes']:.0f} neg60 {r['neg60']:.1f} aprob {r['aprobacion']:.1f} p22 {p22:.1f}")
            print(f"x{x} hc{hc} {lab}: " + " | ".join(s), flush=True)
# budget robustness: x = 1 at -35 % on the base's own -35 % paths
FU = X10.fund_x(days, Mb, X10.mixes_x(Mb, 1)); AL, AM = X10.args(FU, 0.35, Mb, days)
for per in ("T1", "T2"):
    r, tot = X10.plan_cell(X10.mixes_x(Mb, 1), AL, AM, PP[(0.35, per)]); print(f"x1 hc0.35 base -35% paths {per}: med {r['med_mes']:.0f} p10 {r['p10_mes']:.0f}", flush=True)
# more independent sets: T1 -35 % x0 p10
FU = X10.fund_x(days, Mb, X10.mixes_x(Mb, 0)); AL, AM = X10.args(FU, 0.35, Mb, days); M0 = X10.mixes_x(Mb, 0); v = []
ii = PER["T1"]
for seed in range(100, 120):
    g = np.random.default_rng(seed); paths = [P.boot_idx(ii[0], ii[-1] + 1, L, g) for _ in range(1000)]
    r, tot = X10.plan_cell(M0, AL, AM, paths); v.append(float(np.percentile(tot, 10)))
v = np.array(v); print("T1 hc0.35 x0 p10 over 20 more sets:", np.round(np.sort(v)).astype(int).tolist(), "mean", round(v.mean()), "sd", round(v.std(ddof=1)), "share < 1600", (v < 1600).mean(), "min", round(v.min()))
print("time", round(time.time() - t0))
