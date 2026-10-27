# Experimento 05 (frente 5B): presupuesto por plaza (regla 6 del runbook) dentro de la simulación — 2026-10-27

**Veredicto: la regla pre-registrada deja la regla 6 como está, y la medición muestra que, leída como está escrita, no actúa.** Con revisión trimestral (la plaza deja de comprar evals cuando su neto desde la última revisión cae debajo de −$4.000 en Lucid 150K o −$1.500 en MFFU, y vuelve a comprar en la revisión siguiente) **ninguna plaza llega al presupuesto dentro de un trimestre, ni siquiera sin edge: 0 días de pausa en las 6 celdas y el plan es idéntico, camino por camino, al plan sin presupuesto.** La protección que el runbook le atribuye ("sin edge acota el p10 a −$2.095 por mes") es la del **modo anual** (la plaza no vuelve a comprar en los 12 meses, como `integ_budget.py`): sin edge sube el p10 del plan de $-3.712 / $-4.182 a $-2.095 / $-2.095 por mes, pero con −35 % en 2023-26 baja el p10 de $1.801 a $1.452 (rompe el umbral de $1.600) y sube P(año negativo) de 4,2 a 6,0 %. Por eso el modo anual gana la elección en 2020-22 (empate en condiciones, 7 de 12; mejor p10 sin edge) y **no confirma en 2023-26**. Ningún presupuesto mueve las condiciones de la función objetivo con el edge completo. Unidad: plan completo (5 Lucid 150K 6c/3c + 3 MFFU 1x8), cupón; caminos NQ real 2020-02-26 → 2026-10-08; T1 = arranques 2020-22 (elige), T2 = 2023-26 (confirma); 1.000 caminos bootstrap pareados por celda (los de la base) y 84 / 132 planes sobre historia contigua; costos $1,90 + 2 ticks por lado, fees con cupón.

## Qué se corrió

`research/mine/exp05_budget.py`: `seat_flow_b` = `objective.seat_flow` + el presupuesto: antes de cada compra de eval la plaza suma su caja ya cobrada (retiros − fees) desde la última revisión (cada 63 días hábiles desde el inicio del camino, común a todas las plazas) y, si es menor que −presupuesto, espera a la revisión siguiente; en modo anual no hay revisiones. Una fondeada que ya opera no se toca. Autotest: con presupuesto infinito reproduce `objective.run_seat` en 3.600 asientos (flujo, caja + saldo y registro de evals idénticos). Seis candidatos, tres edges, la regla escrita en `docs/PLAN_2026-10-27_exp05.md` (edge del chequeo contiguo fijado: completo y −35 %). Corrida: 3 min.

## Plan completo (8 cuentas), bootstrap, T1 / T2

| Presupuesto por plaza (Lucid / MFFU) | Mediana $/mes | p10 | P(año < 0) % | Ventanas 60 d neg. % | Evals / año | Evals perdidas / mes | Cumple (de 6) · M1 M1 M2 M3 M4 M5 | Días en pausa por año (8 plazas) |
|---|---|---|---|---|---|---|---|---|
| **Edge completo** | | | | | | | | |
| sin presupuesto (base) | 16.173 / 14.689 | 9.243 / 7.041 | 0,0 / 0,6 | 4,5 / 8,5 | 47 / 70 | 1,89 / 3,28 | 4 / 4 ✓✓✓✗✗✓ ✓✓✓✗✗✓ | 0 / 0 |
| −1.500 / −600 trimestral | 16.173 / 14.663 | 9.172 / 6.994 | 0,0 / 0,8 | 4,5 / 8,8 | 47 / 70 | 1,89 / 3,27 | 4 / 4 ✓✓✓✗✗✓ ✓✓✓✗✗✓ | 1 / 11 |
| −2.500 / −900 trimestral | 16.173 / 14.689 | 9.243 / 7.040 | 0,0 / 0,6 | 4,5 / 8,5 | 47 / 70 | 1,89 / 3,29 | 4 / 4 ✓✓✓✗✗✓ ✓✓✓✗✗✓ | 0 / 0 |
| **−4.000 / −1.500 trimestral (regla 6)** | 16.173 / 14.689 | 9.243 / 7.041 | 0,0 / 0,6 | 4,5 / 8,5 | 47 / 70 | 1,89 / 3,28 | 4 / 4 ✓✓✓✗✗✓ ✓✓✓✗✗✓ | 0 / 0 |
| −6.000 / −2.500 trimestral | 16.173 / 14.689 | 9.243 / 7.041 | 0,0 / 0,6 | 4,5 / 8,5 | 47 / 70 | 1,89 / 3,28 | 4 / 4 ✓✓✓✗✗✓ ✓✓✓✗✗✓ | 0 / 0 |
| −4.000 / −1.500 anual | 16.173 / 14.689 | 9.243 / 7.040 | 0,0 / 0,9 | 4,5 / 8,5 | 47 / 70 | 1,89 / 3,28 | 4 / 4 ✓✓✓✗✗✓ ✓✓✓✗✗✓ | 0 / 2 |
| **−35 %** | | | | | | | | |
| sin presupuesto (base) | 8.824 / 8.418 | 2.464 / 1.801 | 3,9 / 4,2 | 22,3 / 22,6 | 75 / 100 | 4,00 / 5,72 | 3 / 3 ✓✓✗✗✗✓ ✓✓✗✗✗✓ | 0 / 0 |
| −1.500 / −600 trimestral | 8.725 / 8.296 | 2.315 / 1.472 | 4,0 / 5,7 | 22,5 / 24,2 | 74 / 97 | 3,99 / 5,56 | 3 / 2 ✓✓✗✗✗✓ ✓✗✗✗✗✓ | 12 / 48 |
| −2.500 / −900 trimestral | 8.824 / 8.418 | 2.464 / 1.794 | 3,9 / 4,2 | 22,3 / 22,6 | 75 / 100 | 4,00 / 5,72 | 3 / 3 ✓✓✗✗✗✓ ✓✓✗✗✗✓ | 0 / 1 |
| **−4.000 / −1.500 trimestral (regla 6)** | 8.824 / 8.418 | 2.464 / 1.801 | 3,9 / 4,2 | 22,3 / 22,6 | 75 / 100 | 4,00 / 5,72 | 3 / 3 ✓✓✗✗✗✓ ✓✓✗✗✗✓ | 0 / 0 |
| −6.000 / −2.500 trimestral | 8.824 / 8.418 | 2.464 / 1.801 | 3,9 / 4,2 | 22,3 / 22,6 | 75 / 100 | 4,00 / 5,72 | 3 / 3 ✓✓✗✗✗✓ ✓✓✗✗✗✓ | 0 / 0 |
| −4.000 / −1.500 anual | 8.807 / 8.413 | 2.330 / 1.452 | 4,4 / 6,0 | 22,3 / 23,0 | 74 / 98 | 3,98 / 5,60 | 3 / 2 ✓✓✗✗✗✓ ✓✗✗✗✗✓ | 6 / 27 |
| **Edge cero** | | | | | | | | |
| sin presupuesto (base) | -789 / -566 | -3.712 / -4.182 | 56,4 / 55,3 | 63,4 / 63,1 | 178 / 202 | 12,42 / 14,25 | 1 / 1 ✗✗✗✗✗✓ ✗✗✗✗✗✓ | 0 / 0 |
| −1.500 / −600 trimestral | -1.064 / -1.290 | -3.123 / -3.176 | 60,6 / 62,7 | 68,5 / 70,3 | 157 / 166 | 10,93 / 11,63 | 1 / 1 ✗✗✗✗✗✓ ✗✗✗✗✗✓ | 197 / 297 |
| −2.500 / −900 trimestral | -799 / -637 | -3.695 / -4.128 | 56,6 / 55,4 | 63,7 / 63,8 | 177 / 199 | 12,36 / 14,03 | 1 / 1 ✗✗✗✗✗✓ ✗✗✗✗✗✓ | 8 / 26 |
| **−4.000 / −1.500 trimestral (regla 6)** | -789 / -566 | -3.712 / -4.182 | 56,4 / 55,3 | 63,4 / 63,1 | 178 / 202 | 12,42 / 14,25 | 1 / 1 ✗✗✗✗✗✓ ✗✗✗✗✗✓ | 0 / 0 |
| −6.000 / −2.500 trimestral | -789 / -566 | -3.712 / -4.182 | 56,4 / 55,3 | 63,4 / 63,1 | 178 / 202 | 12,42 / 14,25 | 1 / 1 ✗✗✗✗✗✓ ✗✗✗✗✗✓ | 0 / 0 |
| −4.000 / −1.500 anual | -1.384 / -1.507 | -2.095 / -2.095 | 63,3 / 64,4 | 63,6 / 62,9 | 141 / 150 | 9,92 / 10,63 | 1 / 1 ✗✗✗✗✗✓ ✗✗✗✗✗✓ | 348 / 428 |

Puntaje de la regla en T1: todos 7 de 12. Desempate (p10 sin edge al menos $300 mejor que la regla 6 y P(perder > 5 %) con −35 % ≤ 0,20): pasan −1.500 / −600 trimestral (p10 sin edge $-3.123) y −4.000 / −1.500 anual ($-2.095); gana el anual. Confirmación en T2: pierde la condición de p10 con −35 % (1.452 < 1.600), con ganancia pareada de mediana 0 (P(ganar) 0,02, P(perder > 5 %) 0,05) → no confirma.

## Plan completo, historia contigua (84 / 132 planes)

| Presupuesto | Mediana $/mes | p10 | P(año < 0) % | Ventanas 60 d neg. % | Evals / año | Evals perdidas / mes | Cumple |
|---|---|---|---|---|---|---|---|
| **Edge completo** | | | | | | | |
| sin presupuesto (base) | 12.685 / 18.522 | 6.925 / 2.101 | 0,0 / 5,3 | 12,5 / 22,4 | 54 / 72 | 2,62 / 3,48 | 3 / 3 ✓✓✗✗✗✓ ✓✓✗✗✗✓ |
| −1.500 / −600 trimestral | 12.685 / 18.522 | 6.925 / 2.101 | 0,0 / 5,3 | 12,5 / 22,6 | 54 / 72 | 2,62 / 3,45 | 3 / 3 ✓✓✗✗✗✓ ✓✓✗✗✗✓ |
| −2.500 / −900 trimestral | 12.685 / 18.522 | 6.925 / 2.101 | 0,0 / 5,3 | 12,5 / 22,4 | 54 / 72 | 2,62 / 3,48 | 3 / 3 ✓✓✗✗✗✓ ✓✓✗✗✗✓ |
| **−4.000 / −1.500 trimestral (regla 6)** | 12.685 / 18.522 | 6.925 / 2.101 | 0,0 / 5,3 | 12,5 / 22,4 | 54 / 72 | 2,62 / 3,48 | 3 / 3 ✓✓✗✗✗✓ ✓✓✗✗✗✓ |
| −6.000 / −2.500 trimestral | 12.685 / 18.522 | 6.925 / 2.101 | 0,0 / 5,3 | 12,5 / 22,4 | 54 / 72 | 2,62 / 3,48 | 3 / 3 ✓✓✗✗✗✓ ✓✓✗✗✗✓ |
| −4.000 / −1.500 anual | 12.685 / 18.522 | 6.925 / 1.651 | 0,0 / 8,3 | 12,5 / 22,5 | 54 / 72 | 2,62 / 3,48 | 3 / 3 ✓✓✗✗✗✓ ✓✓✗✗✗✓ |
| **−35 %** | | | | | | | |
| sin presupuesto (base) | 6.163 / 11.285 | 894 / -1.502 | 0,0 / 14,4 | 30,8 / 27,5 | 82 / 110 | 5,03 / 7,20 | 2 / 2 ✓✗✗✗✗✓ ✓✗✗✗✗✓ |
| −1.500 / −600 trimestral | 6.051 / 11.231 | 1.084 / -1.143 | 4,8 / 18,9 | 31,7 / 29,8 | 81 / 104 | 4,94 / 6,74 | 1 / 2 ✓✗✗✗✗✗ ✓✗✗✗✗✓ |
| −2.500 / −900 trimestral | 6.163 / 11.285 | 894 / -1.506 | 0,0 / 14,4 | 30,8 / 27,5 | 82 / 110 | 5,03 / 7,20 | 2 / 2 ✓✗✗✗✗✓ ✓✗✗✗✗✓ |
| **−4.000 / −1.500 trimestral (regla 6)** | 6.163 / 11.285 | 894 / -1.502 | 0,0 / 14,4 | 30,8 / 27,5 | 82 / 110 | 5,03 / 7,20 | 2 / 2 ✓✗✗✗✗✓ ✓✗✗✗✗✓ |
| −6.000 / −2.500 trimestral | 6.163 / 11.285 | 894 / -1.502 | 0,0 / 14,4 | 30,8 / 27,5 | 82 / 110 | 5,03 / 7,20 | 2 / 2 ✓✗✗✗✗✓ ✓✗✗✗✗✓ |
| −4.000 / −1.500 anual | 6.163 / 11.285 | 894 / -2.054 | 0,0 / 21,2 | 30,8 / 29,1 | 82 / 102 | 5,03 / 6,62 | 2 / 2 ✓✗✗✗✗✓ ✓✗✗✗✗✓ |
| **Edge cero** | | | | | | | |
| sin presupuesto (base) | -3.583 / 512 | -4.212 / -5.078 | 59,5 / 49,2 | 79,3 / 73,2 | 193 / 216 | 13,68 / 16,01 | 1 / 0 ✗✗✗✗✗✓ ✗✗✗✗✗✗ |
| −1.500 / −600 trimestral | -2.843 / 401 | -3.212 / -3.303 | 59,5 / 49,2 | 79,4 / 73,7 | 162 / 163 | 11,43 / 11,96 | 1 / 0 ✗✗✗✗✗✓ ✗✗✗✗✗✗ |
| −2.500 / −900 trimestral | -3.554 / 536 | -4.197 / -4.860 | 59,5 / 48,5 | 79,3 / 73,2 | 192 / 212 | 13,65 / 15,71 | 1 / 0 ✗✗✗✗✗✓ ✗✗✗✗✗✗ |
| **−4.000 / −1.500 trimestral (regla 6)** | -3.583 / 512 | -4.212 / -5.078 | 59,5 / 49,2 | 79,3 / 73,2 | 193 / 216 | 13,68 / 16,01 | 1 / 0 ✗✗✗✗✗✓ ✗✗✗✗✗✗ |
| −6.000 / −2.500 trimestral | -3.583 / 512 | -4.212 / -5.078 | 59,5 / 49,2 | 79,3 / 73,2 | 193 / 216 | 13,68 / 16,01 | 1 / 0 ✗✗✗✗✗✓ ✗✗✗✗✗✗ |
| −4.000 / −1.500 anual | -2.095 / -1.283 | -2.095 / -2.095 | 70,2 / 59,8 | 70,0 / 65,0 | 126 / 134 | 9,07 / 9,99 | 1 / 0 ✗✗✗✗✗✓ ✗✗✗✗✗✗ |

Sobre historia contigua se repite el patrón: la regla 6 trimestral es idéntica a no tener presupuesto en las 6 celdas; el modo anual acota el caso sin edge (p10 −$2.095 en los dos períodos, contra $-4.212 / $-5.078) y con −35 % en 2023-26 baja el p10 de $-1.502 a $-2.054 y sube P(año negativo) de 14,4 a 21,2 %; el −1.500 / −600 trimestral acota menos el caso sin edge (p10 $-3.212 / $-3.303) y con −35 % en 2020-22 pierde una condición (1 contra 2). En el modo anual las ventanas en 0 suben a 12-13 % sin edge (plazas paradas): la mejora de ventanas negativas sin edge (70 / 65 % contra 79 / 73 %) es caja que deja de salir, no edge.

**Lectura.** (1) La regla 6 dice "hasta la revisión trimestral". Si la revisión reinicia la cuenta, un presupuesto de −$4.000 por trimestre no se alcanza: una plaza de Lucid 150K sin edge compra ~29-34 evals por año (~7-9 por trimestre, $1.500-1.900 de fees) y las MFFU ~10. Así escrita, la regla no protege nada. (2) Si la plaza no vuelve a comprar en el año (modo anual, la lectura con la que se midió en la ronda 5), la regla corta el peor caso (sin edge, p10 ~−$2.100 por mes en vez de −$3.700 / −$4.200) a costa de cortar plazas que se habrían recuperado con −35 %: en 2023-26 el p10 del plan cae ~$350 por mes y rompe el umbral de $1.600. (3) Un presupuesto trimestral más chico (−1.500 / −600) es un punto intermedio que tampoco confirma (pierde condiciones con −35 %). (4) Ninguna variante toca el edge completo: con el edge completo ninguna plaza se acerca a ningún presupuesto.

## Qué sigue

La regla 6 queda como está por la regla pre-registrada, pero su texto y la cifra que el runbook le atribuye no son coherentes: **decisión de Federico** entre (a) dejarla trimestral sabiendo que no actúa (en la práctica, sin presupuesto), (b) pasarla a anual (protege el caso sin edge, cuesta p10 con −35 % en 2023-26) o (c) sacarla y apoyarse en las reglas de pausa del sistema (puntos 1-4 del runbook), que miran el P&L por contrato y no las fees. Mientras tanto el runbook queda anotado con esta medición. El frente 5B cerró las cuatro palancas de política de la campaña que estaban en el plan (tamaño de eval, retiro, presupuesto; el escalonado de compras queda sin probar) sin mover la función objetivo; las dos condiciones que fallan dependen de las evals de las firmas.

Archivos: `research/mine/exp05_budget.py`, `exp05_budget.json`, `exp05_budget.md`; plan `docs/PLAN_2026-10-27_exp05.md`.
