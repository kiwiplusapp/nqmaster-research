"""Cost of a prop-firm news blackout (MyFundedFutures Rapid sim funded: no positions or orders from 2 minutes before to 2 minutes
after a Tier-1 release: CPI and Employment Report 08:30 ET, FOMC minutes 14:00 ET; FOMC days are already skipped by NQMaster).
Trades open at the window start are closed at the 08:28 (13:58) price (+1 tick slippage); entries inside the window are dropped.
Scenario ALL = the strict reading 'any data release': every day 08:28-08:32 and 09:58-10:02 (upper bound).
Module trades from wrq_entries.pkl (base exits, 1 contract, no conflict filter) -> news_cost.csv"""
import sys, pickle, datetime as dt, numpy as np, pandas as pd
sys.path.insert(0, ".")
sys.path.insert(0, "..")
from core import Data, S
from news import NEWS

ULTRA = ["ORB60", "ORB90", "MSEQ", "MSEQS", "CRT11", "ICT", "MOM11", "MOM1030", "MOM13", "ON07", "REV06", "LON", "VW13", "VOLB",
         "LATE15", "LATEFH", "ENG10", "NF05", "LF06", "LF0430"]
WR70 = ["ORB60", "ORB90", "MSEQ", "MSEQS", "CRT11", "ICT", "MOM11", "REV06", "VW13", "VW13b", "VOLB_tf1", "LATE15", "NF05", "LF06", "LF0430"]
T1_AM = NEWS["CPI"] | NEWS["NFP"]
MIN = set()
for f in NEWS["FOMC"]:
    d = dt.date(f // 10000, f // 100 % 100, f % 100) + dt.timedelta(days=21); MIN.add(int(d.strftime("%Y%m%d")))


def adjust(D, T, windows):
    """windows: function(date) -> list of window-start ET HHMM; returns adjusted P&L per trade and affected flag"""
    pv = 2.0; tick = 0.25; u = T.u0.to_numpy().copy(); hit = np.zeros(len(T), bool)
    sm = D.sm; c = D.c
    for r, t in enumerate(T.itertuples()):
        for w in windows(t.date):
            ws, we = S(w), S(w) + 4                          # 08:28 .. 08:32
            s0, s1 = sm[t.fi], sm[t.tx]
            if ws <= s0 < we:                                # entry inside the window: no trade
                u[r] = 0.0; hit[r] = True; break
            if s0 < ws and s1 >= ws and t.tx > t.fi:          # open across the window start: flat at the 08:28 price
                lo, hi = int(t.fi), int(t.tx)
                k = lo + int(np.searchsorted(sm[lo:hi + 1], ws, side="left")) - 1   # last bar opening before 08:28
                done = False                                  # tx is the time-exit bar: did stop / target close it earlier?
                for q in range(lo + 1, k + 1):
                    if (t.d > 0 and (D.l[q] <= t.sl0 or D.h[q] >= t.tp0)) or (t.d < 0 and (D.h[q] >= t.sl0 or D.l[q] <= t.tp0)):
                        done = True; break
                if done: break
                px = c[k] - t.d * tick
                u[r] = (px - t.ent0) * t.d * pv - 1.90; hit[r] = True; break
    return u, hit


if __name__ == "__main__":
    E = pickle.load(open("wrq_entries.pkl", "rb")); rows = []
    for name, per_split in (("nq_1m.npz", (("IS", 20200101, 20240101), ("C24", 20240101, 20990101))), ("mnq_fut.npz", (("REAL", 20240101, 20990101),))):
        D = Data(name); T0 = E[name]; T0 = T0[~T0.fomc].reset_index(drop=True)
        scen = {"T1 (CPI, NFP 08:30; FOMC minutes 14:00)": lambda d: ([828] if d in T1_AM else []) + ([1358] if d in MIN else []),
                "ALL (every day 08:30 and 10:00)": lambda d: [828, 958]}
        for per, a, b in per_split:
            T = T0[(T0.date >= a) & (T0.date < b)].reset_index(drop=True)
            for sn, fn in scen.items():
                u, hit = adjust(D, T, fn)
                for prof, mods in (("Ultra", ULTRA), ("WR70Plus", WR70)):
                    m = T["mod"].isin(mods).to_numpy(); base = T.u0.to_numpy()[m]; new = u[m]
                    g = lambda x: x[x > 0].sum() / -x[x <= 0].sum()
                    nz = new[np.abs(new) > 0]
                    rows.append(dict(per=per, scenario=sn, profile=prof, trades=int(m.sum()), affected=int(hit[m].sum()),
                                     pnl_base=round(base.sum()), pnl_new=round(new.sum()), change_pct=round(100 * (new.sum() / base.sum() - 1), 1),
                                     pf_base=round(g(base), 3), pf_new=round(g(nz), 3), wr_base=round(100 * (base > 0).mean(), 1), wr_new=round(100 * (nz > 0).mean(), 1)))
            print(name, per, flush=True)
    R = pd.DataFrame(rows); R.to_csv("news_cost.csv", index=False); pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 50)
    print(R.to_string(index=False))
