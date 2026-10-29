# Disposición de la revisión de código completa de NQMaster.cs (29-oct)

Informe del revisor tal cual: `code_review_nqmaster_2026-10-29.md` (misma carpeta). Correcciones en `research/mine/patch_live_safety.py` (+ `patch_clock_check.py` v3); todo lo que puede cambiar órdenes corre solo en vivo. `check.sh` verde; la cadena backup + 5 parches regenera `NQMaster.cs`; falta F5.

| Hallazgo | Severidad | Qué se hizo |
|---|---|---|
| Doble salida / overfill deja una posición inversa sin stop | alta | **Corregido:** ejecución de salida con más lotes que los del módulo → alerta `OVERFILL` y aplanado; control por barra de lotes sin dueño (2 barras) → alerta y aplanado; `ExitModule` no manda una segunda salida mientras la primera trabaja; `IgnoreOverfill = true`. Simulacro en Sim en el runbook. |
| Estado de la cuenta prop faltante → colchón sobrestimado | alta | **Corregido:** sin archivo legible y con saldo distinto del inicial → `PROP STATE UNKNOWN`, colchón chico (tope de riesgo activo) y sin guardar el pico hasta cargar un override; aviso en cada sesión mientras `PropThresholdOverride` esté cargado. |
| Monitor de borde: descarta el estado guardado en silencio; deja de alarmar desde feb-2027 | media | **Parcial:** ahora avisa cuando descarta el estado (runbook: dejar NinjaTrader corriendo a las 18:00 ET). **Pendiente** antes de feb-2027: reaplicar el estado guardado más los días posteriores del histórico, y un archivo por perfil y grupo. |
| Deshabilitar / editar con posición abierta la deja sin stop; se borra el archivo de posiciones | media | **Corregido en parte:** alerta sonora `STOPPED WITH AN OPEN POSITION` y no se borra el archivo si la cuenta está posicionada; regla en el runbook (no deshabilitar con posición; revisar la opción de NinjaTrader que cancela las salidas al deshabilitar). |
| `ConnectionLossHandling` no fijado | media | **Pendiente:** simulacro de desconexión en Sim (runbook) antes de fijarlo; sin probarlo no se cambia el valor por defecto. |
| Guarda entre cuentas falla abierta | media | **Corregido en parte:** publica en cada ejecución (salidas) y, antes de armar el control de sincronización, el signo de la posición de la cuenta. La relectura con reintentos y las señales opuestas en la misma barra quedan para el Playback de 2 cuentas (runbook). |
| Eval nueva con el mismo nombre hereda el mejor día | baja | **Runbook** (EvalStartDate = hoy o borrar el archivo). |
| Cuenta simulada por nombre | baja | **Runbook** (primer día: "EN VIVO" y "CUENTA REAL"). |
| Roll una sesión tarde | baja | **Corregido** (día de operación de la sesión). |
| Barras tardías sin alerta | baja | **Corregido** (alerta tras 3 seguidas). |
| Retiro debitado en sesión dispara el stop diario de la escalera | baja | **Runbook** (retiros con la estrategia deshabilitada y plana, fuera de sesión). |
| `Time[0]` fuera de try en el control de reloj | baja | **Corregido** (`patch_clock_check.py` v3, `Times[0][0]`). |
| `NQAccountGuard.cs` con archivo de pausa global | baja | **Runbook** (no se usa con este plan). |
| Eval de Lucid 150K se puede perder en un solo trade (por diseño) | info | Sin cambio (validado en la campaña); el panel de riesgo abierto lo muestra. |
