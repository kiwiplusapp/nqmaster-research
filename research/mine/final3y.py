"""Federico 2026-10-09: 'MyFundedFutures and Lucid with WR70Plus and Ultra, best configurations, last 3 years: eval time, pass rate,
trade win rate, money per month, instruments, profile'. Uses the CURRENT NQMaster logic (2026-10-08 rules: ORB prior-close,
VOLB break-even, MOM1030/MOM13 agreement, VOLB trend-only 10:47 cutoff) on REAL MNQ futures 2024-02..2026-09 (the full real-futures
history we have, ~2.7 years) + GoldMaster on REAL MGC (dense grids, unchanged modules).
Step 1: trade sets per profile from the wrq_ engine with true entry price / exit bar, minute equity paths per day (realised + open
        adverse excursion; close MTM for profit stops) -> exact intraday lows for the trailing-drawdown sims.
Step 2: Lucid Flex 50K and MyFundedFutures Rapid EOD 50K: eval (1 contract) and funded lifecycle, history / +1 tick / bootstrap.
-> final3y.json (artifact data), final3y_trades.pkl"""
import os, sys, json, pickle, datetime as dt, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import wrq_port, wrq_combo
from wrq_lib import getD, PER, SLIP
from wrq_exits import arrays, sim
from wrq_port import BASE_W, ULTRA, WR70
from wrq_combo import build, BE, ORBt, VTSO
import acct1c_lib as A
from acct_lab import Z
from news import NEWS

PERIOD = "REAL"; NAME = "mnq_fut.npz"; TICK = 0.25


def module_trades2(per, mod, p=None, slip=SLIP, keep=None):
    name, lo, hi = PER[per]; D = getD(name); E = wrq_port.entries()[name]; E = E[E["mod"] == mod].sort_values("fi", kind="stable")
    if keep is not None: E = E[keep(E, name)]
    Aa = arrays(E); u, ok, out = sim(Aa, D, slip, p or {}, False)
    m = ok & (Aa["date"] >= lo) & (Aa["date"] < hi) & (~Aa["fomc"])
    fi = Aa["fi"][m]; xi = out[m, 1].astype(np.int64); s = Aa["d"][m]
    e = Aa["ent0"][m] + np.where(Aa["et"][m] == 0, s * slip, 0.0)
    return pd.DataFrame(dict(date=Aa["date"][m], mod=mod, tin=D.sm[fi], tout=D.sm[xi] + 1, d=s, u=u[m], fi=fi, xi=xi, e=e, w=BASE_W.get(mod, 1.0)))


wrq_port.module_trades = module_trades2; wrq_combo.module_trades = module_trades2

EST_MODS = ["CRT11", "ORB90", "MSEQ", "ON07", "REV06", "VOLB_tf1", "VW13b", "VW13", "ENG10", "LATEFH"]
PROFILES = {
    "Ultra": (ULTRA, {**BE, **ORBt}, ("MOM1030", "MOM13"), True),
    "UltraLean": ({k: v for k, v in ULTRA.items() if k not in ("ON07", "LATEFH", "ENG10")}, {**BE, **ORBt}, ("MOM1030", "MOM13"), True),
    "WR70Plus": (WR70, {**ORBt, **VTSO}, (), True),
    "Estable": ({k: (ULTRA.get(k) if k in ULTRA else WR70.get(k)) for k in EST_MODS}, {"ORB90": ORBt["ORB90"], **VTSO}, (), False),
}


def trades(prof):
    mods, over, agr, boosts = PROFILES[prof]
    wrq_port.PROFILES["_f"] = mods
    X = build(PERIOD, "_f", {k: v for k, v in over.items() if k in mods}, tuple(a for a in agr if a in mods))
    if not boosts: X["w"] = 1.0
    return X.sort_values(["date", "tin"]).reset_index(drop=True)


T1 = {d: [828] for d in (NEWS["CPI"] | NEWS["NFP"])}
for f in NEWS["FOMC"]:
    m = int((dt.date(f // 10000, f // 100 % 100, f % 100) + dt.timedelta(days=21)).strftime("%Y%m%d")); T1.setdefault(m, []).append(1358)


def news_adjust(X):
    """MFFU funded: flat 2 min before T1 releases: trades open at 08:28 / 13:58 closed at the prior bar close - 1 tick; entries inside
    the window dropped."""
    D = getD(NAME); X = X.copy(); drop = []
    for i, t in enumerate(X.itertuples()):
        for w in T1.get(t.date, []):
            ws = ((w // 100) * 60 + w % 100 - 1080) % 1440
            if ws <= D.sm[t.fi] < ws + 4: drop.append(i); break
            if D.sm[t.fi] < ws <= D.sm[t.xi]:
                k = t.fi + int(np.searchsorted(D.sm[t.fi:t.xi + 1], ws, side="left")) - 1
                px = D.c[k] - t.d * TICK
                X.iat[i, X.columns.get_loc("u")] = (px - t.e) * t.d * D.pv - D.comm; X.iat[i, X.columns.get_loc("xi")] = k; break
    return X.drop(X.index[drop]).reset_index(drop=True)


def minute_paths(X, days):
    """per day: equity low path (realised before + open adverse + exit min) and close-MTM path, 1440 session minutes"""
    D = getD(NAME); pos = {d: i for i, d in enumerate(days)}; nd = len(days)
    Rinc = np.zeros((nd, 1440)); OA = np.zeros((nd, 1440)); XA = np.zeros((nd, 1440)); OC = np.zeros((nd, 1440)); ex = np.zeros(nd)
    for t in X.itertuples():
        if t.date not in pos: continue
        r = pos[t.date]; s = t.d; w = t.w
        q = np.arange(t.fi, t.xi); sm = D.sm[q]
        adv = ((D.l[q] - t.e) if s > 0 else (t.e - D.h[q])) * D.pv - D.comm
        cls = (D.c[q] - t.e) * s * D.pv - D.comm
        np.add.at(OA[r], sm, w * adv); np.add.at(OC[r], sm, w * cls)
        mx = D.sm[t.xi]; advx = ((D.l[t.xi] - t.e) if s > 0 else (t.e - D.h[t.xi])) * D.pv - D.comm
        Rinc[r, mx] += w * t.u; XA[r, mx] += w * min(advx, t.u); ex[r] += w
    Rc = np.cumsum(Rinc, 1)
    low = Rc - Rinc + OA + XA; close = Rc + OC
    return low, close, Rc[:, -1], ex


def day_vectors(nqlow, nqclose, nqfin, gL, gR, G=0.0):
    tl = nqlow + gL; lo = tl.min(1); cl = nqfin + gR[:, -1]
    if G > 0:
        tc = nqclose + gL
        hit = tc >= G; has = hit.any(1); t = hit.argmax(1)
        for d in np.nonzero(has)[0]:
            lo[d] = tl[d, :t[d] + 1].min(); cl[d] = tc[d, t[d]]
    return np.minimum(lo, cl), cl


def stats_trades(u):
    u = np.asarray(u, float); w = u[u > 0]; l = u[u <= 0]
    return dict(n=int(len(u)), wr=round(100 * len(w) / max(len(u), 1), 1), pf=round(w.sum() / -l.sum(), 2) if len(l) else None,
                avg_win=round(w.mean(), 1) if len(w) else 0, avg_loss=round(l.mean(), 1) if len(l) else 0, exp=round(u.mean(), 2))


if __name__ == "__main__":
    z = Z(PERIOD); days = z["days"]; nd = len(days)
    OUT = {"period": [int(days[0]), int(days[-1])], "days": int(nd), "profiles": {}, "accounts": {}}
    GOLD = {"Robust": A.items([], A.GR, 1.0), "WinRate": A.items([], A.GW, 1.0), "WinRate x2": A.items([], A.GW, 2.0)}
    GL = {k: A._sum(PERIOD, it) for k, it in GOLD.items()}; GX = {k: A.exits(PERIOD, it) for k, it in GOLD.items()}
    gold_tr = pickle.load(open("gold_curated_trades.pkl", "rb"))
    gt = {k: pd.concat([gold_tr[m][PERIOD].assign(mod=m) for m in mods]) for k, mods in
          (("Robust", ["OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206"]), ("WinRate", ["OD1030", "ENG0408", "SVWAP22"]))}
    for k in gt: gt[k] = gt[k][gt[k].date.isin(days)]
    TR = {}; PATHS = {}
    for prof in PROFILES:
        X = trades(prof); TR[prof] = X
        PATHS[(prof, False)] = minute_paths(X, days); PATHS[(prof, True)] = minute_paths(news_adjust(X), days)
        print(prof, len(X), flush=True)
    pickle.dump(TR, open("final3y_trades.pkl", "wb"))
    # ---------------- trade-level and monthly stats (1 base contract; gold at 1 MGC per module)
    months = pd.to_datetime(pd.Series(days).astype(str)).dt.to_period("M").astype(str).to_numpy()
    for prof, gname in (("Ultra", "Robust"), ("UltraLean", "Robust"), ("WR70Plus", "WinRate")):
        X = TR[prof]; u_nq = X.u * X.w; low, close, fin, ex = PATHS[(prof, False)]
        gfin = GL[gname][1][:, -1]
        g_u = gt[gname].u.to_numpy()
        dnq = pd.Series(fin, index=days); dall = dnq + gfin
        rec = {}
        for lab, d, uu, ntr in (("nq", dnq, u_nq.to_numpy(), len(X)), ("nq_gold", dall, np.concatenate([u_nq.to_numpy(), g_u]), len(X) + len(g_u))):
            eq = d.cumsum(); mo = d.groupby(months).sum()
            r = stats_trades(uu); r.update(trades_per_day=round(ntr / nd, 2), per_month=round(d.mean() * 21), max_dd=round((eq.cummax() - eq).max()),
                                           worst_month=round(mo.min()), best_month=round(mo.max()), pos_months=f"{(mo > 0).sum()}/{len(mo)}",
                                           sharpe=round(d.mean() / d.std() * np.sqrt(252), 2), worst_day=round(d.min()))
            r["monthly"] = {k: round(v) for k, v in mo.items()}
            yrs = {}
            for y in (2024, 2025, 2026):
                mk = (days // 10000) == y; dd = d[mk]
                if lab == "nq": uy = uu[(X.date // 10000 == y).to_numpy()]
                else: uy = np.concatenate([u_nq[(X.date // 10000 == y).to_numpy()].to_numpy(), g_u[(gt[gname].date // 10000 == y).to_numpy()]])
                s = stats_trades(uy); s.update(per_month=round(dd.mean() * 21)); yrs[y] = s
            r["years"] = yrs
            last6 = days >= 20260401; dd = d[last6]
            if lab == "nq": u6 = uu[(X.date >= 20260401).to_numpy()]
            else: u6 = np.concatenate([u_nq[(X.date >= 20260401).to_numpy()].to_numpy(), g_u[(gt[gname].date >= 20260401).to_numpy()]])
            s = stats_trades(u6); s.update(per_month=round(dd.mean() * 21)); r["last6"] = s
            rec[lab] = r
        rec["gold"] = stats_trades(g_u); rec["gold"]["per_month"] = round(gfin.mean() * 21)
        mods = {}
        for m, g in X.groupby("mod"):
            s = stats_trades((g.u * g.w).to_numpy()); s["per_month"] = round((g.u * g.w).sum() / nd * 21); mods[m] = s
        rec["modules"] = mods
        OUT["profiles"][prof] = rec
        print(prof, rec["nq_gold"]["wr"], rec["nq_gold"]["pf"], rec["nq_gold"]["per_month"], flush=True)
    pickle.dump((PATHS, GL, GX), open("/tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad/final3y_paths.pkl", "wb"))
    json.dump(OUT, open("final3y_stats.json", "w"), indent=1, default=int)
