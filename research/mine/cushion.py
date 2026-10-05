"""Cushion-based sizing in the FUNDED account (and the full 12-month lifecycle) for LucidFlex 50K and Apex 50K (2026 EOD rules).
Size each day from the cushion = balance - current loss threshold (known at the session start):
  k = k_lo if cushion < C1;  k_mid if C1 <= cushion < C2;  k_hi if cushion >= C2.
Lucid scaling plan respected (max 20/30/40 micros at profit <1k/1-2k/>=2k; our max simultaneous exposure is 5 units per lot,
so k <= 4 always fits). Payout policy: request when profit >= X (Lucid: 50% of profit up to $2,000; 5 payouts; 90% split)."""
import os, sys, pickle, itertools, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lucid import lucid_eval, RES
from eod_eval import run_eval, CAPS

@njit(cache=True)
def lucid_funded_dyn(day, fav, adv, rel, start, end, klo, kmid, khi, C1, C2, X, own_dl):
    i = np.searchsorted(day, start); bal = 0.0; pke = 0.0; locked = False; cash = 0.0; n = 0; qd = 0; cyc0 = 0.0; d = start
    while d < end:
        thr = 100.0 if (locked or pke >= 2100.0) else pke - 2000.0
        cu = bal - thr
        k = klo if cu < C1 else (kmid if cu < C2 else khi)
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
def life(day, fav, adv, rel, nd, H, step, ek, klo, kmid, khi, C1, C2, X, own_dl, fee, out):
    r = 0
    for s in range(0, nd - H, step):
        i = s; cash = 0.0; fees = 0.0; npay = 0; nev = 0; nf = 0; nb = 0
        while i < s + H:
            nev += 1; fees += fee
            res, used = lucid_eval(day, fav, adv, rel, nd, i, ek, 0.0, s + H - i)
            j = i + used
            if res != 1: i = j; continue
            nf += 1
            c, n, st, e = lucid_funded_dyn(day, fav, adv, rel, j, s + H, klo, kmid, khi, C1, C2, X, own_dl)
            cash += c; npay += n; nb += st == -1; i = e + 1
        out[r, 0] = cash - fees; out[r, 1] = npay; out[r, 2] = nev; out[r, 3] = nf; out[r, 4] = nb; r += 1
    return r

if __name__ == "__main__":
    PROF = {"Ultra": pickle.load(open(os.path.join(RES, "mine", "ultra_paths.pkl"), "rb")), "WR70Plus": pickle.load(open(os.path.join(RES, "mine", "wr70plus_paths.pkl"), "rb"))}
    PER = ("IS", "C24", "REAL")
    POL = [("fijo 1", 1, 1, 1, 0, 0), ("fijo 2", 2, 2, 2, 0, 0)]
    for klo, kmid, khi in ((1, 2, 2), (1, 2, 3), (1, 2, 4), (1, 1, 2), (1, 1, 3), (2, 2, 3), (2, 3, 4)):
        for C1, C2 in ((1500, 2500), (2000, 3000), (2500, 4000), (3000, 5000)):
            POL.append((f"{klo}/{kmid}/{khi} @ {C1}/{C2}", klo, kmid, khi, C1, C2))
    rows = []
    for prof, PP in PROF.items():
        for nm, klo, kmid, khi, C1, C2 in POL:
            for X in (3000.0, 4000.0, 5000.0):
                for own in (0.0, 600.0):
                    r = dict(prof=prof, pol=nm, X=X, own_dl=own)
                    for per in PER:
                        P = PP[per]; a = np.array([lucid_funded_dyn(P["day"], P["fav"], P["adv"], P["rel"], s, s + 252, klo, kmid, khi, float(C1), float(C2), X, own) for s in range(P["ndays"] - 252)])
                        r.update({f"{per}_Ecash": round(a[:, 0].mean()), f"{per}_bust": round(100 * (a[:, 2] == -1).mean(), 1), f"{per}_all5": round(100 * (a[:, 1] == 5).mean(), 1)})
                    r["minEcash"] = min(r[f"{p}_Ecash"] for p in PER)
                    rows.append(r)
        print(prof, "funded done", flush=True)
    F = pd.DataFrame(rows); F.to_csv(os.path.join(RES, "mine", "cushion_funded.csv"), index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200)
    for prof in PROF:
        x = F[F.prof == prof].sort_values("minEcash", ascending=False)
        print("\n==", prof, "funded: best by worst-period expected cash"); print(x.head(12).to_string(index=False))
        print(x[x.pol.isin(["fijo 1", "fijo 2"])].to_string(index=False))
    # lifecycle with the best robust funded policies (+ fixed references), eval with 3 contracts
    out = np.zeros((2000, 5)); L = []
    for prof, PP in PROF.items():
        x = F[F.prof == prof].sort_values("minEcash", ascending=False).head(4)
        cand = [(r.pol, r.X, r.own_dl) for r in x.itertuples()] + [("fijo 1", 3000.0, 0.0), ("fijo 2", 4000.0, 600.0)]
        for nm, X, own in cand:
            p = next(pp for pp in POL if pp[0] == nm)
            for ek in (1, 2, 3):
                r = dict(prof=prof, funded=f"{nm} X{int(X)} dl{int(own)}", eval_k=ek)
                for per in PER:
                    P = PP[per]; n = life(P["day"], P["fav"], P["adv"], P["rel"], P["ndays"], 252, 3, ek, p[1], p[2], p[3], float(p[4]), float(p[5]), X, own, 105.2, out)
                    o = out[:n]; r.update({f"{per}_mo": round(o[:, 0].mean() / 12), f"{per}_p10": round(np.percentile(o[:, 0], 10) / 12), f"{per}_busts": round(o[:, 4].mean(), 2)})
                L.append(r)
    Lf = pd.DataFrame(L); Lf.to_csv(os.path.join(RES, "mine", "cushion_life.csv"), index=False)
    print(Lf.to_string(index=False))
