# Perfil Ultra (2026-10-03)

## Datos 2015-2026
- Nasdaq 1 minuto de histdata (NSXUSD) 2015-2019 + 2020-2026: una sola fuente continua (data/nqhd_long.npz), sin volumen (VWAP = TWAP).
- **Módulos actuales en 2015-2019:** el portafolio pierde todos los años con costos reales (PF 0.79). La causa son los costos: en 2015 el NQ valía ~4,500 y se movía ~55 puntos por día, así que los costos pesaban 3.5% del rango, contra 0.46% hoy. **Antes de costos, el PF fue de 1.01 a 1.34 todos los años.**
- **Normalizando a los costos de hoy** (0.345% del ATR por trade):
  - **Robustos 2015-2026:** ICT, MSEQ, CRT11, LON y ORB60.
  - **Solo funcionan desde 2020:** MOM11, MOM1030, MOM13, ON07 y REV06 (PF 0.86-0.99 en 2015-19). Es un riesgo de régimen.

## Minero con 11 años (research/mine, results_long.csv y results_longnorm.csv)
- Eligiendo con 2015-2019 y probando en 2020-23, 2024-26 y MNQ real, la familia más robusta es **VOL_BREAK** (volatility breakout de Larry Williams): 53% de sus variantes pasan PF ≥ 1.15 en todos los tramos.
- **Variante elegida:** stop-entry en apertura RTH ± 0.45 × rango RTH del día previo, en ambas direcciones, stop en la apertura, objetivo 2R, entradas hasta las 15:00. PF normalizado 1.22 / 1.23 / 1.37; en MNQ real 1.42; 0.76 trades por día.
- **También descartado:**
  - Meta-labeling con machine learning (walk-forward de 5 años): no ordena los trades.
  - Tipo de día a las 10:30 (rango de la primera hora, volumen relativo): ruido.

## Ultra = MaxPlus2 + VOLB (1 contrato base, ICT x2)

| | Trades/día | WR | PF | Sharpe | $/mes |
|---|---|---|---|---|---|
| CFD 2020-23 | 4.66 | 64.9 | 1.42 | 3.09 | 1,656 |
| CFD 2024-26 | 4.62 | 63.5 | 1.45 | 3.43 | 2,317 |
| MNQ real 2024-26 | 4.45 | 64.3 | 1.48 | 3.61 | 2,429 |
| 2026 real | 3.91 | 66.6 | 1.63 | 4.23 | 3,266 |

## Cuentas Apex ($/mes por cuenta; evaluación con 4 contratos, fondeada con 1)
- **25K:** Ultra $682 / $695 / $754, contra MaxPlus $603 / $589 / $708.
- **50K:** Ultra $1,238 / $1,362 / $1,443, contra MaxPlus $725 / $893 / $898.

## En NinjaTrader
- Perfil **Ultra**. Interruptor: UseVolBreak.
- VOLB nunca cancela órdenes de otros módulos: espera si hay una posición u orden en dirección contraria.
- **Corrección incluida:** en MaxPlus2 el ICT no tenía su doble tamaño; ahora lo tiene en MaxPlus2 y en Ultra.
- Copias de seguridad: `NQMaster_backup_pre_maxplus2.cs` y `NQMaster_backup_pre_ultra.cs`.
