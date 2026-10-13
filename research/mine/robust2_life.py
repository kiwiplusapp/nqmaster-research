"""Robustness lab, step 4: full account lifecycle per 'slot' (buy eval -> pass -> funded -> payouts -> bust -> buy a new eval ...)
for MyFundedFutures Rapid EOD 50K and Lucid Flex 50K at 1 contract, with the eval daily profit stop (MFFU $800 / Lucid $1,400,
needed for the 30% / 50% consistency rules). Policies: a LOW set while the cushion is below a threshold, Ultra above it, in the
eval (2 gears) and in the funded account (gear by day-start cushion). LOW = Ultra with a per-trade $ risk cap (150-300) or Estable.
1,000 resampled 12-month paths per period (10-day blocks of real days, the same paths for every policy), plus +1 tick per side.
Chosen on 2020-23, confirmed on 2024-26. -> robust2_life.json"""
import os, sys, json, pickle, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_build import minute_paths, SP, setup
import robust2_build as RB
from mffu_rapid import life_m
import acct1c_lib as A
from wrq_lib import getD
NB = 1000; H = 252; BLK = 10


def full_paths(X, days):
    """intraday low path and close-MTM path per day (nd x 1440) -> (low, close, fin)"""
    D = getD(RB.NAME); pos = {d: i for i, d in enumerate(days)}; nd = len(days)
    Rinc = np.zeros((nd, 1440)); OA = np.zeros((nd, 1440)); XA = np.zeros((nd, 1440)); OC = np.zeros((nd, 1440))
    for t in X.itertuples():
        r = pos.get(t.date)
        if r is None: continue
        s = t.d; w = t.w; q = np.arange(t.fi, t.xi); sm = D.sm[q]
        adv = ((D.l[q] - t.e) if s > 0 else (t.e - D.h[q])) * D.pv - D.comm
        cls = (D.c[q] - t.e) * s * D.pv - D.comm
        np.add.at(OA[r], sm, w * adv); np.add.at(OC[r], sm, w * cls)
        mx = D.sm[t.xi]; advx = ((D.l[t.xi] - t.e) if s > 0 else (t.e - D.h[t.xi])) * D.pv - D.comm
        Rinc[r, mx] += w * t.u; XA[r, mx] += w * min(advx, t.u)
    Rc = np.cumsum(Rinc, 1)
    return Rc - Rinc + OA + XA, Rc + OC, Rc[:, -1]


def vectors(low, close, fin, G):
    lo = low.min(1); cl = fin.copy()
    if G > 0:
        hit = close >= G; has = hit.any(1); t = hit.argmax(1)
        for d in np.nonzero(has)[0]: lo[d] = low[d, :t[d] + 1].min(); cl[d] = close[d, t[d]]
    return np.minimum(lo, cl), cl


def boot(days, mask, seed):
    pos = np.nonzero(mask)[0]; rng = np.random.default_rng(seed); nb = H // BLK + 2
    st = rng.integers(0, len(pos) - BLK, size=(NB, nb))
    return [np.ascontiguousarray(np.concatenate([pos[s:s + BLK] for s in row])[:H + 1]) for row in st]


SETS = ["Ultra", "Estable", "WR70Plus", "Ultra_cap150", "Ultra_cap200", "Ultra_cap250", "Ultra_cap300"]
FIRMS = {"MFFU": dict(G=800.0, cons=0.3, fee=157.0), "Lucid": dict(G=1400.0, cons=0.5, fee=105.2)}


def run_life(V, firm, low_e, Ce, low_f, c1, ids, cost):
    F = FIRMS[firm]; sfx = "_t1" if cost else ""
    EL = np.ascontiguousarray(np.array([V[(low_e + sfx, F["G"])][0], V[("Ultra" + sfx, F["G"])][0]]))
    EC = np.ascontiguousarray(np.array([V[(low_e + sfx, F["G"])][1], V[("Ultra" + sfx, F["G"])][1]]))
    FL = np.ascontiguousarray(np.array([V[(low_f + sfx, 0.0)][0], V[("Ultra" + sfx, 0.0)][0], V[("Ultra" + sfx, 0.0)][0]]))
    FC = np.ascontiguousarray(np.array([V[(low_f + sfx, 0.0)][1], V[("Ultra" + sfx, 0.0)][1], V[("Ultra" + sfx, 0.0)][1]]))
    res = np.zeros((len(ids), 9))
    for k, ix in enumerate(ids):
        o = np.zeros((2, 9))
        if firm == "MFFU": r = life_m(EL, EC, float(Ce), 3000.0, 2000.0, F["cons"], 4, F["fee"], FL, FC, float(c1), float(c1), 4100.0, 0, ix, H, H, o)
        else: r = A.life(EL, EC, float(Ce), 3000.0, 2000.0, F["cons"], np.ones(len(V[("Ultra", 0.0)][0]), np.bool_), F["fee"], FL, FC, float(c1), float(c1), 0, 4000.0, 150.0, 2000.0, 2000.0, ix, H, H, o)
        res[k, :o.shape[1]] = o[0]
    return dict(per_month=round(float(res[:, 0].mean() / 12)), p10_month=round(float(np.percentile(res[:, 0], 10) / 12)), evals=round(float(res[:, 1].mean()), 2),
                passes=round(float(res[:, 2].mean()), 2), funded_busts=round(float(res[:, 3].mean()), 2), payouts=round(float(res[:, 4].mean()), 1),
                accounts_lost=round(float((res[:, 1] - res[:, 2] + res[:, 3]).mean()), 2), p_neg_year=round(100 * float((res[:, 0] < 0).mean()), 1))


if __name__ == "__main__":
    setup(); TR = pickle.load(open(os.path.join(HERE, "robust2_trades.pkl"), "rb"))
    days = pickle.load(open(os.path.join(SP, "robust2_paths.pkl"), "rb"))[0]
    V = {}
    for k in SETS:
        low, close, fin = full_paths(TR[k], days)
        c = (TR[k].w * 1.0).groupby(TR[k].date).sum().reindex(days, fill_value=0.0).to_numpy()
        for G in (0.0, 800.0, 1400.0):
            lo, cl = vectors(low, close, fin, G); V[(k, G)] = (lo, cl)
            lo2, cl2 = vectors(low - c[:, None], close - c[:, None], fin - c, G); V[(k + "_t1", G)] = (lo2, cl2)
        print("paths", k, flush=True)
    pickle.dump((days, V), open(os.path.join(SP, "robust2_vecs.pkl"), "wb"))
    IDS = {"2020-23": boot(days, (days >= 20200101) & (days < 20240101), 11), "2024-26": boot(days, days >= 20240101, 12)}
    OUT = {}
    POL = [("today: Ultra eval / Ultra funded", "Ultra", 0, "Ultra", 0), ("today: Estable<1200 eval / Ultra funded", "Estable", 1200, "Ultra", 0)]
    for low in ("Ultra_cap150", "Ultra_cap200", "Ultra_cap250", "Ultra_cap300", "Estable"):
        for Ce in (0, 1200, 1600, 2000):
            for c1 in (0, 1500, 2000, 2500, 3000):
                if Ce == 0 and c1 == 0: continue
                POL.append((f"eval {low}<{Ce} / funded {low}<{c1}", low, Ce, low, c1))
    for firm in FIRMS:
        for name, le, Ce, lf, c1 in POL:
            r = {}
            for per, ids in IDS.items():
                r[per] = run_life(V, firm, le, Ce, lf, c1, ids, False)
                r[per + " +1tick"] = run_life(V, firm, le, Ce, lf, c1, ids, True)
            OUT[f"{firm} | {name}"] = r
            print(firm, f"{name:46s}", {p: (v["per_month"], v["funded_busts"], v["accounts_lost"], v["p_neg_year"]) for p, v in r.items()}, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "robust2_life.json"), "w"), indent=1)
