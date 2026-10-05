"""Stage 1: broad, low-parameter scan of every strategy family. Reports in-sample (2020-2023) and
out-of-sample (2024-2026) statistics in R units (net of 1 tick slippage + $1 RT commission)."""
import itertools
import sys
import time
import numpy as np
import pandas as pd
import engine as en
import evalkit as ev
from common import Ctx, SPLIT

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 30)

cx = Ctx()
o, h, l, c, v, om, dayid = cx.o, cx.h, cx.l, cx.c, cx.v, cx.om, cx.dayid
rows = []


def record(family, cfg, res):
    df = ev.to_df(res, cx.d, family)
    ins = df[df.date < SPLIT]; oos = df[df.date >= SPLIT]
    a = ev.stats(ins); b = ev.stats(oos)
    rows.append(dict(family=family, cfg=cfg,
                     n_is=a.get("n", 0), wr_is=a.get("wr"), avg_is=a.get("avg"), pf_is=a.get("pf"), tot_is=a.get("total"), dd_is=a.get("maxdd"),
                     n_oos=b.get("n", 0), wr_oos=b.get("wr"), avg_oos=b.get("avg"), pf_oos=b.get("pf"), tot_oos=b.get("total"), dd_oos=b.get("maxdd"),
                     avg_risk=round(df.risk.mean(), 1) if len(df) else 0))
    return df


t0 = time.time()
which = sys.argv[1] if len(sys.argv) > 1 else "all"

# ---------------- IFVG ----------------
if which in ("all", "ifvg"):
    for rr, slm in [(1.0, 1.5), (1.5, 1.5), (2.0, 1.5), (1.0, 1.0)]:
        for ref_mode in (0, 1):   # 0 = IFVG line, 1 = confirmation close
            sig = en.ifvg_signals(o, h, l, c, cx.atr, 0.25, 0.50, 0.65, 0.05, 2, 500, 500, ref_mode, slm, rr, 20, True, False, 1.5, 50)
            s, ref, line, zt, zb, risk, gv, gr, gp = sig
            gate = gv & gr & gp
            for (ws, we, wname) in [(570, 930, "NY"), (0, 1440, "24h")]:
                modes = (0, 2) if ref_mode == 0 else (0, 1)
                for mode in modes:
                    res = en.sim_ifvg(o, h, l, c, om, dayid, s, ref, risk, gate, rr, mode, ws, we, 955, 15, True, 0.0, 0.0)
                    record("IFVG", f"rr{rr} sl{slm} ref={'line' if ref_mode == 0 else 'close'} {wname} mode={['pine', 'market', 'limit'][mode]}", res)
    print("ifvg done", round(time.time() - t0, 1))

# ---------------- ORB ----------------
if which in ("all", "orb"):
    for or_len, mode, stop_mode, rr in itertools.product((5, 15, 30), (0, 1), (0, 3), (1.0, 2.0, 3.0, 0.0)):
        if mode == 0 and stop_mode == 3:
            continue
        res = en.sim_orb(o, h, l, c, om, dayid, cx.open_idx, cx.atr, or_len, mode, stop_mode, 0.0, rr, 955, 720, 0.0, 0.0, cx.zero_dir, 1)
        record("ORB", f"or{or_len} {['candle-dir', 'breakout'][mode]} stop={['opp', '', '', 'mid'][stop_mode]} rr={rr if rr else 'EOD'}", res)
    print("orb done", round(time.time() - t0, 1))

# ---------------- Noise-area momentum ----------------
if which in ("all", "noise"):
    sigma = cx.sigma()
    for band, chk, hs, vw in itertools.product((1.0,), (30, 10, 1), (0.5, 1.0, 2.0), (1, 0, -1)):
        res = en.sim_noise(o, h, l, c, v, om, cx.open_idx, cx.prev_close, sigma, band, chk, 600, 930, 955, hs, vw, 0.0, cx.zero_dir)
        record("NOISE", f"band{band} chk{chk} hard{hs} vwap={['none', 'twap', 'vwap'][vw + 1]}", res)
    print("noise done", round(time.time() - t0, 1))

# ---------------- FVG time windows (Silver Bullet family) ----------------
if which in ("all", "fvg"):
    for (ws, we, wn), gap, em, sm, rr in itertools.product([(600, 660, "SB 10-11"), (570, 600, "open 9:30-10"), (840, 900, "PM 14-15")],
                                                          (0.3, 0.8), (0, 1), (0, 1), (1.0, 2.0, 3.0)):
        res = en.sim_fvg_window(o, h, l, c, om, dayid, cx.open_idx, cx.atr, ws, we, gap, em, sm, rr, 955, 20, cx.zero_dir, 1)
        record("FVGWIN", f"{wn} gap{gap} entry={['edge', 'mid'][em]} stop={['c1', 'c2'][sm]} rr{rr}", res)
    print("fvg done", round(time.time() - t0, 1))

# ---------------- Overnight sweep reversal ----------------
if which in ("all", "sweep"):
    for win_end, rr, buf, ms in itertools.product((630, 660, 720), (1.0, 1.5, 2.0, 3.0), (2,), (0, 4)):
        res = en.sim_sweep(o, h, l, c, om, dayid, cx.open_idx, win_end, rr, buf, 955, ms, cx.zero_dir)
        record("SWEEP", f"win<{win_end//60}:{win_end%60:02d} rr{rr} minsweep{ms}t", res)
    print("sweep done", round(time.time() - t0, 1))

# ---------------- Gap fade ----------------
if which in ("all", "gap"):
    atr_day = cx.atr_daily()
    for (gmin, gmax), sm, ff, dl in itertools.product([(0.05, 0.3), (0.1, 0.5), (0.3, 1.0)], (0.5, 1.0), (0.5, 1.0), (0, 5)):
        res = en.sim_gap(o, h, l, c, om, dayid, cx.open_idx, cx.prev_close, atr_day, gmin, gmax, sm, ff, dl, 955)
        record("GAP", f"gap {gmin}-{gmax}xATRd stop{sm}xgap fill{ff} delay{dl}", res)
    print("gap done", round(time.time() - t0, 1))

out = pd.DataFrame(rows)
out.to_csv(f"scan_{which}.csv", index=False)
print(out.to_string(index=False))
