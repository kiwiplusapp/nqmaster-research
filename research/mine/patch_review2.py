"""Second code-review round (2026-10-07) for NQMaster.cs and GoldMaster.cs.
NQMaster: (1) ENG10 retry really runs (it was blocked by eng10Done); (11) stop / limit entries cancelled for an opposite trade are
PARKED and re-placed when no opposite position / order remains (dropped if their level trades meanwhile or the module window ends),
as research only drops a fill against an open opposite position; parked modules take no new signals; (2) best day of a session that
NinjaTrader did not see close is recovered from the saved day start; (5) PropPeakOverride replaces the peak again; (8) VOLB in
realtime with the ask/bid right at the level -> market entry instead of skipping; (9) eval target un-latches only when the whole
account is flat; (10) a rejected stop/target exits only its module; (12) VOLB trend-only invalidation checked during deferrals;
order references only replaced when the previous order is finished.
GoldMaster: (3) GetRealtimeOrder at go-live; (4) day start at go-live = cash - realized today (no open P&L), stops from the
simulated history reset; NQMaster's prop file (same account) gives the day start and best day when available; (6) order references
captured from the Enter* calls and never overwritten by late events of an old order, parked setups re-armed only when the old order
is finished; (7) only stop orders are parked; (9) target un-latch only when the whole account is flat; (13) edge monitor divides by
the size actually traded that day."""
P = r"D:\NinjaTrader Strategy\{}.cs"
def patch(name, reps):
    s = open(P.format(name), encoding="utf-8").read()
    for a, b in reps:
        n = s.count(a); assert n == 1, (name, n, a[:110]); s = s.replace(a, b)
    open(P.format(name), "w", encoding="utf-8", newline="\n").write(s); print(name, "patched", len(reps))

NQ = [
# ---- Mod fields for parking
("\t\t\tpublic bool Retry;\n\t\t}",
 "\t\t\tpublic bool Retry;\n\t\t\tpublic bool Parked, ParkLimit; public double ParkPx; public int ParkQty;	// entry cancelled for an opposite trade, re-placed when free\n\t\t}"),
# ---- (1) ENG10 retry before the eng10Done early return
("\t\tprivate void ManageEng10(int openMin)\n\t\t{\n\t\t\tif (eng10Done || eng10.InTrade)",
 "\t\tprivate void ManageEng10(int openMin)\n\t\t{\n"
 "\t\t\tif (eng10Retry && !eng10.InTrade && !eng10.Parked) { if (openMin >= 600 && openMin < 689) Eng10Place(); else eng10Retry = false; return; }\n"
 "\t\t\tif (eng10Done || eng10.InTrade)"),
("\t\t\tif (eng10Retry && openMin < 689) { Eng10Place(); return; }\n", ""),
# ---- (12) VOLB: deferral wait after the trend-only invalidation; (8) realtime at-level market entry
("\t\t\tif (CurrentBars[0] <= deferUntil && openMin < 899) return;      // another module is waiting for VOLB's order to be cancelled\n", ""),
("\t\t\t\td = trendDir;\n\t\t\t}\n\t\t\tif (Working(volb.Entry))",
 "\t\t\t\td = trendDir;\n\t\t\t}\n\t\t\tif (CurrentBars[0] <= deferUntil) return;      // another module is waiting for VOLB's order to be cancelled\n\t\t\tif (Working(volb.Entry))"),
("\t\t\tif (PastLevel(d, lvl)) { volbDone = true; return; }   // already through: no chase\n",
 "\t\t\tif (PastLevel(d, lvl))\n\t\t\t{\n"
 "\t\t\t\t// realtime with the ask / bid right at the level (a stop there would be rejected): market entry; further through: no chase\n"
 "\t\t\t\tdouble mk = double.NaN;\n"
 "\t\t\t\tif (State == State.Realtime) try { mk = d == 1 ? GetCurrentAsk() : GetCurrentBid(); } catch { }\n"
 "\t\t\t\tif (!double.IsNaN(mk) && (mk - lvl) * d <= TickSize && !OppBusy(d, volb))\n"
 "\t\t\t\t{ ArmPriceBracket(volb, d, Instrument.MasterInstrument.RoundToTickSize(rthOpenPx)); if (d == 1) EnterLong(0, Qty(), volb.Sig); else EnterShort(0, Qty(), volb.Sig); }\n"
 "\t\t\t\tvolbDone = true; return;\n\t\t\t}\n"),
# ---- parked modules take no new signals
("\t\t\tif (!o.Armed || o.InTrade || Working(o.Entry) || o.Trades >= 2) return;",
 "\t\t\tif (o.Parked || !o.Armed || o.InTrade || Working(o.Entry) || o.Trades >= 2) return;"),
("\t\t\t\tif (ict.InTrade || Working(ict.Entry) || ictTrades >= 3 || d != trendDir || atrCount < 14) continue;",
 "\t\t\t\tif (ict.InTrade || Working(ict.Entry) || ict.Parked || ictTrades >= 3 || d != trendDir || atrCount < 14) continue;"),
# ---- call ManageParked each minute after the trade gate
("\t\t\tbool canTrade = CanTrade();\n\t\t\tif (!canTrade) { CancelAllEntries(); UpdateDashboard(); return; }\n",
 "\t\t\tbool canTrade = CanTrade();\n\t\t\tif (!canTrade) { CancelAllEntries(); UpdateDashboard(); return; }\n\t\t\tManageParked(openMin, closeMin);\n"),
("\t\t\tm11Dir = 0; onSum = 0; lonDir = 0;\n\t\t}", "\t\t\tm11Dir = 0; onSum = 0; lonDir = 0;\n\t\t\tforeach (Mod m in mods) m.Parked = false;\n\t\t}"),
("\t\tprivate void CancelAllEntries() { foreach (Mod m in mods) if (Working(m.Entry)) CancelOrder(m.Entry); }",
 "\t\tprivate void CancelAllEntries() { foreach (Mod m in mods) { m.Parked = false; if (Working(m.Entry)) CancelOrder(m.Entry); } }\n"
 "\t\t// ---- parking (research/mine/patch_review2.py): research keeps every module's order working and only drops a fill against an open\n"
 "\t\t// opposite position. NinjaTrader's managed rules cannot hold opposite entry orders at once, so the cancelled one is kept here and\n"
 "\t\t// re-placed as soon as no opposite position / working order remains. Dropped if its level trades while blocked or its window ends.\n"
 "\t\tprivate void ParkOrder(Mod o)\n\t\t{\n"
 "\t\t\tOrder e = o.Entry;\n\t\t\tif (e == null || !Working(e)) return;\n"
 "\t\t\tif (o != volb && (e.OrderType == OrderType.StopMarket || e.OrderType == OrderType.Limit))\n"
 "\t\t\t{ o.Parked = true; o.ParkLimit = e.OrderType == OrderType.Limit; o.ParkPx = o.ParkLimit ? e.LimitPrice : e.StopPrice; o.ParkQty = Math.Max(1, e.Quantity); Log(o.Sig + \" order parked (opposite trade)\"); }\n"
 "\t\t\tCancelOrder(e);\n\t\t}\n"
 "\t\tprivate bool OppBusy(int d, Mod self)\n\t\t{\n"
 "\t\t\tif ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return true;\n"
 "\t\t\tforeach (Mod o in mods) if (o != self && Working(o.Entry) && o.Dir == -d) return true;\n\t\t\treturn false;\n\t\t}\n"
 "\t\tprivate bool ParkExpired(Mod o, int openMin, int closeMin)\n\t\t{\n"
 "\t\t\tif (o.Kind == 0) return closeMin >= 780;\n"
 "\t\t\tif (o == eng10) return openMin >= 689;\n"
 "\t\t\tif (o == lon) return openMin >= 480;\n"
 "\t\t\tif (o == ict) return CurrentBars[1] >= ictExpiry || (ict.Dir == -1 && High[0] > ictExtPend) || (ict.Dir == 1 && Low[0] < ictExtPend);\n"
 "\t\t\treturn true;\n\t\t}\n"
 "\t\tprivate void ManageParked(int openMin, int closeMin)\n\t\t{\n"
 "\t\t\tforeach (Mod o in mods)\n\t\t\t{\n"
 "\t\t\t\tif (!o.Parked || Working(o.Entry)) continue;					// the cancel is still pending\n"
 "\t\t\t\tbool hit = o.ParkLimit ? (o.Dir == 1 ? Low[0] <= o.ParkPx : High[0] >= o.ParkPx) : (o.Dir == 1 ? High[0] >= o.ParkPx : Low[0] <= o.ParkPx);\n"
 "\t\t\t\tif (o.InTrade || hit || ParkExpired(o, openMin, closeMin)) { o.Parked = false; Log(o.Sig + \" parked order dropped\" + (hit ? \" (level traded while blocked)\" : \"\")); continue; }\n"
 "\t\t\t\tif (OppBusy(o.Dir, o)) continue;\n"
 "\t\t\t\to.Parked = false;\n"
 "\t\t\t\tif (o.ParkLimit) { if (o.Dir == 1) EnterLongLimit(0, true, o.ParkQty, o.ParkPx, o.Sig); else EnterShortLimit(0, true, o.ParkQty, o.ParkPx, o.Sig); }\n"
 "\t\t\t\telse if (PastLevel(o.Dir, o.ParkPx)) { Log(o.Sig + \" parked order dropped (level passed)\"); continue; }\n"
 "\t\t\t\telse if (o.Dir == 1) EnterLongStopMarket(0, true, o.ParkQty, o.ParkPx, o.Sig); else EnterShortStopMarket(0, true, o.ParkQty, o.ParkPx, o.Sig);\n"
 "\t\t\t\tLog(o.Sig + \" parked order re-placed @ \" + Fmt(o.ParkPx));\n\t\t\t}\n\t\t}"),
("\t\t\tforeach (Mod m in mods) if (Working(m.Entry) && m.Dir == -d) { CancelOrder(m.Entry); blocked = true; }",
 "\t\t\tforeach (Mod m in mods) if (Working(m.Entry) && m.Dir == -d) { ParkOrder(m); blocked = true; }"),
("\t\t\t\tforeach (Mod o in mods) if (o != m && Working(o.Entry) && o.Dir == -m.Dir) CancelOrder(o.Entry);",
 "\t\t\t\tforeach (Mod o in mods) if (o != m && Working(o.Entry) && o.Dir == -m.Dir) ParkOrder(o);"),
# ---- order references: never overwritten by a late event of an older order
("\t\t\tMod m = BySig(order.Name);\n\t\t\tif (m != null) m.Entry = order;\n\t\t\tif (orderState == OrderState.Rejected)\n\t\t\t{\n\t\t\t\tPrint(string.Format(\"NQMaster | {0} REJECTED: {1} {2}\", order.Name, error, nativeError));\n"
 "\t\t\t\t// a rejected stop-loss / target leaves a position unprotected -> flatten; a rejected entry is simply skipped\n"
 "\t\t\t\tif (m == null && Position.MarketPosition != MarketPosition.Flat) FlattenAll(\"protective order rejected\");\n\t\t\t}",
 "\t\t\tMod m = BySig(order.Name);\n\t\t\tif (m != null && (m.Entry == null || m.Entry == order || !Working(m.Entry))) m.Entry = order;\n"
 "\t\t\tif (orderState == OrderState.Rejected)\n\t\t\t{\n\t\t\t\tPrint(string.Format(\"NQMaster | {0} REJECTED: {1} {2}\", order.Name, error, nativeError));\n"
 "\t\t\t\t// a rejected stop-loss / target leaves that module unprotected -> exit it; any other rejected exit -> flatten; a rejected entry is skipped\n"
 "\t\t\t\tif (m == null && Position.MarketPosition != MarketPosition.Flat)\n\t\t\t\t{\n"
 "\t\t\t\t\tMod f = (order.Name == \"Stop loss\" || order.Name == \"Profit target\") ? BySig(order.FromEntrySignal) : null;\n"
 "\t\t\t\t\tif (f != null) { if (f.InTrade) ExitModule(f, \"protective order rejected\"); }\n"
 "\t\t\t\t\telse FlattenAll(\"exit order rejected\");\n\t\t\t\t}\n\t\t\t}"),
# ---- (5) PropPeakOverride replaces the peak; (2) best day of a session NinjaTrader did not see close
("\t\t\t\t\tint fd; double ds, bd;\n"
 "\t\t\t\t\tif (a.Length >= 4 && int.TryParse(a[1], out fd) && fd == today && double.TryParse(a[2], NumberStyles.Any, CultureInfo.InvariantCulture, out ds)) propDayStart = ds;\n",
 "\t\t\t\t\tint fd; double ds, bd;\n"
 "\t\t\t\t\tif (a.Length >= 4 && int.TryParse(a[1], out fd) && double.TryParse(a[2], NumberStyles.Any, CultureInfo.InvariantCulture, out ds))\n"
 "\t\t\t\t\t{ if (fd == today) propDayStart = ds; else if (fd < today) savedPrevDayStart = ds; }\n"),
("\t\t\tif (PropPeakOverride > 0) propPeak = Math.Max(propPeak, PropPeakOverride);\n",
 "\t\t\tif (PropPeakOverride > 0) propPeak = PropPeakOverride;		// manual correction (e.g. a stale file after an account reset)\n"),
("\t\t\tif (!double.IsNaN(propDayStart)) { propRestoredDay = today; }\n",
 "\t\t\t// the last session NinjaTrader saw start was not closed by it (shut down before 18:00): its P&L = today's start - its start\n"
 "\t\t\tif (!double.IsNaN(savedPrevDayStart) && !double.IsNaN(propDayStart)) { propBestDay = Math.Max(propBestDay, propDayStart - savedPrevDayStart); savedPrevDayStart = double.NaN; }\n"
 "\t\t\tif (!double.IsNaN(propDayStart)) { propRestoredDay = today; }\n"),
("\t\tprivate bool propLive; private double propBestDay = 0; private int propRestoredDay = -1;",
 "\t\tprivate bool propLive; private double propBestDay = 0, savedPrevDayStart = double.NaN; private int propRestoredDay = -1;"),
# ---- (9) un-latch only when the whole account is flat, on the realized balance
("\t\t\tif (EvalTarget > 0 && targetHit && Position.MarketPosition == MarketPosition.Flat)\n\t\t\t{\n"
 "\t\t\t\tdouble eqF = bal + Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar);\n"
 "\t\t\t\tdouble today = double.IsNaN(propDayStart) ? 0 : eqF - propDayStart, need = EvalTarget;\n\t\t\t\tif (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);\n\t\t\t\tif (eqF < StartBalance + need)",
 "\t\t\tif (EvalTarget > 0 && targetHit && Position.MarketPosition == MarketPosition.Flat && Math.Abs(Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar)) < 0.01)\n\t\t\t{\n"
 "\t\t\t\tdouble today = double.IsNaN(propDayStart) ? 0 : bal - propDayStart, need = EvalTarget;\n\t\t\t\tif (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);\n\t\t\t\tif (bal < StartBalance + need)"),
]
patch("NQMaster", NQ)

GOLD = [
# ---- (3)(4) go-live: realtime orders, day start without open P&L, simulated-history stops reset, NQMaster prop file
("\t\t\t\t// enabled mid-day: the day started at equity now minus what the account already realized today\n\t\t\t\ttry\n\t\t\t\t{\n"
 "\t\t\t\t\tdouble rp = Account.Get(AccountItem.RealizedProfitLoss, Currency.UsDollar);\n"
 "\t\t\t\t\tacctDayStart = AcctEquity() - rp; evDayStart = Account.Get(AccountItem.CashValue, Currency.UsDollar) - rp;\n"
 "\t\t\t\t\tif (double.IsNaN(evBestDay)) evBestDay = EvalBestDaySoFar;\n\t\t\t\t}\n\t\t\t\tcatch { }\n",
 "\t\t\t\tforeach (Mod m in mods) if (m.Entry != null) m.Entry = GetRealtimeOrder(m.Entry);\n"
 "\t\t\t\t// enabled mid-day: the day started at cash now minus what the account already realized today (NQMaster's saved day start\n"
 "\t\t\t\t// for this account wins when it is from today); stops computed on the simulated history earlier today do not carry over\n"
 "\t\t\t\ttry\n\t\t\t\t{\n"
 "\t\t\t\t\tdouble rp = Account.Get(AccountItem.RealizedProfitLoss, Currency.UsDollar), fpk, fds, fbd; int fdt;\n"
 "\t\t\t\t\tacctDayStart = Account.Get(AccountItem.CashValue, Currency.UsDollar) - rp;\n"
 "\t\t\t\t\tif (ReadNqProp(out fpk, out fdt, out fds, out fbd) && fdt == sessionDate && !double.IsNaN(fds)) acctDayStart = fds;\n"
 "\t\t\t\t\tevDayStart = acctDayStart;\n"
 "\t\t\t\t\tif (double.IsNaN(evBestDay)) evBestDay = EvalBestDaySoFar;\n"
 "\t\t\t\t\tif (!double.IsNaN(fbd)) evBestDay = Math.Max(evBestDay, fbd);\n\t\t\t\t}\n\t\t\t\tcatch { }\n"
 "\t\t\t\tacctStopped = false; dayStopped = false; dayStartPnl = netPnl;\n"),
# ---- NewSession: best day also from NQMaster's file; edge size of the day
("\t\t\t\tif (!double.IsNaN(evDayStart)) evBestDay = Math.Max(evBestDay, eq - evDayStart);\n\t\t\t\tevDayStart = eq;\n\t\t\t}\n\t\t}",
 "\t\t\t\tif (!double.IsNaN(evDayStart)) evBestDay = Math.Max(evBestDay, eq - evDayStart);\n\t\t\t\tevDayStart = eq;\n"
 "\t\t\t\tdouble fpk, fds, fbd; int fdt;\n\t\t\t\tif (ReadNqProp(out fpk, out fdt, out fds, out fbd) && !double.IsNaN(fbd)) evBestDay = Math.Max(evBestDay, fbd);\n\t\t\t}\n"
 "\t\t\tedgeQty = Qty();\n\t\t}\n"
 "\t\t// NQMaster's prop file for this account: \"peak;tradeDate;dayStart;bestDay\" (older files: \"peak\")\n"
 "\t\tprivate bool ReadNqProp(out double peak, out int date, out double dayStart, out double bestDay)\n\t\t{\n"
 "\t\t\tpeak = dayStart = bestDay = double.NaN; date = 0;\n"
 "\t\t\ttry\n\t\t\t{\n"
 "\t\t\t\tstring f = Path.Combine(Core.Globals.UserDataDir, \"nqmaster_prop_\" + Account.Name + \".txt\");\n"
 "\t\t\t\tif (!File.Exists(f)) return false;\n"
 "\t\t\t\tstring[] a = File.ReadAllText(f).Trim().Split(';'); double v;\n"
 "\t\t\t\tif (double.TryParse(a[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) peak = v;\n"
 "\t\t\t\tif (a.Length >= 4)\n\t\t\t\t{\n"
 "\t\t\t\t\tint.TryParse(a[1], out date);\n"
 "\t\t\t\t\tif (double.TryParse(a[2], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) dayStart = v;\n"
 "\t\t\t\t\tif (double.TryParse(a[3], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) bestDay = v;\n\t\t\t\t}\n"
 "\t\t\t\treturn true;\n\t\t\t}\n\t\t\tcatch { return false; }\n\t\t}"),
# ---- (13) edge monitor per traded size
("\t\t\t\tdouble z = fomcToday ? 0.0 : (netPnl - dayStartPnl) / Math.Max(1, Contracts) / (10.0 * atr);",
 "\t\t\t\tdouble z = fomcToday ? 0.0 : (netPnl - dayStartPnl) / Math.Max(1, edgeQty) / (10.0 * atr);"),
("\t\tprivate double edgeS; private int edgeDays; private bool edgeAlarm, edgePaused, edgeDayRth;",
 "\t\tprivate double edgeS; private int edgeDays, edgeQty = 1; private bool edgeAlarm, edgePaused, edgeDayRth;"),
# ---- (7) only stop orders are parked
("\t\tprivate void Park(Mod o) { o.Def = true; o.DPx = o.Entry.StopPrice; CancelOrder(o.Entry); Log(o.Sig + \" stop order parked (opposite trade)\"); }",
 "\t\tprivate void Park(Mod o)\n\t\t{\n"
 "\t\t\tif (o.Entry.OrderType == OrderType.StopMarket) { o.Def = true; o.DPx = o.Entry.StopPrice; Log(o.Sig + \" stop order parked (opposite trade)\"); }\n"
 "\t\t\tCancelOrder(o.Entry);\n\t\t}"),
# ---- (6) capture order references at submission; re-arm parked setups only when the old order is finished
("\t\t\tif (m.Dir == 1) EnterLong(m.Q, m.Sig); else EnterShort(m.Q, m.Sig);\n",
 "\t\t\tOrder o = m.Dir == 1 ? EnterLong(m.Q, m.Sig) : EnterShort(m.Q, m.Sig);\n\t\t\tif (o != null) m.Entry = o;\n"),
("\t\t\tif (d == 1) EnterLongStopMarket(0, true, m.Q, px, m.Sig); else EnterShortStopMarket(0, true, m.Q, px, m.Sig);\n",
 "\t\t\tOrder o = d == 1 ? EnterLongStopMarket(0, true, m.Q, px, m.Sig) : EnterShortStopMarket(0, true, m.Q, px, m.Sig);\n\t\t\tif (o != null) m.Entry = o;\n"),
("\t\t\t\tif (!OppPos(m.Dir) && !OppWork(m.Dir, m)) { m.Def = false; StopEntry(m, m.Dir, m.DPx, m.Sl, m.Tp, m.ExpireMin); }",
 "\t\t\t\tif (!OppPos(m.Dir) && !OppWork(m.Dir, m) && !Working(m.Entry)) { m.Def = false; StopEntry(m, m.Dir, m.DPx, m.Sl, m.Tp, m.ExpireMin); }"),
("\t\t\tMod m = BySig(order.Name);\n\t\t\tif (m != null) m.Entry = order;\n\t\t\tif (orderState == OrderState.Rejected)\n\t\t\t{\n\t\t\t\tPrint(string.Format(\"GoldMaster",
 "\t\t\tMod m = BySig(order.Name);\n\t\t\tif (m != null && (m.Entry == null || m.Entry == order || !Working(m.Entry))) m.Entry = order;\n\t\t\tif (orderState == OrderState.Rejected)\n\t\t\t{\n\t\t\t\tPrint(string.Format(\"GoldMaster"),
("\t\t\tif (orderState == OrderState.Cancelled && pendMod != null && !pendMod.InTrade && !OppPos(pendMod.Dir) && !OppWork(pendMod.Dir, pendMod)) { Mod pm = pendMod; pendMod = null; SendMarket(pm); }",
 "\t\t\tif (orderState == OrderState.Cancelled && pendMod != null && !pendMod.InTrade && !Working(pendMod.Entry) && !OppPos(pendMod.Dir) && !OppWork(pendMod.Dir, pendMod)) { Mod pm = pendMod; pendMod = null; SendMarket(pm); }"),
# ---- (9) target: latch on equity, un-latch only with the whole account flat (realized balance)
("\t\t\telse if (targetHit && Position.MarketPosition == MarketPosition.Flat && eq - StartBalance < need)\n"
 "\t\t\t{ targetHit = false; Print(string.Format(\"GoldMaster | eval target not met after closing (+{0:0}, needed {1:0}) - trading resumes.\", eq - StartBalance, need)); }",
 "\t\t\telse if (targetHit && Position.MarketPosition == MarketPosition.Flat && Math.Abs(eq - bal) < 0.01)\n\t\t\t{\n"
 "\t\t\t\tdouble needF = EvalTarget;\n"
 "\t\t\t\tif (ConsistencyPct > 0) needF = Math.Max(needF, Math.Max(evBestDay, bal - evDayStart) * 100.0 / ConsistencyPct);\n"
 "\t\t\t\tif (bal - StartBalance < needF) { targetHit = false; Print(string.Format(\"GoldMaster | eval target not met after closing (+{0:0}, needed {1:0}) - trading resumes.\", bal - StartBalance, needF)); }\n\t\t\t}"),
]
patch("GoldMaster", GOLD)
