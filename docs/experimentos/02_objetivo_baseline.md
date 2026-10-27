# Experimento 02 (frente 5B): línea de base de la función objetivo del programa — 2026-10-27

**Veredicto: el plan vigente no cumple la función objetivo de la consigna. El asiento Lucid Flex 150K 6c/3c, con el edge completo, cumple 2 de las 6 condiciones en 2020-22 (ventanas negativas de 60 días 7,9 % < 10 %; 8 días hábiles para aprobar ≤ 10) y 1 de 6 en 2023-26 (7 días; las ventanas negativas suben a 11,4 %). No cumple ingreso (mediana $2.417 / $2.242 por mes contra > $2.759; p10 $1.450 / $1.235 contra ≥ $1.600), evals perdidas (0,34 / 0,60 por mes contra < 0,12) ni aprobación por intento (49 % / 41 % contra ≥ 65 %). Con −35 % de edge no cumple ninguna condición de ingreso ni de pérdida (mediana $1.378 / $1.342, ventanas negativas 27 % / 25 %, 0,75 / 1,07 evals perdidas por mes).** Caminos: NQ real 2020-02-26 → 2026-10-08 (1.638 días), T1 = arranques 2020-22 (elección), T2 = 2023-26 (chequeo); 1.000 caminos bootstrap de 252 días hábiles por celda (bloques de 21 días, mismas semillas que `integ_paired` / `integ_port`); costos $1,90 + 2 ticks por lado dentro de los caminos y fees de cada firma con cupón (Lucid 150K $215, MFFU $157). Nada se re-optimizó: es la medición de lo que hay.

## Qué se construyó

`research/mine/objective.py`: `fund_flow` / `seat_flow` son copias de `prop_wf.fund` / `prop_wf.seat` que además escriben el **flujo de caja diario** del asiento (fee al comprar la eval, 90 % de cada retiro el día que se pide) y un **registro por eval** (inicio, resultado, fin, quiebre de la fondeada, retiros). `selftest`: 2.400 asientos (3 edges × 2 períodos × 2 asientos × 200 caminos), **0 diferencias** contra `prop_wf.seat` en neto, evals, aprobadas, quiebres, retiros y primer retiro; la caja y la contabilidad caja + saldo coinciden al final de cada camino. Con las semillas y el orden de sorteo de `integ_paired.py` (20261021) e `integ_port.py` (4242) reproduce **al dólar** las medianas y p10 de los asientos y del plan publicados en el runbook (0 diferencias en 12 celdas de asiento y 6 de plan). Corrida completa: 29 s.

Definiciones pre-registradas (`docs/PLAN_2026-10-27.md`): **M1** mediana y p10 entre caminos del neto de 12 meses / 12 (y, aparte, la distribución de los 12 cortes de 21 días de cada camino); **M2** fracción de ventanas móviles de 60 días hábiles (paso 1, 193 por camino) con flujo de caja negativo (`neg60`), y la misma sobre caja + saldo de la fondeada (`mtm`; el saldo se pierde al quebrar); **M3** evals quebradas por mes (y fondeadas quebradas por mes); **M4** aprobadas / (aprobadas + quebradas) sobre evals terminadas (y `p22_3` = P(fondeado en ≤ 22 días hábiles con hasta 3 evals seriadas) sobre inicios reales, la primaria pre-registrada de `prop_wf`); **M5** mediana de días hábiles de la compra a la aprobación. Umbrales de la consigna interpretados sobre el asiento L150 (la consigna no fija la unidad; sus magnitudes coinciden con el asiento).

## Resultado: asiento Lucid Flex 150K 6c/3c (cupón; T1 / T2)

| Métrica | Umbral | Edge completo | −35 % | Edge cero |
|---|---|---|---|---|
| M1 mediana $/mes | > 2.759 | **2.417 / 2.242** ✗ | 1.378 / 1.342 ✗ | −70 / −95 ✗ |
| M1 p10 $/mes | ≥ 1.600 | **1.450 / 1.235** ✗ | 370 / 317 ✗ | −627 / −752 ✗ |
| M1 caja por mes de 21 días: mediana / p10 / P(<0) | — | 2.485 / −430 / 22 % · 2.485 / −645 / 31 % | 0 / −645 / 42 % · 0 / −860 / 44 % | −430 / −1.075 / 76 % · −645 / −1.075 / 75 % |
| M2 ventanas de 60 días negativas, caja (caja + saldo) | < 10 % | **7,9 % ✓ / 11,4 % ✗** (18,6 / 21,6) | 26,9 / 25,4 ✗ (35 / 35) | 63 / 63 ✗ |
| M3 evals perdidas por mes | < 0,12 | **0,34 / 0,60 ✗** | 0,75 / 1,07 ✗ | 2,08 / 2,45 ✗ |
| M3 fondeadas perdidas por mes | — | 0,116 / 0,224 | 0,20 / 0,27 | 0,27 / 0,30 |
| M4 aprobación por intento | ≥ 65 % | **49 % / 41 % ✗** | 31 / 27 ✗ | 13 / 13 ✗ |
| M4 P(fondeado ≤ 22 d, ≤ 3 evals) | ≥ 65 % | **69 % / 71 % ✓** | 54 / 51 ✗ | 30 / 31 ✗ |
| M5 días para aprobar, mediana (p75) | ≤ 10 | **8 (12) / 7 (11) ✓** | 8 (11) / 7 (10) ✓ | 6 (9) / 6 (9) ✓ |
| Evals por año · retiros por año · evals abiertas al cierre | — | 8,3 · 11,6 · 0,23 / 12,4 · 10,9 · 0,24 | 13,4 / 17,9 evals | 29 / 34 evals |

Con precio de lista ($285) la mediana baja a $2.374 / $2.166 y el p10 a $1.409 / $1.158; el resto no cambia (las fees no alteran qué eval aprueba).

**Lectura.** (1) El ingreso queda 12-19 % por debajo del umbral de mediana y 9-23 % del de p10 ya con el edge completo. (2) La aprobación depende de la definición: por intento el 6c aprueba 41-49 % (la mitad de las evals se pierde: 0,34-0,60 por mes, es decir $880 / $1.540 por año de fees perdidas por asiento, 3 / 6 % del neto), pero encadenando hasta 3 intentos el 69-71 % de los arranques está fondeado en 22 días hábiles, que es la métrica con la que se eligió el 6c en `prop_wf`. La consigna pide ≥ 65 % y < 0,12 evals perdidas por mes a la vez: con la geometría actual de la eval (6 contratos, trailing EOD $4.500, objetivo $9.000) las dos cosas no se cumplen juntas. (3) La caja mensual es grumosa (retiro al llegar a $6.000, tope $3.000): el 22-31 % de los meses de 21 días son negativos aun con el edge completo, la mediana mensual con −35 % de edge es $0 (ni fee ni retiro en el mes típico) y el p10 mensual es −$430 / −$645; el umbral "p10 ≥ $1.600" solo tiene sentido sobre el neto anual / 12, que es como está medido. (4) Las ventanas de 60 días: 7,9 % en T1 y 11,4 % en T2 en caja; 19-22 % si se cuenta el saldo no retirado que se pierde al quebrar. (5) Los días para aprobar cumplen en todos los casos: la eval de 6 contratos es rápida; su costo es la tasa de quiebre.

## Resultado: asiento MFFU Rapid 50K 1x8 y plan completo

| | Umbral | MFFU 1x8 edge completo | MFFU −35 % | Plan 5 L150 + 3 MFFU edge completo | Plan −35 % | Plan edge cero |
|---|---|---|---|---|---|---|
| M1 mediana / p10 $/mes | 2.759 / 1.600 | 1.388 / 642 · 1.184 / 347 | 703 / −52 · 510 / −92 | **16.173 / 9.243 · 14.689 / 7.041** | 8.824 / 2.464 · 8.418 / 1.801 | −789 / −3.712 · −566 / −4.182 |
| Caja por mes de 21 días: mediana / p10 / P(<0) | — | 619 / −157 / 10 % · 0 / −157 / 16 % | 0 / −157 / 20 % · 0 / −157 / 26 % | 14.743 / −1.075 / 15 % · 13.500 / −2.150 / 23 % | 2.664 / −3.092 / 36 % · 2.270 / −3.696 / 38 % | −2.621 / −5.375 / 76 % · −3.225 / −6.317 / 74 % |
| M2 ventanas de 60 días negativas, caja (caja + saldo) | < 10 % | 5,5 (5,4) ✓ / 16,2 (13,7) ✗ | 26,0 / 34,6 ✗ | **4,5 (13,5) ✓ / 8,5 (17,3) ✓** | 22,3 / 22,6 ✗ | 63 / 63 ✗ |
| M3 evals perdidas por mes (plan: las 5 L150 juntas; fondeadas perdidas) | < 0,12 | 0,022 / 0,072 ✓ | 0,11 / 0,18 | 1,81 / 3,07 (0,61 / 1,10) | 3,68 / 5,25 (1,02 / 1,32) | 10,4 / 12,2 (1,38 / 1,55) |
| M4 aprobación por intento (P fondeado ≤ 22 d) | ≥ 65 % | 81 % (40 %) ✓ / 64 % (48 %) ✗ | 54 / 48 ✗ | — | — | — |
| M5 días para aprobar, mediana (p75) | ≤ 10 | 23 (35) / 19 (26) ✗ | 21 / 21 ✗ | — | — | — |

MFFU es el espejo de Lucid: eval de 1 contrato con 8 lotes de alto acierto, aprueba 64-81 % por intento y pierde 0,02-0,07 evals por mes, pero tarda 19-23 días hábiles y rinde la mitad. El plan completo cumple las ventanas de 60 días con el edge completo (4,5 % / 8,5 %) y no con −35 % (22 %); con el edge completo el 15-23 % de los meses de 21 días del plan son negativos en caja.

## Qué sigue (frente 5B, una idea por sesión, siempre contra esta base con ganancia pareada sobre los mismos caminos, P(gain) ≥ 0,80)

Las condiciones que fallan (ingreso, evals perdidas, aprobación por intento) dependen de la geometría de la eval y del ciclo de retiros, no de los módulos: candidatos documentados y no probados sobre la caja: umbral y momento del retiro (hoy $6.000 con 5 días ≥ $250), escalonado de las compras entre asientos (5 días fijos vs esperar a fondear), tamaño de la eval 6c vs menos contratos medido con las cinco métricas a la vez (en `prop_wf` se eligió por P(fondeado ≤ 22 d) y neto), y la regla de pausa del runbook (60 días negativos) dentro de la simulación. Ninguno toca `NQMaster.cs` ni parámetros de módulos. La decisión previa es de Federico: **confirmar la unidad de los umbrales (asiento L150 o plan) y la definición de "aprobación" (por intento o P(fondeado ≤ 22 d, ≤ 3 evals))**; la tabla trae las dos.

Archivos: `research/mine/objective.py`, `objective_baseline.json`, `objective_baseline.md`; plan `docs/PLAN_2026-10-27.md`.
