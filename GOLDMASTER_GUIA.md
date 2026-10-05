# GOLD MASTER: estrategia para oro (MGC)

`GoldMaster.cs` está compilada e instalada. En NinjaTrader abrí el NinjaScript Editor y presioná **F5**.

## Cómo usarla
1. Abrí un gráfico de **MGC de 1 minuto** con el horario completo de Globex (18:00-17:00 ET).
2. Cargá al menos **30 días** antes del inicio del backtest: necesita ~20 días de sesión regular (09:30-16:00 ET) para calcular el ATR y la tendencia.
3. Agregá la estrategia **GoldMaster** y elegí el **Profile**.
4. Cierra todo a las 16:51 ET y no opera los días de FOMC.

Funciona aparte de NQMaster: un gráfico de MNQ con NQMaster y otro de MGC con GoldMaster, en la misma cuenta.

## Perfiles
1 MGC por módulo, comisión $1,90 ida y vuelta + 1 tick de slippage por lado.

| Perfil | Datos | Trades/día | Win rate | PF | Sharpe | $/mes | DD máx |
|---|---|---|---|---|---|---|---|
| **WinRate** (recomendado) | CFD 2020-23 | 0,30 | 64,7% | 1,42 | 1,23 | $43 | $447 |
| | CFD 2024-26 | 0,35 | **68,8%** | **1,74** | 1,98 | $177 | $612 |
| | **MGC real 2024-26** | 0,29 | **70,3%** | **1,99** | 2,38 | $215 | $504 |
| **Robust** | CFD 2020-23 | 0,88 | 59,4% | 1,22 | 1,25 | $101 | $1.131 |
| | CFD 2024-26 | 0,94 | 61,4% | 1,35 | 1,65 | $399 | $1.807 |
| | MGC real 2024-26 | 0,88 | 61,9% | 1,37 | 1,68 | $429 | $1.684 |

**Prueba de 16 años** (2010-2019, con el costo actual relativo a la volatilidad):
- **WinRate:** PF 1,05 en 2010-14 y 0,85 en 2015-19. Antes de 2020 no ganaba.
- **Robust:** PF 1,20 en 2010-14 y 1,08 en 2015-19. Ganó en los 16 años.

**Junto a NQMaster Ultra** (MNQ real 2024-26), la correlación diaria es 0,00:
- El Sharpe sube de 3,61 a 3,89 con WinRate y a 3,96 con Robust.
- El drawdown casi no cambia.

## Módulos
| Módulo | Regla | MGC 2024-26 |
|---|---|---|
| **OD1030** | Si de 9:30 a 10:30 el oro se movió ≥ 0,3 ATR a favor de la tendencia, entra a las 10:30. Stop del otro lado de ese movimiento (máx. 0,5 ATR), objetivo 0,5R. | 61 trades, WR 74%, PF 3,0 |
| **ENG0408** | La vela de 4 h de Londres (04:00-08:00) cierra más allá del extremo de la vela 00:00-04:00. Entre 9:30 y 15:00, orden stop 1 tick por encima/debajo de la vela de Londres. Stop del otro lado, objetivo 0,5R. | 83 trades, WR 69%, PF 2,0 |
| **SVWAP22** | A las 22:00, si el precio está ≥ 0,3 ATR lejos del VWAP de la sesión, opera hacia el VWAP. Stop 0,25 ATR, objetivo 0,5R. | 48 trades, WR 69%, PF 1,3 |
| **ASIA** (Robust) | Rango asiático 20:00-24:00. Primera ruptura entre 00:00 y 06:00, solo a favor de la tendencia. Stop del otro lado (máx. 0,6 ATR), objetivo 1R. | 305 trades, WR 56%, PF 1,2 |
| **ENG0206** (Robust) | Igual que ENG0408, con las velas 22:00-02:00 y 02:00-06:00. | 90 trades, WR 63%, PF 1,2 |
| ENG0610, LATE | Solo en Custom. ENG0610 perdió plata en MGC real. | — |

ATR = media exponencial de 14 días de los rangos de la sesión regular. Tendencia = cierre anterior contra su media de 20 días.

## Para validar en NinjaTrader
Backtest de MGC 1 minuto del 01/02/2024 a hoy, 1 contrato, comisión $1,90:
- **WinRate:** ~190 trades, WR ~70%, PF ~2, ~+$6.600.
- **Robust:** ~580 trades, WR ~62%, PF ~1,37, ~+$13.600.

Las diferencias chicas son normales: el orden de llenado intrabarra de NinjaTrader no es igual al del backtest de investigación.

## Lo que conviene saber
- El oro tiene ventajas intradía mucho más débiles que el Nasdaq. De 38.000 variantes probadas en 16 años, menos de 20 ganaron en todos los períodos.
- **WinRate** cumple el objetivo de win rate ≥ 68% y PF ≥ 1,5 en 2024-26, pero depende del régimen del oro desde 2020: más volatilidad y tendencia. Si el oro vuelve a un mercado lateral como el de 2015-19, puede dejar de ganar.
- **Robust** gana menos por trade, pero ganó en los 16 años.
- Hace pocos trades (~6 por mes con WinRate). Para que mueva la cuenta, subí los contratos por módulo.

Investigación: `research/mine/gold_*.py`, `families_gold.py`, `results_gold*.csv`. Datos: `research/data/xau_long.npz` (oro 2010-2026) y `mgc_fut.npz`.
