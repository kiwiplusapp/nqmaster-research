# Evaluaciones de prop firm (simulación con datos reales 2024–26)
Volver a [[00 - MAPA]] · Reglas: [[Objetivo y reglas]]

| Cuenta | Tamaño | Aprobación en ≤20 días | Aprobación sin límite | Quema | Días medianos |
|---|---|---|---|---|---|
| Topstep 50K | 1 contrato por módulo | ~12% | **85–86%** | 9% | ~42–47 |
| Apex-type 50K ($2.5k de drawdown) | 1 | ~12% | **90%** | 5% | ~44 |
| 25K ($1.5k / $1.5k) | 1 | ~45% | **82–83%** | 16% | ~18–21 |
| 25K | 2 | 62% | 67% | 32% | 7 |

- **Techo teórico**: la aprobación en 20 días depende del Sharpe (Sharpe 3 → ~66%, 5 → ~80%). Ver [[Lecciones clave]].
- **Ciclo completo en Topstep 50K** (eval, fondeo, retiros y quemas): ~**$1,060 netos por mes por cuenta** (supuesto: $49/mes de eval y $149 de activación).
- **Arriesgar 0.5% por trade** en vez de contratos fijos empeora el resultado (Sharpe 2.61 contra 3.01).

## Apex 25K Full (2026-09-28): MaxPlus con ICT x2 (research/apex25.py)
Reglas: objetivo $1,500 y trailing intradía de $1,500. En la cuenta fondeada (PA):
- Safety net de $26,100; hay que tener $26,600 para pedir un pago.
- Cada pago es de $500 a $1,000, con 5 días de +$100 y consistencia del 50%.
- Máximo 6 pagos.
- Costo: $17.70/mes la evaluación y $90 el PA.

Evaluación, 2 contratos que bajan a 1 con drawdown > $400, en MNQ real:
- A 30 días: 57% de pases y 26% de quemadas.
- Sin límite de tiempo: 70% de pases y 30% de quemadas.
- Mediana: 9 días para pasar.
- Con 1 contrato fijo: 46% / 19% a 30 días.

Ciclo de 12 meses por cuenta (evaluación adaptativa y cuenta fondeada con 1 contrato, repitiendo la evaluación al quemar):
- MNQ real: ~$680/mes netos, ~9 pagos por año, ~3.7 evaluaciones compradas.
- CFD 2024-26: ~$535/mes.

Varias cuentas (MNQ real):
- 3 cuentas: ~$2,050/mes (peor año $1,300/mes).
- 5 cuentas: ~$3,400-3,500/mes.
- Escalonar las entradas cada 10 días sube el 10% peor ($1,341 → $1,573 con 3 cuentas).

## Apex 25K: pasar más rápido (2026-09-29, research/minute_path.py, evalfast.py, life25.py)
El simulador nuevo trabaja minuto a minuto con la ganancia NO realizada, igual que Apex (el drawdown sigue al pico incluyendo trades abiertos). Datos: MaxPlus con ICT x2. En 2026 la evaluación no tiene mínimo de días ni consistencia, y el acceso dura 30 días.

Evaluación, % de pases / quemas en 21 días de mercado, y días hasta tener la cuenta fondeada (repitiendo evaluaciones):

| Tamaño | 2020-23 | 2024-26 CFD | MNQ real | Días a fondeada (real) | Evaluaciones por fondeada |
|---|---|---|---|---|---|
| 1 fijo | 38/13 | 34/24 | 46/25 | 31 | 2.2 |
| 2→1 (DD>$400) | 52/25 | 44/37 | 53/31 | 17 | 1.9 |
| 2 fijo | 53/43 | 45/54 | 56/42 | 11 | 1.8 |
| **4 fijo** | 39/61 | 34/66 | 35/65 | **7** | 2.8 |
| 8 fijo | 29/71 | 27/73 | 29/71 | 5 | 3.4 |
| MOM11 solo x8 (winrate alto / RR bajo) | 36/60 | 40/60 | 43/57 | 12 | 2.4 |

Ciclo de 12 meses por cuenta, neto $/mes (2020-23 / 2024-26 CFD / real), cuenta fondeada con 1 contrato:
- Evaluación con 1 fijo: 376 / 475 / 545.
- Evaluación 2→1: 476 / 530 / 638.
- **Evaluación con 4 fijo: 575 / 616 / 739 (la mejor).**
- Evaluación con 4 fijo y fondeada con 2 contratos: 688 / 602 / 803, pero con más quemas de la fondeada.

Otros resultados:
- Guardar colchón antes de retirar (B = $500-1500) baja las quemas de la fondeada, pero deja 12-25% menos dinero: conviene retirar apenas se pueda.
- Con 4 contratos, la exposición máxima simultánea es de 20 MNQ (el límite de la cuenta es 40).
- Winrate alto con RR bajo no sube la probabilidad de pasar. Sin ventaja por trade, la probabilidad de pasar es ≈ DD / (DD + objetivo) = 50%. Arriesgar más solo cambia la velocidad.

## Ideas probadas y descartadas (2026-09-29)
- **Entradas con orden límite** en los módulos por horario (research/limitentry.py): peores por selección adversa. Por ejemplo, MOM11 real pasa de PF 1.36 a 1.04-1.19.
- **Señales opuestas bloqueadas por conflicto:** solo ~1% de los trades y pierden (PF 0.55-0.89). El filtro de conflictos está bien.
