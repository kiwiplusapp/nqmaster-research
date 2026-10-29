import os, sys, json, time, numpy as np
os.chdir("/home/user/nqmaster-research/research/mine"); sys.path.insert(0, os.getcwd())
import prop_wf as P, objective as O, exp10_stress as X10
H, L = X10.H, X10.L
days, Mb, FU0, PER = O.setup()
# 1) haircut used with x = 3 is the base one, not the one of the costed mix
Mx = X10.mixes_x(Mb, 3); FU = X10.fund_x(days, Mb, Mx); AL, AM = X10.args(FU, 0.35, Mb, days)
for mix in X10.MIXES:
    hb = P.haircut(days, Mb[mix][2], 0.35); hx = P.haircut(days, Mx[mix][2], 0.35)
    print(mix, "FU.h == base:", np.array_equal(FU.h(0.35, mix), hb), "| != costed:", not np.allclose(FU.h(0.35, mix), hx), "| T1 h base/costed", round(float(hb[0]), 2), round(float(hx[0]), 2))
print("eval Hh L150 == base:", np.array_equal(AL["Hh"], P.haircut(days, Mb[(0, 4)][2], 0.35)), " MFFU:", np.array_equal(AM["Hh"], P.haircut(days, Mb[(0, 8)][2], 0.35)))
print("FU.H keys only base-prefilled:", sorted(FU.H.keys()) == sorted([(hc, m) for hc in X10.HCS for m in X10.MIXES]))
# 2) is the 'completo' T1 path set adverse also at full edge / 2015-19 edge? p10 over independent sets
rng_p = np.random.default_rng(4242); PP = {}
for hc in P.HC:
    for per, ii in PER.items(): PP[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, L, rng_p) for _ in range(1000)]
M0 = X10.mixes_x(Mb, 0); FU = X10.fund_x(days, Mb, M0)
for hc in (0.0, 0.68):
    AL, AM = X10.args(FU, hc, Mb, days)
    for per in ("T1", "T2"):
        ii = PER[per]; r, t = X10.plan_cell(M0, AL, AM, PP[(0.0, per)]); v = []; md = []
        for seed in range(200, 208):
            g = np.random.default_rng(seed); paths = [P.boot_idx(ii[0], ii[-1] + 1, L, g) for _ in range(1000)]
            r2, t2 = X10.plan_cell(M0, AL, AM, paths); v.append(np.percentile(t2, 10)); md.append(np.median(t2))
        print(f"hc{hc} {per}: exp10 paths p10 {np.percentile(t,10):.0f} med {np.median(t):.0f} | 8 other sets p10 mean {np.mean(v):.0f} sd {np.std(v, ddof=1):.0f} range {min(v):.0f}..{max(v):.0f}; med mean {np.mean(md):.0f} sd {np.std(md, ddof=1):.0f}", flush=True)
