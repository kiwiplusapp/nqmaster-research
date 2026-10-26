---
name: validacion
description: Protocolo de validación de ideas y cambios de NQMaster (períodos, costos, criterios de aceptación, paridad con NinjaTrader, trampas conocidas). Usar antes de proponer, aceptar o rechazar cualquier módulo, filtro, parámetro, regla de riesgo o conclusión de investigación.
---

# Protocolo de validación

## Períodos y costos

| Etiqueta | Datos | Uso |
|---|---|---|
| IS | CFD 2020-23 (`nq_1m.npz`) | Único período donde se elige |
| C24 | CFD 2024-26 | Comprobación sin re-optimizar |
| REAL | Futuros MNQ 2024-26 (`mnq_fut.npz`) | Comprobación con datos reales |
| Régimen | `nqhd_long.npz` 2015-19 (y `nqdb.npz` real 2010-26) | Prueba de régimen, con costos normalizados (0,345% del ATR) |

Costos: $1,90 de comisión por contrato + 1 tick por lado. Prueba de estrés: +4 ticks.
Protocolo reciente (rondas de 2026-10): T1 elige (2020-23), T2 comprueba (2024-26), 2010-19 en costo normalizado como control.

## Regla de aceptación

Una idea entra solo si funciona en IS, C24 y REAL sin re-optimizar. Además, para tocar el sistema:

1. PF mínimo fijado antes de mirar (p. ej. T1 ≥ 1,3 y T2 ≥ 1,2) y sigue ≥ 1,1 con +4 ticks.
2. Plateau: los vecinos del parámetro (±20%, ±30 min) no colapsan.
3. Sumada al portafolio (con `conflict_filter`), sube el Sharpe en los dos períodos y el DD y el peor mes no suben más de 5%.
4. Registrar cuántas configuraciones se miraron: la tasa base de que algo pase T1 y T2 es 6-20% (`P(T2|T1)` ≈ 15-25%).
5. Control con características mezcladas (null shuffle) cuando se buscan filtros sobre trades.

## Trampas conocidas

- Simulaciones de entradas con límite: usar máquina de estados barra por barra. Cancelar el límite antes del fill en la misma barra infla el PF (bug de ICT, PF 1,53 vs 1,23).
- Lookahead típico: rango de la noche completa usado antes de tiempo, pivotes de timeframe mayor, `security()` de Pine, órdenes de prioridad dentro de la barra.
- Importar un script con trabajo a nivel de módulo lo vuelve a correr y puede borrar datos densos: usar `if __name__ == "__main__"`.
- Datos sin volumen o CFD sobrestiman: `mnq_fut.npz` y `nqdb.npz` son futuros reales. La réplica en CFD sobrestimó 2026 una vez.
- Las cifras de cuentas dependen de la ruta: usar bootstrap por bloques, no la media de un solo historial. Cotizar siempre edge completo, −35% y edge cero.
- Evaluaciones dentro de la misma firma y mismo camino de mercado están correlacionadas: no son pruebas independientes.

## Paridad con NinjaTrader

1. Strategy Analyzer: MNQ 1 min, Profile Ultra, Contracts 1, PropMode Off, desde 2024-01-01, comisión $1,90 + 1 tick. Exportar trades a CSV.
2. `cd research/mine && python3 parity_check.py <csv> --set ultra_d4`.
3. Compuertas: G1 ≥ 92% de trades emparejados, G2 $ dentro de ±3%, G3 correlación diaria ≥ 0,95, G4 cada módulo ≥ 90% si n ≥ 20.
4. Fallos conocidos: ICT (~82%, el límite de 5m llena más tarde en NT) y MSEQS (~56%, NT exige que ORB60 haya llenado). Cualquier otro fallo es un bug nuevo.
5. `research/mine/impl_gap.py` mide la brecha módulo por módulo en vivo.

## Chequeos de código

- `bash tools/nt8_stub/check.sh NQMaster.cs` (mcs, sintaxis C# 5 contra un stub). No sustituye F5 en NinjaTrader.
- NinjaTrader rechaza palabras contextuales como nombre de parámetro o identificador (`when`, `value`, `var`, `from`, `with`, `and`, `or`, `not`, `on`) aunque mcs las acepte.
- `python3 tools/check_guards.py` revisa los guards `__main__` de scripts importados.

## Conclusiones

Nunca afirmar que algo "no se puede mejorar" sin mostrar el experimento. El techo del edge por trade está documentado en `docs/historia/`. El del sistema no.
Antes de re-proponer una idea, buscarla en `docs/historia/ifvg-sniper-nt8-project.md` y en `Conocimiento/Descartado/`.
