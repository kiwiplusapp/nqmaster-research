"""Runner overlay: trade 2 contracts per signal; contract 1 exits exactly as today, contract 2 stays open after a WINNING exit
and is managed by a trailing stop until 15:55. Losing trades are unchanged (both contracts hit the same stop), so the only
difference vs '2 contracts, same exits' is delta = d * (Y - X) * $2 per runner contract - 1 tick slippage, where X = the
winning exit price and Y = the runner exit. Trailing rules (ATR = daily ATR):
  BE   : stop at the original entry, no trail, exit 15:55
  T(k) : stop = max(entry, best price - k*ATR) for longs (mirror for shorts), checked on 1-min bars, stop-first
  L(k) : stop starts at X - k*ATR (gives back at most k*ATR), then trails best - k*ATR
Entry price E is recovered from the trade P&L (E = X - d*(u+1.9)/2 with X from the 1-min bar at exit) -> small tick errors only."""
import os, sys, pickle, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
from core import Data
T = pickle.load(open("robust_trades.pkl", "rb"))

@njit(cache=True)
def run_trail(o, h, l, c, sm, ex_i, de_i, d, X, E, atr, mode, k, flat_sm, out):
    for t in range(len(ex_i)):
        j0 = ex_i[t] + 1; s = d[t]; a = atr[t]
        if j0 > de_i[t] or a <= 0: out[t] = 0.0; continue
        if mode == 0: stop = E[t]
        elif mode == 1: stop = E[t]
        else: stop = X[t] - s * k * a
        best = X[t]; y = np.nan
        for q in range(j0, de_i[t] + 1):
            if sm[q] >= flat_sm: y = o[q] - s * 0.25; break
            if s == 1:
                if o[q] <= stop: y = o[q] - 0.25; break
                if l[q] <= stop: y = stop - 0.25; break
                best = max(best, h[q])
                if mode >= 1: stop = max(stop, best - k * a) if mode == 2 else max(E[t], max(stop, best - k * a))
            else:
                if o[q] >= stop: y = o[q] + 0.25; break
                if h[q] >= stop: y = stop + 0.25; break
                best = min(best, l[q])
                if mode >= 1: stop = min(stop, best + k * a) if mode == 2 else min(E[t], min(stop, best + k * a))
        if np.isnan(y): y = c[de_i[t]] - s * 0.25
        out[t] = s * (y - X[t]) * 2.0

def prep(F, D):
    date2day = pd.Series(np.arange(D.nd), index=D.daydate); date2day = date2day[~date2day.index.duplicated(keep="last")]
    dd = F.date.map(date2day).fillna(-1).astype(int).to_numpy(); ok = dd >= 0
    ds = D.ds[np.maximum(dd, 0)]; de = D.de[np.maximum(dd, 0)]
    # exit bar index: first bar of the day with sm >= tout-1 (tout = exit bar sm + 1)
    ex = np.array([ds[i] + np.searchsorted(D.sm[ds[i]:de[i] + 1], F.tout.iat[i] - 1) if ok[i] else -1 for i in range(len(F))])
    ex = np.minimum(ex, de)
    X = np.where(ex >= 0, D.c[np.maximum(ex, 0)], np.nan)          # approx winning exit level (target filled inside that bar)
    usd = F.u.to_numpy() + np.where(F["mod"].isin(["VW13", "VOLB"]) | (F.get("src", "") == ""), 0.0, 0.0)
    E = X - F.d.to_numpy() * (usd + 1.9) / 2
    return ex, de, X, E, D.atr[np.maximum(dd, 0)], ok
DD = {"nq": Data("nq_1m.npz"), "mnq": Data("mnq_fut.npz")}
RULES = [("BE", 0, 0.0)] + [(f"T{k}", 1, k) for k in (0.10, 0.15, 0.20, 0.30, 0.40)] + [(f"L{k}", 2, k) for k in (0.10, 0.15, 0.20, 0.30)]
rows = []; KEEP = {}
for prof in ("Ultra", "WR70Plus", "Core6"):
    for per in ("IS", "C24", "REAL"):
        F, days = T[prof][per]; D = DD["mnq" if per == "REAL" else "nq"]
        ex, de, X, E, A, ok = prep(F, D)
        win = (F.u.to_numpy() > 0) & ok & (F.tout.to_numpy() - 1 < D.sm[0] * 0 + ((1530 // 100) * 60 + 30 - 1080) % 1440)
        base2 = (2 * F.u * F.w).groupby(F.date).sum().reindex(days, fill_value=0.0).to_numpy()
        def met(dly, x):
            return dict(sharpe=dly.mean() / dly.std() * 252 ** .5, mo=dly.mean() * 21, pf=x[x > 0].sum() / -x[x <= 0].sum(),
                        maxdd=float((np.maximum.accumulate(np.cumsum(dly)) - np.cumsum(dly)).max()))
        x2 = (2 * F.u * F.w).to_numpy()
        r0 = met(base2, x2); rows.append(dict(prof=prof, per=per, rule="2 contratos, salidas actuales", **r0, runner_pf=np.nan, n_run=0))
        for nm, mode, k in RULES:
            out = np.zeros(len(F))
            idx = np.where(win)[0]
            o2 = np.zeros(len(idx))
            run_trail(D.o, D.h, D.l, D.c, D.sm, ex[idx].astype(np.int64), de[idx].astype(np.int64), F.d.to_numpy()[idx].astype(np.float64), X[idx], E[idx], A[idx], mode, k, ((1555 // 100) * 60 + 55 - 1080) % 1440, o2)
            out[idx] = o2 * F.w.to_numpy()[idx]
            # per-trade total for PF: contract1 = u*w, contract2 = u*w + delta (losers: both lose)
            xt = x2 + out
            dly = pd.Series(xt).groupby(F.date.to_numpy()).sum().reindex(days, fill_value=0.0).to_numpy()
            r = met(dly, xt); dlt = out[idx]
            rows.append(dict(prof=prof, per=per, rule=nm, **r, runner_pf=(dlt[dlt > 0].sum() / -dlt[dlt <= 0].sum()) if (dlt <= 0).any() else np.nan, n_run=len(idx),
                             runner_mean=dlt.mean()))
            KEEP[(prof, per, nm)] = out
        print(prof, per, "done", flush=True)
R = pd.DataFrame(rows); R.to_csv("runner.csv", index=False); pickle.dump(KEEP, open("runner_delta.pkl", "wb"))
pd.set_option("display.width", 250)
for prof in ("Ultra", "WR70Plus", "Core6"):
    x = R[R.prof == prof]
    for c in ("sharpe", "pf", "mo", "maxdd", "runner_pf"):
        print(prof, c); print(x.pivot(index="rule", columns="per", values=c)[["IS", "C24", "REAL"]].round(3).to_string())
