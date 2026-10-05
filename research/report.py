"""Helpers to print a full report (yearly table, IS/OOS, $ sizing, prop-firm pass study) for one trade list."""
import numpy as np
import pandas as pd
import evalkit as ev
import propsim
from common import SPLIT


def full_report(name, df, cx, risks=(100, 150, 200, 250), max_losses=3, daily_stop_r=3.0, daily_target_r=0.0):
    print("=" * 110)
    print(name)
    print("-" * 110)
    ins = df[df.date < SPLIT]; oos = df[df.date >= SPLIT]
    print("IS  (2020-2023):", ev.stats(ins, cx.rth_days[cx.rth_days < SPLIT]))
    print("OOS (2024-2026):", ev.stats(oos, cx.rth_days[cx.rth_days >= SPLIT]))
    print(ev.by_year(df).to_string())
    sized = ev.size_dollars(df, 100)
    print(f"sizeable at $100 risk: {len(sized)}/{len(df)} trades, avg qty {sized.qty.mean():.2f}, avg stop {df.risk.mean():.1f} pts")
    t = propsim.risk_table(df, cx.rth_days, risks=risks, max_losses=max_losses, daily_stop_r=daily_stop_r, daily_target_r=daily_target_r)
    print(t.to_string(index=False))
    return t
