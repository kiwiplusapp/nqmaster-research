# Experimento 04: umbral de retiro X de la Lucid 150K fondeada — 1000 caminos

Regla: sin cambio: el incumbente X = 6.000 gana la eleccion en T1

| unidad | X | edge | periodo | med $/mes | p10 | P(anio<0) % | neg60 % (mtm) [=0] | evals/anio | evals perd./mes | ctas perd./mes | retiros/anio | aprob. % | dias (p75) | cumple | pareado vs 6.000: med [ci90] P(gain) P(loss>5%) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| asiento | 4600 | hc0.0 | T1 | 2436 | 1437 | 0.0 | 6.7 (18.4) [0.5] | 9.3 | 0.385 | 0.164 | 12.0 | 48.8 | 8 (12) | 2 -med_mes -p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -18 [-486, +405] 0.41 0.28 |
| asiento | 5000 | hc0.0 | T1 | 2468 | 1407 | 0.0 | 7.0 (18.2) [0.5] | 9.0 | 0.376 | 0.151 | 11.8 | 48.7 | 8 (12) | 2 -med_mes -p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -19 [-390, +391] 0.34 0.16 |
| asiento | 6000 | hc0.0 | T1 | 2417 | 1450 | 0.0 | 7.9 (18.6) [0.8] | 8.3 | 0.341 | 0.116 | 11.6 | 49.3 | 8 (12) | 2 -med_mes -p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| asiento | 7000 | hc0.0 | T1 | 2350 | 1468 | 0.0 | 8.4 (19.1) [1.2] | 7.8 | 0.317 | 0.090 | 11.3 | 49.7 | 8 (12) | 2 -med_mes -p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-450, +279] 0.26 0.30 |
| asiento | 8000 | hc0.0 | T1 | 2219 | 1450 | 0.0 | 8.6 (19.7) [1.9] | 7.4 | 0.302 | 0.073 | 11.0 | 49.4 | 8 (12) | 2 -med_mes -p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -18 [-603, +315] 0.30 0.45 |
| asiento | 10000 | hc0.0 | T1 | 2142 | 1278 | 0.1 | 9.4 (21.9) [3.6] | 6.9 | 0.283 | 0.059 | 10.3 | 49.4 | 8 (12) | 2 -med_mes -p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -225 [-864, +261] 0.21 0.67 |
| asiento | 12000 | hc0.0 | T1 | 2125 | 1089 | 0.1 | 10.3 (24.6) [5.3] | 6.6 | 0.275 | 0.054 | 9.7 | 48.8 | 8 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -396 [-1071, +90] 0.12 0.80 |
| asiento | 4600 | hc0.0 | T2 | 2228 | 1204 | 0.1 | 9.5 (20.7) [0.2] | 13.4 | 0.648 | 0.263 | 11.3 | 40.8 | 7 (11) | 2 -med_mes -p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -19 [-552, +360] 0.40 0.26 |
| asiento | 5000 | hc0.0 | T2 | 2238 | 1220 | 0.0 | 10.0 (20.9) [0.3] | 13.1 | 0.635 | 0.253 | 11.2 | 40.8 | 7 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -16 [-413, +359] 0.33 0.17 |
| asiento | 6000 | hc0.0 | T2 | 2242 | 1235 | 0.2 | 11.4 (21.6) [0.3] | 12.4 | 0.597 | 0.224 | 10.9 | 41.0 | 7 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| asiento | 7000 | hc0.0 | T2 | 2206 | 1170 | 0.2 | 12.5 (22.6) [0.4] | 11.8 | 0.565 | 0.201 | 10.7 | 41.2 | 7 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-396, +297] 0.24 0.28 |
| asiento | 8000 | hc0.0 | T2 | 2107 | 1099 | 0.3 | 13.6 (23.6) [0.6] | 11.2 | 0.540 | 0.180 | 10.4 | 41.2 | 7 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -36 [-585, +333] 0.27 0.48 |
| asiento | 10000 | hc0.0 | T2 | 2053 | 964 | 0.4 | 15.6 (26.1) [1.5] | 10.3 | 0.496 | 0.149 | 9.7 | 41.2 | 7 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -207 [-846, +350] 0.24 0.68 |
| asiento | 12000 | hc0.0 | T2 | 1999 | 928 | 0.5 | 16.9 (28.1) [2.8] | 9.7 | 0.466 | 0.132 | 9.1 | 41.2 | 7 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -360 [-1071, +297] 0.16 0.79 |
| asiento | 4600 | hc0.35 | T1 | 1418 | 352 | 3.4 | 23.9 (33.8) [0.8] | 14.4 | 0.808 | 0.229 | 7.8 | 30.7 | 8 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-423, +352] 0.37 0.27 |
| asiento | 5000 | hc0.35 | T1 | 1375 | 357 | 3.8 | 25.0 (34.3) [0.9] | 14.2 | 0.798 | 0.224 | 7.6 | 30.7 | 8 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-417, +330] 0.28 0.20 |
| asiento | 6000 | hc0.35 | T1 | 1378 | 370 | 3.9 | 26.9 (35.2) [1.0] | 13.4 | 0.753 | 0.200 | 7.5 | 30.8 | 8 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| asiento | 7000 | hc0.35 | T1 | 1360 | 369 | 4.1 | 28.2 (35.9) [1.3] | 12.7 | 0.716 | 0.178 | 7.3 | 30.7 | 8 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-280, +271] 0.18 0.25 |
| asiento | 8000 | hc0.35 | T1 | 1342 | 287 | 4.7 | 28.6 (36.1) [2.1] | 12.1 | 0.679 | 0.161 | 7.1 | 30.9 | 8 (10) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-450, +315] 0.26 0.38 |
| asiento | 10000 | hc0.35 | T1 | 1189 | 269 | 5.6 | 29.0 (36.5) [3.8] | 11.1 | 0.622 | 0.133 | 6.7 | 31.1 | 8 (10) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -135 [-675, +369] 0.27 0.55 |
| asiento | 12000 | hc0.35 | T1 | 1035 | 287 | 6.3 | 29.7 (37.2) [6.3] | 10.4 | 0.576 | 0.121 | 6.2 | 31.6 | 8 (10) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -189 [-847, +332] 0.21 0.65 |
| asiento | 4600 | hc0.35 | T2 | 1321 | 306 | 4.1 | 22.2 (33.2) [0.7] | 18.9 | 1.127 | 0.294 | 7.8 | 26.8 | 7 (10) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -10 [-498, +315] 0.33 0.28 |
| asiento | 5000 | hc0.35 | T2 | 1328 | 300 | 4.1 | 23.2 (33.6) [0.8] | 18.6 | 1.112 | 0.288 | 7.7 | 26.9 | 7 (10) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -5 [-391, +295] 0.27 0.20 |
| asiento | 6000 | hc0.35 | T2 | 1342 | 317 | 4.4 | 25.4 (34.5) [0.8] | 17.9 | 1.071 | 0.265 | 7.5 | 26.7 | 7 (10) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| asiento | 7000 | hc0.35 | T2 | 1320 | 317 | 5.1 | 27.5 (35.7) [0.9] | 17.1 | 1.019 | 0.245 | 7.4 | 26.9 | 7 (10) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-280, +279] 0.20 0.26 |
| asiento | 8000 | hc0.35 | T2 | 1270 | 280 | 5.7 | 29.5 (36.7) [1.2] | 16.3 | 0.975 | 0.227 | 7.1 | 27.0 | 7 (10) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-468, +351] 0.25 0.45 |
| asiento | 10000 | hc0.35 | T2 | 1126 | 145 | 7.2 | 32.4 (38.2) [2.0] | 15.3 | 0.915 | 0.198 | 6.6 | 26.8 | 7 (10) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -175 [-657, +368] 0.23 0.63 |
| asiento | 12000 | hc0.35 | T2 | 1010 | 63 | 8.9 | 33.9 (39.1) [3.8] | 14.4 | 0.860 | 0.179 | 6.1 | 26.9 | 7 (10) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -225 [-865, +315] 0.20 0.70 |
| asiento | 4600 | hc1.0 | T1 | -41 | -627 | 52.3 | 59.9 (62.6) [0.6] | 29.8 | 2.114 | 0.279 | 2.8 | 13.2 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-75, +202] 0.26 0.23 |
| asiento | 5000 | hc1.0 | T1 | -52 | -627 | 52.4 | 60.6 (62.9) [0.6] | 29.6 | 2.105 | 0.277 | 2.7 | 13.2 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-46, +197] 0.19 0.21 |
| asiento | 6000 | hc1.0 | T1 | -70 | -627 | 54.3 | 63.2 (64.4) [0.6] | 29.2 | 2.076 | 0.273 | 2.6 | 13.3 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| asiento | 7000 | hc1.0 | T1 | -88 | -645 | 55.7 | 65.8 (65.8) [0.7] | 28.8 | 2.042 | 0.267 | 2.4 | 13.3 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-207, +18] 0.05 0.17 |
| asiento | 8000 | hc1.0 | T1 | -123 | -645 | 56.8 | 68.1 (66.7) [0.8] | 28.2 | 2.003 | 0.258 | 2.3 | 13.3 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-255, +72] 0.10 0.30 |
| asiento | 10000 | hc1.0 | T1 | -223 | -663 | 60.7 | 72.4 (67.9) [1.6] | 27.2 | 1.930 | 0.245 | 1.9 | 13.3 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -18 [-414, +125] 0.10 0.50 |
| asiento | 12000 | hc1.0 | T1 | -277 | -663 | 63.2 | 74.5 (67.8) [2.8] | 26.4 | 1.878 | 0.235 | 1.7 | 13.3 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -153 [-550, +161] 0.10 0.60 |
| asiento | 4600 | hc1.0 | T2 | -80 | -717 | 53.4 | 59.0 (62.3) [0.2] | 35.0 | 2.511 | 0.315 | 3.2 | 12.5 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-178, +258] 0.30 0.25 |
| asiento | 5000 | hc1.0 | T2 | -74 | -728 | 52.9 | 59.7 (62.7) [0.2] | 34.8 | 2.502 | 0.312 | 3.1 | 12.4 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-127, +207] 0.26 0.24 |
| asiento | 6000 | hc1.0 | T2 | -95 | -752 | 55.2 | 63.0 (64.5) [0.2] | 34.1 | 2.448 | 0.303 | 2.9 | 12.5 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| asiento | 7000 | hc1.0 | T2 | -123 | -752 | 56.4 | 65.2 (65.6) [0.3] | 33.6 | 2.412 | 0.297 | 2.7 | 12.5 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-225, +54] 0.07 0.17 |
| asiento | 8000 | hc1.0 | T2 | -141 | -752 | 57.2 | 67.3 (66.6) [0.4] | 33.1 | 2.374 | 0.293 | 2.6 | 12.5 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-253, +108] 0.10 0.30 |
| asiento | 10000 | hc1.0 | T2 | -227 | -753 | 59.8 | 70.3 (67.7) [0.9] | 32.2 | 2.312 | 0.285 | 2.3 | 12.6 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-414, +126] 0.11 0.49 |
| asiento | 12000 | hc1.0 | T2 | -277 | -770 | 60.9 | 72.0 (68.0) [2.0] | 31.3 | 2.251 | 0.271 | 2.1 | 12.5 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -135 [-550, +179] 0.13 0.58 |
| plan | 4600 | hc0.0 | T1 | 16189 | 8985 | 0.0 | 4.1 (13.1) [0.1] | 51.8 | 2.077 | 0.881 | 124.0 | 50.7 | 9 (15) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -85 [-2154, +1706] 0.43 0.20 |
| plan | 5000 | hc0.0 | T1 | 16191 | 9013 | 0.0 | 4.3 (13.1) [0.1] | 50.9 | 2.048 | 0.826 | 123.2 | 50.6 | 9 (15) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -43 [-1875, +1572] 0.43 0.17 |
| plan | 6000 | hc0.0 | T1 | 16173 | 9243 | 0.0 | 4.5 (13.5) [0.2] | 47.3 | 1.892 | 0.650 | 122.1 | 50.9 | 9 (15) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 7000 | hc0.0 | T1 | 15699 | 9267 | 0.1 | 4.4 (13.6) [0.2] | 44.4 | 1.773 | 0.499 | 120.9 | 51.0 | 9 (15) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -100 [-1593, +1280] 0.28 0.21 |
| plan | 8000 | hc0.0 | T1 | 15367 | 8968 | 0.1 | 4.5 (13.6) [0.3] | 42.6 | 1.699 | 0.417 | 119.3 | 51.0 | 9 (15) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -446 [-2458, +1299] 0.25 0.38 |
| plan | 10000 | hc0.0 | T1 | 14829 | 8320 | 0.3 | 4.8 (14.6) [0.6] | 40.0 | 1.588 | 0.345 | 116.1 | 51.4 | 9 (15) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -1117 [-3452, +847] 0.14 0.61 |
| plan | 12000 | hc0.0 | T1 | 14599 | 7613 | 0.3 | 5.4 (16.4) [0.9] | 38.4 | 1.512 | 0.329 | 112.9 | 51.7 | 9 (15) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -1800 [-4410, +269] 0.07 0.79 |
| plan | 4600 | hc0.0 | T2 | 14699 | 7202 | 0.7 | 7.6 (16.8) [0.1] | 74.7 | 3.480 | 1.471 | 111.9 | 43.0 | 8 (13) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -57 [-2459, +1609] 0.44 0.21 |
| plan | 5000 | hc0.0 | T2 | 14661 | 7206 | 0.7 | 8.0 (17.0) [0.1] | 73.6 | 3.431 | 1.420 | 111.2 | 43.0 | 8 (13) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -31 [-2201, +1389] 0.43 0.16 |
| plan | 6000 | hc0.0 | T2 | 14689 | 7041 | 0.6 | 8.5 (17.3) [0.1] | 70.3 | 3.284 | 1.256 | 110.4 | 42.8 | 8 (13) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 7000 | hc0.0 | T2 | 14462 | 6815 | 0.6 | 9.2 (18.1) [0.1] | 66.9 | 3.096 | 1.147 | 109.1 | 43.4 | 8 (13) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -36 [-1765, +1045] 0.24 0.20 |
| plan | 8000 | hc0.0 | T2 | 14243 | 6676 | 0.6 | 9.6 (18.8) [0.2] | 64.5 | 2.996 | 1.043 | 107.5 | 43.2 | 8 (13) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -468 [-2370, +1394] 0.23 0.39 |
| plan | 10000 | hc0.0 | T2 | 13840 | 6159 | 0.9 | 10.6 (20.4) [0.2] | 60.0 | 2.771 | 0.904 | 104.4 | 43.6 | 8 (14) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -1116 [-3692, +1270] 0.16 0.63 |
| plan | 12000 | hc0.0 | T2 | 13455 | 6027 | 1.2 | 11.0 (21.3) [0.6] | 56.5 | 2.602 | 0.812 | 101.2 | 43.8 | 8 (14) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -1734 [-4646, +630] 0.12 0.76 |
| plan | 4600 | hc0.35 | T1 | 8691 | 2258 | 3.3 | 20.0 (29.9) [0.5] | 80.0 | 4.317 | 1.325 | 70.7 | 33.7 | 9 (13) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-1930, +1393] 0.43 0.21 |
| plan | 5000 | hc0.35 | T1 | 8786 | 2182 | 3.3 | 20.8 (30.2) [0.5] | 79.1 | 4.264 | 1.304 | 70.0 | 33.8 | 9 (13) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-1726, +1088] 0.39 0.17 |
| plan | 6000 | hc0.35 | T1 | 8824 | 2464 | 3.9 | 22.3 (31.1) [0.6] | 74.5 | 4.002 | 1.169 | 69.1 | 34.1 | 9 (13) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 7000 | hc0.35 | T1 | 8672 | 2500 | 4.5 | 22.8 (31.6) [0.7] | 70.9 | 3.793 | 1.059 | 68.3 | 34.3 | 9 (13) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-1161, +1154] 0.21 0.23 |
| plan | 8000 | hc0.35 | T1 | 8449 | 2465 | 4.5 | 22.9 (31.7) [1.2] | 67.7 | 3.607 | 0.968 | 67.3 | 34.6 | 9 (13) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -189 [-1812, +1645] 0.25 0.40 |
| plan | 10000 | hc0.35 | T1 | 7708 | 2544 | 4.5 | 23.6 (31.4) [1.7] | 62.7 | 3.321 | 0.832 | 65.3 | 35.0 | 9 (14) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -648 [-2628, +1665] 0.23 0.56 |
| plan | 12000 | hc0.35 | T1 | 7201 | 1915 | 5.5 | 24.5 (32.0) [2.5] | 60.3 | 3.200 | 0.764 | 63.2 | 34.9 | 9 (14) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -992 [-3558, +1213] 0.17 0.68 |
| plan | 4600 | hc0.35 | T2 | 8386 | 1831 | 3.9 | 20.8 (30.6) [0.2] | 105.2 | 6.048 | 1.722 | 68.9 | 29.6 | 8 (13) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -43 [-1986, +1503] 0.38 0.25 |
| plan | 5000 | hc0.35 | T2 | 8466 | 1849 | 4.0 | 21.4 (30.7) [0.2] | 104.0 | 5.971 | 1.687 | 68.6 | 29.7 | 8 (13) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-1600, +1364] 0.35 0.17 |
| plan | 6000 | hc0.35 | T2 | 8418 | 1801 | 4.2 | 22.6 (31.3) [0.3] | 100.0 | 5.721 | 1.593 | 67.6 | 29.9 | 8 (13) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 7000 | hc0.35 | T2 | 8313 | 1820 | 4.7 | 23.9 (32.4) [0.4] | 96.7 | 5.536 | 1.477 | 66.7 | 29.8 | 8 (13) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-1325, +1340] 0.22 0.28 |
| plan | 8000 | hc0.35 | T2 | 7924 | 1449 | 5.6 | 25.7 (33.6) [0.4] | 92.8 | 5.288 | 1.392 | 65.5 | 30.2 | 8 (13) | 2 +med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -307 [-2069, +1916] 0.24 0.47 |
| plan | 10000 | hc0.35 | T2 | 7421 | 1221 | 6.6 | 27.2 (34.5) [0.8] | 87.4 | 4.973 | 1.256 | 62.9 | 30.3 | 8 (14) | 2 +med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -880 [-3196, +1655] 0.23 0.64 |
| plan | 12000 | hc0.35 | T2 | 6877 | 901 | 7.6 | 27.9 (34.7) [1.4] | 83.0 | 4.706 | 1.161 | 60.7 | 30.6 | 8 (14) | 2 +med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -1167 [-3938, +1215] 0.20 0.70 |
| plan | 4600 | hc1.0 | T1 | -573 | -3622 | 55.8 | 60.5 (63.6) [0.3] | 180.4 | 12.583 | 1.775 | 19.2 | 14.2 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-384, +936] 0.28 0.20 |
| plan | 5000 | hc1.0 | T1 | -575 | -3666 | 55.8 | 61.3 (64.0) [0.3] | 179.8 | 12.533 | 1.770 | 18.8 | 14.2 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-252, +934] 0.20 0.18 |
| plan | 6000 | hc1.0 | T1 | -789 | -3712 | 56.4 | 63.4 (65.0) [0.3] | 178.3 | 12.423 | 1.751 | 18.1 | 14.2 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 7000 | hc1.0 | T1 | -917 | -3735 | 57.5 | 65.7 (66.3) [0.2] | 175.8 | 12.250 | 1.721 | 17.3 | 14.2 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-1035, +90] 0.06 0.24 |
| plan | 8000 | hc1.0 | T1 | -1065 | -3763 | 58.7 | 68.1 (67.2) [0.3] | 173.2 | 12.067 | 1.681 | 16.6 | 14.2 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-1208, +459] 0.09 0.39 |
| plan | 10000 | hc1.0 | T1 | -1357 | -3807 | 61.7 | 72.0 (68.1) [0.4] | 168.5 | 11.737 | 1.621 | 15.1 | 14.2 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -225 [-1981, +717] 0.11 0.54 |
| plan | 12000 | hc1.0 | T1 | -1687 | -3840 | 64.5 | 75.0 (68.3) [0.7] | 165.1 | 11.503 | 1.576 | 13.9 | 14.2 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -677 [-2384, +541] 0.11 0.64 |
| plan | 4600 | hc1.0 | T2 | -494 | -3995 | 54.3 | 60.8 (63.6) [0.1] | 206.7 | 14.586 | 1.964 | 20.2 | 13.5 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-936, +1035] 0.34 0.25 |
| plan | 5000 | hc1.0 | T2 | -514 | -4087 | 54.9 | 61.1 (63.8) [0.1] | 205.8 | 14.521 | 1.954 | 19.9 | 13.5 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-714, +1015] 0.28 0.25 |
| plan | 6000 | hc1.0 | T2 | -566 | -4182 | 55.3 | 63.1 (64.8) [0.1] | 202.1 | 14.248 | 1.913 | 18.9 | 13.5 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 7000 | hc1.0 | T2 | -659 | -4228 | 56.1 | 65.2 (65.7) [0.2] | 199.4 | 14.053 | 1.884 | 18.3 | 13.6 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-1035, +179] 0.09 0.21 |
| plan | 8000 | hc1.0 | T2 | -822 | -4250 | 57.4 | 67.2 (66.7) [0.2] | 197.3 | 13.901 | 1.861 | 17.4 | 13.6 | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-1238, +279] 0.10 0.36 |
| plan | 10000 | hc1.0 | T2 | -1213 | -4322 | 60.1 | 70.4 (67.8) [0.5] | 192.4 | 13.547 | 1.803 | 15.8 | 13.6 | 7 (13) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -239 [-2102, +516] 0.11 0.55 |
| plan | 12000 | hc1.0 | T2 | -1679 | -4333 | 62.2 | 72.8 (68.1) [0.9] | 187.9 | 13.230 | 1.744 | 14.5 | 13.6 | 7 (13) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -694 [-2659, +538] 0.12 0.64 |

Historia contigua:

| unidad | X | edge | periodo | n | med $/mes | p10 | neg60 % | evals perd./mes | ctas perd./mes | retiros/anio | cumple |
|---|---|---|---|---|---|---|---|---|---|---|---|
| asiento_contiguo | L150 X4600 | hc0.0 | T1 | 89 | 2157 | 1402 | 11.7 | 0.50 | 0.106 | 11.8 | 1 |
| asiento_contiguo | L150 X5000 | hc0.0 | T1 | 89 | 2009 | 1239 | 13.0 | 0.49 | 0.142 | 11.2 | 1 |
| asiento_contiguo | L150 X6000 | hc0.0 | T1 | 89 | 2107 | 1171 | 16.6 | 0.51 | 0.094 | 11.2 | 1 |
| asiento_contiguo | L150 X7000 | hc0.0 | T1 | 89 | 2053 | 964 | 18.4 | 0.53 | 0.052 | 11.0 | 1 |
| asiento_contiguo | L150 X8000 | hc0.0 | T1 | 89 | 2053 | 964 | 18.0 | 0.53 | 0.045 | 10.7 | 1 |
| asiento_contiguo | L150 X10000 | hc0.0 | T1 | 89 | 2107 | 960 | 15.8 | 0.33 | 0.031 | 9.8 | 1 |
| asiento_contiguo | L150 X12000 | hc0.0 | T1 | 89 | 1728 | 946 | 14.5 | 0.32 | 0.022 | 9.1 | 1 |
| asiento_contiguo | L150 X4600 | hc0.0 | T2 | 137 | 2147 | 507 | 23.1 | 0.68 | 0.278 | 10.0 | 1 |
| asiento_contiguo | L150 X5000 | hc0.0 | T2 | 137 | 2212 | 552 | 24.6 | 0.69 | 0.235 | 9.9 | 1 |
| asiento_contiguo | L150 X6000 | hc0.0 | T2 | 137 | 2467 | 588 | 25.5 | 0.65 | 0.210 | 10.1 | 1 |
| asiento_contiguo | L150 X7000 | hc0.0 | T2 | 137 | 2278 | 370 | 26.0 | 0.63 | 0.200 | 9.7 | 1 |
| asiento_contiguo | L150 X8000 | hc0.0 | T2 | 137 | 2278 | 363 | 26.4 | 0.65 | 0.187 | 9.5 | 1 |
| asiento_contiguo | L150 X10000 | hc0.0 | T2 | 137 | 2314 | 145 | 29.6 | 0.56 | 0.128 | 9.3 | 1 |
| asiento_contiguo | L150 X12000 | hc0.0 | T2 | 137 | 2089 | 138 | 30.9 | 0.59 | 0.126 | 8.6 | 1 |
| asiento_contiguo | L150 X4600 | hc0.35 | T1 | 89 | 1241 | 228 | 31.6 | 0.96 | 0.151 | 7.8 | 1 |
| asiento_contiguo | L150 X5000 | hc0.35 | T1 | 89 | 1263 | 228 | 32.5 | 0.96 | 0.148 | 7.6 | 1 |
| asiento_contiguo | L150 X6000 | hc0.35 | T1 | 89 | 1135 | 275 | 31.1 | 0.91 | 0.109 | 7.4 | 1 |
| asiento_contiguo | L150 X7000 | hc0.35 | T1 | 89 | 1117 | 275 | 32.8 | 0.88 | 0.104 | 7.2 | 1 |
| asiento_contiguo | L150 X8000 | hc0.35 | T1 | 89 | 1117 | 110 | 33.2 | 0.86 | 0.099 | 7.1 | 1 |
| asiento_contiguo | L150 X10000 | hc0.35 | T1 | 89 | 838 | -26 | 34.1 | 0.74 | 0.065 | 5.8 | 1 |
| asiento_contiguo | L150 X12000 | hc0.35 | T1 | 89 | 856 | -186 | 30.2 | 0.66 | 0.049 | 5.2 | 1 |
| asiento_contiguo | L150 X4600 | hc0.35 | T2 | 137 | 1362 | -305 | 29.8 | 1.25 | 0.196 | 7.2 | 1 |
| asiento_contiguo | L150 X5000 | hc0.35 | T2 | 137 | 1437 | -191 | 29.4 | 1.22 | 0.187 | 7.2 | 1 |
| asiento_contiguo | L150 X6000 | hc0.35 | T2 | 137 | 1460 | -295 | 30.1 | 1.32 | 0.167 | 7.1 | 1 |
| asiento_contiguo | L150 X7000 | hc0.35 | T2 | 137 | 1460 | -320 | 30.4 | 1.28 | 0.164 | 7.0 | 1 |
| asiento_contiguo | L150 X8000 | hc0.35 | T2 | 137 | 1153 | -320 | 41.5 | 1.17 | 0.137 | 6.4 | 1 |
| asiento_contiguo | L150 X10000 | hc0.35 | T2 | 137 | 974 | -412 | 41.8 | 1.01 | 0.134 | 6.0 | 1 |
| asiento_contiguo | L150 X12000 | hc0.35 | T2 | 137 | 1153 | -444 | 41.3 | 0.97 | 0.109 | 6.0 | 1 |
| asiento_contiguo | L150 X4600 | hc1.0 | T1 | 89 | -479 | -717 | 71.0 | 2.35 | 0.263 | 2.8 | 1 |
| asiento_contiguo | L150 X5000 | hc1.0 | T1 | 89 | -432 | -717 | 70.2 | 2.33 | 0.263 | 2.8 | 1 |
| asiento_contiguo | L150 X6000 | hc1.0 | T1 | 89 | -591 | -717 | 78.3 | 2.28 | 0.263 | 2.5 | 1 |
| asiento_contiguo | L150 X7000 | hc1.0 | T1 | 89 | -591 | -717 | 79.6 | 2.33 | 0.232 | 2.3 | 1 |
| asiento_contiguo | L150 X8000 | hc1.0 | T1 | 89 | -591 | -717 | 81.6 | 2.28 | 0.230 | 2.0 | 1 |
| asiento_contiguo | L150 X10000 | hc1.0 | T1 | 89 | -591 | -717 | 82.8 | 2.25 | 0.230 | 2.0 | 1 |
| asiento_contiguo | L150 X12000 | hc1.0 | T1 | 89 | -591 | -717 | 82.8 | 2.25 | 0.230 | 2.0 | 1 |
| asiento_contiguo | L150 X4600 | hc1.0 | T2 | 137 | 166 | -878 | 69.3 | 2.77 | 0.217 | 3.2 | 1 |
| asiento_contiguo | L150 X5000 | hc1.0 | T2 | 137 | 173 | -878 | 69.4 | 2.77 | 0.217 | 3.1 | 1 |
| asiento_contiguo | L150 X6000 | hc1.0 | T2 | 137 | 66 | -878 | 72.8 | 2.76 | 0.214 | 2.8 | 1 |
| asiento_contiguo | L150 X7000 | hc1.0 | T2 | 137 | 12 | -878 | 73.7 | 2.75 | 0.214 | 2.8 | 1 |
| asiento_contiguo | L150 X8000 | hc1.0 | T2 | 137 | 12 | -878 | 74.3 | 2.75 | 0.214 | 2.8 | 1 |
| asiento_contiguo | L150 X10000 | hc1.0 | T2 | 137 | -6 | -878 | 81.4 | 2.69 | 0.214 | 2.4 | 1 |
| asiento_contiguo | L150 X12000 | hc1.0 | T2 | 137 | -34 | -878 | 80.8 | 2.62 | 0.213 | 2.4 | 1 |
| plan_contiguo | plan X4600 | hc0.0 | T1 | 84 | 13020 | 7586 | 9.0 | 2.59 | 0.527 | 114.2 | 4 |
| plan_contiguo | plan X5000 | hc0.0 | T1 | 84 | 11855 | 7268 | 10.0 | 2.54 | 0.722 | 111.2 | 3 |
| plan_contiguo | plan X6000 | hc0.0 | T1 | 84 | 12685 | 6925 | 12.5 | 2.62 | 0.474 | 111.2 | 3 |
| plan_contiguo | plan X7000 | hc0.0 | T1 | 84 | 12526 | 6385 | 12.5 | 2.76 | 0.274 | 110.1 | 3 |
| plan_contiguo | plan X8000 | hc0.0 | T1 | 84 | 12570 | 6329 | 12.3 | 2.73 | 0.237 | 108.8 | 3 |
| plan_contiguo | plan X10000 | hc0.0 | T1 | 84 | 12383 | 6023 | 12.8 | 1.73 | 0.168 | 104.4 | 3 |
| plan_contiguo | plan X12000 | hc0.0 | T1 | 84 | 10790 | 5647 | 11.6 | 1.75 | 0.123 | 100.8 | 3 |
| plan_contiguo | plan X4600 | hc0.0 | T2 | 132 | 16603 | 1529 | 21.5 | 3.64 | 1.530 | 108.0 | 2 |
| plan_contiguo | plan X5000 | hc0.0 | T2 | 132 | 17163 | 1615 | 22.0 | 3.67 | 1.306 | 107.4 | 3 |
| plan_contiguo | plan X6000 | hc0.0 | T2 | 132 | 18522 | 2101 | 22.4 | 3.48 | 1.177 | 108.5 | 3 |
| plan_contiguo | plan X7000 | hc0.0 | T2 | 132 | 17865 | 1233 | 23.8 | 3.36 | 1.136 | 106.5 | 2 |
| plan_contiguo | plan X8000 | hc0.0 | T2 | 132 | 18050 | 985 | 23.8 | 3.44 | 1.066 | 105.7 | 2 |
| plan_contiguo | plan X10000 | hc0.0 | T2 | 132 | 17725 | 189 | 27.4 | 2.99 | 0.774 | 104.4 | 1 |
| plan_contiguo | plan X12000 | hc0.0 | T2 | 132 | 16343 | -124 | 27.6 | 3.12 | 0.751 | 101.3 | 1 |
| plan_contiguo | plan X4600 | hc0.35 | T1 | 84 | 6159 | 703 | 31.9 | 5.28 | 0.990 | 69.1 | 2 |
| plan_contiguo | plan X5000 | hc0.35 | T1 | 84 | 6161 | 757 | 33.0 | 5.25 | 0.977 | 68.3 | 2 |
| plan_contiguo | plan X6000 | hc0.35 | T1 | 84 | 6163 | 894 | 30.8 | 5.03 | 0.769 | 67.2 | 2 |
| plan_contiguo | plan X7000 | hc0.35 | T1 | 84 | 5852 | 894 | 32.1 | 4.87 | 0.745 | 66.1 | 2 |
| plan_contiguo | plan X8000 | hc0.35 | T1 | 84 | 5852 | 732 | 32.9 | 4.77 | 0.720 | 65.3 | 2 |
| plan_contiguo | plan X10000 | hc0.35 | T1 | 84 | 4867 | -153 | 37.9 | 4.13 | 0.558 | 58.9 | 1 |
| plan_contiguo | plan X12000 | hc0.35 | T1 | 84 | 4815 | -1176 | 42.2 | 3.73 | 0.473 | 55.9 | 1 |
| plan_contiguo | plan X4600 | hc0.35 | T2 | 132 | 11000 | -1723 | 28.1 | 6.83 | 1.044 | 70.3 | 2 |
| plan_contiguo | plan X5000 | hc0.35 | T2 | 132 | 11282 | -1437 | 27.5 | 6.70 | 0.999 | 70.6 | 2 |
| plan_contiguo | plan X6000 | hc0.35 | T2 | 132 | 11285 | -1502 | 27.5 | 7.20 | 0.895 | 69.9 | 2 |
| plan_contiguo | plan X7000 | hc0.35 | T2 | 132 | 11231 | -1742 | 27.4 | 7.00 | 0.883 | 69.6 | 2 |
| plan_contiguo | plan X8000 | hc0.35 | T2 | 132 | 9592 | -1954 | 32.5 | 6.47 | 0.749 | 66.5 | 2 |
| plan_contiguo | plan X10000 | hc0.35 | T2 | 132 | 9494 | -2241 | 34.6 | 5.65 | 0.733 | 64.5 | 2 |
| plan_contiguo | plan X12000 | hc0.35 | T2 | 132 | 9813 | -2522 | 35.9 | 5.41 | 0.616 | 64.6 | 2 |
| plan_contiguo | plan X4600 | hc1.0 | T1 | 84 | -2983 | -4190 | 74.4 | 14.02 | 1.636 | 21.3 | 1 |
| plan_contiguo | plan X5000 | hc1.0 | T1 | 84 | -2750 | -4158 | 71.8 | 13.90 | 1.636 | 21.3 | 1 |
| plan_contiguo | plan X6000 | hc1.0 | T1 | 84 | -3583 | -4212 | 79.3 | 13.68 | 1.636 | 19.8 | 1 |
| plan_contiguo | plan X7000 | hc1.0 | T1 | 84 | -3583 | -4212 | 80.1 | 13.95 | 1.488 | 19.3 | 1 |
| plan_contiguo | plan X8000 | hc1.0 | T1 | 84 | -3583 | -4212 | 80.8 | 13.72 | 1.478 | 17.8 | 1 |
| plan_contiguo | plan X10000 | hc1.0 | T1 | 84 | -3583 | -4212 | 82.7 | 13.55 | 1.478 | 17.5 | 1 |
| plan_contiguo | plan X12000 | hc1.0 | T1 | 84 | -3583 | -4212 | 82.7 | 13.55 | 1.478 | 17.5 | 1 |
| plan_contiguo | plan X4600 | hc1.0 | T2 | 132 | 878 | -5078 | 71.1 | 16.11 | 1.242 | 23.9 | 0 |
| plan_contiguo | plan X5000 | hc1.0 | T2 | 132 | 776 | -5078 | 71.2 | 16.11 | 1.242 | 23.8 | 0 |
| plan_contiguo | plan X6000 | hc1.0 | T2 | 132 | 512 | -5078 | 73.2 | 16.01 | 1.231 | 22.3 | 0 |
| plan_contiguo | plan X7000 | hc1.0 | T2 | 132 | 346 | -5078 | 74.1 | 16.00 | 1.231 | 22.2 | 0 |
| plan_contiguo | plan X8000 | hc1.0 | T2 | 132 | 305 | -5078 | 74.4 | 15.96 | 1.231 | 21.9 | 0 |
| plan_contiguo | plan X10000 | hc1.0 | T2 | 132 | -210 | -5078 | 82.3 | 15.70 | 1.231 | 20.1 | 0 |
| plan_contiguo | plan X12000 | hc1.0 | T2 | 132 | -353 | -5078 | 81.7 | 15.36 | 1.228 | 19.9 | 0 |
