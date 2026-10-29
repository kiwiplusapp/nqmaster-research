"""patch_open_risk.py v2 (2026-10-29, problema abierto 5 de docs/ESTADO.md: panel sin riesgo de cuenta; v2 tras la revision adversarial del 29-oct).
Aplica sobre NQMaster.cs v4.3 + patch_clock_check.py v2. Agrega al panel (cuenta simulada y CUENTA REAL) el P&L si todas las posiciones abiertas de
ESTA instancia de NQMaster tocan su stop, con la comision de salida ($1,90 ida y vuelta / 2) y 1 tick de slippage por lote, y el colchon que quedaria.
v2: campos propios del panel (RStopV / RStopPx) en vez de los de los brackets explicitos, asi BracketStop y la logica de ordenes quedan como estaban en
todos los modos (FillSeries Off / Tick1 / Second1); en la CUENTA REAL no cuenta la posicion historica (virtual) que la estrategia puede tener al
habilitarse con WaitUntilFlat. No cambia ningun trade. Idempotente. Run: python3 research/mine/patch_open_risk.py && bash tools/nt8_stub/check.sh NQMaster.cs"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); P = os.path.join(ROOT, "NQMaster.cs")
s = open(P, encoding="utf-8").read()
if "RStopV" in s: print("ya aplicado"); sys.exit(0)
if "PnlAtStops" in s: sys.exit("NQMaster.cs tiene la v1 del riesgo abierto: regenerar desde el backup (ver docs/ESTADO.md)")
def rep(a, b, n=1):
    global s
    if s.count(a) != n: sys.exit(f"ancla no encontrada ({s.count(a)}): {a[:90]}")
    s = s.replace(a, b)
rep("			public bool XStopPrice, XTgtPrice, XExitPending;",
    "			public double RStopV = double.NaN; public bool RStopPx;	// panel open risk only (patch_open_risk.py): the stop level of the last BracketStop call\n			public bool XStopPrice, XTgtPrice, XExitPending;")
rep("""		private void BracketStop(Mod m, CalculationMode mode, double v)
		{
""", """		private void BracketStop(Mod m, CalculationMode mode, double v)
		{
			m.RStopPx = mode == CalculationMode.Price; m.RStopV = v;	// panel open risk only (patch_open_risk.py); nothing else reads it
""")
rep("""		private double BracketPx(Mod m, bool stop)
		{""", """		// open risk for the panel (patch_open_risk.py v2): P&L of this NQMaster instance's open lots if every one hits its stop, from the entry price
		// (the panel balance is realised cash), minus the exit commission ($1.90 round turn / 2) and 1 tick of slippage per lot. A stop beyond the entry
		// (VOLB break-even) counts in favour. realAcct: skip while the account position does not match the strategy's (historical position after enabling).
		private double PnlAtStops(bool realAcct)
		{
			double r = 0; int lots = 0;
			try
			{
				if (realAcct)
				{
					int a = SignedQty(PositionAccount), q = SignedQty(Position);
					if (a == 0 || q == 0 || Math.Sign(a) != Math.Sign(q)) return 0;
				}
				foreach (Mod m in mods)
				{
					if (!m.InTrade || m.OpenQty <= 0 || double.IsNaN(m.RStopV) || m.EntryPx <= 0) continue;
					int dir = m.Dir != 0 ? m.Dir : (Position.MarketPosition == MarketPosition.Short ? -1 : 1);
					double sp = m.RStopPx ? m.RStopV : m.EntryPx - dir * m.RStopV * TickSize;
					r += (sp - m.EntryPx) * dir * m.OpenQty * Instrument.MasterInstrument.PointValue; lots += m.OpenQty;
				}
				r -= lots * (0.95 + TickSize * Instrument.MasterInstrument.PointValue);
			}
			catch { return 0; }
			return lots > 0 ? r : 0;
		}
		private double BracketPx(Mod m, bool stop)
		{""")
rep("""					b.AppendLine(string.Format("Saldo {0}  ·  límite de pérdida {1}  ·  colchón {2}", Usd(bal), Usd(StartBalance + cy.Thr), Usd(prof - cy.Thr)));
""", """					b.AppendLine(string.Format("Saldo {0}  ·  límite de pérdida {1}  ·  colchón {2}", Usd(bal), Usd(StartBalance + cy.Thr), Usd(prof - cy.Thr)));
					double pst = PnlAtStops(false);
					if (pst != 0) b.AppendLine(string.Format("Si tocan los stops abiertos de NQMaster (este gráfico, con comisión y 1 tick): {0}  ·  colchón que queda {1}{2}", Usd(pst), Usd(prof - cy.Thr + pst), prof - cy.Thr + pst <= 0 ? "  ·  ATENCIÓN: alcanza para perder la cuenta" : ""));
""")
rep("""				b.AppendLine(string.Format("Saldo {0} ({1})  ·  límite {2}  ·  colchón {3}", Usd(eq), Usd(eq - StartBalance), Usd(propThr), Usd(eq - propThr)));
""", """				b.AppendLine(string.Format("Saldo {0} ({1})  ·  límite {2}  ·  colchón {3}", Usd(eq), Usd(eq - StartBalance), Usd(propThr), Usd(eq - propThr)));
				double pstR = PnlAtStops(true);
				if (pstR != 0) b.AppendLine(string.Format("Si tocan los stops abiertos de NQMaster (este gráfico, con comisión y 1 tick): {0}  ·  colchón que queda {1}{2}", Usd(pstR), Usd(eq - propThr + pstR), eq - propThr + pstR <= 0 ? "  ·  ATENCIÓN: alcanza para perder la cuenta" : ""));
""")
open(P, "w", encoding="utf-8").write(s); print("patch_open_risk v2 aplicado")
