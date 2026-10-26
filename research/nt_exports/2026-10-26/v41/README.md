# Corridas con el parche v4.1 (26-oct, noche): Off 2024 → hoy, Tick1 2026-06-01 → hoy y Off 2026-06-01 → hoy (H1)

Archivos: `trades_off_2026-06-01_hoy.csv` (Off sobre la ventana del Tick1, para H1); `trades_off_2024-01-01_hoy.csv` + `output_off_2024-01-01_hoy.extract.txt` (Off, TraceOrders on; el Output completo de 9,6 MB no se versiona, el extracto tiene las líneas de NQMaster); `trades_tick1_2026-06-01_hoy.csv` + `orders_tick1_2026-06-01_hoy.csv` + `output_tick1_2026-06-01_hoy.txt` (Tick1, TraceOrders off). Comparaciones: `fill_gap_tick1_vs_off.md` (crudo, todo el período), `fill_gap_tick1_vs_off2024.md` (sin el 25-jun), `fill_gap_v41_vs_v3.md` (efecto de los brackets explícitos sobre la corrida v3).

## Compuerta A: Off v4.1 = baseline

`trades_off_2024-01-01_hoy.csv` es **idéntico byte a byte** al export Standard pre-parche del 26-oct (3.295 trades). Tercera vez que la equivalencia con Off se prueba en la PC (v3, v3 órdenes, v4.1).

## Tick1 v4.1: la mecánica de los brackets explícitos funciona

| Qué | Evidencia |
|---|---|
| Brackets en la serie de ticks | En el **export de trades** (hora del fill) los `StopX` / `TargetX` traen segundos: ICT `TargetX` 10:52:20 (Off "Profit target" 10:53:00), ICT `StopX` 13:25:25, LON `TargetX` 09:36:56, CRT11 `TargetX` 14:18:39. Fills exactamente en el nivel (`StopX` = stop en el 100 %, `TargetX` = límite en el 97 %); el tick de slippage no está (ICT stop 29.935,50 contra 29.935,25 en Off) → `fill_gap --slip-b 1 --slip-b-scope all`. |
| OCO / cancel del hermano | 113 `StopX` llenados, los 113 con un `TargetX` cancelado a ≤ 1 min; 170 `TargetX` llenados, los 170 con un `StopX` cancelado. 392 entradas = 113 + 170 + 109 salidas por tiempo o cierre. |
| Contadores `RUN TIME` | `0 orphan protective orders cancelled, 0 market exits forced without a confirmed cancel`. Sin "Ignored", sin rechazos, sin `STALE`. |
| Hueco de ticks | **19 minutos sin ticks el 2026-06-25, 11:01 → 11:19 ET** (último tick 10:58:48). Continuum no tiene ticks de ese tramo; el día se excluye de H1 (`--exclude-dates 20260625`) o se recarga el histórico de ticks de ese día en la PC. Resto de la ventana: 0 huecos. |
| Tiempo | Off: 21,1 s para 991.109 barras de 1 min (21 µs por barra). Tick1: 64,0 s para 144.135 barras de 1 min y 236 M ticks (444 µs por barra de 1 min, 0,27 µs por tick): **×21 por barra de 1 minuto**. Un Tick1 2024 → hoy tardaría ~7 min si hubiera ticks. |
| Columna `Time` del export de órdenes | Es la hora de **envío** de la orden, no la del fill: las entradas muestran el último tick antes del cierre de barra (segundos ≠ :00 en el 90 %) y los brackets la hora del fill de la entrada (:00 en el 83 % de los `TargetX`). Para leer fills usar el export de trades. Corrige la lectura del README de `tick1_jun_today` (allí sí eran `Set*` en la serie de 1 min: lo probaba el export de trades). |

## H1 / H2 (26-oct, con `trades_off_2026-06-01_hoy.csv`): el modelo de fills de 1 minuto se sostiene

Off y Tick1 sobre **el mismo período (2026-06-01 → 2026-10-23, mismo *Days to load*)**: 392 trades cada uno, 388 pares sin el 25-jun (hueco de ticks), 100 % emparejados, **0 cambios de desenlace** (stop 111/111, target 169/169, tiempo 108/108). Informe: `fill_gap_h1.md` (+ `_pairs.csv`). Comando: `python3 fill_gap.py trades_off_2026-06-01_hoy.csv trades_tick1_2026-06-01_hoy.csv --slip-b 1 --slip-b-scope all --exclude-dates 20260625 --research ultra_d4`.

| Lectura | Pares | Tick1 − Off | Por trade (IC 95 %) | Δneto / neto Standard (IC 95 %) |
|---|---|---|---|---|
| Todo, tick sintético + brackets relativos al fill desplazados | 388 | **−$58 (−1,1 %)** | −0,15 (−1,10 .. +0,80) | **−1,1 % (−8,2 % .. +5,9 %)** |
| Sin las 48 salidas por tiempo que v4.1 decidió una barra después (mecánica, no precio) | 340 | +$10 (+0,2 %) | +0,03 (−0,02 .. +0,08) | +0,2 % (−0,1 % .. +0,6 %), 0 flips |
| Lectura cruda anterior (tick sintético sin desplazar los brackets; sesgo −1 tick por bracket) | 388 | −$182 (−3,5 %) | −0,47 (−1,41 .. +0,48) | −3,5 % (−10,4 % .. +3,6 %) |

**Regla 5A.4 del plan:** el IC queda entero por encima de −15 % en las tres lecturas → **el modelo de fills de 1 minuto se da por bueno; nada del programa se recalcula con un neto corregido por fills**. Ventana: 4 meses, 388 trades, un solo período; la Δ por tipo de orden es −0,24 $/trade en entradas a mercado (IC −1,58 .. +1,10, dominada por las 48 salidas mecánicas), +0,07 en entradas stop (IC −0,06 .. +0,20), +0,10 en límite (IC −0,20 .. +0,39). Las entradas límite de LON llenan 0,42 ticks *mejor* en ticks (fill a través del nivel); las stop de VOLB llenan igual en 58 de 59.

**Slippage (una sola vez):** Off trae el tick de NinjaTrader en entradas a mercado/stop y en salidas por stop/mercado. NinjaTrader no aplica slippage en la serie secundaria, así que `fill_gap --slip-b 1` se lo suma a Tick1 **y desplaza con el fill los niveles de los brackets que la estrategia calcula desde `EntryPx`** (1 tick en módulos con stop/target en ticks y en el break-even de VOLB, 1 + R ticks en el target de los módulos `PriceTarget`, 0 en el stop absoluto). Sin ese desplazamiento cada bracket de Tick1 lee exactamente 1 tick peor (64/64 MOM11, 31/31 REV06… todos con Δ = −$0,50): era el −3,5 % de la lectura cruda, no precio. El slippage real (H5) reemplaza la hipótesis de 1 tick por celda, nunca se suma.

### Dos hallazgos de mecánica que salen de la comparación (van al parche v4.2)

1. **`EntryBar` de los fills a mercado (v4.1 → v4.2).** En Off, NinjaTrader llena la orden a mercado en la apertura de la barra siguiente pero llama `OnExecutionUpdate` con `CurrentBars[0]` todavía en la barra que la envió (ON07 con MaxHold 60: fill 07:00:00 ET, salida 08:00:00). En Tick1 el fill llega en el primer tick del minuto siguiente con el mismo `CurrentBars[0]`, y `FillAhead()` de v4.1 le sumaba 1 → la salida por tiempo se decide una barra después (`ON07 exit: time exit` a las 09:01 en el Output, 08:00 ET → 08:01). Afecta a las 48 salidas por MaxHold de ON07 (26), NF05 (15), LF0430 (4), SO04, MOM1030 y ORFAIL; no a las del flatten de 15:56 ni a la de LON 09:31 (hora fija). Para stop/límite el +1 sigue siendo correcto (Off los evalúa en la barra cuyo rango contiene el nivel). **v4.2:** `FillAhead(t, order)` suma la barra solo si `OrderType != Market`.
2. **`LateBar()` en Market Replay.** `Core.Globals.Now` es el reloj de la PC también bajo la conexión Playback, así que cada barra reproducida del 13-15 oct se leyó como "processed late" (13 días) y la estrategia no entró nunca: eso explica el Playback sin trades. **v4.2:** `NowClock()` devuelve la última barra de 1 min bajo la conexión Playback (leído en cada llamada) y `Core.Globals.Now` si no; lo usan `LateBar()` y `RollDue()` (que con la PC después del roll del contrato habría frenado el replay). En vivo (sin Playback) nada cambia; `playbackMode` (fijado en `State.Realtime`) solo decide si la serie de llenado sigue encendida.

Ambos cambios están condicionados (`fillCfg > 0` o Playback): con Off en el Analyzer el código es el mismo → el export Off tiene que seguir idéntico byte a byte (cuarta prueba).

## Qué sigue

1. Federico, en la PC con v4.2 (`check.sh` verde acá; revisión adversarial en `docs/experimentos/01_revision_parche_fillseries.md`): **F5** y, en este orden: (a) `Off` 2024-01-01 → hoy, export de trades: tiene que ser idéntico byte a byte a `trades_off_2024-01-01_hoy.csv` (si no, frenar); (b) `Tick1` 2026-06-01 → hoy, export de trades + Output: las 48 salidas por MaxHold tienen que coincidir al minuto con Off (`fill_gap.py … --slip-b 1` debe dar "0 time exits were decided on another bar"); (c) `Off` 2026-06-01 → hoy con **Slippage = 0** en el Analyzer, export de trades: contra el Tick1 de (b) **sin `--slip-b`** es la lectura de H1 sin ningún modelo de slippage (brackets desde el fill crudo en los dos lados); (d) Playback Tick1, Contracts 6, 2026-10-13 → 10-15: Output con `Playback connection: strategy clock = last 1-minute bar`, contadores `RUN TIME` en 0 y pestaña Orders vacía tras el flatten de 15:56; (e) Playback **Off** sobre los mismos 3 días, export de trades: comparar los *hold* de las salidas por MaxHold con el backtest Off de esos días (prueba del `CurrentBar` en tiempo real; si difieren en 1 barra, el vivo tiene el off-by-one y se corrige en v4.3).
2. Opcional: recargar los ticks del 2026-06-25 en Historical Data Manager y repetir (b).
3. Después: P3 (exports de cada cuenta prop; Sim101 aparte) y S2 (paridad por módulo).
