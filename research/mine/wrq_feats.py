"""wrq_feats: decision-time features for every wrq entry (information up to the bar BEFORE the fill bar, daily data from prior
days only). Directional features are signed by the trade direction (+ = in favour of the trade).
  tr10/tr20/tr50  (prior close - SMA n of prior closes) / ATR          r5/r20/r60  n-day return of prior closes / ATR
  atrr            ATR / median ATR of the previous 60 days              risk        stop distance / ATR
  vw              (close - RTH VWAP) / ATR (RTH only)                    svw         (close - session VWAP) / ATR
  pdcd            (close - prior RTH close) / ATR                       gap         (RTH open - prior close) / ATR (after 09:30)
  onr             overnight range 18:00 -> min(entry, 09:29) / ATR       pdr         prior RTH range / ATR
  pdpos           prior close position in the prior RTH range (1 = at the extreme in trade direction)
  dpos            position of the close in the session range so far (1 = at the extreme in trade direction)
  m30             30-minute move / ATR      rv60  sum |1m close changes| over 60 bars / ATR      tso  minutes since 09:30
  dow             weekday 0-4
-> wrq_feats.pkl {dataset: DataFrame aligned with wrq_entries.pkl rows}"""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_lib import getD, S

def feats(D, E):
    fi = E.fi.to_numpy(np.int64); s = E.d.to_numpy(float); day = D.day[fi]; A = D.atr[day]; A = np.where(A > 0, A, np.nan)
    j = np.maximum(fi - 1, 0); px = D.c[j]
    pdc = D.pdc
    ser = pd.Series(pdc)
    out = {}
    for n in (10, 20, 50):
        sma = ser.rolling(n, min_periods=n).mean().to_numpy(); out[f"tr{n}"] = (pdc[day] - sma[day]) * s / A
    for n in (5, 20, 60):
        prev = ser.shift(n).to_numpy(); out[f"r{n}"] = (pdc[day] - prev[day]) * s / A
    med = pd.Series(D.atr).rolling(60, min_periods=20).median().shift(1).to_numpy(); out["atrr"] = D.atr[day] / med[day]
    out["risk"] = np.abs(E.ent0.to_numpy() - E.sl0.to_numpy()) / A
    vw = D.vwap[j]; out["vw"] = (px - vw) * s / A
    out["svw"] = (px - D.svwap[j]) * s / A
    out["pdcd"] = (px - pdc[day]) * s / A
    ro = D.ro[day]; after = (ro >= 0) & (ro <= j)
    out["gap"] = np.where(after, (D.o[np.maximum(ro, 0)] - pdc[day]) * s / A, np.nan)
    pdh, pdl = D.L[day, 0], D.L[day, 3]
    out["pdr"] = (pdh - pdl) / A
    pos = (pdc[day] - pdl) / (pdh - pdl); out["pdpos"] = np.where(s > 0, pos, 1 - pos)
    # session-so-far quantities (python loop over entries; ~10k per dataset)
    onr = np.full(len(fi), np.nan); dpos = np.full(len(fi), np.nan); rv = np.full(len(fi), np.nan); m30 = np.full(len(fi), np.nan)
    s930 = S(930); ds = D.ds; absd = np.abs(np.diff(D.c, prepend=D.c[0]))
    cs = np.cumsum(absd)
    for k in range(len(fi)):
        a = ds[day[k]]; jj = j[k]
        if jj < a: continue
        seg_h = D.h[a:jj + 1]; seg_l = D.l[a:jj + 1]
        hi = seg_h.max(); lo = seg_l.min()
        if hi > lo: dpos[k] = (px[k] - lo) / (hi - lo) if s[k] > 0 else (hi - px[k]) / (hi - lo)
        # overnight range up to min(entry, 09:29)
        sm = D.sm[a:jj + 1]; mm = sm < s930
        if mm.any(): onr[k] = (seg_h[mm].max() - seg_l[mm].min()) / A[k]
        b = max(a, jj - 60); rv[k] = (cs[jj] - cs[b]) / A[k] if jj > a else np.nan
        b = jj - 30
        if b >= a: m30[k] = (D.c[jj] - D.c[b]) * s[k] / A[k]
    out.update(onr=onr, dpos=dpos, rv60=rv, m30=m30)
    out["tso"] = (D.sm[fi] - s930).astype(float)
    out["dow"] = pd.to_datetime(E.date.astype(str), format="%Y%m%d").dt.dayofweek.to_numpy().astype(float)
    return pd.DataFrame(out, index=E.index)

if __name__ == "__main__":
    EN = pickle.load(open("wrq_entries.pkl", "rb")); OUT = {}
    for name, E in EN.items():
        OUT[name] = feats(getD(name), E); print(name, OUT[name].shape, flush=True)
    pickle.dump(OUT, open("wrq_feats.pkl", "wb"))
    print(OUT["nq_1m.npz"].describe().T.round(2).to_string())
