# Auditoría de robustez NQMaster (2026-10-03)

Página: https://claude.ai/artifact/8FesKUvF4JKEYCPwdaSJ2X · código: research/mine/robust_build.py, robust_lab.py, robust_monitor.py, robust_report.py

## Las diez pruebas (Ultra; CFD 2020-23 / CFD 2024-26 / MNQ real 2024-26)

- **Sobreajuste:**
  - Elegir "la mejor" del minero: PBO 40%; el Sharpe cae de 2.05 a 0.59 fuera de muestra.
  - Variantes por módulo: CRT11 2%, LON 0.1%, MSEQ 0.1%, ICT 16%. ORB60 y ON07 ~50%, porque sus variantes son casi iguales.
- **Fuera de muestra:** Sharpe 3.09 / 3.43 / 3.61. Sharpe deflactado con 50.000 intentos: ~100% en CFD y 95% en MNQ real.
- **Más parámetros:** Core6 (6 módulos de 11 años) da Sharpe 2.45 / 2.94 / 2.88. Ultra es mejor en todos los períodos; Core queda de respaldo.
- **Costos:** con +4 ticks por lado Ultra sigue en PF 1.30 / 1.35 / 1.39. Para PF 1 harían falta 15-23 ticks por lado.
- **Mesetas:** el PF cambia de forma suave con el objetivo R en todos los módulos.
- **Régimen:**
  - Todos los años 2020-26 dan PF > 1, y todos los tercios de ATR y VIX también.
  - Días de tendencia: PF 2.7. Días de rango: PF 0.74-0.85. **Riesgo principal: un mercado lateral prolongado.**
  - En 2015-19 solo el 5% de los días tenía ATR ≥ 150, así que el filtro bloquea ese régimen. En esos días el PF fue 1.42.
- **Drawdown (1 lote, un año tipo 2024-26):** típico $4.8k; 1 de cada 20 años $6.8k; 1 de cada 100 años $8.6k. Meses negativos: 18%.
- **Correlación:** media 0.03-0.04; los 14 módulos equivalen a 12.3 apuestas independientes.
- **Evidencia:** 2,924 trades en MNQ real equivalen a ~380 días independientes. Sharpe al 5-95%: 2.4-4.8.
- **En vivo:** monitor CUSUM agregado a NQMaster (ver NQMASTER_GUIA.md, sección "Perfil Core y monitor de ventaja").
