import numpy as np, pandas as pd
from wr60 import build, sim
B = build(5)
out = np.zeros((len(B["c"]) // 3, 4))
k = sim(B["o"], B["h"], B["l"], B["c"], B["om"], B["day"], B["up20"], 5, 0.5, 1.75, 0.0, 0, 630, 945, 955, 0.0, out)
o = out[:k]
df = pd.DataFrame(dict(pts=o[:, 0], date=B["date"][o[:, 1].astype(int)], t_in=B["om"][o[:, 1].astype(int)], t_out=B["om"][o[:, 3].astype(int)] + 5))
df["usd"] = df.pts * 2.0 - 1.0
print(len(df), df.usd.sum()); df.to_pickle("mseq_times.pkl")
