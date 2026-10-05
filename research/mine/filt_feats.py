"""Context features at entry for every base (MaxPlus+confluence) trade. All known at the entry bar."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import Data, S
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = pickle.load(open(os.path.join(RES, "feat_trades2.pkl"), "rb"))
def feats(D, F):
    F = F.copy()
    dd = pd.Series(np.arange(D.nd), index=D.daydate).groupby(level=0).last()
    rows = []
    sma = pd.Series(D.pdc).rolling(20, min_periods=15).mean().to_numpy()       # SMA20 of prior closes (pdc is prior close)
    for r in F.itertuples():
        d = dd.get(r.date, -1)
        if d < 0: rows.append([np.nan] * 12); continue
        a, b = D.ds[d], D.de[d] + 1; sm = D.sm[a:b]
        i = a + min(np.searchsorted(sm, r.tin), b - a - 1)
        A = D.atr[d]; s = r.d; px = D.o[i]; ro = D.ro[d]
        vw = D.vwap[i - 1] if i > a else np.nan
        f_vw = (px - vw) * s / A if not np.isnan(vw) else np.nan
        f_open = (px - D.o[ro]) * s / A if ro >= 0 and ro < i else np.nan
        hi = D.h[a:i].max() if i > a else np.nan; lo = D.l[a:i].min() if i > a else np.nan
        rth_hi = D.h[ro:i].max() if ro >= 0 and ro < i else np.nan; rth_lo = D.l[ro:i].min() if ro >= 0 and ro < i else np.nan
        f_rng = (rth_hi - rth_lo) / A if not np.isnan(rth_hi) else np.nan
        f_pos = ((px - lo) / (hi - lo) if s == 1 else (hi - px) / (hi - lo)) if i > a and hi > lo else np.nan     # where in session range (1 = at the extreme in trade direction)
        f_trend = (D.pdc[d] - sma[d]) * s / A if not np.isnan(sma[d]) else np.nan
        f_gap = (D.o[ro] - D.pdc[d]) * s / A if ro >= 0 and not np.isnan(D.pdc[d]) else np.nan
        f_pdret = (D.pdc[d] - D.pdc[d - 1]) * s / A if d >= 1 and not np.isnan(D.pdc[d - 1]) else np.nan
        f_m30 = (D.c[i - 1] - D.c[max(a, i - 31)]) * s / A if i > a + 1 else np.nan
        f_5d = (D.pdc[d] - D.pdc[d - 5]) * s / A if d >= 5 and not np.isnan(D.pdc[d - 5]) else np.nan
        f_atr = A / np.nanmedian(D.atr[max(0, d - 100):d]) if d > 20 else np.nan
        pdh, pdl = D.L[d, 0], D.L[d, 3]
        f_pd = ((px - pdh) / A if s == 1 else (pdl - px) / A) if not np.isnan(pdh) else np.nan     # beyond the prior-day extreme in trade direction
        f_sess = (px - D.svwap[i - 1]) * s / A if i > a else np.nan
        rows.append([f_vw, f_open, f_rng, f_pos, f_trend, f_gap, f_pdret, f_m30, f_5d, f_atr, f_pd, f_sess])
    X = pd.DataFrame(rows, columns=["vw", "open", "rng", "pos", "trend", "gap", "pdret", "m30", "ret5", "atr", "pd", "svw"], index=F.index)
    return pd.concat([F, X], axis=1)
if __name__ == "__main__":
    out = {}
    for per, key in (("IS", "nq_1m.npz"), ("C24", "nq_1m.npz"), ("REAL", "mnq_fut.npz")):
        D = Data(key); F, days = T[per]
        F = F.copy(); F["w"] = F.base_w * np.where(F.rev_bucket, 2.0, 1.0) * np.where((F["mod"] == "REV06") & F.lon_same, 0.0, 1.0)
        out[per] = (feats(D, F[F.w > 0]), days); print(per, len(out[per][0]), flush=True)
    pickle.dump(out, open("base_feats.pkl", "wb"))
