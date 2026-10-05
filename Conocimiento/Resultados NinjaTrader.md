# Resultados en NinjaTrader (validación real)
Volver a [[00 - MAPA]]

Strategy Analyzer, del 01-ene-2024 al 27-sep-2026, 1 minuto, con comisión ($1.90) y slippage de 1 tick.

| Corrida | Trades | Win rate | PF | Neto | Max DD |
|---|---|---|---|---|---|
| **MNQ MaxSharpe (última)** | 2,635 | 65.9% | **1.30** | **+$30,025** | $3,415 |
| MNQ MaxSharpe, solo 2026 | 582 | 67.2% | 1.40 | +$11,134 | $2,578 |
| MNQ WinRate70 | 1,966 | 68.6% | 1.35 | +$23,775 | $2,757 |
| **MGC Gold** | 410 | 47.8% | 1.21 | +$4,952 | $1,476 |
| MGC con MaxSharpe (❌ perfil equivocado) | 2,269 | 61.0% | 0.93 | −$5,563 | $6,744 |

Total con dos gráficos: ~**$35,000** en 2.7 años con 1 contrato por módulo (~$1,090 por mes).

Mi backtest frente a NinjaTrader por módulo: diferencias chicas, salvo ICT (la simulación era optimista) y MOM11 (reglas de órdenes, ya corregido).

Versiones anteriores: [[Estrategias legacy]] (el Pullback Engine v1 daba PF 1.02 en 2026 por el bug de feriados).

## MaxPlus 2020-2026, 1 contrato, MNQ real en NinjaTrader (2026-09-29)

| | Confluencia OFF | Confluencia ON |
|---|---|---|
| Neto | $75,509 | **$84,579 (+12%)** |
| PF | 1.31 | **1.34** |
| Drawdown máximo | $4,209 | **$3,406** |
| $/mes | $943 | $1,056 |
| Trades | 7,176 | 6,887 |

Con confluencia ON:
- **PF por módulo:** CRT11 1.79, ORB60 1.59, MSEQS 2.52, MSEQ 1.50, ICT 1.39, ORB90 1.35, MOM13 1.26, REV06 1.23, LON 1.21, ON07 1.18, MOM11 1.17, MOM1030 1.14. Todos ganan.
- **Por año:** 2020 $6.2k, 2021 $7.3k, 2022 $22.3k, 2023 $9.4k, 2024 $8.4k, 2025 $16.8k, 2026 (9 meses) $14.2k. Todos positivos.
- **Regla A validada en NinjaTrader:** los trades de la tarde con doble tamaño dan PF 1.82 (286 trades, $18.0k), contra PF 1.33 de los de tamaño normal.

**Adaptativo repetido sobre estos mismos trades:**
- 2→1 @600: $105.6k.
- 2→1 @800: $114.5k (DD $4.4k).
- 3→1 @600: $112.1k.

El backtest de NinjaTrader con 3→1 @600 dio $80.4k y 150 trades menos: algo se comporta distinto con tamaños grandes. Falta revisarlo con la lista de trades y el Log de ese backtest.
