# Plan 5 × 150K y módulos nocturnos (7-oct-2026)
Volver a [[00 - MAPA]] · Anterior: [[Perfil final 6-oct (50K, 2 contratos)]] · Guía: `NQMASTER_GUIA.md`, sección "★★ PLAN RECOMENDADO"

## El límite que cambia todo
Lucid permite **5 cuentas fondeadas por hogar** (10 en total, $750K combinados). Con ese tope importa el dinero **por cuenta**, y la 150K gana:

| Cuenta (contratos eval / fondeada) | $/mes por cuenta | Peor de 9 pruebas |
|---|---|---|
| **150K 6 / 3 + módulos nocturnos** | **$2.168** | $1.981 |
| 150K 6 / 3 | $1.984 | $1.723 |
| 50K 2 / 2 | $1.311 | $1.160 |

- **5 × 150K:** $9.800-12.500 por mes; año malo (10% peor) $5.300-7.100; P(año en pérdida) ≤ 0,7%.
- **Contratos:** el peor día llega a 66 micros con 6 contratos (límite de la evaluación: 100) y a 33 con 3 contratos (la fondeada arranca con 40).

## Módulos nocturnos nuevos (revertir la madrugada)
Probé en el Nasdaq las familias que había encontrado para el oro: ~16.000 configuraciones. El filtro fue estricto: 2020-23 y 2024-26, futuros reales, 2015-19 (nunca usado para elegir), +4 ticks de deslizamiento, mejora del Sharpe del portafolio en los 3 períodos y del dinero por cuenta.
- **NF05:** a las 05:00, si el precio se movió ≥ 0,35 ATR desde las 20:00, operar en contra. Stop 0,2 ATR, objetivo 2R. PF 1,61 en 2015-19.
- **LF06:** a las 06:00, si se movió ≥ 0,2 ATR desde las 04:00, operar en contra. Stop 0,2 ATR, objetivo 0,5R. Win rate 74%.
- **LF0430:** a las 04:30, si se movió ≥ 0,1 ATR desde las 04:00, operar en contra y a favor de la tendencia. Stop 0,35 ATR, objetivo 0,5R.
- **Resultado:** el Sharpe del portafolio pasa de 3,12-3,59 a 3,31-3,71, con el mismo win rate.

**Lección:** en la madrugada del Nasdaq funciona **revertir**. Las rupturas nocturnas no funcionan: 0 de 1.536 configuraciones pasaron.

## Descartado
- Filtrar un lado (solo largos o solo cortos) por módulo.
- Más módulos de oro.
- Subir a 3 contratos en la fondeada.
- Evaluaciones de repuesto en paralelo: pasan o fallan juntas.
- Momentum anclado a las 09:30: repite MOM11 y MOM1030.

## Código
Tres rondas de revisión con agentes. La más importante: las órdenes que un trade opuesto cancela o bloquea ahora quedan en espera y vuelven cuando se libera el lado contrario, como en la investigación.

Herramienta nueva: `research/mine/nt_compare.py` compara módulo por módulo una exportación de trades de NinjaTrader contra la investigación.
