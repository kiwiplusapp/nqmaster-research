"""Swap test: the noise-area momentum (Q_NOISE, Zarattini et al. 2024) overlaps VOLB (daily corr 0.55). Replace VOLB in Ultra by a NOISE
config chosen on IS only (max IS daily Sharpe of Ultra-minus-VOLB plus NOISE_j), report C24 / REAL. Writes q_swap.json."""
import os, sys, json, pickle, ast, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def sh(x): return float(x.mean() / x.std() * 252 ** .5)
if __name__ == "__main__":
    T = pickle.load(open("robust_trades.pkl", "rb")); Z = np.load("q_daily_Q_NOISE.npz"); R = pd.read_csv("q_results_Q_NOISE.csv")
    PER = {"IS": ("cfd", 20200201, 20240101), "C24": ("cfd", 20240101, 10 ** 9), "REAL": ("real", 20240201, 10 ** 9)}
    base = {}; novb = {}; X = {}
    for per, (src, a, b) in PER.items():
        F, days = T["Ultra"][per]; base[per] = (F.u * F.w).groupby(F.date).sum().reindex(days, fill_value=0.0)
        G = F[F["mod"] != "VOLB"]; novb[per] = (G.u * G.w).groupby(G.date).sum().reindex(days, fill_value=0.0)
        M = pd.DataFrame(Z[src].T.astype(float), index=Z[src + "_days"]); X[per] = M.reindex(days, fill_value=0.0).to_numpy()
    sc = {per: np.array([sh(novb[per].to_numpy() + X[per][:, j]) for j in range(X[per].shape[1])]) for per in PER}
    j = int(np.argmax(sc["IS"])); J = {"chosen_on_IS": R.params[j]}
    for per in PER:
        J[per] = dict(ultra=round(sh(base[per].to_numpy()), 3), ultra_minus_volb=round(sh(novb[per].to_numpy()), 3), swap=round(float(sc[per][j]), 3),
                      ultra_mo=round(float(base[per].mean() * 21)), swap_mo=round(float((novb[per].to_numpy() + X[per][:, j]).mean() * 21)),
                      share_of_noise_cfgs_beating_ultra=round(float((sc[per] > sh(base[per].to_numpy())).mean()), 3))
    json.dump(J, open("q_swap.json", "w"), indent=1); print(json.dumps(J, indent=1))
