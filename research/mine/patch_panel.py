"""2026-10-23 panel window (Federico chose 'opción 2'): NQMaster publishes an immutable snapshot to NQMasterUI.Hub (NQMasterPanel.cs)
on the last historical bars and every live bar; the window opens at go-live on a chart (never in the Strategy Analyzer) and Ctrl+Shift+P
on the chart reopens it. Backup NQMaster_backup_pre_panel.cs."""
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, "NQMaster.cs"); s = open(P, encoding="utf-8-sig").read()
if "NQMasterUI.Hub" in s: raise SystemExit("already patched")
shutil.copy(P, os.path.join(ROOT, "NQMaster_backup_pre_panel.cs"))
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:80]); s = s.replace(a, b)
# 1. equity curve points + event rows with a kind + cash curve
rep("""			if (statFirst == DateTime.MinValue || statDayHalted) return;
			if (double.IsNaN(liveStartPnl)) { histUnitSum += d / Math.Max(1, statQty); histDays++; }""",
"""			if (statFirst != DateTime.MinValue && curSessDay > 0) { eqDays.Add(IntDay(curSessDay)); eqVals.Add(netPnl); }
			if (statFirst == DateTime.MinValue || statDayHalted) return;
			if (double.IsNaN(liveStartPnl)) { histUnitSum += d / Math.Max(1, statQty); histDays++; }""")
rep("""			cyEvents.Add(day.ToString("dd-MM-yy", CultureInfo.InvariantCulture) + "  " + s);
			if (cyEvents.Count > 400) cyEvents.RemoveAt(0);""",
"""			cyEvents.Add(day.ToString("dd-MM-yy", CultureInfo.InvariantCulture) + "  " + s);
			if (cyEvents.Count > 400) cyEvents.RemoveAt(0);
			NQMasterUI.EventRow er = new NQMasterUI.EventRow(); er.Day = day; er.Text = s;
			er.Kind = s.Contains("PERDIDA") ? -1 : (s.Contains("APROBADA") || s.Contains("RETIRO") || s.Contains("COMPLETADA") ? 1 : 0);
			cyEvRows.Add(er); if (cyEvRows.Count > 400) cyEvRows.RemoveAt(0);
			cashDays.Add(day); cashVals.Add(cyPayCash - cyFeeEval - cyFeeAct);""")
# CyEvent for a payout is called after the cash is added; for a purchase CyEvent runs after the fee is added -> curve right
# 2. publish + open + hotkey
PANEL = """		// ---- panel window (NQMasterPanel.cs): an immutable snapshot for NQMasterUI.Hub; only on a chart (never in the Strategy Analyzer)
		private List<DateTime> eqDays = new List<DateTime>(); private List<double> eqVals = new List<double>();
		private List<NQMasterUI.EventRow> cyEvRows = new List<NQMasterUI.EventRow>(); private List<DateTime> cashDays = new List<DateTime>(); private List<double> cashVals = new List<double>();
		private string panelKey; private bool panelKeyHooked;
		private static DateTime IntDay(int d) { try { return new DateTime(d / 10000, d / 100 % 100, d % 100); } catch { return DateTime.MinValue; } }
		private bool PanelWanted { get { return ShowPanelWindow && ChartControl != null; } }
		private void PanelPublish()
		{
			if (!PanelWanted || (State == State.Historical && CurrentBars[0] < Count - 2)) return;
			try { NQMasterUI.Hub.Publish(BuildSnapshot()); } catch (Exception e) { Print("NQMaster | panel snapshot skipped: " + e.Message); }
		}
		private void PanelOpen()
		{
			if (!PanelWanted) return;
			PanelPublish(); NQMasterUI.Hub.Open();
			if (panelKeyHooked) return;
			try { ChartControl.Dispatcher.InvokeAsync(new Action(() => { try { ChartControl.PreviewKeyDown += OnPanelKey; panelKeyHooked = true; } catch { } })); } catch { }
		}
		private void PanelClose()
		{
			try { if (panelKey != null) NQMasterUI.Hub.Remove(panelKey); } catch { }
			try { if (panelKeyHooked && ChartControl != null) ChartControl.Dispatcher.InvokeAsync(new Action(() => { try { ChartControl.PreviewKeyDown -= OnPanelKey; } catch { } })); } catch { }
		}
		// Ctrl+Shift+P on the chart reopens the panel window
		private void OnPanelKey(object sender, System.Windows.Input.KeyEventArgs e)
		{
			try
			{
				System.Windows.Input.ModifierKeys mk = System.Windows.Input.Keyboard.Modifiers;
				if (e.Key == System.Windows.Input.Key.P && (mk & System.Windows.Input.ModifierKeys.Control) != 0 && (mk & System.Windows.Input.ModifierKeys.Shift) != 0)
				{ NQMasterUI.Hub.Open(); e.Handled = true; }
			}
			catch { }
		}
		private NQMasterUI.Snapshot BuildSnapshot()
		{
			NQMasterUI.Snapshot s = new NQMasterUI.Snapshot();
			string acct = Account != null ? Account.Name : "-", ins = Instrument != null ? Instrument.FullName : "-";
			if (panelKey == null) panelKey = acct + "|" + ins + "|" + GetHashCode().ToString(CultureInfo.InvariantCulture);
			s.Key = panelKey; s.Title = acct + "  ·  " + ins + "  ·  " + Profile; s.Account = acct; s.Instrument = ins; s.Profile = Profile.ToString();
			s.Mode = State == State.Realtime ? (SimAccount ? "EN VIVO (simulación)" : "EN VIVO") : "BACKTEST"; s.Status = StatusEs(); s.Time = ToEt(Times[0][0]);
			s.Trend = trendDir == 1 ? "ALCISTA" : trendDir == -1 ? "BAJISTA" : "-"; s.Atr = double.IsNaN(todayAtr) ? 0 : todayAtr; s.Pullback = pullbackDay;
			s.Trades = totalTrades; s.WinRate = totalTrades > 0 ? 100.0 * totalWins / totalTrades : 0; s.Pf = grossLoss > 0 ? grossWin / grossLoss : 0; s.Net = netPnl;
			double months = statFirst != DateTime.MinValue ? Math.Max(1.0, (statLast - statFirst).TotalDays / 30.44) : 1;
			s.PerTrade = totalTrades > 0 ? netPnl / totalTrades : 0; s.PerMonth = netPnl / months; s.MaxDd = statMaxDd; s.First = statFirst; s.Commission = statComm;
			s.BestDay = double.IsNaN(statBestDay) ? 0 : statBestDay; s.WorstDay = double.IsNaN(statWorstDay) ? 0 : statWorstDay; s.GreenPct = statDays > 0 ? 100.0 * statGreenDays / statDays : 0;
			int step = Math.Max(1, eqVals.Count / 600);		// at most ~600 points, the last one always included
			for (int i = 0; i < eqVals.Count; i += step) { s.EqDays.Add(eqDays[i]); s.EqVals.Add(eqVals[i]); }
			if (eqVals.Count > 0 && (eqVals.Count - 1) % step != 0) { s.EqDays.Add(eqDays[eqDays.Count - 1]); s.EqVals.Add(eqVals[eqVals.Count - 1]); }
			s.EqVals.Add(netPnl); s.EqDays.Add(s.Time.Date);
			s.Live = !double.IsNaN(liveStartPnl); if (s.Live) { s.LiveDays = liveDays; s.LiveTrades = totalTrades - liveStartTrades; s.LivePnl = netPnl - liveStartPnl; s.LiveExpected = liveExpect; }
			s.EdgeOn = EdgeMonitor && !double.IsNaN(edgeH) && edgeH > 0;
			if (s.EdgeOn) { s.EdgePct = 100 * edgeS / edgeH; s.EdgeDays = edgeDays; s.EdgeState = edgeFbLeft > 0 ? "MODO DEFENSIVO" : edgeAlarm ? "ALARMA" : (edgeHw > 0 && edgeS >= edgeHw ? "AVISO" : "OK"); }
			// modules: every closed trade by its entry name (all + last 365 days), plus the live state of each module
			Dictionary<string, double[]> st = new Dictionary<string, double[]>();
			if (SystemPerformance != null && SystemPerformance.AllTrades != null && SystemPerformance.AllTrades.Count > 0)
			{
				TradeCollection all = SystemPerformance.AllTrades; DateTime from = all[all.Count - 1].Exit.Time.AddDays(-365);
				foreach (Trade t in all)
				{
					string k = t.Entry != null && !string.IsNullOrEmpty(t.Entry.Name) ? t.Entry.Name : "?"; double[] a;
					if (!st.TryGetValue(k, out a)) { a = new double[8]; st[k] = a; }
					double p = t.ProfitCurrency; bool yr = t.Exit != null && t.Exit.Time >= from;
					a[0] += 1; if (p > 0) { a[1] += 1; a[2] += p; } else a[3] -= p;
					if (yr) { a[4] += 1; if (p > 0) { a[5] += 1; a[6] += p; } else a[7] -= p; }
				}
			}
			HashSet<string> seen = new HashSet<string>();
			foreach (Mod m in mods)
			{
				if (seen.Contains(m.Sig)) continue; seen.Add(m.Sig);
				double[] a; st.TryGetValue(m.Sig, out a);
				if (!m.On && a == null) continue;
				s.Modules.Add(ModRow(m.Sig, m.On, m.InTrade ? "en posición" : (Working(m.Entry) ? "orden puesta" : ""), a));
			}
			foreach (KeyValuePair<string, double[]> kv in st) if (!seen.Contains(kv.Key)) s.Modules.Add(ModRow(kv.Key, false, "", kv.Value));
			// account simulation
			if (cy != null && (cyOn || cyFrozen))
			{
				s.SimOn = true; s.SimFrozen = cyFrozen; s.Firm = cy.Firm;
				s.Evals = cyEvalN; s.EvalPass = cyEvPass; s.EvalLost = cyEvBust; s.Funded = cyFundN; s.FundedLost = cyFuBust; s.FundedDone = cyFuDone; s.Payouts = cyPayN;
				s.PayGross = cyPayGross; s.PayCash = cyPayCash; s.Fees = cyFeeEval + cyFeeAct; s.SimNet = cyPayCash - s.Fees;
				s.SimMonths = cyFirst != DateTime.MinValue ? Math.Max(1.0, (cyLastDay - cyFirst).TotalDays / 30.44) : 1; s.SimPerMonth = s.SimNet / s.SimMonths;
				s.Events.AddRange(cyEvRows.Count > 60 ? cyEvRows.GetRange(cyEvRows.Count - 60, 60) : cyEvRows);
				s.CashDays.AddRange(cashDays); s.CashVals.AddRange(cashVals);
				if (!cyStarted) s.SimStatus = string.Format("La primera evaluación empieza al terminar el calentamiento ({0}/{1} días)", rthDaysSeen, WarmupDays);
				else if (cy.Alive && !cyFrozen)
				{
					double prof = netPnl - cyBase - cy.Withdrawn;
					s.SimPhase = cy.Funded ? "FONDEADA" : "EVALUACIÓN"; s.SimNumber = cy.Funded ? cyFundN : cyEvalN; s.SimDay = cy.Days + 1;
					s.SimProfit = prof; s.SimTarget = cy.T; s.SimBalance = StartBalance + prof; s.SimLimit = StartBalance + cy.Thr; s.SimCushion = prof - cy.Thr; s.SimDd = cy.D;
					if (cy.Funded) s.SimNext = cy.NextPayout(Usd);
				}
				else s.SimStatus = cyStatus;
			}
			else if (PropMode != NQMasterPropMode.Off) s.SimStatus = PropPreset == NQMasterPropPreset.Manual ? "Para simular retiros y cuentas perdidas elegí un preset de firma (Lucid, MFFU...)." : "Simulación del ciclo apagada (Backtest: simular el ciclo = false).";
			// the real prop account (live, not a Sim account)
			if (State == State.Realtime && !SimAccount && PropMode != NQMasterPropMode.Off && !double.IsNaN(propThr))
			{
				double eq = PropEquity();
				s.RealOn = true; s.RealName = acct; s.RealPhase = PhaseName(PropMode); s.RealBalance = eq; s.RealProfit = eq - StartBalance; s.RealLimit = propThr; s.RealCushion = eq - propThr;
				s.RealToday = double.IsNaN(propDayStart) ? 0 : eq - propDayStart; s.RealDd = PropTrailingDD; s.RealTarget = PropMode == NQMasterPropMode.Eval ? EvalTarget : 0;
				if (PropMode == NQMasterPropMode.Funded) s.RealPayout = (eq - StartBalance >= FundedPayoutAt ? "DISPONIBLE: " : "") + payoutHint;
			}
			foreach (string w in DashWarnings().Split('\\n')) { string x = w.Trim(); if (x.StartsWith("! ")) x = x.Substring(2); if (x.Length > 0) s.Warnings.Add(x); }
			if (edgeAlarm && !s.Warnings.Contains("ALARMA del monitor de borde: revisar antes de seguir")) s.Warnings.Add("ALARMA del monitor de borde: revisar antes de seguir");
			return s;
		}
		private static NQMasterUI.ModuleRow ModRow(string name, bool on, string state, double[] a)
		{
			NQMasterUI.ModuleRow r = new NQMasterUI.ModuleRow(); r.Name = name; r.On = on; r.State = state;
			if (a != null)
			{
				r.Trades = (int)a[0]; r.Wr = a[0] > 0 ? 100 * a[1] / a[0] : 0; r.Pf = a[3] > 0 ? a[2] / a[3] : 0; r.Net = a[2] - a[3];
				r.Trades365 = (int)a[4]; r.Wr365 = a[4] > 0 ? 100 * a[5] / a[4] : 0; r.Pf365 = a[7] > 0 ? a[6] / a[7] : 0; r.Net365 = a[6] - a[7];
			}
			return r;
		}
"""
rep("		private void UpdateDashboard()\n		{\n", PANEL + "		private void UpdateDashboard()\n		{\n			PanelPublish();\n")
# 3. lifecycle: open at go-live, remove at the end
rep("				liveStartPnl = netPnl; liveStartTrades = totalTrades; liveStart = ToEt(Times[0][0]);\n",
    "				liveStartPnl = netPnl; liveStartTrades = totalTrades; liveStart = ToEt(Times[0][0]);\n				PanelOpen();\n")
rep("			else if (State == State.Terminated)\n			{\n", "			else if (State == State.Terminated)\n			{\n				PanelClose();\n")
# 4. property
rep('		[Display(Name = "Imprimir el log en Output", Order = 2, GroupName = "07. Panel")] public bool PrintLog { get; set; }\n',
    '		[Display(Name = "Imprimir el log en Output", Order = 2, GroupName = "07. Panel")] public bool PrintLog { get; set; }\n'
    '		[Display(Name = "Abrir la ventana del panel al pasar a vivo (Ctrl+Shift+P en el gráfico la vuelve a abrir; necesita NQMasterPanel.cs)", Order = 3, GroupName = "07. Panel")] public bool ShowPanelWindow { get; set; }\n')
rep("				PropPreset = NQMasterPropPreset.Manual; CycleSim = true; EvalPrice = 0; ActivationFee = 0;\n",
    "				PropPreset = NQMasterPropPreset.Manual; CycleSim = true; EvalPrice = 0; ActivationFee = 0; ShowPanelWindow = true;\n")
open(P, "w", encoding="utf-8-sig").write(s); print("patched")
