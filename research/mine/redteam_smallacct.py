"""RED TEAM of the 2026-10-13 small-account study (smallacct_*.py). Independent, clean-room re-implementation of the Lucid Flex eval
(EOD trailing drawdown with lock, consistency, daily profit stop) and the serial-restart protocol, written from the rules only (no import of
mffu_rapid / robust2_life / smallacct_*). Same day paths (scratchpad smallacct_paths.pkl). Plain Python + numpy.
Sections: A reproduction, B biases (overlap bootstrap, path bootstrap, calendar days, profit-stop latency, edge haircut), C rule sensitivity,
claim-2 G grid with paired bootstrap, claim-3 start-day timing.  -> redteam_smallacct.json (numbers used in redteam_smallacct.md)"""
import os, json, pickle, time, numpy as np

SP = "/tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad"
HERE = os.path.dirname(os.path.abspath(__file__))
days, P = pickle.load(open(os.path.join(SP, "smallacct_paths.pkl"), "rb"))
n = len(days)
CAL = np.load(os.path.join(SP, "redteam_cal.npz"))      # full RTH calendar 2020-26 + daily ATR (written once from wrq_lib.getD)
cal, cal_atr = CAL["dd"], CAL["atr"]
calpos = np.searchsorted(cal, days)
assert (cal[calpos] == days).all()
H = 120


# ---------------------------------------------------------------- day vectors -------------------------------------------------------------
def day_vectors(prof, cap, G=0.0, ticks=0, haircut=0.0, latency=0):
    """per-day (intraday equity low, end-of-day P&L) per base contract.  G > 0: account daily profit stop -> the day ends at the first minute
    whose mark-to-market close >= G (exit at that minute's close, or `latency` minutes later).  ticks: extra ticks per side ($1 per contract
    traded per extra tick per side round trip).  haircut: $ removed from every day (edge haircut)."""
    low, close, fin = P[(prof, cap)]
    c = P[(prof, cap, "cost")] * ticks + haircut
    low = low - (c if np.ndim(c) == 0 else c[:, None]); close = close - (c if np.ndim(c) == 0 else c[:, None]); fin = fin - c
    lo = low.min(1).copy(); cl = np.array(fin, dtype=float).copy()
    if G > 0:
        hit = close >= G
        for d in np.nonzero(hit.any(1))[0]:
            t = int(np.argmax(hit[d])); te = min(t + latency, 1439)
            lo[d] = low[d, :te + 1].min(); cl[d] = close[d, te]
    lo = np.minimum(lo, cl)
    return lo, cl


# ---------------------------------------------------------------- one eval ----------------------------------------------------------------
def run_eval(LO, CL, s, T, D, cons, lock=100.0, C=None, LO0=None, CL0=None, hmax=H):
    """Lucid-Flex-style eval from day s. Threshold = (max end-of-day balance so far) - D, frozen at +lock once that max reaches D + lock.
    Bust if intraday low touches the threshold. Pass at the close of a day with profit >= T and best day <= cons x profit.
    Optional 2 gears: below cushion C (balance - threshold at day start) use LO0/CL0.  returns (+1 pass / -1 bust / 0 open, days used)"""
    bal = 0.0; peak = 0.0; best = -1e18; m = len(LO)
    for k in range(hmax):
        d = s + k
        if d >= m: return 0, k
        thr = min(peak - D, lock)
        if C is not None and bal - thr < C: lo, cl = LO0[d], CL0[d]
        else: lo, cl = LO[d], CL[d]
        if bal + lo <= thr: return -1, k + 1
        bal += cl
        if cl > best: best = cl
        if bal > peak: peak = bal
        if bal >= T and (cons <= 0 or best <= cons * bal): return 1, k + 1
    return 0, hmax


def all_starts(LO, CL, T, D, cons, **kw):
    m = len(LO); res = np.zeros(m, np.int8); ln = np.zeros(m, np.int32)
    LO = LO.tolist(); CL = CL.tolist()
    if kw.get("LO0") is not None: kw["LO0"] = kw["LO0"].tolist(); kw["CL0"] = kw["CL0"].tolist()
    for s in range(m): res[s], ln[s] = run_eval(LO, CL, s, T, D, cons, **kw)
    return res, ln


def serial(res, ln, s0):
    """eval at s0, after each bust a new eval the next day. returns (index of the pass day or -1, evals bought)"""
    s = s0; k = 0; m = len(res)
    while s < m:
        k += 1
        if res[s] == 1: return s + ln[s] - 1, k
        if res[s] == -1: s = s + ln[s]; continue
        return -1, k
    return -1, k


def funded_within(res, ln, starts, W, pos=None, their_convention=False):
    """1/0 per start: funded (pass day) within W days counted on the day list (pos None) or on calendar positions pos.
    their_convention: smallacct_protocol counts pass-day offset <= W (i.e. W+1 days incl. the start day)."""
    out = np.zeros(len(starts)); ev = np.zeros(len(starts))
    for i, s0 in enumerate(starts):
        j, k = serial(res, ln, s0); ev[i] = k
        if j < 0: continue
        el = (j - s0 + 1) if pos is None else (pos[j] - pos[s0] + 1)
        out[i] = el <= (W + 1 if their_convention else W)
    return out, ev


def single_stats(res, ln, starts, W=22):
    r = res[starts]; l = ln[starts]
    return dict(p22=round(100 * float(np.mean((r == 1) & (l <= W))), 1), ever=round(100 * float(np.mean(r == 1)), 1),
                bust=round(100 * float(np.mean(r == -1)), 1), med=float(np.median(l[r == 1])) if (r == 1).any() else None)


# start-day sets exactly as in the study
S1e = np.nonzero((days >= 20200301) & (days < 20240101))[0]; S1e = S1e[S1e < n - 120]
S2e = np.nonzero(days >= 20240101)[0]; S2e = S2e[S2e < n - 120]
S1p = np.nonzero((days >= 20200301) & (days < 20231101))[0]
S2p = np.nonzero(days >= 20240101)[0]; S2p = S2p[S2p < n - 50]

ACC = {"25K": dict(T=1250.0, D=1000.0, cons=0.5), "50K": dict(T=3000.0, D=2000.0, cons=0.5)}


def setup(acc, prof="UltraR", cap=0, ticks=0, G=None, gate=None, haircut=0.0, latency=0, T=None, D=None, cons=None):
    a = dict(ACC[acc]);
    if T is not None: a["T"] = T
    if D is not None: a["D"] = D
    if cons is not None: a["cons"] = cons
    if G is None: G = 0.9 * a["cons"] * a["T"] if a["cons"] > 0 else 0.0
    LO, CL = day_vectors(prof, cap, G, ticks, haircut, latency)
    kw = {}
    if gate is not None:                                  # gate = (low profile, cap, cushion)
        L0, C0 = day_vectors(gate[0], gate[1], G, ticks, haircut, latency); kw = dict(C=gate[2], LO0=L0, CL0=C0)
    return (LO, CL, a, kw)


def outcomes(st):
    LO, CL, a, kw = st
    return all_starts(LO, CL, a["T"], a["D"], a["cons"], **kw)


def summary(res, ln):
    f1, e1 = funded_within(res, ln, S1p, 22); f2, e2 = funded_within(res, ln, S2p, 22)
    g1, _ = funded_within(res, ln, S1p, 22, their_convention=True); g2, _ = funded_within(res, ln, S2p, 22, their_convention=True)
    c1, _ = funded_within(res, ln, S1p, 22, pos=calpos); c2, _ = funded_within(res, ln, S2p, 22, pos=calpos)
    w1, _ = funded_within(res, ln, S1p, 33); w2, _ = funded_within(res, ln, S2p, 33)
    return dict(single_T1=single_stats(res, ln, S1e), single_T2=single_stats(res, ln, S2e),
                serial22_T1=round(100 * f1.mean(), 1), serial22_T2=round(100 * f2.mean(), 1),
                serial22_theirconv_T1=round(100 * g1.mean(), 1), serial22_theirconv_T2=round(100 * g2.mean(), 1),
                serial22_calendar_T1=round(100 * c1.mean(), 1), serial22_calendar_T2=round(100 * c2.mean(), 1),
                serial33_T1=round(100 * w1.mean(), 1), serial33_T2=round(100 * w2.mean(), 1),
                evals_T1=round(float(e1.mean()), 2), evals_T2=round(float(e2.mean()), 2))


def mbb_diff(a, b, L, R=4000, seed=1):
    """moving-block bootstrap of mean(a) - mean(b) over start days (paired), block length L"""
    rng = np.random.default_rng(seed); N = len(a); nb = int(np.ceil(N / L)); d = a - b; out = np.empty(R)
    for r in range(R):
        st = rng.integers(0, N - L + 1, nb); idx = (st[:, None] + np.arange(L)).ravel()[:N]; out[r] = d[idx].mean()
    return [round(100 * float(np.percentile(out, q)), 1) for q in (2.5, 50, 97.5)]


def mbb_mean(a, L, R=4000, seed=2):
    return mbb_diff(a, np.zeros_like(a), L, R, seed)


if __name__ == "__main__" and os.environ.get("RT_ONLY_LOW") != "1":
    t0 = time.time(); OUT = {}
    # ---------------- A. reproduction --------------------------------------------------------------------------------------------------
    A = {}
    cfgA = {"25K pick (Estable<250 gear)": dict(acc="25K", gate=("Estable", 0, 250.0)), "25K no gating": dict(acc="25K"),
            "25K no gating +1 tick": dict(acc="25K", ticks=1), "50K (UltraR150 f=0 = no gating)": dict(acc="50K"),
            "50K +1 tick": dict(acc="50K", ticks=1)}
    RES = {}
    for k, c in cfgA.items():
        res, ln = outcomes(setup(**c)); RES[k] = (res, ln); A[k] = summary(res, ln); print("A", k, A[k], round(time.time() - t0), flush=True)
    OUT["A"] = A
    # ---------------- B1. overlapping starts: block bootstrap of 25K - 50K (serial funded <= 22 d) ---------------------------------------
    B = {}
    for per, S in (("T1", S1p), ("T2", S2p)):
        a, _ = funded_within(*RES["25K pick (Estable<250 gear)"], S, 22); b, _ = funded_within(*RES["50K (UltraR150 f=0 = no gating)"], S, 22)
        B[per] = dict(diff=round(100 * (a.mean() - b.mean()), 1), n_starts=len(S),
                      **{f"CI95_block{L}": mbb_diff(a, b, L) for L in (10, 22, 44, 66)},
                      **{f"25K_CI95_block{L}": mbb_mean(a, L) for L in (10, 44)}, **{f"50K_CI95_block{L}": mbb_mean(b, L) for L in (10, 44)})
        # autocorrelation of the start indicator: effective number of independent starts
        def neff(x):
            x = x - x.mean(); v = (x * x).mean(); s = 0.0
            for lag in range(1, 120):
                r = (x[:-lag] * x[lag:]).mean() / v
                if r < 0.05: break
                s += r
            return int(len(x) / (1 + 2 * s))
        B[per]["n_eff_25K"] = neff(a); B[per]["n_eff_50K"] = neff(b)
    print("B1", B, flush=True)
    # ---------------- B2. path-level block bootstrap (10-day blocks of real days inside each period) --------------------------------------
    st25 = setup("25K", gate=("Estable", 0, 250.0)); st50 = setup("50K")
    PB = {}
    for per, lo_, hi_ in (("T1", 20200301, 20231101), ("T2", 20240101, 99999999)):
        pos = np.nonzero((days >= lo_) & (days < hi_))[0]; rng = np.random.default_rng(7); diffs = []; v25 = []; v50 = []
        Lsyn = len(pos) + 60
        for r in range(150):
            st = rng.integers(0, len(pos) - 10, Lsyn // 10 + 1); idx = np.concatenate([pos[s:s + 10] for s in st])[:Lsyn]
            out = []
            for (LO, CL, a, kw) in (st25, st50):
                kw2 = dict(kw)
                if kw: kw2["LO0"] = kw["LO0"][idx]; kw2["CL0"] = kw["CL0"][idx]
                res, ln = all_starts(LO[idx], CL[idx], a["T"], a["D"], a["cons"], **kw2)
                f, _ = funded_within(res, ln, np.arange(Lsyn - 60), 22); out.append(f.mean())
            v25.append(out[0]); v50.append(out[1]); diffs.append(out[0] - out[1])
        q = lambda x: [round(100 * float(np.percentile(x, p)), 1) for p in (2.5, 50, 97.5)]
        PB[per] = dict(serial22_25K=q(v25), serial22_50K=q(v50), diff=q(diffs), P_diff_le_10=round(100 * float(np.mean(np.array(diffs) <= 0.10)), 1))
        print("B2", per, PB[per], round(time.time() - t0), flush=True)
    OUT["B_overlap"] = B; OUT["B_pathboot"] = PB
    # ---------------- B3. excluded days -------------------------------------------------------------------------------------------------
    ex = {}
    for per, lo_, hi_ in (("T1", 20200301, 20231101), ("T2", 20240101, 99999999)):
        m = (cal >= lo_) & (cal < hi_); ml = (days >= lo_) & (days < hi_)
        ex[per] = dict(calendar_days=int(m.sum()), list_days=int(ml.sum()), missing_pct=round(100 * (1 - ml.sum() / m.sum()), 1),
                       list22_equals_calendar=round(22 * m.sum() / ml.sum(), 1))
    OUT["B_excluded_days"] = ex; print("B3", ex, flush=True)
    # ---------------- B4. profit-stop latency and bust-level stress ---------------------------------------------------------------------
    B4 = {}
    for lab, c in {"25K stop exit 1 min late": dict(acc="25K", latency=1), "25K stop exit 3 min late": dict(acc="25K", latency=3),
                   "50K stop exit 3 min late": dict(acc="50K", latency=3)}.items():
        res, ln = outcomes(setup(**c)); s = summary(res, ln); B4[lab] = {k: s[k] for k in ("serial22_T1", "serial22_T2")}; print("B4", lab, B4[lab], flush=True)
    OUT["B_latency"] = B4
    # ---------------- B5. edge haircut (as the study, % of period mean daily P&L, plus 1 tick) -------------------------------------------
    fin = P[("UltraR", 0)][2]; mu1 = fin[S1p].mean(); mu2 = fin[S2p].mean(); HC = {}
    for hc in (0.0, 0.35, 0.6, 1.0):
        h = np.where(np.arange(n) < S2p[0], hc * mu1, hc * mu2); row = {}
        for acc in ("25K", "50K"):
            res, ln = outcomes(setup(acc, ticks=1, haircut=h)); s = summary(res, ln); row[acc] = (s["serial22_T1"], s["serial22_T2"])
        HC[f"edge-{int(hc * 100)}%"] = row; print("B5", hc, row, flush=True)
    OUT["B_haircut"] = HC
    # ---------------- C. rule sensitivity (25K, no gating) ------------------------------------------------------------------------------
    C = {}
    grid = {"base T1250 D1000 c50 +0t": {}, "+1 tick/side": dict(ticks=1), "+2 ticks/side": dict(ticks=2),
            "D 900": dict(D=900.0), "D 1100": dict(D=1100.0), "T 1500": dict(T=1500.0), "cons 40%": dict(cons=0.4), "cons none (no stop)": dict(cons=0.0),
            "cons none, stop 562": dict(cons=0.0, G=562.5), "D 900 +1t": dict(D=900.0, ticks=1), "T 1500 D 900 +2t": dict(T=1500.0, D=900.0, ticks=2),
            "T 1500 cons 40% +1t": dict(T=1500.0, cons=0.4, ticks=1)}
    for lab, kw in grid.items():
        res, ln = outcomes(setup("25K", **kw)); s = summary(res, ln)
        C[lab] = dict(single_p22_T1=s["single_T1"]["p22"], single_p22_T2=s["single_T2"]["p22"], serial22_T1=s["serial22_T1"], serial22_T2=s["serial22_T2"],
                      serial22_cal_T1=s["serial22_calendar_T1"], serial22_cal_T2=s["serial22_calendar_T2"], evals_T2=s["evals_T2"])
        print("C", lab, C[lab], flush=True)
    OUT["C_sensitivity"] = C
    # ---------------- claim 2: G grid, +1 tick, paired block bootstrap vs the claimed G -------------------------------------------------
    G2 = {}
    for acc, gs, g0 in (("25K", (350, 450, 500, 562.5, 625, 700, 900, 0), 562.5), ("50K", (700, 1000, 1200, 1350, 1500, 1700, 2000, 0), 1350)):
        F = {}
        for g in gs:
            res, ln = outcomes(setup(acc, ticks=1, G=float(g)))
            F[g] = (funded_within(res, ln, S1p, 22)[0], funded_within(res, ln, S2p, 22)[0])
        rows = {}
        for g in gs:
            rows[str(g)] = dict(T1=round(100 * F[g][0].mean(), 1), T2=round(100 * F[g][1].mean(), 1),
                                dT1_vs_claim_CI44=mbb_diff(F[g][0], F[g0][0], 44), dT2_vs_claim_CI44=mbb_diff(F[g][1], F[g0][1], 44))
        G2[acc] = rows; print("G", acc, {k: (v["T1"], v["T2"]) for k, v in rows.items()}, flush=True)
    OUT["claim2_G"] = G2
    # ---------------- claim 3: start-day timing (no gating, serial 22 d) -----------------------------------------------------------------
    import pandas as pd
    atr = pd.Series(cal_atr, index=cal); ratio = (atr / atr.rolling(60, min_periods=30).median()).reindex(days).to_numpy()
    prev10 = pd.Series(fin).rolling(10).sum().shift(1).to_numpy()
    TM = {}
    for acc in ("25K", "50K"):
        res, ln = outcomes(setup(acc)); r = {}
        for per, S in (("T1", S1p[days[S1p] >= 20200501]), ("T2", S2p)):
            f, _ = funded_within(res, ln, S, 22)
            for gname, mk in (("ATR<=1.15", ratio[S] <= 1.15), ("prev10<=0", prev10[S] <= 0)):
                a = f[mk]; b = f[~mk]
                # block bootstrap of subset - complement: resample blocks of start days, keep labels
                rng = np.random.default_rng(3); L = 22; nb = int(np.ceil(len(f) / L)); ds = []
                for _ in range(3000):
                    st = rng.integers(0, len(f) - L + 1, nb); idx = (st[:, None] + np.arange(L)).ravel()[:len(f)]
                    mm = mk[idx]
                    if mm.any() and (~mm).any(): ds.append(f[idx][mm].mean() - f[idx][~mm].mean())
                r[f"{per} {gname}"] = dict(subset=round(100 * a.mean(), 1), rest=round(100 * b.mean(), 1), n=int(mk.sum()),
                                          diff_CI95=[round(100 * float(np.percentile(ds, q)), 1) for q in (2.5, 50, 97.5)])
        TM[acc] = r; print("T", acc, r, flush=True)
    OUT["claim3_timing"] = TM
    json.dump(OUT, open(os.path.join(HERE, "redteam_smallacct.json"), "w"), indent=1, default=float)
    print("done", round(time.time() - t0), "s")


def low_sensitivity():
    """B6: how much do busts depend on the intraday-low measurement?  close-only low (optimistic bound: only end-of-day / stop-day P&L
    can breach) vs the study's bar-extreme open-trade low vs low - $100 / - $200 (e.g. stop slippage or a later-minute extreme)."""
    out = {}
    for acc in ("25K", "50K"):
        LO, CL, a, kw = setup(acc, ticks=1)
        for lab, L in (("close-only low", np.minimum(CL, 0.0)), ("study low", LO), ("low - $100", LO - 100), ("low - $200", LO - 200)):
            res, ln = all_starts(L, CL, a["T"], a["D"], a["cons"]); s = summary(res, ln)
            out[f"{acc} {lab}"] = (s["serial22_T1"], s["serial22_T2"], s["single_T2"]["bust"])
    return out


if __name__ == "__main__":
    o = json.load(open(os.path.join(HERE, "redteam_smallacct.json"))); o["B_low"] = low_sensitivity(); print(o["B_low"])
    json.dump(o, open(os.path.join(HERE, "redteam_smallacct.json"), "w"), indent=1, default=float)
