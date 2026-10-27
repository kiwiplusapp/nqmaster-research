# Experimento 01 (frente 5A): realismo de ejecución y paridad — borrador 2026-10-27

**Veredicto H1/H2: los fills de 1 minuto de NinjaTrader (Standard) no sobreestiman el neto. Con fills de 1 tick el neto es +0,4 % (IC 95 % −0,0 % .. +0,7 %) sobre 388 trades de 2026-06-01 → 2026-10-23, 0 cambios de desenlace. Regla 5A.4: el IC queda entero por encima de −15 %, así que ningún neto del programa se recalcula por fills; la lista de trades Standard sigue siendo la referencia del motor de campaña.** Período: CFD/MNQ futuros 2026-06-22 → 2026-10-23 (ticks de Continuum desde el 2026-05-31; 1 día excluido por 19 minutos sin ticks). n = 388 pares (392 trades por lado). Costos: $1,90 por contrato + 1 tick por lado en los dos lados (Standard lo trae; a la serie de ticks, donde NinjaTrader no aplica slippage, se le suma el mismo tick y se desplazan con él los brackets que la estrategia calcula desde el fill).

## Cómo se midió

1. `NQMaster.cs` con la propiedad `FillSeries` (parche reproducible `research/mine/patch_fillseries.py`, v4.2): con Tick1 agrega una serie de 1 tick, manda todas las órdenes ahí y reemplaza `SetStopLoss`/`SetProfitTarget` por brackets explícitos `StopX`/`TargetX` en esa serie (NinjaTrader deja los `Set*` en la serie primaria: 0 de 283 fills con hora de tick en la corrida v3). Con Off el export es **idéntico byte a byte** al pre-parche (4 pruebas). `OrderFillResolution.High` no existe para estrategias multi-serie (P0).
2. Dos corridas del Strategy Analyzer sobre el mismo período y el mismo *Days to load* (el ATR de Wilder hace que dos inicios distintos den otros niveles): Off y Tick1. `research/mine/fill_gap.py` empareja trade a trade (fecha, módulo, dirección, ±3 min), reporta Δticks de entrada y salida, Δ$/trade con IC 95 %, flips y cambios de desenlace, y verifica en qué serie llenó cada orden (segundos ≠ :00) y fills imposibles contra `mnq_fut.npz`.
3. Tratamiento del slippage, una sola vez: Standard trae 1 tick en entradas a mercado/stop y en salidas stop/mercado; a Tick1 se le suma el mismo tick (`--slip-b 1`) y los niveles de bracket calculados desde `EntryPx` se mueven con el fill (1 tick en módulos con stop/target en ticks y en el break-even de VOLB; 1 + R ticks en el target de los módulos `PriceTarget`; 0 en stops absolutos). Sin ese desplazamiento cada bracket leía exactamente 1 tick peor (−3,5 % espurio). El slippage real (H5) reemplaza la hipótesis por celda, nunca se suma.

## Resultado (Off v4.2 vs Tick1 v4.2, `research/nt_exports/2026-10-26/v42/fill_gap_h1.md`)

| Tipo de entrada | n | Δ entrada (ticks) | Δ salida (ticks) | Δ$/trade (IC 95 %) | Total |
|---|---|---|---|---|---|
| Mercado | 274 | −0,08 | 0,00 | +0,04 (−0,01 .. +0,09) | +$10 |
| Stop | 83 | +0,02 | −0,16 | +0,07 (−0,06 .. +0,20) | +$6 |
| Límite | 31 | −0,26 | +0,06 | +0,10 (−0,20 .. +0,39) | +$3 |
| Total | 388 | −0,07 | −0,03 | +0,05 (−0,00 .. +0,10) | +$19 (+0,4 %) |

(+ = peor en Tick1.) Desenlaces: stop 111/111, target 169/169, tiempo 108/108; flips 0,0 %. Las entradas límite (LON) llenan mejor en ticks porque el fill atraviesa el nivel; 15 de 111 `StopX` llenan 1 tick a través del nivel (VOLB, 2 veces 2 ticks): ese es todo el "slippage de precio" que el modelo de 1 minuto no ve. Tiempo de cómputo: ×20 por barra de 1 minuto (66,7 s para 144 k barras y 236 M ticks).

**Alcance.** 4 meses, un solo período, perfil Ultra, 1 contrato, datos demo de Continuum. No dice nada de la liquidez con 6 contratos (eso es H5) ni de los módulos que no operaron en la ventana (ENG10, ENG26, RSI2). Un replay de ticks sobre 2024-26 (Databento) queda descartado: el IC no cruza −15 %.

## Hallazgos de mecánica destapados por la comparación (corregidos en v4.2, `docs/experimentos/01_revision_parche_fillseries.md`)

- `EntryBar` de los fills a mercado: NinjaTrader en Standard carga el fill a la barra que envió la orden aunque llene en la apertura siguiente; v4.1 lo ponía una barra después en Tick1 y 48 de 108 salidas por MaxHold salían tarde. Corregido por tipo de orden; verificado: v4.2 vs v4.1 difieren exactamente en esas 49 salidas y en nada más.
- `Core.Globals.Now` es el reloj de la PC bajo la conexión Playback: `LateBar()` rechazaba todas las barras reproducidas (el Market Replay no entró nunca) y `RollDue()` leía la fecha real. Ahora `NowClock()` usa la última barra de 1 min en Playback. Verificado en Playback Off (16-oct): en tiempo real `CurrentBars[0]` es la última barra cerrada, igual que el motor Standard, así que las entradas a mercado tienen el mismo `EntryBar` en vivo y en backtest; para entradas stop/límite queda un residuo de una barra sin consumidor práctico en Ultra (documentado, candidato v4.3).
- `atrDaily` (Wilder, k = 14) depende del primer día cargado: Days to load = 120 fijo en el runbook.

## S2 (2026-10-27): paridad por módulo, causas trade por trade y parches

Baseline (export Standard de P1 contra `ultra_d4`, 2024-01-22 → 2026-10-08): G1 91,0 %, G3 0,918, G4 falla en ORFAIL 34 %, RV11 54 %, CAM3 56 %, MSEQS 56 %, ICT 80 %, SO04 89 %; 243 trades solo-NT (+$7.719) y 295 solo-investigación (+$1.380). Tres revisores con contexto limpio clasificaron los no emparejados (informes en el scratchpad de la sesión; lo esencial está acá).

| Causa | Trades | Lado equivocado (regla del plan: referencia = investigación salvo información no disponible en tiempo real) | Corrección |
|---|---|---|---|
| **(a) Tendencia apagada 20 sesiones** tras una sesión de Globex sin barras RTH (2025-01-09 duelo Carter, 2026-04-03 Viernes Santo): `research/ict.py` calculaba la SMA 20 con `min_periods=20` sobre una tabla con NaN; NT usa los últimos ≤ 20 cierres que existen, mínimo 15 | 100 solo-NT (12 módulos con filtro de tendencia) | Investigación (artefacto de datos) | `ict.py` / `ict_fix.py` / `foundations.py`: SMA sobre los cierres que existen, ≥ 15, la sesión sin RTH conserva la tendencia. Verificado: solo cambian los días con tendencia 0 (166 sesiones 2010-26 en `nqdb`, 85 en `mnq_fut`) |
| **(c) Medias ruedas**: NT no opera con `SkipShortSessions = true` (25 cierres 13:00 ET); la investigación sí | 59 solo-investigación | Lista de investigación (regla operativa de NT, calendario conocido) | `six_build.py`: fuera los días con último RTH < 15:59 |
| **(d) Instrumento**: el set `ultra_d4` está construido sobre NQ (`nqdb.npz`); NT opera MNQ. Señales al borde del umbral, volumen relativo de RV11 (NQ ≤ 0,8 vs MNQ > 0,8), patrones de 5 min que no existen en el otro | 13 ICT, 5 MSEQS, 16 RV11, ~10 de bordes | Ninguno: medición | `build_parity_mnq.py` → `research_set('ultra_d4_mnq')`: mismas reglas sobre `mnq_fut.npz` (CPI09 conserva sus trades NQ) |
| **ORFAIL / CAM3 (port):** `SixEnter` descartaba la señal cuando `DirectionAllowed` la difería por una stop opuesta de VOLB trabajando, sin reintento (TimeEntry y MSEQ sí reintentan) | 62 de 69 ORFAIL y 13 de 14 CAM3 solo-investigación | NT | `patch_parity_s2.py` (1): reintento en la barra siguiente con el mismo stop/target |
| **ICT (port):** al diferir, volvía a armar la búsqueda de 5 min y exigía el gatillo otra vez | 5 perdidos + 4 fills 9-26 min tarde | NT | `patch_parity_s2.py` (2): el setup se guarda y el límite se coloca en la barra de 1 min siguiente |
| **ICT (investigación, lookahead):** `ict_fix.py` consumía LonH/LonL con barras de 18:00-02:00, antes de que exista el rango de Londres | 2 solo-NT | Investigación | `ict_fix.py`: solo barras 05:00-09:29 consumen esos niveles (como `SetupIctLevels`). ICT vuelve a validación: standalone T1 PF 1,26 → 1,38, **T2 PF 1,15 → 1,09 (+4 ticks 1,04; ya estaba bajo el 1,2 del protocolo)** |
| **MSEQS (port):** NT exigía el fill real de ORB60 corto; la regla validada usa la señal cruda de ORB60 (ruptura del mínimo del rango en día de pullback bajista), que el filtro ORBt descarta | 7 de 12 solo-investigación | NT (la regla usa solo información disponible) | `patch_parity_s2.py` (3): señal virtual `orbSigDir` y gate `closeMin > orbSigMin` |
| `conflict_filter` (posición opuesta solo en la investigación), umbrales al borde, VW13 2.º lote (dedup correcto) | 23 solo-NT, ~9 bordes | Ninguno | — |

**Paridad después de los parches Python (sin tocar el export de NT):** sobre `ultra_d4` (NQ) G1 91,2 %, G3 0,925, SO04 92,6 % pasa, RV11 67,7 %; sobre **`ultra_d4_mnq` (MNQ): G1 95,5 % (pasa), G2 −1,5 % (pasa), G3 0,937 (< 0,95), 11 módulos en 100 %, VOLB 94,5 %, MOM11/MOM13 98,4 %, LON 98,8 %**; quedan en rojo exactamente los módulos del parche NT: ORFAIL 34,9 %, CAM3 55,6 %, MSEQS 68,2 %, ICT 88,5 %. Proyección con el parche NT (conteos de los revisores): ORFAIL ~93 %, CAM3 ~97 %, MSEQS 22/22, ICT ~96 %, G1 ~98 %.

**Efecto de los fixes sobre la investigación (`ultra_d4`, sin re-optimizar):** T1 2020-23 n 3.977 → 4.068, PF 1,462 → 1,458, Sharpe 3,53 → 3,55, DD $4.667 → $4.681; T2 2024-26 n 3.421 → 3.505, PF 1,500 → 1,492, $/mes 2.557 → 2.589, Sharpe 4,03 → 3,99, DD y peor mes iguales. Módulos: ICT T2 PF 1,09 (ver arriba); CAM3 T2 PF 0,78 → 0,74 (ya negativo en 2024-26, como en `six_oos`); el resto ±0,05 de PF.

**Revisión adversarial del parche NT (`patch_parity_s2.py`, 27-oct) y disposición (v2):**

| Sev. | Hallazgo | Disposición |
|---|---|---|
| media | El reintento de ORFAIL/CAM3 entraba aunque la barra de la deferral hubiera cruzado el stop (`pend5` descarta en ese caso): orden a mercado que llena más allá del stop → "filled beyond stop", una vuelta de comisión; la investigación habría perdido 1R, que NT no puede reproducir. | **Corregido (v2):** se descarta con `Log("… dropped (stop crossed during the deferral)")`. Sesgo residual documentado: NT salta esos perdedores, como ya hace `pend5`. |
| baja | Reintento perdido en silencio si la barra siguiente retorna antes del despacho (noticias, flatten, `!canTrade`, `LateBar`). | **Corregido (v2):** `Log("… dropped (bar skipped)")`. |
| baja | Un solo reintento: en vivo, si la cancelación de la stop opuesta no se confirmó en la barra siguiente, se vuelve a diferir y la señal se pierde; sin efecto en el Analyzer. | Aceptado: visible en el Output; se mide en Playback. |
| baja | `ictPendQty` no se re-escalaba al pasar a vivo (como `pend5Qty` y `ParkQty`). | **Corregido (v2).** Documentado: una señal diferida en la última barra histórica dispara en la primera en vivo (ventana ≤ 5 min), igual que `m.Retry`. |
| baja | ICT pendiente bloqueado por una POSICIÓN opuesta esperaba 5 barras y se descartaba; el camino directo lo aparca (`ParkSetup`). | **Corregido (v2):** si `DirectionAllowed` falla sin `lastDeferred`, se aparca con el límite, extremo y vencimiento guardados. |
| baja | Si el límite fue tocado en la barra de la deferral, la investigación llena en la siguiente y NT no lo sabe (llena tarde o nunca; si además violó el extremo, descarta). | Inherente a diferir una barra; causa residual documentada. |
| baja | La señal virtual de ORB60 exige `orb.On` y rango 60 (el OR solo se trackea para módulos encendidos): Custom con ORB60 apagado → MSEQS nunca habilita (igual que antes). | Documentado en el código. |
| info | `pullbackDay` queda NaN la sesión posterior a una media rueda (heredado); ahora también afecta al gate de MSEQS. `orbFirstDir/orbFirstMin` sin lectores. | Verificar en la próxima paridad; cosmético. |

Verificado por el revisor: resets por sesión, `lastDeferred` leído en la misma sentencia que `SixEnter`, ManageVolb respeta `deferUntil` y no recoloca la stop antes del reintento, `CurrentBars[1]` válido en el bloque de 1 min, sin doble orden ICT (la serie primaria se procesa primero y el gatillo de 5 min hace `continue` con `ictPendDir != 0`), la señal virtual reproduce `nt_v3_replica` (dirección = tendencia, `l[i] <= orl − tick`, ventana < 13:00, PR < 0,44) y `closeMin > orbSigMin` ⇔ `last1 >= first_short`. Verificación directa pendiente en el Output del Analyzer: un MSEQS en el mismo 5 min que la línea `ORB60 raw short signal`.

**Reproducibilidad:** `cd research/mine && rm wrq_entries_db.pkl && python3 -c "import db_long; db_long.entries_db()" && python3 cand16.py && python3 six_base.py && python3 regen_six_keys.py && python3 six_build.py` (3 min) regenera `ultra_d4`; `python3 wrq_build.py && python3 wrq_feats.py && python3 build_parity_mnq.py` (1,5 min) regenera `ultra_d4_mnq`; `python3 parity_check.py <csv> --set ultra_d4_mnq`. Código NT: `cp archive/backups/NQMaster_backup_pre_fillseries.cs NQMaster.cs && python3 research/mine/patch_fillseries.py && python3 research/mine/patch_parity_s2.py && bash tools/nt8_stub/check.sh NQMaster.cs`.

## S3 (2026-10-27): lista corregida, neto por módulo y recálculo de campaña

**Lista corregida.** H1 no exige corrección de fills (+0,4 %, IC −0,0 .. +0,7 %) y H5 espera cuentas prop, así que la "lista con `u` ajustado por celda" es la propia lista regenerada: `six_ultra6_trades.pkl` (`research_set('ultra_d4')`, NQ, campaña) y `six_ultra6_trades_mnq.pkl` (`ultra_d4_mnq`, paridad), con la tendencia corregida, las medias ruedas fuera, el lookahead de ICT corregido e ICT a 1 contrato. No se crea un `_exec.pkl` aparte: los ajustes por celda son cero hasta H5.

**Neto por módulo, 1 contrato base (MOM1030/CPI09 ×4, ICT ×1), $/mes, antes → después de la corrección** (sets construidos con el mismo constructor sobre el código del commit 90d8755 y sobre el actual; IS = CFD 2020-02..2023, C24 = CFD 2024-26, REAL = MNQ 2024-26; filtro de conflictos aplicado):

| Módulo | IS | C24 | REAL | Módulo | IS | C24 | REAL |
|---|---|---|---|---|---|---|---|
| VOLB | 276 → 276 | 595 → 595 | 545 → 542 | LF0430 | 40 → 37 | 66 → 50 | 54 → 53 |
| ORB60 | 234 → 234 | 286 → 286 | 334 → 334 | ON07 | 29 → 32 | 46 → 52 | 42 → 52 |
| CRT11 | 129 → 129 | 229 → 229 | 252 → 252 | VW13 | 54 → 58 | 58 → 58 | 42 → 47 |
| MOM1030 | 60 → 52 | 128 → 129 | 224 → 209 | SO04 | 28 → 28 | 64 → 60 | 41 → 45 |
| CPI09 | 105 → 105 | 198 → 198 | 207 → 207 | LATE15 | 46 → 45 | 32 → 31 | 32 → 43 |
| MSEQ | 239 → 239 | 196 → 192 | 185 → 192 | ORFAIL | 42 → 42 | 12 → 10 | 54 → 41 |
| MOM11 | 70 → 70 | 117 → 116 | 190 → 181 | RV11 | 30 → 30 | −8 → −8 | 38 → 38 |
| ORB90 | 162 → 162 | 126 → 126 | 174 → 174 | LF06 | 24 → 24 | 35 → 35 | 40 → 35 |
| MOM13 | 142 → 151 | 168 → 170 | 150 → 153 | ICT | 43 → 21 | 53 → 32 | 61 → 28 |
| LON | 66 → 56 | 138 → 134 | 133 → 139 | REV06 | 32 → 28 | 40 → 43 | 15 → 27 |
| NF05 | 72 → 72 | 81 → 77 | 92 → 90 | CAM3 | 8 → 7 | 16 → 16 | 4 → 2 |
| MSEQS | 60 → 60 | 55 → 55 | 63 → 63 | **Total** | **1.990 → 1.956** | **2.731 → 2.687** | **2.974 → 2.946** |

Totales: PF 1,49 → 1,48 / 1,53 → 1,52 / 1,61 → 1,58; Sharpe 3,84 → 3,79 / 4,16 → 4,08 / 4,70 → 4,57; DD $4.219 → $4.282 / $3.624 → $3.466 / $3.989 → $3.722. La baja del neto es ICT ×2 → ×1 (−$22 / −$21 / −$33 por mes); la tendencia corregida agrega trades a MOM13, ON07, LON, VW13, LATE15 y ORFAIL con efecto neto ≈ 0; ORFAIL y MOM1030 en REAL bajan por el filtro de conflictos con los trades nuevos.

**Campaña (arnés `prop_wf`, mismo código y semillas, caminos reconstruidos desde la lista corregida; `integ_paired.py`, `integ_port.py`, `integ_budget.py`).** Los caminos vivían en un scratchpad de otra sesión (no reproducible); ahora se reconstruyen en `research/tmp/scratch` (`acct_2027.build()`, lista de días `days_real()`, medias ruedas a P&L 0 como NT). Plan 5 × Lucid Flex 150K 6c/3c + 3 × MFFU 1x8, $/mes con cupón, mediana (p10) antes → después:

| Edge | 2020-23 | 2024-26 |
|---|---|---|
| Completo | 16.280 (9.529) → **16.173 (9.243)** | 14.739 (7.238) → **14.689 (7.041)** |
| −35 % | 8.838 (2.188) → **8.824 (2.464)** | 8.610 (2.000) → **8.418 (1.801)**; P(año negativo) 5,0 → 4,2 % |
| Cero | −699 (−3.660) → **−789 (−3.712)** | −266 (−4.005) → **−566 (−4.182)** |

Por asiento (mediana $/mes): Lucid 150K edge completo 2.467 → 2.417 / 2.260 → 2.242, −35 % 1.423 → 1.378 / 1.406 → 1.342, cuentas perdidas por año 1,51 → 1,39 / 2,75 → 2,69; MFFU 1x8 1.414 → 1.388 / 1.163 → 1.184, −35 % 717 → 703 / 503 → 510. Las reglas pre-registradas de incumbentes no cambian (Lucid 150K 6c/3c y MFFU 1x8 siguen). Precio de lista y presupuesto por plaza: mismas diferencias (≤ 2 %). **Veredicto S3: la corrección de datos y la paridad no mueven la campaña más allá del ruido de la propia corrección (−0,7 % a −2,2 % de mediana; p10 −3 % a +12 %); las cifras del runbook se actualizan con estos valores.**

## Pendiente del experimento

- **H3, paridad (S2 hecha en la nube; falta la PC):** F5 del parche `patch_parity_s2.py`, Off 2024 → hoy byte a byte igual al Off de v4.2 **salvo** ORFAIL/CAM3/ICT/MSEQS (los únicos módulos tocados), export de trades → `parity_check.py <csv> --set ultra_d4_mnq`: objetivo G1 ≥ 92 %, G3 ≥ 0,95 y los cuatro módulos ≥ 90 %. Después: VOLB 94,5 % y G3 (correlación diaria) si no llegan al 0,95 con el parche; `mnq_fut.npz` tiene 3 días sin barras RTH (2025-08-29, 2026-01-23, 2026-09-28) que no son feriados: revisar el export de barras. Los cuatro módulos de 6 años siguen "paridad pendiente" en el runbook hasta ese export.
- **H5, slippage real por módulo × franja (P3): en espera.** Al 27-oct no hay cuentas prop operando, así que no hay fills reales; la hipótesis de 1 tick por lado (+4 en estrés) sigue en todas las cifras. Cuando haya exports de cuentas prop, `research/mine/slip_model.py` reemplaza la hipótesis por celda con n ≥ 15. Sim101 en vivo mide el motor de simulación de NinjaTrader (bid/ask del feed, como Playback), no un bróker: solo como respaldo etiquetado.
- **Neto por contrato por mes por módulo en IS/C24/REAL:** entregado en S3 con la hipótesis de 1 tick; se recalcula con el slippage real cuando haya cuentas prop (H5).
- Playback Tick1 con 6 contratos (13-15 oct, modo Historical): **pasó** — 16/16 trades iguales al backtest Tick1 (misma barra de entrada y salida, brackets a 1-4 s), fills parciales por volumen de tick con re-dimensión de brackets, NinjaTrader reduce y cancela el hermano, 59 órdenes todas Filled/Cancelled, 90 lotes dentro = 90 fuera, 0 huérfanas. Playback Off del 16-oct (1 contrato): **10/10 trades en la misma barra que el backtest Off, las tres salidas por MaxHold/hora fija incluidas → sin off-by-one de `EntryBar` en vivo para entradas a mercado**; residuo acotado para entradas stop/límite (VOLB/ENG10 MaxHold 400, `orbFirstMin` ±1 min), candidato v4.3 de una línea documentado en `v42/README.md`.

## Reproducibilidad

`cp archive/backups/NQMaster_backup_pre_fillseries.cs NQMaster.cs && python3 research/mine/patch_fillseries.py && bash tools/nt8_stub/check.sh NQMaster.cs` regenera el código. `cd research/mine && python3 fill_gap.py ../nt_exports/2026-10-26/v41/trades_off_2026-06-01_hoy.csv ../nt_exports/2026-10-26/v42/trades_tick1_2026-06-01_hoy.csv --slip-b 1 --slip-b-scope all --exclude-dates 20260625 --research ultra_d4` regenera la tabla. Autotest: `fill_gap.py x.csv x.csv` → 100 % emparejado, Δ = 0.
