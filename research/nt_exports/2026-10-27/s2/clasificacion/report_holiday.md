# S2 — Causa (a) ventanas post-feriado, (b) VW13 y resto de los no emparejados (ultra_d4 vs Standard 2024-01-22 → 2026-10-08)

Datos de trabajo: `unmatched_*.csv` / `matched_*.csv` (243 NT-only, 295 research-only, 2.991 emparejados; research dedup 3.286, NT 3.234). Anexos en la misma carpeta: `trend_cmp.csv` (tendencia research vs regla NT por día), `nt_only_annot.csv`, `res_only_annot.csv`, `analyze.py`.

## 1. Causa (a): confirmada, con el mecanismo exacto

- **Clústeres.** 100 de los 243 NT-only caen en dos ventanas de exactamente 20 sesiones: **2025-01-10 → 2025-02-06** y **2026-04-06 → 2026-05-01**. Cada una empieza en la sesión siguiente a una sesión de Globex **sin barras RTH** en `nqdb.npz`: 2025-01-09 (duelo nacional Carter, CME equity cerró 09:30 ET: 930 barras nocturnas, 0 RTH) y 2026-04-03 (Viernes Santo: 909 barras, 0 RTH). Año Nuevo no crea agujero (la sesión no existe → `dayid` sigue contiguo) y los feriados con cierre 13:00 ET (MLK, Presidents, Memorial, Juneteenth, 3/4-jul, Labor, Black Friday, 24-dic) tampoco (hay cierre RTH). 2024-10 (15) **no** es ventana: 1 trade/día en 12 módulos, 4 descartados por el `conflict_filter` de la investigación → ruido normal.
- **Dónde nace el artefacto.** `research/ict.py:42` arma la tabla `rth` indexada por `dayid` con `.reindex(range(nd))` → la sesión sin RTH queda con `c = NaN`. `ict.py:52` `sma = rth.c.rolling(20, min_periods=20).mean().shift(1)`: un NaN dentro de la ventana anula la media durante 20 sesiones; `ict.py:49` `pc = rth.c.shift(1)` anula además el día siguiente al agujero; `ict.py:53` `.fillna(0)` convierte el NaN en tendencia **0 = módulo apagado** para todo módulo con `tf=1`. Copias idénticas: `research/ict_fix.py:49-53` (ICT) y `research/mine/foundations.py:85` (`trend_series`, rama "sma"; herramienta de auditoría, no genera pickles). Consumidores: `research/mine/core.py:10,31` (`D.trend`, todas las familias minadas), `research/mine/wrq_build.py:64` (`ict.day_levels(Dr)` → `tmom`), `research/london.py:9,101`, `research/tmom.py:8`.
- **Serie diaria.** Tendencia research = 0 en exactamente los 40 días de las dos ventanas (los únicos días con 0 en 2024-26); la regla NT recalculada día a día da ±1 en todos (`trend_cmp.csv`). El ATR no se afecta (`ewm(ignore_na=True)`: 354,4 el 9 y el 10-ene). Período completo 2020-10-15..2026-10: **80 de 1.548 sesiones (5,2 %)** con tendencia 0 espuria (tras 2021-04-02 y 2023-04-07 Viernes Santo, 2025-01-09, 2026-04-03). En `nq_1m.npz` (IS/C24) 63 sesiones (2021-04, 2023-04/05, 2025-01/02); en `mnq_fut.npz` 85 (además 2025-08-29, 2026-01-23, 2026-09-28: días **sin datos RTH en ese feed**, no feriados); `nqhd_long.npz` 152.
- **Regla NT.** `NQMaster.cs:856-872` `FinalizeRthDay` solo corre si `dayHasBars` (llamadas en 690 y 843): la sesión sin RTH no entra a `rthCloses` (865-866, últimos ≤ 20) y `trendDir` se recalcula con ≥ `TrendMin` = 15 cierres (868, 1454); nunca se resetea. En la sesión del feriado mismo NT conserva el `trendDir` anterior (no hay finalize).
- **Módulos afectados** (tf=1 en research y `Trend`/`trendDir` en NT): MOM1030, MOM13, ON07, REV06 (`wrq_build.py:65-66`, último campo de la tupla; `tmom.py:35`; `NQMaster.cs:552-555`), ICT (`ict_fix.py:166`; cs:1344), LON (`london.py:40`; cs:1192), VW13/VW13b (`wrq_build.py:200-201`; cs:557), LATE15 (grid LATE_MOM 762 `tf=1`; cs:558), LF0430 (`wrq_build.py:207`; cs:564), SO04 (CLOCK_ANCHOR 1527 `tf=1`; cs:569), ORFAIL (OR_FAIL 142 `tf=1`; cs:1059), CAM3 (PIVOT_FADE 365 `tf=1`; cs:833). **No afectados:** MOM11, VOLB, NF05, LF06, RV11 (`tf=0`), CPI09 (sin tendencia), ORB60/90 (`nt_v2_replica.daily_stats` salta sesiones sin RTH: ver `foundations.py:128-150`), MSEQ/MSEQS (`wr60.py:19-30`, por fecha RTH), CRT11 (`crt.py:21-31`, por fecha RTH).
- **Prueba en los trades.** Dentro de las ventanas la investigación tomó **0** trades de esos 12 módulos (sí tomó MOM11 29, VOLB 31, MSEQ 16, ORB 14, NF05 9…) y NT tomó **90** (ON07 19, MOM13 18, REV06 12, VW13 10, MOM1030 7, LON 7, SO04 5, LATE15 5, LF0430 3, ICT 2, CAM3 1, ORFAIL 1). Los otros 10 NT-only en ventana (VOLB 4, MSEQ 2, CPI09, ORB90, CRT11, RV11) son coincidencia/cascada (con módulos de tendencia en posición cambian `deferUntil` y conflictos en NT).

## 2. Cuantificación (cota superior: supone que la investigación hubiera tomado exactamente los 90 trades de NT)

G1 = emparejados / research (`parity_check.py:50`): sumar 90 a numerador y denominador → **91,0 % → 91,3 %**. G3 (corr. diaria) 0,918 → 0,925. $ NT de esos 90: +$1.122 (todos los NT-only suman +$10.928 en NT; los research-only +$1.380). G4 por módulo (ahora → con fix): SO04 89,2 → **90,0** (pasa justo), MOM13 94,6 → 95,1, ON07 93,5 → 93,9, REV06 95,3 → 95,5, VW13 97,4 → 97,5, LON 91,9 → 92,2, ICT 80,4 → 81,1, CAM3 56,2 → 57,6, ORFAIL 34,3 → 34,9, MOM1030 97,0 → 97,2, LATE15 100, LF0430 97,7 → 97,8; los demás no cambian. **Conclusión:** la causa (a) es real y exacta pero no es lo que hunde G1/G4: ORFAIL, RV11, CAM3, MSEQS e ICT quedan igual. En la práctica el fix también puede alterar el `conflict_filter` (trades nuevos bloquean opuestos) → la cota no es exacta.

**Hallazgo adicional, causa (c) sesiones cortas.** NT trae `SkipShortSessions = true` por defecto (`NQMaster.cs:416`; bloqueo en 1963; `shortSession` 176-186) → **0 trades NT** en los 25 días con cierre 13:00 ET del período ni en las 2 sesiones sin RTH; la investigación los opera: **59 research-only** (ON07 13, RV11 8, REV06 6, LON 5, VOLB 5, MOM13 4, MSEQ 4, NF05 4, VW13 3, SO04 2, CRT11/ICT/LF06/MOM1030/ORFAIL 1), $ +378. `six_build.py:17` filtra solo FOMC y ATR < 150 (`RB.days_real()`), no sesiones cortas. Sin esos 59: **G1 92,7 % (pasa)**, G3 0,919; con (a)+(c): **G1 92,9 %**, G3 0,927 (sigue < 0,95), G4: ON07 98,5, REV06 98,2, MOM13 97,0, NF05 95,3, MSEQ 95,0, LON 94,8, SO04 92,6, VOLB 91,0, RV11 67,7. Decisión de Federico: es regla operativa de NT (no artefacto de datos) y el calendario CME se conoce de antemano (información disponible en tiempo real) → o se excluyen esos días en `nt_compare.research_set` (abajo) o se corre el Analyzer con `SkipShortSessions = false`. Para el motor de campaña con el preset real (que sí los salta) corresponde excluirlos.

## 3. Fix exacto (lado Python) y cadena de regeneración

`research/ict.py:52-53` (y la copia `research/ict_fix.py:52-53`), antes:
```python
    sma = rth.c.rolling(20, min_periods=20).mean().shift(1)
    trend = np.sign((pc - sma).fillna(0)).to_numpy().astype(np.int64)
```
después (verificado: **0 diferencias** contra la regla NT simulada día a día en las 4.209 sesiones de `nqdb.npz`; en 2024-26 corrige exactamente los 40 días):
```python
    cr = rth.c.dropna()                                                    # solo sesiones con RTH (NQMaster.cs:865-871): un feriado sin RTH no entra a la ventana
    tn = np.sign(cr - cr.rolling(20, min_periods=15).mean())              # tendencia para la sesión SIGUIENTE: último cierre vs media de los últimos <= 20, >= 15 (TrendMin)
    trend = tn.reindex(range(nd)).shift(1).ffill().fillna(0).to_numpy().astype(np.int64)   # la sesión sin RTH conserva la tendencia anterior, como NT
```
`research/mine/foundations.py:85` (`trend_series`, rama "sma"): misma construcción sobre `c.dropna()` con `min_periods=min(15, spec[1])` y `reindex+ffill`; `foundations.py check` (asserts 233/240/245) fallará a propósito porque reproduce los arrays viejos → actualizar sus referencias después. Opcional ATR: `ict.py:49` `pc = rth.c.shift(1)` → `rth.c.ffill().shift(1)` para que el TR del día posterior al agujero use el último cierre RTH como `atrPrevClose` (cs:858, 863); afecta un valor de TR por agujero. `min_periods=15` solo importa en las primeras 20 sesiones de cada dataset (2010 / 2020).

Sesiones cortas (si se decide excluirlas en la investigación), `research/mine/nt_compare.py:46`, después de `X = X[~X["mod"].isin([...])]`:
```python
        from wrq_lib import getD; D = getD("nqdb.npz"); rl = pd.Series(D.om).where((D.om >= 570) & (D.om < 960)).groupby(D.day).max()
        short = set(D.daydate[rl.reindex(range(D.nd)).fillna(0).to_numpy() < 959])        # cierre RTH antes de 15:59 o sin RTH = SkipShortSessions (NQMaster.cs:183, 1963)
        X = X[~X.date.isin(short)]
```

Cadena para `ultra_d4` (`nt_compare.py:44-50` lee `six_ultra6_trades.pkl`): (1) borrar la caché `research/mine/wrq_entries_db.pkl` (`db_long.py:35-36` la devuelve si existe) y regenerarla con `wrq_build.build("nqdb.npz")` — **medido 59 s**; `wrq_entries.pkl` (nq_1m/mnq_fut/nqhd_long, `wrq_build.py:235-237`) solo si se quieren refrescar IS/C24 (~3 min est.). (2) `python3 cand16.py` → `cand16_trades.pkl` (+ `cand16.json`) vía `robust2_build.setup()` (no medido; minutos). (3) `python3 six_base.py` → `six_trades.pkl` (segundos; CPI09 viene de `ultraq_trades.pkl` y no cambia: `cpi_lab.py` no usa tendencia). (4) `trades_db_new.pkl` (OR_FAIL 142 → ORFAIL) y `trades_db_old.pkl` (CLOCK_ANCHOR 1527 → SO04, PIVOT_FADE 365 → CAM3; 140 MB, gitignored, se reconstruye del .xz): los genera `run_mine_db.py` (familias sobre `core.Data` → `D.trend`; 13 min / 45k configs en 4 CPUs según `docs/historia/ifvg-sniper-nt8-project.md:141`) — basta `MINE_TAG=db_old python3 run_mine_db.py CLOCK_ANCHOR PIVOT_FADE` y `MINE_TAG=db_new python3 run_mine_db.py OR_FAIL`, o un script puntual que regenere esas 3 claves y actualice los pickles (segundos). RV11 (`tf=0`) no cambia. Ojo: regenerar también cambia `results_db_*.csv`, insumo de `six_reselect.py` / `six_oos.py` → repetir la selección es decisión aparte. (5) `python3 six_build.py` → `six_ultra6_trades.pkl`. (6) `parity_check.py <csv> --set ultra_d4`. Los otros sets (`robust_trades.pkl`, `final3y_trades.pkl`, `ultraq_trades.pkl`) arrastran el mismo artefacto pero no están en esta cadena. **Impacto en métricas validadas:** los 12 módulos con tendencia estuvieron apagados el 5,2 % de las sesiones 2020-26 (IS: 63 sesiones) → el fix agrega trades; hay que re-correr IS / C24 / REAL sin re-optimizar (corrección de datos, no de parámetros).

## 4. VW13 (causa b)

- NT: `vw13.MinDist = 0.15; vw13.DoubleDist = 0.30` (`NQMaster.cs:557`) → un trade con qty 2 si |close − VWAP| ≥ 0,30 ATR (cs:1146). Investigación: VW13b (x = 0,15) y VW13 (x = 0,30) como filas separadas en el **mismo minuto** (tin 1141 = 13:01 ET) con el mismo `u` → el `drop_duplicates(["date","mod","tin","d"])` de `parity_check.py:32` es correcto: NT 62 trades con qty 2 vs 59 pares duplicados en research. No hace falta sumar lotes: G2 compara $ por contrato en ambos lados (`nt_compare.py:88`, `u = pnl/qty`). Opcional: alerta (no gate) qty-2 NT vs filas dobles research (62 vs 59).
- 13 NT-only: **10 en las ventanas (causa a)**. 3 fuera (2024-10-08, 2024-10-09, 2026-01-20): en research |close − VWAP| / ATR = 0,144 / 0,149 / 0,146, **justo bajo 0,15** con el ATR de la investigación (ewm desde 2010); NT los tomó porque su `atrDaily` (Wilder rampado desde el inicio del Analyzer, ya anotado en ESTADO) es algo menor ese día. Umbral marginal, no bug de matching.
- 4 research-only: 3 en sesiones cortas (2024-07-03, 2024-11-29, 2024-12-24; causa c); 1 (2025-07-14, distancia 0,308, tendencia +1) **sin explicar** (NT no lo operó; posible bloqueo por posición/defer; haría falta el log de NT).
- Cambio en `nt_compare` / `parity_check` por VW13: **ninguno**.

## 5. Resto, fuera de las ventanas (solo conteos)

`wrq_port.conflict_filter` (`wrq_port.py:49-57`, primero en llegar, sin posiciones opuestas) descarta 95 filas del set; **23 NT-only** (todos fuera de ventana) existen en el set sin filtrar a ±3 min → los descartó la investigación y NT sí los operó (su lógica de conflicto difiere en esos casos): MOM11 9, VOLB 7, CAM3 3, ORFAIL 2, RV11 2. Los research-only no los explica el filtro (sobrevivieron).

| Módulo | NT-only fuera de ventana → mismo día misma dir. / opuesta / descartado por conflict_filter | research-only → mismo día misma dir. / sesión corta / día ausente en NT |
|---|---|---|
| VOLB | 26 → 13 / 1 / 7 | 49 → 16 / 5 / 28 |
| ON07 | 7 → 0 / 0 / 0 | 17 → 0 / 13 / 4 |
| REV06 | 12 → 0 / 0 / 0 | 10 → 0 / 6 / 4 |
| MOM13 | 4 → 0 / 0 / 0 | 10 → 0 / 4 / 6 |
| MOM1030 | 11 → 0 / 0 / 0 (señal ausente en research; umbral 0,2 ATR con ATR distinto, no determinado) | 3 → 0 / 1 / 2 |
| LON | 5 → 0 / 0 / 0 | 14 → 0 / 5 / 9 |
| MOM11 | 12 → 0 / 1 / 9 | 20 → 0 / 0 / 20 (NT no entró esos días: acuerdo VWAP / sesión completa / conflicto NT; no determinado) |
| ICT | 15 → 2 / 0 / 0 | 10 → 2 / 1 / 7 |
| MSEQ | 12 → 4 / 0 / 0 | 12 → 3 / 4 / 5 |

**No determinado:** la causa de los 11 MOM1030 y 20 MOM11 (hace falta el log de NT o replicar su ATR rampado); VW13 2025-07-14; el efecto del arranque del Analyzer (NT usa 15-19 cierres hasta ~2024-02-20: 5 NT-only en el primer mes, no atribuidos). Los módulos de 6 años (ORFAIL 69 research-only, RV11 18, CAM3 14) y MSEQS no son causa (a) ni (c) salvo 10 trades: quedan para su propio informe.
