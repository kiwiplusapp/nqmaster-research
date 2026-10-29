import os, sys, pickle, numpy as np
os.chdir("/home/user/nqmaster-research/research/mine"); sys.path.insert(0, os.getcwd())
import prop_wf as P, exp10_stress as X10
days, Mb = P.build_mix()
dd, Pp = pickle.load(open(P.SRC, "rb"))
print("days equal:", np.array_equal(np.asarray(dd), days), len(days))
print("LO shape", Mb[(0,4)][0].shape)
# 1) cc embedded in the cached base mix: at the first minute of the session no position is open -> CL_b[:,0] = -cc
for cap, m in X10.MIXES:
    a, b, ca, cb = Pp[cap]; cc = ca + m * cb
    LO, CL, FIN = Mb[(cap, m)]
    print((cap, m), "CL_b[:,0] == -cc:", np.allclose(CL[:, 0], -cc), "max|dif|", float(np.abs(CL[:, 0] + cc).max()),
          "| a,b,g at min0 ~0:", float(np.abs(a[1][:, 0]).max()), float(np.abs(b[1][:, 0]).max()), "| mean cc/day", round(float(cc.mean()), 2),
          "| days cc>0", int((cc > 0).sum()))
# 2) cap-0 mixes differ only by 4*(b - cb)
a, b, ca, cb = Pp[0]
d = Mb[(0, 8)][2] - Mb[(0, 4)][2]; print("FIN(0,8)-FIN(0,4) == 4(b-cb):", np.allclose(d, 4 * (b[2] - cb)))
d = Mb[(0, 8)][1] - Mb[(0, 4)][1]; print("CL(0,8)-CL(0,4) == 4(b-cb):", np.allclose(d, 4 * (b[1] - cb[:, None])))
# 3) implied gold path identical across caps (so cc of each cap is the one in its own mix)
g = {}
for cap, m in X10.MIXES:
    a, b, ca, cb = Pp[cap]; cc = ca + m * cb
    g[(cap, m)] = a[2] + m * b[2] - cc - Mb[(cap, m)][2]
print("implied gold FIN equal (0,4) vs (0,8):", np.allclose(g[(0,4)], g[(0,8)]), " (0,4) vs (300,4):", np.allclose(g[(0,4)], g[(300,4)]))
print("implied gold FIN mean/day", float(g[(0,4)].mean()), "nonzero days", int((np.abs(g[(0,4)]) > 1e-9).sum()))
try:
    from seats_plan import gold_paths
    gg = gold_paths(days, "Robust"); print("gold_paths rebuilt; FIN equal to implied:", np.allclose(gg[2], g[(0,4)]))
except Exception as e:
    print("gold_paths not rebuilt:", type(e).__name__, str(e)[:120])
# 4) mixes_x subtracts exactly x*cc from LO, CL, FIN of each mix
for x in (1, 3):
    Mx = X10.mixes_x(Mb, x)
    for cap, m in X10.MIXES:
        a, b, ca, cb = Pp[cap]; cc = ca + m * cb
        ok = all(np.allclose(Mb[(cap, m)][q] - Mx[(cap, m)][q], x * (cc[:, None] if q < 2 else cc)) for q in range(3))
        print(f"x={x} {(cap, m)} Mb - Mx == x*cc (LO, CL, FIN):", ok)
# 5) contract-trades: units (MNQ). a single (0,4) day mean: ca vs cb
a, b, ca, cb = Pp[0]
print("ca mean", round(float(ca.mean()), 2), "cb mean", round(float(cb.mean()), 2), "cc(0,4) mean", round(float((ca + 4 * cb).mean()), 2), "cc(0,8)", round(float((ca + 8 * cb).mean()), 2))
i1 = days < P.T1_END; i2 = (days >= P.T1_END) & (days < P.T2_END)
for mix in X10.MIXES:
    a, b, ca, cb = Pp[mix[0]]; cc = ca + mix[1] * cb; F = Mb[mix][2]
    print(mix, "T1: FIN mean", round(float(F[i1].mean()), 1), "cc mean", round(float(cc[i1].mean()), 2), " T2: FIN mean", round(float(F[i2].mean()), 1), "cc mean", round(float(cc[i2].mean()), 2),
          " -> 1 tick/side = % of daily edge T1", round(100 * float(cc[i1].mean() / F[i1].mean()), 1), "T2", round(100 * float(cc[i2].mean() / F[i2].mean()), 1))
