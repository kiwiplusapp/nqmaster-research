# Linea de base de la funcion objetivo (objective.py, 1000 caminos)

Umbrales: med_mes 2759.0, p10_mes 1600.0, neg60 10.0, evals_perdidas_mes 0.12, aprobacion 65.0, dias_aprobar 10.0

| asiento | edge | periodo | fee | med $/mes | p10 | P(anio<0) % | mes21 med / p10 / P<0 | neg60 % (mtm) [=0] | evals/anio | evals perd./mes | ctas perd./mes | aprob. % | p22_3 % | dias aprobar (p75) | cumple |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L150 6c/3c | hc0.0 | T1 | coupon | 2417 | 1450 | 0.0 | 2485 / -430 / 22 | 7.9 (18.6) [0.8] | 8.3 | 0.341 | 0.116 | 49.3 | 69.3 | 8 (12) | -med_mes -p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc0.0 | T1 | list | 2374 | 1409 | 0.2 | 2415 / -570 / 22 | 7.9 (19.1) [0.8] | 8.3 | 0.341 | 0.116 | 49.3 | — | 8 (12) |  |
| MFFU 1x8 | hc0.0 | T1 | coupon | 1388 | 642 | 0.7 | 619 / -157 / 10 | 5.5 (5.4) [12.5] | 1.4 | 0.022 | 0.010 | 80.8 | 39.9 | 23 (35) | -med_mes -p10_mes +neg60 +evals_perdidas_mes +aprobacion -dias_aprobar |
| L150 6c/3c | hc0.0 | T2 | coupon | 2242 | 1235 | 0.2 | 2485 / -645 / 31 | 11.4 (21.6) [0.3] | 12.4 | 0.597 | 0.224 | 41.0 | 71.3 | 7 (11) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc0.0 | T2 | list | 2166 | 1158 | 0.3 | 2415 / -855 / 31 | 11.4 (22.4) [0.3] | 12.4 | 0.597 | 0.224 | 41.0 | — | 7 (11) |  |
| MFFU 1x8 | hc0.0 | T2 | coupon | 1184 | 347 | 3.6 | 0 / -157 / 16 | 16.2 (13.7) [9.9] | 2.5 | 0.072 | 0.052 | 64.4 | 47.6 | 19 (26) | -med_mes -p10_mes -neg60 +evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc0.35 | T1 | coupon | 1378 | 370 | 3.9 | 0 / -645 / 42 | 26.9 (35.2) [1.0] | 13.4 | 0.753 | 0.200 | 30.8 | 54.2 | 8 (11) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc0.35 | T1 | list | 1314 | 271 | 4.9 | 0 / -855 / 42 | 27.0 (36.2) [1.0] | 13.4 | 0.753 | 0.200 | 30.8 | — | 8 (11) |  |
| MFFU 1x8 | hc0.35 | T1 | coupon | 703 | -52 | 14.6 | 0 / -157 / 20 | 26.0 (25.5) [17.8] | 2.9 | 0.108 | 0.051 | 54.0 | 30.5 | 21 (33) | -med_mes -p10_mes -neg60 +evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc0.35 | T2 | coupon | 1342 | 317 | 4.4 | 0 / -860 / 44 | 25.4 (34.5) [0.8] | 17.9 | 1.071 | 0.265 | 26.7 | 51.2 | 7 (10) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc0.35 | T2 | list | 1254 | 200 | 7.2 | 0 / -1140 / 44 | 26.1 (35.9) [0.8] | 17.9 | 1.071 | 0.265 | 26.7 | — | 7 (10) |  |
| MFFU 1x8 | hc0.35 | T2 | coupon | 510 | -92 | 19.3 | 0 / -157 / 26 | 34.6 (32.0) [15.7] | 4.3 | 0.177 | 0.097 | 48.2 | 31.4 | 21 (31) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc1.0 | T1 | coupon | -70 | -627 | 54.3 | -430 / -1075 / 76 | 63.2 (64.4) [0.6] | 29.2 | 2.076 | 0.273 | 13.3 | 29.5 | 6 (9) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc1.0 | T1 | list | -239 | -831 | 62.5 | -570 / -1425 / 76 | 64.4 (66.4) [0.6] | 29.2 | 2.076 | 0.273 | 13.3 | — | 6 (9) |  |
| MFFU 1x8 | hc1.0 | T1 | coupon | -131 | -183 | 73.4 | -157 / -314 / 63 | 80.0 (73.8) [6.7] | 10.3 | 0.652 | 0.122 | 19.0 | 16.7 | 17 (24) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc1.0 | T2 | coupon | -95 | -752 | 55.2 | -645 / -1075 / 75 | 63.0 (64.5) [0.2] | 34.1 | 2.448 | 0.303 | 12.5 | 30.8 | 6 (9) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc1.0 | T2 | list | -292 | -998 | 61.3 | -855 / -1425 / 75 | 65.0 (66.7) [0.2] | 34.1 | 2.448 | 0.303 | 12.5 | — | 6 (9) |  |
| MFFU 1x8 | hc1.0 | T2 | coupon | -131 | -196 | 74.9 | -157 / -314 / 58 | 78.2 (72.6) [9.5] | 10.5 | 0.680 | 0.116 | 17.8 | 14.2 | 20 (30) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar |

| plan (8 cuentas) | edge | periodo | med $/mes | p10 | p90 | P(anio<0) % | mes21 med / p10 / P<0 | neg60 % (mtm) [dias] | evals/anio | evals perd./mes (L150 / MFFU) | ctas perd./mes | aprob. % (L150 / MFFU) | dias aprobar (p75) (L150 / MFFU) | cumple |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 L150 + 3 MFFU | hc0.0 | T1 | 16173 | 9243 | 22837 | 0.0 | 14743 / -1075 / 15 | 4.5 (13.5) [20, 252] | 47.3 | 1.89 (1.81 / 0.08) | 0.65 | 50.9 (48.0 / 78.7) | 9 (15) (8 / 22) | +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| 5 L150 + 3 MFFU | hc0.0 | T2 | 14689 | 7041 | 21646 | 0.6 | 13500 / -2150 / 23 | 8.5 (17.3) [20, 252] | 70.3 | 3.28 (3.07 / 0.21) | 1.26 | 42.8 (40.3 / 64.5) | 8 (13) (7 / 19) | +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| 5 L150 + 3 MFFU | hc0.35 | T1 | 8824 | 2464 | 15910 | 3.9 | 2664 / -3092 / 36 | 22.3 (31.1) [20, 252] | 74.5 | 4.00 (3.68 / 0.32) | 1.17 | 34.1 (31.5 / 54.0) | 9 (13) (8 / 21) | +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| 5 L150 + 3 MFFU | hc0.35 | T2 | 8418 | 1801 | 15613 | 4.2 | 2270 / -3696 / 38 | 22.6 (31.3) [20, 252] | 100.0 | 5.72 (5.25 / 0.47) | 1.59 | 29.9 (27.2 / 50.5) | 8 (13) (7 / 20) | +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| 5 L150 + 3 MFFU | hc1.0 | T1 | -789 | -3712 | 5310 | 56.4 | -2621 / -5375 / 76 | 63.4 (65.0) [20, 252] | 178.3 | 12.42 (10.43 / 1.99) | 1.75 | 14.2 (13.3 / 18.6) | 7 (12) (6 / 17) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| 5 L150 + 3 MFFU | hc1.0 | T2 | -566 | -4182 | 5075 | 55.3 | -3225 / -6317 / 74 | 63.1 (64.8) [20, 252] | 202.1 | 14.25 (12.23 / 2.02) | 1.91 | 13.5 (12.7 / 18.4) | 7 (12) (6 / 20) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |

Historia contigua (inicio real cada 5 dias, 252 dias; sin bootstrap):

| unidad | edge | periodo | n caminos | med $/mes | p10 | P(anio<0) % | neg60 % (mtm) [=0] | evals perd./mes | aprob. % | dias aprobar | cumple |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L150 6c/3c | hc0.0 | T1 | 89 | 2107 | 1171 | 0.0 | 16.6 (20.8) [1.3] | 0.51 | 37.4 | 7 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| MFFU 1x8 | hc0.0 | T1 | 89 | 820 | 284 | 0.0 | 6.4 (12.5) [22.1] | 0.03 | 75.4 | 28 | -med_mes -p10_mes +neg60 +evals_perdidas_mes +aprobacion -dias_aprobar |
| L150 6c/3c | hc0.0 | T2 | 137 | 2467 | 588 | 3.6 | 25.5 (27.8) [0.3] | 0.65 | 38.9 | 9 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| MFFU 1x8 | hc0.0 | T2 | 137 | 1858 | -92 | 16.8 | 24.9 (25.3) [11.7] | 0.08 | 61.5 | 29 | -med_mes -p10_mes -neg60 +evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc0.35 | T1 | 89 | 1135 | 275 | 0.0 | 31.1 (30.6) [0.2] | 0.91 | 21.6 | 9 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| MFFU 1x8 | hc0.35 | T1 | 89 | 260 | -92 | 32.6 | 41.3 (39.4) [20.4] | 0.16 | 45.1 | 21 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc0.35 | T2 | 137 | 1460 | -295 | 14.6 | 30.1 (34.5) [1.5] | 1.32 | 18.7 | 7 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| MFFU 1x8 | hc0.35 | T2 | 137 | 1103 | -118 | 34.3 | 34.2 (34.6) [18.7] | 0.21 | 34.6 | 23 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc1.0 | T1 | 89 | -591 | -717 | 58.4 | 78.3 (79.5) [0.0] | 2.28 | 12.4 | 6 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| MFFU 1x8 | hc1.0 | T1 | 89 | -170 | -209 | 62.9 | 84.8 (78.4) [2.4] | 0.72 | 17.8 | 18 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc1.0 | T2 | 137 | 66 | -878 | 48.9 | 72.8 (74.4) [0.0] | 2.76 | 9.1 | 8 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| MFFU 1x8 | hc1.0 | T2 | 137 | -105 | -254 | 55.5 | 79.6 (82.1) [7.3] | 0.74 | 11.9 | 26 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar |
| 5 L150 + 3 MFFU | hc0.0 | T1 | 84 | 12685 | 6925 | 0.0 | 12.5 (18.2) [0.5] | 2.62 | 40.2 | 7 | +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| 5 L150 + 3 MFFU | hc0.0 | T2 | 132 | 18522 | 2101 | 5.3 | 22.4 (23.9) [0.3] | 3.48 | 41.0 | 10 | +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| 5 L150 + 3 MFFU | hc0.35 | T1 | 84 | 6163 | 894 | 0.0 | 30.8 (30.3) [0.0] | 5.03 | 24.5 | 10 | +med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| 5 L150 + 3 MFFU | hc0.35 | T2 | 132 | 11285 | -1502 | 14.4 | 27.5 (32.6) [0.1] | 7.20 | 19.9 | 8 | +med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| 5 L150 + 3 MFFU | hc1.0 | T1 | 84 | -3583 | -4212 | 59.5 | 79.3 (78.4) [0.0] | 13.68 | 13.0 | 8 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| 5 L150 + 3 MFFU | hc1.0 | T2 | 132 | 512 | -5078 | 49.2 | 73.2 (74.6) [0.0] | 16.01 | 9.3 | 11 | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar |
