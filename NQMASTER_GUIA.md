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
| **150K 6 / 3 + NF05** (ver abajo) | **$2.069** | **$1.815** | | |
| 50K 2 / 2 + NF05 | $1.362 | $1.234 | | |

**Con 5 cuentas** (mismos trades en todas, evaluaciones escalonadas cada 5 días; 1.500 años simulados por período; 2020-23 / 2024-26 CFD / 2024-26 real):

| Plan | $/mes promedio | Año malo (10% peor) | P(año en pérdida) | Capital inicial para evaluaciones (90% de los casos) |
|---|---|---|---|---|
| **5 × 150K, 6 / 3, con NF05** | **$9.383 / $11.070 / $12.142** | $4.827 / $5.759 / $6.836 | ≤ 0,7% | ~$9.400-12.800 |
| 5 × 150K, 6 / 3, sin NF05 | $8.824 / $10.914 / $11.818 | $4.271 / $5.567 / $6.655 | ≤ 1,2% | ~$9.700-12.500 |
| 5 × 50K, 2 / 2, con NF05 | $6.105 / $7.162 / $7.676 | $3.152 / $3.533 / $3.842 | ≤ 0,6% | ~$3.600-4.900 |

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

**Límites de contratos:** con 1 contrato por módulo hay como máximo 11 micros abiertos a la vez (p99: 7). Con 6 contratos el peor día llega a 66 micros, debajo de los 100 de la evaluación de 150K. Con 3 contratos llega a 33, debajo de los 40 con que arranca la fondeada de 150K. En 50K con 2 contratos el peor día llega a 22 micros contra 20 en el arranque de la fondeada: pasa muy rara vez, pero existe.

**Configuración 150K:**

| Fase | NQMaster (MNQ) | GoldMaster (MGC) |
|---|---|---|
| **Evaluación** | Ultra · **Contracts 6** · PropMode Eval · StartBalance **150000** · PropTrailingDD **4500** · EvalTarget **9000** · ConsistencyPct 50 · EvalProfitStop **4200** | Robust · **Contracts 6** · StartBalance **150000** · EvalTarget **9000** · AccountProfitStop **4200** |
| **Fondeada** | **Contracts 3** · PropMode Funded · StartBalance 150000 · PropTrailingDD 4500 · FundedCushionSafe **1700** · FundedCushionFull **3400** · FundedPayoutAt **6000** | Robust · **Contracts 3** · StartBalance 150000 · EvalTarget 0 · AccountProfitStop 0 |

- El modo pasar fácil (EvalMode) de GoldMaster está calibrado para 50K; no usarlo con 150K.
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
