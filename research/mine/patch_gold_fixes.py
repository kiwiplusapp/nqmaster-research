"""Patch GoldMaster.cs with the code-review fixes (2026-10-06) + two small NQMaster follow-ups.
GoldMaster:
1 conflicts like research (gold_port.conflict_filter): only an opposite POSITION blocks; stop setups blocked by an opposite position /
  working order are parked and re-armed when free (dropped if their level is touched meanwhile or they expire); a market entry that
  meets an opposite working stop parks it and is sent once it is cancelled; fills park (not drop) opposite working entries.
2 realtime: stop level already passed -> market entry (if the target is not passed too); rejected stop/target -> exit the module;
  rejected entry -> module reset; RealtimeErrorHandling = IgnoreAllErrors.
3 account day start / eval day start on the first live session = equity now - realized today.
4 ASIA: first breakout tracked every bar (also when not armed); both sides in one bar -> no trade.
5 warm-up: ATR/trend need 60 RTH days (load >= 120 days), warning in realtime.
6 eval target on equity incl. open P&L + re-check once flat; partial fills; FOMC days count z = 0 in the edge monitor; ENG0610 off by default.
NQMaster: eval day start on the first live session = equity - realized today; ENG10 retry does not chase more than 0.5R;
  target un-latch uses equity incl. open P&L."""
p = r"D:\NinjaTrader Strategy\GoldMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b, cnt=1):
    global s
    n = s.count(a); assert n == cnt, (n, a[:120]); s = s.replace(a, b)
rep("\t\t\tpublic double Sl, Tp;\n\t\t}", "\t\t\tpublic double Sl, Tp;\n\t\t\tpublic bool Def; public double DPx;		// parked stop setup (blocked by an opposite position / order)\n\t\t}")
rep("\t\tprivate double asH, asL; private bool asHas, asBroken;\n",
    "\t\tprivate double asH, asL; private bool asHas, asBroken; private int asFirst, rthDays;\n\t\tprivate Mod pendMod; private int pendBar = -1;\n")
rep("RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;", "RealtimeErrorHandling = RealtimeErrorHandling.IgnoreAllErrors;	// rejections handled in OnOrderUpdate")
rep("UseAsia = true; UseEng0206 = true; UseLate = false;", "UseAsia = true; UseEng0206 = true; UseLate = false;\n\t\t\t\tUseEng0610 = false;")
rep("\t\t\t\tBuildModules();\n\t\t\t}\n\t\t}\n",
    "\t\t\t\tBuildModules();\n\t\t\t}\n\t\t\telse if (State == State.Realtime)\n\t\t\t{\n"
    "\t\t\t\t// enabled mid-day: the day started at equity now minus what the account already realized today\n"
    "\t\t\t\ttry\n\t\t\t\t{\n\t\t\t\t\tdouble rp = Account.Get(AccountItem.RealizedProfitLoss, Currency.UsDollar);\n"
    "\t\t\t\t\tacctDayStart = AcctEquity() - rp; evDayStart = Account.Get(AccountItem.CashValue, Currency.UsDollar) - rp;\n"
    "\t\t\t\t\tif (double.IsNaN(evBestDay)) evBestDay = EvalBestDaySoFar;\n\t\t\t\t}\n\t\t\t\tcatch { }\n"
    "\t\t\t\tif (rthDays < 60) Print(\"GoldMaster | WARNING: only \" + rthDays + \" RTH days loaded - set Days to load >= 120 (ATR / trend warm-up).\");\n"
    "\t\t\t}\n\t\t}\n")
# ---- ASIA first breakout, tracked every bar
rep("\t\t\t\tasH = Math.Max(asH, High[0]); asL = Math.Min(asL, Low[0]);\n\t\t\t}\n",
    "\t\t\t\tasH = Math.Max(asH, High[0]); asL = Math.Min(asL, Low[0]);\n\t\t\t}\n"
    "\t\t\t// ---- first Asian-range breakout 00:00-06:00 (research: the first breakout decides; both sides in one bar = no trade)\n"
    "\t\t\tif (asHas && asFirst == 0 && sm >= S(0) && sm < S(600))\n\t\t\t{\n"
    "\t\t\t\tbool up = High[0] >= asH + TickSize, dn = Low[0] <= asL - TickSize;\n"
    "\t\t\t\tasFirst = up && dn ? 2 : (up ? 1 : (dn ? -1 : 0));\n"
    "\t\t\t\tif (asFirst == 2 && asia.InTrade) ExitModule(asia, \"both Asian sides broken in one bar\");\n\t\t\t}\n")
rep("\t\t\tif (asia.On && Working(asia.Entry) && asia.Dir != 0)\n\t\t\t{\n\t\t\t\t// the opposite side broke first -> no trade today (research: the first breakout decides)\n"
    "\t\t\t\tif ((asia.Dir == 1 && Low[0] <= asL - TickSize) || (asia.Dir == -1 && High[0] >= asH + TickSize)) { CancelOrder(asia.Entry); asBroken = true; }\n\t\t\t}\n",
    "\t\t\t// the opposite side broke first -> no trade today\n"
    "\t\t\tif (asia.On && Working(asia.Entry) && asia.Dir != 0 && asFirst != 0 && asFirst != asia.Dir) { CancelOrder(asia.Entry); asBroken = true; }\n")
rep("\t\t\tif (!AtrOk || trendDir == 0 || asBroken) return;", "\t\t\tif (!AtrOk || trendDir == 0 || asBroken || asFirst != 0) return;")
# ---- parked setups and pending market entry, after CanTrade
rep("\t\t\tif (!CanTrade()) { CancelAllEntries(); UpdateDashboard(); return; }\n",
    "\t\t\tif (!CanTrade()) { CancelAllEntries(); UpdateDashboard(); return; }\n"
    "\t\t\tif (pendMod != null)\n\t\t\t{\n\t\t\t\tMod pm = pendMod;\n"
    "\t\t\t\tif (CurrentBar - pendBar > 1 || pm.InTrade || OppPos(pm.Dir)) pendMod = null;\n"
    "\t\t\t\telse if (!OppWork(pm.Dir, pm)) { pendMod = null; SendMarket(pm); }\n\t\t\t}\n"
    "\t\t\t// parked stop setups: re-arm once no opposite position / order remains; drop if touched meanwhile (research drops a fill\n"
    "\t\t\t// against an open opposite position) or expired\n"
    "\t\t\tforeach (Mod m in mods)\n\t\t\t{\n\t\t\t\tif (!m.Def) continue;\n"
    "\t\t\t\tbool hit = m.Dir == 1 ? High[0] >= m.DPx : Low[0] <= m.DPx;\n"
    "\t\t\t\tif (hit || m.InTrade || (m.ExpireMin >= 0 && sm >= m.ExpireMin - 1) || (m == asia && asFirst != 0)) { m.Def = false; continue; }\n"
    "\t\t\t\tif (!OppPos(m.Dir) && !OppWork(m.Dir, m)) { m.Def = false; StopEntry(m, m.Dir, m.DPx, m.Sl, m.Tp, m.ExpireMin); }\n\t\t\t}\n")
# ---- session reset / warm-up
rep("\t\t\t\tcloses.Add(rthC); while (closes.Count > 20) closes.RemoveAt(0);\n", "\t\t\t\tcloses.Add(rthC); while (closes.Count > 20) closes.RemoveAt(0); rthDays++;\n")
rep("\t\t\tsvPv = 0; svV = 0; odHas = false; asHas = false; asBroken = false;\n", "\t\t\tsvPv = 0; svV = 0; odHas = false; asHas = false; asBroken = false; asFirst = 0; pendMod = null;\n")
rep("\t\t\tforeach (Mod m in mods) { m.Done = false; m.ExpireMin = -1; m.Dir = 0; }\n", "\t\t\tforeach (Mod m in mods) { m.Done = false; m.ExpireMin = -1; m.Dir = 0; m.Def = false; }\n")
rep("return !double.IsNaN(atr) && atr > 0 && closes.Count >= 15; }", "return !double.IsNaN(atr) && atr > 0 && closes.Count >= 15 && rthDays >= 60; }")
rep('status = AtrOk ? "trading" : "warming up (needs ~20 RTH days)";', 'status = AtrOk ? "trading" : "warming up (needs 60 RTH days: Days to load >= 120)";')
# ---- edge monitor: FOMC days count as z = 0 (research)
rep("\t\t\tbool counted = EdgeMonitor && rthHas && !fomcToday && AtrOk && sessionDate > 0;", "\t\t\tbool counted = EdgeMonitor && rthHas && AtrOk && sessionDate > 0;")
rep("\t\t\t\tdouble z = (netPnl - dayStartPnl) / Math.Max(1, Contracts) / (10.0 * atr);", "\t\t\t\tdouble z = fomcToday ? 0.0 : (netPnl - dayStartPnl) / Math.Max(1, Contracts) / (10.0 * atr);")
# ---- orders
rep("""		private bool OppositeBusy(int d)
		{
			if ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return true;
			foreach (Mod m in mods) if (Working(m.Entry) && m.Dir == -d) return true;
			return false;
		}
		private void MarketEntry(Mod m, int d, double sl, double tp)
		{
			if (OppositeBusy(d) || m.InTrade) { Log(m.Sig + " skipped (opposite position / order)"); return; }
			sl = Instrument.MasterInstrument.RoundToTickSize(sl); tp = Instrument.MasterInstrument.RoundToTickSize(tp);
			m.Dir = d; m.Sl = sl; m.Tp = tp;
			SetStopLoss(m.Sig, CalculationMode.Price, sl, false);
			SetProfitTarget(m.Sig, CalculationMode.Price, tp);
			if (d == 1) EnterLong(Contracts, m.Sig); else EnterShort(Contracts, m.Sig);
			Log(string.Format("{0} {1} market | SL {2} TP {3}", m.Sig, d == 1 ? "BUY" : "SELL", Fmt(sl), Fmt(tp)));
		}
		private void StopEntry(Mod m, int d, double px, double sl, double tp, int expireSm)
		{
			if (OppositeBusy(d) || m.InTrade) { Log(m.Sig + " skipped (opposite position / order)"); return; }
			px = Instrument.MasterInstrument.RoundToTickSize(px); sl = Instrument.MasterInstrument.RoundToTickSize(sl); tp = Instrument.MasterInstrument.RoundToTickSize(tp);
			m.Dir = d; m.Sl = sl; m.Tp = tp; m.ExpireMin = expireSm;
			SetStopLoss""",
"""		private bool OppPos(int d) { return Position.MarketPosition == (d == 1 ? MarketPosition.Short : MarketPosition.Long); }
		private bool OppWork(int d, Mod self) { foreach (Mod o in mods) if (o != self && Working(o.Entry) && o.Dir == -d) return true; return false; }
		private void Park(Mod o) { o.Def = true; o.DPx = o.Entry.StopPrice; CancelOrder(o.Entry); Log(o.Sig + " stop order parked (opposite trade)"); }
		private void MarketEntry(Mod m, int d, double sl, double tp)
		{
			if (OppPos(d) || m.InTrade) { Log(m.Sig + " skipped (opposite position)"); return; }
			sl = Instrument.MasterInstrument.RoundToTickSize(sl); tp = Instrument.MasterInstrument.RoundToTickSize(tp);
			m.Dir = d; m.Sl = sl; m.Tp = tp; m.Def = false;
			if (OppWork(d, m))
			{
				// NinjaTrader ignores an entry while an opposite entry order works: park those orders, enter once they are cancelled
				pendMod = m; pendBar = CurrentBar;
				foreach (Mod o in mods) if (o != m && Working(o.Entry) && o.Dir == -d) Park(o);
				return;
			}
			SendMarket(m);
		}
		private void SendMarket(Mod m)
		{
			SetStopLoss(m.Sig, CalculationMode.Price, m.Sl, false);
			SetProfitTarget(m.Sig, CalculationMode.Price, m.Tp);
			if (m.Dir == 1) EnterLong(Contracts, m.Sig); else EnterShort(Contracts, m.Sig);
			Log(string.Format("{0} {1} market | SL {2} TP {3}", m.Sig, m.Dir == 1 ? "BUY" : "SELL", Fmt(m.Sl), Fmt(m.Tp)));
		}
		private void StopEntry(Mod m, int d, double px, double sl, double tp, int expireSm)
		{
			if (m.InTrade) return;
			px = Instrument.MasterInstrument.RoundToTickSize(px); sl = Instrument.MasterInstrument.RoundToTickSize(sl); tp = Instrument.MasterInstrument.RoundToTickSize(tp);
			m.Dir = d; m.Sl = sl; m.Tp = tp; m.ExpireMin = expireSm; m.Def = false;
			if (OppPos(d) || OppWork(d, m)) { m.Def = true; m.DPx = px; Log(m.Sig + " parked (opposite position / order)"); return; }
			if (State == State.Realtime)
			{
				// level already passed (a stop there would be rejected): research fills at the open -> market entry unless the target is passed too
				double mk = double.NaN;
				try { mk = d == 1 ? GetCurrentAsk() : GetCurrentBid(); } catch { }
				if (!double.IsNaN(mk) && (mk - px) * d >= 0) { if ((mk - tp) * d < 0) SendMarket(m); else Log(m.Sig + " skipped (target already passed)"); return; }
			}
			SetStopLoss""")
rep("\t\tprivate void CancelAllEntries() { foreach (Mod m in mods) if (Working(m.Entry)) CancelOrder(m.Entry); }",
    "\t\tprivate void CancelAllEntries() { pendMod = null; foreach (Mod m in mods) { m.Def = false; if (Working(m.Entry)) CancelOrder(m.Entry); } }")
rep("\t\t\tif (orderState == OrderState.Rejected) Print(string.Format(\"GoldMaster | {0} REJECTED: {1} {2}\", order.Name, error, nativeError));\n",
    "\t\t\tif (orderState == OrderState.Rejected)\n\t\t\t{\n\t\t\t\tPrint(string.Format(\"GoldMaster | {0} REJECTED: {1} {2}\", order.Name, error, nativeError));\n"
    "\t\t\t\tMod f = m == null && (order.Name == \"Stop loss\" || order.Name == \"Profit target\") ? BySig(order.FromEntrySignal) : null;\n"
    "\t\t\t\tif (f != null && f.InTrade) ExitModule(f, \"protective order rejected\");\n"
    "\t\t\t\telse if (m != null && !m.InTrade) { m.Dir = 0; m.ExpireMin = -1; m.Def = false; if (pendMod == m) pendMod = null; }\n\t\t\t}\n"
    "\t\t\t// a market entry waiting for an opposite stop order to be cancelled\n"
    "\t\t\tif (orderState == OrderState.Cancelled && pendMod != null && !pendMod.InTrade && !OppPos(pendMod.Dir) && !OppWork(pendMod.Dir, pendMod)) { Mod pm = pendMod; pendMod = null; SendMarket(pm); }\n")
rep("\t\t\t\tif (execution.Order.OrderState != OrderState.Filled) return;\n\t\t\t\tm.InTrade = true; m.EntryBar = CurrentBar;\n",
    "\t\t\t\tif (execution.Order.Filled <= 0) return;\n\t\t\t\tif (m.InTrade) return;			// further partial fills of the same entry\n\t\t\t\tm.InTrade = true; m.EntryBar = CurrentBar; m.Def = false;\n")
rep("\t\t\t\tforeach (Mod o in mods) if (o != m && Working(o.Entry) && o.Dir == -m.Dir) CancelOrder(o.Entry);\n",
    "\t\t\t\tforeach (Mod o in mods) if (o != m && Working(o.Entry) && o.Dir == -m.Dir) Park(o);\n")
# ---- eval target on equity incl. open P&L, re-check once flat
rep("""			if (EvalTarget <= 0 || targetHit || State != State.Realtime) return;
			double bal = Account.Get(AccountItem.CashValue, Currency.UsDollar);
			if (double.IsNaN(evDayStart)) { evDayStart = bal; if (double.IsNaN(evBestDay)) evBestDay = EvalBestDaySoFar; }
			double need = EvalTarget;
			if (ConsistencyPct > 0) need = Math.Max(need, Math.Max(evBestDay, bal - evDayStart) * 100.0 / ConsistencyPct);
			if (bal - StartBalance >= need) { targetHit = true; FlattenAll("eval target"); Print(string.Format("GoldMaster | EVAL TARGET REACHED (+{0:0}, needed {1:0}) - trading stopped.", bal - StartBalance, need)); }""",
"""			if (EvalTarget <= 0 || State != State.Realtime) return;
			double bal = Account.Get(AccountItem.CashValue, Currency.UsDollar), eq = bal + Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar);
			if (double.IsNaN(evDayStart)) { evDayStart = bal; if (double.IsNaN(evBestDay)) evBestDay = EvalBestDaySoFar; }
			double need = EvalTarget;
			if (ConsistencyPct > 0) need = Math.Max(need, Math.Max(evBestDay, eq - evDayStart) * 100.0 / ConsistencyPct);
			if (!targetHit && eq - StartBalance >= need) { targetHit = true; FlattenAll("eval target"); Print(string.Format("GoldMaster | EVAL TARGET REACHED (+{0:0}, needed {1:0}) - trading stopped.", eq - StartBalance, need)); }
			else if (targetHit && Position.MarketPosition == MarketPosition.Flat && eq - StartBalance < need)
			{ targetHit = false; Print(string.Format("GoldMaster | eval target not met after closing (+{0:0}, needed {1:0}) - trading resumes.", eq - StartBalance, need)); }""")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("gold patched")

# ---------------- NQMaster follow-ups
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
rep("\t\t\tif (!double.IsNaN(propDayStart)) { propRestoredDay = today; }\n",
    "\t\t\t// first start of the day (no saved state): the day started at equity now minus what the account already realized today\n"
    "\t\t\tif (double.IsNaN(propDayStart)) { try { propDayStart = PropEquity() - Account.Get(AccountItem.RealizedProfitLoss, Currency.UsDollar); } catch { } }\n"
    "\t\t\tif (!double.IsNaN(propDayStart)) { propRestoredDay = today; }\n")
rep("\t\t\tif (PastLevel(e10d, e10px)) { if (e10d == 1) EnterLong(0, Qty(), eng10.Sig); else EnterShort(0, Qty(), eng10.Sig); }\n",
    "\t\t\tif (PastLevel(e10d, e10px))\n\t\t\t{\n"
    "\t\t\t\tif ((Close[0] - e10px) * e10d > 0.5 * Math.Abs(e10px - e10sl)) { Log(\"ENG10 skipped (price ran > 0.5R past the level)\"); return; }\n"
    "\t\t\t\tif (e10d == 1) EnterLong(0, Qty(), eng10.Sig); else EnterShort(0, Qty(), eng10.Sig);\n\t\t\t}\n")
rep("\t\t\t\tdouble today = double.IsNaN(propDayStart) ? 0 : bal - propDayStart, need = EvalTarget;\n\t\t\t\tif (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);\n\t\t\t\tif (bal < StartBalance + need)",
    "\t\t\t\tdouble eqF = bal + Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar);\n"
    "\t\t\t\tdouble today = double.IsNaN(propDayStart) ? 0 : eqF - propDayStart, need = EvalTarget;\n\t\t\t\tif (ConsistencyPct > 0) need = Math.Max(need, Math.Max(propBestDay, today) * 100.0 / ConsistencyPct);\n\t\t\t\tif (eqF < StartBalance + need)")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("nq patched")
