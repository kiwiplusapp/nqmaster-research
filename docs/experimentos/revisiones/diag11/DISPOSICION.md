# Disposición de la revisión del diagnóstico 11 (30-oct)

El informe del revisor está tal cual en `revision_d11.md`. Sus scripts están en `variants.py` y `best_partition.py`.

**Veredicto del revisor: aprobado con reservas.** La conclusión se sostiene: repartir los módulos multiplica los quiebres. Lo confirmó con el set exacto, con 5 semillas, con umbrales de $500 a $6.000 y con la mejor partición posible.

| Hallazgo | Severidad | Qué se hizo |
|---|---|---|
| Los períodos no son los del pre-registro: el corte es 2023, no 2024 | Media | **Corregido:** los rótulos dicen T1 2020-10..2022-12 y T2 2023-01..2026-10, el corte de `prop_wf`. El corte de 2024 queda como sensibilidad post-hoc: ×1,5-1,9 en 2024-26 y ×2,1-2,5 en 2020-23. El plan lleva una nota de corrección. |
| El set no es el de 2027: tenía LATEFH y le faltaba `conflict_filter` | Media | **Corregido:** el script v2 usa `nt_compare.research_set('ultra_d4')`, con 23 módulos. Mismo veredicto. |
| El criterio pre-registrado era imposible por construcción | Media | **Corregido en el informe:** el titular dice "criterio no evaluable" y que la evidencia que decide es post-hoc. |
| "5D cerrado, no queda ninguna regla" afirma de más | Media | **Corregido:** pasa a "cerrado para la partición y las reglas de la consigna". La escalera de MFFU y el stop de $1.500 sí estaban probados en la ronda 5 (`integ_ladder.json`): con −35 %, P(ganancia) 0,54-0,63 y P(año negativo) +14 a +22 puntos, no pasan. Ahora el informe lo cita. Quedan como no probados partir por firma y los perfiles distintos por plaza a 1×. |
| M2 no se midió; "ningún detalle del motor la da vuelta" no está probado | Media | **Corregido:** se quitó la frase. El informe dice que M2 no se midió y que la desincronización podría mejorarla. No se corrió la celda en el motor: armar caminos por grupo de módulos requiere reconstruir `acct2027_paths`. Queda anotado como límite. |
| La "coincidencia" es asimétrica | Baja | **Corregido:** se informan las dos direcciones. |
| La "favorable" no es la más favorable; son 477 sorteos, no 2.000 | Baja | **Corregido:** el informe dice cuántos sorteos pasan el filtro (494 con el set exacto) y cita la cota del revisor (mejor partición por quiebres: ×3,98 en T1, ×1,46 / ×1,73 en T2). |
| El pre-registro no se puede verificar | Baja | **Reconocido** en el plan y en el informe. En adelante, el plan se commitea antes de correr. |
| Escenarios donde la partición convenga | Baja | Agregado al informe: ninguna celda con edge sube 10 % o menos; el mínimo es ×1,18. |
