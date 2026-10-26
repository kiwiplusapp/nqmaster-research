# Estado de NQMaster (2026-10-26, noche)

Leer esto primero. Detalle por tema en `docs/guia/INDICE.md`, historia de decisiones en `docs/historia/`.

## Qué es hoy

- Una sola estrategia de NinjaTrader 8 (`NQMaster.cs`, ~2.800 líneas) que opera NQ/MNQ en 1 minuto, con una serie interna de 5 minutos.
- Corre unos 20 módulos en paralelo: ORB60/90, MOM11, MOM1030, CRT11, ICT, VOLB, LON, módulos nocturnos (NF05, LF06, LF0430, ON07, REV06), CPI09 y cuatro módulos de seis años.
- Solo NQ. GoldMaster está en `archive/legacy/` y no se usa.
- Tiene panel en español, motor de ciclo de cuenta (`PropCycle`), guarda entre cuentas, monitor de ventaja y capas de seguridad operativa.
- Los módulos y el motor de cuentas están descritos en `docs/guia/modulos.md` y `docs/guia/reglas-prop.md`.

## Perfil activo

- Perfil **Ultra** (el default), con `SixYearModules` en true: SO04, RV11, ORFAIL y CAM3. Es el conjunto que la investigación llama `ultra_d4`.
- CPI09 y los multiplicadores x4 de MOM1030 y CPI09 están activos.
- Alternativas: WR70Plus, Durable (6 módulos, defensivo) y Custom.
- Defensa ante alarma de edge: `DisableModules = MOM1030,MOM13,REV06`.
- Sin multiplicador de order flow ni re-entrada de VOLB: ambos están apagados y falló su validación.

## Firmas y presets en uso

| Plan | Preset | Notas |
|---|---|---|
| 5 cuentas Lucid Flex 150K | `Lucid150K` | Eval 6 contratos, fondeada 3. Tope de 5 fondeadas por hogar |
| 3 cuentas MFFU Rapid EOD 50K | `Mffu50K` | Eval y fondeada a 1 contrato. Apagón de noticias en fondeada |
| Alternativa de 50K rápida | `LucidPro50K` | Eval 4 contratos, no está en el plan base |

- Misma firma, mismo perfil, misma PC. Lucid y MFFU prohíben posiciones opuestas entre cuentas propias.
- Reglas exactas en `.claude/skills/prop-rules/SKILL.md`. Operación diaria en `RUNBOOK_OPERACION.md`.
- Apex y Topstep quedaron fuera por prohibir automatización o exigir su plataforma.

## Métricas honestas

Son las del nivel de planificación (perturbaciones de ±20% en todos los parámetros), no las del mejor backtest.

| Métrica | Valor |
|---|---|
| Sharpe | ~2,5 (el backtest puntual da 3,6) |
| Profit factor | ~1,3 (el backtest da 1,5) |
| Drawdown máximo | ~$5.600 por contrato base |
| Win rate | ~65% |
| Ingreso por contrato base | mediana ~$29k al año con edge completo, ~$19k con 35% menos |

- El edge es de régimen posterior a 2020. Antes de 2020, con costos normalizados, es débil o nulo.
- Con edge cero, el sistema pierde unos $130 al mes por cuenta en fees.
- Cotizar siempre tres casos: edge completo, −35% y edge cero.

## Cinco problemas abiertos

1. **Paridad NT fallida en ICT y MSEQS.** ICT empareja ~82% de los trades y MSEQS ~56%. NT llena los límites de 5m más tarde y exige que ORB60 haya llenado. Impacto chico (~$24/mes en MSEQS), pero `parity_check.py` falla G4. Causas en `docs/guia/validacion.md`.
2. **Cambios del 21-oct sin compilar.** Panel nuevo, `PropCycle`, guarda entre cuentas (C6) y reinicio de presets pasaron solo el stub de C# 5. Falta F5 en la PC, un Strategy Analyzer con `parity_check.py --set ultra_d4` y la prueba en Playback. No comprar cuentas antes.
3. **Fragilidad horaria.** Correr 15 minutos un módulo de reloj baja el Sharpe del portafolio entre 0,3 y 0,7 (CRT11, MOM11, MOM1030, CPI09). Si la zona horaria ET queda mal tras un cambio de horario de verano, el edge desaparece. Chequear el reloj de barras en cada DST.
4. **Meses malos de la campaña.** Agosto-2026 dio −$3.700 por contrato y el verano 2026 quemó el 59-88% de las fondeadas nuevas en 60 días. Un drawdown de $3.700 no cabe en un trailing de $2.000. No hay filtro de régimen que lo evite: la autocorrelación es ~0.
5. **Panel sin datos de riesgo de cuenta.** Según tu lista, el panel no muestra el riesgo de la cuenta. Qué mostrar está sin definir. El runbook ya cita el colchón y el monitor de borde como lo que se mira a diario. Revisar el panel contra eso antes de diseñar nada.

## Experimento 01 en curso (2026-10-26): realismo de ejecución y paridad

Plan aprobado: `docs/PLAN_2026-10-26.md`. Programa completo (5A-5F) en la consigna de esa sesión; cada frente termina en `docs/experimentos/<nn>_<nombre>.md`.

- **Código (S1, sin F5):** `NQMaster.cs` tiene la propiedad `FillSeries` (Off / Tick1 / Second1, grupo "09. Backtest: realismo de ejecución"). Con Tick1 o Second1 agrega una serie intrabar (índice 2) y manda todas las órdenes ahí (patrón SampleIntrabarBacktest); con Off (default) el comportamiento es el de antes: `fillBip = 0` en cada llamada, guard `BarsInProgress == 2` inerte, `FillBar()`/`FillBarTime()` devuelven lo mismo que antes. Imprime `RUN TIME` en Output para medir el ratio Off / Tick1. Parche reproducible: `research/mine/patch_fillseries.py` (v3 tras la revisión adversarial: en `State.Realtime` las órdenes vuelven a la serie de 1 min con aviso, contador `TICK GAP` en el `RUN TIME`, `FillBar()` guiado también por la hora del fill); backup `archive/backups/NQMaster_backup_pre_fillseries.cs`; `check.sh` verde. Revisor: con Off, sin hallazgos. **P2a hecho (26-oct, noche): F5 ok en la PC y el export con `FillSeries = Off` 2024-01-01 → 2026-10-23 es idéntico byte a byte al export pre-parche en los 3.295 trades, y en las 13.869 órdenes salvo los identificadores de orden y OCO que NinjaTrader numera por corrida** (`research/nt_exports/2026-10-26/fillseries_off/`, informe `fill_gap_off_vs_standard.md`). El template de las cuentas en vivo lleva `FillSeries = Off`.
- **Herramientas:** `research/mine/fill_gap.py` (Standard vs Tick1 vs investigación: Δticks de entrada y salida, Δ$/trade con IC 95 %, cambios de desenlace, fills fuera de la barra) y `research/mine/slip_model.py` (slippage real por cuenta prop / sim, módulo y franja, contra el export Standard). Autotest con el export del 14-oct contra sí mismo: 100 % emparejado, Δ = 0; slippage = exactamente el tick que el backtest ya cobra. `research/nt_trades.py` ahora conserva precios de fill, nombre de salida, dirección y barras.
- **Baseline Standard con el código actual (P1 hecho el 26-oct, F5 ok en la PC):** `research/nt_exports/2026-10-26/standard/` (trades + orders, 2024-01-01 → 2026-10-23, 3.295 trades, neto NT $100.417). `parity_check.py --set ultra_d4` → **FALLA**: G1 91,0 % (< 92), G2 +1,1 % ok, G3 correlación diaria 0,918 (< 0,95), G4 falla en 6 módulos: ORFAIL 34,3 % (NT 40 trades vs 105 en la investigación), RV11 53,8 % (29 vs 39), CAM3 56,2 % (26 vs 32), MSEQS 55,6 %, ICT 80,4 %, SO04 89,2 %. Los cuatro módulos de 6 años, que entraron el 16-19 oct sin pasar por el Analyzer, son el problema nuevo; con el umbral del programa (95 %) además quedan cortos VOLB 90,1, LON 91,9, NF05 91,8, CRT11 92,2, CPI09 92,3, MSEQ 92,7, ON07 93,5, MOM13 94,6. Informe: `research/nt_exports/2026-10-26/standard/parity_ultra_d4.md`.
- **P0 (26-oct):** el Analyzer confirma que `High` solo existe para estrategias de una serie → va el parche `FillSeries`. Proveedor Continuum (demo), 32 GB RAM, **ticks de MNQ solo desde 2026-08-25 (44 días hábiles)**; `Second1` no extiende la ventana (los segundos se construyen desde los ticks). H1/H2 ajustadas a esa ventana en el plan.
- **Dato de datos:** el feed de NinjaTrader (MNQ DEC26) y `mnq_fut.npz` difieren de nivel de precio en 2 fechas (2025-07-15 y 2025-08-19, 135-350 puntos en el mismo minuto). No afecta el $ de cada lado, sí cualquier comparación de niveles entre feeds; `fill_gap.py` los cuenta aparte (`feed_offset`). Revisar esos dos días antes de usar la paridad de precios.
- **P2b (26-oct, noche, `research/nt_exports/2026-10-26/tick1_trace/README.md`):** corrida Tick1 con TraceOrders. Las 495 órdenes trazadas (entradas, salidas por tiempo y los 16 cierres `Sell` / `Buy to cover`) salieron con `BarsInProgress=2`; 0 ignoradas, 0 errores, 0 `TICK GAP`. NinjaTrader no traza las órdenes protectoras de `SetStopLoss` / `SetProfitTarget`, así que su serie se verifica en el export de trades (segundos ≠ :00 en "Stop loss" / "Profit target"). **Los ticks de Continuum empiezan el 2026-08-02**, no el 25-08: ventana de ~58 días hábiles. 121 M ticks procesados en 33,9 s (82.560 barras de 1 min).
- **P2c (26-oct, noche, `research/nt_exports/2026-10-26/tick1_jun_today/README.md`):** corrida Tick1 2026-06-01 → 2026-10-23 (392 trades, 236 M ticks en 68 s, 0 `TICK GAP`; ticks de Continuum desde al menos el 2026-05-31). **El modelo de fills de v3 es mixto:** las entradas y salidas que emite NQMaster van a la serie de ticks, pero las protectoras de `SetStopLoss` / `SetProfitTarget` quedan en la serie de 1 minuto (0 % de los 283 fills de "Stop loss" / "Profit target" con segundos ≠ :00) y NinjaTrader no aplica `Slippage` en la serie secundaria (entradas exactamente 1 tick mejores que Standard). Resultado crudo +13,7 % (+$598 en 392 trades) y +9,5 % con el tick sintético en entradas: **no es una medición de H1**. Sigue el parche v4 (plan B: salidas explícitas en la serie de llenado) y la repetición de las corridas (c)/(d) sobre 2026-06-01 → hoy.
- **Aporte de SO04 / RV11 / ORFAIL / CAM3 (medido 26-oct, anotado en el runbook):** investigación 2024-26 +$100/mes por contrato (5,2 % del neto), Sharpe 3,54 → 3,64, DD igual, peor mes −$2.279 → −$2.410; 2020-23 +$87/mes (6,1 %), Sharpe 3,21 → 3,32; en NinjaTrader +$143/mes (6,7 %). Siguen encendidos con la etiqueta "paridad pendiente"; no contar su aporte al planificar cuentas.
- **Parche v4 (26-oct, noche; `research/mine/patch_fillseries.py`, `check.sh` verde, revisión adversarial en curso, SIN F5):** con `FillSeries` ≠ Off los `Set*` se reemplazan por brackets explícitos `StopX` / `TargetX` en la serie de llenado (`BracketStop` / `BracketTarget` guardan el nivel, `PlaceBrackets` los emite en cada ejecución de la entrada, `ModuleMarketExit` los cancela antes de una salida a mercado y la manda al confirmarse el cancel, guardia de huérfanas y contadores en la línea `RUN TIME`). En `Realtime` vuelve a la serie de 1 min salvo en la conexión Playback (prueba de brackets con 6 contratos: `ORPHAN` y `market exits forced` deben ser 0 en el Output y la pestaña Orders tiene que quedar vacía tras el flatten de 15:56). Con Off los `Bracket*` caen en los `Set*` originales.
- **Variable de estado que separa corridas con distinto inicio (26-oct):** `atrDaily` es un suavizado de Wilder (k = 14) que arranca en el primer día cargado: dos corridas con dos meses de diferencia difieren en los stops/targets de 36 de 62 trades iguales y en 20 de 74 trades sobre la misma ventana (la mayoría en los dos primeros días tras el calentamiento, por la SMA de 20 cierres con mínimo 15). Afecta cuentas en vivo que arrancan con otro *Days to load*: el runbook pasa a **Days to load = 120 fijo** (peso del arranque 0,6 % contra ~28 % con 45). La investigación usa el mismo EMA desde 2020.
- **Nube:** `tools/propcycle_test/run_test.py` vuelve a correr: las grillas `research/tmp/dense` se reconstruyen con la cadena `dense_build → ict_redo → dense_profiles → dense_extra → gnq_port → nqdrive_port` (4 min, 2,1 GB), ahora en `tools/cloud_setup.sh`. Resultado con el código v3: 780 casos, 0 diferencias C# vs investigación, 0 port Python vs investigación.
- **Reproducibilidad (26-oct, `docs/experimentos/00_reproducibilidad_tablas.md`):** de las tres tablas que regenera la cadena `dense`, `gnq_port.csv` y `nqdrive_port.csv` se reproducen exactas (solo cambian finales de línea CRLF → LF); **`nqdrive_lc.csv` es no reproducible en el período REAL** (38 de 72 filas, $/mes hasta +16 %, p10 hasta ±43 %): determinista, datos sin cambios desde el 5-oct, causa más probable el estado de las grillas densas del 7-oct (bug de reconstrucción, corregido el 15-oct), no demostrable porque ese estado no se guardó. Heredan la etiqueta **no reproducible** las frases "en el ciclo de cuenta" de NF05 y LF06/LF0430 en `docs/guia/modulos.md`. Ningún número del runbook ni de los presets sale de esas tablas. Regenerada guardada en `research/mine/nqdrive_lc_regen_2026-10-26.csv`.
- **Revisión adversarial de v4 (26-oct, `docs/experimentos/01_revision_parche_fillseries.md`):** Off sin hallazgos de comportamiento; con Tick1 cuatro correcciones aplicadas en v4.1 (hedge guard literal con Off, re-dimensión de brackets en fills parciales, callbacks tardíos de brackets viejos ignorados, salida a mercado acotada a los lotes que quedan, cancelación de brackets al quedar plano). `check.sh` verde; **falta F5**.
- **Pendiente de la PC (Federico):** F5 de v4.1 y P2 en el orden del plan. Después: (c) Tick1 y (d) Off sobre 2026-06-01 → hoy con exports de trades y órdenes y las líneas `RUN TIME`; P3 (exports de cada cuenta prop; Sim101 aparte).
- **Herramientas (26-oct):** `fill_gap.py` lee los sellos de tiempo por export (serie de ticks = hora del tick, serie de 1 min = cierre de barra) y acepta `--slip-b N` (slippage sintético para los fills de la serie de ticks) y `--stamps-b`. `docs/experimentos/01_revision_parche_fillseries.md`: informe del revisor adversarial del parche con la disposición de cada hallazgo.
- **Nube:** `tools/propcycle_test/run_test.py` no corre acá: necesita `research/tmp/dense/meta.pkl`, que está en `.gitignore` y fuera de `tools/data_manifest.json`. `mcs` hay que instalarlo (`apt-get install mono-mcs`, ~4 min).

## Siguiente paso

Cerrar el punto 2 dentro del experimento 01: F5, export Standard, `parity_check.py --set ultra_d4`, y las corridas Tick1 del plan. Hasta entonces, las cifras de cuentas son de investigación.

## Dónde mirar

- Datos y comandos: `CLAUDE.md`. Protocolo de validación: `.claude/skills/validacion/SKILL.md`.
- Ideas descartadas: `Conocimiento/Descartado/` y `docs/historia/ifvg-sniper-nt8-project.md`.
- Versiones anteriores del código: `archive/backups/` y `archive/legacy/`.
