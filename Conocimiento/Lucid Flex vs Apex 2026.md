# Lucid Flex 50K vs Apex 50K (reglas 2026) — 2026-10-03

Código: `research/mine/eod_eval.py`, `eod_pol.py`, `lucid.py` (CSV: eod_eval, eod_pol, lucid_eval, lucid_funded, lucid_life).
Simulación minuto a minuto con los trades de NQMaster (Ultra y WR70Plus), CFD 2020-23 / CFD 2024-26 / MNQ real 2024-26.

## Reglas modeladas
- **Apex 50K desde 1-mar-2026:** objetivo $3,000, **drawdown $2,000** (legacy $2,500), 30 días.
  - Intradía: trailing sobre la equity abierta, sin límite diario.
  - EOD: el umbral se mueve solo con el cierre del día; límite diario de $1,000 (fuentes: pausa del día).
- **Lucid Flex 50K:** objetivo $3,000, pérdida máxima $2,000 EOD (se bloquea en +$100 al llegar a +$2,100), sin límite diario, consistencia 50% en la evaluación, **sin límite de tiempo**, $105.2 pago único, sin activación.
  - Fondeada: sin límite diario ni consistencia; cobro con 5 días ≥ $150; cobra 50% de la ganancia hasta $2,000; 90% para vos; 5 cobros.

## Aprobado (Ultra)
- **Apex 2026 intradía:** la política vieja (2→3, DLL 800) cae a 33-35%. Mejor política: 1 contrato → 2 desde el día 8 si < $2,000, DLL 400 = 38 / 43 / 45-47%.
- **Apex 2026 EOD (pausa):** 2 → 3 desde el día 12 si < $1,500, DLL 600 = 49 / 50 / 51%. Si el límite diario quemara la cuenta: 41-46%.
- **Lucid Flex:**

| Contratos | Aprueba (IS / C24 / real) | Días típicos |
|---|---|---|
| 1 | 84 / 72 / 75% | 21-29 |
| 2 | 53 / 47 / 53% | 10-12 |
| 3 | 42 / 36 / 41% | 7 |

## $/mes por cuenta en 12 meses (recomprando, comisiones incluidas)

| Plan | IS | C24 | Real | Quemadas de fondeada/año |
|---|---|---|---|---|
| Apex 2026 intradía (Ultra) | 974 | 1,027 | 1,103 | 0.7 |
| Apex 2026 EOD (Ultra) | 1,039 | 1,081 | 1,142 | 0.7 |
| Lucid Flex conservadora: eval 3 contratos, fondeada 1, cobro con ≥ $3,000 | 1,043 | 1,308 | 1,456 | 1.2 |
| **Lucid Flex agresiva: eval 3 contratos, fondeada 2 + DLL 600, cobro con ≥ $4,000** | **1,630** | **1,450** | **1,582** | 3.1 |

- El percentil 10 de la agresiva es 1,096 / 1,007 / 1,342 $/mes: incluso un año malo queda por encima del promedio de Apex 2026.
- Aun así, las reglas de Lucid salen de fuentes externas: hay que confirmarlas en su panel.
- No se contó el pase a LucidLive tras el 5.º cobro (supuesto conservador).
