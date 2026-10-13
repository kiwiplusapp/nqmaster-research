"""2026-10-12 code-audit fixes (research/mine/audit_code_2026-10-12.md) for NQMaster.cs and GoldMaster.cs.
  C1  GoldMaster flattens at 16:00 ET (MFFU auto-closes at 16:10, Lucid at 16:45).
  H1  account vs strategy position check (realtime): a mismatch for 2 bars flattens the instrument on the account, raises an
      alert and stops the strategy (an exit sent for a position the firm already closed would open a reverse position).
  H2  holiday / half-day sessions: session end read with SessionIterator; no new entries in short sessions (SkipShortSessions),
      flatten 5 min before an early close, all entries cancelled at every session start, no entries on a bar processed > 2 min late.
  H3  MaxOpenContracts: open + working contracts (all instruments of the account in realtime) never above the cap.
  M1  2026-10-02 NFP and the 2027 CPI / NFP times added; unreadable NewsTimes / FomcDates entries are printed; warning when
      the news list ends within 35 days.
  M2  realtime: an entry dropped by the stale-order watchdog keeps blocking the opposite direction while it may still be live;
      5 bars (not 2) before an unconfirmed realtime order is dropped.
  M3  a module is 'in trade' until all of its lots are closed (multi-lot entries filled in parts).
  M4  mid-session restart: peak and cushion from the saved day start, not from intraday cash.
  M5  roll guard: no new entries from the NinjaTrader roll date of the chart's contract (MNQ: 8 days before the 3rd-Friday expiry;
      MGC: 7 days before the contract month) - move the strategy to the next contract.
  M6  Alert() + daily log file Documents\\NinjaTrader 8\\nqmaster_logs\\<account>_<date>.txt (realtime), exit fills logged,
      realtime warm-up warning.
  L1  2 rejected orders switch a module off for the session; a rejection mentioning liquidation / disabled / margin stops entries.
  L4  no trading if the Eastern time zone cannot be found.
Writes NQMaster_backup_pre_audit.cs / GoldMaster_backup_pre_audit.cs first. Run from research/mine."""
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NEWS27 = ("2026-10-02 08:30,2027-01-08 08:30,2027-01-13 08:30,2027-02-05 08:30,2027-02-11 08:30,2027-03-05 08:30,2027-03-10 08:30,"
          "2027-04-02 08:30,2027-04-13 08:30,2027-05-07 08:30,2027-05-12 08:30,2027-06-04 08:30,2027-06-10 08:30,2027-07-02 08:30,"
          "2027-07-14 08:30,2027-08-06 08:30,2027-08-11 08:30,2027-09-03 08:30,2027-09-14 08:30,2027-10-08 08:30,2027-10-14 08:30,"
          "2027-11-05 08:30,2027-11-10 08:30,2027-12-03 08:30,2027-12-10 08:30")


def sub(s, a, b, n=1):
    c = s.count(a)
    assert c == n, (a[:90], c, n)
    return s.replace(a, b)


# ------------------------------------------------------------------------------------------------ shared C# helpers
def ops_block(tag, short):
    """tag: NQMaster / GoldMaster; short: 'NQM' / 'GOLD'"""
    cur = "CurrentBars[0]" if tag == "NQMaster" else "CurrentBar"
    return f'''
		// ---- operations layer (2026-10-12 code audit, research/mine/audit_code_2026-10-12.md) ----
		private SessionIterator sessIt; private int sessEndMin = 17 * 60; private bool shortSession, syncArmed, desyncHalt, rejectHalt, rollHalt;
		private int desyncBars, capLogBar = -1, capCuts; private List<Order> rtZombies = new List<Order>();
		private static int SignedQty(NinjaTrader.Cbi.Position p) {{ return p == null || p.MarketPosition == MarketPosition.Flat ? 0 : (p.MarketPosition == MarketPosition.Long ? p.Quantity : -p.Quantity); }}
		// H1: the firm's auto-close, a manual flatten, a restart with a real position or an overfill leave the account and the strategy
		// apart; an exit sent then opens a reverse, unprotected position. 2 bars apart -> flatten this instrument, alert, stop.
		private void CheckAccountSync()
		{{
			if (!AccountSyncGuard || State != State.Realtime || desyncHalt) return;
			int acct, strat;
			try {{ acct = SignedQty(PositionAccount); strat = SignedQty(Position); }} catch {{ return; }}
			if (!syncArmed) {{ if (strat != 0) return; syncArmed = true; }}	// WaitUntilFlat: compare once the simulated history position is closed
			if (acct == strat) {{ desyncBars = 0; return; }}
			if (++desyncBars < 2) return;
			desyncHalt = true;
			try {{ Account.Flatten(new[] {{ Instrument }}); }} catch (Exception ex) {{ Print("{tag} | account flatten failed: " + ex.Message); }}
			Warn("{short}_desync", string.Format("{tag} | ACCOUNT / STRATEGY POSITION MISMATCH for 2 bars: account {{0}}, strategy {{1}} ({{2}}). The account position and orders of this instrument were closed and the strategy stops. Check the Positions / Orders tabs, then enable it again.", acct, strat, Instrument.FullName));
			try {{ SetState(State.Terminated); }} catch {{ }}
		}}
		// H2: real session end (holidays / half days end at 13:00-13:15 ET; NinjaTrader's trading-hours template knows them)
		private void SessionBounds()
		{{
			sessEndMin = 17 * 60; shortSession = false;
			try
			{{
				if (sessIt == null) sessIt = new SessionIterator(Bars);
				sessIt.GetNextSession(Time[0], true);
				DateTime se = ToEt(sessIt.ActualSessionEnd);
				sessEndMin = se.Hour * 60 + se.Minute;
				shortSession = sessEndMin >= 9 * 60 && sessEndMin < 16 * 60;
			}}
			catch {{ }}
			if (shortSession) Log(string.Format("short session (holiday / half day): the market closes {{0:00}}:{{1:00}} ET{{2}}", sessEndMin / 60, sessEndMin % 60, SkipShortSessions ? " - no new entries this session" : ""));
			rollHalt = State == State.Realtime && RollDue();
			if (rollHalt) Warn("{short}_roll", "{tag} | ROLL DATE reached for " + Instrument.FullName + ": no new entries. Move the strategy to the next contract (same settings).");
		}}
		private int FlatMin {{ get {{ int f = FlattenTime > 0 ? Hm(FlattenTime) : 24 * 60; return shortSession ? Math.Min(f, sessEndMin - 5) : f; }} }}
		private bool LateBar(DateTime barTime) {{ try {{ return State == State.Realtime && (Core.Globals.Now - barTime).TotalSeconds > 120; }} catch {{ return false; }} }}
		// H3: open + working contracts (realtime: every instrument of the account, so MNQ and MGC together) never above MaxOpenContracts
		private int OpenAndWorking(object self)
		{{
			int n = Position.MarketPosition == MarketPosition.Flat ? 0 : Position.Quantity;
			foreach (Mod m in mods) if ((object)m != self && Working(m.Entry) && !zombies.Contains(m.Entry)) n += Math.Max(0, m.Entry.Quantity - m.Entry.Filled);
			if (State == State.Realtime)
			{{
				try {{ lock (Account.Positions) foreach (NinjaTrader.Cbi.Position p in Account.Positions) if (p.Instrument != Instrument && p.MarketPosition != MarketPosition.Flat) n += p.Quantity; }} catch {{ }}
			}}
			return n;
		}}
		private int CapQty(object self, string who, int q)
		{{
			if (MaxOpenContracts <= 0 || q <= 0) return q;
			int room = MaxOpenContracts - OpenAndWorking(self);
			if (q <= room) return q;
			int nq = Math.Max(0, room); capCuts++;
			if (capLogBar != {cur}) {{ capLogBar = {cur}; Log(string.Format("{{0}} size {{1}} -> {{2}} (max open contracts {{3}})", who, q, nq, MaxOpenContracts)); }}
			return nq;
		}}
		// M2: in realtime an order the watchdog gave up on may still rest at the exchange -> it keeps blocking the opposite direction
		private bool RtZombieOpp(int d)
		{{
			foreach (Order z in rtZombies) if (Working(z) && (z.OrderAction == OrderAction.Buy ? 1 : -1) == -d) return true;
			return false;
		}}
		private void RejectSeen(string nativeError)
		{{
			string ne = (nativeError ?? "").ToLowerInvariant();
			if (!rejectHalt && (ne.Contains("liquidat") || ne.Contains("disabled") || ne.Contains("margin") || ne.Contains("not allowed") || ne.Contains("locked")))
			{{ rejectHalt = true; Warn("{short}_rejhalt", "{tag} | the account refuses orders (" + nativeError + "): no new entries this session."); }}
		}}
		// M6: important events also go to an alert and to Documents\\NinjaTrader 8\\nqmaster_logs\\<account>_<date>.txt
		private void LogFile(string line)
		{{
			if (!LogToFile || State != State.Realtime) return;
			try
			{{
				string dir = Path.Combine(Core.Globals.UserDataDir, "nqmaster_logs"); Directory.CreateDirectory(dir);
				File.AppendAllText(Path.Combine(dir, (Account != null ? Account.Name : "acct") + "_" + DateTime.Now.ToString("yyyyMMdd", CultureInfo.InvariantCulture) + ".txt"),
					DateTime.Now.ToString("HH:mm:ss", CultureInfo.InvariantCulture) + " " + line + Environment.NewLine);
			}}
			catch {{ }}
		}}
		private void Warn(string id, string msg)
		{{
			Print(msg);
			if (State != State.Realtime) return;
			LogFile(msg);
			try {{ Alert(id, Priority.High, msg, NinjaTrader.Core.Globals.InstallDir + @"\\sounds\\Alert1.wav", 60, Brushes.Red, Brushes.White); }} catch {{ }}
		}}
		private void NewsListCheck()
		{{
			if (!NewsBlackout || newsEt == null) return;
			DateTime last = DateTime.MinValue; foreach (DateTime e in newsEt) if (e.Hour == 8 && e > last) last = e;
			if ((last - ToEt(Core.Globals.Now)).TotalDays < 35) Warn("{short}_news", "{tag} | NEWS LIST ends " + last.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture) + ": add the next CPI / NFP times (bls.gov) in 'Extra Tier-1 times'.");
		}}
'''


OPS_PROPS = '''		[NinjaScriptProperty][Display(Name = "Account sync guard: account and strategy position apart 2 bars -> flatten this instrument and stop (off if anything else trades it on this account)", Order = 1, GroupName = "{g}")] public bool AccountSyncGuard {{ get; set; }}
		[NinjaScriptProperty][Display(Name = "Skip holiday / half-day sessions (early close)", Order = 2, GroupName = "{g}")] public bool SkipShortSessions {{ get; set; }}
		[NinjaScriptProperty][Range(0, 500)][Display(Name = "Max open contracts, whole account (Lucid 50K funded 20, MFFU 50K 30; 0 = off)", Order = 3, GroupName = "{g}")] public int MaxOpenContracts {{ get; set; }}
		[NinjaScriptProperty][Display(Name = "Roll guard: no new entries from the roll date of the chart's contract", Order = 4, GroupName = "{g}")] public bool RollGuard {{ get; set; }}
		[NinjaScriptProperty][Display(Name = "Log file (Documents\\\\NinjaTrader 8\\\\nqmaster_logs, realtime)", Order = 5, GroupName = "{g}")] public bool LogToFile {{ get; set; }}
'''


def patch_nq(s):
    s = sub(s, "\t\t\tpublic int OfQ0, OfWant; public Order OfChangeOrd, OfNoChange; public int OfChangeBar = -1;	// order-flow boost: size before the boost, last re-size\n",
            "\t\t\tpublic int OfQ0, OfWant; public Order OfChangeOrd, OfNoChange; public int OfChangeBar = -1;	// order-flow boost: size before the boost, last re-size\n"
            "\t\t\tpublic int OpenQty, RejToday;	// lots still open (multi-lot entries close in parts), rejected orders this session\n")
    # news list
    s = sub(s, "// CPI / NFP from the BLS schedules (2024 - Dec 2026; 2027 not published yet: add them in NewsTimes), minutes = decision + 21 days.",
            "// CPI / NFP from the BLS schedules (2024 - Dec 2027; 2027 schedule published 2026-10-09), minutes = decision + 21 days.")
    s = sub(s, '2027-12-29 14:00";\n\t\tprivate List<DateTime> newsEt; private bool profUltra, volbBeSet;',
            '2027-12-29 14:00,' + NEWS27 + '";\n\t\tprivate List<DateTime> newsEt; private bool profUltra, volbBeSet;')
    s = sub(s, "\t\tprivate string status = \"waiting\";\n", "\t\tprivate string status = \"waiting\";\n" + ops_block("NQMaster", "nqm"))
    # defaults
    s = sub(s, "\t\t\t\tWarmupDays = 15;\n", "\t\t\t\tWarmupDays = 15;\n\t\t\t\tAccountSyncGuard = true; SkipShortSessions = true; MaxOpenContracts = 20; RollGuard = true; LogToFile = true;\n")
    # data loaded: time zone, unreadable entries, session iterator
    s = sub(s, "\t\t\t\ttry { etZone = TimeZoneInfo.FindSystemTimeZoneById(\"Eastern Standard Time\"); } catch { etZone = null; }\n\t\t\t\tbadTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);\n\t\t\t\tif (badTimeframe) Print(\"NQMaster | Needs a 1-MINUTE chart (CME US Index Futures ETH).\");\n",
            "\t\t\t\ttry { etZone = TimeZoneInfo.FindSystemTimeZoneById(\"Eastern Standard Time\"); } catch { etZone = null; }\n\t\t\t\tbadTimeframe = !(BarsPeriod.BarsPeriodType == BarsPeriodType.Minute && BarsPeriod.Value == 1);\n\t\t\t\tif (badTimeframe) Print(\"NQMaster | Needs a 1-MINUTE chart (CME US Index Futures ETH).\");\n"
            "\t\t\t\tif (etZone == null) { badTimeframe = true; Print(\"NQMaster | Windows time zone 'Eastern Standard Time' not found: every module uses ET clock times, so the strategy does not trade.\"); }\n"
            "\t\t\t\ttry { sessIt = new SessionIterator(Bars); } catch { sessIt = null; }\n")
    s = sub(s, "\t\t\t\t\tif (DateTime.TryParseExact(raw.Trim(), \"yyyy-MM-dd\", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) fomc.Add(d.Year * 10000 + d.Month * 100 + d.Day);\n",
            "\t\t\t\t\tif (DateTime.TryParseExact(raw.Trim(), \"yyyy-MM-dd\", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) fomc.Add(d.Year * 10000 + d.Month * 100 + d.Day);\n"
            "\t\t\t\t\telse Print(\"NQMaster | FOMC dates: cannot read '\" + raw.Trim() + \"' (format yyyy-MM-dd)\");\n")
    s = sub(s, "\t\t\t\t\tif (DateTime.TryParseExact(raw.Trim(), \"yyyy-MM-dd HH:mm\", CultureInfo.InvariantCulture, DateTimeStyles.None, out nt)) newsEt.Add(nt);\n",
            "\t\t\t\t\tif (DateTime.TryParseExact(raw.Trim(), \"yyyy-MM-dd HH:mm\", CultureInfo.InvariantCulture, DateTimeStyles.None, out nt)) newsEt.Add(nt);\n"
            "\t\t\t\t\telse Print(\"NQMaster | news times: cannot read '\" + raw.Trim() + \"' (format yyyy-MM-dd HH:mm, 24 h, e.g. 2027-01-08 08:30)\");\n")
    # realtime switch: warnings
    s = sub(s, "\t\t\t\teqPeak = netPnl;	// adaptive size measures the drawdown from the moment the strategy goes live\n\t\t\t\tPropGoLive();\n",
            "\t\t\t\teqPeak = netPnl;	// adaptive size measures the drawdown from the moment the strategy goes live\n\t\t\t\tPropGoLive();\n"
            "\t\t\t\tsyncArmed = false; desyncBars = 0; NewsListCheck();\n"
            "\t\t\t\tif (atrCount < AtrMin || rthDaysSeen < WarmupDays) Warn(\"nqm_warmup\", string.Format(\"NQMaster | WARNING: only {0} RTH days loaded, the warm-up needs {1}: modules stay idle until then (set Days to load >= 45).\", rthDaysSeen, WarmupDays));\n"
            "\t\t\t\trollHalt = RollDue(); if (rollHalt) Warn(\"nqm_roll\", \"NQMaster | ROLL DATE reached for \" + Instrument.FullName + \": no new entries. Move the strategy to the next contract (same settings).\");\n"
            "\t\t\t\tLog(string.Format(\"LIVE on {0} | profile {1} | contracts {2} | prop {3} | max open contracts {4} | account sync guard {5}\", Instrument.FullName, Profile, Contracts, PropMode, MaxOpenContracts, AccountSyncGuard ? \"on\" : \"off\"));\n")
    # bar update: sync check, session start
    s = sub(s, "\t\t\tProcessClosedTrades();\n\t\t\tPurgeStaleEntries();\n\n\t\t\tif (Bars.IsFirstBarOfSession)\n\t\t\t{\n\t\t\t\tEdgeDayClose(etOpen);\n",
            "\t\t\tProcessClosedTrades();\n\t\t\tPurgeStaleEntries();\n\t\t\tCheckAccountSync();\n\t\t\tif (desyncHalt) return;\n\n\t\t\tif (Bars.IsFirstBarOfSession)\n\t\t\t{\n"
            "\t\t\t\tCancelAllEntries();                                  // nothing from the last session survives (half days: no 15:56 cancel)\n"
            "\t\t\t\tforeach (Order z in rtZombies) { try { if (Working(z)) CancelOrder(z); } catch { } }\n\t\t\t\trtZombies.Clear(); rejectHalt = false;\n"
            "\t\t\t\tSessionBounds();\n\t\t\t\tEdgeDayClose(etOpen);\n")
    s = sub(s, "\t\t\tif (FlattenTime > 0 && closeMin >= Hm(FlattenTime) && closeMin < 18 * 60) { FlattenAll(\"end of day\"); UpdateDashboard(); return; }\n",
            "\t\t\tif (closeMin >= FlatMin && closeMin < 18 * 60) { FlattenAll(shortSession ? \"early close (holiday / half day)\" : \"end of day\"); UpdateDashboard(); return; }\n")
    s = sub(s, "\t\t\tbool canTrade = CanTrade();\n\t\t\tif (!canTrade) { CancelAllEntries(); UpdateDashboard(); return; }\n",
            "\t\t\tbool canTrade = CanTrade();\n\t\t\tif (!canTrade) { CancelAllEntries(); UpdateDashboard(); return; }\n"
            "\t\t\tif (LateBar(Time[0])) { Log(\"bar processed late (session break / data gap): no new entries on it\"); UpdateDashboard(); return; }\n")
    # 5-minute series
    s = sub(s, "\t\t\tif (etDate != rthDay || !CanTrade()) return;\n\t\t\tif (FlattenTime > 0 && closeMin >= Hm(FlattenTime)) return;\n",
            "\t\t\tif (desyncHalt || etDate != rthDay || !CanTrade() || LateBar(Times[1][0])) return;\n\t\t\tif (closeMin >= FlatMin) return;\n")
    # session reset of module rejections
    s = sub(s, "\t\t\tforeach (Mod m in mods) m.Parked = false;\n\t\t\tpend5 = null;\n", "\t\t\tforeach (Mod m in mods) { m.Parked = false; m.RejToday = 0; }\n\t\t\tpend5 = null;\n")
    # CanTrade
    s = sub(s, "\t\tprivate bool CanTrade()\n\t\t{\n\t\t\tif (newsBlock5 && BarsInProgress == 1) { status = \"NEWS BLACKOUT\"; return false; }\n",
            "\t\tprivate bool CanTrade()\n\t\t{\n"
            "\t\t\tif (desyncHalt) { status = \"ACCOUNT / STRATEGY POSITION MISMATCH - see Output\"; return false; }\n"
            "\t\t\tif (rejectHalt) { status = \"the account refuses orders - see Output\"; return false; }\n"
            "\t\t\tif (SkipShortSessions && shortSession) { status = \"holiday / half-day session: no trading\"; return false; }\n"
            "\t\t\tif (rollHalt) { status = \"ROLL DATE: move the strategy to the next contract\"; return false; }\n"
            "\t\t\tif (newsBlock5 && BarsInProgress == 1) { status = \"NEWS BLACKOUT\"; return false; }\n")
    # alerts on key events
    s = sub(s, "Print(string.Format(\"NQMaster | EVAL TARGET REACHED (+{0:0}, needed {1:0}) - trading stopped.\", bal - StartBalance, need));",
            "Warn(\"nqm_target\", string.Format(\"NQMaster | EVAL TARGET REACHED (+{0:0}, needed {1:0}) - trading stopped.\", bal - StartBalance, need));")
    s = sub(s, "Print(\"NQMaster | DRAWDOWN GUARD - trading stopped.\");", "Warn(\"nqm_dd\", \"NQMaster | DRAWDOWN GUARD - trading stopped.\");")
    s = sub(s, "\t\t\t\t\tPrint(string.Format(\"NQMaster | EDGE MONITOR ALARM {0}:", "\t\t\t\t\tWarn(\"nqm_edge\", string.Format(\"NQMaster | EDGE MONITOR ALARM {0}:")
    # exits never sent while the account and the strategy disagree
    s = sub(s, "\t\tprivate void ExitModule(Mod m, string why)\n\t\t{\n", "\t\tprivate void ExitModule(Mod m, string why)\n\t\t{\n\t\t\tif (desyncHalt) return;\n")
    s = sub(s, "\t\tprivate void FlattenAll(string why)\n\t\t{\n\t\t\tCancelAllEntries();\n", "\t\tprivate void FlattenAll(string why)\n\t\t{\n\t\t\tCancelAllEntries();\n\t\t\tif (desyncHalt) return;\n")
    # opposite-direction checks include realtime zombies
    s = sub(s, "\t\t\tif ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return false;\n\t\t\t// an opposite MARKET entry",
            "\t\t\tif ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return false;\n\t\t\tif (RtZombieOpp(d)) return false;\n\t\t\t// an opposite MARKET entry")
    s = sub(s, "\t\t\tforeach (Mod o in mods) if (o != self && Working(o.Entry) && o.Dir == -d) return true;\n\t\t\treturn false;\n",
            "\t\t\tforeach (Mod o in mods) if (o != self && Working(o.Entry) && o.Dir == -d) return true;\n\t\t\treturn RtZombieOpp(d);\n")
    s = sub(s, "\t\t\tforeach (Mod o in mods) if (o != volb && Working(o.Entry) && o.Dir == -d) return;\n",
            "\t\t\tforeach (Mod o in mods) if (o != volb && Working(o.Entry) && o.Dir == -d) return;\n\t\t\tif (RtZombieOpp(d)) return;\n")
    # watchdog: 5 bars in realtime, realtime zombies keep blocking
    s = sub(s, "\t\t\t\tif (m.CancelOrd == e && CurrentBars[0] - m.CancelBar >= 2) why = \"cancel never confirmed\";\n\t\t\t\telse if (age >= 2 && (s == OrderState.Initialized || s == OrderState.Submitted)) why = \"never accepted\";\n\t\t\t\telse if (age >= 2 && e.OrderType == OrderType.Market && s != OrderState.PartFilled) why = \"market entry never filled\";\n",
            "\t\t\t\tint lim = State == State.Realtime ? 5 : 2;\n"
            "\t\t\t\tif (m.CancelOrd == e && CurrentBars[0] - m.CancelBar >= lim) why = \"cancel never confirmed\";\n\t\t\t\telse if (age >= lim && (s == OrderState.Initialized || s == OrderState.Submitted)) why = \"never accepted\";\n\t\t\t\telse if (age >= lim && e.OrderType == OrderType.Market && s != OrderState.PartFilled) why = \"market entry never filled\";\n")
    s = sub(s, "\t\t\tzombies.Add(e); zombieCount++;\n\t\t\tm.Entry = null; m.SeenOrd = null; m.CancelOrd = null;\n\t\t\tPrint(string.Format(\"{0} | NQMaster | STALE ORDER dropped",
            "\t\t\tzombies.Add(e); zombieCount++;\n\t\t\tif (State == State.Realtime) { rtZombies.Add(e); Warn(\"nqm_stale\", \"NQMaster | STALE ORDER in realtime: \" + m.Sig + \" \" + e.OrderAction + \" \" + e.OrderType + \" - check the Orders tab; it keeps blocking the opposite direction while it may be live.\"); }\n"
            "\t\t\tm.Entry = null; m.SeenOrd = null; m.CancelOrd = null;\n\t\t\tPrint(string.Format(\"{0} | NQMaster | STALE ORDER dropped")
    # rejections
    s = sub(s, "\t\t\t\tPrint(string.Format(\"NQMaster | {0} REJECTED: {1} {2}\", order.Name, error, nativeError));\n",
            "\t\t\t\tWarn(\"nqm_rej\", string.Format(\"NQMaster | {0} REJECTED: {1} {2}\", order.Name, error, nativeError));\n"
            "\t\t\t\tif (m != null && ++m.RejToday == 2) Log(m.Sig + \" off for the rest of the session (2 rejected orders)\");\n\t\t\t\tRejectSeen(nativeError);\n")
    # M3 open lots per module + exit logging
    s = sub(s, "\t\t\t\tbool first = !m.InTrade;\n\t\t\t\tm.InTrade = true; m.EntryPx = execution.Order.AverageFillPrice;\n",
            "\t\t\t\tbool first = !m.InTrade;\n\t\t\t\tm.InTrade = true; m.EntryPx = execution.Order.AverageFillPrice; m.OpenQty += quantity;\n")
    s = sub(s, "\t\t\tif (from != null && execution.Order.OrderState == OrderState.Filled) from.InTrade = false;\n",
            "\t\t\tif (from != null)\n\t\t\t{\n\t\t\t\tfrom.OpenQty = Math.Max(0, from.OpenQty - quantity); if (from.OpenQty == 0) from.InTrade = false;\n"
            "\t\t\t\tLog(string.Format(\"{0} exit fill: {1} x{2} @ {3}{4}\", from.Sig, execution.Order.Name, quantity, Fmt(price), State == State.Realtime ? string.Format(\" | account cash {0:0}\", Account.Get(AccountItem.CashValue, Currency.UsDollar)) : \"\"));\n\t\t\t}\n")
    s = sub(s, "\t\t\tif (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) x.InTrade = false;\n",
            "\t\t\tif (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) { x.InTrade = false; x.OpenQty = 0; }\n", n=2)
    # H3 + L1: every entry size goes through OfApply -> cap and per-module rejections; call sites skip a 0 size
    s = sub(s, "\t\tprivate int OfApply(Mod m, int q, int d) { m.OfQ0 = q; return OfQty(q, d, m.Sig); }",
            "\t\tprivate int OfApply(Mod m, int q, int d) { m.OfQ0 = q; if (m.RejToday >= 2) return 0; return CapQty(m, m.Sig, OfQty(q, d, m.Sig)); }")
    reps = [
        ("Order po = pend5Dir == 1 ? EnterLong(0, pq, pend5.Sig) : EnterShort(0, pq, pend5.Sig);", "Order po = pq <= 0 ? null : (pend5Dir == 1 ? EnterLong(0, pq, pend5.Sig) : EnterShort(0, pq, pend5.Sig));"),
        ("Order r = d == 1 ? (through ? EnterLong(0, oq, o.Sig) : EnterLongStopMarket(0, true, oq, entry, o.Sig)) : (through ? EnterShort(0, oq, o.Sig) : EnterShortStopMarket(0, true, oq, entry, o.Sig));",
         "if (oq <= 0) { o.Trades = 2; return; }\n\t\t\tOrder r = d == 1 ? (through ? EnterLong(0, oq, o.Sig) : EnterLongStopMarket(0, true, oq, entry, o.Sig)) : (through ? EnterShort(0, oq, o.Sig) : EnterShortStopMarket(0, true, oq, entry, o.Sig));"),
        ("Order vm = d == 1 ? EnterLong(0, vq, volb.Sig) : EnterShort(0, vq, volb.Sig);", "Order vm = vq <= 0 ? null : (d == 1 ? EnterLong(0, vq, volb.Sig) : EnterShort(0, vq, volb.Sig));"),
        ("Order vr = d == 1 ? EnterLongStopMarket(0, true, vsq, lvl, volb.Sig) : EnterShortStopMarket(0, true, vsq, lvl, volb.Sig);", "if (vsq <= 0) return;\n\t\t\tOrder vr = d == 1 ? EnterLongStopMarket(0, true, vsq, lvl, volb.Sig) : EnterShortStopMarket(0, true, vsq, lvl, volb.Sig);"),
        ("Order em = e10d == 1 ? EnterLong(0, eq, eng10.Sig) : EnterShort(0, eq, eng10.Sig);", "Order em = eq <= 0 ? null : (e10d == 1 ? EnterLong(0, eq, eng10.Sig) : EnterShort(0, eq, eng10.Sig));"),
        ("Order er = e10d == 1 ? EnterLongStopMarket(0, true, esq, e10px, eng10.Sig) : EnterShortStopMarket(0, true, esq, e10px, eng10.Sig);", "Order er = esq <= 0 ? null : (e10d == 1 ? EnterLongStopMarket(0, true, esq, e10px, eng10.Sig) : EnterShortStopMarket(0, true, esq, e10px, eng10.Sig));"),
        ("Order tr = d == 1 ? EnterLong(0, tq, m.Sig) : EnterShort(0, tq, m.Sig);", "if (tq <= 0) return;\n\t\t\tOrder tr = d == 1 ? EnterLong(0, tq, m.Sig) : EnterShort(0, tq, m.Sig);"),
        ("Order cr = d == 1 ? EnterLong(0, cq, crt.Sig) : EnterShort(0, cq, crt.Sig);", "if (cq <= 0) return;\n\t\t\tOrder cr = d == 1 ? EnterLong(0, cq, crt.Sig) : EnterShort(0, cq, crt.Sig);"),
        ("Order lr = lon.Dir == 1 ? EnterLongLimit(0, true, lq, lim, lon.Sig) : EnterShortLimit(0, true, lq, lim, lon.Sig);", "if (lq <= 0) { lonStage = 3; return; }\n\t\t\t\tOrder lr = lon.Dir == 1 ? EnterLongLimit(0, true, lq, lim, lon.Sig) : EnterShortLimit(0, true, lq, lim, lon.Sig);"),
        ("Order mo = EnterLong(0, OfApply(mseq, mq, 1), mseq.Sig);", "int mq2 = OfApply(mseq, mq, 1); Order mo = mq2 <= 0 ? null : EnterLong(0, mq2, mseq.Sig);"),
        ("Order so = EnterShort(0, OfApply(mseqs, sq, -1), mseqs.Sig);", "int sq2 = OfApply(mseqs, sq, -1); Order so = sq2 <= 0 ? null : EnterShort(0, sq2, mseqs.Sig);"),
        ("Order rr = d == 1 ? EnterLong(0, rq, rsi.Sig) : EnterShort(0, rq, rsi.Sig);", "Order rr = rq <= 0 ? null : (d == 1 ? EnterLong(0, rq, rsi.Sig) : EnterShort(0, rq, rsi.Sig));"),
        ("Order ir = d == 1 ? EnterLongLimit(0, true, iqo, lim, ict.Sig) : EnterShortLimit(0, true, iqo, lim, ict.Sig);", "Order ir = iqo <= 0 ? null : (d == 1 ? EnterLongLimit(0, true, iqo, lim, ict.Sig) : EnterShortLimit(0, true, iqo, lim, ict.Sig));"),
        ("\t\t\t\tint pkq = OfApply(o, o.ParkQty, o.Dir);\n", "\t\t\t\tint pkq = OfApply(o, o.ParkQty, o.Dir);\n\t\t\t\tif (pkq <= 0) { o.Parked = true; continue; }		// no room under the contract cap yet\n"),
    ]
    for a, b in reps: s = sub(s, a, b)
    # M4: mid-session restart -> peak and cushion from the saved day start
    s = sub(s, "\t\t\t\tif (propRestoredDay == tday && !double.IsNaN(propDayStart)) { }                  // restarted mid-session: keep the saved day start\n",
            "\t\t\t\tbool restored = propRestoredDay == tday && !double.IsNaN(propDayStart);\n"
            "\t\t\t\tif (restored) { }                  // restarted mid-session: keep the saved day start\n")
    s = sub(s, "\t\t\t\tif (eq > propPeak) propPeak = eq;\n\t\t\t\tPropSave(tday);\n",
            "\t\t\t\tdouble eqRef = restored ? propDayStart : eq;			// intraday cash is not an end-of-day balance\n\t\t\t\tif (eqRef > propPeak) propPeak = eqRef;\n\t\t\t\tPropSave(tday);\n")
    s = sub(s, "\t\t\t\tpropCushion = eq - propThr;\n", "\t\t\t\tpropCushion = eqRef - propThr;\n")
    # roll date (CME equity index: Thursday 8 days before the 3rd-Friday expiry)
    s = sub(s, "\t\tprivate int FlatMin {",
            "\t\tprivate bool RollDue()\n\t\t{\n\t\t\tif (!RollGuard) return false;\n\t\t\ttry\n\t\t\t{\n"
            "\t\t\t\tif (Instrument.MasterInstrument.InstrumentType != InstrumentType.Future) return false;\n"
            "\t\t\t\tDateTime ex = Instrument.Expiry; if (ex.Year < 2000) return false;\n"
            "\t\t\t\tDateTime first = new DateTime(ex.Year, ex.Month, 1);\n"
            "\t\t\t\tDateTime roll = first.AddDays(((int)DayOfWeek.Friday - (int)first.DayOfWeek + 7) % 7 + 14 - 8);\n"
            "\t\t\t\treturn ToEt(Core.Globals.Now).Date >= roll.Date;\n\t\t\t}\n\t\t\tcatch { return false; }\n\t\t}\n"
            "\t\tprivate int FlatMin {")
    # log file
    s = sub(s, "\t\tprivate void Log(string m) { if (PrintLog) Print(string.Format(\"{0} | NQM | {1}\", Times[0][0].ToString(\"yyyy-MM-dd HH:mm\", CultureInfo.InvariantCulture), m)); }",
            "\t\tprivate void Log(string m)\n\t\t{\n\t\t\tstring line = string.Format(\"{0} | NQM | {1}\", Times[0][0].ToString(\"yyyy-MM-dd HH:mm\", CultureInfo.InvariantCulture), m);\n"
            "\t\t\tif (PrintLog) Print(line);\n\t\t\tLogFile(line);\n\t\t}")
    # dashboard
    s = sub(s, "\t\t\tif (zombieCount > 0) txt += string.Format(\"\\nStale orders dropped: {0} (see Output)\", zombieCount);\n\t\t\tif (UseOrderFlowBoost) txt += \"\\n\" + OfStatus();\n",
            "\t\t\tif (zombieCount > 0) txt += string.Format(\"\\nStale orders dropped: {0} (see Output)\", zombieCount);\n"
            "\t\t\tif (capCuts > 0) txt += string.Format(\"\\nMax open contracts {0}: {1} entries cut\", MaxOpenContracts, capCuts);\n"
            "\t\t\tif (shortSession) txt += string.Format(\"\\nShort session: closes {0:00}:{1:00} ET\", sessEndMin / 60, sessEndMin % 60);\n"
            "\t\t\tif (UseOrderFlowBoost) txt += \"\\n\" + OfStatus();\n")
    # properties
    s = sub(s, "\t\t[NinjaScriptProperty][Range(0.0, 1.0)][Display(Name = \"Min stop for structure modules",
            OPS_PROPS.format(g="10. Operations (safety)") + "\t\t[NinjaScriptProperty][Range(0.0, 1.0)][Display(Name = \"Min stop for structure modules")
    return s


def patch_gold(s):
    s = sub(s, "\t\t\tpublic bool Def; public double DPx; public int Q = 1;		// parked stop setup (blocked by an opposite position / order)\n",
            "\t\t\tpublic bool Def; public double DPx; public int Q = 1;		// parked stop setup (blocked by an opposite position / order)\n"
            "\t\t\tpublic int OpenQty, RejToday;	// lots still open, rejected orders this session\n")
    s = sub(s, '2027-12-29 14:00";\n\t\tprivate List<DateTime> newsEt;', '2027-12-29 14:00,' + NEWS27 + '";\n\t\tprivate List<DateTime> newsEt;')
    s = sub(s, "\t\tprivate int flattenBar = -1; private string status = \"waiting\";\n",
            "\t\tprivate int flattenBar = -1; private string status = \"waiting\";\n" + ops_block("GoldMaster", "gold"))
    # C1: flatten before the firms' cutoffs (MFFU 16:10, Lucid 16:45)
    s = sub(s, "\t\t\t\tContracts = 1; FlattenTime = 1651; SkipFomc = true; FomcDates = \"\";\n",
            "\t\t\t\tContracts = 1; FlattenTime = 1600; SkipFomc = true; FomcDates = \"\";	// 1600: MFFU auto-closes at 16:10 ET, Lucid at 16:45 (was 1651)\n"
            "\t\t\t\tAccountSyncGuard = true; SkipShortSessions = true; MaxOpenContracts = 20; RollGuard = true; LogToFile = true;\n")
    s = sub(s, "\t\t\t\tif (badTimeframe) Print(\"GoldMaster | Needs a 1-MINUTE MGC chart.\");\n",
            "\t\t\t\tif (badTimeframe) Print(\"GoldMaster | Needs a 1-MINUTE MGC chart.\");\n"
            "\t\t\t\tif (etZone == null) { badTimeframe = true; Print(\"GoldMaster | Windows time zone 'Eastern Standard Time' not found: the strategy does not trade.\"); }\n"
            "\t\t\t\ttry { sessIt = new SessionIterator(Bars); } catch { sessIt = null; }\n")
    s = sub(s, "\t\t\t\t\tif (DateTime.TryParseExact(raw.Trim(), \"yyyy-MM-dd\", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) fomc.Add(d.Year * 10000 + d.Month * 100 + d.Day);\n",
            "\t\t\t\t\tif (DateTime.TryParseExact(raw.Trim(), \"yyyy-MM-dd\", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) fomc.Add(d.Year * 10000 + d.Month * 100 + d.Day);\n"
            "\t\t\t\t\telse Print(\"GoldMaster | FOMC dates: cannot read '\" + raw.Trim() + \"' (format yyyy-MM-dd)\");\n")
    s = sub(s, "\t\t\t\t\tif (DateTime.TryParseExact(raw.Trim(), \"yyyy-MM-dd HH:mm\", CultureInfo.InvariantCulture, DateTimeStyles.None, out nt)) newsEt.Add(nt);\n",
            "\t\t\t\t\tif (DateTime.TryParseExact(raw.Trim(), \"yyyy-MM-dd HH:mm\", CultureInfo.InvariantCulture, DateTimeStyles.None, out nt)) newsEt.Add(nt);\n"
            "\t\t\t\t\telse Print(\"GoldMaster | news times: cannot read '\" + raw.Trim() + \"' (format yyyy-MM-dd HH:mm, 24 h, e.g. 2027-01-08 08:30)\");\n")
    s = sub(s, "\t\t\t\tif (rthDays < WarmupDays) Print(\"GoldMaster | WARNING: only \" + rthDays + \" RTH days loaded, warm-up needs \" + WarmupDays + \" - set Days to load >= \" + (2 * WarmupDays) + \" or lower 'Warm-up days'.\");\n",
            "\t\t\t\tif (rthDays < WarmupDays) Warn(\"gold_warmup\", \"GoldMaster | WARNING: only \" + rthDays + \" RTH days loaded, warm-up needs \" + WarmupDays + \" - set Days to load >= \" + (2 * WarmupDays) + \" or lower 'Warm-up days'.\");\n"
            "\t\t\t\tsyncArmed = false; desyncBars = 0; NewsListCheck();\n"
            "\t\t\t\trollHalt = RollDue(); if (rollHalt) Warn(\"gold_roll\", \"GoldMaster | ROLL DATE reached for \" + Instrument.FullName + \": no new entries. Move the strategy to the next contract (same settings).\");\n"
            "\t\t\t\tif (FlattenTime > 1609) Warn(\"gold_flat\", \"GoldMaster | Flatten time \" + FlattenTime + \" ET is after MyFundedFutures' 16:10 auto-close: use 1600.\");\n")
    s = sub(s, "\t\t\tProcessClosedTrades();\n\t\t\tPurgeStaleEntries();\n\t\t\tif (prevSm < 0 || sm < prevSm) NewSession(etOpen);\n",
            "\t\t\tProcessClosedTrades();\n\t\t\tPurgeStaleEntries();\n\t\t\tCheckAccountSync();\n\t\t\tif (desyncHalt) return;\n\t\t\tif (prevSm < 0 || sm < prevSm) NewSession(etOpen);\n")
    s = sub(s, "\t\tprivate void NewSession(DateTime etOpen)\n\t\t{\n\t\t\tEdgeDayClose();\n",
            "\t\tprivate void NewSession(DateTime etOpen)\n\t\t{\n"
            "\t\t\tCancelAllEntries();                                  // nothing from the last session survives (half days)\n"
            "\t\t\tforeach (Order z in rtZombies) { try { if (Working(z)) CancelOrder(z); } catch { } }\n\t\t\trtZombies.Clear(); rejectHalt = false;\n"
            "\t\t\tforeach (Mod m in mods) m.RejToday = 0;\n\t\t\tSessionBounds();\n\t\t\tEdgeDayClose();\n")
    s = sub(s, "\t\t\tif (FlattenTime > 0 && closeMin >= Hm(FlattenTime) && closeMin < 18 * 60) { FlattenAll(\"end of day\"); UpdateDashboard(); return; }\n",
            "\t\t\tif (closeMin >= FlatMin && closeMin < 18 * 60) { FlattenAll(shortSession ? \"early close (holiday / half day)\" : \"end of day\"); UpdateDashboard(); return; }\n")
    s = sub(s, "\t\t\tif (!CanTrade()) { CancelAllEntries(); UpdateDashboard(); return; }\n",
            "\t\t\tif (!CanTrade()) { CancelAllEntries(); UpdateDashboard(); return; }\n"
            "\t\t\tif (LateBar(Time[0])) { Log(\"bar processed late (session break / data gap): no new entries on it\"); UpdateDashboard(); return; }\n")
    s = sub(s, "\t\tprivate bool CanTrade()\n\t\t{\n\t\t\tif (fomcToday) { status = \"FOMC day: no trading\"; return false; }\n",
            "\t\tprivate bool CanTrade()\n\t\t{\n"
            "\t\t\tif (desyncHalt) { status = \"ACCOUNT / STRATEGY POSITION MISMATCH - see Output\"; return false; }\n"
            "\t\t\tif (rejectHalt) { status = \"the account refuses orders - see Output\"; return false; }\n"
            "\t\t\tif (SkipShortSessions && shortSession) { status = \"holiday / half-day session: no trading\"; return false; }\n"
            "\t\t\tif (rollHalt) { status = \"ROLL DATE: move the strategy to the next contract\"; return false; }\n"
            "\t\t\tif (fomcToday) { status = \"FOMC day: no trading\"; return false; }\n")
    s = sub(s, "Print(string.Format(\"GoldMaster | EVAL TARGET REACHED (+{0:0}, needed {1:0}) - trading stopped.\", eq - StartBalance, need));",
            "Warn(\"gold_target\", string.Format(\"GoldMaster | EVAL TARGET REACHED (+{0:0}, needed {1:0}) - trading stopped.\", eq - StartBalance, need));")
    s = sub(s, "\t\t\t\t\tPrint(string.Format(\"GoldMaster | EDGE MONITOR ALARM {0}:", "\t\t\t\t\tWarn(\"gold_edge\", string.Format(\"GoldMaster | EDGE MONITOR ALARM {0}:")
    s = sub(s, "\t\tprivate void ExitModule(Mod m, string why)\n\t\t{\n", "\t\tprivate void ExitModule(Mod m, string why)\n\t\t{\n\t\t\tif (desyncHalt) return;\n")
    s = sub(s, "\t\tprivate void FlattenAll(string why)\n\t\t{\n\t\t\tCancelAllEntries();\n", "\t\tprivate void FlattenAll(string why)\n\t\t{\n\t\t\tCancelAllEntries();\n\t\t\tif (desyncHalt) return;\n")
    s = sub(s, "\t\tprivate bool OppWork(int d, Mod self) { foreach (Mod o in mods) if (o != self && Working(o.Entry) && o.Dir == -d) return true; return false; }",
            "\t\tprivate bool OppWork(int d, Mod self) { foreach (Mod o in mods) if (o != self && Working(o.Entry) && o.Dir == -d) return true; return RtZombieOpp(d); }")
    # H3 + L1 sizes
    s = sub(s, "\t\t\tm.Q = Qty();\n\t\t\tOrder o = m.Dir == 1 ? EnterLong(m.Q, m.Sig) : EnterShort(m.Q, m.Sig);\n",
            "\t\t\tm.Q = m.RejToday >= 2 ? 0 : CapQty(m, m.Sig, Qty());\n\t\t\tif (m.Q <= 0) { Log(m.Sig + \" skipped (contract cap / rejections)\"); m.Q = 1; return; }\n"
            "\t\t\tOrder o = m.Dir == 1 ? EnterLong(m.Q, m.Sig) : EnterShort(m.Q, m.Sig);\n")
    s = sub(s, "\t\t\tm.Q = Qty();\n\t\t\tOrder o = d == 1 ? EnterLongStopMarket(0, true, m.Q, px, m.Sig) : EnterShortStopMarket(0, true, m.Q, px, m.Sig);\n",
            "\t\t\tm.Q = m.RejToday >= 2 ? 0 : CapQty(m, m.Sig, Qty());\n\t\t\tif (m.Q <= 0) { Log(m.Sig + \" skipped (contract cap / rejections)\"); m.Q = 1; return; }\n"
            "\t\t\tOrder o = d == 1 ? EnterLongStopMarket(0, true, m.Q, px, m.Sig) : EnterShortStopMarket(0, true, m.Q, px, m.Sig);\n")
    # watchdog
    s = sub(s, "\t\t\t\tif (m.CancelOrd == e && CurrentBar - m.CancelBar >= 2) why = \"cancel never confirmed\";\n\t\t\t\telse if (age >= 2 && (s == OrderState.Initialized || s == OrderState.Submitted)) why = \"never accepted\";\n\t\t\t\telse if (age >= 2 && e.OrderType == OrderType.Market && s != OrderState.PartFilled) why = \"market entry never filled\";\n",
            "\t\t\t\tint lim = State == State.Realtime ? 5 : 2;\n"
            "\t\t\t\tif (m.CancelOrd == e && CurrentBar - m.CancelBar >= lim) why = \"cancel never confirmed\";\n\t\t\t\telse if (age >= lim && (s == OrderState.Initialized || s == OrderState.Submitted)) why = \"never accepted\";\n\t\t\t\telse if (age >= lim && e.OrderType == OrderType.Market && s != OrderState.PartFilled) why = \"market entry never filled\";\n")
    s = sub(s, "\t\t\tzombies.Add(e); zombieCount++;\n\t\t\tm.Entry = null; m.SeenOrd = null; m.CancelOrd = null;\n\t\t\tPrint(string.Format(\"{0} | GoldMaster | STALE ORDER dropped",
            "\t\t\tzombies.Add(e); zombieCount++;\n\t\t\tif (State == State.Realtime) { rtZombies.Add(e); Warn(\"gold_stale\", \"GoldMaster | STALE ORDER in realtime: \" + m.Sig + \" \" + e.OrderAction + \" \" + e.OrderType + \" - check the Orders tab; it keeps blocking the opposite direction while it may be live.\"); }\n"
            "\t\t\tm.Entry = null; m.SeenOrd = null; m.CancelOrd = null;\n\t\t\tPrint(string.Format(\"{0} | GoldMaster | STALE ORDER dropped")
    s = sub(s, "\t\t\t\tPrint(string.Format(\"GoldMaster | {0} REJECTED: {1} {2}\", order.Name, error, nativeError));\n",
            "\t\t\t\tWarn(\"gold_rej\", string.Format(\"GoldMaster | {0} REJECTED: {1} {2}\", order.Name, error, nativeError));\n"
            "\t\t\t\tif (m != null && ++m.RejToday == 2) Log(m.Sig + \" off for the rest of the session (2 rejected orders)\");\n\t\t\t\tRejectSeen(nativeError);\n")
    # M3
    s = sub(s, "\t\t\t\tif (execution.Order.Filled <= 0) return;\n\t\t\t\tif (m.InTrade) return;			// further partial fills of the same entry\n",
            "\t\t\t\tif (execution.Order.Filled <= 0) return;\n\t\t\t\tm.OpenQty += quantity;\n\t\t\t\tif (m.InTrade) return;			// further partial fills of the same entry\n")
    s = sub(s, "\t\t\tif (from != null && execution.Order.OrderState == OrderState.Filled) { from.InTrade = false; from.EntryBar = -1; }\n\t\t\tif (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) { x.InTrade = false; x.EntryBar = -1; }\n",
            "\t\t\tif (from != null)\n\t\t\t{\n\t\t\t\tfrom.OpenQty = Math.Max(0, from.OpenQty - quantity); if (from.OpenQty == 0) { from.InTrade = false; from.EntryBar = -1; }\n"
            "\t\t\t\tLog(string.Format(\"{0} exit fill: {1} x{2} @ {3}\", from.Sig, execution.Order.Name, quantity, Fmt(price)));\n\t\t\t}\n"
            "\t\t\tif (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) { x.InTrade = false; x.EntryBar = -1; x.OpenQty = 0; }\n")
    s = sub(s, "\t\t\tif (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) { x.InTrade = false; x.EntryBar = -1; }\n\t\t}\n\t\tprivate bool PauseActive()",
            "\t\t\tif (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) { x.InTrade = false; x.EntryBar = -1; x.OpenQty = 0; }\n\t\t}\n\t\tprivate bool PauseActive()")
    # roll date for gold (NinjaTrader rolls MGC about a week before the contract month)
    s = sub(s, "\t\tprivate int FlatMin {",
            "\t\tprivate bool RollDue()\n\t\t{\n\t\t\tif (!RollGuard) return false;\n\t\t\ttry\n\t\t\t{\n"
            "\t\t\t\tif (Instrument.MasterInstrument.InstrumentType != InstrumentType.Future) return false;\n"
            "\t\t\t\tDateTime ex = Instrument.Expiry; if (ex.Year < 2000) return false;\n"
            "\t\t\t\treturn ToEt(Core.Globals.Now).Date >= new DateTime(ex.Year, ex.Month, 1).AddDays(-7);\n\t\t\t}\n\t\t\tcatch { return false; }\n\t\t}\n"
            "\t\tprivate int FlatMin {")
    s = sub(s, "\t\tprivate void Log(string m) { if (PrintLog) Print(string.Format(\"{0} | GOLD | {1}\", Time[0].ToString(\"yyyy-MM-dd HH:mm\", CultureInfo.InvariantCulture), m)); }",
            "\t\tprivate void Log(string m)\n\t\t{\n\t\t\tstring line = string.Format(\"{0} | GOLD | {1}\", Time[0].ToString(\"yyyy-MM-dd HH:mm\", CultureInfo.InvariantCulture), m);\n"
            "\t\t\tif (PrintLog) Print(line);\n\t\t\tLogFile(line);\n\t\t}")
    s = sub(s, "\t\t\tif (zombieCount > 0) txt += string.Format(\"\\nStale orders dropped: {0} (see Output)\", zombieCount);\n\t\t\tif (EdgeMonitor && edgeDays > 0)",
            "\t\t\tif (zombieCount > 0) txt += string.Format(\"\\nStale orders dropped: {0} (see Output)\", zombieCount);\n"
            "\t\t\tif (capCuts > 0) txt += string.Format(\"\\nMax open contracts {0}: {1} entries cut\", MaxOpenContracts, capCuts);\n"
            "\t\t\tif (shortSession) txt += string.Format(\"\\nShort session: closes {0:00}:{1:00} ET\", sessEndMin / 60, sessEndMin % 60);\n"
            "\t\t\tif (EdgeMonitor && edgeDays > 0)")
    s = sub(s, "\t\t[NinjaScriptProperty][Range(1000, 1659)][Display(Name = \"Flatten time (ET HHmm)\", Order = 2, GroupName = \"02. Risk / account\")] public int FlattenTime { get; set; }",
            "\t\t[NinjaScriptProperty][Range(1000, 1659)][Display(Name = \"Flatten time (ET HHmm; 1600 - MFFU closes at 16:10, Lucid at 16:45)\", Order = 2, GroupName = \"02. Risk / account\")] public int FlattenTime { get; set; }\n"
            + OPS_PROPS.format(g="06. Operations (safety)").rstrip("\n"))
    return s


if __name__ == "__main__":
    for name, fn in (("NQMaster.cs", patch_nq), ("GoldMaster.cs", patch_gold)):
        p = os.path.join(ROOT, name); b = os.path.join(ROOT, name.replace(".cs", "_backup_pre_audit.cs"))
        if not os.path.exists(b): shutil.copy(p, b)
        s = open(b, encoding="utf-8").read()
        s = fn(s)
        open(p, "w", encoding="utf-8", newline="").write(s)
        print("patched", name)
