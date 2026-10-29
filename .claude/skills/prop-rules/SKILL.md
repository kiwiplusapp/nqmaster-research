---
name: prop-rules
description: Reglas exactas de Lucid Flex 150K y MFFU Rapid EOD 50K tal como las usa RUNBOOK_OPERACION.md y los presets Lucid150K / Mffu50K de NQMaster. Usar al tocar presets, el motor PropCycle, el panel de cuenta, retiros, tamaños por fase o al contestar sobre qué permite cada firma.
---

# Reglas de cuentas prop usadas por NQMaster

Fuente de verdad en código: `PropPreset` y `PropCycle` en `NQMaster.cs` (los bloques `case NQMasterPropPreset.Lucid150K` y `Mffu50K`).
Fuente operativa: `RUNBOOK_OPERACION.md`. Si algo no coincide, manda el código del preset. Reglas verificadas por web en oct-2026; confirmar por escrito antes de comprar.

## Lucid Flex 150K (preset `Lucid150K`, modelo 0)

| Concepto | Valor |
|---|---|
| Saldo / objetivo de eval | 150.000 / 9.000 de ganancia |
| Drawdown | 4.500 trailing al cierre (EOD). El piso se traba en saldo inicial + 100 cuando la ganancia llega a 4.600 |
| Consistencia en eval | 50%: el mejor día no puede pasar de 50% de la ganancia total, así que el objetivo efectivo sube si hay un día grande |
| DLL | Opcional, apagado al comprar |
| Eval, tamaño | 6 contratos por módulo, stop de ganancia diario 4.050 (0,9 × 50% × objetivo), máximo 100 micros abiertos |
| Fondeada, tamaño | 3 contratos, risk cap $300 por contrato mientras el colchón < 1.687, máximo 40 micros abiertos |
| Consistencia fondeada | Ninguna |
| Retiro | Ganancia ≥ 6.000 (aviso del preset) y 5 días con ganancia ≥ 250 en el ciclo. Se pide min(3.000, 50% de la ganancia), mínimo 500. Se pide después del cierre de las 16:00 ET |
| Pagos | 5 retiros. Después Lucid pasa la cuenta a Live (discrecional) |
| Precio de lista | 285 (cupón ~215) |
| Límites del hogar | 5 cuentas fondeadas, 10 en total |
| Comisión | MNQ $1,00 ida y vuelta en Lucid, la investigación usa $1,90 |

Modelo en `PropCycle`: Model 0, `Q`=250, `Cap1`=`Cap2`=3000, `NpMax`=5, `Lock`=100.

## MFFU Rapid EOD 50K (preset `Mffu50K`, modelo 2)

| Concepto | Valor |
|---|---|
| Saldo / objetivo de eval | 50.000 / 3.000 |
| Drawdown | 2.000 trailing EOD, piso trabado en inicial + 100 |
| Consistencia en eval | 30% |
| Días mínimos | 4. Si el objetivo se alcanza antes, se deshabilita NQMaster en esa cuenta y se completan los días a mano con 1 MNQ |
| Eval, tamaño | `Contracts` 1 con MOM1030/CPI09 ×8 (`EvalHighWrMultiplier` 8), stop de ganancia diario 800, máximo 30 micros |
| Fondeada, tamaño | 1 contrato forzado, risk cap $300 mientras el colchón < 2.000, máximo 30 micros (MNQ y MGC cuentan juntos) |
| Consistencia fondeada | Ninguna |
| Noticias | Nivel 1 (CPI, NFP, FOMC): sin posiciones ni órdenes ±2 min. `NewsBlackout` queda en true al fondear |
| Retiro | Sin tope tras el colchón de 2.100. El preset pide al llegar a ganancia 4.600 y deja 4.100 en la cuenta (`FundedPayoutAt` 4600) |
| Reparto | 90/10 |
| Límites | 3 cuentas máximo. Cierre automático ~16:10 ET. Pase automático a Live al llegar a 10.000 de ganancia neta en un día, con revisión del riesgo |
| Límite de precio CME | Deshabilitar las fondeadas si el contrato está a menos de 2% de un límite (no está en el código) |
| Precio de lista | 157 |

Variantes: `Mffu50KLadder` (escalera 1→4 contratos, retiro desde 11.600) es opción, no el plan base. El escalón de 2 contratos a 4.000 de colchón exige `PropPreset` Manual.

## Reglas comunes

- Lucid y MFFU permiten bots, y las dos prohíben posiciones opuestas entre cuentas propias. Misma firma = mismo perfil en todas las cuentas y en la misma PC (`HedgeGroup` LUCID / MFFU lo pone el preset).
- Evaluación nueva el día después de cada quiebre. Presupuesto por plaza: retirado el 29-oct (`docs/DECISIONES_2026-10-29.md`, D2; experimento 05).
- El backtest de NinjaTrader no retira ni quiebra cuentas. Para ciclos usar el panel (`CycleSim`) o `research/mine/dash_cycle_ref.py`.
- Apex prohíbe automatización desde 2026-03-01 y Topstep solo permite TopstepX: no usar.
- Si cambia el motor de cuentas, correr `python3 tools/propcycle_test/run_test.py` (tiene que dar 0 diferencias).
