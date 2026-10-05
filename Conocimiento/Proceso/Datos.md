# Datos
Volver a [[00 - MAPA]]

| Dataset | Origen | Período | Uso |
|---|---|---|---|
| NQ CFD 1m | Dukascopy USATECHIDXUSD | 2020–2026 | In-sample y validación larga |
| NQ histdata | histdata.com | 2020–2026 | Comprobación cruzada |
| **MNQ / NQ futuros reales** | Exportación propia (BarExporterUTC) | 2024-01 → 2026-09 | **Validación real** |
| **MGC futuros reales** | Exportación propia | 2024-01 → 2026-09 | Validación del oro |
| XAUUSD 1m | histdata.com | 2020–2026 | Historia larga del oro |
| FOMC / CPI / NFP | federalreserve.gov / BLS | 2020–2026 | Filtro de noticias |

- Exportador: `BarExporterUTC.cs` (indicador) → `Documents\NinjaTrader 8\export_*.csv`, con timestamps UTC al cierre de la vela.
- Conversión: `research/prep_nt.py`. Los precios del oro se escalan ×2.5 para que 1 tick = 0.25.
- CFD y futuros reales: correlación de retornos de 1 minuto 0.994. Los futuros tienen rangos ~8% más amplios.
