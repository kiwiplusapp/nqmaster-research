# Corrida Tick1 con TraceOrders (P2b del plan), Output del 2026-10-26 03:16

Archivo: `NinjaScript_Output_2026-10-26_tick1_trace.txt` (3.139 líneas; las últimas líneas `MNQPROPBUNDLE... TERMINATED` son de otro add-on, no de NQMaster). Strategy Analyzer con el parche v3 compilado, `FillSeries = Tick1`, `TraceOrders` on, Ultra, 1 contrato.

| Qué | Resultado |
|---|---|
| Carga | `fill series Tick1 (orders on BarsInProgress 2), trace orders on` |
| Cambio de serie | `FILL SERIES Tick1: orders on BarsInProgress 2 from this bar` el **2026-08-02 19:04** (hora PC; apertura de la sesión del domingo): Continuum tiene ticks desde el 2026-08-02, no desde el 25-08 como mostraba el gráfico |
| Entradas y salidas explícitas | 495 `SubmitOrderManaged`, **todas con `BarsInProgress=2`**: 23 módulos de entrada, salidas por tiempo `<MOD>X`, y los 16 cierres de toda la posición `Sell` / `Buy to cover` de las 15:56 ET (ninguno ignorado) |
| Stop loss / Profit target | 964 llamadas `SetStopTarget()`. NinjaTrader **no traza** por `SubmitOrderManaged` las órdenes protectoras que genera internamente, así que el Output no dice en qué serie quedaron. Se verifica en el export de trades: los fills de "Stop loss" / "Profit target" tienen que traer segundos ≠ :00 (`fill_gap.py`, sección "Which series filled the orders") |
| Órdenes ignoradas / errores / `STALE` / `TICK GAP` | 0 |
| Fills | 219 entradas (primera NF05 2026-08-21 06:00, última MOM11 2026-10-23 12:00), 196 `exit fill` con señal (los cierres `Sell` / `Buy to cover` no se registran por módulo) |
| `RUN TIME` | 33,9 s de reloj, 82.560 barras de 1 min, **120.990.863 barras de la serie de ticks** (~2,1 M ticks por día) |

Pendiente para cerrar P2: export de trades (y órdenes) de esta misma corrida, y una corrida `Off` sobre el mismo período exacto con su línea `RUN TIME`.
