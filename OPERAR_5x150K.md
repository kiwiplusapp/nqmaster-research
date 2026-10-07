# Operar 5 cuentas LucidFlex 150K con NQMaster + GoldMaster

Guía práctica del plan recomendado (detalle y cifras en `NQMASTER_GUIA.md`, sección "★★ PLAN RECOMENDADO"). Lucid permite como máximo 5 cuentas fondeadas por hogar.

## Antes de empezar (una sola vez)
1. Abrí el NinjaScript Editor, presioná **F5** y verificá que compilen NQMaster y GoldMaster.
2. Corré la validación en Strategy Analyzer (sección "Validar NinjaTrader contra la investigación" de la guía).
   - NQMaster Ultra en MNQ y GoldMaster Robust en MGC, del 01/02/2024 a hoy, con Contracts 1.
   - Exportá los trades y corré `python nt_compare.py ... --set ultra` y `--set gold_robust`.
   - Si algún módulo difiere mucho, avisame antes de operar.
3. Corré 2 semanas en una cuenta **Sim** con la configuración de evaluación.

## Cada cuenta: dos gráficos y dos estrategias
- **Gráfico de MNQ de 1 minuto** (Trading hours: CME US Index Futures ETH) con **NQMaster**.
- **Gráfico de MGC de 1 minuto** (horario completo de Globex) con **GoldMaster**.
- En los dos, **Days to load ≥ 120**.
- Elegí la cuenta Lucid en la estrategia. Cada cuenta tiene su propio par de gráficos.

## Fase 1: evaluación
| Parámetro | NQMaster | GoldMaster |
|---|---|---|
| Profile | Ultra | Robust |
| Contracts | **6** | **6** |
| PropMode | Eval | — |
| StartBalance | 150000 | 150000 |
| PropTrailingDD | 4500 | — |
| EvalTarget | 9000 | 9000 |
| ConsistencyPct | 50 | 50 |
| EvalProfitStop / AccountProfitStop | **4200** | **4200** |
| EvalStartDate | **fecha de hoy** | **fecha de hoy** |
| EvalBestDaySoFar | 0 (si la cuenta es nueva) | 0 |

- **Escalonar:** arrancá una evaluación nueva **cada 5 días hábiles**, no las 5 el mismo día. Así no se queman todas en la misma mala racha.
- **Archivo de estado:** si reusás un nombre de cuenta, borrá `Documents\NinjaTrader 8\nqmaster_prop_<cuenta>.txt` o poné `EvalStartDate` en la fecha de hoy.
- **Qué esperar:** pasa ~40% de las veces, en ~9 días hábiles. Cuando se quema, comprá otra (~$285) y empezá de nuevo.
- **Al llegar al objetivo**, la estrategia cierra todo y deja de operar sola.

## Fase 2: fondeada (cuando Lucid aprueba la cuenta)
| Parámetro | NQMaster | GoldMaster |
|---|---|---|
| Contracts | **3** | **3** |
| PropMode | Funded | — |
| StartBalance | 150000 | 150000 |
| PropTrailingDD | 4500 | — |
| FundedCushionSafe | 1700 | — |
| FundedCushionFull | 3400 | — |
| FundedPayoutAt | 6000 | — |
| EvalTarget / AccountProfitStop | — | 0 / 0 |

- **Cobro:** cuando el panel de NQMaster muestra **PAYOUT**, pedí el cobro en Lucid. Para eso la ganancia tiene que ser ≥ $6.000 y tiene que haber 5 días de ≥ $250 desde el último cobro. Cada cobro es el 50% de la ganancia, hasta $3.000, al 90%.
- **Después de 5 cobros**, la cuenta pasa a la revisión para cuenta real de Lucid. Ese lugar se libera para una evaluación nueva.
- **Si se quema**, comprá una evaluación nueva para ese lugar. **Una por lugar libre**: tener evaluaciones de repuesto en paralelo rinde menos.

## Control diario (2 minutos)
- **Panel de NQMaster:**
  - modo (FULL / NO-BOOST / SAFE),
  - colchón sobre el límite,
  - aviso de cobro,
  - monitor de ventaja (% de la alarma).
- **Salida de NinjaScript:** buscar "REJECTED", "ALARM" o "WARNING".
- **Pausa manual:** crear `pause_trading.txt` (NQMaster) o `pause_gold.txt` (GoldMaster) en `Documents\NinjaTrader 8` detiene las entradas nuevas.
- **Días de FOMC:** no opera solo; las fechas ya están cargadas hasta 2028.

## Qué esperar (5 cuentas, simulación de 1.500 años por período)
- **Por mes:** ~$9.800-12.500 de promedio. En un año malo (10% peor), ~$5.300-7.100 por mes.
- **P(año en pérdida):** ≤ 0,7%.
- **Capital para evaluaciones** antes de los primeros cobros: hasta ~$8.300-12.300 (90% de los casos).
- **Por cuenta y por año:** ~13 evaluaciones compradas y ~3 fondeadas quemadas. Ya está descontado.

Si tenés menos capital, la misma lógica funciona con 50K: 2 contratos en evaluación y en fondeada. Rinde unos $1.390 por mes por cuenta.
