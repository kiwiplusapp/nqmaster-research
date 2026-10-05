# Filtros y optimizaciones rechazadas
Volver a [[00 - MAPA]]
- **Filtros por módulo** (día de semana, volatilidad, gap, retornos): el Sharpe sube de 2.84 a 3.64 en 2020–23, pero no cambia en datos reales → sobreajuste.
- **Filtro de rango nocturno**: miraba el futuro. Corregido, no aporta nada.
- **Optimizar pesos**, **targets más chicos** (el win rate sube pero el PF baja), **breakeven**, **tamaño según volatilidad**, **límites diarios**: ninguno mejora.
- **Sacar módulos**: solo VWAP60 restaba (desactivado); el resto suma.

## Ronda 28-sep (tarde)
- **Régimen de VIX** (cierre del día anterior): con VIX ≤ 15 el portafolio rinde menos (PF 0.91 / 1.23 / 1.19) y con VIX > 25 más (1.48 / 1.70 / 1.62). Pero ni ajustar el tamaño ni saltarse días según el VIX mejora el Sharpe de forma consistente. ❌
- **Calendario**: OPEX, vencimiento trimestral, primer y último día del mes, lunes y viernes. Ningún día conviene saltarlo. Duplicar el tamaño el primer día del mes no mejora de forma consistente. ❌
- **Apagar un módulo después de una mala racha** (PF de los últimos 20, 40 o 60 trades menor a 1): **empeora** (Sharpe real 3.41 → 2.98–3.18). Las rachas malas se revierten, así que **no hay que apagar módulos por rachas**. ❌
