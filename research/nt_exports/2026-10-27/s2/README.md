# Export Off 2024-01-01 → 2026-10-23 con v4.3 (v4.2 + `patch_parity_s2.py`), 27-oct

- `trades_off_2024-01-01_hoy_v43.csv`: Strategy Analyzer, Ultra, 1 contrato, Standard, $1,90 + 1 tick, con el parche de paridad de S2 (reintento ORFAIL/CAM3, ICT diferido en 1 min, MSEQS por señal cruda de ORB60). Todavía con `IctMultiplier = 2` (la decisión ICT x1 es posterior a este export).
- `fill_gap_v43_vs_v42.md`: contra el Off de v4.2 (`../../2026-10-26/v42/trades_off_2024-01-01_hoy.csv`): 3.269 pares idénticos ($ iguales), 5 pares con 1 barra de diferencia (cascada), no emparejados solo en los módulos parcheados y su cascada: ORFAIL +74, CAM3 +13, MSEQS +7, ICT +13/−6, VOLB −7/+1, MOM11 −12, MOM1030 +6, MOM13/MSEQ/ORB60/ORB90 +1, RV11 −1.
- `parity_ultra_d4_mnq.md`: **G1 98,5 %, G2 −1,6 %, G3 0,981, PASA**; 13 módulos en 100 %, CAM3 91,7 %, VOLB 94,5 %, RV11 96,4 %, CRT11 95,1 %. (`ultra_d4_mnq` = mismas reglas sobre `mnq_fut.npz`, el instrumento del Analyzer; período común 2024-01-22 → 2026-09-25.)
- `parity_ultra_d4.md`: contra el set de campaña en NQ: G1 94,1 %, G3 0,970; fallan ICT 89,5 %, MSEQS 81,5 %, RV11 67,7 % por diferencias de instrumento (NQ vs MNQ).
