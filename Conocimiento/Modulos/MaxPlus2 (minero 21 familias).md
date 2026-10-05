# MaxPlus2: resultado del minero de estrategias (2026-10-02)

## El minero (research/mine/)
- Motor único en 1 minuto: entradas a mercado, límite y stop; slippage de 1 tick; comisión $1.90; stop primero dentro de la barra.
- **21 familias y 9,254 variantes.** Familias: AMD/POC (Ismael Huerta), rangos de sesión, retest y fade de niveles (PD/ON/Londres/VA), VWAP pullback y bandas, opening drive y su pullback, 8 patrones de 5m (Donchian, consecutivas, fractal sweep, FVG, order block, squeeze, engulfing, inside bar), regla del 80% de VA, anclas horarias (VWAP, VWAP de sesión, POC/cierre previo, apertura de sesión), gap, retest de HOD, volatility breakout (L. Williams), pivotes clásicos y Camarilla, números redondos, niveles semanales, divergencia de RSI, inventario overnight, inside day.
- **Protocolo:** elegir con CFD 2020-23 y validar con CFD 2024-26 y MNQ real 2024-26. Para las reglas de contexto: elegir con 2020-23, validar con 2024-25 y usar **2026 como examen final** (no se usa para elegir).
- **Robustez por familia** (% de variantes elegidas en 2020-23 que se sostienen en 2024-26, CFD y real):
  - VOL_BREAK: 92%.
  - OPEN_DRIVE: 62%.
  - VWAP_PULLBACK: 29%.
  - Rangos de sesión: 25%.
  - Anclas horarias: 18%.
  - **AMD/POC: 0%** (PF mediano 0.86 / 0.90 / 0.88), igual que los patrones de 5m, niveles, pivotes y números redondos.
- **Volatility breakout** (k = 0.45 × rango del día previo desde la apertura, a favor de la tendencia, stop en la apertura, 2R): PF 1.43 / 1.47 / 1.37. Suma dinero, pero baja el winrate total 1-1.6 puntos. Opcional, no incluido.
- **SOPEN 08:00:** descartado, es un pico aislado de parámetros. **VW13 (13:01, precio ≥ 0.30 ATR de la VWAP a favor de la tendencia, stop 0.15 ATR, 0.5R):** estable entre sus vecinos; incluido.

## Minero de filtros (12 variables de contexto por trade)
- Elegir filtros solo con 2020-23 es **sobreajuste**: en esa muestra el PF sube de 1.39 a 1.70, pero fuera de ella el Sharpe baja y se pierde 24% de dinero.
- **Error de lookahead corregido:** "gap" en módulos de la madrugada, y LON tenía guardada la hora de entrada fija en 05:00.
- **Protocolo estricto: quedan 12 reglas.**
  - 11 de doble tamaño:
    - CRT11: trend, gap, pdret.
    - MSEQ: posición en el rango, momentum de 30 min, retorno de 5 días.
    - ORB60: gap, retorno de 5 días, ratio de ATR.
    - ORB90: cerca de la VWAP, lejos de la apertura.
  - 1 de salto: ON07 cuando el día previo fue en contra (< −0.36 ATR).
  - **Tope total ×2.**

## MaxPlus2 = MaxPlus + confluencia + 12 reglas de contexto + VW13 (1 contrato base)

| | WR | PF | Sharpe | $/mes | DD |
|---|---|---|---|---|---|
| CFD 2020-23 | 66.2→66.9 | 1.389→1.460 | 3.06→3.25 | 1049→1383 | 2835→3579 |
| CFD 2024-26 | 65.2→65.7 | 1.365→1.411 | 3.01→3.08 | 1314→1664 | 3251→4180 |
| MNQ real 2024-26 | 66.2→66.8 | 1.397→1.449 | 3.22→3.32 | 1368→1750 | 3037→4074 |
| **2026 examen final, CFD** | 67.2→67.5 | 1.419→1.489 | 3.11→3.26 | 1752→2261 | |
| **2026 examen final, real** | 68.9→69.2 | 1.504→1.582 | 3.51→3.62 | 1778→2313 | |

## Cuentas de prop firm (simulación minuto a minuto con ganancia no realizada)
- **Apex 25K:** conviene **MaxPlus** en evaluación y fondeada. Con MaxPlus2 la fondeada se quema 3.4 veces por año en lugar de 1.9, y deja −10% de dinero.
- **Apex 50K** (por cuenta, $/mes CFD 2020-23 / CFD 2024-26 / real):
  - MaxPlus2: evaluación ×4 → fondeada ×1: $1,013 / $1,022 / $1,197, con 0.4 / 1.0 / 0.4 quemas por año.
  - MaxPlus: evaluación ×4 → fondeada ×2: $1,383 / $1,336 / $1,379, pero con ~2 quemas por año.
  - MaxPlus: evaluación ×4 → fondeada ×1: $725 / $893 / $898.
