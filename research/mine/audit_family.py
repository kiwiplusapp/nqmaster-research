"""AUDIT step 3 (mined / night / gold modules): selection bias and parameter plateaus inside each module's family.
For every module the WHOLE family grid it was picked from is re-run (CFD 2020-26 and futures 2024-26, FOMC skipped):
  PBO (CSCV, S=16) of 'pick the best config of the family' on CFD 2020-26 daily P&L (configs with >= 100 trades);
  IS -> OOS: rank configs on IS (2020-23) PF, median C24 / REAL PF of the top 1 / 10 / 50, Spearman(IS PF, REAL PF);
  rank of the chosen config's REAL PF inside the family;
  plateau: every one-parameter neighbour of the chosen config (adjacent value for numeric params, any other value for
  categorical ones) -> PF IS / C24 / REAL and 2015-19 cost-normalised (NQ: nqhd_long 0.345% ATR; gold: xau_long 2015-19 0.96%).
Output: audit_family.json, audit_neighbours.csv"""
import os, sys, json, math, itertools, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data, run_events
from run_mine import FAMILIES
from news import NEWS
FOMC = np.array(sorted(NEWS["FOMC"]))
MODS = {   # module: (instrument, family, params)
    "VOLB(U)": ("nq", "VOL_BREAK", {'k': 0.45, 's': 0.35, 'R': 2.0, 'tf': 0, 'w1': 1500, 'hold': 400, 'stop': 0}),
    "VOLB(W)": ("nq", "VOL_BREAK", {'k': 0.45, 's': 0.35, 'R': 0.5, 'tf': 1, 'w1': 1500, 'hold': 400, 'stop': 0}),
    "VW13(0.30)": ("nq", "CLOCK_ANCHOR", {'anc': 'VWAP', 'T': 1300, 'x': 0.3, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}),
    "VW13b(0.15)": ("nq", "CLOCK_ANCHOR", {'anc': 'VWAP', 'T': 1300, 'x': 0.15, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}),
    "LATE15": ("nq", "LATE_MOM", {'T': 1500, 'sig': 'RTH', 'x': 0.5, 'tf': 1, 'k': 0.3, 'R': 0.5}),
    "LATEFH": ("nq", "LATE_MOM", {'T': 1500, 'sig': 'FHRTH', 'x': 0.25, 'tf': 0, 'k': 0.2, 'R': 0.5}),
    "ENG10": ("nq", "ENGULF_4H", {'eng': '0610v0206@1000', 'ent': 2, 'R': 0.5, 'stop': 1, 'trend': 1, 'w1': 1130, 'body': 2}),
    "NF05": ("nq", "G_DRIVE", dict(A=2000, T=540, x=0.35, mode=-1, tf=0, k=0.2, stop=0, R=2.0, hold=240)),
    "LF06": ("nq", "NQ_DRIVE", dict(A=400, T=120, x=0.2, mode=-1, tf=0, k=0.2, stop=0, R=0.5, hold=240)),
    "LF0430": ("nq", "NQ_DRIVE", dict(A=400, T=30, x=0.1, mode=-1, tf=1, k=0.35, stop=0, R=0.5, hold=240)),
    "G:ENG0408": ("gold", "ENGULF_4H", {'eng': '0408v0004@0930', 'ent': 2, 'R': 0.5, 'stop': 2, 'trend': 0, 'w1': 1500, 'body': 2}),
    "G:SVWAP22": ("gold", "CLOCK_ANCHOR", {'anc': 'SVWAP', 'T': 2200, 'x': 0.3, 'mode': -1, 's': 0.25, 'R': 0.5, 'tg': 0, 'tf': 0, 'hold': 120}),
    "G:OD1030": ("gold", "OPEN_DRIVE", {'T': 60, 'x': 0.3, 'stop': 0, 'R': 0.5, 'tf': 1, 'hold': 400}),
    "G:ASIA1R": ("gold", "G_ORB", {'A': 2000, 'T': 240, 'W': 360, 'cap': 0.6, 'R': 1.0, 'tf': 1, 'hold': 600}),
    "G:ENG0206": ("gold", "ENGULF_4H", {'eng': '0206v2202@0930', 'ent': 2, 'R': 0.5, 'stop': 2, 'trend': 0, 'w1': 1500, 'body': 2}),
}
FLAT = {"nq": 955, "gold": 1010}; NC = {"nq": 0.00345, "gold": 0.0096}
def pfu(u):
    u = np.asarray(u); gl = -u[u <= 0].sum(); return float(u[u > 0].sum() / gl) if gl > 0 and len(u) >= 20 else np.nan
def run(D, fam, p, inst, nc=None):
    gen, grid, md = FAMILIES[fam]
    df = run_events(D, gen(D, p), flat=FLAT[inst], maxday=md, slip=0.0 if nc else 0.25, norm_cost=nc)
    return df[~np.isin(df.date.to_numpy(), FOMC)]
def pbo(M, S=16):
    n, N = M.shape; b = np.array_split(np.arange(n), S)
    s1 = np.array([M[ix].sum(0) for ix in b]); s2 = np.array([(M[ix] ** 2).sum(0) for ix in b]); cnt = np.array([len(ix) for ix in b], float)
    combs = np.array([[i in c for i in range(S)] for c in itertools.combinations(range(S), S // 2)], float)
    lam, deg = [], []
    for k0 in range(0, len(combs), 800):
        C = combs[k0:k0 + 800]; O = 1 - C
        def sh(W):
            m = (W @ s1) / (W @ cnt)[:, None]; v = (W @ s2) / (W @ cnt)[:, None] - m * m; return m / np.sqrt(np.maximum(v, 1e-12))
        a = sh(C); o = sh(O); k = a.argmax(1); ok = o[np.arange(len(k)), k]
        rk = (o < ok[:, None]).mean(1) + 0.5 * (o == ok[:, None]).mean(1); rk = np.clip(rk, 1 / N, 1 - 1 / N)
        lam.append(np.log(rk / (1 - rk))); deg.append(np.c_[a[np.arange(len(k)), k], ok])
    lam = np.concatenate(lam); deg = np.concatenate(deg)
    return dict(PBO=round(float((lam <= 0).mean()), 3), median_logit=round(float(np.median(lam)), 2), N=int(N),
                IS_best_sharpe=round(float(deg[:, 0].mean() * 252 ** .5), 2), OOS_sharpe_of_IS_best=round(float(deg[:, 1].mean() * 252 ** .5), 2), P_OOS_loss=round(float((deg[:, 1] < 0).mean()), 3))
def neighbours(grid, p):
    keys = list(p); vals = {k: sorted({g[k] for g in grid if k in g}, key=lambda v: (isinstance(v, str), v)) for k in keys}
    out = []
    for j, g in enumerate(grid):
        diff = [k for k in keys if g.get(k) != p[k]]
        if len(diff) != 1 or set(g) != set(p): continue
        k = diff[0]; v = vals[k]
        if isinstance(p[k], str): out.append((j, k, g[k])); continue
        i0, i1 = v.index(p[k]), v.index(g[k])
        if abs(i0 - i1) == 1: out.append((j, k, g[k]))
    return out
if __name__ == "__main__":
    J = {}; NB = []
    for inst, files in (("nq", ("nq_1m.npz", "mnq_fut.npz", "nqhd_long.npz")), ("gold", ("xau_long.npz", "mgc_fut.npz", "xau_long.npz"))):
        Dc, Dr, Dl = Data(files[0]), Data(files[1]), (Data(files[2]) if files[2] != files[0] else None)
        Dl = Dl or Dc
        fams = sorted({f for m, (i, f, p) in MODS.items() if i == inst})
        for fam in fams:
            gen, grid, md = FAMILIES[fam]; cols = {}; colr = {}; stats = []
            grid = list(grid) + [p for m, (i, f, p) in MODS.items() if i == inst and f == fam and p not in grid]     # out-of-grid chosen variants (e.g. VOLB R0.5)
            for j, p in enumerate(grid):
                a = run(Dc, fam, p, inst); a = a[a.date >= 20200201]; b = run(Dr, fam, p, inst); b = b[b.date >= 20240201]
                ui, uc = a.usd[a.date < 20240101], a.usd[a.date >= 20240101]
                stats.append(dict(j=j, IS_n=len(ui), IS_pf=pfu(ui), C24_pf=pfu(uc), REAL_n=len(b), REAL_pf=pfu(b.usd), IS_sh=np.nan))
                if len(a) >= 100: cols[j] = a.groupby("date").usd.sum()
                if len(b) >= 40: colr[j] = b.groupby("date").usd.sum()
            S = pd.DataFrame(stats).set_index("j")
            alld = np.array(sorted(set(Dc.date[(Dc.date >= 20200201)]) - set(FOMC)))
            M = pd.DataFrame(cols).reindex(alld, fill_value=0.0).fillna(0.0)
            fam_pbo = pbo(M.to_numpy()) if M.shape[1] >= 10 else {}
            print(inst, fam, len(grid), "configs; PBO", fam_pbo, flush=True)
            for m, (i, f, p) in MODS.items():
                if i != inst or f != fam: continue
                jc = next(j for j, g in enumerate(grid) if g == p); r = dict(module=m, family=fam, inst=inst, configs=len(grid), chosen_j=jc)
                r.update({k: (round(float(v), 3) if isinstance(v, (float, np.floating)) else int(v)) for k, v in S.loc[jc].items() if k != "IS_sh"})
                ok = S[(S.IS_n >= 100) & S.IS_pf.notna()]
                r["family_pbo"] = fam_pbo
                rk = ok.sort_values("IS_pf", ascending=False)
                for top in (1, 10, 50):
                    t = rk.head(top); r[f"top{top}_IS_pf_med"] = round(float(t.IS_pf.median()), 3); r[f"top{top}_C24_pf_med"] = round(float(t.C24_pf.median()), 3); r[f"top{top}_REAL_pf_med"] = round(float(t.REAL_pf.median()), 3)
                r["family_median_pf"] = {c: round(float(ok[c].median()), 3) for c in ("IS_pf", "C24_pf", "REAL_pf")}
                r["spearman_IS_REAL"] = round(float(ok[["IS_pf", "REAL_pf"]].corr(method="spearman").iloc[0, 1]), 3)
                r["spearman_IS_C24"] = round(float(ok[["IS_pf", "C24_pf"]].corr(method="spearman").iloc[0, 1]), 3)
                r["chosen_REAL_pct_rank"] = round(float((ok.REAL_pf < S.loc[jc, "REAL_pf"]).mean()), 3)
                r["chosen_IS_pct_rank"] = round(float((ok.IS_pf < S.loc[jc, "IS_pf"]).mean()), 3)
                # sub-family PBO: configs sharing the anchor / clock of the chosen one (the cluster it was picked from)
                ck = {"VOL_BREAK": [], "CLOCK_ANCHOR": ["anc", "T"], "LATE_MOM": ["T"], "ENGULF_4H": ["eng"], "G_DRIVE": ["A", "T"], "NQ_DRIVE": ["A", "T"], "OPEN_DRIVE": ["T"], "G_ORB": ["A", "T"]}[fam]
                if ck:
                    sub = [j for j in M.columns if all(grid[j][k] == p[k] for k in ck)]
                    r["cluster"] = {k: p[k] for k in ck}; r["cluster_n"] = len(sub)
                    if len(sub) >= 10: r["cluster_pbo"] = pbo(M[sub].to_numpy())
                # neighbours, incl. 2015-19 cost-normalised
                nbs = neighbours(grid, p); rows = []
                l0 = run(Dl, fam, p, inst, NC[inst]); l0 = l0[(l0.date >= 20150201) & (l0.date < 20200101)]; r["L1519_pf"] = round(pfu(l0.usd), 3); r["L1519_n"] = len(l0)
                for j, k, v in nbs:
                    l = run(Dl, fam, grid[j], inst, NC[inst]); l = l[(l.date >= 20150201) & (l.date < 20200101)]
                    s = S.loc[j]; rows.append(dict(module=m, param=k, value=str(v), chosen=str(p[k]), j=j, IS_n=int(s.IS_n), IS_pf=s.IS_pf, C24_pf=s.C24_pf, REAL_pf=s.REAL_pf, L1519_pf=pfu(l.usd), L1519_n=len(l)))
                Nb = pd.DataFrame(rows); NB.append(Nb)
                if len(Nb):
                    allp = Nb[["IS_pf", "C24_pf", "REAL_pf"]]
                    r["nb_n"] = len(Nb); r["nb_median"] = {c: round(float(Nb[c].median()), 3) for c in ("IS_pf", "C24_pf", "REAL_pf", "L1519_pf")}
                    r["nb_min"] = {c: round(float(Nb[c].min()), 3) for c in ("IS_pf", "C24_pf", "REAL_pf", "L1519_pf")}
                    r["nb_share_all3_ge_1.1"] = round(float((allp.min(axis=1) >= 1.1).mean()), 2); r["nb_share_all3_ge_1.0"] = round(float((allp.min(axis=1) >= 1.0).mean()), 2)
                    r["nb_share_1519_ge_1.0"] = round(float((Nb.L1519_pf >= 1.0).mean()), 2)
                J[m] = r; print(m, {k: v for k, v in r.items() if k not in ("family_pbo",)}, flush=True)
        del Dc, Dr, Dl
    json.dump(J, open("audit_family.json", "w"), indent=1, default=float)
    pd.concat(NB, ignore_index=True).to_csv("audit_neighbours.csv", index=False)
    print("done")
