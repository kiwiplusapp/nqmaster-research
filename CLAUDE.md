# NQMaster: trading algorítmico NQ / MNQ (NinjaTrader 8)

## Usuario
- El usuario es **Federico**. Empezá cada respuesta con su nombre ("Federico — ...").
- Respondé en español, directo, sin opiniones que no pidió. Ejecutá la tarea; si falta un dato, resolvelo vos.
- Sus instrucciones globales completas están en `claude/global-CLAUDE.md`.

## Primer paso en una sesión en la nube
Los datos grandes (historial de precios NQ / MNQ / oro / ES / euro / plata / petróleo y algunos sets de trades) están comprimidos como `.xz`. Si `research/data/nq_1m.npz` no existe, corré una vez:

```bash
bash tools/cloud_setup.sh
```

Instala los paquetes de `requirements.txt` y reconstruye los 26 archivos desde sus `.xz` (verifica SHA-256). `python3 tools/restore_data.py --check` solo verifica.

Si agregás o modificás un archivo de más de 40 MB, corré `python tools/compress_data.py` antes del commit: crea el `.xz`, actualiza `tools/data_manifest.json` e ignora el original en `.gitignore`.

## Estructura
- `NQMaster.cs`: la estrategia final de NinjaTrader 8 (perfiles Ultra, WR70Plus, Core, MaxSharpe, etc.). Guía: `NQMASTER_GUIA.md`. Backups: `NQMaster_backup_pre_*.cs`.
- Otras estrategias `.cs` y sus guías `*_GUIA.md`: versiones anteriores y módulos sueltos.
- `Conocimiento/`: base de conocimiento en Obsidian (empezar por `00 - MAPA.md`). `Mapa.canvas` y `.obsidian/` son la vista de Obsidian.
- `research/`: motor de backtest en Python (numpy + numba). `research/data/`: precios en 1 minuto (`*.npz` listos para usar, `*_utc.pkl` fuente). `research/mine/`: minería de estrategias, auditoría de robustez, simulaciones de prop firms (Apex, Lucid).
- `claude/memory/`: la memoria de Claude de este proyecto (veredictos de investigación, decisiones, resultados por fecha).
- `tools/`: compresión y restauración de datos, setup de la nube.

## Cómo correr la investigación
- Los scripts de `research/mine/` se corren desde su carpeta: `cd research/mine && python3 robust_lab.py`. Los de `research/` desde `research/`.
- `core.Data("nq_1m.npz")` carga los precios desde `research/data/`.
- Períodos estándar: IS = CFD 2020-23 (donde se elige todo), C24 = CFD 2024-26, REAL = futuros MNQ 2024-26, más 2015-19 (`nqhd_long.npz`) como prueba de régimen. Costos: $1,90 de comisión + 1 tick por lado.
- Regla de validación: una idea se acepta solo si funciona en IS, C24 y REAL sin re-optimizar.
- Los `patch_*.py` de `research/mine/` tienen rutas de Windows (`D:\NinjaTrader Strategy\...`): en la nube, cambialas por rutas relativas antes de correrlos.

## Compilar NQMaster.cs
Solo en la PC de Windows con NinjaTrader 8 (necesita sus DLL). En la nube se puede editar el `.cs`, pero la compilación se verifica en la PC: `csc.exe` con referencias a `NinjaTrader.Core.dll`, `NinjaTrader.Gui.dll` y `NinjaTrader.Custom.dll` (ver la memoria), o F5 en el NinjaScript Editor.

## Memoria del proyecto
@claude/memory/ifvg-sniper-nt8-project.md
