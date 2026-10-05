# Metodología de validación
Volver a [[00 - MAPA]]

- **Simulación vela a vela** (Python/numba) sobre velas de 1 minuto. Sin mirar el futuro: las decisiones se toman al cierre de la vela y la orden se ejecuta en la siguiente.
- **Costos**: 1 tick de slippage en entradas a mercado/stop y en stops; los targets solo se llenan si el precio los atraviesa por 1 tick; $1 round turn (NinjaTrader usa $1.90). Si en la misma vela se tocan stop y target, se asume el stop.
- **Validación**: los parámetros se eligen con **2020–2023** (CFD), se verifican con **2024–2026** (CFD) y con **futuros reales 2024–2026**.
- **Anti-sobreajuste**: se revisan los parámetros vecinos, el rendimiento año por año, que la mejora se sostenga en los 3 períodos, y cuántas configuraciones se probaron.
- Métricas: PF, win rate, Sharpe diario, drawdown y simulación de evals desde cada día de inicio posible.

## Errores encontrados (y corregidos)
- **Ilusión de ejecución** en IFVG (TradingView llena órdenes que en la realidad no se llenan).
- **Mirar el futuro** en una simulación de FVG por prioridad de órdenes; niveles del overnight; y un filtro de rango nocturno que usaba datos hasta las 9:29 para entradas a las 3:00.
- **Repintado** en ZigZag PA (security de Pine v1/v2).
- **Bug de feriados** en NinjaTrader: días posteriores a sesiones cortas.
- **ICT**: la simulación cancelaba órdenes límite de más, y eso la hacía optimista (PF 1.61 contra 1.23 real en NinjaTrader).
- **Reglas de órdenes de NinjaTrader**: una entrada se ignora si hay una orden opuesta pendiente. Se resolvió cancelando la orden opuesta y entrando en la vela siguiente.

Relacionado: [[Datos]] · [[Lecciones clave]]
