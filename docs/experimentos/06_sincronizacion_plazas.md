# Diagnóstico 06 (frente 5B): sincronización de las plazas del plan — 2026-10-27

**Resultado: las 5 plazas de Lucid Flex 150K terminan siendo la misma cuenta, y la caja de cualquier par de plazas del plan se mueve igual mes a mes.** En el 87-100 % de los pares de plazas de Lucid, las dos compran una eval el mismo día en algún momento del año (mediana: día 22-70 desde el arranque). Desde ahí son idénticas, porque ven el mismo camino de mercado con las mismas reglas. Las MFFU se fusionan menos con edge (19-72 % de los pares), pero la correlación de la caja + saldo mensual entre plazas es ~1 en todos los casos: las fondeadas operan los mismos trades. **El escalonado inicial de 5 días se borra en el primer o segundo mes**, así que el último ítem pendiente del frente 5B ("escalonado de las compras entre asientos") no puede cambiar las métricas del año; no se corre como experimento de política. Diagnóstico, no experimento pre-registrado: no cambia ninguna cifra ni ninguna regla.

Caminos: los del plan de la base (rng 4242, 252 + 25 días), 300 caminos por celda; plan 5 Lucid 150K 6c/3c + 3 MFFU 1x8, arranques cada 5 días; T1 = arranques 2020-22, T2 = 2023-26; costos $1,90 + 2 ticks por lado, fees con cupón. Script `research/mine/diag_sync_seats.py` → `diag_sync_seats.json`.

| Edge | Período | Lucid: pares fusionados (día mediano) | MFFU: pares fusionados (día mediano) | Plazas efectivas (Lucid / MFFU) |
|---|---|---|---|---|
| Completo | 2020-22 | 87 % (70) | 19 % (33) | 1,0 de 5 / 1,0 de 3 |
| Completo | 2023-26 | 95 % (38) | 53 % (40) | 1,0 / 1,0 |
| −35 % | 2020-22 | 96 % (36) | 59 % (39) | 1,0 / 1,0 |
| −35 % | 2023-26 | 100 % (30) | 72 % (45) | 1,0 / 1,0 |
| Cero | 2020-22 | 100 % (24) | 99 % (37) | 1,0 / 1,0 |
| Cero | 2023-26 | 100 % (22) | 98 % (30) | 1,0 / 1,0 |

"Plazas efectivas" = n² / suma de la matriz de correlación de la caja + saldo mensual de las plazas (días 20-251); 1,0 significa que n plazas se comportan como una sola multiplicada por n.

**Cómo se fusionan.** La eval de 6 contratos dura 6-8 días y quiebra en los días grandes en contra; un día así quiebra a la vez todas las evals de Lucid abiertas, sin importar cuándo empezaron, y todas recompran al día siguiente. MFFU (1 contrato, ×8 lotes) quiebra menos, por eso se fusiona menos con edge.

**Qué implica.**
1. El plan de 8 cuentas no diversifica: el ingreso y el riesgo escalan con la cantidad de cuentas. Las cifras de la campaña ya lo incluyen (todas las plazas corren sobre el mismo camino), así que ningún número publicado cambia; cambia la lectura. "5 Lucid" es una apuesta 5 veces más grande a la misma cuenta, no 5 apuestas.
2. Escalonar el arranque no sirve más allá del primer o segundo mes. Desincronizar de forma permanente (por ejemplo, no recomprar el mismo día que otra plaza de la misma firma) solo cambiaría el momento de las fees y de los retiros, no los trades de las fondeadas, que son los que llevan la correlación: el beneficio esperado es chico y tiene un costo en días sin operar. Queda anotado como idea no probada.
3. Diversificar de verdad exige que las cuentas operen cosas distintas (otros perfiles o módulos por cuenta), y eso ya no es política de campaña: es el frente 5D (robustez) o una decisión de Federico sobre perfiles.
