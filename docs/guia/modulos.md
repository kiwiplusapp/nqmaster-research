# Módulos y perfiles de NQMaster

> Parte de `NQMASTER_GUIA.md` partida por tema el 2026-10-26. Texto sin cambios, secciones en el orden original. Índice: `docs/guia/INDICE.md`.

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

## Módulo NF05 (2026-10-07): a las 05:00, revertir el movimiento nocturno
Sale de probar en el Nasdaq las familias descubiertas para el oro (`research/mine/gnq_check.py`, `gnq_port.py`, `gnq_lc.py`; 8.568 configuraciones).
- **Regla:** a las 05:00 ET, si el precio se movió ≥ 0,35 ATR diario desde la apertura de la barra de las 20:00, opera en contra de ese movimiento, a mercado y en cualquier dirección. Stop 0,2 ATR, objetivo 2R, máximo 240 minutos.
- **Solo:** PF 1,65 / 1,32 / 1,33 (2020-23 / 2024-26 CFD / real), unos 0,19 trades por día y WR 48-56%.
- **Prueba de régimen 2015-19** (con costo normalizado, nunca usada para elegir): PF **1,61**, 254 trades. Es la más robusta de todas las candidatas.
- **Con deslizamiento extra:** +2 ticks por lado PF 1,33, +4 ticks 1,29. Correlación diaria con Ultra 0,01-0,11.
- **En el portafolio:** Sharpe 3,12 / 3,37 / 3,59 → 3,21 / 3,38 / 3,62 y +3-4% de dinero.
- **En el ciclo de cuenta** (**no reproducible** desde el repo, 26-oct: `nqdrive_lc.csv` cambia en REAL, ver `docs/experimentos/00_reproducibilidad_tablas.md`)**:** 150K $1.984 → $2.069 por mes por cuenta, mejor en 8 de 9 pruebas; 50K $1.311 → $1.362.
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
- **Cuenta 150K 6 / 3** (**no reproducible** desde el repo, 26-oct, ver `docs/experimentos/00_reproducibilidad_tablas.md`)**:** $2.069 → **$2.168 por mes por cuenta**. Mejor en las 9 de 9 pruebas, y la peor pasa de $1.815 a $1.981.
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

## Oro: reversiones de madrugada con 16 años (`research/mine/gold_new_port.py`, `lc150.py`)
Las mismas 5.760 configuraciones de impulsos anclados, corridas en oro 2010-2026. Solo 4 ganan en los cinco tramos, cerca de lo que daría el azar con tantas pruebas:
- GF07: a las 07:00, revertir el movimiento desde las 06:00. WR 76%.
- GD11: a las 11:00, seguir el impulso desde las 10:00.

En la cuenta 150K suman +1% de promedio, pero la peor prueba no mejora y por separado ganan en 3-4 de 9 pruebas. **No entran.**

Guía operativa paso a paso: `OPERAR_5x150K.md`.
