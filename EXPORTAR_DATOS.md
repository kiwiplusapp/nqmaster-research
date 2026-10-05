# Exportar el historial real de MNQ desde NinjaTrader (para hacer backtests con tus datos)

El archivo que mandaste (`MNQ 12-26.Last.txt`) solo trae datos del 13 al 28 de septiembre de 2026, porque exporta un único contrato. Para tener todo desde 2024 hay que exportar la serie continua:

1. **Tools → Options → Market Data → Merge policy = "Merge back adjusted"** → OK.
2. **Tools → Historical Data → Load**: instrumento `MNQ 12-26`, tipo **1 Minute**, desde **01/01/2024** hasta hoy → **Download**. Espera a que termine.
3. En NinjaTrader abre **New → NinjaScript Editor**, abre el indicador **BarExporterUTC** (ya está instalado) y pulsa **F5** para compilar.
4. Abre un gráfico:
   - Instrumento `MNQ 12-26`, **1 Minute**, Trading hours **CME US Index Futures ETH**.
   - Load data based on: **Custom range**, desde **01/01/2024** hasta hoy.
5. Agrega el indicador **BarExporterUTC** (clic derecho → Indicators). Cuando termine de cargar, en **New → NinjaScript Output** vas a ver: `historical export done: N bars -> ...export_MNQ_12-26_1Minute.csv`.
6. Mándame ese archivo, que queda en `Documents\NinjaTrader 8\export_MNQ_12-26_1Minute.csv`.

Con ese archivo corro todos los backtests sobre los mismos datos que usa tu Strategy Analyzer.
