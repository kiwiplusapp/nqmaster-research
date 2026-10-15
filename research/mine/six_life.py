"""2026-10-16 six-year round, step 6: account check of the new portfolio vs current Ultra on real NQ 2020-10..2026 minute paths.
MFFU Rapid EOD 50K, 1 base contract, current Mffu50K preset (eval: MOM1030/CPI09 x8 + daily profit stop $800; funded: x4, $300 risk cap
below a $2,000 cushion, keep $4,100), new modules at 1 contract in every gear (risk cap applies to them too), opposite-position conflicts removed (wrq_port.conflict_filter). Edge: full and 35% haircut
(haircut = 35% of each portfolio's own mean daily P&L). Metrics per 12-month seat (starts every 5 days): $/month, accounts lost per
year, P(negative year); eval single pass <= 20 list days, bust %, serial funded <= 20 days. T1 starts 2020-10..2023-10, T2 2024-01..
Usage: python3 six_life.py (reads six_final_set.json: list of {fam, j} or {'existing': 'LATEFH'}). -> six_life.json"""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from wrq_lib import getD
from mffu_rapid import life_m
from month80 import outcomes, serial_first
from sniper_life import build
import core_e
H = 252


def new_trades(D, spec):
    from run_mine_db import FAMILIES
    rows = []
    R = pd.concat([pd.read_csv(os.path.join(HERE, f)) for f in ("results_db_old.csv", "results_db_new.csv")] +
                  ([pd.read_csv(os.path.join(HERE, "results_b7.csv"))] if os.path.exists(os.path.join(HERE, "results_b7.csv")) else []), ignore_index=True)
    X = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["Ultra"][0]
    for s in spec:
        if "existing" in s:
            g = X[X["mod"] == s["existing"]].copy(); g = RB.attach(g, RB.setup()); g["risk"] = g["risk"]
            rows.append(g[["date", "mod", "d", "u", "w", "fi", "xi", "e", "risk"]]); continue
        p = s.get("params") or ast.literal_eval(R[(R.fam == s["fam"]) & (R.j == s["j"])].params.iloc[0])
        gen, grid, mx = FAMILIES[s["fam"]]; t = core_e.run_events_e(D, gen(D, p), flat=955, maxday=mx, slip=0.25)
        t = t.assign(mod=f"{s['fam']}#{s.get('j', '')}", u=t.usd, w=1.0, risk=t.risk * D.pv)
        rows.append(t[["date", "mod", "d", "u", "w", "fi", "xi", "e", "risk"]])
    return pd.concat(rows, ignore_index=True)


if __name__ == "__main__":
    spec = json.load(open(os.path.join(HERE, "six_final_set.json")))
    E = RB.setup(); D = getD(RB.NAME)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]; days = days[days >= 20201015]; n = len(days); idx = np.arange(n, dtype=np.int64)
    T = build(E, D); T = T[T.date.isin(days)]; S8 = T["mod"].isin(["MOM1030", "CPI09"])
    NW = new_trades(D, spec); NW = NW[NW.date.isin(days)]
    NW = NW.assign(tin=D.sm[NW.fi.to_numpy().astype(int)], tout=D.sm[NW.xi.to_numpy().astype(int)] + 1)
    from wrq_port import conflict_filter                 # NinjaTrader skips an entry opposite to an open position
    print("new trades", len(NW), NW["mod"].value_counts().to_dict(), flush=True)
    d24 = int(np.searchsorted(days, 20240101))
    s1 = np.nonzero(days < 20231101)[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 40]
    OUT = {}
    for label, extra in (("Ultra (today)", None), ("Ultra + new", NW)):
        P = {}
        A0 = conflict_filter((T if extra is None else pd.concat([T, extra], ignore_index=True)).sort_values(["date", "tin"]).reset_index(drop=True))
        for cap in (0, 300):
            R0 = A0[~A0["mod"].isin(["MOM1030", "CPI09"])]; S1 = A0[A0["mod"].isin(["MOM1030", "CPI09"])].assign(w=1.0)
            if cap: R0 = R0[R0.risk <= cap]
            P[cap] = (full_paths(R0, days), full_paths(S1, days), R0.w.groupby(R0.date).sum().reindex(days, fill_value=0).to_numpy(), S1.w.groupby(S1.date).sum().reindex(days, fill_value=0).to_numpy())
        fin = P[0][0][2] + 4 * P[0][1][2]; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())
        def vecm(cap, m, G, h):
            a, b, ca, cb = P[cap]
            return vectors(a[0] + m * b[0] - h[:, None], a[1] + m * b[1] - h[:, None], a[2] + m * b[2] - h, G)
        for hc in (0.0, 0.35):
            h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
            ev = vecm(0, 8, 800.0, h); EL = np.ascontiguousarray(np.array([ev[0], ev[0]])); EC = np.ascontiguousarray(np.array([ev[1], ev[1]]))
            full = vecm(0, 4, 0.0, h); low = vecm(300, 4, 0.0, h)
            FL = np.ascontiguousarray(np.array([low[0], full[0], full[0]])); FC = np.ascontiguousarray(np.array([low[1], full[1], full[1]]))
            out = np.zeros((n, 9)); k = life_m(EL, EC, -1e9, 3000.0, 2000.0, 0.3, 4, 157.0, FL, FC, 2000.0, 1e9, 4100.0, 0, idx, H, 5, out)
            o = out[:k]; st = np.arange(k) * 5
            res, ddd = outcomes(ev[0], ev[1], 3000, 2000, 0.3, 4, n)
            rec = {}
            for tag, ok, ss in (("T1", (st + H) < d24, s1), ("T2", st >= d24, s2)):
                x = o[ok]
                se = [serial_first(res, ddd, s, 20) for s in ss]
                rec[tag] = dict(usd_month=round(float(x[:, 0].mean() / 12)), p10_month=round(float(np.percentile(x[:, 0], 10) / 12)),
                                lost_per_year=round(float((x[:, 1] - x[:, 2] + x[:, 3]).mean()), 2), neg_year_pct=round(100 * float((x[:, 0] < 0).mean()), 1),
                                eval_pass20=round(100 * float(np.mean([(res[s] == 1) and ddd[s] < 20 for s in ss])), 1), eval_bust=round(100 * float(np.mean([res[s] == -1 for s in ss])), 1),
                                serial20=round(100 * float(np.mean([a for a, _ in se])), 1))
            OUT[f"{label} | edge-{int(hc*100)}%"] = rec
            print(label, f"edge-{int(hc*100)}%", rec, flush=True)
    json.dump(OUT, open(os.path.join(HERE, "six_life.json"), "w"), indent=1)
