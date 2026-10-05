"""Professional statistics for Apex 50K (intraday trailing, open-equity) with the NQMaster profiles, on minute-level paths.
Eval: target $3,000, trailing $2,500 on open equity, 21 trading days (30 calendar days), eval price c (default $105, range 90-120).
PA (2026 rules): trailing $2,500 on open equity until the peak reaches 52,600, then the floor locks at 50,100; payout request when
balance >= 52,600 and >= 5 days of +$250 since the last payout and best day < 50% of the cycle profit; amount = min(cap, bal-52,100),
>= $500; caps 1500,1500,2000,2500,2500,3000; account closes after 6 payouts. PA activation fee f (default $90).
Optional PA daily guards: stop the day after +dg realized (consistency helper) or after -dl realized."""
import os, sys, pickle, json, math, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evalfast import run as eval_run
CAPS = np.array([1500., 1500., 2000., 2500., 2500., 3000.])

@njit(cache=True)
def pa_detail(day, fav, adv, rel, start, end, k, DD, lock_at, lock_floor, req_bal, safety, qday, caps, dg, dl, out_pay):
    """Returns cash, n payouts, status (-1 bust, 1 done, 0 open), end day, first payout day; payout days written into out_pay."""
    i = np.searchsorted(day, start)
    bal = 0.0; pk = 0.0; cash = 0.0; n = 0; cyc0 = 0.0; best = -1e9; qd = 0; d = start; first = -1
    while d < end:
        stopped = False; last = 0.0
        while i < len(day) and day[i] == d:
            if stopped: i += 1; continue
            thr = lock_floor if pk >= lock_at else pk - DD
            if bal + k * adv[i] <= thr: return cash, n, -1, d, first
            b = bal + k * fav[i]
            if b > pk: pk = b
            last = rel[i]; i += 1
            if dg > 0 and k * last >= dg: stopped = True
            if dl > 0 and k * last <= -dl: stopped = True
        dp = k * last; bal += dp
        if bal > pk: pk = bal
        if dp >= qday: qd += 1
        if dp > best: best = dp
        prof = bal - cyc0
        if qd >= 5 and bal >= req_bal and prof > 0 and best < 0.5 * prof:
            amt = min(caps[n], bal - safety)
            if amt >= 500:
                bal -= amt; cash += amt; out_pay[n] = d; n += 1; cyc0 = bal; best = -1e9; qd = 0
                if first < 0: first = d
                if n == 6: return cash, n, 1, d, first
        d += 1
    return cash, n, 0, end, first

def eval_attempts(P, k, T=3000.0, D=2500.0, maxd=21):
    r = np.array([eval_run(P["day"], P["fav"], P["adv"], P["rel"], P["ndays"], s, T, D, maxd, 0, k, 1, 0.0, 0.0, 0.0) for s in range(P["ndays"] - maxd)])
    return r[:, 0], r[:, 1]

def pa_runs(P, k, dg=0.0, dl=0.0, H=252):
    rows = []; pay = np.zeros(6)
    for s in range(0, P["ndays"] - 60):
        pay[:] = -1
        cash, n, st, end, first = pa_detail(P["day"], P["fav"], P["adv"], P["rel"], s, min(P["ndays"], s + H), k, 2500.0, 2600.0, 100.0, 2600.0, 2100.0, 250.0, CAPS, dg, dl, pay)
        rows.append((cash, n, st, end - s, (first - s) if first >= 0 else np.nan, s + H > P["ndays"]))
    return pd.DataFrame(rows, columns=["cash", "n", "status", "life", "first", "truncated"])

def lifecycle(P, ek, pk, c, f, dg=0.0, dl=0.0, H=252, step=3):
    out = []; pay = np.zeros(6); nd = P["ndays"]
    for s in range(0, nd - H, step):
        i = s; cash = fees = 0.0; npay = ne = npa = nb = 0
        while i < s + H:
            ne += 1; fees += c
            r, used = eval_run(P["day"], P["fav"], P["adv"], P["rel"], nd, i, 3000.0, 2500.0, min(21, s + H - i), 0, ek, 1, 0.0, 0.0, 0.0)
            j = i + used
            if r != 1: i = j; continue
            fees += f; npa += 1
            cs, n, st, end, first = pa_detail(P["day"], P["fav"], P["adv"], P["rel"], j, s + H, pk, 2500.0, 2600.0, 100.0, 2600.0, 2100.0, 250.0, CAPS, dg, dl, pay)
            cash += cs; npay += n; nb += st == -1; i = end + 1
        out.append((cash - fees, cash, fees, npay, ne, npa, nb))
    return pd.DataFrame(out, columns=["net", "cash", "fees", "payouts", "evals", "pas", "pa_busts"])

def geo(p, c):
    q = 1 - p
    return dict(p=p, E_attempts=1 / p, SD_attempts=math.sqrt(q) / p, P_first_try=p, P_need_2plus=q, P_need_3plus=q ** 2, P_need_5plus=q ** 4,
                P_6_busts_in_row=q ** 6, attempts_90pct=math.ceil(math.log(0.10) / math.log(q)) if q > 0 else 1, attempts_95pct=math.ceil(math.log(0.05) / math.log(q)) if q > 0 else 1,
                E_cost=c / p, cost_90pct=c * (math.ceil(math.log(0.10) / math.log(q)) if q > 0 else 1))

if __name__ == "__main__":
    RES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROFILES = {"WR70Plus": pickle.load(open(os.path.join(RES, "mine", "wr70plus_paths.pkl"), "rb")), "Ultra": pickle.load(open(os.path.join(RES, "mine", "ultra_paths.pkl"), "rb"))}
    REP = {}
    for prof, PP in PROFILES.items():
        for per in ("REAL", "C24", "IS"):
            P = PP[per]; R = REP.setdefault(prof, {}).setdefault(per, {})
            # ---- evaluation, per attempt
            for k in (1, 2, 3, 4, 5, 6):
                res, used = eval_attempts(P, k)
                p = (res == 1).mean(); b = (res == -1).mean(); t = (res == 0).mean()
                dp = used[res == 1]; db = used[res == -1]
                e = dict(pass_=p, bust=b, timeout=t, mean_attempt_days=used.mean(),
                         days_pass_q=[float(np.percentile(dp, q)) for q in (10, 25, 50, 75, 90)] if len(dp) else None,
                         days_bust_q=[float(np.percentile(db, q)) for q in (25, 50, 75)] if len(db) else None,
                         E_days_to_funded=used.mean() / p if p > 0 else None)
                for c in (90, 105, 120): e[f"geo_{c}"] = geo(p, c)
                R[f"eval_k{k}"] = e
            # ---- funded account (PA), per PA started on every day
            for k in (1, 2):
                for dg, dl in ((0.0, 0.0), (750.0, 0.0), (1000.0, 0.0), (0.0, 600.0), (1000.0, 600.0)):
                    D = pa_runs(P, k, dg, dl); full = D[~D.truncated]
                    dist = {int(n): float((full.n == n).mean()) for n in range(7)}
                    R[f"pa_k{k}_dg{int(dg)}_dl{int(dl)}"] = dict(P_any_payout=float((full.n >= 1).mean()), P_bust=float((full.status == -1).mean()), P_all6=float((full.n == 6).mean()),
                        E_cash=float(full.cash.mean()), med_cash=float(full.cash.median()), payout_dist=dist, med_days_first=float(full["first"].median()),
                        q_days_first=[float(np.nanpercentile(full["first"], q)) for q in (25, 50, 75)], E_life=float(full.life.mean()), n=len(full))
            # ---- 12-month lifecycle per account slot, eval price 105 (+ 90 and 120), PA fee 90
            for ek in (1, 2, 3, 4, 6):
                for pk in (1, 2):
                    for c in (90, 105, 120):
                        L = lifecycle(P, ek, pk, c, 90.0)
                        R[f"life_e{ek}_p{pk}_c{c}"] = dict(net_mo=float(L.net.mean() / 12), p10_mo=float(L.net.quantile(0.1) / 12), p90_mo=float(L.net.quantile(0.9) / 12),
                            P_year_loss=float((L.net < 0).mean()), evals_yr=float(L.evals.mean()), pas_yr=float(L.pas.mean()), payouts_yr=float(L.payouts.mean()),
                            pa_busts_yr=float(L.pa_busts.mean()), fees_yr=float(L.fees.mean()), cash_yr=float(L.cash.mean()))
            print(prof, per, "done", flush=True)
    json.dump(REP, open(os.path.join(RES, "mine", "apex50_report.json"), "w"), indent=1)
    print("saved")
