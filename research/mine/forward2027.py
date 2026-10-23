"""2026-10-19 'que en 2026-2027 funcione': what to expect, month by month, from the 2027 default (Ultra + durable four + GoldMaster Robust)
per BASE contract, and the tripwires that say the edge is gone. Daily $ per contract on real NQ (2020-10..2026-10) + gold, block bootstrap
(21-day blocks) of 2,000 forward 12-month paths drawn from 2024-26 (the most recent regime) and from 2020-26 (all), at full edge,
-35% and zero edge (mean removed). Output: quantiles of the month, the quarter and the year; P(losing month); P(2+ / 3+ losing months
in a row within the year); drawdown quantiles; and tripwire levels = values that a full-edge system breaches with <= 5% probability. -> forward2027.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
NEW = {"SO04": ("CLOCK_ANCHOR", 1527), "RV11": ("RVOL_DRIVE", 4226), "ORFAIL": ("OR_FAIL", 142), "CAM3": ("PIVOT_FADE", 365)}
GOLD = ["OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206"]

if __name__ == "__main__":
    U = pickle.load(open(os.path.join(HERE, "six_ultra6_trades.pkl"), "rb"))["Ultra6"]
    U = U[~U["mod"].isin(["CA04V", "GD03", "ENG26", "LATEFH"])]
    from wrq_port import conflict_filter
    U = conflict_filter(U.sort_values(["date", "tin"]).reset_index(drop=True))
    days = np.array(sorted(U.date.unique()))
    d = (U.u * U.w).groupby(U.date).sum()
    G = pickle.load(open(os.path.join(HERE, "gold_curated_trades.pkl"), "rb")); gp = []
    for m in GOLD:
        a = G[m]["IS"]; gp.append(a[a.date < 20240216]); b = G[m]["REAL"]; gp.append(b[b.date >= 20240216])
    g = pd.concat(gp); g = (g.u * g.w).groupby(g.date).sum()
    alld = np.union1d(days, g.index.to_numpy()); alld = alld[alld >= 20201015]
    x = d.reindex(alld, fill_value=0.0) + g.reindex(alld, fill_value=0.0)
    rng = np.random.default_rng(2027); OUT = {}
    for src, lo in (("2024-26", 20240101), ("2020-26", 20201015)):
        v = x[x.index >= lo].to_numpy(); mu = v.mean()
        for hc in (0.0, 0.35, 1.0):
            w = v - hc * mu; P = []
            for b in range(2000):
                s = rng.integers(0, len(w) - 21, 13); P.append(np.concatenate([w[a:a + 21] for a in s])[:252])
            P = np.array(P); mo = P[:, :252].reshape(2000, 12, 21).sum(2); qt = mo.reshape(2000, 4, 3).sum(2); yr = P.sum(1)
            eq = np.cumsum(P, 1); dd = (np.maximum.accumulate(eq, 1) - eq).max(1)
            neg = mo < 0; run2 = np.array([max((np.convolve(r, np.ones(2), "valid") == 2).any(), False) for r in neg]); run3 = np.array([(np.convolve(r, np.ones(3), "valid") == 3).any() for r in neg])
            q = lambda a: {p: round(float(np.percentile(a, p))) for p in (5, 10, 25, 50, 75, 90)}
            OUT[f"{src} | edge-{int(hc*100)}%"] = dict(mean_day=round(float(w.mean()), 1), month=q(mo), quarter=q(qt), year=q(yr), maxdd_year=q(dd),
                P_losing_month=round(100 * float(neg.mean()), 1), P_2_losing_in_row=round(100 * float(run2.mean()), 1), P_3_losing_in_row=round(100 * float(run3.mean()), 1),
                P_losing_quarter=round(100 * float((qt < 0).mean()), 1), P_losing_year=round(100 * float((yr < 0).mean()), 1))
            r = OUT[f"{src} | edge-{int(hc*100)}%"]
            print(f"{src} edge-{int(hc*100):3d}%  month p10/p50/p90 {r['month'][10]}/{r['month'][50]}/{r['month'][90]}  quarter p5/p50 {r['quarter'][5]}/{r['quarter'][50]}  year p10/p50 {r['year'][10]}/{r['year'][50]}  DD p50/p90 {r['maxdd_year'][50]}/{r['maxdd_year'][90]}  P(month<0) {r['P_losing_month']}  P(2 in row) {r['P_2_losing_in_row']}  P(3 in row) {r['P_3_losing_in_row']}  P(q<0) {r['P_losing_quarter']}  P(yr<0) {r['P_losing_year']}", flush=True)
    full = OUT["2020-26 | edge-0%"]
    OUT["tripwires_per_contract"] = dict(quarter_below=full["quarter"][5], year_drawdown_above=full["maxdd_year"][90], three_losing_months_in_row_prob_full_edge=full["P_3_losing_in_row"])
    json.dump(OUT, open(os.path.join(HERE, "forward2027.json"), "w"), indent=1)
