# Corrida Tick1 2026-06-01 → 2026-10-23 (P2c del plan), parche v3, TraceOrders off

Archivos: `output_tick1_2026-06-01_hoy.txt`, `trades_tick1_2026-06-01_hoy.csv` (392 trades), `orders_tick1_2026-06-01_hoy.csv` (1.705 órdenes). Comparación contra el export `Off` 2024 → hoy (mismo código v3): `fill_gap_tick1_vs_off.md` (crudo) y `fill_gap_tick1slip_vs_off.md` (con 1 tick de slippage sintético en las entradas de Tick1).

## Lo que dice el Output

- `FILL SERIES Tick1 ... from this bar` el **2026-05-31 19:04**: Continuum tenía ticks desde el inicio de la corrida. La ventana de ticks es, como mínimo, 2026-06-01 → hoy (no 08-25 ni 08-02): toda la corrida es con fills de ticks; no hay tramo previo para la prueba de equivalencia (la equivalencia Off = código anterior ya está probada byte a byte en P2a).
- `RUN TIME`: 68,1 s, 144.135 barras de 1 min, 235.979.550 barras de ticks (~2,3 M ticks por día). 0 `TICK GAP`, 0 errores.

## Veredicto: el modelo de fills de v3 es MIXTO, no sirve todavía para H1

| Evidencia (export de órdenes, estado Filled, % con segundos ≠ :00) | Lectura |
|---|---|
| Entradas de mercado (MOM11 94 %, ON07 97 %, REV06 100 %, NF05 100 %…), stop (ORB60 71 %, ORB90 90 %, VOLB 78 %) y límite (ICT 92 %, LON 100 %); salidas por tiempo `<MOD>X` 78-100 %; cierres `Sell` 80 %, `Buy to cover` 93 % | Todo lo que NQMaster emite con `fillBip` **sí** va a la serie de ticks |
| **"Stop loss" 0 % (114 fills), "Profit target" 0 % (169 fills)**; ejemplo: stop 30.048,00 → fill 30.047,75 a las 7:00:00 | Las órdenes protectoras de `SetStopLoss` / `SetProfitTarget` **quedan en la serie de 1 minuto** (lógica Standard, con su tick de slippage, selladas al cierre de barra). El supuesto del plan no se cumple → **plan B**: salidas explícitas `ExitLongStopMarket` / `ExitLongLimit` en la serie de llenado desde `OnExecutionUpdate` |
| Entradas Tick1 vs Off: mediana **−1,00 tick** (mejor) en las 277 de mercado y las 84 stop; límite 0 | NinjaTrader **no aplica `Slippage = 1`** a los fills de la serie secundaria. Para comparar, `fill_gap.py --slip-b 1` suma el tick sintético (`--slip-b-scope entries` mientras las salidas sigan en la serie de 1 min) |
| Duración B − A = **+2,3 min** de media (MOM11 +6,8, REV06 +4,7); 2 flips stop→tiempo, 1 target→stop, 1 stop→target | Con la entrada a mitad de minuto, las protectoras (en la serie de 1 min) quedan activas recién desde la barra siguiente: el stop y el target no se revisan en lo que resta del minuto de entrada. Artefacto del modelo mixto, no un efecto de fills |
| Salidas B − A: −2,62 ticks en entradas de mercado, −0,89 en stop (mejor), por los dos puntos anteriores | Idem |
| Resultado crudo: B − A = **+$598 (+13,7 %)** sobre $4.380 en 392 trades emparejados; con el tick sintético en entradas **+$417 (+9,5 %)**, $/trade +1,06 (IC 95 % −1,79 .. +3,92), flips 0,5 % | **No es una medición de H1**: mezcla la ausencia de slippage, la demora de las protectoras y los fills reales. Se repite con v4 |
| 4 entradas Tick1 fuera del rango ±1 tick del minuto de `mnq_fut.npz`; 0 en Off | A mirar en S2 (ticks de Continuum vs minutos de Databento) |

## Dato colateral: calentamiento

Dos corridas Tick1 sobre la misma ventana 2026-08-21 → 09-15 pero con inicio distinto (2026-08-01 vs 2026-06-01) coinciden en 62 de 70-74 trades, con 12 + 8 trades distintos y stops distintos: con 15 días de calentamiento el estado (ATR, tendencia) todavía no es idéntico. Toda comparación va sobre corridas del mismo período exacto, como estaba previsto.

## Qué sigue

1. Parche v4 (plan B): con `fillCfg > 0`, no llamar a los `Set*`; en el fill de la entrada emitir `ExitLongStopMarket` / `ExitLongLimit` (o `Short`) en `fillBip` con los mismos niveles (ticks o precio, incluido el target recalculado por precio de fill y el break-even de VOLB), cancelarlas antes de las salidas a mercado, y revisión adversarial. Con `Off` nada cambia.
2. Repetir (c) Tick1 y (d) Off sobre 2026-06-01 → hoy; `fill_gap.py --slip-b 1` (scope `all`). Verificación en el export de órdenes: "Stop loss" y "Profit target" con segundos ≠ :00.
