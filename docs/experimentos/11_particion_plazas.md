# Diagnóstico 11 (2026-10-30, frente 5D): repartir los módulos entre plazas

**Veredicto: no pasa, con el criterio pre-registrado y con la lectura post-hoc.**
- **Proxy pre-registrado (caída máxima en 252 días):** quedó saturado cerca del 100 % y no discrimina; ver la sección del criterio.
- **Lectura post-hoc (no pre-registrada; quiebres por año con renovación):** repartir los módulos en dos grupos y darle a cada plaza el doble de contratos multiplica los quiebres por par de plazas:
  - ×1,5 a ×1,9 en 2024-26;
  - ×2,6 a ×7,6 en 2020-23.
  - A cambio, los quiebres de las dos plazas coinciden menos: 7-53 % de las veces, contra 100 % hoy.
- **Consecuencia:** no se corre en el motor de campaña y el **frente 5D queda cerrado**. No queda ninguna regla de cuenta sin probar.

Plan pre-registrado: `docs/PLAN_2026-10-30_diag11.md`. Script: `research/mine/diag_partition.py` (5 s) → `diag_partition.json`.

## Qué se midió

Datos y costos:
- NQ real 2020-10 a 2026-10 (`six_ultra6_trades.pkl`), en $ por contrato.
- Costos de la lista de investigación: $1,90 de comisión + 1 tick por lado.
- Set 2027 sin CA04V, GD03 ni ENG26: 25 módulos.
- T1 = 2020-23 (537 días, acá se eligió la partición). T2 = 2024-26 (941 días).

Las dos plazas del par:
- **Base:** las dos operan el set completo a 1×.
- **Partición:** una opera el grupo A y la otra el grupo B, cada una a 2×. La exposición del plan a cada módulo es la misma de la base.

Las dos particiones:
- **Alternada:** módulos ordenados por $/día de T1 y repartidos A/B uno y uno.
- **Favorable:** entre 2.000 particiones al azar con medias parecidas, la de menor correlación A-B en T1.

Bootstrap: 2.000 caminos de 252 días, en bloques de 21 días.

**Dato de fondo:** la correlación diaria promedio entre módulos es 0,034. Una plaza ya está diversificada por dentro. Partirla resigna esa diversificación a cambio de desincronizar los quiebres entre plazas.

## Resultado

**Criterio pre-registrado.** Una plaza quiebra si la caída máxima desde el pico, en 252 días, alcanza $1.500 o $2.000 por contrato. Para que la partición pase, los quiebres por par no deben subir más de 10 % y P(quiebran las dos) debe bajar al menos 30 %.

| Período | Umbral | Base: P(quiebre) / P(las dos) | Favorable: P(quiebre A / B) / P(las dos) | Pasa |
|---|---|---|---|---|
| T1 | $1.500 | 92,0 % / 92,0 % | 98,0 / 100,0 % / 98,0 % | no |
| T1 | $2.000 | 42,8 % / 42,8 % | 81,1 / 100,0 % / 81,0 % | no |
| T2 | $1.500 | 99,8 % / 99,8 % | 100 / 100 % / 100 % | no |
| T2 | $2.000 | 94,5 % / 94,5 % | 97,7 / 100 % / 97,6 % | no |

En un año, la caída máxima de 1 contrato del set completo supera el umbral casi siempre. El proxy satura y no puede mostrar la desincronización. El veredicto pre-registrado es "no pasa", pero por sí solo no es concluyente.

**Lectura post-hoc (no pre-registrada).** Se agregó al ver la saturación. Cada vez que una plaza quiebra, arranca de nuevo, y se cuentan los quiebres por año. "Coincidencia" es el % de quiebres de A que caen a ±5 días de un quiebre de B.

| Período | Umbral | Base: quiebres por par / coincidencia | Alternada | Favorable |
|---|---|---|---|---|
| T1 | $1.500 | 4,63 / 100 % | 11,97 / 36 % | 13,76 / 26 % |
| T1 | $2.000 | 1,07 / 100 % | 6,71 / 7 % | 8,11 / 10 % |
| T2 | $1.500 | 10,59 / 100 % | 15,97 / 24 % | 18,33 / 53 % |
| T2 | $2.000 | 5,34 / 100 % | 9,63 / 18 % | 10,19 / 42 % |

Cada quiebre cuesta una eval nueva y el colchón perdido. Pasar de 1,07 a 6,7-8,1 quiebres por par en 2020-23, o de 5,3 a 9,6-10,2 en 2024-26, cuesta mucho más de lo que vale desincronizar.

Con menos edge (también post-hoc, partición favorable) se repite el mismo patrón. A cada plaza se le resta, por igual, una parte de su media diaria. Cada celda muestra quiebres por par en la base → con partición, y entre paréntesis la coincidencia con partición.

| Período | Edge | Umbral $1.500 | Umbral $2.000 |
|---|---|---|---|
| T1 | −35 % | 11,2 → 18,9 (51 %) | 5,2 → 11,5 (17 %) |
| T1 | cero | 25,9 → 31,0 (81 %) | 16,2 → 21,5 (59 %) |
| T2 | −35 % | 12,9 → 23,2 (53 %) | 8,9 → 13,9 (48 %) |
| T2 | cero | 25,1 → 35,0 (69 %) | 16,7 → 23,3 (58 %) |

## Límites

- Es un diagnóstico, no el motor de campaña. No modela evals, retiros, fees, el tope de riesgo de la fondeada ni el trailing con traba en +$100.
- El umbral por contrato es un proxy de la Lucid 150K a 3c y de la MFFU 50K a 1c.
- La diferencia es tan grande que ningún detalle del motor la da vuelta: los quiebres crecen ×1,2 a ×7,6 en todas las celdas, con los tres casos de edge.
- No se probó partir sin duplicar los contratos. Eso es bajar el tamaño, y el tamaño ya se estudió (experimento 03, acct_k, ladder).

## Frente 5D

Las reglas de cuenta de la consigna ya estaban probadas y descartadas:
- tope diario por ATR, semanal y mensual, y límite de riesgo abierto (ddlab, 0/40);
- tamaño según el colchón (`Conocimiento/Descartado/Ronda de mejoras 3-oct`);
- pausa tras racha (experimento 07);
- tamaño según la volatilidad (experimento 09).

El estrés de costos y de régimen está en el experimento 10. La única palanca que quedaba, que las plazas operen cosas distintas, tampoco sirve.

Lo que sigue en pie para el problema 4 de ESTADO (los meses malos queman fondeadas):
- el monitor de borde;
- la regla 4 como señal de revisión;
- el umbral de costos del runbook.
