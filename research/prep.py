"""Convert the raw UTC minute bars into ET-indexed numpy arrays used by the research engine.

Bar timestamps are bar OPEN times (Dukascopy convention). `om` = ET minute-of-day of the bar open.
Trading day follows CME Globex: bars from 18:00 ET belong to the next calendar day's session.
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))


def build(src="nq_1m_utc.pkl", dst="nq_1m.npz"):
    df = pd.read_pickle(os.path.join(ROOT, "data", src))
    et = df["time_utc"].dt.tz_convert("America/New_York")
    om = (et.dt.hour * 60 + et.dt.minute).to_numpy().astype(np.int32)
    session_date = (et + pd.Timedelta(hours=6)).dt.strftime("%Y%m%d").astype(np.int32).to_numpy()
    dow = (et + pd.Timedelta(hours=6)).dt.dayofweek.to_numpy().astype(np.int32)

    # Drop the CME daily maintenance hour and any weekend fragments.
    keep = ~((om >= 17 * 60) & (om < 18 * 60)) & (dow < 5)
    df = df[keep].reset_index(drop=True)
    om, session_date, dow = om[keep], session_date[keep], dow[keep]

    uniq, dayid = np.unique(session_date, return_inverse=True)
    out = dict(
        o=df["open"].to_numpy(np.float64),
        h=df["high"].to_numpy(np.float64),
        l=df["low"].to_numpy(np.float64),
        c=df["close"].to_numpy(np.float64),
        v=df["volume"].to_numpy(np.float64),
        om=om,
        dayid=dayid.astype(np.int32),
        date=session_date,
        dates=uniq.astype(np.int32),
        dow=dow,
        epoch=(df["time_utc"].dt.tz_convert(None).astype("datetime64[s]").astype("int64") // 60).to_numpy(np.int64),
    )
    np.savez(os.path.join(ROOT, "data", dst), **out)
    print("bars", len(out["c"]), "days", len(uniq), uniq[0], "->", uniq[-1])


def load(name=None):
    name = name or os.environ.get("NQ_DATA", "nq_1m.npz")
    z = np.load(os.path.join(ROOT, "data", name))
    return {k: z[k] for k in z.files}


if __name__ == "__main__":
    build()
