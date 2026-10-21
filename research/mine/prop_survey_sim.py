"""2026-10-21 Firm-generic prop-account race (survey of bot-friendly futures prop firms, propfirms_2026-10-21.md).
Paths: lucidpro_week.load() with 'nogold' = NQ-only 2027 default (Ultra as coded + SO04/RV11/ORFAIL/CAM3), real NQ 2020-02..2026-10,
+1 tick per side, MINUTE resolution (LO = realized + open at the adverse extreme, CL = minute close equity, cumulative intraday).
Size k = base MNQ contracts per module, MOM1030/CPI09 at m=4 (NQMaster default multiplier). Edge haircut h = 0.35 x mean daily P&L x k
(per period). T1 starts 2020-03..2023-10, T2 starts 2024-01.. (only starts with room for the window). Nothing fitted on T2; the eval size k
per plan is chosen on T1 (max serial pass within 22 trading days per $ of fees) and reported on T2.
EVAL race (per plan): target T (flatten when reached, NQMaster EvalTarget), drawdown D: 'eod' (threshold = peak close - D), 'intra' (peak of
minute-close equity - D: optimistic, the true intraday peak uses the minute high), 'static' (-D); lock at +lock once the peak reaches D+lock;
DLL soft (day stopped at -dll, liquidated at the adverse extreme) or hard (bust); consistency c: pass only when best day <= c x profit
(NQMaster raises its target to bestDay/c); min days: target reached before min days -> parked (1-micro days, no risk) until min days;
time limit H (Trading Pit 21 trading days).
FUNDED (generic): same drawdown model, lock at +lock (and on the first payout when lock_on_pay), payout at the close when eligible
(policy: request once balance >= X, keep >= keep above the post-payout threshold, uncapped firms keep $4,100): amount = min(cap_n, bal - B, frac x bal) >= minreq, cycle profit >= minprof, cycle best day <= pc x cycle profit,
>= nq days of >= qthr in the cycle, >= md days in the cycle; split s; account ends after npmax payouts. Funded size 1 base contract (x4).
Outputs prop_survey_sim.json. Run: python3 prop_survey_sim.py  (about 5-10 min on 4 CPUs)."""
import os, sys, json, numpy as np
from numba import njit, prange
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
if "nogold" not in sys.argv: sys.argv.append("nogold")
import lucidpro_week as LW

# ---- plan rules (50K unless stated). price = typical price paid per eval (coupon when one is standing), list = list price, monthly = subscription
# kind of funded model: dict keys described in the docstring. Values from propfirms_2026-10-21.json (keep in sync).
PLANS = {
 "Lucid Flex 50K":        dict(T=3000, D=2000, trail="eod", lock=100, dll=0, hard=0, cons=0.50, mind=0, H=0, price=146, monthly=0, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=1, B=0, cap1=2000, cap2=2000, frac=0.5, minreq=500, minprof=1, pc=0, nq=5, qthr=150, md=0, npmax=5, split=0.9, dll=0, hard=0)),
 "Lucid Pro 50K (DLL off)":dict(T=3000, D=2000, trail="eod", lock=100, dll=0, hard=0, cons=0, mind=0, H=0, price=115.4, monthly=0, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=1, B=2100, cap1=2000, cap2=2500, frac=1.0, minreq=500, minprof=500, pc=0.40, nq=0, qthr=0, md=3, npmax=5, split=0.9, dll=0, hard=0)),
 "Lucid Pro 50K (DLL 1200)":dict(T=3000, D=2000, trail="eod", lock=100, dll=1200, hard=0, cons=0, mind=0, H=0, price=115.4, monthly=0, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=1, B=2100, cap1=2000, cap2=2500, frac=1.0, minreq=500, minprof=500, pc=0.40, nq=0, qthr=0, md=3, npmax=5, split=0.9, dll=1200, hard=0)),
 "LucidDaily 50K (EOD eval)":dict(T=3000, D=2000, trail="eod", lock=100, dll=0, hard=0, cons=0.50, mind=0, H=0, price=166, monthly=0, act=0,
                               F=dict(D=2000, trail="intra", lock=100, lock_on_pay=0, B=2100, cap1=1e9, cap2=1e9, frac=1.0, minreq=500, minprof=0, pc=0, nq=0, qthr=0, md=0, npmax=0, split=0.9, dll=0, hard=0)),
 "MFFU Rapid EOD 50K":    dict(T=3000, D=2000, trail="eod", lock=100, dll=0, hard=0, cons=0.30, mind=4, H=0, price=157, monthly=0, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=0, B=2100, cap1=1e9, cap2=1e9, frac=1.0, minreq=500, minprof=500, pc=0, nq=0, qthr=0, md=0, npmax=0, split=0.9, dll=0, hard=0)),
 "MFFU Rapid 50K (intraday funded)":dict(T=3000, D=2000, trail="eod", lock=100, dll=0, hard=0, cons=0.50, mind=2, H=0, price=157, monthly=0, act=0,
                               F=dict(D=2000, trail="intra", lock=100, lock_on_pay=0, B=2100, cap1=1e9, cap2=1e9, frac=1.0, minreq=500, minprof=500, pc=0, nq=0, qthr=0, md=0, npmax=0, split=0.9, dll=0, hard=0)),
 "MFFU Builder 50K":      dict(T=3000, D=2000, trail="eod", lock=100, dll=1000, hard=0, cons=0, mind=1, H=0, price=107, monthly=0, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=0, B=2100, cap1=2000, cap2=2000, frac=1.0, minreq=500, minprof=500, pc=0.50, nq=0, qthr=0, md=2, npmax=5, split=0.8, dll=1000, hard=0)),
 "Bulenox Opt1 50K (intraday)":dict(T=3000, D=2500, trail="intra", lock=100, dll=0, hard=0, cons=0, mind=0, H=0, price=90, monthly=0, act=148,
                               F=dict(D=2500, trail="intra", lock=100, lock_on_pay=0, B=2600, cap1=1500, cap2=1500, frac=1.0, minreq=1000, minprof=1000, pc=0.40, nq=0, qthr=0, md=10, npmax=0, split=1.0, dll=0, hard=0)),
 "Bulenox Opt2 50K (EOD+DLL)":dict(T=3000, D=2500, trail="eod", lock=100, dll=1100, hard=0, cons=0, mind=0, H=0, price=90, monthly=0, act=148,
                               F=dict(D=2500, trail="eod", lock=100, lock_on_pay=0, B=2600, cap1=1500, cap2=1500, frac=1.0, minreq=1000, minprof=1000, pc=0.40, nq=0, qthr=0, md=10, npmax=0, split=1.0, dll=1100, hard=0)),
 "FundedNext Rapid Pro 50K":dict(T=3000, D=2000, trail="eod", lock=100, dll=0, hard=0, cons=0, mind=0, H=0, price=149.99, monthly=0, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=0, B=0, cap1=1200, cap2=1200, frac=1.0, minreq=250, minprof=500, pc=0.40, nq=0, qthr=0, md=3, npmax=5, split=0.9, dll=0, hard=0)),
 "FundedNext Rapid Daily 50K":dict(T=3000, D=2000, trail="eod", lock=100, dll=1000, hard=0, cons=0, mind=0, H=0, price=149.99, monthly=0, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=0, B=2100, cap1=1200, cap2=1200, frac=1.0, minreq=250, minprof=500, pc=0, nq=0, qthr=0, md=1, npmax=5, split=0.9, dll=1000, hard=0)),
 "FundedNext Flex 50K":   dict(T=2500, D=1500, trail="eod", lock=100, dll=0, hard=0, cons=0.40, mind=0, H=0, price=71, monthly=0, act=0,
                               F=dict(D=1500, trail="eod", lock=100, lock_on_pay=1, B=0, cap1=1500, cap2=1500, frac=0.5, minreq=250, minprof=1, pc=0, nq=5, qthr=200, md=0, npmax=0, split=0.8, dll=0, hard=0)),
 "Tradeify Select 50K":   dict(T=3000, D=2000, trail="eod", lock=100, dll=0, hard=0, cons=0.40, mind=3, H=0, price=116, monthly=0, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=1, B=0, cap1=2500, cap2=2500, frac=0.5, minreq=250, minprof=1, pc=0, nq=5, qthr=150, md=0, npmax=0, split=0.9, dll=0, hard=0)),
 "Tradeify Growth 50K":   dict(T=3000, D=2000, trail="eod", lock=100, dll=1250, hard=0, cons=0, mind=1, H=0, price=116, monthly=0, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=0, B=3000, cap1=1500, cap2=2000, frac=1.0, minreq=250, minprof=1, pc=0.35, nq=5, qthr=150, md=0, npmax=0, split=0.9, dll=1250, hard=0)),
 "FTMO Futures Growth 50K":dict(T=3000, D=2000, trail="eod", lock=100, dll=0, hard=0, cons=0.40, mind=0, H=0, price=119, monthly=1, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=0, B=0, cap1=2500, cap2=2500, frac=0.5, minreq=20, minprof=1, pc=0, nq=4, qthr=150, md=0, npmax=0, split=0.9, dll=1000, hard=0)),
 "FTMO Futures Pro 50K":  dict(T=3000, D=3000, trail="eod", lock=100, dll=1000, hard=1, cons=0.50, mind=0, H=0, price=139, monthly=1, act=0,
                               F=dict(D=3000, trail="eod", lock=100, lock_on_pay=0, B=0, cap1=5000, cap2=5000, frac=1.0, minreq=20, minprof=1, pc=0, nq=5, qthr=200, md=0, npmax=0, split=0.9, dll=1000, hard=1)),
 "TradeDay Fast Pass 50K":dict(T=3000, D=2000, trail="eod", lock=100, dll=0, hard=0, cons=0.45, mind=3, H=0, price=95, monthly=1, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=0, B=0, cap1=1500, cap2=1500, frac=1.0, minreq=250, minprof=1, pc=0.45, nq=0, qthr=0, md=5, npmax=0, split=0.8, dll=0, hard=0)),
 "Trading Pit Prime 50K": dict(T=3000, D=2000, trail="eod", lock=100, dll=1000, hard=0, cons=0.40, mind=3, H=21, price=150, monthly=0, act=0,
                               F=dict(D=2000, trail="eod", lock=100, lock_on_pay=0, B=0, cap1=1500, cap2=1500, frac=0.5, minreq=250, minprof=1, pc=0, nq=3, qthr=150, md=0, npmax=0, split=0.8, dll=0, hard=0)),
}
POLICY = {"Lucid Flex 50K": (4000, 1000), "Tradeify Select 50K": (4000, 1000), "FTMO Futures Growth 50K": (4000, 1000), "FundedNext Flex 50K": (3000, 1000),
          "Lucid Pro 50K (DLL off)": (4100, 1000), "Lucid Pro 50K (DLL 1200)": (4100, 1000)}
for _n, _p in PLANS.items():
    _X, _k = POLICY.get(_n, (0, 1000))
    if _p["F"]["cap1"] > 1e8: _p["F"]["B"] = 4100  # uncapped daily payouts: keep $4,100 (house MFFU policy)
    _p["F"]["X"] = _X; _p["F"]["keep"] = _k
PLANS["Bulenox Opt1 50K (stress D-150)"] = dict(PLANS["Bulenox Opt1 50K (intraday)"], D=2350)
TR = {"eod": 0, "intra": 1, "static": 2}


@njit(cache=True)
def race(LO, CL, s, n, T, D, tr, lock, dll, hard, cons, mind, H):
    """one eval from day s. Returns (1 pass / -1 bust / 0 open, day index of the outcome)."""
    eq = 0.0; pk = 0.0; best = -1e18; d = s; end = n if H <= 0 else min(n, s + H)
    while d < end:
        locked = pk >= D + lock
        thr = lock if locked else (-D if tr == 2 else pk - D)
        last = 0.0; ipk = pk
        for j in range(LO.shape[1]):
            if dll > 0 and LO[d, j] <= -dll:
                if hard == 1: return -1, d
                last = -dll; break
            if eq + LO[d, j] <= thr: return -1, d
            cur = eq + CL[d, j]
            if cur >= T:
                b = best if best > CL[d, j] else CL[d, j]
                if cons <= 0.0 or b <= cons * cur:
                    nd = d - s + 1
                    return 1, (d if nd >= mind else s + mind - 1)
            if tr == 1 and not locked and cur > ipk:
                ipk = cur; thr = ipk - D
                if ipk >= D + lock: thr = lock; locked = True
            last = CL[d, j]
        eq += last
        if last > best: best = last
        if tr == 1:
            if ipk > pk: pk = ipk
        if eq > pk: pk = eq
        d += 1
    return 0, end


@njit(parallel=True, cache=True)
def all_starts(LO, CL, starts, T, D, tr, lock, dll, hard, cons, mind, H, res, off):
    n = LO.shape[0]
    for i in prange(len(starts)):
        r, e = race(LO, CL, starts[i], n, T, D, tr, lock, dll, hard, cons, mind, H); res[i] = r; off[i] = e - starts[i]


@njit(cache=True)
def funded(LO, CL, s, n, W, D, tr, lock, lock_on_pay, B, cap1, cap2, frac, minreq, minprof, pc, nq, qthr, md, npmax, split, dll, hard, X, keep):
    """funded account from day s for W days. Returns (cash, payouts, status -1 bust / 1 ended by payouts / 0 open, first payout offset or -1)."""
    bal = 0.0; pk = 0.0; cash = 0.0; m = 0; cyc0 = 0.0; best = -1e18; qd = 0; nd = 0; locked = False; first = -1
    end = min(n, s + W); d = s
    while d < end:
        if pk >= D + lock: locked = True
        thr = lock if locked else (-D if tr == 2 else pk - D)
        last = 0.0; ipk = pk; dead = False
        for j in range(LO.shape[1]):
            if dll > 0 and LO[d, j] <= -dll:
                if hard == 1: dead = True
                last = -dll; break
            if bal + LO[d, j] <= thr: dead = True; break
            cur = bal + CL[d, j]
            if tr == 1 and not locked and cur > ipk:
                ipk = cur; thr = ipk - D
                if ipk >= D + lock: thr = lock; locked = True
            last = CL[d, j]
        if dead: return cash, m, -1, first
        bal += last; nd += 1
        if tr == 1 and ipk > pk: pk = ipk
        if bal > pk: pk = bal
        if last > best: best = last
        if last >= qthr and qthr > 0: qd += 1
        prof = bal - cyc0
        cap = cap1 if m == 0 else cap2
        amt = bal - B
        if frac < 1.0 and frac * bal < amt: amt = frac * bal
        if cap < amt: amt = cap
        tpost = lock if (locked or lock_on_pay == 1) else thr
        if bal - tpost - keep < amt: amt = bal - tpost - keep
        ok = bal >= X and amt >= minreq and prof >= minprof and nd >= md and (nq == 0 or qd >= nq) and (pc <= 0.0 or best <= pc * prof)
        if ok:
            bal -= amt; cash += split * amt; m += 1; cyc0 = bal; best = -1e18; qd = 0; nd = 0
            if first < 0: first = d - s
            if lock_on_pay == 1: locked = True
            if npmax > 0 and m >= npmax: return cash, m, 1, first
        d += 1
    return cash, m, 0, first


@njit(parallel=True, cache=True)
def funded_all(LO, CL, starts, W, D, tr, lock, lop, B, c1, c2, frac, minreq, minprof, pc, nq, qthr, md, npmax, split, dll, hard, X, keep, out):
    n = LO.shape[0]
    for i in prange(len(starts)):
        c, m, st, f = funded(LO, CL, starts[i], n, W, D, tr, lock, lop, B, c1, c2, frac, minreq, minprof, pc, nq, qthr, md, npmax, split, dll, hard, X, keep)
        out[i, 0] = c; out[i, 1] = m; out[i, 2] = st; out[i, 3] = f


def mats(P, k, m, h):
    return LW.mats(P, k, m, h)


def eval_metrics(res, off, starts_all, n, fee_first, fee_re, monthly):
    """res/off per start day (index = day). Single and serial metrics per start set."""
    out = {}
    for W in (10, 22, 120):
        st = starts_all[starts_all < n - W]
        out[f"single_{W}"] = round(100 * float(np.mean([(res[s] == 1) and off[s] < W for s in st])), 1)
        out[f"bust_{W}"] = round(100 * float(np.mean([(res[s] == -1) and off[s] < W for s in st])), 1)
    for W in (10, 22):
        st = starts_all[starts_all < n - W]; ok = []; fees = []; evs = []
        for s0 in st:
            s = s0; k = 0; got = False; fee = 0.0
            while s - s0 < W:
                k += 1; dur = min(off[s] + 1, s0 + W - s)
                fee += (fee_first if k == 1 else fee_re) * (max(1, -(-dur // 21)) if monthly else 1)  # subscription: one month per started 21 trading days
                if res[s] == 1 and s + off[s] - s0 < W: got = True; break
                if res[s] == -1 and s + off[s] - s0 < W: s = s + off[s] + 1
                else: break
            ok.append(got); fees.append(fee); evs.append(k)
        out[f"serial_{W}"] = round(100 * float(np.mean(ok)), 1); out[f"serial_{W}_evals"] = round(float(np.mean(evs)), 2)
        out[f"serial_{W}_fees"] = round(float(np.mean(fees)), 0)
        out[f"serial_{W}_per100"] = round(100 * float(np.mean(ok)) / max(1.0, float(np.mean(fees))) * 100, 1)  # pass-% per $100
    return out


def run():
    days, P = LW.load(); n = len(days); d24 = int(np.searchsorted(days, 20240101))
    a, b, ca, cb = P[0]; fin = a[2] + 4 * b[2] - ca - 4 * cb; mu1, mu2 = float(fin[:d24].mean()), float(fin[d24:].mean())
    S1 = np.nonzero((days >= 20200301) & (days < 20231101))[0].astype(np.int64); S2 = np.nonzero(days >= 20240101)[0].astype(np.int64)
    OUT = dict(meta=dict(days=[int(days[0]), int(days[-1])], mu_per_contract_day=[round(mu1, 1), round(mu2, 1)], n_T1=len(S1), n_T2=len(S2)), eval={}, funded={}, life={})
    MATS = {}
    for hc in (0.0, 0.35):
        h = np.where(np.arange(n) < d24, hc * mu1, hc * mu2)
        for k in (1, 2, 3, 4):
            MATS[(hc, k)] = mats(P, k, 4, h)
    allst = np.arange(n - 1, dtype=np.int64)
    for name, p in PLANS.items():
        fee_re = p["price"]
        for (hc, k), (LO, CL) in MATS.items():
            res = np.zeros(len(allst), np.int8); off = np.zeros(len(allst), np.int64)
            all_starts(LO, CL, allst, float(p["T"]), float(p["D"]), TR[p["trail"]], float(p["lock"]), float(p["dll"]), int(p["hard"]),
                       float(p["cons"]), int(p["mind"]), int(p["H"]), res, off)
            for per, st in (("T1", S1), ("T2", S2)):
                OUT["eval"][f"{name} | k{k} | edge-{int(hc*100)}% | {per}"] = eval_metrics(res, off, st, n, p["price"], fee_re, p["monthly"])
        print(name, " ".join(f"k{k} {OUT['eval'][f'{name} | k{k} | edge-0% | T1']['serial_22']:.0f}/{OUT['eval'][f'{name} | k{k} | edge-0% | T2']['serial_22']:.0f}" for k in (1, 2, 3, 4)), flush=True)
    # best k per plan chosen on T1 full edge: max serial_22 per $100 of fees (ties -> higher serial_22)
    best = {}
    for name in PLANS:
        sc = [(OUT["eval"][f"{name} | k{k} | edge-0% | T1"]["serial_22_per100"], OUT["eval"][f"{name} | k{k} | edge-0% | T1"]["serial_22"], k) for k in (1, 2, 3, 4)]
        best[name] = max(sc)[2]
    OUT["best_k_T1"] = best
    # funded: every plan at 1 base contract (x4), starts = every day; P(>=1 payout within 63 trading days ~ 90 calendar days), 252-day cash
    allst2 = np.arange(n - 1, dtype=np.int64)
    for name, p in PLANS.items():
        F = p["F"]
        for hc in (0.0, 0.35):
            LO, CL = MATS[(hc, 1)]
            for W in (63, 252):
                o = np.zeros((len(allst2), 4))
                funded_all(LO, CL, allst2, W, float(F["D"]), TR[F["trail"]], float(F["lock"]), int(F["lock_on_pay"]), float(F["B"]), float(F["cap1"]), float(F["cap2"]),
                           float(F["frac"]), float(F["minreq"]), float(F["minprof"]), float(F["pc"]), int(F["nq"]), float(F["qthr"]), int(F["md"]), int(F["npmax"]),
                           float(F["split"]), float(F["dll"]), int(F["hard"]), float(F["X"]), float(F["keep"]), o)
                for per, st in (("T1", S1), ("T2", S2)):
                    st = st[st < n - W]; x = o[st]
                    key = f"{name} | edge-{int(hc*100)}% | {per}"; r = OUT["funded"].setdefault(key, {})
                    if W == 63:
                        r["P_payout_90cd"] = round(100 * float(((x[:, 3] >= 0) & (x[:, 3] < 63)).mean()), 1)
                        r["bust_90cd"] = round(100 * float((x[:, 2] == -1).mean()), 1)
                    else:
                        r["cash_12m_mean"] = round(float(x[:, 0].mean())); r["cash_12m_median"] = round(float(np.median(x[:, 0])))
                        r["payouts_12m"] = round(float(x[:, 1].mean()), 2); r["bust_12m"] = round(100 * float((x[:, 2] == -1).mean()), 1)
                        r["P_payout_12m"] = round(100 * float((x[:, 1] >= 1).mean()), 1)
    # one-year slot: serial evals at best k until funded (<= 120 trading days), then funded 1c until day 252 of the slot (no re-buy after a funded bust)
    for name, p in PLANS.items():
        F = p["F"]; k = best[name]
        for hc in (0.0, 0.35):
            LO, CL = MATS[(hc, k)]; FLO, FCL = MATS[(hc, 1)]
            res = np.zeros(len(allst), np.int8); off = np.zeros(len(allst), np.int64)
            all_starts(LO, CL, allst, float(p["T"]), float(p["D"]), TR[p["trail"]], float(p["lock"]), float(p["dll"]), int(p["hard"]), float(p["cons"]), int(p["mind"]), int(p["H"]), res, off)
            for per, st in (("T1", S1), ("T2", S2)):
                st = st[st < n - 252]; nets = []; fund = []
                for s0 in st:
                    s = s0; fee = 0.0; kk = 0; fd = -1
                    while s - s0 < 120:
                        kk += 1; dur = min(off[s] + 1, s0 + 120 - s)
                        fee += p["price"] * (max(1, -(-dur // 21)) if p["monthly"] else 1)
                        if res[s] == 1: fd = s + off[s] + 1; break
                        if res[s] == -1: s = s + off[s] + 1
                        else: break
                    cash = 0.0
                    if fd > 0 and fd < s0 + 252:
                        fee += p["act"]
                        c, m, stt, f = funded(FLO, FCL, fd, n, s0 + 252 - fd, float(F["D"]), TR[F["trail"]], float(F["lock"]), int(F["lock_on_pay"]), float(F["B"]),
                                              float(F["cap1"]), float(F["cap2"]), float(F["frac"]), float(F["minreq"]), float(F["minprof"]), float(F["pc"]), int(F["nq"]),
                                              float(F["qthr"]), int(F["md"]), int(F["npmax"]), float(F["split"]), float(F["dll"]), int(F["hard"]), float(F["X"]), float(F["keep"]))
                        cash = c
                    nets.append(cash - fee); fund.append(fd > 0)
                nets = np.array(nets)
                OUT["life"][f"{name} | k{k} | edge-{int(hc*100)}% | {per}"] = dict(net_mean=round(float(nets.mean())), net_median=round(float(np.median(nets))),
                    net_p10=round(float(np.percentile(nets, 10))), P_neg=round(100 * float((nets < 0).mean()), 1), P_funded_120=round(100 * float(np.mean(fund)), 1))
        print("life", name, k, [OUT["life"][f"{name} | k{k} | edge-{e}% | {per}"]["net_mean"] for e in (0, 35) for per in ("T1", "T2")], flush=True)
    json.dump(OUT, open(os.path.join(HERE, "prop_survey_sim.json"), "w"), indent=1)


if __name__ == "__main__":
    run()
