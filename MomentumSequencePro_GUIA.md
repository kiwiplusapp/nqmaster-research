# NQ Momentum Sequence PRO: guía

Archivo: `MomentumSequencePro.cs`. Compilado contra tu NinjaTrader 8 e instalado en `Documents\NinjaTrader 8\bin\Custom\Strategies`.
En NinjaTrader abre el NinjaScript Editor y pulsa **F5**.

## Lógica
| Parte | Regla |
|---|---|
| Filtro diario | Último cierre RTH por encima de la SMA20 de cierres RTH. Si no, la estrategia no opera ese día. |
| Setup (5 min) | 1 vela bajista ("main") y después 5 velas alcistas. Cada una cierra más alto que la anterior y ninguna perfora el mínimo de la vela main. |
| Horario | La vela que da la señal debe abrir entre 10:30 y 15:45 ET. |
| Entrada | A mercado, en la apertura de la vela siguiente. Solo compras. |
| Stop | Cierre de la señal − 1.75 × (cierre de la señal − mínimo de la vela main). |
| Target | 0.5R, medido desde el precio de fill. |
| Salida por tiempo | Cierra todo a las 15:55 ET. |

## Resultados (backtest barra a barra de esta misma lógica, NQ 1m de ene-2020 a sep-2026)
Supuestos: 1 MNQ, 1 tick de slippage en entrada y stop, $1 de comisión round turn. Los targets se llenan solo si el precio los atraviesa por 1 tick.

| Métrica | Valor |
|---|---|
| Trades | 535 (~1.5 por semana) |
| **Win rate** | **65.4%** |
| **Profit factor** | **1.52** |
| Neto | +$9,880 por 1 MNQ |
| Ganancia media / pérdida media | +$83 / −$103 |
| Riesgo mediano por trade | 88 pts ($177 por MNQ) |
| Max drawdown | $1,847 |
| Peor día | −$567 |
| Pérdidas seguidas (máx.) | 6 |
| Meses positivos | 69% |

| Año | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (ene–sep) |
|---|---|---|---|---|---|---|---|
| Trades | 99 | 85 | 44 | 90 | 102 | 64 | 51 |
| Win rate | 66.7% | 68.2% | 63.6% | 73.3% | 63.7% | 53.1% | 64.7% |
| PF | 1.28 | 1.92 | 1.40 | 2.37 | 1.46 | 1.08 | 1.65 |

| Validación | Win rate | PF |
|---|---|---|
| In-sample 2020–2023 | 68.6% | 1.66 |
| Out-of-sample 2024–sep 2026 | 60.8% | 1.38 |
| Con 2 ticks de slippage (estrés) | 65.2% | 1.49 |

**Estabilidad de parámetros:** los vecinos siguen dando PF 1.3–1.6. Es el caso de N = 4–5, target 0.5–0.75R, stop 1.75–3× y filtro VWAP opcional.

**Honestidad:**
- Salió de un grid de ~22,000 combinaciones. Aunque la zona es amplia y estable, en vivo espera algo menos: PF ~1.2–1.4.
- 2025 fue flojo: PF 1.08, win rate 53%.
- El tramo sep-2024 a ene-2026 dio PF 1.03.
- Solo opera en compras y en días alcistas. En un mercado bajista largo casi no opera, y eso es a propósito.

## Configuración en NinjaTrader
| Campo | Valor |
|---|---|
| Instrumento | MNQ (contrato front) |
| Serie | **Minute 5** (con otro timeframe no opera y lo avisa en el Output) |
| Trading hours | CME US Index Futures ETH |
| Días a cargar | 60 o más (la SMA20 necesita 20 días RTH completos) |
| Order quantity | Strategy |

## Prop firm
| Cuenta | Tamaño sugerido | Por qué |
|---|---|---|
| 50K (drawdown $2,000–2,500) | **1 MNQ** | Drawdown histórico de $1,847 |
| 100K / 150K (drawdown $3,000–4,500) | 2 MNQ | Drawdown de ~$3,700 |
| 25K (drawdown $1,200–1,500) | No recomendada | El drawdown de 1 MNQ supera el límite |

- Con 1 MNQ gana ~$1,470 por año. Es lenta para pasar una eval sola.
- Suma mucho combinada con NQ Trend Day PRO: son ventajas distintas y operan otros setups.
- **Pausa manual:** crea `Documents\NinjaTrader 8\pause_trading.txt` antes de CPI, FOMC o NFP. Bórralo para reanudar.
- Parámetros de riesgo:
  - `Daily loss limit`: 600. Cierra todo y detiene el día.
  - `Max trades per day`: 6.
  - `Risk per trade $`: si es mayor que 0, calcula los contratos según el stop.
  - `Trailing drawdown`: pon el de tu firma.

## Verificación antes de usarla en una eval
1. Strategy Analyzer: MNQ, 5 min, ETH, de 2024-01-01 a hoy, slippage 1, con comisión. Mándame Summary + Trades (CSV) para compararlo trade por trade.
2. 2 a 4 semanas en Sim101.
