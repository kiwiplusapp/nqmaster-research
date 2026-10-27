import sys, json, numpy as np
sys.path.insert(0, "/home/user/nqmaster-research/research/mine")
import prop_wf as P, objective as O, exp05_budget as E5, exp03_eval_size as E3
H = O.H; L = H + 25; MAXEV = O.MAXEV
B = json.load(open("/home/user/nqmaster-research/research/mine/objective_baseline.json")); X = json.load(open("/home/user/nqmaster-research/research/mine/exp05_budget.json"))
days, M, FU, PER = O.setup(); n = len(days); idx = np.arange(n, dtype=np.int64); hc = 0.0; per = "T2"; ii = PER[per]
Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}; AL, AM = O.seat_args(FU, hc, E5.L150, Hm), O.seat_args(FU, hc, E5.MF, Hm)
pp = [idx[s0:s0 + L] for s0 in np.arange(ii[0], ii[-1] + 2 - L, 5)]
for order in (((AM, 3), (AL, 5)), ((AL, 5), (AM, 3))):
    flows = np.zeros((len(pp), L)); mtms = np.zeros((len(pp), L)); tot = np.zeros(len(pp)); evs = []; nev = []
    for b, bi in enumerate(pp):
        ev_all = np.zeros((8 * MAXEV, 5)); kk = 0
        for A, cnt in order:
            for s in range(cnt):
                f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); k = O.run_seat(M, A, bi, 5 * s, H, f, mm, ev)
                flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + k] = ev[:k]; kk += k
        evs.append(ev_all); nev.append(kk)
    r = E3.plan_metrics(flows, mtms, evs, nev, tot); print("orden", "MFFU primero" if order[0][1] == 3 else "Lucid primero", "neg60_mtm", r["neg60_mtm"])
print("base", B["plan_contiguo"]["5 L150 + 3 MFFU | hc0.0 | T2 | coupon"]["neg60_mtm"], "exp05 sin", X["plan_contiguo"]["plan sin | hc0.0 | T2"]["neg60_mtm"])
for c in ("T1500", "T4000"):
    print(c, "contig hc0.35 T2 neg60", X["plan_contiguo"][f"plan {c} | hc0.35 | T2"]["neg60"])
