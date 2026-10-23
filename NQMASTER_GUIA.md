# NQ MASTER: todo el portafolio en una sola estrategia

## ★★★★★★★★★★★★★★★★★★★ 2026-10-23: ventana del panel (NQMasterPanel.cs)

- **Archivo nuevo, obligatorio:** copiá `NQMasterPanel.cs` junto a `NQMaster.cs` en `Documents\NinjaTrader 8\bin\Custom\Strategies` y apretá F5. Sin ese archivo NQMaster no compila.
- **Cuándo se abre:** al pasar a vivo en un gráfico, se abre una ventana aparte "NQMaster". En el Strategy Analyzer no se abre. Si la cerrás, **Ctrl+Shift+P** con el gráfico seleccionado la vuelve a abrir. Se apaga con *Abrir la ventana del panel...* (grupo 07).
- **Una sola ventana para todas las cuentas:** cada NQMaster activo (una cuenta, un instrumento) aparece en el selector de arriba.
- **Pestañas:**
  - **Resumen:** estado, tendencia y ATR; tarjetas de neto, por mes, % de ganadoras, caída máxima, días positivos y por trade; curva de ganancia diaria; en vivo, lo real contra lo esperado; barra del monitor de borde.
  - **Cuenta:** la cuenta real (saldo, límite, colchón con barra de color, objetivo, retiro disponible) y la simulación del ciclo (resultado neto, retiros, evaluaciones, fondeadas, costos, curva de lo cobrado neto, la cuenta actual con barras de colchón y objetivo, y el historial con fechas en verde y rojo).
  - **Módulos:** tabla por módulo con trades, ganadoras, PF y neto, de todo el período y de los últimos 365 días; PF menor a 1 en rojo.
  - **Avisos:** los avisos activos y los datos de la corrida.
- **Seguridad:** la estrategia solo publica una foto de sus datos; la ventana la lee una vez por segundo. La ventana no puede tocar órdenes, y si falla algo del dibujo la estrategia sigue operando y la ventana muestra el error.
- **Estado:** pasó el chequeo de sintaxis en la nube contra un stub de NinjaTrader y de WPF (`tools/nt8_stub/WpfStub.cs`). El aspecto real se ajusta con capturas tuyas después del F5.
- El panel de texto sobre el gráfico sigue igual; se apaga con *Mostrar el panel*.

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

## ★★★★★★★★★★★★★★★★★ 2026-10-21: plan de cuentas (ronda 5)

Pedido de Federico: más pase en evals de 50K, más probabilidad de cobrar por cuenta, más ingreso con buen win rate y poco drawdown, sin overfitting. Solo NQ (sin GoldMaster). Insumos: `research/mine/prop_wf_report.md` (optimizador walk-forward de políticas: ninguna aceptada), `prop_survey_report.md` + `propfirms_2026-10-21.md` (firmas que permiten bots), `b13_report.md` (lote 13: 0 sobrevivientes). Pruebas de integración: bootstrap pareado, 1.000 caminos por corte, fees con cupón y de lista (`research/mine/integ_*.py` / `integ_*.json`). La configuración exacta de cada cuenta está en `RUNBOOK_OPERACION.md`, que manda sobre esta guía.

**Regla fijada antes de correr:** una plaza o eval nueva reemplaza a la actual solo si, con 35% menos edge, en 2020-23 y en 2024-26 y con los dos niveles de fee, la mediana de la ganancia pareada es > 0 con P ≥ 0,80 y su P(año negativo) no empeora más de 3 puntos (MFFU: además no puede perder más de $100/mes extra sin edge). Nada nuevo pasó: **el plan sigue siendo 5 Lucid Flex 150K + 3 MFFU Rapid EOD 50K**.

### Plazas (cifras de investigación, paridad NT pendiente; 2020-23 / 2024-26)

| Plaza | Cantidad | Preset | Fondeada ≤22 días (hasta 3 evals) | $/mes por plaza: edge completo | con 35% menos | sin edge | P(año negativo) con 35% menos |
|---|---|---|---|---|---|---|---|
| Lucid Flex 150K | 5 | `Lucid150K` (eval 6c, fondeada 3c) | 69 / 72% (35% menos 53 / 53%) | 2.467 / 2.260 | 1.423 / 1.406 | −38 / −52 | 3,4 / 4,6% |
| MFFU Rapid EOD 50K | 3 | `Mffu50K` (eval 1c ×8, fondeada 1c, retiro dejando $4.100) | 41 / 49% (30 / 32%) | 1.414 / 1.163 | 717 / 503 | −131 / −131 | 13,7 / 18,4% |
| Lucid Pro 50K (alternativa a la 150K si se prioriza el pase de 50K) | 0 | `LucidPro50K` | 88 / 84% (73 / 74%) | 1.209 / 1.131 | 804 / 682 | −42 / −114 | 2,2 / 6,0% |
| MFFU Builder 50K (condicional) | 0 | Manual | — | 958 / 835 (optimista) | 539 / 452 | −35 / −111 | — |
| Bulenox Opt1 50K (condicional) | 0 | Manual | — | 855 / 810 (optimista) | 480 / 444 | −49 | — |
| FundedNext Rapid Pro 50K (desborde) | 0 | `LucidPro50K` en eval + Manual | — | 612 / 645 | 344 / 331 | −120 / −146 | — |

Plan completo (5 L150 + 3 MFFU, mismo camino, escalonadas 5 días), $/mes: edge completo 16.280 / 14.739; con 35% menos 8.838 / 8.610 (p10 2.188 / 2.000, P(año negativo) 4 / 5%); sin edge −699 / −266 con cupón (−1.541 / −1.212 con lista). Presupuesto por plaza (−$4.000 Lucid / −$1.500 MFFU): sin edge el p10 sube a −$2.095 por mes; con 35% menos P(año negativo) 4,6 / 6,1%.

- La 150K le gana a Flex 50K 2c/2c (+$486 / +$553 por mes con 35% menos, P 0,91) y a Pro 50K 4c/1c (+$645 / +$768, P 0,92), pero el CI90 incluye 0: la decisión es "no cambiar", no "la 150K es mejor con 90% de confianza". Flex 50K y Pro 50K empatan entre sí.
- MFFU eval 2c o 3c no pasa la regla (con 35% menos +$15 a +$50/mes con P 0,55-0,65; sin edge −$105 a −$288/mes). La escalera (`Mffu50KLadder`) queda como **opción**: con 35% menos +$501 / +$306 por mes pero P 0,63 / 0,58, P(año negativo) 30 / 34% contra 16 / 16%.

### Cambios de código (NQMaster.cs; backup `NQMaster_backup_pre_round5.cs`; solo stub C# 5, **sin F5**)
- **C2, limpieza de plantillas en todos los presets** (no Manual): `EvalMode`, `AdaptiveSize` false; `EvalCushionFull`, `EvalDailyStop`, `FundedCushionSafe`, `FundedCushionFull`, `DailyLossLimit` 0; `FundedHighFull` true; `FundedStepUpCushion`, `FundedLadderStep`, `DailyLossPerContract` 0 salvo con `Mffu50KLadder`; `NewsBlackout` false (Mffu50K lo vuelve a poner en Funded). Mffu50K fondeada fuerza Contracts 1; en eval avisa si Contracts ≠ 1. `HedgeGroup` por firma si está vacío (LUCID / MFFU / FNEXT). El Output imprime una segunda línea `preset ...` con contratos, retiro, escalón, escalera, grupo y apagón de noticias, y un WARNING si `UseOrderFlowBoost` o `VolbReArm` están activos (no se pisan). Consecuencia: el escalón opcional de MFFU (`FundedStepUpCushion` 4000) ahora solo se puede usar con PropPreset Manual.
- **C3, texto de retiro por firma** en el panel (línea `PAYOUT:`), con la regla exacta del simulador: Flex 50K/25K/150K = min(tope, 50% de la ganancia) con 5 días ≥ $150 / $150 / $250 (topes $2.000 / $1.000 / $3.000); Pro 50K = min(tope, ganancia − 2.100) ≥ $2.000, ≥ 3 días, ciclo ≥ $500, mejor día ≤ 40%, topes 2.000 / 2.500 (Pro 25K: 1.100, 1.000, 1.000 / 1.500); MFFU = retirar hasta dejar FundedPayoutAt − 500; Manual y FundedNext25K = "seguí la regla de la firma en RUNBOOK_OPERACION.md".
- **C6, guarda entre cuentas reforzada:** el archivo de cada cuenta (`nqmaster_positions\<grupo>_<cuenta>_NQ.txt`) ahora dice `posición;L;S;hora` (L / S = posición o entrada en espera long / short, también órdenes zombi en vivo) y se escribe cada minuto, al colocar, cancelar, rechazar o llenar una entrada (escritura con archivo temporal + reemplazo). Una entrada nueva se bloquea si otra cuenta del grupo tiene la bandera opuesta (posición o entrada en espera); también el re-envío de órdenes estacionadas, la entrada de mercado de VOLB y la orden stop de VOLB, que antes no pasaban por la guarda. Cada barra se cancelan las entradas propias en espera opuestas a una **posición** de otra cuenta. Si igual se llena una entrada con una posición opuesta en otra cuenta: se cierra enseguida (salida del módulo + `FlattenAll` en la barra siguiente si hace falta), alerta `HEDGE GUARD` y Log. Archivos de versiones viejas (`dir;hora`) se siguen leyendo. Todo solo en tiempo real: el backtest y la paridad no cambian.
  - Detalle de implementación (no estaba en el plan textual): la entrada en espera opuesta de otra cuenta **no** bloquea si esta cuenta también tiene una entrada en espera de ese mismo lado. Con cuentas iguales es el espejo de nuestra propia orden, que la misma señal estaciona acá y en la otra cuenta; bloquearla haría que, por ejemplo, con el stop de VOLB en espera todas las cuentas salteen las entradas opuestas que la investigación toma (estacionando VOLB). Las posiciones opuestas siempre bloquean, y el cierre al llenarse cubre el caso en que la otra cuenta no tome la misma señal.

### Qué no se cambió y por qué
- Las 5 plazas de Lucid siguen en Flex 150K: ni Flex 50K 2c/2c ni Pro 50K pasan la regla. Lucid Pro 50K queda como alternativa si se prefiere aprobar evals de 50K.
- Mffu50K por defecto sin cambios de valores (eval 1c ×8, fondeada 1c, retiro dejando $4.100). Sin presets nuevos (Mffu50KFast y MffuBuilder50K retirados).
- Valores de LucidPro50K, Lucid150K, LucidPro25K, FundedNext25K y Mffu50KLadder: iguales (solo C2 y C3). Lucid50K no fuerza Contracts (las recetas 1c y 2c no coinciden y no está en el plan).
- Ninguna política de `prop_wf` elegida en 2020-22 entra como default (escalones por colchón o días, stops intradía en eval, retiro lo antes posible + stop 500).
- Estrategia y módulos: sin cambios (lote 13 con 0 sobrevivientes). GoldMaster: sin uso.
- Sin código para el objetivo "pegajoso" de los días mínimos de MFFU: se resuelve deshabilitando la estrategia (runbook).
- No se agregan Tradeify, FTMO Pro, Trading Pit, LucidDaily, Apex ni Topstep (motivos en `propfirms_2026-10-21.md`).

### Riesgos abiertos
- **Sin compilar en NinjaTrader.** C6 toca `OnExecutionUpdate`, `OnOrderUpdate` y la publicación de archivos: un error ahí puede bloquear entradas legítimas o cerrar de más. Antes de operar con varias cuentas: F5, Playback con 2 cuentas del mismo grupo (una con risk cap activo y otra sin cap), y ninguna posición opuesta simultánea.
- **Paridad:** las cifras suponen NQMaster.cs = `ultra_d4`; no hay export NT con los ×4 ni con los módulos de 6 años; G4 falló en ICT (82%) y MSEQS (56%) el 16-oct.
- **MaxOpenContracts** cuenta posiciones + entradas en espera; la simulación solo lotes ejecutados. Lucid150K fondeada (3c, tope 40) y Mffu50K eval (×8, tope 30) pueden cortar más: medir los cortes en las corridas por preset.
- **Significancia:** la ventaja de la 150K tiene P 0,87-0,92 con CI90 que incluye 0; P(cobrar ≤62 días) y P(año negativo) se comparan sin prueba pareada de proporciones.
- **La 150K aprueba menos** (una eval 43 / 44% vs 48 / 44% de Pro 50K; con 3 evals 69 / 72% vs 88 / 84%) y quema 2,5-3,3 fondeadas por año con 35% menos: es una elección de ingreso.
- **Rotación:** ~25% del ingreso de la 150K con 35% menos viene de recomprar después de 5 pagos; la recompra inmediata de Lucid sigue sin confirmar. Live de Lucid ("cierra todas las sim", supuesto conservador): −1,8 a −3,1% de la mediana. Live de MFFU no está modelado.
- **Fees:** precios con cupón marcados S (150K $215, lista $285). Sin edge el plan pierde −$699 / −$266 por mes con cupón y −$1.541 / −$1.212 con lista. El presupuesto por plaza se eligió entre 3 valores ya vistos.
- **No simulado:** el apagón de noticias de MFFU (−1,5 a −6,8% del P&L), la regla de límite de precio −2% de MFFU, los trades simbólicos de días mínimos y C6 (puede sacar algunos trades).
- **Liquidez:** 5 L150 + 3 MFFU quedan dentro del caso de 10 cuentas de `liquidity.csv` (3,8% del volumen mediano del minuto en LON, 7,8% en p10). Si se suman Bulenox o FundedNext, revisar los módulos nocturnos.

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

## ★★★★★★★★★★★★★★ 2026-10-19: plan 2026-2027, cuentas 25K de Lucid y módulos de WR alto con RR negativo

Pedido: "¿recomendás muchas cuentas 25K de Lucid? Probá módulos nuevos de WR alto y RR negativo, mejorá todo el sistema y entregame algo que en 2026-2027 funcione casi seguro". Respuesta corta: **"casi seguro" no existe**; abajo están las probabilidades con el edge completo, con 35% menos y con 50% menos. Lo que cambió en el código y en la operación está en `RUNBOOK_OPERACION.md` (versión 2026-10-19), que manda sobre esta guía.

### 1. ¿Muchas cuentas 25K de Lucid? No para ingreso (`research/mine/acct_2027.py` → `acct_2027.json`)

Mismo simulador de asientos que el 17-oct (Ultra + 6 años durables + oro Robust, 12 meses, bootstrap 300 años, asientos correlados), $/día calendario, mediana 2020-23 / 2024-26:

| Plan | Edge completo | −35% | −50% | P(año negativo) −35% |
|---|---|---|---|---|
| 5 × Lucid Flex 25K | 106 / 132 | 56 / 65 | 39 / 41 | 10 / 9% |
| 5 × Lucid Pro 25K | 105 / 137 | 57 / 61 | 35 / 35 | 12 / 11% |
| 5 × Lucid Flex 50K 2c | 230 / 281 | 119 / 153 | 91 / 91 | 8 / 7% |
| **5 × Lucid Flex 150K** (preset `Lucid150K`) | **352 / 459** | **189 / 266** | 136 / 152 | 7 / 3% |
| 3 × MFFU 50K escalera (preset `Mffu50KLadder`) | 335 / 575 | 78 / 156 | −1 / 23 | 34 / 23% |
| 3 MFFU escalera + 5 Lucid 25K | 444 / 704 | 138 / 212 | 52 / 79 | 11 / 7% |
| **3 MFFU escalera + 5 Lucid 150K** | **691 / 1.021** | **273 / 406** | 157 / 210 | **7 / 4%** |

- Lucid deja **5 fondeadas por hogar**: cada plaza ocupada por una 25K rinde $20-27/día contra $69-94 una 150K. Con el tope de 5, gana la cuenta grande.
- Una 25K se quema 8-11 veces por año (DD $1.000); sirve solo para tener la **primera** fondeada rápido (preset `LucidPro25K`).
- La escalera de MFFU amplifica: con −50% de edge su mediana es ~0. Lucid 150K a 3 contratos es la parte estable del plan.

### 2. Módulos nuevos de WR alto y RR negativo: ninguno (`families9.py`, `b9_report.md`)

5 familias nuevas en 16 años de NQ real (números redondos, test del máximo/mínimo overnight, toque del settlement, scalp con tendencia, "snap" de estiramiento), targets 0,2 / 0,3 / 0,5 R con stops anchos, 2.196 configuraciones, chequeos de lookahead sin violaciones. **0 sobrevivientes**: en todas las familias el WR queda en o debajo del break-even del target (83 / 77 / 67%). Junto con `negrr_lab.py` (RR negativo sobre los módulos actuales: más WR, menos $ y Sharpe fuera de muestra), el RR negativo queda descartado. Nota Obsidian: `Descartado/Lote 9 WR alto RR negativo (19-oct).md`.

### 3. Lo que sí cambió para 2027

- **Default nuevo: Ultra + 4 módulos de 6 años "durables"** (SO04, RV11, ORFAIL, CAM3; `SixYearModules` true; CA04V, GD03 y ENG26 apagados; LATEFH ya no se fuerza). Validado en 2010-19 (datos nunca usados para elegirlos, `six_oos.py`): Sharpe 0,19→0,40 / 1,13→1,25 / 3,42→3,61 / 3,49→3,55 (2010-14 / 2015-19 / 2020-23 / 2024-26), DD máx. más bajo en los 4 bloques, $ +2-18%. PF casi igual (−0,02 en 2024-26). Los otros 3 (CA04V, GD03, ENG26) perdían en 2010-14.
- **Monitor de borde recalibrado** para el default (`monitor_recal3.py`): k 0,0899, h 26,93, aviso 9,22. Falsa alarma 0% en 1 año / 0,2% en 3; edge muerto detectado en ~247 días (mediana), edge negativo en ~137.
- **Presets** `Mffu50KLadder` (toda la receta de la escalera en un solo ajuste) y `Lucid150K` (eval 6c con stop diario $4.050; fondeada 3c, risk cap $300 bajo $1.687, retiro a $6.000): menos ajustes a mano = menos errores.
- **Calendarios verificados** contra la Fed y el BLS hasta fin de 2027 (`calendar_check_2026-10-19.md`): 2 fechas viejas de minutas FOMC corregidas, decisión FOMC 14:00 agregada al apagón. Identificadores que NinjaTrader podía rechazar (`from`, `on`) renombrados.
- **Alarmas trimestrales** (`forward2027.py`): dos trimestres negativos seguidos = pausa (pasa 0,3% de los años con el edge completo, 55% sin edge); un trimestre negativo = apagar la escalera hasta un trimestre positivo.
- `nt_compare.py` / `parity_check.py --set ultra_d4` para validar el default nuevo en Strategy Analyzer.

### 4. Expectativa honesta 2027 por contrato base (`forward2027.json`)

Edge completo: mes p10 −$465 / mediana $1.964; año p10 $17,7k; drawdown del año p90 $4.150. P(año positivo por contrato) ~100% con el edge completo, 98% con 35% menos, 49% sin edge (moneda al aire). Con 35% menos: mediana del año $19k por contrato, P(trimestre negativo) 14%, P(3 meses negativos seguidos) 16%. La incógnita principal sigue siendo si el régimen post-2020 continúa: en 2010-19 el sistema da Sharpe 0,2-1,2.

### 5. Pendiente en la PC

1. F5 de `NQMaster.cs` y `GoldMaster.cs` (solo verificados con el stub).
2. Strategy Analyzer Ultra 1c 2024-01-01→hoy con el default nuevo, exportar CSV y `python parity_check.py <csv> --set ultra_d4`.
3. Strategy Analyzer con `PropPreset Mffu50KLadder` y `Lucid150K` para revisar la mecánica (los retiros y quiebres no se reproducen).

## ★★★★★★★★★★★★★ 2026-10-17: "quiero $250-300 por día" — mapa de ingresos y plan de cuentas

Pedido: subir el promedio diario a $250-300 con buen win rate, "hacé lo que haga falta"; después: "$200 por día por cuenta, que siga funcionando en el futuro". Respuesta corta: **el sistema por contrato no llega**; a $250-300 por día se llega con **tamaño y cantidad de cuentas fondeadas**, y solo si el edge se mantiene cerca del backtest. Todo lo que sigue es por día **calendario** (365 días), neto de comisiones, fees de evaluación y reparto 90/10 de las firmas. Las simulaciones por cuenta (secciones 2 y 2b) llevan además 1 tick extra por lado.

Scripts en `research/mine/`: `income_map.py` (por contrato), `seats_plan.py` + `seats_tables.py` (por cuentas), `ladder_plan.py` (escalera de tamaño por cuenta), `reentry_lab.py` (segundo intento tras stop), `families8.py` + `b8_select.py` (familias nuevas).

### 1. Qué da un contrato base hoy (`income_map.json`, NQ real 2020-10 a 2026-10)

| Set | $/día edge completo | $/día con −35% | $/mes | Sharpe | DD máx. | Contratos para $250/día (completo / −35%) |
|---|---|---|---|---|---|---|
| Ultra | 72 | 47 | 2.183 | 3,70 | 4.582 | 3,5 / 5,4 |
| Ultra + oro Robust | 80 | 52 | 2.424 | 3,90 | 4.554 | 3,1 / 4,8 |
| Ultra + módulos 6 años | 81 | 53 | 2.465 | 3,99 | 5.008 | 3,1 / 4,8 |
| **Ultra + 6 años + oro Robust** | **89** | **58** | **2.705** | **4,15** | **4.181** | **2,8 / 4,3** |
| UltraQ | 65 | 42 | 1.979 | 3,54 | 4.759 | 3,8 / 5,9 |
| WR70Plus + oro | 59 | 38 | 1.782 | 3,79 | 3.151 | 4,3 / 6,6 |

- Por año, el mismo set (Ultra + 6 años + oro) rinde entre **$57/día (2023) y $238/día (2026)** por contrato. El promedio esconde años flojos.
- Con 1 tick más de slippage por lado: −6%.
- Los módulos de 6 años (`SixYearModules`) y el oro suman +24% de $/día **sin subir el DD** (el oro lo baja: correlación ~0).

### 2. Qué da un conjunto de cuentas fondeadas (`seats_plan_gold.json`)

Simulación de 12 meses por asiento (evaluación → fondeada → retiros → quiebre → nueva evaluación), todos los asientos sobre el mismo camino de mercado (correlados), arranques escalonados 5 días, 400 años bootstrap por período. Reglas: MFFU Rapid EOD 50K preset actual (1c, retiro dejando $4.100; "step-up" = 2c desde $4.000 de colchón), Lucid Flex 50K (eval 2c con stop de ganancia diario $1.350, fondeada 2c, retiro a $4.000), Lucid Flex 150K (eval 6c, fondeada 3c, stop diario $4.050, retiro a $6.000). Topes: MFFU 3 cuentas, Lucid 5 fondeadas.

**Ultra + oro Robust**, $/día calendario, mediana bootstrap 2020-23 / 2024-26 (p10 entre paréntesis):

| Plan | Edge completo | −35% | −50% | P(año negativo) a −35% |
|---|---|---|---|---|
| 1 MFFU 50K 1c | 35 / 61 (10 / 32) | 10 / 24 | 1 / 11 | 27% / 16% |
| 3 MFFU 50K 1c | 105 / 182 (35 / 98) | 31 / 72 | 5 / 33 | 26% / 15% |
| 3 MFFU step-up 2c | 162 / 297 (41 / 125) | 32 / 100 | −3 / 32 | 33% / 20% |
| 5 Lucid Flex 50K 2c | 211 / 266 (103 / 154) | 97 / 133 | 71 / 80 | 13% / 8% |
| 1 Lucid 150K 6c/3c | 66 / 88 (35 / 53) | 33 / 42 | 21 / 23 | 12% / 8% |
| 5 Lucid 150K 6c/3c | 330 / 432 (175 / 279) | 162 / 206 | 106 / 122 | 11% / 8% |
| 3 MFFU 1c + 5 Lucid 50K 2c | 317 / 447 (154 / 271) | 131 / 207 | 84 / 116 | 12% / 9% |
| 3 MFFU 1c + 5 Lucid 150K | 441 / 616 (222 / 381) | 187 / 278 | 114 / 159 | 10% / 7% |

**Ultra + 6 años + oro Robust** (el set recomendado), mismo formato:

| Plan | Edge completo | −35% | −50% | P(año negativo) a −35% |
|---|---|---|---|---|
| 1 MFFU 50K 1c | 43 / 66 (19 / 34) | 16 / 29 | 8 / 13 | 24% / 11% |
| 3 MFFU 50K 1c | 130 / 203 (56 / 104) | 47 / 86 | 24 / 39 | 23% / 11% |
| 3 MFFU step-up 2c | 214 / 325 (77 / 131) | 60 / 117 | 24 / 37 | 27% / 16% |
| 5 Lucid Flex 50K 2c | 232 / 276 (123 / 168) | 118 / 161 | 85 / 87 | 9% / 6% |
| 1 Lucid 150K 6c/3c | 73 / 93 (40 / 60) | 36 / 55 | 25 / 30 | 8% / 4% |
| 5 Lucid 150K 6c/3c | 371 / 472 (202 / 311) | 181 / 272 | 126 / 154 | 7% / 4% |
| 3 MFFU 1c + 5 Lucid 50K 2c | 370 / 484 (194 / 286) | 168 / 241 | 108 / 128 | 9% / 5% |
| 3 MFFU 1c + 5 Lucid 150K | 507 / 682 (274 / 423) | 235 / 353 | 159 / 196 | 7% / 4% |

### 2b. "$200 por día POR CUENTA": escalera de tamaño dentro de la fondeada (`ladder_plan.py`)

Idea: los contratos por módulo suben con el colchón al inicio del día (colchón = saldo − piso del trailing), +1 contrato por cada tramo de colchón hasta un máximo, y se retira solo lo que sobra por encima del colchón que sostiene la escalera. El ingreso por cuenta escala con la ganancia retenida y **se frena solo** si el edge se apaga (a −35% el tamaño medio cae de 2,6 a 1,5 contratos; a −50% vuelve a ~1). Mismos caminos de mercado que arriba, Ultra + 6 años + oro, $/día calendario, mediana bootstrap 2020-23 / 2024-26:

| Política por cuenta | Edge completo: mediana (historia) | P(≥$200/día) | Quiebres/año | Tamaño medio | −35%: mediana | P(año negativo) −35% | −50%: mediana |
|---|---|---|---|---|---|---|---|
| MFFU 50K 1c (hoy) | 45 / 68 (55 / 72) | 0% / 0% | 0.27 / 0.50 | 0.8 | 18 / 28 | 20% / 14% | 6 / 11 |
| MFFU step-up 2c a $4k (deja $6,1k) | 68 / 104 (94 / 119) | 0% / 2% | 0.27 / 0.56 | 1.4 | 22 / 31 | 28% / 18% | 5 / 12 |
| MFFU escalera hasta 3c, +1 por $3k, deja $8k | 97 / 146 (136 / 172) | 3% / 25% | 0.27 / 0.68 | 2.0 | 27 / 42 | 30% / 25% | 0 / 13 |
| MFFU escalera hasta 4c, +1 por $2k, deja $8k | 119 / 154 (177 / 201) | 18% / 33% | 0.73 / 1.95 | 2.4 | 28 / 45 | 32% / 23% | 0 / 12 |
| MFFU escalera hasta 4c, +1 por $3k, deja $11k | 119 / 189 (169 / 221) | 19% / 46% | 0.27 / 0.69 | 2.6 | 29 / 42 | 35% / 28% | -2 / 6 |
| MFFU escalera hasta 4c, +1 por $4k, deja $14k | 107 / 191 (158 / 213) | 10% / 46% | 0.23 / 0.35 | 2.7 | 23 / 55 | 38% / 28% | -2 / 1 |
| Lucid 150K 3c (hoy) | 60 / 87 (75 / 74) | 0% / 0% | 1.51 / 2.04 | 3.0 | 32 / 47 | 9% / 6% | 19 / 28 |
| Lucid 150K escalera 3→4c | 63 / 85 (80 / 76) | 0% / 0% | 1.52 / 2.32 | 3.7 | 33 / 45 | 10% / 6% | 19 / 21 |
| Lucid 150K escalera 3→5c | 61 / 80 (74 / 74) | 0% / 0% | 1.41 / 2.21 | 4.3 | 27 / 39 | 13% / 10% | 18 / 22 |

- **Respuesta:** $200/día por cuenta se alcanza solo con el edge completo y la escalera hasta 4 contratos en MFFU 50K, y recién **desde el segundo año** (el primer año arranca de cero colchón). Revisión adversarial (`redteam_2026-10-17.md`, M1-M4, con blackout de noticias, tick extra en oro y haircut de eval corregidos): primer año $110-160/día (2020-23 / 2024-26), régimen estable (años 2-3) $197-232/día con 45-64% de los años ≥ $200; con 35% menos edge $47-53 el primer año y $84-86 en régimen, con 2-4 cuentas perdidas por año. **La escalera amplifica lo que haya** (más ingreso si el edge sigue, más años negativos si se apaga).
- **Sesgo de selección (H3):** los parámetros de la escalera se eligieron viendo los dos períodos. Elegidos solo en 2020-23 saldría "+1 por $2k, deja $8k": en 2024-26 da 15-19% menos y **2,8× más quiebres** (1,95 vs 0,69 por año). Dejar $11k está calibrado al peor día de 2024-26 (−$2.572 por contrato, −$10,3k a 4 contratos): un día 10% peor que el máximo de la muestra quiebra la cuenta y los $11k retenidos. Los módulos de 6 años (elegidos en 2020-23) y el oro (elegido en CFD 2020-23) tampoco son fuera de muestra: descontarlos deja la escalera en $163-217/día en régimen.
- Lucid 150K no escala: los retiros están topeados ($3.000 por retiro, 5 retiros) y a 3 contratos ya quiebra 1,5-2 veces por año. Pasar a cuenta real ("go live") cierra las sim en Lucid y en MFFU fusiona las 3 cuentas a discreción de la firma: no está modelado (±5-15%).
- Implementado en NQMaster (grupo 07, opcional): `FundedLadderStep` (0 = apagado) y `FundedLadderMax`. Receta MFFU: preset `Mffu50K` o `Manual`, `FundedStepUpCushion` 3000, `FundedStepUpContracts` 2, `FundedLadderStep` 3000, `FundedLadderMax` 4, `FundedPayoutAt` 11600 (deja $11.100), `MaxOpenContracts` 30. Con la escalera prendida el preset ya **no** pisa `FundedPayoutAt` (antes lo bajaba a $6.600 y la cuenta casi nunca llegaba a 4 contratos: $123-145/día en vez de $197-232; H1 de la revisión). Backup `NQMaster_backup_pre_ladder.cs`, stub OK, **falta F5**. La superficie es plana en dólares (tramos de $2-4k, retención ±$2k) pero no en quiebres.


- **Edge cero** (solo suerte y economía de las firmas): todos los planes dan mediana negativa (−$5 a −$65/día) y 70-90% de años negativos. Las fees se pagan igual.
- La columna "historia" **sobrepesa el medio de cada período** (cada ventana de 12 meses tiene que caber dentro del período): infla el edge 14-17% en 2020-23 y 4-5% en 2024-26 (revisión adversarial, H2). Para un año futuro vale la **mediana bootstrap**, no la historia.

### 3. Lectura y plan

1. **Con el edge completo**, $250-300/día lo dan: 5 Lucid 150K, o 3 MFFU + 5 Lucid 50K a 2 contratos, o 3 MFFU + 5 Lucid 150K (más margen). Con 1-3 cuentas no se llega.
2. **Con 35% menos edge** (el supuesto realista de la auditoría), solo el combo grande (3 MFFU + 5 Lucid 150K, 8 cuentas) se acerca: mediana $190-280/día, p10 entre $0 y $50, 7-10% de años negativos.
3. **Camino sugerido** (en orden, sin saltar pasos; los números con 6 años + oro son parcialmente dentro de muestra, ver sesgo de selección en 2b):
   - Prender `SixYearModules` y `GoldMaster Robust` en todas las cuentas (antes: backtest de paridad en NT, ver sección del 16-oct).
   - Cubrir los 3 asientos MFFU (1c, preset `Mffu50K`).
   - Pasar las Lucid 50K a 150K a medida que se renuevan: cada asiento 150K rinde ~2,5× uno de 50K con 2c y quiebra menos.
   - Recién con 6-8 cuentas fondeadas y 3 meses de P&L real cerca del backtest, considerar el step-up de MFFU.
4. Capital de arranque: ~$1.500-2.500 en evaluaciones por ronda (MFFU $157, Lucid 50K $146, Lucid 150K ~$285); cada quiebre de fondeada cuesta una evaluación nueva y 1-2 meses sin ingreso de ese asiento.

### 4. Qué se investigó hoy para subir el edge por trade (nada pasó)

- **Familias nuevas, lote 8** (`b8_report.md`, 2.856 configuraciones en 16 años de NQ real): ruptura de máximos/mínimos de N días, reversión a la media por z-score al mediodía, continuación de la primera pierna, vela de agotamiento. Cero sobrevivientes; la única que pasa 2020-23 (ruptura de 3 días con límite en el nivel) se desarma en 2024-26 y con 4 ticks.
- **Segundo intento tras un stop** (`reentry_report.md`): ORB60/90 y MSEQ ya permiten segundo trade (casi nunca ocurre tras stop); los módulos de reloj no tienen segundo gatillo; reentrar a mercado en la misma dirección pierde (PF 0,87-0,96); dar vuelta la posición gana en 2024-26 pero no en 2020-23 y bloquea 16-30% de entradas base. **Único candidato: VOLB re-armado** (mismos niveles, cualquier lado, antes de las 15:00): 181 trades, PF 1,52 / 1,32, +$58/mes por contrato, Sharpe sube en los dos períodos, 2015-19 positivo, pero DD máximo +6% (límite +5%). Queda como **`VolbReArm` opcional, apagado** (grupo 02). Backup `NQMaster_backup_pre_volbrearm.cs`, stub OK, **falta F5**.

### 2c. Escalera + stop diario por contrato y lectura en régimen (`ladder_stop.py`, ventanas de 36 meses, bloques de 21 días, 300 caminos)

MFFU 50K, Ultra + 6 años + oro, $/día calendario, mediana bootstrap 2020-23 / 2024-26; "y1" = primer año, "y2-3" = años 2 y 3 (régimen):

| Política | Edge completo y1 | y2-3 (p10) | P(y2-3 ≥ $200) | Quiebres/año | −35% y2-3 (p10) | Quiebres/año −35% |
|---|---|---|---|---|---|---|
| 1 contrato (hoy) | 43 / 67 | 64 / 86 (44 / 65) | 0 / 0% | 0,16 / 0,27 | 33 / 44 (11 / 18) | 0,83 / 1,44 |
| Escalera hasta 4c, +1 por $3k, deja $11,1k | 133 / 199 | 220 / 265 (138 / 168) | 64 / 76% | 0,12 / 0,61 | 91 / 103 (24 / 27) | 0,72 / 1,65 |
| **Ídem + stop diario $1.500 por contrato** | 129 / 196 | 214 / 288 (136 / 207) | 61 / 92% | 0,09 / 0,19 | 96 / 125 (20 / 40) | 0,73 / 1,20 |
| Escalera elegida solo en 2020-23 (+1 por $2k, deja $8,1k) | 134 / 184 | 184 / 209 (114 / 125) | 42 / 54% | 0,54 / 1,79 | 78 / 75 (20 / 16) | 1,50 / 2,94 |
| Escalera hasta 3c, deja $8,1k | 101 / 148 | 165 / 205 (99 / 127) | 23 / 55% | 0,16 / 0,45 | 72 / 84 (19 / 25) | 0,80 / 1,64 |

- El stop diario de **$1.500 por contrato por módulo** (cuenta entera, realizado + abierto) recorta el peor día de −$10,3k a −$6k a 4 contratos: quiebres 0,61 → 0,19 por año en 2024-26 con el mismo ingreso; $1.000 y $2.000 no ayudan. A 1 contrato es neutro (coincide con lo visto el 3-oct).
- Implementado: `DailyLossPerContract` (grupo 03, 0 = apagado; 1500 con la escalera; multiplica los contratos por módulo fijados al inicio del día; se evalúa en `PropDailyCheck` sobre la cuenta entera, realizado + abierto, y en backtest usa el extremo adverso de la vela). **Receta MFFU completa** (revisión de código 2026-10-17, `research/mine/code_review_2026-10-17.md`): NQMaster preset `Mffu50K`, `SixYearModules` true, `FundedStepUpCushion` 3000, `FundedStepUpContracts` 2, `FundedLadderStep` 3000, `FundedLadderMax` 4, `FundedPayoutAt` 11600, `DailyLossPerContract` 1500, `MaxOpenContracts` 30; GoldMaster Robust con `FundedStepUpCushion` 3000, `FundedStepUpContracts` 2, `FundedLadderStep` 3000, `FundedLadderMax` 4 (la investigación escala el oro junto con el NQ; GoldMaster ahora tiene la misma escalera). Stub OK, **falta F5**.
- Salvedades de la revisión de código: (1) el tope de 30 micros recorta entradas en ~1-4% de los días a 4 contratos (lotes abiertos p99 32, máx. 44) y justo en días de tendencia: mirar la línea "entries cut" del panel en la corrida de NT y comparar con `FundedLadderMax` 3; (2) el Strategy Analyzer no reproduce la escalera (sin retiros ni quiebres el colchón crece y se queda en 4 contratos): la corrida en NT verifica la mecánica, no el ingreso; (3) pedir los retiros después del cierre de las 16:00, porque el tamaño del día se fija al inicio con el colchón de ese momento; (4) corregido: las órdenes que vienen del histórico al pasar a tiempo real se redimensionan al tamaño del colchón real (antes salían con el tamaño del backtest), el stop por contrato ya no cambia la conducta de `DailyLossLimit` (sigue siendo solo realizado), `FundedPayoutAt` nunca queda por debajo del tope de la escalera + $2.600 con el preset, `VolbReArm` solo con VOLB 2R y sin remanente trabajando. Backups `NQMaster_backup_pre_review17.cs`, `GoldMaster_backup_pre_ladder.cs`.

### 2d. ¿Y si el edge se apaga? (`ladder_decay.py`, 36 meses, 300 caminos, MFFU 50K, Ultra + 6 años + oro)

El recorte de edge **crece dentro de la ventana** (0% al inicio → 100% al final) en vez de ser constante. Total neto de 3 años (mediana / p10) y cuentas perdidas en 3 años, 2020-23 / 2024-26:

| Escenario | 1 contrato | Escalera 4c + stop $1.500/contrato |
|---|---|---|
| Edge completo constante | $61,7k / $87,1k (p10 45k / 64k), 0,5 / 0,9 quiebres | **$205k / $273k** (p10 141k / 188k), 0,3 / 0,7 |
| −35% constante | $30k / $40k, 2,4 / 4,8 | $91k / $110k (p10 29k / 33k), 2,1 / 3,4 |
| Se apaga en 3 años | $25k / $28k | $67k / $92k (p10 15k / 23k) |
| Se apaga en 18 meses | $8k / $13k (p10 −2k / −1k) | $21k / $28k (p10 −4k / −5k) |
| Se apaga en 6 meses y queda en cero | −$1,8k / −$1,3k (solo fees) | −$4,1k / −$2,1k (solo fees) |

- En ningún escenario la escalera pierde más que el contrato fijo salvo ~$2k de fees cuando el edge muere rápido: el colchón retenido que se pierde es ganancia de la propia cuenta, no capital propio. La escalera es una **opción sobre el edge**: cobra mucho más si sigue, y si se apaga pierde lo mismo que la cuenta chica (las fees).
- Lo que sí cambia con un edge que muere es la cantidad de evaluaciones compradas (3-7 en 3 años a −35% o peor): ahí es donde manda la regla de pausa del runbook (P&L real por contrato < 0 a los 60 días, o alarma del monitor).

### 4b. Revisión adversarial (`research/mine/redteam_2026-10-17.md`)

Conclusiones que sobreviven: "$250-300/día necesita ~8 cuentas fondeadas" (con edge completo mediana $290-460/día; con −35% solo 3 MFFU + 5 Lucid 150K llega, y la mitad de las veces: $192-264 con Ultra + oro, $236-326 con 6 años) y "$200/día por cuenta solo con la escalera MFFU y el edge completo" (desde el año 2, en el mercado 2024-26, y sin que el preset pise el retiro). Arreglado: H1 (preset). Pendiente de modelar: blackout de noticias MFFU (1,5-7% del P&L), tick extra en oro, haircut de la eval ×8 (10-12% chico), "go live", tope de 30 micros (~1% a 4 contratos), años de 252 días = 373 calendario (+2%).

### 5. Lo que no se puede prometer

- Probabilidad de que un conjunto de 8 cuentas promedie ≥ $250/día en un año: ~93-99% con el edge completo, ~35-60% con 35% menos edge, ~1-4% sin edge.
- Probabilidad de que una cuenta MFFU con escalera promedie ≥ $200/día: ~45-64% en régimen con el edge completo (primer año menos), ~0-6% con 35% menos.
- El edge es un régimen post-2020 (`db_long.json`). Si se apaga, las cuentas se queman pagando fees: el monitor de borde y la revisión anual siguen siendo obligatorios.


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

## ★★★★★ 2026-10-13 (night): ONE eval, no second purchase, >= 70% pass (English) — READ THIS FIRST

Scripts: `research/mine/single70.py` (wide grid of 22,000 settings; its Bulenox rows wrongly allowed running without the mandatory DLL, and its "robust" view mixed periods, so do not use it for decisions) and **`research/mine/single70b.py`** (the clean protocol) -> `single70b.json`. Each setting is chosen on 2020-23 starts and checked on 2024-26 starts. It runs on real Databento NQ futures, at 1 contract, with $1.90 + 1 tick per side. Each start is a single attempt with no restarts. "Within N days" counts listed trading days.

**The answer.** One eval passes more than 70% of the time when it is allowed to run **without a deadline** on a **50K account** at **1 contract** (Lucid, Bulenox and MFFU evals have no time limit). The winning setting, chosen on 2020-23 alone, is **profile WR70Plus with an account daily stop of $900** (on Bulenox, its own $1,100 DLL). The pass comes later, not faster: the median is ~37-40 trading days.

| One eval, 1 contract | Pass within 1 month / 2 months / 3 months / 6 months, 2020-23 | Same, 2024-26 | 90% interval (6 months, 2024-26) | 35% weaker edge (6 months, 2020-23 / 2024-26) | Bust |
|---|---|---|---|---|---|
| **Bulenox Opt2 50K, WR70Plus, DLL $1,100** | 14 / 54 / 71 / **89%** | 14 / 46 / 65 / **83%** | 67-94 | **67% / 65%** | 2.5% / 16% |
| **Lucid Flex 50K, WR70Plus, EvalDailyStop $900** (+ profit stop $1,350 for the 50% rule) | 13 / 54 / 71 / **88%** | 15 / 47 / 65 / **77%** | 64-93 | 65% / 63% | 7.5% / 22% |
| Lucid Pro 50K, WR70Plus, EvalDailyStop $900 | 13 / 54 / 71 / **88%** | 14 / 47 / 65 / **77%** | 64-93 | 65% / 62% | 7.5% / 22% |
| MFFU Rapid EOD 50K, WR70Plus, EvalDailyStop $900 (+ $800 profit stop) | 10 / 52 / 72 / **90%** | 13 / 44 / 63 / **77%** | 64-93 | 64% / 63% | 6.5% / 22% |
| Lucid Flex 50K, Ultra, no stop (faster alternative) | 24 / 60 / 74 / 83% | 31 / 68 / 73 / 75% | 65-90 | 57% / 54% | 17% / 25% |
| Bulenox Opt2 50K, Ultra (faster alternative) | 24 / 60 / 75 / 84% | 31 / 67 / 73 / 78% | 67-93 | 66% / 60% | 16% / 22% |

- **Within one month, a single eval stays at about 50% in every setup tested.** Even the best 2020-23 choice falls to 43-53% on 2024-26. The trade-off is time: the patient WR70Plus setting needs ~2 months and passes most often.
- The 25K accounts are worse for a single attempt (about 50-60% on 2024-26 at any horizon): their target is close to the drawdown. Their advantage is speed with restarts (section below).
- Risk-cap or Estable gearing chosen on 2020-23 for 25K accounts did not hold on 2024-26, so it is not recommended.

**Settings (NQMaster, PropMode = Eval, Contracts = 1, AdaptiveSize false):**
- Lucid Flex 50K: Profile **WR70Plus**, PropPreset **Lucid50K** (target 3,000, DD 2,000, 50% consistency, profit stop 1,350), then **EvalDailyStop 900** and **NightOnWr70 = true** (the tested WR70Plus set includes the night fades NF05 / LF06 / LF0430; the code default is false).
- Lucid Pro 50K: as above, but set ConsistencyPct 0 and EvalProfitStop 0 after the preset (set PropPreset Manual and enter them by hand).
- Bulenox Opt2 50K: PropPreset Manual, StartBalance 50000, PropTrailingDD 2500, ConsistencyPct 0, EvalTarget 3000, EvalProfitStop 0, EvalRiskCapCushion 0, **EvalDailyStop 1100** (Bulenox applies its own $1,100 DLL; NQMaster just stops at the same level). Bulenox allows automation only if it is your own strategy on your own accounts.
- MFFU Rapid EOD 50K: PropPreset **Mffu50K** (target 3,000, DD 2,000, 30% consistency, profit stop 800), Profile WR70Plus, NightOnWr70 true, **EvalDailyStop 900**.
- Every WR70Plus setting above: **NightOnWr70 = true** (Bulenox too).
- GoldMaster: off in the eval (not part of this test).
- Let it run: no deadline, no reset. Check the edge monitor weekly.

## ★★★★ 2026-10-13 (later): 75-90% funded within one month — the route (English) — READ THIS FIRST

Script: `research/mine/month80.py` -> `month80.json`. Real Databento NQ futures, Ultra after the 10-12 overhaul, $1.90 + 1 tick per side. "Within a month" is counted strictly: the funded account must be reached in at most 20 listed trading days, which is about 22 real trading days. The day list skips FOMC and ATR<150 days. Two periods: T1 = starts 2020-03..2023-10 and T2 = starts 2024-01..2026. Nothing was fitted on T2. The 90% intervals come from a block bootstrap with 44-day blocks. "Edge -35%" removes 35% of the mean daily profit, as a realistic forward estimate.

**The route.** Use a **25K evaluation with no consistency rule** (Lucid Pro 25K or FundedNext Rapid Pro 25K). Run **2 contracts per module** in the eval, and **buy a new eval the day after any bust**. The 2 contracts double the speed toward the small $1,250-1,500 target. A bust only costs $80-125 and one day, and with no consistency rule nothing slows the pass down.

| Setup | Funded within a month, T1 / T2 | 90% interval T1 / T2 | Edge -35%, T1 / T2 | Evals bought (T2) | Fees (T2) |
|---|---|---|---|---|---|
| **Lucid Pro 25K, eval 2c + restarts** | **89.9% / 92.5%** | 83-95 / 90-97 | **83.3% / 89.1%** | 2.4 | $294 |
| **FundedNext Rapid Pro 25K, eval 2c + restarts** | **87.1% / 91.4%** | 78-93 / 88-97 | **80.5% / 81.8%** | 2.5 | $196 |
| Lucid Flex 25K, eval 2c + restarts | 85.6% / 90.4% | 81-95 / 87-97 | 73.9% / 85.0% | 2.4 | $212 |
| Bulenox Opt2 25K, eval 3c + restarts | 88.0% / 89.9% | 81-93 / 86-96 | 74.2% / 69.4% | 2.1 | $374 |
| Lucid Pro 50K, eval 4c + restarts | 87.1% / 91.4% | 78-93 / 88-97 | 80.6% / 81.8% | 2.4 | $469 |
| Lucid Pro 25K, eval 1c + restarts | 71.7% / 75.0% | 60-82 / 66-88 | 57.4% / 67.2% | 1.7 | $208 |
| Lucid Flex 25K, eval 1c + restarts | 64.6% / 68.6% | 54-76 / 59-83 | 53.3% / 54.5% | 1.8 | $156 |
| MFFU Rapid EOD 50K, eval 1c + restarts | 19.6% / 29.6% | | 13.6% / 21.0% | 1.2 | $190 |

**One eval on its own** (no restart) peaks at about 50-55% within a month in every setup: Bulenox 25K 1c 54.7/53.3, Lucid Pro 25K 1c 54.0/49.9, Lucid Pro 25K 2c 44.8/44.0. A single attempt is limited by the size of the edge, about $90-120 per day per contract against a $1,000 drawdown. Going above that takes the restart protocol, and with restarts 2 contracts is better than 1. Contracts above 2 on a 25K account do not help Lucid. Bulenox needs 3 contracts because its target is $1,500 with a $500 DLL.

**How to run it (preset `LucidPro25K` or `FundedNext25K`, group 07, PropMode = Eval):**
- The preset sets: balance 25,000; trailing DD 1,000; consistency 0; target 1,250 (Lucid Pro) or 1,500 (FundedNext); **Contracts 2**; no eval profit stop; no eval risk cap; MaxOpenContracts 20. Profile: **Ultra**. GoldMaster: off in the eval, because its fixed $2,000 DD does not fit a 25K account.
- At checkout, choose **no daily loss limit** (Lucid Pro offers a no-DLL add-on). 2c Ultra can briefly hold up to about 20 micros. Lucid Pro 25K allows 20 micros in the eval, so MaxOpenContracts 20 is the guard.
- **Bust -> buy the next eval the same evening and start it the next session.** This step is what produces the 90%. Waiting days between evals loses most of the gain.
- When it passes, set PropMode = Funded. The same preset then sets the funded account to **1 contract**, a $150 per-contract risk cap below a $500 cushion, payout request at $1,500 profit, and no step-up. Funded income at 1 contract on a 25K account is about $670-700 per month per seat (earlier study `smallacct_life2.py`, Lucid Flex 25K). The money comes from stacking seats: Lucid allows 5 funded accounts.
- Budget: about 2.4-3.5 evals per funded account, $200-400 in fees.

**Caveats.**
- The edge was assembled with 2020-26 in view. The 35% haircut rows are the planning numbers: 80-89% for Lucid Pro 25K and FundedNext 25K.
- The rules were checked in October 2026 (Lucid Pro: no eval consistency, 25K target 1,250, DD 1,000 EOD; FundedNext Rapid Pro: no consistency, target 1,500, DD 1,000). Re-check them before buying.
- NQMaster.cs changed: new presets LucidPro25K and FundedNext25K (`patch_preset2.py`, backup `NQMaster_backup_pre_preset2.cs`). It passes the stub compile; **press F5 on the PC**.

## ★★★ 2026-10-13: the fastest route to a funded account at 1 contract (English) — READ THIS FIRST

Scripts: `research/mine/smallacct_build.py`, `smallacct_eval.py`, `smallacct_protocol.py`, `smallacct_haircut.py`, `smallacct_g.py`, `smallacct_life.py`, `smallacct_life2.py`, `smallacct_mffu.py`, `smallacct_timing.py`, `smallacct_conc.py`, `smallacct_profiles.py`. Data: real Databento NQ futures, Ultra after the 10-12 overhaul, 1 base contract per module, $1.90 + 1 tick per side. "Start days": every trading day of 2020-03..2023-10 (T1) and 2024-01..2026 (T2); nothing was fitted on T2.

**The finding.** What decides "funded within a month" at 1 contract is the account size and what you do after a bust. A 1-contract Ultra earns about $90-120 per day whatever the account. A $25K account asks for $1,250-1,500 profit; a $50K account asks for $3,000. So the 25K target is reached in about half the time, and a bust costs $80-175, not a month.

| Setup (all with serial restarts: a bust is followed by a new eval the next day) | Eval fee | Single eval passed in 22 d | **Funded within 22 trading days** | within 33 d | Evals bought | Fees |
|---|---|---|---|---|---|---|
| **Lucid Flex 25K** | $89 | 53% / 50% | **72% / 73%** | 84% / 88% | 1.7 | $155 |
| Lucid Pro 25K | $123 | 55% / 54% | 68% / 69% | 80% / 81% | 1.5 | $183 |
| Bulenox Option 2 25K | $175 | 58% / 54% | 64% / 67% | 78% / 82% | 1.3 | $227 |
| FundedNext Rapid Pro 25K | $80 | 50% / 50% | 63% / 56% | 79% / 67% | 1.5 | $118 |
| Tradeify Select 25K | $109 | 46% / 45% | 57% / 52% | 73% / 64% | 1.5 | $165 |
| Lucid Flex 50K | $146 | 27% / 37% | 30% / 44% | 50% / 66% | 1.2 | $170 |
| MFFU Rapid EOD 50K | $157 | 21% / 30% | 23% / 33% | 44% / 47% | 1.1 | $171 |
| Bulenox Option 2 50K | $175 | 27% / 37% | 30% / 42% | 50% / 62% | 1.1 | $184 |

Each cell is 2020-23 / 2024-26. Tradeify must not run the same bot as another firm (their rules), so it is listed only for completeness.

**Independent review (`research/mine/redteam_smallacct.md`): the simulator is exact (rebuilt from scratch, 0.0-point mismatch) and all three findings survive, but the headline levels are about 3 points too high.** The study counted a pass on day 23 as "within 22 days" (+1.7 to 2.3 points) and the day list omits FOMC and ATR < 150 days (+0.7 to 1.6 points). Strict 22 trading days, Lucid 25K vs 50K: **2024-26 69.8% vs 41.2%** (table says 72.8 vs 44.3), **2020-23 68.1% vs 27.2%**; with +1 tick 69.1 / 39.5 and 65.3 / 25.8. The 95% interval on the 25K level is about 58-84% (few independent starts: 24-44 per period); the 25K-minus-50K gap is +28 points in 2024-26 (CI +17 to +40) and +42 in 2020-23 (+32 to +54). The strategy itself was built with 2020-26 in view, so 2024-26 is not out-of-sample for the edge: **a realistic forward estimate for Lucid 25K is about 55%** (35% edge haircut: 54-56% vs 19-27% on 50K). Rule sensitivity on 25K: target $1,500 -6 to -8 points, no consistency +6, +2 ticks -1.5 to -4.5, drawdown $900/$1,100 +-1. The profit stop is a plateau: use 0.8-1.0 x consistency x target (50K: $1,200-1,500; 25K: $500-625). Not quantified: the Lucid rules come from third-party summaries, and a 25K funded account has a $1,000 drawdown, a $1,000 payout cap and a 10-micro limit.

**Realistic expectation (edge cut by 35%, +1 tick, `smallacct_haircut.py`):** funded within 22 days is Lucid Flex 25K 56% / 58%, Lucid Pro 25K 59% / 70%, FundedNext 25K 54% / 61%, against Lucid 50K 20% / 29% and MFFU 50K 15% / 23%. With the edge gone entirely the 25K still gets there 33-38% of the time, because the restarts are cheap and the target is small; that is luck, not edge, and it costs fees. The ranking 25K ≫ 50K holds at every edge level.

**Income per seat is a different question** (12-month lifecycle, eval with restarts → funded → payouts → bust → new eval; net of fees, `smallacct_life2.py`, `smallacct_mffu.py`). $ per month, 2020-23 / 2024-26:

| Seat | Backtest edge | 35% less edge | Accounts lost per year (2024-26) |
|---|---|---|---|
| Lucid Flex 25K | $706 / $672 | $403 / $407 | 7.4 (fees $89 each) |
| Lucid Flex 50K | $861 / $1,043 | $433 / $620 | 2.0 |
| Lucid Pro 50K | $766 / $859 | $408 / $443 | 1.7 |
| MFFU Rapid EOD 50K, 1 contract, cap $300 below $2,000 | $1,029 / $1,538 | $484 / $774 | 0.5 |
| MFFU Rapid EOD 50K, step-up to 2 contracts from a $3,000 cushion | $1,611 / $2,139 | $655 / $1,107 | 0.7 |

MFFU pays best because payouts are uncapped and daily. Lucid caps each payout at $1,000 (25K) or $2,000 (50K). At 60% less edge every seat is close to break-even: the system needs a real edge.

**Settings (new property `Account preset` in group 07, applied with PropMode Eval or Funded):**

| Preset | Eval | Funded |
|---|---|---|
| Lucid25K | balance 25,000, drawdown 1,000, target 1,250, **profit stop 560**, no risk cap, max 20 contracts | cap $150 below a $500 cushion, max 10 contracts, request payout at $1,500 |
| Lucid50K | balance 50,000, drawdown 2,000, target 3,000, **profit stop 1,350**, no risk cap, max 40 | cap $300 below a $1,000 cushion, max 20, payout at $4,000 |
| Mffu50K | target 3,000, consistency 30%, profit stop 800, no risk cap, max 30 | cap $300 below a $2,000 cushion, max 30, payout at $6,600 |

- Choose Lucid **without** the daily loss limit (DLL off), `Contracts` 1.
- The profit stop that enforces the consistency rule is best at about 0.9 × consistency % × target. The earlier text "700 with 1 contract" was too low: on Lucid 50K it cost about 9 points of 22-day pass rate (28 / 43% at $1,350 against 20 / 33% at $700).
- **On a 25K account the default risk cap (active below a $1,200 cushion) is always on, because the whole drawdown is only $1,000. A $300 cap that is always on cuts funded-within-a-month from 73% to 67% on Lucid 25K (a $150 cap: to 14%).** The preset turns it off in evals. Never use the 50K defaults on a 25K account.
- GoldMaster is not part of the 25K plan: its trailing drawdown is fixed at $2,000.

**The protocol.** Buy the 25K eval. When it busts, buy the next one the next day. Stop at the first pass; the funded account is the one you keep. More seats in parallel (starting 3-5 days apart) add only 2-5 points (Lucid 25K: 73% → 75%) and double the fees, so run one eval at a time per firm. Lucid allows 10 accounts in total.

**Tested and rejected (do not add):**
- Choosing the start day: volatility at the start, or "start after a bad 10 days". The sign flips between 2020-23 and 2024-26 (Lucid 25K, 66% vs 76%).
- A cap on simultaneously open contracts: flat from 6 contracts up, worse below.
- A risk cap or the Estable set in the eval: the same or slower (always-on $300 cap, funded within 22 days on Lucid 50K: 44% → 16%). WR70R is slower on both (Lucid 25K 69% vs 73%, 50K 27% vs 44%); `Ultra` stays.
- The earlier "start evals only when the volatility is low" idea (AtrStartMax) is not supported by this larger sample; leave it at 0.

**Open items.**
- MFFU 25K rules are not documented here; the row marked * assumes the 50K rules scaled (target $1,500, drawdown $1,000, consistency 30%).
- Bulenox allows bots only if you built them yourself and own the accounts; confirm in writing.
- Check that Lucid delivers a new eval account immediately after a bust.
- The 22 "trading days" count only days the strategy trades (no FOMC or ATR < 150 days), so a month is about 22-23.

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
- **Límites de Lucid:** el máximo de contratos abiertos a la vez sería ~20 micros en el peor día (16 en el 99% de los días). Entra en el límite de la evaluación (30) y en el de la fondeada inicial (20). Con 3 contratos se pasaría. **(Desactualizado 2026-10-12:** con los módulos nocturnos y VW13 x2 el máximo validado es 11 MNQ a 1 contrato = 22 micros a 2 contratos; desde 2026-10-12 la propiedad *Max open contracts* (20 por defecto) lo limita.)

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

### ¿WR70Plus con 1 contrato en la fondeada?
La evaluación es la misma (LucidPro 50K, 4 contratos, Ultra) y solo cambia la fondeada. Ingreso por cuenta, promedio y peor de 9 pruebas (`research/mine/funded_wr.py`, `funded_wr.csv`):

| Fondeada | $/mes | Peor | Fondeadas quemadas/año | Retiros/año |
|---|---|---|---|---|
| **Ultra 2c, tope de ganancia diaria $400-500 (recomendado)** | **$1.578-1.605** | $1.238-1.331 | 5,1-5,2 | 11,7-12,5 |
| WR70Plus 2c, tope $400 | $1.291 | $1.130 | 3,0 | 9,6 |
| Ultra 1c, tope $700 | $1.217 | $963 | 1,3 | 8,7 |
| WR70Plus 1c, sin tope | $990 | $813 | 0,7 | 7,5 |

WR70Plus con 1 contrato quema muy pocas fondeadas, pero deja ~38% menos plata: cada retiro tarda más en juntarse. Si lo que importa es el ingreso, va Ultra con 2 contratos y tope de $400-500. Si importa quemar poco, va WR70Plus con 1 contrato (Profile WR70Plus + NightOnWr70, Contracts 1, FundedProfitStop 0; GoldMaster WinRate 1).

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

## ★ 2026-10-09 MFFU vs Lucid playbook (English) — report: https://claude.ai/artifact/16gzpcEvJBHeKWkqTUuoFZ

Current NQMaster logic (2026-10-08 rules) + GoldMaster on REAL MNQ/MGC futures, 2024-02-01..2026-09-25 (657 days), 1 contract, $1.90 + 1 tick per side. Scripts `research/mine/final3y.py`, `final3y_acct.py`, `final3y_haircut.py`; page copy `research/mine/final3y_report.html`.

| Profile (with gold) | WR | PF | Trades/day | $/month | Max DD | Worst month |
|---|---|---|---|---|---|---|
| Ultra + gold Robust | 65.2% | 1.50 | 5.93 | $3,143 | $6,097 | -$3,132 |
| Ultra lean + gold Robust | 65.8% | 1.53 | 5.10 | $2,968 | $5,467 | -$2,897 |
| WR70Plus + gold WinRate | 69.8% | 1.56 | 3.52 | $1,967 | $3,784 | -$2,306 |

Eval at 1 contract (pass % history, median trading days): MFFU Ultra fixed 77% / 21 d, Estable 88% / 27.5 d, WR70Plus 83% / 29 d; Lucid Ultra fixed 78% / 18 d, Estable 89% / 23 d, WR70Plus 83% / 28 d.

Money per account per month (history / +1 tick / resampled; realistic = 35% less edge, resampled):
- **MFFU Rapid EOD 50K, Ultra eval -> Ultra 1c funded, keep $4,100: $2,137 / $1,984 / $2,012; realistic ~$1,050 (recommended).**
- MFFU with step-up (2 contracts from balance $53,100, withdraw above $56,100): $3,888 / $3,592 / $3,336; realistic ~$1,580.
- Lucid Flex 50K, Ultra eval -> Ultra 1c funded: $1,458 / $1,382 / $1,341; realistic ~$780.
- WR70Plus funded earns ~40% less (MFFU ~$1,100-1,240, Lucid ~$800-940).

Settings — MFFU eval: NQMaster Ultra, Contracts 1, PropMode Eval, EvalTarget 3000, PropTrailingDD 2000, EvalCushionFull 0 (or 1200 + EvalSafeSet Estable for max pass), ConsistencyPct 30, EvalProfitStop 800, AtrStartMax 0; GoldMaster Robust 1 (WinRate 2 with Estable), EvalTarget 3000, ConsistencyPct 30, AccountProfitStop 800. MFFU funded: NQMaster PropMode Funded, FundedCushionSafe 0, FundedCushionFull 0, FundedHighFull true, FundedPayoutAt 4600, NewsBlackout true; GoldMaster Robust 1, NewsBlackout true; withdraw down to $54,100. Lucid: same with ConsistencyPct 50, EvalProfitStop / AccountProfitStop 1400, FundedPayoutAt 4000, NewsBlackout false.

### Automatic funded step-up + computed confidence (2026-10-09)

- New properties (NOT compiled yet, F5 on the PC): NQMaster group 07 `FundedStepUpCushion` (0 = off) and `FundedStepUpContracts` (2); GoldMaster group 02 the same two. In PropMode Funded, when the cushion over the EOD-trailing threshold at the session start is >= FundedStepUpCushion, every module trades FundedStepUpContracts; below it, back to Contracts. MyFundedFutures: FundedStepUpCushion 3000 on BOTH strategies (2 contracts from a $53,100 balance), FundedPayoutAt 6600, withdraw down to $56,100. Script: `research/mine/patch_stepup.py`; backups `*_backup_pre_stepup.cs`.
- `research/mine/final3y_conf.py` (600 resampled years x edge haircut 0-100%, prior 10/20/30/20/12/8% on 0/20/35/50/75/100% edge loss): MFFU Ultra 1c P(positive year) 82% (99% with backtested edge), P(>= $1,200/month) 38% (83%); step-up 50% (91%); Lucid 1c 20% (64%); P(>= 80% of backtest) 25% (67% even with a perfect edge). Worst 10% of years about -$120/month per account (eval fees).
- `research/mine/final3y_weak.py`: if the audit-weak modules (ON07, LATEFH, ENG10, MOM1030, MOM13 + 3 gold) or the 2020-only modules are luck, MFFU Ultra still makes $1,315-1,553/month resampled and stays >= Ultra lean and WR70Plus -> keep Ultra.
- `research/mine/nt_compare.py --set ultra_final | ultralean_final | wr70plus_final` compares a Strategy Analyzer export with the current-rule research trades.

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
