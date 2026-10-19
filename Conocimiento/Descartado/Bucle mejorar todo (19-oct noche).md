# Bucle "mejorar todo sin excepciones" (19-oct-2026, noche)

Pedido: menos drawdown, más trades, más win rate, PF igual o mayor, robusto, sin overfitting. Siete líneas en paralelo con protocolo preregistrado (elegir 2020-23, confirmar 2024-26 y 2010-19 normalizado, +4 ticks, meseta, portafolio con conflictos).

| Línea | Celdas | Sobrevivientes |
|---|---|---|
| Reglas de riesgo para el drawdown (`ddlab_report.md`) | 40 | 0 — el DD baja 1:1 con la ganancia |
| Más trades: segundas instancias, re-armados, bandas de VWAP (`more_trades_report.md`) | 1.072 + 13 + 9 | 0 |
| Bitcoin MBT con datos Binance (`btc_report.md`) | 65.544 | 0 — el costo es 1,5-4% del ATR |
| Oro en 16 años de futuros reales (`gold16_report.md`) | 65.544 | 0 (1 en meseta, $25/mes) |
| Fades de noticias macro aparte del CPI (`news_fade_report.md`) | 4.032 | 0 — solo el CPI revierte en la apertura |
| Perturbación de parámetros (`perturb_report.md`) | 7.762 | nada que cambiar; nivel honesto Sharpe ~2,5 / PF 1,3 / DD $5,6k; lo frágil son las horas |
| Cimientos globales (`foundations_report.md`) | ver informe | ver informe |

Lo que quedó: chequeo del reloj de barras tras cada cambio de horario, variante defensiva `DisableModules = MOM1030,MOM13,REV06`, lista de vigilancia de enero. Ver [[Plan 2026-2027 (19-oct)]] y `RUNBOOK_OPERACION.md`.
