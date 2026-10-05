# IFVG Sniper — Estrategia NinjaTrader 8

Port 1:1 del motor IFVG de `IFVG Sniper Entry Engine [trade_w_samet] v3` (Pine v6), con ejecución automática y una capa de riesgo para prop firms.
Archivo: `IFVGSniperStrategy.cs` (ya copiado a `Documents\NinjaTrader 8\bin\Custom\Strategies\`).

## 1. Instalar
1. Abrir NinjaTrader → New → NinjaScript Editor → **F5** (compilar).
2. Chart: **MNQ (contrato front), 1 Minute**, Trading hours **CME US Index Futures ETH**, cargar al menos 30 días.
3. Strategies → añadir **IFVGSniperStrategy** → elegir cuenta → Enabled.

## 2. Qué hace solo
| Pieza | Comportamiento |
|---|---|
| Señal | Mismo motor que el indicador: memoria de FVG ocultos, inversión con buffer ATR, filtro Custom (gap 0.25 ATR, cuerpo 0.50, rango 0.65 ATR, break 0.05 ATR), room filter, path filter, guard de volatilidad. |
| Entrada | `LimitAtIfvgLine`: orden limit en el midpoint del IFVG, cancelada tras 15 velas o si el precio toca el TP antes de llenar. `MarketNextBar`: mercado a la apertura siguiente. |
| SL / TP | SL = 1.5 × ATR(14), TP = 1R. Adjuntos automáticamente (OCO) al llenarse la entrada. Mín. 20 ticks, máx. 200 ticks. |
| Tamaño | `floor($100 / (stop + 1 tick slippage + comisión))` contratos, máx. 15. Si 1 contrato supera $100 → no opera. |
| Horario (ET) | Entradas 09:30–15:30, sin entradas nuevas desde 15:30, flat obligatorio 15:55. Blackout de noticias 08:30 / 10:00 / 14:00 (−2 / +5 min). |
| Prop firm | Stop diario −$300 (cierra todo), meta diaria +$400, máx. 8 trades/día, stop tras 3 pérdidas seguidas. En real: guard de trailing drawdown $2000 (buffer $200) y meta de cuenta opcional. El tamaño se reduce para que un stop nunca rompa el límite diario ni el drawdown. |
| Dashboard | Estado, P&L del día, stats reales y línea **"Pine"** (simulación idéntica al indicador) para comparar. |

## 3. Validar contra TradingView
En Strategy Analyzer, mismo rango de fechas que en TradingView, con `Use session filter = false`:
la línea **Pine** del dashboard / Output debe coincidir con las stats del indicador (± diferencias del feed de datos).
La línea **Real fills** es lo que realmente pasa con órdenes ejecutables.

## 4. Backtest realista (Strategy Analyzer)
- Order fill resolution: **High → Tick 1** (requiere datos tick; si no, Standard).
- Slippage: **1** tick. Commission: tu template (MNQ ≈ $0.50–$1.40 ida y vuelta por contrato).
- Desactiva `Print trade log` y `Show visuals` para optimizar.

## 5. Ajustar a tu prop firm (grupo 06)
| Parámetro | Topstep 50K | Apex 50K |
|---|---|---|
| Max trailing drawdown | 2000 | 2500 |
| Account profit target | 3000 | 3000 |
| Daily loss limit | 300 (el de la firma es 1000) | 300 |
| Flatten time (ET) | 1555 (límite 16:10) | 1555 (límite 16:59) |

## 6. Por qué los números reales pueden diferir del 60 %
El indicador cuenta el trade desde el cierre de la vela de confirmación con entrada en el midpoint, **aunque el precio nunca vuelva al midpoint**. Si el precio va directo al TP sin retroceder, el indicador lo cuenta como ganador, pero en la vida real la limit nunca se llena. La estrategia solo cuenta fills reales, por eso compara ambas líneas (Pine vs Real) antes de ir a real.
