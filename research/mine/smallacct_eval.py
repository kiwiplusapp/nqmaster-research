"""1-contract pass-probability study, step 2: every firm / account size with a bot-friendly eval, Ultra (post-overhaul) at 1 contract per module,
gear policy = low gear (per-trade risk cap or Estable) while the cushion over the liquidation level is below f x drawdown, full profile above.
Starts: every trading day of T1 (2020-23, used to choose f and the low gear) and T2 (2024-26, check, nothing re-fitted). Rules per setup as in
propfirms_2026.md (EOD trailing, lock at start+100 when the peak passes DD+100; consistency enforced through a daily profit stop of 0.9 x c x target;
Bulenox Option 2 daily loss limit applied as a day stop). Pass within 22 trading days (~ one calendar month) and eventual (120 days).
-> smallacct_eval.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_life import vectors, SP
from mffu_rapid import ev_m

# name: (target, dd, consistency, min_days, dll, fee)
SETUPS = {
    "MFFU Rapid EOD 50K": (3000, 2000, 0.30, 4, 0, 157),
    "MFFU Rapid EOD 25K*": (1500, 1000, 0.30, 4, 0, 100),
    "Lucid Flex 50K": (3000, 2000, 0.50, 0, 0, 146),
    "Lucid Flex 25K": (1250, 1000, 0.50, 0, 0, 89),
    "Lucid Pro 50K": (3000, 2000, 0, 0, 0, 192),
    "Lucid Pro 25K": (1250, 1000, 0, 0, 0, 123),
    "FundedNext Rapid Pro 50K": (3000, 2000, 0, 0, 0, 150),
    "FundedNext Rapid Pro 25K": (1500, 1000, 0, 0, 0, 80),
    "Tradeify Select 25K": (1500, 1000, 0.40, 3, 0, 109),
    "Tradeify Growth 50K": (3000, 2000, 0, 1, 0, 150),
    "Bulenox Opt2 50K": (3000, 2500, 0, 0, 1100, 175),
    "Bulenox Opt2 25K": (1500, 1500, 0, 0, 500, 175),
}
LOWS = [("UltraR", 150), ("UltraR", 200), ("UltraR", 300), ("Estable", 0)]
FRACS = [0.0, 0.25, 0.5, 0.75, 1.0]
H = 120


def prep(P, key, G, dll, t1):
    low, close, fin = P[key]
    if t1:
        c = P[key + ("cost",)]; low = low - c[:, None]; close = close - c[:, None]; fin = fin - c
    lo, cl = vectors(low, close, fin, G)
    if dll > 0:
        hit = lo <= -dll
        cl = np.where(hit, -float(dll), cl); lo = np.where(hit, -float(dll), lo)
    return np.ascontiguousarray(lo), np.ascontiguousarray(cl)


def run_starts(EL, EC, C, T, D, cons, mind, idx, starts):
    n = len(idx); res = np.zeros(len(starts), np.int8); dd = np.zeros(len(starts), np.int32)
    for i, s in enumerate(starts):
        r, j = ev_m(EL, EC, float(C), float(T), float(D), float(cons), int(mind), idx, int(s), min(n, int(s) + H))
        res[i] = r; dd[i] = j - s + 1
    return res, dd


def stats(res, dd):
    ok = res != 0
    p22 = float(np.mean((res == 1) & (dd <= 22))); pe = float(np.mean(res == 1)); bust = float(np.mean(res == -1))
    med = float(np.median(dd[res == 1])) if (res == 1).any() else None
    return dict(p22=round(100 * p22, 1), pass_ever=round(100 * pe, 1), bust=round(100 * bust, 1), median_days=med, n=int(len(res)))


if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))
    n = len(days); idx = np.arange(n, dtype=np.int64)
    s1 = np.nonzero((days >= 20200301) & (days < 20240101))[0]; s2 = np.nonzero((days >= 20240101))[0]; s2 = s2[s2 < n - 120] if (n - 120) > s2[0] else s2[:len(s2) - 25]
    s1 = s1[s1 < n - 120]
    OUT = {}
    for name, (T, D, cons, mind, dll, fee) in SETUPS.items():
        G = 0.9 * cons * T if cons > 0 else 0.0
        best = None; rows = []
        for t1 in (False, True):
            hi = prep(P, ("UltraR", 0), G, dll, t1)
            for lname, lcap in LOWS:
                lo_ = prep(P, (lname, lcap), G, dll, t1)
                EL = np.ascontiguousarray(np.array([lo_[0], hi[0]])); EC = np.ascontiguousarray(np.array([lo_[1], hi[1]]))
                for f in FRACS:
                    C = f * D if f > 0 else -1e9
                    a = stats(*run_starts(EL, EC, C, T, D, cons, mind, idx, s1)); b = stats(*run_starts(EL, EC, C, T, D, cons, mind, idx, s2))
                    rows.append(dict(cost1tick=t1, low=f"{lname}{lcap or ''}", f=f, T1=a, T2=b))
        # choose on T1 without the extra tick: max P(<=22d)
        base = [r for r in rows if not r["cost1tick"]]
        pick = max(base, key=lambda r: r["T1"]["p22"] + 0.25 * r["T1"]["pass_ever"])
        stress = [r for r in rows if r["cost1tick"] and r["low"] == pick["low"] and r["f"] == pick["f"]][0]
        nogate = [r for r in base if r["f"] == 0.0][0]
        OUT[name] = dict(rules=dict(target=T, dd=D, cons=cons, mind=mind, dll=dll, fee=fee), pick=pick, pick_plus1tick=stress, no_gating=nogate)
        print(f"{name:26s} pick {pick['low']:>10s} f={pick['f']:<4} | T1 p22 {pick['T1']['p22']:5.1f} ever {pick['T1']['pass_ever']:5.1f} med {pick['T1']['median_days']} | T2 p22 {pick['T2']['p22']:5.1f} ever {pick['T2']['pass_ever']:5.1f} bust {pick['T2']['bust']:5.1f} med {pick['T2']['median_days']} | T2+1tick p22 {stress['T2']['p22']:5.1f} | no gating T2 p22 {nogate['T2']['p22']:5.1f}", flush=True)
        OUT[name]["all"] = rows
    json.dump(OUT, open(os.path.join(HERE, "smallacct_eval.json"), "w"), indent=1)
