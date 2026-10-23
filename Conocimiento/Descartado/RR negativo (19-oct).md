# RR negativo (19-oct-2026)

Pedido: "¿un RR negativo puede mejorar el sistema? Probalo en 2020-23 y después en 2024-26".

Prueba (`research/mine/negrr_lab.py`): cada módulo de Ultra con objetivo = RR × stop base (RR 0,2 / 0,3 / 0,5 / 0,75) y stop ampliado ×1 / ×1,5 / ×2 / ×3; 16 celdas por módulo, 21 módulos, cada celda re-simulada dentro del portafolio entero sobre NQ real (motor de salidas `wrq`, 1 minuto, $1,90 + 1 tick). Elegido en 2020-23, comprobado en 2024-26.

| Portafolio | 2020-23: WR / PF / $mes / Sharpe | 2024-26: WR / PF / $mes / Sharpe |
|---|---|---|
| Base (Ultra como está) | 66,1 / 1,46 / 2.023 / 3,55 | 64,9 / 1,46 / 2.530 / 3,54 |
| Uniforme RR 0,2, stop ×1 | 83,5 / 1,27 / 616 / 2,53 | 81,5 / 1,13 / 392 / 1,16 |
| Uniforme RR 0,5, stop ×1 | 68,9 / 1,37 / 1.514 / 3,20 | 66,8 / 1,29 / 1.525 / 2,67 |
| Uniforme RR 0,75, stop ×2 | 59,3 / 1,39 / 2.579 / 2,58 | 56,9 / 1,24 / 2.097 / 1,72 (DD 16,5k) |
| Elegido por módulo en 2020-23 (Sharpe, WR ≥ base) | 69,4 / 1,52 / 2.269 / 3,71 | 67,3 / 1,39 / 2.218 / 2,98 |

- 336 celdas: 83 superan al módulo base en 2020-23, 18 en los dos períodos (22%, igual que el azar: 23%).
- Único módulo consistente: NF05 con objetivo chico (RR 0,2, stop ×1): WR 89 / 93%, PF 2,1 / 2,5, pero gana $1,4-1,9k por período en vez de $2,9-3,2k; en el portafolio suma +0,02 de Sharpe y resta ~$1k por período. No vale el cambio.

**Veredicto:** el RR negativo sube el WR y baja el dinero y el Sharpe fuera de muestra. Rechazado (coincide con `wr70_variants` y `frontier.py` del 3 y 8 de octubre).
