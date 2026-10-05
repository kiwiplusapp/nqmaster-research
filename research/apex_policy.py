import numpy as np, pandas as pd
exec(open("conflict.py").read().split("for tag, lo, split")[0])
TOP = {"ORB60", "CRT11", "MOM11", "LON", "MSEQ"}
def daily_arrays(tag, lo, weights=None):
    V = pd.read_pickle(f"variants_{tag}.pkl"); V = V[(V.date >= lo) & ~V.fomc]
    prof = {k: v for k, v in PROFILES["MAX_SHARPE"].items() if k != "GOLD"}
    F = conflict_filter(pick(V, prof).reset_index(drop=True))
    w = F["mod"].map(weights).fillna(1.0) if weights else 1.0
    F = F.assign(u=w * F.usd - 0.9 * (w if weights else 1.0))
    days = np.array(sorted(pd.read_pickle(f"variants_{tag}.pkl").query(f"date>={lo}").date.unique()))
    tot = np.zeros(len(days)); mn = np.zeros(len(days)); mx = np.zeros(len(days)); idx = {d: i for i, d in enumerate(days)}
    for d, g in F.groupby("date"):
        c = np.cumsum(g.sort_values("tout").u.to_numpy()); i = idx[d]; tot[i] = c[-1]; mn[i] = min(0, c.min()); mx[i] = max(0, c.max())
    return tot, mn, mx
def sim(t, mn, mx, policy, T=3000, D=2500, maxd=22):
    out = []
    for s in range(len(t) - 5):
        eq = 0; pk = 0; r = None
        for i in range(s, min(len(t), s + maxd)):
            k = policy(eq, pk)
            if eq + k * mn[i] <= pk - D: r = ("b", i - s + 1); break
            pk = max(pk, eq + k * mx[i]); eq += k * t[i]
            if eq >= T: r = ("p", i - s + 1); break
        out.append(r)
    p = [r[1] for r in out if r and r[0] == "p"]; b = sum(1 for r in out if r and r[0] == "b")
    return 100 * len(p) / len(out), 100 * b / len(out), (np.median(p) if p else np.nan)
POL = {
    "fixed 1": lambda eq, pk: 1,
    "fixed 2": lambda eq, pk: 2,
    "start 2, drop to 1 if DD from peak > $800": lambda eq, pk: 2 if pk - eq < 800 else 1,
    "start 2, drop to 1 if cushion < $1500": lambda eq, pk: 2 if eq - (pk - 2500) >= 1500 else 1,
    "start 1, 2 after +$500": lambda eq, pk: 2 if eq >= 500 else 1,
    "start 1, 2 after +$1000, 3 after +$2000": lambda eq, pk: 3 if eq >= 2000 else (2 if eq >= 1000 else 1),
    "start 2, 3 after +$1000, 1 if eq < -$800": lambda eq, pk: 1 if eq < -800 else (3 if eq >= 1000 else 2),
}
for tag, lo in (("mnq_fut", 20240201), ("nq_1m", 20200201)):
    base = daily_arrays(tag, lo)
    tier = daily_arrays(tag, lo, weights={m: 2.0 for m in TOP})
    print(f"\n===== {tag} (Apex 50K: target $3,000, trailing $2,500 intraday realized)")
    for nm, pol in POL.items():
        a = sim(*base, pol, maxd=22); b = sim(*base, pol, maxd=44)
        print(f"{nm:45s} | 30 days: pass {a[0]:3.0f}% bust {a[1]:3.0f}% med {a[2]:4.0f}d | 60 days: pass {b[0]:3.0f}% bust {b[1]:3.0f}%")
    for nm, pol in (("TIER: 2 on top-5 modules, 1 on others", lambda eq, pk: 1), ("TIER + drop to half if DD>$800", lambda eq, pk: 1 if pk - eq < 800 else 0.5)):
        a = sim(*tier, pol, maxd=22); b = sim(*tier, pol, maxd=44)
        print(f"{nm:45s} | 30 days: pass {a[0]:3.0f}% bust {a[1]:3.0f}% med {a[2]:4.0f}d | 60 days: pass {b[0]:3.0f}% bust {b[1]:3.0f}%")
