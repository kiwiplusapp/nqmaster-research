# CISD (Triton Trades), 9 EMA + VWAP y Engulfing 4H (Omar) — 2026-10-03

Código: `research/mine/families3.py`, minero `run_mine.py` (17,856 variantes), cartera `b3_port.py`, Apex `b3_eval.py`.
Protocolo: elegir con CFD 2020-23 (IS) → verificar CFD 2024-26 (C24) y MNQ real 2024-26 (REAL) → 11 años con coste normalizado.

## CISD estilo Triton (14,400 variantes)
H1 orderblock / H1 FVG / barrida de PDH-PDL, overnight o Londres → CISD en 1, 3 o 5 min → entrada a mercado, en FVG o retest del CISD; objetivo 0.5-3R o liquidez opuesta (London low, ON low, PDL); ventanas 8:30-12:00; con y sin tendencia.
- Mediana de PF < 1 en todas las ventanas, temporalidades, setups y objetivos (IS 0.91-0.99, REAL 0.83-0.89).
- De las 808 variantes buenas en IS, solo el 13% sigue con PF > 1 en MNQ real (base de todas las variantes: 14%) → **ventaja nula, sobreajuste puro.**
- Lo que sí funciona de esta idea ya está en NQMaster (módulo ICT). No tenemos datos de 30 segundos.

## 9 EMA + VWAP (1,152 variantes)
Pullback a la EMA9 del lado de la VWAP, cruce EMA9/VWAP, rebote en VWAP; 1/2/3/5 min.
- El pullback y el rebote pierden en todos los periodos (mediana de PF 0.86-0.96).
- Solo el cruce en 5 min (9:45-11:30) tiene una ventaja mínima: PF 1.10-1.30, WR 53-68%, ~0.6 trades/día; 11 años 1.05-1.27.
- En WR70Plus: +0.36 trades/día pero PF 1.502 → 1.471 y WR 71.5 → 71.0 → **no se agrega.**

## Engulfing 4H + NY (Omar, 2,304 variantes)
Vela 4H 02-06 que envuelve a la 22-02 → dirección; entrada en NY a mercado / ruptura 15m / ruptura de la vela 4H / ruptura del rango de 15 min; objetivo 0.5-2R.
- La familia tiene sesgo positivo desde 2020 (58-60% de las variantes con PF > 1), pero en 2015-19 solo el 38%.
- La mejor de WR alto (#411: ruptura de la vela 4H, stop en el otro extremo, 0.5R): WR 72.6 / 69.7 / 71.8%, PF 1.45 / 1.57 / 1.71, pero solo 0.1 trades/día y **PF 0.84 en 2015-19.**
- En la cartera WR70Plus el efecto es neutro (REAL PF 1.502 → 1.498; 2026 1.546 → 1.530). En Apex mueve el aprobado ±2 puntos (ruido) → **no se agrega.**

## Otras pruebas del mismo día
- Tope de posiciones simultáneas (`concur_eval.py`): baja PF y $/mes y no sube el aprobado → rechazado.
