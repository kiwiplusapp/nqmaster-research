# NQMaster

Estrategia algorítmica para futuros del Nasdaq (MNQ / NQ) en NinjaTrader 8, con toda la investigación que la respalda.

## Contenido
| Carpeta / archivo | Qué es |
|---|---|
| `NQMaster.cs` | Estrategia final (NinjaTrader 8). Guía de uso en `NQMASTER_GUIA.md`. |
| `Conocimiento/` | Base de conocimiento (Obsidian). Empezar por `00 - MAPA.md`. |
| `research/` | Backtests en Python, minería de estrategias, auditorías y simulaciones de prop firms. |
| `research/data/` | Historial de precios en 1 minuto: Nasdaq (CFD 2015-2026, futuros MNQ/NQ 2024-2026), oro (CFD y futuros MGC), S&P, euro, plata y petróleo. |
| `claude/` | Memoria e instrucciones de Claude para este proyecto. |
| `tools/` | Compresión y restauración de los datos grandes. |

## Empezar (nube o PC nueva)
```bash
git clone https://github.com/kiwiplusapp/nqmaster-research.git
cd nqmaster-research
bash tools/cloud_setup.sh
```
`cloud_setup.sh` instala las dependencias de Python y descomprime los 26 archivos de datos grandes (guardados como `.xz`, ~400 MB en el repo, ~3,1 GB descomprimidos). Cada archivo se verifica con SHA-256.

## Trabajar desde la nube con Claude Code
1. Abrí [claude.ai/code](https://claude.ai/code) y elegí este repositorio.
2. En la configuración del entorno, poné como script de setup: `bash tools/cloud_setup.sh`.
3. Claude lee `CLAUDE.md` y la memoria de `claude/memory/` al empezar cada sesión.

NinjaTrader solo corre en Windows: la estrategia se edita en la nube, pero se compila y se opera en la PC.
