# Perfil MaxTrades (MOM1130 + RSI2)

Pedido: más trades por día sin bajar el winrate.

**Módulos agregados** (elegidos sobre CFD 2020-23 y verificados en CFD 2024-26 y en MNQ real 2024-26):
- **MOM1130**: igual que [[MOM11]] pero a las 11:30 (precio vs apertura RTH, con VWAP de acuerdo), stop 0.25 ATRd, objetivo 0.3R. WR ~77%, PF 1.10 / 1.12 / 1.13.
- **RSI2**: RSI(2) en 5m < 10 (> 90) a favor de la tendencia diaria (SMA20) y de la tendencia intradía (precio vs apertura RTH y VWAP), entre 10:30 y 15:45. Stop 0.15 ATRd, objetivo 0.3R, máximo 120 min, hasta 3 por día. WR ~76-79%, PF 1.14 / 1.11 / 1.12.

**Portfolio (MNQ real 2024-02 → 2026-09, solo NQ, sin FOMC, $1.90 de comisión):**

| Perfil | Trades/día | WR | PF | Neto |
|---|---|---|---|---|
| MaxSharpe | 3.7 | 66.9% | 1.35 | $32,012 |
| MaxTrades | 5.2 | 70.0% | 1.27 | $32,497 |

Apex 50K (adaptativo 2→1): a 30 días, 36% de pases con 12% de quemadas, contra 31% / 5% con MaxSharpe.

**Conclusión:** hay más trades y más winrate, pero el dinero es casi el mismo, porque los trades nuevos apenas cubren la comisión. Para ganar más dinero con el mismo winrate hay que subir el tamaño (contratos o cuentas), no la cantidad de trades.

Probado y descartado en la misma búsqueda (research/intra.py, mom_vwap_times.py): pullback a la EMA20, toque de VWAP, continuación de HOD/LOD y MOM a otras horas.
