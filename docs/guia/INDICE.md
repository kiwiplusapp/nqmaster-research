# Guía de NQMaster: índice

`NQMASTER_GUIA.md` (1.870 líneas, cronológica) se partió por tema el 2026-10-26.
El texto no cambió. Dentro de cada archivo las secciones siguen el orden original,
así que lo más nuevo suele estar arriba en `changelog.md` y `reglas-prop.md`.

| Archivo | Qué contiene | Cuándo leerlo |
|---|---|---|
| `modulos.md` | Perfiles (Ultra, WR70Plus, Durable, Custom), módulos NF05/LF06/LATE15, confluencia, monitor de ventaja, uso básico | Antes de tocar un módulo o un perfil |
| `reglas-prop.md` | Reglas y presets de Lucid / MFFU / Apex, planes de cuentas, tamaño por fase, pasar evaluación, retiros | Antes de elegir cuenta, preset o tamaño |
| `validacion.md` | Auditorías, revisiones de código 1-5, bugs corregidos, paridad NT vs investigación, ideas descartadas | Antes de proponer algo que quizá ya se probó |
| `changelog.md` | Rondas de cambios por fecha: panel y ciclo de cuenta (21-oct), overhaul (12-oct), seis años (16-oct), UltraQ/CPI09, order flow, warm-up | Para saber qué cambió y cuándo |

## Por dónde empezar

1. Estado actual y problemas abiertos: `docs/ESTADO.md`.
2. Qué se hace a diario: `RUNBOOK_OPERACION.md`.
3. Qué reglas usa cada firma: `.claude/skills/prop-rules/SKILL.md`.
4. Cómo se valida una idea: `.claude/skills/validacion/SKILL.md`.

## Otros documentos

- `docs/historia/`: memoria del proyecto con los veredictos de investigación por fecha.
- `Conocimiento/`: base Obsidian (`00 - MAPA.md`), incluye `Descartado/`.
- `archive/legacy/`: estrategias viejas con sus guías.
- `archive/backups/`: copias `*_backup_pre_*.cs` de cada parche.
- `research/mine/*.md`: informes de cada experimento.

## Convenciones

- Cifras de investigación = 1 contrato base, costos $1,90 + 1 tick por lado.
- Las cifras con "−35%" son el recorte de edge usado como caso realista.
- Nada de lo descrito está compilado en NinjaTrader salvo que la sección lo diga.
