# Descartado en la auditoría del 16-oct-2026

Protocolo: preregistro en el docstring de cada script. Se elige en 2020-23 y se confirma en 2024-26 y en 2010-19 (costos normalizados al 0,345% del ATR). Sistema base: Ultra actual (UltraR + CPI09, MOM1030 y CPI09 ×4).

## Risk parity / HRP (`research/mine/c3_portfolio.py`, 8 configuraciones)

Pesos por volatilidad inversa (RP) y Hierarchical Risk Parity con covarianza Ledoit-Wolf. Ventanas de 126/252 días, rebalanceo mensual, versiones continua y entera.

| Período | Fijo (hoy), Sharpe | Mejor RP/HRP, Sharpe |
|---|---|---|
| 2010-14 | 0,42 | negativo |
| 2015-19 | 1,21 | 0,92 |
| 2020-23 | 3,43 | 3,42 |
| 2024-26 | 4,00 | 4,00, con 27% menos $ |

**Ninguna configuración mejora el Sharpe en los cuatro períodos.** Solo desapalancan: menos drawdown y menos plata.

Apagar el módulo más débil de cada par correlacionado tampoco pasa:

- ORB90 (correlación 0,57 con ORB60): el Sharpe baja en 2010-14, 2020-23 y 2024-26.
- VW13 (0,57 con VW13b): el Sharpe baja en 2020-23 y 2024-26.

## Apagar módulos "débiles" (`audit16_stats.py`, `x4 -MOD`)

| Apagar | Sharpe 2010-14 / 2015-19 / 2020-23 / 2024-26 | Resultado |
|---|---|---|
| ICT | 0,42→0,58 / 1,21→1,15 / 3,43→3,43 / 4,00→4,02 | Falla 2015-19 (peor mes también peor en 2010-14) |
| REV06 | 0,42→0,47 / 1,21→1,24 / 3,43→3,40 / 4,00→4,05 | Falla 2020-23 |
| ON07 | 0,42→0,40 / 1,21→1,25 / 3,43→3,39 / 4,00→3,96 | Falla 3 de 4 períodos |

El shrinkage bayesiano empírico da, para 2020-26, P(edge > 0 después de 1 tick extra) ≥ 0,90 en todos los módulos salvo ICT (0,84) y REV06 (0,83). Esos dos quedan en **vigilancia**, no apagados.

## Pausar ante una alarma del monitor

Repetido de `os_adapt.py`: pausar empeora el Sharpe 2013-19 (0,88 → 0,69-0,86). Lo que sí se usa es el fallback al set revisado.

## Tamaño "sniper" (15-oct)

Agrandar cuando un módulo tuvo ≥ 80% de WR en el último año: esos trades dan PF 1,34 y pasan peor la evaluación que 2 contratos fijos. Descartado (`sniper_eval.py`).

## Reglas de no perseguir y medición de slippage real

No se pudieron probar: no hay datos de tick ni de cuentas en vivo. Los ticks crudos de Databento se borraron y los créditos están gastados.

- Con +4 ticks por lado el sistema sigue positivo: Sharpe 2020-23 3,43 → 2,79 y 2024-26 4,00 → 3,48.
- Queda **pendiente** de datos en vivo. La herramienta para medirlo es `research/mine/impl_gap.py`.
