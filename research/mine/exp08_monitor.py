"""exp08_monitor.py (2026-10-29, experimento 08 / frente 5C): monitor de borde (CUSUM) y respuesta a la alarma re-validados sobre 2010-26
con el z corregido (antes de 2020: z = normalizado / 100; os_adapt.py usaba normalizado / (2 x ATR)), k / h vigentes (monitor_recal3.json)
y el set vigente (Ultra = UltraR + CPI09 x4 + SO04 / RV11 / ORFAIL / CAM3). Plan: docs/PLAN_2026-10-29_exp08.md.
Run (desde research/mine): python3 exp08_monitor.py  -> exp08_monitor.json"""
import os, sys, json, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from wrq_lib import getD
from news import NEWS
from audit16_stats import load
from os_adapt import review_set, stats, DUR, pf
NEW = {"SO04": ("CLOCK_ANCHOR", 1527), "RV11": ("RVOL_DRIVE", 4226), "ORFAIL": ("OR_FAIL", 142), "CAM3": ("PIVOT_FADE", 365)}
MR3 = json.load(open(os.path.join(HERE, "monitor_recal3.json")))["Ultra + durable four"]
K, Hh, HW = MR3["alarm"]["k"], MR3["alarm"]["h"], MR3["warn"]["h"]
PER = {"2013-19 norm": (20130101, 20200101), "2020-23 real": (20200101, 20240101), "2024-26 real": (20240101, 20991231)}


def build(with_new=True):
    D = getD("nqdb.npz")
    days = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); days = days[(days >= 20100701) & ~np.isin(days, list(NEWS["FOMC"]))]
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(days).to_numpy()
    if with_new == "os_adapt_set":                                                            # el set exacto de os_adapt.py (UltraR + CPI09 sin x4)
        C = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb")); Q = pickle.load(open(os.path.join(HERE, "ultraq_trades.pkl"), "rb"))["UltraQ"]
        R, N = C["UltraR"]; R = pd.concat([R, Q[0][Q[0]["mod"] == "CPI09"]], ignore_index=True); N = pd.concat([N, Q[1][Q[1]["mod"] == "CPI09"]], ignore_index=True)
    else:
        sets, cur = load(); R, N = cur[0].copy(), cur[1].copy()
    if with_new is True:
        TR = {}
        for f in ("trades_db_old.pkl", "trades_db_new.pkl"): TR.update(pickle.load(open(os.path.join(HERE, f), "rb")))
        for nm, key in NEW.items():
            R = pd.concat([R, pd.DataFrame(dict(date=TR[key]["real"].date.to_numpy(), mod=nm, u=TR[key]["real"].usd.to_numpy(), w=1.0))], ignore_index=True)
            N = pd.concat([N, pd.DataFrame(dict(date=TR[key]["norm"].date.to_numpy(), mod=nm, u=TR[key]["norm"].usd.to_numpy(), w=1.0))], ignore_index=True)
    for X in (R, N): X["x"] = X.u * X.w
    mods = sorted(set(N["mod"]) | set(R["mod"]))
    Mn = N.pivot_table(index="date", columns="mod", values="x", aggfunc="sum").reindex(index=days, columns=mods, fill_value=0.0).fillna(0.0)
    Mr = R.pivot_table(index="date", columns="mod", values="x", aggfunc="sum").reindex(index=days, columns=mods, fill_value=0.0).fillna(0.0)
    M = Mn.copy(); post = days >= 20200101; M.loc[post] = Mr.loc[post]                       # normalizado antes de 2020, real desde 2020
    return days, atr, mods, M.to_numpy(), N, post


def zday(row, t, atr, post, zmode):
    if zmode == "corregido": return row / (2.0 * atr[t]) if post[t] else row / 100.0
    return row / (2.0 * atr[t])                                                              # os_adapt.py (mal escalado antes de 2020)


def run(days, atr, mods, Mv, N, post, pol, k, h, hw, zmode="corregido"):
    n = len(days); out = np.zeros(n); s = 0.0; until = -1; fb = None; alarms = []; warns = []; off = 0; half = 0; warned = False
    col = {m: i for i, m in enumerate(mods)}; allm = list(range(len(mods)))
    for t in range(n):
        if t < until: act = fb; off += 1
        else: act = allm
        scale = 0.5 if (pol == "WH" and t >= until and s > hw) else 1.0      # el estado del CUSUM al empezar el dia (solo dias previos)
        half += scale < 1.0
        out[t] = scale * (Mv[t, act].sum() if len(act) else 0.0)
        if pol != "Y" and t >= until:
            z = zday(Mv[t, act].sum(), t, atr, post, zmode)                  # el monitor mira el P&L por contrato base (sin el medio tamano)
            s = max(0.0, s + k - z)
            if s <= 0: warned = False
            if not warned and s > hw: warned = True; warns.append(int(days[t]))
            if s > h:
                alarms.append(int(days[t])); s = 0.0; warned = False
                if pol.startswith("P"): fb = []; until = t + 1 + int(pol[1:])
                elif pol in ("W252", "WH"): fb = [col[m] for m in review_set(N, mods, int(days[t]))]; until = t + 1 + 252
                elif pol == "D252": fb = [col[m] for m in DUR if m in col]; until = t + 1 + 252
    return out, alarms, warns, off, half


def summary(days, x):
    rec = {nm: stats(x[(days >= lo) & (days < hi)]) for nm, (lo, hi) in PER.items()}
    yrs = {int(y): round(float(x[(days // 10000) == y].sum())) for y in range(2011, 2027)}
    rec["anios_negativos_2011_19"] = int(sum(v < 0 for y, v in yrs.items() if y < 2020)); rec["anios"] = yrs; return rec


def decide(OUT):
    inc = OUT["politicas"]["W252"]; R = {}
    for p, r in OUT["politicas"].items():
        if p in ("W252", "D252"): continue
        c1 = r["2013-19 norm"]["sharpe"] > inc["2013-19 norm"]["sharpe"] and r["2013-19 norm"]["net"] >= inc["2013-19 norm"]["net"]
        c2 = all(r[q]["net"] >= 0.95 * inc[q]["net"] and r[q]["sharpe"] >= inc[q]["sharpe"] - 0.05 for q in ("2020-23 real", "2024-26 real"))
        R[p] = dict(gana_2013_19=c1, no_pierde_2020_26=c2, pasa=c1 and c2)
    ok = [p for p, v in R.items() if v["pasa"]]
    R["ganador"] = max(ok, key=lambda p: OUT["politicas"][p]["2013-19 norm"]["sharpe"]) if ok else "W252"
    R["veredicto"] = "sin cambio: W252 (la respuesta implementada) sigue" if R["ganador"] == "W252" else (f"{R['ganador']} reemplaza a W252" + (" (sacar la respuesta a la alarma; el monitor queda como alerta)" if R["ganador"] == "A" else ""))
    return R


if __name__ == "__main__":
    OUT = {"k": K, "h": Hh, "aviso": HW, "control_os_adapt": {}, "politicas": {}}
    # control: set de os_adapt (sin los 4 de 6 anios), z mal escalado y k / h viejos -> debe reproducir os_adapt.json
    ref = json.load(open(os.path.join(HERE, "os_adapt.json")))
    days, atr, mods, Mv, N, post = build(with_new="os_adapt_set")
    for pol, key in (("A", "A"), ("W252", "W252")):
        x, al, wa, off, half = run(days, atr, mods, Mv, N, post, pol, 0.0758, 18.57, 1e18, zmode="os_adapt")
        rec = summary(days, x); OUT["control_os_adapt"][pol] = dict(alarmas=len(al), **{q: rec[q] for q in PER})
        print(f"control {pol}: alarmas {len(al)} (os_adapt {ref[key]['alarms']}) | " + " | ".join(f"{q}: net {rec[q]['net']} (os_adapt {ref[key][q]['net']}) Sh {rec[q]['sharpe']} ({ref[key][q]['sharpe']})" for q in PER), flush=True)
    days, atr, mods, Mv, N, post = build(with_new=True)
    for zmode in ("os_adapt", "corregido"):
        x, al, wa, off, half = run(days, atr, mods, Mv, N, post, "A", K, Hh, HW, zmode=zmode)
        OUT[f"alarmas_A_z_{zmode}"] = al; OUT[f"avisos_A_z_{zmode}"] = wa
        print(f"set vigente, k/h vigentes, z {zmode}: alarmas {al} | avisos {len(wa)}", flush=True)
    for pol in ("A", "W252", "P63", "P126", "P252", "D252", "WH"):
        x, al, wa, off, half = run(days, atr, mods, Mv, N, post, pol, K, Hh, HW)
        rec = summary(days, x); rec.update(alarmas=al, dias_en_respuesta=off, dias_medio_tamano=half); OUT["politicas"][pol] = rec
        print(f"{pol:5s} alarmas {len(al):2d} dias resp {off:4d} medio {half:4d} | " + " | ".join(f"{q}: net {rec[q]['net']:>7,} Sh {rec[q]['sharpe']:5.2f} DD {rec[q]['maxdd']:>6,}" for q in PER) + f" | anios neg 2011-19 {rec['anios_negativos_2011_19']}", flush=True)
    OUT["regla"] = decide(OUT); print(OUT["regla"])
    json.dump(OUT, open(os.path.join(HERE, "exp08_monitor.json"), "w"), indent=1)
