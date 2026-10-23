"""Independent check of the NQMaster dashboard's ACCOUNT SIMULATION (2026-10-21). Replays closed trades through the same account
rules (propcycle.py = Python port of NQMaster.PropCycle, three-way audited by tools/propcycle_test/run_test.py): buy an eval ->
pass or lose it -> next session a new eval or the funded account -> payouts at the close -> lost / completed -> new eval.

Input A, NinjaTrader trades export of a run WITH the cycle simulation (Strategy Analyzer > Trades > right click > Export):
    python3 dash_cycle_ref.py --csv "C:/.../trades.csv" --preset Lucid25K [--fee 89] [--tz America/Argentina/Buenos_Aires]
    The export already has the eval / funded sizes and stops of each phase, so the trades are replayed as they are.
Input B, research trades (1 base contract per module, current system ultra_d4), scaled to the preset's eval / funded contracts:
    python3 dash_cycle_ref.py --research --preset Lucid25K --start 2026-06-23 --end 2026-10-08
Differences vs the dashboard: this script sees only CLOSED trades, so the intraday low is the lowest running realized P&L of the
day (the strategy also counts the open position at each bar's worst price -> it can lose an account this script keeps), and the
per-trade risk cap of the funded presets is not applied to research trades (no risk column)."""
import os, sys, argparse, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from propcycle import from_preset, PRESETS
# eval / funded contracts and daily profit stops per preset (NQMaster ApplyPreset with the default Contracts 1)
SIZE = {"Lucid25K": (1, 1, 560, 0), "Lucid50K": (1, 1, 1350, 0), "Lucid150K": (6, 3, 4050, 0), "LucidPro25K": (2, 1, 0, 0),
        "LucidPro50K": (4, 1, 0, 1000), "FundedNext25K": (2, 1, 0, 0), "Mffu50K": (1, 1, 800, 0)}


def days_from_trades(t):
    """t: columns day (session date), tout, pnl -> list of (day, [cumulative realized after each trade])"""
    out = []
    for d, g in t.sort_values(["day", "tout"]).groupby("day"):
        out.append((d, g.pnl.cumsum().values))
    return out


def run(days, preset, fee=None, act=0.0, scale=None, warm=0, h=0.0):
    c = from_preset(preset, fee=fee, act=act); ev_k, fu_k, G_ev, G_fu = SIZE[preset]
    st = dict(evals=0, ev_pass=0, ev_lost=0, funded=0, fu_lost=0, fu_done=0, pays=0, gross=0.0, cash=0.0, fees=0.0, act=0.0)
    ev = []; nxt = "eval"; wait = 0; started = False
    for i, (d, cum) in enumerate(days):
        if i < warm: continue
        if c.alive and started:
            pass
        elif nxt and wait > 0: wait -= 1; continue
        elif nxt:
            c.start(nxt == "funded"); started = True
            if nxt == "funded": st["funded"] += 1; st["act"] += act; ev.append((d, f"Fondeada #{st['funded']} activada"))
            else: st["evals"] += 1; st["fees"] += c.fee; ev.append((d, f"Eval #{st['evals']} comprada (${c.fee:.0f})"))
            nxt = None
        k = (ev_k if not c.funded else fu_k) if scale else 1.0; G = G_fu if c.funded else G_ev
        raw0 = c.raw; last = 0.0; res = 0
        for x in cum:
            x = k * (x - h)                      # h = edge haircut per day and base contract (research convention: the whole day shifted)
            if G > 0 and last >= G: break            # daily profit stop (the strategy flattens and stops the day)
            res = c.bar(raw0 + min(x, last), raw0 + x)
            if res: break
            last = x
        if res == -1:
            if c.funded: st["fu_lost"] += 1; ev.append((d, f"Fondeada #{st['funded']} PERDIDA ({c.pays} retiros)"))
            else: st["ev_lost"] += 1; ev.append((d, f"Eval #{st['evals']} PERDIDA (dia {c.days + 1})"))
            nxt = "eval"; wait = 0; continue
        if res == 1:
            st["ev_pass"] += 1; ev.append((d, f"Eval #{st['evals']} APROBADA en {c.days + 1} dias")); nxt = "funded"; wait = max(0, c.mindays - (c.days + 1)); continue
        if not len(cum): last = -k * h
        amt = c.day_close(raw0 + last)
        if amt > 0: st["pays"] += 1; st["gross"] += amt; st["cash"] += c.split * amt; ev.append((d, f"RETIRO #{c.pays} ${amt:,.0f}"))
        if not c.alive: st["fu_done"] += 1; ev.append((d, f"Fondeada #{st['funded']} COMPLETADA")); nxt = "eval"
    st["net"] = st["cash"] - st["fees"] - st["act"]
    return st, ev, c


def report(st, ev, c, d0, d1, title):
    months = max(1.0, (pd.Timestamp(str(d1)) - pd.Timestamp(str(d0))).days) / 30.44
    print(f"\n{title}  ({c.firm}, {d0} -> {d1}, {months:.1f} meses)")
    print(f"  Evals compradas {st['evals']}  aprobadas {st['ev_pass']}  perdidas {st['ev_lost']}")
    print(f"  Fondeadas {st['funded']}  perdidas {st['fu_lost']}  completadas {st['fu_done']}")
    print(f"  Retiros {st['pays']}  pedidos ${st['gross']:,.0f}  cobrados ${st['cash']:,.0f}  costos ${st['fees'] + st['act']:,.0f}")
    print(f"  RESULTADO NETO ${st['net']:,.0f}  (~${st['net'] / months:,.0f}/mes)")
    for d, e in ev[-12:]: print(f"    {d}  {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv"); ap.add_argument("--research", action="store_true"); ap.add_argument("--set", default="ultra_d4")
    ap.add_argument("--preset", default="Lucid25K", choices=list(PRESETS)); ap.add_argument("--fee", type=float); ap.add_argument("--act", type=float, default=0.0)
    ap.add_argument("--tz", default="America/Argentina/Buenos_Aires"); ap.add_argument("--start"); ap.add_argument("--end"); ap.add_argument("--haircut", type=float, default=0.0, help="0.35 = 35%% less edge, 1 = zero edge")
    a = ap.parse_args()
    if a.csv:
        from nt_trades import load_nt
        t = load_nt(a.csv); et = t.tout.dt.tz_localize(a.tz).dt.tz_convert("America/New_York").dt.tz_localize(None)
        t["day"] = (et + pd.Timedelta(hours=6)).dt.strftime("%Y%m%d").astype(int); t["tout"] = et
        scale = False
    else:
        from nt_compare import research_set
        X, _ = research_set(a.set); t = pd.DataFrame({"day": X.date.astype(int), "tout": X.tout, "pnl": X.u * X.w}); scale = True
    if a.start: t = t[t.day >= int(a.start.replace("-", ""))]
    if a.end: t = t[t.day <= int(a.end.replace("-", ""))]
    days = days_from_trades(t)
    h = a.haircut * float(np.mean([cum[-1] for _, cum in days]))
    st, ev, c = run(days, a.preset, fee=a.fee, act=a.act, scale=scale, h=h)
    report(st, ev, c, days[0][0], days[-1][0], ("NinjaTrader export" if a.csv else f"research {a.set}") + (f", edge -{a.haircut:.0%}" if a.haircut else ""))
