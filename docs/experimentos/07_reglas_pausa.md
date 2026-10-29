# Experimento 07 (frente 5C): reglas de pausa 1 y 4 del runbook dentro de la simulación de campaña — 2026-10-29

**Veredicto (regla pre-registrada): la regla 1 se retira, la regla 4 queda pero no protege dentro de 12 meses, y ninguna regla basada en el P&L del sistema protege la campaña en el primer año.** La regla 1 ("después de 60 días hábiles, P&L acumulado por contrato base negativo → pausar") confunde un edge 35 % más bajo con un edge muerto: con −35 % pausa la campaña en el 24 / 28 % de los años (bootstrap; 49 / 46 % sobre historia contigua), casi siempre en el día 60, y lleva P(año negativo) del plan de 4 / 4 % a 23 / 26 % y el p10 de $2.464 / $1.801 a −$688 / −$807 por mes (P(perder > 5 %) 0,21 / 0,26 > 0,20). Con el edge muerto todo el año acota la cola (p10 −$3.712 / −$4.182 → −$1.177 / −$1.351) pero no la mediana (P(ganar) 0,51 / 0,48). La regla 4 ("dos trimestres calendario seguidos negativos") casi no cuesta (P(perder > 5 %) ≤ 0,04) pero sin edge recién actúa en el día 126-189 y no mejora la mediana (P(ganar) 0,41 / 0,39). Unidad: plan completo (5 Lucid 150K 6c/3c + 3 MFFU 1x8); 1.000 caminos bootstrap por celda (los de la base: sin regla reproduce `integ_port.json` al dólar) y 84 / 132 planes sobre historia contigua; T1 = arranques 2020-22, T2 = 2023-26; costos $1,90 + 2 ticks por lado, fees con cupón.

**Por qué no hay regla rápida que sirva:** el P&L del sistema por contrato base (mezcla de la campaña) tiene media de $106 / $102 por día y desvío diario de $423 / $467 (T1 / T2); separar un edge 35 % más bajo de uno muerto con 2 errores estándar exige ~150 / 200 días hábiles de datos, sin contar que los tramos malos se agrupan (lo que alarga el plazo). La regla 1 decide con 60 días: no tiene datos para distinguir y por eso pausa años buenos con −35 %. La regla 4 junta ~126-189 días, el orden de magnitud correcto, pero para entonces ya pasó medio año. Es un límite de información, no de diseño de la regla.

## Qué se corrió

`research/mine/exp07_pause_rules.py`: el día de pausa se calcula con el P&L del sistema por contrato base (mezcla de la campaña con MOM1030/CPI09 ×4, menos el recorte del escenario) acumulado desde el día 0 del camino, usando solo días anteriores; la pausa (`Enabled = false`) corta las 8 cuentas desde ese día hasta el fin de los 12 meses y el saldo abierto de las fondeadas no se cuenta como caja (como el fin del horizonte de la base). Escenarios con cambio de régimen: arreglos de días duplicados (copia con edge completo y copia sin edge) y salto de una a otra en el día 63 o 126 del camino. Autotest: sin regla reproduce el plan de la base al dólar en los tres escenarios constantes, y un cambio fuera del camino reproduce "completo". Regla de decisión en `docs/PLAN_2026-10-29_exp07.md`. Las reglas 2 (alarma del monitor + año de fallback negativo, no puede actuar en 12 meses) y 3 (brecha entre la cuenta real y la investigación, 0 en la simulación) no se simulan. Corrida: 2 min.

## Bootstrap (T1 / T2)

| Regla | Mediana $/mes | p10 | P(año < 0) % | Ventanas 60 d neg. % | Planes pausados % | P(ganar) / P(perder > 5 %) vs base, T1 · T2 |
|---|---|---|---|---|---|---|
| **Edge completo** | | | | | | |
| sin regla (base) | 16.173 / 14.689 | 9.243 / 7.041 | 0,0 / 0,6 | 4,5 / 8,5 | 0 / 0 | — |
| R1: acumulado < 0 desde el día 60 | 16.031 / 14.480 | 8.157 / 454 | 4,4 / 9,1 | 4,6 / 8,2 | 4 / 10 | 0,00 / 0,04 · 0,00 / 0,10 |
| R4: dos trimestres negativos | 16.173 / 14.689 | 9.243 / 6.994 | 0,1 / 1,2 | 4,5 / 8,6 | 0 / 2 | 0,00 / 0,00 · 0,00 / 0,01 |
| R1 + R4 | 16.031 / 14.480 | 8.157 / 454 | 4,5 / 9,2 | 4,6 / 8,3 | 4 / 11 | 0,00 / 0,04 · 0,00 / 0,10 |
| **−35 % de edge** | | | | | | |
| sin regla (base) | 8.824 / 8.418 | 2.464 / 1.801 | 3,9 / 4,2 | 22,3 / 22,6 | 0 / 0 | — |
| R1: acumulado < 0 desde el día 60 | 7.534 / 7.038 | -688 / -807 | 23,2 / 25,5 | 19,6 / 19,0 | 24 / 28 | 0,02 / 0,21 · 0,03 / 0,26 |
| R4: dos trimestres negativos | 8.820 / 8.380 | 1.968 / 1.409 | 5,0 / 6,1 | 22,3 / 22,6 | 5 / 8 | 0,02 / 0,02 · 0,02 / 0,04 |
| R1 + R4 | 7.514 / 6.995 | -688 / -813 | 23,2 / 25,7 | 19,6 / 19,1 | 26 / 32 | 0,03 / 0,22 · 0,04 / 0,27 |
| **Edge cero todo el año** | | | | | | |
| sin regla (base) | -789 / -566 | -3.712 / -4.182 | 56,4 / 55,3 | 63,4 / 63,1 | 0 / 0 | — |
| R1: acumulado < 0 desde el día 60 | -802 / -877 | -1.177 / -1.351 | 77,3 / 75,9 | 29,3 / 28,1 | 84 / 84 | 0,51 / 0,32 · 0,48 / 0,35 |
| R4: dos trimestres negativos | -1.277 / -1.174 | -2.518 / -3.005 | 62,9 / 61,1 | 56,3 / 56,3 | 58 / 56 | 0,41 / 0,16 · 0,39 / 0,16 |
| R1 + R4 | -802 / -874 | -1.173 / -1.343 | 77,3 / 75,8 | 29,3 / 28,1 | 88 / 88 | 0,55 / 0,33 · 0,52 / 0,35 |

## Cambio de régimen a mitad del año (bootstrap, caminos de "completo")

| Regla | Mediana $/mes | p10 | P(año < 0) % | Ventanas 60 d neg. % | Planes pausados % | P(ganar) / P(perder > 5 %) vs base, T1 · T2 | Demora mediana de la pausa desde el cambio (días) |
|---|---|---|---|---|---|---|---|
| **Edge completo hasta el día 63, cero después** | | | | | | | |
| sin regla (base) | 2.995 / 2.591 | -1.954 / -2.572 | 26,2 / 29,1 | 50,3 / 52,3 | 0 / 0 | — | — / None |
| R1: acumulado < 0 desde el día 60 | 2.616 / 2.015 | -713 / -892 | 25,5 / 28,7 | 41,6 / 40,5 | 41 / 45 | 0,29 / 0,11 · 0,31 / 0,13 | 76 / 54 |
| R4: dos trimestres negativos | 2.999 / 2.383 | -1.567 / -2.024 | 24,8 / 29,8 | 49,8 / 51,5 | 44 / 48 | 0,34 / 0,09 · 0,33 / 0,13 | 126 / 126 |
| R1 + R4 | 2.647 / 2.046 | -694 / -887 | 24,9 / 28,4 | 41,5 / 40,3 | 58 / 61 | 0,42 / 0,14 · 0,42 / 0,17 | 116 / 95 |
| **Edge completo hasta el día 126, cero después** | | | | | | | |
| sin regla (base) | 7.082 / 6.439 | 2.021 / 353 | 4,8 / 8,6 | 29,2 / 32,1 | 0 / 0 | — | — / None |
| R1: acumulado < 0 desde el día 60 | 6.952 / 6.127 | 1.192 / -492 | 7,7 / 13,2 | 28,3 / 29,2 | 12 / 18 | 0,07 / 0,04 · 0,10 / 0,07 | 68 / -36 |
| R4: dos trimestres negativos | 7.102 / 6.425 | 2.067 / 459 | 4,6 / 8,4 | 29,2 / 32,1 | 32 / 34 | 0,27 / 0,02 · 0,26 / 0,04 | 126 / 126 |
| R1 + R4 | 6.950 / 6.199 | 1.163 / -492 | 7,8 / 12,9 | 28,3 / 29,3 | 36 / 41 | 0,28 / 0,06 · 0,28 / 0,10 | 126 / 126 |

Con el edge muerto desde el día 63, la regla 1 pausa el 41 / 45 % de los planes con una demora mediana de 76 / 54 días y mejora el p10 (de −$1.954 / −$2.572 a −$713 / −$892) a costa de la mediana; la regla 4 tarda 126 días. Si el edge muere en el día 126, a ninguna regla le alcanza el año: la 1 pausa el 12 / 18 % (en 2023-26, mayormente antes del cambio: demora mediana -36 días).

## Historia contigua (84 / 132 planes)

| Regla | Mediana $/mes | p10 | P(año < 0) % | Ventanas 60 d neg. % | Planes pausados % | P(ganar) / P(perder > 5 %) vs base, T1 · T2 |
|---|---|---|---|---|---|---|
| **Edge completo** | | | | | | |
| sin regla (base) | 12.685 / 18.522 | 6.925 / 2.101 | 0,0 / 5,3 | 12,5 / 22,4 | 0 / 0 | — |
| R1: acumulado < 0 desde el día 60 | 12.605 / 18.522 | -454 / -745 | 14,3 / 31,1 | 12,0 / 13,3 | 14 / 30 | — |
| R4: dos trimestres negativos | 12.685 / 18.522 | 6.925 / -379 | 0,0 / 12,1 | 12,5 / 22,7 | 0 / 12 | — |
| R1 + R4 | 12.605 / 18.522 | -454 / -745 | 14,3 / 31,1 | 12,0 / 13,2 | 14 / 33 | — |
| **−35 % de edge** | | | | | | |
| sin regla (base) | 6.163 / 11.285 | 894 / -1.502 | 0,0 / 14,4 | 30,8 / 27,5 | 0 / 0 | — |
| R1: acumulado < 0 desde el día 60 | 2.230 / 9.850 | -795 / -891 | 44,0 / 38,6 | 27,8 / 13,7 | 49 / 46 | — |
| R4: dos trimestres negativos | 6.163 / 11.285 | 894 / -1.822 | 0,0 / 28,8 | 30,8 / 26,3 | 2 / 30 | — |
| R1 + R4 | 1.498 / 9.850 | -795 / -891 | 44,0 / 38,6 | 27,9 / 13,6 | 51 / 47 | — |
| **Edge cero todo el año** | | | | | | |
| sin regla (base) | -3.583 / 512 | -4.212 / -5.078 | 59,5 / 49,2 | 79,3 / 73,2 | 0 / 0 | — |
| R1: acumulado < 0 desde el día 60 | -840 / -984 | -1.138 / -1.404 | 98,8 / 81,1 | 23,9 / 30,0 | 99 / 81 | — |
| R4: dos trimestres negativos | -1.965 / -1.952 | -3.497 / -2.730 | 76,2 / 62,9 | 63,0 / 57,8 | 75 / 67 | — |
| R1 + R4 | -840 / -992 | -1.138 / -1.404 | 98,8 / 81,8 | 23,9 / 29,7 | 99 / 95 | — |

Sobre historia contigua la regla 1 es peor: con el edge completo pausa el 14 / 30 % de los planes (p10 de $6.925 / $2.101 a −$454 / −$745); los planes que arrancan antes de un tramo malo real (2023 T3) cruzan el acumulado negativo en el día 60. La regla 4 con el edge completo en 2023-26 pausa el 12 % (p10 −$379).

## Saldo abierto al pausar (medición prometida en el plan, `research/mine/exp07_open_balance.py`)

El día de la pausa las fondeadas tienen poco saldo positivo: en promedio por plan pausado, regla 1 $647-2.139 con el edge completo, $454-1.088 con −35 % y $794-796 sin edge; regla 4, $1.093-3.480. Contando el 90 % de ese saldo como cobrado (cota superior: en la realidad la cuenta queda abierta) ningún P(ganar) ni P(perder > 5 %) se mueve más de 0,02: **el veredicto no depende de la convención.**

## Qué cambia

- **Runbook:** la regla 1 se retira; la regla 4 queda con la nota "no protege dentro de 12 meses; sirve como freno en años siguientes"; las reglas 2 y 3 quedan como están (no simulables acá). Con esto, la campaña no tiene protección automática contra un edge muerto durante el primer año: **el costo de ese escenario es el que ya figura en las cifras de la campaña (edge cero: −$789 / −$566 por mes con cupón, p10 −$3.712 / −$4.182)** y es el precio del seguro.
- **Siguiente (5C):** el monitor de borde y su respuesta a la alarma, que es la única protección para los años siguientes; su validación sobre 2010-19 (`os_adapt.py`) usó un z mal escalado antes de 2020 y parámetros viejos (relevamiento del 29-oct): se re-valida con el z corregido.

Archivos: `research/mine/exp07_pause_rules.py`, `exp07_pause_rules.json`, `exp07_open_balance.py`, `exp07_open_balance.json`; plan `docs/PLAN_2026-10-29_exp07.md`.
