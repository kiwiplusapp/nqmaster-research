# Portafolio v8 (final): NQ + Oro + reglas de cuenta

## Mejoras de esta ronda (todas medidas con secuencia intradía real)

| Mejora | Resultado | Estado |
|---|---|---|
| **No operar en días de FOMC** (calendario oficial Fed 2020–2026) | Sharpe 3.00 / 2.98 / 3.21 → **3.03 / 3.04 / 3.30** (2020–23 / 2024–26 CFD / real). 25K: aprobación 78 → **83%**, quema 20 → **16%** | ✅ En **NQAccountGuard** |
| Días de CPI y NFP | El portafolio rinde bien (PF 1.2–1.55) | Se opera normal |
| Límite de pérdida diaria / tope de ganancia diaria | No mejoran (las pérdidas vienen repartidas en el día) | ❌ |
| **Módulo ICT de apertura programado** | Era el único validado que faltaba en NinjaTrader | ✅ **NQIctOpen** (gráfico de **5 min**) |
| Guardián de cuenta | Pausa todo en FOMC, al llegar al objetivo y cerca del drawdown máximo | ✅ **NQAccountGuard** |

## Instancias en NinjaTrader (1 contrato fijo cada una)

| # | Estrategia | Gráfico | Configuración |
|---|---|---|---|
| 1 | NQPullbackDayEngine | MNQ 1 min | ORB60 + VWAP60 + MSEQ; ORB30, ORB15 y VWAP30 apagados; Pullback max 0.44; Skip 2-day 0 |
| 2 | NQCrt11 | MNQ 1 min | Por defecto |
| 3–7 | NQTimeMom ×5 | MNQ 1 min | MOM11 (VWAP sí), MOM13, MOM1030, ON07, REV06 (ver PORTAFOLIO_DIARIO.md v4) |
| 8 | NQLondonFvg | MNQ 1 min | Por defecto |
| 9 | **NQIctOpen** | **MNQ 5 min** | Por defecto |
| 10 | NQPullbackDayEngine en oro | MGC 1 min | Solo ORB30, target 2R, pullback filter off |
| 11 | **NQAccountGuard** | MNQ 1 min | Topstep 50K: Start 50000, **Eval target 3000** (en la eval), **Max drawdown 2000**, Buffer 250 |

## Trades por día

| Período | Trades/día | Win rate | PF | Neto (1 contrato por módulo) |
|---|---|---|---|---|
| 2024–26 (real) | **4.3** | 64.3% | 1.34 | +$40,446 |
| 2026 (ene → sep) | **3.8** | 65.5% | **1.42** | **+$16,582** |
| **Último mes (28-ago → 25-sep)** | **3.9 (82 trades en 21 sesiones)** | 67.1% | 1.41 | +$1,603 (DD $244) |

Por módulo, en trades por día: MOM11 0.78, oro ORB30 0.59, MOM1030 / MOM13 / ON07 / REV06 0.42 cada uno, LON 0.29, ORB60 0.29, MSEQ 0.26, CRT11 0.18, VWAP60 0.15, ICT 0.10.

## Negocio con Topstep 50K (una cuenta, 1 contrato por módulo)
Ciclo completo simulado con datos reales 2024–26: eval, fondeo, retiros (con $2,000 de colchón), quemas y cuentas nuevas. Supuesto de costos: $49/mes de eval y $149 de activación.
- **Neto para vos: ~$1,060 por mes y por cuenta** (entre $1,000 y $1,150 según la fecha de inicio).
- En ~19 meses: 1.2 evals aprobadas, 0.1 evals quemadas, 0.2 cuentas fondeadas quemadas y 23 retiros.
- Con varias cuentas copiando la misma señal, el ingreso escala (Topstep permite varias cuentas fondeadas), pero **todas ganan y pierden los mismos días**.

## Ajuste final: aporte de cada módulo (sacando uno por vez)
Cambio en el Sharpe al quitar cada módulo, en 2020–23 / 2024–26 CFD / MNQ real (negativo = el módulo suma):

| Módulo | Cambio en Sharpe |
|---|---|
| MOM11 | −0.07 / −0.25 / −0.40 |
| CRT11 | −0.14 / −0.19 / −0.17 |
| ORB60 | −0.21 / −0.14 / −0.16 |
| Oro | −0.07 / −0.16 / −0.17 |
| Londres | 0.00 / −0.18 / −0.20 |
| ICT | −0.09 / −0.13 / −0.13 |
| ON07 | −0.06 / −0.13 / −0.13 |
| MSEQ | −0.27 / −0.08 / −0.01 |
| MOM1030 | −0.03 / −0.07 / −0.11 |
| REV06 | −0.03 / −0.05 / −0.06 |
| MOM13 | 0.00 / +0.08 / +0.05 (neutral) |
| **VWAP60** | **+0.03 / +0.12 / +0.12 → resta en los 3 períodos: se APAGA** |

**Cambio:** en NQPullbackDayEngine (MNQ) poner **VWAP60 on = false**. Sharpe real 3.35 → **3.47**.
