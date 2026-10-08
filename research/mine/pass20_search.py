"""Federico 2026-10-08: 'raise the win rate of each trade / I want something better'. Two questions, same yardstick:
1) The high-WR mixes (WR 73-80%, small targets) vs WR70Plus: per-trade WR / PF / Sharpe AND Lucid 50K pass rate within 20 days.
2) A direct search for the module x target x size mix that maximises the 20-day Lucid 50K pass rate (chosen on IS = CFD 2020-23),
   then checked out of sample on C24 (CFD 2024-26) and REAL (MNQ futures 2024-26).
Trades: wr70_variants.pkl (every module x target variant) with ICT replaced by the corrected sim, + LATE15 / ENG10 / LATEFH and the
night modules NF05 / LF06 / LF0430. FOMC days removed. Daily resolution: close = day P&L; low = sum over modules of each module's
worst cumulative realized point of the day (sorted by exit time; open-trade drawdown not modelled). Lucid 50K: target 3,000,
EOD-trailing 2,000 locking at +100, best day <= 50% of profit. Same sim for every mix, so the comparison is fair.
-> pass20_search.csv"""
import sys, pickle, random, numpy as np, pandas as pd
from numba import njit
sys.path.insert(0, "."); sys.path.insert(0, "..")
from news import NEWS
FOMC = set(NEWS["FOMC"])
LIM = {"IS": ("nq_1m", 20200201, 20240101), "C24": ("nq_1m", 20240101, 30000000), "REAL": ("mnq_fut", 20240201, 30000000)}
DRIVES = {"NF05": dict(A=2000, T=540, x=0.35, mode=-1, tf=0, k=0.2, stop=0, R=2.0, hold=240),
          "LF06": dict(A=400, T=120, x=0.2, mode=-1, tf=0, k=0.2, stop=0, R=0.5, hold=240),
          "LF0430": dict(A=400, T=30, x=0.1, mode=-1, tf=1, k=0.35, stop=0, R=0.5, hold=240)}

def trades(per):
    src, lo, hi = LIM[per]
    A = pickle.load(open("wr70_variants.pkl", "rb"))[src]
    A = A[(A.date >= lo) & (A.date < hi) & (A["mod"] != "ICT") & ~A.date.isin(FOMC)]
    parts = [pd.DataFrame(dict(date=A.date, mod=A["mod"], var=A["var"].astype(str), tout=A.tout, x=A.u * A.w, u=A.u))]
    from ict_redo import ictf
    I = ictf(per, 1.0); I = I[~I.date.isin(FOMC)]
    parts.append(pd.DataFrame(dict(date=I.date, mod="ICT", var="1.0", tout=I.tout, x=I.u, u=I.u)))
    from ultra_plus_lib import mined
    for key, nm in ((("LATE_MOM", 762), "LATE15"), (("ENGULF_4H", 1172), "ENG10"), (("LATE_MOM", 1107), "LATEFH")):
        M = mined(key, per, nm); parts.append(pd.DataFrame(dict(date=M.date, mod=nm, var="fix", tout=M.tout, x=M.u, u=M.u)))
    from core import Data, run_events
    from families_gold import gen_drive
    D = Data(src + ".npz")
    for nm, p in DRIVES.items():
        df = run_events(D, gen_drive(D, p), flat=955, maxday=1, slip=0.25)
        df = df[(df.date >= lo) & (df.date < hi) & ~df.date.isin(FOMC)]
        parts.append(pd.DataFrame(dict(date=df.date.to_numpy(), mod=nm, var="fix", tout=D.sm[df.xi.to_numpy().astype(int)] + 1, x=df.usd.to_numpy(), u=df.usd.to_numpy())))
    return pd.concat(parts, ignore_index=True)

def matrices(T):
    days = np.array(sorted(T.date.unique())); idx = {d: i for i, d in enumerate(days)}; C = {}; L = {}; S = {}
    for (m, v), g in T.groupby(["mod", "var"]):
        c = np.zeros(len(days)); l = np.zeros(len(days))
        for d, h in g.sort_values("tout").groupby("date"):
            cs = np.cumsum(h.x.to_numpy()); c[idx[d]] = cs[-1]; l[idx[d]] = min(0.0, cs.min())
        C[(m, v)] = c; L[(m, v)] = l; S[(m, v)] = (len(g), int((g.u > 0).sum()), g.x[g.x > 0].sum(), -g.x[g.x <= 0].sum())
    return days, C, L, S

@njit(cache=True)
def p20(C, L, k, T, D, cons, maxd):
    n = len(C); ok = 0; bust = 0; m = n - maxd; dsum = 0
    for s in range(m):
        eq = 0.0; pk = 0.0; best = -1e9
        for d in range(s, s + maxd):
            thr = 100.0 if pk >= D + 100.0 else pk - D
            if eq + k * L[d] <= thr: bust += 1; break
            c = k * C[d]; eq += c
            if c > best: best = c
            if eq > pk: pk = eq
            if eq >= T and best <= cons * eq: ok += 1; dsum += d - s + 1; break
    return 100.0 * ok / m, 100.0 * bust / m, dsum / max(ok, 1)

PERS = ("IS", "C24", "REAL"); DATA = {}
for per in PERS:
    DATA[per] = matrices(trades(per)); print(per, len(DATA[per][0]), "days", len(DATA[per][1]), "streams", flush=True)
STREAMS = sorted(DATA["IS"][1])
OPTS = {}
for (m, v) in STREAMS: OPTS.setdefault(m, []).append(v)
MODS = sorted(OPTS)

def combo(sel, per):
    days, C, L, S = DATA[per]; c = np.zeros(len(days)); l = np.zeros(len(days)); n = w = gp = gl = 0
    for m, ch in sel.items():
        if ch is None or (m, ch[0]) not in C: continue
        v, q = ch; c += q * C[(m, v)]; l += q * L[(m, v)]; a = S[(m, v)]; n += a[0]; w += a[1]; gp += q * a[2]; gl += q * a[3]
    return c, l, dict(wr=100 * w / max(n, 1), pf=gp / gl if gl else 0, sharpe=c.mean() / c.std() * 252 ** .5 if c.std() > 0 else 0,
                      tpd=n / len(days), mo=c.mean() * 21)

def score(sel, per, ks=(1, 2, 3, 4)):
    c, l, st = combo(sel, per); best = (-1, 0, 0, 0)
    for k in ks:
        p, b, dd = p20(c, l, float(k), 3000.0, 2000.0, 0.5, 20)
        if p > best[0]: best = (p, b, dd, k)
    return best, st

def fixed_k(sel, per, k):
    c, l, st = combo(sel, per); p, b, dd = p20(c, l, float(k), 3000.0, 2000.0, 0.5, 20); return p, b, dd, st

def parse(s):
    sel = {}
    for tok in s.split():
        m, rest = tok.split(":"); v, q = rest.rsplit("x", 1); v = v if (m, v) in DATA["IS"][1] else ("%.2f" % float(v) if (m, "%.2f" % float(v)) in DATA["IS"][1] else v); sel[m] = (v, int(q))
    return sel

if __name__ == "__main__":
    random.seed(11)
    NIGHT = "NF05:fixx1 LF06:fixx1 LF0430:fixx1"
    BASE = {"WR70Plus + noche (tu perfil)": "CRT11:2.0x1 ICT:1.0x2 MOM11:0.3x1 MSEQ:0.5x1 MSEQS:0.75x1 ORB60:0.75x1 ORB90:0.6x1 REV06:0.3x1 VOLB_tf1:0.5x1 VW13b:0.5x1 LATE15:fixx1 " + NIGHT,
            "Ultra + noche": "CRT11:2.0x1 ICT:1.0x2 LON:2.0x1 MOM11:0.3x1 MOM1030:0.3x1 MOM13:1.0x1 MSEQ:0.5x1 MSEQS:0.75x1 ON07:1.0x1 ORB60:0.6x1 ORB90:0.6x1 REV06:0.3x1 VOLB_tf0:2.0x1 VW13b:0.5x1 LATE15:fixx1 ENG10:fixx1 LATEFH:fixx1 " + NIGHT,
            "WR 75% (4 trades/dia)": "CRT11:2.0x2 ICT:1.0x2 MOM11:0.3x1 MOM13:0.3x1 MSEQ:0.5x2 MSEQS:0.75x2 ORB60:0.75x2 ORB90:0.3x1 REV06:0.3x1 RSI2_0.15:0.3x1 VOLB_tf1:0.5x2 VW13:0.5x2",
            "WR 75% (2 trades/dia)": "MSEQ:0.5x2 MSEQS:0.75x2 ORB60:0.75x2 ORB90:0.3x1 REV06:0.3x1 RSI2_0.15:0.3x1 VW13:0.5x2",
            "WR 80% (4 trades/dia)": "MOM11:0.3x1 MOM1130:0.3x1 MOM13:0.3x1 ORB60:0.3x2 ORB90:0.3x2 REV06:0.3x1 RSI2_0.15:0.3x1",
            "WR 80% (1 trade/dia)": "MOM11:0.3x1 ORB60:0.3x2"}
    rows = []
    for nm, s in BASE.items():
        sel = parse(s); r = dict(mezcla=nm)
        for per in PERS:
            (p, b, dd, k), st = score(sel, per)
            r.update({f"{per}_wr": st["wr"], f"{per}_pf": st["pf"], f"{per}_sharpe": st["sharpe"], f"{per}_tpd": st["tpd"], f"{per}_p20": p, f"{per}_k": k})
        # contracts chosen on IS, applied to C24 / REAL
        kIS = r["IS_k"]
        for per in ("C24", "REAL"): r[f"{per}_p20_kIS"] = fixed_k(sel, per, kIS)[0]
        r["mods"] = s; rows.append(r); print(nm, {k: round(v, 2) for k, v in r.items() if isinstance(v, float)}, flush=True)
    # direct search on IS
    CH = {m: [None] + [(v, q) for v in OPTS[m] for q in (1, 2)] for m in MODS}
    found = []
    for start in range(30):
        sel = {m: random.choice(CH[m]) for m in MODS}; imp = True
        while imp:
            imp = False
            for m in random.sample(MODS, len(MODS)):
                cur = score(sel, "IS")[0][0]; bc = sel[m]
                for ch in CH[m]:
                    sel[m] = ch; o = score(sel, "IS")[0][0]
                    if o > cur + 1e-9: cur = o; bc = ch; imp = True
                sel[m] = bc
        key = " ".join(f"{m}:{c[0]}x{c[1]}" for m, c in sorted(sel.items()) if c is not None)
        if key not in [f[1] for f in found]: found.append((score(sel, "IS")[0][0], key))
        print("start", start, round(found[-1][0], 1), flush=True)
    found.sort(reverse=True)
    for i, (o, key) in enumerate(found[:8]):
        sel = parse(key); r = dict(mezcla=f"busqueda #{i + 1}")
        for per in PERS:
            (p, b, dd, k), st = score(sel, per)
            r.update({f"{per}_wr": st["wr"], f"{per}_pf": st["pf"], f"{per}_sharpe": st["sharpe"], f"{per}_tpd": st["tpd"], f"{per}_p20": p, f"{per}_k": k})
        kIS = r["IS_k"]
        for per in ("C24", "REAL"): r[f"{per}_p20_kIS"] = fixed_k(sel, per, kIS)[0]
        r["mods"] = key; rows.append(r)
    R = pd.DataFrame(rows); R.to_csv("pass20_search.csv", index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 200)
    cols = ["mezcla"] + [f"{p}_{x}" for p in PERS for x in ("wr", "pf", "sharpe", "tpd")]
    print(R[cols].round(2).to_string(index=False))
    print(R[["mezcla", "IS_p20", "IS_k", "C24_p20_kIS", "REAL_p20_kIS", "C24_p20", "REAL_p20"]].round(1).to_string(index=False))
    print(R[["mezcla", "mods"]].to_string(index=False))
