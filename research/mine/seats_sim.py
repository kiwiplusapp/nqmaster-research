"""Lucid household limits: 5 funded accounts, 10 accounts in total. Each funded 'seat' sits empty while its replacement eval runs
(~44% of the year at 150K 6c). Policy: for every empty seat keep up to P evals running (started at least G days apart, total
accounts <= 10); the first eval that passes fills an empty seat; a pass with no empty seat is lost (fee only). Day-by-day simulation of
5 seats on the same market path (same strategies -> correlated), 150K eval 6c / funded 3c with the night modules; 1,500 block-bootstrap
years per period from a cold start. -> seats_sim.csv"""
import sys, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, ".")
import prof_grid_lib
import lc_lib as LL
from acct_life import CFG
from acct_policy import vec
from acct_bigger import ACC
@njit(cache=True)
def run(LO, CL, F0, F1, c1, c2, X, T, D, Q, CAP, FEE, H, S, P, G, MAXACC):
    # eval state arrays (max 10)
    eon = np.zeros(10, np.bool_); eeq = np.zeros(10); epk = np.zeros(10); ebest = np.zeros(10)
    fon = np.zeros(S, np.bool_); fbal = np.zeros(S); fpk = np.zeros(S); flock = np.zeros(S, np.bool_); fqd = np.zeros(S, np.int64); fcyc = np.zeros(S); fm = np.zeros(S, np.int64)
    cash = 0.0; fees = 0.0; last_start = -999; nev = 0; npass = 0; nlost = 0; nbust = 0; seat_days = 0
    for d in range(H):
        # --- start evals for empty seats
        nf = 0
        for s in range(S):
            if fon[s]: nf += 1
        ne = 0
        for i in range(10):
            if eon[i]: ne += 1
        empty = S - nf
        if empty > 0 and ne < P * empty and nf + ne < MAXACC and d - last_start >= G:
            for i in range(10):
                if not eon[i]:
                    eon[i] = True; eeq[i] = 0.0; epk[i] = 0.0; ebest[i] = -1e9; fees += FEE; nev += 1; last_start = d; break
        # --- evals trade the day
        for i in range(10):
            if not eon[i]: continue
            thr = 100.0 if epk[i] >= D + 100.0 else epk[i] - D
            if eeq[i] + LO[d] <= thr: eon[i] = False; continue
            c = CL[d]; eeq[i] += c
            if c > ebest[i]: ebest[i] = c
            if eeq[i] > epk[i]: epk[i] = eeq[i]
            if eeq[i] >= T and ebest[i] <= 0.5 * eeq[i]:
                eon[i] = False; npass += 1; placed = False
                for s in range(S):
                    if not fon[s]:
                        fon[s] = True; fbal[s] = 0.0; fpk[s] = 0.0; flock[s] = False; fqd[s] = 0; fcyc[s] = 0.0; fm[s] = 0; placed = True; break
                if not placed: nlost += 1
        # --- funded accounts trade the day (from the next day after activation is approximated by same-day start; small effect)
        for s in range(S):
            if not fon[s]: continue
            seat_days += 1
            thr = 100.0 if (flock[s] or fpk[s] >= D + 100.0) else fpk[s] - D
            cu = fbal[s] - thr; j = 0 if cu < c1 else (1 if cu < c2 else 2)
            if fbal[s] + F0[j, d] <= thr: fon[s] = False; nbust += 1; continue
            c = F1[j, d]; fbal[s] += c
            if fbal[s] > fpk[s]: fpk[s] = fbal[s]
            if c >= Q: fqd[s] += 1
            if fqd[s] >= 5 and fbal[s] - fcyc[s] > 0 and fbal[s] >= X:
                amt = min(CAP, 0.5 * fbal[s])
                if amt >= 500.0:
                    fbal[s] -= amt; cash += 0.9 * amt; fm[s] += 1; fqd[s] = 0; fcyc[s] = fbal[s]; flock[s] = True
                    if fm[s] == 5: fon[s] = False
    return cash - fees, nev, npass, nlost, nbust, seat_days
EXTRA = ["N:NF05", "N:LF06", "N:LF0430"]
E = LL.define("UA_FULL_GR+NIGHT", CFG["UA_FULL_GR"] + EXTRA); F = tuple(LL.define(x + "+NIGHT", CFG[x] + EXTRA) for x in ("UA_SAFE_GR", "UA_NOB_GR", "UA_FULL_GR"))
POL = {"1 eval por plaza vacía (actual)": (1, 1), "2 evals por plaza, cada 3 días": (2, 3), "2 evals por plaza, cada 1 día": (2, 1), "3 evals por plaza, cada 2 días": (3, 2), "2 evals por plaza, cada 5 días": (2, 5)}
rows = []
for acc, ek, fk in (("150K", 6, 3), ("50K", 2, 2)):
    T, D, Q, CAP, FEE = ACC[acc]; sc = D / 2000.0
    for per in ("IS", "C24", "REAL"):
        ev = vec(per, E, 0.0, 0.4667 * T / ek); nd = len(ev[0]); LO = ek * ev[0]; CL = ek * ev[1]
        fv = [vec(per, c, 0.0, 0.0) for c in F]; F0 = fk * np.array([v[0] for v in fv]); F1 = fk * np.array([v[1] for v in fv])
        for nm, (P, Gp) in POL.items():
            rng = np.random.default_rng(11); out = []
            for b in range(1500):
                idx = np.concatenate([np.arange(s, s + 10) % nd for s in rng.integers(0, nd, 27)])[:252]
                out.append(run(LO[idx].copy(), CL[idx].copy(), F0[:, idx].copy(), F1[:, idx].copy(), 750.0 * sc, 1500.0 * sc, 2.0 * CAP, T, D, Q, CAP, FEE, 252, 5, P, Gp, 10))
            o = np.array(out)
            rows.append(dict(cuenta=acc, per=per, politica=nm, mes=round(o[:, 0].mean() / 12), p10=round(np.percentile(o[:, 0], 10) / 12), ploss=round(100 * (o[:, 0] < 0).mean(), 1),
                             evals=round(o[:, 1].mean(), 1), pasan=round(o[:, 2].mean(), 1), perdidas=round(o[:, 3].mean(), 2), quemadas=round(o[:, 4].mean(), 1), ocupacion=round(100 * o[:, 5].mean() / (5 * 252), 1)))
        print(acc, per, flush=True)
R = pd.DataFrame(rows); R.to_csv("seats_sim.csv", index=False); pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 40)
print(R.to_string(index=False))
print(R.pivot_table(index=["cuenta", "politica"], columns="per", values="mes").to_string())
