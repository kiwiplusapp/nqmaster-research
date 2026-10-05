# Plan 4 × 25K: NQ Trend Day (ORB + VWAP), guía de prueba

## 1. Compilar
NinjaTrader → New → NinjaScript Editor → **F5**. Estrategia: `NYOpeningRangeTrend` (se muestra como "NQ Trend Day v2").

## 2. Crear 4 cuentas de simulación
Control Center → pestaña **Accounts** → clic derecho → **Add Simulation Account**. Por ejemplo `Sim-A`, `Sim-B`, `Sim-C`, `Sim-D`, con $25,000 cada una. Si tu versión no tiene esa opción, usa solo `Sim101` para la prueba.

## 3. Una instancia por cuenta
Control Center → **Strategies** → clic derecho → **New Strategy** → `NYOpeningRangeTrend`.

| Campo | Valor |
|---|---|
| Instrument | **MNQ** (contrato front, ej. MNQ 12-26) |
| Data series | **Minute 1** |
| Trading hours | **CME US Index Futures ETH** |
| Days to load | **60** (necesita 20+ días para la tendencia y el ATR) |
| Account | Sim-A (luego Sim-B, Sim-C, Sim-D) |
| Order quantity | **Strategy** |

Los valores por defecto ya son los del plan:

| Parámetro | Valor | Qué hace |
|---|---|---|
| ORB target / VWAP target | 2R | Objetivo de cada módulo |
| Risk per trade | $100 | Tamaño base |
| 1-contract max risk | $200 | Permite 1 MNQ aunque el stop sea ancho |
| Max contracts | 3 | Tope por trade |
| Stop day after N losses | 2 | Corta el día tras 2 pérdidas seguidas |
| Daily loss limit | $450 | Sin trades nuevos tras −$450 en el día |
| Max trailing drawdown | **1200** (cámbialo al de tu firma) | Frena la cuenta antes del límite (buffer $150) |
| Flatten time | 15:55 ET | Todo cerrado antes del cierre |

Activa **Enabled** en las 4. Operan solas entre 10:30 y 15:55 ET, con unos 3–4 trades por semana.

## 4. Qué esperar (réplica exacta del código, 2020–2026)

| Métrica por cuenta | 2020–26 | 2026 |
|---|---|---|
| Promedio semanal | ~$75 | ~$124 |
| **Las 4 cuentas juntas** | **~$300/semana** | **~$495/semana** |
| Semanas ≥ $400 (4 cuentas) | 42% | 38% |
| Peor semana (4 cuentas) | −$3,662 | −$2,267 |
| Win rate | 46.7% | 49.6% |
| Riesgo de tocar −$1,200 en 3 meses (por cuenta) | 17% | 0% |

Las 4 cuentas hacen el mismo trade: ganan juntas y pierden juntas.

## 5. Prueba en Sim (2–4 semanas)
- Anota cada viernes el P&L de cada cuenta y el número de trades.
- **Sigue adelante** si después de 4 semanas la suma se parece a la tabla (ganadora o levemente negativa, con 3–4 trades por semana).
- **Detente y revisemos** si una cuenta pierde más de $900 o si el comportamiento no coincide (por ejemplo, 0 trades o trades fuera de horario).
- Envíame el Output window y el Strategy Performance para compararlo trade por trade con el backtest.

## 6. Fase de evaluación (antes de estar fondeado)

| Modo | Risk per trade | 1-contract max risk | Max trailing drawdown | Resultado esperado |
|---|---|---|---|---|
| Conservador | 100–200 | 200–300 | el de la firma | Pasa ~85%, lento (meses) |
| Sprint 20 días | 300 | 400 | el de la firma | Pasa ~45–50%, falla ~50% |

En la eval, usa `Account profit target` = el objetivo de la firma, para que deje de operar al pasar.
