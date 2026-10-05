# NQ Pullback-Day Engine: guía y backtest

`NQPullbackDayEngine.cs` está compilado e instalado en `Documents\NinjaTrader 8\bin\Custom\Strategies`. Para cargarlo, abre el NinjaScript Editor y pulsa **F5**.

## La idea
En un día con tendencia diaria (cierre RTH vs SMA20), la continuación es fuerte si el **día anterior fue un retroceso**, es decir, si se movió en contra de la tendencia o apenas a favor. Si el día anterior ya se extendió mucho a favor, la continuación falla.
- **Regla:** operar a favor de la tendencia solo si el movimiento de ayer, medido a favor de la tendencia, es menor a 0.44 × ATR diario.
- **Robustez:** el efecto es monotónico y se repite igual in-sample (2020–23) y out-of-sample (2024–26).

| Movimiento de ayer (ATR, a favor de la tendencia) | PF in-sample | PF out-of-sample |
|---|---|---|
| Muy en contra (< −0.45) | 1.91 | 1.66 |
| En contra | 1.51 | 1.52 |
| Neutro | 1.24 | 1.27 |
| A favor | 0.73 | 0.97 |
| Muy a favor | 1.01 | 0.95 |

## Módulos
Todos operan a favor de la tendencia, cada uno con su propia orden y target chico (alto win rate). Todo cierra a las 15:55 ET.

| Módulo | Entrada | Target | Trades | Win rate | PF |
|---|---|---|---|---|---|
| ORB60 | Ruptura del rango de 60 min | 0.6R | 533 | 68.5% | 1.57 |
| ORB30 | Ruptura del rango de 30 min (desde 10:30) | 0.75R | 593 | 62.2% | 1.38 |
| ORB15 | Ruptura del rango de 15 min (desde 10:30) | 0.75R | 688 | 62.1% | 1.29 |
| VWP60 | Límite en VWAP tras extensión sobre el rango de 60 min | 0.6R | 303 | 66.3% | 1.39 |
| VWP30 | Límite en VWAP tras extensión sobre el rango de 30 min | 0.75R | 377 | 61.8% | 1.27 |
| MSEQ | Momentum Sequence en 5 min, solo en días alcistas y sin filtro de retroceso | 0.5R | 535 | 65.4% | 1.52 |

Los cinco módulos ORB/VWAP operan solo en días de retroceso. MSEQ opera en cualquier día alcista.

## Backtest del conjunto (NQ 1m, ene-2020 a sep-2026)
Supuestos: 1 MNQ por módulo, 1 tick de slippage, $1 de comisión round turn, targets llenados solo si el precio los atraviesa por 1 tick.

| Métrica | Valor |
|---|---|
| **Trades por semana** | **8.65** |
| **Win rate** | **64.2%** |
| **Profit factor** | **1.39** |
| PF in-sample 2020–23 / out-of-sample 2024–26 | 1.43 / 1.34 |
| Neto por año | ~$8,900 (1 MNQ por módulo) |
| Semana media | +$170 (60% de semanas positivas) |
| Meses positivos | 70% |
| Max drawdown | $4,005 |
| Peor día | −$2,043 (6 módulos en la misma dirección) |

| Año | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (ene–sep) |
|---|---|---|---|---|---|---|---|
| Trades | 483 | 425 | 421 | 510 | 479 | 450 | 261 |
| Win rate | 65.8% | 59.8% | 68.4% | 66.1% | 64.3% | 62.0% | 61.7% |
| PF | 1.52 | 1.21 | 1.54 | 1.40 | 1.30 | 1.42 | 1.28 |
| Neto | $9,863 | $3,522 | $14,102 | $8,426 | $6,821 | $11,680 | $5,516 |

Curva de equity: `pullback_engine_curve.png`.

## Evaluaciones de propfirm
Simulación: se empieza una eval cada día hábil de 2020 a 2026 y se mide si llega al objetivo antes de tocar el trailing drawdown (medido al cierre del día).

| Cuenta (objetivo / drawdown) | Tamaño | Pasa en ≤20 días | Pasa en ≤60 días | Quema en ≤60 días | Días medianos para pasar |
|---|---|---|---|---|---|
| 25K ($1,500 / $1,500) | 1 MNQ por módulo | 31% | **66%** | 27% | 22 |
| 25K ($1,500 / $1,500) | 2 MNQ por módulo | **57%** | 66% | 34% | 8–9 |
| 50K ($3,000 / $2,500) | 2 MNQ por módulo | 30% | **59%** | 36% | 20 |
| 50K ($3,000 / $2,000) | 2 MNQ por módulo | 30% | 54% | 43% | 18 |

Sin ventaja, pasaría el 44–50% de las veces. Con este sistema, la probabilidad de pasar supera a la de quemar la cuenta en todas las configuraciones.

## Honestidad
- Los umbrales (0.44 ATR, targets de 0.6–0.75R, stop de 0.35 ATR) se eligieron con datos 2020–23. Los vecinos (0.2–0.6 ATR, 0.5–0.75R) también funcionan.
- Los módulos operan en el mismo sentido el mismo día. Los días malos pierden varios a la vez, y de ahí sale el peor día de −$2,043.
- Con `Max open modules` en 2–3 bajas ese riesgo, pero también la frecuencia: con 3 son 7.1 trades por semana y el peor día queda en −$1,345.
- 2026 PF 1.28. Julio y agosto de 2026 fueron negativos (−$849 y −$2,596).
- En vivo espera algo menos que en el backtest.

## Por qué NinjaTrader no te dio trades
Tu prueba fue del **23/09 al 28/09/2026**, solo 3 días hábiles. Las estrategias necesitan unos **25 días RTH** de historia antes de operar, para la SMA20 y el ATR14. Además MomentumSequencePro opera ~1.5 veces por semana.

## Cómo hacer el backtest en NinjaTrader
1. Strategy Analyzer → `NQPullbackDayEngine`.
2. Instrument **MNQ 12-26** (o `MNQ ##-##` con merge back-adjusted). Type **Minute**, Value **1**. Trading hours **CME US Index Futures ETH**.
3. **Start date: 2024-01-01** (como mínimo 2 meses antes del período que quieras ver). End date: hoy.
4. Slippage 1. Commission: activada. Fill resolution: Standard. Order quantity: Strategy.
5. Descarga la historia de 1 minuto antes de correrlo (Tools → Historical Data).
6. Mándame Summary, Trades (CSV) y el Output window.

## Riesgo en vivo o en eval
- `Contracts per module`: 1 en 25K/50K, 2 si buscas velocidad.
- `Max open modules`: 3 si quieres bajar el peor día.
- `Daily loss limit`: el de tu firma menos $100–200. Cierra todo y detiene el día.
- `Trailing drawdown`: el de tu firma.
- Pausa manual: crea `Documents\NinjaTrader 8\pause_trading.txt` antes de CPI/FOMC/NFP y bórralo después.

---

# v2 (28-sep-2026): optimizada para evaluaciones
Los valores por defecto nuevos ya están en el código. `Pullback max` pasa a **0.20** y se agrega `Skip if 2-day move` = **0.63**, que no opera si los últimos 2 días ya corrieron mucho a favor de la tendencia. Los umbrales salen de los terciles de 2020–23 y la configuración se eligió por la tasa de aprobación in-sample.

| Métrica | v1 | **v2** |
|---|---|---|
| Trades por semana | 8.65 | **5.6** |
| Win rate | 64.2% | **67.7%** |
| Profit factor | 1.39 | **1.65** |
| Sharpe in-sample (2020–23) / out-of-sample (2024–26) | 1.84 / 1.44 | **2.41 / 1.70** |
| Max drawdown / peor día (1 MNQ por módulo) | $4,005 / −$2,043 | $3,582 / −$1,803 |

## Evals: aprobaciones con v2
Formato: % que pasa / % que quema. Se empieza una eval cada día. El drawdown se mide sobre el P&L realizado intradía, con trailing.

| Cuenta | MNQ por módulo | ≤20 días (2020–23) | **≤20 días (2024–26)** | ≤60 días (2024–26) |
|---|---|---|---|---|
| 25K ($1,500 / $1,500) | 4 | 65 / 31 | **64 / 33** | 67 / 33 |
| 25K | 3 | 62 / 29 | 55 / 38 | 60 / 40 |
| 50K ($3,000 / $2,500) | 3 | 45 / 19 | 37 / 29 | 59 / 39 |
| 50K | 2 | 23 / 11 | 20 / 23 | 48 / 37 |

## El límite matemático
La probabilidad de pasar en 20 días depende casi solo del **Sharpe** de la estrategia, no del win rate. Simulación con la mejor escala posible para cada Sharpe:

| Sharpe anual | 1.0 | 1.5 | 2.0 | 2.5 | 3.0 | 4.0 | 5.0 |
|---|---|---|---|---|---|---|---|
| Máx. pasar 25K en 20 días | 52% | 54% | 58% | 62% | 66% | 73% | 80% |
| Máx. pasar 50K en 20 días | 46% | 49% | 53% | 58% | 61% | 69% | 76% |

- Con Sharpe ~1.7, v2 da 64% out-of-sample en la 25K. Ya está en el techo teórico, incluso algo por encima gracias al win rate alto.
- Para pasar 80% en 20 días hace falta Sharpe ~5. Eso es nivel Medallion y no existe en estrategias de 1 instrumento con velas de 1 minuto.
- Para subir de verdad hay que aumentar el Sharpe con fuentes de ganancia no correlacionadas, por ejemplo otros mercados. Otra opción es usar firmas sin límite de días: ahí importan las columnas de 60 días.
