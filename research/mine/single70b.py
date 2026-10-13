"""2026-10-13 single eval >= 70%: clean protocol on top of single70.py (which mixed T1/T2 in its 'robust' view and let Bulenox Opt2
run without its mandatory DLL). Only settings NQMaster already has, 1 contract:
  profile Ultra  : low gear none / risk cap 150 / 200 / 300 (RiskCapPerContract below EvalRiskCapCushion) / Estable (EvalCushionFull)
  profile WR70Plus: low gear none / risk cap 200
  cushion C (0.4-1.3 x DD), account daily stop L (EvalDailyStop; Bulenox Opt2 = its own DLL or tighter)
Chosen on T1 (starts 2020-03..2023-10) per firm for p66 (~3 months) and p120 (~6 months, no time limit at these firms);
reported on T2 (starts 2024-01..2026-04), 35% edge haircut, 44-day block bootstrap 90% interval. -> single70b.json"""
import os, sys, json, pickle, itertools, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_life import SP
from single70 import run_starts, vec, metrics, FIRMS, H, WS


def boot(ok, blk=44, B=1000, seed=11):
    rng = np.random.default_rng(seed); nb = max(1, len(ok) // blk); out = []
    for _ in range(B):
        st = rng.integers(0, len(ok) - blk, nb); out.append(ok[np.concatenate([np.arange(a, a + blk) for a in st])].mean())
    return [round(100 * float(np.percentile(out, 5)), 1), round(100 * float(np.percentile(out, 95)), 1)]


if __name__ == "__main__":
    days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb")); n = len(days)
    d24 = int(np.searchsorted(days, 20240101))
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0].astype(np.int64)
    s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - H].astype(np.int64)
    SETS = {"U": ("UltraR", 0), "U150": ("UltraR", 150), "U200": ("UltraR", 200), "U300": ("UltraR", 300),
            "W": ("WR70R", 0), "W200": ("WR70R", 200), "E": ("Estable", 0)}
    VC = {}

    def V(key, G, L, hc):
        kk = (key, G, L, hc)
        if kk not in VC:
            low, close, fin = P[SETS[key]]; c = P[SETS[key] + ("cost",)]
            mu1 = fin[:d24].mean(); mu2 = fin[d24:].mean(); h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
            VC[kk] = vec(low - c[:, None] - h[:, None], close - c[:, None] - h[:, None], fin - c - h, G, L)
        return VC[kk]

    def sim(firm, low, full, C, L, hc, st):
        T, D, cons, mind, dll, mx = FIRMS[firm]; G = 0.9 * cons * T if cons > 0 else 0.0
        A = V(low or full, G, L, hc); B = V(full, G, L, hc)
        EL = np.ascontiguousarray(np.array([A[0], B[0], B[0]])); EC = np.ascontiguousarray(np.array([A[1], B[1], B[1]]))
        r = np.zeros(len(st), np.int64); o = np.zeros(len(st), np.int64)
        run_starts(EL, EC, float(C if low else 0), -1, float(T), float(D), float(cons), int(mind), st, H, r, o)
        return r, o

    FAM = [("U", None), ("U", "U150"), ("U", "U200"), ("U", "U300"), ("U", "E"), ("W", None), ("W", "W200")]
    rows = []
    for firm, (T, D, cons, mind, dll, mx) in FIRMS.items():
        Ls = [0.0, 0.3 * D, 0.45 * D, 0.6 * D] if dll == 0 else sorted(set([float(dll)] + [x for x in (0.3 * D, 0.45 * D, 0.6 * D) if x < dll]))
        for (full, low), C, L in itertools.product(FAM, [0.4 * D, 0.6 * D, 0.8 * D, 1.0 * D, 1.3 * D], Ls):
            if low is None and C != 0.4 * D: continue
            rec = dict(firm=firm, profile={"U": "Ultra", "W": "WR70Plus"}[full], low=low or "-", C=C if low else 0.0, L=L)
            for hc in (0.0, 0.35):
                for tag, st in (("T1", s1), ("T2", s2)):
                    m = metrics(*sim(firm, low, full, C, L, hc, st)); sfx = "" if hc == 0 else "_h35"
                    for k, v in m.items(): rec[f"{tag}_{k}{sfx}"] = v
            rows.append(rec)
    R = pd.DataFrame(rows); R.to_csv(os.path.join(HERE, "single70b_grid.csv"), index=False)
    OUT = {}
    for firm in FIRMS:
        F = R[R.firm == firm]; dll = FIRMS[firm][4]
        base = F[(F.profile == "Ultra") & (F.low == "-") & (F.L == float(dll))].iloc[0]
        for obj in ("p66", "p120"):
            b = F.sort_values([f"T1_{obj}", f"T1_p44"], ascending=False).iloc[0]
            low = None if b.low == "-" else b.low; full = "U" if b.profile == "Ultra" else "W"
            r, o = sim(firm, low, full, b.C, b.L, 0.0, s2); ci = {f"T2_ci90_p{w}": boot(((r == 1) & (o < w)).astype(float)) for w in (44, 66, 120)}
            rb, ob = sim(firm, None, "U", 0, float(dll), 0.0, s2); cib = {f"T2_ci90_p{w}": boot(((rb == 1) & (ob < w)).astype(float)) for w in (44, 66, 120)}
            key = f"{firm} | chosen on T1 for {obj}"
            OUT[key] = {"setting": dict(profile=b.profile, low=b.low, C=float(b.C), L=float(b.L)), **{c: (float(b[c]) if b[c] == b[c] else None) for c in R.columns if c[:3] in ("T1_", "T2_")}, **ci}
            OUT[f"{firm} | Ultra 1c, no gating"] = {**{c: (float(base[c]) if base[c] == base[c] else None) for c in R.columns if c[:3] in ("T1_", "T2_")}, **cib}
            print(f"{firm:26s} {obj:4s} -> {b.profile:8s} low {b.low:4s} C {b.C:5.0f} L {b.L:5.0f} | T1 " + "/".join(f"{b[f'T1_p{w}']:.0f}" for w in (20, 44, 66, 120)) +
                  " | T2 " + "/".join(f"{b[f'T2_p{w}']:.0f}" for w in (20, 44, 66, 120)) + f" CI {ci['T2_ci90_p120']} | h35 T1 {b[f'T1_{obj}_h35']:.0f} T2 {b[f'T2_{obj}_h35']:.0f}"
                  f" | med {b.T1_med_days}/{b.T2_med_days} | base T1 {base[f'T1_{obj}']:.0f} T2 {base[f'T2_{obj}']:.0f} h35 {base[f'T1_{obj}_h35']:.0f}/{base[f'T2_{obj}_h35']:.0f}", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "single70b.json"), "w"), indent=1)
