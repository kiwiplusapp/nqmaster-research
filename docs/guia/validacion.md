# Validación, auditorías, revisiones de código y descartes

> Parte de `NQMASTER_GUIA.md` partida por tema el 2026-10-26. Texto sin cambios, secciones en el orden original. Índice: `docs/guia/INDICE.md`.

## ★★★★★★★★★★★★★★★★ 2026-10-21: ronda 4 — promediar entradas, literatura clásica, resultados de mega-caps, ORB con delta (elegir 2019-22, comparar 2023-26)

Pedidos: "¿promediar la entrada sirve?", "buscá estrategias que no hayas probado, verificá en 2019-2023 y compará en 2023-2026", "el ORB de Fabio Valentini con delta de volumen, ¿sirve o ya está?", "creá estrategias con patrones, volumen, delta, heatmap". Protocolo igual que antes (más el control 2010-18 normalizado por costos, +4 ticks, meseta, portafolio con filtro de conflictos). **Resultado: 0 cambios al edge en 4 líneas (~17.000 celdas).** Lucid Pro 50K del 20-oct: ver `RUNBOOK_OPERACION.md` (preset `LucidPro50K`).

| Línea | Celdas | Resultado | Informe |
|---|---|---|---|
| Promediar entradas (mitad a mejor precio, agregar a favor, piramidar, todo límite, segunda mitad N min después; 23 módulos) | 338 | **0**. A mejor precio: WR +1-3 pts pero la 2ª mitad se llena más en los perdedores, $ −10..−47%; piramidar con stop a la entrada: WR −16..−39 pts; todo límite: pierde 26-62% de las señales (selección adversa). P(mejora 2023-26 \| mejoró 2019-22) 24% = azar. Para 1 contrato ni aplica | `avg_entry_report.md` |
| Literatura clásica: Williams (Oops, Smash, inside/outside), Raschke/Connors (Turtle Soup+1, 80-20, Pinball, Holy Grail, Anti, Double 7, %b, R3), Crabel (NR/stretch), Taylor, tipos de apertura de Steidlmayer | 3.105 | **0**. 12 familias mediana PF 0,6-1,1. Open-drive con tendencia es real (PF 1,8/1,9/1,3/1,2) pero corr 0,3 con MOM1030/ORB60/VOLB: no suma Sharpe. Smash Day: Sharpe +0,05 pero peor mes +13%; con tendencia PF 2-4 y 8 trades/año → vigilancia | `b11_report.md` |
| Resultados de mega-caps (9 tickers, fechas de 8-K de la SEC 2009-26) y rebalanceos del Nasdaq-100 | 1.218 | **0**. El gap del día siguiente se revirtió en 2010-22 (fade PF 1,47) y continúa en 2023-26 (follow 1,53): régimen, no regla. El default ya rinde más esos días (PF 1,75/1,45 vs 1,54/1,44); saltar o doblar empeora. Post-hoc: ORB60 ×2 el día después (+$75/mes) → revisión de enero | `earn_lab_report.md` |
| ORB + delta (delta real de ticks 2025-05→2026-10: 9.792 celdas; proxy de barra 2010-26, corr 0,6 con el delta real: 2.208) + absorción, divergencia, flip en VWAP, clímax | 12.000 | **0**. El delta en el minuto de ruptura no hace nada; el delta de sesión a favor sube el PF pero recorta 50-70% de los trades y los ORB base pierden; 1 sobreviviente real (ORB15 + delta 15 min) con DD +20% en el portafolio y sin historia antes de 2025; los 4 sobrevivientes del proxy son ORB60 con tendencia (= ORB60 de la casa) y bajan el Sharpe. FabioOrb (FundedSync) PF 1,14 en 2026 es coherente con un ORB de todos los días + delta (PF 1,1-1,4) vs ORB60 en días de pullback (1,9-2,4). Heatmap: necesita profundidad del libro, no disponible | `delta_report.md` |

### Robustez operativa (mismo día)
- Barras faltantes: los módulos de reloj exigen la barra exacta del minuto (igual que la investigación); pasa en 0,4-1,2% de las sesiones nocturnas; no se cambia (cambiarlo rompe la paridad).
- Runbook: sección "qué pasa si se cae la PC" (stops/targets viven en el broker; salidas por tiempo y cierre 15:55 no; recuperación al reiniciar).

### Conclusión
Cuatro rondas en tres días (~190.000 celdas) con el mismo resultado: el edge por trade está en su techo y las ideas populares (promediar, delta, patrones clásicos, noticias, eventos) o ya están dentro del sistema, o no tienen edge en NQ intradía, o cambian de signo entre regímenes. Lo que queda por medir es la ejecución en vivo (slippage real), que ningún backtest puede dar.

## ★★★★★★★★★★★★★★★ 2026-10-19 (noche): bucle "mejorar todo sin excepciones" — 7 líneas de investigación, 0 cambios al edge, 1 hallazgo operativo

Pedido: "menor drawdown, más trades, mejor win rate, PF igual o mayor, robusto, sin overfitting; buscá, implementá, testeá y repetí". Se corrieron 7 líneas en paralelo con protocolo preregistrado (elegir en 2020-23, confirmar en 2024-26 y en 2010-19 normalizado por costos, +4 ticks, meseta, portafolio con filtro de conflictos). Resultado honesto: **ninguna cambia el edge**; el sistema está en su techo por trade. Lo que sí salió es un hallazgo operativo (el reloj) y un nivel honesto de planificación.

| Línea | Qué se probó | Resultado | Informe |
|---|---|---|---|
| Drawdown | 40 reglas de riesgo: stops más cortos por ATR, saltear riesgo alto, tope de riesgo abierto, stop diario en ATR, tope por dirección, corte de sesión, stops semanal/mensual | **0/40**. Cada punto de DD cuesta un punto de ganancia (corr 0,63/0,77). Ninguna baja los quiebres de MFFU sin bajar el ingreso | `research/mine/ddlab_report.md` |
| Más trades | 13 segundas instancias en otras horas, re-armado tras stop en 9 módulos, OR 5/10 min, Camarilla L2/H2/L4/H4, familia nueva de bandas de VWAP (528 celdas, sin lookahead) | **0 aceptados**. Las segundas instancias son los mismos trades (hasta 94% de solapamiento) o ruido; tasa base del archivo (54.558 celdas): P(pasa 2024-26 \| pasa 2020-23) 21%, con 2010-19 6,6% | `more_trades_report.md` |
| Bitcoin (MBT) | Binance 1m 2017-26 → `data/btc_1m.npz`; 65.544 configs + mapa horario 6.768 celdas | **0**. Costo = 1,5% del ATR en 2024-26 y 4% en 2020-23 (NQ 0,42%); sin costos hay patrones, con costos PF 1,01/1,16. Lucid no lista MBT; MFFU lo cuenta como mini | `btc_report.md` |
| Oro 16 años reales | 65.544 configs en `mgcdb.npz` con todas las familias (varias nunca probadas en oro) | **0**. 146 → 31 → 6 → 1 en meseta (INSIDE_DAY, $25/mes). Los módulos actuales de GoldMaster tampoco pasarían el protocolo: el oro es diversificador, no edge | `gold16_report.md` |
| Fades de noticias | 13 listas de fechas 2009-26 validadas por el pico del minuto de publicación; grilla CPI09 + celda CPI09 trasplantada a PPI, ventas, PIB, PCE, pedidos, minutas, bienes duraderos | **0**. Solo el CPI tiene la reversión en la apertura (pico 5,2× vs 2,4-4,2×); los demás rinden como un día cualquiera (PF ~0,8). Los datos de las 10:00 no mueven el NQ | `news_fade_report.md` |
| Perturbación de parámetros | 7.762 celdas: cada módulo ±20% / ±30 min (uno a uno, factorial, 200 sorteos conjuntos), 200 sorteos de todo el sistema a la vez, +1/+2/+4 ticks | **Nada que cambiar** (recentrar, suavizar o apagar módulos no pasa). Hallazgos: (1) lo frágil son las **horas** (15 min de desfase: Sharpe −0,3 a −0,7 por módulo), no stops ni targets; (2) con todo ±20% el sistema rinde Sharpe ~2,5 / PF 1,3 / DD $5,6k por contrato = nivel honesto; (3) ranking de fragilidad: MOM1030, MOM13, REV06, MOM11, ON07, VW13, SO04, CRT11; robustos: ORFAIL, NF05, MSEQS, VOLB, ORB60 | `perturb_report.md` |
| Cimientos globales | 34 alternativas: filtro de tendencia (SMA 10-50, EMA, momentum N días, SMA20&50, sin filtro), ventana de ATR 7-30 y rango RTH vs sesión completa, MinATR 100-250, umbral de pullback 0,30-0,60 y sin filtro, cierre 15:45-16:14 | **Nada que cambiar**. El filtro de tendencia vale 0,95/1,12 de Sharpe (sin él PF −0,22, DD +68%); el filtro de pullback vale 0,4-0,7; el ATR de rango RTH es correcto (sesión completa −0,55/−0,81). SMA20 y ATR14 son óptimos locales "robustos a un paso" (los vecinos pierden 0,1-0,2 de Sharpe pero mantienen PF ≥ 1,44); pullback 0,44 y cierre 15:55 están en meseta | `foundations_report.md` |

### Qué cambió en la operación (runbook)
- **Chequeo del reloj de barras** después de cada cambio de horario de verano (EE. UU. y Argentina): los módulos de reloj deben entrar a su hora ET exacta. NQMaster convierte la zona de NinjaTrader a ET; si esa zona está mal, todo entra corrido y el edge desaparece.
- **Variante defensiva** si el monitor avisa: `DisableModules = MOM1030,MOM13,REV06` (2024-26 Sharpe 4,03 vs 4,07, PF 1,52, −12% de ganancia, DD más bajo en 2020-23).
- **Planificar con el nivel honesto** (Sharpe ~2,5, PF ~1,3, DD ~$5.600 por contrato), no con la celda exacta.
- **Lista de vigilancia de enero**: REV06, LATE15, CAM3, LF0430, MSEQ, MOM1030, ON07, CRT11, VW13, ICT.

### Qué significa para el objetivo "menos DD, más trades, más WR, PF igual o mayor"
Con un mismo conjunto de señales esas cuatro cosas no se mueven juntas: subir el WR baja el PF (RR negativo, 19-oct), bajar el DD baja la ganancia 1:1 (ddlab), y más trades de las mismas familias son los mismos trades. Lo único que las mueve juntas es un edge **nuevo y no correlacionado**, y hoy se agotaron los candidatos baratos (bitcoin, oro, noticias, bandas de VWAP, segundas instancias). Lo que queda son ingredientes caros o lentos: order flow en vivo con meses de grabación propia, otro mercado con costo bajo (ninguno de los micros lo tiene), o esperar a que la revisión de enero confirme qué módulos sobreviven.

## ★★★★★★★★★★★ 2026-10-16: auditoría completa (en español)

Informe: `Conocimiento/Auditoria 16-oct-2026.md`. Plan de ingresos (17-oct): `Conocimiento/Plan 250-300 por dia (17-oct).md`, informe https://claude.ai/artifact/NveGr9pnXUb7GpdQYfmjPb. Operación diaria: `RUNBOOK_OPERACION.md` (manda sobre esta guía si se contradicen).

Cambios en `NQMaster.cs` (stub OK, **falta F5**). Backups: `NQMaster_backup_pre_ops16.cs` y `NQMaster_backup_pre_review16.cs`.

- **Monitor de borde recalibrado** para los ×4 de MOM1030/CPI09. Con los valores viejos daba una falsa alarma el 2024-03-18.

  | Perfil | k | h | aviso |
  |---|---|---|---|
  | Ultra | 0,085 | 24,44 | 9,12 |
  | UltraQ | 0,0773 | 26,08 | 9,04 |
  | WR70Plus | 0,0634 | 12,07 | 6,86 |
  | Durable | 0,0455 | 10,35 | 6,98 |

  - El nuevo nivel de **aviso** solo alerta.
  - El estado del monitor se guarda en `nqmaster_edge_<cuenta>.txt` y sobrevive reinicios.
- **Preset Mffu50K, fondeada: sin escalón por defecto.** Pide el retiro al llegar a $4.600 de ganancia y deja $4.100.
  - El escalón a 2 contratos (`FundedStepUpCushion` 4000, retiro a $6.600) es opcional: más ingreso mediano si el edge es real, pero duplica el tamaño y suma 6-7 puntos a P(año negativo) con 35% menos edge. Ver revisión adversarial.
  - El panel ahora dice hasta cuánto retirar.
- **Grupo 10, nuevas propiedades:**
  - `InactivityAlarm`: avisa si un módulo no opera más de 1,5× su máximo histórico, o si pasan 12 días sin shorts o sin longs.
  - `CrossAccountGuard` y `HedgeGroup`: no abren NQ opuesto a otra cuenta de la misma PC (prohibición de hedging en Lucid y MFFU).
- **Arreglos de la revisión de código** (`research/mine/audit_code_2026-10-16.md`):
  - F1: el risk cap mide MOM1030/CPI09 por lote.
  - F2: el objetivo de evaluación ya no corta las fondeadas.
  - F3: estado del monitor persistido.
  - F5: el ×8 de evaluación es el total de lotes.
  - F6: aviso cuando la tabla de fallback se queda sin años.
  - F8: el informe de salud no llama a Log al terminar.
  - F9: los días de roll o pausa no cuentan en el monitor.
- **Log de tamaño en cada entrada:** muestra base → pedido → enviado.

Herramientas:

- `research/mine/parity_check.py`: compuerta de paridad con NinjaTrader; correr antes de cada cambio de código.
- `research/mine/impl_gap.py`: brecha de implementación en vivo.
- `tools/check_guards.py`: guardas de importación.
- `tools/nt8_stub/check.sh`: verificación de sintaxis.

Descartado: risk parity/HRP, apagar ICT/ON07 y apagar módulos redundantes (`Conocimiento/Descartado/Auditoria 16-oct ...`). REV06 queda en vigilancia: apagarlo mejora 3 de 4 períodos, pero toca la regla de confluencia y esa interacción no está probada.

## ★★★★★★★★★★ 2026-10-15 (night): the operating system, as one design (English)

Playbook page: `research/mine/os_playbook.html` (published as the "NQMaster Operating System" artifact). Research: `research/mine/os_adapt.py` -> `os_adapt.json`. Patches: `patch_fallback.py`, plus a fix to the Mffu50K preset (below).

**Six layers.**
1. **Edge.** Profile Ultra.
2. **Size.** 1 base contract, MOM1030/CPI09 ×4, ×8 in 50K evals.
3. **Account.** Presets.
4. **Protection.** FOMC, ATR, risk cap, guards.
5. **Adaptation.** Edge monitor → fallback.
6. **Feedback.** Health report, panel, log.

**New: what the edge monitor does on an alarm (`os_adapt.py`).**
- Test period: 2013-19 cost-normalised. It is out of sample for the monitor's calibration, which used 2020-26 and never fires there. Ultra's edge was weak in those years.

| On alarm | Sharpe 2013-19 | Max DD | Losing years 2011-19 | 2020-23 real |
|---|---|---|---|---|
| Alert only (old default) | 0.88 | $1,519 | 3 | $78,579 |
| Pause 63 / 126 / 252 days | 0.73 / 0.69 / 0.86 | $1,526-2,101 | 4 | $78,579 |
| **Review-set fallback 252 days, yearly table (shipped)** | **1.05** | **$1,338** | **2** | $78,579 |
| Review-set fallback, exact alarm date | 1.15 | $1,249 | 1 | $78,579 |
| Yearly review always on (no monitor) | 1.52 | $709 | 1 | $60,870 |

- **Pausing on an alarm is worse than doing nothing.** Keep `EdgeMonitorPause = false`.
- The fallback switches off the modules that failed the 5-year review (cost-normalised PF ≤ 1.05) for 252 monitored trading days, then resets the CUSUM and returns to the full profile.
- Yearly table built into the code:

  | Year | Modules off |
  |---|---|
  | 2020 | LF0430 LF06 MOM11 MOM13 ON07 ORB60 ORB90 REV06 VW13 |
  | 2021 | LF0430 LF06 MOM11 MOM13 ON07 VW13 |
  | 2022 | LF0430 LF06 ON07 VW13 |
  | 2023 | LF06 ON07 |
  | 2024 | LF06 VW13 |
  | 2025-26 | none |
  | 2027 | REV06 |

- The always-on yearly review would have cost $17.7k in 2020-23 because it keeps recovering modules off. **So REV06 stays on in 2027 unless the monitor fires.** This replaces the earlier "REV06 off for 2027" advice.
- Evidence size: 9 alarms in 9 years. The gain held for every length tested (126 / 252 / 378 days: Sharpe 0.97 / 1.05 / 1.07 vs 0.88).
- New properties in group 06: `EdgeAlarmFallback` (true), `EdgeFallbackDays` (252), `EdgeFallbackOff` (empty = built-in table). The panel shows "FALLBACK n days left". Backup: `NQMaster_backup_pre_fallback.cs`.

**Fix: Mffu50K preset, funded.**
- It withdrew only above $6,600 profit, a value meant for the 2-contract step-up, while step-up is off by default.
- Now it requests the payout at $4,600 (keeps $4,100) when step-up is off, and at $6,600 when it is on.
- Tested at 1 contract (`smallacct_cushion.py`): keeping $4k gives $1,029 / $1,538 a month vs $836-976 / $1,323-1,478 when keeping $5-7k.
- The preset now also turns on the news blackout in the funded account (MFFU rule: flat ±2 min around Tier-1 news).

**Settings, the whole system.**
- MFFU 50K eval: Ultra, Contracts 1, PropMode Eval, PropPreset Mffu50K.
- MFFU 50K funded: the same with PropMode Funded.
- Lucid Pro 25K, fastest: PropPreset LucidPro25K; new eval the day after a bust.
- GoldMaster Robust on MGC alongside.
- Defaults for everything else: Days to load ≥ 45, edge monitor on, fallback on.

Stub compile OK, NOT compiled in NinjaTrader: F5.

## ★★★★★★★ 2026-10-14 (later): 16-year robustness table + yearly module review (English)

Script: `research/mine/robust16.py` -> `robust16.json`. Years 2013-19 are cost-normalised (cost 0.345% of ATR per trade); 2020-26 are real $ per MNQ, 1 contract.

| Year | Ultra PF / WR | UltraQ PF / WR | Durable PF / WR | Ultra $ | UltraQ $ | Durable $ |
|---|---|---|---|---|---|---|
| 2013 | 0.89 / 59 | 0.95 / 63 | 0.99 / 56 | | | |
| 2014 | 1.15 / 63 | 1.19 / 66 | 1.54 / 62 | | | |
| 2015 | 0.95 / 59 | 0.99 / 62 | 1.03 / 55 | | | |
| 2016 | 1.25 / 64 | 1.28 / 67 | 1.29 / 58 | | | |
| 2017 | 1.18 / 62 | 1.14 / 64 | 1.26 / 59 | | | |
| 2018 | 1.21 / 63 | 1.23 / 66 | 1.46 / 61 | | | |
| 2019 | 1.10 / 60 | 1.08 / 64 | 1.34 / 62 | | | |
| 2020 | 1.41 / 67 | 1.41 / 69 | 1.46 / 60 | 15,551 | 13,632 | 8,099 |
| 2021 | 1.42 / 66 | 1.52 / 71 | 1.49 / 63 | 13,933 | 14,110 | 7,432 |
| 2022 | 1.72 / 70 | 1.77 / 73 | 1.94 / 68 | 37,400 | 32,670 | 21,219 |
| 2023 | 1.27 / 64 | 1.29 / 67 | 1.41 / 64 | 11,693 | 10,552 | 6,923 |
| 2024 | 1.40 / 64 | 1.40 / 67 | 1.52 / 62 | 19,190 | 16,740 | 11,148 |
| 2025 | 1.51 / 68 | 1.52 / 70 | 1.68 / 62 | 27,731 | 24,145 | 16,679 |
| 2026 to Oct 8 | 1.61 / 66 | 1.68 / 68 | 2.12 / 62 | 30,569 | 28,514 | 20,906 |

- Durable's six modules were chosen with 2010-26 in view, so its old years are not out of sample.
- 2013 and 2015 were losing years for Ultra and UltraQ: the edge is mostly a post-2020 regime.

**Yearly module review (new rule, tested walk-forward):**
- Each January, switch off any module whose last-5-year cost-normalised PF is ≤ 1.05.
- The rule uses only past data. From 2013 to 2026 it gave 13 of 14 positive years, and in 2013-19 it switched off the modules that later failed.
- In 2020-21 it switched the newly working modules back on late, which cost about $18k versus Ultra in 2020-23. In 2024-26 it was equal to Ultra.
- **Decision for January 2027: switch REV06 off** (UseRev06 = false). REV06's PF is 1.01 on 2024-26 research and 1.03 in the NinjaTrader run.
- Re-run `python robust16.py` every January for the next year's list.

## Error corregido en la investigación de ICT
La simulación cancelaba la orden límite si en la misma barra el precio también superaba el extremo del barrido. En la realidad se llena y pierde. Con la corrección (`research/ict_fix.py`), ICT da PF 1,23 / 1,39 / 1,37 en lugar de 1,53 / 1,56 / 1,53. El 1,23 coincide exacto con la validación en NinjaTrader. En el total de Ultra el efecto es chico: PF −0,01 y Sharpe −0,03 a −0,06. NQMaster no cambia: en NinjaTrader los llenados ya son reales.

## Errores de la investigación corregidos (2026-10-06 noche)
- **El constructor de datos se re-ejecutaba al importarlo.** Cada script que usaba `dense_build.py` o `ict_redo.py` reconstruía los datos base y borraba lo agregado después: ICT corregido, WR70Plus, Core, ENG10 y LATEFH. Los dos ahora solo construyen al ejecutarlos directamente. Todo se reconstruyó en orden y se verificó: 76 módulos, ninguno faltante.
- **Faltaban los datos de cuenta de ENG10 y LATEFH.** Las simulaciones de cuenta los omitían sin aviso. Ahora están (`dense_extra.py`). Si falta un módulo, `acct_policy.sums` avisa.
- Con los datos completos se recalcularon la grilla de perfiles, la verificación final y la velocidad de evaluación. El perfil de evaluación no cambia. En la fondeada, el oro Robust pasa a ser mejor que WinRate.

## Arreglos de código (2026-10-06 noche)
**NQMaster:**
- Una señal que choca con una orden opuesta pendiente ya no se pierde: ORB, ICT y ENG10 reintentan cuando se cancela la otra orden. ENG10 no persigue el precio más de 0,5R.
- En vivo, si el precio ya pasó el nivel de una orden stop, entra a mercado en vez de mandar una orden que el broker rechazaría. Un rechazo ya no apaga la estrategia, y si se rechaza un stop de protección, cierra la posición.
- El objetivo de la evaluación se mide con la ganancia abierta incluida. Si al cerrar no se cumple, la estrategia sigue operando.
- LATE15 y LATEFH miden el movimiento desde el cierre de la primera barra de la sesión regular, como la investigación.
- El pico de la cuenta, el inicio del día y el mejor día se guardan en un archivo y se recuperan si NinjaTrader se reinicia.
- Si se activa a mitad del día, descuenta lo que la cuenta ya ganó o perdió ese día.
- Los llenados parciales se cuentan una sola vez y el objetivo se recalcula con el precio promedio.
- Cierre del día a las 15:56.

**GoldMaster:**
- Solo una posición opuesta abierta bloquea una entrada, como en la investigación. Antes también la bloqueaba una orden pendiente, y eso costaba 4-5% de la ganancia.
- Las órdenes stop bloqueadas quedan en espera y se vuelven a poner cuando se libera el lado contrario.
- ASIA respeta "la primera ruptura decide" aunque no estuviera armada a tiempo. Si una barra rompe los dos lados, no opera.
- El stop diario de la cuenta funciona desde la primera sesión en vivo.
- Antes de operar espera tener 60 días de sesión regular cargados.
- Mismas protecciones en vivo que NQMaster: entrada a mercado si el precio ya pasó el nivel, rechazos sin apagar la estrategia, objetivo con ganancia abierta y llenados parciales.
- ENG0610 viene apagado por defecto.

Backups: `NQMaster_backup_pre_fixes.cs`, `NQMaster_backup_pre_evalcushion.cs`, `GoldMaster_backup_pre_fixes.cs`, `GoldMaster_backup_pre_evalmode.cs`.

## Segunda revisión de código (2026-10-07)
**NQMaster:**
- **El reintento de ENG10 ahora sí se ejecuta.** Antes quedaba bloqueado y ENG10 perdía el trade cuando chocaba con otra orden.
- **Órdenes en espera:** si una orden stop o límite (ORB, ENG10, ICT, LON) se cancela por un trade opuesto, queda en espera. Se vuelve a poner cuando no hay posición ni orden contraria. Se descarta si el precio pasa por su nivel mientras espera o si termina su horario, igual que en la investigación. Mientras espera, ese módulo no toma señales nuevas.
- **Mejor día:** si NinjaTrader se cerró antes de las 18:00, el resultado de ese día se recupera al volver a abrir. La regla de consistencia ya no se calcula corta.
- **PropPeakOverride** vuelve a reemplazar el pico guardado (para corregir un archivo viejo).
- **VOLB en vivo:** si el precio está justo en el nivel, entra a mercado en vez de descartar el trade.
- **Objetivo de la evaluación:** solo se desactiva si toda la cuenta está sin posiciones. El resultado abierto de GoldMaster ya no lo prende y apaga.
- **Stops rechazados:** un stop o objetivo rechazado cierra solo su módulo.
- **VOLB tendencia (WR70Plus):** controla su invalidación también mientras espera.
- **Referencias de órdenes:** un aviso tardío de una orden vieja ya no pisa la nueva.

**GoldMaster:**
- Actualiza sus órdenes al pasar a vivo.
- El inicio del día en vivo no cuenta la ganancia abierta del momento. Usa el inicio del día y el mejor día que guarda NQMaster para esa cuenta. No arrastra stops calculados con trades simulados.
- Las órdenes se registran al enviarlas. Una orden en espera se vuelve a poner solo cuando la anterior terminó.
- Solo pone en espera órdenes stop.
- El objetivo de la evaluación se desactiva solo con la cuenta sin posiciones.
- El monitor de ventaja divide por el tamaño realmente operado ese día.

Backups: `NQMaster_backup_pre_review2.cs`, `GoldMaster_backup_pre_review2.cs`. Parche: `research/mine/patch_review2.py`.

## Tercera revisión de código (2026-10-07)
- **Orden en espera que vuelve antes de tiempo:** una orden puesta en espera ya no vuelve antes de que entre el módulo que la desplazó. Antes podía hacer perder la entrada de MOM11, MOM1130 o LATEFH cuando iban contra la tendencia.
- **Setups con una posición opuesta abierta:** si al colocarse un ORB, ENG10, LON o ICT hay una posición opuesta abierta, el setup queda en espera en vez de perderse. Se pone cuando se cierra esa posición, salvo que el precio haya pasado por su nivel mientras tanto. Es lo que hace la investigación.
- **PropPeakOverride:** se aplica una sola vez; el archivo lo recuerda en un 5° campo. En reinicios posteriores se usa el pico más alto guardado.
- **Mejor día:** se recupera solo de la sesión inmediatamente anterior. Si el archivo es anterior a `EvalStartDate`, se ignoran su inicio de día y su mejor día; GoldMaster hace lo mismo. **Al empezar una evaluación nueva, poné `EvalStartDate` = fecha de inicio** en las dos estrategias.
- **Detalles:**
  - ORB no se rearma mientras su orden está en espera.
  - Las órdenes quedan registradas al enviarlas.
  - Si el precio toca el nivel mientras se cancela la orden, queda anotado y la orden se descarta.

Backups: `NQMaster_backup_pre_review3.cs`, `GoldMaster_backup_pre_review3.cs`. Parche: `research/mine/patch_review3.py`.

## Cuarta revisión de código (2026-10-07)
- **Dos entradas a mercado opuestas en la misma barra** (por ejemplo REV06 y LF06 a las 06:00, o MOM11 y MSEQ a las 11:00): gana la primera, como en la investigación. Antes la segunda cancelaba a la primera, y el backtest y el vivo se comportaban distinto. Las entradas a mercado ahora quedan registradas al enviarlas.
- **MSEQ y MSEQS:** si los frena una orden stop o límite contraria, reintentan en la barra de 1 minuto siguiente en vez de perder el trade.
- **ORB** espera a que entre el módulo diferido.
- **Archivo de estado:**
  - Una evaluación nueva no hereda el pico de un archivo anterior a `EvalStartDate`. GoldMaster hace lo mismo.
  - `PropPeakOverride` se aplica también sobre archivos viejos.

Backups: `NQMaster_backup_pre_review4.cs`, `GoldMaster_backup_pre_review4.cs`. Parche: `research/mine/patch_review4.py`.

## Quinta revisión de código (2026-10-07)
No encontró problemas graves. Ajustes de tiempo aplicados:
- ORB solo espera a un módulo diferido si ese módulo va en contra de ORB.
- La espera dura 1 barra en la serie de 1 minuto, 2 para MSEQ y MSEQS, y 5 para ICT, y nunca se acorta.
- El reintento de MSEQ o MSEQS se descarta si en la barra el precio tocó su stop.

**PropPeakOverride:** dejalo en **0**, salvo que quieras corregir a propósito el pico guardado. Si queda puesto, se aplica una vez sobre archivos de versiones anteriores y puede bajar un pico real más alto.

Backup: `NQMaster_backup_pre_review5.cs`. Parche: `research/mine/patch_review5.py`.

## Órdenes trabadas: 0 cortos desde agosto 2025 (corregido 2026-10-07)
**Qué pasó.** En Strategy Analyzer (Ultra, MNQ, del 01/01/2024 al 06/10/2026) el último corto fue el 12/08/2025. Después hubo 0 cortos en 14 meses y VOLB no volvió a operar.
- **La causa.** El 13/08/2025 a las 09:32 ET, VOLB puso una compra stop en 25.492. NinjaTrader nunca la procesó: el precio pasó ese nivel el 15/09/2025 sin llenarla, y cancelarla no tuvo efecto.
- **Por qué bloqueaba los cortos.** La estrategia la seguía viendo como orden activa. Cada corto encontraba "una orden de compra activa en contra", la mandaba a cancelar y se postergaba para siempre.
- **El mismo riesgo en vivo.** Puede pasar operando en vivo con cualquier módulo. Además, al pasar de histórico a tiempo real, NinjaTrader puede mandar esa orden vieja al mercado.

**El arreglo (NQMaster y GoldMaster).** Un vigilante revisa, en cada barra de 1 minuto, las órdenes de entrada de cada módulo y descarta una orden si:
- sigue sin ser aceptada (Initialized o Submitted) 2 barras después;
- es una entrada a mercado que no se llenó en 2 barras;
- se pidió cancelarla hace 2 barras o más y la cancelación no se confirmó.

Todas las entradas se cancelan a las 15:56, así que una orden trabada se libera ese mismo día como máximo.

Cuando el vigilante descarta una orden, intenta cancelarla, el módulo y la dirección contraria vuelven a operar, y en Output aparece una línea `STALE ORDER dropped (...)`. Al terminar la prueba sale el total, que también se ve en el panel.

Al pasar a tiempo real, toda entrada que siga Initialized se cancela y no se convierte. En histórico, las órdenes sanas se procesan en el momento, y en vivo en segundos, así que el vigilante no toca órdenes válidas.

**Cuánto costó el error** (`research/mine/shorts_bug_eval.py`, mismo CSV comparado con la investigación):

| Período | Lado | Trades | Cortos | WR | PF | $/mes (1 contrato base) | Lucid 50K, 2 contratos: aprueba | Mediana de días |
|---|---|---|---|---|---|---|---|---|
| 02/2024 a 07/2025 | NinjaTrader | 2.222 | 802 | 62,2% | 1,33 | 2.271 | 62,8% | 13 |
| 02/2024 a 07/2025 | Investigación | 2.165 | 786 | 62,4% | 1,34 | 2.342 | 61,8% | 13 |
| 13/08/2025 a 09/2026 | NinjaTrader | 908 | **0** | 65,7% | 1,33 | **1.180** | **36,0%** | 15 |
| 13/08/2025 a 09/2026 | Investigación | 1.406 | 577 | 65,9% | 1,47 | **3.104** | **57,4%** | **9** |

- Antes del bloqueo, NinjaTrader y la investigación coinciden.
- Durante el bloqueo se perdieron 577 cortos (WR 65,7%, PF 1,53, +$17,6k por contrato) y 109 largos de VOLB (+$3,7k).
- En los trades que sí coinciden, NinjaTrader y la investigación dan casi lo mismo ($44,3k vs $45,0k), así que el resto del port está bien.
- La simulación de evaluaciones es diaria (sin drawdown intradía) y sirve para comparar.

**Qué hacer.**
1. Compilá con F5.
2. Repetí la prueba en Strategy Analyzer del 01/01/2024 a hoy, con Contracts 1 y PropMode Off.
3. Exportá los trades y corré `python nt_compare.py "<csv>" --set ultra`. Deberían volver los cortos de VOLB, MOM11, CRT11, LON, etc. desde agosto 2025.
4. Si en Output aparece alguna línea `STALE ORDER`, mandámela: dice qué orden era, de qué módulo, a qué precio y en qué estado quedó.

Backups: `NQMaster_backup_pre_zombie.cs`, `GoldMaster_backup_pre_zombie.cs`.

## Validar NinjaTrader contra la investigación (`research/mine/nt_compare.py`)
1. En Strategy Analyzer, corré NQMaster Ultra en MNQ de 1 minuto del 01/02/2024 a hoy, con **Contracts 1**, PropMode Off y comisión $1,90. Cargá al menos 120 días antes.
2. En la pestaña Trades, hacé clic derecho, elegí **Export** y guardá el CSV.
3. En `research/mine`, corré:
   `python nt_compare.py "ruta\al\archivo.csv" --set ultra`
4. Para GoldMaster Robust en MGC, usá `--set gold_robust`.

El informe muestra, módulo por módulo, los trades de la investigación y de NinjaTrader, cuántos coinciden en día, dirección y minuto de entrada (±3 min), y el win rate, PF y $ por contrato de cada lado. Los trades sin pareja quedan en `nt_compare_<set>_mismatch.csv`.

**Prueba con la exportación vieja de MaxPlus (septiembre):** en los trades que coinciden, investigación $34.315 y NinjaTrader $33.452 (−2,5%). LON coincide 194 de 194, con el mismo resultado. Las diferencias de cantidad vienen de módulos que esa versión no tenía.

## Probado el 2026-10-07 y descartado
- **Filtrar un lado (solo largos o solo cortos) por módulo:** elegido con 2020-23, se equivoca en 3 de 5 casos fuera de muestra.
- **Más módulos de oro (LATE1430, DRIVE11, ASIA05):** ±$10 por mes, ruido.
- **3 contratos en la fondeada con colchón grande:** +$5 en el mejor caso, ruido.

**Año por año** (Ultra ampliado + oro WinRate, 1 contrato, trading libre): todos los años ganan.
- PF de 1,26 a 1,66, win rate de 62% a 68% y 64-100% de meses positivos (2020-2026).
- En futuros reales: 2024 +$18.095, 2025 +$32.805, 2026 (hasta septiembre) +$34.972.
