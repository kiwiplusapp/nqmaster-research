# Diagnóstico 11 (2026-10-30, frente 5D): repartir los módulos entre plazas

**Veredicto: no conviene.** El criterio pre-registrado no se pudo evaluar, y la evidencia que decide es post-hoc.

**El criterio pre-registrado.** Usaba la caída máxima en 252 días, y esa medida satura: en un año, 1 contrato del set completo casi siempre cae más que el umbral. Además, el criterio era imposible por construcción. Como P(quiebran las dos) ≥ P(A) + P(B) − 1, bajar ese número un 30 % con la base en 93-99 % exigía que cada plaza quebrara menos que en la base, justo lo contrario de la hipótesis.

**La lectura post-hoc (no pre-registrada).** Se cuentan los quiebres por año, y cada vez que una plaza quiebra arranca de nuevo. Repartir los módulos en dos grupos, con el doble de contratos por plaza, multiplica los quiebres por par de plazas:
- **Edge completo:** ×1,5 a ×1,7 en 2023-26 y ×2,8 a ×6,2 en 2020-22.
- **Corte del plan (2024):** ×1,5 a ×1,9 en 2024-26 y ×2,1 a ×2,5 en 2020-23.
- **Con −35 % y con edge cero:** ×1,2 a ×2,0.

A cambio, los quiebres de las dos plazas coinciden menos: entre 6 % y 47 % de las veces, contra 100 % hoy.

**Consecuencia.** La partición no se corre en el motor de campaña. 5D queda cerrado **para la partición y para las reglas de cuenta de la consigna**. Lo que queda sin probar está al final.

- Plan: `docs/PLAN_2026-10-30_diag11.md`. Ojo: se commiteó junto con este informe, así que el pre-registro no se puede verificar por git.
- Script: `research/mine/diag_partition.py` (v2, 12 s) → `diag_partition.json`.
- Revisión adversarial: `docs/experimentos/revisiones/diag11/`.

## Qué se midió

**Set.** Es el set exacto de la campaña: `nt_compare.research_set('ultra_d4')`, NQ real de 2020-10 a 2026-10, en $ por contrato y con los costos de la lista ($1,90 + 1 tick por lado). Son 23 módulos, con `conflict_filter`. La v1 usaba 25 módulos (con LATEFH, que está apagado por defecto) y no aplicaba el filtro.

**Períodos.** Se usa el mismo corte que `prop_wf`:
- **T1:** 2020-10 a 2022-12 (536 días). Acá se elige la partición.
- **T2:** 2023-01 a 2026-10 (941 días).

La v1 los rotulaba mal como 2020-23 / 2024-26. Como sensibilidad post-hoc, también se corrió con el corte de 2024 que decía el plan.

**Comparación.**
- **Base:** las dos plazas operan el set completo a 1×.
- **Partición:** una opera el grupo A y la otra el B, cada una a 2×. La exposición del plan a cada módulo es la misma.
- **Grupos:**
  - "Alternada": módulos ordenados por $/día de T1 y repartidos uno y uno.
  - "Favorable": entre las 494 particiones al azar (de 2.000) con medias de T1 a ±10 %, la de menor correlación A-B en T1.
- **Bootstrap:** 2.000 caminos de 252 días en bloques de 21, los mismos para la base y para la partición.

**Dato de fondo.** La correlación diaria promedio entre módulos es 0,034. Cada plaza ya está diversificada por dentro, y partirla resigna esa diversificación a cambio de desincronizar los quiebres.

## Resultado post-hoc (quiebres por año con renovación)

Cada celda: quiebres por par de plazas en 252 días, y entre paréntesis la coincidencia. La coincidencia es el % de quiebres de una plaza que caen a ±5 días de un quiebre de la otra; se da A→B / B→A.

| Período | Umbral por contrato | Base | Alternada | Favorable |
|---|---|---|---|---|
| T1 2020-22 | $1.500 | 4,55 (100 %) | 13,03 (38 / 43 %) | 12,67 (15 / 27 %) |
| T1 2020-22 | $2.000 | 1,02 (100 %) | 6,20 (6 / 8 %) | 6,37 (6 / 12 %) |
| T2 2023-26 | $1.500 | 10,41 (100 %) | 15,31 (27 / 40 %) | 16,08 (34 / 47 %) |
| T2 2023-26 | $2.000 | 5,74 (100 %) | 9,67 (21 / 36 %) | 9,46 (28 / 38 %) |

Los umbrales representan dos cuentas: $1.500 por contrato es la Lucid 150K fondeada a 3c (trailing $4.500), y $2.000 es la MFFU 50K a 1c.

**Con el corte del plan (2024):**

| Período | $1.500 | $2.000 |
|---|---|---|
| T1 2020-23 | 6,38 → 13,6-13,7 | 3,04 → 7,6 |
| T2 2024-26 | 10,50 → 15,8-16,3 | 5,15 → 9,4-9,7 |

**Con menos edge (partición favorable):** a cada plaza se le resta por igual una parte de su media diaria.

| Período | Edge | $1.500: base → partición (coincidencia) | $2.000: base → partición (coincidencia) |
|---|---|---|---|
| T1 | −35 % | 10,0 → 16,6 (22 %) | 4,7 → 9,5 (14 %) |
| T1 | cero | 24,6 → 29,4 (46 %) | 16,1 → 19,5 (38 %) |
| T2 | −35 % | 13,0 → 21,0 (39 %) | 9,1 → 12,7 (37 %) |
| T2 | cero | 24,1 → 31,9 (57 %) | 15,7 → 21,0 (40 %) |

Cada quiebre cuesta una eval nueva y el colchón perdido. La exposición del plan no cambia, así que el ingreso esperado tampoco cambia por la partición: solo cambia cómo se reparte entre plazas. Cada plaza a 2× con la mitad de los módulos tiene más varianza: según el revisor, con el set de la v1, su Sharpe cae de 4,26 a 2,90-4,12 en T1 y de 3,65 a 2,39-3,22 en T2. Una plaza con el set completo y ~1,3× contratos la domina.

**Cotas del revisor (calculadas con el set de la v1; con el set exacto da ×1,17 a ×6,76, el mismo patrón).**
- Con la mejor partición posible, elegida directamente por quiebres en T1 (1.574 candidatas), los quiebres por par suben ×3,98 en T1 y ×1,46 / ×1,73 en T2.
- Con umbrales de $500 a $6.000, ninguna celda con edge sube 10 % o menos; el mínimo es ×1,18.
- Con 5 semillas, la celda extrema queda en ×5,95-7,41.

## Límites

- Es un diagnóstico, no el motor de campaña. No modela evals, retiros, fees, el tope de riesgo de la fondeada ni el trailing con traba en +$100. Sin la traba, el proxy da ~5 quiebres por año, contra 1,5-2 en el motor.
- No se midió M2, que es la métrica que hoy falla: las ventanas de 60 días con caja negativa. La partición desincroniza los quiebres, y eso podría mejorar M2 aunque haya más quiebres. No está probado que no lo haga. Lo que sí se ve es que sube el costo por quiebres en todas las celdas.
- El plan tiene 5 Lucid + 3 MFFU y no se parte en mitades exactas.

## Qué queda sin probar en 5D

**Ya probado y descartado:**
- Tope diario por ATR, semanal y mensual, y límite de riesgo abierto (ddlab, 0/40).
- Tamaño según el colchón en la fondeada (`Conocimiento/Descartado/Ronda de mejoras 3-oct`).
- La escalera de MFFU con y sin stop diario de $1.500 por contrato. En la integración de la ronda 5 (`research/mine/integ_ladder.json`) no pasó: con −35 %, P(ganancia) quedó en 0,54-0,63, por debajo de 0,80, y P(año negativo) empeoró 14-22 puntos.
- Pausa tras racha (experimento 07).
- Tamaño según la volatilidad (experimento 09).
- Estrés de costos y de régimen (experimento 10).
- Esta partición.

**Sin probar:**
- Partir por firma (Lucid = un grupo, MFFU = el otro).
- Perfiles distintos por plaza a 1×, por ejemplo algunas plazas en WR70Plus o Durable. Esto baja la exposición del plan y además es una decisión de perfil.

Ninguna de las dos se puede leer bien sin el motor de campaña. Las dos chocan con lo que muestra este diagnóstico: a igual exposición, una plaza con menos módulos quiebra más.
