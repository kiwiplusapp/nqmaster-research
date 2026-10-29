"""r7_common.py: carga compartida para la revision del exp07 (solo importa; no escribe en el repo)."""
import os, sys, numpy as np
MINE = "/home/user/nqmaster-research/research/mine"
sys.path.insert(0, MINE); os.chdir(MINE)
import prop_wf as P, objective as O, exp03_eval_size as E3, exp07_pause_rules as X

L = X.L; H = X.H


def load():
    days, M, FU, PER = O.setup(); n = len(days)
    CONST = {"completo": 0.0, "-35%": 0.35, "cero": 1.0}
    ARc = {k: X.arrays(days, M, FU, hc) for k, hc in CONST.items()}; ARs = X.arrays_switch(days, M, FU)
    rng = np.random.default_rng(4242); paths = {}
    for hc in P.HC:
        for per, ii in PER.items(): paths[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, L, rng) for _ in range(1000)]
    return days, M, FU, PER, n, CONST, ARc, ARs, paths


def sw(bi, n, S):
    return bi + n * (np.arange(L) >= S)
