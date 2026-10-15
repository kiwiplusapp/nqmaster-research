# Ronda de 6 años y familias nuevas (16-oct-2026)

Federico pidió un backtest de los últimos 6 años, mejorar las estrategias existentes y sumar nuevas. El detalle está en `NQMASTER_GUIA.md`, sección "2026-10-16 (tarde)".

## Qué se probó

El criterio fue el mismo para todo. Ventana: 2020-10 a 2026-10, NQ real de Databento.

- Se elige en 2020-10 a 2023 y se comprueba en 2024-26. Ya no se exige 2010-19.
- En 2020-10 a 2023: PF ≥ 1,3.
- En 2024-26: PF ≥ 1,2, y PF ≥ 1,1 con 4 ticks de slippage.
- Meseta de parámetros: los vecinos también tienen que funcionar.
- En el portafolio: tiene que subir el Sharpe en los dos períodos, sin empeorar más de 5% el drawdown máximo ni el peor mes.

## Descartado

- **5 familias nuevas** (`research/mine/families7.py`, `b7_report.md`; 4.764 configuraciones):
  - **SQZ_BOX** (squeeze intradía) y **ON_POS** (posición dentro del rango nocturno): sin edge.
  - **PD_ACCEPT** (aceptación sobre el rango del día previo) y **PERIOD_OPEN** (apertura semanal o mensual): débiles. Pierden en 2010-14 y no suman al portafolio.
  - **ER_PERSIST** (eficiencia del recorrido a las 10:30): es la única que persiste fuera de muestra, pero es el mismo momentum que MOM1030, VOLB y MOM11, y baja el Sharpe de Ultra.
- **ORB de 08:20:** vuelve a pasar la selección con barras de 1 minuto. Sigue descartado porque el backtest con ticks le saca el edge.
- **Pesos por módulo elegidos en 2020-23:** empeoran 2024-26. Lo mismo al apagar MOM11 y MOM13.
- **ENG10:** sigue apagado, falla en 2024-26 (PF 1,10).

## Aceptado a medias

Siete módulos nuevos más LATEFH quedan programados en NQMaster, en el grupo 11, **apagados por defecto**: CA04V, SO04, GD03, RV11, ENG26, ORFAIL y CAM3.

| | Ultra hoy | Con los módulos nuevos |
|---|---|---|
| Sharpe 2020-23 | 3,45 | 3,76 |
| Sharpe 2024-26 | 3,96 | 4,09 |
| Ganancia en 6 años | | +9% |
| Drawdown máximo | | menor |

En cuentas (MFFU 50K), el resultado de 2024-26 es casi neutro:

| | Edge completo | Con 35% menos edge |
|---|---|---|
| Cambio en $/mes por cuenta | +$67 | +$8 |
| P(año negativo) | | 0% → 9% |

No pasa el criterio de cuentas de la auditoría del 16-oct. Solo hay que prenderlo si la corrida en NinjaTrader con los módulos en true gana y pasa la paridad (`parity_check.py --set ultra6`).
