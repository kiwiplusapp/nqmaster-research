"""1-contract pass-probability study, step 3: PROTOCOLS. A bust is not the end of the month: a new eval can be bought the next day.
For each setup (policy chosen on T1 in smallacct_eval.py) and every start day s0 in T1 / T2:
  serial   : eval starts at s0; after a bust the next one starts the day after.
  stagger  : N seats start at s0, s0+g, s0+2g ... and each restarts after its own bust; the account that passes first is the funded one.
P(funded within 22 / 33 trading days), expected number of evals bought until then and expected eval fees.  -> smallacct_protocol.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from smallacct_eval import SETUPS, prep, run_starts, H
from robust2_life import SP


def outcomes(EL, EC, C, T, D, cons, mind, n):
    idx = np.arange(n, dtype=np.int64)
    return run_starts(EL, EC, C, T, D, cons, mind, idx, np.arange(n))


def serial(res, dd, s0, W):
    """returns (funded_offset or None, evals_bought_until_funded_or_W, fees_counted) for a seat starting at s0"""
    s = s0; k = 0; n = len(res)
    while s < n and s - s0 < W + 1:
        k += 1
        if res[s] == 1: return s + dd[s] - 1 - s0, k
        if res[s] == -1: s = s + dd[s]
        else: return None, k
    return None, k


def protocol(res, dd, starts, W, N, g, fee):
    f = []; cost = []; evals = []
    for s0 in starts:
        best = None; k_tot = 0
        seats = []
        for i in range(N):
            seats.append(serial(res, dd, s0 + i * g, W + 8) if s0 + i * g < len(res) else (None, 0))
        offs = [(o + i * g) if o is not None else None for i, (o, k) in enumerate(seats)]
        valid = [o for o in offs if o is not None]
        first = min(valid) if valid else None
        ok = first is not None and first <= W
        # evals bought by the time of the first funded day (or by W): count restarts only up to that day
        k_all = 0
        for i in range(N):
            si = s0 + i * g; t = si; k = 0
            horizon = (first if ok else W)
            while t < len(res) and t - s0 <= horizon:
                k += 1
                if res[t] == 1: break
                if res[t] == -1: t = t + dd[t]
                else: break
            k_all += k
        f.append(ok); evals.append(k_all); cost.append(k_all * fee)
    return round(100 * float(np.mean(f)), 1), round(float(np.mean(evals)), 2), round(float(np.mean(cost)))


if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))
    ev = json.load(open(os.path.join(HERE, "smallacct_eval.json"))); n = len(days)
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 50]
    OUT = {}
    for name, (T, D, cons, mind, dll, fee) in SETUPS.items():
        G = 0.9 * cons * T if cons > 0 else 0.0
        pk = ev[name]["pick"]; lname = pk["low"]; lcap = int("".join(ch for ch in lname if ch.isdigit()) or 0); lname = "Estable" if lname.startswith("Estable") else "UltraR"
        hi = prep(P, ("UltraR", 0), G, dll, False); lo_ = prep(P, (lname, lcap), G, dll, False)
        EL = np.ascontiguousarray(np.array([lo_[0], hi[0]])); EC = np.ascontiguousarray(np.array([lo_[1], hi[1]]))
        C = pk["f"] * D if pk["f"] > 0 else -1e9
        res, dd = outcomes(EL, EC, C, T, D, cons, mind, n)
        r = {}
        for lab, N, g in (("serial", 1, 0), ("2 seats +5d", 2, 5), ("3 seats +5d", 3, 5), ("3 seats +3d", 3, 3)):
            for W in (22, 33):
                a = protocol(res, dd, s1, W, N, g, fee); b = protocol(res, dd, s2, W, N, g, fee)
                r[f"{lab} W{W}"] = dict(T1=a, T2=b)
        OUT[name] = dict(policy=pk["low"] + f" f={pk['f']}", fee=fee, **r)
        print(f"{name:26s} fee {fee:4d} | serial W22 T1 {r['serial W22']['T1']} T2 {r['serial W22']['T2']} | 2 seats W22 T2 {r['2 seats +5d W22']['T2']} | 3 seats W22 T2 {r['3 seats +5d W22']['T2']} | serial W33 T2 {r['serial W33']['T2']}", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "smallacct_protocol.json"), "w"), indent=1)
