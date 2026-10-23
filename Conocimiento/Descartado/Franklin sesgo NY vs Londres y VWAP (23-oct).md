# Franklin: sesgo NY contra Londres y VWAP (23-oct-2026)

Regla del reel: a las 9:25-9:30 de NY, si el precio está por encima de Londres y del VWAP, solo compras; si está por debajo de los dos, solo ventas. El reel no da entrada, stop ni objetivo.

- Prueba: `research/mine/families14.py` (1.296 variantes: ventana de Londres, "por encima" = máximo / mitad / cierre de Londres, con o sin VWAP, con o sin tendencia, entrada a mercado a las 9:30 / quiebre de la primera vela de 15 min / quiebre del pre-NY, 4 stops, 3 objetivos), 16 años de futuros reales (Databento), protocolo de siempre (`b14_select.py`, `b14_select.json`).
- Tal como lo dice el reel (comprar o vender a mercado a las 9:30): factor de beneficio mediano 1,04 en 2020-23 y 0,94 en 2024-26. El VWAP no cambia nada (con y sin VWAP dan igual).
- Lo único que aguanta: quiebre de la primera vela de 15 min cuando NY abre por encima del máximo de Londres (o por debajo del mínimo), mantenido hasta el cierre: 3 variantes con PF 1,25-1,40 en todos los períodos, pero 30-48% de ganadoras y un trade cada 4-8 días.
- Sumado a NQMaster: baja el Sharpe en los dos períodos (−0,03 a −0,35), sube la caída máxima 5-48% y baja el % de ganadoras. Se superpone con ORB60/ORB90/VOLB (correlación 0,17-0,42).

**Descartado.** No se agrega.
