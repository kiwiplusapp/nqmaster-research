# Perfil WR70Plus (2026-10-03)

**Objetivo:** winrate ≥ 70% con PF igual o mayor. Búsqueda en research/mine/wr70_search.py: ~70 variantes de módulos (objetivos chicos incluidos, variants_ext_*.pkl), coordinate ascent con 400 arranques, elegido solo con 2020-23 (WR ≥ 70.5%, ≥ 3 trades/día, máximo PF).

**Composición:**
- ORB60 0.75R, ORB90 0.6R, MSEQ 0.5R, MSEQS, CRT11 2R, ICT 1R (×2), MOM11 y REV06.
- VW13: distancia a la VWAP ≥ 0.15 ATR; 2 contratos si es ≥ 0.30.
- VOLB solo a favor de la tendencia, con objetivo 0.5R.
- Apagados: LON, ON07, MOM13 y MOM1030.
- Con reglas de confluencia y de contexto.

| | WR | PF | Sharpe | $/mes | Trades/día |
|---|---|---|---|---|---|
| CFD 2020-23 | 72.8 | 1.545 | 3.22 | 1,344 | 3.06 |
| CFD 2024-26 | 70.8 | 1.454 | 2.84 | 1,527 | 3.01 |
| MNQ real 2024-26 | 71.5 | 1.502 | 3.03 | 1,595 | 2.87 |
| 2026 CFD / real | 71.2 / 71.9 | 1.507 / 1.546 | 2.95 / 2.95 | 1,950 / 1,879 | 2.6-2.9 |

Referencia, MaxPlus con las mismas reglas: WR 67.0 / 65.9 / 67.1 y PF 1.44 / 1.40 / 1.44.

**Apex** ($/mes por cuenta, evaluación con 4 contratos y fondeada con 1; tramos 2020-23 / 2024-26 CFD / real):
- 25K: $581 / $492 / $603.
- 50K: $930 / $996 / $1,148.
- Gana menos que **Ultra** (25K: $682-754; 50K: $1,238-1,443) porque hace menos trades. WR70Plus es para quien prioriza winrate y PF; Ultra, para quien prioriza dinero.

**En NinjaTrader:** perfil WR70Plus. Copia previa: `NQMaster_backup_pre_wr70plus.cs`.
