# Plan $250-300 por día (17-oct-2026)

Pedido de Federico: promedio de $250-300 por día con buen win rate. Veredicto: **no sale de mejorar el edge por trade** (dos rondas más de investigación, cero sobrevivientes); sale de **tamaño y cantidad de cuentas fondeadas**, y depende de que el edge siga cerca del backtest.

## Por contrato base ($/día calendario, 2020-10 a 2026-10)

| Set | Completo | −35% | Sharpe |
|---|---|---|---|
| Ultra | 72 | 47 | 3,70 |
| Ultra + oro Robust | 80 | 52 | 3,90 |
| Ultra + módulos 6 años | 81 | 53 | 3,99 |
| Ultra + 6 años + oro | 89 | 58 | 4,15 |

Por año: $57/día (2023) a $238/día (2026) con el set completo.

## Por cuentas (mediana bootstrap, 2020-23 / 2024-26)

| Plan | Completo | −35% |
|---|---|---|
| 3 MFFU 50K 1c | 105 / 182 | 31 / 72 |
| 5 Lucid Flex 50K 2c | 211 / 266 | 97 / 133 |
| 5 Lucid 150K 6c/3c | 330 / 432 | 162 / 206 |
| 3 MFFU + 5 Lucid 150K | 441 / 616 | 187 / 278 |

Con 6 años + oro: 3 MFFU + 5 Lucid 150K **507 / 682** (−35%: 235 / 353, p10 23 / 97, 4-7% de años negativos).

## $200 por día por cuenta: escalera de tamaño

MFFU 50K, +1 contrato por cada $3k de colchón hasta 4, retiro dejando $11,1k: mediana $119 / 189 por día (hoy 1c: 43 / 66), 19-46% de los años ≥ $200, quiebres 0,27 / 0,69 por año; con −35%: 29 / 42 y 28-35% de años negativos. La escalera amplifica el edge que haya y se frena sola si se apaga. Lucid 150K no escala (retiros topeados). Implementado como `FundedLadderStep` / `FundedLadderMax` (opcional).

Sin edge: todo negativo (las fees se pagan igual).

## Camino

1. Prender `SixYearModules` + GoldMaster Robust (paridad en NT primero).
2. 3 asientos MFFU 1c.
3. Lucid 50K → 150K al renovar.
4. Step-up MFFU solo con 6-8 fondeadas y 3 meses de P&L real.

## Descartado hoy

- Lote 8 de familias (ruptura N días, z-score mediodía, primera pierna, agotamiento): 2.856 configs, 0 sobrevivientes → [[Descartado/Lote 8 y re-entradas (17-oct)]].
- Re-entradas tras stop: solo VOLB re-armado tiene sustancia (+$58/mes, DD +6%) → `VolbReArm` opcional, apagado.

Scripts: `research/mine/income_map.py`, `seats_plan.py`, `seats_tables.py`, `reentry_lab.py`, `families8.py`. Guía: `NQMASTER_GUIA.md` sección 17-oct.
