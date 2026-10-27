# Linea de base de la funcion objetivo (objective.py, 1000 caminos)

Umbrales: med_mes 2759.0, p10_mes 1600.0, neg60 10.0, evals_perdidas_mes 0.12, aprobacion 65.0, dias_aprobar 10.0

| asiento | edge | periodo | fee | med $/mes | p10 | P(anio<0) % | mes21 med / p10 / P<0 | neg60 % (mtm) | evals/anio | evals perd./mes | ctas perd./mes | aprob. % | p22_3 % | dias aprobar (p75) | cumple |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L150 6c/3c | hc0.0 | T1 | coupon | 2417 | 1450 | 0.0 | 2485 / -430 / 22 | 7.9 (18.6) | 8.3 | 0.341 | 0.116 | 49.3 | 69.3 | 8 (12) | -med_mes -p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc0.0 | T1 | list | 2374 | 1409 | 0.2 | 2415 / -570 / 22 | 7.9 (19.1) | 8.3 | 0.341 | 0.116 | 49.3 | nan | 8 (12) |  |
| MFFU 1x8 | hc0.0 | T1 | coupon | 1388 | 642 | 0.7 | 619 / -157 / 10 | 5.5 (5.4) | 1.4 | 0.022 | 0.010 | 80.8 | 39.9 | 23 (35) | -med_mes -p10_mes +neg60 +evals_perdidas_mes +aprobacion -dias_aprobar |
| L150 6c/3c | hc0.0 | T2 | coupon | 2242 | 1235 | 0.2 | 2485 / -645 / 31 | 11.4 (21.6) | 12.4 | 0.597 | 0.224 | 41.0 | 71.3 | 7 (11) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc0.0 | T2 | list | 2166 | 1158 | 0.3 | 2415 / -855 / 31 | 11.4 (22.4) | 12.4 | 0.597 | 0.224 | 41.0 | nan | 7 (11) |  |
| MFFU 1x8 | hc0.0 | T2 | coupon | 1184 | 347 | 3.6 | 0 / -157 / 16 | 16.2 (13.7) | 2.5 | 0.072 | 0.052 | 64.4 | 47.6 | 19 (26) | -med_mes -p10_mes -neg60 +evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc0.35 | T1 | coupon | 1378 | 370 | 3.9 | 0 / -645 / 42 | 26.9 (35.2) | 13.4 | 0.753 | 0.200 | 30.8 | 54.2 | 8 (11) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc0.35 | T1 | list | 1314 | 271 | 4.9 | 0 / -855 / 42 | 27.0 (36.2) | 13.4 | 0.753 | 0.200 | 30.8 | nan | 8 (11) |  |
| MFFU 1x8 | hc0.35 | T1 | coupon | 703 | -52 | 14.6 | 0 / -157 / 20 | 26.0 (25.5) | 2.9 | 0.108 | 0.051 | 54.0 | 30.5 | 21 (33) | -med_mes -p10_mes -neg60 +evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc0.35 | T2 | coupon | 1342 | 317 | 4.4 | 0 / -860 / 44 | 25.4 (34.5) | 17.9 | 1.071 | 0.265 | 26.7 | 51.2 | 7 (10) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc0.35 | T2 | list | 1254 | 200 | 7.2 | 0 / -1140 / 44 | 26.1 (35.9) | 17.9 | 1.071 | 0.265 | 26.7 | nan | 7 (10) |  |
| MFFU 1x8 | hc0.35 | T2 | coupon | 510 | -92 | 19.3 | 0 / -157 / 26 | 34.6 (32.0) | 4.3 | 0.177 | 0.097 | 48.2 | 31.4 | 21 (31) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc1.0 | T1 | coupon | -70 | -627 | 54.3 | -430 / -1075 / 76 | 63.2 (64.4) | 29.2 | 2.076 | 0.273 | 13.3 | 29.5 | 6 (9) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc1.0 | T1 | list | -239 | -831 | 62.5 | -570 / -1425 / 76 | 64.4 (66.4) | 29.2 | 2.076 | 0.273 | 13.3 | nan | 6 (9) |  |
| MFFU 1x8 | hc1.0 | T1 | coupon | -131 | -183 | 73.4 | -157 / -314 / 63 | 80.0 (73.8) | 10.3 | 0.652 | 0.122 | 19.0 | 16.7 | 17 (24) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar |
| L150 6c/3c | hc1.0 | T2 | coupon | -95 | -752 | 55.2 | -645 / -1075 / 75 | 63.0 (64.5) | 34.1 | 2.448 | 0.303 | 12.5 | 30.8 | 6 (9) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar |
| L150 6c/3c | hc1.0 | T2 | list | -292 | -998 | 61.3 | -855 / -1425 / 75 | 65.0 (66.7) | 34.1 | 2.448 | 0.303 | 12.5 | nan | 6 (9) |  |
| MFFU 1x8 | hc1.0 | T2 | coupon | -131 | -196 | 74.9 | -157 / -314 / 58 | 78.2 (72.6) | 10.5 | 0.680 | 0.116 | 17.8 | 14.2 | 20 (30) | -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar |

| plan | edge | periodo | med $/mes | p10 | p90 | P(anio<0) % | mes21 med / p10 / P<0 | neg60 % (mtm) [dias] | evals perd./mes 5 L150 | ctas perd./mes 5 L150 |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 L150 + 3 MFFU | hc0.0 | T1 | 16173 | 9243 | 22837 | 0.0 | 14743 / -1075 / 15 | 4.5 (13.5) [20, 252] | 1.815 | 0.613 |
| 5 L150 + 3 MFFU | hc0.0 | T2 | 14689 | 7041 | 21646 | 0.6 | 13500 / -2150 / 23 | 8.5 (17.3) [20, 252] | 3.069 | 1.105 |
| 5 L150 + 3 MFFU | hc0.35 | T1 | 8824 | 2464 | 15910 | 3.9 | 2664 / -3092 / 36 | 22.3 (31.1) [20, 252] | 3.681 | 1.022 |
| 5 L150 + 3 MFFU | hc0.35 | T2 | 8418 | 1801 | 15613 | 4.2 | 2270 / -3696 / 38 | 22.6 (31.3) [20, 252] | 5.246 | 1.319 |
| 5 L150 + 3 MFFU | hc1.0 | T1 | -789 | -3712 | 5310 | 56.4 | -2621 / -5375 / 76 | 63.4 (65.0) [20, 252] | 10.429 | 1.381 |
| 5 L150 + 3 MFFU | hc1.0 | T2 | -566 | -4182 | 5075 | 55.3 | -3225 / -6317 / 74 | 63.1 (64.8) [20, 252] | 12.226 | 1.552 |
