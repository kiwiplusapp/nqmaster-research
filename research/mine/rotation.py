"""Rotation vs copier vs staggered for Apex 50K evals, trade-level (realized) simulation with Ultra trades (1-lot units x k).
Every scenario runs 3 'slots' for 63 trading days; a slot that busts or times out (21 trading days) is replaced the same day
(new eval, $105); a slot that passes is done (funded). Rotation: entries go to the active account; a losing trade moves the
active pointer to the next live account."""
import os, sys, ast, pickle, numpy as np, pandas as pd
sys.path.insert(0, "."); RES = os.path.dirname(os.getcwd()); sys.path.insert(0, RES)
import final_pkg
from final_pkg import pkg_base, base, cand_trades, conflict_filter, get
from families2 import FAMILIES2
from core import Data, run_events
def get2(ps):
    gen, grid, md = FAMILIES2["VOL_BREAK"]; p = ast.literal_eval(ps); out = {}
    for key, nm in (("nq", "nq_1m.npz"), ("mnq", "mnq_fut.npz")):
        D = final_pkg._D.get(key) or Data(nm); final_pkg._D[key] = D
        df = run_events(D, gen(D, p), flat=955, maxday=md); df["tin"] = D.sm[df.fi.to_numpy().astype(int)]; df["tout"] = D.sm[df.xi.to_numpy().astype(int)] + 1
        out[key] = df[["date", "usd", "tin", "tout", "d"]]
    return out
VW = get("CLOCK_ANCHOR", "{'anc': 'VWAP', 'T': 1300, 'x': 0.3, 'mode': 1, 's': 0.15, 'R': 0.5, 'tg': 0, 'tf': 1, 'hold': 120}")
VB = get2("{'k': 0.45, 's': 0.35, 'R': 2.0, 'tf': 0, 'w1': 1500, 'hold': 400, 'stop': 0}")
TR = {}
for per in ("IS", "C24", "REAL"):
    days = base(per)[1]
    F = conflict_filter(pd.concat([pkg_base(per, True), cand_trades(VW, per, "VW13", 1.0), cand_trades(VB, per, "VOLB", 1.0)], ignore_index=True).sort_values(["date", "tin"]).reset_index(drop=True))
    di = {d: i for i, d in enumerate(days)}
    F = F[F.date.isin(di)]
    TR[per] = (np.array([di[d] for d in F.date]), (F.u * F.w).to_numpy(), len(days))
class Acct:
    def __init__(s, start): s.start = start; s.eq = 0.0; s.pk = 0.0; s.state = 0       # 0 live, 1 pass, -1 bust, 2 timeout
def run(per, mode, k, H=63, T=3000.0, D=2500.0, stagger=10):
    dix, pnl, nd = TR[per]; out = []
    for s0 in range(0, nd - H - 25, 2):
        slots = [Acct(s0 + (stagger * j if mode == "stagger" else 0)) for j in range(3)]
        bought = 3; passes = 0; active = 0
        lo = np.searchsorted(dix, s0); hi = np.searchsorted(dix, s0 + H)
        for t in range(lo, hi):
            day = dix[t]
            for j, a in enumerate(slots):                          # time-outs and replacements
                if a.state == 0 and day - a.start >= 21: a.state = 2
                if a.state in (-1, 2) and day < s0 + H: slots[j] = Acct(day); bought += 1
            live = [j for j, a in enumerate(slots) if a.state == 0 and a.start <= day]
            if not live: continue
            x = pnl[t] * k
            targets = live if mode in ("copy", "stagger") else [active if active in live else live[0]]
            for j in targets:
                a = slots[j]; a.eq += x; a.pk = max(a.pk, a.eq)
                if a.eq >= T: a.state = 1; passes += 1
                elif a.eq <= a.pk - D: a.state = -1
            if mode == "rotate" and x < 0:
                cur = targets[0]; nxt = [j for j in live if j != cur]
                active = (nxt[0] if nxt else cur) if len(live) > 1 else cur
                # move to the next account in circular order
                order = sorted(live); i = order.index(cur); active = order[(i + 1) % len(order)]
        out.append((passes, bought))
    a = np.array(out)
    return dict(passes=round(a[:, 0].mean(), 2), P_zero=round(100 * (a[:, 0] == 0).mean(), 1), evals=round(a[:, 1].mean(), 1), cost_per_pass=round(105 * a[:, 1].sum() / max(1, a[:, 0].sum())))
rows = []
for per in ("REAL", "C24", "IS"):
    for mode, k in (("copy", 2), ("stagger", 2), ("rotate", 2), ("rotate", 4), ("rotate", 6)):
        r = run(per, mode, k); r.update(per=per, mode=f"{mode} x{k}"); rows.append(r)
g = pd.DataFrame(rows); pd.set_option("display.width", 220)
for c in ("passes", "P_zero", "evals", "cost_per_pass"):
    print(c); print(g.pivot(index="mode", columns="per", values=c)[["REAL", "C24", "IS"]].to_string())
