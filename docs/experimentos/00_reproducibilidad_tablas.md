# Reproducibilidad de las tablas que regenera la cadena `dense` (2026-10-26)

Veredicto: **2 de 3 tablas se reproducen exactas; `nqdrive_lc.csv` no se reproduce en el período REAL** (38 de 72 filas cambian, hasta +16 % en $/mes). Ningún número del runbook ni de los presets sale de estas tablas; sí salen de ellas las cifras "en el ciclo de cuenta" de la guía de módulos para NF05, LF06 y LF0430.

## Qué se comparó

La cadena `dense_build → ict_redo → dense_profiles → dense_extra → gnq_port → nqdrive_port` (ahora en `tools/cloud_setup.sh`) reescribe tres tablas commiteadas el 2026-10-07 (commits 61be6ca y 410a8c7). Se corrieron tres veces en la nube el 26-oct: la cadena completa dos veces y `gnq_port.py` + `nqdrive_port.py` sueltos dos veces. Las cuatro salidas son idénticas entre sí: **la regeneración es determinista** (el único azar, el bootstrap de 1.000 años de `nqdrive_lc`, usa `default_rng(31 + q)` con semilla fija).

| Tabla | Qué contiene | Filas × columnas | Regenerada vs commiteada |
|---|---|---|---|
| `gnq_port.csv` | métricas por trade de Ultra + NF05 / LF0315 / NM22 (tpd, wr, pf, sharpe, $/mes) en IS / C24 / REAL | 27 × 7 | **idéntica en los 135 valores**. Solo cambian los finales de línea: la commiteada tiene CRLF (Windows), la regenerada LF. Por eso `git diff` marcaba las 27 líneas |
| `nqdrive_port.csv` | ídem para Ultra+NF05 + LF06 / LF0430 | 12 × 7 | **idéntica en los 60 valores**; mismo tema de CRLF |
| `nqdrive_lc.csv` | ciclo de cuenta 50K 2c/2c y 150K 6c/3c por candidato × período × prueba (historia / +1 tick / Monte Carlo): $/mes, p10, P(pérdida), evals, aprobadas, quemadas, retiros, días | 72 × 12 | **IS y C24 idénticos; REAL distinto** en las 3 pruebas y los 4 candidatos. `mo` mediana +0,1 %, máximo +$331 (+16 %); `p10` hasta ±43 %; `fbust` ±0,8 quemadas/año; `evals` hasta −1,8/año |

Detalle de `nqdrive_lc` REAL, prueba "historia", $/mes por plaza (commiteado → regenerado): 150K final+NF05 2.094 → 2.269; +LF06 2.102 → 2.257; +LF0430 2.245 → 2.402; +LF06+LF0430 2.228 → 2.348. 50K: 1.276 → 1.278, 1.287 → 1.300, 1.287 → 1.287, 1.350 → 1.350.

## Causa

- **No es aleatoriedad**: semilla fija, cuatro corridas iguales.
- **No es versión de datos**: `mnq_fut.npz` (REAL) y `nq_1m.npz` tienen el mismo SHA-256 en el manifiesto desde el 2026-10-05 (`1d536284…`, `e445ac0b…`); `research/ict.py` (ATR y niveles diarios) no cambió desde el 5-oct; los trade sets (`robust_trades.pkl`, 5-oct) tampoco, y las dos tablas por trade lo confirman.
- **No es el orden de la cadena**: las tablas por trade salen iguales en la cadena completa y sueltas.
- **Hipótesis descartada**: que el 7-oct faltaran las grillas `N:ENG0610` / `N:LATEFH` (están en el set de cuenta `UA_FULL_GR`, definido en `prof_grid_lib.py`, y el bug de reconstrucción las borraba). Quitándolas hoy, 150K REAL "historia" da 2.431 y C24 1.906, no los 2.094 / 1.984 commiteados.
- **Queda**: el estado de las grillas densas REAL con que se calculó la tabla del 7-oct (ese día `dense_build` se re-ejecutaba al importarse y borraba o pisaba claves agregadas después; corregido el 15-oct con los guards de importación). No está guardado el `meta.pkl` ni el `REAL.npz` del 7-oct, así que **no se puede probar cuál era la versión**. Lo que sí vale: la versión regenerada hoy es la que produce el código y los datos del repo.

## Dónde se usan

- **Runbook (`RUNBOOK_OPERACION.md`)**: ninguna cifra sale de estas tablas; sus fuentes son `integ_paired.json`, `integ_eval_150k.json`, `integ_port.json`, `integ_budget.json`, `integ_ladder.json` y `prop_wf.json` (ronda 5, 21-oct).
- **Presets (`ApplyPreset` en `NQMaster.cs`)**: reglas de las firmas, nada viene de aquí.
- **`docs/guia/modulos.md`**: las frases "En el portafolio: Sharpe 3,12 / 3,37 / 3,59 → 3,21 / 3,38 / 3,62" (NF05) y "3,21 / 3,38 / 3,62 → 3,31 / 3,47 / 3,71" (LF06+LF0430) salen de `gnq_port.csv` / `nqdrive_port.csv`: **reproducibles**. Las frases "En el ciclo de cuenta: 150K $1.984 → $2.069 por mes… 50K $1.311 → $1.362" (NF05) y "Cuenta 150K 6/3: $2.069 → $2.168… 50K 2/2: $1.362 → $1.393, mejor en 7 de 9" (LF06/LF0430) mezclan los tres períodos (`mean9`), incluido REAL: **no reproducibles** desde el repo; se marcan en ESTADO.
- `report_150k.py` (informe HTML del 7-oct) las lee las tres: el informe no se regenera igual.

## Decisión

- Las tablas commiteadas quedan como están (son el registro del 7-oct); la regenerada de `nqdrive_lc` se guarda al lado como `research/mine/nqdrive_lc_regen_2026-10-26.csv` para comparar.
- Regla desde hoy: todo resultado de investigación que no se reproduzca desde el repo lleva la etiqueta **no reproducible** en `docs/ESTADO.md`, y las frases de la guía que dependen de él la heredan.
- Qué sigue (S2 o después, no bloquea el experimento 01): añadir al manifiesto un hash de `meta.pkl` y de las claves de cada `<per>.npz` para que una tabla pueda decir con qué grillas se calculó.

Comandos: `cd research/mine && python3 gnq_port.py && python3 nqdrive_port.py` (68 + 53 s); comparación: `diff <(tr -d '\r' < gnq_port.csv) <regenerado>`; prueba de la hipótesis ENG10/LATEFH: ver la sesión del 26-oct (script inline sobre `lc_lib.define` / `vec` / `life_q`).
