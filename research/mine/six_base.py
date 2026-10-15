"""2026-10-16 'backtest de los últimos 6 años' (Federico): current profiles on real Databento NQ, 2020-10-15 .. last data (2026-10-08),
$ per MNQ at 1 base contract, $1.90 commission + 1 tick per side (already in u), stress +4 ticks per side (extra $3 per contract round trip).
Ultra = UltraR (cand16, after the 10-12 overhaul) + CPI09, MOM1030 and CPI09 at x4 (current defaults). UltraQ / WR70R as built.
Split for later selection: T1 = 2020-10-15..2023-12-31 (choose), T2 = 2024-01-01..end (check). -> six_base.json, six_trades.pkl"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
START, MID = 20201015, 20240101


def profiles():
    X = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb")); Q = pickle.load(open(os.path.join(HERE, "ultraq_trades.pkl"), "rb"))["UltraQ"][0]
    cpi = Q[Q["mod"] == "CPI09"][["date", "mod", "tin", "tout", "d", "u", "w"]].copy()
    P = {}
    u = X["UltraR"][0][["date", "mod", "tin", "tout", "d", "u", "w"]].copy()
    u = pd.concat([u, cpi], ignore_index=True); u.loc[u["mod"].isin(["MOM1030", "CPI09"]), "w"] = 4.0
    P["Ultra"] = u
    q = Q[["date", "mod", "tin", "tout", "d", "u", "w"]].copy(); q.loc[q["mod"].isin(["MOM1030", "CPI09"]), "w"] = 4.0; P["UltraQ"] = q
    w = X["WR70R"][0][["date", "mod", "tin", "tout", "d", "u", "w"]].copy(); w = pd.concat([w, cpi], ignore_index=True)
    w.loc[w["mod"] == "CPI09", "w"] = 4.0; P["WR70Plus"] = w
    for k in P: P[k] = P[k][P[k].date >= START].sort_values(["date", "tin"]).reset_index(drop=True)
    return P


def stats(T, extra=0.0):
    pnl = T.w * (T.u - extra); win = T.u > 0
    d = pnl.groupby(T.date).sum()
    days = pd.to_datetime(d.index.astype(str)); m = d.groupby(days.to_period("M")).sum()
    eq = d.cumsum(); dd = float((eq.cummax() - eq).max())
    span_m = max(1.0, (days.max() - days.min()).days / 30.44)
    gp, gl = pnl[pnl > 0].sum(), -pnl[pnl <= 0].sum()
    return dict(trades=int(len(T)), per_day=round(len(T) / max(1, len(d)) , 2), wr=round(100 * float(win.mean()), 1), pf=round(float(gp / gl), 3),
                net=round(float(pnl.sum())), per_month=round(float(pnl.sum() / span_m)), maxdd=round(dd), worst_month=round(float(m.min())),
                pos_months=f"{int((m > 0).sum())}/{len(m)}", sharpe=round(float(d.mean() / d.std() * np.sqrt(252)), 2))


if __name__ == "__main__":
    P = profiles(); OUT = {}
    for nm, T in P.items():
        r = dict(all=stats(T), T1=stats(T[T.date < MID]), T2=stats(T[T.date >= MID]), all_plus4ticks=stats(T, 3.0))
        r["years"] = {int(y): stats(g) for y, g in T.groupby(T.date // 10000)}
        r["modules"] = {m: dict(T1=stats(g[g.date < MID]) if (g.date < MID).sum() >= 5 else None, T2=stats(g[g.date >= MID]) if (g.date >= MID).sum() >= 5 else None)
                        for m, g in T.groupby("mod")}
        OUT[nm] = r
        a = r["all"]; print(f"{nm:9s} 6y: {a['trades']} tr {a['per_day']}/day WR {a['wr']} PF {a['pf']} ${a['net']:,} (${a['per_month']:,}/mo) DD ${a['maxdd']:,} worst mo ${a['worst_month']:,} {a['pos_months']} SR {a['sharpe']} | +4t PF {r['all_plus4ticks']['pf']}")
        print("   years:", {y: (v['pf'], v['net']) for y, v in r["years"].items()})
    json.dump(OUT, open(os.path.join(HERE, "six_base.json"), "w"), indent=1)
    pickle.dump(P, open(os.path.join(HERE, "six_trades.pkl"), "wb"))
