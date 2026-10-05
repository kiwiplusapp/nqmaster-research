# 🗺️ MAPA DEL PROYECTO: Trading algorítmico NQ + Oro (NinjaTrader 8)

> Punto de entrada. Todo el conocimiento del proyecto, cómo avanzamos y el estado actual.
> Vista visual: abrir **[[Mapa.canvas]]**.

## Estado actual (28-sep-2026)
- Estrategia final: **[[NQMaster]]**, una sola estrategia con dos gráficos (MNQ y MGC).
- **Validada en NinjaTrader** con futuros reales 2024–2026: ver [[Resultados NinjaTrader]].
  - MNQ MaxSharpe: 2,635 trades, win rate 65.9%, **PF 1.30**, **+$30,025**, DD $3,415.
  - MGC Gold: 410 trades, win rate 47.8%, PF 1.21, +$4,952.
- Próximo paso: **2–4 semanas en Sim**, después eval de Topstep 50K. Ver [[Proximos pasos]].

## Proceso
- [[Objetivo y reglas]]: qué busca Federico y las reglas de la prop firm
- [[Cronologia]]: cómo avanzamos, versión por versión
- [[Metodologia]]: cómo se valida (y los errores que encontramos)
- [[Datos]]: fuentes, exportaciones y conversiones
- [[Lecciones clave]]

## Lo que funciona (módulos del portafolio)
| Módulo | Idea | Nota |
|---|---|---|
| ORB60 | Ruptura del rango de 60 min en días de retroceso, a favor de la tendencia | [[ORB60 Pullback Day]] |
| MSEQ | Secuencia de momentum en 5 min, días alcistas | [[MSEQ Momentum Sequence]] |
| CRT11 | Candle Range Theory: vela de 11:00 contra la de 10:00 | [[CRT11]] |
| MOM11 | Momentum a las 11:00 con filtro VWAP | [[MOM11]] |
| MOM13 / MOM1030 / ON07 / REV06 | Momentum o reversión por horario | [[Modulos por horario]] |
| LON | Ruptura de Londres + FVG | [[LON London FVG]] |
| ICT | Barrido + CISD en la apertura de NY | [[ICT Open]] |
| GOLD | ORB30 del oro a favor de la tendencia | [[GOLD ORB30]] |
| Guard | FOMC, objetivo de la eval, drawdown | [[Account Guard]] |

## Lo que NO funciona (descartado con datos)
- [[IFVG y SMC]] · [[ICT Sniper y PO3]] · [[Estrategias TradingView]] · [[Order flow y perfil de volumen]]
- [[Oro por horario]] · [[Filtros y optimizaciones rechazadas]] · [[Machine learning]]

## Resultados
- [[Resultados NinjaTrader]]: validación real
- [[Evaluaciones prop firm]]: tasas de aprobación y dinero por mes

## Oro (5-oct-2026)
- [[GoldMaster (oro)]]: estrategia propia para MGC. Perfil WinRate: WR 70%, PF 1,99 en MGC real 2024-26 (0,3 trades/día). Perfil Robust: PF 1,37 y positivo en 16 años.
