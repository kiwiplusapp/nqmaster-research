# Decisiones 2026-10-29 (delegadas por Federico: "tomá vos las decisiones en base a lo que sea mejor para el rendimiento del bot")

Criterio único: rendimiento del sistema medido con los experimentos 02-06, sin mover ninguna cifra publicada. Cada decisión dice qué evidencia la sostiene y qué la revertiría.

## D1. Función objetivo: las dos condiciones de evals dejan de ser condiciones duras

**Antes (consigna del programa):** mediana > $2.759/mes sin p10 < $1.600; ventanas negativas de 60 días < 10 %; evals perdidas < 0,12 por mes; aprobación ≥ 65 %; días para aprobar ≤ 10.

**Desde hoy:**

| Condición | Estado | Por qué |
|---|---|---|
| M1 mediana > $2.759 y p10 ≥ $1.600 por mes (plan completo) | se mantiene | es el resultado |
| M2 ventanas de 60 días hábiles con caja negativa < 10 % (plan completo) | se mantiene, **y se lee también sobre historia contigua y con −35 % de edge** | es la condición que hoy falla donde importa (contiguo 12,5 / 22,4 %; con −35 % 22 %) |
| M5 días para aprobar ≤ 10 (mediana, evals de Lucid) | se mantiene | velocidad para llegar a fondeada |
| M4 aprobación | **pasa a P(fondeado en ≤ 22 días hábiles con ≤ 3 evals seriadas) ≥ 65 % en la eval de Lucid 150K**; la aprobación por intento y la de MFFU se siguen informando | la aprobación por intento choca con M5 (experimento 03: la única eval que la cumple tarda 60 días y pierde la mitad del ingreso); P(fondeado ≤ 22 d) es la métrica primaria pre-registrada con la que se eligió el 6c y es lo que el operador vive |
| M3 evals perdidas por mes | **deja de ser condición; se informa como costo** | ninguna política de Lucid la cumple porque las 3 MFFU solas ya pierden 0,08-0,47 por mes (revisión del experimento 03), y su costo (las fees) ya está restado en M1: como condición dura premiaría políticas que pierden ingreso para ahorrar un costo ya contado |

Con estas condiciones la base (experimento 02) cumple todas con el edge completo en el bootstrap; **falla M2 sobre historia contigua y con −35 %** (y M4 con −35 %: 54 / 51 %). Ese es el objetivo de los frentes siguientes. Lo revertiría: que Federico prefiera minimizar fees perdidas por sobre el ingreso neto.

### La base (experimento 02) con la función objetivo D1

`python3 research/mine/objective.py d1` (desde `research/mine`). Plan 5 Lucid 150K 6c/3c + 3 MFFU 1x8, cupón; T1 = arranques 2020-22, T2 = 2023-26; M4 y M5 de la eval de Lucid (P(fondeado ≤ 22 d) sobre inicios reales).

| Caminos | Edge | Período | Mediana $/mes | p10 | Ventanas 60 d neg. % | P(fondeado ≤ 22 d) L150 % | Días aprobar L150 | Evals perdidas / mes (costo) | Cumple |
|---|---|---|---|---|---|---|---|---|---|
| bootstrap | completo | T1 | 16.173 | 9.243 | 4,5 | 69,3 | 8 | 1,89 | 5/5 |
| bootstrap | completo | T2 | 14.689 | 7.041 | 8,5 | 71,3 | 7 | 3,28 | 5/5 |
| bootstrap | −35 % | T1 | 8.824 | 2.464 | 22,3 | 54,2 | 8 | 4,00 | 3/5 |
| bootstrap | −35 % | T2 | 8.418 | 1.801 | 22,6 | 51,2 | 7 | 5,72 | 3/5 |
| bootstrap | cero | T1 | -789 | -3.712 | 63,4 | 29,5 | 6 | 12,42 | 1/5 |
| bootstrap | cero | T2 | -566 | -4.182 | 63,1 | 30,8 | 6 | 14,25 | 1/5 |
| contiguo | completo | T1 | 12.685 | 6.925 | 12,5 | 69,3 | 7 | 2,62 | 4/5 |
| contiguo | completo | T2 | 18.522 | 2.101 | 22,4 | 71,3 | 9 | 3,48 | 4/5 |
| contiguo | −35 % | T1 | 6.163 | 894 | 30,8 | 54,2 | 9 | 5,03 | 2/5 |
| contiguo | −35 % | T2 | 11.285 | -1.502 | 27,5 | 51,2 | 7 | 7,20 | 2/5 |
| contiguo | cero | T1 | -3.583 | -4.212 | 79,3 | 29,5 | 6 | 13,68 | 1/5 |
| contiguo | cero | T2 | 512 | -5.078 | 73,2 | 30,8 | 8 | 16,01 | 1/5 |

Con el edge completo la base cumple 5 de 5 en el bootstrap y 4 de 5 sobre historia contigua: **la condición que falla es M2 (ventanas negativas de 60 días: 12,5 / 22,4 % contiguo; 22 % con −35 %)**, y con −35 % también M4 (54 / 51 %).

## D2. Regla 6 del runbook (presupuesto por plaza): se retira

Experimento 05 y su revisión: con reinicio en cada revisión trimestral la regla se dispara 1 vez en 8.000 plazas-año aun sin edge (no actúa); el modo anual protege el caso sin edge pero con −35 % en 2023-26 baja el p10 del plan de $1.801 a $1.452 (rompe M1) y no pasó la confirmación pre-registrada; la lectura "acumula hasta disparar" protege poco (p10 sin edge +$434 / +$441 por mes) y deja el p10 con −35 % en el borde ($1.609). Ninguna variante mejora el rendimiento con el edge completo ni con −35 %. **La protección contra un edge muerto queda en las reglas de pausa del sistema (puntos 1-4 del runbook), que miran el P&L por contrato y se validan en el frente 5C.** Lo revertiría: una validación de las pausas 1-4 que muestre que no detectan un edge muerto antes de que el presupuesto actúe.

## D3. Siguiente frente: 5C (régimen), con M2 sobre historia contigua y con −35 % como objetivo

El frente 5B cerró sin mover la función objetivo: las palancas de campaña (tamaño de eval, retiro, presupuesto, escalonado) no tocan la condición que falla (M2), y el plan de 8 cuentas es una sola cuenta multiplicada (diagnóstico 06). Las ventanas negativas vienen de los tramos malos del mercado: es un problema de régimen. Reglas del frente: solo información disponible en tiempo real, nada se re-optimiza, una idea entra solo si funciona en IS, C24 y REAL, y se mide con la función objetivo de D1 sobre los caminos de campaña.
