"""2026-10-16 six-year round, step 5: combine the re-selected mined candidates (six_reselect.json accepted, minus the 08:20 G_ORB
breakout rejected by the 2025-26 tick backtest, minus near-duplicates of portfolio modules) + LATEFH re-enabled. Forward selection on
T1 Sharpe only (add a candidate while T1 Sharpe rises by >= 0.01), then report T2, +4 ticks and duplicates (max |corr| with any Ultra module).
-> six_combo.json"""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import six_lib as S
from six_modules import mod_daily


def sr(x): return float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else 0.0


if __name__ == "__main__":
    O = json.load(open(os.path.join(HERE, "six_reselect.json")))
    C = pd.DataFrame(O["candidates"]); C = C[C.accepted & ~C.params.str.contains("'A': 820")]
    TR = {}
    for f in ("trades_db_old.pkl", "trades_db_new.pkl", "trades_nga.pkl"): TR.update(pickle.load(open(os.path.join(HERE, f), "rb")))
    U = S.base(); M = mod_daily(U); idx = M.index
    X = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["Ultra"][0]
    g = X[(X["mod"] == "LATEFH") & (X.date >= S.START)]
    cands = {"LATEFH(existing code)": ((g.w * g.u).groupby(g.date).sum().reindex(idx, fill_value=0.0), (g.w * g.u).to_numpy(), g.date.to_numpy())}
    seen = set()
    for r in C.itertuples():
        t = TR[(r.fam, r.j)]["real"]; t = t[t.date >= S.START]
        key = (r.fam, round(r.T1["pf"], 2), round(r.T2["pf"], 2))
        if key in seen: continue                                        # identical trade sets (hold 240 vs 600 etc.)
        seen.add(key)
        cands[f"{r.fam}#{r.j}"] = (t.usd.groupby(t.date).sum().reindex(idx, fill_value=0.0), t.usd.to_numpy(), t.date.to_numpy())
    info = {}
    for k, (d, u, dt) in cands.items():
        cm = {m: float(np.corrcoef(d, M[m])[0, 1]) for m in M.columns if M[m].std() > 0}
        mx = max(cm.items(), key=lambda kv: abs(kv[1]))
        info[k] = dict(maxcorr_module=mx[0], maxcorr=round(mx[1], 3), stats=S.tstats(u, dt), plus4=S.tstats(u - 3.0, dt))
    dup = [k for k, v in info.items() if abs(v["maxcorr"]) >= 0.4]
    print("duplicates (|corr| >= 0.4 with a module):", {k: (info[k]['maxcorr_module'], info[k]['maxcorr']) for k in dup})
    pool = [k for k in cands if k not in dup]
    tot = M.sum(axis=1); t1 = idx < S.MID; chosen = []
    while True:
        best = (sr(tot[t1]) + 0.01, None)
        for k in pool:
            if k in chosen: continue
            s = sr((tot + cands[k][0])[t1])
            if s > best[0]: best = (s, k)
        if best[1] is None: break
        chosen.append(best[1]); tot = tot + cands[best[1]][0]
        print("add", best[1], "T1 SR", round(best[0], 3), flush=True)
    b = S.metr(M.sum(axis=1)); c = S.metr(tot)
    extra = sum(len(cands[k][1]) for k in chosen)
    # +4 ticks on the whole combined portfolio
    U4 = S.metr(S.daily(U, extra=3.0) + sum(cands[k][0] - 3.0 * pd.Series(cands[k][2]).value_counts().reindex(idx, fill_value=0).values for k in chosen) if chosen else S.daily(U, extra=3.0))
    OUT = dict(chosen=chosen, info=info, duplicates=dup, base=b, combined=c, combined_plus4=U4, base_plus4=S.metr(S.daily(U, extra=3.0)), extra_trades=extra)
    print("base    ", {p: (b[p]['sharpe'], b[p]['net'], b[p]['maxdd'], b[p]['worst_month']) for p in b})
    print("combined", {p: (c[p]['sharpe'], c[p]['net'], c[p]['maxdd'], c[p]['worst_month']) for p in c})
    print("+4 ticks base", OUT["base_plus4"]["T2"]["sharpe"], "combined", U4["T2"]["sharpe"])
    for k in chosen: print(k, info[k])
    json.dump(OUT, open(os.path.join(HERE, "six_combo.json"), "w"), indent=1, default=str)
