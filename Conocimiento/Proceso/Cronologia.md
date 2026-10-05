# Cronología: cómo avanzamos
Volver a [[00 - MAPA]]

1. **IFVG Sniper**: port del indicador de Pine a NinjaTrader. En TradingView marcaba 81% de acierto; con órdenes reales dio 42% y PF 0.71. Ver [[IFVG y SMC]].
2. **NQ Trend Day (ORB + VWAP)**: primera ventaja real (PF ~1.36 en 2020–26, más débil en 2025–26).
3. **Búsqueda masiva**: más de 25,000 configuraciones (ICT, SMC, PO3, Miner, ML, order flow, stat-arb). Casi nada sobrevive. Ver [[Machine learning]], [[ICT Sniper y PO3]].
4. **Estrategias de TradingView** que trajo Federico: Peak Hours (pierde), ZigZag PA (repinta), **Momentum Sequence** (sí funciona → [[MSEQ Momentum Sequence]]).
5. **Pullback Day Engine**: descubrimiento del **día de retroceso** (la tendencia sigue con fuerza después de un día en contra) → [[ORB60 Pullback Day]].
6. **Bug de feriados** encontrado con el CSV de trades de NinjaTrader: el backtest daba PF 1.29 y NinjaTrader 1.02. Corregido. Ver [[Metodologia]].
7. **Datos reales de futuros** exportados con BarExporterUTC (MNQ, NQ y MGC desde 2024). Ver [[Datos]].
8. **CRT** → [[CRT11]]. **Dhesi / ICT** → solo sirve la apertura de NY → [[ICT Open]].
9. **MOM11** (módulo diario, ~80% de acierto) → portafolio diario (99% de los días con trades).
10. **Mapa horario** del día completo → [[Modulos por horario]]. **Londres** → [[LON London FVG]].
11. **Optimización profesional**: filtros y pesos rechazados; aceptados el filtro VWAP en MOM11 y los **contratos fijos**. Ver [[Filtros y optimizaciones rechazadas]].
12. **Oro**: solo funciona ORB30 → [[GOLD ORB30]]. Perfil de volumen: no funciona.
13. **Noticias**: saltar días de FOMC → [[Account Guard]]. Módulo ICT programado.
14. **[[NQMaster]]**: todo en una sola estrategia, con los perfiles MaxSharpe, WinRate70 y Gold.
15. **Validación en NinjaTrader** con los datos de Federico: PF 1.30 en NQ y 1.21 en oro ✅. Ver [[Resultados NinjaTrader]].
