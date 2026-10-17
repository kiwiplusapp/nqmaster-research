# Runbook de operación NQMaster (versión 2026-10-17)

Una página. Si algo de acá contradice una sección vieja de `NQMASTER_GUIA.md`, manda esta.

## Antes de operar (una vez, y después de cada cambio de código)

1. **F5** en el NinjaScript Editor. Tiene que compilar sin errores. En la nube solo se verifica la sintaxis contra un stub (`bash tools/nt8_stub/check.sh NQMaster.cs`).
2. **Strategy Analyzer**: MNQ, 1 minuto, Profile Ultra, Contracts 1, PropMode Off, desde 2024-01-01 hasta hoy, comisión $1,90 y 1 tick de slippage.
   - Exportá los trades (CSV).
   - Corré `python parity_check.py <csv> --set ultra_r` desde `research/mine`.
   - Tiene que decir **PASA**, o fallar solo en ICT y MSEQS por los motivos conocidos (ver "Divergencias abiertas" más abajo).
3. En el Output del backtest no debería aparecer ningún `INACTIVITY ... no SHORT / no LONG`. Si aparece, hay una orden atascada: no operes.
4. Days to load ≥ 45 (NQ) y ≥ 120 (oro, GoldMaster).

## Configuración por cuenta (no mezclar perfiles dentro de la misma firma)

| Cuenta | Ajustes |
|---|---|
| MFFU Rapid EOD 50K, evaluación | Profile Ultra · Contracts 1 · PropMode Eval · PropPreset Mffu50K |
| MFFU Rapid EOD 50K, fondeada | Igual, con PropMode Funded. El preset pone el risk cap $300 por debajo de un cushion de $2.000, el pedido de retiro al llegar a $4.600 de ganancia (retirás hasta dejar $4.100) y el apagón de noticias. El escalón a 2 contratos (`FundedStepUpCushion` 4000, retiro a $6.600) es **opcional**: más ingreso mediano si el edge es real, pero duplica el tamaño y suma 6-7 puntos a P(año negativo) con 35% menos edge. |
| MFFU Rapid EOD 50K, fondeada, **escalera de tamaño** (opcional, 17-oct; objetivo "$200/día por cuenta") | PropMode Funded + preset Mffu50K + `FundedStepUpCushion` 3000, `FundedStepUpContracts` 2, `FundedLadderStep` 3000, `FundedLadderMax` 4, `FundedPayoutAt` 11600, `DailyLossPerContract` 1500, `MaxOpenContracts` 30. Sube 1 contrato por módulo por cada $3.000 de colchón (día de inicio) hasta 4; retirás solo lo que supere $11.100 de ganancia. En régimen (años 2-3) $214-288/día con el edge completo y $96-125 con 35% menos; quiebres 0,1-0,2 por año (1,2 con −35%). Amplifica lo que haya: si el edge se apaga, el colchón retenido se pierde. Nunca corrió en NinjaTrader: Strategy Analyzer con el preset completo antes de usarlo. |
| Lucid Pro 25K (fondeo rápido) | PropPreset LucidPro25K; evaluación nueva al día siguiente de cada pérdida |

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
| `EDGE MONITOR WARNING` | El resultado viene por debajo del backtest. Pasa por azar 1 de cada 4 años. | Nada. Solo seguí mirando. |
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
- Cada enero: pedime que corra `research/mine/robust16.py` y actualice la tabla `FallbackList` del año.

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
