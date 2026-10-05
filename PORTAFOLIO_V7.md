# Portafolio v7: NQ + Oro (versión final, 28-sep-2026)

## Qué se investigó en esta ronda (todo validado: se elige con 2020–23 y se verifica en 2024–26 y en futuros reales)

| Investigación | Variantes | Resultado |
|---|---|---|
| Oro: momentum y reversión por horario, en todas las horas | 7,128 | Sin ventaja (PF mediano 0.74–0.90) |
| Oro: los módulos del NQ (ORB, VWAP, MSEQ, CRT, Londres, ICT) | 90 | Solo **ORB30 a favor de la tendencia** se sostiene |
| NQ: perfil de volumen (rechazo en VAH/VAL, aceptación de valor, LVN) con volumen real | 200+ | Sin ventaja (PF 0.83–1.04) |
| NQ: fade del Initial Balance | 288 | Sin ventaja, salvo lo que ya cubre CRT11 |
| NQ: filtros por módulo, pesos, targets | 30+ | Sobreajuste, rechazado |

## Configuración final (cada fila es una instancia en NinjaTrader, 1 contrato cada una)

| # | Estrategia | Gráfico | Configuración |
|---|---|---|---|
| 1 | NQPullbackDayEngine | MNQ 1 min | ORB60 + VWAP60 + MSEQ activos; ORB30, ORB15 y VWAP30 apagados; Pullback max 0.44; Skip 2-day 0 |
| 2 | NQCrt11 | MNQ 1 min | Por defecto |
| 3 | NQTimeMom "MOM11" | MNQ 1 min | 1100, -2, no, 0.25, 0.3, 0, trend no, **VWAP sí** |
| 4 | NQTimeMom "MOM13" | MNQ 1 min | 1300, -2, no, 0.20, 1.0, 240, trend sí |
| 5 | NQTimeMom "MOM1030" | MNQ 1 min | 1030, -2, no, 0.20, 0.3, 60, trend sí |
| 6 | NQTimeMom "ON07" | MNQ 1 min | 0700, 30, no, 0.20, 1.0, 60, trend sí |
| 7 | NQTimeMom "REV06" | MNQ 1 min | 0600, 30, **sí**, 0.20, 0.3, 240, trend sí |
| 8 | NQLondonFvg | MNQ 1 min | Por defecto |
| 9 | **NQPullbackDayEngine en ORO** | **MGC 1 min** | Solo **ORB30 activo**, target **2.0R**; Use pullback filter **off**; StopCap 0.35; demás módulos y MSEQ apagados |

Contratos **fijos**: 1 por instancia. No usar % de riesgo, porque el Sharpe baja.
(El módulo ICT de apertura no está programado para NinjaTrader; los números de abajo no lo incluyen.)

## Resultados (futuros reales MNQ + MGC, 2024 → sep-2026)

| | Sharpe | Neto/año | Max DD |
|---|---|---|---|
| Portafolio v7 | **3.32** | **$15,441** | $3,041 |
| 2026 (ene → sep) | **4.07** | **+$17,932** | — |

En 2026 el 65% de los días cerraron en verde. En la base larga (CFD 2020–26) el Sharpe es 3.12.

## Evaluaciones (empezando cualquier día de 2024–26; % pasa / % quema)

| Cuenta | Tamaño | En ≤20 días | Sin límite de tiempo | Días medianos |
|---|---|---|---|---|
| **Topstep 50K** ($3k / $2k, consistencia 50%) | 1 | 12 / 5 | **86 / 9** | 42 |
| Topstep 50K | 2 | 40 / 26 | 65 / 33 | 17 |
| **Apex-type 50K** ($3k / $2.5k) | 1 | 12 / 2 | **90 / 5** | 44 |
| Apex-type 50K | 2 | 45 / 12 | 76 / 22 | 18 |
| **25K** ($1.5k / $1.5k) | 1 | 45 / 8 | **82 / 16** | **18** |
| 25K | 2 | 62 / 29 | 67 / 32 | 7 |
| Topstep 100K ($6k / $3k) | 2 | 12 / 9 | 72 / 22 | 38 |

**Conclusiones:**
- **Topstep no tiene límite de tiempo.** Con 1 contrato por módulo pasa **86%** (Apex-type **90%**) y quema menos del 10%, en unos 2 meses.
- **La 25K con 1 contrato** es el mejor equilibrio: **82% de aprobación, mediana de 18 días**.
- Duplicar el tamaño acelera (7–18 días), pero baja la aprobación a 65–76%.
