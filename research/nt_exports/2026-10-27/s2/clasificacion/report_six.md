# Paridad módulos de seis años (ORFAIL, CAM3, RV11, SO04): causas trade por trade

Export Standard 2024-01-22 → 2026-10-08 (MNQ, 1 contrato, Ultra). Investigación = `six_ultra6_trades.pkl` filtrado por `wrq_port.conflict_filter` (nt_compare.py:44-48). Método: reglas lado a lado, cruce de los no emparejados con el export de **trades y de órdenes** de NT, y re-ejecución de los generadores de investigación con los parámetros exactos sobre NQ (`nqdb.npz`) y sobre **MNQ** (`mnq_fut.npz`, lo que ve NinjaTrader). Scripts y salidas en `scratchpad/s2/work/` (a_cross, b_replay, c_compare, d_orders, f_calib, g_replica, h_rows).

## Parámetros exactos (six_reselect.json) y port

| Módulo | Investigación | NT |
|---|---|---|
| ORFAIL = OR_FAIL#142 `{T:15, w1:1400, bk:0.1, tfb:5, tg:'opp', tf:1}` hold 240 | families5.py:171-204 (`_orfail`), 207, 211 | OrfTrack NQMaster.cs:1040-1064, NewMod 573 (R 1.0, MaxHold 240) |
| CAM3 = PIVOT_FADE#365 `{piv:CAM3, w0:1000, w1:1530, sweep:0, conf:10, tg:1(VWAP), R:1, tf:1}` hold 240 | families2.py:36-47 + families.py:183-213 (`_lfade`) | Cam3Track 1067-1083, niveles 833-834, NewMod 574 |
| RV11 = RVOL_DRIVE#4226 `{T:1100, cond:('lo',0.8), ref:'pdc', x:0.25, dm:1, tf:0, k:0.15, R:1}` hold 400 | families5.py:78-108 | AddTime 571 (1100, lb −7 = full1, 0.15, R 1, hold 400, trend false), RvolMax 1103-1108 |
| SO04 = CLOCK_ANCHOR#1527 `{anc:SOPEN, T:400, x:0.35, mode:1, s:0.15, R:1, tg:0, tf:1, hold:330}` | families.py:463-496 | AddTime 569 (401, lb −1 = sessOpen, 0.15, R 1, 330, trend true), MinDist 0.35 |

Las cuatro lógicas de señal son equivalentes línea a línea (ventanas, umbrales, cierre de 5 min `(openMin-570)%5==4` ≡ `(sm[j]-sm[r])%5==4`, stop/target, tendencia SMA20 de cierres RTH: ict.py:52-53 ≡ NQMaster.cs:868-871). **Prueba:** el generador de investigación sobre barras MNQ reproduce 53/69 ORFAIL y 12/14 CAM3 research_only en la misma fecha, minuto y dirección → el dato no explica el faltante; lo explica el flujo de entrada de NT.

## ORFAIL — 105 inv. / 40 NT / 36 emparejados (34 %)

| Causa | n (ro / no) | Evidencia | Lado equivocado | Cambio |
|---|---|---|---|---|
| **Señal descartada por orden opuesta trabajando (VOLB) sin reintento.** `SixEnter` → `DirectionAllowed(d)` (1016) → bucle 1946 parquea/cancela la stop opuesta y devuelve false (1947); a diferencia de `TimeEntry` (800-802) y `pend5` (788-796) no hay reintento y `orfDone` ya quedó en true (1057). VOLB tiene una stop trabajando desde las 09:31 del lado más cercano al cierre (921, 952), que tras una ruptura fallida es casi siempre el opuesto a la señal. | **62 / 0** (+1 "flip") | Réplica NT sobre MNQ: VOLB opuesta trabajando en la barra de señal en 62/69 research_only vs 5/36 emparejados (emparejados: 18 VOLB ya llenada, 9 cambiando de lado, 4 mismo lado). Export de órdenes: 41 órdenes ORFAIL, todas Filled (ninguna cancelada → la orden nunca se envió); en 46/69 casos aparece una cancelación de VOLB **del lado opuesto a la señal** 2 barras después (vs 1/36 emparejados, base 0,03 cancelaciones/min); mismo patrón +2 en 16 MOM11 diferidos (calibración). | **NT (bug de port)** | Ver cambio 1 |
| Media sesión (cierre 13:00): NT no opera (`SkipShortSessions=true` 416, CanTrade 1964); la lista de investigación las incluye (six_build.py:20 solo quita FOMC/ATR) | 1 / 0 (20250526) | days_nq.csv: 26 sesiones con último RTH < 15:59 en 2024-26 | Lista de investigación (filtro operativo de NT documentado) | Cambio 3 |
| Tendencia = 0 en investigación 20 días tras sesión sin barras RTH (2025-01-09, 2026-04-03): `rth.c.rolling(20,min_periods=20)` sobre índice con NaN (ict.py:42,52-53); NT conserva `trendDir` (868) | 0 / 1 (20250121) | days_nq.csv: trend==0 en 20250110-20250206 y 20260406-20260501 | **Investigación** (artefacto, no es la regla) | Cambio 2 |
| Divergencia de cartera: `conflict_filter` quita el trade porque en investigación VOLB estaba abierta en contra; en NT esa VOLB no existía | 0 / 2 (20250516, 20260929) | g_replica.py: "research opposite open: VOLB", "NT opposite open: []" | Ninguno (consecuencia de otros desajustes de VOLB) | — |
| Dato NQ vs MNQ (señal en otro cierre de 5 min) | 0 / 1 (20240227: NT 11:45, inv. 11:55; MNQ dispara 11:45) | replay_mnq.csv | Ninguno | — |
| Sin determinar | 5 / 0 (20240416, 20250723, 20250818*, 20260911, 20261008**) | *NT no operó nada ese día; **fuera del rango de mnq_fut.npz | — | — |

## CAM3 — 32 / 26 / 18 (56 %)

| Causa | n (ro / no) | Evidencia | Lado | Cambio |
|---|---|---|---|---|
| Igual que ORFAIL: señal descartada por VOLB opuesta trabajando (1016, 1946-1947), sin reintento; `camDone=true` (1076) | **13 / 0** | Réplica: VOLB opuesta en 13/14 research_only vs 0/18 emparejados (17/18 VOLB ya llenada). Órdenes: VOLB del lado opuesto cancelada o **llenada** 2 barras después en 12/14 | NT (port) | Cambio 1 |
| conflict_filter (VOLB opuesta abierta solo en investigación) | 0 / 4 (20240723, 20250516, 20251017, 20260710) | g_replica.py | Ninguno | — |
| Tendencia 0 (ventana post 2026-04-03) | 0 / 1 (20260421) | days_nq.csv | Investigación | Cambio 2 |
| Dato NQ vs MNQ (la regla sobre MNQ sí dispara: 7/8 nt_only) | 0 / 3 (20240408, 20260311, 20260826) | replay_mnq.csv | Ninguno | — |
| Sin determinar | 1 / 0 (20250924) | VOLB ya llenada misma dirección; sin orden CAM3 | — | — |

## RV11 — 39 / 29 / 21 (54 %)

| Causa | n (ro / no) | Evidencia | Lado | Cambio |
|---|---|---|---|---|
| Media sesión (feriados con cierre 13:00) | **8 / 0** | 20241128, 20241224, 20250526, 20250619, 20260119, 20260216, 20260525, 20260703 | Lista de investigación | Cambio 3 |
| **Volumen relativo del instrumento**: la regla se validó con volumen NQ; NT la aplica con volumen MNQ y el ratio cruza 0,8 | **10 / 6** | g_replica.py: ro → rv NQ ≤ 0,8 pero MNQ > 0,8 en 9/10 (p. ej. 20240312 0,31 vs 1,09; 20240917 0,26 vs 0,80; 20260616 0,12 vs 1,32); no → NQ > 0,8 y MNQ ≤ 0,8 en 6/6 (20240520, 20241014, 20250204, 20250922, 20251027, 20260813) | Ninguno de los dos códigos; decisión de validación | Cambio 4 |
| conflict_filter (ORFAIL / MOM11 opuesto abierto solo en investigación) | 0 / 2 (20260615, 20260914) | g_replica.py | Ninguno | — |

RV11 no sufre el bug de SixEnter: `TimeEntry` reintenta al diferir (800-802; 20250617 entró a las 11:01, tin_n = tin_r + 1).

## SO04 — 65 / 66 / 58 (89 %)

| Causa | n (ro / no) | Evidencia | Lado | Cambio |
|---|---|---|---|---|
| Tendencia 0 en investigación (ventanas 2025-01 y 2026-04) | 0 / **5** (20250113, 20250130, 20250204, 20260408, 20260430) | days_nq.csv trend==0; distancia ≥ 0,35 en ambos datos | Investigación | Cambio 2 |
| Media sesión | 2 / 0 (20250526, 20260525) | — | Lista de investigación | Cambio 3 |
| Umbral 0,35 ATR al borde, dato NQ vs MNQ | 3 / 2 (ro 20240829 0,41/0,35; 20251030 0,353/0,331; 20251231 −0,362/−0,343; no 20240523 0,349/0,38; 20250416 −0,331/−0,358) | g_replica.py (NQ / MNQ) | Ninguno | — |
| Calentamiento NT (primer día operado, 12:01) | 1 / 0 (20240122) | NT: TrendMin 15 cierres (1454), AtrMin 14 (1453) | Ninguno | — |
| Sin determinar | 1 / 1 (20250715: sin barra 04:00 en mnq_fut; 20260914: dist NQ −0,24 vs MNQ −0,80, una serie tiene una barra rara) | — | — | — |

## Cambios de código, ordenados por ganancia de paridad

**1. NQMaster.cs — reintento de una barra para ORFAIL/CAM3 cuando `DirectionAllowed` difiere (≈ +62 ORFAIL → ~93 %, +13 CAM3 → ~97 %).** Misma convención que TimeEntry/MSEQ; stop y target siguen siendo los de la barra de señal (orfSl/orfTp, camSl/camTp, absolutos vía FixTgt 2192).
- 105 antes: `private int orfBrk, orfBi, orfSig;` → después: `private int orfBrk, orfBi, orfSig, orfPend, orfPendBar = -1;`
- 106 antes: `private int camSide, camBr = -1, camSig;` → después: `private int camSide, camBr = -1, camSig, camPend, camPendBar = -1;`
- 812-813 antes:
  `if (orfSig != 0) { int os = orfSig; orfSig = 0; SixEnter(orf, os, orfSl, orfTp); }`
  `if (camSig != 0) { int cs = camSig; camSig = 0; SixEnter(cam3, cs, camSl, camTp); }`
  después:
  `if (orfSig != 0) { int os = orfSig; orfSig = 0; SixEnter(orf, os, orfSl, orfTp); if (lastDeferred) { orfPend = os; orfPendBar = CurrentBars[0]; } }`
  `else if (orfPend != 0) { int os = orfPend; orfPend = 0; if (CurrentBars[0] == orfPendBar + 1) SixEnter(orf, os, orfSl, orfTp); }`
  `if (camSig != 0) { int cs = camSig; camSig = 0; SixEnter(cam3, cs, camSl, camTp); if (lastDeferred) { camPend = cs; camPendBar = CurrentBars[0]; } }`
  `else if (camPend != 0) { int cs = camPend; camPend = 0; if (CurrentBars[0] == camPendBar + 1) SixEnter(cam3, cs, camSl, camTp); }`
- 831 `orfSig = 0;` → `orfSig = 0; orfPend = 0;`; 833 `camSig = 0;` → `camSig = 0; camPend = 0;`
(`lastDeferred` se pone en false al entrar en SixEnter, 1013, y en true solo en 1947.) El bloqueo por **posición** opuesta (1939) sí coincide con `conflict_filter` y se mantiene. Los trades perdidos suman +$264 (69 ORFAIL) y −$428 (14 CAM3) por contrato: la paridad mejora, el P&L casi no.

**2. research/ict.py:52-53 — tendencia sin huecos (+5 SO04, +1 ORFAIL, +1 CAM3; también afecta a ORB60/MOM13/VW13/LATE15 en esas ventanas).**
antes: `sma = rth.c.rolling(20, min_periods=20).mean().shift(1)` / `trend = np.sign((pc - sma).fillna(0)).to_numpy().astype(np.int64)`
después: `cc = rth.c.dropna()` / `trend = np.sign(cc.shift(1) - cc.rolling(20, min_periods=20).mean().shift(1)).reindex(range(nd)).ffill().fillna(0).to_numpy().astype(np.int64)`
Cambia la lista de trades 2025-01-10→02-06 y 2026-04-06→05-01: hay que re-correr la validación antes de adoptar las cifras.

**3. research/mine/six_build.py:20 — quitar medias sesiones de la lista de paridad (−11 research_only: 8 RV11, 2 SO04, 1 ORFAIL).**
antes: `ok = set(RB.days_real())`
después: `ok = set(RB.days_real()); rth = (D.om >= 570) & (D.om < 960); last = pd.Series(D.om[rth]).groupby(D.day[rth]).max(); ok -= set(D.daydate[last.index[last < 959]].tolist())`
Alternativa equivalente para la corrida de paridad: Strategy Analyzer con `SkipShortSessions = false`.

**4. RV11 — decisión, no código (16 trades).** El módulo se eligió con volumen NQ (RVOL_DRIVE sobre `nqdb.npz`); NT lo corre con volumen MNQ. Opciones: re-validar #4226 con `mnq_fut.npz` (el replay ya existe: 41 trades 2024-26 vs 45 con NQ), o aceptar la tolerancia por módulo y documentarla en parity_check.py junto a ICT/VW13.

**5. Sin fix directo:** 8 nt_only por `conflict_filter` (la VOLB/ORFAIL/MOM11 opuesta solo existe en investigación) y ~9 casos al borde del umbral por dato NQ vs MNQ.

## No determinado
- NT no operó nada los días 20250714, 20250818, 20250829 (investigación sí); 20250829 tampoco tiene barras RTH en `mnq_fut.npz` → probable corte de datos; los otros dos sin explicación con los exports disponibles.
- ORFAIL research_only 20240416, 20250723, 20260911, 20261008; CAM3 20250924; SO04 20250715 y 20260914.
- La marca de tiempo "+2 barras" de las cancelaciones en el export de órdenes del Analyzer (las órdenes colocadas y canceladas en la misma barra se marcan en +0; las de barras anteriores en +2): sirve como huella, no cambia la conclusión.
