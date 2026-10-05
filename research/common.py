"""Shared data loading and per-day helpers for the research scripts."""
import numpy as np
from prep import load
import engine as en

SPLIT = 20240101   # in-sample < SPLIT <= out-of-sample


class Ctx:
    def __init__(self):
        d = load()
        self.d = d
        self.o, self.h, self.l, self.c, self.v = d["o"], d["h"], d["l"], d["c"], d["v"]
        self.om, self.dayid, self.date = d["om"], d["dayid"], d["date"]
        self.dates = d["dates"]
        nd = len(self.dates)
        self.nd = nd
        self.atr = en.atr_nt(self.h, self.l, self.c, 14)

        self.open_idx = np.full(nd, -1, np.int64)
        self.close_idx = np.full(nd, -1, np.int64)
        i570 = np.where(self.om == 570)[0]
        self.open_idx[self.dayid[i570]] = i570
        i959 = np.where(self.om == 959)[0]
        self.close_idx[self.dayid[i959]] = i959

        self.prev_close = np.full(nd, np.nan)
        for dd in range(1, nd):
            if self.close_idx[dd - 1] >= 0:
                self.prev_close[dd] = self.c[self.close_idx[dd - 1]]

        self.rth_days = self.dates[self.open_idx >= 0]
        self.zero_dir = np.zeros(nd, np.int64)
        self._sigma = None

    def atr_daily(self, n=14):
        """Wilder ATR of RTH daily bars, known at the open (uses prior days only)."""
        nd = self.nd
        hi = np.full(nd, np.nan); lo = np.full(nd, np.nan); cl = np.full(nd, np.nan)
        for dd in range(nd):
            i0, i1 = self.open_idx[dd], self.close_idx[dd]
            if i0 >= 0 and i1 > i0:
                hi[dd] = self.h[i0:i1 + 1].max(); lo[dd] = self.l[i0:i1 + 1].min(); cl[dd] = self.c[i1]
        out = np.full(nd, np.nan)
        a = np.nan; prev_c = np.nan; cnt = 0
        for dd in range(nd):
            out[dd] = a      # value available at today's open
            if np.isnan(hi[dd]):
                continue
            tr = hi[dd] - lo[dd] if np.isnan(prev_c) else max(hi[dd] - lo[dd], abs(hi[dd] - prev_c), abs(lo[dd] - prev_c))
            cnt += 1
            k = min(cnt, n)
            a = tr if np.isnan(a) else ((k - 1) * a + tr) / k
            prev_c = cl[dd]
        return out

    def sigma(self, lookback=14):
        if self._sigma is not None:
            return self._sigma
        nd = self.nd
        moves = np.full((nd, 390), np.nan)
        for dd in range(nd):
            i0 = self.open_idx[dd]
            if i0 < 0:
                continue
            seg = np.arange(i0, min(i0 + 390, len(self.c)))
            ok = self.om[seg] == 570 + (seg - i0)
            k = (seg - i0)[ok]
            moves[dd, k] = np.abs(self.c[seg[ok]] / self.o[i0] - 1.0)
        sig = np.full((nd, 390), np.nan)
        valid_days = np.where(self.open_idx >= 0)[0]
        for pos, dd in enumerate(valid_days):
            if pos < lookback:
                continue
            prev = valid_days[pos - lookback:pos]
            sig[dd] = np.nanmean(moves[prev], axis=0)
        self._sigma = sig
        return sig
