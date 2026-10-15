# Auditoría NQMaster: 16-oct-2026

Mandato: valor esperado fuera de muestra, ruina por cuenta, paridad investigación ↔ NinjaTrader y la verdad sobre las expectativas. Todas las cifras salen de scripts en `research/mine/`. Hubo revisión adversarial independiente (`research/mine/redteam_2026-10-16.md`); sus correcciones ya están aplicadas abajo.

- Esta ronda evaluó **~80 cambios candidatos**.
- **Ninguno mejora el edge.** Lo aceptado son correcciones de bugs, calibración, alertas y cumplimiento.
- **El sistema está en su techo de edge.**

## Lo esencial

**Qué cambió en el código** (`NQMaster.cs`; verificación de sintaxis C# 5 contra stub OK; **falta F5**):

| Cambio | Por qué | Estado |
|---|---|---|
| Risk cap: MOM1030 y CPI09 se miden por riesgo de 1 lote (F1) | Con el ×4, MOM1030 nunca operaba mientras el cap estaba activo | Bug corregido |
| El ×8 de evaluación es el total de lotes: 8 con 1 contrato, 2×4 con 2 (F5) | Con 2 contratos daba 16 lotes, y la investigación muestra que es peor | Bug corregido |
| El objetivo de evaluación no corta cuentas fondeadas (F2) | Una cuenta pasada a Funded podía quedar frenada para siempre | Bug corregido |
| Estado del monitor de borde guardado en disco (F3) | Cada reinicio lo reseteaba, así que en la práctica nunca alarmaba | Bug corregido |
| Días de roll o pausa no cuentan en el monitor (F9) | Sumaban días de P&L cero | Bug corregido |
| Monitor recalibrado: Ultra k 0,085 / h 24,44 (UltraQ, WR70Plus y Durable también) | Con los ×4 nuevos, los parámetros viejos daban una falsa alarma el 2024-03-18 | Corrección, con costo (ver abajo) |
| Nivel AVISO del monitor (solo alerta) | Compensa en parte la detección más lenta | Sin efecto en trades |
| Alarma de inactividad: por módulo, y 12 días sin shorts o sin longs | El máximo histórico es 8 días; el bug de los shorts duró 13 meses | Solo alerta |
| Guarda entre cuentas de la misma PC | Lucid y MFFU prohíben posiciones opuestas entre cuentas propias | Cumplimiento |
| Panel: "retirá hasta dejar $X" | El tamaño del retiro decide cuánto cushion queda | Operación |
| Log de tamaño por entrada | Observabilidad | — |
| Preset Mffu50K fondeada | **Sin escalón por defecto.** Retiro al llegar a $4.600 de ganancia; dejás $4.100 | Igual que antes |

**El costo del monitor recalibrado:** el umbral queda justo encima del peor episodio histórico.

| | Antes | Ahora |
|---|---|---|
| Mediana de días para detectar un edge muerto | 183 | 241 |
| P(detectarlo en un año) | 72% | 56% |

El nivel AVISO salta antes (~68 días en mediana para un edge muerto), pero con ~23% de falsos avisos por año.

**Descartado** (detalle en `Descartado/Auditoria 16-oct (risk parity, apagar modulos, sniper).md`):

- risk parity / HRP;
- apagar ICT u ON07;
- apagar módulos redundantes (ORB90, VW13);
- pausar ante alarmas;
- sizing "sniper".

**En vigilancia:**

- **REV06.** Apagarlo mejora 3 de 4 períodos; el único donde ayuda es 2020-23, el de su selección. En 2024-26 dejó +$30 (PF 1,00) y su probabilidad posterior de edge en 2010-19 es 0. No lo apago porque también alimenta la regla de confluencia (signo nocturno ON07+REV06+LON) y esa interacción no está probada. **Es el primer candidato de la revisión de enero.**
- **Escalón a 2 contratos en MFFU** (`FundedStepUpCushion` 4000 con retiro a $6.600). Queda **opcional**: ver la tabla de ingreso.

## Ingreso realista por cuenta MFFU Rapid 50K

Script: `final_dist16.py`. Un contrato base, ciclo de 12 meses (evaluación con reinicio → fondeada → retiros), 278 asientos-año solapados.

| Edge | Política | $/mes mediana | p10 | p90 | P(año negativo) | P(promedio ≥ $1.200/mes) | Cuentas perdidas/año | Fondeadas perdidas/año |
|---|---|---|---|---|---|---|---|---|
| completo | **default** | **1.324** | 35 | 2.366 | 9,0% | 53% | 1,17 | 0,35 |
| completo | escalón opcional | 2.157 | −39 | 4.051 | 12,6% | 60% | 1,18 | 0,36 |
| −35% | **default** | **682** | −118 | 1.766 | 27,7% | 26% | 3,14 | 0,90 |
| −35% | escalón opcional | 1.071 | −118 | 2.982 | 30,9% | 45% | 3,05 | 0,88 |
| cero | default | −124 | −222 | 812 | 65,8% | 0% | 10,4 | 1,30 |
| cero | escalón opcional | −131 | −222 | 892 | 83,5% | 0% | 10,4 | 1,30 |

- Las "cuentas perdidas" son sobre todo evaluaciones fallidas de $157.
- El escalón gana más con edge completo en el 86-94% de los caminos del bootstrap del revisor. Con 35% menos edge, solo en el 48-62%, y sube P(año negativo) 6-7 puntos.
- El escalón duplica el tamaño, así que el drawdown en dólares empeora: **falla tu criterio del 5%** y por eso no es default.
- Si lo activás, retirá solo hasta dejar $6.100. Sacar todo lo que permite MFFU (por encima de $2.100) es una política no probada.

## Los 5 mayores riesgos vigentes y su defensa

Medidos en `premortem16.py` (política default) y `audit16_stats.py`.

1. **Régimen de alta volatilidad / rango.**
   - Una cuenta fondeada **nueva** se pierde dentro de 90 días:

     | Arranque | Edge completo | 35% menos edge |
     |---|---|---|
     | 2024-26 | 14% | 34% |
     | 2020-23 | 28% | 51% |
     | Verano 2026 | **73%** | 88% |

   - Los días de rango dan PF 0,76; los de tendencia, PF 4,67.
   - Con 1 contrato, P(drawdown ≥ $2.000 en 90 días) = 49% (74% con 35% menos edge).
   - Defensa parcial: risk cap por debajo de un cushion de $2.000 y cuentas escalonadas.
   - **No hay defensa completa: es el tamaño (1 MNQ con ×4 en dos módulos) contra $2.000 de drawdown.**
2. **Fin del régimen post-2020.**
   - En 2010-19 el mismo sistema da Sharpe 0,85 (costos normalizados), contra 3,67 en 2020-26.
   - Defensa: monitor y fallback (detección lenta, ver arriba), y la regla de pausa a 60 días de vivo.
3. **Bug silencioso de ejecución.**
   - Defensa nueva: alarma de inactividad por dirección, watchdog, `parity_check.py` antes de cada cambio e `impl_gap.py` en vivo.
4. **Reglas de la firma.**
   - Hedging entre cuentas: guarda nueva, solo en la misma PC. Usá el mismo perfil en todas las cuentas de una firma.
   - Noticias MFFU: el preset aplana y cancela órdenes.
   - 30 micros contando MNQ y MGC juntos.
   - Apex y Topstep: no usar.
5. **Deslizamiento real.**
   - Con +4 ticks por lado el Sharpe 2020-23 / 2024-26 baja de 3,43 / 4,00 a 2,79 / 3,48.
   - **No está medido en vivo.**

## Qué dice (y qué no) la estadística

- Las fórmulas son correctas (las verificó el revisor): DSR 0,95 con 100.000 pruebas, PBO 0,51 entre 33 variantes, Hansen SPA p < 0,001.
- **Pero no prueban robustez:**
  - El DSR trata 20 módulos, cada uno elegido entre miles, como una sola prueba. Con ruido puro, una cartera así podría mostrar un Sharpe de ~11, así que 3,67 no la distingue de selección.
  - El PBO compara variantes casi idénticas.
  - El SPA contra cero es trivial con variantes claramente positivas.
- **La evidencia real de que no todo es selección:**
  - En la minería de 16 años, pasar 2020-23 multiplicó por 10 la chance de pasar 2024-26 (15% vs 1,4% de base).
  - NinjaTrader reproduce la investigación (92,7% de trades, P&L ±1%).
  - Los módulos más viejos siguieron rindiendo en 2024-26.
- **La evidencia en contra:** en 2010-19 el DSR es 0 y solo VOLB y NF05 tienen probabilidad posterior de edge positivo.
- **Meses 2020-26:**
  - 15 de 82 negativos, peor mes −$2.210, racha máxima de 3. El P&L de 12 meses móviles nunca fue negativo.
  - Bootstrap con edge completo: 1,9 meses negativos por año y 4% de probabilidad de 3 seguidos.
  - Con 35% menos edge: 3,2 meses negativos por año y 17% de probabilidad de 3 seguidos.

## Paridad y reproducibilidad

- **Datos:** 45 archivos con SHA-256 OK.
- **Trades:** la reconstrucción desde cero da trades **idénticos** a los guardados (6 perfiles × 2 eras).
- **Compuerta `parity_check.py`** sobre el export de NinjaTrader del 14-oct:

  | Compuerta | Resultado |
  |---|---|
  | Trades emparejados | 94,6% |
  | P&L de los emparejados | +0,8% |
  | Correlación diaria | 0,968 |
  | Módulo ICT | 82% — **falla la compuerta del 90%** (NinjaTrader llena el retest más tarde) |
  | Módulo MSEQS | 56% — **falla la compuerta del 90%** |

  MSEQS en NinjaTrader exige que ORB60 se haya llenado; la investigación usa la señal de ORB60 antes de los filtros. Son ~$24/mes. Queda abierto.
- **Falta validar en NinjaTrader:** CPI09, los ×4/×8 y los arreglos F1-F9. Hace falta un backtest nuevo.
- **Bugs viejos de investigación encontrados:**
  - Las configuraciones sin boost de los estudios del 5-6 de octubre no tenían MSEQS en REAL (~$57/mes).
  - El haircut no escalaba con el tamaño en los estudios de escalón, lo que inflaba el escalón.
  - CPI09 nunca recibía el risk cap en la investigación.
  - Ninguno cambia una decisión vigente.

## Bloqueado (necesita algo de Federico)

- **Edge independiente (ZN/ZB, M2K, MYM):** exportar desde NinjaTrader con `BarExporterUTC.cs` (2024-26, 1 minuto). Es la única palanca que sube el techo.
- **Deslizamiento real y reglas de "no perseguir":** datos de cuenta en vivo o simulada.
- **Refactor de NQMaster en clases:** solo con F5 y `parity_check.py` en la PC.

## Respuestas honestas

1. **¿Cuánto es real y cuánto selección?**
   - Evidencia a favor: la persistencia de 2020-23 a 2024-26, la paridad con NinjaTrader y los módulos viejos que siguen rindiendo.
   - Evidencia en contra: 2010-19 casi sin edge, y DSR/PBO/SPA que no pueden separar skill de selección en una cartera armada módulo por módulo.
   - Mi estimación: **40-75% del rendimiento del backtest 2020-26 es real, mientras dure el régimen.** El haircut de 35% está en el medio. Que llegue a 50% es tan plausible como que no.
2. **¿Más de $1.200 por cuenta y por mes durante 12 meses?**
   - Con la configuración default, P(promedio de 12 meses ≥ $1.200) = 53% con edge completo, 26% con 35% menos y 0% con edge cero. Ponderando por la incertidumbre, **~30%**. Con el escalón opcional, ~40%, a cambio de más años negativos.
   - Que **todos** los meses superen $1.200: < 5%.
   - Perder cuentas es seguro: ~1,2 por año por asiento con edge completo (casi todas evaluaciones fallidas) y ~3 con 35% menos. Las fondeadas perdidas son 0,35-0,9 por año.
3. **Mejor jugada:** no seguir optimizando el edge, que está en su techo. En orden:
   1. F5 y backtest con `parity_check.py`.
   2. **Una** cuenta MFFU durante 60-90 días, con `impl_gap.py`.
   3. En paralelo, exportar ZN, M2K y MYM para buscar un flujo independiente.
   4. Escalar a más cuentas, con el mismo perfil, solo con evidencia en vivo.
4. **Qué me haría cambiar de opinión:**
   - 60-90 días en vivo con P&L por contrato < 65% de lo esperado: pausa.
   - Deslizamiento real > 4 ticks.
   - Un flujo con correlación < 0,15 que pase los 4 períodos.
   - Otro agosto seguido de otro.
   - La paridad del backtest nuevo con fallas fuera de ICT y MSEQS.
