# Disposición de la revisión de `patch_panel_risk.py` (frente 5E, 30-oct)

El informe del revisor está tal cual en `revision_panel_risk.md`, en esta misma carpeta. Veredicto: **F5 sí**. El parche es solo panel: no cambia órdenes, estado ni el Output de paridad, y no puede lanzar excepciones. Los hallazgos son de texto y se corrigen en la v2 del parche.

| Hallazgo | Severidad | Qué se hizo en la v2 |
|---|---|---|
| El objetivo de la eval usa el saldo sin lo no realizado; el chequeo, con lo no realizado | Low | **Corregido:** el panel usa el mismo saldo con lo no realizado que el chequeo del objetivo. |
| "Se activa con colchón menor a X" cuando el tope se decide con el colchón al abrir la sesión | Low | **Corregido:** el texto dice "si el colchón al abrir la sesión es menor a X". |
| "Contratos base hoy" no es lo que opera (MOM1030 y CPI09 ×4, ×8 en la eval de MFFU) | Low | **Corregido:** pasa a decir "Lotes por módulo hoy N", con los lotes de MOM1030 y CPI09 según `HwQty`, salvo con `noBoost`. |
| En la eval no se muestra el tope de riesgo | Low | **Corregido:** se muestra en la eval cuando `EvalRiskCapCushion` > 0 (en los presets vale 0). |
| "Hasta mañana" no es exacto | Low | **Corregido:** "hasta la próxima sesión (18:00 ET)", en los estados, en "DETENIDO" y en el runbook. |
| Traducciones de la noticia y de la guarda entre cuentas incompletas | Low | **Corregido:** "sin posiciones ni entradas" y "la posición o una entrada opuesta". |
| La línea "Cada día" del runbook | Info | **Corregido:** aclara qué fases tienen stops del día y la salvedad de las alertas de aplanado. |
| Las líneas nuevas no aparecen en Sim ni en Playback | Info | **Runbook:** en "Primer día de cada cuenta", revisar esas líneas en la cuenta real. |
| `StartsWith` sin `Ordinal` | Nit | **Corregido.** |
| Un chequeo automático de estados sin traducir | Info | **No hecho:** hoy cubre los 16, y un estado nuevo se ve en inglés en el panel sin romper nada. |

Además, la v2 detecta un `NQMaster.cs` que trae la v1 y pide regenerar desde el backup.

Verificación: `check.sh` 0; `cr_fmtcheck` 132 llamadas, 0 sospechosas; la cadena de 7 parches se regenera desde el backup y es idempotente.
