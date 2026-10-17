# Lote 8 y re-entradas (17-oct-2026)

## Familias nuevas (lote 8), 16 años de NQ real, protocolo fijado antes de correr

| Familia | Configs | PF mediana T1 / T2 / 2010-14 / 2015-19 | Pasan T1 | Pasan todo |
|---|---|---|---|---|
| NDAY_BRK (ruptura de máximos/mínimos de 3-20 días) | 1.344 | 0,96 / 1,07 / 0,95 / 1,16 | 1 | 0 |
| ZMR (reversión por z-score 11:00-14:30) | 432 | 0,92 / 0,99 / 0,83 / 0,91 | 0 | 0 |
| LEG2 (continuación de la primera pierna) | 648 | 0,68 / 0,66 / 0,68 / 0,73 | 0 | 0 |
| EXH1 (vela de agotamiento, fade) | 432 | 0,78 / 0,66 / 0,63 / 0,69 | 0 | 0 |

- La única que pasa 2020-23 (NDAY_BRK, 3 días, límite en el nivel, 1R): PF 1,42 → 1,04 en 2024-26, 0,99 con 4 ticks.
- Lectura: la ruptura de N días es una copia correlada del ORB; las velas grandes que cierran en el extremo son continuación en NQ, no agotamiento; el z-score de 1 minuto se lo comen los costos.

## Segundo intento tras un stop

| Candidato | n | PF T1 / T2 | Sharpe T1 / T2 (base 3,47 / 3,96) | DD máx. | Pasa |
|---|---|---|---|---|---|
| VOLB re-armado, cualquier lado | 181 | 1,52 / 1,32 | 3,53 / 4,02 | 4.582 → 4.859 (+6%) | no (solo DD) |
| VOLB re-armado, mismo lado | 88 | 1,61 / 0,98 | 3,50 / 3,95 | +9% | no |
| Reentrada a mercado misma dirección (estructura) | 718 | 0,96 / 0,87 | 3,30 / 3,63 | +25% | no |
| Dar vuelta la posición (estructura) | 719 | 1,07 / 1,33 | 3,43 / 4,22 | igual | no (T1; bloquea 16% de entradas base) |
| LON re-armado | 5 | — | — | — | no (no ocurre) |

ORB60/90 ya permiten 2 trades por día (el segundo casi siempre viene tras un objetivo, PF 4,05 / 1,50); MSEQ secuencias ilimitadas; módulos de reloj sin segundo gatillo.

`VolbReArm` quedó en NQMaster como opción apagada. Detalle: `research/mine/reentry_report.md`, `b8_report.md`.
