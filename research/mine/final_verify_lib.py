import numpy as np
from acct_life import CFG
from acct_lab import Z
def exits(per, cfg):
    z = Z(per); n = len(z["days"]); out = np.zeros(n)
    for m in CFG[cfg]:
        if m + "|R" not in z.files: continue
        R = z[m + "|R"]; ch = (np.abs(np.diff(R, axis=1)) > 1e-6).sum(1); out += ch * (2.0 if m.startswith("G:") else 1.0)
    return out
