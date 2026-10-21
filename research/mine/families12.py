"""Batch 12 (2026-10-21): layer B of the volume / delta / order-flow round = the layer-A delta families (delta_orb.py) run with a
BAR-DELTA PROXY on 16 years of real NQ futures (nqdb.npz has volume).  Proxy per 1-min bar: 'cl' = volume x (2 (close - low) /
(high - low) - 1) (close location), 'tr' = sign(close - open) x volume (tick rule).  Validated against the true aggressor delta on
2025-05..2026-10 (delta_orb.py proxy -> proxy_validation.json): 1-min corr cl 0.54 / tr 0.61, 15-min sums 0.53 / 0.60, sign agreement
69 / 76% -> above the 0.5 bar fixed before looking, so the results are evidence, but noisy evidence.
Federico's split (env MINE_T1=20190101 MINE_T2=20230101 in run_mine_db.py, defaults untouched): T1 = 2019-01..2022-12 real $ (choose),
T2 = 2023-01..2026-10 real $ (check); cost-normalised A = 2010-06..2014-12, B = 2015-01..2018-12 (regime control).
  PX_ORB    opening range 09:30 + T (15 / 30 / 60); stop order 1 tick beyond the edge (features from bars <= b-1) or first 1-min close
            beyond (market next open, features <= b); stop at the opposite edge (floor 0.10 ATR, skip > 1 ATR) or 0.35 ATR; target 1 / 2 R;
            trend filter 0 / 1; breakouts until 14:00; max 1 / day.  dw = delta window: none (CONTROL), dl5 / dl15 (proxy delta / volume
            ratio of the last 5 / 15 min >= dthr 0 / .03 / .06 / .10), cum (since 09:30 >= 0 / .01 / .02 / .04), q5 / q15 (raw delta of the
            last 5 / 15 min >= the dthr quantile (.5 / .75 / .9) of |the previous 12 same-length windows|).  px = proxy kind.
  PX_ABS    absorption at the RTH extreme / ORB30 edge (volume >= m x 20-min mean, body <= 1/4 range) -> fade; dcond none (control) /
            with / against (proxy delta vs the extreme direction); stop k ATR, target R.
  PX_DIV    new W-min high / low with the session proxy CVD not confirming -> fade (control fade_all); confirming -> follow (control
            follow_all).
  PX_VFLIP  price at the RTH VWAP (0.05 ATR), 5-min proxy delta ratio flips sign (|dl5| >= thr) -> follow; control: 5-min price change flips.
  PX_CLIMAX |proxy delta| >= z std of the previous 60 min -> fade / follow; control: volume >= mean + z std, direction = sign(close - open).
Grid 2,208 configs.  Selection in b12_select.py (protocol at its top)."""
import numpy as np
from core import ev_from_lists
from delta_orb import proxy_flow, orb_events, cond_mask, a2_base, a2_events

CATEGORICAL12 = ("ent", "tf", "dw", "px", "loc", "dcond", "mode", "dir", "src")


def gen_px_orb(D, p):
    ev, k, d = orb_events(D, p["T"], p["ent"], p["sk"], p["R"], p["tf"])
    ok = k >= 200; ev = {kk: v[ok] for kk, v in ev.items()}; k = k[ok]; d = d[ok]
    if len(k) == 0: return ev_from_lists([])
    if p["dw"] == "none": return ev
    F = proxy_flow(D, p["px"]); Fe = F.feats(k, ev["d"], D.ds[d], D.ro[d]); m = cond_mask(Fe, p["dw"], p["dthr"])
    return {kk: v[m] for kk, v in ev.items()}


def _a2(fam):
    def gen(D, p):
        B = a2_base(D, proxy_flow(D, p["px"]), 0, D.n); return a2_events(D, B, fam, p)
    return gen


def _g(**kw):
    import itertools
    keys = list(kw); return [dict(zip(keys, vals)) for vals in itertools.product(*kw.values())]


_CONDS = [("none", 0.0)] + [(f"dl{w}", t) for w in (5, 15) for t in (0.0, 0.03, 0.06, 0.10)] + [("cum", t) for t in (0.0, 0.01, 0.02, 0.04)] + [(f"q{w}", q) for w in (5, 15) for q in (0.5, 0.75, 0.9)]
GRID_ORB = [dict(T=T, ent=e, sk=sk, R=R, tf=tf, px=px, dw=dw, dthr=dt) for T in (15, 30, 60) for e in ("stop", "close") for sk in ("opp", 0.35) for R in (1.0, 2.0)
            for tf in (0, 1) for px in ("cl", "tr") for dw, dt in _CONDS]
GRID_ABS = _g(loc=("sess", "orb30"), m=(2.0, 3.0), dcond=("none", "with", "against"), k=(0.2, 0.35), R=(0.5, 1.0, 2.0), px=("cl", "tr"))
GRID_DIV = _g(W=(15, 30), mode=("fade_div", "fade_all", "follow_conf", "follow_all"), k=(0.2, 0.35), R=(0.5, 1.0, 2.0), px=("cl", "tr"))
GRID_VFLIP = _g(thr=(0.05, 0.10), mode=("delta", "price"), k=(0.2, 0.35), R=(0.5, 1.0, 2.0), px=("cl", "tr"))
GRID_CLIMAX = _g(z=(3.0, 4.0), dir=("fade", "follow"), src=("delta", "vol"), k=(0.2, 0.35), R=(0.5, 1.0, 2.0), px=("cl", "tr"))

FAMILIES12 = {"PX_ORB": (gen_px_orb, GRID_ORB, 1), "PX_ABS": (_a2("ABS"), GRID_ABS, 2), "PX_DIV": (_a2("DIV"), GRID_DIV, 2),
              "PX_VFLIP": (_a2("VFLIP"), GRID_VFLIP, 2), "PX_CLIMAX": (_a2("CLIMAX"), GRID_CLIMAX, 2)}

if __name__ == "__main__":
    print({k: len(v[1]) for k, v in FAMILIES12.items()}, sum(len(v[1]) for v in FAMILIES12.values()))
