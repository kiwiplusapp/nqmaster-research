# All-in en trades de 80% WR, solo en evaluaciones (16-oct-2026)

Pedido de Federico: usar todos los contratos disponibles (tope de micros de la evaluación, menos lo que ya está abierto) cuando entra un trade de un módulo con ≥80% de acierto. Script `research/mine/allin_eval.py`, resultados en `allin_eval.csv` / `allin_eval.json`.

## Datos

- Base: Ultra + CPI09 sobre NQ real 2020-26, con el mínimo intradía de los trades abiertos, +1 tick por lado.
- Reglas de cada firma según `month80.py`.
- Arranques de evaluación: T1 2020-03 a 2023-10, T2 2024 en adelante.

## Grupos de trades all-in

| Grupo | Trades | Por semana | WR | Ganancia media | Pérdida media | PF |
|---|---|---|---|---|---|---|
| Fijo (MOM1030 + CPI09) | 344 | 1,05 | 81% | $47 | −$118 | 1,72 |
| Walk-forward (WR ≥80% en el último año) | 1.557 | 4,75 | 79,6% | $46 | −$132 | 1,34 |

Los montos son por contrato.

## Resultado

- **Con 40 micros:**
  - Cada pérdida promedio es de −$4.700 y la peor de −$16.300.
  - El 92% de las pérdidas superan el drawdown de la cuenta: una pérdida quema la evaluación.
  - El 38% de los trades, incluso los ganadores, toca en algún momento una pérdida flotante igual o mayor al drawdown.
- **Lucid Pro 50K, evaluación nueva al día siguiente de cada quema, fondeada dentro de 20 días (T1 / T2):**

  | Tamaño | Edge completo | Edge −35% |
  |---|---|---|
  | All-in fijo | 62 / 74% | 47 / 51% |
  | All-in walk-forward | 88 / 72% | 83 / 59% |
  | 4 contratos fijos en todo | 88 / 91% | 79 / 82% |

- **Lucid Pro 25K, mismo criterio:**

  | Tamaño | Edge completo | Edge −35% |
  |---|---|---|
  | All-in fijo | 81 / 87% | 70 / 83% |
  | All-in walk-forward | 97 / 88% | 94 / 74% |
  | 2 contratos fijos | 92 / 93% | 83 / 89% |

- **MFFU 50K, all-in fijo:** 29 / 47% (2 contratos fijos: 52 / 58%).
- **Evaluación única:** se quema el 55-80% de las veces. Entre el 25% y el 74% de las quemas llegan dentro de los primeros 5 días.

## Veredicto

Rechazado.

- El walk-forward le gana al tamaño fijo uniforme solo en T1. En T2 y con 35% menos edge pierde en todas las firmas.
- El all-in fijo pierde siempre.
- Gasta más evaluaciones (2,1 a 3,0 contra 1,7 a 2,4).

Con trades de 80% WR y pérdida media 3 veces la ganancia media, poner todo en un trade convierte cada pérdida en una cuenta quemada. Ir a fondo en tamaño fijo funciona mejor que ir a fondo solo en esos trades.
