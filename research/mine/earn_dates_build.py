"""2026-10-21 Build the event date lists for earn_lab.py (mega-cap earnings + Nasdaq-100 index events) -> research/news_dates_earn_<ticker>.csv,
research/news_dates_ndx_rebal.csv.
EARNINGS: SEC EDGAR full-text search (efts.sec.gov/LATEST/search-index, JSON) for 8-K filings with Item 2.02 'Results of Operations and
Financial Condition' per company CIK, 2009-01..2026-12. The 8-K 'period_ending' (date of the reported event = press-release date) is used,
not the filing date (filings accepted after 17:30 ET get the next business day's filing date). All nine companies release AFTER the close,
so date = the trading day of the release; the NQ reaction is the next session's overnight gap (18:00 -> 09:30), checked in earn_lab.py.
Non-earnings 2.02 filings (preliminary results, guidance cuts, re-casts, TSLA delivery reports 2013-22 carry item 7.01, 2023+ fall on day 1-3
of Jan/Apr/Jul/Oct and are removed by the quarter rule) are removed: TSLA 7.01 rows and day 1-3 of Jan/Apr/Jul/Oct dropped, then at most one date per calendar quarter: when a quarter has several 2.02 filings
the LAST of those within 12 days of the ticker's median day-of-quarter (from quarters with one filing) is kept, else the nearest; dropped rows are
listed in the 'note' column of the first row. Verified by hand: NVDA 2019-01-28 pre-announcement -> 02-14 kept, NVDA 2022-08-08 -> 08-24,
NFLX 2019-12-16 recast dropped, TSLA deliveries dropped. CIK history: GOOGL = Google Inc (1288776) to
2015-09 then Alphabet (1652044); AVGO = Avago Technologies (1441634) to 2016-01, Broadcom Ltd (1649338) 2016-02..2018-03, Broadcom Inc
(1730168) since 2018-04; META = Facebook/Meta (1326801, IPO 2012-05); TSLA (1318605, IPO 2010-06).
INDEX EVENTS (rule-based, Nasdaq methodology): quarterly NDX rebalance = executed at the close of the third Friday of Mar/Jun/Sep/Dec
(effective the next Monday) = quad-witching day (index options/futures expiry); annual reconstitution = December third Friday (same day,
announced ~Dec 10); special rebalances executed at the close of 2011-04-29 and 2023-07-21. Columns: date, kind (Q/A/S), note.
Raw EDGAR JSON is cached in the scratchpad (dl/edgar). Run: cd research/mine && python3 earn_dates_build.py"""
import os, sys, json, subprocess, datetime as dt, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DL = "/tmp/claude-0/-home-user-nqmaster-research/176a42ca-c215-52e2-84dc-57e214e477d4/scratchpad/dl/edgar"
UA = "NQMaster research leonel.sch2003@gmail.com"
TODAY = dt.date.today().strftime("%Y-%m-%d")
CIKS = {"NVDA": ["0001045810"], "AAPL": ["0000320193"], "MSFT": ["0000789019"], "AMZN": ["0001018724"], "GOOGL": ["0001288776", "0001652044"],
        "META": ["0001326801"], "TSLA": ["0001318605"], "AVGO": ["0001441634", "0001649338", "0001730168"], "NFLX": ["0001065280"]}


def fetch(cik, start="2009-01-01", end="2026-12-31"):
    os.makedirs(DL, exist_ok=True); hits = []; frm = 0
    while True:
        fn = os.path.join(DL, f"{cik}_{frm}.json")
        if not os.path.exists(fn):
            url = (f"https://efts.sec.gov/LATEST/search-index?q=%222.02%22&forms=8-K&ciks={cik}&dateRange=custom&startdt={start}&enddt={end}&from={frm}")
            subprocess.run(["curl", "-sS", "-m", "60", "-A", UA, url, "-o", fn], check=True)
        d = json.load(open(fn)); h = d["hits"]["hits"]; hits += h
        tot = d["hits"]["total"]["value"]
        if not h or len(hits) >= tot: break
        frm += len(h)
    rows = {}
    for x in hits:
        s = x["_source"]
        if "2.02" not in s.get("items", []): continue
        rows[s["adsh"]] = dict(date=s["period_ending"], file_date=s["file_date"], items=" ".join(s.get("items", [])), adsh=s["adsh"])
    return pd.DataFrame(list(rows.values()))


def build_earnings():
    summary = {}
    for tk, ciks in CIKS.items():
        df = pd.concat([fetch(c) for c in ciks], ignore_index=True).drop_duplicates("date").sort_values("date").reset_index(drop=True)
        df["ts"] = pd.to_datetime(df.date); notes = []
        # an 8-K that bundles other items can carry an earlier period_ending (TSLA 2023-01-20 credit agreement, release 01-25): when the
        # filing date is 2+ business days after period_ending, the release day is the filing day (same-day after-close filing)
        bd = np.busday_count(df.ts.to_numpy().astype("datetime64[D]"), pd.to_datetime(df.file_date).to_numpy().astype("datetime64[D]"))
        for j in np.nonzero(bd >= 2)[0]:
            notes.append(f"period_ending {df.date[j]} filed {df.file_date[j]} ({bd[j]} bdays later, items {df['items'][j]}): date := file_date")
            df.loc[j, "date"] = df.file_date[j]; df.loc[j, "ts"] = pd.to_datetime(df.file_date[j])
        if tk == "TSLA":
            bad = df["items"].str.contains("7.01") | ((df.ts.dt.day <= 3) & df.ts.dt.month.isin([1, 4, 7, 10]))
            notes += [f"TSLA deliveries/7.01 dropped: {r.date} items {r[3]}" for r in df[bad].itertuples()]; df = df[~bad].reset_index(drop=True)
        df["q"] = df.ts.dt.year * 10 + df.ts.dt.quarter; df["doq"] = (df.ts - df.ts.dt.to_period("Q").dt.start_time).dt.days
        cnt = df.q.map(df.q.value_counts()); med = df[cnt == 1].groupby(df.ts.dt.quarter[cnt == 1]).doq.median()
        keep = []
        for q, g in df.groupby("q"):
            if len(g) == 1: keep.append(g.index[0]); continue
            m = med.get(int(q % 10), g.doq.median()); near = g[(g.doq - m).abs() <= 12]
            best = near.index[-1] if len(near) else (g.doq - m).abs().idxmin(); keep.append(best)      # several near the usual day: the LAST (a pre-announcement precedes the report)
            notes += [f"quarter {q}: dropped {r.date} items {r[3]} (kept {df.date[best]})" for r in g.drop(best).itertuples()]
        out = df.loc[keep, ["date", "file_date", "items", "adsh"]].copy()
        out["date"] = out.date.str.replace("-", "").astype(int); out["file_date"] = out.file_date.str.replace("-", "")
        out["source"] = "SEC EDGAR FTS 8-K item 2.02 period_ending"; out["fetched"] = TODAY
        out["note"] = ""
        if notes: out.loc[out.index[0], "note"] = " | ".join(notes)
        out.to_csv(os.path.join(ROOT, f"news_dates_earn_{tk.lower()}.csv"), index=False)
        yrs = out.date // 10000; per = yrs.value_counts().sort_index()
        summary[tk] = dict(n=int(len(out)), first=int(out.date.min()), last=int(out.date.max()), dropped=len(notes),
                           years_not_4={int(y): int(c) for y, c in per.items() if c != 4 and 2010 <= y <= 2025})
        print(tk, summary[tk], flush=True)
    return summary


def third_friday(y, m):
    d = dt.date(y, m, 15)
    while d.weekday() != 4: d += dt.timedelta(days=1)
    return d


def build_index():
    rows = []
    for y in range(2010, 2027):
        for m in (3, 6, 9, 12):
            d = third_friday(y, m)
            if d > dt.date(2026, 12, 31): continue
            rows.append(dict(date=int(d.strftime("%Y%m%d")), kind="A" if m == 12 else "Q",
                             note="annual reconstitution + quarterly rebalance + quad witching (close)" if m == 12 else "quarterly rebalance + quad witching (close)"))
    rows += [dict(date=20110429, kind="S", note="special rebalance AAPL weight cap (effective 2011-05-02)"),
             dict(date=20230721, kind="S", note="special rebalance magnificent-7 concentration (effective 2023-07-24)")]
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True); df["source"] = "Nasdaq-100 methodology rule (3rd Friday Mar/Jun/Sep/Dec) + announced specials"; df["fetched"] = TODAY
    df.to_csv(os.path.join(ROOT, "news_dates_ndx_rebal.csv"), index=False); print("ndx_rebal", len(df)); return len(df)


if __name__ == "__main__":
    s = build_earnings(); n = build_index()
    json.dump(dict(earnings=s, ndx_rebal=n), open(os.path.join(HERE, "earn_dates_summary.json"), "w"), indent=1)
