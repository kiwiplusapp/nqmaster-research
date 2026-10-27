# Reglas de cuentas prop, presets y planes de cuentas

> Parte de `NQMASTER_GUIA.md` partida por tema el 2026-10-26. Texto sin cambios, secciones en el orden original. Índice: `docs/guia/INDICE.md`.

## ★★★★★★★★★★★★★★★★★ 2026-10-21: plan de cuentas (ronda 5)

Pedido de Federico: más pase en evals de 50K, más probabilidad de cobrar por cuenta, más ingreso con buen win rate y poco drawdown, sin overfitting. Solo NQ (sin GoldMaster). Insumos: `research/mine/prop_wf_report.md` (optimizador walk-forward de políticas: ninguna aceptada), `prop_survey_report.md` + `propfirms_2026-10-21.md` (firmas que permiten bots), `b13_report.md` (lote 13: 0 sobrevivientes). Pruebas de integración: bootstrap pareado, 1.000 caminos por corte, fees con cupón y de lista (`research/mine/integ_*.py` / `integ_*.json`). La configuración exacta de cada cuenta está en `RUNBOOK_OPERACION.md`, que manda sobre esta guía.

**Regla fijada antes de correr:** una plaza o eval nueva reemplaza a la actual solo si, con 35% menos edge, en 2020-23 y en 2024-26 y con los dos niveles de fee, la mediana de la ganancia pareada es > 0 con P ≥ 0,80 y su P(año negativo) no empeora más de 3 puntos (MFFU: además no puede perder más de $100/mes extra sin edge). Nada nuevo pasó: **el plan sigue siendo 5 Lucid Flex 150K + 3 MFFU Rapid EOD 50K**.

### Plazas (cifras de investigación, paridad NT pendiente; 2020-23 / 2024-26)

Cifras del recálculo del 27-oct con la lista corregida (`integ_paired.json`; Lucid Pro recalculada en el mismo arnés).

| Plaza | Cantidad | Preset | Fondeada ≤22 días (hasta 3 evals) | $/mes por plaza: edge completo | con 35% menos | sin edge | P(año negativo) con 35% menos |
|---|---|---|---|---|---|---|---|
| Lucid Flex 150K | 5 | `Lucid150K` (eval 6c, fondeada 3c) | 69 / 71% (35% menos 54 / 51%) | 2.417 / 2.242 | 1.378 / 1.342 | −70 / −95 | 3,9 / 4,4% |
| MFFU Rapid EOD 50K | 3 | `Mffu50K` (eval 1c ×8, fondeada 1c, retiro dejando $4.100) | 40 / 48% (31 / 31%) | 1.388 / 1.184 | 703 / 510 | −131 / −131 | 14,6 / 19,3% |
| Lucid Pro 50K (alternativa a la 150K si se prioriza el pase de 50K) | 0 | `LucidPro50K` | 88 / 84% (73 / 74%) | 1.209 / 1.083 | 794 / 656 | −52 / −110 | 2,7 / 6,3% |
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

## Apex 25K: configuración recomendada (2026-09-29)
- **Evaluación:** Profile MaxPlus, AdaptiveSize = false, **Contracts = 4**, EvalTarget = 1500, MaxDrawdown = 0. Pasa ~35% de las veces, en ~2 días de mercado cuando pasa; ~7 días y ~2.8 evaluaciones ($50) por cuenta fondeada.
- **Cuenta fondeada:** Profile MaxPlus, AdaptiveSize = false, **Contracts = 1**. Retirar apenas se cumplan las condiciones de pago.

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

## Evaluaciones de repuesto en paralelo: no conviene (`research/mine/seats_sim.py`)
Lucid permite 10 cuentas en total, pero solo 5 fondeadas. Simulé, día por día, tener 2 o 3 evaluaciones escalonadas por cada lugar libre para reponerlo más rápido. No conviene: todas operan los mismos trades, así que pasan o fallan juntas. Las que pasan sin lugar libre se pierden y se pagan evaluaciones de más. La política actual, una evaluación por lugar libre, rinde 3-25% más que cualquier variante en paralelo.

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
