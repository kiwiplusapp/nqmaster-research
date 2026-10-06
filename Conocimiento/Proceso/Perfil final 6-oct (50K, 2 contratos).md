# Perfil final 6-oct: Lucid 50K con 2 contratos
Volver a [[00 - MAPA]] · Guía: sección "★ PERFIL FINAL" en `NQMASTER_GUIA.md` · Relacionado: [[Prop con 1 contrato]], [[GoldMaster (oro)]]

## Configuración
| Fase | NQMaster (MNQ) | GoldMaster (MGC) |
|---|---|---|
| Evaluación | Ultra ampliado · Contracts 2 · PropMode Eval · EvalTarget 3000 · ConsistencyPct 50 · EvalProfitStop 1400 | Robust · Contracts 2 · EvalTarget 3000 · AccountProfitStop 1400 |
| Fondeada | Contracts 2 · PropMode Funded · colchón 750 / 1500 · cobro a $4.000 | **Robust** · Contracts 2 · EvalTarget 0 |

- **$ por mes por cuenta:** $1.314 de promedio en 9 pruebas (3 períodos × historia, +1 tick y Monte Carlo); la peor da $1.163.
- **Probabilidad de un año en pérdida:** ≤ 1,4%.
- **Evaluación:** pasa el 48%, con una mediana de 9 días. El 93% de las que pasan lo hacen en ≤ 22 días.

## La velocidad de la evaluación tiene un techo
Con un límite que sigue al pico, la probabilidad de pasar depende de la ganancia diaria dividida por su varianza:

P(pasar) ≈ exp(−T·θ / (e^(θ·D) − 1)), con θ = 2μ/σ²

- Más contratos dan más velocidad pero menos aprobación.
- Para aprobar el 80% en ~18 días haría falta un Sharpe anual de ~5. El sistema tiene 3,3-3,9.
- Se probaron 480 reglas de tamaño dinámico. La mejor sube la probabilidad de pasar en ≤ 22 días en solo 1,9 puntos.
- **Modo pasar fácil** (1 contrato, 2 desde la 9ª sesión si la ganancia es < $2.100 y el colchón ≥ $1.000): aprueba el 62% con una mediana de 15 días, a cambio de un 10% menos de $.

## Errores encontrados esa noche
- **El constructor de datos de cuenta se re-ejecutaba al importarlo** y borraba los módulos agregados después: ICT corregido, WR70Plus, Core, ENG10 y LATEFH. Corregido; todo se reconstruyó y verificó.
- **Revisión de código de NQMaster y GoldMaster.**
  - Señales perdidas por choques con órdenes opuestas.
  - Órdenes stop rechazadas en vivo, que apagaban la estrategia.
  - Objetivo de la evaluación sin contar la ganancia abierta.
  - Referencia de LATE distinta a la investigación.
  - Estado de la cuenta perdido al reiniciar.
  - Llenados parciales.
  - En GoldMaster: bloqueos más estrictos que la investigación (−4-5% de ganancia), la regla de la primera ruptura de ASIA y el calentamiento del ATR.

## Descartado
- Pesos por módulo con máximo Sharpe: no se sostienen fuera de muestra.
- Petróleo: confirmado de nuevo, solo 1 de 38.000 configuraciones sobrevive en 2011-19.
