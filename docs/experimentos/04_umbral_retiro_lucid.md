# Experimento 04 (frente 5B): umbral de retiro de la Lucid Flex 150K fondeada medido con la función objetivo — 2026-10-27

**Veredicto: sin cambio. La regla pre-registrada mantiene el retiro a $6.000.** Los siete umbrales (de $4.600 a $12.000; todo lo demás igual) cumplen las mismas 7 de 12 condiciones en 2020-22 sumando edge completo y −35 %, y el desempate (mediana $/mes con −35 %) lo gana el $6.000 ($8.824; $5.000 $8.786, $4.600 $8.691, $12.000 $7.201). **El umbral de retiro no mueve ninguna condición de la función objetivo:** las ventanas negativas de 60 días con −35 % quedan entre 20 y 28 % (umbral 10 %) y las evals perdidas entre 1,5 y 3,5 por mes (umbral 0,12) en todos los candidatos. El trade-off es monótono: cobrar antes ($4.600) baja las ventanas negativas ~2 puntos (20,0 / 20,8 contra 22,3 / 22,6 % con −35 %) pero quema más fondeadas (0,88 / 1,47 contra 0,65 / 1,26 por mes) y compra más evals; cobrar más tarde ($10.000-12.000) quema la mitad de fondeadas pero pierde 7-14 % del ingreso con P(perder > 5 %) 0,56-0,79. Entre $4.600 y $7.000 el ingreso es el mismo dentro del ruido (−0,6 a +0,0 %, P(ganar) 0,21-0,44). Unidad: plan completo (5 Lucid 150K 6c/3c con umbral X + 3 MFFU 1x8 sin cambios), cupón; caminos NQ real 2020-02-26 → 2026-10-08; T1 = arranques 2020-22 (elige), T2 = 2023-26 (confirma); 1.000 caminos bootstrap pareados por celda (mismos caminos y semillas que la base; el $6.000 reproduce la base) y 84 / 132 planes sobre historia contigua; costos $1,90 + 2 ticks por lado y fees con cupón. Nada de la estrategia cambia.

## Qué se corrió

`research/mine/exp04_payout_x.py`: umbral X ∈ {4.600, 5.000, 6.000, 7.000, 8.000, 10.000, 12.000} como único parámetro de la fondeada (la firma sigue pidiendo 5 días ≥ $250 y paga min($3.000, 50 % de la ganancia); con X ≥ 4.600 el piso ya está trabado en +$100 al primer retiro en todos los candidatos), asiento y plan sobre los caminos de la base, ganancia pareada, historia contigua y la regla escrita en `docs/PLAN_2026-10-27_exp04.md` (si empata en condiciones con $6.000 tiene que ganarle con P ≥ 0,80). Corrida: 1 min.

## Plan completo (8 cuentas), bootstrap, T1 / T2

| Umbral X | Mediana $/mes | p10 | Ventanas 60 d negativas % | Evals perdidas / mes | Fondeadas perdidas / mes | Cumple (de 6) · M1 M1 M2 M3 M4 M5 | Ingreso pareado vs $6.000 |
|---|---|---|---|---|---|---|---|
| **Edge completo** | | | | | | | |
| 4.600 | 16.189 / 14.699 | 8.985 / 7.202 | 4,1 / 7,6 | 2,08 / 3,48 | 0,88 / 1,47 | **4 / 4** ✓✓✓✗✗✓ ✓✓✓✗✗✓ | -0,5 % (P ganar 0,43) / -0,4 % (0,44) |
| 5.000 | 16.191 / 14.661 | 9.013 / 7.206 | 4,3 / 8,0 | 2,05 / 3,43 | 0,83 / 1,42 | **4 / 4** ✓✓✓✗✗✓ ✓✓✓✗✗✓ | -0,3 % (P ganar 0,43) / -0,2 % (0,43) |
| 6.000 | 16.173 / 14.689 | 9.243 / 7.041 | 4,5 / 8,5 | 1,89 / 3,28 | 0,65 / 1,26 | **4 / 4** ✓✓✓✗✗✓ ✓✓✓✗✗✓ | incumbente |
| 7.000 | 15.699 / 14.462 | 9.267 / 6.815 | 4,4 / 9,2 | 1,77 / 3,10 | 0,50 / 1,15 | **4 / 4** ✓✓✓✗✗✓ ✓✓✓✗✗✓ | -0,6 % (P ganar 0,28) / -0,2 % (0,24) |
| 8.000 | 15.367 / 14.243 | 8.968 / 6.676 | 4,5 / 9,6 | 1,70 / 3,00 | 0,42 / 1,04 | **4 / 4** ✓✓✓✗✗✓ ✓✓✓✗✗✓ | -2,8 % (P ganar 0,25) / -3,2 % (0,23) |
| 10.000 | 14.829 / 13.840 | 8.320 / 6.159 | 4,8 / 10,6 | 1,59 / 2,77 | 0,34 / 0,90 | **4 / 3** ✓✓✓✗✗✓ ✓✓✗✗✗✓ | -6,9 % (P ganar 0,14) / -7,6 % (0,16) |
| 12.000 | 14.599 / 13.455 | 7.613 / 6.027 | 5,4 / 11,0 | 1,51 / 2,60 | 0,33 / 0,81 | **4 / 3** ✓✓✓✗✗✓ ✓✓✗✗✗✓ | -11,1 % (P ganar 0,07) / -11,8 % (0,12) |
| **−35 % de edge** | | | | | | | |
| 4.600 | 8.691 / 8.386 | 2.258 / 1.831 | 20,0 / 20,8 | 4,32 / 6,05 | 1,32 / 1,72 | **3 / 3** ✓✓✗✗✗✓ ✓✓✗✗✗✓ | +0,0 % (P ganar 0,43) / -0,5 % (0,38) |
| 5.000 | 8.786 / 8.466 | 2.182 / 1.849 | 20,8 / 21,4 | 4,26 / 5,97 | 1,30 / 1,69 | **3 / 3** ✓✓✗✗✗✓ ✓✓✗✗✗✓ | +0,0 % (P ganar 0,39) / +0,0 % (0,35) |
| 6.000 | 8.824 / 8.418 | 2.464 / 1.801 | 22,3 / 22,6 | 4,00 / 5,72 | 1,17 / 1,59 | **3 / 3** ✓✓✗✗✗✓ ✓✓✗✗✗✓ | incumbente |
| 7.000 | 8.672 / 8.313 | 2.500 / 1.820 | 22,8 / 23,9 | 3,79 / 5,54 | 1,06 / 1,48 | **3 / 3** ✓✓✗✗✗✓ ✓✓✗✗✗✓ | +0,0 % (P ganar 0,21) / +0,0 % (0,22) |
| 8.000 | 8.449 / 7.924 | 2.465 / 1.449 | 22,9 / 25,7 | 3,61 / 5,29 | 0,97 / 1,39 | **3 / 2** ✓✓✗✗✗✓ ✓✗✗✗✗✓ | -2,1 % (P ganar 0,25) / -3,6 % (0,24) |
| 10.000 | 7.708 / 7.421 | 2.544 / 1.221 | 23,6 / 27,2 | 3,32 / 4,97 | 0,83 / 1,26 | **3 / 2** ✓✓✗✗✗✓ ✓✗✗✗✗✓ | -7,3 % (P ganar 0,23) / -10,5 % (0,23) |
| 12.000 | 7.201 / 6.877 | 1.915 / 901 | 24,5 / 27,9 | 3,20 / 4,71 | 0,76 / 1,16 | **3 / 2** ✓✓✗✗✗✓ ✓✗✗✗✗✓ | -11,2 % (P ganar 0,17) / -13,9 % (0,20) |

Aprobación (≈ 51 / 43 % con edge completo) y días para aprobar (9 / 8) no dependen del umbral: la eval es la misma. Puntaje de la regla en T1: $4.600 7 · $5.000 7 · $6.000 7 · $7.000 7 · $8.000 7 · $10.000 7 · $12.000 7 (todos empatan; decide la mediana con −35 %).

## Plan completo, historia contigua (84 / 132 planes con inicio real cada 5 días)

| Umbral X | Mediana $/mes | p10 | Ventanas 60 d negativas % | Evals perdidas / mes | Fondeadas perdidas / mes | Cumple |
|---|---|---|---|---|---|---|
| **Edge completo** | | | | | | |
| 4.600 | 13.020 / 16.603 | 7.586 / 1.529 | 9,0 / 21,5 | 2,59 / 3,64 | 0,53 / 1,53 | 4 / 2 |
| 5.000 | 11.855 / 17.163 | 7.268 / 1.615 | 10,0 / 22,0 | 2,54 / 3,67 | 0,72 / 1,31 | 3 / 3 |
| 6.000 | 12.685 / 18.522 | 6.925 / 2.101 | 12,5 / 22,4 | 2,62 / 3,48 | 0,47 / 1,18 | 3 / 3 |
| 7.000 | 12.526 / 17.865 | 6.385 / 1.233 | 12,5 / 23,8 | 2,76 / 3,36 | 0,27 / 1,14 | 3 / 2 |
| 8.000 | 12.570 / 18.050 | 6.329 / 985 | 12,3 / 23,8 | 2,73 / 3,44 | 0,24 / 1,07 | 3 / 2 |
| 10.000 | 12.383 / 17.725 | 6.023 / 189 | 12,8 / 27,4 | 1,73 / 2,99 | 0,17 / 0,77 | 3 / 1 |
| 12.000 | 10.790 / 16.343 | 5.647 / -124 | 11,6 / 27,6 | 1,75 / 3,12 | 0,12 / 0,75 | 3 / 1 |
| **−35 %** | | | | | | |
| 4.600 | 6.159 / 11.000 | 703 / -1.723 | 31,9 / 28,1 | 5,28 / 6,83 | 0,99 / 1,04 | 2 / 2 |
| 5.000 | 6.161 / 11.282 | 757 / -1.437 | 33,0 / 27,5 | 5,25 / 6,70 | 0,98 / 1,00 | 2 / 2 |
| 6.000 | 6.163 / 11.285 | 894 / -1.502 | 30,8 / 27,5 | 5,03 / 7,20 | 0,77 / 0,89 | 2 / 2 |
| 7.000 | 5.852 / 11.231 | 894 / -1.742 | 32,1 / 27,4 | 4,87 / 7,00 | 0,75 / 0,88 | 2 / 2 |
| 8.000 | 5.852 / 9.592 | 732 / -1.954 | 32,9 / 32,5 | 4,77 / 6,47 | 0,72 / 0,75 | 2 / 2 |
| 10.000 | 4.867 / 9.494 | -153 / -2.241 | 37,9 / 34,6 | 4,13 / 5,65 | 0,56 / 0,73 | 1 / 2 |
| 12.000 | 4.815 / 9.813 | -1.176 / -2.522 | 42,2 / 35,9 | 3,73 / 5,41 | 0,47 / 0,62 | 1 / 2 |

Sobre historia contigua el $4.600 es el único que baja las ventanas negativas del plan de 2020-22 bajo el 10 % (9,0 contra 12,5 %), pero en 2023-26 su p10 cae a $1.529 (umbral 1.600) y cumple 2 contra 3; los umbrales altos pierden p10 y ventanas en 2023-26. Ningún candidato domina al $6.000 en los dos períodos.

## Asiento Lucid 150K solo (edge completo, bootstrap, T1 / T2)

| Umbral X | Mediana $/mes | p10 | Ventanas 60 d neg. %, caja | Ídem caja + saldo | Evals perdidas / mes | Fondeadas perdidas / mes | Retiros / año |
|---|---|---|---|---|---|---|---|
| 4.600 | 2.436 / 2.228 | 1.437 / 1.204 | 6,7 / 9,5 | 18,4 / 20,7 | 0,385 / 0,648 | 0,164 / 0,263 | 12,0 / 11,3 |
| 5.000 | 2.468 / 2.238 | 1.407 / 1.220 | 7,0 / 10,0 | 18,2 / 20,9 | 0,376 / 0,635 | 0,151 / 0,253 | 11,8 / 11,2 |
| 6.000 | 2.417 / 2.242 | 1.450 / 1.235 | 7,9 / 11,4 | 18,6 / 21,6 | 0,341 / 0,597 | 0,116 / 0,224 | 11,6 / 10,9 |
| 7.000 | 2.350 / 2.206 | 1.468 / 1.170 | 8,4 / 12,5 | 19,1 / 22,6 | 0,317 / 0,565 | 0,090 / 0,201 | 11,3 / 10,7 |
| 8.000 | 2.219 / 2.107 | 1.450 / 1.099 | 8,6 / 13,6 | 19,7 / 23,6 | 0,302 / 0,540 | 0,073 / 0,180 | 11,0 / 10,4 |
| 10.000 | 2.142 / 2.053 | 1.278 / 964 | 9,4 / 15,6 | 21,9 / 26,1 | 0,283 / 0,496 | 0,059 / 0,149 | 10,3 / 9,7 |
| 12.000 | 2.125 / 1.999 | 1.089 / 928 | 10,3 / 16,9 | 24,6 / 28,1 | 0,275 / 0,466 | 0,054 / 0,132 | 9,7 / 9,1 |

**Lectura.** (1) El umbral reparte el mismo edge entre cobrar antes y conservar colchón: si el retiro se pide justo en el umbral, con $4.600 la cuenta cobra $2.300 y queda con $2.300 de saldo ($2.200 de colchón sobre el piso de +$100); con $6.000 cobra $3.000 y queda con $3.000 ($2.900 de colchón); con $12.000 cobra $3.000 y queda con $9.000 ($8.900), por eso quema la mitad de fondeadas pero tarda más en cobrar y pierde más saldo al 5.º retiro (las ventanas sobre caja + saldo del asiento suben de 18-21 % con $4.600 a 25-28 % con $12.000). (2) Ninguna variante acerca las dos condiciones que fallan: las evals perdidas las fija la eval de 6 contratos (experimento 03) y la recompra tras quemar; el umbral solo mueve las fondeadas quemadas, que son una fracción de esas evals. (3) La mejora de ventanas negativas que da cobrar antes es real pero chica (~2 puntos) y con −35 % el plan queda en 20-21 %, lejos del 10 %.

## Qué sigue

Con los experimentos 03 y 04 el frente 5B agotó las dos palancas de política de la Lucid 150K que más pesan (tamaño de la eval y umbral de retiro) sin mover la función objetivo. Las dos condiciones que fallan (evals perdidas y aprobación por intento) dependen de la geometría de la eval de la firma. Siguiente idea pre-registrada del plan: la regla de pausa del runbook (60 días negativos, presupuesto por plaza) dentro de la simulación, que ataca directamente las evals compradas cuando el edge se apaga. Decisión pendiente de Federico: qué condición de evals cede (o pasar M4 a P(fondeado ≤ 22 d)).

Archivos: `research/mine/exp04_payout_x.py`, `exp04_payout_x.json`, `exp04_payout_x.md`; plan `docs/PLAN_2026-10-27_exp04.md`.
