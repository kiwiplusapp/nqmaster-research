# Portafolio diario NQ: 3 estrategias en la misma cuenta

Opera el **99% de los días** (1.9 trades por día), con **win rate ~71%**, **PF ~1.38** y todos los años positivos.

## Las 3 estrategias (ya instaladas; en NinjaTrader abre el NinjaScript Editor y pulsa F5)

| Estrategia | Qué hace | Configuración |
|---|---|---|
| **NQMom11** (nueva) | A las 11:00 ET compra si el precio está sobre la apertura de las 9:30, vende si está debajo. Stop 0.25 ATR, target 0.3R. **Opera todos los días.** | Valores por defecto |
| **NQPullbackDayEngine** | ORB60 + VWAP60 en días de retroceso, y Momentum Sequence en 5 minutos | **ORB30 off, ORB15 off, VWAP30 off**, Pullback max = **0.44**, Skip 2-day = **0** |
| **NQCrt11** | CRT de la vela de 11:00 contra la de 10:00, a favor de la tendencia, 2R | Valores por defecto |

Las 3 van en **MNQ, 1 Minute, CME US Index Futures ETH**, en la misma cuenta. Cada estrategia lleva su propia posición: NinjaTrader las separa aunque compartan cuenta.

## Backtest (1 MNQ por estrategia, 1 tick de slippage, $1 de comisión round turn)

| Datos | Trades/día | Días operados | Win rate | PF | Neto/año | Max DD | Sharpe |
|---|---|---|---|---|---|---|---|
| NQ 2020–2026 (CFD) | 1.95 | 99% | 71.4% | 1.37 | $6,680 | $2,976 | 2.36 |
| **MNQ real 2024–2026 (tus datos)** | **1.88** | **99%** | **71.1%** | **1.38** | **$7,786** | **$2,691** | **2.42** |

PF por año: 2020 1.33, 2021 1.56, 2022 1.42, 2023 1.30, 2024 1.22–1.26, 2025 1.38–1.43, 2026 1.45–1.50.

Por módulo, con MNQ real 2024–26:

| Módulo | Win rate | PF |
|---|---|---|
| MOM11 | 80.7% | 1.29 |
| ORB60 | 66% | 1.52 |
| VWAP60 | 67% | 1.32 |
| MSEQ | 60% | 1.32 |
| CRT11 | 48% (a 2R) | 1.56 |

## Evaluaciones (datos reales 2024–26; % pasa / % quema; el resto sigue activa)

| Cuenta | MNQ por estrategia | ≤20 días | ≤60 días |
|---|---|---|---|
| 25K ($1,500 / $1,500) | 1 | 20 / 8 | **65 / 18** |
| 25K | 2 | 49 / 27 | 62 / 38 |
| 50K ($3,000 / $2,500) | 2 | 20 / 11 | **63 / 20** |
| 50K | 3 | 34 / 29 | 56 / 44 |

Con 1 MNQ en la 25K o 2 MNQ en la 50K, la probabilidad de quemar la cuenta es baja (18–20%) y la de pasar ronda el 63–65% en 60 días.

## Cómo verificarlo en NinjaTrader
Corre en el Strategy Analyzer cada estrategia por separado. Usa MNQ 12-26, 1 Minute, ETH, desde **2024-01-01** hasta hoy, slippage 1 y comisión activada. Mándame los 3 Summary y comparo con mi backtest.

---

# v4 (28-sep): más módulos de NQ, sin otros mercados

## Cambios
1. **MOM11 con filtro VWAP**: solo opera si el precio está del mismo lado del VWAP y de la apertura. Los días en que no coinciden perdían en los 3 períodos.
2. **4 módulos nuevos en otros horarios**, todos con la estrategia **NQTimeMom** (una instancia por módulo):

| Instancia | Entry time | Lookback | Reverse | Stop ATR | Target R | Max hold | Trend | VWAP agree |
|---|---|---|---|---|---|---|---|---|
| MOM11 (reemplaza a NQMom11) | 1100 | -2 | no | 0.25 | 0.3 | 0 | no | **sí** |
| MOM13 | 1300 | -2 | no | 0.20 | 1.0 | 240 | sí | no |
| MOM1030 | 1030 | -2 | no | 0.20 | 0.3 | 60 | sí | no |
| ON07 | 0700 | 30 | no | 0.20 | 1.0 | 60 | sí | no |
| REV06 | 0600 | 30 | **sí** | 0.20 | 0.3 | 240 | sí | no |

Siguen **NQPullbackDayEngine** (ORB60 + VWAP60 + MSEQ) y **NQCrt11** como antes.

## Resultado (tus datos MNQ 2024–26)

| | Sharpe | Neto/año (1 MNQ por módulo) | Días operados |
|---|---|---|---|
| Portafolio v3 | 2.42 | $7,786 | 99% |
| **v4** | **2.73** | **$10,711** | 97% |

Sharpe de v4 en 2020–23 (CFD): 2.77; en 2024–26 (CFD): 2.54.

## Evaluaciones con v4 (% pasa / % quema)

| Cuenta | MNQ por módulo | ≤10 días | ≤20 días | ≤60 días | Sin límite |
|---|---|---|---|---|---|
| 25K ($1,500 / $1,500) | 3 | 56 / 29 | 65 / 34 | 66 / 34 | 66 / 34 |
| 25K | 2 | 42 / 18 | 63 / 27 | 71 / 29 | 71 / 29 |
| 50K ($3,000 / $2,500) | 2 | 11 / 6 | 35 / 14 | 72 / 25 | 74 / 26 |
| **50K** | **1** | 0 / 0 | 4 / 1 | 49 / 7 | **88 / 12** |

**Rápido o seguro:**
- **Rápido:** 25K con 3 MNQ. Pasa ~65% en unas 1–2 semanas.
- **Seguro:** 50K con 1 MNQ en una firma sin límite de días. Pasa **88%**, pero tarda 2–3 meses.

Los módulos nuevos se eligieron mirando los 3 períodos, así que son menos confiables que ORB60, CRT11 y MOM11. Verifícalos en el Strategy Analyzer antes de usarlos.

---

# v5: + ruptura de Londres con FVG (NQLondonFvg)
- **Reglas:** rango de 00:00 a 03:00 ET. La ruptura (cierre fuera del rango) tiene que darse antes de las 6:00 y a favor de la tendencia. Entrada con límite en el primer FVG después de la ruptura, válido hasta las 8:00. Stop en el lado opuesto del rango. Target 2R. Cierre a las 9:30.
- **Resultado:** PF 1.19 en 2020–23 (CFD), 1.37 en 2024–26 (CFD) y **1.39 en MNQ real**. Su correlación con el resto del portafolio es 0.10.
- **Portafolio completo (v4 + ICT apertura + Londres):** Sharpe **2.97** en MNQ real (2.86 en 2020–23, 2.76 en 2024–26 CFD).
- **Evaluaciones (MNQ real):**

| Cuenta | MNQ por módulo | Pasa / quema en 15 días | Pasa / quema en 20 días |
|---|---|---|---|
| 25K | 2 | 59 / 25 | 65 / 28 |
| 50K | 3 | 48 / 25 | 57 / 29 |

- La ruptura de Londres tal como se suele enseñar (cualquier rango y cualquier dirección) **no funciona en NQ**: PF mediano 0.90 en 6,912 variantes.

---

# v6: optimización profesional (qué se probó y qué quedó)
Método: cada mejora se elige con 2020–23 y solo se acepta si también funciona en 2024–26 (CFD) y en MNQ real.

| Idea | Resultado | Decisión |
|---|---|---|
| Filtros por módulo (día de semana, volatilidad, gap, retornos previos): 30+ candidatos | En 2020–23 el Sharpe subía de 2.84 a 3.64; en MNQ real quedaba igual (2.84 → 2.85) | **Rechazado** (sobreajuste) |
| Filtro de rango nocturno para Londres y ON07 | Parecía muy bueno, pero usaba datos posteriores a la entrada. Corregido, no tiene efecto | **Rechazado** |
| Optimizar pesos por módulo | Sin mejora fuera de muestra | Rechazado: pesos iguales |
| Targets más chicos para subir el win rate | El win rate sube 10–15 puntos, pero el PF baja | Rechazado |
| Fade del Initial Balance | PF mediano 0.85–1.04; la versión a favor de la tendencia repite CRT11 | Rechazado |
| ORB 15m + EMA20 en 2m | PF ~1.4–1.5 filtrado, pero se superpone con ORB60 | Rechazado |
| **Filtro VWAP en MOM11** | Mejora en los 3 períodos | **Aceptado** |
| **Contratos fijos por módulo en vez de % de riesgo** | Sharpe real 2.61 → **3.01**; los trades con stop corto son mejores | **Aceptado** |

## Topstep 50K con 1 MNQ fijo por módulo (MNQ real)

| | Trades | Win rate | PF | Neto | Max DD |
|---|---|---|---|---|---|
| 2026 (ene → sep) | 618 (3.3/día) | 69.3% | **1.49** | **+$14,162** | $2,473 |
| Último mes | 69 | 76.8% | **2.21** | +$2,782 (81% de días verdes) | $105 |

Por mes en 2026:

| Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep |
|---|---|---|---|---|---|---|---|---|
| +$305 | +$908 | +$2,351 | +$2,162 | +$3,815 | +$1,259 | +$381 | −$597 | +$3,577 |

**Combine Topstep 50K (empezando cualquier día de 2024–26):** pasa **83%**, quema 11%, en una mediana de 53 días.
**Cuenta fondeada:** 60% sobrevive 6 meses. En promedio te llevas $3,828 cada 6 meses por cuenta.

Con 2 MNQ por módulo la eval se pasa más rápido (mediana 19 días), pero quema el 34%.
