"""r9_check2: selftest de exp09, escalado exacto de la fondeada, ATR (NaN, al abrir, filtro MinAtrPoints), orden de suma de neg60_mtm,
exposicion media V1 por periodo, P&L por contrato por tercil de ATR y descomposicion del P&L bruto V1 vs V0."""
import os, sys, numpy as np, pandas as pd
MINE = "/home/user/nqmaster-research/research/mine"; os.chdir(MINE); sys.path.insert(0, MINE)
import prop_wf as P, objective as O, exp09_volsize as X, exp03_eval_size as E3

days, M, FU, PER = O.setup(); atr = X.atr_days(days); n = len(days)
print("dias", n, days[0], days[-1], "| NaN ATR:", int(np.isnan(atr).sum()), "| ATR<=0:", int((atr <= 0).sum()))
D = X.getD("nqdb.npz"); dd = pd.Series(D.daydate); print("daydate duplicados (sin 0):", int(dd[dd > 0].duplicated().sum()))
# duplicados que caen en dias de campana
dup = dd[(dd > 0) & dd.duplicated(keep=False)]; print("dup en campana:", int(np.isin(dup.values, days).sum()), sorted(set(dup.values[np.isin(dup.values, days)]))[:10])

# (1) selftest del script (1.200 asientos)
bad = X.selftest(); print("selftest bad =", bad)

# (2) escalado exacto de la fondeada: filas k=1 x k == dayvec con k, para k = 2, 3, 4 y hc 0 / 0.35
for hc in (0.0, 0.35):
    FL1, FC1, fp1 = FU.tiers(hc, "LucidFlex150K", (1, 1687, 0, 6000, 0))
    for k in (2, 3, 4):
        FLk, FCk, fpk = FU.tiers(hc, "LucidFlex150K", (k, 1687, 0, 6000, 0))
        print(f"fondeada hc{hc} k{k}: FL igual al bit {np.array_equal(FL1 * k, FLk)}, FC igual {np.array_equal(FC1 * k, FCk)}, fp igual {np.array_equal(fp1, fpk)}")

# (3) ATR y filtro MinAtrPoints = 150: dias con ATR < 150 deberian no operar (FIN == 0) si es el mismo ATR
FIN = M[(0, 4)][2]
lo = atr < 150; print("dias campana con ATR<150:", int(lo.sum()), "| de ellos con FIN != 0:", int((FIN[lo] != 0).sum()), "| dias con FIN==0 en total:", int((FIN == 0).sum()))
# ATR sin desplazar (usaria el dia mismo) vs desplazado: correlacion del |P&L| con cada uno
# (4) exposicion media de V1
ke, kf = X.kvecs(days, atr, "V1")
for per, ii in PER.items():
    print(f"{per}: ATR media {atr[ii].mean():.1f} mediana {np.median(atr[ii]):.1f} | eval k medio {ke[ii].mean():.3f} (V0 6) | fondeada k medio {kf[ii].mean():.3f} (V0 3) | dist fondeada", dict(zip(*np.unique(kf[ii], return_counts=True))))
print("ATR_ref", float(np.median(atr[days < P.T1_END])))

# (5) P&L diario por contrato (mezcla (0, 4), edge completo) por tercil de ATR
def terc(mask, lab):
    a = atr[mask]; f = FIN[mask]; q = np.quantile(a, [1 / 3, 2 / 3]); b = np.digitize(a, q)
    rows = []
    for t in range(3):
        s = b == t; rows.append((t, s.sum(), a[s].mean(), f[s].mean(), f[s].mean() / a[s].mean() * 100, f[s].std() / a[s].mean() * 100))
    print(f"--- {lab}: tercil, dias, ATR medio, P&L/dia por contrato $, P&L / ATR (x100, $/pt), desvio/ATR")
    for r in rows: print("   T%d n %4d ATR %6.1f pnl %7.2f pnl/ATR %6.3f sd/ATR %6.2f" % r)
    # regresion pnl ~ ATR por dia: pendiente e intercepto
    A = np.vstack([np.ones(mask.sum()), a]).T; c, *_ = np.linalg.lstsq(A, f, rcond=None)
    print(f"   OLS pnl = {c[0]:.1f} + {c[1]:.4f} x ATR  (intercepto > 0 => menos que proporcional; < 0 => mas que proporcional)")
allm = days < P.T2_END
terc(allm, "2020-26"); terc(days < P.T1_END, "T1"); terc((days >= P.T1_END) & allm, "T2")

# (6) descomposicion del P&L bruto (sin cuenta): sum k_t FIN_t (V1) vs 6 sum FIN_t (V0) y vs una V1 con la misma exposicion media (k escalado)
for per, ii in PER.items():
    v0 = 6 * FIN[ii].sum(); v1 = (ke[ii] * FIN[ii]).sum(); kn = ke[ii] * 6 / ke[ii].mean(); v1n = (kn * FIN[ii]).sum()
    f0 = 3 * FIN[ii].sum(); f1 = (kf[ii] * FIN[ii]).sum(); fn = (kf[ii] * 3 / kf[ii].mean() * FIN[ii]).sum()
    print(f"{per} eval: V1/V0 bruto {v1 / v0:.3f} | exposicion V1/V0 {ke[ii].mean() / 6:.3f} | V1 a igual exposicion / V0 {v1n / v0:.3f}   || fondeada: V1/V0 {f1 / f0:.3f} | exposicion {kf[ii].mean() / 3:.3f} | igual exposicion {fn / f0:.3f}")
    # riesgo: desvio diario V1 vs V0
    print(f"     desvio diario eval V1/V0 {np.std(ke[ii] * FIN[ii]) / np.std(6 * FIN[ii]):.3f} ; Sharpe diario V0 {FIN[ii].mean() / FIN[ii].std():.4f} V1 {np.mean(ke[ii] * FIN[ii]) / np.std(ke[ii] * FIN[ii]):.4f}")
