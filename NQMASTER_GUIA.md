# NQ MASTER: todo el portafolio en una sola estrategia

`NQMaster.cs` está compilada e instalada. En NinjaTrader abre el NinjaScript Editor y pulsa **F5**. Reemplaza las 11 instancias anteriores.

## Cómo usarla

| Gráfico | Estrategia | Profile | Configuración |
|---|---|---|---|
| **MNQ 1 minuto** (ETH) | NQMaster | **MaxSharpe** o **WinRate70** | Contracts 1, Skip FOMC sí |
| **MGC 1 minuto** (ETH) | NQMaster | **Gold** | Contracts 1 (solo con MaxSharpe) |

- La estrategia agrega sola la serie de 5 minutos que usan MSEQ e ICT.
- **Cuenta de prop firm:** pon Eval target (por ejemplo 3000) y Max drawdown (por ejemplo 2000) en la instancia de **MNQ**. Solo actúan en tiempo real.
- **Pausa manual:** sigue funcionando con `pause_trading.txt`.
- **Una diferencia con las instancias separadas:** una sola estrategia no puede estar comprada y vendida a la vez en MNQ. Si un módulo quiere entrar en contra de otra posición abierta, se salta ese trade. Pasa en ~1% de los trades y el resultado no cambia (incluso mejora un poco).

## Resultados (futuros reales MNQ/MGC, 1 contrato por módulo, sin días FOMC, reglas de la estrategia única)

| Perfil | Período | Trades/día | Win rate | PF | Neto | Max DD |
|---|---|---|---|---|---|---|
| **MaxSharpe + Gold** | 2024–26 | 4.15 | 64.4% | 1.35 | +$39,595 | $2,398 |
| | 2026 | 3.66 | 66.0% | **1.45** | **+$16,742** | $1,389 |
| | Último mes (21 sesiones) | 3.81 (**80 trades**) | 66.2% | 1.32 | +$1,267 | $248 |
| **WinRate70** (solo NQ) | 2024–26 | 2.85 | **70.9%** | 1.42 | +$28,111 | $2,005 |
| | 2026 | 2.53 | **70.7%** | 1.38 | +$7,971 | $1,948 |
| | Último mes | 2.52 (**53 trades**) | **71.7%** | 1.32 | +$642 | $181 |

Validación del perfil WinRate70 en 2020–23 (CFD): 70.0% de win rate, PF 1.37. En 2024–26 (CFD): 69.7%, PF 1.36.

Win rate por mes de WinRate70 en 2026: 65, 81, 66, 82, 74, 73, 70, **55 (agosto)**, 78%.

## ¿Qué perfil elegir?
- **Más dinero:** MaxSharpe + oro, con dos gráficos. En 2026 ganó el doble que WinRate70.
- **Más aciertos y simplicidad:** WinRate70, con un gráfico. Acierta ~71%, opera menos y gana menos.

## Origen de los datos (nada inventado)
- **Futuros reales:** tus exportaciones de NinjaTrader MNQ y MGC en 1 minuto, 2024-01 → 2026-09 (`Documents\NinjaTrader 8\export_*.csv`).
- **Historia larga:** NQ CFD Dukascopy 2020–2026 y oro XAUUSD de histdata.com 2020–2026.
- **Costos:** 1 tick de slippage en entradas a mercado/stop y en stops, $1 de comisión round turn por contrato.
- **Fechas FOMC:** federalreserve.gov. **CPI:** archivo de BLS.
- **Único supuesto:** los costos de Topstep en la simulación del negocio ($49/mes y $149 de activación).
- Todo son backtests. El paso siguiente es correr NQMaster en el Strategy Analyzer, para confirmar que NinjaTrader reproduce estos números.

## Perfil MaxTrades (nuevo)
Es MaxSharpe (solo NQ) más MOM1130 y RSI2. Usalo en un gráfico MNQ de 1 minuto.
En MNQ real 2024-26: 5.2 trades por día, WR 70.0%, PF 1.27, neto $32,497. MaxSharpe en el mismo período: 3.7 trades por día, WR 66.9%, PF 1.35, $32,012.
Da más trades y más winrate con el mismo dinero. Para ganar más hay que subir los contratos (AdaptiveSize o más cuentas).

## Perfil MaxPlus (nuevo, recomendado sobre MaxSharpe)
MaxSharpe + ORB90 (días pullback, 0.6R) + MSEQS (MSEQ en corto solo en días en que el ORB60 entró en corto). Usalo en un gráfico MNQ de 1 minuto.
MNQ real 2024-26: 3.9 trades por día, WR 66.8%, PF 1.369, $37,539. MaxSharpe en el mismo período: 3.7 por día, 66.9%, PF 1.351, $32,012.
Mejora trades, PF y $/mes en los tres tramos de datos. El drawdown es algo mayor ($3.4k contra $2.5k en MNQ real).

### MaxPlus: control de riesgo
ICT opera con 2 contratos (IctMultiplier = 2) para que su riesgo sea igual al de los otros módulos. En MNQ real 2024-26: PF 1.376, Sharpe 3.20, $1,259/mes (MaxSharpe: 1.351 / 3.19 / $1,023).
Para evaluaciones Apex usá AdaptiveSize = true, SizeHigh 2, SizeLow 1 y SizeDownDrawdown 600. En MNQ real: 37% de pases con 10% de quemadas a 30 días, y 84% / 15% sin límite de tiempo.

## Apex 25K: configuración recomendada (2026-09-29)
- **Evaluación:** Profile MaxPlus, AdaptiveSize = false, **Contracts = 4**, EvalTarget = 1500, MaxDrawdown = 0. Pasa ~35% de las veces, en ~2 días de mercado cuando pasa; ~7 días y ~2.8 evaluaciones ($50) por cuenta fondeada.
- **Cuenta fondeada:** Profile MaxPlus, AdaptiveSize = false, **Contracts = 1**. Retirar apenas se cumplan las condiciones de pago.

## Reglas de confluencia (UseConfluence = true, activas en MaxPlus y Custom)
- **A:** CRT11, MOM13, MSEQ y MSEQS con entrada después de las 11:00 operan con doble tamaño cuando van contra el trade de MOM11 y a favor de la dirección overnight (ON07/REV06/LON).
- **B:** REV06 no opera si LON ya entró en la misma dirección.
- **Resultado en MNQ real 2024-26 (1 contrato base):** PF 1.376 → 1.397 y $1,259 → $1,368 por mes. En la ventana Output aparecen como "confluence x2" y "REV06 skipped".

## Perfil MaxPlus2 (2026-10-02)
MaxPlus + reglas de confluencia + 12 reglas de contexto + módulo VW13. Interruptores: UseContextRules y UseVw13.
- **Resultado con 1 contrato base:** sube winrate, PF, Sharpe y dinero en todos los tramos, incluido 2026 (fuera de muestra). En MNQ real 2026: WR 68.9→69.2%, PF 1.50→1.58, +30% de dinero. El drawdown es ~30% mayor.
- **Apex 25K:** usar **MaxPlus**, no MaxPlus2.
- **Apex 50K o cuenta propia:** usar **MaxPlus2**. En 50K: Contracts 4 en la evaluación y Contracts 1 en la cuenta fondeada.
- En la ventana Output aparecen como "context x2" y "ON07 skipped".

## Perfil Ultra (recomendado, 2026-10-03)
MaxPlus2 + VOLB (volatility breakout de Larry Williams, robusto 2015-2026). Unos 4.5 trades por día, PF ~1.45-1.6 y Sharpe 3.4-4.2 (2024-26), winrate ~64-66%.
- **Apex 25K:** evaluación con Contracts 4 y fondeada con Contracts 1. Unos $680-750 por mes por cuenta.
- **Apex 50K:** evaluación con Contracts 4 y fondeada con Contracts 1. Unos $1,240-1,440 por mes por cuenta.

## Perfil WR70Plus (2026-10-03)
Winrate ≥ 70% y PF ≥ 1.45 en todos los tramos. MNQ real 2024-26: WR 71.5%, PF 1.50, 2.9 trades por día.
Apaga LON, ON07, MOM13 y MOM1030. Agrega VW13 (2 contratos cuando el precio está lejos de la VWAP) y VOLB a favor de la tendencia con objetivo 0.5R.
Gana menos dinero que Ultra: elegilo si priorizás el winrate.

## Perfil Core y monitor de ventaja (2026-10-03)

### Perfil Core
- Solo los 6 módulos que funcionaron 11 años: ORB60 (0.6R), MSEQ, CRT11, LON, ICT ×2 y VOLB (2R). Sin MOM, ON07, REV06, VW13, contexto ni confluencia.
- Resultados (1 lote): Sharpe 2.45 / 2.94 / 2.88, PF 1.38 / 1.51 / 1.50, 1.85 trades/día (CFD 2020-23 / CFD 2024-26 / MNQ real).
- Uso: respaldo si el monitor de ventaja da alarma con Ultra.

### Monitor de ventaja (grupo "06. Edge monitor")
- CUSUM del resultado diario por contrato, normalizado por el ATR diario: S = max(0, S + k − z), alarma si S > h.
- Calibración automática por perfil: Ultra k 0.0755 / h 16.21; WR70Plus k 0.0559 / h 15.05; Core k 0.0397 / h 9.98.
- Ultra: 1.5% de falsas alarmas por año, ninguna en 2020-26. Si la ventaja desaparece, la detecta en ~7 meses (mediana); si se vuelve negativa, en ~4 meses.
- Edge monitor start date = el día que empezás en vivo.
- Pause new entries on alarm = false (solo avisa) o true (deja de abrir trades hasta que cambies la fecha de inicio).
- Panel: "Edge monitor: X% of alarm". La ventana Output imprime una línea EDGE por día.
- Auditoría completa: research/mine/robust_lab.py, robust_monitor.py, robust_report.py.
- Página: https://claude.ai/artifact/8FesKUvF4JKEYCPwdaSJ2X

## Módulo LATE15 (2026-10-03, noche)
- A las 15:00 ET, si el precio ya se movió al menos 0.5 × ATR desde la apertura RTH en la dirección de la tendencia diaria, entra a favor. Stop 0.3 ATR, objetivo 0.5R, cierre 15:55.
- Activo en Ultra, WR70Plus y Core (switch "LATE15 on").
- Resultado solo: PF 1.44 / 1.29 / 1.29 (CFD 2020-23 / CFD 2024-26 / MNQ real) y 1.39 en 2015-19. Unos 0.17 trades por día.
- En la cartera suma +$30-40 por mes por lote, sin empeorar el Sharpe ni el drawdown.

## Cuentas de prop con 1 contrato (actualizado 2026-10-05: protocolo EQUILIBRIO)
Optimizado sobre el ciclo completo de 12 meses: evaluación, fondeada, cobros y costos de cada evaluación. Lucid Flex 50K, 1 contrato por módulo.

**Evaluación**
- **NQMaster:** Profile = Ultra, Contracts = 1, PropMode = **Eval**, EvalTarget = 3000, ConsistencyPct = 50. El objetivo real pasa a ser el mayor entre $3.000 y 2× el mejor día, por la regla del 50% de Lucid.
- **GoldMaster:** Profile = **Robust**, Contracts = 1, EvalTarget = 3000, StartBalance = 50000.
- Arrancá apenas compres la evaluación. Esperar a un ATR "bueno" sube la aprobación, pero cuesta más ingreso del que recupera.

**Fondeada**
- **NQMaster:** PropMode = **Funded**. Opera en SAFE (sin ×2 y sin VOLB, LON, MOM1030 ni MOM11) si el colchón sobre el nivel de liquidación es < $750, y completo por encima.
- **GoldMaster:** Profile = **WinRate**, EvalTarget = 0.
- Pedí el cobro cuando la ganancia llegue a **$5.000**; el panel avisa.

**Resultado por cuenta y por mes** (CFD 2020-23 / CFD 2024-26 / MNQ+MGC real 2024-26):

| Prueba | Hoy (Ultra / Ultra / cobro $5k) | EQUILIBRIO |
|---|---|---|
| Historia | $794 / $833 / $1.010 | **$822 / $943 / $1.209** |
| Costos +1 tick por lado | $723 / $851 / $885 | **$759 / $923 / $1.085** |
| Monte Carlo (2.000 años) | $658 / $939 / $978 | **$677 / $1.012 / $1.087** |
| Fondeadas quemadas por año (historia) | 0,16 / 1,26 / 1,00 | **0,08 / 0,72 / 0,58** |
| Días para aprobar la evaluación (mediana) | 30 / 25 / 22 | **29 / 22 / 20** |
| Aprobación de la evaluación | 84 / 72 / 75% | 84 / 71 / 74% (igual) |

**Varias cuentas a la vez** (Monte Carlo, ingreso total por mes, EQUILIBRIO; 2020-23 / 2024-26 real):
- 3 cuentas: $2.043 / $3.224. El 10% de peores años: $847 / $1.995.
- 5 cuentas: $3.405 / $5.370. El 10% de peores años: $1.454 / $3.255.
- Probabilidad de un año negativo: menos de 4%.

**Alternativa APROBACIÓN** (si preferís perder menos evaluaciones aunque se gane menos):
- EvalCushionFull = 900, EvalDailyStop = 700, AtrStartMax = 1,15 (empezar solo con el panel en "OK").
- FundedCushionSafe = 1500, FundedHighFull = false, cobro a $6.000.
- Aprobación 95 / 82 / 89%, pero ~$475-800 por mes por cuenta.

**Lo que no se puede:** con 1 contrato, aprobar en más porcentaje y a la vez más rápido. Los dos dependen de la ganancia por unidad de varianza, y la ventaja por trade ya está en su techo. Las variaciones de ±5 puntos en el porcentaje de aprobación son ruido estadístico.

Investigación: `research/mine/acct_*.py` (`acct_life2.py`, `acct_mc.py`, `acct_multi.py`, `acct_evalcheck.py`).

**Variante EQ2** (un poco más de ingreso, algunas fondeadas quemadas más):
- Configuración: FundedCushionSafe = 750, **FundedCushionFull = 1500**, cobro a **$4.000**.
- Opera SAFE con colchón < $750, sin ×2 entre $750 y $1.500, y completo por encima.
- Ingreso por cuenta y por mes: $871 / $1.031 / $1.293 (historia) y $699 / $1.066 / $1.111 (Monte Carlo). Es +5-9% sobre EQUILIBRIO.

## Lucid Flex 100K con 1 contrato (2026-10-05)
Reglas: objetivo $6.000, drawdown de cierre diario $3.000 (se fija en +$100 al cerrar arriba de +$3.100), consistencia 50% en la evaluación. En la fondeada, días de ≥ $200 y cobro del 50% hasta $2.500. Precio ~$215 con cupón.

Simulación del ciclo completo, protocolo EQUILIBRIO (2020-23 CFD / 2024-26 CFD / 2024-26 real):

| Cuenta | Aprobación | Días para aprobar | Fondeadas quemadas/año | $/mes por cuenta |
|---|---|---|---|---|
| 50K, 1 contrato | 87 / 69 / 72% | 29 / 24 / 21 | 0,23 / 1,33 / 0,70 | $856 / $1.003 / $1.304 |
| **100K, 1 contrato** | **98 / 90 / 88%** | 58 / 52 / 48 | **0,02 / 0,40 / 0,36** | $731 / $901 / $1.012 |
| 100K, 2 contratos | 64 / 57 / 61% | 25 / 20 / 20 | 0,59 / 0,78 / 0,69 | $1.196 / $1.427 / $1.767 |

**Configuración en 100K:**
- **NQMaster:** StartBalance = 100000, PropTrailingDD = 3000, EvalTarget = 6000, FundedCushionSafe = 1125, FundedPayoutAt = 5000.
- **GoldMaster:** StartBalance = 100000, EvalTarget = 6000 en la evaluación.

## Configuración elegida por Federico (2026-10-05): 50K con EQ2
Prioridad: más ingreso, aunque se quemen más cuentas.
- **Evaluación:**
  - NQMaster: Ultra, Contracts 1, PropMode Eval, EvalTarget 3000, ConsistencyPct 50.
  - GoldMaster: Robust, Contracts 1, EvalTarget 3000, StartBalance 50000.
- **Fondeada:**
  - NQMaster: PropMode Funded, FundedCushionSafe 750, FundedCushionFull 1500, cobro cuando la ganancia llega a $4.000 (FundedPayoutAt 4000).
  - GoldMaster: WinRate, EvalTarget 0.
- **Esperado por cuenta:**
  - Aprobación ~71-84%, en ~20-29 días.
  - $871 / $1.031 / $1.293 por mes (historia) y $700 / $1.053 / $1.110 (Monte Carlo).
  - Fondeadas quemadas ~0,1-0,9 por año.

## MÁXIMO DINERO: 50K con 2 contratos (2026-10-05, reemplaza la configuración anterior)
Ciclo completo de 12 meses por cuenta, con el costo de cada evaluación ($105) descontado (`research/mine/acct_k.py`, `acct_kmc.py`).
- **Evaluación:**
  - NQMaster: Ultra, **Contracts 2**, PropMode Eval, EvalTarget 3000, ConsistencyPct 50.
  - GoldMaster: Robust, **Contracts 2**, EvalTarget 3000, StartBalance 50000.
  - Sin stop diario ni modo SAFE: con 2 contratos no mejoran.
- **Fondeada:**
  - NQMaster: **Contracts 2**, PropMode Funded, FundedCushionSafe 750, FundedCushionFull 1500, cobro a **$4.000**.
  - GoldMaster: WinRate, **Contracts 2**.
- **Límites de Lucid:** el máximo de contratos abiertos a la vez sería ~20 micros en el peor día (16 en el 99% de los días). Entra en el límite de la evaluación (30) y en el de la fondeada inicial (20). Con 3 contratos se pasaría.

| $/mes por cuenta | Historia | Costo +1 tick | Monte Carlo |
|---|---|---|---|
| 2020-23 | **$1.369** (antes $871) | $1.158 ($781) | $991 ($696) |
| 2024-26 CFD | **$1.282** ($1.031) | $1.228 ($967) | $1.276 ($1.061) |
| 2024-26 real | **$1.510** ($1.293) | $1.249 ($1.194) | $1.436 ($1.113) |

- **Evaluación:** aprueba ~47-54% (antes ~70-87%), pero en **10-11 días** (antes 21-29).
- **Costo:** se compran ~9 evaluaciones por año por cuenta (~$975), y aun así se gana más.
- **Fondeadas quemadas:** ~2-2,8 por año por cuenta. Es el precio de ganar más.
- **Probabilidad de un año en pérdida:** ≤ 2%.
- **Probado y descartado:** SAFE o stop diario en la evaluación con 2 contratos; 3 contratos (no entra en los límites); más contratos solo en el oro (quema más y gana menos en real).

## Ultra ampliado: más trades con el mismo win rate (2026-10-06)
Activos por defecto en el perfil Ultra (switches en "01. Module switches"):
- **ENG10:** la vela de 4 h 06:00-10:00 cierra fuera del máximo o mínimo de la vela 02:00-06:00, a favor de la tendencia. Entre las 10:00 y las 11:30, orden stop 1 tick por fuera de la vela. Stop a mitad de su rango, objetivo 0,5R.
- **LATEFH:** a las 15:00, si la primera media hora (cierre de las 10:00 contra el cierre anterior) y el movimiento del día van en la misma dirección, ambos ≥ 0,25 ATR, continúa. Stop 0,20 ATR, objetivo 0,5R.
- **VW13 wide:** VW13 desde 0,15 ATR de distancia a la VWAP, con 2 lotes desde 0,30 (como en WR70Plus).

Resultado (2020-23 / 2024-26 CFD / 2024-26 real):

| | Ultra | Ultra ampliado |
|---|---|---|
| Trades por día | 4,63 / 4,67 / 4,46 | **5,39 / 5,45 / 5,15** |
| Win rate | 63,3 / 64,7 / 64,2% | 63,7 / 65,0 / 64,1% |
| PF | 1,44 / 1,41 / 1,47 | 1,42 / 1,41 / 1,45 |
| Sharpe | 3,37 / 3,04 / 3,58 | 3,37 / 3,12 / 3,59 |
| Ciclo de cuenta, Monte Carlo, 1 contrato ($/mes) | 1.054 / 686 / 1.114 | **1.084 / 766 / 1.129** |
| Ídem, 2 contratos | 1.248 / 957 / 1.473 | 1.212 / 1.024 / 1.401 (parejo) |

## Error corregido en la investigación de ICT
La simulación cancelaba la orden límite si en la misma barra el precio también superaba el extremo del barrido. En la realidad se llena y pierde. Con la corrección (`research/ict_fix.py`), ICT da PF 1,23 / 1,39 / 1,37 en lugar de 1,53 / 1,56 / 1,53. El 1,23 coincide exacto con la validación en NinjaTrader. En el total de Ultra el efecto es chico: PF −0,01 y Sharpe −0,03 a −0,06. NQMaster no cambia: en NinjaTrader los llenados ya son reales.

## Configuración para pasar rápido en 50K y por qué no usar tamaño adaptativo (2026-10-07, `research/mine/eval50_fede.py`)
Federico probó en NinjaTrader WR70Plus con 4 contratos que bajan a 1 tras $800 de caída (AdaptiveSize) y stop diario de $500. Comparación en Lucid 50K, con los módulos nocturnos, 3 períodos:

| Configuración | Pasa | Pasa en ≤ 22 días | Mediana | $/mes por cuenta | P(año en pérdida) |
|---|---|---|---|---|---|
| **WR70Plus 2 fijos** | **59%** | **47%** | 13 días | $1.208 | 1,0% |
| **Ultra 2 fijos** | 48% | 45% | 10 días | **$1.393** | 1,6% |
| Ultra 3 fijos | 40% | 39% | 6 días | $1.400 | 1,3% |
| WR70Plus 4 fijos | 38% | 37% | 7 días | $1.250 | 1,1% |
| WR70Plus 4→1 @$800 + stop diario $500 | 42% | 23% | 19 días | $611 | 21% |
| Ultra 4→1 @$800 + stop diario $500 | 35% | 23% | 16 días | $581 | 27% |

- **El tamaño adaptativo con stop diario de $500 es lo peor.** Después de caer $800 opera con 1 contrato y tarda mucho en recuperarse, y el stop de $500 corta días que terminaban bien.
- **Para aprobar más seguido:** WR70Plus + `NightOnWr70` + GoldMaster WinRate, **2 contratos fijos**, AdaptiveSize false y DailyLossLimit 0. El resto, igual que el plan 50K: PropMode Eval, StartBalance 50000, PropTrailingDD 2000, EvalTarget 3000, ConsistencyPct 50, EvalProfitStop / AccountProfitStop 1400 y EvalStartDate = hoy.
- **Para más dinero:** Ultra + GoldMaster Robust, 2 fijos.

**Probar en NinjaTrader:**
- Contracts 1, PropMode Off, AdaptiveSize false.
- **Fecha de inicio 4-6 meses antes** del período que querés mirar. NQMaster calienta ~15-25 días de sesión regular y GoldMaster 60; una prueba de 31 días opera solo los últimos días.
- **Un mes solo no decide:** en la investigación con futuros reales, agosto 2026 perdió con los dos perfiles (Ultra −$2.975, WR70Plus −$3.591). Septiembre, hasta el 25, ganó con los dos (+$5.833 y +$2.854).

## ★★ PLAN RECOMENDADO (2026-10-07): 5 cuentas LucidFlex 150K
Lucid permite como máximo **5 cuentas fondeadas por hogar**, 10 cuentas en total y $750K combinados. Con ese límite manda el dinero **por cuenta**. Con tamaño proporcional al límite de pérdida, la 150K deja más que la 100K y la 50K (`research/mine/acct_bigger.py`, `acct_150k.py`, `multi150.py`).

Reglas LucidFlex usadas (octubre 2026):

| Cuenta | Objetivo | Pérdida máx. (EOD) | Día de cobro | Tope por cobro | Costo eval |
|---|---|---|---|---|---|
| 50K | $3.000 | $2.000 | ≥ $150 | $2.000 | ~$105 |
| 100K | $6.000 | $3.000 | ≥ $200 | $2.500 | ~$215 |
| 150K | $9.000 | $4.500 | ≥ $250 | $3.000 | ~$285 |

En todas, la evaluación tiene regla de consistencia del 50%. El límite se fija en saldo inicial + $100. Cada cobro es el 50% de la ganancia, hasta el tope, al 90%, con 5 cobros.

**$ por mes por cuenta** (promedio de 9 pruebas y la peor):

| Cuenta y contratos (eval / fondeada) | Promedio | Peor | Evals por año | Pasa |
|---|---|---|---|---|
| 150K 7 / 3 | $1.997 | $1.817 | 13,8 | 37% |
| **150K 6 / 3** | **$1.984** | **$1.723** | 12,7 | 40% |
| 150K 4 / 4 | $1.892 | $1.643 | 10,0 | 49% |
| 100K 4 / 3 | $1.607 | $1.445 | 15,3 | 39% |
| 50K 2 / 2 (perfil anterior) | $1.311 | $1.160 | 12,3 | 48% |
| 150K 6 / 3 + NF05 (ver abajo) | $2.069 | $1.815 | | |
| **150K 6 / 3 + NF05 + LF06 + LF0430 (actual)** | **$2.168** | **$1.981** | | |
| 50K 2 / 2 + NF05 + LF06 + LF0430 | $1.393 | $1.268 | | |

**Con 5 cuentas** (mismos trades en todas, evaluaciones escalonadas cada 5 días; 1.500 años simulados por período; 2020-23 / 2024-26 CFD / 2024-26 real):

| Plan | $/mes promedio | Año malo (10% peor) | P(año en pérdida) | Capital inicial para evaluaciones (90% de los casos) |
|---|---|---|---|---|
| **5 × 150K, 6 / 3, con NF05 + LF06 + LF0430 (actual)** | **$9.787 / $11.497 / $12.462** | $5.253 / $6.114 / $7.144 | ≤ 0,7% | ~$8.300-12.300 |
| 5 × 150K, 6 / 3, con NF05 | $9.383 / $11.070 / $12.142 | $4.827 / $5.759 / $6.836 | ≤ 0,7% | ~$9.400-12.800 |
| 5 × 150K, 6 / 3, sin NF05 | $8.824 / $10.914 / $11.818 | $4.271 / $5.567 / $6.655 | ≤ 1,2% | ~$9.700-12.500 |
| 5 × 50K, 2 / 2, con NF05 | $6.105 / $7.162 / $7.676 | $3.152 / $3.533 / $3.842 | ≤ 0,6% | ~$3.600-4.900 |

**Año por año** (`research/mine/year150.py`; una cuenta 150K 6 / 3 con los módulos nocturnos):

| Año | Datos | $/mes arrancando en enero | Promedio de todos los arranques del año | Peor arranque |
|---|---|---|---|---|
| 2020 | CFD | $1.610 | $1.378 | $769 |
| 2021 | CFD | $1.586 | $2.539 | $1.160 |
| 2022 | CFD | $3.185 | $2.687 | $1.378 |
| 2023 | CFD | $1.383 | $492 | −$306 |
| 2024 | real | $1.989 | $2.349 | $1.491 |
| 2025 | real | $1.491 | $2.335 | $1.242 |
| 2026 (8,7 meses) | real | $3.311 | $3.222 | $2.806 |

Todos los años son positivos arrancando en enero. Pero hay rachas flojas: una cuenta que empezó a mitad de 2023 pudo perder ~$300 por mes durante varios meses. Por eso conviene escalonar las 5 cuentas y no juzgar el sistema por un mes.

## Escalar más allá de 5 cuentas: sumar Apex 150K (`apex150.py`, `combo_sim.py`)
Lucid limita a 5 fondeadas. **Apex permite hasta 20 cuentas PA por hogar.**

**Reglas Apex 2026, versión EOD, 150K** (damnpropfirms / quantvps, octubre 2026):
- **Evaluación:** objetivo $9.000, pérdida máxima $4.000 que sigue al cierre, stop diario blando de $2.000, sin consistencia.
- **Cuenta PA:**
  - activación de $119,
  - cobro tras 5 días que califican,
  - ningún día puede ser ≥ 50% de la ganancia del ciclo,
  - se retira lo que esté por encima de inicial + $4.100,
  - topes 2.500 / 3.000 / 3.000 / 3.000 / 4.000 / $5.000,
  - 100% para vos,
  - 6 cobros.

**Por cuenta Apex 150K:**
- Con 5 contratos en evaluación y **2 en la PA**: **$1.953 por mes**, peor prueba $1.719, 0,7 PA quemadas por año.
- Con 3 contratos en la PA rinde menos, por la regla del 50% y el stop diario.

**Plan combinado** (todas las cuentas operan los mismos trades; 1.500 años simulados por período; 2020-23 / 2024-26 CFD / real):

| Plan | $/mes promedio | Año malo (10% peor) | P(año en pérdida) | Capital inicial (90%) |
|---|---|---|---|---|
| 5 Lucid 150K | $9.711 / $11.348 / $12.281 | $5.231 / $5.946 / $6.886 | ≤ 0,5% | ~$8.300-11.400 |
| **5 Lucid + 5 Apex 150K** | **$18.167 / $21.252 / $22.962** | $10.135 / $11.938 / $13.495 | ≤ 0,3% | ~$12.400-17.700 |
| 5 Lucid + 10 Apex 150K | $26.574 / $31.150 / $33.609 | $14.903 / $17.948 / $20.163 | ≤ 0,4% | ~$15.700-22.700 |
| 5 Lucid + 20 Apex 150K | $43.451 / $50.863 / $54.977 | $25.326 / $30.847 / $34.226 | ≤ 0,5% | ~$22.400-31.800 |

**Configuración Apex 150K:**
- **NQMaster:** Ultra · Contracts 5 en la evaluación / 2 en la PA · StartBalance 150000 · PropTrailingDD 4000 · EvalTarget 9000 · ConsistencyPct 0 · EvalProfitStop 0 · EvalDailyStop 2000 en la evaluación. En la PA, el stop diario de $2.000 lo aplica Apex.
- **Gating en la PA:** PropMode Funded, FundedCushionSafe 1500, FundedCushionFull 3000.
- **GoldMaster:** Robust con los mismos contratos, StartBalance 150000 y AccountDailyStop 2000.

**Antes de escalar:**
1. **Liquidez** (`liquidity.py`, volumen real MNQ + NQ en el minuto de entrada, 2024-26): todas las cuentas mandan las mismas órdenes al mismo tiempo. La orden de una señal, sumando todas las cuentas, representa este porcentaje del volumen de ese minuto:

   | Cuentas | Madrugada (LON, NF05, LF0430, LF06, REV06, ON07) | Horario regular |
   |---|---|---|
   | 5 | 1-2% (2-4% en días tranquilos) | < 0,5% |
   | 10 | 2-4% (4-8%) | < 1% |
   | 25 | 4-10% (8-20%) | < 3% |

   Hasta ~10 cuentas el impacto es chico. Con 25, los módulos de madrugada pueden pagar varios ticks; aguantan +4 ticks (PF ≥ 1,29), no mucho más. Para pasar de ~10 cuentas, conviene apagar los módulos de madrugada en las cuentas extra. **Crecé de a poco y medí el deslizamiento real** con `nt_compare.py`.
2. **Reglas de Apex:** el costo de la evaluación ($150 con descuento) y el mínimo diario para calificar ($250) son supuestos. Confirmarlos antes de comprar.
3. **Términos de cada firma:** confirmar que permiten trading automático y copiar operaciones entre cuentas. No hay cobertura entre cuentas: todas operan en la misma dirección.

**LucidDirect (fondeo directo, sin evaluación; `direct_sim.py`): no conviene.**
- **Reglas en 150K:** $836, pérdida máxima $5.000 (EOD), stop diario blando de $3.000.
- **Ciclo de cobro:** el ciclo necesita $9.000 de ganancia la primera vez y $4.500 después. Ningún día puede superar el 20% del ciclo. Se retira lo que esté por encima de inicial + $5.100, hasta $3.000-3.500.
- **Resultado:** como mucho **$909 por mes por lugar** contra $2.168 de LucidFlex, aun con un stop diario de ganancia. La regla del 20% frena los cobros (~4-5 por año).
- **LucidFlex** es el mejor producto de Lucid para este sistema: la fondeada no tiene regla de consistencia y cobra el 50% de la ganancia.

**Stop diario propio en la fondeada (`fdll150.py`): no conviene.** Con $2.000 deja casi el mismo dinero y quema 20% menos fondeadas, pero empeora la peor prueba ($1.884 contra $1.981). Con valores más chicos pierde dinero.

## Módulo NF05 (2026-10-07): a las 05:00, revertir el movimiento nocturno
Sale de probar en el Nasdaq las familias descubiertas para el oro (`research/mine/gnq_check.py`, `gnq_port.py`, `gnq_lc.py`; 8.568 configuraciones).
- **Regla:** a las 05:00 ET, si el precio se movió ≥ 0,35 ATR diario desde la apertura de la barra de las 20:00, opera en contra de ese movimiento, a mercado y en cualquier dirección. Stop 0,2 ATR, objetivo 2R, máximo 240 minutos.
- **Solo:** PF 1,65 / 1,32 / 1,33 (2020-23 / 2024-26 CFD / real), unos 0,19 trades por día y WR 48-56%.
- **Prueba de régimen 2015-19** (con costo normalizado, nunca usada para elegir): PF **1,61**, 254 trades. Es la más robusta de todas las candidatas.
- **Con deslizamiento extra:** +2 ticks por lado PF 1,33, +4 ticks 1,29. Correlación diaria con Ultra 0,01-0,11.
- **En el portafolio:** Sharpe 3,12 / 3,37 / 3,59 → 3,21 / 3,38 / 3,62 y +3-4% de dinero.
- **En el ciclo de cuenta:** 150K $1.984 → $2.069 por mes por cuenta, mejor en 8 de 9 pruebas; 50K $1.311 → $1.362.
- **En NQMaster:** `UseNf05` (activado en Ultra). Es un módulo horario con un tipo de referencia nuevo: la apertura de la barra de una hora ancla.
- **LF0315:** a las 03:15, revertir el movimiento desde las 03:00. PF 1,15 en 2015-19 y sube el Sharpe por trade, pero en el ciclo de cuenta da resultados mixtos. Queda como `UseLf0315`, apagado.
- **Descartadas:** 18:00 → 19:00 (PF 0,62 en 2015-19) y 08:20 → 08:50 (PF 0,80 en 2015-19), que funcionaban solo en 2020-26. Las de impulso desde las 09:30 se descartan porque repiten MOM1030 y MOM11 (correlación 0,3-0,5) y bajan el Sharpe. G_ORB 08:20 se descarta porque depende del deslizamiento en la noticia (PF 1,04 con +4 ticks).

Backup: `NQMaster_backup_pre_nf05.cs`. Parche: `research/mine/patch_nf05.py`.

## Módulos LF06 y LF0430 (2026-10-07): revertir el arranque de Londres
Salen de ampliar la búsqueda de impulsos anclados a 16 horas ancla (`research/mine/nqdrive_check.py`, `nqdrive_port.py`, `nqdrive_lc.py`; 5.760 configuraciones), con Ultra + NF05 como base. Las dos pasaron 2015-19 y +4 ticks, y suben el Sharpe del portafolio en los 3 períodos. Las dos están activadas en Ultra (`UseLf06`, `UseLf0430`).

| Módulo | Regla | PF 2020-23 / 24-26 CFD / real | Win rate | 2015-19 | +4 ticks |
|---|---|---|---|---|---|
| **LF06** | A las 06:00, si el precio se movió ≥ 0,2 ATR desde las 04:00, operar en contra (cualquier dirección). Stop 0,2 ATR, objetivo 0,5R, máx. 240 min. | 1,49 / 1,40 / 1,45 | **~74%** | 1,20 | 1,32 |
| **LF0430** | A las 04:30, si se movió ≥ 0,1 ATR desde las 04:00, operar en contra, solo a favor de la tendencia diaria. Stop 0,35 ATR, objetivo 0,5R, máx. 240 min. | 1,52 / 1,46 / 1,43 | ~61% | 1,10 | 1,36 |

- **Portafolio, sumando las dos a Ultra + NF05:** Sharpe 3,21 / 3,38 / 3,62 → **3,31 / 3,47 / 3,71**, +3-4% de dinero, win rate igual (63-65%).
- **Cuenta 150K 6 / 3:** $2.069 → **$2.168 por mes por cuenta**. Mejor en las 9 de 9 pruebas, y la peor pasa de $1.815 a $1.981.
- **Cuenta 50K 2 / 2:** $1.362 → $1.393, mejor en 7 de 9.
- **Descartadas en esta búsqueda:**
  - 01:00 → 05:00: repite NF05.
  - 05:00 → 09:00 y 07:00 → 09:00: pierden en 2015-19.
  - 07:00 → 11:00 a favor: correlación 0,3-0,4 con Ultra.
  - Las de 12:00 y 13:00: pierden en 2015-19.

Backup: `NQMaster_backup_pre_lf06.cs`. Parche: `research/mine/patch_lf06.py`.

**Robustez de parámetros:** los tres módulos están sobre una meseta, no sobre un pico aislado. Al variar el stop, el objetivo y el tiempo máximo, la mediana de PF de los vecinos (2020-23 / 2024-26 CFD / real) da:
- **NF05:** 1,32 / 1,21 / 1,32 con umbral 0,35 ATR. Con 0,1 y 0,2 ATR no funciona: el efecto es revertir movimientos nocturnos **grandes**.
- **LF06:** 1,30 / 1,24 / 1,31 con umbral 0,2 ATR.
- **LF0430:** 1,48 / 1,13 / 1,20 con su umbral, a favor de la tendencia. Con el umbral contiguo (0,2 ATR, cualquier dirección) también funciona: 1,37 / 1,35 / 1,24.

**Límites de contratos:** con 1 contrato por módulo hay como máximo 11 micros abiertos a la vez (p99: 7). Con 6 contratos el peor día llega a 66 micros, debajo de los 100 de la evaluación de 150K. Con 3 contratos llega a 33, debajo de los 40 con que arranca la fondeada de 150K. En 50K con 2 contratos el peor día llega a 22 micros contra 20 en el arranque de la fondeada: pasa muy rara vez, pero existe.

**Configuración 150K:**

| Fase | NQMaster (MNQ) | GoldMaster (MGC) |
|---|---|---|
| **Evaluación** | Ultra · **Contracts 6** · PropMode Eval · StartBalance **150000** · PropTrailingDD **4500** · EvalTarget **9000** · ConsistencyPct 50 · EvalProfitStop **4200** | Robust · **Contracts 6** · StartBalance **150000** · EvalTarget **9000** · AccountProfitStop **4200** |
| **Fondeada** | **Contracts 3** · PropMode Funded · StartBalance 150000 · PropTrailingDD 4500 · FundedCushionSafe **1700** · FundedCushionFull **3400** · FundedPayoutAt **6000** | Robust · **Contracts 3** · StartBalance 150000 · EvalTarget 0 · AccountProfitStop 0 |

- El modo pasar fácil (EvalMode) de GoldMaster está calibrado para 50K; no usarlo con 150K.

**Pasar la evaluación más fácil (`eval150_easy.py`, con los módulos nocturnos, fondeada 3 contratos):**

| Contratos en la evaluación | Pasa | Mediana | Evals por año | $/mes por cuenta | Peor prueba |
|---|---|---|---|---|---|
| **6 (recomendado)** | 41% | 9 días | 12,2 | **$2.168** | $1.981 |
| 5 | 45% | 10 días | 11,1 | $2.104 | $1.797 |
| 4 | **50%** | 13 días | 8,7 | $2.051 | $1.755 |

Con 4 contratos pasa la mitad de las veces y se compran un 30% menos de evaluaciones, a cambio de un 5% menos de dinero. Para usarlo: Contracts 4 en la evaluación, en NQMaster y en GoldMaster; el resto igual.

**Alternativa de win rate alto (150K, 6 / 3; `research/mine/wr150.py`):** NQMaster **WR70Plus** + GoldMaster **WinRate**, con los módulos nocturnos sumados en la investigación.

| Perfil | Win rate real | PF real | $/mes por cuenta | Peor prueba | Fondeadas quemadas por año |
|---|---|---|---|---|---|
| **Ultra + noche + oro Robust (recomendado)** | 63,6% | 1,43 | **$2.168** | $1.981 | 2,8 |
| WR70Plus + noche + oro WinRate | **69,5%** | **1,50** | $1.903 | $1.739 | **1,3** |

Gana 6 puntos de win rate y quema la mitad de fondeadas, a cambio de un 12% menos de dinero.

**Configuración:** Profile = **WR70Plus** y **NightOnWr70 = true**, que agrega NF05, LF06 y LF0430. GoldMaster en Profile = **WinRate**. Los contratos y los parámetros de prop son los mismos del plan 150K.
- Si vas a tener menos de 5 cuentas y el capital es la restricción, la 50K rinde más por dólar de evaluación. Con 5 cuentas, la 150K deja más dinero total.

## ★ PERFIL FINAL (actualizado 2026-10-06 noche): 50K Lucid, 2 contratos, oro Robust en las dos fases
Recalculado con los datos corregidos esta noche (ver "Errores de la investigación corregidos" más abajo). Sale de 168 combinaciones de perfil de evaluación, perfil de fondeada, contratos y cobro, con ICT corregido. Cada una se probó con historia, costos +1 tick y Monte Carlo en 3 períodos (`research/mine/prof_grid.py`, `final_verify2.py`).

| Fase | NQMaster (MNQ) | GoldMaster (MGC) |
|---|---|---|
| **Evaluación** | Profile **Ultra** (ampliado: ENG10, LATEFH y VW13 wide activos) · **Contracts 2** · PropMode **Eval** · EvalTarget 3000 · ConsistencyPct 50 · **EvalProfitStop 1400** | Profile **Robust** · **Contracts 2** · EvalTarget 3000 · StartBalance 50000 · **AccountProfitStop 1400** |
| **Fondeada** | **Contracts 2** · PropMode **Funded** · FundedCushionSafe **750** · FundedCushionFull **1500** · cobro a **$4.000** | Profile **Robust** (antes WinRate) · **Contracts 2** · EvalTarget 0 · AccountProfitStop 0 |

**Cambio en la fondeada: oro Robust en vez de WinRate.** Gana en 7 de las 9 pruebas. El promedio pasa de $1.275 a **$1.314 por mes por cuenta** y la peor prueba de $1.107 a **$1.163**. Las fondeadas quemadas no cambian.

**Velocidad de la evaluación** (promedio de 3 períodos, empezando cada día de la historia; `research/mine/eval_speed.py`, `eval_pol50.py`):

| Tamaño en la evaluación | Pasa | ≤ 15 días | ≤ 22 días | Mediana | $/mes por cuenta |
|---|---|---|---|---|---|
| **2 contratos fijos (perfil final)** | 48% | 38% | 45% | 9 días | $1.314 |
| Modo pasar fácil (ver abajo) | 62% | 33% | 46% | 15 días | $1.179 |
| 1 contrato fijo | 69% | 28% | 40% | 20 días | $1.119 |

- Con 2 contratos la evaluación se define rápido: el 93% de las que pasan lo hacen en ≤ 22 días. Pero solo pasa la mitad.
- **No hay forma de pasar el 80% en 15-22 días con la ventaja actual.** Con un límite que sigue al pico, la probabilidad de pasar depende de la ganancia diaria comparada con su variación. Más contratos dan más velocidad pero menos seguridad. Para 80% en ~18 días haría falta un Sharpe anual de ~5; el sistema tiene 3,3-3,9.
- Se probaron 480 reglas de tamaño dinámico. La mejor sube la probabilidad de pasar en ≤ 22 días de 44,8% a 46,7%.
- Pesos por módulo optimizados con 2020-23 no mejoraron 2024-26.

**Modo pasar fácil (opcional):** pasa más seguido a cambio de un 10% menos de dinero.
- **NQMaster:** Contracts 1 · EvalMode on · EvalStartDate = día de inicio · EvalLateDay 8 · EvalLateGoal 2100 · EvalLateContracts 2 · EvalLateMinCushion 1000 (necesita PropMode Eval).
- **GoldMaster:** Contracts 1 · EvalMode on · EvalStartDate = día de inicio. Los demás valores ya vienen por defecto.
- Opera 1 contrato las primeras 8 sesiones. Desde la 9ª pasa a 2 si la ganancia todavía es menor a $2.100 y quedan al menos $1.000 sobre el límite.

**Stop de ganancia en la evaluación:** si la cuenta gana $1.400 en el día, se deja de operar. Así ningún día supera el 50% de los $3.000 (regla de consistencia de Lucid) y se aprueba al llegar al objetivo. Suma +5-7% en Monte Carlo en los 3 períodos. Con 1 contrato, usá 700.

**$ por mes por cuenta** (2024-26 CFD / 2020-23 CFD / 2024-26 real):

| Prueba | Este perfil | Ultra anterior con 2 contratos |
|---|---|---|
| Historia | $1.282 / $1.421 / $1.278 | $1.158 / $1.383 / $1.356 |
| Costos +1 tick por lado | $1.261 / $1.292 / $1.252 | $1.120 / $1.300 / $1.343 |
| Monte Carlo (1.000 años) | $1.378 / $1.163 / $1.503 | $1.167 / $1.008 / $1.348 |

- **Promedio de las 9 pruebas:** $1.314 contra $1.243. Peor prueba: $1.163 contra $1.008.
- **Probabilidad de un año en pérdida:** 0,6-1,4%.
- **Por cuenta y por año:** ~9-14 evaluaciones compradas, ~3-4 fondeadas quemadas y ~8-11 cobros. Más contratos implican más cuentas quemadas, pero más plata.
- Con costos +1 tick, el Ultra anterior rinde algo más en datos reales ($1.343 contra $1.252), porque los módulos nuevos agregan trades. En el promedio de las 9 pruebas, el perfil final sigue arriba.

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

## Oro: reversiones de madrugada con 16 años (`research/mine/gold_new_port.py`, `lc150.py`)
Las mismas 5.760 configuraciones de impulsos anclados, corridas en oro 2010-2026. Solo 4 ganan en los cinco tramos, cerca de lo que daría el azar con tantas pruebas:
- GF07: a las 07:00, revertir el movimiento desde las 06:00. WR 76%.
- GD11: a las 11:00, seguir el impulso desde las 10:00.

En la cuenta 150K suman +1% de promedio, pero la peor prueba no mejora y por separado ganan en 3-4 de 9 pruebas. **No entran.**

Guía operativa paso a paso: `OPERAR_5x150K.md`.

## Evaluaciones de repuesto en paralelo: no conviene (`research/mine/seats_sim.py`)
Lucid permite 10 cuentas en total, pero solo 5 fondeadas. Simulé, día por día, tener 2 o 3 evaluaciones escalonadas por cada lugar libre para reponerlo más rápido. No conviene: todas operan los mismos trades, así que pasan o fallan juntas. Las que pasan sin lugar libre se pierden y se pagan evaluaciones de más. La política actual, una evaluación por lugar libre, rinde 3-25% más que cualquier variante en paralelo.

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

## ¿75-80% de evaluaciones aprobadas en 20 días? (2026-10-07, `research/mine/eval20.py`, `eval20_life.py`)
Medido con el sistema ya corregido (con cortos y módulos nocturnos) sobre Lucid Flex 50K: objetivo $3.000, MLL $2.000 EOD, consistencia 50% y stop de ganancia diario $1.400. Cada día hábil cuenta como un inicio posible. Promedio de IS, C24 y REAL:

| Configuración | Aprueba en ≤20 días hábiles | Aprueba sin límite | Mediana de días | Quema |
|---|---|---|---|---|
| WR70Plus + noche + oro WinRate, **2 contratos** | 45% | 60% | 14 | 40% |
| WR70Plus + noche, 2 contratos (tu prueba) | 43% | 60% | 14 | 40% |
| Ultra + noche + oro Robust, 2 contratos | 44% | 49% | 10 | 51% |
| WR70Plus + noche + oro WinRate, **1 contrato** | 20% | **84%** (70% en C24) | 32 | 16% |
| 1 contrato, pasa a 2 en el día 15 si va < $2.100 | 26% | 71% | 23 | 29% |

- **Ninguna configuración llega a 75-80% en ≤20 días.** Las más de 300 políticas de tamaño probadas (subir o bajar contratos según el día y el colchón) quedan en 41-46%.
- **Por qué:** el porcentaje que aprueba en un plazo fijo depende de qué tan estable es la ganancia diaria (Sharpe). Haría falta un Sharpe anual de ~5 a 6, y el sistema tiene ~3,5 a 4.
- **Qué forma de cuenta lo permitiría** (`eval20_map.csv`, k = contratos):
  - sin regla de consistencia,
  - objetivo de ≤ $750 × k,
  - drawdown de ≥ $1.500 × k, es decir, el drawdown del doble del objetivo.

  Con la consistencia del 50%, el techo es ~55%, aunque el objetivo sea chico.
- **Lo que sí se puede elegir:**
  - **Velocidad:** 2 contratos. ~45% aprueba en 20 días, mediana 14 días.
  - **Probabilidad:** 1 contrato + oro WinRate. 84% aprueba, pero tarda ~6 semanas (Lucid no tiene límite de tiempo).

## Subir el win rate por trade: ¿ayuda a aprobar? (2026-10-08, `research/mine/pass20_search.py`)
Todas las mezclas se miden igual: Lucid 50K, aprobar en ≤20 días, simulación diaria. Los contratos se eligen en IS (2020-23) y se aplican en C24 y en MNQ real.

| Mezcla | Win rate (MNQ real) | Profit factor (real) | Trades/día | Aprueba ≤20 días (IS / C24 / real) |
|---|---|---|---|---|
| WR70Plus + noche (tu perfil) | 68,9% | 1,37 | 3,5 | 42 / 40 / 44% |
| Ultra + noche | 63,8% | 1,38 | 6,0 | 38 / 40 / 44% |
| Win rate 75%, 4 trades/día | 72,7% | 1,33 | 4,0 | 43 / 30 / 35% |
| Win rate 80%, 4 trades/día | 77,7% | 1,19 | 3,9 | 38 / 41 / 41% |
| Win rate 80%, 1 trade/día | 80,6% | 1,36 | 1,2 | 25 / 34 / 36% |
| Mejor de la búsqueda directa (elegida en IS) | 70,2% | 1,31 | 4,4 | **55** / 39 / 45% |

- **El win rate sí se puede subir a 75-80%,** achicando los objetivos de ganancia. Pero cada ganancia es más chica y el profit factor baja, así que se aprueba igual o menos.
- **La búsqueda directa** probó 30 arranques sobre 23 módulos, cada uno con sus objetivos y tamaños. En 2020-23 llega a 55%, pero fuera de muestra vuelve a 39-45%, lo mismo que tu perfil: es sobreajuste. No se cambia el perfil.

## ★ Evaluación con 1 contrato: modo Estable (2026-10-08)
Pedido: aprobar ~84% de las evaluaciones con 1 contrato y tardar menos de ~6 semanas.

**Qué hace.** Mientras la cuenta tiene colchón (≥ $1.200 sobre el umbral de pérdida), opera Ultra completo con los módulos nocturnos. Si el colchón baja de $1.200, ese día opera solo los módulos más estables, sin multiplicador x2:
- CRT11, ORB90, MSEQ, ON07, REV06, VW13, ENG10 y LATEFH;
- VOLB, solo a favor de la tendencia y con objetivo 0,5R.

El oro sigue operando todo el tiempo.

### Configuración
| Dónde | Ajuste |
|---|---|
| NQMaster (MNQ 1 min) | Profile **Ultra**, Contracts **1**, AdaptiveSize **false**, DailyLossLimit **0** |
| NQMaster, grupo 07 | PropMode **Eval**, EvalTarget **3000**, Trailing drawdown **2000**, Eval: full mode when cushion ≥ **1200**, Eval: modules below the cushion **Estable**, EvalProfitStop **1400**, ConsistencyPct **50**, AtrStartMax **1.15** |
| GoldMaster (MGC 1 min) | Profile **WinRate**, Contracts **2** |
| Arranque | Comprá o empezá la evaluación **solo el día en que el panel diga "OK to start a new eval"**: el ATR del día es menor a 1,15 veces su mediana de 60 días, y pasa en ~7 de cada 10 días. |

### Resultado (simulación exacta minuto a minuto, Lucid Flex 50K, cada día posible de inicio)
| Plan | Aprueba CFD 2024-26 | Aprueba MNQ real 2024-26 | Aprueba CFD 2020-23 | Mediana de días hábiles |
|---|---|---|---|---|
| Hoy (WR70Plus + noche + oro WinRate, 1 contrato) | 57-65% | 75-76% | 95% | 25-35 |
| **Modo Estable, cambio a $1.200 (recomendado)** | **92%** | **83%** | **96%** | **28-32** |
| Modo Estable, cambio a $1.500 (más seguro, más lento) | 93% | 91% | 96% | 34-36 |
| 2 contratos con modo Estable | 47-58% | 55-61% | 62-74% | 10-14 |

- **Prueba de remuestreo** (2.000 historias armadas con bloques de 20 días): el plan aprueba con una mediana de ~73-78%, en un rango de 55-90%, y le gana al de hoy en ~2 de cada 3 historias. El 84% no está garantizado: depende del mercado de esas semanas.
- **El cambio está en cuántas se aprueban, no en la velocidad.** Con 1 contrato la ganancia es de ~$100-150 por día, así que llegar a $3.000 lleva ~4-6 semanas igual. Con 2 contratos se tarda la mitad, pero se aprueba ~55%.

### Probado y descartado
- **Buscar en 2020-23 qué módulos usar en cada modo y con qué peso:** 97-98% en esos años, 56-81% fuera de muestra. Es sobreajuste.
- **2 contratos desde el arranque o después del bloqueo:** quema más evaluaciones.
- **Minería completa sobre el S&P (MES, 45.278 configuraciones, `results_es.csv`, `es_check.py`):** ningún candidato sobrevive a 2015-19 más 4 ticks de costo. En MES el costo es 1,27% del rango diario, contra 0,41% en MNQ.

### Para probarlo en Strategy Analyzer
- El cambio de modo usa la ganancia de NQMaster desde su primer trade.
- Para ver una evaluación, empezá la prueba ~2 meses antes del día de inicio (NQMaster necesita ~25 días de mercado de arranque).
- En una prueba de años, una vez que la ganancia pasa $2.100 el umbral queda fijo y la estrategia opera siempre en modo completo.

Scripts: `research/mine/fast1c.py`, `gate84.py`, `gate84b.py`, `gate84c.py`, `gate_joint.py`, `gate_start.py`, `gate_impl.py`, `gate_struct.py`, `gate_final.py` (con remuestreo), `gate_lo.py`, `gate_g.py`, `gate_k2.py`. Backup: `NQMaster_backup_pre_estable.cs`.

## LucidPro: evaluación sin consistencia (2026-10-08)
Pregunta: ¿se puede sacar la regla de consistencia en Lucid?
- **LucidFlex:** no. La evaluación exige que el mejor día sea ≤ 50% de la ganancia, y no hay ningún agregado para quitarla (artículo de soporte de Lucid del 26-08-2026). Si te pasás, no se pierde la cuenta: hay que seguir operando hasta bajar ese porcentaje.
- **LucidPro:** la evaluación **no tiene consistencia**, y se puede aprobar en un día. Reglas de la 50K (proea.app, verificadas el 03-10-2026):
  - Evaluación: objetivo $3.000, pérdida máxima de $2.000 al cierre que se fija en +$100, máximo 4 minis / 40 micros. Pérdida diaria de $1.200 suave y opcional: se quita con un agregado de ~$20. Precio de lista $192 (Flex $146).
  - Fondeada: tamaño completo desde el primer día, colchón de $2.100 (el retiro mínimo de $500 se pide con saldo ≥ inicio + $2.600), tope de retiro $2.000 el primero y $2.500 después, reparto 90/10.
  - Consistencia de la fondeada: **40% por ciclo de retiro** (el mejor día ≤ 40% de la ganancia del ciclo).

### Con 1 contrato no cambia nada
Con 1 contrato la regla del 50% casi nunca frena: un día rara vez supera $1.500. Aprobación con el modo Estable a $1.200, Flex contra Pro: 87/99/85% en los dos casos (CFD 2024-26 / CFD 2020-23 / MNQ real). La mediana de días también es la misma (26-31). Sacar la consistencia no acerca el 84% ni lo hace más rápido.

### Con 3 o 4 contratos sí sirve
| Ultra + noche + oro Robust | Flex aprueba | Pro aprueba | Mediana de días, Flex → Pro |
|---|---|---|---|
| 2 contratos | 44 / 53 / 50% | 47 / 56 / 53% | 9-10 → 7-8 |
| 3 contratos | 36 / 46 / 42% | 42 / 49 / 49% | 6-7 → 4-5 |
| 4 contratos | 32 / 38 / 36% | 38 / 44 / 40% | 5-6 → **3** |

(CFD 2024-26 / CFD 2020-23 / MNQ real; todos los días de inicio. Esperar el ATR < 1,15 no cambia nada con 3-4 contratos. Activar la pérdida diaria de $1.200 en la evaluación baja la aprobación hasta 8 puntos, así que conviene comprar el agregado sin pérdida diaria.)

### Ingreso por cuenta (ciclo de 12 meses: evaluaciones, fondeada y retiros; 9 pruebas = historia, +1 tick y 1.000 años de Monte Carlo en 3 períodos)
| Plan | $/mes por cuenta (promedio) | Peor de 9 | Evaluaciones/año | Fondeadas quemadas/año |
|---|---|---|---|---|
| Flex: evaluación 2c / fondeada 2c, retiro a $4.000 (el plan de hoy) | $1.393 | $1.268 | 12 | 3,6 |
| Pro: evaluación 4c / fondeada 2c, sin tope diario | $1.284 | $1.045 | 13 | 2,8 |
| **Pro: evaluación 4c / fondeada 2c, tope de ganancia diaria $500 en la fondeada, retiro apenas se pueda** | **$1.578** | **$1.331** | 18 | 5,2 |
| Pro: igual con tope de $400 | $1.605 | $1.238 | 19 | 5,1 |
| Pro: evaluación 3c / fondeada 2c, tope $400 | $1.477 | $1.188 | 16 | 5,0 |

- Sin tope diario en la fondeada, Pro gana menos que Flex: la regla del 40% por ciclo frena los retiros.
- Con el tope de $500 (cuenta entera), Pro supera a Flex en 8 de las 9 pruebas, +13% de promedio. Entre $400 y $700 los resultados son parecidos, no hay un valor exacto que importe.
- Con 4 contratos, el máximo de posiciones abiertas a la vez llega rara vez a ~44 micros contra el límite de 40: Lucid rechaza esa orden y NQMaster la ignora. Para no tocar nunca el límite, usá 3 contratos ($1.477).
- Supuestos: Pro a $152 por evaluación (Flex $105). Si pagás el precio de lista, son ~$90/mes menos y Pro sigue arriba. Las dos cuentas cuentan hasta 5 retiros y después pasan a cuenta real.

### Configuración LucidPro 50K
| Fase | NQMaster (MNQ) | GoldMaster (MGC) |
|---|---|---|
| Evaluación | Profile **Ultra**, Contracts **4**, AdaptiveSize false. Grupo 07: PropMode **Eval**, EvalTarget 3000, PropTrailingDD 2000, EvalCushionFull **0**, EvalProfitStop **0**, ConsistencyPct **0**, AtrStartMax 0 | Profile **Robust**, Contracts **4**, AccountProfitStop **0**, ConsistencyPct **0**, EvalTarget 3000 |
| Fondeada | Profile **Ultra**, Contracts **2**. Grupo 07: PropMode **Funded**, FundedCushionSafe 750, FundedCushionFull 1500, **FundedProfitStop 500**, FundedPayoutAt 2600 | Profile **Robust**, Contracts **2**, **AccountProfitStop 500** |

Pedí el retiro apenas el saldo pase el inicio + $2.600 y el mejor día del ciclo sea ≤ 40% de la ganancia del ciclo. Con el tope de $500 esto se cumple casi siempre.

Script: `research/mine/lucidpro.py` (`lucidpro_eval.csv`, `lucidpro_life.csv`, `lucidpro_life_fg.csv`, `lucidpro_life_fg2.csv`). Código nuevo: `FundedProfitStop` en NQMaster. Backup: `NQMaster_backup_pre_lucidpro.cs`.

## ★ Cuenta fondeada en 22 días o menos (2026-10-08)
Pedido: aprobar en un porcentaje muy alto y en no más de 22 días hábiles.

**Una sola evaluación de 50K no llega:** con la ganancia diaria del sistema, ninguna configuración aprueba una evaluación de 50K más de ~50-55% de las veces en 22 días. Lo que sí llega es esto: **si una evaluación se quema, comprás otra y arrancás la sesión siguiente**. Cada evaluación con 4 contratos se define en ~3 días (aprueba o se quema), así que en 22 días entran varias.

### % de veces con cuenta fondeada dentro de 22 días hábiles
Ultra + noche + oro Robust; evaluación nueva al día siguiente de cada quema. Simulación minuto a minuto, todos los días de inicio.

| Plan | Historia (CFD 24-26 / CFD 20-23 / MNQ real) | Con +1 tick de costo | Remuestreo: mediana / peor 10% | Mediana de días | Evaluaciones usadas | Costo |
|---|---|---|---|---|---|---|
| **LucidPro 50K, 4 contratos** | **97 / 94 / 97%** | 97 / 93 / 97% | 94-98% / 89-95% | **5** | 2,4 | ~$370 |
| LucidPro 50K, 3 contratos | 93 / 86 / 92% | 93 / 85 / 92% | 88-95% / 81-89% | 6 | 2,1 | ~$320 |
| LucidPro 25K, 2 contratos | 98 / 96 / 98% | 97 / 96 / 98% | 96-99% / 93-96% | 4 | 2,3 | ~$200 |
| LucidFlex 50K, 2 contratos | 73 / 63 / 74% | 72 / 61 / 72% | 64-77% / 52-68% | 11 | 1,9 | ~$195 |
| LucidFlex 50K, 1 contrato | 47 / 33 / 54% | 45 / 30 / 52% | 32-57% / 21-44% | 13 | 1,2 | ~$130 |

- Cada evaluación sola aprueba ~40%. El 94-97% sale de reintentar rápido. El costo de las evaluaciones extra está incluido arriba, y también en el ingreso mensual de la sección LucidPro ($1.578 por cuenta con evaluación 4c y fondeada 2c con tope de $500).
- La 25K es igual de segura y más barata, pero la fondeada paga topes más chicos ($1.000 / $1.500). Con el límite de 5 fondeadas por hogar, la 50K deja más plata por cuenta.
- La configuración en NinjaTrader es la de la tabla "Configuración LucidPro 50K" de arriba. Cuando una evaluación se quema: comprá otra, cargá NQMaster y GoldMaster en la cuenta nueva con los mismos ajustes y arrancá la sesión siguiente. El archivo del grupo 07 es por nombre de cuenta, así que la nueva arranca limpia.

Scripts: `research/mine/funded22.py` (`funded22.csv`) y `funded22_boot.py` (`funded22_boot.csv`).
