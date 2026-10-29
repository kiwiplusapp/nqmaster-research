# Experimento 10 (frente 5D): estrés de la campaña por costos de ejecución y por edge de régimen — 2026-10-29

**Resultado: con el edge completo el plan aguanta al menos +3 ticks por lado de costo extra sin romper el ingreso (M1) en el bootstrap; con −35 % de edge no tiene margen; y sobre historia contigua de 2023-26 el p10 ya cae debajo de $1.600 con +1 tick.** Cada tick extra por lado ($1 por contrato ida y vuelta, sobre los 2 ticks que ya llevan los caminos) cuesta ~$1.162 / $1.122 por mes de mediana con el edge completo (7-8 %). Con −35 %, en estos caminos el p10 ya está en $1.475 / $1.504 sin costo extra (en los caminos de la base daba $2.464 / $1.801): **la condición de p10 con −35 % depende de qué caminos se sorteen, no es robusta.** Con el edge de 2015-19 (32 % del actual por trade) la mediana del plan es +$3.290 / +$3.243 por mes, el p10 −$1.986 / −$2.216 y 26-27 % de los años son negativos. **Sin edge, la media positiva del plan (+$133 / +$46 por mes) depende de los costos: con 1 tick más por lado ya es −$302 / −$977.** Unidad: plan completo (5 Lucid 150K 6c/3c + 3 MFFU 1x8); 1.000 caminos bootstrap (los de "completo" de la base, los mismos en todas las celdas) y 84 / 132 planes contiguos; T1 = arranques 2020-22, T2 = 2023-26; fees con cupón.

## Qué se corrió

`research/mine/exp10_stress.py`: a cada mezcla de la campaña se le resta x dólares por contrato-trade y por día (x ticks extra por lado; `cc` = contratos-trade del día de la mezcla), con el recorte de edge calculado sobre la mezcla sin el costo extra (costo y edge independientes); plan y asiento Lucid sobre los mismos caminos para todas las celdas. Autotest: sin costo extra y con el edge completo reproduce `integ_port.json` al dólar. Plan en `docs/PLAN_2026-10-29_exp10.md`. Corrida: 3 min.

## Resultado (T1 / T2)

| Edge | Ticks extra por lado | Mediana $/mes | Media | p10 | P(año < 0) % | Ventanas 60 d neg. % | P(fondeado ≤ 22 d) % | Cumple D1 (de 5) | Contiguo: mediana / p10 / ventanas neg. % |
|---|---|---|---|---|---|---|---|---|---|
| Edge completo | +0 | 16.173 / 14.689 | 16.283 / 14.679 | 9.243 / 7.041 | 0,0 / 0,6 | 4,5 / 8,5 | 69 / 71 | 5 / 5 | 12.685 / 18.522 · 6.925 / 2.101 · 12 / 22 |
|  | +1 | 15.075 / 13.626 | 15.119 / 13.513 | 8.080 / 5.839 | 0,1 / 0,8 | 6,0 / 10,8 | 66 / 67 | 5 / 4 | 12.272 / 17.234 · 6.451 / 1.071 · 13 / 23 |
|  | +2 | 14.026 / 12.413 | 13.923 / 12.283 | 6.811 / 4.801 | 0,2 / 1,3 | 8,1 / 13,3 | 65 / 64 | 4 / 3 | 12.091 / 15.900 · 5.500 / 1.078 · 18 / 26 |
|  | +3 | 12.687 / 11.325 | 12.481 / 11.228 | 5.295 / 4.014 | 0,7 / 2,7 | 11,5 / 15,9 | 63 / 63 | 3 / 3 | 9.885 / 12.282 · 3.888 / 582 · 21 / 26 |
| −35 % | +0 | 8.811 / 8.047 | 9.064 / 8.439 | 1.475 / 1.504 | 4,9 / 6,4 | 23,2 / 23,7 | 54 / 51 | 2 / 2 | 6.163 / 11.285 · 894 / −1.502 · 31 / 27 |
|  | +1 | 7.296 / 6.812 | 7.827 / 7.344 | 491 / 347 | 7,9 / 8,7 | 27,7 / 27,9 | 49 / 49 | 2 / 2 | 4.658 / 8.269 · −1.689 / −2.148 · 42 / 36 |
|  | +2 | 6.296 / 5.834 | 6.797 / 6.259 | −247 / −598 | 11,3 / 12,5 | 32,1 / 32,3 | 45 / 47 | 2 / 2 | 3.894 / 7.751 · −2.093 / −2.370 · 50 / 36 |
|  | +3 | 5.601 / 5.259 | 5.989 / 5.486 | −715 / −1.136 | 14,1 / 16,0 | 35,3 / 35,2 | 43 / 46 | 2 / 2 | 2.094 / 6.994 · −2.216 / −2.532 · 52 / 40 |
| Edge de 2015-19 (−68 %) | +0 | 3.290 / 3.243 | 3.690 / 3.477 | −1.986 / −2.216 | 25,7 / 27,0 | 45,7 / 44,7 | 40 / 41 | 2 / 2 | 1.208 / 4.314 · −2.649 / −3.440 · 53 / 52 |
|  | +1 | 2.390 / 2.316 | 3.020 / 2.758 | −2.322 / −2.683 | 31,1 / 32,6 | 49,0 / 48,6 | 36 / 38 | 1 / 1 | 706 / 3.049 · −2.997 / −3.569 · 53 / 62 |
|  | +2 | 1.555 / 1.473 | 2.197 / 2.068 | −2.740 / −3.020 | 37,9 / 37,7 | 52,9 / 52,2 | 33 / 36 | 1 / 1 | −475 / 2.606 · −3.165 / −4.556 · 55 / 71 |
|  | +3 | 616 / 717 | 1.329 / 1.393 | −3.131 / −3.413 | 44,9 / 43,5 | 58,1 / 55,8 | 31 / 34 | 1 / 1 | −3.152 / 1.504 · −3.537 / −4.545 · 77 / 71 |
| Edge cero | +0 | −656 / −801 | 133 / 46 | −3.797 / −4.198 | 56,8 / 57,8 | 63,9 / 63,7 | 29 / 31 | 1 / 1 | −3.583 / 512 · −4.212 / −5.078 · 79 / 73 |
|  | +1 | −1.174 / −2.067 | −302 / −977 | −3.931 / −4.704 | 63,2 / 66,9 | 66,5 / 70,9 | 27 / 29 | 1 / 1 | −3.637 / −1.445 · −4.231 / −5.181 · 79 / 83 |
|  | +2 | −1.669 / −2.515 | −800 / −1.430 | −4.173 / −4.927 | 69,1 / 71,1 | 69,5 / 73,2 | 27 / 27 | 1 / 1 | −3.799 / −1.659 · −4.447 / −5.484 · 79 / 83 |
|  | +3 | −2.034 / −3.012 | −1.220 / −1.993 | −4.385 / −5.255 | 73,0 / 77,1 | 71,9 / 75,4 | 23 / 23 | 1 / 1 | −3.914 / −1.846 · −4.592 / −5.573 · 78 / 83 |

## Salidas operativas (pre-registradas)

- **Presupuesto de costos con el edge completo: al menos +3 ticks por lado** (el máximo de la grilla) con M1 en T1 y T2 en el bootstrap. Sobre historia contigua de 2023-26: 0 (el p10 contiguo pasa de $2.101 a $1.071 con +1 tick).
- **Presupuesto de costos con −35 %: ninguno** (M1 falla ya sin costo extra en estos caminos).
- **Costo extra con el que la mediana del plan llega a 0:** más de +3 ticks con el edge completo, con −35 % y con el edge de 2015-19 (la mediana con +3 ticks sigue en $616 / $717); 0 sin edge.
- **Umbral para cuando haya fills reales (H5):** las cifras de campaña cargan $3,90 por contrato ida y vuelta ($1,90 de comisión + 4 ticks). En Lucid (comisión de $1,00 ida y vuelta, `.claude/skills/prop-rules/SKILL.md`) eso equivale a ~2,9 ticks de slippage por lado. Como con −35 % no hay margen, **si el costo real medido por contrato ida y vuelta supera $3,90 la campaña se recalcula con el costo medido y no se compran cuentas nuevas hasta revisarla**; con el edge completo el plan seguiría cumpliendo M1 hasta ~$6,90.

## Qué cambia

- **Runbook:** el umbral de costo de arriba se agrega a la sección de la campaña.
- **Decisión D6 (sin pausa automática):** se mantiene, pero su fundamento ("sin edge la campaña tiene media positiva") vale solo con los costos actuales; con 1 tick más por lado la media sin edge es negativa. Queda atada al umbral: si los costos reales superan lo supuesto, D6 se re-evalúa con el costo medido.
- **Lectura de la función objetivo:** con −35 % la condición de p10 está en el borde (cambia de cumplir a no cumplir según los caminos sorteados): no se puede dar por cumplida.

Archivos: `research/mine/exp10_stress.py`, `exp10_stress.json`; plan `docs/PLAN_2026-10-29_exp10.md`.
