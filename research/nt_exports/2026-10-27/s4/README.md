# 2026-10-27 · S4 · corrida (d'): Off con Slippage = 0 contra Tick1 sin tick sintético

Export de Federico (Strategy Analyzer, `FillSeries = Off`, **Slippage = 0**, código v4.3 con `IctMultiplier = 1`, 2026-06-01 → hoy, 405 trades, primer trade 2026-06-22, último 2026-10-26): `trades_off_slip0_2026-06-01_hoy.csv`.

**Qué es la corrida.** Emparejado por (fecha, módulo, dirección, minuto de entrada) con el Off v4.3 normal (`s2/trades_off_2024-01-01_hoy_v43.csv`, misma ventana): 405 de 405 pares; 370 de 374 entradas a mercado / stop están **exactamente 1 tick mejor** que con Slippage = 1 (las 31 límite iguales) → el Analyzer corrió con Slippage = 0. El export también vino **sin comisión** (columna `Commission` = 0,00 $ en todas las filas; el Off normal trae 1,90 $ por contrato): `trades_off_slip0_2026-06-01_hoy_comm190.csv` es el mismo archivo con $1,90 por contrato restado del `Profit` y la columna `Commission` completada, para compararlo con el Tick1 de v4.2, que sí la trae. Ningún otro campo cambia.

**Lectura (d') de H1, sin ningún modelo de slippage** (`fill_gap_d_slip0.md`; A = Off Slippage 0 con comisión, B = Tick1 v4.2 crudo, sin `--slip-b`, 25-jun excluido como en H1):

| | n pares | B − A total | por trade (IC 95 %) | Δ relativo al neto Standard | flips | cambios de desenlace |
|---|---|---|---|---|---|---|
| (d') Off slip 0 vs Tick1 crudo | 387 | **+$22 (+0,4 %)** | +0,06 (+0,00 .. +0,11) | **+0,4 % (IC +0,0 % .. +0,8 %)** | 0,3 % (1) | 1 |
| H1 final (Off slip 1 vs Tick1 + tick sintético + brackets desplazados) | 388 | +$19 (+0,4 %) | +0,05 (−0,00 .. +0,10) | +0,4 % (IC −0,0 % .. +0,7 %) | 0 | 0 |

Las dos lecturas coinciden: el desplazamiento de brackets que `fill_gap.py` aplica al tick sintético (`bracket_shift`) reproduce lo que el Analyzer hace cuando el fill no lleva slippage. La reserva del revisor ("el titular depende de un contrafactual de $124") queda cerrada con una medición directa. Regla 5A.4: IC entero por encima de −15 %.

Por tipo de entrada (B − A por trade): mercado +0,04 (274), stop +0,08 (83), límite +0,12 (30). Entradas: −0,08 ticks de media (B mejor); salidas −0,03 ticks. Fills imposibles: 0 fuera de la barra ±1 tick en los 282 fills con barra en `mnq_fut.npz` (112 sin barra desde el 2026-09-28).

**No emparejados (8):** 7 solo en A y 1 solo en B, todos de los módulos del parche v4.3 que el Tick1 v4.2 no tiene: ORFAIL 5 (reintentos tras la deferral: 28-ago, 4-sep, 8-oct, 9-oct, 23-oct), ICT 9-oct (v4.3 entra 10:20, v4.2 entraba 10:25: es el mismo trade, fix del setup diferido) y un MOM1030 del 28-ago en cascada. Fuera de esos 8 el emparejado es 387 de 387.

**Dato lateral (Off slip 0 vs Off slip 1, misma versión v4.3):** 90 de 405 pares tienen otra salida porque los brackets relativos al fill se mueven 1 tick con la entrada; el neto por contrato difiere en $1.722 en la ventana (+$1.164 de comisión, el resto slippage), como corresponde a 1 tick + $1,90 por lado. 5 trades (LF0430 ×2, LATE15 ×2, VW13) existen solo con Slippage = 1 por cascada de posición.

Archivos: `fill_gap_d_slip0.md`, `fill_gap_d_slip0_pairs.csv`, `fill_gap_d_slip0_unmatched.csv`.
