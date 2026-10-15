# Auditoría NQMaster: 16-oct-2026

Mandato: valor esperado fuera de muestra, ruina por cuenta, paridad investigación ↔ NinjaTrader y la verdad sobre las expectativas. Todas las cifras salen de scripts en `research/mine/` (nombre entre paréntesis). Total de configuraciones evaluadas en esta ronda: **~115**. Aceptadas: **2** (una calibración y una política de cuenta).

## Lo esencial

**Qué cambió en el código** (NQMaster.cs; verificación de sintaxis C# 5 OK; **falta F5** en la PC):

| Cambio | Evidencia | Estado |
|---|---|---|
| Monitor de borde recalibrado: Ultra k 0,085 / h 24,44 (antes 0,0758 / 18,57); UltraQ y WR70Plus también | Con los ×4 nuevos, los parámetros viejos daban una **falsa alarma el 2024-03-18** (`monitor_recal2.py`) | ACEPTADO (corrección) |
| Nuevo nivel AVISO del monitor (solo alerta; ~23% de falsos avisos por año) | Mismo script | ACEPTADO (sin efecto en trades) |
| Estado del monitor guardado en disco (`nqmaster_edge_<cuenta>.txt`) | Sin esto, un reinicio lo reseteaba y nunca alarmaba (revisión F3) | ACEPTADO (bug) |
| Risk cap: MOM1030/CPI09 se miden por riesgo de 1 lote, como en la investigación | Antes, el ×4 los dejaba sin operar siempre que el cap estaba activo (F1) | ACEPTADO (bug) |
| El ×8 de evaluación es el total de lotes (8 con 1 contrato, 2×4 con 2) | Con 2 contratos daba 16 lotes, y la investigación muestra que es peor (F5) | ACEPTADO (bug) |
| El objetivo de evaluación ya no corta las cuentas fondeadas (F2) | Revisión de código | ACEPTADO (bug) |
| Días bloqueados (roll, pausa) no cuentan en el monitor (F9) | Revisión de código | ACEPTADO (bug) |
| Preset Mffu50K fondeada: 2 contratos desde un cushion de $4.000, retiro por encima de $6.100 | `c4_cushion.py`: ver tabla de ingreso | ACEPTADO (ver advertencias) |
| Alarma de inactividad (por módulo y por dirección: 12 días sin shorts/longs) | Máximo histórico 8 días; el bug de los shorts duró 13 meses | ACEPTADO (solo alerta) |
| Guarda entre cuentas: no abrir NQ en sentido opuesto a otra cuenta de la misma PC | Lucid y MFFU prohíben el hedging entre cuentas propias | ACEPTADO (cumplimiento) |
| Log de tamaño en cada entrada (base → pedido → enviado) | Observabilidad | ACEPTADO |

**Qué NO cambió (descartado):** risk parity / HRP, apagar ICT, REV06 u ON07, apagar módulos redundantes, pausar ante alarmas, sizing "sniper". Detalle en `Descartado/Auditoria 16-oct (risk parity, apagar modulos, sniper).md`.

**Herramientas nuevas:**

- `parity_check.py`: compuerta de paridad NT ↔ investigación con 4 umbrales.
- `impl_gap.py`: brecha de implementación por módulo y por cuenta.
- `tools/check_guards.py`: importar un script ya no reconstruye datos en silencio.
- `tools/nt8_stub/check.sh`: verificación de sintaxis C# 5.
- `RUNBOOK_OPERACION.md`.

## Ingreso realista por cuenta MFFU Rapid 50K (1 contrato, `final_dist16.py`)

Ciclo de vida de 12 meses: evaluación con reinicio → fondeada → retiros. Hay 278 asientos-año (arranques cada 5 días, 2020-2025; se solapan, así que son bastante menos independientes).

| Edge | Política | $/mes mediana | p10 | p90 | P(año negativo) | P(promedio ≥ $1.200/mes) | Cuentas perdidas/año (evals fallidas + fondeadas) | Fondeadas perdidas/año |
|---|---|---|---|---|---|---|---|---|
| completo | hoy | 1.324 | 35 | 2.366 | 9,0% | 53% | 1,17 | 0,35 |
| completo | **nuevo preset** | **2.157** | −39 | 4.051 | 12,6% | 60% | 1,18 | 0,36 |
| −35% | hoy | 682 | −118 | 1.766 | 27,7% | 26% | 3,14 | 0,90 |
| −35% | **nuevo preset** | **1.281** | −118 | 3.098 | 30,2% | 53% | 3,05 | 0,88 |
| cero | hoy | −124 | −222 | 812 | 65,8% | 0% | 10,4 | 1,30 |
| cero | nuevo preset | −131 | −222 | 1.822 | 66,5% | 14% | 10,4 | 1,30 |

- El preset nuevo sube la mediana ~60-90%.
- No cambia las cuentas perdidas.
- Sube la probabilidad de año negativo unos 3 puntos, porque hay más varianza.
- Con edge cero, todo es casi cero: la suerte y las comisiones de la firma no pagan.

## Los 5 mayores riesgos vigentes y su defensa

Medidos en `premortem16.py` y `audit16_stats.py`.

1. **Régimen de alta volatilidad / rango (verano 2026).**
   - Una cuenta fondeada nueva arrancada entre junio y agosto de 2026 se perdía dentro de 90 días el **73%** de las veces (88% con 35% menos edge). En arranques normales: 14% (2024-26) y 28% (2020-23).
   - Los días de rango dan PF 0,76; los de tendencia, PF 4,67.
   - Defensa: el risk cap por debajo de un cushion de $2.000 y varias cuentas escalonadas. Un cap hasta $3.000 baja el verano a 41% pero cuesta ingreso en años normales; se probó y no pasó la regla.
   - **No hay defensa completa: es el costo del tamaño frente a un drawdown de $2.000.**
2. **Fin del régimen post-2020.**
   - Con costos normalizados, 2010-19 da Sharpe 0,85 contra 3,67 en 2020-26.
   - El shrinkage por módulo en 2010-19 deja positivos solo VOLB y NF05.
   - Defensa: el monitor recalibrado (detecta un edge muerto en una mediana de ~241 días), el fallback de un año y la regla de pausa a 60 días.
3. **Bug de ejecución silencioso** (precedente: shorts bloqueados 13 meses).
   - Defensa nueva: alarma de inactividad por dirección (12 días), watchdog de órdenes zombi, `parity_check.py` antes de cada cambio y `impl_gap.py` en vivo.
4. **Violación de reglas de la firma.**
   - Hedging entre cuentas: guarda nueva, solo dentro de la misma PC.
   - Noticias en MFFU fondeada: el preset pone el apagón, que también cancela órdenes pendientes.
   - Límite de micros (MNQ y MGC juntos en MFFU): `MaxOpenContracts`.
   - Apex y Topstep: no usar.
5. **Deslizamiento real mayor al supuesto.**
   - Con +4 ticks por lado el Sharpe 2020-23 / 2024-26 baja de 3,43 / 4,00 a 2,79 / 3,48. El sistema aguanta hasta ~15-23 ticks antes de dar cero.
   - El deslizamiento real **no está medido**: se mide con `impl_gap.py` sobre la cuenta real.

Otros 5 del pre-mortem (menor probabilidad):

- Desconexión con posición abierta: `AccountSyncGuard`.
- Roll mal hecho: `RollGuard`.
- Reinicio a mitad de sesión: inicio del día guardado y estado del monitor persistido.
- Calendario de noticias vencido: alerta `NEWS LIST`; cubierto hasta dic-2027.
- Error de configuración: los presets imprimen todos los valores.

## Auditoría estadística (`audit16_stats.py`)

- **Deflated Sharpe 2020-26:**
  - Sharpe 3,67. DSR 0,95 con 100.000 pruebas, 0,88 con 300.000 y 0,75 con 1.000.000.
  - Varianza de Sharpe entre pruebas estimada sobre 36.756 configuraciones minadas.
  - **Sobrevive a la corrección por pruebas múltiples, pero es en muestra para el régimen:** el sistema se armó mirando 2020-26.
  - En 2010-19 (costos normalizados): Sharpe 0,85 y DSR ≈ 0.
- **PBO de elegir entre 33 variantes** del sistema (perfiles, multiplicadores, quitar un módulo): **0,51** en 2020-26. Elegir "la mejor variante" no aporta nada. Las diferencias entre variantes son ruido; por eso no se cambian los defaults por diferencias chicas.
- **Hansen SPA contra cero:** p < 0,001 en 2010-19 y en 2020-26. Hay edge positivo; lo incierto es su tamaño.
- **Meses (2020-26):**
  - 15 de 82 meses negativos. Peor mes −$2.210. Racha máxima de 3 meses negativos. El P&L de 12 meses móviles nunca fue negativo.
  - Bootstrap con edge completo: ~1,9 meses negativos por año y 4% de probabilidad de 3 seguidos.
  - Con 35% menos edge: 3,2 meses negativos por año y 17% de probabilidad de 3 seguidos.

## Paridad y reproducibilidad (fase A)

- **Datos:** 45 archivos con SHA-256 OK.
- **Trades:** la reconstrucción desde cero da trades **idénticos** a `cand16_trades.pkl` (6 perfiles × 2 eras). Cifras reproducidas: UltraR 2020-23 WR 66,93%, PF 1,47, Sharpe 3,38; 2024-26 WR 65,66%, PF 1,50, Sharpe 3,65.
- **NinjaTrader 2024-01 → 2026-10:**

  | Compuerta | Resultado |
  |---|---|
  | Trades emparejados | 94,6% |
  | P&L de los emparejados | +0,8% |
  | Correlación diaria | 0,968 |
  | Módulo ICT (5 min, límite) | 82% — **falla la compuerta del 90%** |
  | Módulo MSEQS | 56% — **falla la compuerta del 90%** |

  - ICT: NinjaTrader llena el retest más tarde.
  - MSEQS: en NinjaTrader exige que ORB60 se haya llenado; la investigación usa la señal de ORB60 antes de los filtros. Unos $24/mes a favor de la investigación.
  - Ambas quedan como divergencias abiertas y documentadas.
- **La validación en NT no cubre** CPI09, los ×4/×8, los arreglos F1-F9 ni el preset nuevo: **hace falta un backtest nuevo.**
- **Las guardas de importación encontraron un bug de investigación viejo.** Las configuraciones sin boost (NOB) de los estudios del 5-6 de octubre no tenían MSEQS en REAL: unos $57/mes, 2,7%. No cambia ninguna decisión vigente.

## Líneas abiertas que no se pudieron cerrar

- **C1, edge independiente (ZN/ZB, M2K, MYM):** bloqueado por falta de datos. No hay fuente gratuita y los créditos de Databento están gastados. Para probarlo hay que exportarlos desde NinjaTrader con `BarExporterUTC.cs` (2024-26, 1 minuto). Es la **única palanca** que puede subir el techo de pase.
- **C2, deslizamiento real y "no perseguir":** sin datos de tick ni de cuenta en vivo.
- **Refactor de NQMaster en clases (fase D4):** no se hizo, porque sin NinjaTrader no se puede probar que la paridad de trades quede idéntica. Recomiendo hacerlo con F5 y `parity_check.py` en la PC.

## Respuestas honestas

1. **¿Cuánto es real y cuánto selección?**
   - La elección entre variantes es ruido (PBO 0,51), pero el edge base no: SPA p < 0,001 y DSR 0,75-0,95 incluso con 300.000-1.000.000 pruebas.
   - El problema es el régimen. En 2010-19 el mismo sistema rinde un cuarto del Sharpe.
   - Mi rango: **entre 50% y 80% del rendimiento del backtest 2020-26 es real mientras dure el régimen**. El haircut de 35% está en el medio de ese rango.
   - No sé cuánto dura el régimen. Nada en los datos lo predice: autocorrelación de meses ~0 y filtros de régimen fallidos.
2. **¿Más de $1.200 por cuenta y por mes durante 12 meses?**
   - Con el preset nuevo, P(promedio de 12 meses ≥ $1.200) = 60% con edge completo y 53% con 35% menos. Ponderando por la incertidumbre del edge, **~45%**.
   - **Todos** los meses por encima de $1.200: < 5%, porque ~1 de cada 5 meses pierde.
   - Perder cuentas es seguro, no probable: ~1,2 cuentas por año por asiento con edge completo (casi todas evaluaciones fallidas de $157) y ~3 con 35% menos. Las fondeadas perdidas son 0,4-0,9 por año.
3. **Mejor jugada:** dejar de optimizar el borde, que está en su techo. En orden:
   1. Compilar y validar en NinjaTrader (F5 y backtest con `parity_check.py`).
   2. Operar **una** cuenta MFFU durante 60-90 días con `impl_gap.py`.
   3. En paralelo, exportar ZN, M2K y MYM para probar un flujo independiente; es lo único que sube el techo.
   4. Recién con evidencia en vivo, escalar a 3 cuentas MFFU + Lucid con el mismo perfil.
4. **Qué me haría cambiar de opinión:**
   - 60-90 días en vivo con P&L por contrato < 65% de lo esperado: cambio a pausa.
   - Deslizamiento real > 4 ticks por lado.
   - Un flujo nuevo con correlación < 0,15 que pase los 4 períodos.
   - Dos meses tipo agosto seguidos: el régimen se está terminando.
   - La paridad del backtest nuevo con fallas fuera de ICT y MSEQS.

## Revisión adversarial

(ver `research/mine/redteam_2026-10-16.md`)
