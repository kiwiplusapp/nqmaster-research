"""2026-10-22 Federico: 'what if we trade only the New York session with 4 contracts?'. Current system (ultra_d4 = acct_2027 trade set
without gold), real Databento NQ 2020-26, $1.90 + slippage as in research. NY = entries 09:30-16:00 ET (research minute index sm = minutes since 18:00 ET: 930-1319) (drops NF05, LF06, LF0430, ON07,
REV06, LON, SO04 and any other overnight entry). Minute paths per day (robust2_life.full_paths), x k contracts per module.
Eval: prop_wf.race (minute, EOD trailing, consistency, profit stop G); serial = new eval the day after a bust, up to 3 inside 22 days.
Funded: acct1c_lib.fu_flex / fu_pro, mffu_rapid.fu_m over 252 days from each start (k contracts, no risk cap).
T1 starts 2020-03..2023-10, T2 2024-01..; edge full / -35% / zero (haircut scaled with k).  -> nyonly.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from robust2_life import full_paths, vectors, SP
import prop_wf, acct1c_lib as A, mffu_rapid as M
CACHE = os.path.join("/tmp/claude-0/-home-user-nqmaster-research/176a42ca-c215-52e2-84dc-57e214e477d4/scratchpad", "nyonly_paths.pkl")
DURABLE = [{"fam": "CLOCK_ANCHOR", "j": 1527}, {"fam": "RVOL_DRIVE", "j": 4226}, {"fam": "OR_FAIL", "j": 142}, {"fam": "PIVOT_FADE", "j": 365}]


def build():
    if os.path.exists(CACHE): return pickle.load(open(CACHE, "rb"))
    import robust2_build as RB
    from wrq_lib import getD
    from sniper_life import build as sbuild
    from wrq_port import conflict_filter
    from six_life import new_trades
    E = RB.setup(); D = getD(RB.NAME)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]
    T = sbuild(E, D); T = T[T.date.isin(days)]
    NW = new_trades(D, DURABLE); NW = NW[NW.date.isin(days)]
    NW = NW.assign(tin=D.sm[NW.fi.to_numpy().astype(int)], tout=D.sm[NW.xi.to_numpy().astype(int)] + 1)
    X = conflict_filter(pd.concat([T, NW], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
    X["smin"] = D.sm[X.fi.to_numpy().astype(int)]; X["smout"] = D.sm[X.xi.to_numpy().astype(int)]
    ny = (X.smin >= 930) & (X.smin < 1320)
    out = {"days": days, "X": X[["date", "mod", "d", "u", "w", "smin", "smout", "fi", "xi"]], "ALL": full_paths(X, days), "NY": full_paths(X[ny], days)}
    pickle.dump(out, open(CACHE, "wb")); return out


def stats(X, fin, days, k):
    n = len(days); m = n / 21.0; p = X.u * X.w
    eq = np.cumsum(fin * k); dd = np.max(np.maximum.accumulate(eq) - eq)
    return dict(trades_day=round(len(X) / n, 2), wr=round(100 * (X.u > 0).mean(), 1), pf=round(p[p > 0].sum() / -p[p < 0].sum(), 2),
                usd_month=round(k * fin.sum() / m), maxdd=round(dd), worst_day=round(k * fin.min()), best_day=round(k * fin.max()))


def max_open(X, k):
    ev = []
    for t in X.itertuples(): ev += [(t.fi, k * t.w), (t.xi, -k * t.w)]
    ev.sort(key=lambda e: (e[0], -e[1] < 0)); cur = 0; mx = 0; arr = []
    for _, q in ev: cur += q; mx = max(mx, cur)
    # per-day maxima for a p99
    return mx


FIRMS = {"Lucid Flex 50K": dict(T=3000, D=2000, cons=0.5, mind=1, G=1350, fee=146, fund="flex", Q=150, cap1=2000, cap2=2000, X=4000),
         "Lucid Pro 50K": dict(T=3000, D=2000, cons=0.0, mind=1, G=0, fee=192, fund="pro", cap1=2000, cap2=2500, X=2000),
         "MFFU 50K": dict(T=3000, D=2000, cons=0.3, mind=4, G=800, fee=157, fund="mffu", X=4100),
         "Lucid Flex 150K": dict(T=9000, D=4500, cons=0.5, mind=1, G=4050, fee=285, fund="flex", Q=250, cap1=3000, cap2=3000, X=6000)}


def run():
    P = build(); days = np.asarray(P["days"]); n = len(days); idx = np.arange(n, dtype=np.int64)
    d24 = int(np.searchsorted(days, 20240101))
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]
    OUT = {"stats": {}, "max_open_micros": {}, "eval": {}, "funded": {}}
    for sess in ("ALL", "NY"):
        lo, cl, fin = P[sess]; X = P["X"] if sess == "ALL" else P["X"][(P["X"].smin >= 930) & (P["X"].smin < 1320)]
        for k in (1, 2, 4):
            OUT["stats"][f"{sess} {k}c"] = {"2020-23": stats(X[X.date < 20240101], fin[:d24], days[:d24], k), "2024-26": stats(X[X.date >= 20240101], fin[d24:], days[d24:], k)}
            OUT["max_open_micros"][f"{sess} {k}c"] = max_open(X, k)
        mu1, mu2 = fin[:d24].mean(), fin[d24:].mean()
        for hc in (0.0, 0.35, 1.0):
            h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
            for k in (1, 2, 4):
                LO = np.ascontiguousarray(k * (np.minimum(lo, cl) - h[:, None])); CL = np.ascontiguousarray(k * (cl - h[:, None]))
                # minute matrices ordered by clock minute; NY rows are monotonic in time, ALL rows put 18:00-24:00 after RTH (same as research)
                for firm, F in FIRMS.items():
                    ep = np.array([F["T"], F["D"], F["cons"], F["mind"], F["G"], 0, 0, 1, 1, 0, 0, 0, 0, 100.0, 0], np.float64)
                    res = np.zeros(n, np.int8); end = np.zeros(n, np.int64)
                    prop_wf.race_all(LO, CL, np.zeros(n), idx, ep, res, end)
                    for per, st in (("T1", s1), ("T2", s2)):
                        st = st[st + 22 <= n]
                        single = np.mean([(res[s] == 1) and end[s] - s < 22 for s in st]); bust = np.mean([(res[s] == -1) and end[s] - s < 22 for s in st])
                        ser = np.mean([prop_wf.chain(res, end, s, 22, 3, n)[0] for s in st])
                        OUT["eval"][f"{sess} | {k}c | {firm} | edge-{int(hc*100)}% | {per}"] = dict(single22=round(100 * single, 1), bust22=round(100 * bust, 1), serial3_22=round(100 * ser, 1))
                    # funded: daily vectors (low incl. open, close) with the firm's own day
                    fl, fc = vectors(LO, CL, k * (fin - h), 0.0)
                    FL = np.ascontiguousarray(np.vstack([fl] * 3)); FC = np.ascontiguousarray(np.vstack([fc] * 3))
                    for per, st in (("T1", s1), ("T2", s2)):
                        st = st[st + 252 <= n][::5]; rows = []
                        for s in st:
                            if F["fund"] == "flex": cash, mm, stt, d = A.fu_flex(FL, FC, -1e9, -1e9, idx, s, s + 252, float(F["X"]), float(F["D"]), float(F["Q"]), float(F["cap1"]))
                            elif F["fund"] == "pro": cash, mm, stt, d = A.fu_pro(FL, FC, -1e9, -1e9, idx, s, s + 252, float(F["X"]), float(F["D"]), float(F["cap1"]), float(F["cap2"]), 0.4, 5, 3)
                            else: cash, mm, stt, d = M.fu_m(FL, FC, -1e9, -1e9, idx, s, s + 252, float(F["X"]), float(F["D"]), 0)
                            rows.append((cash, mm, stt == -1, d - s))
                        r = np.array(rows, float)
                        OUT["funded"][f"{sess} | {k}c | {firm} | edge-{int(hc*100)}% | {per}"] = dict(cash_median=round(float(np.median(r[:, 0]))), payouts_mean=round(float(r[:, 1].mean()), 1),
                            lost_pct=round(100 * float(r[:, 2].mean()), 1), lost_within_60d=round(100 * float(((r[:, 2] == 1) & (r[:, 3] < 60)).mean()), 1))
        print(sess, "done", flush=True)
    json.dump(OUT, open(os.path.join(HERE, "nyonly.json"), "w"), indent=1)
    return OUT


if __name__ == "__main__":
    run()
