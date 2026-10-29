# Experimento 09 (frente 5C): contratos de Lucid 150K según la volatilidad (riesgo en dólares constante) — 2026-10-29

**Veredicto (regla pre-registrada): sin cambio, los contratos fijos (6 en la eval, 3 en la fondeada) siguen.** Ajustar los contratos de Lucid al ATR del día (contratos = base × ATR de referencia / ATR del día; eval 3-9, fondeada 2-4) empata en condiciones en 2020-22 (14 de 20 contra 14) y con −35 % baja la mediana ($8.436 contra $8.824; P(ganar) 0,37 < 0,80): no se elige. En 2023-26 además empeora: pierde 6 % de la mediana con el edge completo y 11 % con −35 % (P(ganar) 0,28 / 0,26), las ventanas negativas del bootstrap pasan de 8,5 a 10,8 % (rompe el 10 %) y el p10 contiguo de $2.101 a $1.234. Mejora la velocidad de la eval en 2020-22 (P(fondeado ≤ 22 d) 77 % contra 69 %) y las ventanas contiguas de 2020-22 (11,1 contra 12,5 %), pero no lo sostiene en 2023-26. **Por qué (corregido tras la revisión adversarial):** el P&L del sistema por punto de ATR es parejo entre los terciles medio y alto (37,5 contra 38,4 por cada 100 puntos de ATR en 2020-26; t ≈ 0,1) y ~40 % más bajo en el tercil bajo (22,6; t ≈ 1,9, evidencia débil), que es justo donde la regla carga 7-9 contratos; además, con la referencia fija de 2020-22 la regla opera en promedio 5,7 % más contratos en T1 y 6,1 % menos en T2 (el ATR medio sube de 270 a 321), y aun igualando la exposición por período sigue perdiendo (−2,6 / −4,6 % con el edge completo, −7,9 / −10,8 % con −35 %). Unidad: plan completo (5 Lucid 150K + 3 MFFU 1x8 sin cambios); 1.000 caminos bootstrap por celda (los de la base: V0 la reproduce) y 84 / 132 planes y 89 / 137 asientos contiguos; T1 = arranques 2020-22, T2 = 2023-26; costos $1,90 + 2 ticks por lado, fees con cupón.

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

Confirma, ahora con la mecánica de la cuenta y la función objetivo, el descarte del 28-sep ("tamaño según volatilidad"): el tercil de ATR bajo rinde menos por punto de ATR, así que cargarle más contratos para igualar el riesgo en dólares cuesta ingreso. La simulación no modela el tope de contratos abiertos (con 9c × 4 de MOM1030 / CPI09 son 36 micros por módulo en la eval, tope 100; con 4c × 4, 16 en la fondeada, tope 40). Queda anotado en `Conocimiento/Descartado`. Las ventanas negativas de 60 días sobre historia contigua siguen siendo la condición que falla; las palancas de campaña y de tamaño no la mueven.

Archivos: `research/mine/exp09_volsize.py`, `exp09_volsize.json`; plan `docs/PLAN_2026-10-29_exp09.md`.

## Revisión adversarial (29-oct, revisor con contexto limpio y la lista de la sección 6 del plan) — entra tal cual

Federico — revisión adversarial del experimento 09 (contratos de Lucid 150K según la volatilidad). El veredicto "sin cambio" es correcto y robusto. La implementación está verificada al bit. Lo que no se sostiene tal como está escrito es la explicación ("el edge rinde más que proporcionalmente con ATR alto").

Scripts de verificación (solo lectura, no escriben en el repo):
- /tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r9_check1.py
- /tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r9_check2.py
- /tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r9_check3.py
- /tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r9_check4.py
- /tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r9_check5.py
- /tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad/r9_check6.py

| Severidad | Hallazgo | Evidencia | Recomendación |
|---|---|---|---|
| media | **La explicación no está sostenida tal como está escrita.** Dice que "el edge rinde más que proporcionalmente con ATR alto" y que "achicarse justo ahí cuesta". Los datos muestran otra cosa: entre ATR medio y alto el edge es proporcional, y el déficit está en el tercil bajo, que es justo donde V1 carga 7-9 contratos. | r9_check2/4: caminos de campaña `M[(0,4)][2]` con `atr_days`, 2020-26. P&L por contrato y por día por tercil de ATR: $45 / $103 / $162 (ATR medio 202 / 273 / 424). **P&L por punto de ATR (×100): 22,6 / 37,5 / 38,4.** Alto contra medio: t = 0,1. Bajo contra el resto: t = 1,9. En T2: 18,8 / 34,7 / 36,6 (t 0,2 y 1,6). En T1: 28 / 33 / 48 (t 1,1). Lo que cita el informe (`audit_regimes.csv`:2-4 y :10-12) son $ absolutos por día del perfil Ultra. Que suban con el ATR es lo esperable aun con un edge proporcional, así que no prueba la desproporción. P&L bruto de la eval con la misma exposición media: V1/V0 = 0,866 en T1 y 0,859 en T2. | Reescribir la frase en informe:3 y :30, ESTADO:134 y Descartado:12. Propuesta: "el tercil de ATR bajo rinde ~40 % menos por punto de ATR (evidencia débil, t≈1,9) y V1 le pone 7-9 contratos; entre ATR medio y alto el edge es proporcional". El veredicto no cambia. |
| baja | **Con ATR_ref = mediana de T1, V1 no opera la misma exposición que V0.** En T1 opera 5,7 % más contratos y en T2 6,1 % menos. El informe atribuye la pérdida de T2 solo a la forma del edge, sin mencionar el efecto de nivel (el ATR medio pasa de 270 a 321). La "mejora de velocidad" de T1 (77 contra 69 %) usa en parte ese tamaño extra. | r9_check2: contratos medios en la eval 6,35 (T1) y 5,63 (T2); en la fondeada 3,12 y 2,85. Diagnóstico r9_check3 (ATR_ref elegido por período para que el promedio dé 6,0; usa información futura, sirve solo como diagnóstico): V1 sigue perdiendo. Con edge completo, −2,6 % en T1 (P(ganar) 0,36) y −4,6 % en T2 (0,35). Con −35 %, −7,9 % y −10,8 % (0,32 / 0,28). P(fondeado ≤ 22 d) en T1: 75,4. El sesgo favoreció a V1 en T1, no a V0. ATR_ref usa todo T1 (el futuro dentro del período de elección) pero no filtra nada hacia T2. | Agregar una oración al informe con la exposición media por período y este diagnóstico. No cambia el veredicto. |
| baja | **Cifra mal transcripta:** "$57-94 en el tercil bajo". | `audit_regimes.csv`:2 da 56,6 (CFD 2020-26) y :10 da 90,6 (REAL 2024-26). El 94,2 es el tercil **medio** de CFD (:3). El mismo error está en PLAN_2026-10-29_exp09.md:41. | Corregir a "$57-91" y aclarar que son $ absolutos por día del perfil Ultra. |
| baja | **El informe no da el máximo teórico de contratos abiertos**, que el plan prometía informar (§5). | PLAN:42. Con 9c × MOM1030/CPI09 ×4 son 36 micros por módulo en la eval (tope 100). Con 4c × 4 son 16 en la fondeada (tope 40; prop-rules SKILL.md:19-20). La simulación no modela ese tope. | Una línea en el informe. No afecta el veredicto. |
| baja | **"Siguiente paso" del ESTADO desactualizado:** cierra los experimentos 07 y 08 pero no el 09. | docs/ESTADO.md:138 | Agregar "Experimento 09 cerrado (sin cambio)". |
| info | **`race_v` y `seat_flow_v` son idénticas a la base salvo el contrato por día.** | r9_check1 (diff textual). Las únicas diferencias: las ramas de `ptype` se reemplazan por `k = kv[t]` (exp09_volsize.py:21 contra prop_wf.py:92-95), `L` pasa a llamarse `Lx` y la llamada usa `race_v`. Con `pt = 0` la base usa `k = kA`, así que son equivalentes. | — |
| info | **El autotest se reproduce y el camino de V1 (contratos que varían) pasa una prueba independiente.** | Autotest re-corrido: 1.200 asientos, 0 diferencias (flujo, mtm y evals al bit). r9_check6: 800 asientos V1 (hc 0 / 0,35, T1 / T2) contra `objective.seat_flow` alimentado con matrices pre-escaladas por día (LO' = kv·(LO − h), Hh = 0, eval de 1 contrato): 0 diferencias. Confirma el índice por día absoluto: `kv[idx[d]]` y `kf[None, :]`. | — |
| info | **V0 reproduce la base.** | r9_check1: 192 cifras contra objective_baseline.json (plan y asiento L150; bootstrap y contiguo; hc 0 / 0,35; T1 / T2). Son idénticas, incluidos `p22_3` y los veredictos D1. La única excepción es `neg60_mtm` contiguo hc0 T2: 23,918 contra 23,923. Se debe al orden de suma: `plan_cell` suma MFFU antes que L150 (exp09:113-118) y `objective.contiguous` suma L150 primero. Sumando con L150 primero da 23,922754 exacto (r9_check3 d). `neg60_mtm` no es condición D1. | — |
| info | **El ATR del día se conoce al abrir y es el mismo del filtro `MinAtrPoints`.** | ict.py:49-51 calcula el TR de RTH con `ewm(alpha=1/14)` y `shift(1)`. Es lo mismo que NQMaster.cs:885-902 (Wilder con k = min(n, 14), calculado en la primera barra de la sesión); solo difieren en el arranque de 2010. Alineación de fechas: corr(\|P&L t\|, rango RTH t) = 0,44 contra 0,22 en t±1. Los 17 días hábiles de 2020-26 con ATR < 150 en nqdb son exactamente los que faltan en los días de campaña (están 0 de 17), así que los caminos usan el mismo ATR para el filtro de 150. No hay NaN ni fechas duplicadas; el ATR va de 150,5 a 818. | — |
| info | **El escalado de la fondeada es exacto.** | r9_check2: `FU.tiers(k=1)` × k es igual al bit a `FU.tiers(k)` para k = 2, 3, 4 y hc 0 / 0,35 (FL, FC, fp). Con stop de ganancia 0 y de pérdida 0, `dayvec` (prop_wf.py:178-189) solo hace mínimos y productos por k > 0. | — |
| info | **El risk cap de $300 escala bien.** Nota: con 4c bajo un colchón de $1.687, un trade que el cap deja pasar puede arriesgar hasta $1.200 (71 % del colchón), contra $900 con 3c. Es lo que fija el plan ("todo lo demás igual") y lo que haría NQMaster. | NQMaster.cs:1518 calcula `perBase = stopPts·PV·qty/Qty()`, o sea por contrato base. acct_2027.py:46 filtra `risk ≤ cap` por contrato. Saltear un trade no depende de cuántos contratos haya, así que las filas de la mezcla (300, 4) × k son exactas. | — |
| info | **La regla se aplicó como está escrita y ninguna lectura razonable cambia el veredicto.** | `decide()` (exp09:163-175) coincide con PLAN:21. Puntaje T1: 14 contra 14 (5+4+3+2 cada uno). P(ganar) con −35 % en T1 = 0,369 < 0,80, así que V1 no se elige. Lecturas alternativas: solo hc0, 9-9; solo bootstrap, 8-8; solo contiguo, 6-6; solo condiciones del plan (M1/M2), 8-8; T1+T2, 28-25 a favor de V0; desempate con edge completo, 0,514. Con un haircut de −35 % proporcional al ATR del día (r9_check3 c): 14-14, P(ganar) 0,44, T2 −9,5 %. Aun si V1 se hubiera elegido, falla en T2: pierde neg60 en bootstrap hc0, p10 en bootstrap hc0,35 y p10 en contiguo hc0, con P(perder > 5 %) de 0,53 y 0,63 (> 0,20). | — |
| info | **El informe, el ESTADO y Descartado no contradicen el JSON**, salvo la explicación (fila 1) y el "$94" (fila 3). | Coinciden con el JSON: las 16 filas de la tabla, las ganancias pareadas (36 / −873 y −343 / −946; P(ganar) 0,51 / 0,28 / 0,37 / 0,26; P(perder > 5 %) 0,27 / 0,53 / 0,47 / 0,63), la distribución de contratos, ATR_ref 266 y los caminos contiguos (84 / 132 planes, 89 / 137 asientos). También ESTADO:134 (14-14; −6 % / −11 %; M2 10,8 %) y Descartado:12. | — |

## Veredicto del revisor

La implementación es correcta: V0 reproduce la base al bit, V1 pasa una prueba independiente, el ATR es el del filtro y no mira hacia adelante, y el escalado de la fondeada y del risk cap es exacto.

La regla pre-registrada se aplicó como está escrita. "Sin cambio" es robusto a todas las lecturas razonables, incluidos el haircut proporcional al ATR y la exposición igualada.

Lo que hay que corregir es la explicación. El edge es proporcional entre ATR medio y alto; lo que cuesta es cargar 7-9 contratos en el tercil bajo, que rinde ~40 % menos por punto de ATR (t≈1,9). A eso se suma un efecto de nivel: V1 opera 6 % menos en 2023-26.

Hay que cambiar esa frase en el informe, el ESTADO y Descartado, y corregir "$57-94" por "$57-91". **Aprobado con reservas de texto; el veredicto no cambia.**

### Disposición de cada hallazgo (29-oct)

| Hallazgo | Qué se hizo |
|---|---|
| La explicación ("rinde más que proporcionalmente con ATR alto") no se sostiene | **Corregida** en el veredicto, en "Qué deja", en el ESTADO y en `Conocimiento/Descartado`: P&L por punto de ATR parejo entre ATR medio y alto, ~40 % menor en el tercil bajo (t ≈ 1,9), donde la regla carga 7-9 contratos. |
| Exposición distinta entre períodos (efecto de nivel) | **Agregada** (5,7 % más contratos en T1, 6,1 % menos en T2) con el diagnóstico de exposición igualada (sigue perdiendo). |
| "$57-94" mal transcripto | **Corregido** al quitar la cita (eran $ absolutos por día del perfil Ultra, $57-91 en el tercil bajo); el plan pre-registrado conserva su texto original. |
| Máximo teórico de contratos abiertos | **Agregado.** |
| "Siguiente paso" del ESTADO sin el 09 | **Corregido.** |

Scripts del revisor: `docs/experimentos/revisiones/09_contratos_por_volatilidad/`.
