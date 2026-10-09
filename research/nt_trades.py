import numpy as np, pandas as pd
def load_nt(path):
    t = pd.read_csv(path, sep=";", dtype=str).dropna(subset=["Trade number"])
    # numbers: '1.234,56 $' or '-$1234,56' (both exports seen); times: 24 h or 12 h with 'a m' / 'p m' (Spanish Windows locale)
    num = lambda s: s.str.replace("$", "", regex=False).str.strip().str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
    t["pnl"] = num(t["Profit"]); t["qty"] = t["Qty"].astype(int)
    def tm(s):
        s = s.str.replace("a m", "AM", regex=False).str.replace("p m", "PM", regex=False).str.replace("a. m.", "AM", regex=False).str.replace("p. m.", "PM", regex=False)
        return pd.to_datetime(s, format="%d/%m/%Y %I:%M:%S %p") if s.str.contains("M$", regex=True).all() else pd.to_datetime(s, format="%d/%m/%Y %H:%M:%S")
    t["tin"] = tm(t["Entry time"]); t["tout"] = tm(t["Exit time"])
    t["mod"] = t["Entry name"]; t["y"] = t.tin.dt.year
    return t
if __name__ == "__main__":
    t = load_nt(r"C:\Users\XINTETICO\Downloads\backtesting\trades of maxplus 2020-2026 1 contract confluence rule on.csv")
    pf = lambda u: round(u[u > 0].sum() / -u[u <= 0].sum(), 2) if (u <= 0).any() else np.nan
    print("total", round(t.pnl.sum()), "trades", len(t))
    g = t.groupby("mod").agg(n=("pnl", "size"), wr=("pnl", lambda u: round(100 * (u > 0).mean(), 1)), pf=("pnl", pf), net=("pnl", "sum"), qty2=("qty", lambda q: int((q >= 2).sum())))
    g["per_yr"] = (g.net / 6.74).round(0); print(g.sort_values("net", ascending=False).round(0).to_string())
    print("\nby year:"); print(t.groupby("y").pnl.agg(n="size", wr=lambda u: round(100 * (u > 0).mean(), 1), pf=pf, net="sum").round(0).to_string())
    # confluence (qty 2 on late modules) performance
    L = t[t["mod"].isin(["CRT11", "MOM13", "MSEQ", "MSEQS"])]
    for q in (1, 2):
        x = L[L.qty == q]; print(f"late modules qty {q}: n {len(x)}, PF {pf(x.pnl)}, net {x.pnl.sum():.0f}, per-contract net {x.pnl.sum()/q:.0f}")
    t.to_pickle("nt_trades_on.pkl")
