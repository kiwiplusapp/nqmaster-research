"""Apex 25K Full (intraday trailing $1,500, target $1,500) eval + PA lifecycle with MaxPlus (ICT x2), realized intraday DD.
PA: safety net 26,100 (threshold stops trailing at 25,100 once peak >= 26,600), payout = min(1000, bal-26,100) >= 500,
5 days >= $100 since last payout, 50% consistency (best day < 50% of cycle profit), 6 payouts then closed. Eval $17.70/21 days, PA $90."""
import pickle, numpy as np, pandas as pd
exec(open("riskrules.py").read().split('if __name__ == "__main__":')[0])
def arrays(per):
    P, F = M["mnq_fut"] if per == "REAL" else M["nq_1m"]
    if per == "C24": F = F[F.date >= 20240101]; days = P.index[P.index >= 20240101]
    elif per == "IS": F = F[F.date < 20240101]; days = P.index[P.index < 20240101]
    else: days = P.index
    T = apply(F, w={"ICT": 2.0}); days = np.array(days)
    tot = np.zeros(len(days)); mn = np.zeros(len(days)); mx = np.zeros(len(days)); idx = {x: i for i, x in enumerate(days)}
    for x, g in T.groupby("date"):
        c = np.cumsum(g.sort_values("tout").uw.to_numpy()); i = idx[x]; tot[i] = c[-1]; mn[i] = min(0, c.min()); mx[i] = max(0, c.max())
    return tot, mn, mx
def eval_run(t, mn, mx, s, pol, T=1500, D=1500):
    eq = pk = 0.0
    for i in range(s, len(t)):
        k = pol(eq, pk)
        if eq + k * mn[i] <= pk - D: return "b", i
        pk = max(pk, eq + k * mx[i]); eq += k * t[i]
        if eq >= T: return "p", i
    return None, len(t)
def pa_run(t, mn, mx, s, pol):
    bal = 25000.0; pk = bal; cash = 0.0; n = 0; cyc0 = bal; best = 0.0; qd = 0
    for i in range(s, len(t)):
        k = pol(bal - 25000, pk - 25000)
        thr = 25100.0 if pk >= 26600 else pk - 1500
        if bal + k * mn[i] <= thr: return cash, n, "bust", i
        pk = max(pk, bal + k * mx[i]); d = k * t[i]; bal += d
        if d >= 100: qd += 1
        best = max(best, d); prof = bal - cyc0
        if qd >= 5 and bal >= 26600 and prof > 0 and best < 0.5 * prof:
            amt = min(1000.0, bal - 26100)
            if amt >= 500:
                bal -= amt; cash += amt; n += 1; cyc0 = bal; best = 0.0; qd = 0
                if n == 6: return cash, n, "done", i
    return cash, n, "open", len(t)
POLS = {"fijo 1": lambda e, p: 1, "adapt 2->1 DD>$400": lambda e, p: 2 if p - e < 400 else 1, "adapt 2->1 DD>$600": lambda e, p: 2 if p - e < 600 else 1, "fijo 2": lambda e, p: 2}
if __name__ == "__main__":
    for per in ("REAL", "C24"):
        t, mn, mx = arrays(per); n = len(t)
        print(f"\n===== {per} ({n} days)")
        for en, ep in POLS.items():
            r30 = [eval_run(t, mn, mx, s, ep) for s in range(n - 22)]
            p30 = np.mean([r[0] == "p" and r[1] - s < 22 for s, r in enumerate(r30)]); b30 = np.mean([r[0] == "b" and r[1] - s < 22 for s, r in enumerate(r30)])
            pinf = np.mean([r[0] == "p" for r in r30]); binf = np.mean([r[0] == "b" for r in r30]); med = np.median([r[1] - s + 1 for s, r in enumerate(r30) if r[0] == "p"])
            print(f"EVAL {en:20s}: 30d pass {100*p30:3.0f}% bust {100*b30:3.0f}% | no limit pass {100*pinf:3.0f}% bust {100*binf:3.0f}% | median days to pass {med:.0f}")
        for en, ep in (("adapt 2->1 DD>$400", POLS["adapt 2->1 DD>$400"]),):
            for pn, pp in (("fijo 1", POLS["fijo 1"]), ("adapt 2->1 DD>$400", POLS["adapt 2->1 DD>$400"]), ("fijo 2", POLS["fijo 2"])):
                res = []
                for s in range(0, n - 252, 5):                      # 12-month lifecycle per account, repeat evals until pass
                    i = s; cash = 0.0; fees = 0.0; payouts = 0; evals = 0; pas = 0; pabust = 0
                    while i < s + 252:
                        evals += 1; r, j = eval_run(t, mn, mx, i, ep); fees += 17.70 * max(1, (min(j, s + 252) - i + 1) / 21)
                        if r != "p": i = j + 1; continue
                        fees += 90; pas += 1; c, k, st, j2 = pa_run(t[:s + 252], mn[:s + 252], mx[:s + 252], j + 1, pp); cash += c; payouts += k
                        if st == "bust": pabust += 1
                        i = j2 + 1
                    res.append((cash - fees, cash, fees, payouts, evals, pas, pabust))
                a = np.array(res)
                print(f"12 months, eval {en} -> PA {pn:20s}: net/month ${a[:,0].mean()/12:5.0f} (median ${np.median(a[:,0])/12:5.0f}, worst ${a[:,0].min()/12:5.0f}) | payouts/yr {a[:,3].mean():.1f} | evals bought {a[:,4].mean():.1f} | PAs {a[:,5].mean():.1f} busted {a[:,6].mean():.1f} | P(year<0) {100*(a[:,0]<0).mean():.0f}%")
