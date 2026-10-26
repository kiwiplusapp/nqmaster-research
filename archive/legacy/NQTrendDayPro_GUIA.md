# NQ Trend Day PRO: entregables

Estrategia: `NQTrendDayPro.cs` (compilada contra tu NinjaTrader 8.1.8.2 e instalada en Strategies).
Todos los resultados vienen de un replicador vela a vela de la misma lógica (`research/nt_v3_replica.py`), con datos de 1 minuto del Nasdaq-100.
Costos simulados: $1 ida y vuelta por contrato y 1 tick de slippage en entradas stop o a mercado y en stops. Ningún número es estimado.

---

## 0. Qué objetivos no se pueden cumplir a la vez

| Tu objetivo | Qué mostró la investigación (más de 25,000 configuraciones en 15 familias, 2020–2026) |
|---|---|
| PF ≥ 1.5 | Ninguna configuración llega a 1.5 en los últimos 2 años, ni in-sample ni out-of-sample. La máxima fue 1.41 in-sample y luego cayó a 0.93 out-of-sample. |
| 3–10 trades por día | Las ventajas que sobreviven dan 0.8–1.1 trades por día. A mayor frecuencia (scalping, FVG, IFVG, reversión, order flow) la expectativa queda negativa después de costos. **Forzar un mínimo de 3 trades por día obligaría a tomar trades sin ventaja**, así que el mínimo no se impone. El máximo de 10 sí existe como contador duro. |
| Win rate 65–80% | Se consigue con TP1 en 0.5R (70–75%), pero en el out-of-sample esa versión **pierde** (PF 0.93). Mejor compromiso: TP1 en 1R con breakeven y runner en 2R, win rate ~50–56%. |
| Expectativa positiva (objetivo #1) | Se mantiene, pero es fina: PF 1.06 out-of-sample y 1.04 en walk-forward. |

**Mejor compromiso:** una sola familia de ventaja (tendencia intradía en días de tendencia), gestión de 2 patas y una capa de riesgo propfirm estricta. Es lo más robusto que encontré, y aun así **no alcanza tus mínimos**. No la pases a una evaluación sin antes validarla en NinjaTrader con futuros reales (sección 7).

---

## 1. El edge

**Por qué debería funcionar:**
- Los días en que el NQ abre alineado con su tendencia diaria (cierre sobre o bajo la SMA20) tienden a extender el rango de la primera hora (momentum intradía, ver Zarattini y Aziz 2023 sobre ORB).
- El módulo VWAP entra en el retroceso al precio medio institucional en esos mismos días.
- Es un efecto documentado en índices y positivo en 6 de 7 años (2020–2026).

**Cuándo falla:**
- **Regímenes de reversión o rango con volatilidad alta.** Por ejemplo mayo–junio 2025 y julio–agosto 2026: −$3,536 y −$3,025 en esos meses.
- Días de noticias.
- Cambios bruscos de tendencia en los que el sesgo SMA20 queda atrasado.
- **La ventaja se debilitó desde 2025.**

---

## 2. Código
`NQTrendDayPro.cs`, un solo archivo, órdenes managed con 4 signal names (`ORB1`, `ORB2`, `VWP1`, `VWP2`).

**Timeframe: 1 minuto.** El rango de apertura y las órdenes necesitan precisión de minuto. Las decisiones se toman al cierre de cada vela (sin repintado). El sesgo diario y el ATR se construyen solo con días RTH ya completos.

**Historical vs Realtime:**
- El guard de trailing drawdown opera solo en `State.Realtime` y se mide desde que la estrategia pasa a live.
- Las órdenes históricas se convierten con `GetRealtimeOrder`.
- `StartBehavior = WaitUntilFlat`.

**Pausa manual para noticias:** crea el archivo `pause_trading.txt` en `Documents\NinjaTrader 8\`. La estrategia cancela las órdenes pendientes y no abre nada nuevo. Bórralo para reanudar, sin reiniciar.

---

## 3. Parámetros

| Parámetro | Default | Rango de optimización | Lógica | Rango que siguió siendo rentable (IS y OOS) |
|---|---|---|---|---|
| Opening range | 60 min | 45–60 | Tamaño de la "primera hora" | 60 funciona. Con 45 el out-of-sample empeora (PF 0.80–1.05) |
| Stop cap | 0.25 × ATRd | 0.15–0.25 | Tope del stop según volatilidad | 0.20–0.25 (PF out-of-sample 1.09–1.10). Con 0.15 pierde (0.80–0.87) |
| TP1 | 1.0R | 0.5–1.0 | Asegura la mitad de la posición | 1.0 es estable. 0.5 da win rate de 70% pero falla out-of-sample |
| TP2 (runner) | 2.0R | 1.5–3.0 | Captura la extensión del día de tendencia | 1.5–3.0 son parecidos (PF 1.06–1.13 out-of-sample con cap 0.25) |
| Breakeven tras TP1 | Sí, +1 tick | — | El runner no puede convertirse en pérdida | Fijo |
| VWAP extension | 0.10 × ATRd | 0.05–0.15 | Exige que el día se haya extendido | 0.05–0.15, con PF del módulo 1.2–1.3 en 2020–26 |
| ORB / VWAP last entry | 13:00 / 14:30 | fijos | Evita entradas tarde | No optimizar |
| Flatten | 15:55 ET | fijo | Regla propfirm | No optimizar |
| Contratos TP1 / runner | 1 / 1 | — | 2 MNQ por trade | Escalar solo con cuenta mayor |
| Max $ riesgo por trade | 500 | — | Salta trades con stop enorme | Ajustar a la cuenta |
| Pérdida diaria | $600 (cierra todo) | — | Regla propfirm | Según la firma |
| Meta diaria | 0 (off) | — | Opcional | — |
| Max trades por día | 10 (duro) | — | Contador | En la práctica nunca se alcanza |
| Stop tras N pérdidas | 2 | — | Corta los días malos | — |
| Trailing drawdown | $2,000 (buffer $200) | — | Según la firma | — |

Parámetros que **no** se optimizan: el sesgo SMA20 y el ATR14 (definición estándar); las horas se optimizan solo por lógica.

---

## 4. Backtest y optimización en el Strategy Analyzer

1. **Datos:**
   - Instrument: `MNQ ##-##` (Tools → Options → Market Data → Merge policy = Merge back adjusted).
   - Minute 1, Trading hours **CME US Index Futures ETH**.
   - Rango: 2024-09-25 → hoy.
   - Tu conexión debe tener historia de 1 minuto de 2 años (descárgala antes).
2. **Settings:**
   - Order fill resolution: **High → Tick 1** (si tienes ticks; si no, Standard).
   - Slippage: **1**.
   - Include commission: **True**, con la comisión real de tu broker o firma (MNQ ~$0.50–1.00 por lado).
   - Set order quantity: **Strategy**.
   - Entries per direction 1, Entry handling **UniqueEntries** (vienen por defecto).
3. **Estas 3 corridas:**
   - **In-sample (optimización):** 2024-09-25 → 2026-01-25. Optimizar solo `StopCapAtr` (0.15/0.20/0.25), `Tp1R` (0.5/0.75/1.0) y `Tp2R` (1.5/2.0/3.0). Fitness: *Max Profit Factor*, con mínimo 150 trades.
   - **Out-of-sample:** 2026-01-26 → hoy, con los parámetros elegidos **sin tocarlos**.
   - **Walk-forward:** Backtest type = Walk Forward, Optimization period 365 días, Test period 120 días, mismos 3 parámetros.
4. **Aprobación mínima:** PF out-of-sample ≥ 1.3, peor mes ≥ −$2,000, drawdown máximo < 60% del trailing drawdown de la firma. Si no se cumple, **no pasar a eval**.

---

## 5. Métricas que necesito para iterar
- Summary: Net profit, **Profit factor**, **% profitable**, Max drawdown, Avg trade, número de trades.
- Trades por día (trades / días operados), **peor día** y mejor día.
- **Curva por mes** (Analysis → Periods → Monthly).
- Separado por módulo (filtra por signal name en Trades: ORB1/ORB2 vs VWP1/VWP2).
- Exportación CSV de la pestaña Trades (clic derecho → Export), para compararla trade por trade con mi replicador.
- Output window de 1–2 días, para verificar el log de entradas y salidas.

---

## 6. Checklist antes de eval y de cuenta fondeada
- [ ] Compila (F5) y corre en Strategy Analyzer sin errores.
- [ ] El backtest de NinjaTrader con futuros reales se parece al del replicador (sección 7), con diferencias menores al 20%.
- [ ] PF out-of-sample ≥ 1.3 y walk-forward positivo (hoy **no se cumple** en el replicador).
- [ ] 4 semanas en **Sim101** en tiempo real: entradas a la hora correcta, parciales y breakeven funcionando, cierre a las 15:55.
- [ ] Pérdida diaria, trailing drawdown y contratos máximos iguales a las reglas exactas de la firma.
- [ ] Probar la pausa manual (crear y borrar `pause_trading.txt`) y la pérdida diaria (en Sim, bajando temporalmente el límite).
- [ ] Revisar el calendario económico cada mañana: CPI, FOMC y NFP → pausa.
- [ ] En la eval, riesgo de 1+1 MNQ. No subir tamaño hasta 30 días fondeado con resultados en línea.
- [ ] Criterio de apagado: 2 meses seguidos negativos o drawdown mayor al 50% del límite de la firma.

---

## 7. Resultados de backtest (replicador vela a vela, 2 MNQ por trade, pérdida diaria $600)

Configuración por defecto: rango de 60 minutos, stop cap 0.25 ATR, TP1 = 1R (50%) + breakeven, runner 2R.

| Período | Trades | Trades/día | Win rate | PF | Expectativa | Neto | Max DD | Peor día |
|---|---|---|---|---|---|---|---|---|
| In-sample (sep-2024 → ene-2026) | 278 | 0.81 | 54.3% | 1.25 | +$31/trade (+0.076R) | +$8,655 | $5,101 | −$759 |
| **Out-of-sample (feb → sep-2026)** | **139** | **0.80** | **45.3%** | **1.06** | **+$10/trade (+0.042R)** | **+$1,373** | **$7,375** | **−$857** |
| 2 años completos | 417 | 0.81 | 51.3% | 1.17 | +$24/trade | +$10,028 | $7,375 | −$857 |

**Walk-forward** (re-optimiza cada 4 meses con 12 meses de historia, entre 72 configuraciones):

| Test | Elegida | PF test | Neto |
|---|---|---|---|
| ene–may 2025 | 1.0R/1.5R, cap 0.20 | 1.32 | +$4,074 |
| may–sep 2025 | 2R, cap 0.25 | 0.68 | −$3,573 |
| sep 2025–ene 2026 | 0.5R, cap 0.20 | 1.55 | +$2,459 |
| ene–may 2026 | 0.5R, cap 0.20 | 1.46 | +$3,570 |
| may–sep 2026 | 0.5R/3R, cap 0.20 | 0.64 | −$4,729 |
| **Total (20 meses)** | — | **1.04** | **+$1,801, DD $7,307, win rate 60.2%** |

**Curva mensual (2 años, $):**
- **Oct-24 a Jun-25:** +1,642, +1,127, +231, −243, +1,396, +525, +6,457, −1,895, −1,326
- **Jul-25 a Mar-26:** −311, −969, −450, +2,491, −2,240, +1,160, +1,032, +650, −951
- **Abr-26 a Sep-26:** +2,061, +1,781, +3,135, −3,536, −3,025, +1,286

**Conclusión honesta:**
- **Expectativa positiva, pero lejos de PF 1.5.** Dos cortes de 4 meses de 5 en el walk-forward perdieron.
- **Frecuencia ~0.8 trades por día.**
- Con 2 MNQ, el drawdown de $7,375 **supera** el trailing drawdown típico de una 50K ($2,000–2,500). Con 1 MNQ en vez de 2 el drawdown en dólares se reduce a la mitad, pero ya no se puede hacer la salida parcial en 2 patas.
- **No la recomiendo para una evaluación** hasta que el backtest con datos reales de futuros y el Sim confirmen algo mejor.
