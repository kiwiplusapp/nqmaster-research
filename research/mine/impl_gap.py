"""2026-10-16 C2: implementation-gap tracker. For a NinjaTrader trade export (Strategy Analyzer, Sim101 or a live/prop account), per
module: matched trades, research $ vs NT $ per contract, the gap per trade with its t-statistic, and the gap in $ per month; plus the
whole-account comparison of the last 60 trading days vs research. Thresholds fixed in advance:
  module ALERT  : >= 30 matched trades, mean gap <= -max($5, 25% of |research mean|) per trade and t <= -2
  account ALERT : last 60 trading days NT $ per contract below 65% of research (the 35% planning haircut) and the difference
                  below -2 standard errors of the daily difference
Usage (from research/mine): python impl_gap.py <NT trades.csv> [--set ultra_r] -> impl_gap_<set>_<date>.md, exit 1 on ALERT.
For live accounts the research set must cover the same dates (rebuild the research trades with new data first)."""
import os, sys, argparse, datetime, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from nt_compare import research_set, nt_frame, match
from parity_check import TOL_MOD

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--set", default="ultra_r"); ap.add_argument("--tol", type=int, default=3)
    ap.add_argument("--tz", default="America/Argentina/Buenos_Aires"); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    R, inst = research_set(a.set); N = nt_frame(a.csv, a.tz)
    lo, hi = max(R.date.min(), N.date.min()), min(R.date.max(), N.date.max())
    R = R[(R.date >= lo) & (R.date <= hi)].drop_duplicates(["date", "mod", "tin", "d"]).reset_index(drop=True); N = N[(N.date >= lo) & (N.date <= hi)].reset_index(drop=True)
    rows = []; alerts = []; months = max(1.0, (pd.to_datetime(str(hi)) - pd.to_datetime(str(lo))).days / 30.4)
    for md in sorted(set(R["mod"]) | set(N["mod"])):
        r = R[R["mod"] == md].reset_index(drop=True); n = N[N["mod"] == md].reset_index(drop=True)
        if not len(r) or not len(n): rows.append(dict(module=md, matched=0)); continue
        r, n = match(r, n, TOL_MOD.get(md, a.tol)); m = r[r.k >= 0]
        if len(m) < 2: rows.append(dict(module=md, matched=len(m))); continue
        g = n.loc[m.k.values, "u"].to_numpy() - m.u.to_numpy(); se = g.std(ddof=1) / np.sqrt(len(g)); t = g.mean() / se if se > 0 else 0.0
        thr = max(5.0, 0.25 * abs(m.u.mean()))
        flag = len(g) >= 30 and g.mean() <= -thr and t <= -2
        if flag: alerts.append(md)
        rows.append(dict(module=md, matched=len(m), research_per_trade=round(float(m.u.mean()), 1), nt_per_trade=round(float(m.u.mean() + g.mean()), 1),
                         gap_per_trade=round(float(g.mean()), 1), t=round(float(t), 2), gap_per_month=round(float(g.sum() / months)),
                         unmatched_research_usd=round(float(r[r.k < 0].u.sum())), unmatched_nt_usd=round(float(n[n.k < 0].u.sum())), alert="ALERT" if flag else ""))
    S = pd.DataFrame(rows)
    d_all = sorted(set(R.date) | set(N.date)); last = d_all[-60:] if len(d_all) >= 60 else d_all
    dr = R.groupby("date").u.sum().reindex(last, fill_value=0.0); dn = N.groupby("date").u.sum().reindex(last, fill_value=0.0)
    diff = dn - dr; se = diff.std(ddof=1) * np.sqrt(len(diff)) if len(diff) > 1 else np.inf
    acct_alert = dn.sum() < 0.65 * dr.sum() and diff.sum() < -2 * se
    txt = (f"# Brecha de implementación: {a.set} ({lo}-{hi}, {months:.1f} meses)\n\n"
           f"- Últimos {len(last)} días hábiles: investigación ${dr.sum():,.0f}, NinjaTrader ${dn.sum():,.0f} por contrato "
           f"(umbral 65% = ${0.65 * dr.sum():,.0f}; diferencia {diff.sum():+,.0f}, 2 errores estándar = {2 * se:,.0f}).\n"
           f"- Cuenta: **{'ALERTA' if acct_alert else 'ok'}** | Módulos en alerta: **{', '.join(alerts) if alerts else 'ninguno'}**\n\n```\n{S.to_string(index=False)}\n```\n")
    out = a.out or os.path.join(HERE, f"impl_gap_{a.set}_{datetime.date.today():%Y%m%d}.md")
    open(out, "w", encoding="utf-8").write(txt); print(txt)
    sys.exit(1 if (alerts or acct_alert) else 0)
