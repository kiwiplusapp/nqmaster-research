# Experimento 09 (frente 5C): contratos de Lucid 150K según la volatilidad (riesgo en dólares constante) — 2026-10-29

**Veredicto (regla pre-registrada): sin cambio, los contratos fijos (6 en la eval, 3 en la fondeada) siguen.** Ajustar los contratos de Lucid al ATR del día (contratos = base × ATR de referencia / ATR del día; eval 3-9, fondeada 2-4) empata en condiciones en 2020-22 (14 de 20 contra 14) y con −35 % baja la mediana ($8.436 contra $8.824; P(ganar) 0,37 < 0,80): no se elige. En 2023-26 además empeora: pierde 6 % de la mediana con el edge completo y 11 % con −35 % (P(ganar) 0,28 / 0,26), las ventanas negativas del bootstrap pasan de 8,5 a 10,8 % (rompe el 10 %) y el p10 contiguo de $2.101 a $1.234. Mejora la velocidad de la eval en 2020-22 (P(fondeado ≤ 22 d) 77 % contra 69 %) y las ventanas contiguas de 2020-22 (11,1 contra 12,5 %), pero no lo sostiene en 2023-26: **los días de ATR alto son los más rentables por contrato** (tercil alto $167-212 por día contra $57-94 en el bajo, `audit_regimes.csv`) y achicarse justo ahí cuesta más de lo que ahorra en quiebres. Unidad: plan completo (5 Lucid 150K + 3 MFFU 1x8 sin cambios); 1.000 caminos bootstrap por celda (los de la base: V0 la reproduce) y 84 / 132 planes y 89 / 137 asientos contiguos; T1 = arranques 2020-22, T2 = 2023-26; costos $1,90 + 2 ticks por lado, fees con cupón.

## Qué se corrió

`research/mine/exp09_volsize.py`: `race_v` / `seat_flow_v` = los núcleos de la base con contratos por día; la fondeada usa las filas de 1 contrato escaladas por los contratos del día (exacto: sin stop de ganancia ni de pérdida las filas son lineales en los contratos). ATR del día = Wilder 14 desplazado un día (se conoce al abrir, el mismo del filtro `MinAtrPoints`); ATR de referencia = mediana de los días de T1 = 266 puntos. Contratos de la eval en T1: 4c 112, 5c 157, 6c 124, 7c 91, 8c 106, 9c 106 días; en T2: 3c 112, 4c 204, 5c 118, 6c 154, 7c 204, 8c 119, 9c 25. Autotest: con contratos constantes 6 / 3 reproduce la base al bit (1.200 asientos). Regla en `docs/PLAN_2026-10-29_exp09.md`. Corrida: 40 s.

## Resultado (T1 / T2)

| Política | Mediana $/mes | p10 | Ventanas 60 d neg. % | P(fondeado ≤ 22 d) % | Días aprobar | Evals perdidas / mes (costo) | Cumple D1 (de 5) · M1 M1 M2 M4 M5 |
|---|---|---|---|---|---|---|---|
| **bootstrap, edge completo** | | | | | | | |
| **V0 (6c / 3c fijos)** | 16.173 / 14.689 | 9.243 / 7.041 | 4,5 / 8,5 | 69 / 71 | 8 / 7 | 1,89 / 3,28 | 5 / 5 ✓✓✓✓✓ ✓✓✓✓✓ |
| V1 (por volatilidad) | 16.164 / 13.751 | 9.531 / 6.138 | 4,2 / 10,8 | 77 / 71 | 7 / 9 | 1,98 / 3,39 | 5 / 4 ✓✓✓✓✓ ✓✓✗✓✓ |
| **bootstrap, −35 %** | | | | | | | |
| **V0 (6c / 3c fijos)** | 8.824 / 8.418 | 2.464 / 1.801 | 22,3 / 22,6 | 54 / 51 | 8 / 7 | 4,00 / 5,72 | 3 / 3 ✓✓✗✗✓ ✓✓✗✗✓ |
| V1 (por volatilidad) | 8.436 / 7.463 | 1.725 / 934 | 23,5 / 26,6 | 57 / 53 | 8 / 9 | 4,49 / 5,78 | 3 / 2 ✓✓✗✗✓ ✓✗✗✗✓ |
| **contiguo, edge completo** | | | | | | | |
| **V0 (6c / 3c fijos)** | 12.685 / 18.522 | 6.925 / 2.101 | 12,5 / 22,4 | 69 / 71 | 7 / 9 | 2,62 / 3,48 | 4 / 4 ✓✓✗✓✓ ✓✓✗✓✓ |
| V1 (por volatilidad) | 14.109 / 17.847 | 7.744 / 1.234 | 11,1 / 22,4 | 77 / 71 | 6 / 9 | 2,35 / 4,04 | 4 / 3 ✓✓✗✓✓ ✓✗✗✓✓ |
| **contiguo, −35 %** | | | | | | | |
| **V0 (6c / 3c fijos)** | 6.163 / 11.285 | 894 / −1.502 | 30,8 / 27,5 | 54 / 51 | 9 / 7 | 5,03 / 7,20 | 2 / 2 ✓✗✗✗✓ ✓✗✗✗✓ |
| V1 (por volatilidad) | 5.737 / 10.667 | 253 / −2.749 | 30,7 / 29,0 | 57 / 53 | 8 / 8 | 5,60 / 5,91 | 2 / 2 ✓✗✗✗✓ ✓✗✗✗✓ |

Ganancia pareada de la mediana del plan, V1 − V0: edge completo 36 / −873 $/mes (P(ganar) 0,51 / 0,28, P(perder > 5 %) 0,27 / 0,53); −35 % −343 / −946 (P(ganar) 0,37 / 0,26, P(perder > 5 %) 0,47 / 0,63).

## Qué deja

Confirma, ahora con la mecánica de la cuenta y la función objetivo, el descarte del 28-sep ("tamaño según volatilidad"): el edge no es proporcional al ATR (rinde más que proporcionalmente en ATR alto), así que igualar el riesgo en dólares le saca ingreso a los mejores días. Queda anotado en `Conocimiento/Descartado`. Las ventanas negativas de 60 días sobre historia contigua siguen siendo la condición que falla; las palancas de campaña y de tamaño no la mueven.

Archivos: `research/mine/exp09_volsize.py`, `exp09_volsize.json`; plan `docs/PLAN_2026-10-29_exp09.md`.
