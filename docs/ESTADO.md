# Estado de NQMaster (2026-10-26)

Leer esto primero. Detalle por tema en `docs/guia/INDICE.md`, historia de decisiones en `docs/historia/`.

## Qué es hoy

- Una sola estrategia de NinjaTrader 8 (`NQMaster.cs`, ~2.800 líneas) que opera NQ/MNQ en 1 minuto, con una serie interna de 5 minutos.
- Corre unos 20 módulos en paralelo: ORB60/90, MOM11, MOM1030, CRT11, ICT, VOLB, LON, módulos nocturnos (NF05, LF06, LF0430, ON07, REV06), CPI09 y cuatro módulos de seis años.
- Solo NQ. GoldMaster está en `archive/legacy/` y no se usa.
- Tiene panel en español, motor de ciclo de cuenta (`PropCycle`), guarda entre cuentas, monitor de ventaja y capas de seguridad operativa.
- Los módulos y el motor de cuentas están descritos en `docs/guia/modulos.md` y `docs/guia/reglas-prop.md`.

## Perfil activo

- Perfil **Ultra** (el default), con `SixYearModules` en true: SO04, RV11, ORFAIL y CAM3. Es el conjunto que la investigación llama `ultra_d4`.
- CPI09 y los multiplicadores x4 de MOM1030 y CPI09 están activos.
- Alternativas: WR70Plus, Durable (6 módulos, defensivo) y Custom.
- Defensa ante alarma de edge: `DisableModules = MOM1030,MOM13,REV06`.
- Sin multiplicador de order flow ni re-entrada de VOLB: ambos están apagados y falló su validación.

## Firmas y presets en uso

| Plan | Preset | Notas |
|---|---|---|
| 5 cuentas Lucid Flex 150K | `Lucid150K` | Eval 6 contratos, fondeada 3. Tope de 5 fondeadas por hogar |
| 3 cuentas MFFU Rapid EOD 50K | `Mffu50K` | Eval y fondeada a 1 contrato. Apagón de noticias en fondeada |
| Alternativa de 50K rápida | `LucidPro50K` | Eval 4 contratos, no está en el plan base |

- Misma firma, mismo perfil, misma PC. Lucid y MFFU prohíben posiciones opuestas entre cuentas propias.
- Reglas exactas en `.claude/skills/prop-rules/SKILL.md`. Operación diaria en `RUNBOOK_OPERACION.md`.
- Apex y Topstep quedaron fuera por prohibir automatización o exigir su plataforma.

## Métricas honestas

Son las del nivel de planificación (perturbaciones de ±20% en todos los parámetros), no las del mejor backtest.

| Métrica | Valor |
|---|---|
| Sharpe | ~2,5 (el backtest puntual da 3,6) |
| Profit factor | ~1,3 (el backtest da 1,5) |
| Drawdown máximo | ~$5.600 por contrato base |
| Win rate | ~65% |
| Ingreso por contrato base | mediana ~$29k al año con edge completo, ~$19k con 35% menos |

- El edge es de régimen posterior a 2020. Antes de 2020, con costos normalizados, es débil o nulo.
- Con edge cero, el sistema pierde unos $130 al mes por cuenta en fees.
- Cotizar siempre tres casos: edge completo, −35% y edge cero.

## Cinco problemas abiertos

1. **Paridad NT fallida en ICT y MSEQS.** ICT empareja ~82% de los trades y MSEQS ~56%. NT llena los límites de 5m más tarde y exige que ORB60 haya llenado. Impacto chico (~$24/mes en MSEQS), pero `parity_check.py` falla G4. Causas en `docs/guia/validacion.md`.
2. **Cambios del 21-oct sin compilar.** Panel nuevo, `PropCycle`, guarda entre cuentas (C6) y reinicio de presets pasaron solo el stub de C# 5. Falta F5 en la PC, un Strategy Analyzer con `parity_check.py --set ultra_d4` y la prueba en Playback. No comprar cuentas antes.
3. **Fragilidad horaria.** Correr 15 minutos un módulo de reloj baja el Sharpe del portafolio entre 0,3 y 0,7 (CRT11, MOM11, MOM1030, CPI09). Si la zona horaria ET queda mal tras un cambio de horario de verano, el edge desaparece. Chequear el reloj de barras en cada DST.
4. **Meses malos de la campaña.** Agosto-2026 dio −$3.700 por contrato y el verano 2026 quemó el 59-88% de las fondeadas nuevas en 60 días. Un drawdown de $3.700 no cabe en un trailing de $2.000. No hay filtro de régimen que lo evite: la autocorrelación es ~0.
5. **Panel sin datos de riesgo de cuenta.** Según tu lista, el panel no muestra el riesgo de la cuenta. Qué mostrar está sin definir. El runbook ya cita el colchón y el monitor de borde como lo que se mira a diario. Revisar el panel contra eso antes de diseñar nada.

## Siguiente paso

Cerrar el punto 2: F5, parity en Strategy Analyzer y una eval de prueba. Hasta entonces, las cifras de cuentas son de investigación.

## Dónde mirar

- Datos y comandos: `CLAUDE.md`. Protocolo de validación: `.claude/skills/validacion/SKILL.md`.
- Ideas descartadas: `Conocimiento/Descartado/` y `docs/historia/ifvg-sniper-nt8-project.md`.
- Versiones anteriores del código: `archive/backups/` y `archive/legacy/`.
