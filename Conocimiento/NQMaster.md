# NQMaster: la estrategia final
Volver a [[00 - MAPA]]

Archivo: `NQMaster.cs` (compilado e instalado).

## Configuración
| Gráfico | Profile | Parámetros |
|---|---|---|
| MNQ 1 min (ETH) | **MaxSharpe** (o WinRate70) | Contracts 1, Skip FOMC ✔, Eval target 3000 (eval), Max drawdown 2000, Buffer 250 |
| MGC 1 min (ETH) | **Gold** | Contracts 1 |

## Perfiles
- **MaxSharpe**: [[ORB60 Pullback Day]] 0.6R + [[MSEQ Momentum Sequence]] + [[CRT11]] + [[MOM11]] + [[Modulos por horario]] + [[LON London FVG]] + [[ICT Open]].
- **WinRate70**: sin LON, MOM13 ni oro; ORB60 a 0.75R → ~69–71% de win rate.
- **Gold**: [[GOLD ORB30]].

## Detalles técnicos
- Órdenes managed, una señal por módulo. No opera en contra de una posición abierta. Si hay una orden opuesta pendiente, la cancela y entra en la vela siguiente.
- Agrega por su cuenta una serie de 5 minutos (para MSEQ e ICT).
- Incluye [[Account Guard]].

Resultados: [[Resultados NinjaTrader]]. Estrategias anteriores: [[Estrategias legacy]].
