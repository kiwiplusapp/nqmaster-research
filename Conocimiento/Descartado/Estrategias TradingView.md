# Estrategias de TradingView que trajo Federico
Volver a [[00 - MAPA]]
- **NASDAQ 100 Peak Hours**: PF 0.82–0.94. Además tenía un bug: el trailing estaba en ticks en lugar de puntos. ❌
- **ZigZag PA V4.1**: en TradingView PF 26 y 89% de acierto por repintado; sin repintar, PF 0.85. ❌
- **Momentum Sequence (Herman)**: ✅ funciona en 5 minutos, solo compras → [[MSEQ Momentum Sequence]].
- **ORB 15m + EMA20 en 2m**: sin filtro PF ~0.9–1.0; con filtros PF 1.4–1.5, pero repite lo que ya hace ORB60 y no suma.
- **Londres de LozTradez**: tal como se enseña no funciona; la versión con tendencia → [[LON London FVG]].

## Estrategias de traders de redes (28-sep)
- **Gerard García**: ORB de 5 min + scaling in, 1% de riesgo. PF 0.90 / 1.11 / 1.14; el scaling in no mejora. Nuestro [[ORB60 Pullback Day]] es mejor (~1.55). ❌
- **Tradefather**: bank level (zona lateral) + vela de momentum mayor que el ATR, con breakeven, trailing y scale-in. 960 variantes en 1 y 5 min, PF mediano 0.82–0.91 en 2024–26 y datos reales. Las variantes que ganaban en 2020–23 dan PF 0.80 en datos reales. BE, trailing y scale-in no cambian nada. ❌
