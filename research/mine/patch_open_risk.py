"""patch_open_risk.py (2026-10-29, problema abierto 5 de docs/ESTADO.md: panel sin riesgo de cuenta). Aplica sobre NQMaster.cs v4.3 + patch_clock_check.py.
Agrega al panel (seccion de la cuenta simulada y de la CUENTA REAL) el riesgo abierto: el P&L si todas las posiciones abiertas tocan su stop
(sum (stop - entrada) x direccion x lotes x valor del punto) y el colchon que quedaria. Para eso BracketStop registra el nivel del stop tambien
con FillSeries = Off (los campos XStopV / XStopPrice solo los leen BracketPx y PlaceBrackets, que con Off sale enseguida): no cambia ningun trade.
Idempotente. Run: python3 research/mine/patch_open_risk.py && bash tools/nt8_stub/check.sh NQMaster.cs"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); P = os.path.join(ROOT, "NQMaster.cs")
s = open(P, encoding="utf-8").read()
if "PnlAtStops" in s: print("ya aplicado"); sys.exit(0)
def rep(a, b, n=1):
    global s
    if s.count(a) != n: sys.exit(f"ancla no encontrada ({s.count(a)}): {a[:90]}")
    s = s.replace(a, b)
rep("""		private void BracketStop(Mod m, CalculationMode mode, double v)
		{
			if (fillBip == 0) { SetStopLoss(m.Sig, mode, v, false); return; }
			m.XStopPrice = mode == CalculationMode.Price; m.XStopV = v;
""", """		private void BracketStop(Mod m, CalculationMode mode, double v)
		{
			m.XStopPrice = mode == CalculationMode.Price; m.XStopV = v;	// recorded with FillSeries Off too: the panel's open risk (patch_open_risk.py); with Off only PnlAtStops reads it
			if (fillBip == 0) { SetStopLoss(m.Sig, mode, v, false); return; }
""")
rep("""		private double BracketPx(Mod m, bool stop)
		{""", """		// open risk for the panel (patch_open_risk.py, 2026-10-29): P&L of the open lots if every one of them hits its stop, from the entry price
		// (the account balance on the panel is realised cash). A stop already beyond the entry (VOLB break-even) counts in favour. Slippage not included.
		private double PnlAtStops()
		{
			double r = 0;
			try
			{
				foreach (Mod m in mods)
				{
					if (!m.InTrade || m.OpenQty <= 0 || double.IsNaN(m.XStopV) || m.EntryPx <= 0) continue;
					int dir = m.Dir != 0 ? m.Dir : (Position.MarketPosition == MarketPosition.Short ? -1 : 1);
					double sp = m.XStopPrice ? m.XStopV : m.EntryPx - dir * m.XStopV * TickSize;
					r += (sp - m.EntryPx) * dir * m.OpenQty * Instrument.MasterInstrument.PointValue;
				}
			}
			catch { return 0; }
			return r;
		}
		private double BracketPx(Mod m, bool stop)
		{""")
rep("""					b.AppendLine(string.Format("Saldo {0}  ·  límite de pérdida {1}  ·  colchón {2}", Usd(bal), Usd(StartBalance + cy.Thr), Usd(prof - cy.Thr)));
""", """					b.AppendLine(string.Format("Saldo {0}  ·  límite de pérdida {1}  ·  colchón {2}", Usd(bal), Usd(StartBalance + cy.Thr), Usd(prof - cy.Thr)));
					double pst = PnlAtStops();
					if (pst != 0) b.AppendLine(string.Format("Si tocan todos los stops abiertos: {0}  ·  colchón que queda {1}{2}", Usd(pst), Usd(prof - cy.Thr + pst), prof - cy.Thr + pst <= 0 ? "  ·  ATENCIÓN: alcanza para perder la cuenta" : ""));
""")
rep("""				b.AppendLine(string.Format("Saldo {0} ({1})  ·  límite {2}  ·  colchón {3}", Usd(eq), Usd(eq - StartBalance), Usd(propThr), Usd(eq - propThr)));
""", """				b.AppendLine(string.Format("Saldo {0} ({1})  ·  límite {2}  ·  colchón {3}", Usd(eq), Usd(eq - StartBalance), Usd(propThr), Usd(eq - propThr)));
				double pstR = PnlAtStops();
				if (pstR != 0) b.AppendLine(string.Format("Si tocan todos los stops abiertos: {0}  ·  colchón que queda {1}{2}", Usd(pstR), Usd(eq - propThr + pstR), eq - propThr + pstR <= 0 ? "  ·  ATENCIÓN: alcanza para perder la cuenta" : ""));
""")
open(P, "w", encoding="utf-8").write(s); print("patch_open_risk aplicado")
