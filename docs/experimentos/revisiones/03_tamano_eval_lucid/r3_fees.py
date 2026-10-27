import sys, os, json, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine"); os.chdir("/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O
days, M, FU, PER = O.setup(); n = len(days); idx = np.arange(n, dtype=np.int64); F = P.FIRMS["LucidFlex150K"]; J = json.load(open("exp03_eval_size.json"))
for hc in P.HC:
    Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    for per, ii in PER.items():
        for k in (1, 2):
            ep = P.ep_of(F, (0, k, k, 0, 0, 0, 0)); res = np.zeros(n, np.int64); end = np.zeros(n, np.int64); P.race_all(M[(0, 4)][0], M[(0, 4)][1], Hm[(0, 4)], idx, ep, res, end)
            st = ii[ii + 22 <= n]; b22 = int(((res[st] == -1) & (end[st] - st < 22)).sum())
            # peor caida de 1c en los primeros 22 dias de cada inicio vs trailing 4500
            print(f"hc{hc} {per} k{k}: inicios {len(st)}, quiebres en < 22 d: {b22}; fees22_3 JSON {J['asiento'][f'L150 {k}c/3c | hc{hc} | {per}']['fees22_3']:.2f} = 215 x (1 + {J['asiento'][f'L150 {k}c/3c | hc{hc} | {per}']['fees22_3']/215-1:.4f})")
