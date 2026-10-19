"""more_trades.py (2026-10-19): 'MORE TRADES AT THE SAME QUALITY' for the 2027 default NQMaster set (nt_compare set ultra_d4 =
Ultra + SO04/RV11/ORFAIL/CAM3, opposite-position conflicts removed). Real Databento NQ (research/data/nqdb.npz), $ per MNQ incl.
$1.90 + 1 tick; T1 2020-10-15..2023-12-31 (choose), T2 2024-01.. (check, never used to choose), A 2010-14 / B 2015-19 cost-normalised
(0.345% of ATR, P&L in % of ATR) as the regime check.

PRE-REGISTERED PROTOCOL (written before any candidate was run; see PROTOCOL below). A candidate ADDITION is accepted only if ALL hold:
  standalone T1: n >= 60, PF >= 1.3, WR >= 55 ;  T2: PF >= 1.2 ;  +4 ticks ($3 per trade): T2 PF >= 1.1
  regime: cost-normalised A (2010-14) PF >= 0.95 and B (2015-19) PF >= 1.05
  plateau: every neighbouring grid cell (one step up / down on each numeric axis, other params equal) has T1 PF >= 1.15
  portfolio (candidate added to the raw base set and run through wrq_port.conflict_filter): Sharpe up in T1 AND T2, max DD and worst month
  not worse by > 5% in either period, WR of the whole set not lower by > 0.5 pt, PF of the whole set not lower by > 0.02 (both periods),
  correlation of the candidate's daily P&L with the base daily P&L < 0.3.
Workstreams: (A) second instances of the durable modules' families on OTHER signal cells (other anchor / window / threshold; cells that
only change the trend filter or the exit of an existing module's signal are the same signal and are excluded); (B) one re-arm after a
stop-out (stop order back at the original entry level, same direction, same stop and target distance, until the module's own deadline)
for NF05, LF06, LF0430, SO04, RV11, ORFAIL, CAM3, CRT11, LATE15, plus the ORFAIL family re-arm (next failed break after the stop-out);
(C) OR_FAIL on 5/10-minute ranges and the Camarilla fade at L2/H2 and L4/H4 (families10.py, mined with run_mine_db.py MINE_TAG=b10);
(D) NEW ingredient: VWAP_BAND2 (session VWAP +- k sigma, bands from bars <= t-1, lookahead-checked) mined in the same batch.
Outputs: more_trades.json, more_trades_report.md.  Usage: cd research/mine && python3 more_trades.py  (b10 mining must have finished)."""
import os, sys, json, ast, pickle, time, numpy as np, pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.dirname(HERE)
for p in (HERE, RES):
    if p not in sys.path: sys.path.insert(0, p)
from core import Data, run_events, S, TICK, SLIP
from wrq_port import conflict_filter
from news import NEWS

START, MID = 20201015, 20240101
PER_REAL = (("T1", START, MID), ("T2", MID, 20991231))
PER_NORM = (("A", 20100101, 20150101), ("B", 20150101, 20200101))
NORM = 0.00345
PROTOCOL = dict(standalone=dict(T1_n=60, T1_pf=1.3, T1_wr=55.0, T2_pf=1.2, T2_pf_plus4=1.1, A_pf=0.95, B_pf=1.05), plateau_T1_pf=1.15,
                portfolio=dict(sharpe="up in T1 and T2", maxdd_pct=5.0, worst_month_pct=5.0, wr_pts=0.5, pf=0.02, corr=0.3),
                top_per_family=3, plus4_usd=3.0, note="fixed before running any candidate (2026-10-19)")
DROP_D4 = ["CA04V", "GD03", "ENG26", "LATEFH"]
VERDICT = [
    "- **Nothing is added.** 0 of the 23 candidates run under the pre-registered protocol passes it: 13 second-instance cells (part A), 10 re-arms (part B), 0 cells of the three new/extended families even reach the standalone bar (part C/D).",
    "- Part A (other cells of the durable families): of 54,558 archived cells only 971 pass the T1 standalone rules, 21% of those pass T2 PF >= 1.2 and 6.6% also pass the 2010-19 regime check (the chance of a random T1 survivor holding up). The 13 new-signal representatives (one per signal, top 3 per family) split into (i) cells that are the SAME trades as a module already in the set on 39-94% of their entries (G_DRIVE 09:30 drives = MOM1030/ORB, NQ_DRIVE 07:00/01:00 = ON07/LF06, LATE_MOM 15:00 VW = LATE15, SVWAP 04:00 x0.3 = SO04/CA04V) - they raise correlation and DD, not trade count - and (ii) genuinely new cells (PDC 10:30, VWAP 12:30, RVOL 10:00/10:15, NQ_DRIVE 07:00 fade) that are thin (n 33-73 per period), sit on no plateau (a neighbour below PF 1.15 in every case but two) and lower the set's WR / Sharpe when added. Only 2 of 13 sit on a plateau (CLOCK_ANCHOR#1277 PDC 10:30 and RVOL_DRIVE#778) and both fail the standalone and portfolio rules. All 13 together: Sharpe -0.11 / -0.56 (T1/T2), WR -1.2 / -1.5 pt, max DD +26% / +83%.",
    "- Part B (re-arm at the original entry level after a stop-out, the VOLB rule applied to NF05, LF06, LF0430, CRT11, LATE15, SO04, RV11, ORFAIL, CAM3, plus the ORFAIL family re-arm): the price rarely comes back to the entry level inside the module's own window (LF0430: 0 of 22 stop-outs; NF05 10/14 trades per period from 69 stop-outs), the re-entries that do fire lose out of sample (T2 PF 0.12-1.16 for every module but CRT11 with n = 6), and the 2010-19 regime view is below 1 for LF06, SO04, RV11, CAM3 and ORFAIL (NF05 and CRT11 are positive there but fail T1/T2). All level re-arms together: +101 / +97 trades, Sharpe +0.04 / -0.04, WR -0.55 / -0.68 pt. Consistent with reentry_lab (2026-10-17): the only re-arm with an edge is VOLB's, already available as VolbReArm.",
    "- Part C (OR_FAIL on 5/10-minute ranges, 288 cells: median PF 0.995 / 0.942 / 0.989 / 1.002 (T1/T2/A/B), 2 T1 survivors, 0 pass T2; Camarilla L2/H2 and L4/H4 fades, 256 cells: median 0.938 / 0.848, 6 T1 survivors, 0 pass T2): nothing; the 15-minute range with the CAM3 level remain isolated cells.",
    "- Part D (NEW VWAP_BAND2: session VWAP +- 2/3 sigma fades and band-1 momentum, bands strictly from bars <= t-1, lookahead check 0 violations on 3 cells / 11,009 signals; 528 cells): median PF 0.969 / 0.984 / 0.925 / 0.956, best T1 PF 1.80 (n < 60), exactly 1 cell passes the T1 rules (#375: fade of the 3rd band 11:00-15:00 with the trend, 0.25 ATR stop, 1R: n 67, PF 1.45 T1 / 1.60 T2) and it fails the 2010-19 check (A 0.96, B 0.79), i.e. a post-2020 cell with 1-in-16 base odds of holding. The session-VWAP bands carry no edge beyond what VW13 (13:00 RTH-VWAP distance) already captures.",
    "- Honest reading: the base set already contains every robust cell of these families; its neighbours are either the same trades again (size, not frequency) or noise-level cells whose T1 PF is the selection artefact the base rates predict (P(T2 & regime | T1) = 7%). 'More trades per day at the same WR / PF / DD' is not available from second instances, re-arms or VWAP bands on this data; the trade-count lever remains size and the number of accounts (memory 2026-09-28, 2026-10-17). No change to NQMaster is proposed.",
]
_G = {}


def getD():
    if "D" not in _G: _G["D"] = Data("nqdb.npz")
    return _G["D"]


def families():
    if "F" not in _G:
        import run_mine_db
        _G["F"] = run_mine_db.FAMILIES
    return _G["F"]


def ok_days():
    """Days NQMaster trades: RTH present, ATR >= 150 (MinAtrPoints), not FOMC; from 2020."""
    if "ok" in _G: return _G["ok"]
    D = getD(); dd = np.array(sorted(set(D.daydate[D.ro >= 0]))); dd = dd[dd >= 20200101]
    atr = pd.Series(D.atr, index=D.daydate).groupby(level=0).last().reindex(dd).to_numpy()
    _G["ok"] = set(dd[(atr >= 150) & ~np.isin(dd, list(NEWS["FOMC"]))].tolist()); return _G["ok"]


def all_days(lo, hi):
    D = getD(); dd = np.array(sorted(set(D.daydate[D.ro >= 0]))); return dd[(dd >= lo) & (dd < hi)]


# ------------------------------------------------------------------------------------------------ base set (ultra_d4)
def load_base():
    """raw = Ultra6 minus the four modules dropped on 2026-10-19 (not conflict-filtered); base = conflict_filter(raw) = nt_compare ultra_d4."""
    if "base" in _G: return _G["base"]
    X = pickle.load(open(os.path.join(HERE, "six_ultra6_trades.pkl"), "rb"))["Ultra6"][["date", "mod", "tin", "tout", "d", "u", "w"]].copy()
    raw = X[~X["mod"].isin(DROP_D4)].sort_values(["date", "tin"], kind="stable").reset_index(drop=True)
    base = conflict_filter(raw).reset_index(drop=True)
    _G["base"] = (raw, base); return _G["base"]


def load_base_norm():
    """Cost-normalised 2010-19 view of the base: db_long 'Ultra' norm rows (old Ultra exits, MOM1030 x4, no ENG10 / LATEFH) + the durable
    six-year modules' norm trades (as in six_oos.py)."""
    if "basen" in _G: return _G["basen"]
    U = pickle.load(open(os.path.join(HERE, "db_long_trades.pkl"), "rb"))["Ultra"][1].copy()
    U.loc[U["mod"] == "MOM1030", "w"] = 4.0; U = U[~U["mod"].isin(["ENG10", "LATEFH"])][["date", "mod", "tin", "tout", "d", "u", "w"]]
    parts = [U]
    for nm, key in {"SO04": ("CLOCK_ANCHOR", 1527), "RV11": ("RVOL_DRIVE", 4226), "ORFAIL": ("OR_FAIL", 142), "CAM3": ("PIVOT_FADE", 365)}.items():
        parts.append(module_trades(key, nm, "norm")[["date", "mod", "tin", "tout", "d", "u", "w"]])
    raw = pd.concat(parts, ignore_index=True); raw = raw[raw.date < 20200101].sort_values(["date", "tin"], kind="stable").reset_index(drop=True)
    _G["basen"] = (raw, conflict_filter(raw).reset_index(drop=True)); return _G["basen"]


# ------------------------------------------------------------------------------------------------ trades of a mined cell (regenerated)
@njit(cache=True)
def _exec_abs(o, h, l, c, om, day, ev_i, ev_d, ev_t, ev_px, ev_sl, ev_tp, ev_exp, ev_dead, flat, maxday, out, SLIP):
    """core.execute with an ABSOLUTE deadline bar (ev_dead) instead of a hold count; returns pts, fi, xi, d, risk, entry."""
    n = len(c); k = 0; busy = -1; curday = -1; cnt = 0
    for e in range(len(ev_i)):
        si = ev_i[e]
        if si <= busy or si + 1 >= n: continue
        j0 = si + 1
        if day[j0] != day[si]: continue
        if day[si] != curday:
            curday = day[si]; cnt = 0
        if cnt >= maxday: continue
        d = ev_d[e]; sl = ev_sl[e]; tp = ev_tp[e]; fi = -1; ent = 0.0
        if ev_t[e] == 0:
            if om[j0] >= flat and om[j0] < 1080: continue
            fi = j0; ent = o[j0] + d * SLIP
        else:
            px = ev_px[e]; last = min(ev_exp[e], n - 1)
            for j in range(j0, last + 1):
                if day[j] != day[si] or (om[j] >= flat and om[j] < 1080): break
                if ev_t[e] == 1:
                    if (d == 1 and l[j] <= px - TICK) or (d == -1 and h[j] >= px + TICK):
                        fi = j; ent = min(px, o[j]) if d == 1 else max(px, o[j]); break
                    if (d == 1 and h[j] >= tp) or (d == -1 and l[j] <= tp): break
                else:
                    if (d == 1 and h[j] >= px) or (d == -1 and l[j] <= px):
                        fi = j; ent = (max(px, o[j]) if d == 1 else min(px, o[j])) + d * SLIP; break
            if fi < 0: continue
        if (d == 1 and (ent <= sl or ent >= tp)) or (d == -1 and (ent >= sl or ent <= tp)): continue
        ex = np.nan; q = fi
        while q < n:
            if d == 1:
                if q > fi and o[q] <= sl: ex = o[q] - SLIP; break
                if l[q] <= sl: ex = sl - SLIP; break
                if q > fi and h[q] >= tp + TICK: ex = max(o[q], tp); break
            else:
                if q > fi and o[q] >= sl: ex = o[q] + SLIP; break
                if h[q] >= sl: ex = sl + SLIP; break
                if q > fi and l[q] <= tp - TICK: ex = min(o[q], tp); break
            if (q >= ev_dead[e]) or (om[q] >= flat and om[q] < 1080) or q + 1 >= n or day[q + 1] != day[q]:
                ex = c[q] - d * SLIP; break
            q += 1
        out[k, 0] = d * (ex - ent); out[k, 1] = fi; out[k, 2] = q; out[k, 3] = d; out[k, 4] = abs(ent - sl); out[k, 5] = ent; k += 1
        busy = q; cnt += 1
    return k


def run_ev(ev, maxday=1, norm=False, absolute=False, flat=955):
    """Events -> trades with pts, entry price and risk. norm: no slippage, cost 0.345% ATR, P&L in % of ATR. absolute: ev['hold'] = deadline bar."""
    D = getD()
    if len(ev["i"]) == 0: return pd.DataFrame(columns=["date", "usd", "fi", "xi", "d", "risk", "e", "pts"])
    order = np.argsort(ev["i"], kind="stable"); a = {k: np.ascontiguousarray(np.asarray(v)[order]) for k, v in ev.items()}
    out = np.zeros((len(a["i"]) + 1, 6)); slip = 0.0 if norm else SLIP
    if absolute:
        k = _exec_abs(D.o, D.h, D.l, D.c, D.om, D.day, a["i"].astype(np.int64), a["d"].astype(np.int64), a["t"].astype(np.int64), a["px"].astype(np.float64),
                      a["sl"].astype(np.float64), a["tp"].astype(np.float64), a["exp"].astype(np.int64), a["hold"].astype(np.int64), flat, maxday, out, slip)
    else:
        from core_e import execute_e
        k = execute_e(D.o, D.h, D.l, D.c, D.om, D.day, a["i"].astype(np.int64), a["d"].astype(np.int64), a["t"].astype(np.int64), a["px"].astype(np.float64),
                      a["sl"].astype(np.float64), a["tp"].astype(np.float64), a["exp"].astype(np.int64), a["hold"].astype(np.int64), flat, maxday, out, slip)
    o = out[:k]; fi = o[:, 1].astype(np.int64); pts = o[:, 0]
    if norm:
        A = D.atr[D.day[fi]]; usd = np.where(A > 0, (pts - NORM * A) / np.where(A > 0, A, 1) * 100, 0.0)
    else: usd = pts * D.pv - D.comm
    return pd.DataFrame(dict(date=D.date[fi], usd=usd, fi=fi, xi=o[:, 2].astype(np.int64), d=o[:, 3], risk=o[:, 4], e=o[:, 5], pts=pts))


def frame(r, name):
    D = getD()
    return pd.DataFrame(dict(date=r.date.to_numpy(), mod=name, tin=D.sm[r.fi.to_numpy().astype(int)], tout=D.sm[r.xi.to_numpy().astype(int)] + 1,
                             d=r.d.to_numpy(), u=r.usd.to_numpy(), w=1.0, fi=r.fi.to_numpy(), xi=r.xi.to_numpy(), risk=r.risk.to_numpy(), e=r.e.to_numpy()))


_MT = {}
def module_trades(key, name, view="real"):
    """Regenerated trades of a mined cell (fam, j): real $ (T1/T2, days NQMaster trades) or norm (2010-19 regime view)."""
    k = (key, view)
    if k in _MT: return _MT[k].assign(mod=name)
    gen, grid, maxday = families()[key[0]]; ev = gen(getD(), grid[key[1]])
    r = run_ev(ev, maxday, norm=(view == "norm")); T = frame(r, name)
    if view == "real": T = T[(T.date >= START) & T.date.isin(ok_days())]
    _MT[k] = T.reset_index(drop=True); return _MT[k].assign(mod=name)


# ------------------------------------------------------------------------------------------------ metrics
def pmetrics(T, lo, hi, days):
    T = T[(T.date >= lo) & (T.date < hi)]; dd = days[(days >= lo) & (days < hi)]
    x = (T.u * T.w); d = x.groupby(T.date).sum().reindex(dd, fill_value=0.0); eq = d.cumsum()
    mo = d.groupby(pd.to_datetime(d.index.astype(str)).to_period("M")).sum() if len(d) else pd.Series([0.0])
    w = x[x > 0].sum(); l = -x[x <= 0].sum()
    return dict(n=int(len(T)), tpd=round(len(T) / max(1, len(dd)), 3), wr=round(100 * float((T.u > 0).mean()), 2) if len(T) else None,
                pf=round(float(w / l), 3) if l > 0 else None, sharpe=round(float(d.mean() / d.std() * np.sqrt(252)), 3) if d.std() > 0 else 0.0,
                net=round(float(x.sum())), maxdd=round(float((eq.cummax() - eq).max())), worst_month=round(float(mo.min())), avg=round(float(x.mean()), 2) if len(T) else None)


def standalone(T, Tn=None, extra=3.0):
    """Per-period standalone stats of a candidate: real T1/T2 (+4 ticks on T2), norm A/B."""
    out = {}
    for lab, lo, hi in PER_REAL:
        out[lab] = pmetrics(T, lo, hi, all_days(lo, hi))
    T4 = T.assign(u=T.u - extra); out["T2_plus4"] = pmetrics(T4, MID, 20991231, all_days(MID, 20991231))
    if Tn is not None:
        for lab, lo, hi in PER_NORM: out[lab] = pmetrics(Tn, lo, hi, all_days(lo, hi))
    return out


def std_pass(st):
    p = PROTOCOL["standalone"]; g = lambda lab, k: (st.get(lab) or {}).get(k)
    c = dict(T1_n=(g("T1", "n") or 0) >= p["T1_n"], T1_pf=(g("T1", "pf") or 0) >= p["T1_pf"], T1_wr=(g("T1", "wr") or 0) >= p["T1_wr"],
             T2_pf=(g("T2", "pf") or 0) >= p["T2_pf"], T2_plus4=(g("T2_plus4", "pf") or 0) >= p["T2_pf_plus4"],
             A_pf=(g("A", "pf") or 0) >= p["A_pf"], B_pf=(g("B", "pf") or 0) >= p["B_pf"])
    return c, all(c.values())


def daily_series(T, days):
    return (T.u * T.w).groupby(T.date).sum().reindex(days, fill_value=0.0)


def portfolio_test(cands, label):
    """cands: list of candidate trade frames (real). Combined = conflict_filter(raw base + candidates). Returns base / comb metrics, deltas, pass."""
    raw, base = load_base(); days = np.array(sorted(base.date.unique()))
    C = pd.concat([c[["date", "mod", "tin", "tout", "d", "u", "w"]] for c in cands], ignore_index=True)
    C = C[(C.date >= START) & C.date.isin(ok_days())]
    comb = conflict_filter(pd.concat([raw, C], ignore_index=True).sort_values(["date", "tin"], kind="stable").reset_index(drop=True))
    out = {"label": label, "cand_n": int(len(C)), "cand_kept": int(comb["mod"].isin(C["mod"].unique()).sum()), "base": {}, "comb": {}, "delta": {}}
    cd = daily_series(C, days); bd = daily_series(base, days)
    out["corr"] = round(float(np.corrcoef(bd, cd)[0, 1]), 3) if cd.std() > 0 else 0.0
    for lab, lo, hi in PER_REAL:
        m = (days >= lo) & (days < hi)
        out["corr_" + lab] = round(float(np.corrcoef(bd[m], cd[m])[0, 1]), 3) if cd[m].std() > 0 else 0.0
        b = pmetrics(base, lo, hi, days); c = pmetrics(comb, lo, hi, days); out["base"][lab] = b; out["comb"][lab] = c
        out["delta"][lab] = dict(sharpe=round(c["sharpe"] - b["sharpe"], 3), wr=round((c["wr"] or 0) - (b["wr"] or 0), 2), pf=round((c["pf"] or 0) - (b["pf"] or 0), 3),
                                 maxdd_pct=round(100 * (c["maxdd"] / b["maxdd"] - 1), 1) if b["maxdd"] else 0.0,
                                 worst_month_pct=round(100 * (c["worst_month"] / b["worst_month"] - 1), 1) if b["worst_month"] else 0.0,
                                 net=c["net"] - b["net"], tpd=round(c["tpd"] - b["tpd"], 3), n=c["n"] - b["n"])
    # blocked base trades = base rows no longer in comb (an opposite candidate position was open first)
    out["base_blocked"] = int(len(base) - comb[~comb["mod"].isin(C["mod"].unique())].shape[0])
    P = PROTOCOL["portfolio"]; dl = out["delta"]
    chk = dict(sharpe_up=all(dl[l]["sharpe"] > 0 for l in ("T1", "T2")), maxdd=all(dl[l]["maxdd_pct"] <= P["maxdd_pct"] for l in ("T1", "T2")),
               worst_month=all(dl[l]["worst_month_pct"] <= P["worst_month_pct"] for l in ("T1", "T2")), wr=all(dl[l]["wr"] >= -P["wr_pts"] for l in ("T1", "T2")),
               pf=all(dl[l]["pf"] >= -P["pf"] for l in ("T1", "T2")), corr=out["corr"] < P["corr"])
    out["checks"] = chk; out["pass"] = all(chk.values())
    return out


def portfolio_norm(cands_norm, label):
    raw, base = load_base_norm(); out = {"label": label, "base": {}, "comb": {}}
    C = pd.concat([c[["date", "mod", "tin", "tout", "d", "u", "w"]] for c in cands_norm], ignore_index=True) if cands_norm else raw.iloc[:0]
    comb = conflict_filter(pd.concat([raw, C], ignore_index=True).sort_values(["date", "tin"], kind="stable").reset_index(drop=True))
    for lab, lo, hi in PER_NORM:
        dd = all_days(lo, hi); out["base"][lab] = pmetrics(base, lo, hi, dd); out["comb"][lab] = pmetrics(comb, lo, hi, dd)
    return out


# ------------------------------------------------------------------------------------------------ mined-grid scan (parts A, C, D)
SIGKEYS = {"CLOCK_ANCHOR": ["anc", "T", "x", "mode"], "G_DRIVE": ["A", "T", "x", "mode"], "NQ_DRIVE": ["A", "T", "x", "mode"],
           "RVOL_DRIVE": ["T", "cond", "ref", "x", "dm"], "LATE_MOM": ["T", "sig", "x"], "OPEN_DRIVE": ["T", "x"], "OR_FAIL": ["T", "w1", "bk", "tfb"],
           "PIVOT_FADE": ["piv", "w0", "w1", "sweep", "conf"], "VOL_BREAK": ["k", "w1"],
           "VWAP_BAND2": ["mode", "w0", "w1"], "OR_FAIL_X": ["T", "w1", "bk", "tfb"], "PIVOT_FADE_X": ["piv", "w0", "w1", "sweep", "conf"]}
# signals already in the 2027 default set (or tested and dropped on 2026-10-19), by family: any cell with the same signal tuple is NOT a new instance
EXISTING = {"G_DRIVE": [("NF05", (2000, 540, 0.35, -1))], "NQ_DRIVE": [("LF06", (400, 120, 0.2, -1)), ("LF0430", (400, 30, 0.1, -1))],
            "CLOCK_ANCHOR": [("SO04", ("SOPEN", 400, 0.35, 1)), ("CA04V dropped", ("SVWAP", 400, 0.2, 1)), ("VW13", ("VWAP", 1300, 0.3, 1))],
            "RVOL_DRIVE": [("RV11", (1100, ("lo", 0.8), "pdc", 0.25, 1))], "LATE_MOM": [("LATE15", (1500, "RTH", 0.5)), ("LATEFH dropped", (1500, "FHRTH", 0.25))],
            "OPEN_DRIVE": [("MOM1030 (10:30 vs RTH open)", (60, None))], "OR_FAIL": [("ORFAIL", (15, 1400, 0.1, 5))],
            "PIVOT_FADE": [("CAM3", ("CAM3", 1000, 1530, 0.0, 10))], "VOL_BREAK": [("VOLB", (0.45, 1500)), ("VOLB k0.45 w1200", (0.45, 1200))]}
NON_AXES = {"tf", "mode", "dm", "stop", "tg", "tfb", "piv", "anc", "sig", "cond", "ref", "sm"}


def load_results():
    if "R" in _G: return _G["R"]
    fr = []
    for f in ("results_db_old.csv", "results_db_new.csv", "results_b10.csv"):
        p = os.path.join(HERE, f)
        if os.path.exists(p): fr.append(pd.read_csv(p))
    R = pd.concat(fr, ignore_index=True); R["p"] = R.params.map(ast.literal_eval)
    _G["R"] = R; return R


def sig_of(fam, p):
    keys = SIGKEYS[fam]
    if fam == "OPEN_DRIVE" and p["T"] == 60: return (60, None)
    return tuple(p[k] for k in keys)


def is_existing(fam, p):
    return any(sig_of(fam, p) == s for _, s in EXISTING.get(fam, []))


def csv_pass(r):
    p = PROTOCOL["standalone"]
    return (r.T1_n >= p["T1_n"] and (r.T1_pf or 0) >= p["T1_pf"] and (r.T1_wr or 0) >= p["T1_wr"], (r.T2_pf or 0) >= p["T2_pf"],
            (r.A_pf or 0) >= p["A_pf"] and (r.B_pf or 0) >= p["B_pf"])


def base_rates(R, fams):
    out = {}
    for fam in ["ALL"] + list(fams):
        X = R if fam == "ALL" else R[R.fam == fam]
        if not len(X): continue
        t1 = X.apply(lambda r: csv_pass(r)[0], axis=1); t2 = X.apply(lambda r: csv_pass(r)[1], axis=1); ab = X.apply(lambda r: csv_pass(r)[2], axis=1)
        out[fam] = dict(cells=int(len(X)), T1_pass=int(t1.sum()), median_pf={k: (None if X[k + "_pf"].isna().all() else round(float(X[k + "_pf"].median()), 3)) for k in ("T1", "T2", "A", "B")},
                        best_T1_pf=round(float(X.T1_pf.max()), 3) if X.T1_pf.notna().any() else None, P_T2_pass_all=round(100 * float(t2.mean()), 1),
                        P_T2_given_T1=round(100 * float(t2[t1].mean()), 1) if t1.sum() else None,
                        P_T2AB_all=round(100 * float((t2 & ab).mean()), 1), P_T2AB_given_T1=round(100 * float((t2 & ab)[t1].mean()), 1) if t1.sum() else None)
    return out


def neighbours(R, fam, j):
    """One-step neighbours on each numeric axis with all other params equal -> list of (axis, value, T1_pf, n)."""
    X = R[R.fam == fam]; row = X[X.j == j].iloc[0]; p = row.p; out = []
    for ax, v in p.items():
        if ax in NON_AXES or not isinstance(v, (int, float)) or isinstance(v, bool): continue
        if fam == "VWAP_BAND2" and ax == "R" and p.get("tg") == 0: continue
        same = X[X.p.map(lambda q: all(q.get(k) == p[k] for k in p if k != ax))]
        vals = sorted(set(same.p.map(lambda q: q[ax])))
        if len(vals) < 2: continue
        i = vals.index(v)
        for nv in ([vals[i - 1]] if i > 0 else []) + ([vals[i + 1]] if i + 1 < len(vals) else []):
            r = same[same.p.map(lambda q: q[ax] == nv)].iloc[0]
            out.append(dict(axis=ax, value=nv, T1_pf=None if pd.isna(r.T1_pf) else float(r.T1_pf), T1_n=int(r.T1_n)))
    return out


def plateau_ok(nb):
    return all((x["T1_pf"] or 0) >= PROTOCOL["plateau_T1_pf"] for x in nb)


def scan_family(R, fam, top=3):
    """Cells of a family passing the standalone csv rules on T1, T2 and A/B, not an existing signal, one representative (best T1 PF) per signal tuple,
    top-N by T1 PF."""
    X = R[R.fam == fam].copy()
    if not len(X): return [], {}
    ok = X.apply(lambda r: all(csv_pass(r)), axis=1)
    X = X[ok]; X = X[~X.p.map(lambda p: is_existing(fam, p))]
    reps = {}
    for _, r in X.iterrows():
        s = sig_of(fam, r.p)
        if s not in reps or r.T1_pf > reps[s].T1_pf: reps[s] = r
    rows = sorted(reps.values(), key=lambda r: -r.T1_pf)
    info = dict(cells=int((R.fam == fam).sum()), pass_all_csv=int(ok.sum()), new_signals=len(reps))
    return rows[:top], info


def evaluate_cell(R, fam, j, name):
    """Full protocol on one mined cell: standalone (regenerated trades), plateau, portfolio."""
    T = module_trades((fam, j), name, "real"); Tn = module_trades((fam, j), name, "norm")
    st = standalone(T, Tn); chk, sp = std_pass(st); nb = neighbours(R, fam, j); pl = plateau_ok(nb)
    port = portfolio_test([T], name)
    raw, base = load_base()
    # overlap with the base: candidate entries at the same minute and direction as a base trade (same-bar duplicates = a size change, not a new trade)
    key = set(zip(base.date, base.tin, base.d)); ov = float(np.mean([(a, b, c) in key for a, b, c in zip(T.date, T.tin, T.d)])) if len(T) else 0.0
    rec = dict(name=name, fam=fam, j=int(j), params=repr(R[(R.fam == fam) & (R.j == j)].p.iloc[0]), standalone=st, standalone_checks=chk, standalone_pass=sp,
               neighbours=nb, plateau_pass=pl, portfolio=port, same_minute_overlap_pct=round(100 * ov, 1),
               accepted=bool(sp and pl and port["pass"]))
    return rec, T, Tn


# ------------------------------------------------------------------------------------------------ part B: re-arm after a stop-out
REARM_ULTRA = ["NF05", "LF06", "LF0430", "CRT11", "LATE15"]
REARM_SIX = {"SO04": ("CLOCK_ANCHOR", 1527), "RV11": ("RVOL_DRIVE", 4226), "ORFAIL": ("OR_FAIL", 142), "CAM3": ("PIVOT_FADE", 365)}
HOLD_SIX = {"SO04": 330, "RV11": 400, "ORFAIL": 240, "CAM3": 240}


def stopouts_ultra(norm=False):
    """Stop-outs of the Ultra modules: real = rows of the ultra_d4 base (fi from cand16 UltraR), exit reason from the wrq exit engine
    (reentry_lab.module_exits: rs 0 = stop loss); norm = every entry 2010-19 of the module (regime view, no conflict filter)."""
    import reentry_lab as RL
    D = getD(); E = RL.entries(); out = []
    raw, base = load_base()
    X = pickle.load(open(os.path.join(HERE, "cand16_trades.pkl"), "rb"))["UltraR"][0]
    for mod in REARM_ULTRA:
        Rm = RL.module_exits(D, E, mod, slip=0.0 if norm else SLIP, norm=norm)
        Rm = Rm[Rm.rs == 0].copy(); Rm["date"] = D.date[Rm.fi.to_numpy()]
        if norm:
            Rm = Rm[Rm.date < 20200101]
        else:
            b = base[base["mod"] == mod][["date", "tin", "d"]].drop_duplicates()
            xm = X[X["mod"] == mod][["date", "tin", "d", "fi"]].merge(b, on=["date", "tin", "d"]).drop_duplicates("fi")
            Rm = Rm[Rm.fi.isin(set(xm.fi))]
        out.append(Rm.assign(mod=mod))
    return pd.concat(out, ignore_index=True)


def stopouts_six(norm=False):
    D = getD(); out = []
    for nm, key in REARM_SIX.items():
        gen, grid, maxday = families()[key[0]]; ev = gen(D, grid[key[1]]); r = run_ev(ev, maxday, norm=norm)
        if not norm: r = r[(r.date >= START) & r.date.isin(ok_days())]
        else: r = r[r.date < 20200101]
        st = r[r.pts <= -r.risk + (0.01 if norm else -0.2)].copy()   # stop fill = sl -/+ slippage (real; worse on a gap), = sl in the norm run
        st["ent0"] = st.e - st.d * (0.0 if norm else SLIP); st["sl0"] = st.ent0 - st.d * st.risk
        # target distance from the generator's events (tp - px) matched on the signal bar (fi - 1 for market entries)
        evf = pd.DataFrame(dict(i=ev["i"], tpd=np.abs(ev["tp"] - ev["px"]), px=ev["px"], d=ev["d"])).drop_duplicates("i").set_index("i")
        st["tgt"] = evf.tpd.reindex(st.fi - 1).to_numpy(); st["tx"] = np.minimum(st.fi + HOLD_SIX[nm], D.de[D.day[st.fi.to_numpy()]])
        st = st[np.isfinite(st.tgt)]
        out.append(st[["date", "fi", "xi", "d", "ent0", "sl0", "tgt", "tx"]].assign(mod=nm))
    return pd.concat(out, ignore_index=True)


def rearm_level(st, norm=False):
    """Stop order back at the original entry level after the stop-out bar, same direction, same stop / target distance, until the module's deadline."""
    D = getD(); parts = []
    for mod, g in st.groupby("mod"):
        d = g.d.to_numpy().astype(np.int64); px = g.ent0.to_numpy(); risk = np.abs(g.ent0.to_numpy() - g.sl0.to_numpy())
        tgt = g.tgt.to_numpy() if "tgt" in g else np.abs(g.tp0.to_numpy() - g.ent0.to_numpy())
        xi = g.xi.to_numpy().astype(np.int64); tx = g.tx.to_numpy().astype(np.int64)
        ok = (tx > xi + 1) & (risk > 0) & (tgt > 0)
        ev = dict(i=xi[ok], d=d[ok], t=np.full(ok.sum(), 2), px=px[ok], sl=px[ok] - d[ok] * risk[ok], tp=px[ok] + d[ok] * tgt[ok], exp=tx[ok], hold=tx[ok])
        r = run_ev(ev, maxday=2, norm=norm, absolute=True)
        parts.append(frame(r, mod + "_RE"))
    return pd.concat(parts, ignore_index=True)


@njit(cache=True)
def _orfail_re(o, h, l, c, sm, ro, de, atr, trend, T, w1, bk, tfb, tg, tf, startbar, out):
    """families5._orfail restarted from startbar[d] (bar after the stop-out) with the same opening range -> the NEXT failed break."""
    nd = len(ro); n = 0
    for d in range(nd):
        r = ro[d]; sb = startbar[d]
        if r < 0 or atr[d] <= 0 or sb < 0: continue
        A = atr[d]; hi = -1e18; lo = 1e18; q = r
        while q <= de[d] and sm[q] - sm[r] < T:
            hi = max(hi, h[q]); lo = min(lo, l[q]); q += 1
        if q > de[d]: continue
        brk = 0; ext = 0.0; bi = -1
        for j in range(max(q, sb), de[d] + 1):
            if sm[j] >= w1: break
            if brk == 0:
                if h[j] > hi + bk * A: brk = 1; ext = h[j]; bi = j
                elif l[j] < lo - bk * A: brk = -1; ext = l[j]; bi = j
                if brk == 0: continue
            else:
                if brk == 1: ext = max(ext, h[j])
                else: ext = min(ext, l[j])
            if j - bi > 30: break
            if tfb == 5 and (sm[j] - sm[r]) % 5 != 4: continue
            back = (brk == 1 and c[j] < hi) or (brk == -1 and c[j] > lo)
            if not back: continue
            s = -brk
            if tf == 1 and s != trend[d]: break
            if tf == -1 and s == trend[d]: break
            sl = ext + TICK if s == -1 else ext - TICK
            risk = (c[j] - sl) * s
            if risk < 0.03 * A or risk > 0.4 * A: break
            if tg == 0: tp = c[j] + s * 0.5 * risk
            elif tg == 1: tp = c[j] + s * risk
            elif tg == 2: tp = (hi + lo) / 2
            else: tp = lo if s == -1 else hi
            if (tp - c[j]) * s <= TICK: break
            out[n, 0] = j; out[n, 1] = s; out[n, 2] = 0; out[n, 3] = c[j]; out[n, 4] = sl; out[n, 5] = tp; out[n, 6] = j; out[n, 7] = 240; n += 1
            break
    return n


def orfail_family_rearm(st, norm=False):
    from families5 import TG
    from core import ev_from_lists
    D = getD(); p = families()["OR_FAIL"][1][142]; g = st[st["mod"] == "ORFAIL"]
    startbar = np.full(D.nd, -1, np.int64); startbar[D.day[g.xi.to_numpy()]] = g.xi.to_numpy() + 1
    out = np.zeros((D.nd, 8)); n = _orfail_re(D.o, D.h, D.l, D.c, D.sm, D.ro, D.de, D.atr, D.trend, p["T"], S(p["w1"]), p["bk"], p["tfb"], TG[p["tg"]], p["tf"], startbar, out)
    r = run_ev(ev_from_lists(out[:n].tolist()), 1, norm=norm)
    return frame(r, "ORFAIL_RE2")


def part_b():
    OUT = {}
    st_u = stopouts_ultra(False); st_s = stopouts_six(False)
    stn_u = stopouts_ultra(True); stn_s = stopouts_six(True)
    base_counts = {m: int((st_u["mod"] == m).sum()) for m in REARM_ULTRA}; base_counts.update({m: int((st_s["mod"] == m).sum()) for m in REARM_SIX})
    OUT["stopouts_real"] = base_counts
    RE = pd.concat([rearm_level(st_u), rearm_level(st_s)], ignore_index=True); REn = pd.concat([rearm_level(stn_u, True), rearm_level(stn_s, True)], ignore_index=True)
    RE = RE[(RE.date >= START) & RE.date.isin(ok_days())]
    RE2 = orfail_family_rearm(st_s); RE2 = RE2[(RE2.date >= START) & RE2.date.isin(ok_days())]; RE2n = orfail_family_rearm(stn_s, True)
    raw, base = load_base(); OUT["cands"] = {}; keep = []
    for mod in list(REARM_ULTRA) + list(REARM_SIX) + ["ORFAIL_RE2"]:
        nm = mod + "_RE" if mod != "ORFAIL_RE2" else mod
        T = RE[RE["mod"] == nm] if mod != "ORFAIL_RE2" else RE2; Tn = REn[REn["mod"] == nm] if mod != "ORFAIL_RE2" else RE2n
        if len(T) == 0: OUT["cands"][nm] = dict(name=nm, n=0); continue
        st = standalone(T, Tn); chk, sp = std_pass(st); port = portfolio_test([T], nm)
        rec = dict(name=nm, standalone=st, standalone_checks=chk, standalone_pass=sp, plateau_pass=None, portfolio=port, accepted=bool(sp and port["pass"]))
        OUT["cands"][nm] = rec
        if rec["accepted"]: keep.append((nm, T, Tn))
        print(f"  B {nm:12s} n {st['T1']['n']}/{st['T2']['n']} WR {st['T1']['wr']}/{st['T2']['wr']} PF {st['T1']['pf']}/{st['T2']['pf']} +4t {st['T2_plus4']['pf']} "
              f"A/B {st.get('A', {}).get('pf')}/{st.get('B', {}).get('pf')} | port dSR {port['delta']['T1']['sharpe']}/{port['delta']['T2']['sharpe']} corr {port['corr']} pass {rec['accepted']}", flush=True)
    # all level re-arms together (information only; not an acceptance test)
    OUT["all_level_rearms_together"] = portfolio_test([RE], "all level re-arms")
    return OUT, keep


# ------------------------------------------------------------------------------------------------ report
def _f(x, nd=2):
    return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def _fails(rec):
    f = [k for k, v in rec["standalone_checks"].items() if not v]
    if rec.get("plateau_pass") is False: f.append("plateau")
    f += ["port:" + k for k, v in rec["portfolio"]["checks"].items() if not v]
    return ", ".join(f) if f else "none"


def _cand_rows(cands):
    L = ["| candidate | cell | n T1/T2 | WR T1/T2 | PF T1 / T2 / T2+4t | A / B PF (norm) | plateau | port dSharpe T1/T2 | dWR T1/T2 | dPF T1/T2 | dDD% T1/T2 | dWorstMo% T1/T2 | corr | same-min overlap | fails |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for nm, r in cands.items():
        if "standalone" not in r: L.append(f"| {nm} | re-arm | 0 trades | | | | | | | | | | | | no re-entry fired |"); continue
        st = r["standalone"]; d = r["portfolio"]["delta"]; g = lambda lab, k: (st.get(lab) or {}).get(k)
        L.append(f"| {nm} | {r.get('params', 're-arm').replace(chr(39), '').replace(' ', '')[:95]} | {g('T1','n')}/{g('T2','n')} | {_f(g('T1','wr'),1)}/{_f(g('T2','wr'),1)} | {_f(g('T1','pf'),3)} / {_f(g('T2','pf'),3)} / {_f(g('T2_plus4','pf'),3)} | "
                 f"{_f(g('A','pf'),3)} / {_f(g('B','pf'),3)} | {r.get('plateau_pass')} | {_f(d['T1']['sharpe'],3)}/{_f(d['T2']['sharpe'],3)} | {_f(d['T1']['wr'])}/{_f(d['T2']['wr'])} | "
                 f"{_f(d['T1']['pf'],3)}/{_f(d['T2']['pf'],3)} | {_f(d['T1']['maxdd_pct'],1)}/{_f(d['T2']['maxdd_pct'],1)} | {_f(d['T1']['worst_month_pct'],1)}/{_f(d['T2']['worst_month_pct'],1)} | {_f(r['portfolio']['corr'],3)} | {_f(r.get('same_minute_overlap_pct'),1)}% | {_fails(r)} |")
    return L


def _port_block(t, title):
    if t is None: return [f"{title}: no candidates."]
    L = [f"**{title}** ({t['cand_n']} candidate trades, {t['cand_kept']} kept after the conflict filter, {t['base_blocked']} base trades blocked, corr {t['corr']}):", "",
         "| period | set | trades/day | WR | PF | Sharpe | net $ | max DD | worst month |", "|---|---|---|---|---|---|---|---|---|"]
    for lab in ("T1", "T2"):
        for k in ("base", "comb"):
            m = t[k][lab]; L.append(f"| {lab} | {k} | {m['tpd']} | {_f(m['wr'],1)} | {_f(m['pf'],3)} | {_f(m['sharpe'],3)} | {m['net']} | {m['maxdd']} | {m['worst_month']} |")
    return L + [""]


def write_report(OUT):
    P = OUT["protocol"]; b = OUT["base"]
    L = ["# More trades at the same quality (2026-10-19)", "",
         "Base = the 2027 default set (nt_compare `ultra_d4`: Ultra + SO04/RV11/ORFAIL/CAM3, opposite-position conflicts removed), real Databento NQ, "
         "$ per MNQ incl. $1.90 + 1 tick; T1 2020-10-15..2023 (choose), T2 2024-01..2026-10 (check), A 2010-14 / B 2015-19 cost-normalised (0.345% ATR) regime check. "
         "Script `research/mine/more_trades.py` (+ `families10.py`, mined into `results_b10.csv` / `trades_b10.pkl`); numbers in `more_trades.json`.", "",
         "## Pre-registered protocol (fixed before any candidate was run)", "",
         f"- Standalone: T1 n >= {P['standalone']['T1_n']}, PF >= {P['standalone']['T1_pf']}, WR >= {P['standalone']['T1_wr']}; T2 PF >= {P['standalone']['T2_pf']}; +4 ticks (${P['plus4_usd']} per trade) T2 PF >= {P['standalone']['T2_pf_plus4']}; norm A PF >= {P['standalone']['A_pf']} and B PF >= {P['standalone']['B_pf']}.",
         f"- Plateau: every one-step neighbour on each numeric grid axis (other params equal) has T1 PF >= {P['plateau_T1_pf']}.",
         f"- Portfolio (candidate added to the raw base and run through `wrq_port.conflict_filter`): Sharpe up in T1 AND T2; max DD and worst month not worse by > {P['portfolio']['maxdd_pct']}% in either; set WR not lower by > {P['portfolio']['wr_pts']} pt; set PF not lower by > {P['portfolio']['pf']}; daily-P&L correlation with the base < {P['portfolio']['corr']}.",
         f"- Grid parts: cells passing the standalone rules on the mined csv (T1 as mined = 2020-01..2023) that are a NEW signal (different anchor / window / threshold / mode from every module already in the set; trend-filter-only or exit-only variants of an existing signal are the same signal), one representative per signal (best T1 PF), top {P['top_per_family']} per family, then everything re-run on regenerated trades with T1 = 2020-10-15..2023 and NQMaster's day filter (ATR >= 150, no FOMC).",
         "- Base rate P(T2 pass | T1 pass) is reported per family against the whole 54,558-cell archive so selection bias can be judged.",
         "- Re-arm (part B): one stop order back at the original entry level after a stop-loss exit, same direction, same stop and target distance, until the module's own deadline (the rule accepted for VOLB on 2026-10-17); ORFAIL also gets its family re-arm (next failed break after the stop-out).", "",
         "## Base set", "", "| period | trades/day | WR | PF | Sharpe | net | max DD | worst month |", "|---|---|---|---|---|---|---|---|"]
    for lab in ("T1", "T2", "A", "B"):
        m = b[lab]; L.append(f"| {lab}{' (norm, % ATR)' if lab in 'AB' else ''} | {m['tpd']} | {_f(m['wr'],1)} | {_f(m['pf'],3)} | {_f(m['sharpe'],3)} | {m['net']} | {m['maxdd']} | {m['worst_month']} |")
    L += ["", "(The 2010-19 base view uses the db_long 'Ultra' norm rows (pre-overhaul exits, MOM1030 x4, ENG10/LATEFH off) plus the four durable six-year modules, as in six_oos.py.)", ""]
    # counts + base rates
    L += ["## Cells scanned and base rates", "", "| family | cells | median PF T1 / T2 / A / B | pass T1 (csv) | P(T2 pass) all cells | P(T2 pass given T1 pass) | P(T2 and A/B pass given T1 pass) | new signals tested |", "|---|---|---|---|---|---|---|---|"]
    for part in ("A", "CD"):
        for fam, v in OUT[part]["base_rates"].items():
            if fam == "ALL" and part == "CD": continue
            fi = OUT[part]["families"].get(fam, {}); mp = v["median_pf"]
            L.append(f"| {fam}{' (whole archive)' if fam == 'ALL' else ''} | {v['cells']} | {_f(mp['T1'],3)} / {_f(mp['T2'],3)} / {_f(mp['A'],3)} / {_f(mp['B'],3)} | {v['T1_pass']} | {v['P_T2_pass_all']}% | {_f(v['P_T2_given_T1'],1)}% | {_f(v['P_T2AB_given_T1'],1)}% | {fi.get('new_signals', '-')} ({fi.get('pass_all_csv', '-')} cells pass all csv rules) |")
    L += ["", "## Part A: second instances of the durable modules' families (other cells)", ""] + _cand_rows(OUT["A"]["cands"]) + [""]
    L += _port_block(OUT["A"].get("all_tested_together"), "Information only: all part-A representatives added together")
    nm_ = [(nm, r) for nm, r in OUT["A"]["cands"].items() if "standalone" in r and len(_fails(r).split(", ")) <= 2 and _fails(r) != "none"]
    if nm_:
        L += ["Near-misses (at most two failed rules) and their grid neighbours (T1 PF as mined; the plateau rule needs every neighbour >= 1.15):", ""]
        for nm, r in nm_:
            L.append(f"- {nm}: fails {_fails(r)}; neighbours " + ", ".join(f"{x['axis']}={x['value']}: {_f(x['T1_pf'],2)} (n {x['T1_n']})" for x in r["neighbours"]))
        L.append("")
    L += ["## Part B: one re-arm after a stop-out", "", f"Stop-outs in the base (T1+T2): {OUT['B']['stopouts_real']}", ""] + _cand_rows(OUT["B"]["cands"]) + [""]
    L += _port_block(OUT["B"].get("all_level_rearms_together"), "Information only: all level re-arms added together")
    lc = OUT["CD"].get("lookahead_check")
    L += ["## Part C/D: OR_FAIL 5/10-minute ranges, Camarilla L2/H2 and L4/H4, NEW VWAP_BAND2 family", "",
          f"Mined with `MINE_TAG=b10 MINE_PROCS=2 python3 run_mine_db.py VWAP_BAND2 OR_FAIL_X PIVOT_FADE_X` (1,072 cells, 38 s). VWAP_BAND2 lookahead check (bands recomputed from bars <= t-1 and the signal bar's own volume/high perturbed): {lc}", ""]
    L += _cand_rows(OUT["CD"]["cands"]) + [""]
    L += ["## All accepted additions together", ""]
    if OUT.get("all_accepted"): L += _port_block(OUT["all_accepted"], "Accepted additions")
    else: L += ["None accepted: the base set is unchanged (trades/day, WR, PF, Sharpe, max DD, worst month and the 2010-19 norm view are the base rows above).", ""]
    L += ["## Verdict", ""]
    L += OUT.get("verdict", [])
    open(os.path.join(HERE, "more_trades_report.md"), "w").write("\n".join(L) + "\n")


# ------------------------------------------------------------------------------------------------ main
def part_grid(R, fams, label):
    OUT = {"base_rates": base_rates(R, fams), "families": {}, "cands": {}}; keep = []
    for fam in fams:
        rows, info = scan_family(R, fam, PROTOCOL["top_per_family"]); OUT["families"][fam] = dict(info, tested=[int(r.j) for r in rows])
        print(f"{label} {fam}: {info} -> testing {[int(r.j) for r in rows]}", flush=True)
        for r in rows:
            nm = f"{fam}#{int(r.j)}"
            rec, T, Tn = evaluate_cell(R, fam, int(r.j), nm); OUT["cands"][nm] = rec
            st = rec["standalone"]; port = rec["portfolio"]
            print(f"  {nm:22s} {r.params[:70]} n {st['T1']['n']}/{st['T2']['n']} WR {st['T1']['wr']}/{st['T2']['wr']} PF {st['T1']['pf']}/{st['T2']['pf']} +4t {st['T2_plus4']['pf']} "
                  f"A/B {st['A']['pf']}/{st['B']['pf']} plateau {rec['plateau_pass']} | port dSR {port['delta']['T1']['sharpe']}/{port['delta']['T2']['sharpe']} "
                  f"dWR {port['delta']['T1']['wr']}/{port['delta']['T2']['wr']} dPF {port['delta']['T1']['pf']}/{port['delta']['T2']['pf']} corr {port['corr']} overlap {rec['same_minute_overlap_pct']}% -> {rec['accepted']}", flush=True)
            if rec["accepted"]: keep.append((nm, T, Tn))
    return OUT, keep


def part_info(R, fams, label):
    """Information only: every new-signal representative of these families that passes the standalone csv rules (top-N per family as tested), all together."""
    Ts = []
    for fam in fams:
        rows, _ = scan_family(R, fam, PROTOCOL["top_per_family"])
        for r in rows: Ts.append(module_trades((fam, int(r.j)), f"{fam}#{int(r.j)}", "real"))
    return portfolio_test(Ts, label) if Ts else None


if __name__ == "__main__":
    if "--report" in sys.argv:
        OUT = json.load(open(os.path.join(HERE, "more_trades.json"))); OUT["verdict"] = VERDICT; write_report(OUT); sys.exit(0)
    t0 = time.time(); OUT = {"protocol": PROTOCOL, "base": {}}
    raw, base = load_base(); days = np.array(sorted(base.date.unique()))
    for lab, lo, hi in PER_REAL: OUT["base"][lab] = pmetrics(base, lo, hi, days)
    rawn, basen = load_base_norm()
    for lab, lo, hi in PER_NORM: OUT["base"][lab] = pmetrics(basen, lo, hi, all_days(lo, hi))
    print("base", {k: (v["tpd"], v["wr"], v["pf"], v["sharpe"], v["net"], v["maxdd"]) for k, v in OUT["base"].items()}, round(time.time() - t0), "s", flush=True)
    R = load_results()
    famsA = ["CLOCK_ANCHOR", "G_DRIVE", "NQ_DRIVE", "RVOL_DRIVE", "LATE_MOM", "OPEN_DRIVE", "OR_FAIL", "PIVOT_FADE", "VOL_BREAK"]
    OUT["A"], keepA = part_grid(R, famsA, "A")
    print("part A done", round(time.time() - t0), "s", flush=True)
    OUT["B"], keepB = part_b()
    print("part B done", round(time.time() - t0), "s", flush=True)
    famsC = [f for f in ("OR_FAIL_X", "PIVOT_FADE_X", "VWAP_BAND2") if (R.fam == f).any()]
    OUT["CD"], keepC = part_grid(R, famsC, "C/D")
    try:
        import families10 as F10
        chk = [F10.lookahead_check(getD(), p) for p in (F10.GRID_VWB2[0], F10.GRID_VWB2[100], F10.GRID_VWB2[-1])]
        OUT["CD"]["lookahead_check"] = dict(cells=["GRID_VWB2[0]", "GRID_VWB2[100]", "GRID_VWB2[-1]"], results=[dict(n=c[0], max_dvwap=c[1], max_dsigma=c[2], violations=c[3]) for c in chk])
    except Exception as e:
        OUT["CD"]["lookahead_check"] = repr(e)
    print("part C/D done", round(time.time() - t0), "s", flush=True)
    OUT["A"]["all_tested_together"] = part_info(R, famsA, "all part-A candidates together (information)")
    keep = keepA + keepB + keepC
    OUT["accepted"] = [k[0] for k in keep]
    if keep:
        OUT["all_accepted"] = portfolio_test([k[1] for k in keep], "all accepted together")
        OUT["all_accepted_norm"] = portfolio_norm([k[2] for k in keep if k[2] is not None and len(k[2])], "all accepted together (norm)")
    else:
        OUT["all_accepted"] = None; OUT["all_accepted_norm"] = portfolio_norm([], "base only (norm)")
    OUT["runtime_s"] = round(time.time() - t0); OUT["verdict"] = VERDICT
    json.dump(OUT, open(os.path.join(HERE, "more_trades.json"), "w"), indent=1, default=str)
    write_report(OUT)
    print("accepted:", OUT["accepted"], "runtime", OUT["runtime_s"], "s", flush=True)
