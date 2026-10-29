"""patch_clock_check.py v3 (2026-10-29, problema abierto 3 de docs/ESTADO.md: fragilidad horaria; v2 tras la revision adversarial del 29-oct).
Aplica sobre NQMaster.cs v4.3 (patch_fillseries.py + patch_parity_s2.py). Control de reloj SOLO DE AVISO, dos chequeos:
 (1) plantilla de sesion: los futuros de indices CME (plantilla ETH) terminan una sesion normal a las 17:00 ET; otra hora = la plantilla de horario
     del grafico / de la estrategia no es 'CME US Index Futures ETH'.
 (2) conversion a ET: la hora ET de la barra calculada desde UTC con la regla fija de EE.UU. (horario de verano del 2.o domingo de marzo 02:00 al
     1.er domingo de noviembre 02:00) contra ToEt() (reglas 'Eastern Standard Time' de Windows). Si difieren, los datos de zona horaria de Windows
     estan mal y todos los modulos de reloj operarian corridos. (v1 solo hacia el chequeo 1, que no puede ver errores de zona horaria: los cancela.)
Corre al empezar cada sesion y al pasar a vivo (la primera sesion en vivo se proceso en historico, donde Warn solo imprime). En historico avisa una
sola vez por corrida y cuenta las sesiones; en vivo, una vez por sesion. v3 (revision de codigo del 29-oct): Times[0][0] en vez de Time[0]
(ClockCheck tambien corre desde OnStateChange al pasar a vivo). No cambia ningun trade. Idempotente.
Run: python3 research/mine/patch_clock_check.py && bash tools/nt8_stub/check.sh NQMaster.cs"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); P = os.path.join(ROOT, "NQMaster.cs")
s = open(P, encoding="utf-8").read()
if "UsEtFromUtc" in s: print("ya aplicado"); sys.exit(0)
if "nqm_clock" in s: sys.exit("NQMaster.cs tiene la v1 del control de reloj: regenerar desde el backup (ver docs/ESTADO.md)")
def rep(a, b, n=1):
    global s
    if s.count(a) != n: sys.exit(f"ancla no encontrada ({s.count(a)}): {a[:90]}")
    s = s.replace(a, b)
rep("		private TimeZoneInfo etZone;\n",
    "		private TimeZoneInfo etZone;\n		private int clockWarnDay = -1, clockHistCount; private bool clockHistWarned;	// patch_clock_check.py: clock check state\n")
rep("""			if (shortSession) Log(string.Format("short session (holiday / half day): the market closes {0:00}:{1:00} ET{2}", sessEndMin / 60, sessEndMin % 60, SkipShortSessions ? " - no new entries this session" : ""));
""", """			if (shortSession) Log(string.Format("short session (holiday / half day): the market closes {0:00}:{1:00} ET{2}", sessEndMin / 60, sessEndMin % 60, SkipShortSessions ? " - no new entries this session" : ""));
			ClockCheck();
""")
rep("""				rollHalt = RollDue(); if (rollHalt) Warn("nqm_roll", "NQMaster | ROLL DATE reached for " + Instrument.FullName + ": no new entries. Move the strategy to the next contract (same settings).");
""", """				rollHalt = RollDue(); if (rollHalt) Warn("nqm_roll", "NQMaster | ROLL DATE reached for " + Instrument.FullName + ": no new entries. Move the strategy to the next contract (same settings).");
				ClockCheck();	// patch_clock_check.py: the first live session started in history, where Warn only prints
""")
rep("""			else if (State == State.Terminated)
			{
""", """			else if (State == State.Terminated)
			{
				if (clockHistCount > 1) Print(string.Format("NQMaster | CLOCK CHECK failed on {0} sessions of this run (the first one is in the Output)", clockHistCount));
""")
rep("""		private DateTime ToEt(DateTime t)
		{""", """		// ---- clock check (patch_clock_check.py v2, 2026-10-29), alert only. (1) session template: CME index futures (ETH template) end a regular session
		// at 17:00 ET. (2) ET conversion: ET from the bar's UTC time with the fixed US rule against ToEt() (the Windows 'Eastern Standard Time' rules).
		// If the US ever changes its daylight-saving rule, update UsEtFromUtc.
		private static DateTime UsEtFromUtc(DateTime utc)
		{
			int y = utc.Year;
			DateTime mar = new DateTime(y, 3, 1); DateTime dstStart = mar.AddDays((7 - (int)mar.DayOfWeek) % 7 + 7).AddHours(7);	// 2nd Sunday of March, 02:00 EST = 07:00 UTC
			DateTime nov = new DateTime(y, 11, 1); DateTime dstEnd = nov.AddDays((7 - (int)nov.DayOfWeek) % 7).AddHours(6);		// 1st Sunday of November, 02:00 EDT = 06:00 UTC
			return utc.AddHours(utc >= dstStart && utc < dstEnd ? -4 : -5);
		}
		private string ClockProblem()
		{
			if (!shortSession && sessEndMin != 17 * 60)
				return string.Format("this session ends at {0:00}:{1:00} ET, expected 17:00 ET: set the trading-hours template of the chart and of the strategy to 'CME US Index Futures ETH'", sessEndMin / 60, sessEndMin % 60);
			try
			{
				DateTime utc = TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(Times[0][0], DateTimeKind.Unspecified), Core.Globals.GeneralOptions.TimeZoneInfo);
				double diff = (ToEt(Times[0][0]) - UsEtFromUtc(utc)).TotalMinutes;
				if (Math.Abs(diff) > 1) return string.Format("the ET time of this bar differs by {0:0} min from the US daylight-saving rule: update Windows (time-zone data) and check the NinjaTrader time zone (Tools > Options > General)", diff);
			}
			catch { }
			return null;
		}
		private void ClockCheck()
		{
			string p = ClockProblem(); if (p == null) return;
			if (State != State.Realtime) { clockHistCount++; if (clockHistWarned) return; clockHistWarned = true; }
			else { int d = Times[0][0].Year * 10000 + Times[0][0].Month * 100 + Times[0][0].Day; if (clockWarnDay == d) return; clockWarnDay = d; }
			Warn("nqm_clock", "NQMaster | CLOCK CHECK: " + p + ". Every module uses ET clock times.");
		}
		private DateTime ToEt(DateTime t)
		{""")
open(P, "w", encoding="utf-8").write(s); print("patch_clock_check v3 aplicado")
