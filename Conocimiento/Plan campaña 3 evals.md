# ⚠️ ACTUALIZACIÓN 2026-10-03 (tarde): reglas 2026 y Lucid Flex

**Las Apex 50K nuevas (desde 1-mar-2026) tienen drawdown de $2,000, no $2,500.** Los números de abajo eran con $2,500 (cuentas legacy).
Revisá en el panel de Apex qué drawdown tiene tu cuenta antes de usar esta configuración.

| Cuenta 50K (Ultra, 1 slot) | Aprueba (IS / C24 / MNQ real) | $/mes por cuenta (IS / C24 / real) |
|---|---|---|
| Apex legacy, DD $2,500 intradía | 48 / 49 / 50% | ~1,180-1,270 |
| Apex 2026 intradía, DD $2,000 | 38 / 43 / 45% (mejor política) | 974 / 1,027 / 1,103 |
| Apex 2026 EOD, DD $2,000, DLL $1,000 (pausa) | 49 / 50 / 51% | 1,039 / 1,081 / 1,142 |
| **Lucid Flex 50K (EOD $2,000, sin límite de tiempo)** | 42 / 36 / 41% con 3 contratos (≈7 días); 84 / 72 / 75% con 1 contrato (≈21-29 días) | **1,630 / 1,450 / 1,582** (agresiva) o 1,043 / 1,308 / 1,456 (conservadora) |

### Configuración NQMaster según la cuenta
- **Apex 2026 EOD:** Ultra, Contracts 2, EvalMode true, EvalLateDay 12, EvalLateGoal 1500, EvalLateContracts 3, DailyLossLimit 600.
- **Apex 2026 intradía:** Ultra, Contracts 1, EvalMode true, EvalLateDay 8, EvalLateGoal 2000, EvalLateContracts 2, DailyLossLimit 400.
- **Lucid Flex evaluación:** Ultra, Contracts 3, EvalMode false, DailyLossLimit 0.
- **Lucid Flex fondeada:** Ultra, Contracts 2, DailyLossLimit 600; pedir cobro **solo cuando la ganancia sea ≥ $4,000** (y 5 días ≥ $150) → cobra $2,000 (90% = $1,800). Variante conservadora: Contracts 1, pedir con ≥ $3,000.
- Lucid: reglas tomadas de fuentes externas (pago = 50% de la ganancia hasta $2,000, 5 pagos, bloqueo del drawdown en +$100, sin tarifa de activación). Confirmalas en el panel de Lucid.

---

# Plan de campaña: 3 evaluaciones Apex 50K (2026-10-03)

## Calendario
- Comprá las 3 evaluaciones con **~2 semanas (10 días hábiles) de diferencia**, no 4 días.
- **Por qué:** las tres operan los mismos trades. La probabilidad de que se quemen las 3 en el primer intento (Ultra, MNQ real) cambia mucho con la separación:
  - 0 días de diferencia: 50%.
  - 3 días hábiles (≈4 corridos): 28%.
  - 7 días hábiles: 17%.
  - **10 días hábiles: 12%.**
- Si se quema una, recomprala al día siguiente.

## Qué esperar (Ultra en evaluación, modo evaluación; MNQ real / CFD 2024-26 / CFD 2020-23)
- **Cada evaluación pasa** ~50 / 51 / 50% de las veces en ≤30 días.
- **Al mes** (21 días hábiles), recomprando: **~2.0 / 1.95 / 1.75 cuentas fondeadas**, ~$460-540 gastados en evaluaciones.
- **A los 2 meses:** **~2.7 / 2.8 / 2.6 fondeadas**, 91-98% de tener al menos una, 81-90% de tener las tres, ~$560-645 gastados.
- **A los 3 meses:** ~2.8-3.0 fondeadas.

## Configuración de cada instancia de NQMaster (una por cuenta, MNQ de 1 minuto)

### Evaluación
- Profile = **Ultra**, Contracts = **2**, AdaptiveSize = false.
- **EvalMode = true**, EvalStartDate = fecha en que empieza **esa** evaluación (yyyy-MM-dd).
- EvalLateDay = 12, EvalLateGoal = 2000, EvalLateContracts = 3.
- **DailyLossLimit = 800**, EvalTarget = 3000, StartBalance = 50000, MinAtrPoints = 150.

### Cuenta fondeada
- Profile = **WR70Plus**, Contracts = **1**, EvalMode = false, EvalTarget = 0.
- **DailyLossLimit = 400**, MinAtrPoints = 150.
- Retirar apenas se cumplan las condiciones: saldo ≥ $52,600, 5 días de +$250 y ningún día ≥ 50% de la ganancia.
- **Esperado por cuenta fondeada:** 73-93% de cobrar al menos un pago, cobro esperado $8,400-9,950.

## Reglas de operación
- **No operes a mano** en esas cuentas: mezcla posiciones y cambia el riesgo.
- Ideal: un **VPS** con NinjaTrader abierto todo el día. El sistema opera de 04:00 a 17:00 hora de Buenos Aires.
- **No reinicies** la estrategia a mitad de una evaluación sin mantener la misma EvalStartDate.
- Antes de empezar, confirmá en la web de Apex las reglas vigentes: topes de pago, saldo mínimo y trading automatizado.

## Protecciones nuevas en el código
- **MinAtrPoints = 150:** con 11 años de datos (2015-2026), todos los módulos pierden cuando el rango diario del NQ es menor a 150 puntos (PF 0.6-0.96). Hoy está en ~400 y en 2024-26 nunca bajó de 150.
- **Fechas FOMC 2027** incluidas en el código (Fed: 27 ene, 17 mar, 28 abr, 9 jun, 28 jul, 15 sep, 27 oct, 8 dic de 2027; 26 ene de 2028).
- **Salidas por tiempo** usan la cantidad real abierta: funciona con cualquier tamaño (modo evaluación, ×2, ICT).

## Lo que sí está garantizado y el protocolo de control
- **Pérdida máxima por evaluación = su precio ($90-120).** En Apex no debés el drawdown. Definí de antemano un tope de evaluaciones (por ejemplo 6 = ~$630): esa es tu pérdida máxima posible en la campaña.
- **Incertidumbre del modelo:** con ~79 ventanas independientes de 21 días (2020-2026), la probabilidad de pasar cada evaluación está, con 95% de confianza, entre **~38% y ~60%**.
- **Escenario pesimista (38% por evaluación, separadas 2 semanas):**
  - Al menos una aprobada en 3 intentos: 76%; en 5: 91%; en 8: 98%.
  - Valor esperado por evaluación: aún ≈ +$2,500.
- **Reglas para parar y revisar** (objetivas, decididas antes de empezar):
  1. **Antes de comprar:** el backtest de NinjaTrader 2020-2026 con 1 contrato tiene que dar PF ≥ 1.3, con un winrate de ±3 puntos y una cantidad de trades de ±10% respecto de la simulación. Si no, no se compra nada.
  2. **Sim de 2 semanas:** sin órdenes rechazadas ni ignoradas en el Log, y 3-5 trades por día.
  3. **En vivo:** si se queman **4 evaluaciones seguidas**, pausa y revisión. Por azar pasa el 6% de las veces si la estrategia funciona (15% en el escenario pesimista).
  4. **En vivo:** si en los últimos **60 trades** el PF es < 0.9, pausa y revisión.
  5. **Automático:** si el NQ se mueve menos de 150 puntos por día, el sistema deja de operar solo.
