# NexGenAlgo System 1: trend-pullback con buy stop (16-oct-2026)

## La regla tal como la pasó Federico

- **Tendencia:** EMA 3 > EMA 7 > EMA 50.
- **Volatilidad:** ATR 14 plano o cayendo.
- **Candle 1:** vela bajista que retrocede contra la tendencia.
- **Entrada:** buy stop 1 tick sobre el máximo de la Candle 1.
- **Stop:** 1 tick bajo el mínimo de la Candle 1.
- **Objetivo:** 2R.
- **Horario:** desde 1 hora después del reopen de las 18:00 ET.

Archivos: `research/mine/families6.py` (familia NGA_PB) y `research/mine/results_nga.csv`. Para correrlo: `MINE_TAG=nga python3 run_mine_db.py NGA_PB`.

## Datos

- **Precios:** NQ real de Databento 2010-26.
- **Costos:**
  - 2020-26: $1,90 de comisión + 1 tick por lado.
  - 2010-19: costo normalizado al 0,345% del ATR.
- **Grilla (1.458 variantes):**

  | Parámetro | Valores probados |
  |---|---|
  | Timeframe | 5, 15 y 60 minutos |
  | Chequeo de ATR | ninguno / ≤ 1 vela atrás / ≤ 3 velas atrás |
  | Pullback | cualquier vela bajista / toca la EMA3 / toca la EMA7 |
  | Validez de la orden | 1 o 3 velas |
  | Ventana | sesión entera / noche / RTH |
  | Lado | largo / corto / ambos |
  | Objetivo | 1R, 1,5R y 2R |

## Resultado

- **PF mediano de las 1.458 variantes:**

  | 2010-14 | 2015-19 | 2020-23 | 2024-26 |
  |---|---|---|---|
  | 0,76 | 0,87 | 0,82 | 0,90 |

  - Solo entre el 4% y el 21% de las variantes superan PF 1 en cada período.
  - **Ninguna** supera PF 1,05 en los cuatro períodos.
- **La regla exacta** (largo, 2R, ATR cayendo, sesión entera):
  - En 5 y 15 minutos: WR 30-37%, PF 0,71-0,98 en todos los períodos.
  - En 1 hora (la mejor): WR 37-40%, PF 1,15 (2020-23) y 1,11 (2024-26), pero 0,87 y 0,94 en 2010-19.
- **Elegida en 2020-23** (las 9 variantes con PF ≥1,25): en 2024-26 dan PF 0,90-1,06.
- **Ganadora del período de elección** (1 hora, RTH, ambos lados, 1,5R): PF 1,38 en 2020-23 → 1,01 en 2024-26 y 0,82 en 2010-14.

## Veredicto

Sin edge. Rechazada.

- El "449% en 12 meses" es un backtest promocional, probablemente en forex con apalancamiento y sin costos.
- En NQ, la regla con un objetivo de 2R gana el 33-40% de los trades y no cubre los costos.
