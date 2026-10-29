"""patch_clock_check.py (2026-10-29, problema abierto 3 de docs/ESTADO.md: fragilidad horaria). Aplica sobre NQMaster.cs v4.3 (patch_fillseries.py +
patch_parity_s2.py). Agrega un control de reloj SOLO DE AVISO: en cada sesion que no es media rueda, el fin de sesion de los futuros de indices CME
(plantilla ETH) tiene que caer a las 17:00 ET; si cae en otra hora, la zona horaria de NinjaTrader o el reloj de Windows estan mal y todos los
modulos de reloj operarian corridos (correr 15 min un modulo de reloj baja el Sharpe del portafolio 0,3-0,7). No bloquea entradas: avisa una vez por
sesion. Idempotente. Run: python3 research/mine/patch_clock_check.py && bash tools/nt8_stub/check.sh NQMaster.cs"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); P = os.path.join(ROOT, "NQMaster.cs")
s = open(P, encoding="utf-8").read()
if "nqm_clock" in s: print("ya aplicado"); sys.exit(0)
def rep(a, b, n=1):
    global s
    if s.count(a) != n: sys.exit(f"ancla no encontrada ({s.count(a)}): {a[:80]}")
    s = s.replace(a, b)
rep("		private TimeZoneInfo etZone;\n",
    "		private TimeZoneInfo etZone;\n		private int clockWarnDay = -1;	// patch_clock_check.py: last session date warned by the clock check\n")
rep("""			if (shortSession) Log(string.Format("short session (holiday / half day): the market closes {0:00}:{1:00} ET{2}", sessEndMin / 60, sessEndMin % 60, SkipShortSessions ? " - no new entries this session" : ""));
""", """			if (shortSession) Log(string.Format("short session (holiday / half day): the market closes {0:00}:{1:00} ET{2}", sessEndMin / 60, sessEndMin % 60, SkipShortSessions ? " - no new entries this session" : ""));
			// clock check (patch_clock_check.py, 2026-10-29): CME index futures (ETH template) end the session at 17:00 ET; any other end time on a
			// regular session means the NinjaTrader time zone or the Windows clock is wrong and every clock module would trade shifted. Alert only.
			int clockDay = Time[0].Year * 10000 + Time[0].Month * 100 + Time[0].Day;
			if (!shortSession && sessEndMin != 17 * 60 && clockWarnDay != clockDay)
			{
				clockWarnDay = clockDay;
				Warn("nqm_clock", string.Format("NQMaster | CLOCK CHECK: this session ends at {0:00}:{1:00} ET, expected 17:00 ET (CME index futures, ETH template). Check the NinjaTrader time zone (Tools > Options > General) and the Windows clock: every module uses ET clock times.", sessEndMin / 60, sessEndMin % 60));
			}
""")
open(P, "w", encoding="utf-8").write(s); print("patch_clock_check aplicado")
