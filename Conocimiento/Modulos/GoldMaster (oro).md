# GoldMaster: estrategia propia para el oro
Volver a [[00 - MAPA]] · Guía: `GOLDMASTER_GUIA.md` · Código: `GoldMaster.cs`

## Cómo se buscó (5-oct-2026)
- Datos nuevos: oro CFD **2010-2019** (histdata), unido al 2020-26 → `xau_long.npz` (16 años, 5,8 millones de barras de 1 minuto).
- Minero: 25 familias (29.414 variantes) más 2 familias propias del oro: *drives* y ORB anclados a 18:00, 20:00, 03:00, 08:20 y 09:30 (8.568 variantes). En total 38.000 variantes.
- Costos de MGC: $1,90 + 1 tick por lado ($4 por punto de investigación; los precios están ×2,5).

## Qué se aprendió
- **El oro tiene ventajas mucho más débiles que el NQ.**
  - En 2015-19 solo el 6% de las variantes ganó.
  - Con el costo normalizado, solo ~17 ganaron (PF ≥ 1,1) en los 5 períodos.
- **Ventajas que duran 16 años:**
  - Ruptura del rango asiático (20:00-24:00) a favor de la tendencia: PF ~1,2-1,3.
  - Momentum de las 14:30 a favor de la tendencia: PF ~1,2-1,5.
- **Win rate alto en 2020-26:**
  - *Open drive* de NY (9:30-10:30, a favor de la tendencia, 0,5R).
  - Vela de 4 h de Londres.
  - Fade del VWAP a las 22:00.
  - Antes de 2020 no ganaban.
- **Probado y descartado:**
  - Confirmación con EUR/USD o con la plata: no mejora de forma consistente.
  - Deriva por hora: la de la sesión asiática es positiva pero chica. La de las 18:00 en el CFD es un artefacto de los datos.
- **Elegir solo con 2020-23 se degrada:** WR 66-69% / PF 1,4-1,9 dentro de la muestra pasa a PF 1,15-1,4 fuera de muestra cuando se suman muchos módulos.

## Perfiles
| Perfil | MGC real 2024-26 | CFD 2024-26 | CFD 2020-23 | 2010-19 |
|---|---|---|---|---|
| **WinRate** (OD1030 + ENG0408 + SVWAP22) | WR 70,3%, PF 1,99, 0,29 trades/día | WR 68,8%, PF 1,74 | WR 64,7%, PF 1,42 | PF 1,05 / 0,85 ❌ |
| **Robust** (+ ASIA + ENG0206) | WR 61,9%, PF 1,37, 0,88 trades/día | WR 61,4%, PF 1,35 | WR 59,4%, PF 1,22 | PF 1,20 / 1,08 ✅ |

- Correlación con NQMaster Ultra: **0,00**. El Sharpe conjunto sube de 3,61 a 3,89-3,96.
- Pendiente: validarla en NinjaTrader con MGC real (números esperados en la guía).
