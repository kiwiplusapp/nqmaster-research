"""patch_live_safety.py v2 (2026-10-29, frente 5F: revision de codigo completa de NQMaster.cs, research/mine/code_review_nqmaster_2026-10-29.md).
Aplica sobre NQMaster.cs v4.3 + patch_clock_check.py v3 + patch_open_risk.py v2. Todo lo que puede cambiar ordenes corre SOLO EN VIVO
(State.Realtime), asi el export Off del Strategy Analyzer tiene que salir identico:
 1. Doble salida / overfill (hallazgo alto 1): una ejecucion de salida con mas lotes que los abiertos del modulo -> alerta y aplanado; control por
    barra: lotes de la estrategia que ningun modulo tiene (2 barras) -> alerta y aplanado; ExitModule no manda una segunda salida mientras la
    primera sigue viva; IgnoreOverfill = true (NinjaTrader no termina la estrategia ante un overfill: lo maneja este control).
 2. Estado de la cuenta prop desconocido (hallazgo alto 2): sin archivo de estado legible y con un saldo distinto del inicial -> alerta, el colchon se
    toma chico (tope de riesgo activo) y no se guarda un pico calculado, hasta cargar PropPeakOverride o PropThresholdOverride; aviso en cada sesion
    mientras PropThresholdOverride este cargado.
 3. Terminar con posicion abierta en una cuenta real: alerta sonora y no se borra el archivo de posiciones de la guarda entre cuentas.
 4. Guarda entre cuentas: publica tambien en cada ejecucion (salidas) y, antes de armar el control de sincronizacion, el signo de la posicion de la cuenta.
 5. Monitor de borde: alerta cuando descarta el estado guardado por ser mas viejo que el reconstruido con el historico.
 6. Roll: compara con el dia de operacion de la sesion (antes frenaba una sesion tarde).
 7. Barras tardias: alerta despues de 3 seguidas (reloj de Windows o feed atrasado).
v2 (revision adversarial del parche, 29-oct): el estado desconocido activa el tope de riesgo directamente (la v1 lo hacia bajando el colchon, que no
alcanzaba en Lucid); archivo de estado viejo detectado por el saldo; el override de limite sube el pico guardado; la guarda publica solo la posicion de
la cuenta antes de sincronizar y tambien en OnPositionUpdate; ExitOrd se limpia al pasar a vivo, la salida suprimida se reintenta y hay vigia de salida
trabada; el aplanado escala a Account.Flatten si en 3 barras no queda plano; IgnoreOverfill tambien en Configure y en la linea LIVE; mensajes por motivo.
Idempotente. Run: python3 research/mine/patch_live_safety.py && bash tools/nt8_stub/check.sh NQMaster.cs"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); P = os.path.join(ROOT, "NQMaster.cs")
s = open(P, encoding="utf-8").read()
if "LotOwnershipCheck" in s: print("ya aplicado"); sys.exit(0)
def rep(a, b, n=1):
    global s
    if s.count(a) != n: sys.exit(f"ancla no encontrada ({s.count(a)}): {a[:100]}")
    s = s.replace(a, b)
# 1. overfill / lots without owner
rep("			public bool XStopPrice, XTgtPrice, XExitPending;",
    "			public Order ExitOrd; public int ExitBar = -1; public bool ExitAgain, ExitWarned;	// patch_live_safety.py: the module's last exit order (live only)\n			public bool XStopPrice, XTgtPrice, XExitPending;")
rep("		private int otherDirBar = -1; private bool otherLong, otherShort, otherPosLong, otherPosShort, hedgeFlat;\n",
    "		private int otherDirBar = -1; private bool otherLong, otherShort, otherPosLong, otherPosShort, hedgeFlat;\n		private int ownBars, lateRun, hedgeBars; private bool propStateUnknown; private string hedgeWhy;	// patch_live_safety.py\n")
rep("				RealtimeErrorHandling = RealtimeErrorHandling.IgnoreAllErrors;	// rejections handled in OnOrderUpdate\n",
    "				RealtimeErrorHandling = RealtimeErrorHandling.IgnoreAllErrors;	// rejections handled in OnOrderUpdate\n				IgnoreOverfill = true;	// patch_live_safety.py: an overfill does not stop the strategy (that would cancel the other modules' stops): LotOwnershipCheck flattens\n")
rep("""			if (desyncHalt) return;
			if (fillBip > 0) { ModuleMarketExit(m, Math.Max(1, m.OpenQty > 0 ? m.OpenQty : Position.Quantity), m.Sig + "X"); Log(m.Sig + " exit: " + why); return; }
			if (Position.MarketPosition == MarketPosition.Long) ExitLong(fillBip, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);
			else if (Position.MarketPosition == MarketPosition.Short) ExitShort(fillBip, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);""",
"""			if (desyncHalt) return;
			if (State == State.Realtime && Working(m.ExitOrd)) { m.ExitAgain = true; Log(m.Sig + " exit already working, retried next bar if still needed: " + why); return; }	// patch_live_safety.py
			if (fillBip > 0) { ModuleMarketExit(m, Math.Max(1, m.OpenQty > 0 ? m.OpenQty : Position.Quantity), m.Sig + "X"); Log(m.Sig + " exit: " + why); return; }
			m.ExitBar = CurrentBars[0]; m.ExitAgain = false;
			if (Position.MarketPosition == MarketPosition.Long) m.ExitOrd = ExitLong(fillBip, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);
			else if (Position.MarketPosition == MarketPosition.Short) m.ExitOrd = ExitShort(fillBip, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);""")
rep("""			if (exitMod != null)
			{
				exitMod.OpenQty = Math.Max(0, exitMod.OpenQty - quantity);""",
"""			if (exitMod != null)
			{
				if (State == State.Realtime && quantity > exitMod.OpenQty)	// patch_live_safety.py: more lots exited than the module had = double exit / overfill
				{ Warn("nqm_overfill", string.Format("NQMaster | OVERFILL {0}: {1} x{2} with {3} lots open (modules: {4}) -> flattening this instrument (a reverse position would have no stop)", exitMod.Sig, execution.Order.Name, quantity, exitMod.OpenQty, OwnerList())); hedgeFlat = true; hedgeWhy = "overfill"; }
				exitMod.OpenQty = Math.Max(0, exitMod.OpenQty - quantity);""")
rep("""			if (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) { x.InTrade = false; x.OpenQty = 0; if (fillBip > 0) CancelBrackets(x); }
		}

		private void ProcessClosedTrades()""",
"""			if (Position.MarketPosition == MarketPosition.Flat) foreach (Mod x in mods) { x.InTrade = false; x.OpenQty = 0; if (fillBip > 0) CancelBrackets(x); }
			CrossAccountPublish();	// patch_live_safety.py: exits too (it returns at once outside live / without the guard)
		}

		private void ProcessClosedTrades()""")
rep("""			CheckAccountSync();
			if (desyncHalt) return;
			CrossAccountCancelOpp();
""", """			CheckAccountSync();
			if (desyncHalt) return;
			LotOwnershipCheck();
			ExitRetries();
			CrossAccountCancelOpp();
""")
rep("""		// H2: real session end""", """		// patch_live_safety.py (code review 2026-10-29): lots the strategy holds that no module owns (a double exit / overfill reverses the position
		// with no stop, and the account sync check cannot see it because account and strategy agree) -> 2 bars -> alert and flatten. Live only.
		private void LotOwnershipCheck()
		{
			if (State != State.Realtime || desyncHalt || mods == null) return;
			int strat = SignedQty(Position), own = 0;
			foreach (Mod m in mods) if (m.InTrade && m.OpenQty > 0) own += (m.Dir != 0 ? m.Dir : Math.Sign(strat)) * m.OpenQty;
			if (own == strat) { ownBars = 0; return; }
			if (++ownBars < 2) return;
			ownBars = 0;
			if (!hedgeFlat) Warn("nqm_owner", string.Format("NQMaster | LOTS WITHOUT OWNER for 2 bars: modules {0} ({2}), strategy {1} -> flattening this instrument (a double exit or an overfill left lots without a stop)", own, strat, OwnerList()));
			hedgeFlat = true; hedgeWhy = "lots without owner";
		}
		private string OwnerList() { StringBuilder b = new StringBuilder(); foreach (Mod m in mods) if (m.InTrade && m.OpenQty > 0) b.Append(m.Sig + ":" + (m.Dir * m.OpenQty) + " "); return b.Length > 0 ? b.ToString().TrimEnd() : "none"; }
		// patch_live_safety.py v2: an exit suppressed because the previous one was still working is retried once that one is done; an exit working
		// for 3 bars (not filled, not cancelled) is reported. Live only.
		private void ExitRetries()
		{
			if (State != State.Realtime || desyncHalt || mods == null) return;
			foreach (Mod m in mods)
			{
				if (Working(m.ExitOrd))
				{
					if (!m.ExitWarned && m.ExitBar >= 0 && CurrentBars[0] - m.ExitBar >= 3) { m.ExitWarned = true; Warn("nqm_exitstuck", string.Format("NQMaster | {0} exit order working for 3 bars without a fill: check the Orders tab", m.Sig)); }
					continue;
				}
				m.ExitWarned = false;
				if (m.ExitAgain) { m.ExitAgain = false; if (m.InTrade && m.OpenQty > 0) ExitModule(m, "exit retried (the previous exit was still working)"); }
			}
		}
		// H2: real session end""")
# 2. prop state unknown
rep("""			propLive = true; propPeak = StartBalance; propDayStart = double.NaN; propBestDay = EvalBestDaySoFar;
""", """			propLive = true; propPeak = StartBalance; propDayStart = double.NaN; propBestDay = EvalBestDaySoFar; bool stateOk = false;
""")
rep("""					if (!stalePeak && a.Length > 0 && double.TryParse(a[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) propPeak = Math.Max(propPeak, v);
""", """					if (!stalePeak && a.Length > 0 && double.TryParse(a[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) { propPeak = Math.Max(propPeak, v); stateOk = true; }
					double sc;	// v2: a file older than the last session whose saved balance differs from today's = the account traded elsewhere -> state unknown
					if (stateOk && a.Length >= 6 && fd < prevSessDay && double.TryParse(a[5], NumberStyles.Any, CultureInfo.InvariantCulture, out sc)) { double cnow = double.NaN; try { cnow = AcctCash(); } catch { } if (!double.IsNaN(cnow) && Math.Abs(cnow - sc) > 50) stateOk = false; }
""")
rep("""			if (PropPeakOverride > 0) propPeak = newOverride ? PropPeakOverride : Math.Max(propPeak, PropPeakOverride);
""", """			if (PropPeakOverride > 0) propPeak = newOverride ? PropPeakOverride : Math.Max(propPeak, PropPeakOverride);
			// patch_live_safety.py (code review 2026-10-29): no readable state file and a balance that is not the start balance = the trailing peak is unknown
			double cash0 = double.NaN; try { cash0 = AcctCash(); } catch { }
			propStateUnknown = !stateOk && PropPeakOverride <= 0 && PropThresholdOverride <= 0 && !double.IsNaN(cash0) && cash0 > 0 && Math.Abs(cash0 - StartBalance) > 50;
			if (propStateUnknown) Warn("nqm_prop", string.Format("NQMaster | PROP STATE UNKNOWN for {0}: no readable state file and the balance ({1:0}) is not the start balance, so the trailing-drawdown peak may be wrong. Set PropPeakOverride (the firm's highest end-of-day balance) or PropThresholdOverride (the firm's loss limit). Until then the per-contract risk cap stays on in the funded account and the state is not saved.", Account != null ? Account.Name : "", cash0));
""")
rep("""				PropSave(tday);
				propThr = propPeak >= StartBalance + PropTrailingDD + 100 ? StartBalance + 100 : propPeak - PropTrailingDD;
				if (PropThresholdOverride > 0) propThr = PropThresholdOverride;
""", """				if (!propStateUnknown) PropSave(tday);	// patch_live_safety.py: never persist a peak computed without a state file or an override
				propThr = propPeak >= StartBalance + PropTrailingDD + 100 ? StartBalance + 100 : propPeak - PropTrailingDD;
				if (PropThresholdOverride > 0) propThr = PropThresholdOverride;
				if (State == State.Realtime && PropThresholdOverride > 0) Warn("nqm_thr", string.Format("NQMaster | PropThresholdOverride is set ({0:0}): the loss limit stays fixed and does not follow the trailing drawdown. Clear it once the panel's limit matches the firm's.", PropThresholdOverride));
""")
# 3. terminated with an open position
rep("""				try { if (CrossAccountGuard && PosFile != null && File.Exists(PosFile)) File.Delete(PosFile); } catch { }
""", """				bool openReal = false;	// patch_live_safety.py: stopping with an open position may cancel its stop / target
				try { openReal = wentLive && !desyncHalt && PositionAccount != null && PositionAccount.MarketPosition != MarketPosition.Flat; } catch { }
				if (openReal)
				{
					string om = "NQMaster | STOPPED WITH AN OPEN POSITION on " + Instrument.FullName + ": NinjaTrader may have cancelled its stop / target. Check the Orders tab and protect or close the position NOW.";
					Print(om);
					try { Alert("nqm_stop_open", Priority.High, om, NinjaTrader.Core.Globals.InstallDir + @"\\sounds\\Alert1.wav", 0, Brushes.Red, Brushes.White); } catch { }
				}
				try { if (!openReal && CrossAccountGuard && PosFile != null && File.Exists(PosFile)) File.Delete(PosFile); } catch { }
""")
# 4. cross-account publish: account position before the sync guard is armed
rep("""				int pos = Position.MarketPosition == MarketPosition.Long ? 1 : (Position.MarketPosition == MarketPosition.Short ? -1 : 0);
				foreach (Mod m in mods) if (pos == 0 && m.InTrade && m.Dir != 0) pos = m.Dir;	// fill not yet in Position
				bool l = pos == 1, sh = pos == -1;
				foreach (Mod m in mods)
				{
					if (m.InTrade) { if (m.Dir == 1) l = true; else if (m.Dir == -1) sh = true; }
					if (Working(m.Entry) && !zombies.Contains(m.Entry)) { if (m.Dir == 1) l = true; else if (m.Dir == -1) sh = true; }
				}
""", """				int pos = Position.MarketPosition == MarketPosition.Long ? 1 : (Position.MarketPosition == MarketPosition.Short ? -1 : 0);
				bool preSync = AccountSyncGuard && !syncArmed;	// patch_live_safety.py v2: before the sync guard is armed the strategy's (historical, virtual) position is not the account's
				if (preSync) { try { pos = Math.Sign(SignedQty(PositionAccount)); } catch { } }
				else foreach (Mod m in mods) if (pos == 0 && m.InTrade && m.Dir != 0) pos = m.Dir;	// fill not yet in Position
				bool l = pos == 1, sh = pos == -1;
				if (!preSync) foreach (Mod m in mods)
				{
					if (m.InTrade) { if (m.Dir == 1) l = true; else if (m.Dir == -1) sh = true; }
					if (Working(m.Entry) && !zombies.Contains(m.Entry)) { if (m.Dir == 1) l = true; else if (m.Dir == -1) sh = true; }
				}
""")
# 5. edge monitor discarded state
rep("""				if (d < edgeLastDate) return;			// the history rebuild is newer
""", """				if (d < edgeLastDate) { Warn("nqm_edge_state", string.Format("NQMaster | edge monitor: the saved state ({0}) is older than the history rebuild ({1}) and was ignored: the CUSUM comes from the loaded history only. Keep NinjaTrader running at 18:00 ET so the state is saved every session.", d, edgeLastDate)); return; }	// patch_live_safety.py
""")
# 6. roll on the session's trading day
rep("""				return ToEt(NowClock()).Date >= roll.Date;
""", """				DateTime etn = ToEt(NowClock()); return (etn.Hour >= 18 ? etn.Date.AddDays(1) : etn.Date) >= roll.Date;	// patch_live_safety.py: the session's trading day (it stopped one session late)
""")
# 7. late bars
rep("""			if (LateBar(Time[0])) { Log("bar processed late (session break / data gap): no new entries on it"); UpdateDashboard(); return; }
""", """			if (LateBar(Time[0]))
			{
				Log("bar processed late (session break / data gap): no new entries on it");
				if (++lateRun == 3) Warn("nqm_late", "NQMaster | 3 bars in a row processed late (> 120 s after the bar): no new entries. Synchronize the Windows clock and check the data feed.");	// patch_live_safety.py
				UpdateDashboard(); return;
			}
			lateRun = 0;
""")
# --- v2 additions ---
# B / C. unknown state: per-contract risk cap on in the funded account (the v1 lowered the cushion, which did not reach Lucid's thresholds); no step-up
rep("""			&& propCushion < (PropMode == NQMasterPropMode.Eval ? EvalRiskCapCushion : FundedRiskCapCushion); } }""",
    """			&& (propCushion < (PropMode == NQMasterPropMode.Eval ? EvalRiskCapCushion : FundedRiskCapCushion) || (propStateUnknown && PropMode == NQMasterPropMode.Funded)); } }	// patch_live_safety.py v2""")
rep("""		private bool StepUpOn { get { return PropMode == NQMasterPropMode.Funded && FundedStepUpCushion > 0 && !double.IsNaN(propCushion) && propCushion >= FundedStepUpCushion; } }""",
    """		private bool StepUpOn { get { return PropMode == NQMasterPropMode.Funded && FundedStepUpCushion > 0 && !double.IsNaN(propCushion) && propCushion >= FundedStepUpCushion && !propStateUnknown; } }""")
# D. PropSave stores the balance seen (field 5) to detect a stale file
rep("""			try { File.WriteAllText(PropFile, string.Format(CultureInfo.InvariantCulture, "{0:0.00};{1};{2:0.00};{3:0.00};{4:0.00}", propPeak, tradeDay, propDayStart, propBestDay, PropPeakOverride)); } catch { }""",
    """			double eqs = double.NaN; try { eqs = PropEquity(); } catch { }	// patch_live_safety.py v2: field 5 = balance seen (stale-file check)
			try { File.WriteAllText(PropFile, string.Format(CultureInfo.InvariantCulture, "{0:0.00};{1};{2:0.00};{3:0.00};{4:0.00};{5:0.00}", propPeak, tradeDay, propDayStart, propBestDay, PropPeakOverride, eqs)); } catch { }""")
# E. a threshold override raises the saved peak accordingly (otherwise clearing it brings back the wrong peak)
rep("""				if (!propStateUnknown) PropSave(tday);""",
    """				if (propLive && PropThresholdOverride > 0) propPeak = Math.Max(propPeak, PropThresholdOverride + PropTrailingDD);	// patch_live_safety.py v2
				if (!propStateUnknown) PropSave(tday);""")
# G. ExitOrd from the history is not a live order
rep("""				edgeDayQty = Qty(); statQty = Qty();	// review L14
""", """				edgeDayQty = Qty(); statQty = Qty();	// review L14
				foreach (Mod m in mods) { m.ExitOrd = null; m.ExitAgain = false; m.ExitWarned = false; }	// patch_live_safety.py v2: an exit from the history is not a live order
""")
# I. IgnoreOverfill also at Configure, shown in the LIVE line
rep("""			else if (State == State.Configure)
			{
""", """			else if (State == State.Configure)
			{
				IgnoreOverfill = true;	// patch_live_safety.py v2: also here (a template could carry another value); LotOwnershipCheck handles an overfill
""")
rep("""account sync guard {5}", Instrument.FullName, Profile, Contracts, PropMode, MaxOpenContracts, AccountSyncGuard ? "on" : "off"));""",
    """account sync guard {5} | IgnoreOverfill {6}", Instrument.FullName, Profile, Contracts, PropMode, MaxOpenContracts, AccountSyncGuard ? "on" : "off", IgnoreOverfill));""")
# K. publish on every position change too
rep("""		private void ProcessClosedTrades()""", """		protected override void OnPositionUpdate(Position position, double averagePrice, int quantity, MarketPosition marketPosition)
		{
			CrossAccountPublish();	// patch_live_safety.py v2: the strategy position just changed (it returns at once outside live / without the guard)
		}

		private void ProcessClosedTrades()""")
# M. panel warning
rep("""			if (zombieCount > 0) b.AppendLine(string.Format("! {0} órdenes trabadas descartadas (ver Output)", zombieCount));""",
    """			if (propStateUnknown) b.AppendLine("! Estado de la cuenta desconocido: cargá PropPeakOverride con el saldo de cierre más alto de la firma");	// patch_live_safety.py v2
			if (zombieCount > 0) b.AppendLine(string.Format("! {0} órdenes trabadas descartadas (ver Output)", zombieCount));""")
# hedge flatten escalation (live only) and the reason in the log
rep("""			if (hedgeFlat) { if (Position.MarketPosition == MarketPosition.Flat) hedgeFlat = false; else FlattenAll("cross-account hedge guard"); }
""", """			if (hedgeFlat)
			{
				if (Position.MarketPosition == MarketPosition.Flat) { hedgeFlat = false; hedgeBars = 0; hedgeWhy = null; }
				else
				{
					FlattenAll(hedgeWhy ?? "cross-account hedge guard");
					if (State == State.Realtime && ++hedgeBars >= 3)	// patch_live_safety.py v2: the managed exits did not get flat in 3 bars
					{
						hedgeBars = 0;
						try { Account.Flatten(new[] { Instrument }); } catch (Exception ex) { Print("NQMaster | account flatten failed: " + ex.Message); }
						Warn("nqm_flatfail", string.Format("NQMaster | the strategy could not get flat in 3 bars ({0}): the account position of {1} was flattened directly. Check the Positions and Orders tabs.", hedgeWhy ?? "cross-account hedge guard", Instrument.FullName));
					}
				}
			}
""")
open(P, "w", encoding="utf-8").write(s); print("patch_live_safety v2 aplicado")
