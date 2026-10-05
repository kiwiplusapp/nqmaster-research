# Ronda de mejoras del 3 de octubre: el techo del sistema

Código: research/mine/ (daystate.py, runner.py, seqstate.py, families4.py, late_port.py, trendday_pred.py, overnight*.py, macro.py, runner_td.py, tday*.py, cushion.py).

Todo medido contra Ultra (Sharpe 3.09 / 3.43 / 3.61 en CFD 2020-23 / CFD 2024-26 / MNQ real).

| Idea | Resultado | Decisión |
|---|---|---|
| Estado del día (eficiencia, rango, VWAP) en la entrada | El PF casi no cambia por grupo | ❌ |
| Correr ganadores (trailing) | +5-16% $/mes, pero Sharpe 3.61 → 3.1-3.5 | ❌ |
| Resultado de los trades previos del día | Patrones que se dan vuelta entre períodos | ❌ |
| Momentum de la última hora y media (nunca escaneado antes) | Familia negativa; desde 2024 la última media hora revierte (no usable: en 2020-23 no se veía) | ⚠️ |
| **LATE15**: a las 15:00, si el día ya se movió ≥ 0.5 ATR a favor de la tendencia, seguirlo (stop 0.3 ATR, 0.5R) | PF 1.44 / 1.29 / 1.29 y 1.39 en 2015-19; en cartera +$30-40/mes, Sharpe +0.01 | ✅ agregado (UseLate15) |
| Predicción de "día de tendencia" a las 10:30 | AUC 0.63-0.65 estable; PF de trades: 1.60 en días "alta prob." vs 1.41 en "baja" | — |
| Tamaño según esa predicción | Sharpe +0.03-0.05 con fracciones; con contratos enteros empeora | ❌ |
| Correr ganadores solo en días predichos de tendencia | +1% PF | ❌ |
| TDAY: módulo de tendencia a las 10:30 | Solo: PF 1.37 / 1.34 / 1.37. En la cartera baja el Sharpe (se pisa con MOM1030/MOM11) | ❌ |
| Drift nocturno (largo 18:00 → 07:00) | PF > 1 en todos los períodos (11 años), pero baja el Sharpe de la cartera | ❌ |
| Noticias 8:30 (CPI/NFP) y FOMC | Pocas muestras; el CPI cambia de signo entre períodos | ❌ |
| Tamaño según colchón en la fondeada | Igual o peor que tamaño fijo | ❌ |
| Pedir el cobro en Lucid con ganancia ≥ $5,000 (en vez de $3,000) | Cobro esperado por cuenta $4.2-5.4k → $5.6-7.7k | ✅ regla operativa |

**Conclusión:** la ventaja por trade está en su techo robusto. Las palancas grandes que quedan son de estructura: tipo de cuenta (Lucid), momento del cobro y cantidad de cuentas.
