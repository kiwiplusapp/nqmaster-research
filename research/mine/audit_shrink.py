"""AUDIT step 8: empirical-Bayes forward haircut per module (regression to the mean inside the family each module was picked from).
Model per family (eligible configs): x1 = log PF 2020-23 (IS), x2 = log PF 2024-26 (mean of the C24 and REAL log PF where both exist),
x_k = a_k + mu + e_k, true persistent edge mu ~ (0, tau2), noise var_k = c_k / n_k (n = trades).
tau2 = cov(x1, x2) across configs (0 if negative); c_k from var(x_k) - tau2. For the chosen config the posterior mean of mu uses both
periods (precision weighted); forward PF = exp(a2 + mu_hat) (a2 = family mean in 2024-26). kappa = (PF_fwd - 1) / (PF_obs_family_basis - 1),
the share of the observed edge expected to persist; it is then applied to the module's edge as traded in the profile (constant
deduction per trade) and the profiles are recomputed on REAL / C24 with +1 tick per side.  Also with the module's own 'cluster'
(same clock / anchor) as the prior instead of the whole family.
Output: audit_shrink.csv (per module), audit_shrink_port.csv (profiles)"""
import os, sys, glob, json, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd())
from audit_family import MODS as FMODS
def lpf(x): return np.log(np.clip(np.asarray(x, float), 0.25, 4.0))
def fit(x1, n1, x2, n2):
    ok = np.isfinite(x1) & np.isfinite(x2) & (n1 > 0) & (n2 > 0); x1, n1, x2, n2 = x1[ok], n1[ok], x2[ok], n2[ok]
    tau2 = max(float(np.cov(x1, x2)[0, 1]), 0.0)
    c1 = max(float(np.var(x1) - tau2), 1e-6) / float(np.mean(1 / n1)); c2 = max(float(np.var(x2) - tau2), 1e-6) / float(np.mean(1 / n2))
    return dict(a1=float(np.mean(x1)), a2=float(np.mean(x2)), tau2=tau2, c1=c1, c2=c2, n=int(ok.sum()), rho=round(float(np.corrcoef(x1, x2)[0, 1]), 3))
def post(F, v1, n1, v2, n2):
    if F["tau2"] <= 0: return F["a2"]
    w1 = n1 / F["c1"]; w2 = n2 / F["c2"]; mu = (w1 * (v1 - F["a1"]) + w2 * (v2 - F["a2"])) / (1 / F["tau2"] + w1 + w2); return F["a2"] + mu
def tab_mined(fn, fam):
    R = pd.read_csv(fn); R = R[(R.fam == fam) & (R.IS_n >= 100) & (R.C24_n >= 60)].copy()
    R["x1"] = lpf(R.IS_pf); R["x2"] = (lpf(R.C24_pf) + lpf(R.REAL_pf.fillna(R.C24_pf))) / 2; R["n1"] = R.IS_n; R["n2"] = R.C24_n; return R
def tab_csv(fn, cols):
    R = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(RES, fn)))], ignore_index=True)
    i_n, i_pf, o_n, o_pf, r_pf = cols
    R["n1"] = R[i_n]; R["n2"] = R[o_n]; R = R[(R.n1 >= 100) & (R.n2 >= 50)].copy()
    R["x1"] = lpf(R[i_pf]); R["x2"] = (lpf(R[o_pf]) + lpf(R[r_pf].fillna(R[o_pf]))) / 2 if r_pf else lpf(R[o_pf]); return R
if __name__ == "__main__":
    FJ = json.load(open("audit_family.json")); OJ = json.load(open("audit_oldmods.json"))
    tmp = os.environ.get("AUDIT_TMP", "/tmp"); cache = pickle.load(open(os.path.join(tmp, "audit_oldmods_cache.pkl"), "rb"))
    rows = []
    def add(mod, F, v1, n1, v2, n2, Fc=None, note=""):
        pf_obs = float(np.exp((v1 * n1 + v2 * n2) / (n1 + n2)))          # trade-weighted observed PF on the family basis (2020-26)
        pf_f = float(np.exp(post(F, v1, n1, v2, n2))); r = dict(mod=mod, fam_n=F["n"], fam_rho=F["rho"], fam_PF_2024_26=round(float(np.exp(F["a2"])), 3), obs_IS=round(float(np.exp(v1)), 3),
                                                              obs_2024_26=round(float(np.exp(v2)), 3), obs_pooled=round(pf_obs, 3), fwd_PF_family_prior=round(pf_f, 3),
                                                              kappa_family=round(max(pf_f - 1, -1) / max(pf_obs - 1, 1e-3), 2), note=note)
        if Fc is not None and Fc["n"] >= 15:
            pc = float(np.exp(post(Fc, v1, n1, v2, n2))); r.update(cluster_n=Fc["n"], cluster_rho=Fc["rho"], fwd_PF_cluster_prior=round(pc, 3), kappa_cluster=round(max(pc - 1, -1) / max(pf_obs - 1, 1e-3), 2))
        rows.append(r); print(r, flush=True)
    SRCF = {"VOL_BREAK": "results_all.csv", "CLOCK_ANCHOR": "results_all.csv", "LATE_MOM": "results_b4.csv", "ENGULF_4H": "results_b3.csv", "G_DRIVE": "results_gnq.csv", "NQ_DRIVE": "results_nqdrive.csv"}
    CK = {"VOL_BREAK": [], "CLOCK_ANCHOR": ["anc", "T"], "LATE_MOM": ["T"], "ENGULF_4H": ["eng"], "G_DRIVE": ["A", "T"], "NQ_DRIVE": ["A", "T"]}
    import ast
    for m, (inst, fam, p) in FMODS.items():
        r = FJ[m]
        if inst == "nq":
            R = tab_mined(SRCF[fam], fam); F = fit(R.x1.values, R.n1.values, R.x2.values, R.n2.values)
            R["p"] = R.params.map(ast.literal_eval); sub = R[R.p.map(lambda g: all(g.get(k) == p[k] for k in CK[fam]))] if CK[fam] else None
            Fc = fit(sub.x1.values, sub.n1.values, sub.x2.values, sub.n2.values) if sub is not None and len(sub) >= 15 else None
        else:
            R = pd.concat([pd.read_csv("results_gold.csv"), pd.read_csv("results_goldfam.csv")]); R = R[(R.fam == fam) & (R.IS_n >= 60) & (R.C24_n >= 40)].copy()
            R["x1"] = lpf(R.IS_pf); R["x2"] = (lpf(R.C24_pf) + lpf(R.REAL_pf.fillna(R.C24_pf))) / 2; F = fit(R.x1.values, R.IS_n.values, R.x2.values, R.C24_n.values); Fc = None
        v1 = float(lpf(r["IS_pf"])); v2 = float((lpf(r["C24_pf"]) + lpf(r["REAL_pf"])) / 2)
        add(m, F, v1, r["IS_n"], v2, r["REAL_n"], Fc, note=f"{fam} ({len(R)} eligible)")
    # clock modules: time map (tmom csv, $1 RT basis); chosen = the map cell
    T = tab_csv("tmom_*.csv", ("is_n", "is_pf", "c24_n", "c24_pf", "fut_pf")); F = fit(T.x1.values, T.n1.values, T.x2.values, T.n2.values)
    for m in ("MOM11", "MOM13", "MOM1030", "ON07", "REV06"):
        c = OJ[m]["chosen_in_map"]; t0 = int(eval(c["key"])[0]); sub = T[T.t == t0]; Fc = fit(sub.x1.values, sub.n1.values, sub.x2.values, sub.n2.values) if len(sub) >= 15 else None
        add(m, F, float(lpf(c["IS_pf"])), c["IS_n"], float((lpf(c["C24_pf"]) + lpf(c["REAL_pf"])) / 2), c["IS_n"] * 0.6, Fc, note="time map (tmom)")
    Lg = tab_csv("london_tf1.csv", ("is_n", "is_pf", "c24_n", "c24_pf", "fut_pf")); F = fit(Lg.x1.values, Lg.n1.values, Lg.x2.values, Lg.n2.values)
    _, S = cache["LON grid"]; c = S.loc[str((0, 360, 480, 1, 2, 2.0, 0.25, 570, 1))]
    add("LON", F, float(lpf(c.IS_pf)), c.IS_n, float((lpf(c.C24_pf) + lpf(c.REAL_pf)) / 2), c.IS_n * 0.6, None, note="London grid")
    _, S = cache["ICT grid"]; S = S[(S.IS_n >= 60)].copy(); S["x1"] = lpf(S.IS_pf); S["x2"] = (lpf(S.C24_pf) + lpf(S.REAL_pf)) / 2
    F = fit(S.x1.values, S.IS_n.values.astype(float), S.x2.values, S.IS_n.values * 0.6); c = S.loc[str(("all", (570, 630), 4, 2, 1.0, 1, 0.25))]
    add("ICT", F, float(c.x1), c.IS_n, float(c.x2), c.IS_n * 0.6, None, note="ICT-fix 5m grid")
    C = pd.read_csv(os.path.join(RES, "crt2.csv")); C = C[(C.is_n >= 60) & (C.oos_n >= 40)].copy(); F = fit(lpf(C.is_pf), C.is_n.values.astype(float), lpf(C.oos_pf), C.oos_n.values.astype(float))
    c = C[(C.p == 60) & (C.hours == "11") & (C.bias == 1) & (C.R == 2.0) & (C.min_rng == 0.0) & (C.max_risk == 0.5) & (C.mcf == 0.0) & (C.emode == 0)].iloc[0]
    add("CRT11", F, float(lpf(c.is_pf)), c.is_n, float(lpf(c.oos_pf)), c.oos_n, None, note="CRT grid (crt2.csv, CFD only)")
    W = pd.read_csv(os.path.join(RES, "wr60_tf5.csv")); W["is_n"] = W.n - W.oos_n; W = W[(W.is_n >= 100) & (W.oos_n >= 50)]; F = fit(lpf(W.is_pf), W.is_n.values.astype(float), lpf(W.oos_pf), W.oos_n.values.astype(float))
    fo = pd.read_csv(os.path.join(RES, "wr60_focus.csv")); c = fo[(fo.filt == "up20") & (fo.sess == "rth_1030") & (fo.N == 5) & (fo.R == 0.5) & (fo.sk == 1.75)].iloc[0]
    add("MSEQ", F, float(lpf(c.is_pf)), c.n * 0.7, float(lpf(c.oos_pf)), c.n * 0.3, None, note="MSEQ grid (wr60_tf5) prior, chosen from wr60_focus")
    V = pd.read_csv(os.path.join(RES, "v3_grid.csv")); V = V[(V.IS_trades >= 100) & (V.OOS_trades >= 50)]; F = fit(lpf(V.IS_pf), V.IS_trades.values.astype(float), lpf(V.OOS_pf), V.OOS_trades.values.astype(float))
    for m in ("ORB60", "ORB90"):
        tv = OJ["target_variants"][m]["variants"]["0.6"]; add(m, F, float(lpf(tv["IS"])), 290, float((lpf(tv["C24"]) + lpf(tv["REAL"])) / 2), 190, None, note="ORB v3 grid (no pullback filter; weak prior)")
    K = pd.DataFrame(rows); K.to_csv("audit_shrink.csv", index=False); pd.set_option("display.width", 250); print(K.to_string(index=False))
    # ---------------------------------------------------------------- portfolio with module kappas
    A = pickle.load(open("audit_trades.pkl", "rb")); P = A["prof"]
    kap = dict(zip(K["mod"], K.kappa_family)); kapc = {r.mod: (r.kappa_cluster if pd.notna(getattr(r, "kappa_cluster", np.nan)) else r.kappa_family) for r in K.itertuples()}
    MAP = {"VOLB": {"Ultra": "VOLB(U)", "WR70N": "VOLB(W)"}, "VW13": {"Ultra": "VW13b(0.15)", "WR70N": "VW13b(0.15)"}}
    def pfw(x): gl = -x[x <= 0].sum(); return x[x > 0].sum() / gl
    def deduct(g, k):
        """constant $ per weighted unit so that the module PF edge becomes k x the observed edge (k clipped to [-0.5, 1])."""
        x = (g.u - 1.0) * g.w; pf0 = pfw(x); target = 1 + max(min(k, 1.0), -0.5) * (pf0 - 1)
        lo, hi = -50.0, 200.0
        for _ in range(60):
            c = (lo + hi) / 2; v = pfw((g.u - 1.0 - c) * g.w)
            if v > target: lo = c
            else: hi = c
        return (lo + hi) / 2
    out = []
    for prof in ("Ultra", "WR70N"):
        for per in ("C24", "REAL"):
            F, D = P[prof][per]
            for nm, kk in (("+1 tick only", None), ("+1 tick, family-prior kappa", kap), ("+1 tick, cluster-prior kappa", kapc), ("+1 tick, kappa max(fam,0.5)", {k: max(v, 0.5) for k, v in kap.items()})):
                G = F.copy(); G["u"] = G.u - 1.0
                if kk is not None:
                    for m, g in F.groupby("mod"):
                        key = MAP.get(m, {}).get(prof, m); k = kk.get(key, kk.get(m, 0.5)); k = 0.5 if pd.isna(k) else k
                        G.loc[g.index, "u"] = G.loc[g.index, "u"] - deduct(g, k)
                x = G.u * G.w; d = x.groupby(G.date).sum().reindex(D, fill_value=0.0)
                out.append(dict(prof=prof, per=per, scenario=nm, wr=round(100 * (G.u > 0).mean(), 1), pf=round(pfw(x), 3), sharpe=round(d.mean() / d.std() * 252 ** .5, 2), mo=round(d.mean() * 21)))
    O = pd.DataFrame(out); O.to_csv("audit_shrink_port.csv", index=False); print(O.to_string(index=False))
