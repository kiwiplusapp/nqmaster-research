"""Edge monitor calibration (one-sided CUSUM on daily P&L normalised by the daily ATR: z = day $ per 1 lot / (2 x ATR points)).
S_t = max(0, S_{t-1} + k - z_t), alarm when S_t > h. k = mu/2 (halfway between 'edge as backtested' and 'no edge').
h chosen so the probability of a false alarm within 3 years on live-like data (block bootstrap of 2020-26) is <= 10%.
Reports detection delay when the edge disappears (mean -> 0) or halves; replays 2020-26, REAL 2024-26 and 2015-19.
Updates robust_lab.json['monitor']."""
import os, sys, json, pickle, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data
T = pickle.load(open("robust_trades.pkl", "rb")); J = json.load(open("robust_lab.json")); rng = np.random.default_rng(11)
@njit(cache=True)
def cusum_first(x, k, h):
    s = 0.0
    for t in range(len(x)):
        s = max(0.0, s + k - x[t])
        if s > h: return t + 1
    return -1
@njit(cache=True)
def cusum_path(x, k, h):
    s = 0.0; out = np.zeros(len(x))
    for t in range(len(x)):
        s = max(0.0, s + k - x[t]); out[t] = s
    return out
def boot_idx(n, B, H, L=10):
    idx = np.empty((B, H), np.int64)
    for b in range(B):
        p = rng.integers(n)
        for i in range(H):
            idx[b, i] = p
            p = rng.integers(n) if rng.random() < 1 / L else (p + 1) % n
    return idx
def atr_by_date(D):
    rth = (D.om >= 570) & (D.om < 960)
    g = pd.DataFrame(dict(date=D.date[rth], day=D.day[rth])).groupby("date").day.first()
    return pd.Series(D.atr[g.to_numpy()], index=g.index)
AT = {"nq": atr_by_date(Data("nq_1m.npz")), "mnq": atr_by_date(Data("mnq_fut.npz"))}
def z_of(F, days, key):
    x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0.0)
    a = AT[key].reindex(days).replace(0, np.nan).ffill().bfill()
    z = (d / (2 * a)).to_numpy(); return z[np.isfinite(z)], d.to_numpy(), a.to_numpy()
mon = {}
H = 3000; B = 1000
for prof in ("Ultra", "WR70Plus", "Core6"):
    PP = T[prof]
    z1, _, _ = z_of(*PP["IS"], "nq"); z2, _, _ = z_of(*PP["C24"], "nq"); z = np.concatenate([z1, z2]); zr, dr, ar = z_of(*PP["REAL"], "mnq")
    mu = float(z.mean()); sd = float(z.std()); k = mu / 2
    I = boot_idx(len(z), B, H)
    table = []
    for hs in (8, 12, 15, 18, 22, 26, 30):
        h = hs * sd; a0 = []; a1 = []; a2 = []; a3 = []
        for b in range(B):
            seq = z[I[b]]
            t0 = cusum_first(seq, k, h); a0.append(t0 if t0 > 0 else H)
            t1 = cusum_first(seq - mu, k, h); a1.append(t1 if t1 > 0 else H)
            t2 = cusum_first(seq - 0.5 * mu, k, h); a2.append(t2 if t2 > 0 else H)
            t3 = cusum_first(seq - 1.5 * mu, k, h); a3.append(t3 if t3 > 0 else H)
        a0 = np.array(a0); a1 = np.array(a1); a2 = np.array(a2); a3 = np.array(a3)
        table.append(dict(h_sd=hs, h=round(h, 4), P_false_alarm_1y=round(float((a0 <= 252).mean()), 3), P_false_alarm_3y=round(float((a0 <= 756).mean()), 3),
                          dead_median_days=float(np.median(a1)), dead_p90_days=float(np.percentile(a1, 90)), dead_detect_within_6m=round(float((a1 <= 126).mean()), 3),
                          half_median_days=float(np.median(a2)), half_detect_within_1y=round(float((a2 <= 252).mean()), 3), neg_median_days=float(np.median(a3)), neg_p90_days=float(np.percentile(a3, 90)),
                          hist_alarm=bool(cusum_first(z, k, h) > 0), real_alarm=bool(cusum_first(zr, k, h) > 0)))
    ch = next((t for t in table if t["P_false_alarm_1y"] <= 0.05 and not t["hist_alarm"] and not t["real_alarm"]), table[-1])
    pz = cusum_path(z, k, ch["h"]); pr = cusum_path(zr, k, ch["h"])
    mon[prof] = dict(mu_norm=round(mu, 4), sd_norm=round(sd, 4), k=round(k, 4), table=table, chosen=ch,
                     replay_2020_26_alarm_day=cusum_first(z, k, ch["h"]), replay_2020_26_max_S_over_h=round(float(pz.max() / ch["h"]), 2),
                     replay_REAL_alarm_day=cusum_first(zr, k, ch["h"]), replay_REAL_max_S_over_h=round(float(pr.max() / ch["h"]), 2),
                     typical_day_usd_per_lot=round(float(dr.mean()), 1), typical_atr_real=round(float(np.nanmean(ar))))
    print(prof, mon[prof]["mu_norm"], mon[prof]["sd_norm"], ch, mon[prof]["replay_2020_26_max_S_over_h"], mon[prof]["replay_REAL_max_S_over_h"], flush=True)
# 2015-19: robust modules as traded then (era costs), same normalisation and Core6 thresholds
L = pd.read_pickle(os.path.join(RES, "variants_nqhd_long.pkl"))
core = {"ICT": 1.0, "MSEQ": 0.5, "CRT11": 2.0, "LON": 2.0, "ORB60": 0.6}
L = pd.concat([L[(L["mod"] == m) & (L["var"] == v)] for m, v in core.items()]); L = L[~L.fomc]
L = L.assign(w=np.where(L["mod"] == "ICT", 2.0, 1.0))
DL = Data("nqhd_long.npz"); al = atr_by_date(DL); dl = np.array(sorted(al.index)); dl = dl[(dl >= 20150101) & (dl < 20200101)]
dd = (L.usd * L.w).groupby(L.date).sum().reindex(dl, fill_value=0.0); a = al.reindex(dl).replace(0, np.nan).ffill().bfill()
zl = (dd / (2 * a)).to_numpy(); zl = zl[np.isfinite(zl)]
c6 = mon["Core6"]; first = cusum_first(zl, c6["k"], c6["chosen"]["h"])
Lx = L[(L.date >= 20150101) & (L.date < 20200101)]; u = Lx.usd * Lx.w
mon["replay_2015_19_core"] = dict(alarm_day=first, alarm_date=int(dl[first - 1]) if first > 0 else None, days=len(zl), pf=round(float(u[u > 0].sum() / -u[u <= 0].sum()), 3),
                                  mean_norm=round(float(zl.mean()), 4), share_days_atr_ge150=round(float((a >= 150).mean()), 3),
                                  pf_if_atr_ge150=round(float(u[Lx.date.map(a) >= 150].pipe(lambda v: v[v > 0].sum() / -v[v <= 0].sum())), 3))
print(mon["replay_2015_19_core"])
J["monitor"] = mon; json.dump(J, open("robust_lab.json", "w"), indent=1, default=float)
