# Corridas con el parche v4.1 (26-oct, noche): Off 2024 → hoy y Tick1 2026-06-01 → hoy

Archivos: `trades_off_2024-01-01_hoy.csv` + `output_off_2024-01-01_hoy.extract.txt` (Off, TraceOrders on; el Output completo de 9,6 MB no se versiona, el extracto tiene las líneas de NQMaster); `trades_tick1_2026-06-01_hoy.csv` + `orders_tick1_2026-06-01_hoy.csv` + `output_tick1_2026-06-01_hoy.txt` (Tick1, TraceOrders off). Comparaciones: `fill_gap_tick1_vs_off.md` (crudo, todo el período), `fill_gap_tick1_vs_off2024.md` (sin el 25-jun), `fill_gap_v41_vs_v3.md` (efecto de los brackets explícitos sobre la corrida v3).

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

## H1 todavía no se puede leer: falta la corrida Off sobre el mismo período

El Off recibido es 2024-01-01 → hoy; el Tick1 es 2026-06-01 → hoy. El ATR de Wilder arranca en el primer día cargado (ver ESTADO, *Days to load*), así que los stops y targets en ticks difieren entre las dos corridas (MOM11: 56 de 65 pares con el mismo tipo de salida pero otro nivel) y la comparación mezcla fills con niveles. Con ese confundidor y el tick sintético en todo: Tick1 − Off = +$608 (+13,9 %) en 392 pares, $/trade +1,55 (IC 95 % −1,03 .. +4,13), 1,0 % de flips; sin el 25-jun, ver `fill_gap_tick1_vs_off2024.md`. **No es H1.** H1 se lee con `Off 2026-06-01 → hoy` (21 s de corrida) contra este Tick1.

Lo que sí se puede leer ya, con el mismo período y el mismo ATR: **v4.1 contra v3** (`fill_gap_v41_vs_v3.md`): mover los brackets de la serie de 1 min a los ticks cambia 392 de 392 trades emparejados en +$302 (+6,1 %), salidas −1,54 ticks (incluye el tick de slippage que la serie de ticks no cobra en 113 stops y 109 salidas a mercado ≈ −$111) y duración −0,66 min; 1 trade cambia de stop a target, 0 flips de signo relevantes (0,8 %).

## Qué sigue

1. Federico: `Off` sobre **2026-06-01 → hoy** exacto (mismo *Days to load*), export de trades → `fill_gap.py <off_jun> <tick1_jun> --slip-b 1 --slip-b-scope all --exclude-dates 20260625 --research ultra_d4` = H1/H2.
2. Playback con Tick1 y Contracts 6 (prueba de huérfanas con fills parciales).
3. Opcional: recargar los ticks del 2026-06-25 en Historical Data Manager y repetir el Tick1.
