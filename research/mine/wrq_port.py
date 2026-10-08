"""wrq_port: portfolio reconstruction of the CURRENT NQMaster profiles from wrq entry specs (import-safe).
Ultra (ampliado + night): ORB60 0.6R, ORB90 0.6R, MSEQ, MSEQS, CRT11 2R, ICT (corrected, x2), MOM11 (VWAP agree), MOM1030, MOM13,
  ON07, REV06, LON, VW13 wide (VW13b 0.15 ATR + second lot VW13 at 0.30), VOLB (tf0 2R), LATE15, LATEFH, ENG10, NF05, LF06, LF0430.
WR70Plus (+ NightOnWr70): ORB60 0.75R, ORB90, MSEQ, MSEQS, CRT11, ICT x2, MOM11, REV06, VW13b + VW13, VOLB_tf1 0.5R, LATE15,
  NF05, LF06, LF0430.
Rules as in wr70_eval.build: first-come conflict filter (no opposite NQ positions), confluence A (late CRT11/MOM13/MSEQ/MSEQS after
11:00 x2 when against MOM11 and with the overnight sign of ON07/REV06/LON present in the profile), confluence B (REV06 skipped when
LON already entered the same way), 12 context rules (filt_sel.pkl, cap x2), FOMC days skipped. 1 base contract, $1.90 RT + 1 tick."""
import os, sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wrq_lib import getD, PER, SLIP, S
from wrq_exits import arrays, sim
HERE = os.path.dirname(os.path.abspath(__file__))
ULTRA = {"ORB60": {}, "ORB90": {}, "MSEQ": {}, "MSEQS": {}, "CRT11": {}, "ICT": {}, "MOM11": {}, "MOM1030": {}, "MOM13": {}, "ON07": {}, "REV06": {},
         "LON": {}, "VW13b": {}, "VW13": {}, "VOLB": {}, "LATE15": {}, "LATEFH": {}, "ENG10": {}, "NF05": {}, "LF06": {}, "LF0430": {}}
WR70 = {"ORB60": {"kt": 1.25}, "ORB90": {}, "MSEQ": {}, "MSEQS": {}, "CRT11": {}, "ICT": {}, "MOM11": {}, "REV06": {}, "VW13b": {}, "VW13": {},
        "VOLB_tf1": {}, "LATE15": {}, "NF05": {}, "LF06": {}, "LF0430": {}}
PROFILES = {"Ultra": ULTRA, "WR70Plus": WR70}
BASE_W = {"ICT": 2.0}
LATE = ["CRT11", "MOM13", "MSEQ", "MSEQS"]
_EN = None
def entries():
    global _EN
    if _EN is None: _EN = pickle.load(open(os.path.join(HERE, "wrq_entries.pkl"), "rb"))
    return _EN

def per_data(per):
    return PER[per][0]

def days_of(per):
    name, lo, hi = PER[per]; D = getD(name)
    dd = D.daydate[(D.ro >= 0)]
    dd = dd[(dd >= lo) & (dd < hi)]
    if per != "L15":
        sys.path.insert(0, os.path.dirname(HERE)); from news import NEWS
        dd = dd[~np.isin(dd, list(NEWS["FOMC"]))]
    return np.array(sorted(set(dd)))

def module_trades(per, mod, p=None, slip=SLIP, keep=None):
    """Trades of one module in one period with exit params p; keep: optional boolean function(DataFrame of entries) -> mask."""
    name, lo, hi = PER[per]; D = getD(name); E = entries()[name]; E = E[E["mod"] == mod].sort_values("fi", kind="stable")
    if keep is not None: E = E[keep(E)]
    A = arrays(E); norm = per == "L15"
    u, ok, out = sim(A, D, 0.0 if norm else slip, p or {}, norm)
    m = ok & (A["date"] >= lo) & (A["date"] < hi) & (~A["fomc"] if per != "L15" else True)
    fi = A["fi"][m]; xi = out[m, 1].astype(np.int64)
    return pd.DataFrame(dict(date=A["date"][m], mod=mod, tin=D.sm[fi], tout=D.sm[xi] + 1, d=A["d"][m], u=u[m], fi=fi, w=BASE_W.get(mod, 1.0)))

def conflict_filter(T):
    keep = []
    for d, g in T.groupby("date", sort=False):
        openpos = []
        for r in g.sort_values("tin", kind="stable").itertuples():
            live = [dd for (to, dd) in openpos if to > r.tin]
            if any(dd == -r.d for dd in live): continue
            openpos.append((r.tout, r.d)); keep.append(r.Index)
    return T.loc[keep]

_SEL = None
def apply_rules(X, per, context=True):
    global _SEL
    X = X.sort_values(["date", "tin"]).copy()
    m11 = X[X["mod"] == "MOM11"].groupby("date").d.first()
    on = X[X["mod"].isin(["ON07", "REV06", "LON"])].groupby("date").d.agg(lambda s: np.sign(s.sum()))
    A = X["mod"].isin(LATE) & (X.date.map(m11) * X.d == -1) & (X.date.map(on) * X.d == 1) & (X.tin > S(1100))
    # confluence B: REV06 skipped when LON already entered in the same direction
    lon = X[X["mod"] == "LON"].set_index("date")
    lon_d = lon.d[~lon.index.duplicated()]; lon_t = lon.tin[~lon.index.duplicated()]
    Bskip = (X["mod"] == "REV06") & (X.date.map(lon_d) == X.d) & (X.date.map(lon_t) <= X.tin)
    b = pd.Series(1.0, index=X.index); keep = ~Bskip
    if context:
        if _SEL is None: _SEL = pickle.load(open(os.path.join(HERE, "filt_sel.pkl"), "rb"))
        import filt_feats
        D = getD(per_data(per)); F = filt_feats.feats(D, X[["date", "mod", "tin", "d"]])
        for r, k in _SEL:
            x = F[r["feat"]]; mm = ((X["mod"] == r["mod"]) & ((x < r["hi"]) if r["bucket"].startswith("low") else (x >= r["lo"]))).fillna(False)
            if k == "boost": b[mm] = 2.0
            else: keep &= ~mm
    bw = X.w.copy(); w = bw * np.where(A, 2.0, 1.0) * b
    X["w"] = np.minimum(w, np.maximum(bw, 2.0))
    return X[keep]

def build_profile(per, prof, over=None, slip=SLIP, rules=True, cache=None):
    """over: {mod: (params, keep_fn)} replacing the profile's default exit params / adding an entry filter."""
    parts = []
    for mod, p in PROFILES[prof].items() if isinstance(prof, str) else prof.items():
        q, kf = dict(p), None
        if over and mod in over:
            q2, kf = over[mod]; q = dict(p); q.update(q2 or {})
        key = (per, mod, tuple(sorted(q.items())), slip, kf)
        if cache is not None and key in cache: T = cache[key]
        else:
            T = module_trades(per, mod, q, slip, kf)
            if cache is not None: cache[key] = T
        parts.append(T)
    X = pd.concat(parts, ignore_index=True)
    X = conflict_filter(X.sort_values(["date", "tin"], kind="stable").reset_index(drop=True))
    if rules: X = apply_rules(X, per)
    return X

def metrics(X, days):
    x = X.u * X.w; d = x.groupby(X.date).sum().reindex(days, fill_value=0.0); eq = d.cumsum()
    return dict(n=len(X), tpd=len(X) / len(days), wr=100 * (X.u > 0).mean(), pf=x[x > 0].sum() / -x[x <= 0].sum(),
                sharpe=d.mean() / d.std() * np.sqrt(252), mo=d.mean() * 21, maxdd=(eq.cummax() - eq).max())

def daily(X, days):
    return (X.u * X.w).groupby(X.date).sum().reindex(days, fill_value=0.0)
