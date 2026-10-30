"""patch_edge_restore.py (2026-10-30, frente 5F: revision de codigo completa de NQMaster.cs, hallazgo medio del monitor de borde,
docs/experimentos/revisiones/codigo_2026-10-29/code_review_nqmaster_2026-10-29.md).
Aplica sobre NQMaster.cs v4.3 + patch_clock_check.py v3 + patch_open_risk.py v2 + patch_live_safety.py v2.

Problema: el estado del monitor de borde solo se guardaba en vivo al empezar cada sesion. Si NinjaTrader no corria a las 18:00 ET, al volver
el historico cerraba ese dia, la reconstruccion quedaba mas nueva que el archivo y el archivo se descartaba: el CUSUM quedaba solo con el
historico cargado (Days to load 120). Desde ~feb-2027 ese historico ya no llega a EdgeMonitorStart (2026-10-05) y el CUSUM pasa a ser una
ventana movil de ~84 sesiones, donde la alarma (h 26,93, ~7 meses de mediana con el edge en cero) casi no puede saltar. Ademas el archivo es
por cuenta: cada eval nueva arrancaba sin el estado.

Cambios (solo el monitor de borde; nada cambia trades del backtest: el historico sigue la misma maquina de estados y el estado solo se toca
al pasar a vivo):
 1. EdgeStep: la maquina de estados de EdgeDayClose (modo defensivo, CUSUM, aviso, alarma) en una funcion, para usarla igual en la
    reposicion. El z se calcula tambien en los dias del modo defensivo (antes no hacia falta). Ya no se guarda en medio del modo defensivo:
    se guarda al final, con el estado ya actualizado (la version vieja podia dejar un archivo con alarma y sin modo defensivo, y al
    reiniciar ese dia la alarma quedaba trabada para siempre).
 2. Durante el historico se anota (fecha, z) de cada dia contado y el primer dia con ATR valido (desde donde el historico cubre).
 3. EdgeRestore: parte del estado guardado y le vuelve a aplicar los dias del historico posteriores a su fecha (antes lo descartaba). Si
    el historico empieza despues de la fecha guardada, avisa del hueco. Un archivo con alarma y sin modo defensivo (el caso del punto 1) se
    corrige al leerlo.
 4. Sin archivo propio utilizable (cuenta nueva, otra PC, otro EdgeMonitorStart): una cuenta real toma el estado mas reciente de otra
    cuenta real (no Sim / Playback) con el mismo perfil y la misma fecha de inicio; si hay empate de fecha, el mas severo (modo defensivo,
    alarma, CUSUM mas alto). Sim / Playback no lo hacen, y un estado con fecha posterior a los datos cargados (Playback) se ignora.
 5. Guarda el estado al pasar a vivo (asi queda al dia aunque NinjaTrader nunca este corriendo a las 18:00 ET).
Idempotente. Run: python3 research/mine/patch_edge_restore.py [NQMaster.cs] && bash tools/nt8_stub/check.sh NQMaster.cs"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "NQMaster.cs")
s = open(P, encoding="utf-8").read()
if "EdgeStep(" in s: print("ya aplicado"); sys.exit(0)
if "LotOwnershipCheck" not in s: print("falta patch_live_safety.py"); sys.exit(1)

def rep(a, b):
    global s
    n = s.count(a)
    if n != 1: print("no encontrado (%d): %r" % (n, a[:90])); sys.exit(1)
    s = s.replace(a, b)

# --- 1 + 2: EdgeDayClose -> z for every counted day, history record, EdgeStep
i0 = s.index("		private void EdgeDayClose(DateTime etNow)\n")
i1 = s.index("			edgeDayRth = false;\n		}\n", i0) + len("			edgeDayRth = false;\n		}\n")
old = s[i0:i1]
for frag in ("if (edgeFbLeft > 0)", "edgeFbLeft--; edgeLastDate = DateKey(edgeDayDate); EdgeSave();", "double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);",
             "edgeFbOff = FallbackList(edgeDayDate.Year);", "if (State == State.Realtime) EdgeSave();"):
    if frag not in old: print("EdgeDayClose distinto de lo esperado: falta %r" % frag); sys.exit(1)
new = """		private void EdgeDayClose(DateTime etNow)
		{
			bool counted = EdgeMonitor && edgeDayRth && edgeDayTradable && edgeDayDate != DateTime.MinValue && !double.IsNaN(todayAtr) && todayAtr > 0
				&& !(MinAtrPoints > 0 && todayAtr < MinAtrPoints);
			if (State != State.Realtime && edgeCoverFrom == 0 && edgeDayDate != DateTime.MinValue && !double.IsNaN(todayAtr) && todayAtr > 0) edgeCoverFrom = DateKey(edgeDayDate);	// patch_edge_restore.py
			DateTime st;
			if (counted && DateTime.TryParseExact(EdgeMonitorStart ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) && edgeDayDate >= st)
			{
				double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);
				if (State != State.Realtime) { edgeHistD.Add(DateKey(edgeDayDate)); edgeHistZ.Add(z); }	// patch_edge_restore.py: replayed over a saved state at go-live
				EdgeStep(edgeDayDate, z);
			}
			if (State == State.Realtime) EdgeSave();
			edgeDayRth = false;
		}
		// patch_edge_restore.py: one counted day of the edge monitor (the same state machine for the live day close and for the replay at go-live)
		private void EdgeStep(DateTime day, double z)
		{
			if (double.IsNaN(edgeK)) EdgeParams();
			if (edgeFbLeft > 0)
			{
				// review-set fallback running: the monitor rests (research/mine/os_adapt.py), then resets and the full profile returns
				edgeFbLeft--; edgeLastDate = DateKey(day);
				if (edgeFbLeft == 0) { edgeAlarm = false; edgeS = 0; edgeFbOff = null; Warn("nqm_edge_fb", "NQMaster | edge-monitor fallback finished: full profile again, CUSUM reset."); }
				return;
			}
			edgeS = Math.Max(0.0, edgeS + edgeK - z); edgeDays++; edgeLastDate = DateKey(day);
			if (edgeS <= 0) edgeWarned = false;
			if (!edgeWarned && !edgeAlarm && edgeHw > 0 && edgeS > edgeHw)
			{
				edgeWarned = true;
				Warn("nqm_edge_w", string.Format("NQMaster | EDGE MONITOR WARNING {0}: results are running below the backtest ({1:0}% of the alarm level). Alert only: nothing changes; ~1 in 4 years gives a warning by chance.",
					day.ToString("yyyy-MM-dd"), 100 * edgeS / edgeH));
			}
			if (PrintLog) Print(string.Format("{0} | NQM | EDGE day {1}: z {2:0.000} | CUSUM {3:0.00} / {4:0.00} ({5:0}%)", day.ToString("yyyy-MM-dd"), edgeDays, z, edgeS, edgeH, 100 * edgeS / edgeH));
			if (!edgeAlarm && edgeS > edgeH)
			{
				edgeAlarm = true; edgePaused = EdgeMonitorPause;
				string act = EdgeMonitorPause ? "New entries paused. Review, then set a new 'Edge monitor start date' to resume." : "Alert only (pause and fallback are off).";
				if (!EdgeMonitorPause && EdgeAlarmFallback && EdgeFallbackDays > 0)
				{
					edgeFbOff = FallbackList(day.Year); edgeFbLeft = EdgeFallbackDays; edgeS = 0;
					act = edgeFbOff.Count == 0 ? string.Format("Fallback: the yearly review keeps every module, so nothing changes for {0} days (alert only)." , EdgeFallbackDays)
						: string.Format("Fallback for {0} trading days: modules off = {1}; then the full profile returns.", EdgeFallbackDays, string.Join(" ", edgeFbOff.ToArray()));
				}
				Warn("nqm_edge", string.Format("NQMaster | EDGE MONITOR ALARM {0}: live results are no longer consistent with the backtested edge ({1} days counted). {2}",
					day.ToString("yyyy-MM-dd"), edgeDays, act));
			}
		}
"""
# the alarm / warning texts must be the ones of the current file (only edgeDayDate -> day)
for frag in ("EDGE MONITOR WARNING {0}: results are running below the backtest", "EDGE MONITOR ALARM {0}: live results are no longer consistent",
             "edge-monitor fallback finished: full profile again, CUSUM reset.", "Fallback: the yearly review keeps every module"):
    if frag not in old: print("texto distinto: %r" % frag); sys.exit(1)
s = s[:i0] + new + s[i1:]

# --- 3 + 4 + 5: EdgeRestore
j0 = s.index("		private void EdgeRestore()\n")
j1 = s.index("		private void EdgeDayClose(DateTime etNow)\n", j0)
oldr = s[j0:j1]
if "is older than the history rebuild" not in oldr: print("EdgeRestore distinto de lo esperado"); sys.exit(1)
newr = """		// patch_edge_restore.py: days the loaded history closed (date key, z), and the first day with a valid ATR (where the history covers from)
		private List<int> edgeHistD = new List<int>(); private List<double> edgeHistZ = new List<double>(); private int edgeCoverFrom;
		private bool EdgeFits(string[] p) { return p != null && p.Length >= 9 && p[0] == Profile.ToString() && p[8] == (EdgeMonitorStart ?? ""); }
		private static int EdgeRank(string[] p) { return p[5] != "0" && p[5] != "" ? 2 : (p[4] == "1" ? 1 : 0); }
		// a new account (a new eval, another PC): the newest state of another real account with the same profile and start date
		private string[] EdgeSibling(out string src)
		{
			src = null; string[] best = null;
			try
			{
				string own = EdgeFile;
				foreach (string f in Directory.GetFiles(Core.Globals.UserDataDir, "nqmaster_edge_*.txt"))
				{
					string n = Path.GetFileName(f);
					if (string.Equals(n, Path.GetFileName(own), StringComparison.OrdinalIgnoreCase) || n.StartsWith("nqmaster_edge_Sim") || n.StartsWith("nqmaster_edge_Playback")) continue;
					string[] p; try { p = File.ReadAllText(f).Split(';'); } catch { continue; }
					if (!EdgeFits(p)) continue;
					int d, bd = 0; double sv, bs = 0;
					if (!int.TryParse(p[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out d) || !double.TryParse(p[2], NumberStyles.Any, CultureInfo.InvariantCulture, out sv)) continue;
					if (best != null) { int.TryParse(best[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out bd); double.TryParse(best[2], NumberStyles.Any, CultureInfo.InvariantCulture, out bs); }
					if (best == null || d > bd || (d == bd && (EdgeRank(p) > EdgeRank(best) || (EdgeRank(p) == EdgeRank(best) && sv > bs)))) { best = p; src = n; }
				}
			}
			catch { }
			return best;
		}
		private void EdgeRestore()
		{
			if (!EdgeMonitor || EdgeFile == null) return;
			try
			{
				string src = Path.GetFileName(EdgeFile); string[] p = null;
				if (File.Exists(EdgeFile))
				{
					p = File.ReadAllText(EdgeFile).Split(';');
					if (!EdgeFits(p)) { Print("NQMaster | edge monitor: saved state is for another profile or start date - ignored."); p = null; }
				}
				if (p != null && curSessDay > 0 && int.Parse(p[1], CultureInfo.InvariantCulture) > curSessDay) { Print("NQMaster | edge monitor: saved state is newer than the loaded data (Playback?) - ignored."); p = null; }
				if (p == null && !SimAccount)	// Sim / Playback never take another account's state (a Playback runs on past dates)
				{
					p = EdgeSibling(out src);
					if (p != null) Print("NQMaster | edge monitor: no saved state for this account; starting from the one of " + src);
				}
				if (p == null)
				{
					DateTime st;
					if (DateTime.TryParseExact(EdgeMonitorStart ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) && firstBarDate > DateKey(st))
						Warn("nqm_edge_hist", string.Format("NQMaster | edge monitor: the loaded history starts after the monitor start date ({0}) and no saved state exists, so it only counts {1} days. Load data from the start date or keep NinjaTrader running.", EdgeMonitorStart, edgeDays));
				}
				else
				{
					int d = int.Parse(p[1], CultureInfo.InvariantCulture);
					edgeLastDate = d; edgeS = double.Parse(p[2], CultureInfo.InvariantCulture); edgeDays = int.Parse(p[3], CultureInfo.InvariantCulture);
					edgeAlarm = p[4] == "1"; edgeFbLeft = int.Parse(p[5], CultureInfo.InvariantCulture); edgeWarned = p[7] == "1";
					edgeFbOff = new List<string>(); foreach (string x in p[6].Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries)) edgeFbOff.Add(x);
					// a file written by the old code on the day its fallback ended: alarm on, fallback over -> the reset it missed
					if (edgeAlarm && edgeFbLeft == 0 && !EdgeMonitorPause && EdgeAlarmFallback && EdgeFallbackDays > 0) { edgeAlarm = false; edgeS = 0; edgeFbOff = null; }
					edgePaused = edgeAlarm && EdgeMonitorPause;
					// the days the loaded history closed after the saved state: replayed with the same state machine (before, the saved state was dropped)
					int n = 0;
					for (int i = 0; i < edgeHistD.Count; i++)
						if (edgeHistD[i] > d) { int k = edgeHistD[i]; EdgeStep(new DateTime(k / 10000, k / 100 % 100, k % 100), edgeHistZ[i]); n++; }
					Print(string.Format("NQMaster | edge monitor state restored ({0}, {1}){2}: CUSUM {3:0.00}, {4} days{5}", d, src,
						n > 0 ? string.Format(" + {0} days from the loaded history", n) : "", edgeS, edgeDays, edgeFbLeft > 0 ? ", fallback " + edgeFbLeft + " days left" : ""));
					// the loaded history starts after the next weekday of the saved state: the days in between are not counted
					DateTime dd = new DateTime(d / 10000, d / 100 % 100, d % 100).AddDays(1);
					while (dd.DayOfWeek == DayOfWeek.Saturday || dd.DayOfWeek == DayOfWeek.Sunday) dd = dd.AddDays(1);
					if (edgeCoverFrom > DateKey(dd))
						Warn("nqm_edge_gap", string.Format("NQMaster | edge monitor: the saved state ends on {0} but the loaded history only covers from {1}: the days in between are not counted. Raise Days to load so the history reaches the saved date.", d, edgeCoverFrom));
				}
			}
			catch (Exception e) { Print("NQMaster | edge monitor state not restored: " + e.Message); }
			EdgeSave();	// patch_edge_restore.py: the state is current even if NinjaTrader is never running at 18:00 ET
		}
"""
s = s[:j0] + newr + s[j1:]
open(P, "w", encoding="utf-8").write(s)
print("patch_edge_restore aplicado")
