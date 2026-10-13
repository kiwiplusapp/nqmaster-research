"""hist_profiles: every NQMaster profile / system version the project has had, rebuilt on the SAME real futures data and costs
(Databento NQ 1m 2010-06..2026-10, research/data/nqdb.npz, back-adjusted) with the same entry specs and exit engine as db_long.py
(wrq_build entries -> wrq_entries_db.pkl, wrq_lib.xsim), to answer 'did earlier systems backtest better than today's?' and
'which NinjaTrader profiles are obsolete?'.

Views
  real : $ per 1 MNQ base contract ($1.90 RT + 1 tick per side), weights w = size multiplier (ICT x2, confluence / context x2,
         cap 2x), FOMC days skipped, NQMaster MinAtrPoints guard (trade only days with daily ATR >= 150), 2020-01-01..2026-10-08.
         Day set = every session date of the data in the window minus FOMC (days blocked by the ATR guard count as 0 P&L).
  norm : the same trades with cost = 0.345% of daily ATR and P&L in % of ATR (regime test 2010-14 / 2015-19).
Funded-account risk at 1 contract: an account started on every trading day of 2020-26, EOD trailing drawdown $2,000
  (threshold = max EOD balance - 2,000, locked at start + 100 once reached; breach when an EOD balance <= threshold, daily-close
  approximation), P(bust within 21 / 63 trading days) (starts with the full window available) and P(EOD balance reaches +$3,000
  before a breach) (starts that resolved before 2026-10-08; censored share reported).

Profiles (historical designs; the 'now' variants = how the old NT profiles run in TODAY's NQMaster.cs, where the 10-08 ORB
prior-close rule (OrbPriorCloseAtr 0.10) applies to every profile):
  MaxSharpe (v8 09-28), WinRate70 (09-28), MaxPlus (09-29), MaxPlus2 (10-02), Core (10-03), Ultra_v1 (10-03),
  Ultra_ampliado (10-06), Ultra_night (10-07), Ultra / UltraLean / WR70Plus / Estable (final3y.PROFILES, 10-08 code),
  Core_now, Durable6.  MaxTrades is skipped (MOM1130 / RSI2 entries are not in wrq_entries_db.pkl).
-> hist_profiles.json, hist_profiles_trades.pkl, hist_profiles.md
Run: cd research/mine && python3 hist_profiles.py"""
import os, sys, json, pickle, time, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import wrq_port, wrq_combo
import db_long as DL                        # patches wrq_port / wrq_combo .module_trades with module_trades3, sets PER["DB"/"DB_N"]
import final3y as F3                        # (re-patches module_trades with module_trades2 -> restored below)
from wrq_lib import S, getD
from wrq_port import build_profile, conflict_filter, apply_rules, ULTRA, WR70
from wrq_combo import BE, ORBt
from wrq_agree import n_same
from news import NEWS

wrq_port.module_trades = DL.module_trades3; wrq_combo.module_trades = DL.module_trades3   # final3y import overrode it
NAME = DL.NAME; MIN_ATR = DL.MIN_ATR
LO, HI = 20200101, 20261008
PERIODS = {"2020-2026": (20200101, 20261008), "2020-2023": (20200101, 20231231), "2024-2026": (20240101, 20261008)}
NPERIODS = {"2010-2014": (20100101, 20141231), "2015-2019": (20150101, 20191231), "2020-2023": (20200101, 20231231), "2024-2026": (20240101, 20261008)}

# ------------------------------------------------------------------------------------------------ profile specs
def M(*names, base=ULTRA, **extra):
    d = {}
    for n in names: d[n] = dict(extra.get(n, base.get(n, WR70.get(n, {}))))
    return d

MS_MODS = ["ORB60", "MSEQ", "CRT11", "MOM11", "MOM13", "MOM1030", "ON07", "REV06", "LON", "ICT"]
WR_MODS = ["ORB60", "MSEQ", "CRT11", "MOM11", "MOM1030", "ON07", "REV06", "ICT"]
MP_MODS = MS_MODS + ["ORB90", "MSEQS"]
MP2_MODS = MP_MODS + ["VW13"]
CORE_MODS = ["ORB60", "MSEQ", "CRT11", "LON", "ICT", "VOLB", "LATE15"]
UV1_MODS = MP2_MODS + ["VOLB", "LATE15"]
UAMP_MODS = UV1_MODS + ["ENG10", "LATEFH", "VW13b"]
UN_MODS = UAMP_MODS + ["NF05", "LF06", "LF0430"]
assert set(UN_MODS) == set(ULTRA), set(UN_MODS) ^ set(ULTRA)
DUR_MODS = ["NF05", "CRT11", "VOLB", "MSEQS", "ORB60", "ORB90"]
ORB75 = {"ORB60": {"kt": 1.25}}

# spec: (modules dict, overrides, agreement modules, rules 'none'|'conf'|'full', boosts, ICT weight, date, note)
P = {}
P["MaxSharpe"] = (M(*MS_MODS), {}, (), "none", True, 1.0, "2026-09-28", "v8: 10 modules, ICT x1, no rules")
P["WinRate70"] = (M(*WR_MODS, **ORB75), {}, (), "none", True, 1.0, "2026-09-28", "ORB60 0.75R, no MOM13/LON, ICT x1, no rules")
P["MaxPlus"] = (M(*MP_MODS), {}, (), "conf", True, 2.0, "2026-09-29", "MaxSharpe + ORB90 + MSEQS, ICT x2, confluence")
P["MaxPlus2"] = (M(*MP2_MODS), {}, (), "full", True, 2.0, "2026-10-02", "MaxPlus + 12 context rules + VW13 (0.30 ATR, 1 lot)")
P["Core"] = (M(*CORE_MODS), {}, (), "none", True, 2.0, "2026-10-03", "ORB60 MSEQ CRT11 LON ICTx2 VOLB2R LATE15, no rules")
P["Ultra_v1"] = (M(*UV1_MODS), {}, (), "full", True, 2.0, "2026-10-03", "MaxPlus2 + VOLB + LATE15")
P["Ultra_ampliado"] = (M(*UAMP_MODS), {}, (), "full", True, 2.0, "2026-10-06", "Ultra_v1 + ENG10 + LATEFH + VW13b (VW13 wide)")
P["Ultra_night"] = (M(*UN_MODS), {}, (), "full", True, 2.0, "2026-10-07", "Ultra_ampliado + NF05 + LF06 + LF0430")
for k, note in (("Ultra", "current code: Ultra_night + ORB prior-close, VOLB BE, MOM1030/MOM13 agreement"),
                ("UltraLean", "Ultra without ON07 / LATEFH / ENG10"), ("WR70Plus", "current WR70Plus + NightOnWr70 (ORBt, VOLB_tf1 10:47)"),
                ("Estable", "eval safe set, boosts off")):
    mods, over, agr, boosts = F3.PROFILES[k]
    P[k] = (mods, over, agr, "full", boosts, 2.0, "2026-10-08", note)
P["Core_now"] = (M(*CORE_MODS), {"ORB60": ORBt["ORB60"], **BE}, (), "none", True, 2.0, "2026-10-08", "Core as coded today (ORBt, VOLB BE)")
P["Durable6"] = (M(*DUR_MODS), {**BE, **ORBt}, (), "full", True, 2.0, "2026-10-09", "16-year durable modules, Ultra rules/overrides")
# supplementary: the old NT profiles as they run in today's code (OrbPriorCloseAtr applies to every profile)
P["MaxSharpe_now"] = (M(*MS_MODS), {"ORB60": ORBt["ORB60"]}, (), "none", True, 1.0, "code", "MaxSharpe + ORBt (today's NT MaxSharpe)")
P["WinRate70_now"] = (M(*WR_MODS, **ORB75), {"ORB60": ORBt["ORB60"]}, (), "none", True, 1.0, "code", "WinRate70 + ORBt (today's NT WinRate70)")
P["MaxPlus_now"] = (M(*MP_MODS), dict(ORBt), (), "conf", True, 2.0, "code", "MaxPlus + ORBt (today's NT MaxPlus)")
P["MaxPlus2_now"] = (M(*MP2_MODS), dict(ORBt), (), "full", True, 2.0, "code", "MaxPlus2 + ORBt (today's NT MaxPlus2)")
MAIN = ["MaxSharpe", "WinRate70", "MaxPlus", "MaxPlus2", "Core", "Ultra_v1", "Ultra_ampliado", "Ultra_night", "Ultra", "UltraLean",
        "WR70Plus", "Estable", "Core_now", "Durable6"]
SUPP = ["MaxSharpe_now", "WinRate70_now", "MaxPlus_now", "MaxPlus2_now"]


def build(per, spec, cache):
    mods, over, agr, rules, boosts, ictw = spec[:6]
    wrq_port.PROFILES["_h"] = mods
    over = {k: v for k, v in over.items() if k in mods}; agr = tuple(a for a in agr if a in mods)
    X = build_profile(per, "_h", over, rules=False, cache=cache)                       # conflict-filtered, no rules
    if agr:                                                                            # same as wrq_combo.build
        N = n_same(X); drop = N["mod"].isin(agr) & (N.nsame == 0)
        dropped = set(map(tuple, N.loc[drop, ["date", "mod", "tin"]].to_numpy()))
        parts = []
        for mod, p in mods.items():
            q, kf = dict(p), None
            if mod in over:
                q2, kf = over[mod]; q.update(q2 or {})
            key = (per, mod, tuple(sorted(q.items())), DL.SLIP, kf)
            parts.append(cache[key] if key in cache else DL.module_trades3(per, mod, q, DL.SLIP, kf))
        X = pd.concat(parts, ignore_index=True)
        X = X[[(d, m, t) not in dropped for d, m, t in zip(X.date, X["mod"], X.tin)]]
        X = conflict_filter(X.sort_values(["date", "tin"], kind="stable").reset_index(drop=True))
    if rules != "none": X = apply_rules(X, per, context=(rules == "full"))
    X = X.copy()
    if ictw == 1.0:
        assert rules == "none"; X.loc[X["mod"] == "ICT", "w"] = 1.0                # ICT x1 profiles have no other multipliers
    if not boosts: X["w"] = 1.0
    return X.sort_values(["date", "tin"]).reset_index(drop=True)


# ------------------------------------------------------------------------------------------------ metrics
def longest_dd(d):
    eq = np.concatenate([[0.0], np.cumsum(d)]); pk = np.maximum.accumulate(eq); uw = eq < pk - 1e-9
    best = cur = 0
    for v in uw[1:]:
        cur = cur + 1 if v else 0; best = max(best, cur)
    return int(best), bool(uw[-1])


def real_metrics(X, days):
    x = (X.u * X.w).to_numpy(); n = len(X)
    d = pd.Series(x, index=X.date.to_numpy()).groupby(level=0).sum().reindex(days, fill_value=0.0)
    dv = d.to_numpy(); eq = np.concatenate([[0.0], np.cumsum(dv)])
    mo = d.groupby(pd.to_datetime(pd.Series(days).astype(str)).dt.to_period("M").astype(str).to_numpy()).sum()
    w = x[x > 0].sum(); l = -x[x <= 0].sum()
    ld, ongoing = longest_dd(dv)
    cnt = X["mod"].value_counts(); net = (X.u * X.w).groupby(X["mod"]).sum()
    return dict(trades=int(n), tpd=round(n / len(days), 2), wr=round(100 * float((X.u > 0).mean()), 1), pf=round(float(w / l), 3),
                avg_trade=round(float(x.mean()), 2), per_month=round(float(dv.mean() * 21)), net=round(float(x.sum())),
                sharpe=round(float(dv.mean() / dv.std() * np.sqrt(252)), 2), max_dd=round(float((np.maximum.accumulate(eq) - eq).max())),
                ret_dd=round(float(dv.mean() * 252 / (np.maximum.accumulate(eq) - eq).max()), 2),
                longest_dd_days=ld, dd_ongoing_at_end=ongoing, worst_month=round(float(mo.min())), worst_month_id=str(mo.idxmin()),
                losing_months=int((mo < 0).sum()), months=int(len(mo)), worst_20d=round(float(d.rolling(20).sum().min())),
                worst_day=round(float(dv.min())), top_module=str(cnt.index[0]), top_module_trade_pct=round(100 * float(cnt.iloc[0]) / n, 1),
                top_pnl_module=str(net.idxmax()), top_pnl_module_pct=round(100 * float(net.max() / x.sum()), 1), days=int(len(days)))


def norm_metrics(X):
    x = (X.u * X.w).to_numpy()
    if len(x) == 0: return dict(n=0)
    l = -x[x <= 0].sum()
    return dict(n=int(len(x)), wr=round(100 * float((X.u > 0).mean()), 1), pf=round(float(x[x > 0].sum() / l), 3) if l > 0 else None,
                mean_pct_atr=round(float(x.mean()), 3))


def funded(dv, dates):
    """EOD trailing $2,000 (locks at +100), per start day: bust day offset, +3,000 day offset (np.inf = not reached)."""
    N = len(dv); bust = np.full(N, np.inf); tgt = np.full(N, np.inf)
    for s in range(N):
        b = np.cumsum(dv[s:]); pk = np.maximum.accumulate(np.maximum(b, 0.0)); thr = np.minimum(pk - 2000.0, 100.0)
        br = np.nonzero(b <= thr)[0]; tg = np.nonzero(b >= 3000.0)[0]
        if len(br): bust[s] = br[0]
        if len(tg): tgt[s] = tg[0]
    out = {}
    for lab, m in (("all", np.ones(N, bool)), ("2020-2023", dates < 20240101), ("2024-2026", dates >= 20240101)):
        idx = np.nonzero(m)[0]; rem = N - idx                                   # days available incl. the start day
        r = {}
        for h in (21, 63):
            ok = rem >= h; r[f"p_bust_{h}d"] = round(100 * float((bust[idx][ok] < h).mean()), 1); r[f"n_starts_{h}d"] = int(ok.sum())
        b = bust[idx]; t = tgt[idx]; res = np.isfinite(b) | np.isfinite(t)
        win = t[res] < b[res]
        r["p_reach_3k_first"] = round(100 * float(win.mean()), 1); r["n_resolved"] = int(res.sum())
        r["censored_pct"] = round(100 * float(1 - res.mean()), 1)
        r["median_days_to_3k"] = float(np.median(t[res][win] + 1)) if win.any() else None
        r["p_bust_ever"] = round(100 * float(np.isfinite(b).mean()), 1)
        out[lab] = r
    return out


def dominance(rows, keys_hi, keys_lo):
    """profile -> list of profiles that are at least as good on every key and strictly better on one."""
    out = {}
    for a, ra in rows.items():
        dom = []
        for b, rb in rows.items():
            if a == b: continue
            ge = all(rb[k] >= ra[k] for k in keys_hi) and all(rb[k] <= ra[k] for k in keys_lo)
            gt = any(rb[k] > ra[k] for k in keys_hi) or any(rb[k] < ra[k] for k in keys_lo)
            if ge and gt: dom.append(b)
        out[a] = dom
    return out


NT_NOW = ["MaxSharpe_now", "WinRate70_now", "MaxPlus_now", "MaxPlus2_now", "Core_now", "Ultra", "UltraLean", "WR70Plus", "Estable"]
HI_ALL = ["pf", "wr", "sharpe", "per_month", "worst_20d", "worst_month", "p_reach_3k_first"]; LO_ALL = ["max_dd", "longest_dd_days", "p_bust_63d"]
HI_RA = ["pf", "sharpe", "per_month", "p_reach_3k_first"]; LO_RA = ["max_dd", "p_bust_63d"]


def add_dominance(OUT):
    """dominance among all versions (main + supplementary) and among the profiles as they run in today's NQMaster.cs (NT_NOW),
    full period and per period (funded starts of the same period)."""
    def flat(prof, per="2020-2026", fl="all"):
        r = OUT["profiles"][prof]["real"][per]; f = OUT["profiles"][prof]["funded"][fl]
        return dict(pf=r["pf"], wr=r["wr"], sharpe=r["sharpe"], per_month=r["per_month"], worst_20d=r["worst_20d"], worst_month=r["worst_month"],
                    max_dd=r["max_dd"], longest_dd_days=r["longest_dd_days"], p_bust_63d=f["p_bust_63d"], p_reach_3k_first=f["p_reach_3k_first"])
    OUT["dominance"] = {}
    for tag, profs in (("", MAIN + SUPP), ("nt_now_", NT_NOW)):
        for per, fl in (("2020-2026", "all"), ("2020-2023", "2020-2023"), ("2024-2026", "2024-2026")):
            rows = {p: flat(p, per, fl) for p in profs}; sfx = "" if per == "2020-2026" else "_" + per
            OUT["dominance"][f"{tag}risk_adjusted{sfx}"] = dict(hi=HI_RA, lo=LO_RA, profiles=profs, dominated_by=dominance(rows, HI_RA, LO_RA))
            if per == "2020-2026":
                OUT["dominance"][f"{tag}all_metrics"] = dict(hi=HI_ALL, lo=LO_ALL, profiles=profs, dominated_by=dominance(rows, HI_ALL, LO_ALL))
    return OUT


# ------------------------------------------------------------------------------------------------ markdown report
def _f(v, k=0, pct=False):
    if v is None: return "-"
    if isinstance(v, str): return v
    return (f"{v:,.{k}f}" + ("%" if pct else "")).replace(",", " ") if k == 0 else f"{v:.{k}f}" + ("%" if pct else "")


def real_table(OUT, profs, per, fl):
    h = ("| Profile | Date | Tr/day | WR % | PF | Avg $ | $/mo | Sharpe | Max DD $ | Ret/DD | Longest DD (d) | Worst month $ | Losing mo | "
         "Worst 20d $ | Top module (% trades) | P(bust 21d) | P(bust 63d) | P(+3k first) | Days to +3k |")
    L = [h, "|" + "|".join(["---"] * (h.count("|") - 1)) + "|"]
    for p in profs:
        R = OUT["profiles"][p]; r = R["real"][per]; f = R["funded"][fl]
        L.append(f"| {p} | {R['date']} | {r['tpd']:.2f} | {r['wr']:.1f} | {r['pf']:.2f} | {r['avg_trade']:.1f} | {_f(r['per_month'])} | {r['sharpe']:.2f} | "
                 f"{_f(r['max_dd'])} | {r['per_month'] * 12 / r['max_dd']:.1f} | {r['longest_dd_days']} | {_f(r['worst_month'])} | {r['losing_months']}/{r['months']} | {_f(r['worst_20d'])} | "
                 f"{r['top_module']} {r['top_module_trade_pct']:.0f}% | {f['p_bust_21d']:.1f}% | {f['p_bust_63d']:.1f}% | {f['p_reach_3k_first']:.1f}% | "
                 f"{_f(f['median_days_to_3k'])} |")
    return "\n".join(L)


def norm_table(OUT, profs):
    L = ["| Profile | 2010-14 PF | 2010-14 WR | 2015-19 PF | 2015-19 WR | 2020-23 PF | 2024-26 PF |", "|---|---|---|---|---|---|---|"]
    for p in profs:
        n = OUT["profiles"][p]["norm"]
        L.append(f"| {p} | {_f(n['2010-2014'].get('pf'), 2)} | {_f(n['2010-2014'].get('wr'), 1)} | {_f(n['2015-2019'].get('pf'), 2)} | "
                 f"{_f(n['2015-2019'].get('wr'), 1)} | {_f(n['2020-2023'].get('pf'), 2)} | {_f(n['2024-2026'].get('pf'), 2)} |")
    return "\n".join(L)


def spec_table(OUT, profs):
    L = ["| Profile | Date | Modules | Overrides / agreement | Rules | Note |", "|---|---|---|---|---|---|"]
    for p in profs:
        R = OUT["profiles"][p]
        ov = ", ".join(R["overrides"]) + ((" / agr " + ", ".join(R["agreement"])) if R["agreement"] else "")
        rl = {"none": "conflict only", "conf": "confluence", "full": "confluence + 12 context"}[R["rules"]]
        if not R["boosts"]: rl += ", boosts off"
        elif R["ict_weight"] == 1.0: rl += ", ICT x1"
        L.append(f"| {p} | {R['date']} | {len(R['modules'])}: {' '.join(R['modules'])} | {ov or '-'} | {rl} | {R['note']} |")
    return "\n".join(L)


def render_md(OUT, path):
    prev = open(path).read() if os.path.exists(path) else ""
    a0, a1 = "<!-- analysis -->", "<!-- /analysis -->"
    analysis = prev[prev.index(a0):prev.index(a1) + len(a1)] if a0 in prev and a1 in prev else a0 + "\n(analysis pending)\n" + a1
    S_ = []
    S_.append("# NQMaster: every profile version on the same real futures data\n")
    m = OUT["meta"]
    S_.append(f"Data {m['data']} (Databento NQ 1m, back-adjusted). Real view {m['real_window'][0]}..{m['real_window'][1]}: {m['cost']}; "
              f"size multipliers as each profile had them (ICT x2, confluence/context x2, cap 2x); FOMC days skipped; "
              f"MinAtrPoints 150 (no trading on days with daily ATR < 150: ~15% of 2020 and ~7% of 2021 days); day set = {m['day_set']}. "
              f"Funded risk: {m['funded']}; one account started on every trading day. Norm view: {m['norm_cost']}. Skipped: {m['skipped']}. "
              "Script: research/mine/hist_profiles.py; data: hist_profiles.json, hist_profiles_trades.pkl.\n")
    S_.append(analysis + "\n")
    S_.append("## Full period 2020-01 .. 2026-10 (real view; funded starts 2020-26)\n"); S_.append(real_table(OUT, MAIN, "2020-2026", "all") + "\n")
    S_.append("## 2020-2023 (real futures; this is where most modules were chosen, on CFD data)\n"); S_.append(real_table(OUT, MAIN, "2020-2023", "2020-2023") + "\n")
    S_.append("## 2024-2026 (real futures; funded starts 2024-26)\n"); S_.append(real_table(OUT, MAIN, "2024-2026", "2024-2026") + "\n")
    S_.append("## Regime robustness: cost-normalised view (cost 0.345% of ATR, P&L in % of ATR, no ATR guard)\n"); S_.append(norm_table(OUT, MAIN) + "\n")
    S_.append("## The old NT profiles as they run in today's NQMaster.cs (ORB prior-close rule applies to every profile)\n")
    S_.append(real_table(OUT, [p for pair in zip(["MaxSharpe", "WinRate70", "MaxPlus", "MaxPlus2"], SUPP) for p in pair], "2020-2026", "all") + "\n")
    S_.append(norm_table(OUT, SUPP) + "\n")
    S_.append("## Dominance (full period)\n")
    S_.append(f"Risk-adjusted set: higher better {', '.join(HI_RA)}; lower better {', '.join(LO_RA)}. All-metrics set: higher better {', '.join(HI_ALL)}; "
              f"lower better {', '.join(LO_ALL)}. A profile is dominated when another is at least as good on every metric of the set and better on at least one. "
              "Per-period sets use the funded starts of the same period.\n")
    for k, lab in (("risk_adjusted", "All versions, risk-adjusted set, 2020-26"), ("all_metrics", "All versions, all metrics, 2020-26"),
                   ("risk_adjusted_2020-2023", "All versions, risk-adjusted set, 2020-23"), ("risk_adjusted_2024-2026", "All versions, risk-adjusted set, 2024-26"),
                   ("nt_now_risk_adjusted", "Profiles as coded today (" + ", ".join(NT_NOW) + "), risk-adjusted set, 2020-26"),
                   ("nt_now_all_metrics", "Profiles as coded today, all metrics, 2020-26"),
                   ("nt_now_risk_adjusted_2020-2023", "Profiles as coded today, risk-adjusted set, 2020-23"),
                   ("nt_now_risk_adjusted_2024-2026", "Profiles as coded today, risk-adjusted set, 2024-26")):
        dm = OUT["dominance"][k]
        S_.append(f"**{lab}**\n")
        rows = [f"- {p}: dominated by {', '.join(v)}" for p, v in dm["dominated_by"].items() if v]
        S_.append("\n".join(rows) if rows else "- none")
        S_.append("")
    S_.append("## Per-module contribution, full period ($/month per base contract, PF)\n")
    mods = sorted({md for p in MAIN for md in OUT["profiles"][p]["by_module"]})
    L = ["| Module | " + " | ".join(MAIN) + " |", "|---|" + "|".join(["---"] * len(MAIN)) + "|"]
    for md in mods:
        cells = []
        for p in MAIN:
            b = OUT["profiles"][p]["by_module"].get(md)
            cells.append(f"{b['per_month']} ({_f(b['pf'], 2)})" if b else "")
        L.append(f"| {md} | " + " | ".join(cells) + " |")
    S_.append("\n".join(L) + "\n")
    S_.append("## Profile definitions\n"); S_.append(spec_table(OUT, MAIN + SUPP) + "\n")
    S_.append("## Sanity check vs db_long.json\n")
    for p, rec in OUT["sanity"].items():
        S_.append(f"- {p}: trades identical to db_long_trades.pkl = {rec['trades_identical']}; db_long.json blocks matched: "
                  + ", ".join(f"{k} {'yes' if v['match'] else 'NO ' + str(v['diffs'])}" for k, v in rec.items() if isinstance(v, dict)))
    open(path, "w").write("\n".join(S_) + "\n")


if __name__ == "__main__" and "--md" in sys.argv:
    _O = add_dominance(json.load(open(os.path.join(HERE, "hist_profiles.json"))))
    json.dump(_O, open(os.path.join(HERE, "hist_profiles.json"), "w"), indent=1, default=float)
    render_md(_O, os.path.join(HERE, "hist_profiles.md")); sys.exit(0)

if __name__ == "__main__":
    t0 = time.time()
    E = DL.entries_db(); wrq_port.entries()[NAME] = E
    D0 = getD(NAME)
    wrq_combo.FT[NAME] = pd.DataFrame({"tso": (D0.sm[E.fi.to_numpy()] - S(930)).astype(float)}, index=E.index)   # VTSO filter
    D = getD(NAME); fomc = set(NEWS["FOMC"]) | set(DL.FOMC_1019)
    alld_all = np.array(sorted(set(D.daydate)))
    alld_all = alld_all[~np.isin(alld_all, list(fomc))]
    days_db = np.array(sorted(set(D.daydate[(D.ro >= 0)]))); days_db = days_db[(days_db >= 20100607) & ~np.isin(days_db, list(fomc))]

    cache = {}; TR = {}; OUT = {"meta": dict(data=NAME, real_window=[LO, HI], min_atr=MIN_ATR, cost="$1.90 RT + 1 tick per side, $ per 1 MNQ base contract",
                                            norm_cost="0.345% of daily ATR, P&L in % of ATR",
                                            funded="EOD trailing $2,000, lock at start+100, breach EOD balance <= threshold; target +$3,000 EOD",
                                            day_set="all session dates in the window minus FOMC; ATR<150 days = 0 P&L",
                                            skipped="MaxTrades (MOM1130 / RSI2 entries not available on nqdb)"),
                                  "profiles": {}, "sanity": {}}
    for prof in MAIN + SUPP:
        spec = P[prof]
        Xr = build("DB", spec, cache); Xn = build("DB_N", spec, cache); TR[prof] = (Xr, Xn)
        print(f"{prof:15s} real {len(Xr):6d} norm {len(Xn):6d}  {time.time() - t0:6.0f}s", flush=True)

    # ---- sanity: rebuild of Ultra / UltraLean / WR70Plus vs db_long.json (same day sets and stats function as db_long.py)
    J = json.load(open(os.path.join(HERE, "db_long.json")))
    for prof in ("Ultra", "UltraLean", "WR70Plus"):
        Xr, Xn = TR[prof]; Xg = Xr[Xr.atr >= MIN_ATR]; rec = {}
        for lab, lo, hi in (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019), ("2020-2023", 2020, 2023), ("2024-2026", 2024, 2026)):
            dd = days_db[(days_db // 10000 >= lo) & (days_db // 10000 <= hi)]
            k = lambda X: X[(X.date // 10000 >= lo) & (X.date // 10000 <= hi)]
            mine = dict(real_min_atr=DL.stats(k(Xg), dd), norm=DL.stats(k(Xn), dd, True))
            ref = {v: J["profiles"][prof][lab][v] for v in ("real_min_atr", "norm")}
            diffs = {v: {m: (mine[v][m], ref[v][m]) for m in mine[v] if mine[v][m] != ref[v][m]} for v in mine}
            rec[lab] = dict(match=all(len(x) == 0 for x in diffs.values()), diffs=diffs)
        ref_tr = pickle.load(open(os.path.join(HERE, "db_long_trades.pkl"), "rb"))[prof]
        rec["trades_identical"] = bool(len(ref_tr[0]) == len(Xr) and np.allclose((ref_tr[0].u * ref_tr[0].w).to_numpy(), (Xr.u * Xr.w).to_numpy())
                                       and len(ref_tr[1]) == len(Xn) and np.allclose((ref_tr[1].u * ref_tr[1].w).to_numpy(), (Xn.u * Xn.w).to_numpy()))
        OUT["sanity"][prof] = rec
        print("sanity", prof, rec["trades_identical"], {k: v["match"] for k, v in rec.items() if isinstance(v, dict)}, flush=True)

    # ---- metrics
    for prof in MAIN + SUPP:
        spec = P[prof]; Xr, Xn = TR[prof]
        rec = dict(date=spec[6], note=spec[7], modules=list(spec[0]), overrides=sorted(spec[1]), agreement=list(spec[2]), rules=spec[3],
                   boosts=spec[4], ict_weight=spec[5] if spec[4] else 1.0, real={}, norm={}, funded={}, by_module={})
        Xg = Xr[(Xr.atr >= MIN_ATR) & (Xr.date >= LO) & (Xr.date <= HI)]
        for lab, (lo, hi) in PERIODS.items():
            days = alld_all[(alld_all >= lo) & (alld_all <= hi)]
            rec["real"][lab] = real_metrics(Xg[(Xg.date >= lo) & (Xg.date <= hi)], days)
        for lab, (lo, hi) in NPERIODS.items():
            rec["norm"][lab] = norm_metrics(Xn[(Xn.date >= lo) & (Xn.date <= hi)])
        days = alld_all[(alld_all >= LO) & (alld_all <= HI)]
        dv = pd.Series((Xg.u * Xg.w).to_numpy(), index=Xg.date.to_numpy()).groupby(level=0).sum().reindex(days, fill_value=0.0).to_numpy()
        rec["funded"] = funded(dv, days)
        nd = len(days)
        for m, g in Xg.groupby("mod"):
            x = (g.u * g.w).to_numpy(); l = -x[x <= 0].sum()
            rec["by_module"][m] = dict(n=int(len(x)), wr=round(100 * float((g.u > 0).mean()), 1), pf=round(float(x[x > 0].sum() / l), 2) if l > 0 else None,
                                       per_month=round(float(x.sum() / nd * 21)))
        OUT["profiles"][prof] = rec
        r = rec["real"]["2020-2026"]; f = rec["funded"]["all"]
        print(f"{prof:15s} tpd {r['tpd']:.2f} WR {r['wr']:.1f} PF {r['pf']:.3f} $/mo {r['per_month']:5d} Sh {r['sharpe']:.2f} DD {r['max_dd']:5d} "
              f"bust63 {f['p_bust_63d']:.1f} reach3k {f['p_reach_3k_first']:.1f}", flush=True)

    add_dominance(OUT)
    pickle.dump(TR, open(os.path.join(HERE, "hist_profiles_trades.pkl"), "wb"))
    json.dump(OUT, open(os.path.join(HERE, "hist_profiles.json"), "w"), indent=1, default=float)
    render_md(json.loads(json.dumps(OUT, default=float)), os.path.join(HERE, "hist_profiles.md"))
    print("done", round(time.time() - t0), "s")
