# Experimento 03 (frente 5B): tamaño de la eval de Lucid Flex 150K medido con la función objetivo — 2026-10-27

**Veredicto: sin cambio. La regla pre-registrada elige al 6c actual.** Ningún tamaño de eval (1 a 6 contratos, todo lo demás igual) cumple las 6 condiciones del programa. En 2020-22, sumando edge completo y −35 %, el 6c cumple 7 de 12 y empata con la eval de 1 contrato (7); el desempate pre-registrado (mediana $/mes con −35 %) lo gana el 6c por $8.824 contra $3.715. **El trade-off es monótono:** cada contrato menos en la eval baja las evals perdidas y sube la aprobación por intento, pero alarga la aprobación y recorta el ingreso del plan. Las dos condiciones que hoy fallan (evals perdidas < 0,12 por mes, aprobación ≥ 65 %) solo se cumplen con 1 contrato (edge completo, 2020-22: 0,08 por mes y 93 %), que tarda 60 días hábiles en aprobar (umbral 10) y pierde el 44 / 50 % del ingreso del plan (P(perder > 5 %) 0,99 / 0,98); en 2023-26 además falla p10 y ventanas negativas. El 5c es la única alternativa pareja: ingreso igual dentro del ruido (-0,6 / -1,1 % con el edge completo, +0,8 / +0,2 % con −35 %; P(ganar) 0,41-0,56), 1,49 / 2,67 evals perdidas por mes contra 1,89 / 3,28 (≈ $1.000-1.600 menos de fees por año entre las 5 cuentas), aprobación 56 / 47 % contra 51 / 43 %, pero la aprobación mediana pasa a 10 / 9 días (p75 18 / 16) y con −35 % rompe el umbral de 10 días en 2020-22: suma 6 contra 7 y no gana la elección. Unidad: plan completo (5 Lucid 150K con eval k / fondeada 3c + 3 MFFU 1x8 sin cambios), cupón; caminos NQ real 2020-02-26 → 2026-10-08; T1 = arranques 2020-22 (elige), T2 = 2023-26 (confirma); 1.000 caminos bootstrap pareados por celda (mismos caminos y semillas que la base del experimento 02) y, al lado, 84 / 132 planes sobre historia contigua; costos $1,90 + 2 ticks por lado y fees con cupón ($215 por eval de Lucid). Nada de la estrategia cambia.

## Qué se corrió

`research/mine/exp03_eval_size.py` sobre `objective.py`: para k = 1..6 contratos de eval (objetivo $9.000, trailing EOD $4.500, consistencia 50 % con stop de ganancia diario $4.050, sin stop intradía) con la fondeada 3c sin cambios, asiento y plan sobre los mismos caminos que la base (el 6c reproduce la base al dólar), neto por camino guardado para la ganancia pareada, historia contigua con `contiguous()` y la regla de decisión escrita en `docs/PLAN_2026-10-27_exp03.md` aplicada sin mirar T2 para elegir. Corrida: 2 min (1.000 caminos).

## Plan completo (8 cuentas), bootstrap, T1 / T2

| Eval | Mediana $/mes | p10 | Ventanas 60 d negativas % | Evals perdidas / mes | Aprobación % | Días aprobar (p75) | Cumple (de 6) · patrón M1 M1 M2 M3 M4 M5 | Ingreso pareado vs 6c |
|---|---|---|---|---|---|---|---|---|
| **Edge completo** | | | | | | | | |
| 1c | 9.171 / 7.646 | 3.001 / 1.502 | 6,0 / 13,9 | 0,08 / 0,27 | 93 / 81 | 60 (92) / 52 (87) | **5 / 2** ✓✓✓✓✓✗ ✓✗✗✗✓✗ | -44,3 % (P ganar 0,00, P perder > 5 % 0,99) / -49,9 % (0,01, 0,98) |
| 2c | 12.342 / 10.542 | 5.988 / 3.309 | 6,6 / 14,3 | 0,19 / 0,75 | 88 / 69 | 32 (50) / 27 (41) | **4 / 3** ✓✓✓✗✓✗ ✓✓✗✗✓✗ | -24,6 % (P ganar 0,03, P perder > 5 % 0,93) / -28,3 % (0,05, 0,90) |
| 3c | 14.398 / 12.700 | 7.358 / 5.346 | 6,0 / 12,7 | 0,54 / 1,36 | 76 / 60 | 21 (33) / 18 (27) | **4 / 2** ✓✓✓✗✓✗ ✓✓✗✗✗✗ | -13,2 % (P ganar 0,10, P perder > 5 % 0,77) / -14,1 % (0,13, 0,77) |
| 4c | 15.252 / 13.957 | 8.542 / 5.963 | 5,4 / 10,8 | 1,14 / 1,99 | 61 / 53 | 14 (23) / 13 (20) | **3 / 2** ✓✓✓✗✗✗ ✓✓✗✗✗✗ | -5,5 % (P ganar 0,25, P perder > 5 % 0,53) / -5,6 % (0,28, 0,53) |
| 5c | 15.803 / 14.425 | 9.161 / 6.628 | 4,5 / 9,6 | 1,49 / 2,67 | 56 / 47 | 10 (18) / 9 (16) | **4 / 4** ✓✓✓✗✗✓ ✓✓✓✗✗✓ | -0,6 % (P ganar 0,41, P perder > 5 % 0,26) / -1,1 % (0,41, 0,34) |
| 6c | 16.173 / 14.689 | 9.243 / 7.041 | 4,5 / 8,5 | 1,89 / 3,28 | 51 / 43 | 9 (15) / 8 (13) | **4 / 4** ✓✓✓✗✗✓ ✓✓✓✗✗✓ | incumbente |
| **−35 % de edge** | | | | | | | | |
| 1c | 3.715 / 2.834 | -94 / -318 | 25,7 / 31,9 | 0,36 / 0,64 | 71 / 62 | 55 (109) / 43 (91) | **2 / 1** ✓✗✗✗✓✗ ✓✗✗✗✗✗ | -54,3 % (P ganar 0,05, P perder > 5 % 0,94) / -57,7 % (0,06, 0,93) |
| 2c | 6.596 / 5.888 | 234 / -187 | 27,8 / 33,1 | 0,80 / 1,51 | 63 / 51 | 32 (52) / 27 (43) | **1 / 1** ✓✗✗✗✗✗ ✓✗✗✗✗✗ | -29,5 % (P ganar 0,12, P perder > 5 % 0,82) / -31,7 % (0,13, 0,84) |
| 3c | 7.356 / 6.870 | 736 / 495 | 27,7 / 30,7 | 1,62 / 2,44 | 50 / 44 | 19 (31) / 19 (29) | **1 / 1** ✓✗✗✗✗✗ ✓✗✗✗✗✗ | -14,3 % (P ganar 0,22, P perder > 5 % 0,67) / -15,6 % (0,22, 0,70) |
| 4c | 8.268 / 7.648 | 1.640 / 983 | 24,9 / 27,4 | 2,29 / 3,62 | 44 / 38 | 13 (22) / 13 (21) | **2 / 1** ✓✓✗✗✗✗ ✓✗✗✗✗✗ | -2,9 % (P ganar 0,42, P perder > 5 % 0,46) / -8,3 % (0,29, 0,60) |
| 5c | 8.670 / 8.323 | 2.278 / 1.876 | 22,9 / 24,1 | 3,08 / 4,30 | 39 / 36 | 11 (18) / 9 (16) | **2 / 3** ✓✓✗✗✗✗ ✓✓✗✗✗✓ | +0,8 % (P ganar 0,56, P perder > 5 % 0,28) / +0,2 % (0,51, 0,38) |
| 6c | 8.824 / 8.418 | 2.464 / 1.801 | 22,3 / 22,6 | 4,00 / 5,72 | 34 / 30 | 9 (13) / 8 (13) | **3 / 3** ✓✓✗✗✗✓ ✓✓✗✗✗✓ | incumbente |

Umbrales: > 2.759 · ≥ 1.600 · < 10 % · < 0,12 · ≥ 65 % · ≤ 10. Puntaje de la regla en T1 (condiciones cumplidas con edge completo + −35 %; desempate mediana −35 %): 1c 7 ($3.715) · 2c 5 ($6.596) · 3c 5 ($7.356) · 4c 5 ($8.268) · 5c 6 ($8.670) · 6c 7 ($8.824).

## Plan completo, historia contigua (sin bootstrap; 84 / 132 planes con inicio real cada 5 días)

| Eval | Mediana $/mes | p10 | Ventanas 60 d negativas % | Evals perdidas / mes | Aprobación % | Días aprobar | Cumple |
|---|---|---|---|---|---|---|---|
| **Edge completo** | | | | | | | |
| 1c | 7.492 / 9.156 | 906 / -441 | 7,8 / 26,5 | 0,09 / 0,38 | 92 / 74 | 48 / 61 | 4 / 2 |
| 2c | 8.299 / 14.858 | 3.887 / -123 | 12,1 / 28,5 | 0,22 / 0,97 | 86 / 61 | 32 / 29 | 3 / 1 |
| 3c | 8.509 / 16.542 | 3.823 / 945 | 16,4 / 25,6 | 0,58 / 1,29 | 73 / 58 | 23 / 25 | 3 / 1 |
| 4c | 9.567 / 16.918 | 4.143 / 765 | 18,4 / 25,0 | 1,31 / 2,41 | 57 / 47 | 16 / 16 | 2 / 1 |
| 5c | 12.784 / 18.481 | 7.278 / 1.212 | 12,1 / 23,2 | 2,00 / 2,91 | 46 / 44 | 8 / 12 | 3 / 1 |
| 6c | 12.685 / 18.522 | 6.925 / 2.101 | 12,5 / 22,4 | 2,62 / 3,48 | 40 / 41 | 7 / 10 | 3 / 3 |
| **−35 %** | | | | | | | |
| 1c | 923 / 3.993 | -439 / -620 | 42,8 / 35,8 | 0,62 / 0,88 | 52 / 47 | 43 / 45 | 0 / 1 |
| 2c | 3.483 / 6.485 | -746 / -905 | 47,6 / 36,6 | 1,27 / 1,73 | 49 / 42 | 39 / 35 | 1 / 1 |
| 3c | 5.125 / 9.648 | -662 / -1.190 | 41,1 / 36,0 | 2,00 / 2,45 | 45 / 39 | 19 / 23 | 1 / 1 |
| 4c | 5.274 / 9.419 | -751 / -1.447 | 43,6 / 35,2 | 2,29 / 4,49 | 43 / 26 | 20 / 17 | 1 / 1 |
| 5c | 6.584 / 11.442 | 1.298 / -1.497 | 31,7 / 32,5 | 3,35 / 4,97 | 32 / 27 | 12 / 11 | 1 / 1 |
| 6c | 6.163 / 11.285 | 894 / -1.502 | 30,8 / 27,5 | 5,03 / 7,20 | 25 / 20 | 10 / 8 | 2 / 2 |

Sobre historia contigua el orden se mantiene (ingreso y velocidad crecen con k; evals perdidas y aprobación mejoran al bajar k) y ningún k cambia de signo respecto del bootstrap. El 5c y el 6c quedan empatados también acá (mediana 12.784 / 18.481 contra 12.685 / 18.522; ventanas negativas 12,1 / 23,2 contra 12,5 / 22,4 %).

## Asiento Lucid 150K solo (edge completo, bootstrap, T1 / T2)

| Eval | Mediana $/mes | p10 | Ventanas 60 d neg. % | Evals perdidas / mes | Fondeadas perdidas / mes | Aprobación % | P(fondeado ≤ 22 d, ≤ 3 evals) % | P(≤ 120 d) % | Días (p75) | Fees del plan de 22 d | Retiros / año |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1c | 1.089 / 1.053 | 171 / -36 | 10,6 / 19,7 | 0,000 / 0,007 | 0,053 / 0,084 | 100 / 95 | 3 / 4 | 67 / 68 | 75 (105) / 76 (105) | 215 / 215 | 4,8 / 3,7 |
| 2c | 1.746 / 1.260 | 846 / 360 | 13,3 / 29,4 | 0,017 / 0,107 | 0,081 / 0,148 | 93 / 71 | 21 / 21 | 94 / 92 | 35 (55) / 31 (46) | 218 / 249 | 7,7 / 6,5 |
| 3c | 2.160 / 1.710 | 1.052 / 792 | 14,3 / 23,5 | 0,087 / 0,225 | 0,100 / 0,183 | 76 / 59 | 38 / 40 | 99 / 94 | 21 (33) / 18 (28) | 245 / 289 | 9,3 / 8,3 |
| 4c | 2.178 / 2.071 | 1.242 / 982 | 11,2 / 16,9 | 0,201 / 0,359 | 0,107 / 0,206 | 60 / 51 | 54 / 58 | 90 / 87 | 12 (21) / 12 (19) | 306 / 335 | 10,5 / 9,6 |
| 5c | 2.368 / 2.174 | 1.414 / 1.117 | 8,7 / 13,4 | 0,268 / 0,486 | 0,114 / 0,216 | 55 / 45 | 66 / 67 | 89 / 82 | 10 (15) / 9 (13) | 340 / 385 | 11,2 / 10,4 |
| 6c | 2.417 / 2.242 | 1.450 / 1.235 | 7,9 / 11,4 | 0,341 / 0,597 | 0,116 / 0,224 | 49 / 41 | 69 / 71 | 78 / 80 | 8 (12) / 7 (11) | 380 / 402 | 11,6 / 10,9 |

**Lectura.** (1) La eval de Lucid 150K convierte contratos en velocidad: de 1c a 6c la aprobación mediana baja de 75 a 8 días y P(fondeado ≤ 22 d) sube de 3 a 69 %, mientras la aprobación por intento cae de 100 a 49 % y las evals perdidas suben de 0 a 0,34 por mes y asiento. El ingreso del asiento sube con k porque la cuenta pasa más meses fondeada; las fondeadas perdidas por mes casi no dependen de k (0,05-0,12), porque la fondeada es la misma. (2) Con la función objetivo tal como está escrita, las condiciones M3 y M4 (evals) y M5 (días) son incompatibles bajo las reglas de Lucid: la única eval que cumple M3 y M4 (1c) falla M5 por 50 días y cuesta la mitad del ingreso. No hay k que cumpla las 6; el máximo es 5 de 6 (1c, edge completo, 2020-22) y no se sostiene en 2023-26 (2 de 6). (3) El 5c es un empate técnico con el 6c en ingreso y riesgo, con un 20 % menos de evals perdidas y 5 puntos más de aprobación; pierde por la regla porque la mediana de días llega a 10-11 (umbral 10). Si Federico cambia la definición de aprobación a P(fondeado ≤ 22 d) o relaja M5, el 5c es el primer candidato a re-evaluar; con la regla actual el 6c sigue.

## Qué sigue

El tamaño de la eval no mueve el plan dentro de la función objetivo. Siguientes ideas de 5B (una por sesión, contra la base, pareadas): umbral y momento del retiro de la 150K ($6.000 con 5 días ≥ $250 hoy), escalonado de las compras entre asientos, regla de pausa del runbook dentro de la simulación. Decisión para Federico: si M3 (< 0,12 evals perdidas por mes entre 8 cuentas = 1,4 por año) y M4 (≥ 65 % por intento) se mantienen como están, ninguna geometría de eval de Lucid las alcanza sin romper M5 e ingreso; conviene fijar qué condición cede.

Archivos: `research/mine/exp03_eval_size.py`, `exp03_eval_size.json`, `exp03_eval_size.md`; plan `docs/PLAN_2026-10-27_exp03.md`.
