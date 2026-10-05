"""Does the outcome of today's EARLIER trades predict the next trade? For each trade, look only at trades of the same day that
already EXITED before its entry minute: same-direction wins/losses (sw, sl) and opposite-direction wins/losses (ow, ol).
PF by state per period; rule candidates are chosen on IS only."""
import pickle, numpy as np, pandas as pd
T = pickle.load(open("robust_trades.pkl", "rb"))
def pf(x): return round(float(x[x > 0].sum() / -x[x <= 0].sum()), 3) if (x <= 0).any() and (x > 0).any() else np.nan
def state(F):
    F = F.sort_values(["date", "tin"]).reset_index(drop=True); n = len(F)
    sw = np.zeros(n, int); sl = np.zeros(n, int); ow = np.zeros(n, int); ol = np.zeros(n, int); last = np.zeros(n, int); lastsame = np.zeros(n, int)
    for date, g in F.groupby("date", sort=False):
        idx = g.index.to_numpy(); tin = g.tin.to_numpy(); tout = g.tout.to_numpy(); d = g.d.to_numpy(); u = g.u.to_numpy()
        for a, i in enumerate(idx):
            done = [b for b in range(len(idx)) if tout[b] <= tin[a] and b != a]
            for b in done:
                same = d[b] == d[a]; win = u[b] > 0
                if same and win: sw[i] += 1
                elif same: sl[i] += 1
                elif win: ow[i] += 1
                else: ol[i] += 1
            if done:
                b = max(done, key=lambda z: tout[z]); last[i] = (1 if u[b] > 0 else -1) * (1 if d[b] == d[a] else -1) * 1  # +1 same-win/opp-loss ... encoded below
                lastsame[i] = (2 if d[b] == d[a] else 0) + (1 if u[b] > 0 else 0)          # 3 same win, 2 same loss, 1 opp win, 0 opp loss
            else: lastsame[i] = -1
    F["sw"], F["sl"], F["ow"], F["ol"], F["lastst"] = sw, sl, ow, ol, lastsame
    return F
LAB = {-1: "primer trade del día", 3: "último: misma dir. ganó", 2: "último: misma dir. perdió", 1: "último: dir. opuesta ganó", 0: "último: dir. opuesta perdió"}
pd.set_option("display.width", 250)
for prof in ("Ultra", "WR70Plus"):
    rows = []
    for per in ("IS", "C24", "REAL"):
        F = state(T[prof][per][0]); F["x"] = F.u * F.w
        for k, lab in LAB.items():
            x = F.x[F.lastst == k]; rows.append(dict(per=per, estado=lab, n=len(x), pf=pf(x), wr=round(100 * (F.u[F.lastst == k] > 0).mean(), 1)))
        for nm, m in (("algún stop en misma dir. hoy", F.sl > 0), ("ningún stop en misma dir.", F.sl == 0), ("misma dir. ganó antes (y sin stops)", (F.sw > 0) & (F.sl == 0)),
                      ("2+ stops hoy (cualquier dir.)", (F.sl + F.ol) >= 2), ("opuesta perdió y misma no", (F.ol > 0) & (F.sl == 0))):
            x = F.x[m]; rows.append(dict(per=per, estado=nm, n=len(x), pf=pf(x), wr=round(100 * (F.u[m] > 0).mean(), 1)))
    R = pd.DataFrame(rows)
    print("\n=====", prof); print(R.pivot_table(index="estado", columns="per", values=["n", "pf", "wr"], aggfunc="first")[[("n", "IS"), ("pf", "IS"), ("pf", "C24"), ("pf", "REAL"), ("wr", "IS"), ("wr", "REAL"), ("n", "REAL")]].to_string())
    pickle.dump({per: state(T[prof][per][0]) for per in ("IS", "C24", "REAL")}, open(f"seqstate_{prof}.pkl", "wb"))
