# Runbook de operación NQMaster (versión 2026-10-21, ronda 5, para 2026-2027)

Una página. Si algo de acá contradice una sección vieja de `docs/guia/INDICE.md`, manda esta.

## Antes de operar (una vez, y después de cada cambio de código)

1. **F5** en el NinjaScript Editor. Tiene que compilar sin errores. En la nube solo se verifica la sintaxis contra un stub (`bash tools/nt8_stub/check.sh NQMaster.cs`).
2. **Strategy Analyzer**: MNQ, 1 minuto, Profile Ultra, Contracts 1, PropMode Off, desde 2024-01-01 hasta hoy, comisión $1,90 y 1 tick de slippage.
   - Exportá los trades (CSV).
   - Corré `python parity_check.py <csv> --set ultra_d4_mnq` desde `research/mine` (el default desde el 19-oct es Ultra + los 4 módulos de 6 años durables: SO04, RV11, ORFAIL, CAM3).
   - Tiene que decir **PASA**, o fallar solo en ICT y MSEQS por los motivos conocidos (ver "Divergencias abiertas" más abajo).
3. En el Output del backtest no debería aparecer ningún `INACTIVITY ... no SHORT / no LONG`. Si aparece, hay una orden atascada: no operes.
4. **Days to load = 120 fijo en todas las cuentas NQ** (antes ≥ 45; oro, GoldMaster ≥ 120). Motivo (medido 2026-10-26): el ATR diario de NQMaster es un suavizado de Wilder (`atrDaily = ((k−1)·atrDaily + TR)/k`, k = 14) que arranca desde el primer día cargado y depende del inicio para siempre: dos corridas que empiezan con dos meses de diferencia difieren en los stops y targets de 36 de 62 trades iguales y en 20 de 74 trades sobre la misma ventana. La investigación usa el mismo EMA pero desde 2020. Con 120 días (~84 RTH) el peso del arranque es (13/14)^70 ≈ 0,6 %; con 45 días (~31 RTH) es ~28 %. La tendencia (SMA de 20 cierres, mínimo 15) y el volumen de RV11 (20 días) también necesitan ≥ 20 RTH. Comparaciones entre corridas del Analyzer: mismo inicio exacto.
5. **Antes de comprar cualquier cuenta (ronda 5, 21-oct; obligatorio):**
   - F5 sin errores (los cambios del 21-oct solo pasaron el stub).
   - Strategy Analyzer 2024-01..2026-10 con Ultra, Contracts 1, PropMode Off, y `python parity_check.py <csv> --set ultra_d4_mnq`: tiene que pasar G1-G4 (o fallar solo en ICT y MSEQS por los motivos conocidos).
   - Una corrida por preset: Lucid150K en Eval y en Funded, Mffu50K en Eval y en Funded. Leé en el Output las dos líneas `preset ...` (contratos, retiro, grupo de cobertura, apagón de noticias) y el contador de cortes por `MaxOpenContracts` (líneas `size N -> M (max open contracts ...)`). Si los cortes pasan ~1% de los días, avisame antes de operar.
   - Playback con 2 cuentas del mismo HedgeGroup (una con el risk cap activo y otra sin cap) para probar la guarda entre cuentas: no tiene que aparecer nunca una posición opuesta al mismo tiempo.
   - Confirmaciones por escrito: Lucid (¿pasar a Live cierra las otras cuentas sim? art 16558826; ¿LucidLive permite bots?), MFFU (Live / Builder; ¿los 4 días mínimos exigen un trade por día?).
   - Paridad del 27-oct (v4.3): contra el set sobre MNQ (`--set ultra_d4_mnq`) G1 98,5 %, G2 −1,6 %, G3 0,981, todos los módulos ≥ 90 %; contra el set de campaña sobre NQ (`--set ultra_d4`) G1 94,1 % y **ICT 89,5 %, MSEQS 81,5 %, RV11 67,7 % quedan "paridad pendiente respecto del set de campaña"** (diferencias de instrumento, no de código). En 164 de 3.161 trades NT entra una barra después que la investigación (orden opuesta trabajando): la investigación es ≈ $31/mes por contrato optimista por eso. Las cifras de abajo son del recálculo del 27-oct con la lista corregida.
6. **Simulación de cuenta (panel nuevo, 21-oct):** una corrida del Strategy Analyzer con el preset de la firma, *Fase REAL de la cuenta* = Eval, *Backtest: simular el ciclo* = true y el precio que pagás por la eval.
   - Leé el bloque SIMULACIÓN DE CUENTA: evals compradas, aprobadas y perdidas, fondeadas perdidas, retiros y resultado neto por mes.
   - Exportá los trades y corré `python3 dash_cycle_ref.py --csv <csv> --preset <preset> --fee <precio>` desde `research/mine`: los conteos tienen que coincidir con el panel, salvo alguna cuenta que el panel da por perdida por la posición abierta en el peor precio de una barra.
   - Si cambia el motor de cuentas (`PropCycle`), correr antes `python3 tools/propcycle_test/run_test.py`: tiene que decir 0 diferencias.
7. **Reloj de barras** (después de cada cambio de horario de verano, EE. UU. y Argentina): en el Output del backtest, los módulos de reloj tienen que entrar a su hora ET exacta (MOM1030 10:30, MOM11 11:00, CRT11 12:00, VW13 13:01, MOM13 13:00, LATE15 15:00, CPI09 09:30). NQMaster convierte desde la zona horaria configurada en NinjaTrader a ET; si la zona de NinjaTrader o de Windows está mal, todo entra corrido. La auditoría de perturbación (`perturb_report.md`, 19-oct) muestra que un desfase de 15 minutos borra la mayor parte del edge de los módulos de reloj (Sharpe −0,3 a −0,7 por módulo).

## Configuración por cuenta (plan de la ronda 5, 21-oct; solo NQ, sin GoldMaster)

Plan base: **5 Lucid Flex 150K + 3 MFFU Rapid EOD 50K**. Todas las cuentas con Profile Ultra (default 2027, `SixYearModules` true). DLL de la firma **OFF** al comprar. Cifras de investigación (arnés `prop_wf` solo NQ, +1 tick, 1.000 caminos; primer número arranques 2020-22, segundo arranques 2023-26 (cortes de `prop_wf`)), con la paridad de NinjaTrader pendiente. Fuentes: `research/mine/integ_paired.json`, `integ_eval_150k.json`, `integ_port.json`, `integ_budget.json`, `integ_ladder.json`, `prop_wf.json`.

| Cuenta | Ajustes | Qué esperar (edge completo / con 35% menos edge) |
|---|---|---|
| **Lucid Flex 150K, evaluación** (5 plazas, el tope de Lucid por hogar) | PropMode Eval · **PropPreset Lucid150K**. El preset pone: saldo 150.000, trailing 4.500, consistencia 50%, objetivo 9.000, stop de ganancia diario 4.050, 6 contratos, sin multiplicador ×8, máximo 100 contratos abiertos, grupo de cobertura LUCID, y apaga restos de plantillas viejas. Una eval por plaza; si se quema, otra al día siguiente. | Fondeada en ≤22 días hábiles usando hasta 3 evals: 69 / 71% (con 35% menos: 54 / 51%; sin edge 30 / 31%). Una sola eval: 43 / 44%. Fees esperados del plan de 22 días: ~$380 / $402 (a $215 por eval con cupón). |
| **Lucid Flex 150K, fondeada** | PropMode Funded · PropPreset Lucid150K: 3 contratos, risk cap $300 por debajo de $1.687 de colchón, aviso de retiro a $6.000 de ganancia, máximo 40 contratos abiertos, sin escalón ni escalera. **Retiro:** con ganancia ≥ $6.000 y 5 días ≥ $250 en el ciclo, pedí min($3.000, 50% de la ganancia) (el panel lo dice). **Oferta de Live al 5º pago:** antes de aceptar, confirmá por escrito si cierra las otras cuentas sim (art 16558826); si las cierra, aceptá solo con las otras plazas recién retiradas. | Por plaza, mediana $2.417 / $2.242 por mes (con 35% menos: $1.378 / $1.342, p10 $370 / $317; sin edge −$70 / −$95). P(año negativo) con 35% menos: 4%. Cobro en ≤62 días hábiles desde la primera eval: 81 / 78% (35% menos: 58 / 59%). Fondeadas quemadas por año con 35% menos: 2,4-3,2. Si la plaza termina a los 5 pagos (sin recompra): $1.063 / $1.053 con 35% menos. |
| **MFFU Rapid EOD 50K, evaluación** (3 plazas, el máximo de MFFU) | PropMode Eval · **PropPreset Mffu50K** · **Contracts 1** (si ponés otro valor, el Output avisa: lo simulado es 1 contrato con MOM1030/CPI09 ×8). El preset pone objetivo 3.000, consistencia 30%, stop de ganancia diario 800, máximo 30 contratos abiertos, grupo MFFU. **Días mínimos (4):** si el objetivo llega antes del día 4, apenas aparece `EVAL TARGET REACHED` **deshabilitá NQMaster en esa cuenta**; los trades simbólicos de 1 MNQ se hacen a mano con la estrategia deshabilitada, solo con las 3 cuentas MFFU planas y solo si la ganancia realizada es ≥ $3.050. Eval nueva al día siguiente de cada quiebre. | Fondeada en ≤22 días hábiles usando hasta 3 evals: 40 / 48% (con 35% menos: 31 / 31%). |
| **MFFU Rapid EOD 50K, fondeada** | PropMode Funded · PropPreset Mffu50K: 1 contrato (forzado), risk cap $300 por debajo de $2.000 de colchón, apagón de noticias de nivel 1, máximo 30 contratos (MNQ + MGC juntos), sin escalón ni escalera. **Retiro:** al llegar a $4.600 de ganancia, retirá hasta dejar $4.100 (el panel lo dice). **Límite de precio CME:** deshabilitá las fondeadas MFFU si el contrato está a menos de 2% de un límite de precio (regla de la fondeada; no está en el código). | Por plaza, mediana $1.388 / $1.184 por mes (con 35% menos: $703 / $510, p10 −$52 / −$92; sin edge −$131). P(año negativo) con 35% menos: 15 / 19%. Cobro en ≤62 días hábiles: 33 / 31% (35% menos: 21 / 17%). Fondeadas quemadas por año con 35% menos: 0,6-1,2. El apagón de noticias no está simulado (−1,5 a −6,8% del P&L). |
| MFFU fondeada con **escalera** (opción, no recomendada el primer año) | PropMode Funded · PropPreset **Mffu50KLadder** (1 → 2 contratos con $3.000 de colchón, +1 cada $3.000 hasta 4, retiro solo arriba de $11.100, stop diario $1.500 por contrato). | Año 1 por plaza: $3.962 / $3.126 por mes contra $1.364 / $1.201 sin escalera; con 35% menos $1.140 / $809 contra $641 / $541, pero la ganancia no es significativa (P 0,63 / 0,58), P(año negativo) 30 / 34% contra 16 / 16% y cobro en ≤62 días 8 / 6% contra 18 / 16% (`integ_ladder.json`). |
| Lucid Pro 50K (alternativa en las mismas 5 plazas de Lucid; **no está en el plan base**) | Si preferís aprobar evals de 50K rápido en lugar de ingreso: PropPreset **LucidPro50K** (eval 4 contratos, objetivo 3.000, sin stop de ganancia; fondeada 1 contrato, stop de ganancia diario $1.000, risk cap $300 por debajo de $1.000). **Retiro:** pedí min(tope, ganancia − $2.100) cuando ese monto sea ≥ $2.000, con ≥ 3 días en el ciclo, ganancia del ciclo ≥ $500 y mejor día ≤ 40% del ciclo; tope $2.000 el primer pago y $2.500 después. No la mezcles con la 150K dentro de Lucid sin probar antes la guarda entre cuentas (los filtros difieren). | Fondeada en ≤22 días con hasta 3 evals: 88 / 84% (35% menos: 73 / 74%); una sola eval 48 / 44%. Por plaza $1.209 / $1.083 por mes (35% menos: $794 / $656; sin edge −$52 / −$110). Contra la 150K: −$654 / −$706 por mes con 35% menos. |
| MFFU Builder 50K (**condicional, fuera del plan**) | Solo si MFFU confirma por escrito que su pase a Live (tras 5 pagos) no cierra las Rapid y si se permite un segundo Builder. Manual: saldo 50.000, trailing 2.000, consistencia 0, objetivo 3.000, `EvalDailyStop` 1000, 3 contratos, máximo 40, HedgeGroup MFFU; fondeada 1 contrato, `DailyLossPerContract` 1000, retiro min($2.000, ganancia − $2.100) cuando sea ≥ $500, máximo 4 pagos hasta la confirmación. | $958 / $835 por mes por plaza (35% menos: $539 / $452), optimista: supone rotación tras 5 pagos. |
| Bulenox Opt1 50K (**condicional**) | Solo con confirmación escrita del cargo de $100/mes por NT8 vía Rithmic, topes y consolidación a Live tras 3 pagos. Manual: saldo 50.000, trailing 2.500 intradía, objetivo 3.000, 4 contratos, máximo 50, HedgeGroup BULENOX; fondeada 1 contrato, aviso de retiro a $3.600. | $855 / $810 por mes por plaza (35% menos: $480 / $444), optimista (sin el cargo mensual). |
| FundedNext Rapid Pro 50K (**desborde**, solo si Bulenox no sirve) | Antes, probar la conexión NT8. PropPreset LucidPro50K en Eval con HedgeGroup FNEXT a mano; fondeada Manual: 1 contrato, retiro min($1.200, ganancia) cada 3 días; la cuenta se cierra a las 5 recompensas. | $612 / $645 por mes por plaza (35% menos: $344 / $331). |

**Plan completo (5 Lucid 150K + 3 MFFU, mismo camino de mercado, escalonadas 5 días), $/mes (recalculado el 27-oct con la lista corregida de paridad e ICT ×1, igual que las filas por plaza de la tabla, `integ_paired.json`; antes entre paréntesis):** edge completo mediana $16.173 / $14.689 (16.280 / 14.739); con 35% menos $8.824 / $8.418 (8.838 / 8.610; p10 $2.464 / $1.801, P(año negativo) 3,9 / 4,2%); sin edge −$789 / −$566 con cupón (−$1.604 / −$1.551 con precio de lista; 56-63% de años negativos).

**Presupuesto por plaza: retirado el 29-oct** (ver el punto 6 de las reglas de pausa y `docs/DECISIONES_2026-10-29.md`). Referencia: en modo anual (−$4.000 Lucid / −$1.500 MFFU, sin volver a comprar en 12 meses) acotaba el p10 sin edge a −$2.095 por mes, pero con −35 % en arranques 2023-26 bajaba el p10 del plan de $1.801 a $1.452.

- **Misma firma = mismo perfil en todas las cuentas.** Lucid y MFFU prohíben posiciones opuestas entre cuentas propias.
- **Todas las cuentas de una firma en la misma PC.** `CrossAccountGuard` solo ve las instancias de esa PC. Los presets ponen el grupo de cobertura por firma (LUCID / MFFU / FNEXT) si `HedgeGroup` está vacío; en cuentas Manual ponelo a mano.

## Cada día (2 minutos)

- Mirá el panel del gráfico: estado, cushion, monitor de borde (% de la alarma) y alertas.
- No hace falta tocar nada. **No apagues módulos a mano por un mal día o una mala semana**: está probado que empeora.

## Qué hacer ante cada alerta

| Alerta | Qué significa | Qué hacer |
|---|---|---|
| `STALE ORDER dropped` | NinjaTrader dejó una orden atascada y el watchdog la descartó. | Nada. Si se repite todos los días, avisame. |
| `INACTIVITY <módulo>` | Un módulo no opera hace más días que su máximo histórico ×1,5. | Revisá Working orders, rechazos y que el módulo no esté apagado. Mandame el Log. |
| `INACTIVITY no SHORT / no LONG` | 12 días hábiles sin entradas en una dirección. El máximo de 2020-26 fue 8. | **Prioridad alta**: es el patrón del bug de 13 meses. Reiniciá la estrategia y mandame el Log. |
| `EDGE MONITOR WARNING` | El resultado viene por debajo del backtest. Pasa por azar 1 de cada 4 años. | Nada obligatorio. Opción defensiva validada (`perturb_report.md`): `DisableModules = MOM1030,MOM13,REV06` (los 3 módulos más frágiles; 2024-26 Sharpe 4,03 vs 4,07, PF 1,52, −12% de ganancia, DD más bajo en 2020-23). |
| `EDGE MONITOR ALARM` | El resultado en vivo ya no es compatible con el backtest. | Automático: un año con el set revisado de módulos. Vos: no abras cuentas nuevas y avisame. |
| `ACCOUNT / STRATEGY POSITION MISMATCH` | La cuenta y la estrategia no coinciden. | La estrategia ya aplanó y se detuvo. Revisá la cuenta en el broker antes de reactivarla. |
| `ROLL DATE` | Faltan 8 días para el vencimiento. | Mové la estrategia al contrato siguiente con los mismos ajustes. |
| `NEWS LIST ends` | Se terminan las fechas de noticias cargadas. | Actualizá el calendario (ver abajo). |
| `another account of group ... holds an opposite NQ position / working entry` o `entry cancelled: another account ...` | La guarda entre cuentas bloqueó o canceló una entrada. | Nada. Es la regla de la firma. |
| `HEDGE GUARD: ... flattened at once` | Una entrada se llenó mientras otra cuenta del mismo grupo tenía la posición opuesta; NQMaster la cerró enseguida. | Revisá las dos cuentas en el broker. Si se repite, mandame el Log de ambas. |
| `CLOCK CHECK: this session ends at HH:MM ET, expected 17:00 ET` | El fin de sesión no cae a las 17:00 ET en un día normal: la zona horaria de NinjaTrader (Tools > Options > General) o el reloj de Windows están mal, y todos los módulos de reloj operarían corridos (15 minutos de error bajan el Sharpe 0,3-0,7). | Deshabilitá NQMaster, corregí la zona horaria o el reloj, reiniciá NinjaTrader y verificá que el aviso no vuelva. Revisalo sobre todo la semana del cambio de horario de EE.UU. |
| Panel: `Si tocan todos los stops abiertos: −$X · colchón que queda $Y` | Lo que perdería la cuenta si todas las posiciones abiertas tocan su stop ahora (sin slippage), y el colchón que quedaría sobre el límite de la firma. Con `ATENCIÓN: alcanza para perder la cuenta`, un stop general quema la cuenta. | Es información, no una orden: el tope de riesgo por contrato ya actúa solo con colchón chico. Si la ATENCIÓN aparece seguido en una cuenta, revisá el tamaño (Contracts) de esa cuenta. |

## Reglas de pausa (preacordadas, no se negocian en caliente)

Pausá un perfil (Enabled = false) si se cumple cualquiera de estas (vigentes: 2 y 3; la 4 es señal de revisión; decisión D6 del 29-oct: **ninguna pausa automática por P&L** porque sin edge la campaña tiene valor esperado positivo por la forma de los retiros y pausar solo cambia media por cola, experimento 07):

1. ~~Después de 60 días hábiles en vivo, el P&L acumulado por contrato base es negativo.~~ **Retirada el 29-oct** (experimento 07, `docs/experimentos/07_reglas_pausa.md`): con −35 % de edge pausaba la campaña en 1 de cada 4 años (P(año negativo) del plan de 4 % a 23-26 %) y con el edge muerto no mejoraba la mediana; con 60 días el P&L no alcanza para distinguir un edge más bajo de uno muerto (hacen falta ~150-200 días).
2. El monitor de borde saltó **y** el año de fallback también termina negativo.
3. `python impl_gap.py <csv de la cuenta real>` da ALERTA de cuenta: los últimos 60 días quedan por debajo del 65% de lo esperado y la diferencia supera 2 errores estándar.

4. **Dos trimestres calendario seguidos con P&L negativo por contrato base → revisión, no pausa automática** (decisión D6 del 29-oct, experimento 07): con la pausa automática el plan rompe el p10 con −35 % en 2023-26 ($1.801 → $1.409) y sobre historia real pausaría el 24-30 % de los arranques de 2023-26 aun con el edge completo; sin edge empeora la mediana ~$500-600 por mes y solo mejora el p10. Cuando se cumple: revisar el P&L por módulo y el monitor de borde con datos, y decidir; no apagar por reflejo.
5. **Un trimestre negativo** no pausa, pero **apaga la escalera** (`FundedLadderStep` 0) hasta cerrar un trimestre positivo: con el edge completo pasa 14% de los años, con 35% menos 46%.
6. ~~Presupuesto por plaza~~ **Retirada el 29-oct** (`docs/DECISIONES_2026-10-29.md`, D2; experimento 05): con reinicio trimestral no actuaba, y las variantes que actúan (anual, "acumula hasta disparar") bajan el p10 del plan con −35 % sin mejorar nada con el edge completo. La protección contra un edge muerto queda en los puntos 1-4, que se validan en el frente 5C.

**Nivel honesto para planificar** (`perturb_report.md`): si cada parámetro del sistema estuviera un ±20% / ±30 min desviado de su celda exacta, el portafolio da Sharpe ~2,5 (p10 1,9-2,1), PF ~1,3 y drawdown ~$5.600 por contrato (p90 $7.400). Planificá cuentas con esos números, no con los de la celda exacta (coincide con el recorte de 35% que ya usamos).

Rangos normales por contrato base en 2027 (edge completo, 2020-26): mes p10 −$465 / mediana $1.964; trimestre p5 +$647; año p10 $17.7k; drawdown del año p90 $4.150. Si el drawdown del año supera ~$6.100 por contrato estás en la zona de 35% menos edge o peor.

**No es motivo de pausa:**

- Un mes negativo. Pasa ~2 meses por año con edge completo y ~3 con 35% menos.
- Una racha de 3 meses negativos. Con 35% menos edge la probabilidad es ~17% por año.

## Calendario (cada diciembre)

- Hoy está cargado así:
  - FOMC: hasta 2028-01-26.
  - CPI y noticias de nivel 1 (CPI, NFP, minutas FOMC): hasta 2027-12-10.
- Para 2028 tenés dos opciones:
  - Cargar las fechas en las propiedades `FomcDates`, `CpiDates` y `NewsTimes` (formato `yyyy-MM-dd` / `yyyy-MM-dd HH:mm`).
  - Pedirme que actualice `BuiltinFomc`, `BuiltinCpi` y `BuiltinNews`.
- Fuentes: federalreserve.gov (FOMC y minutas), bls.gov (CPI y Employment Situation).
- Verificado el 19-oct-2026 (`research/mine/calendar_check_2026-10-19.md`): todas las fechas de FOMC, CPI y NFP hasta fin de 2027 coinciden con la Fed y el BLS. Las minutas FOMC desde nov-2026 son estimadas (regla de 3 semanas): revisar la de 2026-12-30 en diciembre. Si hay cierre del gobierno, el BLS mueve fechas: revisar bls.gov.
- El blackout de noticias ahora también cubre la decisión FOMC de las 14:00 (solo importa si apagás `SkipFomc`).
- Cada enero: pedime que corra `research/mine/robust16.py` y actualice la tabla `FallbackList` del año.
- Lista de vigilancia para la revisión de enero (frágiles en la perturbación o con PF < 1 en 2026): REV06, LATE15, CAM3, LF0430, MSEQ, MOM1030, ON07, CRT11, VW13, ICT. No se apagan por un mal año; se apagan si fallan en la revisión de 5 años normalizada.

## Qué pasa si se cae la PC, la conexión o NinjaTrader

- **Stops y targets viven en el broker**: NQMaster los manda con `SetStopLoss` / `SetProfitTarget` al llenarse cada entrada, así que una posición abierta sigue protegida aunque la PC se apague. Lo que NO se ejecuta sin la PC: las salidas por tiempo (`MaxHold`), el cierre a las 15:55 y el break-even de VOLB. La firma cierra sola a las 16:10 (MFFU) / 16:59 (Lucid), así que el peor caso es una posición que corre hasta su stop, target o el cierre de la firma.
- **Al volver**: arrancá la estrategia en el mismo gráfico con **Days to load = 120** (el ATR de Wilder depende del inicio: ver el punto 4 de "Antes de operar"). NQMaster recupera el inicio del día y el pico de la cuenta desde `nqmaster_prop_<cuenta>.txt`; las órdenes que quedaron en el broker las sincroniza `AccountSyncGuard` (si la cuenta y la estrategia no coinciden, aplana y se detiene: revisá antes de reactivar). Las entradas pendientes de la sesión se cancelan al reiniciar (`SkipShortSessions`), no se re-emiten.
- **Barras que faltan** (minuto sin operaciones o hueco del feed): un módulo de reloj entra solo si existe la barra de su minuto; si falta, ese día no opera. Es el mismo criterio de la investigación (coincidencia exacta del minuto) y pasa en 0,4-1,2% de las sesiones nocturnas. Una barra procesada más de 2 minutos tarde tampoco genera entradas (`LateBar`). No hay que cambiar nada.
- **Dos PCs**: `tools/instalar_en_pc.ps1` instala la misma versión; nunca corras la misma cuenta desde las dos PCs a la vez.

## Cumplimiento (releer antes de cada cuenta nueva)

Detalle con fuentes y fechas en `research/mine/propfirms_check_2026-10-16.md`.

- **Lucid:** bots permitidos. Prohibidos el HFT, el microscalping y el hedging entre cuentas. Máximo 5 fondeadas.
- **Una PC por firma y un HedgeGroup por firma** (LUCID / MFFU; los presets lo ponen). La guarda bloquea entradas opuestas a la posición o a la orden de entrada en espera de otra cuenta del grupo, cancela las propias en espera si otra cuenta abre la posición opuesta y cierra enseguida si igual se llena una opuesta. Hasta pasar el Playback con 2 cuentas, no está probado que nunca haya opuestas.
- **MFFU fondeadas:** deshabilitarlas en los días en que el contrato está a menos de 2% de un límite de precio CME (`propfirms_check_2026-10-16.md`).
- **MFFU:** bots permitidos si son propios. En las fondeadas Rapid/Pro no se puede tener ninguna posición ni orden entre 2 minutos antes y 2 minutos después de CPI, NFP, FOMC y las minutas FOMC (el preset lo hace). Prohibido el hedging. Máximo 3 Rapid 50K. El límite de 30 micros cuenta MNQ y MGC juntos.
- **Apex:** prohíbe la automatización. **Topstep:** solo TopstepX, no NinjaTrader. **No usar ninguna de las dos.**

## Divergencias abiertas (conocidas)

- **Módulos de 6 años (SO04, RV11, ORFAIL, CAM3): paridad cerrada el 27-oct** con v4.3 y el set sobre MNQ (SO04 100 %, ORFAIL 100 %, RV11 96 %, CAM3 92 %); la etiqueta "paridad pendiente" se levanta. Historia del 26-oct, con el export de v4.2 y el set sobre NQ: NinjaTrader toma 41 trades de ORFAIL contra 108 de la investigación (34% emparejado), RV11 29 vs 39 (54%), CAM3 26 vs 32 (56%), SO04 69 vs 67 (89%). Lo que NinjaTrader opera gana más por trade que la regla validada (los 4 juntos: NT $143/mes por contrato, 6,7% del neto; investigación $100/mes, 5,2%), pero no es la regla validada. Aporte de los 4 en la investigación: Sharpe 3,54 → 3,64 en 2024-26 y 3,21 → 3,32 en 2020-23, drawdown igual (±1%), peor mes 2024-26 −$2.279 → −$2.410. **Estado: paridad pendiente (experimento 01, S2); siguen encendidos; al planificar cuentas no contar su aporte.** También fallan G1 (91,0% < 92) y G3 (correlación diaria 0,918 < 0,95) por ellos.
- **ICT:** NinjaTrader llena el retest unos minutos después que la investigación (80-82% emparejado).
- **MSEQS:**
  - En NinjaTrader necesita que ORB60 se haya llenado en short; la investigación usa la señal de ORB60 antes de los filtros (56% emparejado, ~$24/mes a favor de la investigación).
  - Si ORB60 está apagado o bloqueado por el risk cap, MSEQS no opera ese día.
- **Reinicios:** el monitor de borde guarda su estado en `nqmaster_edge_<cuenta>.txt` desde el 2026-10-16. La alarma de inactividad por módulo no se guarda: después de un reinicio solo cuentan las alarmas de dirección (12 días), VOLB y MOM11.
