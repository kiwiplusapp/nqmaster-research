"""2026-10-21 dashboard + account-cycle simulation + configuration cleanup (Federico: 'a better, professional dashboard that computes
payouts, shows them, whether accounts burned and how many (buying an eval the next day); audit the calculations; remove what does
not work from the settings'). Applies to NQMaster.cs (backup NQMaster_backup_pre_dashboard.cs). The C# pieces live in
research/mine/dash_parts/ (cycle.cs, dash.cs); PropCycle was inserted before and is audited by tools/propcycle_test/run_test.py."""
import os, re, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, "NQMaster.cs"); PARTS = os.path.join(ROOT, "research", "mine", "dash_parts")
s = open(P, encoding="utf-8-sig").read()
if "private void CycleInit()" in s: raise SystemExit("already patched")
shutil.copy(P, os.path.join(ROOT, "NQMaster_backup_pre_dashboard.cs"))
def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (n, old[:90])
    s = s.replace(old, new)
cycle = open(os.path.join(PARTS, "cycle.cs"), encoding="utf-8").read()
dash = open(os.path.join(PARTS, "dash.cs"), encoding="utf-8").read()
# 1. cycle code after PropCycle, new dashboard replaces the old one
rep("		// </propcycle>\n", "		// </propcycle>\n" + cycle)
i = s.index("		private void UpdateDashboard()"); j = s.index('Draw.TextFixed(this, "NQM_Dash", txt', i); j = s.index("		}\n", j) + 4
s = s[:i] + dash + s[j:]
# 2. Sim / Playback account: virtual account equity (the simulated seat), never Sim101's cash
i = s.index("		// 2026-10-21: realtime prop equity comes from the account's cash."); j = s.index("		private double PropEquity()", i)
s = s[:i] + """		// 2026-10-21: realtime prop equity comes from the account's cash. On a NinjaTrader simulation / playback account (Sim101 starts at
		// $100,000 and keeps its own history) that cash has nothing to do with the prop account (Federico's chart: Sim at $51,426 -> cushion
		// $26,326 on a 25K preset), so Sim/Playback accounts use the strategy's own account: start balance + its P&L since the simulated
		// account started - simulated payouts (the account-cycle simulation keeps running live there). Real prop accounts are read as is.
		private bool SimAccount { get { string n = Account != null ? Account.Name ?? "" : ""; return n.StartsWith("Sim") || n.StartsWith("Playback"); } }
		private double AcctCash()
		{
			if (SimAccount) return StartBalance + netPnl - CyOffset();
			return Account.Get(AccountItem.CashValue, Currency.UsDollar);
		}

""" + s[j:]
rep("			return StartBalance + netPnl;\n		}\n		private void PropGoLive()", "			return StartBalance + netPnl - CyOffset();\n		}\n		private void PropGoLive()")
rep("				: StartBalance + netPnl + (Position.MarketPosition", "				: StartBalance + netPnl - CyOffset() + (Position.MarketPosition")
rep("now = Math.Min(now, StartBalance + netPnl + Position.GetUnrealizedProfitLoss", "now = Math.Min(now, StartBalance + netPnl - CyOffset() + Position.GetUnrealizedProfitLoss")
rep("			if (PropMode == NQMasterPropMode.Off) return;\n			propLive = true;", "			if (PropMode == NQMasterPropMode.Off) return;\n			if (SimAccount) return;	// Sim / Playback: keep the backtest's account state (no prop file)\n			propLive = true;")
rep("				if (PropThresholdOverride > 0) propThr = PropThresholdOverride;\n", "				if (PropThresholdOverride > 0) propThr = PropThresholdOverride;\n				if (CyLive) { propPeak = StartBalance + cy.Pk; propThr = StartBalance + cy.Thr; }	// simulated seat: the audited rules engine\n")
# 3. hooks
rep("				dayStartPnl = netPnl; dayStopped = false;\n", "				StatDayClose();\n				dayStartPnl = netPnl; dayStopped = false;\n")
rep("				EvalSessionStart(tradeDay);\n", "				EvalSessionStart(tradeDay);\n				CycleSessionStart(tradeDay);\n")
rep("			AccountGuard();\n			DailyLossCheck();\n			PropDailyCheck();\n", "			AccountGuard();\n			DailyLossCheck();\n			PropDailyCheck();\n			CycleBar();\n")
rep('			if (targetHit) { status = "eval target reached"; return false; }', '			if (cyHalt) { status = cyStatus.Length > 0 ? cyStatus : "simulaci\\u00f3n de cuenta: sin operar"; return false; }\n			if (targetHit) { status = "eval target reached"; return false; }')
rep("			if (EvalTarget > 0 && !targetHit && PropMode != NQMasterPropMode.Funded)\n", "			if (EvalTarget > 0 && !targetHit && PropMode != NQMasterPropMode.Funded && !cyOn)\n")
rep("				totalTrades++; netPnl += pnl;\n", "				totalTrades++; netPnl += pnl;\n				StatTrade(pnl, SystemPerformance.AllTrades[i].Commission, Times[0][0]);\n")
rep("				ApplyPreset();\n				newsEt = new List<DateTime>();", "				ForceRetired();\n				CycleInit();\n				newsEt = new List<DateTime>();")
rep("				int hq = Math.Max(1, Qty());\n", "				int hq = Math.Max(1, Qty());\n				CycleGoLive();\n				liveStartPnl = netPnl; liveStartTrades = totalTrades; liveStart = ToEt(Times[0][0]);\n")
# 4. ApplyPreset: quiet re-application at phase changes, Spanish payout texts, LucidPro25K payout level = buffer 1,100 + 1,000 (research X 1,000)
i = s.index("		private void ApplyPreset()"); j = s.index("		private bool RollDue()", i)
body = s[i:j].replace("Print(", "PresetPrint(")
body = body.replace('''			if (UseOrderFlowBoost) PresetPrint("NQMaster | WARNING: UseOrderFlowBoost is ON with an account preset (it is not in the account simulations; it FAILED out of sample)");
			if (VolbReArm) PresetPrint("NQMaster | WARNING: VolbReArm is ON with an account preset (it is not in the account simulations)");
''', "")
body = body.replace('payoutHint = string.Format("profit >= ${0:0} and 5 days >= $150 in the cycle -> request min($1,000, 50% of profit)", FundedPayoutAt);',
                    'payoutHint = string.Format("ganancia >= ${0:0} y 5 d\\u00edas >= $100 en el ciclo -> pedir min($1.000, 50% de la ganancia)", FundedPayoutAt);')
body = body.replace('payoutHint = string.Format("profit >= ${0:0} and 5 days >= $150 in the cycle -> request min($2,000, 50% of profit)", FundedPayoutAt);',
                    'payoutHint = string.Format("ganancia >= ${0:0} y 5 d\\u00edas >= $150 en el ciclo -> pedir min($2.000, 50% de la ganancia)", FundedPayoutAt);')
body = body.replace('payoutHint = string.Format("profit >= ${0:0} and 5 days >= $250 in the cycle -> request min($3,000, 50% of profit)", FundedPayoutAt);',
                    'payoutHint = string.Format("ganancia >= ${0:0} y 5 d\\u00edas >= $250 en el ciclo -> pedir min($3.000, 50% de la ganancia)", FundedPayoutAt);')
body = body.replace('payoutHint = "request min(cap, profit - 1,100) once that amount is >= $1,000, >= 3 days in the cycle, cycle profit >= $500, best day <= 40% of the cycle; cap 1,000 first payout then 1,500";',
                    'payoutHint = "pedir min(tope, ganancia - 1.100) cuando eso sea >= $1.000, con >= 3 d\\u00edas en el ciclo, ganancia del ciclo >= $500 y mejor d\\u00eda <= 40% del ciclo; tope 1.000 el primero, luego 1.500";')
body = body.replace('payoutHint = "request min(cap, profit - 2,100) once that amount is >= $2,000, >= 3 days in the cycle, cycle profit >= $500, best day <= 40% of the cycle; cap 2,000 first payout then 2,500";',
                    'payoutHint = "pedir min(tope, ganancia - 2.100) cuando eso sea >= $2.000, con >= 3 d\\u00edas en el ciclo, ganancia del ciclo >= $500 y mejor d\\u00eda <= 40% del ciclo; tope 2.000 el primero, luego 2.500";')
body = body.replace('payoutHint = string.Format("profit >= ${0:0} -> request it and withdraw down to ${1:0} profit (the rest is the cushion)", FundedPayoutAt, Math.Max(0, FundedPayoutAt - 500));',
                    'payoutHint = string.Format("ganancia >= ${0:0} -> pedir el retiro y dejar ${1:0} de ganancia en la cuenta (es el colch\\u00f3n)", FundedPayoutAt, Math.Max(0, FundedPayoutAt - 500));')
body = body.replace("else { EvalTarget = 0; RiskCapPerContract = 150; FundedRiskCapCushion = 500; FundedPayoutAt = 1500; MaxOpenContracts = 20; FundedProfitStop = 0; Contracts = 1; FundedStepUpCushion = 0; }",
                    "else { EvalTarget = 0; RiskCapPerContract = 150; FundedRiskCapCushion = 500; FundedPayoutAt = PropPreset == NQMasterPropPreset.LucidPro25K ? 2100 : 1500; MaxOpenContracts = 20; FundedProfitStop = 0; Contracts = 1; FundedStepUpCushion = 0; }	// LucidPro25K: buffer 1,100 + first payout 1,000 (research X 1,000)")
for k in ("request min($", "profit - 2,100", "withdraw down to"): assert k not in body, k
body = body.replace('		private string PayoutGeneric() { return string.Format("profit >= ${0:0} -> payout: follow the firm rule in RUNBOOK_OPERACION.md", FundedPayoutAt); }', "")
s = s[:i] + body + s[j:]
rep('		private string PayoutGeneric() { return string.Format("profit >= ${0:0} -> payout: follow the firm rule in RUNBOOK_OPERACION.md", FundedPayoutAt); }',
    '		private string PayoutGeneric() { return string.Format("ganancia >= ${0:0} -> retiro: seguir la regla de la firma (RUNBOOK_OPERACION.md)", FundedPayoutAt); }\n		private void PresetPrint(string m) { if (!presetQuiet) Print(m); }')
# 5. retired settings: hidden in the UI and forced to their off / validated values (old templates cannot switch them back on)
FORCE = """		// ---- retired settings (2026-10-21 cleanup): hidden and forced to the validated values. Each one failed out of sample or was
		// superseded (memory: order-flow boost, adaptive size, late eval size-up, cushion gating, ATR start check, monitor pause, VOLB re-arm,
		// MOM1130 / RSI2 / LF0315 / CA04V / GD03 / ENG26 / ENG10 / LATEFH); the edge parameters keep the values every test used.
		private void ForceRetired()
		{
			EvalMode = false; AdaptiveSize = false; UseOrderFlowBoost = false; EvalCushionFull = 0; FundedCushionSafe = 0; FundedCushionFull = 0; FundedHighFull = true;
			AtrStartMax = 0; EdgeMonitorPause = false; EdgeK = 0; EdgeH = 0; MaxDrawdown = 0; VolbReArm = false;
			UseMom1130 = false; UseRsi2 = false; UseLf0315 = false; UseCa04v = false; UseGd03 = false; UseEng26 = false; UseEng10 = false; UseLateFh = false;
			PullbackMaxRet = 0.44; StopCapAtr = 0.35; OrbPriorCloseAtr = 0.10; VolbBreakEven = true; MomAgreement = true; VolbTrendLastEntry = 1047; MinStopAtr = 0.10;
			UseContextRules = true; UseConfluence = true; IctMultiplier = 2; Vw13Wide = true; Cpi09Multiplier = 4; Mom1030Multiplier = 4;
		}
"""
rep("		private void ApplyPreset()\n", FORCE + "		private void ApplyPreset()\n")
rep("				PropPreset = NQMasterPropPreset.Manual;\n", "				PropPreset = NQMasterPropPreset.Manual; CycleSim = true; EvalPrice = 0; ActivationFee = 0;\n")
# 6. properties: Spanish labels, 8 groups, retired ones hidden
G1, G2, G3, G4, G5, G6, G7, G8 = ("01. Perfil y cuenta", "02. Reglas de la cuenta (las completa el preset)", "03. Operación y seguridad",
    "04. Monitor y revisión", "05. Calendario (fechas extra)", "06. Recuperación (reinicio a mitad de una cuenta real)", "07. Panel",
    "08. Avanzado: módulos (perfil Custom o apagar)")
VIS = {
 "Profile": (G1, 1, "Perfil (Ultra = recomendado)"),
 "PropPreset": (G1, 2, "Firma / cuenta (preset): completa saldo, drawdown, objetivo, tamaño y retiros"),
 "PropMode": (G1, 3, "Fase REAL de la cuenta en vivo (Off = sin reglas de fondeo)"),
 "CycleSim": (G1, 4, "Backtest: simular el ciclo (eval, fondeada, retiros, cuentas perdidas, recompra al día siguiente)"),
 "EvalPrice": (G1, 5, "Precio pagado por cada eval $ (0 = precio de lista; poné el precio con cupón)"),
 "ActivationFee": (G1, 6, "Costo de activación de la fondeada $"),
 "Contracts": (G1, 7, "Contratos por módulo (los presets lo ajustan)"),
 "NightOnWr70": (G1, 8, "WR70Plus: incluir los módulos nocturnos NF05 / LF06 / LF0430"),
 "StartBalance": (G2, 1, "Saldo inicial $"),
 "PropTrailingDD": (G2, 2, "Drawdown máximo $ (al cierre; se fija en saldo inicial + 100)"),
 "EvalTarget": (G2, 3, "Eval: objetivo de ganancia $"),
 "ConsistencyPct": (G2, 4, "Eval: consistencia % (mejor día <= % de la ganancia; 0 = sin regla)"),
 "EvalProfitStop": (G2, 5, "Eval: cortar el día al ganar $ (0 = no)"),
 "EvalDailyStop": (G2, 6, "Eval: cortar el día al perder $ (0 = no)"),
 "EvalHighWrMultiplier": (G2, 7, "Eval: lotes totales de MOM1030 / CPI09 (0 = normal, 4 por contrato)"),
 "FundedPayoutAt": (G2, 8, "Fondeada: pedir retiro con ganancia >= $"),
 "FundedProfitStop": (G2, 9, "Fondeada: cortar el día al ganar $ (0 = no)"),
 "DailyLossLimit": (G2, 10, "Cortar el día al perder $ en trades cerrados (0 = no)"),
 "DailyLossPerContract": (G2, 11, "Fondeada: cortar el día al perder $ por contrato, abierto + cerrado (0 = no)"),
 "RiskCapPerContract": (G2, 12, "Tope de riesgo por trade $ por contrato (activo con colchón chico)"),
 "EvalRiskCapCushion": (G2, 13, "Eval: tope de riesgo activo con colchón < $"),
 "FundedRiskCapCushion": (G2, 14, "Fondeada: tope de riesgo activo con colchón < $"),
 "MaxOpenContracts": (G2, 15, "Máximo de contratos abiertos en la cuenta (0 = sin tope)"),
 "FundedStepUpCushion": (G2, 16, "Fondeada: subir de tamaño con colchón >= $ (0 = no)"),
 "FundedStepUpContracts": (G2, 17, "Fondeada: contratos al subir"),
 "FundedLadderStep": (G2, 18, "Fondeada: escalera, +1 contrato cada $ de colchón (0 = no)"),
 "FundedLadderMax": (G2, 19, "Fondeada: escalera, máximo de contratos"),
 "FlattenTime": (G3, 1, "Hora de cierre de todo (ET, HHmm)"),
 "SkipFomc": (G3, 2, "No operar los días de FOMC"),
 "NewsBlackout": (G3, 3, "Sin posiciones ni órdenes 2 min alrededor de CPI / NFP / actas FOMC (MFFU fondeada)"),
 "MinAtrPoints": (G3, 4, "ATR diario mínimo para operar (puntos; 150 = validado)"),
 "WarmupDays": (G3, 5, "Días de calentamiento (15 = validado)"),
 "PauseFile": (G3, 6, "Archivo de pausa manual (si existe, no abre trades)"),
 "SkipShortSessions": (G3, 7, "No operar feriados ni medias jornadas"),
 "RollGuard": (G3, 8, "Frenar entradas desde la fecha de roll del contrato"),
 "AccountSyncGuard": (G3, 9, "Control: posición de la cuenta = posición de la estrategia"),
 "CrossAccountGuard": (G3, 10, "Control entre cuentas de la misma firma (prohibido el hedge)"),
 "HedgeGroup": (G3, 11, "Grupo de cuentas para ese control (uno por firma; vacío = automático)"),
 "LogToFile": (G3, 12, "Guardar log en archivo (Documentos\\\\NinjaTrader 8\\\\nqmaster_logs)"),
 "EdgeMonitor": (G4, 1, "Monitor de borde (compara el rendimiento en vivo con el backtest)"),
 "EdgeMonitorStart": (G4, 2, "Monitor: fecha de inicio (yyyy-MM-dd)"),
 "EdgeAlarmFallback": (G4, 3, "Con alarma: modo defensivo (apaga los módulos de la revisión anual)"),
 "EdgeFallbackDays": (G4, 4, "Duración del modo defensivo (días operables; 252 = 1 año)"),
 "EdgeFallbackOff": (G4, 5, "Módulos del modo defensivo (vacío = tabla interna)"),
 "InactivityAlarm": (G4, 6, "Alarma si un módulo o una dirección deja de operar"),
 "ModuleHealthReport": (G4, 7, "Reporte por módulo en Output (ganadoras / PF / neto)"),
 "DisableModules": (G4, 8, "Apagar módulos (lista separada por comas, ej. REV06)"),
 "FomcDates": (G5, 1, "Fechas FOMC extra (yyyy-MM-dd, separadas por comas)"),
 "CpiDates": (G5, 2, "Fechas CPI extra (yyyy-MM-dd)"),
 "NewsTimes": (G5, 3, "Noticias Tier-1 extra (yyyy-MM-dd HH:mm ET)"),
 "EvalStartDate": (G6, 1, "Fecha de inicio de la cuenta real (yyyy-MM-dd)"),
 "EvalBestDaySoFar": (G6, 2, "Eval: mejor día hasta ahora $"),
 "PropPeakOverride": (G6, 3, "Saldo de cierre más alto hasta ahora $ (0 = automático)"),
 "PropThresholdOverride": (G6, 4, "Límite de liquidación $ (0 = automático)"),
 "ShowDashboard": (G7, 1, "Mostrar el panel"),
 "PrintLog": (G7, 2, "Imprimir el log en Output"),
}
ADV = [("UseOrb", "ORB60"), ("OrbRangeMin", "ORB: minutos del rango (Custom)"), ("OrbTargetR", "ORB: objetivo en R (Custom)"), ("OrbPullbackFilter", "ORB: solo días de pullback (Custom)"),
       ("UseOrb90", "ORB90"), ("UseMseq", "MSEQ"), ("UseMseqShort", "MSEQS"), ("UseCrt", "CRT11"), ("UseMom11", "MOM11"), ("UseMom13", "MOM13"), ("UseMom1030", "MOM1030"),
       ("UseOn07", "ON07"), ("UseRev06", "REV06"), ("UseLon", "LON (Londres)"), ("UseIct", "ICT"), ("UseVolBreak", "VOLB"), ("UseVw13", "VW13"), ("UseLate15", "LATE15"),
       ("UseNf05", "NF05"), ("UseLf06", "LF06"), ("UseLf0430", "LF0430"), ("UseCpi09", "CPI09 (días de CPI)"), ("SixYearModules", "Módulos de 6 años (SO04 RV11 ORFAIL CAM3)"),
       ("UseSo04", "SO04"), ("UseRv11", "RV11"), ("UseOrFail", "ORFAIL"), ("UseCam3", "CAM3")]
for k, (n, lab) in enumerate(ADV): VIS[n] = (G8, k + 1, lab if "(Custom)" in lab or "Módulos" in lab else lab + " activo")
HIDE = set("EvalMode EvalLateDay EvalLateGoal EvalLateContracts EvalLateMinCushion AdaptiveSize SizeHigh SizeLow SizeDownDrawdown UseOrderFlowBoost OrderFlowCvdMin "
           "OrderFlowBoost OrderFlowStack EvalCushionFull EvalSafeSet FundedCushionSafe FundedCushionFull FundedHighFull AtrStartMax EdgeMonitorPause EdgeK EdgeH "
           "MaxDrawdown DrawdownBuffer VolbReArm UseMom1130 UseRsi2 UseLf0315 UseCa04v UseGd03 UseEng26 UseEng10 UseLateFh PullbackMaxRet StopCapAtr OrbPriorCloseAtr "
           "VolbBreakEven MomAgreement VolbTrendLastEntry MinStopAtr UseContextRules UseConfluence IctMultiplier Vw13Wide Cpi09Multiplier Mom1030Multiplier".split())
NEWP = """		[NinjaScriptProperty][Display(Name = "x", Order = 4, GroupName = "x")] public bool CycleSim { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "x", Order = 5, GroupName = "x")] public double EvalPrice { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "x", Order = 6, GroupName = "x")] public double ActivationFee { get; set; }
"""
rep("		[NinjaScriptProperty][Display(Name = \"Profile\", Order = 0, GroupName = \"00. Profile\")] public NQMasterProfile Profile { get; set; }\n",
    "		[NinjaScriptProperty][Display(Name = \"Profile\", Order = 0, GroupName = \"00. Profile\")] public NQMasterProfile Profile { get; set; }\n" + NEWP)
pat = re.compile(r"^(\t\t)((?:\[[^\n]*?\])+)\s*public (\S+) (\w+) \{ get; set; \}$", re.M)
seen = set()
def fix(m):
    ind, attrs, typ, name = m.groups(); seen.add(name)
    if name in HIDE: return f"{ind}[Browsable(false)] public {typ} {name} {{ get; set; }}"
    if name not in VIS: raise SystemExit("no mapping for " + name)
    g, o, lab = VIS[name]
    rng = re.search(r"\[Range\([^\]]*\)\]", attrs); nsp = "[NinjaScriptProperty]" if "[NinjaScriptProperty]" in attrs else ""
    return f'{ind}{nsp}{rng.group(0) if rng else ""}[Display(Name = "{lab}", Order = {o}, GroupName = "{g}")] public {typ} {name} {{ get; set; }}'
s = pat.sub(fix, s)
missing = (set(VIS) | HIDE) - seen
assert not missing, missing
open(P, "w", encoding="utf-8-sig").write(s)
print("patched; properties", len(seen), "visible", len(seen - HIDE), "hidden", len(HIDE & seen))
