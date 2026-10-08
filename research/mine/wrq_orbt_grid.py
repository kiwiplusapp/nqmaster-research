"""wrq_orbt_grid: plateau of the ORB trigger-vs-prior-close rule (ORBt) per threshold, ORB60 / ORB90 (Ultra exits), per period."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
from wrq_port import module_trades
from wrq_combo import k_trig
from wrq_lib import stats, SLIP
if __name__ == "__main__":
    rows = []
    for mod, rm in (("ORB60", 60), ("ORB90", 90)):
        for per, slip in (("IS", SLIP), ("C24", SLIP), ("REAL", SLIP), ("L15", SLIP), ("REAL+4", SLIP * 5)):
            for thr in (None, -0.3, -0.2, -0.1, 0.0, 0.05, 0.1, 0.15, 0.2, 0.3):
                T = module_trades(per.replace("+4", ""), mod, {}, slip, None if thr is None else k_trig(thr, rm))
                s = stats(T.u); s.update(mod=mod, per=per, thr="base" if thr is None else thr); rows.append(s)
    R = pd.DataFrame(rows); R.to_csv("wrq_orbt_grid.csv", index=False)
    R["s"] = R.apply(lambda r: f"{r.n:d} {r.wr:.1f} {r.pf:.2f}", axis=1); pd.set_option("display.width", 250)
    print(R.pivot_table(index=["mod", "thr"], columns="per", values="s", aggfunc="first", sort=False)[["IS", "C24", "REAL", "L15", "REAL+4"]].to_string())
