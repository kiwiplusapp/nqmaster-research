"""Apex 50K under the March-2026 rules: target $3,000, max drawdown $2,000 (was $2,500 legacy), 30 calendar days (21 sessions).
Plans:  INTRA  - trailing on open equity (real time), no DLL.
        EOD    - threshold = (max end-of-day balance) - D, updated once per day at the close; equity may not touch it intraday;
                 Daily Loss Limit $1,000 on open equity: 'pause' = day liquidated at -$1,000 and stopped, 'fail' = eval failed.
Sizing policy as evalpol (k0, late boost) + optional own realized daily stop dl. Same minute paths as evalpol/apex50_stats.
PA (funded) for both plans: D=2000, trailing until peak >= start+2,100 then floor locks at start+100; payouts as apex50_stats
(request >= 52,600, safety 52,100, caps 1.5/1.5/2/2.5/2.5/3k, 5 days >= $250, 50% consistency); EOD PA adds DLL $1,000 pause."""
import os, sys, pickle, numpy as np, pandas as pd
from numba import njit
RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPS = np.array([1500., 1500., 2000., 2500., 2500., 3000.])

@njit(cache=True)
def run_eval(day, fav, adv, rel, ndays, start, T, D, maxd, eod, dll, dll_fail, k0, d_late, lg, k_late, dl):
    i = np.searchsorted(day, start); eq = 0.0; pk = 0.0; pk_eod = 0.0; d = start
    while d < start + maxd and d < ndays:
        dd = d - start
        k = k_late if (dd >= d_late and eq < lg) else k0
        thr = (pk_eod - D) if eod else 0.0
        last = 0.0; stopped = False; liq = False
        while i < len(day) and day[i] == d:
            if stopped: i += 1; continue
            lo = eq + k * adv[i]
            if eod:
                if lo <= thr: return -1, dd + 1
                if dll > 0 and k * adv[i] <= -dll:
                    if dll_fail: return -1, dd + 1
                    liq = True; stopped = True; i += 1; continue
            else:
                if lo <= pk - D: return -1, dd + 1
                b = eq + k * fav[i]
                if b > pk: pk = b
            last = rel[i]; i += 1
            if eq + k * last >= T: return 1, dd + 1
            if dl > 0 and k * last <= -dl: stopped = True
        eq += (-dll) if liq else k * last
        if eq > pk: pk = eq
        if eq > pk_eod: pk_eod = eq
        d += 1
    return 0, maxd

@njit(cache=True)
def stats_eval(day, fav, adv, rel, ndays, T, D, maxd, eod, dll, dll_fail, k0, d_late, lg, k_late, dl):
    n = ndays - maxd; npass = 0; nbust = 0; p14 = 0; used = 0.0
    for s in range(n):
        r, u = run_eval(day, fav, adv, rel, ndays, s, T, D, maxd, eod, dll, dll_fail, k0, d_late, lg, k_late, dl)
        used += u
        if r == 1:
            npass += 1
            if u <= 14: p14 += 1
        elif r == -1: nbust += 1
    return npass / n, nbust / n, p14 / n, used / n

@njit(cache=True)
def pa_run(day, fav, adv, rel, start, end, k, D, eod, dll, own_dl, caps):
    i = np.searchsorted(day, start); bal = 0.0; pk = 0.0; pk_eod = 0.0; cash = 0.0; n = 0; cyc0 = 0.0; best = -1e9; qd = 0; d = start
    lock_at = D + 100.0
    while d < end:
        stopped = False; last = 0.0; liq = False
        locked = (pk_eod if eod else pk) >= lock_at
        thr_eod = 100.0 if locked else pk_eod - D
        while i < len(day) and day[i] == d:
            if stopped: i += 1; continue
            if eod:
                if bal + k * adv[i] <= thr_eod: return cash, n, -1
                if dll > 0 and k * adv[i] <= -dll: liq = True; stopped = True; i += 1; continue
            else:
                thr = 100.0 if pk >= lock_at else pk - D
                if bal + k * adv[i] <= thr: return cash, n, -1
                b = bal + k * fav[i]
                if b > pk: pk = b
            last = rel[i]; i += 1
            if own_dl > 0 and k * last <= -own_dl: stopped = True
        dp = -dll if liq else k * last; bal += dp
        if bal > pk: pk = bal
        if bal > pk_eod: pk_eod = bal
        if dp >= 250.0: qd += 1
        if dp > best: best = dp
        prof = bal - cyc0
        if qd >= 5 and bal >= 2600.0 and prof > 0 and best < 0.5 * prof:
            amt = min(caps[n], bal - 2100.0)
            if amt >= 500:
                bal -= amt; cash += amt; n += 1; cyc0 = bal; best = -1e9; qd = 0
                if n == 6: return cash, n, 1
        d += 1
    return cash, n, 0

def pa_stats(P, k, D, eod, dll, own_dl, H=252):
    rows = []
    for s in range(0, P["ndays"] - H):
        rows.append(pa_run(P["day"], P["fav"], P["adv"], P["rel"], s, s + H, k, D, eod, dll, own_dl, CAPS))
    a = np.array(rows)
    return dict(E_cash=a[:, 0].mean(), P_bust=(a[:, 2] == -1).mean(), P_any=(a[:, 1] >= 1).mean(), P_all6=(a[:, 1] == 6).mean())

if __name__ == "__main__":
    PROF = {"Ultra": pickle.load(open(os.path.join(RES, "mine", "ultra_paths.pkl"), "rb")), "WR70Plus": pickle.load(open(os.path.join(RES, "mine", "wr70plus_paths.pkl"), "rb"))}
    PLANS = {"INTRA D2500 (legacy)": (2500.0, False, 0.0, False), "INTRA D2000 (2026)": (2000.0, False, 0.0, False),
             "EOD D2000 DLL1000 pausa": (2000.0, True, 1000.0, False), "EOD D2000 DLL1000 quema": (2000.0, True, 1000.0, True)}
    POL = {"fijo 1": (1, 99, 0.0, 1, 0.0), "fijo 2": (2, 99, 0.0, 2, 0.0), "fijo 3": (3, 99, 0.0, 3, 0.0), "fijo 4": (4, 99, 0.0, 4, 0.0),
           "2->3 dia12 +DL800": (2, 12, 2000.0, 3, 800.0), "1->2 dia10": (1, 10, 1500.0, 2, 0.0), "1->2 dia10 +DL500": (1, 10, 1500.0, 2, 500.0),
           "2 +DL800": (2, 99, 0.0, 2, 800.0), "3 +DL900": (3, 99, 0.0, 3, 900.0), "2->3 dia8 +DL900": (2, 8, 1500.0, 3, 900.0)}
    rows = []
    for prof, PP in PROF.items():
        for plan, (D, eod, dll, fail) in PLANS.items():
            for pol, (k0, dlate, lg, kl, dl) in POL.items():
                r = dict(prof=prof, plan=plan, pol=pol)
                for per in ("IS", "C24", "REAL"):
                    P = PP[per]
                    p, b, p14, du = stats_eval(P["day"], P["fav"], P["adv"], P["rel"], P["ndays"], 3000.0, D, 21, eod, dll, fail, k0, dlate, lg, kl, dl)
                    r.update({f"{per}_pass": round(100 * p, 1), f"{per}_bust": round(100 * b, 1), f"{per}_p14": round(100 * p14, 1), f"{per}_days": round(du, 1)})
                rows.append(r)
        print(prof, "eval done", flush=True)
    G = pd.DataFrame(rows); G.to_csv(os.path.join(RES, "mine", "eod_eval.csv"), index=False)
    prow = []
    for prof, PP in PROF.items():
        for plan, D, eod, dll in (("INTRA D2500 (legacy)", 2500.0, False, 0.0), ("INTRA D2000 (2026)", 2000.0, False, 0.0), ("EOD D2000 DLL1000", 2000.0, True, 1000.0)):
            for k, own in ((1, 0.0), (1, 400.0), (2, 0.0), (2, 600.0)):
                r = dict(prof=prof, plan=plan, k=k, own_dl=own)
                for per in ("IS", "C24", "REAL"):
                    s = pa_stats(PP[per], k, D, eod, dll, own)
                    r.update({f"{per}_Ecash": round(s["E_cash"]), f"{per}_bust": round(100 * s["P_bust"], 1), f"{per}_any": round(100 * s["P_any"], 1)})
                prow.append(r)
    H = pd.DataFrame(prow); H.to_csv(os.path.join(RES, "mine", "eod_pa.csv"), index=False)
    pd.set_option("display.width", 320); pd.set_option("display.max_rows", 300)
    print(G[["prof", "plan", "pol", "IS_pass", "C24_pass", "REAL_pass", "IS_bust", "C24_bust", "REAL_bust", "REAL_p14", "REAL_days"]].to_string(index=False))
    print(H.to_string(index=False))
