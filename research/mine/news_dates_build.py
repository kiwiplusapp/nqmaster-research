"""2026-10-19 Build the scheduled macro-release date lists 2009-2027 used by news_fade.py -> research/news_dates_<type>.csv
(columns date, time_et, source). Sources (fetched 2026-10-19):
  PPI      : BLS news-release archive https://www.bls.gov/bls/news-release/ppi.htm (archive filenames MMDDYYYY), 08:30 ET.
  JOLTS    : BLS archive https://www.bls.gov/bls/news-release/jolts.htm, 10:00 ET.
  GDP      : BEA archive https://apps.bea.gov/newsreleases/relsarchivegdp.htm (2009-2017) + https://www.bea.gov/news/archive?field_related_product_target_id=451 (2018-26), 08:30.
  PCE      : BEA Personal Income and Outlays, relsarchivepi.htm (2009-17) + archive product 476 (2018-26), 08:30.
  RETAIL   : Census Advance Monthly Retail PDFs www2.census.gov/retail/releases/historical/marts/advYYMM.pdf ('scheduled to be released <date>' chain, 2010-19)
             + Census economic-indicator calendars calendar-listview-<year>.html (2020-26), 08:30.
  DURABLES : Census M3 advance PDFs manufacturing/m3/historical_data/pressreleases/prel/<year>/<mon>YYprel.pdf (chain, 2010-19) + calendars 2020-26, 08:30.
  CLAIMS   : DOL weekly claims rule: every Thursday 08:30, Wednesday when Thursday is a federal holiday (Thanksgiving, Jul 4, Dec 25, Jan 1).
  ISM_MFG  : first business day of the month 10:00; ISM_SERV: third business day 10:00 (ISM rule; federal holidays skipped).
  CB_CONF  : Conference Board consumer confidence, last Tuesday of the month 10:00 (rule).
  UMICH_P  : Michigan sentiment preliminary, 2nd Friday 10:00; UMICH_F final, 4th Friday 10:00 (rule; Good Friday -> Thursday).
  FOMC_MIN : FOMC minutes = decision day + 21 days, 14:00 (news.NEWS FOMC + db_long.FOMC_1019).
  Treasury auctions: NOT built (TreasuryDirect search API returns 400/500; 'auctioned' endpoint caps at 250 records).
Rule-based lists are only approximations: the 08:30/10:00 spike check in news_fade.py decides whether they are usable."""
import os, re, sys, glob, subprocess, datetime as dt, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
DL = "/tmp/claude-0/-home-user-nqmaster-research/176a42ca-c215-52e2-84dc-57e214e477d4/scratchpad/dl"
OUT = os.path.join(ROOT, "news_dates_{}.csv")

PPI = """10152026 09102026 08132026 07152026 06112026 05132026 04142026 03182026 02272026 01302026 01142026 11252025 09102025 08142025 07162025
06122025 05152025 04112025 03132025 02132025 01142025 12122024 11142024 10112024 09122024 08132024 07122024 06132024 05142024 04112024 03142024
02162024 01122024 12132023 11152023 10112023 09142023 08112023 07132023 06142023 05112023 04132023 03152023 02162023 01182023 12092022 11152022
10122022 09142022 08112022 07142022 06142022 05122022 04132022 03152022 02152022 01132022 12142021 11092021 10142021 09102021 08122021 07142021
06152021 05132021 04092021 03122021 02172021 01152021 12112020 11132020 10142020 09102020 08112020 07102020 06112020 05132020 04092020 03122020
02192020 01152020 12122019 11142019 10082019 09112019 08092019 07122019 06112019 05092019 04112019 03132019 02142019 01152019 12112018 11092018
10102018 09122018 08092018 07112018 06132018 05092018 04102018 03142018 02152018 01112018 12122017 11142017 10122017 09132017 08102017 07132017
06132017 05112017 04132017 03142017 02142017 01132017 12142016 11162016 10142016 09152016 08122016 07142016 06152016 05132016 04132016 03152016
02172016 01152016 12112015 11132015 10142015 09112015 08142015 07152015 06122015 05142015 04142015 03132015 02182015 01152015 12122014 11182014
10152014 09162014 08152014 07162014 06132014 05142014 04112014 03142014 02192014 01152014 12132013 11212013 10292013 09132013 08142013 07122013
06142013 05152013 04122013 03142013 02202013 01152013 12132012 11142012 10122012 09132012 08142012 07132012 06132012 05112012 04122012 03152012
02162012 01182012 12152011 11152011 10182011 09142011 08172011 07142011 06142011 05122011 04142011 03162011 02162011 01132011 12142010 11162010
10142010 09162010 08172010 07152010 06162010 05182010 04222010 03172010 02182010 01202010 12152009 11172009 10202009 09152009 08182009 07142009
06162009 05142009 04142009 03172009 02192009 01152009""".split()
JOLTS = """09292026 09012026 08042026 06302026 06022026 05052026 03312026 03132026 02052026 01072026 12092025 09302025 09032025 07292025 07012025
06032025 04292025 04012025 03112025 02042025 01072025 12032024 10292024 10012024 09042024 07302024 07022024 06042024 05012024 04022024 03062024
01302024 01032024 12052023 11012023 10032023 08292023 08012023 07062023 05312023 05022023 04042023 03082023 02012023 01042023 11302022 11012022
10042022 08302022 08022022 07062022 06012022 05032022 03292022 03092022 02012022 01042022 12082021 11122021 10122021 09082021 08092021 07072021
06082021 05112021 04062021 03112021 02092021 01122021 12092020 11102020 10062020 09092020 08102020 07072020 06092020 05152020 04072020 03172020
02112020 01172020 12172019 11052019 10092019 09102019 08062019 07092019 06102019 05072019 04092019 03152019 02122019 01082019 12102018 11062018
10162018 09112018 08072018 07102018 06052018 05082018 04132018 03162018 02062018 01092018 12112017 11072017 10112017 09122017 08082017 07112017
06062017 05092017 04112017 03162017 02072017 01102017 12072016 11082016 10122016 09072016 08102016 07122016 06082016 05102016 04052016 03172016
02092016 01122016 12082015 11122015 10162015 09092015 08122015 07072015 06092015 05122015 04072015 03102015 02102015 01132015 12092014 11132014
10072014 09092014 08122014 07082014 06102014 05092014 04082014 03112014 02112014 01172014 12102013 11222013 10242013 09102013 08062013 07092013
06112013 05072013 04092013 03122013 02122013 01102013 12112012 11062012 10102012 09112012 08072012 07102012 06192012 05082012 04102012 03132012
02072012 01102012 12132011 11082011 10122011 09072011 08102011 07122011 06072011 05112011 04132011 03112011 02082011 01112011 12072010 11092010
10072010 09082010 08112010 07132010 06082010 05112010 04062010 03092010 02092010 01122010 12082009 11102009 10092009 09092009 08122009 07072009
06092009 05122009 04072009 03102009 02102009 01132009""".split()
GDP_0917 = """2017-11-29 2017-10-27 2017-09-28 2017-08-30 2017-07-28 2017-06-29 2017-05-26 2017-04-28 2017-03-30 2017-02-28 2017-01-27 2016-12-22 2016-11-29
2016-10-28 2016-09-29 2016-08-26 2016-07-29 2016-06-28 2016-05-27 2016-04-28 2016-03-25 2016-02-26 2016-01-29 2015-12-22 2015-11-24 2015-10-29 2015-09-25
2015-08-27 2015-07-30 2015-06-24 2015-05-29 2015-04-29 2015-03-27 2015-02-27 2015-01-30 2014-12-23 2014-11-25 2014-10-30 2014-09-26 2014-08-28 2014-07-30
2014-06-25 2014-05-29 2014-04-30 2014-03-27 2014-02-28 2014-01-30 2013-12-20 2013-12-05 2013-11-07 2013-09-26 2013-08-29 2013-07-31 2013-06-26 2013-05-30
2013-04-26 2013-03-28 2013-02-28 2013-01-30 2012-12-20 2012-11-29 2012-10-26 2012-09-27 2012-08-29 2012-07-27 2012-06-28 2012-05-31 2012-04-27 2012-03-29
2012-02-29 2012-01-27 2011-12-22 2011-11-22 2011-10-27 2011-09-29 2011-08-26 2011-07-29 2011-06-24 2011-05-26 2011-04-28 2011-03-25 2011-02-25 2011-01-28
2010-12-22 2010-11-23 2010-10-29 2010-09-30 2010-08-27 2010-07-30 2010-06-25 2010-05-27 2010-04-30 2010-03-26 2010-02-26 2010-01-29 2009-12-22 2009-11-24
2009-10-29 2009-09-30 2009-08-27 2009-07-31 2009-06-25 2009-05-29 2009-04-29""".split()
PCE_0917 = """2017-11-30 2017-10-30 2017-09-29 2017-08-31 2017-08-01 2017-06-30 2017-05-30 2017-05-01 2017-03-31 2017-03-01 2017-01-30 2016-12-22 2016-11-30
2016-10-31 2016-09-30 2016-08-29 2016-08-02 2016-06-29 2016-05-31 2016-04-29 2016-03-28 2016-02-26 2016-02-01 2015-12-23 2015-11-25 2015-10-30 2015-09-28
2015-08-28 2015-08-03 2015-06-25 2015-06-01 2015-04-30 2015-03-30 2015-03-02 2015-02-02 2014-12-23 2014-11-26 2014-10-31 2014-09-29 2014-08-29 2014-08-01
2014-06-26 2014-05-30 2014-05-01 2014-03-28 2014-03-03 2014-01-31 2013-12-23 2013-12-06 2013-11-08 2013-09-27 2013-08-30 2013-08-02 2013-06-27 2013-05-31
2013-04-29 2013-03-29 2013-03-01 2013-01-31 2012-12-21 2012-11-30 2012-10-29 2012-09-28 2012-08-30 2012-07-31 2012-06-29 2012-06-01 2012-04-30 2012-03-30
2012-03-01 2012-01-30 2011-12-23 2011-11-23 2011-10-28 2011-09-30 2011-08-29 2011-08-02 2011-06-27 2011-05-27 2011-04-29 2011-03-28 2011-02-28 2011-01-31
2010-12-23 2010-11-24 2010-11-01 2010-10-01 2010-08-30 2010-08-03 2010-06-28 2010-05-28 2010-05-03 2010-03-29 2010-03-01 2010-02-01 2009-12-23 2009-11-25
2009-10-30 2009-10-01 2009-08-28 2009-08-04 2009-06-26 2009-06-01 2009-04-30 2009-03-02 2009-02-02""".split()
MON = {m: i + 1 for i, m in enumerate("January February March April May June July August September October November December".split())}


def mmddyyyy(s): return int(s[4:8] + s[0:2] + s[2:4])
def iso(s): return int(s.replace("-", ""))


def bea(pid, pat):
    out = set()
    for f in glob.glob(os.path.join(DL, f"bea_{pid}_*.html")):
        h = open(f, encoding="utf-8", errors="ignore").read()
        for m in re.finditer(r'<a href="/news/\d{4}/([^"]*)"[^>]*>([^<]*)</a>.*?<time datetime="(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})', h, re.S):
            slug, title, d, t = m.groups()
            if re.search(pat, title) and iso(d) >= 20180101: out.add((iso(d), t))
    return out


def pdf_chain(folder, pat):
    """Each Census advance PDF names the next release date -> the set of announced release dates."""
    out = set()
    for f in sorted(glob.glob(os.path.join(DL, folder, "*.pdf"))):
        try: txt = subprocess.run(["pdftotext", "-l", "2", f, "-"], capture_output=True, text=True, timeout=60).stdout
        except Exception: continue
        txt = re.sub(r"\s+", " ", txt)
        for m in re.finditer(pat, txt):
            try: out.add(int(f"{int(m.group(3)):04d}{MON[m.group(1)]:02d}{int(m.group(2)):02d}"))
            except KeyError: pass
        m2 = re.search(r"FOR RELEASE AT (\d{1,2}):(\d{2}) [AP]M E[SD]T, \w+, (\w+) (\d{1,2}), (\d{4})", txt)
        if m2 and m2.group(3) in MON: out.add(int(f"{int(m2.group(5)):04d}{MON[m2.group(3)]:02d}{int(m2.group(4)):02d}"))
    return out


def census_cal(label):
    out = set()
    for y in range(2020, 2028):
        f = os.path.join(DL, f"census_{y}.html")
        if not os.path.exists(f): continue
        h = open(f, encoding="utf-8", errors="ignore").read()
        for m in re.finditer(label + r'.*?sorttable_customkey="(\d{8})(\d{4})"', h, re.S):
            out.add((int(m.group(1)), m.group(2)[:2] + ":" + m.group(2)[2:]))
    return out


def fed_holidays(y0=2009, y1=2028):
    from pandas.tseries.holiday import USFederalHolidayCalendar
    return set(pd.Timestamp(d).date() for d in USFederalHolidayCalendar().holidays(f"{y0}-01-01", f"{y1}-12-31"))


def easter(y):
    a = y % 19; b = y // 100; c = y % 100; d = b // 4; e = b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3; h = (19 * a + b - d - g + 15) % 30
    i = c // 4; k = c % 4; l = (32 + 2 * e + 2 * i - h - k) % 7; m = (a + 11 * h + 22 * l) // 451
    return dt.date(y, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)


def d8(d): return int(d.strftime("%Y%m%d"))


def rules():
    H = fed_holidays(); R = {k: set() for k in ("CLAIMS", "ISM_MFG", "ISM_SERV", "CB_CONF", "UMICH_P", "UMICH_F")}
    d = dt.date(2009, 1, 1)
    while d <= dt.date(2027, 12, 31):
        if d.weekday() == 3: R["CLAIMS"].add(d8(d - dt.timedelta(days=1) if d in H else d))
        d += dt.timedelta(days=1)
    for y in range(2009, 2028):
        gf = easter(y) - dt.timedelta(days=2)
        for m in range(1, 13):
            bd = [x for x in (dt.date(y, m, i) for i in range(1, 29)) if x.weekday() < 5 and x not in H]
            R["ISM_MFG"].add(d8(bd[0])); R["ISM_SERV"].add(d8(bd[2]))
            last = dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)
            tue = last
            while tue.weekday() != 1: tue -= dt.timedelta(days=1)
            R["CB_CONF"].add(d8(tue))
            fr = [x for x in (dt.date(y, m, i) for i in range(1, 29)) if x.weekday() == 4]
            for key, f in (("UMICH_P", fr[1]), ("UMICH_F", fr[3])):
                R[key].add(d8(f - dt.timedelta(days=1) if f == gf else f))
    from news import NEWS
    from db_long import FOMC_1019
    fm = set()
    for x in set(NEWS["FOMC"]) | set(FOMC_1019):
        d = dt.datetime.strptime(str(x), "%Y%m%d").date() + dt.timedelta(days=21)
        fm.add(d8(d))
    R["FOMC_MIN"] = fm
    return R


if __name__ == "__main__":
    today = dt.date.today().isoformat()
    lists = {
        "PPI": ({mmddyyyy(s) for s in PPI}, "08:30", "BLS archive bls.gov/bls/news-release/ppi.htm"),
        "JOLTS": ({mmddyyyy(s) for s in JOLTS}, "10:00", "BLS archive bls.gov/bls/news-release/jolts.htm"),
    }
    g = bea(451, r"^GDP|Gross Domestic Product"); gdp = {iso(s) for s in GDP_0917} | {d for d, t in g}
    lists["GDP"] = (gdp, "08:30", "BEA relsarchivegdp.htm (2009-17) + bea.gov/news/archive product 451 (2018-26)")
    p = bea(476, r"Personal Income"); pce = {iso(s) for s in PCE_0917} | {d for d, t in p}
    lists["PCE"] = (pce, "08:30", "BEA relsarchivepi.htm (2009-17) + bea.gov/news/archive product 476 (2018-26)")
    r1 = pdf_chain("marts", r"scheduled (?:to be released|for release on) (\w+) (\d{1,2}), (\d{4})"); r2 = census_cal("Advance Monthly Sales for Retail")
    lists["RETAIL"] = (r1 | {d for d, t in r2}, "08:30", "Census MARTS advance PDFs 2009-19 (next-release chain) + calendar-listview-2020..2026")
    d1 = pdf_chain("m3", r"[Aa]dvance [Rr]eport on [Dd]urable [Gg]oods for \w+ is scheduled for release on (\w+) (\d{1,2}), (\d{4})"); d2 = census_cal("Advance Report on Durable Goods")
    lists["DURABLES"] = (d1 | {d for d, t in d2}, "08:30", "Census M3 advance PDFs 2009-19 (next-release chain) + calendar-listview-2020..2026")
    R = rules()
    for k, t in (("CLAIMS", "08:30"), ("ISM_MFG", "10:00"), ("ISM_SERV", "10:00"), ("CB_CONF", "10:00"), ("UMICH_P", "10:00"), ("UMICH_F", "10:00"), ("FOMC_MIN", "14:00")):
        lists[k] = (R[k], t, "rule (see news_dates_build.py docstring)")
    for k, (ds, t, src) in lists.items():
        ds = sorted(x for x in ds if 20090101 <= x <= 20271231)
        pd.DataFrame(dict(date=ds, time_et=t, source=src, fetched=today)).to_csv(OUT.format(k.lower()), index=False)
        print(f"{k:9s} n={len(ds):4d} {min(ds)}..{max(ds)}  per year 2010-25: {len([x for x in ds if 20100101 <= x < 20260101]) / 16:.1f}")
    print("census pdf chain retail", len(r1), "durables", len(d1), "| calendars retail", len(r2), "durables", len(d2), "| bea gdp 2018+", len(g), "pce", len(p))
