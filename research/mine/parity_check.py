"""Parity gate NinjaTrader <-> research (2026-10-16). Wraps nt_compare.py and turns it into a pass/fail check that is run before
committing any change to NQMaster.cs (and after every Strategy Analyzer export Federico sends).

Gates (fixed 2026-10-16, before looking at new exports):
  G1 overall: >= 92% of research trades matched (same date, module, direction, entry within --tol minutes)
  G2 money  : NT $ per contract within +-3% of research on the matched trades
  G3 daily  : correlation of daily $ >= 0.95
  G4 module : every module with >= 20 research trades matches >= 90%; below that the module is FLAGGED (not a silent pass)
Known, explained differences (documented; still reported, never hidden):
  VW13  - research lists the 2nd lot (distance >= 0.30 ATR) as a separate trade, NT books one trade with qty 2 -> research deduplicated
  ICT   - 5-minute limit entry; NT fills the retest a few bars later than research on some days -> tolerance 45 min for ICT
  holiday windows - research turns the trend filter off ~20 days after holidays (research artifact, not code)
Usage (from research/mine):  python parity_check.py <NT trades.csv> [--set ultra_r] [--tol 3]
Writes parity_<set>_<date>.md (with git commit and NQMaster.cs SHA-256) and returns exit code 1 if any gate fails."""
import os, sys, hashlib, subprocess, argparse, datetime, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from nt_compare import research_set, nt_frame, match

TOL_MOD = {"ICT": 45}
G1, G2, G3, G4, NMIN = 92.0, 3.0, 0.95, 90.0, 20


def sha(path):
    try: return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    except OSError: return "n/a"


def run(csv, setname, tol, tz):
    R, inst = research_set(setname); N = nt_frame(csv, tz)
    lo, hi = max(R.date.min(), N.date.min()), min(R.date.max(), N.date.max())
    R = R[(R.date >= lo) & (R.date <= hi)].copy(); N = N[(N.date >= lo) & (N.date <= hi)].copy()
    R = R.drop_duplicates(["date", "mod", "tin", "d"]).reset_index(drop=True); N = N.reset_index(drop=True)   # VW13 2nd lot = one trade in NT
    R["u1"] = R.u
    parts_r, parts_n = [], []
    for md in sorted(set(R["mod"]) | set(N["mod"])):
        r = R[R["mod"] == md].reset_index(drop=True); n = N[N["mod"] == md].reset_index(drop=True)
        if len(r) and len(n): r, n = match(r, n, TOL_MOD.get(md, tol))
        else: r = r.assign(k=-1); n = n.assign(k=-1)
        parts_r.append(r.assign(mod=md)); parts_n.append(n.assign(mod=md))
    rows = []; fails = []
    for r, n in zip(parts_r, parts_n):
        md = r["mod"].iloc[0] if len(r) else n["mod"].iloc[0]
        m = r[r.k >= 0]; pct = 100 * len(m) / len(r) if len(r) else np.nan
        mn = n.loc[m.k.values, "u"].sum() if len(m) else 0.0
        st = "ok" if len(r) >= NMIN and pct >= G4 else ("FAIL" if len(r) >= NMIN else "low-n")
        if st == "FAIL": fails.append(f"G4 {md} {pct:.1f}%")
        rows.append(dict(module=md, research=len(r), nt=len(n), matched=len(m), pct=round(pct, 1) if pct == pct else None,
                         res_matched_usd=round(m.u1.sum()), nt_matched_usd=round(mn), res_usd=round(r.u1.sum()), nt_usd=round(n.u.sum()), gate=st))
    R2 = pd.concat(parts_r, ignore_index=True); N2 = pd.concat(parts_n, ignore_index=True)
    tot_pct = 100 * sum(x["matched"] for x in rows) / max(1, sum(x["research"] for x in rows))
    mr = sum(x["res_matched_usd"] for x in rows); mn = sum(x["nt_matched_usd"] for x in rows)
    dev = 100 * (mn - mr) / abs(mr) if mr else np.nan
    dr = R2.groupby("date").u1.sum(); dn = N2.groupby("date").u.sum(); idx = dr.index.union(dn.index)
    dcorr = float(np.corrcoef(dr.reindex(idx, fill_value=0), dn.reindex(idx, fill_value=0))[0, 1])
    if tot_pct < G1: fails.append(f"G1 {tot_pct:.1f}% < {G1}")
    if not abs(dev) <= G2: fails.append(f"G2 {dev:+.1f}% outside +-{G2}%")
    if dcorr < G3: fails.append(f"G3 {dcorr:.3f} < {G3}")
    return dict(lo=lo, hi=hi, rows=rows, tot_pct=tot_pct, dev=dev, dcorr=dcorr, fails=fails, nR=len(R2), nN=len(N2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--set", default="ultra_r"); ap.add_argument("--tol", type=int, default=3)
    ap.add_argument("--tz", default="America/Argentina/Buenos_Aires"); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    res = run(a.csv, a.set, a.tol, a.tz)
    try: commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=HERE, text=True).strip()
    except Exception: commit = "n/a"
    S = pd.DataFrame(res["rows"])
    txt = (f"# Paridad NinjaTrader vs investigación: {a.set} ({res['lo']}-{res['hi']})\n\n"
           f"- Commit {commit}, NQMaster.cs SHA-256 {sha(os.path.join(HERE, '..', '..', 'NQMaster.cs'))}, export `{os.path.basename(a.csv)}`, generado {datetime.date.today()}.\n"
           f"- G1 emparejados {res['tot_pct']:.1f}% (umbral {G1}%) | G2 $ emparejados NT vs investigación {res['dev']:+.1f}% (±{G2}%) | G3 correlación diaria {res['dcorr']:.3f} (≥ {G3})\n"
           f"- Resultado: **{'PASA' if not res['fails'] else 'FALLA: ' + '; '.join(res['fails'])}**\n\n```\n{S.to_string(index=False)}\n```\n")
    out = a.out or os.path.join(HERE, f"parity_{a.set}_{datetime.date.today():%Y%m%d}.md")
    open(out, "w", encoding="utf-8").write(txt); print(txt)
    sys.exit(1 if res["fails"] else 0)
