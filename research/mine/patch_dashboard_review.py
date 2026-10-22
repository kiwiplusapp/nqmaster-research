"""2026-10-21 fixes from research/mine/review_dashboard_2026-10-21.md (H1, M2-M5, L6, L7, L10-L12, L14, L16, L17). Backup NQMaster_backup_pre_dashreview.cs."""
p='NQMaster.cs'; s=open(p,encoding='utf-8-sig').read()
def rep(a,b,n=1):
    global s
    assert s.count(a)==n,(s.count(a),a[:80]); s=s.replace(a,b)
rep("			cyOn = false; cyFrozen = true; cyFrozenAt = cyLastDay;\n","			cyOn = false; cyFrozen = true; cyFrozenAt = cyLastDay; cyHalt = false; cyStatus = \"\";	// review H1: a simulated halt never blocks the real account\n")
rep('			if (cyHalt) { status = cyStatus.Length > 0','			if (cyOn && cyHalt) { status = cyStatus.Length > 0')
rep("""					if (want != m.Entry.Quantity) { try { ChangeOrder(m.Entry, want, m.Entry.LimitPrice, m.Entry.StopPrice); Log(string.Format("{0} entry re-sized {1} -> {2} at go-live (cushion size {3} -> {4})", m.Sig, m.Entry.Quantity, want, hq, lq)); } catch { } }
				}
""","""					if (want != m.Entry.Quantity) { try { ChangeOrder(m.Entry, want, m.Entry.LimitPrice, m.Entry.StopPrice); Log(string.Format("{0} entry re-sized {1} -> {2} at go-live (cushion size {3} -> {4})", m.Sig, m.Entry.Quantity, want, hq, lq)); } catch { } }
				}
				if (lq != hq)	// review 2026-10-21 M2: parked setups and the pending MSEQ / MSEQS retry carry the history size as well
				{
					foreach (Mod m in mods) if (m.Parked) m.ParkQty = Math.Max(1, (int)Math.Round(m.ParkQty * (double)lq / hq));
					if (pend5 != null) pend5Qty = Math.Max(1, (int)Math.Round(pend5Qty * (double)lq / hq));
				}
				edgeDayQty = Qty(); statQty = Qty();	// review L14
""")
rep("""			if (SimAccount) return StartBalance + netPnl - CyOffset();
			return Account.Get(AccountItem.CashValue, Currency.UsDollar);""","""			if (SimAccount) return cyOn ? StartBalance + netPnl - CyOffset() : StartBalance + netPnl - (double.IsNaN(simBase) ? netPnl : simBase);
			return Account.Get(AccountItem.CashValue, Currency.UsDollar);""")
rep("		private bool SimAccount { get {","		private double simBase = double.NaN;	// review M3: Sim / Playback without the cycle simulation starts a fresh account at go-live\n		private bool SimAccount { get {")
rep("			if (SimAccount) return;	// Sim / Playback: keep the backtest's account state (no prop file)\n",
    "			if (SimAccount)	// Sim / Playback: no prop file. With the cycle simulation the simulated seat continues; without it a fresh account starts now\n			{\n				if (cyOn) return;\n				simBase = netPnl; propPeak = StartBalance; propDayStart = double.NaN; propBestDay = EvalBestDaySoFar; targetHit = false;\n				PropSessionStart(); return;\n			}\n")
rep("double now = State == State.Realtime ? AcctCash() + Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar)",
    "double now = State == State.Realtime ? AcctCash() + (SimAccount ? (Position.MarketPosition == MarketPosition.Flat ? 0 : Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Closes[0][0])) : Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar))")
rep("			else if (State == State.Terminated)\n			{\n","			else if (State == State.Terminated)\n			{\n				if (presetSnap != null && cy != null) { RestorePreset(presetSnap); PropMode = realMode; }	// review M4: never leave the simulated phase in the properties\n")
rep("			if (cyStarted && cy.Alive)\n			{\n				DateTime prev","			if (cyStarted && cy.Alive && cyPrevTradable)	// review L7: FOMC / low-ATR / skipped sessions are not account days (research day lists skip them)\n			{\n				DateTime prev")
rep('				if (cyWait > 0) { cyWait--; cyHalt = true; cyStatus = "eval aprobada: esperando los días mínimos de la firma"; }',
    '				if (cyWaitPrev && cyPrevTradable && cyWait > 0) cyWait--;\n				if (cyWait > 0) { cyHalt = true; cyWaitNow = true; cyStatus = "eval aprobada: esperando los días mínimos de la firma"; }')
rep("			cyHalt = false; cyLastDay = tradeDay;\n","			cyHalt = false; cyLastDay = tradeDay; cyWaitPrev = cyWaitNow; cyWaitNow = false;\n")
rep("		private DateTime cyPrevDay = DateTime.MinValue;\n","		private DateTime cyPrevDay = DateTime.MinValue; private bool cyPrevTradable = true, cyWaitPrev, cyWaitNow;\n")
rep("				edgeDayQty = Qty();                                  // after the prop cushion is known (funded step-up)\n",
    "				edgeDayQty = Qty();                                  // after the prop cushion is known (funded step-up)\n				statQty = Qty(); statDayHalted = cyOn && cyHalt;\n				cyPrevTradable = !fomcToday && !(MinAtrPoints > 0 && !double.IsNaN(todayAtr) && todayAtr < MinAtrPoints) && !(SkipShortSessions && shortSession) && !rollHalt;\n				if (cyOn && cyHalt) edgeDayTradable = false;	// review L6\n")
rep("""		private void StatDayClose()
		{
			if (totalTrades == statDayTrades0) { if (statFirst != DateTime.MinValue) { if (double.IsNaN(liveStartPnl)) histDays++; else liveDays++; } return; }
			double d = netPnl - dayStartPnl; statDays++; if (d > 0) statGreenDays++;
			statBestDay = double.IsNaN(statBestDay) ? d : Math.Max(statBestDay, d); statWorstDay = double.IsNaN(statWorstDay) ? d : Math.Min(statWorstDay, d);
			if (double.IsNaN(liveStartPnl)) histDays++; else liveDays++;
			statDayTrades0 = totalTrades;
		}""","""		private int statQty = 1; private bool statDayHalted; private double histUnitSum, liveExpect;
		// review M5: the live expectation is the history's P&L per base contract per tradable day (simulation halts excluded) x the live size
		private void StatDayClose()
		{
			double d = netPnl - dayStartPnl; bool traded = totalTrades != statDayTrades0; statDayTrades0 = totalTrades;
			if (traded)
			{
				statDays++; if (d > 0) statGreenDays++;
				statBestDay = double.IsNaN(statBestDay) ? d : Math.Max(statBestDay, d); statWorstDay = double.IsNaN(statWorstDay) ? d : Math.Min(statWorstDay, d);
			}
			if (statFirst == DateTime.MinValue || statDayHalted) return;
			if (double.IsNaN(liveStartPnl)) { histUnitSum += d / Math.Max(1, statQty); histDays++; }
			else { liveDays++; liveExpect += (histDays > 0 ? histUnitSum / histDays : 0) * Math.Max(1, statQty); }
		}""")
rep("				double exp = histDays > 0 ? (liveStartPnl / histDays) * liveDays : 0;\n","				double exp = liveExpect;\n")
rep("				double months = statFirst != DateTime.MinValue ? Math.Max(1.0, (statLast - statFirst).TotalDays) / 30.44 : 1;","				double months = statFirst != DateTime.MinValue ? Math.Max(1.0, (statLast - statFirst).TotalDays / 30.44) : 1;")
rep("				double months = cyFirst != DateTime.MinValue ? Math.Max(1.0, (cyLastDay - cyFirst).TotalDays) / 30.44 : 1;","				double months = cyFirst != DateTime.MinValue ? Math.Max(1.0, (cyLastDay - cyFirst).TotalDays / 30.44) : 1;")
rep('Pct(100.0 * totalWins / totalTrades), Dec(pf)));','Pct(100.0 * totalWins / totalTrades), grossLoss > 0 ? Dec(pf) : "sin pérdidas"));')
rep("			ApplyPhase(NQMasterPropMode.Funded, false);			// funded rule values (payout level) for the engine, printed once\n","			ApplyPhase(NQMasterPropMode.Funded, false);			// funded rule values (payout level) for the engine, printed once\n			double fundedPayoutAt = FundedPayoutAt;\n")
rep("cy.Firm, cy.T, cy.D, ConsistencyPct, cy.Fee, FundedPayoutAt));","cy.Firm, cy.T, cy.D, ConsistencyPct, cy.Fee, fundedPayoutAt));")
rep('b.AppendLine("Cuenta de simulación: el saldo es el de la cuenta simulada, no el de Sim101");',
    'b.AppendLine(cyOn ? "Cuenta de simulación con el ciclo corriendo: no guardes el template mientras corre (la fase cambia sola)" : "Cuenta de simulación: el saldo es una cuenta nueva desde que pasó a vivo, no el de Sim101");')
rep("UseMom1130 = true; UseRsi2 = true;","UseMom1130 = false; UseRsi2 = false;")
open(p,'w',encoding='utf-8-sig').write(s)
print("ok")
