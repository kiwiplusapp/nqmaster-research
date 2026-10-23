"""perturb_report: tables of perturb_lab.json -> perturb_report.md (methods, per-module table, OAT summary, fragility ranking,
walk-forward tests, whole-system sensitivity, slippage). The conclusion / action list is written by hand at the end of the file."""
import os, sys, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import perturb_lib as P
J = json.load(open(os.path.join(HERE, "perturb_lab.json")))
B = J["base"]; M = J["modules"]; L = []
f = lambda x, d=2: ("n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else (f"{x:.{d}f}" if isinstance(x, (int, float)) else str(x)))


def table(rows, cols):
    L.append("| " + " | ".join(cols) + " |"); L.append("|" + "---|" * len(cols))
    for r in rows: L.append("| " + " | ".join(str(x) for x in r) + " |")
    L.append("")


L.append("# Parameter-perturbation robustness audit of the 2027 NQMaster default (2026-10-19)\n")
L.append("Trade set audited: `nt_compare --set ultra_d4` (Ultra + SO04 / RV11 / ORFAIL / CAM3; MOM1030 and CPI09 x4, ICT x2, confluence and "
         "context rules, MinATR 150). Rebuilt here from every module's ORIGINAL signal code on real Databento NQ 2010-06..2026-10 "
         "(`perturb_lib.py`); the rebuild reproduces the committed set row for row (3,895 / 3,897 keys in 2020-10..2023 and 3,359 / 3,360 in "
         "2024-26; the 3 missing rows are CPI09 trades on FOMC/CPI overlap days, u and w identical on every matched row).\n")
L.append("## Methods\n")
L.append("* Periods: A 2010-14 and B 2015-19 cost-normalised (cost 0.345 % of the daily ATR, P&L in % of ATR, no MinATR), T1 2020-23 and T2 2024-26 real $ per MNQ ($1.90 + 1 tick per side, MinATR 150). FOMC days excluded everywhere.")
L.append("* Per module 3-5 key parameters (`perturb_lib.SPEC`): anchor / entry time, threshold x ATR, stop fraction, target R, window / lookback. Three perturbation designs:")
L.append("  * one-at-a-time (OAT): -20 / -10 / +10 / +20 % (clock parameters -30 / -15 / +15 / +30 min; integer parameters rounded);")
L.append("  * a 5^3 factorial of the first three parameters (same steps) for the plateau search;")
L.append(f"  * {M[P.MODS[0]]['n_draws']} random joint draws per module (every parameter at once, uniform +-20 % / +-30 min, seeded per module and draw).")
L.append("* Every cell is re-simulated through the same pipeline as the live set (exit engine, 0.10 ATR minimum stop on structure modules, ORB prior-close trigger, VOLB break-even, MOM1030/MOM13 agreement, confluence A/B, pruned context rules, conflict filter) and evaluated (i) standalone and (ii) inside the portfolio with only that module replaced. MSEQS keeps the base ORB60 short fills as its gate in every cell.")
L.append(f"* Whole-system sensitivity: {J['system']['n_draws']} draws with EVERY module at its draw j simultaneously; slippage +1 / +2 / +4 ticks per side on the base.")
L.append("* Pre-registered scores: frag_IS = mean(share of draws with module PF < 1 in A, in B, in T1; share with portfolio T1 Sharpe > 0.1 below base) -> drop ranking. frag_T2 (T2 PF < 1 share, T2 portfolio Sharpe drop share) is reported, never used to choose. Plateau centre = factorial cell with the highest minimum T1 PF over its 3x3x3 neighbourhood (cells with T1 n < 20 excluded). Smoothing = 3 best centres at 1/3 lot each.")
L.append("* Acceptance of any change (fixed before looking): T2 Sharpe not lower, T2 maxDD not higher by > 5 %, T2 PF and WR not lower, trade count not lower by > 5 %.\n")
L.append("## Base portfolio (2027 default, 1 base contract)\n")
table([[per, B[f"{per}_n"], f(B[f"{per}_tpd"]), f(B[f"{per}_wr"], 1), f(B[f"{per}_pf"], 3), f(B[f"{per}_sharpe"], 2), f(B[f"{per}_maxdd"], 0), f(B[f"{per}_net"], 0), f(B[f"{per}_worst_month"], 0)] for per in ("A", "B", "T1", "T2")],
      ["period", "trades", "tr/day", "WR %", "PF", "Sharpe", "maxDD", "net", "worst month"])
L.append("A / B in % of ATR per contract (cost-normalised), T1 / T2 in $ per MNQ.\n")
L.append("## Per-module perturbation table (200 joint draws per module)\n")
rows = []
for mod in P.MODS:
    m = M[mod]; d = m["draws"]; b = m["base"]
    rows.append([mod, f"{b['A']['pf']:.2f}/{b['B']['pf']:.2f}/{b['T1']['pf']:.2f}/{b['T2']['pf']:.2f}", b["T1"]["n"], b["T2"]["n"],
                 f"{d['A']['pf_median']:.2f} ({d['A']['pf_p10']:.2f})", f"{d['B']['pf_median']:.2f} ({d['B']['pf_p10']:.2f})",
                 f"{d['T1']['pf_median']:.2f} ({d['T1']['pf_p10']:.2f})", f"{d['T2']['pf_median']:.2f} ({d['T2']['pf_p10']:.2f})",
                 f"{100*d['A']['share_pf_lt_1']:.0f}/{100*d['B']['share_pf_lt_1']:.0f}/{100*d['T1']['share_pf_lt_1']:.0f}/{100*d['T2']['share_pf_lt_1']:.0f}",
                 f"{100*d['T1']['port_sharpe_drop_gt_0p1']:.0f}/{100*d['T2']['port_sharpe_drop_gt_0p1']:.0f}", f"{m['frag_IS']:.2f}", f"{m['frag_T2']:.2f}"])
table(rows, ["module", "base PF A/B/T1/T2", "n T1", "n T2", "A PF med (p10)", "B PF med (p10)", "T1 PF med (p10)", "T2 PF med (p10)", "% draws PF<1 A/B/T1/T2", "% draws port Sharpe -0.1 T1/T2", "frag_IS", "frag_T2"])
L.append("## One-at-a-time sensitivity (standalone PF range over the 4 levels; portfolio T2 Sharpe change range)\n")
rows = []
for mod in P.MODS:
    o = pd.DataFrame(M[mod]["oat"])
    if not len(o): continue
    for prm, g in o.groupby("param", sort=False):
        kind = P.SPEC[mod]["pert"][prm]; base = P.SPEC[mod]["base"][prm]
        worst = g.loc[g.T1_pf.idxmin()]
        rows.append([mod, f"{prm} ({kind}, base {base})", f"{g.T1_pf.min():.2f}..{g.T1_pf.max():.2f}", f"{g.T2_pf.min():.2f}..{g.T2_pf.max():.2f}",
                     f"{g.A_pf.min():.2f}..{g.A_pf.max():.2f}", f"{g.B_pf.min():.2f}..{g.B_pf.max():.2f}", f"{g.port_T1_dsharpe.min():+.2f}..{g.port_T1_dsharpe.max():+.2f}",
                     f"{g.port_T2_dsharpe.min():+.2f}..{g.port_T2_dsharpe.max():+.2f}", f"{worst.level:+g} (T1 PF {worst.T1_pf:.2f})"])
table(rows, ["module", "parameter", "T1 PF range", "T2 PF range", "A PF range", "B PF range", "port dSharpe T1", "port dSharpe T2", "worst level (T1)"])
L.append("## Fragility ranking (frag_IS, pre-registered; frag_T2 for information)\n")
table([[i + 1, r["mod"], f"{r['frag_IS']:.3f}", f"{r['frag_IS_rel']:.3f}", f"{r['frag_T2']:.3f}", M[r["mod"]]["plateau"]["base_rank"], M[r["mod"]]["plateau"]["n_candidates"],
        "base" if M[r["mod"]]["plateau"]["centre"] and M[r["mod"]]["plateau"]["centre"]["is_base"] else (json.dumps(M[r["mod"]]["plateau"]["centre"]["eps"]) if M[r["mod"]]["plateau"]["centre"] else "n/a"),
        f"{M[r['mod']]['plateau']['base_cell_min_T1_pf']:.2f}", f"{M[r['mod']]['plateau']['centre']['min_T1_pf']:.2f}" if M[r["mod"]]["plateau"]["centre"] else "n/a",
        f"{M[r['mod']]['plateau']['centre']['T2_pf']:.2f} vs {M[r['mod']]['base']['T2']['pf']:.2f}" if M[r["mod"]]["plateau"]["centre"] else "n/a"]
       for i, r in enumerate(J["ranking"])],
      ["rank", "module", "frag_IS", "frag_IS (relative, PF < 0.9 x base)", "frag_T2", "base cell rank among plateau candidates", "candidates", "plateau centre (eps)", "min T1 PF around base", "min T1 PF around centre", "centre T2 PF vs base"])
L.append("## Walk-forward tests (decided on T1 / A / B, evaluated on T2)\n")
W = J["walk_forward"]; keys = ["T1_sharpe", "T2_sharpe", "T2_pf", "T2_wr", "T2_maxdd", "T2_n", "T2_net", "A_sharpe", "B_sharpe"]
def wrow(lab, m, note=""):
    return [lab, note] + [f(m[k], 3 if k.endswith(("sharpe", "pf")) else (1 if k.endswith("wr") else 0)) for k in keys] + [m.get("accepted", m.get("accepted_ex_n", ""))]
rows = [wrow("base", W["base"])]
for k in (1, 2, 3): rows.append(wrow(f"drop {k} most fragile", W[f"drop_{k}"], ", ".join(W[f"drop_{k}"]["dropped"])))
rows.append(wrow("plateau centre, top-3 fragile", W["plateau_top3_fragile"], ", ".join(W["plateau_top3_fragile"]["modules"]) or "none changed"))
rows.append(wrow("plateau centre, all changed modules", W["plateau_all_changed"], f"{len(W['plateau_all_changed']['modules'])} modules"))
rows.append(wrow("smoothing (3 centres x 1/3 lot), top-3 fragile", W["smooth_top3_fragile"], ", ".join(W["smooth_top3_fragile"]["modules"])))
rows.append(wrow("smoothing, all modules", W["smooth_all"], "fractional lots: diversification idea only"))
table(rows, ["test", "modules", "T1 Sharpe", "T2 Sharpe", "T2 PF", "T2 WR", "T2 maxDD", "T2 trades", "T2 net", "A Sharpe", "B Sharpe", "accepted"])
if W["plateau_each"]:
    L.append("Plateau centre applied one module at a time (modules whose T1 plateau centre is not the base cell):\n")
    table([[mod, json.dumps(M[mod]["plateau"]["centre"]["eps"]), f"{M[mod]['base']['T1']['pf']:.2f} -> {M[mod]['plateau']['centre']['T1_pf']:.2f}", f"{M[mod]['base']['T2']['pf']:.2f} -> {M[mod]['plateau']['centre']['T2_pf']:.2f}",
            f"{m['T1_sharpe'] - B['T1_sharpe']:+.3f}", f"{m['T2_sharpe'] - B['T2_sharpe']:+.3f}", f"{m['T2_pf'] - B['T2_pf']:+.3f}", f"{m['T2_maxdd'] - B['T2_maxdd']:+.0f}", m["accepted"]]
           for mod, m in W["plateau_each"].items()], ["module", "centre eps", "module T1 PF", "module T2 PF", "port dSharpe T1", "port dSharpe T2", "port dPF T2", "port dmaxDD T2", "accepted"])
L.append("## Whole-system sensitivity (every module perturbed at once, 200 draws)\n")
S = J["system"]; rows = []
for per in ("A", "B", "T1", "T2"):
    s = S[per]
    for k in ("sharpe", "pf", "wr", "maxdd", "net", "n"):
        rows.append([per, k, f(s[k]["base"], 3), f(s[k]["median"], 3), f(s[k]["p10"], 3), f(s[k]["p90"], 3), f(s[k]["min"], 3), f(s[k]["max"], 3)])
table(rows, ["period", "metric", "base", "median", "p10", "p90", "min", "max"])
table([[per, f"{100*S[per]['share_sharpe_below_base']:.0f} %", f"{100*S[per]['share_sharpe_drop_gt_0p1']:.0f} %", f"{100*S[per]['share_pf_lt_1']:.0f} %"] for per in ("A", "B", "T1", "T2")],
      ["period", "draws with Sharpe below base", "draws with Sharpe > 0.1 below base", "draws with PF < 1"])
L.append(f"Correlation across the 200 whole-system draws between T1 and T2 Sharpe: {S['corr_T1_T2_sharpe_across_draws']}; between T1 and T2 PF: {S['corr_T1_T2_pf_across_draws']}.\n")
L.append("## Slippage (base set, real views)\n")
rows = [["base (1 tick)"] + [f(B[k], 3 if k.endswith(("sharpe", "pf")) else 0) for k in ("T1_sharpe", "T1_pf", "T1_net", "T2_sharpe", "T2_pf", "T2_net", "T2_maxdd")]]
for lab, m in J["slippage"].items(): rows.append([lab + " per side"] + [f(m[k], 3 if k.endswith(("sharpe", "pf")) else 0) for k in ("T1_sharpe", "T1_pf", "T1_net", "T2_sharpe", "T2_pf", "T2_net", "T2_maxdd")])
table(rows, ["slippage", "T1 Sharpe", "T1 PF", "T1 net", "T2 Sharpe", "T2 PF", "T2 net", "T2 maxDD"])
open(os.path.join(HERE, "perturb_report.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))

CONCLUSION = """
## Honest conclusion

1. **The exact parameter cells are a sharp optimum in 2020-26 and an ordinary cell in 2010-19.** With every parameter of every module
   perturbed at once (+-20 % / +-30 min, 200 draws) the portfolio stays profitable in all 200 draws, but T1 Sharpe falls from 3.68 to a
   median 2.49 (p10 2.10) and T2 from 4.07 to 2.45 (p10 1.86); PF 1.48 -> 1.30 and 1.51 -> 1.28; T2 maxDD $3.6k -> $5.6k median.
   100 % of the draws are below the base by more than 0.1 Sharpe in both T1 and T2. In A 2010-14 and B 2015-19 (never used to choose
   anything) the base cell sits near the middle of the perturbation cloud (50 % / 64 % of draws below it). That is the signature of
   parameters selected with 2020-26 in view: the base cell "knows" 2020-26, not 2010-19. The correlation across draws between T1 and
   T2 Sharpe is 0.07: which perturbation hurts is not predictable from 2020-23.
2. **The fragility is in the clock parameters, not in stops / targets.** Stop fractions, targets and thresholds mostly sit on plateaus
   (OAT PF ranges of a few hundredths). Moving an entry / anchor time by 15 min costs the most: CRT11 candle offset (portfolio T2 Sharpe
   -0.33..-0.71), MOM11 (-0.48), MOM1030 (-0.39), CPI09 window (-0.39), MSEQ window start (-0.28), VW13 (-0.25), ON07 (-0.24).
   This is a real operational risk, not only a statistical one: a 15-minute clock error in NinjaTrader (session template, DST, bar
   timestamps) would remove most of the edge of the time modules.
3. **Fragility ranking (frag_IS, decided on 2010-23 only):** MOM1030 0.81, MOM13 0.50, REV06 0.50, MOM11 0.42, ON07 0.40, VW13 0.38,
   SO04 0.38, CRT11 0.37, LF0430 0.34, ICT 0.32 ... robust: ORFAIL 0.02, NF05 0.02, MSEQS 0.08, VOLB 0.08, ORB60 0.13, LF06 0.15,
   MSEQ 0.17, RV11 0.18. The fragile group is the time-of-day momentum family that only works since 2020 (db_long 2026-10-09).
   Modules whose standalone T2 PF falls below 1 in more than 40 % of the draws: REV06 67 %, LATE15 62 %, CAM3 56 %, LF0430 54 %,
   MSEQ 47 %, MOM1030 43 %, ON07 43 %, CRT11 40 %, VW13 40 %.
4. **None of the pre-registered changes is accepted.**
   * Dropping the 1 / 2 / 3 most fragile modules (MOM1030, MOM13, REV06): T2 Sharpe 4.03 / 3.99 / 4.03 vs 4.07, PF 1.50 / 1.50 / 1.52,
     maxDD +16 % / 0 % / +5 %, net -6 % / -11 % / -12 %, trades -3 / -8 / -15 %. T1 maxDD falls from $4.7k to $3.9k / $3.2k / $3.0k and
     A / B Sharpe rise (drop 3: 0.62 -> 0.68, 1.31 -> 1.32). A robustness / drawdown trade-off, not an improvement: keep as the
     defensive variant (see actions).
   * Re-centring every module on the centre of its T1 plateau: worse everywhere (top-3 fragile: T2 Sharpe 3.72; all 23 modules: 3.22,
     PF 1.40, maxDD +35 %). Applied one module at a time, 4 of 23 centres pass the acceptance test (MOM11, ICT, RV11, CPI09) = chance.
   * Parameter smoothing (3 best plateau cells at 1/3 lot): T2 Sharpe 3.72 (top-3) / 3.08 (all). Rejected; fractional lots are not
     available anyway.
   The exact cells are also the best cells in T2, so "widening" them cannot help in-sample or out-of-sample; what it shows is how
   much of the 2020-26 result depends on the exact minute and threshold choices.
5. **Slippage is not the problem:** +1 / +2 / +4 ticks per side -> T2 Sharpe 3.94 / 3.82 / 3.59, PF 1.49 / 1.47 / 1.43, net
   $87.6k -> $84.8k / $82.1k / $77.0k per contract.

## Recommended 2027 action list

1. **Do not change any parameter.** No plateau re-centring, no smoothing, no drop. The 2027 default stays as is.
2. **Plan with the perturbation cloud, not with the base cell:** per base contract expect Sharpe ~2.5 (p10 ~1.9), PF ~1.3, maxDD
   ~$5.6k (p90 of the T2 draws: see table) instead of 4.1 / 1.51 / $3.6k. This matches the 35 % haircut already used in the account
   simulations; the cloud says ~40 % on Sharpe and +55 % on drawdown. Size accounts for that level.
3. **Verify the clock in NinjaTrader before going live and after every DST change** (bar timestamps of the 11:00 / 10:30 / 13:00 /
   12:00 CRT / 09:30 CPI bars on the chart vs the exchange clock; ModuleHealthReport per module). A 15-minute error silently removes
   most of the time-module edge.
4. **Defensive variant if the edge monitor warns or the January review flags the time modules:** DisableModules = MOM1030,MOM13,REV06
   (T2 Sharpe 4.03, PF 1.52, T1/T2 maxDD $3.0k / $3.7k, -12 % net). It loses little and removes the three most parameter-fragile modules.
5. **January 2027 review watch list** (standalone T2 PF < 1 in > 40 % of the draws): REV06 (already on the list), LATE15, CAM3, LF0430,
   MSEQ, MOM1030, ON07, CRT11, VW13. Review them with the yearly rule (robust16), not with this table alone.
6. Treat this audit as evidence that the 2020-26 Sharpe is partly selection: any future "improvement" that changes a time or threshold
   must beat the base on 2010-19 cost-normalised data as well as T2, otherwise it only moves the cell inside the same cloud.

Files: `perturb_lib.py` (simulators + assembly), `perturb_lab.py` (7,762 cells, 2 processes, 44 min), `perturb_cells.csv`,
`perturb_analysis.py` -> `perturb_lab.json`, `perturb_report.py` -> this file. Module trades per cell in the session scratchpad (not committed).
"""
open(os.path.join(HERE, "perturb_report.md"), "a").write(CONCLUSION)
