"""Patch NQMaster.cs with the fixes from the code review (2026-10-06):
1 conflicting entries: ORB / ICT / ENG10 keep their signal when the entry is deferred (opposite working order being cancelled),
  VOLB stays out while another module is waiting (prevents the cancel / re-place ping-pong).
2 live stop entries already through the level (ask/bid) -> market entry instead of a rejected stop; rejected protective order
  -> flatten; RealtimeErrorHandling = IgnoreAllErrors (the strategy is no longer shut down by one rejected entry).
3 eval target decided on equity incl. open P&L, re-checked once flat (un-latch if the realized balance falls short).
4 LATE15 / LATEFH: RTH move measured from the CLOSE of the first RTH bar (research), skip days without a complete prior RTH close.
5 prop peak after restart = max(StartBalance, saved file, override); day start / best day persisted per trade date.
6 partial fills: bookkeeping once, target recomputed from the average fill on every execution.
minor: flatten at the close of the 15:55 bar (FlattenTime 1556), VOLB cancelled at the close of the 14:59 bar."""
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b, cnt=1):
    global s
    n = s.count(a); assert n == cnt, (n, a[:100]); s = s.replace(a, b)
# ---- 1 deferral handling
rep("\t\t\tif (blocked) { lastDeferred = true; return false; }\n", "\t\t\tif (blocked) { lastDeferred = true; deferUntil = CurrentBars[0] + (BarsInProgress == 1 ? 5 : 1); return false; }\n")
rep("\t\tprivate bool lastDeferred;\n", "\t\tprivate bool lastDeferred; private int deferUntil = -1;\n")
rep("\t\t\to.Armed = false;\n\t\t\tif (!DirectionAllowed(d)) return;\n", "\t\t\to.Armed = false;\n\t\t\tif (!DirectionAllowed(d)) { if (lastDeferred) o.Armed = true; return; }\n")
rep("\t\t\t\tif (risk <= 0 || risk > 0.25 * todayAtr || !DirectionAllowed(d)) continue;\n", "\t\t\t\tif (risk <= 0 || risk > 0.25 * todayAtr) continue;\n\t\t\t\tif (!DirectionAllowed(d)) { if (lastDeferred) ictAct[s] = true; continue; }\n")
rep("\t\t\tif (volbDone || volb.InTrade || double.IsNaN(volbUp) || double.IsNaN(rthOpenPx) || atrCount < 14) return;\n\t\t\tif (openMin >= 900) {",
    "\t\t\tif (volbDone || volb.InTrade || double.IsNaN(volbUp) || double.IsNaN(rthOpenPx) || atrCount < 14) return;\n\t\t\tif (CurrentBars[0] <= deferUntil && openMin < 899) return;      // another module is waiting for VOLB's order to be cancelled\n\t\t\tif (openMin >= 899) {")
# ENG10: decision once at 09:59; if deferred, retry on the next bars until 11:29 (market entry if price already passed the level)
rep("\t\t\tif (openMin != 599) return;\n\t\t\teng10Done = true;\n", "\t\t\tif (eng10Retry && openMin < 689) { Eng10Place(); return; }\n\t\t\tif (openMin != 599) return;\n\t\t\teng10Done = true;\n")
rep("\t\t\tif (!DirectionAllowed(d)) return;\n\t\t\tArmPriceBracket(eng10, d, sl);\n\t\t\tif (d == 1) EnterLongStopMarket(0, true, Qty(), px, eng10.Sig); else EnterShortStopMarket(0, true, Qty(), px, eng10.Sig);\n\t\t\tLog(string.Format(\"ENG10 {0} STOP @ {1} | SL {2}\", d == 1 ? \"BUY\" : \"SELL\", Fmt(px), Fmt(sl)));\n\t\t}\n",
    "\t\t\te10d = d; e10px = px; e10sl = sl; eng10Retry = true; Eng10Place();\n\t\t}\n"
    "\t\tprivate int e10d; private double e10px, e10sl; private bool eng10Retry;\n"
    "\t\tprivate void Eng10Place()\n\t\t{\n"
    "\t\t\tif (!DirectionAllowed(e10d)) { if (!lastDeferred) eng10Retry = false; return; }\n"
    "\t\t\teng10Retry = false;\n\t\t\tArmPriceBracket(eng10, e10d, e10sl);\n"
    "\t\t\tif (PastLevel(e10d, e10px)) { if (e10d == 1) EnterLong(0, Qty(), eng10.Sig); else EnterShort(0, Qty(), eng10.Sig); }\n"
    "\t\t\telse if (e10d == 1) EnterLongStopMarket(0, true, Qty(), e10px, eng10.Sig); else EnterShortStopMarket(0, true, Qty(), e10px, eng10.Sig);\n"
    "\t\t\tLog(string.Format(\"ENG10 {0} @ {1} | SL {2}\", e10d == 1 ? \"BUY\" : \"SELL\", Fmt(e10px), Fmt(e10sl)));\n\t\t}\n"
    "\t\t// price already at/through a stop-entry level? historical: bar close; realtime: current ask / bid (a stop there would be rejected)\n"
    "\t\tprivate bool PastLevel(int d, double px)\n\t\t{\n"
    "\t\t\tif (State == State.Realtime) { try { return d == 1 ? GetCurrentAsk() >= px : GetCurrentBid() <= px; } catch { } }\n"
    "\t\t\treturn d == 1 ? Close[0] >= px : Close[0] <= px;\n\t\t}\n")
rep("\t\t\te10aHas = false; e10bHas = false; eng10Done = false; close10 = double.NaN;\n", "\t\t\te10aHas = false; e10bHas = false; eng10Done = false; eng10Retry = false; close10 = double.NaN; rthFirstClose = double.NaN;\n")
# ---- 2 realtime through-checks and rejection handling
rep("\t\t\tbool through = d == 1 ? Close[0] >= entry : Close[0] <= entry;\n", "\t\t\tbool through = PastLevel(d, entry);\n")
rep("\t\t\tif ((d == 1 && Close[0] >= lvl) || (d == -1 && Close[0] <= lvl)) { volbDone = true; return; }   // already through: no chase",
    "\t\t\tif (PastLevel(d, lvl)) { volbDone = true; return; }   // already through: no chase")
rep("\t\t\t\tRealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;", "\t\t\t\tRealtimeErrorHandling = RealtimeErrorHandling.IgnoreAllErrors;	// rejections handled in OnOrderUpdate")
rep("\t\t\tif (orderState == OrderState.Rejected) Print(string.Format(\"NQMaster | {0} REJECTED: {1} {2}\", order.Name, error, nativeError));\n",
    "\t\t\tif (orderState == OrderState.Rejected)\n\t\t\t{\n\t\t\t\tPrint(string.Format(\"NQMaster | {0} REJECTED: {1} {2}\", order.Name, error, nativeError));\n"
    "\t\t\t\t// a rejected stop-loss / target leaves a position unprotected -> flatten; a rejected entry is simply skipped\n"
    "\t\t\t\tif (m == null && Position.MarketPosition != MarketPosition.Flat) FlattenAll(\"protective order rejected\");\n\t\t\t}\n")
# ---- 3 eval target on equity incl. open P&L, un-latch when the realized balance falls short once flat
rep("\t\t\t\tdouble today = double.IsNaN(propDayStart) ? 0 : bal - propDayStart;\n\t\t\t\tdouble need = EvalTarget;\n\t\t\t\tif (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);\n\t\t\t\tif (bal >= StartBalance + need) {",
    "\t\t\t\tdouble eqNow = bal + Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar);\n\t\t\t\tdouble today = double.IsNaN(propDayStart) ? 0 : eqNow - propDayStart;\n\t\t\t\tdouble need = EvalTarget;\n\t\t\t\tif (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);\n\t\t\t\tif (eqNow >= StartBalance + need) {")
rep("\t\t\tif (MaxDrawdown > 0 && bal <= highWater - MaxDrawdown + DrawdownBuffer && !ddTripped)",
    "\t\t\tif (EvalTarget > 0 && targetHit && Position.MarketPosition == MarketPosition.Flat)\n\t\t\t{\n"
    "\t\t\t\tdouble today = double.IsNaN(propDayStart) ? 0 : bal - propDayStart, need = EvalTarget;\n"
    "\t\t\t\tif (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);\n"
    "\t\t\t\tif (bal < StartBalance + need) { targetHit = false; Print(string.Format(\"NQMaster | eval target not met after closing (+{0:0}, needed {1:0}) - trading resumes.\", bal - StartBalance, need)); }\n\t\t\t}\n"
    "\t\t\tif (MaxDrawdown > 0 && bal <= highWater - MaxDrawdown + DrawdownBuffer && !ddTripped)")
# ---- 4 LATE reference = close of the first RTH bar; skip without a complete prior RTH close
rep("rthOpenPx = Open[0]; SetupIctLevels();", "rthOpenPx = Open[0]; rthFirstClose = Close[0]; SetupIctLevels();")
rep("\t\tprivate Mod orb, orb2, mseq, mseqs, crt, lon, ict, rsi, volb, eng10;\n", "\t\tprivate Mod orb, orb2, mseq, mseqs, crt, lon, ict, rsi, volb, eng10;\n\t\tprivate double rthFirstClose = double.NaN;\n")
rep("\t\t\telse if (m.Lookback == -2) reference = rthOpenPx;\n", "\t\t\telse if (m.Lookback == -2) reference = rthOpenPx;\n\t\t\telse if (m.Lookback == -4) { if (double.IsNaN(full1)) return; reference = rthFirstClose; }\n")
rep('AddTime("LATE15", (custom ? UseLate15 : (ul || w7 || core) && UseLate15), 1500, -2,', 'AddTime("LATE15", (custom ? UseLate15 : (ul || w7 || core) && UseLate15), 1500, -4,')
rep('AddTime("LATEFH", (custom ? UseLateFh : ul && UseLateFh), 1500, -2,', 'AddTime("LATEFH", (custom ? UseLateFh : ul && UseLateFh), 1500, -4,')
# ---- 5 prop peak / day state after a restart
rep("\t\t\tpropLive = true; propPeak = Math.Max(StartBalance, PropEquity()); propDayStart = double.NaN; propBestDay = EvalBestDaySoFar;\n"
    "\t\t\ttry { string f = PropFile; if (f != null && File.Exists(f)) { double v; if (double.TryParse(File.ReadAllText(f).Trim(), NumberStyles.Any, CultureInfo.InvariantCulture, out v)) propPeak = Math.Max(propPeak, v); } } catch { }\n"
    "\t\t\tif (PropPeakOverride > 0) propPeak = PropPeakOverride;\n",
    "\t\t\tpropLive = true; propPeak = StartBalance; propDayStart = double.NaN; propBestDay = EvalBestDaySoFar;\n"
    "\t\t\tDateTime et = ToEt(Times[0][0]); DateTime td = et.Hour >= 18 ? et.Date.AddDays(1) : et.Date; int today = td.Year * 10000 + td.Month * 100 + td.Day;\n"
    "\t\t\ttry\n\t\t\t{\n\t\t\t\tstring f = PropFile;\n\t\t\t\tif (f != null && File.Exists(f))\n\t\t\t\t{\n"
    "\t\t\t\t\tstring[] a = File.ReadAllText(f).Trim().Split(';'); double v;\n"
    "\t\t\t\t\tif (a.Length > 0 && double.TryParse(a[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) propPeak = Math.Max(propPeak, v);\n"
    "\t\t\t\t\tint fd; double ds, bd;\n"
    "\t\t\t\t\tif (a.Length >= 4 && int.TryParse(a[1], out fd) && fd == today && double.TryParse(a[2], NumberStyles.Any, CultureInfo.InvariantCulture, out ds)) propDayStart = ds;\n"
    "\t\t\t\t\tif (a.Length >= 4 && double.TryParse(a[3], NumberStyles.Any, CultureInfo.InvariantCulture, out bd)) propBestDay = Math.Max(propBestDay, bd);\n"
    "\t\t\t\t}\n\t\t\t}\n\t\t\tcatch { }\n"
    "\t\t\tif (PropPeakOverride > 0) propPeak = Math.Max(propPeak, PropPeakOverride);\n"
    "\t\t\tif (!double.IsNaN(propDayStart)) { propRestoredDay = today; }\n")
rep("\t\tprivate bool propLive; private double propBestDay = 0;\n", "\t\tprivate bool propLive; private double propBestDay = 0; private int propRestoredDay = -1;\n"
    "\t\tprivate void PropSave(int tradeDay)\n\t\t{\n\t\t\tif (!propLive) return;\n"
    "\t\t\ttry { File.WriteAllText(PropFile, string.Format(CultureInfo.InvariantCulture, \"{0:0.00};{1};{2:0.00};{3:0.00}\", propPeak, tradeDay, propDayStart, propBestDay)); } catch { }\n\t\t}\n")
rep("\t\t\t\tdouble eq = PropEquity();\n\t\t\t\tif (!double.IsNaN(propDayStart)) propBestDay = Math.Max(propBestDay, eq - propDayStart);\n\t\t\t\tpropDayStart = eq;\n",
    "\t\t\t\tdouble eq = PropEquity();\n\t\t\t\tDateTime et0 = ToEt(Times[0][0]); DateTime td0 = et0.Hour >= 18 ? et0.Date.AddDays(1) : et0.Date; int tday = td0.Year * 10000 + td0.Month * 100 + td0.Day;\n"
    "\t\t\t\tif (propRestoredDay == tday && !double.IsNaN(propDayStart)) { }                  // restarted mid-session: keep the saved day start\n"
    "\t\t\t\telse { if (!double.IsNaN(propDayStart)) propBestDay = Math.Max(propBestDay, eq - propDayStart); propDayStart = eq; }\n"
    "\t\t\t\tpropRestoredDay = -1;\n")
rep("\t\t\t\tif (eq > propPeak) { propPeak = eq; if (propLive) try { File.WriteAllText(PropFile, propPeak.ToString(\"0.00\", CultureInfo.InvariantCulture)); } catch { } }\n",
    "\t\t\t\tif (eq > propPeak) propPeak = eq;\n\t\t\t\tPropSave(tday);\n")
# ---- 6 partial fills
rep("\t\t\t\tif (execution.Order.OrderState != OrderState.Filled) return;\n\t\t\t\tm.InTrade = true; m.EntryPx = execution.Order.AverageFillPrice;\n",
    "\t\t\t\tif (execution.Order.Filled <= 0) return;\n\t\t\t\tbool first = !m.InTrade;\n\t\t\t\tm.InTrade = true; m.EntryPx = execution.Order.AverageFillPrice;\n\t\t\t\tif (first)\n\t\t\t\t{\n")
rep("\t\t\t\t// cancel opposite working entries\n\t\t\t\tforeach (Mod o in mods) if (o != m && Working(o.Entry) && o.Dir == -m.Dir) CancelOrder(o.Entry);\n",
    "\t\t\t\t// cancel opposite working entries\n\t\t\t\tforeach (Mod o in mods) if (o != m && Working(o.Entry) && o.Dir == -m.Dir) CancelOrder(o.Entry);\n\t\t\t\t}\n")
# ---- minor
rep("Contracts = 1; FlattenTime = 1555; SkipFomc = true;", "Contracts = 1; FlattenTime = 1556; SkipFomc = true;")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched")
