"""Minute-level equity path of the MaxPlus portfolio (per 1-unit size, ICT x2) including UNREALIZED P&L, for Apex-style
intraday trailing drawdown (trails the peak of open equity). For each trade: entry = open of the entry bar (+slip),
open P&L per minute from bar high/low (favourable / adverse), realized usd at the exit bar.
Output per dataset: flat arrays (day index, minute, fav, adv, realized-close) of event minutes."""
import pickle, numpy as np, pandas as pd
from ict import load
M = pickle.load(open("modpnl.pkl", "rb"))
def sm(om): return (np.asarray(om) - 1080) % 1440
def build(tag, F, days, mods=None, wmap={"ICT": 2.0}):
    D = load(tag + ".npz"); date = D["date"]; smm = sm(D["om"]); o, h, l, c = D["o"], D["h"], D["l"], D["c"]
    first = pd.Series(np.arange(len(date))).groupby(date).first(); last = pd.Series(np.arange(len(date))).groupby(date).last()
    if mods is not None: F = F[F["mod"].isin(mods)]
    out = {}
    for d, g in F.groupby("date"):
        if d not in first.index: continue
        a, b = first[d], last[d] + 1; mm = smm[a:b]; n = b - a
        fav = np.zeros(n); adv = np.zeros(n); rel = np.zeros(n)
        for r in g.itertuples():
            q = wmap.get(r.mod, 1.0)
            i0 = np.searchsorted(mm, r.tin); i1 = np.searchsorted(mm, r.tout - 1)
            i0 = min(i0, n - 1); i1 = min(max(i1, i0), n - 1)
            e = o[a + i0] + 0.25 * r.d
            if i1 > i0:
                seg = slice(a + i0, a + i1)          # bars while open (exit bar handled by realized)
                if r.d == 1: fv = (h[seg] - e) * 2; av = (l[seg] - e) * 2
                else: fv = (e - l[seg]) * 2; av = (e - h[seg]) * 2
                fav[i0:i1] += q * fv; adv[i0:i1] += q * av
            rel[i1:] += q * r.u
        out[d] = (mm, fav, adv, rel)
    # flatten over the ordered day list (days without trades -> nothing)
    di, fv, av, rl = [], [], [], []
    for k, d in enumerate(days):
        if d not in out: continue
        mm, fav, adv, rel = out[d]
        nz = np.nonzero((fav != 0) | (adv != 0) | (np.diff(np.r_[0.0, rel]) != 0))[0]
        di.append(np.full(len(nz), k)); fv.append(rel[nz] + fav[nz]); av.append(rel[nz] + adv[nz]); rl.append(rel[nz])
    return dict(day=np.concatenate(di), fav=np.concatenate(fv), adv=np.concatenate(av), rel=np.concatenate(rl), ndays=len(days))
if __name__ == "__main__":
    from riskrules import apply
    res = {}
    for per in ("REAL", "C24", "IS"):
        P, F = M["mnq_fut"] if per == "REAL" else M["nq_1m"]
        if per == "C24": F = F[F.date >= 20240101]; days = P.index[P.index >= 20240101]
        elif per == "IS": F = F[F.date < 20240101]; days = P.index[P.index < 20240101]
        else: days = P.index
        T = apply(F)                                           # conflicts already applied upstream; keep all trades
        res[per] = {"ALL": build("mnq_fut" if per == "REAL" else "nq_1m", T, np.array(days)),
                    "MOM11": build("mnq_fut" if per == "REAL" else "nq_1m", T, np.array(days), mods=["MOM11"], wmap={})}
        print(per, len(res[per]["ALL"]["day"]), "events")
    pickle.dump(res, open("minute_paths.pkl", "wb"))
