# Corridas con el parche v4.2 (26-oct): Off 2024 → hoy (compuerta A) y Tick1 2026-06-01 → hoy (H1 final)

Archivos: `trades_off_2024-01-01_hoy.csv` (Off, 3.295 trades), `trades_tick1_2026-06-01_hoy.csv` + `output_tick1_2026-06-01_hoy.txt` (Tick1, 392 trades; el Output trae además una corrida Off 2024 → hoy y una Tick1 anterior). Comparaciones: `fill_gap_h1.md` (H1/H2 contra `../v41/trades_off_2026-06-01_hoy.csv`), `fill_gap_v42_vs_v41.md` (efecto del parche v4.2 sobre la corrida Tick1 de v4.1).

## Compuerta A: Off v4.2 = baseline

`trades_off_2024-01-01_hoy.csv` es **idéntico byte a byte** al Off de v4.1, que lo era al Standard pre-parche. Cuarta prueba de equivalencia con Off (v3, v3 órdenes, v4.1, v4.2).

## Tick1 v4.2: la mecánica queda cerrada

| Qué | Evidencia |
|---|---|
| `RUN TIME` | `66,7 s wall clock, 144.135 1-minute bars, 235.979.550 fill-series bars, 19 tick-gap minutes, 0 orphan protective orders cancelled, 0 market exits forced`. Los 19 minutos sin ticks son los del 2026-06-25 11:01-11:19 (día excluido). Off 2024 → hoy en la misma sesión: 22,7 s para 991.109 barras → **×20 por barra de 1 min** (463 µs vs 23 µs). |
| v4.2 vs v4.1 (mismo Tick1) | 392 pares; **exactamente 49 difieren, todos salidas por MaxHold** (ON07 27, NF05 15, LF0430 4, MOM1030, ORFAIL, SO04) con `hold` una barra menos (ahora igual a Off); los otros 343 pares Δ = 0 en entrada, salida y $. 0 cambios de desenlace. |
| Series | Entradas límite 96,8 % con segundos, stop 96,4 %, `StopX` 96,4 %, `TargetX` 97,6 %; a mercado y salidas por tiempo 0 % (primer tick del minuto siguiente, sellado :00). 0 salidas ≥ 15:58, 0 cierres de NinjaTrader. |

## H1 / H2 final: Tick1 − Off = +0,4 % (IC 95 % −0,0 % .. +0,7 %)

Off y Tick1 v4.2 sobre **2026-06-01 → 2026-10-23, mismo Days to load**, 388 pares sin el 25-jun, 100 % emparejados, **0 cambios de desenlace, 0 flips, 0 salidas por tiempo en otra barra**. Comando: `python3 fill_gap.py ../nt_exports/2026-10-26/v41/trades_off_2026-06-01_hoy.csv ../nt_exports/2026-10-26/v42/trades_tick1_2026-06-01_hoy.csv --slip-b 1 --slip-b-scope all --exclude-dates 20260625 --research ultra_d4`.

| Tipo de entrada | n | Δ entrada (ticks) | Δ salida (ticks) | Δ$/trade (IC 95 %) | Total |
|---|---|---|---|---|---|
| Mercado | 274 | −0,08 | 0,00 | +0,04 (−0,01 .. +0,09) | +$10 |
| Stop | 83 | +0,02 | −0,16 | +0,07 (−0,06 .. +0,20) | +$6 |
| Límite | 31 | −0,26 | +0,06 | +0,10 (−0,20 .. +0,39) | +$3 |
| **Total** | **388** | −0,07 | −0,03 | **+0,05 (−0,00 .. +0,10)** | **+$19 (+0,4 %)** |

(+ = peor para el trade en Tick1.) Con el tick sintético en Tick1 y los brackets relativos al fill desplazados con él (ver `fill_gap_h1.md`, sección *Slippage*), la diferencia que queda es precio puro: las entradas límite de LON llenan 0,26 ticks mejor en ticks (fill a través del nivel), las stop de VOLB/ORB igual en 82 de 83, los `StopX` llenan en el nivel exacto en 96 de 111 y 1 tick a través en 15 (VOLB, 2 veces 2 ticks).

**Regla 5A.4 del plan:** IC entero por encima de −15 % → **el modelo de fills de 1 minuto se da por bueno. Ningún neto del programa se recalcula por fills; la lista de trades de Standard sigue siendo la referencia para el motor de campaña.** Alcance de la afirmación: 4 meses (jun-oct 2026), 388 trades, perfil Ultra con 1 contrato, Continuum demo; con 6 contratos la pregunta es de liquidez/slippage (H5), no de fills.

Lecturas anteriores, para la historia: cruda v4.1 sin desplazar los brackets −3,5 % (sesgo de 1 tick por bracket), v4.1 corregida −1,1 % (incluía las 48 salidas MaxHold tardías), v4.2 +0,4 %.

## Playback Tick1 con 6 contratos (26-oct): pasó

Dos intentos. **Intento 1** (`output_playback_tick1_6c_2026-10-13_16.txt`): la estrategia entró en vivo a las 01:00 del 13-oct con Playback detectado y no procesó barras (el replay no avanzó); su parte histórica (jun → 12-oct en Playback101 con 6 contratos y TraceOrders) ya probó brackets de 6/8/12/14/20 lotes iguales al fill, 220 cancelaciones automáticas del hermano por NinjaTrader, 22 `ChangeOrder` aceptados, 0 ignoradas. **Intento 2, modo Historical, 2026-10-13 → 10-15** (`output_playback_tick1_6c_2026-10-13_15_run2.txt`, `orders_playback_tick1_6c_2026-10-13_15.csv`):

| Qué | Evidencia |
|---|---|
| Playback detectado | `Playback connection: strategy clock = last 1-minute bar` a las 00:59 del 13-oct; `FillSeries Tick1 kept on the Playback connection`; `LIVE on MNQ DEC26 … contracts 6`. Ninguna barra "processed late". |
| Mismos trades que el backtest | **16 de 16** trades del backtest Tick1 de esos días (REV06, VOLB ×3, MOM1030, CRT11, MSEQ, MOM13, CPI09, ICT, ORFAIL, MOM11 ×2, SO04, REV06, ON07) con la misma barra de entrada y de salida; los fills de `StopX`/`TargetX` a 1-4 s de los del Analyzer (REV06 08:09:27 vs 08:09:26, CPI09 10:40:48 vs 10:40:47, ICT 10:57:39 vs 10:57:38). La ICT límite del 13-oct no llenó en ninguno de los dos. |
| Fills parciales | El motor de simulación llena por el volumen de cada tick: 37 ejecuciones de entrada para 16 entradas, 51 ejecuciones de salida (CPI09 con 20 lotes salió en 12 fills de 1-5). Los brackets se emiten en la primera ejecución (1 lote) y `PlaceBrackets` los re-dimensiona en cada ejecución siguiente: 55 `ChangeOrder` aceptados, 0 "re-size failed", y en el export de órdenes las 16 parejas tienen el bracket llenado con `Quantity = Filled` = lotes de la entrada (6, 2, 6, 20, 6, 12, 6, 6, 6, 6, 6, 6). |
| OCO / hermano | NinjaTrader **reduce solo el bracket hermano a medida que el otro llena** ("Amended pending exit order, since associated position is closed", 12 veces: TargetX 6 → 5 tras 1 lote de `StopX`, StopX 20 → 19…) y lo cancela al cerrar la posición (12). Las salidas a mercado (flatten 15:56 ET de CRT11/MSEQ/MOM13 el 13 y VOLB el 15) cancelan los dos brackets con `CancelBrackets` (15 cancelaciones propias) y salen al tick siguiente. |
| Huérfanas | Export de órdenes: **59 órdenes, todas Filled o Cancelled, ninguna Working/Accepted al final** → pestaña Orders vacía. `RUN TIME`: `0 orphan protective orders cancelled, 0 market exits forced`. 90 lotes entrados = 90 lotes salidos. 0 "Ignored", 0 rechazos, 0 `STALE`, 0 desync. |
| Reloj | 68,2 s de reloj para 118 k barras de 1 min + 188 M ticks históricos + 3 días de replay a velocidad máxima. |

Detalle a tener en cuenta: el monitor de edge restauró su estado del archivo `nqmaster_edge_Playback101.txt` de una corrida anterior (`EDGE day 15` en vez de `day 6`): los archivos de estado por cuenta persisten entre replays; no afectó nada (CUSUM 1,3-1,7 de 26,9), pero un replay "limpio" debe borrar `nqmaster_edge_Playback101.txt` / `nqmaster_prop_Playback101.txt` antes.

**Lo que esta prueba no cubre:** el off-by-one de `EntryBar` en tiempo real (MaxHold). En el 13-15 oct no hubo salidas por MaxHold (todas fueron stop, target o flatten). El 16-oct el backtest tiene tres (`LONX`, `NF05X`, `ON07X`): el Playback **Off** sobre el 16-oct (o 13-16) con export de trades de Playback101 contra el backtest Off cierra ese punto.

## Qué sigue

1. Opcional, 3 s: `Off 2026-06-01 → hoy` con **Slippage = 0** en el Analyzer y `fill_gap.py <ese> trades_tick1_2026-06-01_hoy.csv` **sin `--slip-b`**: la misma lectura sin ningún modelo de slippage (brackets desde el fill crudo en los dos lados). Debe dar ≈ +0,4 %.
2. Hecho: Playback Tick1 13-15 oct (arriba).
3. Playback **Off** (FillSeries Off, Contracts 1 basta) sobre **2026-10-16** (o 13 → 16), modo Historical, export de trades de Playback101: los `hold` de `LONX`, `NF05X` y `ON07X` tienen que coincidir con el backtest Off (`trades_off_2024-01-01_hoy.csv`: NF05 240 barras, ON07 60, LON hora fija 09:31); si salen una barra antes o después, el vivo tiene el off-by-one de `EntryBar` y va en v4.3.
4. S2: paridad por módulo (G4: ORFAIL, RV11, CAM3, MSEQS, ICT, SO04) y P3 (slippage real de las cuentas prop, `slip_model.py`).
