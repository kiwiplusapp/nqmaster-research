# Experimento 01 (frente 5A): realismo de ejecución y paridad — borrador 2026-10-26

**Veredicto H1/H2: los fills de 1 minuto de NinjaTrader (Standard) no sobreestiman el neto. Con fills de 1 tick el neto es +0,4 % (IC 95 % −0,0 % .. +0,7 %) sobre 388 trades de 2026-06-01 → 2026-10-23, 0 cambios de desenlace. Regla 5A.4: el IC queda entero por encima de −15 %, así que ningún neto del programa se recalcula por fills; la lista de trades Standard sigue siendo la referencia del motor de campaña.** Período: CFD/MNQ futuros 2026-06-22 → 2026-10-23 (ticks de Continuum desde el 2026-05-31; 1 día excluido por 19 minutos sin ticks). n = 388 pares (392 trades por lado). Costos: $1,90 por contrato + 1 tick por lado en los dos lados (Standard lo trae; a la serie de ticks, donde NinjaTrader no aplica slippage, se le suma el mismo tick y se desplazan con él los brackets que la estrategia calcula desde el fill).

## Cómo se midió

1. `NQMaster.cs` con la propiedad `FillSeries` (parche reproducible `research/mine/patch_fillseries.py`, v4.2): con Tick1 agrega una serie de 1 tick, manda todas las órdenes ahí y reemplaza `SetStopLoss`/`SetProfitTarget` por brackets explícitos `StopX`/`TargetX` en esa serie (NinjaTrader deja los `Set*` en la serie primaria: 0 de 283 fills con hora de tick en la corrida v3). Con Off el export es **idéntico byte a byte** al pre-parche (4 pruebas). `OrderFillResolution.High` no existe para estrategias multi-serie (P0).
2. Dos corridas del Strategy Analyzer sobre el mismo período y el mismo *Days to load* (el ATR de Wilder hace que dos inicios distintos den otros niveles): Off y Tick1. `research/mine/fill_gap.py` empareja trade a trade (fecha, módulo, dirección, ±3 min), reporta Δticks de entrada y salida, Δ$/trade con IC 95 %, flips y cambios de desenlace, y verifica en qué serie llenó cada orden (segundos ≠ :00) y fills imposibles contra `mnq_fut.npz`.
3. Tratamiento del slippage, una sola vez: Standard trae 1 tick en entradas a mercado/stop y en salidas stop/mercado; a Tick1 se le suma el mismo tick (`--slip-b 1`) y los niveles de bracket calculados desde `EntryPx` se mueven con el fill (1 tick en módulos con stop/target en ticks y en el break-even de VOLB; 1 + R ticks en el target de los módulos `PriceTarget`; 0 en stops absolutos). Sin ese desplazamiento cada bracket leía exactamente 1 tick peor (−3,5 % espurio). El slippage real (H5) reemplaza la hipótesis por celda, nunca se suma.

## Resultado (Off v4.2 vs Tick1 v4.2, `research/nt_exports/2026-10-26/v42/fill_gap_h1.md`)

| Tipo de entrada | n | Δ entrada (ticks) | Δ salida (ticks) | Δ$/trade (IC 95 %) | Total |
|---|---|---|---|---|---|
| Mercado | 274 | −0,08 | 0,00 | +0,04 (−0,01 .. +0,09) | +$10 |
| Stop | 83 | +0,02 | −0,16 | +0,07 (−0,06 .. +0,20) | +$6 |
| Límite | 31 | −0,26 | +0,06 | +0,10 (−0,20 .. +0,39) | +$3 |
| Total | 388 | −0,07 | −0,03 | +0,05 (−0,00 .. +0,10) | +$19 (+0,4 %) |

(+ = peor en Tick1.) Desenlaces: stop 111/111, target 169/169, tiempo 108/108; flips 0,0 %. Las entradas límite (LON) llenan mejor en ticks porque el fill atraviesa el nivel; 15 de 111 `StopX` llenan 1 tick a través del nivel (VOLB, 2 veces 2 ticks): ese es todo el "slippage de precio" que el modelo de 1 minuto no ve. Tiempo de cómputo: ×20 por barra de 1 minuto (66,7 s para 144 k barras y 236 M ticks).

**Alcance.** 4 meses, un solo período, perfil Ultra, 1 contrato, datos demo de Continuum. No dice nada de la liquidez con 6 contratos (eso es H5) ni de los módulos que no operaron en la ventana (ENG10, ENG26, RSI2). Un replay de ticks sobre 2024-26 (Databento) queda descartado: el IC no cruza −15 %.

## Hallazgos de mecánica destapados por la comparación (corregidos en v4.2, `docs/experimentos/01_revision_parche_fillseries.md`)

- `EntryBar` de los fills a mercado: NinjaTrader en Standard carga el fill a la barra que envió la orden aunque llene en la apertura siguiente; v4.1 lo ponía una barra después en Tick1 y 48 de 108 salidas por MaxHold salían tarde. Corregido por tipo de orden; verificado: v4.2 vs v4.1 difieren exactamente en esas 49 salidas y en nada más.
- `Core.Globals.Now` es el reloj de la PC bajo la conexión Playback: `LateBar()` rechazaba todas las barras reproducidas (el Market Replay no entró nunca) y `RollDue()` leía la fecha real. Ahora `NowClock()` usa la última barra de 1 min en Playback. Pendiente en vivo: si `CurrentBar` en tiempo real es la última barra cerrada, un fill stop/límite en la barra en formación da `EntryBar` una barra antes que el backtest; se prueba con Playback Off contra backtest Off de los mismos días.
- `atrDaily` (Wilder, k = 14) depende del primer día cargado: Days to load = 120 fijo en el runbook.

## Pendiente del experimento

- **H3, paridad NinjaTrader vs investigación (S2):** baseline del 26-oct FALLA (`research/nt_exports/2026-10-26/standard/parity_ultra_d4.md`): G1 91,0 %, G3 0,918, G4 falla en ORFAIL 34 %, RV11 54 %, CAM3 56 %, MSEQS 56 %, ICT 80 %, SO04 89 %. Los cuatro módulos de 6 años siguen "paridad pendiente" en el runbook (aporte medido: +$100/mes/contrato, 5 % del neto).
- **H5, slippage real por módulo × franja (P3):** exports de las cuentas prop (principal) y Sim101 (respaldo), `research/mine/slip_model.py`; reemplaza la hipótesis de 1 tick por celda con n ≥ 15.
- **Neto por contrato por mes por módulo en IS/C24/REAL** con el slippage de H5: se entrega cuando P3 esté.
- Playback Tick1 con 6 contratos (13-15 oct, modo Historical): **pasó** — 16/16 trades iguales al backtest Tick1 (misma barra de entrada y salida, brackets a 1-4 s), fills parciales por volumen de tick con re-dimensión de brackets, NinjaTrader reduce y cancela el hermano, 59 órdenes todas Filled/Cancelled, 90 lotes dentro = 90 fuera, 0 huérfanas. Queda el off-by-one de `EntryBar` en vivo: Playback Off del 16-oct (tres salidas por MaxHold) contra el backtest Off.

## Reproducibilidad

`cp archive/backups/NQMaster_backup_pre_fillseries.cs NQMaster.cs && python3 research/mine/patch_fillseries.py && bash tools/nt8_stub/check.sh NQMaster.cs` regenera el código. `cd research/mine && python3 fill_gap.py ../nt_exports/2026-10-26/v41/trades_off_2026-06-01_hoy.csv ../nt_exports/2026-10-26/v42/trades_tick1_2026-06-01_hoy.csv --slip-b 1 --slip-b-scope all --exclude-dates 20260625 --research ultra_d4` regenera la tabla. Autotest: `fill_gap.py x.csv x.csv` → 100 % emparejado, Δ = 0.
