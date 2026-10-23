		// ---- account cycle simulation (2026-10-21, Federico: 'calculate payouts, show them, whether it burned, how many burned, buying a new
		// eval the next day'). With a firm preset and PropMode Eval/Funded, the backtest runs the whole seat: buy an eval -> pass (flatten at
		// the target, firm minimum days) or lose it -> next session a new eval (fee) or the funded account (activation) -> payouts at the
		// close with the firm rule -> lost or completed (last payout) -> new eval. Eval and funded sizes and stops are the preset's, switched
		// at each phase change. Rules engine = PropCycle (audited against the research simulators by tools/propcycle_test/run_test.py).
		// Runs on history and, on a Sim/Playback account, live; on a real prop account it stops at go-live (the firm's account is the truth).
		private PropCycle cy; private bool cyOn, cyStarted, cyHalt, cyFrozen, presetQuiet; private NQMasterPropMode realMode = NQMasterPropMode.Off;
		private double cyBase; private int cyNext, cyWait, cyEvalN, cyEvPass, cyEvBust, cyFundN, cyFuBust, cyFuDone, cyPayN; private int cySeat = 1;
		private double cyPayGross, cyPayCash, cyFeeEval, cyFeeAct; private DateTime cyFirst = DateTime.MinValue, cyLastDay = DateTime.MinValue, cyFrozenAt;
		private string cyStatus = ""; private List<string> cyEvents = new List<string>();
		private double[] presetSnap;
		private bool CyLive { get { return cy != null && cyOn && cy.Alive; } }
		private double CyOffset() { return cy != null && cyStarted ? cyBase + cy.Withdrawn : 0; }
		// every account setting ApplyPreset() writes: restored before each phase change so a phase never inherits the other phase's values
		private double[] SnapPreset()
		{
			return new double[] { EvalMode ? 1 : 0, AdaptiveSize ? 1 : 0, EvalCushionFull, EvalDailyStop, FundedCushionSafe, FundedCushionFull, FundedHighFull ? 1 : 0,
				DailyLossLimit, FundedStepUpCushion, FundedLadderStep, DailyLossPerContract, NewsBlackout ? 1 : 0, StartBalance, PropTrailingDD, ConsistencyPct,
				EvalTarget, EvalProfitStop, EvalRiskCapCushion, MaxOpenContracts, EvalHighWrMultiplier, RiskCapPerContract, FundedRiskCapCushion, FundedPayoutAt,
				FundedProfitStop, Contracts, FundedStepUpContracts, FundedLadderMax };
		}
		private void RestorePreset(double[] s)
		{
			int i = 0;
			EvalMode = s[i++] > 0; AdaptiveSize = s[i++] > 0; EvalCushionFull = s[i++]; EvalDailyStop = s[i++]; FundedCushionSafe = s[i++]; FundedCushionFull = s[i++]; FundedHighFull = s[i++] > 0;
			DailyLossLimit = s[i++]; FundedStepUpCushion = s[i++]; FundedLadderStep = s[i++]; DailyLossPerContract = s[i++]; NewsBlackout = s[i++] > 0; StartBalance = s[i++]; PropTrailingDD = s[i++]; ConsistencyPct = s[i++];
			EvalTarget = s[i++]; EvalProfitStop = s[i++]; EvalRiskCapCushion = s[i++]; MaxOpenContracts = (int)s[i++]; EvalHighWrMultiplier = (int)s[i++]; RiskCapPerContract = s[i++]; FundedRiskCapCushion = s[i++]; FundedPayoutAt = s[i++];
			FundedProfitStop = s[i++]; Contracts = (int)s[i++]; FundedStepUpContracts = (int)s[i++]; FundedLadderMax = (int)s[i++];
		}
		private void ApplyPhase(NQMasterPropMode mode, bool quiet)
		{
			PropMode = mode; RestorePreset(presetSnap); presetQuiet = quiet; ApplyPreset(); presetQuiet = false;
		}
		// firm rules per preset (research: acct1c_lib.py / smallacct_life2.py / month80.py / mffu_rapid.py / prop_wf.py FIRMS; list prices)
		private PropCycle FirmRules()
		{
			PropCycle p = new PropCycle();
			switch (PropPreset)
			{
				case NQMasterPropPreset.Lucid25K: p.Firm = "Lucid Flex 25K"; p.Model = 0; p.Q = 100; p.Cap1 = p.Cap2 = 1000; p.Fee = 89; break;
				case NQMasterPropPreset.Lucid50K: p.Firm = "Lucid Flex 50K"; p.Model = 0; p.Q = 150; p.Cap1 = p.Cap2 = 2000; p.Fee = 146; break;
				case NQMasterPropPreset.Lucid150K: p.Firm = "Lucid Flex 150K"; p.Model = 0; p.Q = 250; p.Cap1 = p.Cap2 = 3000; p.Fee = 285; break;
				case NQMasterPropPreset.LucidPro25K: p.Firm = "Lucid Pro 25K"; p.Model = 1; p.Cap1 = 1000; p.Cap2 = 1500; p.Fee = 123; break;
				case NQMasterPropPreset.LucidPro50K: p.Firm = "Lucid Pro 50K"; p.Model = 1; p.Cap1 = 2000; p.Cap2 = 2500; p.Fee = 192; break;
				case NQMasterPropPreset.FundedNext25K: p.Firm = "FundedNext Rapid Pro 25K (aprox.)"; p.Model = 1; p.Cap1 = p.Cap2 = 1200; p.Fee = 80; break;
				case NQMasterPropPreset.Mffu50K: case NQMasterPropPreset.Mffu50KLadder: p.Firm = "MFFU Rapid EOD 50K"; p.Model = 2; p.NpMax = 0; p.MinDays = 4; p.Fee = 157; break;
				default: return null;
			}
			if (EvalPrice > 0) p.Fee = EvalPrice;
			p.Act = ActivationFee;
			return p;
		}
		private void CycleInit()
		{
			realMode = PropMode; presetSnap = SnapPreset(); cy = null; cyOn = false;
			if (!CycleSim || PropMode == NQMasterPropMode.Off || PropPreset == NQMasterPropPreset.Manual || FirmRules() == null) { ApplyPreset(); return; }
			cy = FirmRules();
			ApplyPhase(NQMasterPropMode.Funded, false);			// funded rule values (payout level) for the engine, printed once
			cy.D = PropTrailingDD; cy.Buf = PropTrailingDD + 100;
			if (cy.Model == 0) cy.X = FundedPayoutAt;
			else if (cy.Model == 1) cy.X = Math.Max(500, FundedPayoutAt - cy.Buf);
			else cy.X = FundedPayoutAt - 500;                   // MFFU: request at FundedPayoutAt, keep FundedPayoutAt - 500
			ApplyPhase(NQMasterPropMode.Eval, false);
			cy.T = EvalTarget; cy.Cons = ConsistencyPct / 100.0;
			cyOn = true;
			Print(string.Format("NQMaster | CICLO DE CUENTA ({0}): eval ${1:0} objetivo, drawdown ${2:0}, consistencia {3:0}%, precio eval ${4:0}; fondeada: retiro con ganancia >= ${5:0}. La primera eval empieza al terminar el calentamiento.",
				cy.Firm, cy.T, cy.D, ConsistencyPct, cy.Fee, FundedPayoutAt));
		}
		private void CyEvent(DateTime day, string s)
		{
			cyEvents.Add(day.ToString("dd-MM-yy", CultureInfo.InvariantCulture) + "  " + s);
			if (cyEvents.Count > 400) cyEvents.RemoveAt(0);
			Log("CICLO: " + s);
		}
		private void CyStart(bool funded, DateTime day)
		{
			ApplyPhase(funded ? NQMasterPropMode.Funded : NQMasterPropMode.Eval, true);
			cyBase = netPnl; cy.Start(funded); cyStarted = true;
			propPeak = StartBalance; propDayStart = double.NaN; propBestDay = 0; targetHit = false;
			if (funded) { cyFundN++; cyFeeAct += cy.Act; CyEvent(day, string.Format("Fondeada #{0} activada{1}", cyFundN, cy.Act > 0 ? " (" + Usd(cy.Act) + ")" : "")); }
			else { cyEvalN++; cyFeeEval += cy.Fee; CyEvent(day, string.Format("Eval #{0} comprada ({1})", cyEvalN, Usd(cy.Fee))); }
			if (cyFirst == DateTime.MinValue) cyFirst = day;
		}
		// first bar of a session, before PropSessionStart(): close the last day, then start what is pending
		private void CycleSessionStart(DateTime tradeDay)
		{
			if (!cyOn) return;
			cyHalt = false; cyLastDay = tradeDay;
			if (cyStarted && cy.Alive)
			{
				DateTime prev = cyPrevDay == DateTime.MinValue ? tradeDay : cyPrevDay;
				double amt = cy.DayClose(netPnl - cyBase);
				if (amt > 0)
				{
					cyPayN++; cyPayGross += amt; cyPayCash += cy.Split * amt;
					CyEvent(prev, string.Format("RETIRO #{0} de la fondeada #{1}: {2} (cobrás {3})", cy.Pays, cyFundN, Usd(amt), Usd(cy.Split * amt)));
				}
				if (!cy.Alive) { cyFuDone++; cyNext = 1; cyWait = 0; CyEvent(prev, string.Format("Fondeada #{0} COMPLETADA ({1} retiros: pasa a cuenta real); nueva eval", cyFundN, cy.Pays)); }
			}
			if (!cyStarted) { if (rthDaysSeen >= WarmupDays && atrCount >= AtrMin) CyStart(false, tradeDay); else { cyHalt = true; cyStatus = "calentamiento: la primera eval empieza al completarlo"; } }
			else if (!cy.Alive && cyNext != 0)
			{
				if (cyWait > 0) { cyWait--; cyHalt = true; cyStatus = "eval aprobada: esperando los días mínimos de la firma"; }
				else { bool f = cyNext == 2; cyNext = 0; CyStart(f, tradeDay); }
			}
			cyPrevDay = tradeDay;
		}
		private DateTime cyPrevDay = DateTime.MinValue;
		// every 1-minute bar: account lost (equity incl. the open position at the bar's adverse extreme <= threshold) or eval target reached
		private void CycleBar()
		{
			if (!CyLive || cyHalt) return;
			double raw = netPnl - cyBase, oc = 0, ol = 0;
			if (Position.MarketPosition != MarketPosition.Flat)
			{
				try
				{
					oc = Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Closes[0][0]);
					ol = Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Position.MarketPosition == MarketPosition.Long ? Lows[0][0] : Highs[0][0]);
				}
				catch { }
			}
			int r = cy.Bar(raw + Math.Min(ol, oc), raw + oc);
			if (r == 0) return;
			cyHalt = true; DateTime day = cyLastDay == DateTime.MinValue ? Times[0][0].Date : cyLastDay;
			if (r == -1)
			{
				FlattenAll("SIM: cuenta perdida");
				if (cy.Funded) { cyFuBust++; CyEvent(day, string.Format("Fondeada #{0} PERDIDA (día {1}, {2} retiros cobrados); mañana se compra otra eval", cyFundN, cy.Days + 1, cy.Pays)); }
				else { cyEvBust++; CyEvent(day, string.Format("Eval #{0} PERDIDA (día {1}); mañana se compra otra", cyEvalN, cy.Days + 1)); }
				cyNext = 1; cyWait = 0; cyStatus = "cuenta perdida: nueva eval en la próxima sesión";
			}
			else
			{
				FlattenAll("SIM: objetivo de la eval");
				cyEvPass++; cyNext = 2; cyWait = Math.Max(0, cy.MinDays - (cy.Days + 1));
				CyEvent(day, string.Format("Eval #{0} APROBADA en {1} días", cyEvalN, cy.Days + 1));
				cyStatus = "eval aprobada: la fondeada empieza en la próxima sesión";
			}
		}
		// go-live: a real prop account is the truth -> freeze the simulation, back to the account's real phase and preset values
		private void CycleGoLive()
		{
			if (!cyOn || SimAccount) return;
			cyOn = false; cyFrozen = true; cyFrozenAt = cyLastDay;
			ApplyPhase(realMode, false); targetHit = false;
		}

		// ---- performance statistics for the dashboard (closed trades, as NinjaTrader books them: net of commission when a commission
		// template is set)
		private double statPeak, statMaxDd, statComm, statBestDay = double.NaN, statWorstDay = double.NaN; private int statDays, statGreenDays, statDayTrades0;
		private DateTime statFirst = DateTime.MinValue, statLast = DateTime.MinValue;
		private double liveStartPnl = double.NaN; private int liveStartTrades, liveDays, histDays; private DateTime liveStart;
		private void StatTrade(double pnl, double comm, DateTime t)
		{
			statComm += comm; if (statFirst == DateTime.MinValue) statFirst = t; statLast = t;
			if (netPnl > statPeak) statPeak = netPnl;
			statMaxDd = Math.Max(statMaxDd, statPeak - netPnl);
		}
		private void StatDayClose()
		{
			if (totalTrades == statDayTrades0) { if (statFirst != DateTime.MinValue) { if (double.IsNaN(liveStartPnl)) histDays++; else liveDays++; } return; }
			double d = netPnl - dayStartPnl; statDays++; if (d > 0) statGreenDays++;
			statBestDay = double.IsNaN(statBestDay) ? d : Math.Max(statBestDay, d); statWorstDay = double.IsNaN(statWorstDay) ? d : Math.Min(statWorstDay, d);
			if (double.IsNaN(liveStartPnl)) histDays++; else liveDays++;
			statDayTrades0 = totalTrades;
		}
		private static string Usd(double v)
		{
			string s = Math.Abs(v).ToString("#,0", CultureInfo.InvariantCulture).Replace(',', '.');
			return (v < -0.5 ? "-$" : "$") + s;
		}
		private static string Pct(double v) { return v.ToString("0.0", CultureInfo.InvariantCulture).Replace('.', ',') + "%"; }
		private static string Dec(double v) { return v.ToString("0.00", CultureInfo.InvariantCulture).Replace('.', ','); }
		private string PhaseName(NQMasterPropMode m) { return m == NQMasterPropMode.Eval ? "Evaluación" : m == NQMasterPropMode.Funded ? "Fondeada" : "Off"; }
