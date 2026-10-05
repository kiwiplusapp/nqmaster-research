# ICT, PO3 y modelo Dhesi ❌ (salvo una pieza)
Volver a [[00 - MAPA]]
- **PO3**: 1,440 variantes, sin ventaja.
- **Modelo de Dhesi** (barrido → CISD/IFVG → FVG): 9,600 variantes, PF mediano ~1.0, win rate máximo 64%. Solo sobrevive [[ICT Open]].
- **ICT ATM**: el 65–75% de acierto que se menciona viene de trading discrecional.
- **Fade del IB**: PF mediano 0.85–1.04.

## ICT en la sesión de Asia (20:00-23:30 ET), setups de AG FX / yuvifutures (2026-09-28)
Barrida de liquidez (máximo o mínimo de la sesión RTH anterior, de 18:00-20:00 o de 19:00-20:00), luego CISD/MSS y entrada a mercado, en el FVG de 1m/5m o en el nivel CISD. Objetivo de 1 a 3R, con y sin filtro de tendencia, con y sin SMT contra ES (research/asia_ict.py, 96 configuraciones).
- PF mediano: 1m 0.54-0.71 (2020-23), 0.71-0.75 (2024-26), 0.74-0.86 (MNQ real). 5m: 0.97-1.03 / 0.79-0.89 / 0.92-1.02.
- SMT: solo 5-37 trades. PF 2-4 en 2020-23 pero 0.4-0.6 en 2024-26: no se sostiene.
- Mejor configuración elegida con 2020-23 (5m, 3R, con tendencia): PF 1.32 que cae a 1.04 en 2024-26 y 0.87 en MNQ real.
Conclusión: sin ventaja. Los gráficos de redes muestran casos elegidos a mano.
