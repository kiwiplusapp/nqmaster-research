"""2026-10-15 'detect the best trades and add contracts': size up single high-PF modules of Ultra (+CPI09) and check Sharpe / PF /
$ / max drawdown on 4 periods (A 2010-14, B 2015-19 cost-normalised; T1 2020-23, T2 2024-26 real $ per MNQ). A change is accepted only
if Sharpe goes up in all four periods. -> size_q.json"""
import json, pickle, itertools, numpy as np, pandas as pd
PER = (("A", 20100601, 20150101, 1), ("B", 20150101, 20200101, 1), ("T1", 20200101, 20240101, 0), ("T2", 20240101, 20991231, 0))
pf = lambda x: float(x[x > 0].sum() / -x[x <= 0].sum())


def ev(X, W, lo, hi):
    s = X[(X.date >= lo) & (X.date < hi)].reset_index(drop=True); x = s.u * s.w * s["mod"].map(lambda m: W.get(m, 1.0))
    d = x.groupby(s.date).sum(); eq = d.cumsum()
    return dict(pf=round(pf(x), 3), sh=round(float(d.mean() / d.std() * np.sqrt(252)), 3), net=round(float(x.sum())), dd=round(float((eq.cummax() - eq).max())))


if __name__ == "__main__":
    C = pickle.load(open("cand16_trades.pkl", "rb")); Q = pickle.load(open("ultraq_trades.pkl", "rb"))["UltraQ"]
    R, N = C["UltraR"]; R = pd.concat([R, Q[0][Q[0]["mod"] == "CPI09"]], ignore_index=True); N = pd.concat([N, Q[1][Q[1]["mod"] == "CPI09"]], ignore_index=True)
    base = {p: ev(N if n else R, {}, lo, hi) for p, lo, hi, n in PER}
    out = {"base": base}; rows = []
    for m, k in itertools.product(["CRT11", "NF05", "MSEQS", "ORB60", "ORB90", "VOLB", "CPI09", "MSEQ", "LF06", "MOM1030"], [2, 3]):
        r = {p: ev(N if n else R, {m: k}, lo, hi) for p, lo, hi, n in PER}; out[f"{m} x{k}"] = r
        rows.append(dict(change=f"{m} x{k}", **{f"d{p}_sh": round(r[p]["sh"] - base[p]["sh"], 3) for p in r}, **{f"{p}_pf": r[p]["pf"] for p in r},
                         T2_net=r["T2"]["net"], T2_dd=r["T2"]["dd"], all_up=all(r[p]["sh"] > base[p]["sh"] for p in r)))
    T = pd.DataFrame(rows).sort_values("dT2_sh", ascending=False); pd.set_option("display.width", 250)
    print("base", base); print(T.to_string(index=False))
    json.dump(out, open("size_q.json", "w"), indent=1)
