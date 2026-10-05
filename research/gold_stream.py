import os, numpy as np, pandas as pd
from common import Ctx
import nt_v3_replica as r3
cx = Ctx()
out = {}
for t1 in (1.0, 2.0):
    df = r3.run(cx, contracts=1, t1_frac=1.0, max_consec_losses=0, dll=0, orb_cap=0.35, vw_stop=0.35, t1_r=t1, use_vwap=False, range_min=30)
    df["usd_mgc"] = ((df.usd + 1) / 2) * 4.0 - 1.0
    out[t1] = df.groupby("date").usd_mgc.sum()
pd.to_pickle(out, f"gold_orb30_{os.environ['NQ_DATA'].split('.')[0]}.pkl"); print("ok")
