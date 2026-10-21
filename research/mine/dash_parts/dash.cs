		// ---- dashboard (2026-10-21 redesign): top right = system and performance, top left = account (simulated cycle and/or the real
		// account), bottom left = warnings. Spanish, $ with thousands dots. Drawn on the last historical bars and on every live bar.
		private const string DashLine = "────────────────────────────────────────────────";
		private void UpdateDashboard()
		{
			if (!ShowDashboard || (State == State.Historical && CurrentBars[0] < Count - 2)) return;
			Draw.TextFixed(this, "NQM_Dash", DashSystem(), TextPosition.TopRight, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 80);
			string acct = DashAccount();
			if (acct.Length > 0) Draw.TextFixed(this, "NQM_Acct", acct, TextPosition.TopLeft, Brushes.White, dashFont, Brushes.Transparent, Brushes.Black, 80);
			string warn = DashWarnings();
			if (warn.Length > 0) Draw.TextFixed(this, "NQM_Warn", warn, TextPosition.BottomLeft, Brushes.Orange, dashFont, Brushes.Transparent, Brushes.Black, 80);
			else RemoveDrawObject("NQM_Warn");
		}
		private string DashSystem()
		{
			StringBuilder b = new StringBuilder();
			double pf = grossLoss > 0 ? grossWin / grossLoss : 0;
			string mode = State == State.Realtime ? (SimAccount ? "EN VIVO (simulación)" : "EN VIVO") : "BACKTEST";
			b.AppendLine(string.Format("NQMASTER  ·  {0}  ·  {1}  ·  {2}", Profile, Instrument != null ? Instrument.FullName : "", mode));
			b.AppendLine("Estado: " + StatusEs());
			b.AppendLine(string.Format("Tendencia {0}  ·  ATR diario {1}  ·  día de pullback: {2}", trendDir == 1 ? "ALCISTA" : trendDir == -1 ? "BAJISTA" : "-",
				double.IsNaN(todayAtr) ? "-" : todayAtr.ToString("0"), pullbackDay ? "sí" : "no"));
			StringBuilder mm = new StringBuilder(); int n = 0;
			foreach (Mod m in mods) if (m.On) { mm.Append(m.Sig + (m.InTrade ? "●" : Working(m.Entry) ? "○" : "") + " "); if (++n % 9 == 0) mm.Append("\n         "); }
			b.AppendLine("Módulos: " + mm.ToString().TrimEnd() + "   (● en posición, ○ orden puesta)");
			b.AppendLine(DashLine);
			b.AppendLine(string.Format("RENDIMIENTO{0}", statFirst != DateTime.MinValue ? "  desde " + statFirst.ToString("dd-MM-yy", CultureInfo.InvariantCulture) : ""));
			if (totalTrades == 0) b.AppendLine("Sin trades todavía" + (rthDaysSeen < WarmupDays ? string.Format(" (calentamiento {0}/{1} días)", rthDaysSeen, WarmupDays) : ""));
			else
			{
				double months = statFirst != DateTime.MinValue ? Math.Max(1.0, (statLast - statFirst).TotalDays) / 30.44 : 1;
				b.AppendLine(string.Format("Trades {0}  ·  Ganadoras {1}  ·  Factor de beneficio {2}", totalTrades, Pct(100.0 * totalWins / totalTrades), Dec(pf)));
				b.AppendLine(string.Format("Neto {0}  ·  por trade {1}  ·  por mes {2}", Usd(netPnl), Usd(netPnl / totalTrades), Usd(netPnl / months)));
				b.AppendLine(string.Format("Caída máxima {0}  ·  días positivos {1}", Usd(statMaxDd), statDays > 0 ? Pct(100.0 * statGreenDays / statDays) : "-"));
				if (statDays > 0) b.AppendLine(string.Format("Mejor día {0}  ·  peor día {1}", Usd(statBestDay), Usd(statWorstDay)));
				b.AppendLine(statComm > 0.005 ? string.Format("Comisiones incluidas ({0})  ·  deslizamiento {1} tick", Usd(statComm), Slippage)
					: "SIN comisiones: resultado optimista (cargar $1,90 por contrato ida y vuelta)");
			}
			if (EdgeMonitor && !double.IsNaN(edgeH) && edgeH > 0)
				b.AppendLine(string.Format("Monitor de borde: {0} de la alarma ({1} días){2}", Pct(100 * edgeS / edgeH), edgeDays,
					edgeFbLeft > 0 ? string.Format("  ·  MODO DEFENSIVO {0} días", edgeFbLeft) : edgeAlarm ? "  ·  ALARMA" : 100 * edgeS / edgeH >= 35 ? "  ·  AVISO" : "  ·  OK"));
			if (!double.IsNaN(liveStartPnl))
			{
				int lt = totalTrades - liveStartTrades; double lp = netPnl - liveStartPnl;
				double exp = histDays > 0 ? (liveStartPnl / histDays) * liveDays : 0;
				b.AppendLine(DashLine);
				b.AppendLine(string.Format("EN VIVO desde {0}: {1} sesiones, {2} trades, {3}", liveStart.ToString("dd-MM-yy", CultureInfo.InvariantCulture), liveDays, lt, Usd(lp)));
				if (liveDays > 0) b.AppendLine(string.Format("Esperado por el backtest para {0} sesiones: {1}{2}", liveDays, Usd(exp),
					liveDays < 40 ? "  (menos de 40 sesiones: todavía es ruido)" : lp >= 0.5 * exp ? "  ·  rinde" : "  ·  rinde POR DEBAJO"));
			}
			return b.ToString().TrimEnd();
		}
		private string StatusEs()
		{
			switch (status)
			{
				case "trading": return "operando";
				case "waiting": return "esperando datos";
				default: return status;
			}
		}
		private string DashAccount()
		{
			StringBuilder b = new StringBuilder();
			if (cy != null && (cyOn || cyFrozen))
			{
				double months = cyFirst != DateTime.MinValue ? Math.Max(1.0, (cyLastDay - cyFirst).TotalDays) / 30.44 : 1;
				double fees = cyFeeEval + cyFeeAct, net = cyPayCash - fees;
				b.AppendLine(string.Format("SIMULACIÓN DE CUENTA  ·  {0}{1}", cy.Firm, cyFrozen ? "  (backtest hasta " + cyFrozenAt.ToString("dd-MM-yy", CultureInfo.InvariantCulture) + ")" : ""));
				b.AppendLine("Regla: si se pierde una cuenta, se compra otra eval al día siguiente");
				b.AppendLine(DashLine);
				b.AppendLine(string.Format("Evals compradas   {0,3}   aprobadas {1,3} ({2})   perdidas {3,3}", cyEvalN, cyEvPass, cyEvalN > 0 ? Pct(100.0 * cyEvPass / Math.Max(1, cyEvPass + cyEvBust)) : "-", cyEvBust));
				b.AppendLine(string.Format("Fondeadas         {0,3}   perdidas  {1,3}          completadas {2}", cyFundN, cyFuBust, cyFuDone));
				b.AppendLine(string.Format("Retiros           {0,3}   pedidos {1}   cobrados {2} ({3:0}%)", cyPayN, Usd(cyPayGross), Usd(cyPayCash), cy.Split * 100));
				b.AppendLine(string.Format("Costos            evals {0}{1}", Usd(cyFeeEval), cyFeeAct > 0 ? "  +  activaciones " + Usd(cyFeeAct) : ""));
				b.AppendLine(string.Format("RESULTADO NETO    {0}   ≈ {1} por mes  ({2} meses)", Usd(net), Usd(net / months), months.ToString("0.0", CultureInfo.InvariantCulture).Replace('.', ',')));
				b.AppendLine(DashLine);
				if (!cyStarted) b.AppendLine(string.Format("La primera eval empieza al terminar el calentamiento ({0}/{1} días)", rthDaysSeen, WarmupDays));
				else if (cyFrozen) b.AppendLine("Simulación congelada al pasar a vivo: la cuenta real se muestra abajo");
				else if (cy.Alive)
				{
					double prof = netPnl - cyBase - cy.Withdrawn, bal = StartBalance + prof;
					if (!cy.Funded)
						b.AppendLine(string.Format("Cuenta actual: EVAL #{0}  ·  día {1}  ·  ganancia {2} de {3}", cyEvalN, cy.Days + 1, Usd(prof), Usd(cy.T)));
					else
						b.AppendLine(string.Format("Cuenta actual: FONDEADA #{0}  ·  día {1}  ·  retiros {2}", cyFundN, cy.Days + 1, cy.Pays));
					b.AppendLine(string.Format("Saldo {0}  ·  límite de pérdida {1}  ·  colchón {2}", Usd(bal), Usd(StartBalance + cy.Thr), Usd(prof - cy.Thr)));
					if (!cy.Funded && cy.Cons > 0 && cy.Bal > 0 && cy.Best > cy.Cons * Math.Max(cy.T, cy.Bal))
						b.AppendLine(string.Format("Consistencia: el mejor día ({0}) obliga a llegar a {1}", Usd(cy.Best), Usd(cy.Best / cy.Cons)));
					if (cy.Funded) b.AppendLine("Próximo retiro: " + cy.NextPayout(Usd));
				}
				else b.AppendLine("Cuenta actual: " + (cyStatus.Length > 0 ? cyStatus : "-"));
				int k = Math.Min(8, cyEvents.Count);
				if (k > 0)
				{
					b.AppendLine("Últimos eventos:");
					for (int i = cyEvents.Count - 1; i >= cyEvents.Count - k; i--) b.AppendLine("  " + cyEvents[i]);
				}
			}
			else if (PropMode != NQMasterPropMode.Off && cy == null && State != State.Realtime)
				b.AppendLine(PropPreset == NQMasterPropPreset.Manual ? "Para simular retiros y cuentas perdidas elegí un preset de firma (Lucid, MFFU...)"
					: "Simulación del ciclo apagada (Backtest: simular el ciclo = false)");
			// the real prop account (live, not a Sim account)
			if (State == State.Realtime && !SimAccount && PropMode != NQMasterPropMode.Off && !double.IsNaN(propThr))
			{
				if (b.Length > 0) b.AppendLine(DashLine);
				double eq = PropEquity();
				b.AppendLine(string.Format("CUENTA REAL  ·  {0}  ·  {1}", Account != null ? Account.Name : "", PhaseName(PropMode)));
				b.AppendLine(string.Format("Saldo {0} ({1})  ·  límite {2}  ·  colchón {3}", Usd(eq), Usd(eq - StartBalance), Usd(propThr), Usd(eq - propThr)));
				if (!double.IsNaN(propDayStart)) b.AppendLine("Hoy: " + Usd(eq - propDayStart));
				if (eq <= propThr) b.AppendLine("ATENCIÓN: el saldo está en el límite: verificá la cuenta en la firma");
				if (PropMode == NQMasterPropMode.Eval && EvalTarget > 0) b.AppendLine(string.Format("Objetivo: {0} de {1}", Usd(eq - StartBalance), Usd(EvalTarget)));
				if (PropMode == NQMasterPropMode.Funded) b.AppendLine((eq - StartBalance >= FundedPayoutAt ? "RETIRO DISPONIBLE: " : "Retiro: ") + payoutHint);
			}
			return b.ToString().TrimEnd();
		}
		private string DashWarnings()
		{
			StringBuilder b = new StringBuilder();
			if (zombieCount > 0) b.AppendLine(string.Format("! {0} órdenes trabadas descartadas (ver Output)", zombieCount));
			if (capCuts > 0) b.AppendLine(string.Format("! Tope de {0} contratos abiertos: {1} entradas recortadas", MaxOpenContracts, capCuts));
			if (shortSession) b.AppendLine(string.Format("! Sesión corta: cierra {0:00}:{1:00} ET", sessEndMin / 60, sessEndMin % 60));
			if (edgeAlarm) b.AppendLine("! ALARMA del monitor de borde: revisar antes de seguir");
			if (State == State.Realtime && (atrCount < AtrMin || rthDaysSeen < WarmupDays)) b.AppendLine(string.Format("! Calentamiento incompleto: {0}/{1} días (cargar 45+ días)", rthDaysSeen, WarmupDays));
			if (State == State.Realtime && SimAccount && PropMode != NQMasterPropMode.Off) b.AppendLine("Cuenta de simulación: el saldo es el de la cuenta simulada, no el de Sim101");
			if (RiskCapPerContract > 0 && PropMode != NQMasterPropMode.Off && riskSkips > 0) b.AppendLine(string.Format("Tope de riesgo {0}/contrato: {1} trades salteados con colchón chico", Usd(RiskCapPerContract), riskSkips));
			return b.ToString().TrimEnd();
		}
