"""AUDIT step 2: module and profile statistics on audit_trades.pkl (1 base contract, weights as coded).
 - per module (as traded inside its profile, after the conflict filter): trades/day, WR, PF, daily Sharpe, $/month per period
   IS / C24 / REAL, per calendar year (CFD 2020-26 and REAL 2024-26), last 6 months (2026-04-01..09-25), 2015-19 cost-normalised,
   best-year share of profit and PF without the best year, +1/+2/+4 ticks per side, deflated Sharpe with the family trial count.
 - per profile: the same + DSR for N = 100 ... 300,000 trials, regimes (ATR terciles, trend/range day, VIX terciles).
Output: audit_modules.csv, audit_years.csv, audit_profiles.csv, audit_regimes.csv, audit_dsr.csv"""
import os, sys, math, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from scipy.stats import norm, skew, kurtosis
from core import Data
A = pickle.load(open("audit_trades.pkl", "rb")); P = A["prof"]; L = A["L1519"]
for _g in ("GoldRB", "GoldWR"):          # gold modules carry the 'G:' prefix everywhere (tick cost $2 per side-tick on MGC)
    for _p in list(P[_g]): F_, d_ = P[_g][_p]; P[_g][_p] = (F_.assign(mod="G:" + F_["mod"].astype(str)), d_)
PERS = ("IS", "C24", "REAL")
# trials behind each module (configs searched in the family / script that produced it; the project total is > 300k)
TRIALS = {"ORB60": 2000, "ORB90": 2000, "MSEQ": 22000, "MSEQS": 500, "CRT11": 14000, "LON": 6912, "ICT": 9600, "MOM11": 8500, "MOM13": 8500,
          "MOM1030": 8500, "ON07": 8500, "REV06": 8500, "VW13": 1728, "VOLB": 192, "LATE15": 2304, "LATEFH": 2304, "ENG10": 2304,
          "NF05": 8568, "LF06": 5760, "LF0430": 5760, "G:OD1030": 288, "G:ENG0408": 2304, "G:SVWAP22": 1728, "G:ASIA1R": 1368, "G:ENG0206": 2304}
def dsr(d, N):
    d = np.asarray(d, float); sr = d.mean() / d.std(); n = len(d); g3 = skew(d); g4 = kurtosis(d, fisher=False); emc = 0.5772156649
    sr0 = (1 / n) ** .5 * ((1 - emc) * norm.ppf(1 - 1 / N) + emc * norm.ppf(1 - 1 / (N * math.e)))
    z = (sr - sr0) * (n - 1) ** .5 / (1 - g3 * sr + (g4 - 1) / 4 * sr * sr) ** .5
    return float(norm.cdf(z)), float(sr0 * 252 ** .5)
GOLDP = ("GoldRB", "GoldWR")
def tc(F):          # $ per round turn for 1 extra tick per side: MNQ $1.00, MGC $2.00 (gold rows carry 'G:' or come from a Gold profile)
    return np.where(F["mod"].astype(str).str.startswith("G:"), 2.0, 1.0)
def daily(F, days, extra=0.0):
    x = (F.u - extra * tc(F)) * F.w; return x.groupby(F.date).sum().reindex(days, fill_value=0.0)
def st(F, days, extra=0.0):
    if len(F) == 0: return dict(n=0)
    x = (F.u - extra * tc(F)) * F.w; d = daily(F, days, extra); gl = -x[x <= 0].sum(); eq = d.cumsum()
    return dict(n=len(F), tpd=round(len(F) / len(days), 3), wr=round(100 * ((F.u - extra * tc(F)) > 0).mean(), 1), pf=round(x[x > 0].sum() / gl, 3) if gl > 0 else np.nan,
                sharpe=round(d.mean() / d.std() * 252 ** .5, 2) if d.std() > 0 else np.nan, mo=round(d.mean() * 21, 1), maxdd=round((eq.cummax() - eq).max()))
def pfu(u): u = np.asarray(u); gl = -u[u <= 0].sum(); return round(u[u > 0].sum() / gl, 3) if gl > 0 else np.nan
def mods_of(prof): return sorted(set(np.concatenate([P[prof][p][0]["mod"].unique() for p in PERS])))
L1519MAP = {"VOLB": {"Ultra": "VOLB_U", "WR70N": "VOLB_W"}, "VW13": {"Ultra": "VW13b", "WR70N": "VW13b"}, "ORB60": {"Ultra": "ORB60", "WR70N": "ORB60_075"}}
if __name__ == "__main__":
    rows, yrows, prow, rrows, drows = [], [], [], [], []
    for prof in ("Ultra", "WR70N", "GoldRB", "GoldWR"):
        for m in mods_of(prof):
            r = dict(prof=prof, mod=m)
            for per in PERS:
                F, days = P[prof][per]; G = F[F["mod"] == m]
                for k, v in st(G, days).items(): r[f"{per}_{k}"] = v
                for tk in (1, 2, 4):
                    x = (G.u - tk * tc(G)) * G.w; r[f"{per}_pf+{tk}t"] = pfu(x)
                r[f"{per}_avgw"] = round(G.w.mean(), 2) if len(G) else np.nan
            # last 6 months (2026-04-01 .. 2026-09-25)
            for per in ("C24", "REAL"):
                F, days = P[prof][per]; dd = days[days >= 20260401]; G = F[(F["mod"] == m) & (F.date >= 20260401)]
                s = st(G, dd); r[f"L6_{per}_n"] = s.get("n"); r[f"L6_{per}_wr"] = s.get("wr"); r[f"L6_{per}_pf"] = s.get("pf"); r[f"L6_{per}_mo"] = s.get("mo")
            key = L1519MAP.get(m, {}).get(prof, m)
            if key in L:
                u = L[key].u; r["L1519_n"] = len(u); r["L1519_wr"] = round(100 * (u > 0).mean(), 1); r["L1519_pf"] = pfu(u)
            # by year: CFD 2020-26 and REAL 2024-26
            cfd = pd.concat([P[prof]["IS"][0], P[prof]["C24"][0]]); cd = np.concatenate([P[prof]["IS"][1], P[prof]["C24"][1]])
            G = cfd[cfd["mod"] == m]; yr_pnl = {}
            for y in range(2020, 2027):
                g = G[G.date // 10000 == y]; x = g.u * g.w; yrows.append(dict(prof=prof, mod=m, src="CFD", year=y, n=len(g), wr=round(100 * (g.u > 0).mean(), 1) if len(g) else np.nan, pf=pfu(x), net=round(x.sum())))
                yr_pnl[y] = x.sum()
            F, days = P[prof]["REAL"]; G2 = F[F["mod"] == m]
            for y in (2024, 2025, 2026):
                g = G2[G2.date // 10000 == y]; x = g.u * g.w; yrows.append(dict(prof=prof, mod=m, src="REAL", year=y, n=len(g), wr=round(100 * (g.u > 0).mean(), 1) if len(g) else np.nan, pf=pfu(x), net=round(x.sum())))
            yp = pd.Series(yr_pnl); tot = yp.sum(); by = int(yp.idxmax())
            r["CFD_years_pos"] = int((yp > 0).sum()); r["CFD_best_year"] = by; r["CFD_best_year_share"] = round(float(yp.max() / tot), 2) if tot > 0 else np.nan
            xg = G[G.date // 10000 != by]; r["CFD_pf_ex_best_year"] = pfu(xg.u * xg.w)
            # DSR of the module's daily P&L (CFD 2020-26 and REAL) with its family trial count
            dcf = daily(G, cd).to_numpy(); dre = daily(G2, days).to_numpy(); N = TRIALS.get(m, 1000)
            r["trials"] = N; r["DSR_CFD_famN"] = round(dsr(dcf, N)[0], 3); r["DSR_REAL_famN"] = round(dsr(dre, N)[0], 3); r["DSR_CFD_300k"] = round(dsr(dcf, 300000)[0], 3)
            rows.append(r)
        print(prof, "modules done", flush=True)
    M = pd.DataFrame(rows); M.to_csv("audit_modules.csv", index=False); pd.DataFrame(yrows).to_csv("audit_years.csv", index=False)
    # ------------------------------------------------------------------ profiles
    DD = {"nq": Data("nq_1m.npz"), "mnq": Data("mnq_fut.npz")}
    def day_feats(D):
        rth = (D.om >= 570) & (D.om < 960)
        df = pd.DataFrame(dict(date=D.date[rth], o=D.o[rth], h=D.h[rth], l=D.l[rth], c=D.c[rth], day=D.day[rth]))
        g = df.groupby("date").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), day=("day", "first"))
        g["atr"] = D.atr[g.day.to_numpy()]; g["trendday"] = (g.c - g.o).abs() / (g.h - g.l).replace(0, np.nan) > 0.5
        return g
    FE = {k: day_feats(D) for k, D in DD.items()}
    vix = pd.read_csv(os.path.join(RES, "vix.csv")); vix.columns = [c.lower() for c in vix.columns]
    vcol = [c for c in vix.columns if "date" not in c][0]; dcol = [c for c in vix.columns if "date" in c][0]
    vix["date"] = pd.to_datetime(vix[dcol]).dt.strftime("%Y%m%d").astype(int); vix = vix.set_index("date")[vcol].apply(pd.to_numeric, errors="coerce").shift(1)
    pickle.dump(FE, open("audit_dayfeats.pkl", "wb"))
    for prof in P:
        for per in PERS:
            F, days = P[prof][per]; r = dict(prof=prof, per=per, **st(F, days))
            for tk in (1, 2, 4):
                s = st(F, days, tk); r[f"pf+{tk}t"] = s["pf"]; r[f"sh+{tk}t"] = s["sharpe"]; r[f"mo+{tk}t"] = s["mo"]
            r["breakeven_ticks"] = round(float((F.u * F.w).sum() / F.w.sum()), 1)
            dd = days[days >= 20260401]; s = st(F[F.date >= 20260401], dd); r.update({f"L6_{k}": v for k, v in s.items()})
            prow.append(r)
        for lab, pers, key in (("CFD 2020-26", ("IS", "C24"), "nq"), ("REAL 2024-26", ("REAL",), "mnq")):
            F = pd.concat([P[prof][p][0] for p in pers]); days = np.concatenate([P[prof][p][1] for p in pers]); d = daily(F, days)
            for N in (1, 100, 1000, 10000, 100000, 300000):
                pv, sr0 = dsr(d.to_numpy(), N); drows.append(dict(prof=prof, sample=lab, N=N, sharpe=round(d.mean() / d.std() * 252 ** .5, 2), sr0_ann=round(sr0, 2), DSR=round(pv, 4)))
            x = (F.u * F.w); gp = x.clip(lower=0).groupby(F.date).sum().reindex(days, fill_value=0.0); gl = (-x.clip(upper=0)).groupby(F.date).sum().reindex(days, fill_value=0.0)
            X = pd.DataFrame(dict(d=d.to_numpy(), gp=gp.to_numpy(), gl=gl.to_numpy()), index=days)
            fe = FE[key].reindex(X.index); X["atr"] = fe.atr.to_numpy(); X["trend"] = fe.trendday.map({True: "trend day", False: "range day"}).to_numpy()
            X["vix"] = vix.reindex(X.index).ffill().to_numpy()
            X["atr_t"] = pd.qcut(X.atr, 3, labels=["ATR low", "ATR mid", "ATR high"]); X["vix_t"] = pd.qcut(X.vix, 3, labels=["VIX low", "VIX mid", "VIX high"])
            for col in ("atr_t", "trend", "vix_t"):
                g = X.groupby(col, observed=True).agg(gp=("gp", "sum"), gl=("gl", "sum"), d=("d", "mean"), sd=("d", "std"), n=("d", "size"))
                for k, q in g.iterrows():
                    rrows.append(dict(prof=prof, sample=lab, split=col, bucket=str(k), days=int(q.n), pf=round(q.gp / q.gl, 3), per_day=round(q.d, 1), sharpe=round(q.d / q.sd * 252 ** .5, 2)))
    pd.DataFrame(prow).to_csv("audit_profiles.csv", index=False); pd.DataFrame(rrows).to_csv("audit_regimes.csv", index=False); pd.DataFrame(drows).to_csv("audit_dsr.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200); pd.set_option("display.max_columns", 40)
    print(pd.DataFrame(prow)[["prof", "per", "n", "tpd", "wr", "pf", "sharpe", "mo", "maxdd", "pf+1t", "pf+2t", "pf+4t", "mo+1t", "breakeven_ticks", "L6_n", "L6_wr", "L6_pf", "L6_mo"]].to_string(index=False))
    print(M[["prof", "mod", "IS_n", "IS_wr", "IS_pf", "C24_pf", "REAL_n", "REAL_wr", "REAL_pf", "REAL_mo", "L6_REAL_pf", "L1519_pf", "REAL_pf+4t", "CFD_best_year_share", "CFD_pf_ex_best_year", "DSR_CFD_famN", "DSR_REAL_famN"]].to_string(index=False))
    print(pd.DataFrame(drows).pivot_table(index=["prof", "sample"], columns="N", values="DSR").round(3).to_string())
    print(pd.DataFrame(rrows).pivot_table(index=["prof", "sample"], columns="bucket", values="pf").round(2).to_string())
