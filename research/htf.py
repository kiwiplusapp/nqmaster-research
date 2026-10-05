"""IFVG / Sweep+IFVG on 5- and 15-minute bars built from the 1-minute data (real fills)."""
import itertools, numpy as np, pandas as pd
import engine as en
from common import Ctx

pd.set_option("display.width", 260); pd.set_option("display.max_rows", 300)


def resample(cx, tf):
    o, h, l, c, v, om, dayid, date = cx.o, cx.h, cx.l, cx.c, cx.v, cx.om, cx.dayid, cx.date
    key = dayid.astype(np.int64) * 10000 + (om // tf)
    brk = np.r_[0, np.where(np.diff(key) != 0)[0] + 1]
    end = np.r_[brk[1:], len(c)]
    R = dict(o=o[brk], c=c[end - 1], h=np.maximum.reduceat(h, brk), l=np.minimum.reduceat(l, brk),
             v=np.add.reduceat(v, brk), om=(om[brk] // tf) * tf, dayid=dayid[brk], date=date[brk])
    return R


def atr(h, l, c, n=14):
    return en.atr_nt(h, l, c, n)


def run(tf):
    cx = Ctx()
    R = resample(cx, tf)
    o, h, l, c, v, om, dayid, date = (R[k] for k in ("o", "h", "l", "c", "v", "om", "dayid", "date"))
    a = atr(h, l, c)
    nd = cx.nd
    open_idx = np.full(nd, -1, np.int64); w = np.where(om == 570)[0]; open_idx[dayid[w]] = w
    L = np.load("data/levels.npy")
    rows = []

    def rec(name, res):
        E, X, D, EP, XP, RK, RS = res
        if len(E) < 30:
            return
        pnl = (XP - EP) * D; Rr = (pnl - 0.5) / RK; dt = date[E]
        def st(m):
            r = Rr[m]
            if len(r) == 0:
                return (0, np.nan, np.nan)
            ls = -r[r <= 0].sum()
            return (len(r), round((r > 0).mean() * 100, 1), round(r[r > 0].sum() / ls, 2) if ls > 0 else np.nan)
        a1 = st(dt < 20240101); b1 = st((dt >= 20240101) & (dt < 20260101)); y1 = st(dt >= 20260101)
        rows.append(dict(tf=tf, cfg=name, n_2020_23=a1[0], wr_2020_23=a1[1], pf_2020_23=a1[2], n_2024_25=b1[0], wr_2024_25=b1[1],
                         pf_2024_25=b1[2], n_2026=y1[0], wr_2026=y1[1], pf_2026=y1[2], stop=round(RK.mean(), 1)))

    for rr, slm, (ws, we, wn) in itertools.product((1.0, 2.0), (1.0, 1.5), [(570, 930, "NY"), (570, 690, "NY-AM")]):
        for ref_mode in (0, 1):
            s, ref, line, zt, zb, risk, gv, gr, gp = en.ifvg_signals(o, h, l, c, a, 0.25, 0.5, 0.65, 0.05, 2, 500, 500, ref_mode, slm, rr, 20, True, False, 1.5, 50)
            gate = gv & gr & gp
            for mode in ((0, 2) if ref_mode == 0 else (0, 1)):
                res = en.sim_ifvg(o, h, l, c, om, dayid, s, ref, risk, gate, rr, mode, ws, we, 955, max(2, 15 // (tf // 1)), True, 0.0, 0.0)
                rec(f"PineIFVG {['TV-fill','market','limit'][mode]} {'line' if ref_mode==0 else 'close'} {wn} sl{slm} 1:{rr:g}", res)
    MK = {"PD+ON": np.array([1, 1, 1, 1, 0, 0, 0, 0], np.bool_), "all": np.ones(8, np.bool_)}
    for (mn, mk), em, rr, (ws, we), sm in itertools.product(MK.items(), (0, 1), (1.0, 2.0), [(570, 660), (570, 720)], (0, 1)):
        res = en.sim_sweep_ifvg(o, h, l, c, om, dayid, open_idx, L, mk, a, ws, we, 955, max(3, 30 // tf), max(3, 20 // tf) + 2, 0.0, 0.5,
                                em, max(2, 15 // tf) + 1, sm, 4 if sm == 0 else 2, rr, 120.0, 0.0, 2, 0.0)
        rec(f"SweepIFVG {mn} {['mkt','retest'][em]} {['sweepStop','barStop'][sm]} {ws}-{we} 1:{rr:g}", res)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    out = pd.concat([run(5), run(15)])
    out.to_csv("htf_scan.csv", index=False)
    real = out[~out.cfg.str.contains("TV-fill")]
    tv = out[out.cfg.str.contains("TV-fill")]
    print("TV-fill (not executable): median WR 2026", tv.wr_2026.median(), "max", tv.wr_2026.max())
    print("REAL: configs", len(real), "| PF>1 in all three periods:", int(((real.pf_2020_23 > 1) & (real.pf_2024_25 > 1) & (real.pf_2026 > 1)).sum()),
          "| WR>=60 & PF>1 in 2026:", int(((real.wr_2026 >= 60) & (real.pf_2026 > 1)).sum()))
    print(real.sort_values("pf_2020_23", ascending=False).head(30).to_string(index=False))
