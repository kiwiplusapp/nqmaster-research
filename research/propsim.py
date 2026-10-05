"""Prop-firm evaluation study for a finished trade list: pass rate vs. risk per trade."""
import numpy as np
import pandas as pd
import evalkit as ev


def risk_table(df_pts, all_dates, risks=(100, 150, 200, 250, 300), target=3000.0, max_dd=2000.0,
               max_losses=3, daily_stop_r=3.0, daily_target_r=0.0, max_qty=15):
    rows = []
    for r in risks:
        sized = ev.size_dollars(df_pts, risk_usd=r, max_qty=max_qty)
        sized = ev.apply_daily_rules(sized, max_losses=max_losses, daily_stop=daily_stop_r * r,
                                     daily_target=daily_target_r * r if daily_target_r else 0.0)
        s = ev.stats(sized, all_dates, col="usd")
        p = ev.prop_eval(sized, all_dates, target=target, max_dd=max_dd)
        rows.append(dict(risk=r, trades=s["n"], net_usd=round(s["total"], 0), maxdd_usd=round(s["maxdd"], 0),
                         sharpe=s["sharpe"], pass_pct=p["pass_rate"], days_to_pass=p["median_days_pass"],
                         days_to_fail=p["median_days_fail"], consistency_ok=p["consistency_ok"]))
    return pd.DataFrame(rows)
