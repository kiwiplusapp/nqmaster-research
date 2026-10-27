# NQMaster: trading algorítmico NQ / MNQ (NinjaTrader 8)

Federico es el usuario. Empezá cada respuesta con "Federico — ...", en español y directo. Si falta un dato, resolvelo vos.
Antes de trabajar leé `docs/ESTADO.md` (estado y 5 problemas abiertos). Reglas de git: commit local siempre, `git push` solo si él lo pide.

## Comandos

```bash
bash tools/cloud_setup.sh                       # una vez: pip install + reconstruye los datos .xz (si falta research/data/nq_1m.npz)
python3 tools/restore_data.py --check           # solo verifica SHA-256
cd research/mine && python3 parity_check.py <csv de Strategy Analyzer> --set ultra_d4_mnq   # paridad NT vs investigación (set sobre MNQ; ultra_d4 = set de campaña sobre NQ)
bash tools/nt8_stub/check.sh NQMaster.cs        # chequeo de sintaxis C# 5 contra un stub
python3 tools/propcycle_test/run_test.py        # tras tocar PropCycle: tiene que dar 0 diferencias
python tools/compress_data.py                   # antes de commitear cualquier archivo > 40 MB
```

- Los scripts de `research/mine/` se corren desde su carpeta, los de `research/` desde `research/`. `core.Data("nq_1m.npz")` carga desde `research/data/`.
- Los `patch_*.py` traen rutas de Windows (`D:\NinjaTrader Strategy\...`): pasalas a rutas relativas. Los backups que leen están ahora en `archive/backups/`.
- Un script de `research/mine/` que se importa y trabaja a nivel de módulo se re-ejecuta y puede borrar datos densos: usá `if __name__ == "__main__"`.

## Compilar

`NQMaster.cs` solo se compila en la PC de Windows con NinjaTrader 8 (F5 en el NinjaScript Editor). En la nube el stub chequea sintaxis, no sustituye F5.
NinjaTrader rechaza palabras contextuales como nombre de parámetro (`when`, `value`, `var`, `from`, `with`, `and`, `or`, `not`, `on`) aunque mcs las acepte.

## Períodos y costos

- IS = CFD 2020-23 (acá se elige todo). C24 = CFD 2024-26. REAL = futuros MNQ 2024-26. Régimen = 2015-19 (`nqhd_long.npz`) y `nqdb.npz` (NQ real 2010-26).
- Costos: $1,90 de comisión por contrato + 1 tick por lado. Estrés: +4 ticks.
- Detalle del protocolo: `.claude/skills/validacion/SKILL.md`.

## Reglas

- **Validación:** una idea entra solo si funciona en IS, C24 y REAL sin re-optimizar.
- **Techo:** nunca afirmes que algo no se puede mejorar sin mostrar el experimento que lo prueba. El techo del edge por trade está documentado en `docs/historia`; el del sistema no.
- **Antes de proponer:** buscá la idea en `docs/historia/ifvg-sniper-nt8-project.md` y `Conocimiento/Descartado/`. Muchas ya se probaron.
- **Cifras de cuentas:** dá tres casos (edge completo, −35% y edge cero). No prometas ingresos.
- **Simulaciones:** máquina de estados barra por barra. Un fill con lookahead dio un edge falso más de una vez.

## Dónde está cada cosa

- `NQMaster.cs`: la estrategia (perfiles Ultra, WR70Plus, Durable, Custom). También `NQAccountGuard.cs`, `OrderFlowRecorder.cs`, `BarExporterUTC.cs`.
- `docs/ESTADO.md`: estado actual. `docs/guia/INDICE.md`: guía por tema. `docs/historia/`: veredictos por fecha. `RUNBOOK_OPERACION.md`: operación diaria.
- `.claude/skills/prop-rules/`: reglas de Lucid Flex 150K y MFFU Rapid 50K. `.claude/skills/validacion/`: protocolo de validación.
- `Conocimiento/`: vault de Obsidian (`00 - MAPA.md`; `Descartado/` lista lo rechazado). `Mapa.canvas` y `.obsidian/` son su vista.
- `research/`: motor de backtest (numpy + numba). `research/data/`: precios en 1 minuto. `research/mine/`: minería, auditorías, simulación de cuentas.
- `archive/legacy/`: estrategias viejas y sus guías. `archive/backups/`: copias `*_backup_pre_*.cs`. No se editan.
- `claude/global-CLAUDE.md`: instrucciones globales de Federico.
