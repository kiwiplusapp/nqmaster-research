"""2026-10-16 six-year round, step 4: existing modules under the six-year frame (T1 2020-10-15..2023 choose, T2 2024.. check).
(a) leave-one-out of every Ultra module; (b) re-enable ENG10 / LATEFH (cand16 'Ultra' trades); (c) module weight x0 / x1 / x2 chosen on T1 only
(coordinate ascent on T1 Sharpe, integer weights 0-3, MOM1030/CPI09 kept as base x4 scale), then reported on T2. -> six_modules.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import six_lib as S


def mod_daily(T):
    idx = S.days(); out = {}
    for m, g in T.groupby("mod"):
        out[m] = (g.w * g.u).groupby(g.date).sum().reindex(idx, fill_value=0.0)
    return pd.DataFrame(out).fillna(0.0)


def sr(x):
    return float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else 0.0


if __name__ == "__main__":
    U = S.base(); M = mod_daily(U); idx = M.index; t1 = idx < S.MID; t2 = ~t1
    tot = M.sum(1); OUT = {"base": S.metr(tot)}
    print("base", OUT["base"]["T1"]["sharpe"], OUT["base"]["T2"]["sharpe"])
    loo = {}
    for m in M.columns:
        x = tot - M[m]; r = S.metr(x)
        loo[m] = dict(dSR_T1=round(r["T1"]["sharpe"] - OUT["base"]["T1"]["sharpe"], 3), dSR_T2=round(r["T2"]["sharpe"] - OUT["base"]["T2"]["sharpe"], 3),
                      dNet=r["all"]["net"] - OUT["base"]["all"]["net"], dDD=r["all"]["maxdd"] - OUT["base"]["all"]["maxdd"])
    OUT["leave_one_out"] = loo
    print("LOO (positive = removing helps):"); [print(f"  {m:8s} {v}") for m, v in sorted(loo.items(), key=lambda kv: -kv[1]['dSR_T1'])]
    # re-enable ENG10 / LATEFH
    X = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["Ultra"][0]
    for m in ("ENG10", "LATEFH"):
        g = X[(X["mod"] == m) & (X.date >= S.START)]; cd = (g.w * g.u).groupby(g.date).sum()
        a = S.add_test(cd); ts = S.tstats((g.w * g.u).to_numpy(), g.date.to_numpy())
        OUT[f"add_{m}"] = dict(stats=ts, dSR_T1=round(a["comb"]["T1"]["sharpe"] - a["base"]["T1"]["sharpe"], 3), dSR_T2=round(a["comb"]["T2"]["sharpe"] - a["base"]["T2"]["sharpe"], 3), corr=a["corr"])
        print("add", m, OUT[f"add_{m}"])
    # weights chosen on T1
    w = {m: 1 for m in M.columns}
    for it in range(4):
        ch = False
        for m in M.columns:
            best = (sr((M * pd.Series(w)).sum(1)[t1]), w[m])
            for k in (0, 1, 2, 3):
                ww = dict(w); ww[m] = k; s = sr((M * pd.Series(ww)).sum(1)[t1])
                if s > best[0] + 1e-9: best = (s, k)
            if best[1] != w[m]: w[m] = best[1]; ch = True
        if not ch: break
    x = (M * pd.Series(w)).sum(1); r = S.metr(x)
    OUT["weights_T1"] = dict(w=w, metr=r)
    print("T1-chosen weights", {m: k for m, k in w.items() if k != 1}, "SR T1", r["T1"]["sharpe"], "T2", r["T2"]["sharpe"], "DD", r["all"]["maxdd"], "net", r["all"]["net"])
    # same with weights capped to {0,1} (pure on/off)
    w01 = {m: 1 for m in M.columns}
    for it in range(4):
        ch = False
        for m in M.columns:
            ww = dict(w01); ww[m] = 1 - w01[m]
            if sr((M * pd.Series(ww)).sum(1)[t1]) > sr((M * pd.Series(w01)).sum(1)[t1]) + 1e-9: w01 = ww; ch = True
        if not ch: break
    x = (M * pd.Series(w01)).sum(1); r = S.metr(x)
    OUT["onoff_T1"] = dict(off=[m for m, k in w01.items() if k == 0], metr=r)
    print("T1-chosen on/off: off", OUT["onoff_T1"]["off"], "SR T1", r["T1"]["sharpe"], "T2", r["T2"]["sharpe"], "net", r["all"]["net"])
    json.dump(OUT, open(os.path.join(HERE, "six_modules.json"), "w"), indent=1)
