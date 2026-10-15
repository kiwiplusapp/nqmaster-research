"""2026-10-16 'ALL available contracts on an 80%-WR trade, evals only' (Federico). Same frame as sniper_eval.py / sniper_uniform.py
(UltraR + CPI09, real Databento NQ 2020-26 minute paths incl. open-trade lows, +1 tick per side, firm rules of month80.py, daily profit stop
0.9 x consistency x target, starts T1 2020-03..2023-10 / T2 2024-01..). Sniper trade size = firm eval micro cap minus every contract already
open at its entry minute (rest of Ultra at rest x its weight + earlier sniper trades still open), at least 1. Groups:
  static: MOM1030 + CPI09 (fixed, what NQMaster sizes x4 / eval x8 today)
  wf80  : walk-forward, the module's trailing-365-day WR >= 80% with n >= 20 (only past trades).
rest = 1 (rest of Ultra at 1 contract) or 0 (only the sniper trades). Edge 0 / 35% haircut (scaled with the policy's own mean).
Also: per-trade $ of the all-in trades (worst, avg loss, share of losses >= trailing DD) and the intraday adverse excursion.
-> allin_eval.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import robust2_build as RB
from robust2_life import full_paths, vectors, SP
from wrq_lib import getD
from month80 import SET, outcomes, serial_first
from sniper_eval import wf_flag, conc
from sniper_life import build

FIRMS = ["Lucid Flex 25K", "Lucid Pro 25K", "Lucid Flex 50K", "Lucid Pro 50K", "FundedNext Rapid Pro 50K", "MFFU Rapid EOD 50K"]


def allin_sizes(S, open_rest, days, D, cap):
    """S sorted by date/tin; open_rest (nd x 1440) contracts open from the rest -> size per sniper trade"""
    pos = {d: i for i, d in enumerate(days)}; extra = {}; out = np.zeros(len(S))
    for j, t in enumerate(S.itertuples()):
        r = pos[t.date]; a, b = D.sm[t.fi], min(1440, D.sm[t.xi])
        ex = extra.setdefault(r, np.zeros(1441))
        busy = open_rest[r, a] + np.cumsum(ex)[a]
        q = max(1.0, float(np.floor(cap - busy))); out[j] = q
        ex[a] += q; ex[b] -= q
    return out


if __name__ == "__main__":
    E = RB.setup(); D = getD(RB.NAME)
    days = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))[0]; n = len(days)
    T = build(E, D); flags = {"static": T["mod"].isin(["MOM1030", "CPI09"]).to_numpy(), "wf80": wf_flag(T, 0.80, 365, 20)}
    inday = T.date.isin(days).to_numpy(); T2 = T[inday]
    d24 = int(np.searchsorted(days, 20240101))
    s1 = np.nonzero((days >= 20200301) & (days < 20231101))[0]; s2 = np.nonzero(days >= 20240101)[0]; s2 = s2[s2 < n - 40]
    OUT = {}; rows = []
    for grp, f in flags.items():
        ff = f[inday]; R0 = T2[~ff]; S0 = T2[ff].sort_values(["date", "tin"]).reset_index(drop=True)
        Pr = full_paths(R0, days); cr = R0.w.groupby(R0.date).sum().reindex(days, fill_value=0).to_numpy(); kr = conc(R0, days, D)
        g = S0[S0.date >= 20200101]
        OUT[f"{grp}_trades"] = dict(n=int(len(g)), per_week=round(len(g) / (n / 5), 2), wr=round(100 * float((g.u > 0).mean()), 1),
                                    avg_win_1c=round(float(g.u[g.u > 0].mean()), 1), avg_loss_1c=round(float(g.u[g.u <= 0].mean()), 1),
                                    worst_1c=round(float(g.u.min()), 1), pf=round(float(g.u[g.u > 0].sum() / -g.u[g.u <= 0].sum()), 2),
                                    mods=g["mod"].value_counts().to_dict())
        print(grp, OUT[f"{grp}_trades"], flush=True)
        for firm in FIRMS:
            Tg, Dd, cons, mind, dll, fee, mx = SET[firm]; G = 0.9 * cons * Tg if cons > 0 else 0.0
            for rest in (1, 0):
                q = allin_sizes(S0, rest * kr, days, D, mx); S1 = S0.assign(w=q)
                Ps = full_paths(S1, days); cs = S1.w.groupby(S1.date).sum().reindex(days, fill_value=0).to_numpy()
                lw = rest * Pr[0] + Ps[0]; cl0 = rest * Pr[1] + Ps[1]; fn = rest * Pr[2] + Ps[2]; cc = rest * cr + cs
                mu1 = float(fn[:d24].mean()); mu2 = float(fn[d24:].mean())
                # per-trade all-in $ (incl. +1 tick per contract) and worst intraday adverse excursion per trade
                pnl = q * (S1.u.to_numpy() - 1.0); adv = []
                for t, qq in zip(S1.itertuples(), q):
                    k = np.arange(t.fi, t.xi + 1); a = ((D.l[k] - t.e) if t.d > 0 else (t.e - D.h[k])) * D.pv
                    adv.append(qq * (min(0.0, a.min()) - D.comm - 1.0))
                adv = np.array(adv); m20 = (S1.date >= 20200101).to_numpy()
                rec = dict(group=grp, firm=firm, rest=rest, cap=mx, size_median=float(np.median(q[m20])), size_min=float(q[m20].min()),
                           trade_avg_win=round(float(pnl[m20][pnl[m20] > 0].mean())), trade_avg_loss=round(float(pnl[m20][pnl[m20] <= 0].mean())),
                           trade_worst=round(float(pnl[m20].min())), pct_losses_ge_dd=round(100 * float((pnl[m20] <= -Dd).sum() / max(1, (pnl[m20] <= 0).sum())), 1),
                           pct_trades_adverse_ge_dd=round(100 * float((adv[m20] <= -Dd).mean()), 1), pct_trades_adverse_ge_half_dd=round(100 * float((adv[m20] <= -Dd / 2).mean()), 1))
                for hc in (0.0, 0.35):
                    h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
                    lo, cl = vectors(lw - cc[:, None] - h[:, None], cl0 - cc[:, None] - h[:, None], fn - cc - h, G)
                    if dll > 0:
                        hit = lo <= -dll; cl = np.where(hit, -float(dll), cl); lo = np.where(hit, -float(dll), lo)
                    res, dd = outcomes(lo, cl, Tg, Dd, cons, mind, n); sfx = "" if hc == 0 else "_h35"
                    for tag, st in (("T1", s1), ("T2", s2)):
                        for w in (5, 10, 20): rec[f"{tag}_p{w}{sfx}"] = round(100 * float(np.mean([(res[s] == 1) and dd[s] < w for s in st])), 1)
                        rec[f"{tag}_bust{sfx}"] = round(100 * float(np.mean([res[s] == -1 for s in st])), 1)
                        rec[f"{tag}_bust5{sfx}"] = round(100 * float(np.mean([(res[s] == -1) and dd[s] < 5 for s in st])), 1)
                        se = [serial_first(res, dd, s, 20) for s in st]
                        rec[f"{tag}_serial20{sfx}"] = round(100 * float(np.mean([x for x, _ in se])), 1); rec[f"{tag}_evals{sfx}"] = round(float(np.mean([y for _, y in se])), 2)
                rows.append(rec)
                print(f"{grp:6s} {firm:24s} rest{rest} size med {rec['size_median']:.0f} | p20 {rec['T1_p20']}/{rec['T2_p20']} bust {rec['T1_bust']}/{rec['T2_bust']} "
                      f"serial {rec['T1_serial20']}/{rec['T2_serial20']} evals {rec['T2_evals']} | h35 p20 {rec['T1_p20_h35']}/{rec['T2_p20_h35']} | "
                      f"trade win {rec['trade_avg_win']} loss {rec['trade_avg_loss']} worst {rec['trade_worst']} adv>=DD {rec['pct_trades_adverse_ge_dd']}%", flush=True)
    OUT["rows"] = rows
    pd.DataFrame(rows).to_csv(os.path.join(HERE, "allin_eval.csv"), index=False)
    json.dump(OUT, open(os.path.join(HERE, "allin_eval.json"), "w"), indent=1, default=float)
