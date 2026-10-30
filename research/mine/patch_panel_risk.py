"""patch_panel_risk.py (2026-10-30, frente 5E: panel con el riesgo de cuenta). SOLO PANEL: no toca ordenes, estado ni logica de trading.
Aplica sobre NQMaster.cs v4.3 + patch_clock_check v3 + patch_open_risk v2 + patch_live_safety v5 + patch_edge_restore v4.

ESTADO problema 5: el panel ya mostraba saldo, limite, colchon, resultado del dia, objetivo, retiro y monitor de borde, y patch_open_risk
agrego el riesgo abierto. Lo que faltaba para operar la CUENTA REAL sin abrir el Output:
 1. "Estado:" en castellano. Los estados que frenan la operacion salian en ingles ("prop daily stop", "eval target reached"...).
 2. Contratos base del dia y estado del tope de riesgo de la fondeada: si esta activo (colchon chico), se saltean los trades de mas de
    RiskCapPerContract por contrato; si el escalon de contratos esta activo.
 3. Stops del dia de la cuenta (los mismos valores que PropDailyCheck): stop de ganancia (consistencia de Lucid / MFFU en la eval) y
    stop de perdida; "DETENIDO por hoy" cuando salto uno.
 4. Objetivo de la eval con la consistencia: si el mejor dia (incluido hoy) obliga a llegar a mas que EvalTarget, lo muestra (misma
    formula que el chequeo del objetivo).
Idempotente. Run: python3 research/mine/patch_panel_risk.py [NQMaster.cs] && bash tools/nt8_stub/check.sh NQMaster.cs"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "NQMaster.cs")
s = open(P, encoding="utf-8").read()
if "DayStopsText(" in s: print("ya aplicado"); sys.exit(0)
if "atomic save failed" not in s: sys.exit("falta patch_edge_restore.py v4")

def rep(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit("no encontrado (%d): %r" % (n, a[:90]))
    s = s.replace(a, b)

# 1. statuses in Spanish (display only: the internal strings stay as they are)
rep("""				case "trading": return "operando";
				case "waiting": return "esperando datos";
				default: return status;""", """				case "trading": return "operando";
				case "waiting": return "esperando datos";
				// patch_panel_risk.py: the statuses that stop trading, in Spanish (display only)
				case "NEWS BLACKOUT": return "noticia de alto impacto: sin entradas";
				case "ACCOUNT / STRATEGY POSITION MISMATCH - see Output": return "LA CUENTA Y LA ESTRATEGIA NO COINCIDEN: ver Output";
				case "the account refuses orders - see Output": return "la cuenta rechaza órdenes: ver Output";
				case "holiday / half-day session: no trading": return "feriado o media sesión: no opera";
				case "ROLL DATE: move the strategy to the next contract": return "FECHA DE ROLL: pasá la estrategia al contrato siguiente";
				case "FOMC day: no trading": return "día de FOMC: no opera";
				case "eval target reached": return "objetivo de la eval alcanzado: no opera";
				case "drawdown guard": return "guarda de drawdown: detenida";
				case "daily loss limit": return "límite de pérdida diaria: sin entradas hasta mañana";
				case "prop daily stop": return "stop del día de la cuenta: sin entradas hasta mañana";
				case "MANUAL PAUSE (file)": return "PAUSA MANUAL (archivo de pausa)";
				case "EDGE MONITOR ALARM - review before trading": return "ALARMA DEL MONITOR DE BORDE: revisar antes de operar";
				case "another account holds the opposite NQ position / entry (cross-account guard)": return "otra cuenta del grupo tiene la posición opuesta (guarda entre cuentas)";
				default:
					if (status.StartsWith("low volatility (ATR ")) return "volatilidad baja: no opera " + status.Substring("low volatility ".Length);
					return status;""")

# 2-4. real account section
rep("""				b.AppendLine(string.Format("Saldo {0} ({1})  ·  límite {2}  ·  colchón {3}", Usd(eq), Usd(eq - StartBalance), Usd(propThr), Usd(eq - propThr)));
				double pstR = PnlAtStops(true);""", """				b.AppendLine(string.Format("Saldo {0} ({1})  ·  límite {2}  ·  colchón {3}", Usd(eq), Usd(eq - StartBalance), Usd(propThr), Usd(eq - propThr)));
				b.AppendLine(RiskLine());	// patch_panel_risk.py
				double pstR = PnlAtStops(true);""")
rep("""				if (!double.IsNaN(propDayStart)) b.AppendLine("Hoy: " + Usd(eq - propDayStart));
				if (eq <= propThr)""", """				if (!double.IsNaN(propDayStart)) b.AppendLine("Hoy: " + Usd(eq - propDayStart) + DayStopsText());	// patch_panel_risk.py: the day's stops
				if (eq <= propThr)""")
rep("""				if (PropMode == NQMasterPropMode.Eval && EvalTarget > 0) b.AppendLine(string.Format("Objetivo: {0} de {1}", Usd(eq - StartBalance), Usd(EvalTarget)));""",
    """				if (PropMode == NQMasterPropMode.Eval && EvalTarget > 0)
				{	// patch_panel_risk.py: the consistency rule raises the target (same formula as the eval target check)
					double best = Math.Max(propBestDay, double.IsNaN(propDayStart) ? 0 : eq - propDayStart), needT = EvalTarget;
					if (ConsistencyPct > 0) needT = Math.Max(needT, best * 100.0 / ConsistencyPct);
					b.AppendLine(string.Format("Objetivo: {0} de {1}{2}", Usd(eq - StartBalance), Usd(needT),
						needT > EvalTarget + 0.5 ? string.Format("  (el mejor día, {0}, obliga a más que {1} por la consistencia)", Usd(best), Usd(EvalTarget)) : ""));
				}""")
rep("""		private string DashWarnings()""", """		// patch_panel_risk.py: base contracts of the day and the funded risk cap / step-up state (display only)
		private string RiskLine()
		{
			string r = string.Format("Contratos base hoy {0}", Math.Max(1, edgeDayQty));
			if (PropMode == NQMasterPropMode.Funded && RiskCapPerContract > 0)
				r += RiskCapActive ? string.Format("  ·  tope de riesgo ACTIVO: se saltean los trades de más de {0} por contrato", Usd(RiskCapPerContract))
					: string.Format("  ·  tope de riesgo apagado (se activa con colchón menor a {0})", Usd(FundedRiskCapCushion));
			if (StepUpOn) r += "  ·  escalón de contratos activo";
			return r;
		}
		// patch_panel_risk.py: the account's daily stops, the same values PropDailyCheck uses (display only)
		private string DayStopsText()
		{
			bool ev = PropMode == NQMasterPropMode.Eval;
			double ls = ev ? EvalDailyStop : (PropMode == NQMasterPropMode.Funded && DailyLossPerContract > 0 ? DailyLossPerContract * Math.Max(1, edgeDayQty) : 0);
			double ps = ev ? EvalProfitStop : (PropMode == NQMasterPropMode.Funded ? FundedProfitStop : 0);
			string t = "";
			if (ps > 0) t += string.Format("  ·  stop de ganancia del día en +{0}{1}", Usd(ps), ev ? " (consistencia)" : "");
			if (ls > 0) t += string.Format("  ·  stop de pérdida del día en {0}", Usd(-ls));
			if (propStopped) t += "  ·  DETENIDO por hoy (saltó un stop del día)";
			return t;
		}
		private string DashWarnings()""")
open(P, "w", encoding="utf-8").write(s)
print("patch_panel_risk aplicado")
