"""slip_model.py (2026-10-26, experiment 01 / frente 5A, docs/PLAN_2026-10-26.md H5): real slippage per module x ET band.
Inputs: trade exports of the accounts that ran NQMaster live (Control Center > Trades > filter the account > Export; one file per
account, prop-firm sims on Rithmic / Tradovate = main source; Sim101 / Playback = backup, always reported apart) and the Strategy
Analyzer export (FillSeries Off, Standard, same code, same period) as the reference. Each real trade is paired with the Standard
trade of the same date, module and direction (entry minute within --tol). The order level is inferred from the Standard fill:
  stop-market entries (ORB60 / ORB90 / VOLB / ENG10): level = Standard fill - 1 tick (Standard adds the 1-tick slippage) *
  market entries (every other module)              : arrival price = Standard fill - 1 tick (= open of the fill bar)
  limit entries (LON / ICT)                         : limit = Standard fill (no slippage on limit fills); only the fill count matters
  stop-loss exits (both sides exited 'Stop loss')   : level = Standard exit + 1 tick; tick-offset stops move with the real entry
    (ORB, clock modules, RSI2), price stops do not (VOLB, CRT11, LON, ICT, MSEQ, MSEQS, ORFAIL, CAM3, ENG26, ENG10)
  * when Standard gapped through the level (fill at the open), the inferred level is the open: documented approximation.
Slippage in ticks is signed with the trade: + = adverse. Output per account kind (prop / sim), module and ET band: n, median, mean,
p90, share >= 2 ticks; exit-stop slippage; unmatched real trades (live entries the backtest does not take, e.g. VOLB at market).
Decision rule (pre-registered): a cell (order type x band) with n >= 15 prop trades and median entry slippage > 2 ticks replaces
the fixed 1 tick in the campaign recalculation. -> <out>.md, <out>_trades.csv, <out>.json (cell medians for the recalculation).
Usage (from research/mine):
  python3 slip_model.py --standard <SA_standard.csv> --real <acct1.csv> [--real <acct2.csv> ...] [--sim Sim101,Playback]
                        [--tz America/Argentina/Buenos_Aires] [--tol 3] [--out slip_<tag>]
Self-test: --standard X --real X must give 100% matched and slippage exactly +1.00 tick on stop / market entries and on stop exits
(the 1 tick the Standard backtest itself assumes) and 0 on limit entries; 'excess' = slippage - that backtest assumption."""
import os, sys, argparse, datetime, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from nt_trades import load_nt
from fill_gap import TICK, STOP_MODS, LIMIT_MODS, otype, band, bar_open, match

TICK_STOP_MODS = {"ORB60", "ORB90", "RSI2", "MOM11", "MOM1030", "MOM1130", "MOM13", "ON07", "REV06", "VW13", "LATE15", "LATEFH", "NF05", "LF06", "LF0430", "LF0315", "CPI09", "SO04", "RV11", "CA04V", "GD03"}
SIM_DEFAULT = ("sim101", "playback", "backtest")


def frame(path, tz):
    t = load_nt(path)
    if "Strategy" in t.columns:
        keep = t["Strategy"].str.strip().isin(["NQMaster", ""]) | t["Strategy"].isna()
        if (~keep).any(): print(f"{os.path.basename(path)}: {int((~keep).sum())} rows of other strategies dropped")
        t = t[keep]
    if "Instrument" in t.columns:
        keep = t["Instrument"].str.strip().str.upper().str.startswith(("MNQ", "NQ"))
        if (~keep).any(): print(f"{os.path.basename(path)}: {int((~keep).sum())} rows of other instruments dropped")
        t = t[keep]
    et = lambda s: s.dt.tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("America/New_York").dt.tz_localize(None)
    tin_et = et(t.tin); op = bar_open(tin_et)
    f = pd.DataFrame(dict(account=(t["Account"].str.strip().values if "Account" in t.columns else "?"),
                          date=((op + pd.Timedelta(hours=6)).dt.normalize().dt.strftime("%Y%m%d").astype(int)), mod=t["mod"].str.strip().values, d=t["d"].values,
                          qty=t.qty.values, u=(t.pnl / t.qty).values, epx=t.epx.values, xpx=t.xpx.values, xname=t.xname.str.strip().values,
                          tin=((op.dt.hour * 60 + op.dt.minute - 1080) % 1440).astype(int), mod_et=(op.dt.hour * 60 + op.dt.minute).astype(int), tin_ts=tin_et.values))
    f["otype"] = f["mod"].map(otype); f["band"] = f["mod_et"].map(band)
    return f.sort_values(["date", "tin"]).reset_index(drop=True)


def slippage(Rl, Sd):
    """Rl = real trades with k (partner in Sd). Adds entry / exit slippage in ticks (+ = adverse)."""
    m = Rl[Rl.k >= 0].copy(); s = Sd.loc[m.k.values]
    ref = np.where(m.otype == "limit", s.epx.values, s.epx.values - m.d.values * TICK)
    m["ref_entry"] = ref; m["epx_std"] = s.epx.values
    m["slip_entry"] = ((m.epx.values - ref) * m.d.values / TICK).round(2)
    m["excess_entry"] = (m.slip_entry - np.where(m.otype == "limit", 0.0, 1.0)).round(2)          # beyond the 1 tick the backtest already charges
    both_stop = (m.xname.str.lower().str.startswith("stop").values) & (s.xname.str.lower().str.startswith("stop").values)
    lvl = s.xpx.values + m.d.values * TICK
    lvl = np.where(m["mod"].isin(TICK_STOP_MODS).values, lvl + (m.epx.values - s.epx.values), lvl)
    m["slip_exit_stop"] = np.where(both_stop, ((lvl - m.xpx.values) * m.d.values / TICK).round(2), np.nan)
    m["excess_exit_stop"] = (m.slip_exit_stop - 1.0).round(2)
    m["xname_std"] = s.xname.values; m["u_std"] = s.u.values; m["d_usd"] = (m.u - s.u.values).round(2)
    return m


def cells(M, keys, col):
    rows = []
    for key, g in M.dropna(subset=[col]).groupby(keys):
        key = key if isinstance(key, tuple) else (key,); x = g[col].to_numpy(float)
        ex = g["excess_" + col.split("slip_", 1)[1]].to_numpy(float)
        rows.append(dict(**{k: v for k, v in zip(keys, key)}, n=len(x), median=round(float(np.median(x)), 2), mean=round(float(x.mean()), 2),
                         p90=round(float(np.percentile(x, 90)), 2), ge2_pct=round(100 * float((x >= 2).mean()), 1), excess_med=round(float(np.median(ex)), 2),
                         excess_mean=round(float(ex.mean()), 2), d_usd_per_trade=round(float(g.d_usd.mean()), 2)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--standard", required=True); ap.add_argument("--real", action="append", required=True)
    ap.add_argument("--sim", default="", help="comma list of account names to report as backup (Sim101 / Playback are always backup)")
    ap.add_argument("--tz", default="America/Argentina/Buenos_Aires"); ap.add_argument("--tol", type=int, default=3); ap.add_argument("--out", default=None)
    a = ap.parse_args(); out = a.out or os.path.join(HERE, f"slip_{datetime.date.today():%Y%m%d}")
    S = frame(a.standard, a.tz)
    R = pd.concat([frame(p, a.tz) for p in a.real], ignore_index=True)
    sims = tuple(x.strip().lower() for x in a.sim.split(",") if x.strip()) + SIM_DEFAULT
    R["kind"] = np.where(R.account.str.lower().map(lambda n: any(k in n for k in sims)), "sim", "prop")
    lo, hi = max(S.date.min(), R.date.min()), min(S.date.max(), R.date.max())
    S = S[(S.date >= lo) & (S.date <= hi)].reset_index(drop=True)
    pd.set_option("display.width", 250)
    L = [f"# Real slippage vs Standard backtest ({lo}-{hi}), reference {os.path.basename(a.standard)}", ""]
    allm, cellj = [], {}
    for kind in ("prop", "sim"):
        for acct, Rk in R[R.kind == kind].groupby("account"):
            Rk = Rk[(Rk.date >= lo) & (Rk.date <= hi)].reset_index(drop=True)
            if not len(Rk): continue
            Rk, Sk = match(Rk, S.copy(), a.tol); M = slippage(Rk, Sk); M["account"] = acct; M["kind"] = kind; allm.append(M)
            L.append(f"## {kind.upper()} account {acct}: {len(Rk)} real trades, {len(M)} matched ({100 * len(M) / len(Rk):.1f}%), "
                     f"{int((Rk.k < 0).sum())} without a backtest twin (${Rk[Rk.k < 0].u.sum():,.0f}); backtest trades not taken live in the period: {int((Sk.k < 0).sum())}")
            if len(M):
                L += [f"- entry slippage: median {M.slip_entry.median():+.2f} ticks, mean {M.slip_entry.mean():+.2f}, p90 {M.slip_entry.quantile(0.9):+.2f}, "
                      f">= 2 ticks {100 * (M.slip_entry >= 2).mean():.1f}%; $ per trade real - backtest {M.d_usd.mean():+.2f} (n {len(M)})"]
                ex = M.dropna(subset=["slip_exit_stop"])
                if len(ex): L.append(f"- stop-loss exit slippage (both exited by stop, n {len(ex)}): median {ex.slip_exit_stop.median():+.2f} ticks, mean {ex.slip_exit_stop.mean():+.2f}, p90 {ex.slip_exit_stop.quantile(0.9):+.2f}")
            L.append("")
    if not allm: print("\n".join(L)); sys.exit("no real trades in the reference period")
    M = pd.concat(allm, ignore_index=True)
    for kind in ("prop", "sim"):
        Mk = M[M.kind == kind]
        if not len(Mk): continue
        L += [f"## {kind.upper()} accounts pooled: entry slippage by order type and ET band (ticks, + = adverse)", "```", cells(Mk, ["otype", "band"], "slip_entry").to_string(index=False), "```",
              f"## {kind.upper()} accounts pooled: entry slippage by module", "```", cells(Mk, ["mod"], "slip_entry").to_string(index=False), "```"]
        ex = cells(Mk, ["otype", "band"], "slip_exit_stop")
        if len(ex): L += [f"## {kind.upper()} accounts pooled: stop-loss exit slippage by order type and ET band", "```", ex.to_string(index=False), "```"]
        if kind == "prop":
            c = cells(Mk, ["otype", "band"], "slip_entry"); hit = c[(c.n >= 15) & (c["median"] > 2)]
            L += ["", "## Decision (H5, prop accounts only): cells with n >= 15 and median entry slippage > 2 ticks",
                  "```", (hit.to_string(index=False) if len(hit) else "none"), "```"]
            cellj = {f"{r.otype}|{r.band}": dict(n=int(r.n), median_ticks=float(r.median), mean_ticks=float(r.mean), p90_ticks=float(r.p90), excess_median_ticks=float(r.excess_med), use=bool(r.n >= 15)) for r in c.itertuples()}
    txt = "\n".join(L) + "\n"
    open(out + ".md", "w", encoding="utf-8").write(txt); M.to_csv(out + "_trades.csv", index=False)
    json.dump(dict(reference=os.path.basename(a.standard), period=[int(lo), int(hi)], tick=TICK, prop_cells=cellj), open(out + ".json", "w"), indent=1)
    print(txt); print("->", out + ".md")
