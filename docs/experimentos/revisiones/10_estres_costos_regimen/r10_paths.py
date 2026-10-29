import os, sys, json, time, numpy as np
os.chdir("/home/user/nqmaster-research/research/mine"); sys.path.insert(0, os.getcwd())
import prop_wf as P, objective as O, exp10_stress as X10
H, L = X10.H, X10.L
days, Mb, FU0, PER = O.setup()
rng_p = np.random.default_rng(4242); PP = {}
for hc in P.HC:
    for per, ii in PER.items(): PP[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, L, rng_p) for _ in range(1000)]
base = json.load(open("integ_port.json")); OB = json.load(open("objective_baseline.json"))
out = {}
def cell(x, hc, paths):
    Mx = X10.mixes_x(Mb, x); FU = X10.fund_x(days, Mb, Mx); AL, AM = X10.args(FU, hc, Mb, days)
    r, tot = X10.plan_cell(Mx, AL, AM, paths); return r, tot
def boot_stat(v, fn, B=4000, seed=1):
    g = np.random.default_rng(seed); n = len(v); s = np.array([fn(v[g.integers(0, n, n)]) for _ in range(B)])
    return float(s.std()), [float(np.percentile(s, 5)), float(np.percentile(s, 95))]
t0 = time.time()
# A) the haircut path: x=0 on the BASE paths of each edge must reproduce integ_port (med, p10, p25, p90, Pneg)
for hc in (0.35, 1.0):
    for per in ("T1", "T2"):
        r, tot = cell(0, hc, PP[(hc, per)]); ref = base[f"hc{hc} | {per} | coupon | rot"]
        mine = dict(med=round(np.median(tot)), p10=round(np.percentile(tot, 10)), p25=round(np.percentile(tot, 25)), p90=round(np.percentile(tot, 90)), Pneg=round(100 * float((tot < 0).mean()), 1))
        print(f"A hc{hc} {per} base paths x0: {mine} vs integ_port {[ref[k] for k in ('med','p10','p25','p90','Pneg')]}; mean {tot.mean():.0f} sd {tot.std():.0f}", flush=True)
        out[f"base_paths hc{hc} {per}"] = tot
# B) the experiment's paths (those of 'completo'), x = 0..1 for hc 0.35 and 1.0
for hc in (0.35, 1.0):
    for x in (0, 1):
        for per in ("T1", "T2"):
            r, tot = cell(x, hc, PP[(0.0, per)]); out[f"exp x{x} hc{hc} {per}"] = tot
            p10se, p10ci = boot_stat(tot, lambda v: np.percentile(v, 10)); mse = tot.std(ddof=1) / np.sqrt(len(tot))
            print(f"B x{x} hc{hc} {per}: med {np.median(tot):.0f} p10 {np.percentile(tot,10):.0f} (boot SE {p10se:.0f}, 90% {p10ci[0]:.0f}..{p10ci[1]:.0f}) mean {tot.mean():.0f} (SE {mse:.0f}, 95% {tot.mean()-1.96*mse:.0f}..{tot.mean()+1.96*mse:.0f})", flush=True)
for hc in (0.35, 1.0):
    for per in ("T1", "T2"):
        tb = out[f"base_paths hc{hc} {per}"]; p10se, p10ci = boot_stat(tb, lambda v: np.percentile(v, 10)); mse = tb.std(ddof=1) / np.sqrt(len(tb))
        print(f"B' base paths hc{hc} {per}: p10 {np.percentile(tb,10):.0f} (boot SE {p10se:.0f}, 90% {p10ci[0]:.0f}..{p10ci[1]:.0f}) mean {tb.mean():.0f} (SE {mse:.0f})", flush=True)
# paired difference x1 - x0 at zero edge (same paths)
for per in ("T1", "T2"):
    d = out[f"exp x1 hc1.0 {per}"] - out[f"exp x0 hc1.0 {per}"]; print(f"C paired mean diff x1-x0 hc1.0 {per}: {d.mean():.0f} (SE {d.std(ddof=1)/np.sqrt(len(d)):.0f})")
# D) independent path sets for hc0.35 x0: spread of p10 between sets of 1000 paths
for per in ("T1", "T2"):
    ii = PER[per]; vals = []; means = []
    for seed in (11, 12, 13, 14, 15, 16):
        g = np.random.default_rng(seed); paths = [P.boot_idx(ii[0], ii[-1] + 1, L, g) for _ in range(1000)]
        r, tot = cell(0, 0.35, paths); vals.append(float(np.percentile(tot, 10))); means.append(float(tot.mean()))
        if per == "T1" or True:
            r1, tot1 = cell(0, 1.0, paths); means.append(("hc1 mean", round(float(tot1.mean()))))
    print(f"D {per} hc0.35 x0 p10 over 6 independent sets of 1000 paths: {[round(v) for v in vals]} -> sd {np.std(vals, ddof=1):.0f}; hc1 means {[m for m in means if isinstance(m, tuple)]}", flush=True)
print("time", round(time.time() - t0))
np.savez("/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r10_tots.npz", **{k.replace(" ", "_"): v for k, v in out.items()})
