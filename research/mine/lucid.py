"""Lucid Trading 'LucidFlex 50K' vs Apex 50K (2026 rules) on the NQMaster minute paths (Ultra, WR70Plus; IS/C24/REAL).
LucidFlex eval  : target $3,000, max loss $2,000 EOD trailing (threshold = max closing balance - 2,000, locks at +$100 once the
                  closing balance reaches +$2,100); open equity may not touch the threshold intraday; no DLL (optional, off);
                  50% consistency (largest day <= 50% of total profit at pass); NO time limit; one-time fee $105.2, reset $105.
LucidFlex funded: same $2,000 EOD trailing, locks at +$100 (at +$2,100 or at the first payout request); no DLL, no consistency;
                  payout after 5 days >= $150 since last payout and positive cycle profit; amount = min($2,000, 50% of profit),
                  >= $500; 90% split; 5 payouts, then the account leaves the sim (live account / $900 option ignored = conservative);
                  no activation fee. We choose when to request: only when profit >= X (X is a policy parameter).
Apex 50K 2026   : evaluated with eod_eval.run_eval / pa_run (D=2000; INTRA or EOD+DLL1000 pause), 21 sessions, fee $105, PA fee $90."""
import os, sys, pickle, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eod_eval import run_eval, pa_run, CAPS, RES

@njit(cache=True)
def lucid_eval(day, fav, adv, rel, ndays, start, k, dg, maxd):
    i = np.searchsorted(day, start); eq = 0.0; pke = 0.0; best = -1e9; d = start
    while d < start + maxd and d < ndays:
        thr = 100.0 if pke >= 2100.0 else pke - 2000.0
        last = 0.0; stopped = False
        while i < len(day) and day[i] == d:
            if stopped: i += 1; continue
            if eq + k * adv[i] <= thr: return -1, d - start + 1
            last = rel[i]; i += 1
            dp = k * last; tot = eq + dp
            if tot >= 3000.0 and max(best, dp) <= 0.5 * tot: return 1, d - start + 1
            if dg > 0 and dp >= dg: stopped = True
        dp = k * last; eq += dp
        if dp > best: best = dp
        if eq > pke: pke = eq
        d += 1
    return 0, d - start

@njit(cache=True)
def lucid_funded(day, fav, adv, rel, start, end, k, X, own_dl):
    i = np.searchsorted(day, start); bal = 0.0; pke = 0.0; locked = False; cash = 0.0; n = 0; qd = 0; cyc0 = 0.0; d = start
    while d < end:
        thr = 100.0 if (locked or pke >= 2100.0) else pke - 2000.0
        last = 0.0; stopped = False
        while i < len(day) and day[i] == d:
            if stopped: i += 1; continue
            if bal + k * adv[i] <= thr: return cash, n, -1, d
            last = rel[i]; i += 1
            if own_dl > 0 and k * last <= -own_dl: stopped = True
        dp = k * last; bal += dp
        if bal > pke: pke = bal
        if dp >= 150.0: qd += 1
        if qd >= 5 and bal - cyc0 > 0 and bal >= X:
            amt = min(2000.0, 0.5 * bal)
            if amt >= 500.0:
                bal -= amt; cash += 0.9 * amt; n += 1; qd = 0; cyc0 = bal; locked = True
                if n == 5: return cash, n, 1, d
        d += 1
    return cash, n, 0, end

@njit(cache=True)
def life_lucid(day, fav, adv, rel, nd, H, step, ek, dg, fk, X, own_dl, fee, out):
    r = 0
    for s in range(0, nd - H, step):
        i = s; cash = 0.0; fees = 0.0; npay = 0; nev = 0; nf = 0; nb = 0
        while i < s + H:
            nev += 1; fees += fee
            res, used = lucid_eval(day, fav, adv, rel, nd, i, ek, dg, s + H - i)
            j = i + used
            if res != 1: i = j; continue
            nf += 1
            c, n, st, e = lucid_funded(day, fav, adv, rel, j, s + H, fk, X, own_dl)
            cash += c; npay += n; nb += st == -1; i = e + 1
        out[r, 0] = cash - fees; out[r, 1] = cash; out[r, 2] = fees; out[r, 3] = npay; out[r, 4] = nev; out[r, 5] = nf; out[r, 6] = nb; r += 1
    return r

@njit(cache=True)
def life_apex(day, fav, adv, rel, nd, H, step, D, eod, dll, k0, dlate, lg, kl, dl, pk, pdl, fee, pafee, out):
    r = 0
    for s in range(0, nd - H, step):
        i = s; cash = 0.0; fees = 0.0; npay = 0; nev = 0; nf = 0; nb = 0
        while i < s + H:
            nev += 1; fees += fee
            res, used = run_eval(day, fav, adv, rel, nd, i, 3000.0, D, min(21, s + H - i), eod, dll, False, k0, dlate, lg, kl, dl)
            j = i + used
            if res != 1: i = j; continue
            nf += 1; fees += pafee
            # pa_run returns at bust / 6 payouts / horizon end; find the end day by re-walking is costly -> approximate PA life
            c, n, st = pa_run(day, fav, adv, rel, j, s + H, pk, D, eod, dll if eod else 0.0, pdl, CAPS)
            cash += c; npay += n; nb += st == -1
            i = s + H if st == 0 else j + 1 + _pa_end(day, fav, adv, rel, j, s + H, pk, D, eod, dll if eod else 0.0, pdl)
        out[r, 0] = cash - fees; out[r, 1] = cash; out[r, 2] = fees; out[r, 3] = npay; out[r, 4] = nev; out[r, 5] = nf; out[r, 6] = nb; r += 1
    return r

@njit(cache=True)
def _pa_end(day, fav, adv, rel, start, end, k, D, eod, dll, own):
    # smallest horizon h such that pa_run over [start, start+h) already terminates (bust or 6 payouts)
    lo = 1; hi = end - start
    while lo < hi:
        mid = (lo + hi) // 2
        c, n, st = pa_run(day, fav, adv, rel, start, start + mid, k, D, eod, dll, own, CAPS)
        if st != 0: hi = mid
        else: lo = mid + 1
    return lo

def summarize(out, r):
    o = out[:r]
    return dict(net_mo=o[:, 0].mean() / 12, p10_mo=np.percentile(o[:, 0], 10) / 12, P_year_loss=(o[:, 0] < 0).mean(), evals_yr=o[:, 4].mean(), funded_yr=o[:, 5].mean(),
                payouts_yr=o[:, 3].mean(), busts_yr=o[:, 6].mean(), fees_yr=o[:, 2].mean())

if __name__ == "__main__":
    PROF = {"Ultra": pickle.load(open(os.path.join(RES, "mine", "ultra_paths.pkl"), "rb")), "WR70Plus": pickle.load(open(os.path.join(RES, "mine", "wr70plus_paths.pkl"), "rb"))}
    PER = ("IS", "C24", "REAL"); rows_e = []; rows_f = []; rows_l = []
    for prof, PP in PROF.items():
        for k in (1, 2, 3, 4):
            for dg in (0.0, 1000.0, 1400.0):
                r = dict(prof=prof, k=k, dg=dg)
                for per in PER:
                    P = PP[per]; res = np.array([lucid_eval(P["day"], P["fav"], P["adv"], P["rel"], P["ndays"], s, k, dg, 400) for s in range(P["ndays"] - 120)])
                    ok = res[:, 0] == 1; done = res[:, 0] != 0
                    r.update({f"{per}_pass": round(100 * ok.sum() / max(done.sum(), 1), 1), f"{per}_p21": round(100 * (ok & (res[:, 1] <= 21)).mean(), 1),
                              f"{per}_p42": round(100 * (ok & (res[:, 1] <= 42)).mean(), 1), f"{per}_meddays": float(np.median(res[ok, 1])) if ok.any() else np.nan,
                              f"{per}_open": round(100 * (~done).mean(), 1)})
                rows_e.append(r)
        for k in (1, 2):
            for X in (1000.0, 2000.0, 3000.0, 4000.0):
                for own in (0.0, 400.0, 600.0):
                    r = dict(prof=prof, k=k, X=X, own_dl=own)
                    for per in PER:
                        P = PP[per]; a = np.array([lucid_funded(P["day"], P["fav"], P["adv"], P["rel"], s, s + 252, k, X, own) for s in range(P["ndays"] - 252)])
                        r.update({f"{per}_Ecash": round(a[:, 0].mean()), f"{per}_bust": round(100 * (a[:, 2] == -1).mean(), 1), f"{per}_any": round(100 * (a[:, 1] >= 1).mean(), 1),
                                  f"{per}_all5": round(100 * (a[:, 1] == 5).mean(), 1), f"{per}_daysto5": float(np.median(a[a[:, 1] == 5, 3] - np.arange(len(a))[a[:, 1] == 5])) if (a[:, 1] == 5).any() else np.nan})
                    rows_f.append(r)
        print(prof, "eval+funded done", flush=True)
    E = pd.DataFrame(rows_e); F = pd.DataFrame(rows_f)
    E.to_csv(os.path.join(RES, "mine", "lucid_eval.csv"), index=False); F.to_csv(os.path.join(RES, "mine", "lucid_funded.csv"), index=False)
    pd.set_option("display.width", 320); pd.set_option("display.max_rows", 300)
    print(E.to_string(index=False)); print(F.to_string(index=False))
    # ---- 12-month lifecycle per account slot
    out = np.zeros((2000, 7))
    for prof, PP in PROF.items():
        for ek, dg in ((1, 0.0), (2, 0.0), (2, 1400.0), (3, 1400.0), (4, 1400.0)):
            for fk, X, own in ((1, 2000.0, 0.0), (1, 3000.0, 0.0), (1, 4000.0, 0.0), (1, 3000.0, 400.0), (2, 4000.0, 600.0)):
                r = dict(firm="Lucid Flex", prof=prof, eval=f"k{ek} dg{int(dg)}", funded=f"k{fk} X{int(X)} dl{int(own)}")
                for per in PER:
                    P = PP[per]; n = life_lucid(P["day"], P["fav"], P["adv"], P["rel"], P["ndays"], 252, 3, ek, dg, fk, X, own, 105.2, out)
                    s = summarize(out, n); r.update({f"{per}_{a}": round(b, 2) for a, b in s.items()})
                rows_l.append(r)
        for plan, D, eod, dll, pol in (("Apex INTRA 2026", 2000.0, False, 0.0, (1, 8, 2000.0, 2, 400.0)), ("Apex EOD 2026", 2000.0, True, 1000.0, (2, 12, 1500.0, 3, 600.0))):
            for pk, pdl in ((1, 400.0),):
                r = dict(firm=plan, prof=prof, eval=str(pol), funded=f"k{pk} dl{int(pdl)}")
                for per in PER:
                    P = PP[per]; n = life_apex(P["day"], P["fav"], P["adv"], P["rel"], P["ndays"], 252, 3, D, eod, dll, *pol, pk, pdl, 105.0, 90.0, out)
                    s = summarize(out, n); r.update({f"{per}_{a}": round(b, 2) for a, b in s.items()})
                rows_l.append(r)
        print(prof, "lifecycle done", flush=True)
    L = pd.DataFrame(rows_l); L.to_csv(os.path.join(RES, "mine", "lucid_life.csv"), index=False)
    print(L[["firm", "prof", "eval", "funded"] + [f"{p}_net_mo" for p in PER] + [f"{p}_p10_mo" for p in PER] + ["REAL_evals_yr", "REAL_funded_yr", "REAL_payouts_yr", "REAL_busts_yr"]].to_string(index=False))
