# Estrategias anteriores (archivos en la bóveda)
Volver a [[00 - MAPA]]

| Archivo | Qué es | Estado |
|---|---|---|
| IFVGSniperStrategy.cs | Port del IFVG | ❌ sin ventaja |
| NYOpeningRangeTrend.cs / NQTrendDayPro.cs | ORB + VWAP (v2/v3) | Reemplazado |
| NQSessionDrift.cs | Drift RTH y nocturno | ❌ se debilitó desde 2024 |
| MomentumSequencePro.cs | MSEQ solo | Integrado en NQMaster |
| NQPullbackDayEngine.cs | ORB/VWAP en días de retroceso + MSEQ | Integrado |
| NQCrt11.cs · NQMom11.cs · NQTimeMom.cs · NQLondonFvg.cs · NQIctOpen.cs | Módulos individuales | Integrados |
| NQAccountGuard.cs | Guardián separado | Integrado |
| **NQMaster.cs** | **Todo en uno** | ✅ **usar este** |
| BarExporterUTC.cs | Exportador de datos | Herramienta |

Guías: PORTAFOLIO_V8.md, NQMASTER_GUIA.md, PORTAFOLIO_DIARIO.md, RESULTADOS.md.
