# Experimento 03: tamano de la eval de Lucid 150K (k contratos) — 1000 caminos

Regla: sin cambio: el incumbente 6c gana la eleccion en T1

| unidad | k | edge | periodo | med $/mes | p10 | P(anio<0) % | neg60 % (mtm) [=0] | evals/anio | evals perd./mes | aprob. % | p22_3 % | dias (p75) | cumple | pareado vs 6c: med [ci90] P(gain) P(loss>5%) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| asiento | 1 | hc0.0 | T1 | 1089 | 171 | 8.7 | 10.6 (21.9) [40.5] | 2.4 | 0.000 | 100.0 | 3.0 | 75 (105) | 2 -med_mes -p10_mes -neg60 +evals_perdidas_mes +aprobacion -dias_aprobar | -1450 [-2333, -495] 0.00 0.98 |
| asiento | 2 | hc0.0 | T1 | 1746 | 846 | 0.8 | 13.3 (26.4) [14.9] | 3.4 | 0.017 | 92.8 | 21.3 | 35 (55) | 2 -med_mes -p10_mes -neg60 +evals_perdidas_mes +aprobacion -dias_aprobar | -792 [-1710, -28] 0.05 0.90 |
| asiento | 3 | hc0.0 | T1 | 2160 | 1052 | 0.2 | 14.3 (25.4) [4.6] | 4.7 | 0.087 | 75.9 | 38.1 | 21 (33) | 2 -med_mes -p10_mes -neg60 +evals_perdidas_mes +aprobacion -dias_aprobar | -396 [-1143, +108] 0.16 0.78 |
| asiento | 4 | hc0.0 | T1 | 2178 | 1242 | 0.1 | 11.2 (21.6) [1.7] | 6.4 | 0.201 | 59.9 | 54.0 | 12 (21) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -171 [-882, +262] 0.34 0.56 |
| asiento | 5 | hc0.0 | T1 | 2368 | 1414 | 0.0 | 8.7 (19.2) [1.0] | 7.4 | 0.268 | 54.7 | 66.4 | 10 (15) | 2 -med_mes -p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-577, +297] 0.45 0.30 |
| asiento | 6 | hc0.0 | T1 | 2417 | 1450 | 0.0 | 7.9 (18.6) [0.8] | 8.3 | 0.341 | 49.3 | 69.3 | 8 (12) | 2 -med_mes -p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| asiento | 1 | hc0.0 | T2 | 1053 | -36 | 18.7 | 19.7 (27.4) [42.0] | 2.6 | 0.007 | 95.4 | 4.3 | 76 (105) | 2 -med_mes -p10_mes -neg60 +evals_perdidas_mes +aprobacion -dias_aprobar | -1432 [-2540, -370] 0.01 0.98 |
| asiento | 2 | hc0.0 | T2 | 1260 | 360 | 3.0 | 29.4 (37.7) [7.5] | 5.0 | 0.107 | 71.1 | 21.3 | 31 (46) | 2 -med_mes -p10_mes -neg60 +evals_perdidas_mes +aprobacion -dias_aprobar | -828 [-1783, -10] 0.05 0.91 |
| asiento | 3 | hc0.0 | T2 | 1710 | 792 | 1.2 | 23.5 (31.2) [1.4] | 7.1 | 0.225 | 59.4 | 39.8 | 18 (28) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -464 [-1296, +179] 0.14 0.79 |
| asiento | 4 | hc0.0 | T2 | 2071 | 982 | 0.4 | 16.9 (26.1) [0.4] | 9.2 | 0.359 | 51.2 | 58.0 | 12 (19) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -171 [-972, +315] 0.31 0.63 |
| asiento | 5 | hc0.0 | T2 | 2174 | 1117 | 0.3 | 13.4 (23.3) [0.4] | 10.9 | 0.486 | 45.1 | 67.0 | 9 (13) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +0 [-693, +397] 0.46 0.40 |
| asiento | 6 | hc0.0 | T2 | 2242 | 1235 | 0.2 | 11.4 (21.6) [0.3] | 12.4 | 0.597 | 41.0 | 71.3 | 7 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| asiento | 1 | hc0.35 | T1 | 189 | -36 | 39.3 | 17.0 (23.3) [57.7] | 2.1 | 0.008 | 93.3 | 2.4 | 93 (138) | 2 -med_mes -p10_mes -neg60 +evals_perdidas_mes +aprobacion -dias_aprobar | -928 [-2071, +26] 0.06 0.93 |
| asiento | 2 | hc0.35 | T1 | 1035 | -72 | 16.6 | 36.6 (43.9) [17.7] | 4.1 | 0.097 | 67.0 | 14.5 | 35 (56) | 2 -med_mes -p10_mes -neg60 +evals_perdidas_mes +aprobacion -dias_aprobar | -532 [-1503, +215] 0.16 0.78 |
| asiento | 3 | hc0.35 | T1 | 1018 | 82 | 7.4 | 38.6 (44.5) [4.2] | 6.8 | 0.268 | 49.0 | 30.7 | 18 (29) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -253 [-1089, +251] 0.27 0.67 |
| asiento | 4 | hc0.35 | T1 | 1242 | 271 | 4.4 | 32.1 (38.9) [1.7] | 8.8 | 0.408 | 41.7 | 42.4 | 11 (19) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -10 [-676, +315] 0.48 0.47 |
| asiento | 5 | hc0.35 | T1 | 1360 | 388 | 4.1 | 29.0 (36.6) [1.3] | 11.0 | 0.567 | 35.9 | 49.0 | 9 (14) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +18 [-450, +279] 0.59 0.29 |
| asiento | 6 | hc0.35 | T1 | 1378 | 370 | 3.9 | 26.9 (35.2) [1.0] | 13.4 | 0.753 | 30.8 | 54.2 | 8 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| asiento | 1 | hc0.35 | T2 | 171 | -54 | 45.2 | 25.5 (30.9) [51.6] | 2.5 | 0.036 | 74.7 | 2.9 | 92 (127) | 2 -med_mes -p10_mes -neg60 +evals_perdidas_mes +aprobacion -dias_aprobar | -946 [-2071, +52] 0.06 0.91 |
| asiento | 2 | hc0.35 | T2 | 896 | -108 | 17.0 | 46.3 (51.7) [11.0] | 5.8 | 0.214 | 50.0 | 17.2 | 32 (50) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -532 [-1585, +233] 0.15 0.82 |
| asiento | 3 | hc0.35 | T2 | 982 | 28 | 8.1 | 41.1 (46.3) [2.7] | 8.8 | 0.401 | 41.4 | 30.6 | 19 (29) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -289 [-1117, +269] 0.23 0.70 |
| asiento | 4 | hc0.35 | T2 | 1135 | 163 | 7.4 | 34.0 (40.4) [1.2] | 12.4 | 0.647 | 35.0 | 43.1 | 12 (18) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -135 [-882, +233] 0.32 0.61 |
| asiento | 5 | hc0.35 | T2 | 1288 | 281 | 4.5 | 28.3 (36.0) [0.9] | 14.3 | 0.768 | 33.8 | 54.1 | 9 (13) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +18 [-639, +368] 0.54 0.40 |
| asiento | 6 | hc0.35 | T2 | 1342 | 317 | 4.4 | 25.4 (34.5) [0.8] | 17.9 | 1.071 | 26.7 | 51.2 | 7 (10) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| asiento | 1 | hc1.0 | T1 | -54 | -72 | 91.4 | 49.9 (50.4) [47.2] | 3.2 | 0.150 | 18.4 | 1.4 | 78 (116) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +34 [-1117, +627] 0.52 0.47 |
| asiento | 2 | hc1.0 | T1 | -125 | -179 | 66.6 | 80.9 (80.5) [6.7] | 8.0 | 0.486 | 18.9 | 7.9 | 28 (43) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +98 [-856, +538] 0.57 0.41 |
| asiento | 3 | hc1.0 | T1 | -156 | -305 | 61.1 | 79.3 (77.5) [1.1] | 13.6 | 0.873 | 19.2 | 20.5 | 14 (21) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +94 [-739, +430] 0.63 0.37 |
| asiento | 4 | hc1.0 | T1 | -98 | -430 | 54.9 | 72.2 (70.9) [0.7] | 19.2 | 1.286 | 17.0 | 29.2 | 10 (14) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +107 [-514, +377] 0.63 0.37 |
| asiento | 5 | hc1.0 | T1 | -34 | -538 | 51.7 | 65.6 (66.6) [0.8] | 24.8 | 1.735 | 13.9 | 28.3 | 7 (11) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +72 [-243, +315] 0.77 0.21 |
| asiento | 6 | hc1.0 | T1 | -70 | -627 | 54.3 | 63.2 (64.4) [0.6] | 29.2 | 2.076 | 13.3 | 29.5 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| asiento | 1 | hc1.0 | T2 | -54 | -90 | 87.8 | 51.5 (52.0) [44.7] | 3.4 | 0.172 | 17.1 | 1.0 | 88 (127) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +88 [-1136, +735] 0.55 0.45 |
| asiento | 2 | hc1.0 | T2 | -125 | -215 | 63.4 | 80.2 (79.9) [6.5] | 9.1 | 0.561 | 18.1 | 9.0 | 27 (42) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +151 [-857, +627] 0.60 0.39 |
| asiento | 3 | hc1.0 | T2 | -44 | -358 | 53.1 | 75.0 (74.9) [0.7] | 15.8 | 1.043 | 16.9 | 20.6 | 14 (22) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +169 [-568, +520] 0.70 0.29 |
| asiento | 4 | hc1.0 | T2 | -57 | -502 | 53.0 | 70.9 (70.5) [0.2] | 23.0 | 1.580 | 15.1 | 27.6 | 9 (14) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +143 [-479, +412] 0.65 0.35 |
| asiento | 5 | hc1.0 | T2 | -115 | -645 | 56.5 | 68.8 (69.0) [0.2] | 29.3 | 2.088 | 12.7 | 28.6 | 7 (13) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +54 [-468, +251] 0.63 0.36 |
| asiento | 6 | hc1.0 | T2 | -95 | -752 | 55.2 | 63.0 (64.5) [0.2] | 34.1 | 2.448 | 12.5 | 30.8 | 6 (9) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 1 | hc0.0 | T1 | 9171 | 3001 | 0.8 | 6.0 (11.7) [6.4] | 16.2 | 0.078 | 92.8 | — | 60 (92) | 5 +med_mes +p10_mes +neg60 +evals_perdidas_mes +aprobacion -dias_aprobar | -7163 [-10929, -2857] 0.00 0.99 |
| plan | 2 | hc0.0 | T1 | 12342 | 5988 | 0.2 | 6.6 (14.8) [2.2] | 21.8 | 0.192 | 88.1 | — | 32 (50) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes +aprobacion -dias_aprobar | -3973 [-7446, -380] 0.03 0.93 |
| plan | 3 | hc0.0 | T1 | 14398 | 7358 | 0.0 | 6.0 (15.1) [0.8] | 28.3 | 0.535 | 75.6 | — | 21 (33) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes +aprobacion -dias_aprobar | -2142 [-5285, +410] 0.10 0.77 |
| plan | 4 | hc0.0 | T1 | 15252 | 8542 | 0.1 | 5.4 (14.7) [0.3] | 36.9 | 1.141 | 61.3 | — | 14 (23) | 3 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -892 [-3475, +934] 0.25 0.53 |
| plan | 5 | hc0.0 | T1 | 15803 | 9161 | 0.0 | 4.5 (13.8) [0.2] | 42.1 | 1.489 | 56.3 | — | 10 (18) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -100 [-2234, +1225] 0.41 0.26 |
| plan | 6 | hc0.0 | T1 | 16173 | 9243 | 0.0 | 4.5 (13.5) [0.2] | 47.3 | 1.892 | 50.9 | — | 9 (15) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 1 | hc0.0 | T2 | 7646 | 1502 | 2.4 | 13.9 (18.4) [5.0] | 20.6 | 0.269 | 80.9 | — | 52 (87) | 2 +med_mes -p10_mes -neg60 -evals_perdidas_mes +aprobacion -dias_aprobar | -7331 [-11653, -1745] 0.01 0.98 |
| plan | 2 | hc0.0 | T2 | 10542 | 3309 | 1.8 | 14.3 (21.8) [1.2] | 32.0 | 0.745 | 69.4 | — | 27 (41) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes +aprobacion -dias_aprobar | -4161 [-8166, +4] 0.05 0.90 |
| plan | 3 | hc0.0 | T2 | 12700 | 5346 | 1.1 | 12.7 (21.5) [0.4] | 42.6 | 1.356 | 59.7 | — | 18 (27) | 2 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -2073 [-5643, +718] 0.13 0.77 |
| plan | 4 | hc0.0 | T2 | 13957 | 5963 | 0.7 | 10.8 (19.5) [0.2] | 52.9 | 1.989 | 53.3 | — | 13 (20) | 2 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -828 [-4248, +1287] 0.28 0.53 |
| plan | 5 | hc0.0 | T2 | 14425 | 6628 | 0.5 | 9.6 (18.3) [0.1] | 62.2 | 2.667 | 47.2 | — | 9 (16) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | -163 [-2727, +1880] 0.41 0.34 |
| plan | 6 | hc0.0 | T2 | 14689 | 7041 | 0.6 | 8.5 (17.3) [0.1] | 70.3 | 3.284 | 42.8 | — | 8 (13) | 4 +med_mes +p10_mes +neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 1 | hc0.35 | T1 | 3715 | -94 | 12.9 | 25.7 (28.3) [11.7] | 19.2 | 0.361 | 71.4 | — | 55 (109) | 2 +med_mes -p10_mes -neg60 -evals_perdidas_mes +aprobacion -dias_aprobar | -4788 [-9506, -113] 0.05 0.94 |
| plan | 2 | hc0.35 | T1 | 6596 | 234 | 9.2 | 27.8 (33.1) [4.3] | 28.9 | 0.800 | 62.5 | — | 32 (52) | 1 +med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -2601 [-6828, +828] 0.12 0.82 |
| plan | 3 | hc0.35 | T1 | 7356 | 736 | 6.8 | 27.7 (34.3) [1.6] | 41.8 | 1.620 | 50.3 | — | 19 (31) | 1 +med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -1264 [-5052, +1041] 0.22 0.67 |
| plan | 4 | hc0.35 | T1 | 8268 | 1640 | 4.6 | 24.9 (32.6) [0.9] | 51.8 | 2.294 | 44.5 | — | 13 (22) | 2 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -253 [-3232, +1315] 0.42 0.46 |
| plan | 5 | hc0.35 | T1 | 8670 | 2278 | 4.1 | 22.9 (31.5) [0.7] | 62.5 | 3.084 | 38.9 | — | 11 (18) | 2 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +72 [-2055, +1259] 0.56 0.28 |
| plan | 6 | hc0.35 | T1 | 8824 | 2464 | 3.9 | 22.3 (31.1) [0.6] | 74.5 | 4.002 | 34.1 | — | 9 (13) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 1 | hc0.35 | T2 | 2834 | -318 | 15.6 | 31.9 (31.9) [9.6] | 24.6 | 0.637 | 61.9 | — | 43 (91) | 1 +med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -4854 [-10320, +186] 0.06 0.93 |
| plan | 2 | hc0.35 | T2 | 5888 | -187 | 12.1 | 33.1 (35.9) [3.1] | 40.9 | 1.508 | 51.3 | — | 27 (43) | 1 +med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -2670 [-7481, +1035] 0.13 0.84 |
| plan | 3 | hc0.35 | T2 | 6870 | 495 | 7.5 | 30.7 (36.1) [1.3] | 55.5 | 2.445 | 44.1 | — | 19 (29) | 1 +med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -1316 [-5332, +1280] 0.22 0.70 |
| plan | 4 | hc0.35 | T2 | 7648 | 983 | 5.9 | 27.4 (34.4) [0.5] | 72.8 | 3.624 | 38.0 | — | 13 (21) | 1 +med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | -695 [-3781, +1145] 0.29 0.60 |
| plan | 5 | hc0.35 | T2 | 8323 | 1876 | 5.0 | 24.1 (32.1) [0.4] | 83.0 | 4.295 | 36.1 | — | 9 (16) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +18 [-2845, +1629] 0.51 0.38 |
| plan | 6 | hc0.35 | T2 | 8418 | 1801 | 4.2 | 22.6 (31.3) [0.3] | 100.0 | 5.721 | 29.9 | — | 8 (13) | 3 +med_mes +p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 1 | hc1.0 | T1 | -624 | -936 | 77.8 | 80.9 (74.8) [4.5] | 47.3 | 2.768 | 18.4 | — | 22 (42) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +308 [-5093, +3118] 0.53 0.46 |
| plan | 2 | hc1.0 | T1 | -998 | -1473 | 68.0 | 81.1 (77.0) [1.1] | 72.1 | 4.483 | 18.5 | — | 21 (34) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +470 [-3829, +2616] 0.58 0.41 |
| plan | 3 | hc1.0 | T1 | -857 | -2071 | 60.3 | 76.5 (74.1) [0.4] | 99.6 | 6.388 | 18.6 | — | 15 (22) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +440 [-3107, +2169] 0.64 0.35 |
| plan | 4 | hc1.0 | T1 | -734 | -2686 | 56.7 | 70.8 (69.9) [0.2] | 127.0 | 8.424 | 17.2 | — | 11 (16) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +495 [-1910, +1950] 0.63 0.36 |
| plan | 5 | hc1.0 | T1 | -522 | -3223 | 55.5 | 65.3 (66.6) [0.2] | 155.1 | 10.670 | 14.9 | — | 9 (14) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +340 [-1324, +1559] 0.74 0.25 |
| plan | 6 | hc1.0 | T1 | -789 | -3712 | 56.4 | 63.4 (65.0) [0.3] | 178.3 | 12.423 | 14.2 | — | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |
| plan | 1 | hc1.0 | T2 | -640 | -991 | 77.2 | 79.9 (74.5) [6.9] | 48.9 | 2.910 | 17.7 | — | 26 (49) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +144 [-5411, +3674] 0.52 0.48 |
| plan | 2 | hc1.0 | T2 | -941 | -1578 | 66.6 | 79.7 (75.4) [2.1] | 77.4 | 4.883 | 17.9 | — | 24 (36) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +435 [-4606, +3171] 0.57 0.43 |
| plan | 3 | hc1.0 | T2 | -598 | -2250 | 56.1 | 74.0 (72.3) [0.3] | 111.1 | 7.279 | 17.3 | — | 16 (25) | 0 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion -dias_aprobar | +757 [-2925, +2526] 0.68 0.32 |
| plan | 4 | hc1.0 | T2 | -600 | -2997 | 56.6 | 69.7 (68.9) [0.1] | 146.1 | 9.844 | 16.3 | — | 10 (18) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +657 [-2359, +1989] 0.67 0.33 |
| plan | 5 | hc1.0 | T2 | -930 | -3728 | 59.0 | 68.4 (68.3) [0.1] | 178.8 | 12.506 | 13.8 | — | 9 (15) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | +251 [-2699, +1249] 0.61 0.37 |
| plan | 6 | hc1.0 | T2 | -566 | -4182 | 55.3 | 63.1 (64.8) [0.1] | 202.1 | 14.248 | 13.5 | — | 7 (12) | 1 -med_mes -p10_mes -neg60 -evals_perdidas_mes -aprobacion +dias_aprobar | — |

Historia contigua:

| unidad | k | edge | periodo | n | med $/mes | p10 | neg60 % | evals perd./mes | aprob. % | dias | cumple |
|---|---|---|---|---|---|---|---|---|---|---|---|
| asiento_contiguo | L150 1c/3c | hc0.0 | T1 | 89 | 1089 | -36 | 10.5 | 0.00 | 100.0 | 74 | 2 |
| asiento_contiguo | L150 2c/3c | hc0.0 | T1 | 89 | 1296 | 621 | 15.5 | 0.03 | 88.6 | 32 | 2 |
| asiento_contiguo | L150 3c/3c | hc0.0 | T1 | 89 | 1225 | 603 | 24.4 | 0.10 | 72.2 | 21 | 2 |
| asiento_contiguo | L150 4c/3c | hc0.0 | T1 | 89 | 1503 | 789 | 25.3 | 0.25 | 53.5 | 11 | 0 |
| asiento_contiguo | L150 5c/3c | hc0.0 | T1 | 89 | 2089 | 1171 | 16.0 | 0.38 | 42.9 | 7 | 1 |
| asiento_contiguo | L150 6c/3c | hc0.0 | T1 | 89 | 2107 | 1171 | 16.6 | 0.51 | 37.4 | 7 | 1 |
| asiento_contiguo | L150 1c/3c | hc0.0 | T2 | 137 | 621 | -54 | 24.7 | 0.03 | 83.7 | 85 | 2 |
| asiento_contiguo | L150 2c/3c | hc0.0 | T2 | 137 | 1728 | 118 | 37.8 | 0.14 | 60.6 | 34 | 0 |
| asiento_contiguo | L150 3c/3c | hc0.0 | T2 | 137 | 2125 | 325 | 29.7 | 0.22 | 55.8 | 21 | 0 |
| asiento_contiguo | L150 4c/3c | hc0.0 | T2 | 137 | 2278 | 253 | 29.2 | 0.43 | 44.6 | 15 | 0 |
| asiento_contiguo | L150 5c/3c | hc0.0 | T2 | 137 | 2467 | 406 | 25.8 | 0.53 | 42.3 | 9 | 1 |
| asiento_contiguo | L150 6c/3c | hc0.0 | T2 | 137 | 2467 | 588 | 25.5 | 0.65 | 38.9 | 9 | 1 |
| asiento_contiguo | L150 1c/3c | hc0.35 | T1 | 89 | 171 | -36 | 12.3 | 0.02 | 72.5 | 124 | 2 |
| asiento_contiguo | L150 2c/3c | hc0.35 | T1 | 89 | 568 | -108 | 41.3 | 0.15 | 52.2 | 48 | 0 |
| asiento_contiguo | L150 3c/3c | hc0.35 | T1 | 89 | 982 | -125 | 40.0 | 0.30 | 45.2 | 18 | 0 |
| asiento_contiguo | L150 4c/3c | hc0.35 | T1 | 89 | 928 | -46 | 43.2 | 0.36 | 43.3 | 13 | 0 |
| asiento_contiguo | L150 5c/3c | hc0.35 | T1 | 89 | 1207 | 217 | 32.7 | 0.57 | 29.3 | 9 | 1 |
| asiento_contiguo | L150 6c/3c | hc0.35 | T1 | 89 | 1135 | 275 | 31.1 | 0.91 | 21.6 | 9 | 1 |
| asiento_contiguo | L150 1c/3c | hc0.35 | T2 | 137 | 171 | -54 | 26.3 | 0.05 | 65.2 | 98 | 2 |
| asiento_contiguo | L150 2c/3c | hc0.35 | T2 | 137 | 792 | -108 | 47.7 | 0.22 | 45.3 | 46 | 0 |
| asiento_contiguo | L150 3c/3c | hc0.35 | T2 | 137 | 1225 | -186 | 46.0 | 0.37 | 41.3 | 22 | 0 |
| asiento_contiguo | L150 4c/3c | hc0.35 | T2 | 137 | 1235 | -294 | 45.1 | 0.78 | 25.6 | 16 | 0 |
| asiento_contiguo | L150 5c/3c | hc0.35 | T2 | 137 | 1432 | -176 | 35.1 | 0.87 | 26.9 | 11 | 0 |
| asiento_contiguo | L150 6c/3c | hc0.35 | T2 | 137 | 1460 | -295 | 30.1 | 1.32 | 18.7 | 7 | 1 |
| asiento_contiguo | L150 1c/3c | hc1.0 | T1 | 89 | -54 | -90 | 45.4 | 0.16 | 16.7 | 140 | 0 |
| asiento_contiguo | L150 2c/3c | hc1.0 | T1 | 89 | -125 | -197 | 76.7 | 0.50 | 11.7 | 30 | 0 |
| asiento_contiguo | L150 3c/3c | hc1.0 | T1 | 89 | -269 | -322 | 83.3 | 0.93 | 19.5 | 8 | 1 |
| asiento_contiguo | L150 4c/3c | hc1.0 | T1 | 89 | -376 | -448 | 84.7 | 1.44 | 14.4 | 8 | 1 |
| asiento_contiguo | L150 5c/3c | hc1.0 | T1 | 89 | -520 | -609 | 78.9 | 1.98 | 11.3 | 7 | 1 |
| asiento_contiguo | L150 6c/3c | hc1.0 | T1 | 89 | -591 | -717 | 78.3 | 2.28 | 12.4 | 6 | 1 |
| asiento_contiguo | L150 1c/3c | hc1.0 | T2 | 137 | -54 | -97 | 51.5 | 0.17 | 20.0 | 135 | 0 |
| asiento_contiguo | L150 2c/3c | hc1.0 | T2 | 137 | -125 | -233 | 82.4 | 0.58 | 12.1 | 10 | 1 |
| asiento_contiguo | L150 3c/3c | hc1.0 | T2 | 137 | 235 | -376 | 82.3 | 1.06 | 15.1 | 21 | 0 |
| asiento_contiguo | L150 4c/3c | hc1.0 | T2 | 137 | 245 | -591 | 81.1 | 1.75 | 11.8 | 10 | 1 |
| asiento_contiguo | L150 5c/3c | hc1.0 | T2 | 137 | 20 | -752 | 81.6 | 2.40 | 7.9 | 5 | 1 |
| asiento_contiguo | L150 6c/3c | hc1.0 | T2 | 137 | 66 | -878 | 72.8 | 2.76 | 9.1 | 8 | 1 |
| plan_contiguo | plan k1 | hc0.0 | T1 | 84 | 7492 | 906 | 7.8 | 0.09 | 91.5 | 48 | 4 |
| plan_contiguo | plan k2 | hc0.0 | T1 | 84 | 8299 | 3887 | 12.1 | 0.22 | 86.3 | 32 | 3 |
| plan_contiguo | plan k3 | hc0.0 | T1 | 84 | 8509 | 3823 | 16.4 | 0.58 | 72.8 | 23 | 3 |
| plan_contiguo | plan k4 | hc0.0 | T1 | 84 | 9567 | 4143 | 18.4 | 1.31 | 56.6 | 16 | 2 |
| plan_contiguo | plan k5 | hc0.0 | T1 | 84 | 12784 | 7278 | 12.1 | 2.00 | 45.8 | 8 | 3 |
| plan_contiguo | plan k6 | hc0.0 | T1 | 84 | 12685 | 6925 | 12.5 | 2.62 | 40.2 | 7 | 3 |
| plan_contiguo | plan k1 | hc0.0 | T2 | 132 | 9156 | -441 | 26.5 | 0.38 | 74.2 | 61 | 2 |
| plan_contiguo | plan k2 | hc0.0 | T2 | 132 | 14858 | -123 | 28.5 | 0.97 | 60.8 | 29 | 1 |
| plan_contiguo | plan k3 | hc0.0 | T2 | 132 | 16542 | 945 | 25.6 | 1.29 | 57.5 | 25 | 1 |
| plan_contiguo | plan k4 | hc0.0 | T2 | 132 | 16918 | 765 | 25.0 | 2.41 | 46.5 | 16 | 1 |
| plan_contiguo | plan k5 | hc0.0 | T2 | 132 | 18481 | 1212 | 23.2 | 2.91 | 44.3 | 12 | 1 |
| plan_contiguo | plan k6 | hc0.0 | T2 | 132 | 18522 | 2101 | 22.4 | 3.48 | 41.0 | 10 | 3 |
| plan_contiguo | plan k1 | hc0.35 | T1 | 84 | 923 | -439 | 42.8 | 0.62 | 52.4 | 43 | 0 |
| plan_contiguo | plan k2 | hc0.35 | T1 | 84 | 3483 | -746 | 47.6 | 1.27 | 49.0 | 39 | 1 |
| plan_contiguo | plan k3 | hc0.35 | T1 | 84 | 5125 | -662 | 41.1 | 2.00 | 44.7 | 19 | 1 |
| plan_contiguo | plan k4 | hc0.35 | T1 | 84 | 5274 | -751 | 43.6 | 2.29 | 43.4 | 20 | 1 |
| plan_contiguo | plan k5 | hc0.35 | T1 | 84 | 6584 | 1298 | 31.7 | 3.35 | 32.1 | 12 | 1 |
| plan_contiguo | plan k6 | hc0.35 | T1 | 84 | 6163 | 894 | 30.8 | 5.03 | 24.5 | 10 | 2 |
| plan_contiguo | plan k1 | hc0.35 | T2 | 132 | 3993 | -620 | 35.8 | 0.88 | 46.5 | 45 | 1 |
| plan_contiguo | plan k2 | hc0.35 | T2 | 132 | 6485 | -905 | 36.6 | 1.73 | 41.6 | 35 | 1 |
| plan_contiguo | plan k3 | hc0.35 | T2 | 132 | 9648 | -1190 | 36.0 | 2.45 | 39.4 | 23 | 1 |
| plan_contiguo | plan k4 | hc0.35 | T2 | 132 | 9419 | -1447 | 35.2 | 4.49 | 26.5 | 17 | 1 |
| plan_contiguo | plan k5 | hc0.35 | T2 | 132 | 11442 | -1497 | 32.5 | 4.97 | 27.3 | 11 | 1 |
| plan_contiguo | plan k6 | hc0.35 | T2 | 132 | 11285 | -1502 | 27.5 | 7.20 | 19.9 | 8 | 2 |
| plan_contiguo | plan k1 | hc1.0 | T1 | 84 | -779 | -1072 | 85.4 | 3.07 | 16.9 | 26 | 0 |
| plan_contiguo | plan k2 | hc1.0 | T1 | 84 | -1191 | -1578 | 81.5 | 4.80 | 13.8 | 25 | 0 |
| plan_contiguo | plan k3 | hc1.0 | T1 | 84 | -1856 | -2278 | 86.7 | 7.00 | 18.6 | 12 | 0 |
| plan_contiguo | plan k4 | hc1.0 | T1 | 84 | -2461 | -2850 | 86.1 | 9.46 | 15.0 | 9 | 1 |
| plan_contiguo | plan k5 | hc1.0 | T1 | 84 | -3171 | -3664 | 79.3 | 12.20 | 12.3 | 8 | 1 |
| plan_contiguo | plan k6 | hc1.0 | T1 | 84 | -3583 | -4212 | 79.3 | 13.68 | 13.0 | 8 | 1 |
| plan_contiguo | plan k1 | hc1.0 | T2 | 132 | -372 | -1267 | 82.5 | 3.07 | 14.2 | 48 | 0 |
| plan_contiguo | plan k2 | hc1.0 | T2 | 132 | -606 | -1945 | 84.1 | 5.10 | 11.8 | 24 | 0 |
| plan_contiguo | plan k3 | hc1.0 | T2 | 132 | 1200 | -2662 | 82.8 | 7.47 | 14.1 | 24 | 0 |
| plan_contiguo | plan k4 | hc1.0 | T2 | 132 | 1077 | -3739 | 81.8 | 10.93 | 11.6 | 10 | 1 |
| plan_contiguo | plan k5 | hc1.0 | T2 | 132 | -12 | -4544 | 82.4 | 14.20 | 8.4 | 6 | 1 |
| plan_contiguo | plan k6 | hc1.0 | T2 | 132 | 512 | -5078 | 73.2 | 16.01 | 9.3 | 11 | 0 |
