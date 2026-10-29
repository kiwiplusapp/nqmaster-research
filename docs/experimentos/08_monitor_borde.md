# Experimento 08 (frente 5C): monitor de borde y respuesta a la alarma, re-validados sobre 2010-26 con el z corregido — 2026-10-29

**Veredicto (regla pre-registrada): sin cambio. La respuesta implementada en NinjaTrader (ante la alarma, 252 días sin los módulos cuyo PF de los 5 años previos es ≤ 1,05) sigue siendo la mejor con el z bien escalado.** Corregido el error de unidades de `os_adapt.py` (antes de 2020 dividía un P&L normalizado, que ya está en unidades de 2 × ATR × 100, otra vez por 2 × ATR), con el set vigente y los k / h vigentes (0,0899 / 26,93; aviso 9,22), el monitor alarma 4 veces en 2010-19 (2012-09-25, 2013-08-12, 2015-03-18, 2019-12-16; con el z de `os_adapt.py`, 5) y nunca en 2020-26. En 2013-19 (normalizado, la prueba de estrés) la respuesta implementada da Sharpe 1,25 y neto 9.766 contra 1,08 y 8.959 sin respuesta, 1,04-1,20 con pausas, y 1 año negativo en 2011-19 contra 2; en 2020-26 todas las políticas son idénticas porque el monitor no alarma. El medio tamaño con el aviso (WH) cuesta 9 / 8 % del neto en 2020-23 / 2024-26 por dos avisos sin edge muerto (2021-02 y 2023-07) y no pasa. Un solo camino histórico con 2-4 alarmas: la ventaja del fallback ($807 normalizados en 7 años) es frágil; lo que el experimento muestra es que el error de unidades no cambiaba la elección.

## Qué se corrió

`research/mine/exp08_monitor.py`: P&L diario por módulo del set vigente (Ultra = UltraR + CPI09 con MOM1030/CPI09 ×4, más SO04 / RV11 / ORFAIL / CAM3) desde 2010-07-01, sin FOMC; normalizado (costo 0,345 % del ATR) antes de 2020 y real ($1,90 + 1 tick por lado) desde 2020; z = normalizado / 100 antes de 2020 (verificado: normalizado / 100 = dólares / (2 × ATR), cociente 0,98-1,00 en 2020-26) y dólares / (2 × ATR) desde 2020, como en `NQMaster.cs`. El conjunto de revisión se calcula en la fecha de la alarma con los 5 años previos (sin mirar adelante). **Control:** con el set, el z y los k / h de `os_adapt.py`, la cantidad de alarmas coincide (9 sin respuesta, 4 con fallback) y el Sharpe del fallback en 2013-19 también (1,15); los netos difieren 1-3 % porque las listas de trades se regeneraron el 27-oct (tendencia y medias ruedas).

## Resultado (P&L diario por contrato base; 2013-19 en unidades normalizadas, 2020-26 en dólares)

| Política ante la alarma | Alarmas en 2010-26 | Días en respuesta | 2013-19: neto / Sharpe / DD | 2020-23: neto / Sharpe | 2024-26: neto / Sharpe | Años negativos 2011-19 |
|---|---|---|---|---|---|---|
| A: solo alerta | 2012-09-25, 2013-08-12, 2015-03-18, 2019-12-16 | 0 | 8.959 / 1,08 / 1.534 | 93.459 / 3,71 | 91.326 / 4,11 | 2 |
| **W252: fallback 252 días con el conjunto de revisión (implementado)** | 2012-09-25, 2015-05-19 | 504 | 9.766 / 1,25 / 1.263 | 93.459 / 3,71 | 91.326 / 4,11 | 1 |
| P63: pausa 63 días | 2012-09-25, 2013-08-27, 2015-06-22 | 189 | 8.238 / 1,04 / 1.802 | 93.459 / 3,71 | 91.326 / 4,11 | 2 |
| P126: pausa 126 días | 2012-09-25, 2013-12-12, 2015-06-24 | 378 | 7.765 / 1,04 / 1.860 | 93.459 / 3,71 | 91.326 / 4,11 | 2 |
| P252: pausa 252 días | 2012-09-25, 2015-05-19 | 504 | 8.631 / 1,20 / 1.263 | 93.459 / 3,71 | 91.326 / 4,11 | 1 |
| D252: Durable 252 días (dentro de muestra) | 2012-09-25, 2015-05-19 | 504 | 8.944 / 1,16 / 1.263 | 93.459 / 3,71 | 91.326 / 4,11 | 2 |
| WH: W252 + medio tamaño con el aviso | 2012-09-25, 2015-05-19 | 504 | 8.323 / 1,24 / 953 | 84.665 / 3,63 | 84.202 / 3,99 | 1 |

Avisos del monitor (z corregido): 2011-04-20, 2013-02-12, 2013-12-12, 2015-06-25, 2021-02-09, 2023-07-12. Por año, sin respuesta / con la implementada: 2012 425 / 729, 2013 -767 / -338, 2015 -742 / 240, 2016 3.242 / 2.637; el resto igual.

## Qué cambia

Nada en `NQMaster.cs`: la respuesta implementada queda. Se corrige el registro: `os_adapt.py` tenía un error de unidades antes de 2020 que no cambiaba la elección. **Límite que queda documentado:** con edge muerto el monitor tarda ~246 días en alarmar (`monitor_recal3.json`) y la respuesta solo apaga los módulos débiles; junto con el experimento 07, el sistema no tiene protección automática contra un edge muerto durante el primer año de campaña.

Archivos: `research/mine/exp08_monitor.py`, `exp08_monitor.json`; plan `docs/PLAN_2026-10-29_exp08.md`.
