"""patch_live_safety.py (2026-10-29, frente 5F: revision de codigo completa de NQMaster.cs, research/mine/code_review_nqmaster_2026-10-29.md).
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
    "			public Order ExitOrd;	// patch_live_safety.py: the module's last exit order (no second exit while it works, live only)\n			public bool XStopPrice, XTgtPrice, XExitPending;")
rep("		private int otherDirBar = -1; private bool otherLong, otherShort, otherPosLong, otherPosShort, hedgeFlat;\n",
    "		private int otherDirBar = -1; private bool otherLong, otherShort, otherPosLong, otherPosShort, hedgeFlat;\n		private int ownBars, lateRun; private bool propStateUnknown;	// patch_live_safety.py\n")
rep("				RealtimeErrorHandling = RealtimeErrorHandling.IgnoreAllErrors;	// rejections handled in OnOrderUpdate\n",
    "				RealtimeErrorHandling = RealtimeErrorHandling.IgnoreAllErrors;	// rejections handled in OnOrderUpdate\n				IgnoreOverfill = true;	// patch_live_safety.py: an overfill does not stop the strategy (that would cancel the other modules' stops): LotOwnershipCheck flattens\n")
rep("""			if (desyncHalt) return;
			if (fillBip > 0) { ModuleMarketExit(m, Math.Max(1, m.OpenQty > 0 ? m.OpenQty : Position.Quantity), m.Sig + "X"); Log(m.Sig + " exit: " + why); return; }
			if (Position.MarketPosition == MarketPosition.Long) ExitLong(fillBip, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);
			else if (Position.MarketPosition == MarketPosition.Short) ExitShort(fillBip, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);""",
"""			if (desyncHalt) return;
			if (State == State.Realtime && Working(m.ExitOrd)) { Log(m.Sig + " exit already working, not sent again: " + why); return; }	// patch_live_safety.py
			if (fillBip > 0) { ModuleMarketExit(m, Math.Max(1, m.OpenQty > 0 ? m.OpenQty : Position.Quantity), m.Sig + "X"); Log(m.Sig + " exit: " + why); return; }
			if (Position.MarketPosition == MarketPosition.Long) m.ExitOrd = ExitLong(fillBip, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);
			else if (Position.MarketPosition == MarketPosition.Short) m.ExitOrd = ExitShort(fillBip, Math.Max(1, Position.Quantity), m.Sig + "X", m.Sig);""")
rep("""			if (exitMod != null)
			{
				exitMod.OpenQty = Math.Max(0, exitMod.OpenQty - quantity);""",
"""			if (exitMod != null)
			{
				if (State == State.Realtime && quantity > exitMod.OpenQty)	// patch_live_safety.py: more lots exited than the module had = double exit / overfill
				{ Warn("nqm_overfill", string.Format("NQMaster | OVERFILL {0}: {1} x{2} with {3} lots open -> flattening this instrument (a reverse position would have no stop)", exitMod.Sig, execution.Order.Name, quantity, exitMod.OpenQty)); hedgeFlat = true; }
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
			if (!hedgeFlat) Warn("nqm_owner", string.Format("NQMaster | LOTS WITHOUT OWNER for 2 bars: modules {0}, strategy {1} -> flattening this instrument (a double exit or an overfill left lots without a stop)", own, strat));
			hedgeFlat = true;
		}
		// H2: real session end""")
# 2. prop state unknown
rep("""			propLive = true; propPeak = StartBalance; propDayStart = double.NaN; propBestDay = EvalBestDaySoFar;
""", """			propLive = true; propPeak = StartBalance; propDayStart = double.NaN; propBestDay = EvalBestDaySoFar; bool stateOk = false;
""")
rep("""					if (!stalePeak && a.Length > 0 && double.TryParse(a[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) propPeak = Math.Max(propPeak, v);
""", """					if (!stalePeak && a.Length > 0 && double.TryParse(a[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) { propPeak = Math.Max(propPeak, v); stateOk = true; }
""")
rep("""			if (PropPeakOverride > 0) propPeak = newOverride ? PropPeakOverride : Math.Max(propPeak, PropPeakOverride);
""", """			if (PropPeakOverride > 0) propPeak = newOverride ? PropPeakOverride : Math.Max(propPeak, PropPeakOverride);
			// patch_live_safety.py (code review 2026-10-29): no readable state file and a balance that is not the start balance = the trailing peak is unknown
			double cash0 = double.NaN; try { cash0 = AcctCash(); } catch { }
			propStateUnknown = !stateOk && PropPeakOverride <= 0 && PropThresholdOverride <= 0 && !double.IsNaN(cash0) && Math.Abs(cash0 - StartBalance) > 50;
			if (propStateUnknown) Warn("nqm_prop", string.Format("NQMaster | PROP STATE UNKNOWN for {0}: no readable state file and the balance ({1:0}) is not the start balance, so the trailing-drawdown peak may be wrong. Set PropPeakOverride (the firm's highest end-of-day balance) or PropThresholdOverride (the firm's loss limit). Until then the cushion is treated as small (risk cap on) and the state is not saved.", Account != null ? Account.Name : "", cash0));
""")
rep("""				PropSave(tday);
				propThr = propPeak >= StartBalance + PropTrailingDD + 100 ? StartBalance + 100 : propPeak - PropTrailingDD;
				if (PropThresholdOverride > 0) propThr = PropThresholdOverride;
""", """				if (!propStateUnknown) PropSave(tday);	// patch_live_safety.py: never persist a peak computed without a state file or an override
				propThr = propPeak >= StartBalance + PropTrailingDD + 100 ? StartBalance + 100 : propPeak - PropTrailingDD;
				if (PropThresholdOverride > 0) propThr = PropThresholdOverride;
				if (State == State.Realtime && PropThresholdOverride > 0) Warn("nqm_thr", string.Format("NQMaster | PropThresholdOverride is set ({0:0}): the loss limit stays fixed and does not follow the trailing drawdown. Clear it once the panel's limit matches the firm's.", PropThresholdOverride));
""")
rep("""				propCushion = eqRef - propThr;
""", """				propCushion = eqRef - propThr;
				if (propStateUnknown) propCushion = Math.Min(propCushion, 0.5 * PropTrailingDD);	// patch_live_safety.py: unknown peak -> small cushion (risk cap on)
""")
# 3. terminated with an open position
rep("""				try { if (CrossAccountGuard && PosFile != null && File.Exists(PosFile)) File.Delete(PosFile); } catch { }
""", """				bool openReal = false;	// patch_live_safety.py: stopping with an open position may cancel its stop / target
				try { openReal = wentLive && !SimAccount && PositionAccount != null && PositionAccount.MarketPosition != MarketPosition.Flat; } catch { }
				if (openReal)
				{
					string om = "NQMaster | STOPPED WITH AN OPEN POSITION on " + Instrument.FullName + ": NinjaTrader may have cancelled its stop / target. Check the Orders tab and protect or close the position NOW.";
					Print(om); try { LogFile(om); } catch { }
					try { Alert("nqm_stop_open", Priority.High, om, NinjaTrader.Core.Globals.InstallDir + @"\\sounds\\Alert1.wav", 0, Brushes.Red, Brushes.White); } catch { }
				}
				try { if (!openReal && CrossAccountGuard && PosFile != null && File.Exists(PosFile)) File.Delete(PosFile); } catch { }
""")
# 4. cross-account publish: account position before the sync guard is armed
rep("""				int pos = Position.MarketPosition == MarketPosition.Long ? 1 : (Position.MarketPosition == MarketPosition.Short ? -1 : 0);
""", """				int pos = Position.MarketPosition == MarketPosition.Long ? 1 : (Position.MarketPosition == MarketPosition.Short ? -1 : 0);
				if (AccountSyncGuard && !syncArmed) { try { pos = Math.Sign(SignedQty(PositionAccount)); } catch { } }	// patch_live_safety.py: the historical (virtual) position is not the account's
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
open(P, "w", encoding="utf-8").write(s); print("patch_live_safety aplicado")
