import numpy as np
from acct_life import CFG
from acct_lab import Z, dense_key
def exits(per, cfg):
    z = Z(per); n = len(z["days"]); out = np.zeros(n)
    for m in CFG[cfg]:
        R = z[dense_key(per, m) + "|R"]          # a missing key raises KeyError (was skipped silently); ch = (np.abs(np.diff(R, axis=1)) > 1e-6).sum(1); out += ch * (2.0 if m.startswith("G:") else 1.0)
    return out
