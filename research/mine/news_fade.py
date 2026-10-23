"""2026-10-19 Does the CPI09 idea (fade the 08:30->09:29 move at the 09:30 open on CPI days) work on OTHER scheduled macro releases?
Each release type is a separate hypothesis (date lists research/news_dates_<type>.csv, built by news_dates_build.py).
Real Databento NQ 1-minute 2010-06..2026-10 (nqdb.npz). Periods: A 2010-14 / B 2015-19 cost-normalised (0.345% ATR), T1 2020-23 / T2 2024-26
real $ per MNQ ($1.90 + 1 tick per side; stress 4 ticks). Steps:
 1. Spike check per list: range of the release minute / day ATR vs the median of the same minute on non-release days of the same year;
    hit = ratio >= 2. Lists with a hit rate below 50% are dropped (wrong dates or no NQ reaction).
 2. Grid (families_gold.gen_drive, release days only): anchor = release minute, entry at the next 'open' (09:30 for 08:30 releases,
    10:30 for 10:00, 14:30 for 14:00) when |move since the release| >= x ATR (x 0.03/0.05/0.1/0.2), fade (-1) or follow (+1), fixed stop
    0.25/0.35/0.5 ATR, target 0.5/1/2 R, hold 30/60/120 min; plus the 'early fade' variant (entry 1/5/15 min after the release).
    Protocol fixed before looking: chosen on T1 (n >= 30, PF >= 1.3, WR >= 60) and must hold T2 PF >= 1.2, A >= 1.0, B >= 1.0,
    T2 stress (4 ticks) >= 1.1, plateau (>= half of the one-parameter neighbours T1 PF >= 1.2 and T2 PF >= 1.0).
    The same cells on NON-release days are the control (they must not work there, otherwise it is the plain 09:30 effect).
 3. Transplant: the exact CPI09 cell (x 0.05, fade, stop 0.35 ATR, 0.5R, hold 60) on each release type - one test per type.
    Pre-registered pooled test: the CPI09 cell on all 08:30 monthly BLS/BEA/Census releases together (PPI+RETAIL+DURABLES+GDP+PCE).
 4. Survivors added to the 2027 default (nt_compare.research_set('ultra_d4'), conflict filter), Sharpe/maxDD/worst month T1/T2, 21-day
    block bootstrap of the Sharpe gain.  -> news_fade.json, news_fade_cells.csv, news_fade_report.md (written by hand from the json)."""
import os, sys, json, numpy as np, pandas as pd
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
from core import Data, run_events
from families import grid
from families_gold import gen_drive
from cpi_lab import keep_days, st, NORM, PARTS
from news import NEWS
from news_hist import CPI_ALL, NFP_ALL
from db_long import FOMC_1019

TYPES = {"PPI": 830, "RETAIL": 830, "DURABLES": 830, "GDP": 830, "PCE": 830, "CLAIMS": 830, "JOLTS": 1000, "ISM_MFG": 1000, "ISM_SERV": 1000,
         "CB_CONF": 1000, "UMICH_P": 1000, "UMICH_F": 1000, "FOMC_MIN": 1400}
ENTRY_T = {830: 60, 1000: 30, 1400: 30}                      # minutes from the release to the entry 'open'
CPI09 = dict(x=0.05, mode=-1, tf=0, k=0.35, stop=0, R=0.5, hold=60)
_D = None


def load_dates(t):
    return set(pd.read_csv(os.path.join(ROOT, f"news_dates_{t.lower()}.csv")).date.astype(int))


def getD():
    global _D
    if _D is None: _D = Data("nqdb.npz")
    return _D


def spike(D, dates, om, ctrl_days):
    """ratio = range of the release-minute bar / ATR, divided by the median ratio of the same minute on control days of the same year."""
    m = D.om == om
    r = pd.DataFrame(dict(date=D.date[m], rr=(D.h[m] - D.l[m]) / np.maximum(D.atr[D.day[m]], 1e-9)))
    r = r.groupby("date").rr.first(); yr = r.index // 10000
    base = r[r.index.isin(ctrl_days)].groupby(yr[r.index.isin(ctrl_days)]).median()
    x = r[r.index.isin(dates)]; ratio = x / x.index.map(lambda d: base.get(d // 10000, np.nan)).to_numpy()
    ratio = ratio.dropna()
    return dict(n_dates=len(dates), n_in_data=int(len(ratio)), hit_rate=float((ratio >= 2).mean()), median_ratio=float(ratio.median()),
                hit_rate_2020=float((ratio[ratio.index >= 20200101] >= 2).mean()) if (ratio.index >= 20200101).any() else None,
                hit_rate_pre2020=float((ratio[ratio.index < 20200101] >= 2).mean()) if (ratio.index < 20200101).any() else None)


def cells(om):
    T = ENTRY_T[om]
    G = grid(A=(om,), T=(T,), x=(0.03, 0.05, 0.1, 0.2), mode=(1, -1), tf=(0,), k=(0.25, 0.35, 0.5), stop=(0,), R=(0.5, 1.0, 2.0), hold=(30, 60, 120))
    G += grid(A=(om,), T=(1, 5, 15), x=(0.05, 0.1, 0.2), mode=(-1,), tf=(0,), k=(0.2, 0.35), stop=(0,), R=(0.5, 1.0), hold=(60, 240))
    return G


def evaluate(D, ev, days):
    e = keep_days(ev, D, days); row = {}
    r = run_events(D, e, flat=955, maxday=1, slip=0.25); s = run_events(D, e, flat=955, maxday=1, slip=1.0)
    nm = run_events(D, e, flat=955, maxday=1, slip=0.0, norm_cost=NORM)
    for lab, lo, hi, kind in PARTS:
        n, wr, pf, net = st(nm if kind == "n" else r, lo, hi)
        row.update({f"{lab}_n": n, f"{lab}_wr": wr, f"{lab}_pf": pf, f"{lab}_net": net})
        if kind == "r": row[f"{lab}_pf_stress"] = st(s, lo, hi)[2]
    return row


def run_type(args):
    t, dates, ctrl = args
    D = getD(); om = TYPES[t]; rows = []
    for j, p in enumerate(cells(om)):
        ev = gen_drive(D, p)
        for tag, days in (("rel", dates), ("ctrl", ctrl)):
            rows.append(dict(type=t, j=j, days=tag, params=repr(p), **evaluate(D, ev, days)))
    return rows


def transplant(D, t, dates):
    om = TYPES[t]; p = dict(A=om, T=ENTRY_T[om], **CPI09)
    return dict(type=t, params=repr(p), **evaluate(D, gen_drive(D, p), dates))


def transplant_trades(D, t, dates, norm=False):
    om = TYPES[t]; p = dict(A=om, T=ENTRY_T[om], **CPI09)
    df = run_events(D, keep_days(gen_drive(D, p), D, dates), flat=955, maxday=1, slip=0.0 if norm else 0.25, norm_cost=NORM if norm else None)
    return pd.DataFrame(dict(date=df.date, mod=t[:3] + "09", tin=D.sm[df.fi.to_numpy().astype(int)], tout=D.sm[df.xi.to_numpy().astype(int)] + 1, d=df.d, u=df.usd, w=1.0))


def passes(C):
    """Protocol columns on the release-day grid of one type."""
    C = C.copy()
    C["t1_ok"] = (C.T1_n >= 30) & (C.T1_pf >= 1.3) & (C.T1_wr >= 60)
    C["t2_ok"] = (C.T2_pf >= 1.2) & (C.T2_pf_stress >= 1.1) & (C.A_pf >= 1.0) & (C.B_pf >= 1.0)
    P = C.params.map(eval); keys = ["x", "mode", "k", "R", "hold", "T"]
    plat = []
    for i, r in C.iterrows():
        p = P[i]; nb = [jj for jj, q in P.items() if jj != i and sum(q[kk] != p[kk] for kk in keys) == 1]
        if not nb: plat.append(False); continue
        sub = C.loc[nb]; plat.append(bool(((sub.T1_pf >= 1.2) & (sub.T2_pf >= 1.0)).mean() >= 0.5))
    C["plateau"] = plat
    C["survivor"] = C.t1_ok & C.t2_ok & C.plateau
    return C


def port_metrics(X, days):
    x = X.u * X.w; d = x.groupby(X.date).sum().reindex(days, fill_value=0.0); eq = d.cumsum(); mo = d.groupby(np.asarray(days) // 100).sum()
    return dict(n=int(len(X)), net=float(x.sum()), pf=float(x[x > 0].sum() / -x[x <= 0].sum()), sharpe=float(d.mean() / d.std() * np.sqrt(252)),
                maxdd=float((eq.cummax() - eq).max()), worst_month=float(mo.min()), usd_mo=float(d.mean() * 21))


def block_boot(d0, d1, B=1000, L=21, seed=7):
    rng = np.random.default_rng(seed); n = len(d0); nb = n // L + 1; out = []
    a0 = d0.to_numpy(); a1 = d1.to_numpy()
    for _ in range(B):
        ix = np.concatenate([np.arange(s, s + L) for s in rng.integers(0, n - L, nb)])[:n]
        s0 = a0[ix].mean() / a0[ix].std() * np.sqrt(252); s1 = a1[ix].mean() / a1[ix].std() * np.sqrt(252); out.append(s1 - s0)
    out = np.array(out); return dict(mean=float(out.mean()), p10=float(np.percentile(out, 10)), p50=float(np.median(out)), p90=float(np.percentile(out, 90)), p_gain=float((out > 0).mean()))


def portfolio(D, adds):
    from nt_compare import research_set
    from wrq_port import conflict_filter
    X0, _ = research_set("ultra_d4")
    fomc = set(NEWS["FOMC"]) | set(FOMC_1019)
    days = np.array(sorted(set(D.daydate[D.ro >= 0]))); days = days[(days >= X0.date.min()) & (days <= X0.date.max()) & ~np.isin(days, list(fomc))]
    out = {}
    for name, T in adds.items():
        X1 = pd.concat([X0, T[T.date.isin(days)]], ignore_index=True).sort_values(["date", "tin"], kind="stable").reset_index(drop=True)
        X1 = conflict_filter(X1)
        rec = {}
        for lab, lo, hi in (("T1", 20200101, 20240101), ("T2", 20240101, 20991231)):
            dd = days[(days >= lo) & (days < hi)]
            m0 = port_metrics(X0[(X0.date >= lo) & (X0.date < hi)], dd); m1 = port_metrics(X1[(X1.date >= lo) & (X1.date < hi)], dd)
            d0 = (X0.u * X0.w).groupby(X0.date).sum().reindex(dd, fill_value=0.0); d1 = (X1.u * X1.w).groupby(X1.date).sum().reindex(dd, fill_value=0.0)
            rec[lab] = dict(without=m0, with_=m1, added_trades_kept=int((X1["mod"] == T["mod"].iloc[0]).sum()) if len(T) else 0, boot=block_boot(d0, d1))
        out[name] = rec
    return out


if __name__ == "__main__":
    D = getD()
    alld = set(D.daydate[D.daydate > 0])
    lists = {t: load_dates(t) & alld for t in TYPES}
    news_all = set().union(*lists.values()) | set(CPI_ALL) | set(NFP_ALL) | set(NEWS["FOMC"]) | set(FOMC_1019)
    ctrl = alld - news_all
    # 1. spike validation (CPI and NFP as references)
    spk = {t: spike(D, lists[t], TYPES[t] // 100 * 60 + TYPES[t] % 100, ctrl) for t in TYPES}
    spk["CPI_ref"] = spike(D, set(CPI_ALL) & alld, 510, ctrl); spk["NFP_ref"] = spike(D, set(NFP_ALL) & alld, 510, ctrl)
    for k, v in spk.items(): print(f"spike {k:9s} n={v['n_in_data']:4d} hit={v['hit_rate']:.2f} (pre20 {v['hit_rate_pre2020']}, 2020+ {v['hit_rate_2020']}) median ratio {v['median_ratio']:.2f}", flush=True)
    usable = [t for t in TYPES if spk[t]["hit_rate"] >= 0.5]
    print("usable lists:", usable, flush=True)
    # 2. grids (2 processes)
    with Pool(2) as pool: res = pool.map(run_type, [(t, lists[t], ctrl) for t in usable])
    R = pd.DataFrame([r for rr in res for r in rr]); R.to_csv(os.path.join(HERE, "news_fade_cells.csv"), index=False)
    per_type = {}
    for t in usable:
        C = passes(R[(R.type == t) & (R.days == "rel")].set_index("j")); K = R[(R.type == t) & (R.days == "ctrl")].set_index("j")
        sel = C[C.t1_ok]; surv = C[C.survivor]
        ctrl_same = K.loc[surv.index] if len(surv) else K.iloc[0:0]
        per_type[t] = dict(n_cells=int(len(C)), median_pf={lab: float(C[f"{lab}_pf"].median()) for lab, *_ in PARTS},
                           median_pf_ctrl={lab: float(K[f"{lab}_pf"].median()) for lab, *_ in PARTS},
                           t1_pass=int(len(sel)), base_rate_t2=float((C.T2_pf >= 1.2).mean()), t2_given_t1=float((sel.T2_pf >= 1.2).mean()) if len(sel) else None,
                           all_pass=int(len(surv)), n_fade_t1_pass=int(sum(eval(s)["mode"] == -1 for s in sel.params)),
                           best_t1=C.sort_values("T1_pf", ascending=False).head(5)[["params", "T1_n", "T1_wr", "T1_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf_stress", "A_pf", "B_pf", "plateau"]].to_dict("records"),
                           survivors=surv[["params", "A_n", "A_pf", "B_n", "B_pf", "T1_n", "T1_wr", "T1_pf", "T2_n", "T2_wr", "T2_pf", "T2_pf_stress"]].to_dict("records"),
                           survivors_on_ctrl=ctrl_same[["params", "A_pf", "B_pf", "T1_n", "T1_wr", "T1_pf", "T2_n", "T2_wr", "T2_pf"]].to_dict("records"))
        print(f"{t:9s} cells {len(C)} T1 pass {len(sel)} (fade {per_type[t]['n_fade_t1_pass']}) all {len(surv)} | median PF rel A/B/T1/T2 "
              f"{per_type[t]['median_pf']['A']:.2f}/{per_type[t]['median_pf']['B']:.2f}/{per_type[t]['median_pf']['T1']:.2f}/{per_type[t]['median_pf']['T2']:.2f} "
              f"ctrl {per_type[t]['median_pf_ctrl']['T1']:.2f}/{per_type[t]['median_pf_ctrl']['T2']:.2f}", flush=True)
    # 3. transplanted CPI09 cell (one per type + pre-registered 08:30 pool + control)
    tr = {t: transplant(D, t, lists[t]) for t in usable}
    tr["CPI_ref"] = transplant(D, "PPI", set(CPI_ALL) & alld)
    pool830 = set().union(*[lists[t] for t in ("PPI", "RETAIL", "DURABLES", "GDP", "PCE") if t in usable]) - set(CPI_ALL)
    tr["POOL_0830_monthly"] = transplant(D, "PPI", pool830)
    tr["CTRL_0830"] = transplant(D, "PPI", ctrl); tr["CTRL_1000"] = transplant(D, "JOLTS", ctrl)
    for k, v in tr.items(): print(f"transplant {k:18s} n A/B/T1/T2 {v['A_n']}/{v['B_n']}/{v['T1_n']}/{v['T2_n']} PF {v['A_pf']}/{v['B_pf']}/{v['T1_pf']}/{v['T2_pf']} (T2 stress {v['T2_pf_stress']}) WR T1/T2 {v['T1_wr']}/{v['T2_wr']}", flush=True)
    tr_pass = {k: bool(v["T1_n"] >= 30 and v["T1_pf"] >= 1.3 and v["T1_wr"] >= 60 and v["T2_pf"] >= 1.2 and v["T2_pf_stress"] >= 1.1 and v["A_pf"] >= 1.0 and v["B_pf"] >= 1.0)
               for k, v in tr.items() if k not in ("CPI_ref", "CTRL_0830", "CTRL_1000")}
    # 4. portfolio: grid survivors' types (CPI09 cell as the representative rule, to avoid picking the best cell) + transplant passers
    cand = sorted({t for t in usable if per_type[t]["all_pass"] > 0} | {k for k, v in tr_pass.items() if v and k in TYPES})
    adds = {t: transplant_trades(D, t, lists[t]) for t in cand}
    if "POOL_0830_monthly" in tr_pass and tr_pass["POOL_0830_monthly"]: adds["POOL_0830_monthly"] = transplant_trades(D, "PPI", pool830).assign(mod="POOL09")
    port = portfolio(D, adds) if adds else {}
    for k, v in port.items():
        for lab in ("T1", "T2"):
            a, b = v[lab]["without"], v[lab]["with_"]
            print(f"portfolio +{k} {lab}: Sharpe {a['sharpe']:.2f}->{b['sharpe']:.2f} $/mo {a['usd_mo']:.0f}->{b['usd_mo']:.0f} maxDD {a['maxdd']:.0f}->{b['maxdd']:.0f} worst mo {a['worst_month']:.0f}->{b['worst_month']:.0f} boot dSharpe p50 {v[lab]['boot']['p50']:.2f} [{v[lab]['boot']['p10']:.2f},{v[lab]['boot']['p90']:.2f}] P(gain) {v[lab]['boot']['p_gain']:.2f}", flush=True)
    out = dict(spike=spk, usable=usable, dropped=[t for t in TYPES if t not in usable], n_dates_in_data={t: len(lists[t]) for t in TYPES},
               grid=per_type, transplant=tr, transplant_pass=tr_pass, pool_0830_n_dates=len(pool830), candidates=cand, portfolio=port)
    json.dump(out, open(os.path.join(HERE, "news_fade.json"), "w"), indent=1, default=str)
    print("done")
