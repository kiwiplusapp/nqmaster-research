"""prop_wf.py (2026-10-21): pre-registered WALK-FORWARD prop-policy optimizer on the CURRENT NQ-only system
(2027 default = Ultra as coded + durable six-year modules SO04/RV11/ORFAIL/CAM3, MOM1030/CPI09 x4; GoldMaster OFF).
Paths: acct2027_paths.pkl (real Databento NQ 2020-02..2026-10, $1.90 + 1 tick per side already in; extra +1 tick 'cc' subtracted as in
lucidpro_week.mats) minus seats_plan.gold_paths('Robust') = NQ only.  Nothing is rebuilt.

PRE-REGISTRATION (written before any result was looked at)
  Periods  T1 = eval/funded starts 2020-02-26..2022-12-30 (CHOOSE), T2 = starts 2023-01-03..2026-09-30 (CHECK, never used to choose).
  Edge     haircut hc in {0, 0.35, 1.0}: per mix and period, h = hc x mean daily P&L of THAT mix (1 contract) in that period, subtracted
           every day and multiplied by the contracts traded (haircut scales with size and with the MOM1030/CPI09 lot mix).
  EVAL policy space (per firm): size  fixed k in {1,2,3,4} | cushion gear k = kA if cushion >= C else kB (kA != kB in 1..4,
           C in {1000,1500,2500,3000}; cushion = equity - EOD trailing threshold, start 2000) | late gear: kA, from eval day dL
           (dL in {5,10}) kB while profit < 1500 ((kA,kB) in (1,2),(1,3),(2,3),(2,4),(3,4)); x intraday ACCOUNT stop L in {0,600,900,1200};
           daily profit stop G only where consistency exists (Flex 1350, MFFU 800 = presets); MFFU max 3 contracts (30 micros).
           Minute race: bust when equity + open low <= threshold; pass the minute equity >= target (EvalTarget flattens) and the
           consistency rule holds; MFFU 4 minimum days (assumed met with a token trade once the target is reached).
           Serial restarts: a new eval / reset the day after a bust, up to N in {1,3} inside the window.
           PRIMARY eval metric: P(funded within 22 trading days, N <= 3).  Others: P(<=10 d, N<=3), P(<=22 d single), P(<=120 d, N<=3),
           expected fees of the 22-day plan, P per $100 of fees.
  FUNDED policy space: k in {1,2}; RiskCapPerContract 300 below cushion c in {0,750,1000,1500} (+2000 MFFU = preset);
           account daily profit stop G in {0,500,700,1000,1500} (Lucid Pro only: 40% cycle consistency); payout request X
           (Pro: amount >= 500 or full cap -> X in {500, 2000}; Flex: balance >= {2500,4000,5000}; MFFU keep B in {2600,4100,6100});
           DailyLossPerContract L in {0,1500}; MFFU also the existing ladder recipe (S 3000, K 4, keep 11,100, cap below 2000, L 0/1500).
           PRIMARY funded metric: P(>= 1 payout within 62 trading days (~90 calendar days) of the funded start).
           Others: P(payout <= 41 / 124 td), P(survive 252 td), E cash in 12 months, 12-month seat median $/month (eval + funded + re-buys).
  Selection: T1-best by the primary metric at full edge; if a simpler policy (fixed size / no stop; funded: fewer non-default knobs)
           is within 1.0 pt on T1 it is chosen instead.  ACCEPT only if on T2: bootstrap P(gain) >= 0.8 on the primary (21-day blocks,
           B = 300, same resampled paths for both), not worse by > 5% (relative) on the other metrics incl. seat $/month, and still
           >= the current setup on T2 at 35% haircut.  Base rate: P(T2 top-10% | T1 top-10%) across the policy grid.
  Current setups: Lucid Pro 50K eval 4c (no stop, DLL OFF) serial; funded 1c, FundedProfitStop 1000, cap 300 below 1000, payout at 4,100.
           Lucid Flex 50K (preset Lucid50K 2c): eval 2c + stop 1350; funded 2c cap 300 below 1000, payout at 4,000.
           MFFU 50K (preset Mffu50K): eval 1c x8 high-WR lots + stop 800; funded 1c cap 300 below 2000, keep 4,100.
Run: python3 prop_wf.py eval <firm...> | funded | boot | report   (results in scratchpad parts, merged into prop_wf.json)"""
import os, sys, json, time, pickle, itertools, numpy as np, pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OWN = "/tmp/claude-0/-home-user-nqmaster-research/176a42ca-c215-52e2-84dc-57e214e477d4/scratchpad"
SRC = "/tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad/acct2027_paths.pkl"
MIXF = os.path.join(OWN, "prop_wf_mix.pkl")
T1_END, T2_END = 20230101, 20261001
HC = (0.0, 0.35, 1.0)
NBOOT = int(os.environ.get("NBOOT", "300"))
FIRMS = {
    "LucidPro50K": dict(T=3000.0, D=2000.0, cons=0.0, mind=1, G=0.0, fee=115.4, kmax=4, fund="pro", cap1=2000.0, cap2=2500.0, npmax=5),
    "LucidFlex50K": dict(T=3000.0, D=2000.0, cons=0.5, mind=1, G=1350.0, fee=105.2, kmax=4, fund="flex", Q=150.0, cap1=2000.0, npmax=5),
    "MFFU50K": dict(T=3000.0, D=2000.0, cons=0.3, mind=4, G=800.0, fee=157.0, kmax=3, fund="mffu", npmax=0),
}
# firm-survey plans (propfirms_2026-10-21.json, survey agent): best eval geometry, generic funded model (fund firm 4)
SURVEY = {"BulenoxOpt1_50K": ("Bulenox Opt1", 4), "FundedNextRapidPro50K": ("FundedNext Rapid Pro", 4), "MFFUBuilder50K": ("MFFU Builder", 3)}
_SJ = os.path.join(HERE, "propfirms_2026-10-21.json")
if os.path.exists(_SJ):
    _pl = json.load(open(_SJ))["plans_50k"]
    for _fid, (_pre, _km) in SURVEY.items():
        _nm = [q for q in _pl if q.startswith(_pre)][0]; _p = _pl[_nm]
        FIRMS[_fid] = dict(T=float(_p["T"]), D=float(_p["D"]), cons=float(_p["cons"]), mind=max(1, int(_p["mind"])), G=0.0 if not _p["cons"] else 0.9 * _p["cons"] * _p["T"],
                           fee=float(_p["price"]), act=float(_p["act"]), kmax=_km, trail=_p["trail"], lock=float(_p["lock"]), dll=float(_p["dll"]), hard=int(_p["hard"]),
                           fund="gen", npmax=int(_p["funded"]["npmax"]), FF=_p["funded"], plan=_nm)
CUR_EVAL = {"LucidPro50K": "fix4 L0", "LucidFlex50K": "fix2 L0", "MFFU50K": "fix1x8 L0"}
CUR_FUND = {"LucidPro50K": "k1 c1000 G1000 X2000 L0", "LucidFlex50K": "k2 c1000 X4000 L0", "MFFU50K": "k1 c2000 B4100 L0"}
for _fid in SURVEY:                                     # survey baseline: eval fixed k (survey's choice), funded 1c, payout ASAP
    if _fid in FIRMS: CUR_EVAL[_fid] = f"fix{FIRMS[_fid]['kmax']} L0"; CUR_FUND[_fid] = "k1 c0 G0 X0 L0"


# ------------------------------------------------------------------ data
def build_mix():
    if os.path.exists(MIXF): return pickle.load(open(MIXF, "rb"))
    from seats_plan import gold_paths
    days, P = pickle.load(open(SRC, "rb")); g = gold_paths(days, "Robust"); M = {}
    for cap, m in ((0, 4), (0, 8), (300, 4)):
        a, b, ca, cb = P[cap]; cc = ca + m * cb
        LO = a[0] - g[0] + m * b[0] - cc[:, None]; CL = a[1] - g[1] + m * b[1] - cc[:, None]; FIN = a[2] - g[2] + m * b[2] - cc
        M[(cap, m)] = (np.ascontiguousarray(np.minimum(LO, CL)), np.ascontiguousarray(CL), FIN)
    pickle.dump((np.asarray(days), M), open(MIXF, "wb"), protocol=4); return np.asarray(days), M


def haircut(days, fin, hc):
    t1 = days < T1_END; h = np.zeros(len(days))
    h[t1] = hc * fin[t1].mean(); h[~t1] = hc * fin[~t1].mean(); return h


# ------------------------------------------------------------------ eval race (minute resolution)
@njit(cache=True)
def race(LO, CL, Hh, idx, s, n, ep):
    """ep: T, D, cons, mind, G, L, ptype, kA, kB, C, dL, goal, intra, lock, hardL. Returns (1 pass / -1 bust / 0 open, position).
    intra = 1: trailing threshold follows the minute-close equity peak (optimistic: the true intraday peak uses the minute high).
    hardL > 0: a hard daily loss limit (bust when the day's open low reaches -hardL)."""
    T = ep[0]; D = ep[1]; cons = ep[2]; mind = int(ep[3]); G = ep[4]; L = ep[5]; pt = int(ep[6]); kA = ep[7]; kB = ep[8]; C = ep[9]; dL = ep[10]; goal = ep[11]
    intra = ep[12] > 0; lock = ep[13]; hardL = ep[14]
    eq = 0.0; pk = 0.0; best = -1e9; d = s; nm = LO.shape[1]
    while d < n:
        t = idx[d]; thr = lock if pk >= D + lock else pk - D; cu = eq - thr
        if pt == 0: k = kA
        elif pt == 1: k = kA if cu >= C else kB
        else: k = kB if (d - s >= dL and eq < goal) else kA
        h = Hh[t]; last = 0.0
        for j in range(nm):
            lo = k * (LO[t, j] - h)
            if eq + lo <= thr: return -1, d
            if hardL > 0.0 and lo <= -hardL: return -1, d
            c = k * (CL[t, j] - h); tot = eq + c
            if tot >= T and (cons <= 0.0 or max(best, c) <= cons * tot):
                e = s + int(mind) - 1
                return 1, (d if d > e else e)
            last = c
            if intra and tot > pk:
                pk = tot; thr = lock if pk >= D + lock else pk - D
            if L > 0.0 and c <= -L: break
            if G > 0.0 and c >= G: break
        eq += last
        if last > best: best = last
        if eq > pk: pk = eq
        d += 1
    return 0, n


@njit(cache=True)
def race_all(LO, CL, Hh, idx, ep, res, end):
    n = len(idx)
    for s in range(n):
        r, e = race(LO, CL, Hh, idx, s, n, ep); res[s] = r; end[s] = e


@njit(cache=True)
def chain(res, end, s0, W, N, n):
    """serial evals from s0 (new one the day after a bust), up to N inside W days: (funded 0/1, evals used, days)"""
    s = s0; k = 0
    while k < N and s < n and s - s0 < W:
        k += 1
        if res[s] == 1:
            if end[s] - s0 < W: return 1, k, end[s] - s0 + 1
            return 0, k, W
        if res[s] == -1 and end[s] - s0 < W: s = end[s] + 1
        else: return 0, k, W
    return 0, k, W


def eval_metrics(res, end, starts, fee, n):
    o = {}
    for W in (10, 22, 120):
        st = starts[starts + W <= n]
        for N in (1, 3):
            r = np.array([chain(res, end, s, W, N, n) for s in st])
            o[f"p{W}_{N}"] = 100 * r[:, 0].mean()
            if W == 22 and N == 3: o["fees22_3"] = fee * r[:, 1].mean(); o["med_days22_3"] = float(np.median(r[r[:, 0] == 1, 2])) if r[:, 0].any() else np.nan
    o["p22_3_per100"] = o["p22_3"] / (o["fees22_3"] / 100.0)
    return o


def eval_policies(F):
    pol = {}
    ks = range(1, F["kmax"] + 1)
    for L in (0, 600, 900, 1200):
        for k in ks: pol[f"fix{k} L{L}"] = (0, k, k, 0, 0, 0, L)
        for kA, kB in itertools.permutations(ks, 2):
            for C in (1000, 1500, 2500, 3000): pol[f"cu{kA}/{kB}@{C} L{L}"] = (1, kA, kB, C, 0, 0, L)
        for kA, kB in ((1, 2), (1, 3), (2, 3), (2, 4), (3, 4)):
            if kB > F["kmax"]: continue
            for dL in (5, 10): pol[f"late{kA}>{kB}@d{dL} L{L}"] = (2, kA, kB, 0, dL, 1500, L)
        if F["G"] > 0: pol[f"fix1x8 L{L}"] = (0, 1, 1, 0, 0, 0, L)
    return pol


def ep_of(F, p):
    pt, kA, kB, C, dL, goal, L = p; dll = F.get("dll", 0.0); hard = F.get("hard", 0)
    Le = float(L)
    if dll > 0 and not hard: Le = dll if Le <= 0 else min(Le, dll)
    return np.array([F["T"], F["D"], F["cons"], F["mind"], F["G"], Le, pt, kA, kB, C, dL, goal, 1.0 if F.get("trail") == "intra" else 0.0,
                     F.get("lock", 100.0), dll if hard else 0.0], np.float64)


def nparams(name):
    return (0 if name.startswith("fix") else 2) + (0 if name.endswith(" L0") else 1)


# ------------------------------------------------------------------ funded (daily resolution from minute paths)
@njit(cache=True)
def dayvec(LO, CL, FIN, Hh, k, G, L, lo_out, cl_out):
    for t in range(LO.shape[0]):
        h = Hh[t]; mn = 1e18; cl = k * (FIN[t] - h); stopped = False
        for j in range(LO.shape[1]):
            lo = k * (LO[t, j] - h)
            if lo < mn: mn = lo
            if L > 0.0 and lo <= -L:
                cl = lo; stopped = True; break
            c = k * (CL[t, j] - h)
            if G > 0.0 and c >= G:
                cl = c; stopped = True; break
        lo_out[t] = min(mn, cl); cl_out[t] = cl


@njit(cache=True)
def fund(FL, FC, fp, idx, s, n, rec):
    """fp: 0 firm (0 Lucid Flex, 1 Lucid Pro, 2 MFFU keep-X, 3 MFFU ladder, 4 generic survey model), 1 c1, 2 X, 3 S, 4 K, 5 cap1, 6 cap2,
    7 Q, 8 npmax, 9 D; generic: 10 lock, 11 lock_on_pay, 12 B, 13 frac, 14 minreq, 15 minprof, 16 pc, 17 nq, 18 qthr, 19 md, 20 split, 21 intra.
    FL rows: firms 0-2/4: 0 capped, 1 full; firm 3: 0 capped 1c, 1..K full k.
    rec: 0 first payout offset (-1), 1 cash, 2 bust offset (-1), 3 payouts, 4 last position"""
    firm = int(fp[0]); c1 = fp[1]; X = fp[2]; S = fp[3]; K = int(fp[4]); cap1 = fp[5]; cap2 = fp[6]; Q = fp[7]; npmax = int(fp[8]); D = fp[9]
    lock = 100.0; lop = 0.0; B = 0.0; frac = 1.0; minreq = 500.0; minprof = 0.0; pc = 0.0; nq = 0.0; qthr = 0.0; md = 0.0; split = 0.9
    if firm == 4:
        lock = fp[10]; lop = fp[11]; B = fp[12]; frac = fp[13]; minreq = fp[14]; minprof = fp[15]; pc = fp[16]; nq = fp[17]; qthr = fp[18]; md = fp[19]; split = fp[20]
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; cyc0 = 0.0; best = -1e9; nd = 0; qd = 0; locked = False; d = s
    rec[0] = -1.0; rec[2] = -1.0
    while d < n:
        t = idx[d]
        thr = lock if (locked or pk >= D + lock) else pk - D
        cu = bal - thr
        if firm == 3:
            k = 1 + int(cu / S)
            if k > K: k = K
            g = 0 if (k == 1 and cu < c1) else k
        else: g = 0 if cu < c1 else 1
        if bal + FL[g, t] <= thr:
            rec[1] = cash; rec[2] = d - s; rec[3] = m; rec[4] = d; return
        c = FC[g, t]; bal += c; nd += 1
        if bal > pk: pk = bal
        amt = 0.0
        if firm == 0:
            if c >= Q: qd += 1
            if qd >= 5 and bal - cyc0 > 0 and bal >= X:
                a = min(cap1, 0.5 * bal)
                if a >= 500.0: amt = a; qd = 0; locked = True
        elif firm == 1:
            if c > best: best = c
            prof = bal - cyc0; cap = cap1 if m == 0 else cap2; a = min(cap, bal - (D + 100.0))
            if nd >= 3 and prof >= 500.0 and a >= max(500.0, min(X, cap)) and best <= 0.4 * prof:
                amt = a; best = -1e9; nd = 0
        elif firm == 4:
            if c > best: best = c
            if c >= qthr and qthr > 0: qd += 1
            prof = bal - cyc0; cap = cap1 if m == 0 else cap2; a = min(cap, min(bal - B, frac * bal))
            if (a >= max(minreq, min(X, cap)) and prof >= minprof and (pc <= 0.0 or best <= pc * prof) and qd >= nq and nd >= md):
                amt = a; best = -1e9; nd = 0; qd = 0
                if lop > 0: locked = True
        else:
            if bal - X >= 500.0: amt = bal - X
        if amt > 0.0:
            bal -= amt; cash += (split if firm == 4 else 0.9) * amt; m += 1; cyc0 = bal
            if rec[0] < 0: rec[0] = d - s
            if npmax > 0 and m >= npmax:
                rec[1] = cash; rec[3] = m; rec[4] = d; return
        d += 1
    rec[1] = cash; rec[3] = m; rec[4] = n


@njit(cache=True)
def fund_all(FL, FC, fp, idx, H, out):
    n = len(idx); rec = np.zeros(5)
    for s in range(n):
        fund(FL, FC, fp, idx, s, min(n, s + H), rec)
        for q in range(5): out[s, q] = rec[q]


def fund_policies(firm):
    pol = {}
    if firm == "LucidPro50K":
        for k, c, G, X, L in itertools.product((1, 2), (0, 750, 1000, 1500), (0, 500, 700, 1000, 1500), (500, 2000), (0, 1500)): pol[f"k{k} c{c} G{G} X{X} L{L}"] = (k, c, G, X, L)
    elif firm == "LucidFlex50K":
        for k, c, X, L in itertools.product((1, 2), (0, 750, 1000, 1500), (2500, 4000, 5000), (0, 1500)): pol[f"k{k} c{c} X{X} L{L}"] = (k, c, 0, X, L)
    elif FIRMS[firm]["fund"] == "gen":
        FF = FIRMS[firm]["FF"]; Gs = (0, 500, 700, 1000, 1500) if FF["pc"] > 0 else (0,)
        for k, c, G, X, L in itertools.product((1, 2), (0, 750, 1000, 1500), Gs, (0, int(FF["cap1"])), (0, 1500)): pol[f"k{k} c{c} G{G} X{X} L{L}"] = (k, c, G, X, L)
    else:
        for k, c, B, L in itertools.product((1, 2), (0, 750, 1000, 1500, 2000), (2600, 4100, 6100), (0, 1500)): pol[f"k{k} c{c} B{B} L{L}"] = (k, c, 0, B, L)
        for L in (0, 1500): pol[f"ladder S3000 K4 B11100 c2000 L{L}"] = ("lad", 2000, 0, 11100, L)
    return pol


class Fund:
    """day vectors cache per (hc, mix, k, G, L)"""
    def __init__(s, days, M):
        s.days = days; s.M = M; s.c = {}; s.H = {}
    def h(s, hc, mix):
        if (hc, mix) not in s.H: s.H[(hc, mix)] = haircut(s.days, s.M[mix][2], hc)
        return s.H[(hc, mix)]
    def vec(s, hc, mix, k, G, L, dll=0.0):
        La = float(L) * k
        if dll > 0: La = dll if La <= 0 else min(La, dll)       # firm soft daily loss limit in the funded account
        key = (hc, mix, k, G, La)
        if key not in s.c:
            LO, CL, FIN = s.M[mix]; lo = np.zeros(len(s.days)); cl = np.zeros(len(s.days))
            dayvec(LO, CL, FIN, s.h(hc, mix), float(k), float(G), La, lo, cl); s.c[key] = (lo, cl)
        return s.c[key]
    def tiers(s, hc, firm, p):
        F = FIRMS[firm]; k, c, G, X, L = p
        if k == "lad":
            rows = [s.vec(hc, (300, 4), 1, 0, L)] + [s.vec(hc, (0, 4), q, 0, L) for q in range(1, 5)]
            fp = (3, float(c), float(X), 3000.0, 4, 0, 0, 0, 0, F["D"])
        elif F["fund"] == "gen":
            FF = F["FF"]; dll = float(FF["dll"]) if not FF["hard"] else 0.0
            rows = [s.vec(hc, (300, 4), k, G, L, dll), s.vec(hc, (0, 4), k, G, L, dll)]
            fp = (4, float(c), float(X), 1e9, 1, FF["cap1"], FF["cap2"], 0, FF["npmax"], FF["D"], FF["lock"], FF["lock_on_pay"], FF["B"], FF["frac"],
                  FF["minreq"], FF["minprof"], FF["pc"], FF["nq"], FF["qthr"], FF["md"], FF["split"], 1.0 if FF["trail"] == "intra" else 0.0)
        else:
            rows = [s.vec(hc, (300, 4), k, G, L), s.vec(hc, (0, 4), k, G, L)]
            fi = {"flex": 0, "pro": 1, "mffu": 2}[F["fund"]]
            fp = (fi, float(c), float(X), 1e9, 1, F.get("cap1", 0.0), F.get("cap2", 0.0), F.get("Q", 0.0), F["npmax"], F["D"])
        FL = np.ascontiguousarray(np.array([r[0] for r in rows])); FC = np.ascontiguousarray(np.array([r[1] for r in rows]))
        return FL, FC, np.array(fp, np.float64)


def fund_metrics(o, starts, n):
    r = {}
    for W in (41, 62, 124):
        st = starts[starts + W <= n]; fp = o[st, 0]; r[f"pay{W}"] = 100 * ((fp >= 0) & (fp < W)).mean()
    st = starts[starts + 252 <= n]
    r["surv252"] = 100 * ((o[st, 2] < 0) | (o[st, 2] >= 252)).mean(); r["cash252"] = float(o[st, 1].mean())
    return r


# ------------------------------------------------------------------ 12-month seat (eval serial -> funded -> re-buy)
@njit(cache=True)
def seat(LO, CL, Hh, ep, fee, FL, FC, fp, idx, s0, end, out, act=0.0):
    """out: 0 net cash, 1 evals, 2 passes, 3 funded busts, 4 payouts, 5 first payout offset from s0 (-1), 6 fees until the first payout"""
    i = s0; cash = 0.0; fees = 0.0; nev = 0; npass = 0; nb = 0; npay = 0; first = -1.0; ff = 0.0; rec = np.zeros(5)
    while i < end:
        fees += fee; nev += 1
        r, j = race(LO, CL, Hh, idx, i, end, ep)
        if r != 1:
            i = j + 1; continue
        npass += 1; fees += act
        fund(FL, FC, fp, idx, j + 1, end, rec)
        if first < 0 and rec[0] >= 0: first = j + 1 + rec[0] - s0; ff = fees
        cash += rec[1]; npay += int(rec[3]); nb += rec[2] >= 0; i = int(rec[4]) + 1
    out[0] = cash - fees; out[1] = nev; out[2] = npass; out[3] = nb; out[4] = npay; out[5] = first; out[6] = ff if first >= 0 else fees


@njit(cache=True)
def seat_all(LO, CL, Hh, ep, fee, FL, FC, fp, idx, H, step, out, act=0.0):
    n = len(idx); r = 0; o = np.zeros(7)
    for s in range(0, n - 1, step):
        seat(LO, CL, Hh, ep, fee, FL, FC, fp, idx, s, min(n, s + H), o, act)
        for q in range(7): out[r, q] = o[q]
        r += 1
    return r


def boot_idx(lo, hi, L, rng):
    return np.concatenate([np.arange(s, s + 21) for s in rng.integers(lo, hi - 21, L // 21 + 2)])[:L].astype(np.int64)


# ------------------------------------------------------------------ stages
def stage_eval(firms):
    days, M = build_mix(); n = len(days); idx = np.arange(n, dtype=np.int64)
    s1 = np.nonzero(days < T1_END)[0]; s2 = np.nonzero((days >= T1_END) & (days < T2_END))[0]
    for firm in firms:
        F = FIRMS[firm]; pol = eval_policies(F); rows = []; t0 = time.time()
        for hc in HC:
            H = {m: haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
            for name, p in pol.items():
                mix = (0, 8) if "x8" in name else (0, 4); LO, CL, _ = M[mix]
                res = np.zeros(n, np.int64); end = np.zeros(n, np.int64); race_all(LO, CL, H[mix], idx, ep_of(F, p), res, end)
                for per, st in (("T1", s1), ("T2", s2)):
                    rows.append(dict(firm=firm, policy=name, hc=hc, per=per, nparams=nparams(name), **eval_metrics(res, end, st, F["fee"], n)))
            print(firm, hc, len(pol), round(time.time() - t0), flush=True)
        pd.DataFrame(rows).to_csv(os.path.join(OWN, f"prop_wf_eval_{firm}.csv"), index=False)


def stage_funded():
    days, M = build_mix(); n = len(days); idx = np.arange(n, dtype=np.int64); FU = Fund(days, M)
    s1 = np.nonzero(days < T1_END)[0]; s2 = np.nonzero((days >= T1_END) & (days < T2_END))[0]; rows = []
    for firm in FIRMS:
        for hc in HC:
            for name, p in fund_policies(firm).items():
                FL, FC, fp = FU.tiers(hc, firm, p); o = np.zeros((n, 5)); fund_all(FL, FC, fp, idx, 252, o)
                for per, st in (("T1", s1), ("T2", s2)): rows.append(dict(firm=firm, policy=name, hc=hc, per=per, **fund_metrics(o, st, n)))
        print(firm, flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OWN, "prop_wf_funded.csv"), index=False)



def complexity_f(name, cur):
    a = dict(zip(["k", "c", "G", "X", "L"], name.split()[:5])) if not name.startswith("ladder") else {"lad": 1}
    b = dict(zip(["k", "c", "G", "X", "L"], cur.split()[:5]))
    return 9 if "lad" in a else sum(a.get(q) != b.get(q) for q in b)


def choose(df, metric, cplx):
    """T1-best at full edge; a simpler policy within 1.0 pt on T1 wins (pre-registered)."""
    t1 = df[(df.per == "T1") & (df.hc == 0.0)].set_index("policy")[metric]
    top = t1.max(); near = t1[t1 >= top - 1.0]
    c = pd.Series({p: cplx(p) for p in near.index})
    return c[c == c.min()].index.to_series().map(t1).idxmax()


def base_rate(df, metric):
    a = df[(df.hc == 0.0)].pivot_table(index="policy", columns="per", values=metric)
    q1 = a.T1 >= a.T1.quantile(0.9); q2 = a.T2 >= a.T2.quantile(0.9)
    return dict(P_T2top10_given_T1top10=round(100 * float(q2[q1].mean()), 1), spearman_T1_T2=round(float(a.T1.rank().corr(a.T2.rank())), 3), n=int(len(a)))


def neighbours(names, chosen):
    tok = chosen.split(); out = []
    for p in names:
        t = p.split()
        if len(t) == len(tok) and sum(x != y for x, y in zip(t, tok)) == 1: out.append(p)
    return out


def stage_select(firms):
    days, M = build_mix(); n = len(days); idx = np.arange(n, dtype=np.int64); FU = Fund(days, M); rng = np.random.default_rng(2110)
    i1 = np.nonzero(days < T1_END)[0]; i2 = np.nonzero((days >= T1_END) & (days < T2_END))[0]
    FD = pd.read_csv(os.path.join(OWN, "prop_wf_funded.csv"))
    for firm in firms:
        F = FIRMS[firm]; ED = pd.read_csv(os.path.join(OWN, f"prop_wf_eval_{firm}.csv")); epol = eval_policies(F); fpol = fund_policies(firm)
        ce = choose(ED, "p22_3", nparams); cf = choose(FD[FD.firm == firm], "pay62", lambda p: complexity_f(p, CUR_FUND[firm]))
        R = dict(chosen_eval=ce, chosen_funded=cf, current_eval=CUR_EVAL[firm], current_funded=CUR_FUND[firm],
                 base_rate_eval=base_rate(ED, "p22_3"), base_rate_funded=base_rate(FD[FD.firm == firm], "pay62"))
        def tab(df, pols):
            d = df[df.policy.isin(pols)]; return {f"{r.policy} | hc{r.hc} | {r.per}": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r._asdict().items() if k not in ("policy", "hc", "per", "firm", "Index")} for r in d.itertuples()}
        R["eval_table"] = tab(ED, [ce, CUR_EVAL[firm]]); R["funded_table"] = tab(FD[FD.firm == firm], [cf, CUR_FUND[firm]])
        R["eval_plateau"] = tab(ED[ED.hc == 0.0], neighbours(epol, ce)); R["funded_plateau"] = tab(FD[(FD.firm == firm) & (FD.hc == 0.0)], neighbours(fpol, cf))
        # bootstrap: the same 21-day-block resampled period for chosen and current
        BS = {}
        for hc in HC:
            Hm = {m: haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
            for per, ii in (("T1", i1), ("T2", i2)):
                ev = {p: [] for p in {ce, CUR_EVAL[firm]}}; fu = {p: [] for p in {cf, CUR_FUND[firm]}}
                FT = {p: FU.tiers(hc, firm, fpol[p]) for p in fu}
                for b in range(NBOOT):
                    bi = boot_idx(ii[0], ii[-1] + 1, len(ii), rng); nb = len(bi); st = np.arange(nb)
                    for p in ev:
                        mix = (0, 8) if "x8" in p else (0, 4); res = np.zeros(nb, np.int64); end = np.zeros(nb, np.int64)
                        race_all(M[mix][0], M[mix][1], Hm[mix], bi, ep_of(F, epol[p]), res, end); ev[p].append(eval_metrics(res, end, st, F["fee"], nb))
                    for p in fu:
                        o = np.zeros((nb, 5)); fund_all(*FT[p][:2], FT[p][2], bi, 252, o); fu[p].append(fund_metrics(o, st, nb))
                rec = {}
                for kind, dd, a, c in (("eval", ev, ce, CUR_EVAL[firm]), ("funded", fu, cf, CUR_FUND[firm])):
                    for met in dd[a][0]:
                        x = np.array([q[met] for q in dd[a]]); y = np.array([q[met] for q in dd[c]]); g = x - y
                        rec[f"{kind}:{met}"] = dict(chosen_med=round(float(np.nanmedian(x)), 2), current_med=round(float(np.nanmedian(y)), 2),
                                                    gain_med=round(float(np.nanmedian(g)), 2), gain_ci90=[round(float(np.nanpercentile(g, 5)), 2), round(float(np.nanpercentile(g, 95)), 2)],
                                                    P_gain=round(float(np.nanmean(g > 0)), 3))
                BS[f"hc{hc} | {per}"] = rec
            print(firm, "boot", hc, flush=True)
        R["bootstrap"] = BS
        # 12-month seats (bootstrap) for the 4 combos + P(>=1 payout within 62 td of the first eval) on history
        SE = {}; combos = {"current": (CUR_EVAL[firm], CUR_FUND[firm]), "chosen eval": (ce, CUR_FUND[firm]), "chosen funded": (CUR_EVAL[firm], cf), "chosen both": (ce, cf)}
        for hc in HC:
            Hm = {m: haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
            for per, ii in (("T1", i1), ("T2", i2)):
                paths = [boot_idx(ii[0], ii[-1] + 1, 252, rng) for _ in range(NBOOT)]
                for cn, (pe, pf) in combos.items():
                    mix = (0, 8) if "x8" in pe else (0, 4); FL, FC, fp = FU.tiers(hc, firm, fpol[pf]); x = np.zeros((NBOOT, 7)); o = np.zeros(7)
                    for b, bi in enumerate(paths):
                        seat(M[mix][0], M[mix][1], Hm[mix], ep_of(F, epol[pe]), F["fee"], FL, FC, fp, bi, 0, 252, o, F.get("act", 0.0)); x[b] = o
                    hist = np.zeros((n, 7)); k = seat_all(M[mix][0], M[mix][1], Hm[mix], ep_of(F, epol[pe]), F["fee"], FL, FC, fp, idx, 62, 1, hist, F.get("act", 0.0))
                    hs = hist[:k]; sel = (ii[ii + 62 <= n]); hs = hs[sel]
                    m = x[:, 0] / 12.0
                    SE[f"{cn} | hc{hc} | {per}"] = dict(median_month=round(float(np.median(m))), p10_month=round(float(np.percentile(m, 10))), mean_month=round(float(m.mean())),
                        P_neg_year=round(100 * float((m < 0).mean()), 1), evals_yr=round(float(x[:, 1].mean()), 2), funded_busts_yr=round(float(x[:, 3].mean()), 2), payouts_yr=round(float(x[:, 4].mean()), 2),
                        P_pay62_from_first_eval=round(100 * float(((hs[:, 5] >= 0) & (hs[:, 5] < 62)).mean()), 1), fees_until_pay_or_62=round(float(hs[:, 6].mean())))
            print(firm, "seats", hc, flush=True)
        R["seats"] = SE
        json.dump(R, open(os.path.join(OWN, f"prop_wf_sel_{firm}.json"), "w"), indent=1)


def stage_pay90(firms):
    """best achievable P(>= 1 payout within 62 td of buying the first eval): top-10 T1 eval (p22_3) x top-10 T1 funded (pay62), history starts,
    chosen on T1 (full edge), reported T2 + 35% haircut."""
    days, M = build_mix(); n = len(days); idx = np.arange(n, dtype=np.int64); FU = Fund(days, M)
    i1 = np.nonzero(days < T1_END)[0]; i2 = np.nonzero((days >= T1_END) & (days < T2_END))[0]
    FD = pd.read_csv(os.path.join(OWN, "prop_wf_funded.csv")); OUT = {}; rows = []
    for firm in firms:
        F = FIRMS[firm]; ED = pd.read_csv(os.path.join(OWN, f"prop_wf_eval_{firm}.csv")); epol = eval_policies(F); fpol = fund_policies(firm)
        te = list(ED[(ED.per == "T1") & (ED.hc == 0)].nlargest(10, "p22_3").policy) + [CUR_EVAL[firm]]
        tf = list(FD[(FD.firm == firm) & (FD.per == "T1") & (FD.hc == 0)].nlargest(10, "pay62").policy) + [CUR_FUND[firm]]
        for hc in (0.0, 0.35):
            Hm = {m: haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
            for pe in dict.fromkeys(te):
                mix = (0, 8) if "x8" in pe else (0, 4)
                for pf in dict.fromkeys(tf):
                    FL, FC, fp = FU.tiers(hc, firm, fpol[pf]); hist = np.zeros((n, 7))
                    k = seat_all(M[mix][0], M[mix][1], Hm[mix], ep_of(F, epol[pe]), F["fee"], FL, FC, fp, idx, 62, 1, hist, F.get("act", 0.0)); hs = hist[:k]
                    for per, ii in (("T1", i1), ("T2", i2)):
                        h = hs[ii[ii + 62 <= n]]
                        rows.append(dict(firm=firm, eval=pe, funded=pf, hc=hc, per=per, P_pay62=100 * float(((h[:, 5] >= 0) & (h[:, 5] < 62)).mean()), fees=float(h[:, 6].mean()),
                                         evals=float(h[:, 1].mean())))
        print(firm, "pay90", flush=True)
    D = pd.DataFrame(rows); D.to_csv(os.path.join(OWN, "prop_wf_pay90_" + "_".join(firms) + ".csv"), index=False)
    for firm in firms:
        d = D[D.firm == firm]; t1 = d[(d.per == "T1") & (d.hc == 0)]; b = t1.loc[t1.P_pay62.idxmax()]
        get = lambda pe, pf, hc, per: d[(d["eval"] == pe) & (d.funded == pf) & (d.hc == hc) & (d.per == per)].iloc[0]
        rec = {}
        for lab, (pe, pf) in (("T1-chosen", (b["eval"], b.funded)), ("current", (CUR_EVAL[firm], CUR_FUND[firm]))):
            rec[lab] = dict(eval=pe, funded=pf, **{f"{per} hc{hc}": dict(P_pay62=round(get(pe, pf, hc, per).P_pay62, 1), fees=round(get(pe, pf, hc, per).fees)) for per in ("T1", "T2") for hc in (0.0, 0.35)})
        rec["T2_max_hindsight"] = round(float(d[(d.per == "T2") & (d.hc == 0)].P_pay62.max()), 1)
        json.dump(rec, open(os.path.join(OWN, f"prop_wf_pay90_{firm}.json"), "w"), indent=1)


def stage_merge():
    """prop_wf.json (all parts + Q1/Q3 answers) and prop_wf_policies.csv (every policy row)."""
    OUT = {"preregistration": __doc__.split("PRE-REGISTRATION")[1].split("Run:")[0].strip(), "firms": {k: {q: v for q, v in F.items() if q != "FF"} for k, F in FIRMS.items()}}
    EV = pd.concat([pd.read_csv(os.path.join(OWN, f"prop_wf_eval_{f}.csv")) for f in FIRMS], ignore_index=True)
    FD = pd.read_csv(os.path.join(OWN, "prop_wf_funded.csv"))
    pd.concat([EV.assign(stage="eval"), FD.assign(stage="funded")], ignore_index=True).round(3).to_csv(os.path.join(HERE, "prop_wf_policies.csv"), index=False)
    for f in FIRMS:
        R = {}
        for part in ("sel", "pay90"):
            p = os.path.join(OWN, f"prop_wf_{part}_{f}.json")
            if os.path.exists(p): R[part] = json.load(open(p))
        e = EV[EV.firm == f]; piv = {hc: e[e.hc == hc].pivot_table(index="policy", columns="per") for hc in HC}
        q1 = {}
        for met in ("p10_1", "p22_1", "p10_3", "p22_3", "p120_3"):
            a = piv[0.0][met]; b = a.T1.idxmax()
            q1[met] = dict(T1_chosen=b, T1=round(a.T1[b], 1), T2=round(a.T2[b], 1), T2_hc35=round(piv[0.35][met].T2[b], 1), T2_hc100=round(piv[1.0][met].T2[b], 1),
                           T2_max_hindsight=round(a.T2.max(), 1), current_T2=round(a.T2[CUR_EVAL[f]], 1))
        q3 = {}
        a = piv[0.0]["p22_3"]; a35 = piv[0.35]["p22_3"]
        groups = {"fixed size, no stop": [p for p in a.index if p.startswith("fix") and p.endswith(" L0")],
                  "fixed size + intraday stop": [p for p in a.index if p.startswith("fix") and not p.endswith(" L0")],
                  "cushion schedule, no stop": [p for p in a.index if p.startswith("cu") and p.endswith(" L0")],
                  "days schedule, no stop": [p for p in a.index if p.startswith("late") and p.endswith(" L0")],
                  "any schedule + stop": [p for p in a.index if not p.startswith("fix") and not p.endswith(" L0")]}
        for g, ps in groups.items():
            if not ps: continue
            b = a.T1[ps].idxmax(); q3[g] = dict(T1_chosen=b, T1=round(a.T1[b], 1), T2=round(a.T2[b], 1), T2_hc35=round(a35.T2[b], 1),
                                               p120_3_T2=round(piv[0.0]["p120_3"].T2[b], 1), fees22_T2=round(piv[0.0]["fees22_3"].T2[b]))
        for L in (600, 900, 1200):                      # stop effect on the same size policy: mean T1/T2 change vs L0 over all size policies
            base = [p for p in a.index if p.endswith(" L0")]; d1 = []; d2 = []
            for p in base:
                q = p[:-2] + f"L{L}"
                if q in a.index: d1.append(a.T1[q] - a.T1[p]); d2.append(a.T2[q] - a.T2[p])
            q3[f"stop L{L} vs L0 (mean over size policies, pts)"] = dict(T1=round(float(np.mean(d1)), 1), T2=round(float(np.mean(d2)), 1), share_better_T2=round(100 * float(np.mean(np.array(d2) > 0)), 1))
        R["Q1_best_achievable_eval"] = q1; R["Q3_stops_schedules"] = q3; OUT[f] = R
    json.dump(OUT, open(os.path.join(HERE, "prop_wf.json"), "w"), indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "eval": stage_eval(sys.argv[2:] or list(FIRMS))
    elif cmd == "funded": stage_funded()
    elif cmd == "select": stage_select(sys.argv[2:] or list(FIRMS))
    elif cmd == "merge": stage_merge()
    elif cmd == "pay90": stage_pay90(sys.argv[2:] or list(FIRMS))
    elif cmd == "time":
        days, M = build_mix(); n = len(days); idx = np.arange(n, dtype=np.int64); F = FIRMS["LucidPro50K"]
        H = haircut(days, M[(0, 4)][2], 0.0); res = np.zeros(n, np.int64); end = np.zeros(n, np.int64)
        for p in ((0, 4, 4, 0, 0, 0, 0), (0, 1, 1, 0, 0, 0, 0)):
            t0 = time.time(); race_all(M[(0, 4)][0], M[(0, 4)][1], H, idx, ep_of(F, p), res, end); print(p, round(time.time() - t0, 2), (res == 1).mean(), np.median(end - np.arange(n)))
