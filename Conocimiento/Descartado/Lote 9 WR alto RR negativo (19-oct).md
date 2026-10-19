# Lote 9: WR alto con RR negativo (19-oct-2026)

Pedido de Federico: módulos nuevos de win rate alto con target más chico que el stop, que funcionen en 2026-27.

- Familias (`research/mine/families9.py`): números redondos, test del máximo/mínimo overnight, toque del settlement, scalp con tendencia, "snap" de estiramiento.
- Targets 0,2 / 0,3 / 0,5 R; stops 0,25-0,6 ATR diario o estructura. Break-even antes de costos: 83 / 77 / 67% de WR.
- 2.196 configuraciones sobre 16 años de NQ real (Databento). Elegir en 2020-23, confirmar en 2024-26 y en 2010-19 normalizado.
- Chequeos de lookahead: 0 violaciones.

**Resultado: 0 sobrevivientes.** En todas las familias el WR queda en o debajo del break-even de su target: achicar el target solo cambia PF por WR.

Junto con [[RR negativo (19-oct)]] (RR negativo sobre los módulos actuales), la idea queda descartada. Detalle: `research/mine/b9_report.md`.
