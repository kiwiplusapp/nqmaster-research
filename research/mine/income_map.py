"""2026-10-17 'quiero $250-300 por dia' (Federico): what the current system earns per BASE CONTRACT per calendar day, honestly.
Daily $ series (real Databento NQ 2020-10-15..2026-10-08, $1.90 + 1 tick, 1 base contract per module, MOM1030/CPI09 x4) for
Ultra, Ultra + six-year modules (group 11), UltraQ, WR70Plus, each alone and with GoldMaster Robust / WinRate (gold: CFD XAU 2020-23,
MGC real from 2024-02; 1 contract). Edge scenarios: full, -35% (haircut of the mean daily P&L), -50%, zero; cost +1 tick per side.
Output: $/trading day and $/calendar day, $/month, Sharpe, maxDD, worst month, P(losing month), and the number of base contracts
needed for a $250 and $300 per calendar day average under each scenario. -> income_map.json"""
import os, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); START, END = 20201015, 20261008
GOLD = {"Robust": ["OD1030", "ENG0408", "SVWAP22", "ASIA1R", "ENG0206"], "WinRate": ["OD1030", "ENG0408", "SVWAP22"]}


def nq_sets():
    P = pickle.load(open(os.path.join(HERE, "six_trades.pkl"), "rb")); P6 = pickle.load(open(os.path.join(HERE, "six_ultra6_trades.pkl"), "rb"))
    return {"Ultra": P["Ultra"], "Ultra+six": P6["Ultra6"], "UltraQ": P["UltraQ"], "WR70Plus": P["WR70Plus"]}


def gold_trades(prof):
    G = pickle.load(open(os.path.join(HERE, "gold_curated_trades.pkl"), "rb")); rows = []
    for m in GOLD[prof]:
        a = G[m]["IS"]; a = a[a.date < 20240201]; b = G[m]["REAL"]; b = b[b.date >= 20240201]; c = G[m]["C24"]; c = c[(c.date >= 20240101) & (c.date < 20240216)]
        rows += [a, c, b]
    T = pd.concat(rows, ignore_index=True); return T[(T.date >= START) & (T.date <= END)]


def daily(T, extra=0.0, days=None):
    pnl = T.w * (T.u - extra); d = pnl.groupby(T.date).sum()
    if days is not None: d = d.reindex(days, fill_value=0.0)
    return d


def metr(d, cal_days):
    x = d; eq = x.cumsum(); mo = x.groupby(pd.to_datetime(x.index.astype(str)).to_period("M")).sum()
    return dict(per_trading_day=round(float(x.mean()), 1), per_cal_day=round(float(x.sum() / cal_days), 1), per_month=round(float(x.sum() / cal_days * 30.44)),
                sharpe=round(float(x.mean() / x.std() * np.sqrt(252)), 2), maxdd=round(float((eq.cummax() - eq).max())), worst_month=round(float(mo.min())),
                losing_months_pct=round(100 * float((mo < 0).mean()), 1), p10_month=round(float(mo.quantile(0.1))), median_month=round(float(mo.median())))


if __name__ == "__main__":
    NQ = nq_sets(); days = np.array(sorted(NQ["Ultra"].date.unique()))
    cal = (pd.Timestamp(str(END)) - pd.Timestamp(str(START))).days + 1
    OUT = {}
    for nm, T in NQ.items():
        for g in (None, "Robust", "WinRate"):
            for tick in (0.0, 1.0):                                   # extra ticks per side -> $0.5 x 2 x tick per contract
                extra = tick * 1.0
                d = daily(T, extra, days)
                if g: d = d.add(daily(gold_trades(g), 2.0 * extra, None).reindex(d.index, fill_value=0.0))   # MGC tick $1 -> +$2 per round trip per extra tick
                key = f"{nm}{'+gold ' + g if g else ''} | +{int(tick)} tick"; rec = {}
                for hc in (0.0, 0.35, 0.5, 1.0):
                    x = d - hc * d.mean(); m = metr(x, cal)
                    m["contracts_for_250_day"] = round(250 / m["per_cal_day"], 1) if m["per_cal_day"] > 0 else None
                    m["contracts_for_300_day"] = round(300 / m["per_cal_day"], 1) if m["per_cal_day"] > 0 else None
                    rec[f"edge-{int(hc*100)}%"] = m
                OUT[key] = rec
                f = rec["edge-0%"]; h = rec["edge-35%"]
                print(f"{key:34s} $/cal day {f['per_cal_day']:6.1f} ({h['per_cal_day']:6.1f} @-35%)  $/mo {f['per_month']:5d} ({h['per_month']:5d})  SR {f['sharpe']:.2f}  DD {f['maxdd']:5d}  worst mo {f['worst_month']:6d}  losing mo {f['losing_months_pct']:4.1f}%  c250 {f['contracts_for_250_day']} / {h['contracts_for_250_day']}")
    json.dump(OUT, open(os.path.join(HERE, "income_map.json"), "w"), indent=1)
