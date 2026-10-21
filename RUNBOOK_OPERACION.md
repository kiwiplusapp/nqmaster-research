# Runbook de operación NQMaster (versión 2026-10-19, para 2026-2027)

Una página. Si algo de acá contradice una sección vieja de `NQMASTER_GUIA.md`, manda esta.

## Antes de operar (una vez, y después de cada cambio de código)

1. **F5** en el NinjaScript Editor. Tiene que compilar sin errores. En la nube solo se verifica la sintaxis contra un stub (`bash tools/nt8_stub/check.sh NQMaster.cs`).
2. **Strategy Analyzer**: MNQ, 1 minuto, Profile Ultra, Contracts 1, PropMode Off, desde 2024-01-01 hasta hoy, comisión $1,90 y 1 tick de slippage.
   - Exportá los trades (CSV).
   - Corré `python parity_check.py <csv> --set ultra_d4` desde `research/mine` (el default desde el 19-oct es Ultra + los 4 módulos de 6 años durables: SO04, RV11, ORFAIL, CAM3).
   - Tiene que decir **PASA**, o fallar solo en ICT y MSEQS por los motivos conocidos (ver "Divergencias abiertas" más abajo).
3. En el Output del backtest no debería aparecer ningún `INACTIVITY ... no SHORT / no LONG`. Si aparece, hay una orden atascada: no operes.
4. Days to load ≥ 45 (NQ) y ≥ 120 (oro, GoldMaster).
5. **Reloj de barras** (después de cada cambio de horario de verano, EE. UU. y Argentina): en el Output del backtest, los módulos de reloj tienen que entrar a su hora ET exacta (MOM1030 10:30, MOM11 11:00, CRT11 12:00, VW13 13:01, MOM13 13:00, LATE15 15:00, CPI09 09:30). NQMaster convierte desde la zona horaria configurada en NinjaTrader a ET; si la zona de NinjaTrader o de Windows está mal, todo entra corrido. La auditoría de perturbación (`perturb_report.md`, 19-oct) muestra que un desfase de 15 minutos borra la mayor parte del edge de los módulos de reloj (Sharpe −0,3 a −0,7 por módulo).

## Configuración por cuenta (no mezclar perfiles dentro de la misma firma)

| Cuenta | Ajustes |
|---|---|
| MFFU Rapid EOD 50K, evaluación | Profile Ultra · Contracts 1 · PropMode Eval · PropPreset Mffu50K |
| MFFU Rapid EOD 50K, fondeada | Igual, con PropMode Funded. El preset pone el risk cap $300 por debajo de un cushion de $2.000, el pedido de retiro al llegar a $4.600 de ganancia (retirás hasta dejar $4.100) y el apagón de noticias. El escalón a 2 contratos (`FundedStepUpCushion` 4000, retiro a $6.600) es **opcional**: más ingreso mediano si el edge es real, pero duplica el tamaño y suma 6-7 puntos a P(año negativo) con 35% menos edge. |
| MFFU Rapid EOD 50K, fondeada, **escalera de tamaño** (recomendada para 2027) | PropMode Funded + **PropPreset Mffu50KLadder** (pone todo lo de esta fila en NQMaster; desde el 19-oct). Equivale a: preset Mffu50K + `SixYearModules` true + `FundedStepUpCushion` 3000, `FundedStepUpContracts` 2, `FundedLadderStep` 3000, `FundedLadderMax` 4, `FundedPayoutAt` 11600, `DailyLossPerContract` 1500, `MaxOpenContracts` 30; GoldMaster Robust con `FundedStepUpCushion` 3000, `FundedStepUpContracts` 2, `FundedLadderStep` 3000, `FundedLadderMax` 4. Pedir los retiros después del cierre de las 16:00. Sube 1 contrato por módulo por cada $3.000 de colchón (día de inicio) hasta 4; retirás solo lo que supere $11.100 de ganancia. En régimen (años 2-3) $214-288/día con el edge completo y $96-125 con 35% menos; quiebres 0,1-0,2 por año (1,2 con −35%). Amplifica lo que haya: si el edge se apaga, el colchón retenido se pierde. Nunca corrió en NinjaTrader: Strategy Analyzer con el preset completo antes de usarlo. |
| Lucid Pro 25K (fondeo rápido) | PropPreset LucidPro25K; evaluación nueva al día siguiente de cada pérdida. **No para ingreso**: una 25K fondeada rinde $20-27/día (mediana) contra $69-94 una 150K, y Lucid permite solo 5 fondeadas por hogar (`acct_2027.py`). Usala solo para tener la primera fondeada rápido. |
| **Lucid Pro 50K, eval rápida** (desde el 20-oct) | **PropPreset LucidPro50K**, PropMode Eval, DLL **OFF** al comprar. Pone 4 contratos por módulo, cierra todo al llegar a +$3.000, sin stop de ganancia. GoldMaster Robust con Contracts 4 y EvalTarget 3000. **Si se quema, comprá otra (o reset $115) al día siguiente**; no compres 3 a la vez (con la misma estrategia pasan o se queman juntas). Fondeada en ≤5 días hábiles usando hasta 3 evals: 52% / 66% (2020-23 / 2024-26), con 35% menos edge 45% / 55%, sin edge 33% / 39%; en ≤10 días 77% / 84%. **Solo NQ, sin GoldMaster**: ≤5 días 51% / 61%, ≤10 días 75% / 82% (35% menos edge 66% / 70%). (`lucidpro_week.py`, `lucidpro_week_nogold.json`) |
| Lucid Pro 50K, fondeada | PropPreset LucidPro50K, PropMode Funded: 1 contrato, stop de ganancia diario de cuenta $1.000 (cuida la consistencia del 40%), risk cap $300 por debajo de $1.000 de colchón, pedido de retiro al llegar a $4.100 de ganancia. GoldMaster Robust Contracts 1. Mediana $1.128 / $1.545 por mes por cuenta (con 35% menos edge $713 / $843), 0,7-1,6 quiebres por año. **Solo NQ**: $992 / $1.335 (35% menos edge $640 / $771). |
| Lucid Flex 150K (las 5 plazas de Lucid) | Eval 6 contratos con stop de ganancia diario $4.050; fondeada 3 contratos, risk cap $300 por debajo de $1.687 de colchón, retiro a $6.000. **PropPreset Lucid150K** (desde el 19-oct). GoldMaster: Contracts 3 en fondeada. |

- **Misma firma = mismo perfil en todas las cuentas.** Lucid y MFFU prohíben posiciones opuestas entre cuentas propias.
- `CrossAccountGuard` (por defecto activo) evita las opuestas **solo entre instancias de la misma PC**. Con dos PCs, usá el mismo perfil en todas.

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
| `another account holds the opposite NQ position` | La guarda entre cuentas bloqueó una entrada. | Nada. Es la regla de la firma. |

## Reglas de pausa (preacordadas, no se negocian en caliente)

Pausá un perfil (Enabled = false) si se cumple cualquiera de estas:

1. Después de 60 días hábiles en vivo, el P&L acumulado por contrato base es negativo.
2. El monitor de borde saltó **y** el año de fallback también termina negativo.
3. `python impl_gap.py <csv de la cuenta real>` da ALERTA de cuenta: los últimos 60 días quedan por debajo del 65% de lo esperado y la diferencia supera 2 errores estándar.

4. **Dos trimestres calendario seguidos con P&L negativo por contrato base** (`forward2027.py`): con el edge completo pasa 0,3% de los años, con 35% menos 6%, sin edge 55%.
5. **Un trimestre negativo** no pausa, pero **apaga la escalera** (`FundedLadderStep` 0) hasta cerrar un trimestre positivo: con el edge completo pasa 14% de los años, con 35% menos 46%.

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
- **Al volver**: arrancá la estrategia en el mismo gráfico con **Days to load ≥ 45**. NQMaster recupera el inicio del día y el pico de la cuenta desde `nqmaster_prop_<cuenta>.txt`; las órdenes que quedaron en el broker las sincroniza `AccountSyncGuard` (si la cuenta y la estrategia no coinciden, aplana y se detiene: revisá antes de reactivar). Las entradas pendientes de la sesión se cancelan al reiniciar (`SkipShortSessions`), no se re-emiten.
- **Barras que faltan** (minuto sin operaciones o hueco del feed): un módulo de reloj entra solo si existe la barra de su minuto; si falta, ese día no opera. Es el mismo criterio de la investigación (coincidencia exacta del minuto) y pasa en 0,4-1,2% de las sesiones nocturnas. Una barra procesada más de 2 minutos tarde tampoco genera entradas (`LateBar`). No hay que cambiar nada.
- **Dos PCs**: `tools/instalar_en_pc.ps1` instala la misma versión; nunca corras la misma cuenta desde las dos PCs a la vez.

## Cumplimiento (releer antes de cada cuenta nueva)

Detalle con fuentes y fechas en `research/mine/propfirms_check_2026-10-16.md`.

- **Lucid:** bots permitidos. Prohibidos el HFT, el microscalping y el hedging entre cuentas. Máximo 5 fondeadas.
- **MFFU:** bots permitidos si son propios. En las fondeadas Rapid/Pro no se puede tener ninguna posición ni orden entre 2 minutos antes y 2 minutos después de CPI, NFP, FOMC y las minutas FOMC (el preset lo hace). Prohibido el hedging. Máximo 3 Rapid 50K. El límite de 30 micros cuenta MNQ y MGC juntos.
- **Apex:** prohíbe la automatización. **Topstep:** solo TopstepX, no NinjaTrader. **No usar ninguna de las dos.**

## Divergencias abiertas (conocidas)

- **ICT:** NinjaTrader llena el retest unos minutos después que la investigación (82% emparejado).
- **MSEQS:**
  - En NinjaTrader necesita que ORB60 se haya llenado en short; la investigación usa la señal de ORB60 antes de los filtros (56% emparejado, ~$24/mes a favor de la investigación).
  - Si ORB60 está apagado o bloqueado por el risk cap, MSEQS no opera ese día.
- **Reinicios:** el monitor de borde guarda su estado en `nqmaster_edge_<cuenta>.txt` desde el 2026-10-16. La alarma de inactividad por módulo no se guarda: después de un reinicio solo cuentan las alarmas de dirección (12 días), VOLB y MOM11.
