"""exp07_open_balance.py (2026-10-29, experimento 07, medicion prometida en el plan): saldo abierto de las fondeadas el dia de la pausa.
Saldo de una plaza al pausar = max(0, mtm(fin = p + 1)[p - 1] - mtm(fin = p)[p - 1]) (los dos recorridos son identicos hasta p - 1; el primero no
castiga el saldo en p - 1 y el segundo si). Cota superior del valor de la regla: contar 90 % de ese saldo como cobrado (en la realidad la cuenta
queda abierta: vale entre 0 y eso). Mismos caminos que exp07. -> exp07_open_balance.json"""
import os, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import prop_wf as P, objective as O, exp03_eval_size as E3, exp07_pause_rules as X
L = X.L; H = X.H; MAXEV = X.MAXEV


def open_bal(AR, idx, p):
    tot = 0.0
    for name, cnt in X.PLAN:
        A = AR["A"][name]; LO, CL, _ = AR["M"][A["mix"]]; FL, FC, fp = A["tiers"]
        for s in range(cnt):
            s0 = 5 * s
            if p >= s0 + H or p <= s0: continue
            r = []
            for end in (p, p + 1):
                f = np.zeros(L + 1); mm = np.zeros(L + 1); ev = np.zeros((MAXEV, 5)); O.seat_flow(LO, CL, A["Hh"], A["ep"], A["fee"], FL, FC, fp, idx, s0, end, f, mm, ev, A["act"]); r.append(mm[p - 1])
            tot += max(0.0, r[1] - r[0])          # una fondeada en perdida (saldo bajo el inicial, sin quebrar) vale 0, no negativo
    return tot


if __name__ == "__main__":
    days, M, FU, PER = O.setup(); n = len(days); NB = 1000
    CONST = {"completo": 0.0, "-35%": 0.35, "cero": 1.0}; ARc = {k: X.arrays(days, M, FU, hc) for k, hc in CONST.items()}; ARs = X.arrays_switch(days, M, FU)
    rng = np.random.default_rng(4242); paths = {}
    for hc in P.HC:
        for per, ii in PER.items(): paths[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(1000)]
    base = json.load(open(os.path.join(HERE, "exp07_pause_rules.json"))); OUT = {}
    SC = [(sc, ARc[sc], CONST[sc], None) for sc in CONST] + [("muere63", ARs, 0.0, 63), ("muere126", ARs, 0.0, 126)]
    for sc, AR, hc, S in SC:
        for per in PER:
            pp = paths[(hc, per)] if S is None else [bi + n * (np.arange(L) >= S) for bi in paths[(hc, per)]]
            net0 = np.array([X.plan_run(AR, bi, L)[4] for bi in pp])
            for rule in ("R1", "R4", "R14"):
                net = np.zeros(NB); ob = np.zeros(NB); pd = np.zeros(NB)
                for b, bi in enumerate(pp):
                    p = X.pause_day(AR["x"][bi], rule); pd[b] = p; net[b] = X.plan_run(AR, bi, p)[4]
                    if p < L: ob[b] = open_bal(AR, bi, p)
                up = net + 0.9 * ob / 12.0
                k = f"{sc} | {per} | {rule}"; g_lo = E3.paired(net, net0); g_up = E3.paired(up, net0)
                OUT[k] = dict(saldo_abierto_medio_en_pausa=float(ob[pd < L].mean()) if (pd < L).any() else 0.0, med_lo=float(np.median(net)), med_up=float(np.median(up)),
                              p10_lo=float(np.percentile(net, 10)), p10_up=float(np.percentile(up, 10)), pareado_lo=g_lo, pareado_up=g_up)
                print(f"{k:24s} saldo abierto medio al pausar {OUT[k]['saldo_abierto_medio_en_pausa']:8.0f} | med {OUT[k]['med_lo']:7.0f} -> {OUT[k]['med_up']:7.0f} | p10 {OUT[k]['p10_lo']:7.0f} -> {OUT[k]['p10_up']:7.0f} | "
                      f"P(gain) {g_lo['P_gain']:.2f} -> {g_up['P_gain']:.2f} P(loss>5%) {g_lo['P_loss5']:.2f} -> {g_up['P_loss5']:.2f}", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "exp07_open_balance.json"), "w"), indent=1)
