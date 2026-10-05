# Grabador de order flow (OrderFlowRecorder)

Indicador para NinjaTrader 8 (`OrderFlowRecorder.cs`, ya instalado; presioná F5). Guarda por minuto el flujo de órdenes real del futuro, sin exportar nada a mano.

## Cómo usarlo
1. En NinjaTrader: **Tools > Options > Market data** → tildá **Show Tick Replay**.
2. Abrí un gráfico de **MNQ de 1 minuto**. En *Data Series* tildá **Tick Replay** y cargá todos los días que permita tu proveedor de datos (probá 180-365).
3. Agregá el indicador **OrderFlowRecorder**. Va a tardar: recorre cada tick histórico una vez.
4. Hacé lo mismo en un gráfico de **MGC**.
5. Dejalo en el gráfico: después sigue grabando en vivo. Si lo reiniciás, continúa donde quedó.

Los archivos quedan en `Documents\NinjaTrader 8\orderflow\` (uno por instrumento). Pasámelos o copialos a `research/data/orderflow/` y los analizo.

## Qué guarda (por minuto, en hora UTC)
- Apertura, máximo, mínimo, cierre y volumen.
- **Volumen comprador** (operaciones al precio de venta o más arriba) y **vendedor** (al precio de compra o más abajo), y el **delta**.
- Cantidad de operaciones y volumen de **operaciones grandes** por lado (≥ 10 contratos; se cambia en *Large trade size*).
- Máximo y mínimo del delta acumulado dentro del minuto.
- Tamaño promedio del mejor bid y del mejor ask, y spread promedio.

## Qué voy a investigar con esos datos
- Si el delta y las operaciones grandes en la entrada separan los trades buenos de los malos de cada módulo de NQMaster y GoldMaster.
- Absorción (mucho volumen sin avance del precio) en los niveles que usan ORB, ICT y CRT.
- Divergencias entre el delta y el precio en la apertura de Nueva York.

## Alternativa con más historia
**Databento** vende el historial tick a tick de CME con el lado agresor (años de NQ/MNQ). La cuenta nueva trae crédito gratis. Si abrís una cuenta y descargás los datos "trades" de MNQ (o me pasás los archivos), puedo trabajar con varios años en vez de meses.
