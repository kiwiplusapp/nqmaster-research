"""patch_edge_restore.py v2 (2026-10-30, frente 5F: revision de codigo completa de NQMaster.cs, hallazgo medio del monitor de borde,
docs/experimentos/revisiones/codigo_2026-10-29/code_review_nqmaster_2026-10-29.md).
Aplica sobre NQMaster.cs v4.3 + patch_clock_check.py v3 + patch_open_risk.py v2 + patch_live_safety.py v3.

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
 2. Durante el historico se anota (fecha, z) de cada dia contado y desde que dia cubre el historico (fin del calentamiento).
 3. EdgeRestore: parte del estado guardado y le vuelve a aplicar los dias del historico posteriores a su fecha (antes lo descartaba). Si el
    historico empieza despues de la fecha guardada, avisa del hueco (informativo: con Days to load = 120 fijo esos dias no se recuperan).
 4. Sin archivo propio utilizable (cuenta nueva, otra PC, otro EdgeMonitorStart): una cuenta real toma el estado mas reciente de otra
    cuenta real (no Sim / Playback) con el mismo perfil, la misma fecha de inicio y la misma calibracion (k, h); si hay empate de fecha, el
    mas severo (modo defensivo, alarma, CUSUM mas alto), con aviso.
 5. Guarda el estado al pasar a vivo (asi queda al dia aunque NinjaTrader nunca este corriendo a las 18:00 ET).
v2 (revision adversarial de la v1, 30-oct): un archivo propio que no se puede leer (bloqueado, campos ilegibles) no se pisa: aviso y no se
guarda nada en esa corrida; los descartes y la toma de otra cuenta avisan (Warn); el archivo guarda k y h y se exige la misma calibracion;
la lectura es atomica (TryParse a variables locales); el control "mas nuevo que los datos" usa >= y vale tambien para otras cuentas; la
correccion "alarma sin modo defensivo" solo se aplica al archivo propio y avisa; no se reponen dias del calentamiento; un estado con fecha 0
se compara con EdgeMonitorStart; la reposicion corre antes de PropGoLive (el modo defensivo repuesto apaga sus modulos enseguida); los
avisos de una alarma repuesta dicen que el dia viene del historico; los avisos de hueco y de historico corto ya no proponen subir Days to load.
Idempotente. Run: python3 research/mine/patch_edge_restore.py [NQMaster.cs] && bash tools/nt8_stub/check.sh NQMaster.cs"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "NQMaster.cs")
s = open(P, encoding="utf-8").read()
if "EdgeParse(" in s: print("ya aplicado"); sys.exit(0)
if "EdgeStep(" in s: sys.exit("NQMaster.cs trae la v1 de patch_edge_restore.py: regenerar desde el backup (ver docs/ESTADO.md)")
if "ExitDone(" not in s: sys.exit("falta patch_live_safety.py v3")

def rep(a, b):
    global s
    n = s.count(a)
    if n != 1: sys.exit("no encontrado (%d): %r" % (n, a[:90]))
    s = s.replace(a, b)

# --- EdgeSave: k and h in the file (fields 10-11); nothing is written after an unreadable own file
rep("""			if (State != State.Realtime || !EdgeMonitor || EdgeFile == null) return;
			try
			{
				File.WriteAllText(EdgeFile,""", """			if (State != State.Realtime || !EdgeMonitor || EdgeFile == null || edgeNoSave) return;	// patch_edge_restore.py: edgeNoSave = own file unreadable
			try
			{
				File.WriteAllText(EdgeFile,""")
rep("""edgeWarned ? "1" : "0", EdgeMonitorStart ?? "" }));""",
    """edgeWarned ? "1" : "0", EdgeMonitorStart ?? "", edgeK.ToString("R", CultureInfo.InvariantCulture), edgeH.ToString("R", CultureInfo.InvariantCulture) }));""")

# --- restore before PropGoLive (its PropSessionStart applies the fallback list to the modules)
rep("""				liveStartPnl = netPnl; liveStartTrades = totalTrades; liveStart = ToEt(Times[0][0]);
				PropGoLive();""", """				liveStartPnl = netPnl; liveStartTrades = totalTrades; liveStart = ToEt(Times[0][0]);
				EdgeRestore();	// patch_edge_restore.py: before PropGoLive, whose session start applies a restored fallback to the modules
				PropGoLive();""")
rep("""wentLive = true; PrintModuleReport("loaded history"); EdgeRestore();""", """wentLive = true; PrintModuleReport("loaded history");""")

# --- EdgeDayClose -> z for every counted day, history record, EdgeStep
i0 = s.index("		private void EdgeDayClose(DateTime etNow)\n")
i1 = s.index("			edgeDayRth = false;\n		}\n", i0) + len("			edgeDayRth = false;\n		}\n")
old = s[i0:i1]
for frag in ("if (edgeFbLeft > 0)", "edgeFbLeft--; edgeLastDate = DateKey(edgeDayDate); EdgeSave();", "double z = (netPnl - dayStartPnl) / Math.Max(1, edgeDayQty) / (2.0 * todayAtr);",
             "edgeFbOff = FallbackList(edgeDayDate.Year);", "if (State == State.Realtime) EdgeSave();",
             "EDGE MONITOR WARNING {0}: results are running below the backtest", "EDGE MONITOR ALARM {0}: live results are no longer consistent",
             "edge-monitor fallback finished: full profile again, CUSUM reset.", "Fallback: the yearly review keeps every module"):
    if frag not in old: sys.exit("EdgeDayClose distinto de lo esperado: falta %r" % frag)
new = """		private void EdgeDayClose(DateTime etNow)
		{
			bool counted = EdgeMonitor && edgeDayRth && edgeDayTradable && edgeDayDate != DateTime.MinValue && !double.IsNaN(todayAtr) && todayAtr > 0
				&& !(MinAtrPoints > 0 && todayAtr < MinAtrPoints);
			// patch_edge_restore.py: the first day the history covers = the first day closed with the warm-up done
			if (State != State.Realtime && edgeCoverFrom == 0 && edgeDayDate != DateTime.MinValue && !double.IsNaN(todayAtr) && todayAtr > 0 && atrCount >= AtrMin && rthDaysSeen >= WarmupDays) edgeCoverFrom = DateKey(edgeDayDate);
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
			string dl = day.ToString("yyyy-MM-dd") + (edgeReplay ? " (a day replayed from the loaded history)" : "");
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
					dl, 100 * edgeS / edgeH));
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
					dl, edgeDays, act));
			}
		}
"""
s = s[:i0] + new + s[i1:]

# --- EdgeRestore
j0 = s.index("		private void EdgeRestore()\n")
j1 = s.index("		private void EdgeDayClose(DateTime etNow)\n", j0)
if "is older than the history rebuild" not in s[j0:j1]: sys.exit("EdgeRestore distinto de lo esperado")
newr = """		// patch_edge_restore.py: days the loaded history closed (date key, z), the first day it covers, and the restore's flags
		private List<int> edgeHistD = new List<int>(); private List<double> edgeHistZ = new List<double>(); private int edgeCoverFrom; private bool edgeNoSave, edgeReplay;
		private static DateTime KeyDate(int k) { return new DateTime(k / 10000, k / 100 % 100, k % 100); }
		// same profile, start date and calibration (k, h: fields 10-11; a file of the old 9-field format only counts for this account itself)
		private bool EdgeFits(string[] p, bool other)
		{
			if (p == null || p.Length < 9 || p[0] != Profile.ToString() || p[8] != (EdgeMonitorStart ?? "")) return false;
			if (p.Length < 11) return !other;
			double k, h;
			if (!double.TryParse(p[9], NumberStyles.Any, CultureInfo.InvariantCulture, out k) || !double.TryParse(p[10], NumberStyles.Any, CultureInfo.InvariantCulture, out h)) return false;
			return Math.Abs(k - edgeK) < 1e-6 && Math.Abs(h - edgeH) < 1e-6;
		}
		// all fields or nothing (a half-read file never mixes with the history rebuild)
		private static bool EdgeParse(string[] p, out int d, out double sv, out int days, out bool alarm, out int fb, out bool warned, out List<string> off)
		{
			d = 0; sv = 0; days = 0; alarm = false; fb = 0; warned = false; off = new List<string>();
			if (p == null || p.Length < 9) return false;
			if (!int.TryParse(p[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out d) || !double.TryParse(p[2], NumberStyles.Any, CultureInfo.InvariantCulture, out sv)
				|| !int.TryParse(p[3], NumberStyles.Integer, CultureInfo.InvariantCulture, out days) || !int.TryParse(p[5], NumberStyles.Integer, CultureInfo.InvariantCulture, out fb)) return false;
			if (d != 0 && (d < 19000101 || d > 30000101 || d / 100 % 100 < 1 || d / 100 % 100 > 12 || d % 100 < 1 || d % 100 > 31)) return false;
			alarm = p[4] == "1"; warned = p[7] == "1";
			foreach (string x in p[6].Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries)) off.Add(x);
			return true;
		}
		// a new account (a new eval, another PC): the newest state of another real account with the same profile, start date and calibration
		private string[] EdgeSibling(out string src)
		{
			src = null; string[] best = null; int bd = 0, br = -1; double bs = 0;
			try
			{
				string own = Path.GetFileName(EdgeFile);
				foreach (string f in Directory.GetFiles(Core.Globals.UserDataDir, "nqmaster_edge_*.txt"))
				{
					string n = Path.GetFileName(f);
					if (string.Equals(n, own, StringComparison.OrdinalIgnoreCase) || n.StartsWith("nqmaster_edge_Sim") || n.StartsWith("nqmaster_edge_Playback")) continue;
					string[] p; try { p = File.ReadAllText(f).Split(';'); } catch { continue; }
					int d, days, fb; double sv; bool al, wn; List<string> off;
					if (!EdgeFits(p, true) || !EdgeParse(p, out d, out sv, out days, out al, out fb, out wn, out off)) continue;
					if (curSessDay > 0 && d >= curSessDay) continue;	// newer than the loaded data
					int rk = fb > 0 ? 2 : (al ? 1 : 0);
					if (best == null || d > bd || (d == bd && (rk > br || (rk == br && sv > bs)))) { best = p; src = n; bd = d; br = rk; bs = sv; }
				}
			}
			catch { }
			return best;
		}
		private void EdgeRestore()
		{
			if (!EdgeMonitor || EdgeFile == null) return;
			if (double.IsNaN(edgeK)) EdgeParams();
			string src = Path.GetFileName(EdgeFile);
			try
			{
				string[] p = null; bool own = false;
				if (File.Exists(EdgeFile))
				{
					string[] q = null; string err = null;
					try { q = File.ReadAllText(EdgeFile).Split(';'); } catch (Exception e) { err = e.Message; }
					int d0, n0, f0; double s0; bool a0, w0; List<string> o0;
					if (q == null || (EdgeFits(q, false) && !EdgeParse(q, out d0, out s0, out n0, out a0, out f0, out w0, out o0)))
					{
						edgeNoSave = true;	// never overwrite a state that could not be read: it may be fine on the next start
						Warn("nqm_edge_read", string.Format("NQMaster | edge monitor: the saved state ({0}) could not be read{1}. The monitor runs on the loaded history only and the file is left as it is (nothing is saved in this run). If it repeats, close NinjaTrader and check or delete the file.", src, err != null ? " (" + err + ")" : ""));
						return;
					}
					if (!EdgeFits(q, false)) Warn("nqm_edge_other", "NQMaster | edge monitor: the saved state is for another profile, start date or calibration and was ignored: " + src);
					else if (curSessDay > 0 && int.Parse(q[1], CultureInfo.InvariantCulture) >= curSessDay) Warn("nqm_edge_other", "NQMaster | edge monitor: the saved state is newer than the loaded data (a Playback?) and was ignored: " + src);
					else { p = q; own = true; }
				}
				if (p == null && !SimAccount)	// Sim / Playback never take another account's state (a Playback runs on past dates)
				{
					p = EdgeSibling(out src);
					if (p != null) Warn("nqm_edge_sib", string.Format("NQMaster | edge monitor: no saved state for this account; it starts from the one of {0} (day {1}, CUSUM {2}{3}).", src, p[1], p[2],
						p[5] != "0" ? ", FALLBACK running: " + p[5] + " days left" : (p[4] == "1" ? ", ALARM" : "")));
				}
				if (p == null)
				{
					DateTime st;
					if (DateTime.TryParseExact(EdgeMonitorStart ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) && firstBarDate > DateKey(st))
						Warn("nqm_edge_hist", string.Format("NQMaster | edge monitor: no saved state and the loaded history starts after the monitor start date ({0}): it only counts {1} days. From now on the state is saved and kept.", EdgeMonitorStart, edgeDays));
				}
				else
				{
					int d, days, fb; double sv; bool al, wn; List<string> off;
					EdgeParse(p, out d, out sv, out days, out al, out fb, out wn, out off);
					edgeLastDate = d; edgeS = sv; edgeDays = days; edgeAlarm = al; edgeFbLeft = fb; edgeWarned = wn; edgeFbOff = off;
					// this account's file written by the old code on the day its fallback ended: alarm on, fallback over -> the reset it missed
					if (own && p.Length < 11 && edgeAlarm && edgeFbLeft == 0 && !EdgeMonitorPause && EdgeAlarmFallback && EdgeFallbackDays > 0)
					{ edgeAlarm = false; edgeS = 0; edgeFbOff = null; Print("NQMaster | edge monitor: the saved state had the alarm on with the fallback already over (old version): reset as the fallback end does."); }
					edgePaused = edgeAlarm && EdgeMonitorPause;
					// the days the loaded history closed after the saved state (warm-up excluded): replayed with the same state machine
					int n = 0;
					edgeReplay = true;
					try
					{
						for (int i = 0; i < edgeHistD.Count; i++)
							if (edgeHistD[i] > d && edgeCoverFrom > 0 && edgeHistD[i] >= edgeCoverFrom) { EdgeStep(KeyDate(edgeHistD[i]), edgeHistZ[i]); n++; }
					}
					finally { edgeReplay = false; }
					Print(string.Format("NQMaster | edge monitor state restored ({0}, {1}){2}: CUSUM {3:0.00}, {4} days{5}", d, src,
						n > 0 ? string.Format(" + {0} days from the loaded history", n) : "", edgeS, edgeDays, edgeFbLeft > 0 ? ", fallback " + edgeFbLeft + " days left" : ""));
					// the history covers from after the next weekday of the saved state (or of the start date): the days in between are not counted
					DateTime dd = DateTime.MinValue, st;
					if (d > 0) dd = KeyDate(d).AddDays(1);
					else if (DateTime.TryParseExact(EdgeMonitorStart ?? "", "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out st)) dd = st;
					if (dd != DateTime.MinValue)
					{
						while (dd.DayOfWeek == DayOfWeek.Saturday || dd.DayOfWeek == DayOfWeek.Sunday) dd = dd.AddDays(1);
						if (edgeCoverFrom > DateKey(dd))
							Warn("nqm_edge_gap", string.Format("NQMaster | edge monitor: the saved state ends on {0} but the loaded history only covers from {1}: the days in between are not counted (NinjaTrader was off for longer than the loaded history). Nothing to do: the state continues from here.", d > 0 ? d.ToString(CultureInfo.InvariantCulture) : (EdgeMonitorStart ?? ""), edgeCoverFrom));
					}
				}
			}
			catch (Exception e)
			{
				edgeNoSave = true;
				Warn("nqm_edge_read", "NQMaster | edge monitor: state not restored (" + e.Message + "). The file is left as it is (nothing is saved in this run).");
				return;
			}
			EdgeSave();	// patch_edge_restore.py: the state is current even if NinjaTrader is never running at 18:00 ET
			if (mods != null) foreach (Mod m in mods) if (FallbackOff(m.Sig)) m.On = false;	// a restored fallback applies now (PropGoLive's session start recomputes the rest)
		}
"""
s = s[:j0] + newr + s[j1:]
open(P, "w", encoding="utf-8").write(s)
print("patch_edge_restore v2 aplicado")
