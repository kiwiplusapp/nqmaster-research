"""Federico 2026-10-09 'make this work': which profile survives best if the weakest parts of the edge are luck?
Scenarios on REAL MNQ + MGC 2024-02..2026-09 (final3y trade sets, minute equity paths), MyFundedFutures Rapid EOD 50K,
eval fixed 1 contract (profit stop $800, 30% consistency) -> funded 1 contract keeping $4,100 (Tier-1 news blackout):
  S0 base: as backtested
  S1 audit-weak modules are noise: ON07, LATEFH, ENG10, MOM1030, MOM13 trades de-meaned (same trades, zero average);
     gold ENG0408 / SVWAP22 / ENG0206 removed
  S2 2020-regime modules fade (they lost in 2015-19): MOM11, MOM1030, MOM13, ON07, REV06 de-meaned
  S3 = S1 + S2
History (12-month windows every 3rd day) + 400 resampled years. -> final3y_weak.json"""
import os, sys, json, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import final3y as F3
from final3y import minute_paths, news_adjust, day_vectors, PERIOD
import acct1c_lib as A
from acct_lab import Z
from mffu_rapid import life_m, eval_stats

S1N = ["ON07", "LATEFH", "ENG10", "MOM1030", "MOM13"]; S2N = ["MOM11", "MOM1030", "MOM13", "ON07", "REV06"]
GOLD = {"Robust": ["G:OD1030", "G:ENG0408", "G:SVWAP22", "G:ASIA1R", "G:ENG0206"], "Robust-weak": ["G:OD1030", "G:ASIA1R"],
        "WinRate": ["G:OD1030", "G:ENG0408", "G:SVWAP22"], "WinRate-weak": ["G:OD1030"]}
PROFS = {"Ultra": "Robust", "UltraLean": "Robust", "WR70Plus": "WinRate"}
SCEN = {"S0 as backtested": ([], False), "S1 weak modules are noise": (S1N, True), "S2 2020-regime modules fade": (S2N, False),
        "S3 both": (sorted(set(S1N) | set(S2N)), True)}
NB = 400


def demean(X, mods):
    X = X.copy()
    for m in mods:
        k = X["mod"] == m
        if k.any(): X.loc[k, "u"] = X.loc[k, "u"] - (X.loc[k, "u"] * X.loc[k, "w"]).sum() / X.loc[k, "w"].sum()
    return X


if __name__ == "__main__":
    z = Z(PERIOD); days = z["days"]; nd = len(days)
    TR = pickle.load(open("final3y_trades.pkl", "rb"))
    GL = {k: A._sum(PERIOD, A.items([], v, 1.0)) for k, v in GOLD.items()}
    hidx = np.arange(nd, dtype=np.int64); IDX = [A.boot_idx(nd, q, 253, 10, 31) for q in range(NB)]
    OUT = []
    for sn, (mods, gweak) in SCEN.items():
        for prof, g in PROFS.items():
            X = demean(TR[prof], mods); gk = g + ("-weak" if gweak else ""); gL, gR = (a.astype(np.float64) for a in GL[gk])
            low, close, fin, ex = minute_paths(X, days); lo_e, cl_e = day_vectors(low, close, fin, gL, gR, 800.0)
            lowN, closeN, finN, _ = minute_paths(news_adjust(X), days); lo_f, cl_f = day_vectors(lowN, closeN, finN, gL, gR, 0.0)
            EL = np.ascontiguousarray(np.array([lo_e, lo_e])); EC = np.ascontiguousarray(np.array([cl_e, cl_e]))
            FL = np.ascontiguousarray(np.array([lo_f, lo_f, lo_f])); FC = np.ascontiguousarray(np.array([cl_f, cl_f, cl_f]))
            o = np.zeros((nd, 2)); m = eval_stats(EL, EC, 0.0, 3000.0, 2000.0, 0.3, 4, hidx, 60, o); es = A.esumm(o[:m])
            out = np.zeros((nd, 8)); mm = life_m(EL, EC, 0.0, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 0.0, 0.0, 4100.0, 0, hidx, 252, 3, out)
            hist = out[:mm, 0].mean() / 12
            bs = np.zeros(NB); o1 = np.zeros((2, 8))
            for q, idx in enumerate(IDX): life_m(EL, EC, 0.0, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 0.0, 0.0, 4100.0, 0, idx, 252, 252, o1); bs[q] = o1[0, 0] / 12
            u = np.concatenate([(X.u * X.w).to_numpy()]); dayall = fin + gR[:, -1]
            r = dict(scenario=sn, profile=prof, gold=gk, nq_gold_per_month=round(float(dayall.mean() * 21)), sharpe=round(float(dayall.mean() / dayall.std() * np.sqrt(252)), 2),
                     eval_pass=round(es["pass_pct"], 1), eval_med_days=es["med_days"], life_hist=round(float(hist)), life_boot=round(float(bs.mean())),
                     boot_p10=round(float(np.percentile(bs, 10))), p_pos=round(100 * float((bs > 0).mean()), 1), p_1200=round(100 * float((bs >= 1200).mean()), 1))
            OUT.append(r); print(r, flush=True)
    json.dump(OUT, open("final3y_weak.json", "w"), indent=1)
