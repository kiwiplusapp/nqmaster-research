"""2026-10-10 (Federico: 'can you disable the 25 days warm up?'): configurable warm-up.
NQMaster  WarmupDays (default 15 = validated: ATR needs 14 RTH days, trend 15 closes). 2-14 = trade sooner with short averages
          (ATR = mean of the RTH true ranges so far, trend = close vs mean of the closes so far).
GoldMaster WarmupDays (default 60 = validated: EWM ATR seeded from the first range + SMA20 trend). < 60 = ATR ramps up as a
          plain mean over the first 14 days, trend from min(20, WarmupDays) closes.
Defaults leave both strategies exactly as validated. Run from the repo root."""
import sys


def patch(path, reps):
    s = open(path, encoding="utf-8").read()
    for a, b in reps:
        if s.count(a) != 1: sys.exit(f"{path}: expected 1 x, found {s.count(a)}: {a[:90]!r}")
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8").write(s); print("patched", path)


NQ = [
    ("NewsBlackout = false; NewsTimes = \"\";\n",
     "NewsBlackout = false; NewsTimes = \"\";\n\t\t\t\tWarmupDays = 15;\n"),
    ("\t\t\t\tif (mods != null && totalTrades == 0 && rthDaysSeen < 25)\n\t\t\t\t\tPrint(string.Format(\"NQMaster | 0 trades: only {0} RTH days loaded; needs ~25 days of warm-up. Start the test 2+ months earlier.\", rthDaysSeen));",
     "\t\t\t\tif (mods != null && totalTrades == 0 && rthDaysSeen < WarmupDays + 2)\n\t\t\t\t\tPrint(string.Format(\"NQMaster | 0 trades: only {0} RTH days loaded; needs {1} days of warm-up (property 'Warm-up days'). Start the test earlier or lower it.\", rthDaysSeen, WarmupDays));"),
    ("\t\t\tif (rthCloses.Count >= 15)\n", "\t\t\tif (rthCloses.Count >= TrendMin)\n"),
    ("if (trendDir == 0 || atrCount < 14 || double.IsNaN(todayAtr)) return;", "if (trendDir == 0 || atrCount < AtrMin || double.IsNaN(todayAtr)) return;"),
    ("double.IsNaN(rthOpenPx) || atrCount < 14) return;", "double.IsNaN(rthOpenPx) || atrCount < AtrMin) return;"),
    ("if (!e10aHas || !e10bHas || atrCount < 14 ||", "if (!e10aHas || !e10bHas || atrCount < AtrMin ||"),
    ("if (atrCount < 14 || double.IsNaN(atrDaily) || m.InTrade) return;", "if (atrCount < AtrMin || double.IsNaN(atrDaily) || m.InTrade) return;"),
    ("if (atrCount < 14 || double.IsNaN(todayAtr) || todayAtr <= 0) return;", "if (atrCount < AtrMin || double.IsNaN(todayAtr) || todayAtr <= 0) return;"),
    ("if (atrCount < 14 || double.IsNaN(atrDaily) || d != trendDir) { lonStage = 3; return; }", "if (atrCount < AtrMin || double.IsNaN(atrDaily) || d != trendDir) { lonStage = 3; return; }"),
    ("openMin >= 630 && openMin < 945 && atrCount >= 14)", "openMin >= 630 && openMin < 945 && atrCount >= AtrMin)"),
    ("closeMin >= 630 && closeMin < 945 && atrCount >= 14 && trendDir != 0", "closeMin >= 630 && closeMin < 945 && atrCount >= AtrMin && trendDir != 0"),
    ("ictTrades >= 3 || d != trendDir || atrCount < 14) continue;", "ictTrades >= 3 || d != trendDir || atrCount < AtrMin) continue;"),
    ("if (rthCloses.Count < 15 || double.IsNaN(todayAtr) || todayAtr <= 0) return double.NaN;", "if (rthCloses.Count < TrendMin || double.IsNaN(todayAtr) || todayAtr <= 0) return double.NaN;"),
    ("\t\tprivate double LastClose(int back)",
     "\t\t// warm-up (property WarmupDays; 15 = validated): RTH days of ATR history and closes needed before the modules trade\n"
     "\t\tprivate int AtrMin { get { return Math.Min(14, Math.Max(1, WarmupDays)); } }\n"
     "\t\tprivate int TrendMin { get { return Math.Min(15, Math.Max(2, WarmupDays)); } }\n"
     "\t\tprivate double LastClose(int back)"),
    ("[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = \"Min daily ATR (points) to trade (0 = off)\", Order = 47, GroupName = \"03. Risk / account\")] public double MinAtrPoints { get; set; }",
     "[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = \"Min daily ATR (points) to trade (0 = off)\", Order = 47, GroupName = \"03. Risk / account\")] public double MinAtrPoints { get; set; }\n"
     "\t\t[NinjaScriptProperty][Range(2, 15)][Display(Name = \"Warm-up days (15 = validated; 2 = trade from day 3 with short ATR / trend averages)\", Order = 48, GroupName = \"03. Risk / account\")] public int WarmupDays { get; set; }"),
]
GOLD = [
    ("DailyLossLimit = 0; AccountDailyStop = 0; AccountProfitStop = 0;", "WarmupDays = 60; DailyLossLimit = 0; AccountDailyStop = 0; AccountProfitStop = 0;"),
    ("if (rthDays < 60) Print(\"GoldMaster | WARNING: only \" + rthDays + \" RTH days loaded - set Days to load >= 120 (ATR / trend warm-up).\");",
     "if (rthDays < WarmupDays) Print(\"GoldMaster | WARNING: only \" + rthDays + \" RTH days loaded, warm-up needs \" + WarmupDays + \" - set Days to load >= \" + (2 * WarmupDays) + \" or lower 'Warm-up days'.\");"),
    ("atr = double.IsNaN(atr) ? tr : atr + (tr - atr) / 14.0;",
     "atr = double.IsNaN(atr) ? tr : atr + (tr - atr) / (WarmupDays < 60 ? Math.Min(rthDays + 1, 14) : 14.0);	// short warm-up: plain mean over the first 14 days"),
    ("if (closes.Count >= 20) { double s = 0;", "if (closes.Count >= Math.Min(20, Math.Max(2, WarmupDays))) { double s = 0;"),
    ("private bool AtrOk { get { return !double.IsNaN(atr) && atr > 0 && closes.Count >= 15 && rthDays >= 60; } }",
     "private bool AtrOk { get { return !double.IsNaN(atr) && atr > 0 && closes.Count >= Math.Min(15, Math.Max(2, WarmupDays)) && rthDays >= WarmupDays; } }"),
    ("status = AtrOk ? \"trading\" : \"warming up (needs 60 RTH days: Days to load >= 120)\";",
     "status = AtrOk ? \"trading\" : \"warming up (needs \" + WarmupDays + \" RTH days: Days to load >= \" + (2 * WarmupDays) + \" or lower 'Warm-up days')\";"),
    ("[NinjaScriptProperty][Range(0, 100)][Display(Name = \"Eval consistency % (Lucid 50, 0 = off)\", Order = 10, GroupName = \"02. Risk / account\")] public double ConsistencyPct { get; set; }",
     "[NinjaScriptProperty][Range(0, 100)][Display(Name = \"Eval consistency % (Lucid 50, 0 = off)\", Order = 10, GroupName = \"02. Risk / account\")] public double ConsistencyPct { get; set; }\n"
     "\t\t[NinjaScriptProperty][Range(2, 60)][Display(Name = \"Warm-up days (60 = validated; 2 = trade from day 3 with short ATR / trend averages)\", Order = 15, GroupName = \"02. Risk / account\")] public int WarmupDays { get; set; }"),
]
if __name__ == "__main__":
    nq = sys.argv[1] if len(sys.argv) > 1 else "NQMaster.cs"; gd = sys.argv[2] if len(sys.argv) > 2 else "GoldMaster.cs"
    patch(nq, NQ); patch(gd, GOLD)
