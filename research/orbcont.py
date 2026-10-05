"""ORB-day continuation: on pullback days where ORB60 has entered, take momentum-sequence pullback entries (5m) in the ORB
direction after the ORB entry. Shorts via mirrored prices. Output trades per config."""
import os, sys, itertools, pickle, numpy as np, pandas as pd
tag = sys.argv[1]; os.environ["NQ_DATA"] = tag + ".npz"
import wr60
V = pickle.load(open("VV_plus2.pkl", "rb"))[tag]
o = V[(V["mod"] == "ORB60") & (V["var"] == 0.6)]
od = o.groupby("date").agg(d=("d", "first"), tin=("tin", "min"))
od["om"] = (od.tin + 1080) % 1440
res = {}
for tf in (5, 3):
    B = wr60.build(tf)
    dd = pd.Series(B["date"]).map(od.d).to_numpy(); tom = pd.Series(B["date"]).map(od.om).to_numpy()
    after = B["om"] >= np.nan_to_num(tom, nan=9999)
    for side in (1, -1):
        allow = (dd == side) & after
        if side == 1: o_, h_, l_, c_ = B["o"], B["h"], B["l"], B["c"]
        else: o_, h_, l_, c_ = -B["o"], -B["l"], -B["h"], -B["c"]
        for N, R, sk, we in itertools.product((3, 4, 5), (0.5, 0.75, 1.0), (1.25, 1.75), (870, 945)):
            out = np.zeros((len(c_) // 3, 4))
            k = wr60.sim(o_, h_, l_, c_, B["om"], B["day"], allow, N, R, sk, 0.0, 0, 630, we, 955, 0.0, out)
            ei = out[:k, 1].astype(int); xi = out[:k, 3].astype(int)
            res[(tf, side, N, R, sk, we)] = pd.DataFrame(dict(date=B["date"][ei], usd=out[:k, 0] * 2 - 1.9, tin=B["om"][ei], tout=B["om"][xi] + tf, d=side))
pickle.dump(res, open(f"orbcont_{tag}.pkl", "wb")); print("done", len(res))
