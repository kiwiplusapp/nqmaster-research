# Changelog: rondas de cambios y decisiones por fecha

> Parte de `NQMASTER_GUIA.md` partida por tema el 2026-10-26. Texto sin cambios, secciones en el orden original. Índice: `docs/guia/INDICE.md`.

## ★★★★★★★★★★★★★★★★★★ 2026-10-21: panel nuevo, simulación del ciclo de cuenta y configuración limpia

### Qué cambió
- **Panel en español, en tres bloques.**
  - Arriba a la derecha: el sistema (estado, módulos) y el rendimiento: trades, % ganadoras, factor de beneficio, neto, por trade, por mes, caída máxima, mejor y peor día, días positivos, si hay comisiones y el monitor de borde. En vivo también muestra "esperado por el backtest" contra lo real.
  - Arriba a la izquierda: la **simulación de la cuenta** y, en vivo sobre una cuenta real, la **cuenta real**.
  - Abajo a la izquierda: avisos (órdenes trabadas, tope de contratos, sesión corta, calentamiento, alarma).
- **Simulación del ciclo de cuenta** (propiedad *Backtest: simular el ciclo*, activada por defecto). Con un preset de firma y la fase en Eval o Funded, el backtest hace lo mismo que harías vos:
  1. Compra una eval al terminar el calentamiento y la opera con el tamaño y los cortes de la eval del preset.
  2. Si llega al objetivo (con la regla de consistencia), cierra todo y al día siguiente arranca la fondeada (MFFU: después de los 4 días mínimos).
  3. Si toca el límite de pérdida (contando la posición abierta en el peor precio de cada barra), la cuenta se pierde y **al día siguiente compra otra eval**.
  4. En la fondeada pide los retiros al cierre con la regla de la firma y los descuenta del saldo.
  5. Lucid termina la fondeada al quinto retiro (pasa a cuenta real) y se compra otra eval.
  6. El panel cuenta evals compradas, aprobadas y perdidas, fondeadas perdidas y completadas, retiros pedidos y cobrados (90%), costos y el resultado neto por mes, con los últimos eventos fechados.
- **Precio de la eval:** por defecto el de lista (Lucid Flex 25K $89, 50K $146, 150K $285, Pro 25K $123, Pro 50K $192, MFFU 50K $157, FundedNext 25K $80). Cargá el precio con cupón en *Precio pagado por cada eval*.
- **Cuenta de simulación en vivo (Sim101 / Playback):** la simulación sigue corriendo y el saldo es el de la cuenta simulada, nunca el de Sim101. En una cuenta real de la firma la simulación se congela al pasar a vivo y el panel muestra el saldo, el límite, el colchón y el retiro de la cuenta real.
- **Configuración limpia:** 8 grupos en español y 83 propiedades visibles.
  - 46 propiedades quedaron **ocultas y forzadas** a su valor validado, así que un template viejo no las puede volver a prender:
    - Ideas que fallaron fuera de muestra o fueron reemplazadas: boost de order flow, tamaño adaptativo, subida de tamaño tardía en la eval, gating por colchón (Estable / Safe), chequeo de ATR para arrancar evals, pausa del monitor, re-armado de VOLB y los módulos MOM1130, RSI2, LF0315, CA04V, GD03, ENG26, ENG10 y LATEFH.
    - Parámetros del edge que ningún test cambió: pullback 0,44, tope de stop 0,35, ORB contra cierre previo 0,10, break-even de VOLB, acuerdo MOM, VOLB 10:47, stop mínimo 0,10, reglas de contexto y confluencia, ICT x2, VW13 ancho, CPI09 x4, MOM1030 x4.
  - Los interruptores de módulos quedan en el grupo 08 "Avanzado". Para apagar un módulo alcanza con *Apagar módulos*.
- **LucidPro25K fondeada:** pide el retiro con $2.100 de ganancia (colchón 1.100 + primer retiro 1.000), igual que la investigación.

### Auditoría de los cálculos
- `tools/propcycle_test/run_test.py` pasa los mismos caminos aleatorios por tres implementaciones: el motor de cuentas en C# de NQMaster, su versión Python (`research/mine/propcycle.py`) y los simuladores de investigación (`prop_wf.race`, `fu_flex`, `fu_pro`, `fu_m`).
  - Resultado: **780 y 1.950 casos, 0 diferencias** en aprobaciones, cuentas perdidas, días, cantidad de retiros y dinero cobrado (solo redondeo de 1 centavo).
  - Hay que correrlo de nuevo cada vez que se toque el motor.
- `research/mine/dash_cycle_ref.py` reproduce el panel desde un CSV de trades exportado del Strategy Analyzer, o desde los trades de investigación:
  - `python3 dash_cycle_ref.py --csv "trades.csv" --preset Lucid25K --fee 89`
  - Como solo ve trades cerrados, puede conservar una cuenta que el panel da por perdida por la posición abierta. El tope de riesgo no se aplica a los trades de investigación.

### Qué muestra con los trades de investigación (1 contrato base, ene-2024 a oct-2026, un solo camino histórico)

| Preset | Evals compradas / aprobadas / perdidas | Fondeadas perdidas / completadas | Retiros | Neto por mes: borde completo | −35% | borde cero |
|---|---|---|---|---|---|---|
| Lucid Flex 25K | 23 / 16 / 7 | 8 / 7 | 41 | ~$1.019 | ~$469 | ~$35 |
| Lucid Flex 150K | 23 / 16 / 7 | 9 / 6 | 34 | ~$2.569 | ~$2.149 | ~$135 |
| Lucid Pro 50K | 9 / 6 / 3 | 1 / 4 | 24 | ~$1.482 | ~$867 | ~$52 |
| MFFU 50K | 2 / 1 / 1 | 0 / 0 | 96 | ~$2.189 | ~$1.333 | ~$76 |

- Lucid Flex 25K del 15-jul al 8-oct-2026 (la ventana del gráfico de 120 días): 5 evals compradas (3 aprobadas, 2 perdidas), 3 fondeadas (2 perdidas), **2 retiros** de $1.000, neto +$1.355. Antes dije 5 retiros: esa cuenta suponía una fondeada desde el primer día.
- Con borde cero el neto queda cerca de cero y no negativo porque la firma absorbe las pérdidas y los retiros se llevan la suerte; en remuestreos (secciones de cuentas de abajo) el borde cero da mediana negativa.

### Revisión independiente del código (21-oct)
`research/mine/review_dashboard_2026-10-21.md`: 1 problema grave y 4 medios, todos en el pasaje a vivo o en cuentas Sim; corregidos con `patch_dashboard_review.py`.
- Grave: si la simulación terminaba el historial con la cuenta "frenada" (perdida o aprobada ese día), la cuenta real no operaba nunca. Ahora el freno simulado se borra al pasar a vivo y solo actúa mientras corre la simulación.
- Órdenes estacionadas y el reintento de MSEQ se re-dimensionan al tamaño real al pasar a vivo.
- Sim101 sin simulación del ciclo: arranca una cuenta nueva desde que pasa a vivo.
- Al detener la estrategia se devuelven tus valores (fase, contratos); igual, no guardes el template mientras la simulación corre en Sim.
- "Esperado por el backtest" se calcula por contrato base y por día operable, multiplicado por el tamaño en vivo.
- Los días de FOMC, ATR bajo o feriado no cuentan como días de la cuenta (igual que la investigación); el "por mes" se calcula sobre al menos un mes; PF sin pérdidas dice "sin pérdidas".

### Cómo usarlo
1. Copiá `NQMaster.cs` y apretá F5. No está compilado en NinjaTrader; solo pasó el chequeo de sintaxis.
2. Strategy Analyzer o gráfico: elegí el preset de la firma, *Fase REAL de la cuenta* = Eval, *Backtest: simular el ciclo* = true y cargá el precio que pagás por la eval.
3. Leé el bloque **SIMULACIÓN DE CUENTA**. El neto del Strategy Analyzer **no** descuenta retiros ni costos de evals; el panel sí.
4. Para verificar, exportá los trades y corré `dash_cycle_ref.py` con el mismo preset.
5. Parity con la investigación: sigue siendo con *Fase REAL* = Off (sin simulación), igual que antes.

## ★★★★★★★★★★★★ 2026-10-16 (tarde): backtest de 6 años y módulos nuevos

Ventana: octubre de 2020 a octubre de 2026. Datos: NQ real de Databento. Costos: $1,90 de comisión + 1 tick por lado. Montos: por contrato base.

Scripts en `research/mine/`: `six_base.py`, `six_reselect.py`, `six_modules.py`, `six_combo2.py`, `six_life.py`, `six_build.py`, `b7_report.md`.

**Sistema actual en 6 años** (`six_base.json`):

| Perfil | Trades/día | WR | PF | $/mes | DD máx. | Peor mes | Meses + | Sharpe |
|---|---|---|---|---|---|---|---|---|
| Ultra | 4,7 | 66,3% | 1,50 | $2.184 | $4.582 | −$2.210 | 59/73 | 3,70 |
| UltraQ | 4,0 | 69,2% | 1,53 | $1.980 | $4.759 | −$2.066 | 59/73 | 3,58 |
| WR70Plus | 3,4 | 70,7% | 1,54 | $1.542 | $3.223 | −$2.109 | 60/73 | 3,60 |

- Ultra por año (PF):

  | 2020 (oct-dic) | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
  |---|---|---|---|---|---|---|
  | 0,98 | 1,45 | 1,80 | 1,23 | 1,42 | 1,58 | 1,58 |

- Con 4 ticks de slippage por lado: PF 1,41.

**Qué se probó.** El criterio fue el mismo en todos los casos: elegir en 2020-10 a 2023 y comprobar en 2024-26, sin exigir 2010-19.

- **54.944 estrategias ya minadas:**
  - El ORB de 08:20 vuelve a aparecer, pero queda descartado: el backtest con ticks le saca el edge.
  - Quedan 7 módulos nuevos, uno por señal (`six_combo2.py`).
- **Módulos actuales:**
  - Ninguno mejora al quitarlo en los dos períodos a la vez.
  - ENG10 sigue apagado: falla en 2024-26.
  - LATEFH sí suma.
  - Los pesos por módulo elegidos en 2020-23 empeoran 2024-26, así que se rechazan.
- **5 familias nuevas** (agente, `families7.py`: squeeze, aceptación del rango previo, eficiencia del recorrido, posición en el rango nocturno, aperturas semanal/mensual): ninguna suma. La única con persistencia repite el MOM1030 que ya operamos.

**Módulos nuevos** (grupo 11, `SixYearModules`, **apagado por defecto**):

| Módulo | Qué hace | Trades T1 / T2 | PF T1 / T2 | PF T2 +4 ticks |
|---|---|---|---|---|
| CA04V | 04:00, sigue el precio si está ≥ 0,20 ATR del VWAP de sesión; stop 0,15 ATR, 1R | 103 / 135 | 1,95 / 1,21 | 1,13 |
| SO04 | 04:00, ≥ 0,35 ATR de la apertura de las 18:00, con la tendencia; 1R | 62 / 70 | 1,24 / 1,33 | 1,25 |
| GD03 | 05:00, va contra la movida desde las 03:00 (≥ 0,2 ATR), con la tendencia; stop en el extremo, 2R | 84 / 70 | 1,83 / 1,32 | 1,20 |
| RV11 | 11:00, volumen relativo ≤ 0,8 y ≥ 0,25 ATR del cierre previo; sigue la dirección, 1R | 56 / 51 | 1,58 / 1,52 | 1,44 |
| ENG26 | Vela 4H 02-06 envuelve a la de 22-02; entra a las 09:30, 0,5R | 106 / 102 | 1,57 / 1,33 | 1,26 |
| ORFAIL | Ruptura fallida del rango de 15 minutos, con la tendencia; objetivo el otro lado del rango | 144 / 143 | 1,25 / 1,25 | 1,20 |
| CAM3 | Falso quiebre de Camarilla L3/H3, con la tendencia; objetivo el VWAP | 73 / 65 | 1,29 / 1,34 | 1,24 |
| LATEFH | Ya existía; el mismo interruptor lo prende | 181 / 165 | 1,39 / 1,47 | — |

**Resultado con todos prendidos** (`six_build.py`; incluye el bloqueo de entradas opuestas a una posición abierta):

| | Ultra hoy | Ultra + módulos nuevos |
|---|---|---|
| Sharpe 2020-23 / 2024-26 | 3,45 / 3,96 | 3,76 / 4,09 |
| Ganancia en 6 años | $156,4 mil | $170,2 mil (+9%) |
| DD máximo | $4.694 | $4.406 |
| Peor mes | −$2.210 | −$2.150 |
| WR | 66,7 / 65,8% | 65,3 / 64,1% |

**En cuentas** (`six_life.py`, MFFU 50K, 1 contrato, preset actual, $ por mes por cuenta):

| Período | Edge completo | 35% menos edge | Pasar la evaluación en ≤ 20 días |
|---|---|---|---|
| 2020-23 | 1.713 → 1.984 | 1.142 → 1.351 | 30 → 33% |
| 2024-26 | 2.009 → 2.076 | 1.128 → 1.136 | 44 → 42% |

- En 2024-26, con 35% menos edge, P(año negativo) pasa de 0 a 9% y el percentil 10 baja de $557 a $159.

**Veredicto:** mejora poco y no pasa el criterio de cuentas de la auditoría. Por eso queda apagado hasta probarlo en NinjaTrader.

**Para probarlo:**

1. F5.
2. Strategy Analyzer: MNQ 1 minuto, 2020-10-15 a hoy, Ultra, 1 contrato. Dos corridas: `SixYearModules` en false y en true.
3. Exportá los trades de la corrida en true y corré `python parity_check.py <csv> --set ultra6` desde `research/mine`.
4. Prendelo solo si pasa la paridad y la corrida en true le gana a la otra.

Backup del archivo anterior: `NQMaster_backup_pre_six.cs`. El script `patch_six.py` lo regenera.

## ★★★★★★★★★ 2026-10-15 (later): "big size when an 80% strategy fires, to pass the eval fast" + update (English)

Scripts: `research/mine/sniper_eval.py`, `sniper_uniform.py`, `sniper_life.py` (-> `.json` / `.csv`). Code patches: `patch_evalhw.py`, `patch_report.py`.

Setup of every test:
- Data: real Databento NQ minute paths 2020-26, Ultra after the 10-12 overhaul + CPI09.
- Costs: +1 tick per side; firm rules as `month80.py`; daily profit stop 0.9 × consistency × target.
- Choose on starts 2020-03..2023-10 (T1), check on starts 2024-26 (T2). "Pass ≤ 1 month" = within 20 listed days (about 22 trading days).

**1. The idea as asked: any module that won ≥ 80% over the past year → big size.**
- Walk-forward flag: the module's own trades of the previous 365 days, at least 20 of them, with win rate ≥ 80%. Mostly MOM11, REV06 and MOM1030, about 4.8 trades per week.
- Those trades win 79.6% but average **+$46 per win vs −$132 per loss**, PF 1.34. That is lower than the full system's PF (~1.5).
- One loss at 10 contracts is about −$1,300, which is most of a 50K trailing drawdown.
- Lucid Pro 50K, 1 contract base, sniper trades at 8 contracts: single-eval pass ≤ 1 month 38/39% (T1/T2), but **busts 57/42%**.
- Thresholds of 75%, 85% and a 2-year window behave the same. Sniper-only (no other trades): worse.
- Compared with simply trading 2-4 contracts on everything, it is worse: Lucid Pro 50K at 2c passes 47/47% with 46/49% busts.
- **Verdict: not a good idea.** A high win rate with small targets does not mean a big edge. Size there adds variance, not edge.

**2. What does work: the two fixed ~80% modules (MOM1030, CPI09) at ×8 during the eval only.** 1 contract base, single eval.

| 50K eval, 1 contract | MOM1030/CPI09 ×1 | ×4 (default) | **×8** |
|---|---|---|---|
| Lucid Pro 50K, pass ≤ 1 month T1 / T2 | 24.6 / 35.1% | 27.7 / 41.3% | **33.5 / 46.4%** |
| — busts T1 / T2 | 18 / 24% | 19 / 23% | 27 / 24% |
| — 35% less edge, pass ≤ 1 month | 19.3 / 21.4% | 21.3 / 26.5% | **24.7 / 33.1%** |
| Lucid Flex 50K, pass ≤ 1 month | 24.3 / 34.8% | 27.3 / 40.3% | **33.6 / 47.8%** |
| MFFU Rapid EOD 50K, pass ≤ 1 month | 20.0 / 26.5% | 22.4 / 33.4% | **28.5 / 40.9%** |
| Peak open micros | 10 | 10 | 17 |

- **Lifecycle per 50K seat** (eval with restarts → funded → payouts), $ per month T1 / T2, 35% less edge in brackets:

  | Seat | ×1 / ×1 | ×4 / ×4 (today) | **eval ×8 / funded ×4** | ×8 / ×8 |
  |---|---|---|---|---|
  | MFFU | 1,064 / 1,583 (502 / 768) | 1,324 / 1,865 (708 / 1,008) | **1,351 / 1,903 (852 / 1,107)** | 1,602 / 2,168 |
  | Lucid Flex | 875 / 1,066 (448 / 644) | 939 / 1,230 (563 / 663) | **980 / 1,322 (656 / 686)** | 1,073 / 1,380 |

  - Accounts lost per year: about the same for eval ×8 / funded ×4 as for ×4/×4.
  - ×8 in the funded account roughly doubles funded busts (MFFU 1.2 vs 0.3-0.4 a year), so it stays eval-only.
- Whole portfolio at ×8: PF still rises, but Sharpe peaks at ×4-×6 and the drawdown grows (2020-23: $6.2k vs $4.6k). Outside evals ×4 stays the setting.
- 25K accounts ($1,000 drawdown): ×8 is too big (Lucid Pro 25K, 2020-23 pass 45 vs 53%). Keep the 25K presets (2 contracts, ×4).
- Fastest single eval is still more contracts on everything: Lucid Pro 50K 3c passes about 44% within a month and about 38-43% within 10 days.

**3. Implemented in NQMaster (stub compile OK, NOT compiled in NinjaTrader: F5).**
- `EvalHighWrMultiplier` (group 07, 0-8, default 0 = normal ×4). In PropMode Eval it replaces the MOM1030/CPI09 multiplier.
  - **Presets Lucid50K and Mffu50K set it to 8** in Eval; the preset printout shows it.
  - Funded accounts keep ×4; the SAFE gear (noBoost) still removes it.
  - Backup: `NQMaster_backup_pre_evalhw.cs`.
- `ModuleHealthReport` (group 10, default on). The Output window and log file list per module: trades, win rate, PF and net, for the whole run and the last 365 days.
  - It marks modules at ≥ 80% last year and modules losing last year (review).
  - It prints when the strategy goes live (loaded history) and at the end of a backtest.
  - It is for the yearly review, not for sizing.
- `DisableModules` (group 10, comma list, any profile). Switches modules off by name, e.g. `REV06`, which the walk-forward yearly review (`robust16.py`) flags for 2027. Backup: `NQMaster_backup_pre_report.cs`.

**Settings for a 50K eval now:** Profile Ultra, Contracts 1, PropMode Eval, PropPreset Lucid50K or Mffu50K (sets ×8). Funded: same preset with PropMode Funded (×4).

## ★★★★★★★★ 2026-10-15: "80%+ setups at 4 contracts" (English)

Scripts: `research/mine/wr80_lab.py` -> `wr80_lab.json` / `wr80_lab.csv`, and `research/mine/size_q.py`.

**Question.** Can we know before the entry that a trade belongs to a group that wins 80% or more, and trade 4 contracts there?

**Search.** Every Ultra trade from 2010 to 2026 (real Databento NQ) gets 19 features known before the entry:
- trend, 5/20/60-day returns, ATR regime, stop size;
- VWAP distance, gap, prior-day range and position;
- overnight range, position in the day's range, last-30-minute move, volatility, weekday.

Each candidate setup is one module × one feature × one quantile side. The protocol was fixed before looking:
- Chosen on 2020-23 with win rate ≥ 80% and PF ≥ 1.5.
- Must then hold in 2024-26: win rate ≥ 80% and PF ≥ 1.3.
- And in 2010-19: win rate ≥ 75% and PF ≥ 1.1.

**Result.**
- 182 setups pass 2020-23 and 30 also pass 2024-26 and 2010-19.
- **The same search with the features shuffled at random also gives about 34 survivors (maximum 44).** So no feature finds better trades than chance.
- Every survivor is just **MOM1030**, a module whose normal win rate is already about 80%: 80% in 2020-23, 83% in 2024-26, 75-79% in 2010-19.
- Conclusion: we cannot predict which individual trades will win 80%+. We can only pick the modules whose normal win rate is about 80%.

**Implemented: 4 contracts on the two ~80% modules.**
- MOM1030 win rate: 80-83% since 2020, 75-79% before.
- CPI09 win rate: 78-81% since 2020.
- New properties: `Mom1030Multiplier = 4` and `Cpi09Multiplier = 4`, group 01.

| | Sharpe 2010-14 / 2015-19 / 2020-23 / 2024-26 | PF, same periods | $ 2020-23 / 2024-26 | Max drawdown 2020-23 / 2024-26 |
|---|---|---|---|---|
| Ultra (before) | 0.26 / 1.16 / 3.44 / 3.74 | 1.026 / 1.132 / 1.474 / 1.506 | 78.6k / 77.5k | 3,621 / 4,447 |
| Ultra + MOM1030 x4 + CPI09 x4 | 0.42 / 1.23 / 3.54 / 3.96 | 1.042 / 1.139 / 1.481 / 1.529 | 86.3k / 86.2k | 4,582 / 3,661 |
| UltraQ (before) | 0.61 / 1.14 / 3.36 / 3.59 | 1.068 / 1.142 / 1.510 / 1.531 | 71.0k / 69.4k | 3,390 / 3,985 |
| UltraQ + x4 | 0.76 / 1.17 / 3.48 / 3.78 | 1.085 / 1.145 / 1.519 / 1.552 | 78.8k / 77.6k | 4,711 / 3,143 |

- Sharpe and PF are higher in all four periods, and income rises about 10-11%.
- The 2020-23 drawdown is about $1k larger.
- Rejected: ORB60 x2 (higher PF but lower Sharpe and +$1.3k drawdown); MOM11 x2 (it lost money in 2010-19).
- **ORB at 75%+ win rate:** it is a target choice, not a better setup. ORB60 at 0.4R wins 74-75% with PF 1.42-1.51; at 0.6R (the current setting) it wins 68-71% with PF 1.60-1.62. A higher win rate there means lower PF.

**Options open interest (CME QuikStrike heatmap data), 2026-10-15** — `research/mine/oi_lab.py` -> `oi_lab.json`. This uses Databento NQ quarterly options (NQ.OPT, which does not include the weeklies), with OI as published the day before. It cost about $7.80 of free credit.

| Test | 2024-25 | 2026 |
|---|---|---|
| Close nearer the biggest-OI strike than the open was (front expiry) | 44.6% (control strike 43.1%) | 38.5% (control 43.2%) |
| First touch of a top-3 OI strike, 30 min later reversed | 46.6% (ordinary round number 50.2%) | 45.8% (round number 45.4%) |
| Ultra trades with a big OI strike between entry and target (within 0.4%) | WR 65.0%, PF 1.42 vs 66.2%, 1.47 without | WR 63.0%, PF 1.51 vs 66.8%, 1.66 without |

- No magnet effect and no support/resistance effect.
- Trades with an OI wall ahead are slightly weaker, but they are still clearly profitable (PF 1.4-1.5). Skipping them would lose money.
- **Verdict: the open-interest heatmap does not help NQMaster.** Nothing was implemented.

## ★★★★★★ 2026-10-14: higher win rate AND profit factor — profile UltraQ + CPI09 (English) — READ THIS FIRST

Scripts: `research/news_hist.py` (CPI calendar 2009-2019 from the BLS archive; 2020-26 was already in `news.py`), `research/mine/cpi_lab.py` (CPI strategies), `research/mine/ultra_q2.py` (levers screened on 4 periods), `research/mine/ultraq_build.py` (UltraQ trades + edge-monitor calibration), `research/mine/patch_cpi09.py` (code). Backup `NQMaster_backup_pre_cpi09.cs`.

Data: real Databento NQ 1-minute futures, 2010-06 to 2026-10. Four periods: 2010-14 and 2015-19 cost-normalised (cost 0.345% of ATR); 2020-23 and 2024-26 real $ per MNQ ($1.90 + 1 tick per side).

**1. CPI method (`cpi_lab.py`, 4,968 settings, CPI days only, 211 releases).**
- Most CPI rules lose. The median PF is 0.81-0.92 in every period, and choosing on 2020-23 did not predict 2024-26.
- One family holds in all four periods: **fade the CPI move at the 09:30 open**. Measure the move from the 08:30 bar open to 09:29; if it is at least 0.05 ATR, trade against it at the 09:30 open. Stop 0.35 ATR, target 0.5R, exit after 60 minutes.

| CPI09 | 2010-14 | 2015-19 | 2020-23 | 2024-26 |
|---|---|---|---|---|
| Trades | 42 | 45 | 41 | 27 |
| PF | 1.58 | 1.13 | 1.94 | 2.62 |
| Win rate | — | — | 78% | 81.5% |

- With 4 ticks of slippage per side, the 2024-26 PF is still 2.55.
- The same rule on ordinary days loses (PF 0.82-0.93), so the effect is specific to CPI days. On NFP days it does not hold (2015-19 PF 0.6-0.9).
- The neighbouring settings agree: entering 30 or 60 minutes after the release with a minimum move of 0-0.2 ATR all stay above PF 1.
- Entering right after the release (08:31-08:45) works in 2024-26 but **loses in 2020-23**, because CPI moves trended in 2021-23. So no early entry is used.
- **Caveats:**
  - It trades only about 12 times a year, so it adds roughly $25-50 per month.
  - The samples are small: 18 of 4,968 settings passed, about what chance alone would give. The case for it is the CPI-only control and the stable neighbouring settings.
- It is now module **CPI09**, on by default in Ultra, UltraQ and WR70Plus.
- Effect on WR70Plus: win rate +0.03..0.14 and PF +0.005..0.01 in 3 of 4 periods; in 2015-19 the win rate is -0.03 and PF +0.001, i.e. flat.

**2. Ultra levers (`ultra_q2.py`, list fixed before looking).**
- Tested: drop REV06 / ON07 / the wide VW13 lot / MOM11 / LON / ICT, skip CPI mornings, skip CPI days, skip NFP mornings, and add CPI09.
- No single change raises both win rate and PF in all four periods. The high-win-rate modules (REV06, MOM11) have low PF, and the high-PF modules (LON, ICT, ON07) have low win rates.
- The combination that does raise both everywhere is **UltraQ** = Ultra without ON07, LON, ICT and without the wide VW13 lot, plus CPI09:

| | 2010-14 | 2015-19 | 2020-23 | 2024-26 |
|---|---|---|---|---|
| WR Ultra → UltraQ | 59.7 → 63.5 | 61.5 → 64.6 | 66.9 → 70.2 | 65.7 → 68.3 |
| PF Ultra → UltraQ | 1.023 → 1.068 | 1.133 → 1.142 | 1.470 → 1.510 | 1.499 → 1.531 |
| $ per month (real) | | | 1,610 → 1,478 | 2,301 → 2,103 |
| Max drawdown (real) | | | 3,470 → 3,390 | 4,570 → 3,985 |

- PF is equal or higher in every year 2020-26: 1.41, 1.52, 1.77, 1.29, 1.40, 1.52, 1.68.
- The win rate is +2-4 points every year.
- About 3.9 trades a day.
- Sharpe is about equal: +0.38 / -0.02 / -0.04 / -0.06 versus Ultra.
- **The cost: about 8% less money.** For prop lifecycle income, Ultra stays slightly ahead.
- The changes were picked after seeing all four periods (10 combinations compared). Expect part of the gain to shrink live.

**How to use:**
- Profile **UltraQ** (new) with Contracts 1. CPI09 is on automatically (UseCpi09).
- The CPI dates for 2024-2027 are built in. Add later years in "Extra CPI release dates".
- Edge monitor for UltraQ: k 0.0696, h 20.87.
- To validate in NinjaTrader, export the UltraQ run's trades and run `python nt_compare.py <trades.csv> --set ultra_q`.
- Not compiled in NinjaTrader yet; the stub type-check passes. **Press F5 on the PC.**

## ★★ 2026-10-12 overhaul — READ THIS FIRST (English)

Full report: https://claude.ai/artifact/61HUsYa5HWgrGunADkmDN2 (NQMaster System Audit). Research:
- `research/mine/hist_profiles.md`: every profile on the same real futures data.
- `cand16.py`, `cand16_life.py`, `robust2_*.py`: candidates and the risk layer.
- `stress_hist.py`, `stress_vol.py`, `liqbuf.py`: August-type stress tests.
- `rules16_*.py`: context rules checked on 2010-19.
- `audit_code_2026-10-12.md`: code audit.
- `audit_bestpractices_ai_2026-10-12.md`: best practices and the Python/AI question.

**Older sections below use profile names that no longer exist.** If an older section disagrees with this one, this one wins.

### Profiles now: Ultra (default), WR70Plus, Durable, Custom
- **Removed:** MaxSharpe, WinRate70, MaxPlus, MaxPlus2, Core, MaxTrades, and NQMaster's Gold profile (gold runs in GoldMaster.cs). On the same real futures each later version beat the earlier ones (`hist_profiles.md`):

  | Version | Sharpe 2020-26 |
  |---|---|
  | MaxSharpe | 2.60 |
  | MaxPlus | 2.77 |
  | MaxPlus2 | 2.90 |
  | Ultra (old) | 3.43 |

  No old system did better. **A saved chart/template/workspace that used a removed profile will not load the strategy: remove it and add NQMaster again.**
- **Ultra** changes:
  - ENG10 and LATEFH are off by default (`UseEng10` / `UseLateFh` still exist). The audit found them at chance level.
  - The ORB90 "VWAP" and ORB60 "ATR" context boosts are removed. On 2010-19 data never used to choose them, they held in 1 of 4 periods and failed in 2015-19 and 2024-26.
  - New `MinStopAtr` 0.10: structure trades with a stop narrower than 0.10 x daily ATR are skipped (win rate +0.4-0.8 points in all 4 periods).
- **WR70Plus:** the same two boosts removed, plus the same minimum stop.
- **Durable (new):** the 6 modules that held up on 16 years of real futures (ORB60, ORB90, MSEQS, CRT11, VOLB 2R, NF05). This is the fallback if the edge monitor alarms.
- **Custom:** every switch applies. MOM1130 and RSI2 are only available here.

Real NQ futures, 1 base contract, $1.90 + 1 tick per side:

| Profile | 2010-14 PF* | 2015-19 PF* | 2020-23 WR / PF / Sharpe / $ per month | 2024-26 WR / PF / Sharpe / $ per month | 2024-26 max DD / worst month |
|---|---|---|---|---|---|
| Ultra (old) | 1.01 | 1.12 | 66.6% / 1.48 / 3.53 / $1,912 | 64.9% / 1.46 / 3.52 / $2,395 | $5,871 / -$3,635 |
| **Ultra (new)** | 1.02 | 1.13 | 66.9% / 1.47 / 3.38 / $1,717 | **65.7% / 1.50 / 3.65** / $2,304 | **$4,570 / -$2,670** |
| WR70Plus (old) | 0.98 | 1.07 | 71.8% / 1.59 / 3.68 / $1,440 | 68.8% / 1.46 / 3.17 / $1,581 | $4,059 / -$2,950 |
| **WR70Plus (new)** | 0.98 | 1.09 | **72.2%** / 1.57 / 3.59 / $1,359 | **69.4%** / 1.48 / 3.30 / $1,567 | $3,893 / -$2,885 |
| Durable | 1.18 | 1.23 | 62.9% / 1.60 / 2.73 / $953 | 60.2% / 1.66 / 2.91 / $1,429 | $3,845 / -$2,504 |

\* Cost-normalised; this data was never used to choose anything.

August 2026 at 1 contract: Ultra old -$1,830 (PF 0.76), Ultra new -$1,210 (PF 0.83), WR70Plus -$2,950.

### Risk layer (prop accounts) — the main change against months like August
Losing months are not predictable:
- Month-to-month autocorrelation is about 0.
- Volatility, chop and VIX filters do not predict them.
- 11 of 81 months lost money, which is what random ordering of the same trades gives (13.6% vs 15.6%).

What breaks accounts is a few large-risk trades (VOLB, ORB60, MSEQ) while the cushion is small. So:
- **`RiskCapPerContract` $300 (group 07):** while the cushion is below **`EvalRiskCapCushion` $1,200** (eval) or **`FundedRiskCapCushion` $2,000** (funded), trades risking more than $300 per base contract are skipped. Above those cushions, everything trades.
- **`FundedCushionSafe` default is now 0.** The cap replaces the old SAFE gating.

MyFundedFutures Rapid EOD 50K lifecycle, 1 contract, 1,000 resampled years:

| Setup | $/month 2020-23 / 2024-26 | +1 tick | Accounts lost per year |
|---|---|---|---|
| Ultra old, no cap | $1,115 / $1,508 | $1,005 / $1,397 | 0.56 / 1.65 |
| **Ultra new + cap** | $893 / $1,327 | $788 / $1,214 | 0.45 / **0.70** |
| WR70Plus new + cap | $569 / $674 | $497 / $605 | 0.18 / 0.48 |

Lucid Flex 50K: Ultra new + cap $690 / $882 per month with 0.94 / 1.32 accounts lost, vs old $843 / $1,025 with 1.16 / 3.06. **The trade-off: about 10-20% less money for about half the lost accounts in 2024-26.**

### Honest answer on "never lose an account in a month like August"
Every eval and funded account was started on every real day of summer 2026 (`stress_hist.py`), MFFU 50K, 1 contract:

| Setup | Eval pass, starts Jun-Aug 2026 | Funded busted within 60 days |
|---|---|---|
| Ultra old | 16% | 88% |
| **Ultra new** | 18% | **59%** |
| WR70Plus old | 25% | 73% |
| **WR70Plus new** | **33%** | **47%** |

Over all of 2020-26 the new setup is equal or better: eval pass 80.8% / 75.5% vs 80.6% / 72.8%, and funded 60-day busts 11.9% / 18.0% vs 16.2% / 31.4%.

Summer 2026 had a daily ATR of 530-600 (normal ~340) and a drawdown of $3,671 at 1 contract. A $2,000 trailing drawdown cannot absorb that.

Rejected because they cost more than they saved (2020-23 history and resampling):
- **High-volatility guard** (the cap at any cushion when ATR > 1.2-1.5 x its 250-day median, `stress_vol.py`): -$150 to -$500 per month.
- **Intraday "stop before liquidation" buffer** ($100-400 above the threshold, `liqbuf.py`): no gain.

What protects you in practice:
1. The risk cap.
2. Staggering account starts so they do not all sit on a small cushion together.
3. WR70Plus in the funded account if you prefer fewer busts over money.
4. The edge monitor with recalibrated thresholds:

   | Profile | k | h |
   |---|---|---|
   | Ultra | 0.0758 | 18.57 |
   | WR70Plus | 0.0577 | 12.18 |
   | Durable | 0.0458 | 10.71 |

   Ultra's false-alarm rate is 0.5% per year.

### Operations layer (code audit) — group "10. Operations (safety)"
- **Account sync guard** (on):
  - If the account position and the strategy position differ for 2 bars (firm auto-close, manual flatten, restart with a real position, overfill), the strategy flattens that instrument on the account, raises an alert and stops.
  - **Never trade MNQ/MGC by hand on an account where the strategy runs.** If you must, turn this off first.
- **Skip holiday / half-day sessions** (on):
  - The real session end is read from NinjaTrader's trading hours.
  - No entries in early-close sessions; flat 5 minutes before an early close.
  - All entries are cancelled at every session start.
  - No entries on a bar that arrives more than 2 minutes late.
  - In the 2025-26 NT run, these sessions lost $1,367 on 51 trades.
- **Max open contracts** (20) for the whole account (MNQ + MGC): Lucid 50K funded 20, MFFU 50K 30. The validated peak is 11 MNQ at 1 contract.
- **Roll guard** (on):
  - No new entries from the roll date of the chart's contract (MNQ Dec-26: 2026-12-10).
  - Roll: after 16:00 ET on that day, disable both strategies, enable them on the next contract with the same settings, and keep "Merge back adjusted".
- **Log file** (on): `Documents\NinjaTrader 8\nqmaster_logs\<account>_<date>.txt`. Alerts for target reached, drawdown guard, edge alarm, rejections, stale orders and mismatches.
- **Other fixes:**
  - 2027 CPI/NFP and the missing 2026-10-02 NFP are in the news list. A warning appears when the list ends within 35 days.
  - Unreadable dates are printed.
  - Realtime stale orders keep blocking the opposite side.
  - Multi-lot exits are tracked per lot.
  - A mid-session restart uses the saved day start for the cushion.
  - 2 rejections stop a module for the session; "liquidation / disabled / margin" rejections stop new entries.
- **GoldMaster:** flatten at **16:00 ET** (was 16:51: MFFU closes at 16:10, Lucid at 16:45). The research re-price is neutral; see GOLDMASTER_GUIA.md.

### Recommended settings (unchanged firms, new defaults)
- **MyFundedFutures Rapid EOD 50K**
  - Eval: Profile Ultra, Contracts 1, PropMode Eval, EvalProfitStop 800, MaxOpenContracts 30.
  - Funded: PropMode Funded, Contracts 1, withdraw down to $4,100 profit. Step-up (FundedStepUpCushion 3000) is optional: more money, more variance.
  - GoldMaster Robust 1 contract with FlattenTime 1600.
- **Lucid Flex 50K:** the same, with EvalProfitStop **1350** (not 1400 / 700, see the 2026-10-13 section) and MaxOpenContracts 20. Presets set all of this.
- **Prefer fewer busts over money:** WR70Plus in the funded account.

### What you need to do
1. Copy `NQMaster.cs` and `GoldMaster.cs` to `Documents\NinjaTrader 8\bin\Custom\Strategies` and press **F5**. They were type-checked here against an NT8 API stub, not compiled; if F5 shows an error, send it to me.
2. Remove old NQMaster instances that used removed profiles and add them again.
3. Run the Strategy Analyzer on MNQ 1m from 2025-01-04 with Profile Ultra, Contracts 1 and default settings. Send the trades CSV.
   - Expect fewer trades than the 2026-10-09 run (2,221): ENG10/LATEFH are off, holiday sessions are skipped, and the minimum stop applies.
4. Paste the backtest numbers into the chat before going live.

---


`NQMaster.cs` está compilada e instalada. En NinjaTrader abre el NinjaScript Editor y pulsa **F5**. Reemplaza las 11 instancias anteriores.

## ★ 2026-10-08 research round (English): trade quality, quant strategies, overfitting audit, prop firms
Five parallel studies. Files: `research/mine/wrq_*` (trade quality), `q_*` (quant literature), `audit_*` (overfitting audit),
`acct1c_*` (1-contract account economics), `mffu_*` and `news_cost*` (MyFundedFutures), prop-firm survey notes in
`research/mine/propfirms_2026.md`.

### 1. New rules in NQMaster (group 02, all ON by default)
| Property | Rule | Effect (IS / CFD 2024-26 / MNQ 2024-26) |
|---|---|---|
| `OrbPriorCloseAtr` = 0.10 | ORB60 / ORB90 only trade when the breakout level is >= 0.10 x daily ATR beyond the prior RTH close in the trade direction (-1 = off) | ORB60 PF 1.62/1.60/1.56 -> 1.92/1.81/2.05; ORB90 1.43/1.31/1.38 -> 1.87/1.48/1.75 |
| `VolbBreakEven` = true | VOLB 2R (Ultra): stop to entry + 0.10R once price reaches +0.75R | VOLB WR 52/51/50% -> 61/62/61%, PF 1.25/1.52/1.50 -> 1.30/1.66/1.57 |
| `MomAgreement` = true | MOM1030 / MOM13 (Ultra) only enter when another module already holds a filled position the same way | MOM1030 PF 1.08/1.13/1.17 -> 1.34/1.46/1.71 (2015-19 0.89 -> 1.21); MOM13 1.31/1.17/1.19 -> 1.54/1.45/1.51 |
| `VolbTrendLastEntry` = 1047 | trend-only VOLB (WR70Plus, Estable gear): no entry after 10:47 ET (0 = off) | VOLB_tf1 PF 1.47/1.24/1.20 -> 1.72/1.34/1.31 |

Portfolio (1 base contract, $1.90 + 1 tick, FOMC skipped):
| | WR IS / C24 / REAL | PF IS / C24 / REAL | Sharpe | $/month REAL |
|---|---|---|---|---|
| Ultra before | 65.0 / 63.3 / 63.8 | 1.42 / 1.42 / 1.45 | 3.31 / 3.49 / 3.70 | 2,711 |
| **Ultra now** | **66.6 / 64.9 / 65.8** | **1.50 / 1.50 / 1.54** | 3.71 / 3.70 / 3.95 | 2,707 |
| Ultra now, lean (`UseOn07`, `UseLateFh`, `UseEng10` = false) | 67.5 / 65.8 / 66.8 | 1.52 / 1.53 / 1.57 | 3.60 / 3.69 / 3.92 | 2,534 (max DD -11%) |
| WR70Plus before | 70.6 / 68.0 / 68.8 | 1.52 / 1.41 / 1.46 | 3.36 / 2.88 / 3.15 | 1,769 |
| **WR70Plus now** | **71.3 / 68.8 / 69.8** | **1.61 / 1.45 / 1.53** | 3.86 / 3.08 / 3.50 | 1,751 |
Only these 4 of ~2,550 tested exit / filter changes survived (IS -> OOS correlation of PF gains ~0.0-0.1; PBO ~0.56 for
'pick the best exit / filter'): smaller targets raise WR mechanically but not PF. Lean Ultra: the audit rates ON07, LATEFH and
ENG10 as chance-level evidence (isolated parameter cells, profit concentrated in one year); dropping them costs 6-8% of $ but
raises WR and PF and lowers drawdown.

### 2. Quant strategies from the literature (q_*): nothing to add
9 new families (2,784 configs): noise-area intraday momentum (Zarattini 2024; real on NQ but it duplicates VOLB), pre-FOMC drift,
turn of month, pre-holiday, rebalancing flows, same-half-hour persistence, time-series momentum, variance-ratio regimes, NQ-vs-ES
relative strength, cross-asset lead-lag (1-minute lagged correlation 0.005-0.01). Two thin survivors (month-end rebalancing fade,
afternoon variance-ratio momentum) add +0.02..+0.2 Sharpe with confidence intervals including 0 and WR 40-55% -> not added.
"Quantum" trading: no demonstrated, implementable edge (best-known claim: HSBC + IBM 2025 on bond quote fill rates).

### 3. Overfitting audit (audit_*)
- Profiles pass the deflated Sharpe test at 300k trials (Ultra 1.00 CFD / 0.93 REAL); every year 2020-26 positive.
- Modules are weaker than their backtests: in most mined families the IS-best config has ~0 out-of-sample Sharpe.
  Strong: CRT11, MSEQ, ORB60, VOLB, LON, NF05, LF06. Watch: ICT x2 (2026 PF 0.73), MOM11, ORB90, VW13, REV06, LATE15, LF0430.
  Chance-level: MOM1030 / MOM13 without the agreement rule, ON07, LATEFH, ENG10; gold ENG0408, SVWAP22, ENG0206 (gold is a
  diversifier with low proven edge: DSR 0.03-0.26).
- Realistic forward expectation (+1 tick, 35% of the edge removed): Ultra WR ~63%, PF ~1.26, ~$1,700/month per base contract;
  WR70Plus WR ~69%, PF ~1.27, ~$1,100/month (2024-26 volatility). Range days remain the main risk (PF 0.76-0.84).

### 4. Prop firms (survey verified Oct 2026, sources in propfirms_2026.md)
- **Apex bans automation since 2026-03-01 (Apex 4.0)** -> the Apex scaling plan in OPERAR_5x150K.md is no longer valid.
- Topstep: NinjaTrader closed to new accounts (TopstepX only). Take Profit Trader, Alpha Futures, Phidias, Earn2Trade: no bots.
- Bot-friendly: Lucid, MyFundedFutures (MFFU), Bulenox, FundedNext, (FTMO Futures beta), Tradeify (exclusive use only).
- Going live closes the sim accounts at Lucid / Topstep / MFFU.

### 5. Best 1-contract plan: MyFundedFutures Rapid EOD 50K (mffu_rapid*.py, exact dense grids, 9 tests)
Rules (help.myfundedfutures.com, Aug 2026): eval $157 one-time, target $3,000, $2,000 EOD trailing (locks at +$100), no DLL,
30% consistency, min 4 days, 30 micros; funded: EOD trailing $2,000 locking at +$100, no consistency, no DLL, **daily payouts with
no cap** once $2,100 buffer is cleared (min $500), 90/10, max 3 Rapid accounts, **Tier-1 news: flat and no orders 2 min around
CPI / Employment Report / FOMC minutes** (bots allowed; no HFT, no hedging, no copy trading between traders).
| | Eval pass (hist / +1 tick / bootstrap) | Median days | $/month per account slot (mean / worst of 9) | Cash per funded month |
|---|---|---|---|---|
| Eval Estable 1c -> funded **1c**, keep $4,100 | 99/86/82 · 97/80/77 · 92/70/69 | 28-36 | **1,647 / 1,113** | ~2,360 |
| Eval Estable 1c -> funded 1c, 2c from $3,000 cushion (manual), keep $6,100 | same | same | 2,780 / 1,927 | ~4,100 |
| Lucid Flex 50K, eval Estable 1c -> funded 1c (acct1c_) | 99/87/85 | 26-31 | 1,033 / 840 | ~1,850 |
- News blackout cost (news_cost.py): Ultra -2.4/-4.0/-5.7% of P&L, WR70Plus -4.2/-1.3/-2.8% (IS/C24/REAL). Not in the table.
- Assumes the account keeps running (MFFU moves accounts to live at its discretion or after a $10k day; live = $0 start,
  $2,000 EOD, 90/10 daily, up to $5k of sim profit into a reserve). If it were moved to live after 12 payouts with no income
  afterwards: ~$960/month.
- Under the realistic forward haircut (35% of the edge removed, mffu_haircut.py): 1c/1c $712/month per slot (eval pass ~59%),
  1c -> 2c $1,171; cash per funded month still $1,690 (1c) / $2,800 (2c).

**NinjaTrader settings, MFFU Rapid EOD 50K**
- Eval: NQMaster Profile Ultra, Contracts 1, AdaptiveSize false, PropMode Eval, EvalTarget 3000, PropTrailingDD 2000,
  EvalCushionFull 1200, EvalSafeSet Estable, EvalProfitStop 800, ConsistencyPct 30, AtrStartMax 0, NewsBlackout false.
  GoldMaster Profile WinRate, Contracts 2, EvalTarget 3000, ConsistencyPct 30, AccountProfitStop 800, NewsBlackout false.
- Funded: NQMaster Profile Ultra, Contracts 1, PropMode Funded, FundedCushionSafe 0, FundedCushionFull 0, FundedProfitStop 0,
  FundedPayoutAt 4600, **NewsBlackout true**. GoldMaster Profile Robust, Contracts 1, AccountProfitStop 0, **NewsBlackout true**.
  Request a payout whenever the balance is >= start + $4,600 and withdraw down to start + $4,100.
- 2027 CPI / Employment Report dates are not published yet: add them to `NewsTimes` ("yyyy-MM-dd 08:30", comma list) when BLS
  publishes the 2027 schedule. FOMC minutes (decision + 21 days, 14:00) are built in through 2027.
- Ask MFFU support in writing to confirm that (a) a NinjaTrader bot is fine on Rapid EOD, and (b) holding positions through
  non-Tier-1 releases (e.g. 08:30 jobless claims, 10:00 ISM) is allowed on Rapid EOD sim funded; their policy text has one line
  that reads as 'no positions 2 min around any data release' (if so: -15-18% of Ultra P&L, news_cost.py scenario ALL).

## ★ 2026-10-09 Order-flow boost (EXPERIMENTAL, group 09 "Order flow", default OFF)

> **RESULT (same day): FAILED the out-of-sample test -> keep `UseOrderFlowBoost` OFF; the Tick Replay backtest below is not needed.**
> Second free Databento credit ($116.61 of $125): NQ aggressor trades for 11 NEW months (2025-05..2026-03) + MNQ for Sep 2025, rule unchanged
> (`research/mine/of_validate.py` -> `of_validate.json`). On 1,207 new Ultra trades the boosted 19% averaged $19.0 (PF 1.49, WR 64.8%) vs
> $19.4 (PF 1.42, WR 66.8%) for the rest; rank correlation -0.02; better in only 6 of 11 months; the top fifth of the delta was one of the
> WORST groups (PF 1.28). Boost ON made more $ (+18%) only because the size was bigger: PF 1.43 -> 1.45, max DD +9% = plain leverage.
> The Apr-Oct 2026 result was luck. Delta over the last 5 / 15 / 30 minutes: orderings flip between the samples too (`of_validate_other.py`).
> MNQ's own flow vs NQ's (Sep 2025): correlation 0.67-0.72, same boost decision 70% of the time.

What it does: NQMaster reads every trade from the tick stream (`OnMarketData`), splits volume into aggressive buys (trade at/above the ask) and aggressive sells (at/below the bid; tick rule in between, same as `OrderFlowRecorder.cs`), and keeps the **session cumulative delta** = (buys - sells) / (buys + sells) since 18:00 ET. When an entry goes the same way as the delta by >= `OrderFlowCvdMin` (0.015), its size is multiplied by `OrderFlowBoost` (2).
- `OrderFlowStack` off (default): never above 2x the base size (a trade already at x2 from context / confluence / ICT stays x2). On: x2 on top (up to 4x).
- Market entries use the delta at the bar close before the fill (= research). Resting stop / limit entries (ORB60, ORB90, VOLB, ENG10, LON, ICT) are re-sized every 1-minute bar until they fill (`ChangeOrder`; if NinjaTrader ignores a change, that order keeps its size and the Output says so).
- Not in safe / no-boost prop modes, not in the Gold profile. It changes **size only**: same trades, same entries, same exits.
- Dashboard line: current session delta, which side is boosted now, boosted / total entries. End of run (Output): "order flow: N trades read, X of Y entries filled with the boost".

Research (`research/mine/of_trades.py`, `of_boost.py` -> `of_boost.json`; Databento NQ aggressor trades 2026-04-01..10-08, Ultra on real NQ futures, $ per MNQ contract):

| Apr 1 - Oct 8 2026 | Entries boosted | Net | PF | Max DD |
|---|---|---|---|---|
| Boost OFF | - | $18,096 | 1.43 | $4,154 |
| Boost ON (cap, default) | 16% | $23,943 | 1.54 | $4,479 |
| Boost ON + Stack | 16% | $27,473 | 1.61 | $4,479 |
| Jul-Oct only (out of sample): OFF / cap | 12% | $3,082 / $5,368 | 1.13 / 1.21 | $4,154 / $4,479 |

Honest caveat: it was 1 of ~30 order-flow cells tested, with a weak rank correlation (0.06): it is NOT statistically proven. Boosted trades did better in every full month Apr-Sep, but that is ~100 trades. It also uses MNQ's own trades on an MNQ chart, while the research used NQ's.

### How to backtest it (Strategy Analyzer)
1. F5 in the NinjaScript Editor (the new code is parse-checked only).
2. Tools > Options > Market data: tick **Show Tick Replay**.
3. Strategy Analyzer: NQMaster, MNQ 12-26, 1 Minute, **Tick Replay ticked** in the data series, from **2026-02-01** (warm-up ~25 RTH days) to 2026-10-08, same commission / slippage 1 as before. Profile Ultra, Contracts 1, AdaptiveSize false, PropMode Off, everything else default.
4. Run A: `UseOrderFlowBoost` = false. Run B: `UseOrderFlowBoost` = true. Same settings, both with Tick Replay (slow: it reads every tick).
5. Check the last Output line of run B: about 12-20% of entries boosted is expected. "NO TICK DATA" = Tick Replay is not on or the data provider has no tick history for those dates.
6. Send both trade CSVs: `research/mine/nt_compare.py` + a split of boosted vs not boosted per module and per month will tell whether MNQ's flow behaves like NQ's. Keep it on only if run B beats run A in Jul-Oct too.
7. If MNQ shows nothing: one more run B on an **NQ** chart (Contracts 1 = 10x MNQ dollars) tests the exact research flow; if NQ works and MNQ doesn't, NQMaster can be changed to read NQ's flow while trading MNQ.

Live: the delta needs the whole session. A chart loaded mid-session does not boost until the next 18:00 ET start (dashboard: "waiting for the next 18:00 ET session") unless Tick Replay is also on for the live chart. Script `research/mine/patch_orderflow.py`; backup `NQMaster_backup_pre_orderflow.cs`.

## ★ 2026-10-10 Warm-up days (new setting, both strategies)

- **NQMaster** group "03. Risk / account" → `Warm-up days` (default **15** = validated: ATR from 14 RTH days, trend from 15 closes). Range 2-15.
- **GoldMaster** group "02. Risk / account" → `Warm-up days` (default **60** = validated). Range 2-60.
- With 2 the modules trade from the 3rd RTH day of loaded data. ATR is then the plain average of the few days seen and the
  trend is today's close vs the average of the few closes seen: until ~15 (NQ) / ~20 (gold) days are loaded the signals are an
  approximation and **those first weeks will not match the research**. After that everything is identical to the default.
- Live trading never needs a low value: when a strategy is enabled it first runs over the history loaded on the chart, so with
  **Days to load ≥ 45 (NQMaster) / ≥ 120 (GoldMaster)** it is already warmed up at the first live minute.
- Backtests that must match the research: keep the defaults and start the Strategy Analyzer 1-2 months (NQ) / 3 months (gold)
  before the period you want to look at. Script `research/mine/patch_warmup.py`; backups `*_backup_pre_warmup.cs`.
