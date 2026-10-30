# Disposición de la revisión de código completa de NQMaster.cs (29-oct)

Informe del revisor tal cual: `code_review_nqmaster_2026-10-29.md` (misma carpeta). Correcciones en `research/mine/patch_live_safety.py` v2 (+ `patch_clock_check.py` v3); todo lo que puede cambiar órdenes corre solo en vivo. `check.sh` verde; la cadena backup + 5 parches regenera `NQMaster.cs`; falta F5. La v1 del parche pasó por una revisión adversarial propia (`revision_patch_live_safety_v1.md`, tal cual); su disposición está más abajo y la tabla de arriba ya describe la v2.

| Hallazgo | Severidad | Qué se hizo |
|---|---|---|
| Doble salida / overfill deja una posición inversa sin stop | alta | **Corregido:** ejecución de salida con más lotes que los del módulo → alerta `OVERFILL` y aplanado; control por barra de lotes sin dueño (2 barras) → alerta y aplanado; si en 3 barras no queda plano, `Account.Flatten` del instrumento; `ExitModule` no manda una segunda salida mientras la primera trabaja (la suprimida se reintenta; vigía de 3 barras); `IgnoreOverfill = true` en SetDefaults y Configure. No se puede provocar en Sim: prueba de falsos positivos con los dos Playback ya hechos (runbook). |
| Estado de la cuenta prop faltante → colchón sobrestimado | alta | **Corregido (v2):** sin archivo legible, o con un archivo anterior a la sesión previa cuyo saldo guardado no coincide con el de hoy, y con saldo distinto del inicial → `PROP STATE UNKNOWN`: en la fondeada, tope de riesgo activo y sin escalón de MFFU; nada se guarda hasta cargar un override. En la eval no hay tope por diseño. El archivo guarda también el saldo al quedar plano. Con `PropThresholdOverride` el pico guardado sube a override + trailing. |
| Monitor de borde: descarta el estado guardado en silencio; deja de alarmar desde feb-2027 | media | **Parcial:** ahora avisa cuando descarta el estado (runbook: dejar NinjaTrader corriendo a las 18:00 ET). **Pendiente** antes de feb-2027: reaplicar el estado guardado más los días posteriores del histórico, y un archivo por perfil y grupo. |
| Deshabilitar / editar con posición abierta la deja sin stop; se borra el archivo de posiciones | media | **Corregido en parte:** alerta `STOPPED WITH AN OPEN POSITION` (no verificado que suene en `Terminated`; se prueba en Sim) y no se borra el archivo si la cuenta está posicionada; regla en el runbook (no deshabilitar con posición; revisar la opción de NinjaTrader que cancela las salidas al deshabilitar). |
| `ConnectionLossHandling` no fijado | media | **Pendiente:** simulacro de desconexión en Sim (runbook) antes de fijarlo; sin probarlo no se cambia el valor por defecto. |
| Guarda entre cuentas falla abierta | media | **Corregido en parte (v2):** publica en cada ejecución y en `OnPositionUpdate`; antes de armar el control de sincronización publica solo la posición de la cuenta (la v1 la pisaba con la de los módulos virtuales). La relectura con reintentos y las señales opuestas en la misma barra quedan para el Playback de 2 cuentas (runbook). |
| Eval nueva con el mismo nombre hereda el mejor día | baja | **Runbook** (EvalStartDate = hoy o borrar el archivo). |
| Cuenta simulada por nombre | baja | **Runbook** (primer día: "EN VIVO" y "CUENTA REAL"). |
| Roll una sesión tarde | baja | **Corregido** (día de operación de la sesión). |
| Barras tardías sin alerta | baja | **Corregido** (alerta tras 3 seguidas). |
| Retiro debitado en sesión dispara el stop diario de la escalera | baja | **Runbook** (retiros con la estrategia deshabilitada y plana, fuera de sesión). |
| `Time[0]` fuera de try en el control de reloj | baja | **Corregido** (`patch_clock_check.py` v3, `Times[0][0]`). |
| `NQAccountGuard.cs` con archivo de pausa global | baja | **Runbook** (no se usa con este plan). |
| Eval de Lucid 150K se puede perder en un solo trade (por diseño) | info | Sin cambio (validado en la campaña); el panel de riesgo abierto lo muestra. |

## Disposición de la revisión del parche v1 (`revision_patch_live_safety_v1.md`)

| Hallazgo | Severidad | Qué se hizo en la v2 |
|---|---|---|
| El estado desconocido no prende el tope de riesgo en ninguna Lucid | alta | **Corregido** como pidió: `RiskCapActive` usa `propStateUnknown && Funded` directamente y `StepUpOn` exige `!propStateUnknown`; no se toca el colchón (así la eval no cae al set Estable). Aviso y runbook dicen que en eval no hay tope. |
| Archivo de estado viejo pasa por bueno | media | **Corregido:** el archivo guarda el saldo visto (6.º campo), al empezar la sesión y en la barra siguiente a quedar plano. Si el archivo es anterior a la sesión previa y el saldo de hoy difiere en más de $50 → estado desconocido. Guardar al quedar plano evita el falso positivo de una sesión sin NinjaTrader después de un día con trades. Runbook: copiar `nqmaster_prop_*` y `nqmaster_edge_*` al cambiar de PC. |
| `PropThresholdOverride` vuelve al error en silencio | media | **Corregido:** con el override cargado el pico sube a override + trailing antes de guardar; aviso y runbook recomiendan `PropPeakOverride` como camino normal. **No hecho:** mostrar en el aviso el límite calculado sin override (con el pico coherente ya no hace falta para no quedar circular). |
| Publicar antes de sincronizar no tiene efecto | media | **Corregido** como pidió: antes de `syncArmed` publica el signo de `PositionAccount` y salta los módulos. |
| `ExitOrd` bloquea salidas o se traga una necesaria | media | **Corregido:** `ExitOrd`/`ExitAgain`/`ExitWarned` se limpian al pasar a vivo; una salida suprimida marca `ExitAgain` y se reintenta cuando la anterior deja de trabajar; vigía de 3 barras con aviso. **No hecho:** refrescar `ExitOrd` en `OnOrderUpdate` (opcional). |
| `IgnoreOverfill = true` sin escalamiento ni prueba | media | **Corregido en parte:** escalamiento a `Account.Flatten` del instrumento a las 3 barras sin quedar plano (cancela también los brackets; después la guarda de sincronización detiene la estrategia); `IgnoreOverfill` también en Configure e impreso en la línea LIVE. **Decisión:** queda `true`. Con `false`, NinjaTrader detiene la estrategia ante el overfill y cancela los stops de los otros módulos, comportamiento que tampoco está verificado (el revisor lo cita de memoria). Con `true`, el camino es código propio con escalamiento acotado (~5 barras desde los lotes sin dueño; en la v3 el escalamiento además detiene la estrategia). **No hecho:** una propiedad de prueba para provocar el overfill (sería un módulo/propiedad nueva solo para el simulacro). El simulacro 3 del runbook pasa a ser la prueba de falsos positivos con los dos Playback. |
| `Terminated`: el aviso cubre menos de lo que dice | baja | **Corregido en parte:** sin `!SimAccount` (se ve y se prueba en Sim), sin aviso tras `desyncHalt`. Runbook: la alerta puede no sonar; mirar Orders siempre al detener. **No hecho:** escribir el log con `File.AppendAllText` (queda en Output con `Print`). |
| Publicación al final de `OnExecutionUpdate` antes de actualizar `Position` | baja | **Corregido:** override `OnPositionUpdate` que publica. |
| Bordes de `PROP STATE UNKNOWN` | baja | **Corregido:** con saldo ≤ 0 no decide; el panel muestra la línea de estado desconocido; el runbook menciona `EvalBestDaySoFar`. |
| Mensajes del aplanado y del roll | baja | **Corregido:** `hedgeWhy` con motivo propio; `OwnerList()` con `Sig:OpenQty` en los avisos; fila `ROLL DATE` del runbook reescrita. |
| La documentación da por resuelto lo que no está | baja | **Corregido:** filas 72-74 y simulacro 3 del runbook, esta disposición y ESTADO. |
| Histórico, `LotOwnershipCheck`, chequeo de overfill, gate, reloj | info | Sin cambio. Criterio de la PC: export Off 2024 → hoy idéntico al v4.3 salvo ICT 2 → 1; Playback Tick1 13-15 oct y Off 16 oct con 0 `OVERFILL` y 0 `LOTS WITHOUT OWNER`. |


## Disposición de la revisión del parche v2 (`revision_patch_live_safety_v2.md`, tal cual)

Veredicto del revisor: F5 sí, dinero real todavía no (dos medias y las pruebas en la PC). La v3 de `patch_live_safety.py` corrige:

| Hallazgo | Severidad | Qué se hizo en la v3 |
|---|---|---|
| El escalamiento a `Account.Flatten` no detiene la estrategia: la barra siguiente puede abrir una posición inversa real | media | **Corregido** como pidió: a la 3.ª barra sin quedar plano, `desyncHalt = true`, `Account.Flatten`, aviso y `SetState(Terminated)`, sin `FlattenAll` en esa barra (dos aplanados gestionados antes, en las barras 1 y 2). |
| Un `PropPeakOverride` que quedó cargado apaga para siempre el estado desconocido | media | **Corregido** como pidió: la condición pide `!(PropPeakOverride > 0 && newOverride)`; el aviso dice que tiene que ser un valor nuevo; runbook: volverlo a 0 tras el primer arranque sin aviso. |
| Reintento y aplanado en la misma barra: doble salida | baja | **Corregido:** `ExitRetries` corre después de los aplanados de la barra (justo antes de las salidas por tiempo) y no corre con `hedgeFlat` ni si salió un `FlattenAll` en esa barra. |
| `ExitAgain` no se limpia al quedar plano | baja | **Corregido:** `ExitDone` (al llegar `OpenQty` a 0, en el reseteo plano y en la primera ejecución de una entrada nueva) limpia `ExitAgain`, el contador de reintentos y `ExitOrd` si ya no trabaja. |
| El vigía solo avisa; llamadores de una sola vez | baja | **Corregido:** una salida cancelada o rechazada con el módulo todavía en posición se reintenta hasta 2 veces; después aviso `exit cancelled / rejected 3 times`. Runbook: cancelar la trabada (se reenvía); si sigue, deshabilitar y cerrar a mano. |
| Chequeo de archivo viejo: falsos positivos y negativos | baja | **Runbook:** los dos falsos positivos conservadores (posición cerrada en el broker con la PC apagada, retiro con la estrategia deshabilitada) y una prueba única en la primera cuenta real. El caso (c), caja leída antes de que el broker la actualice, queda a mirar en la línea `exit fill ... account cash` del Log. Los falsos negativos (archivo de 5 campos, saldo que vuelve a ±$50) quedan dichos en "Dos PCs". |
| Runbook: textos que no siguen al código | baja | **Corregido:** fila de OVERFILL / lotes sin dueño (esperar hasta 5 min; para intervenir, deshabilitar primero), "Dos PCs" y simulacro 3 (0 `could not get flat`, 0 `exit retried`, 0 `exit order working`). |
| La v2 no detecta un archivo con la v1 | baja | **Corregido:** la v3 corta con "regenerar desde el backup" si encuentra `LotOwnershipCheck` sin `ExitDone`. |
| Para F5: `OnPositionUpdate(Position ...)` | info | **Corregido:** `NinjaTrader.Cbi.Position`. |
| `PropThresholdOverride` fuera de rango | info | **Corregido:** fuera de [inicial − trailing, inicial + $100] se ignora con aviso (`ThrOv()` en todos los usos; en histórico vale lo mismo que antes). |
| Histórico: nada nuevo cambia órdenes ni estado | info | Sin cambio; lo nuevo de la v3 también corre solo en vivo (`ExitRetries`, `hedgeBars`, `thrOvBad`), y `ExitDone` en histórico solo toca campos que se leen en vivo. |

`check.sh` 0; `cr_fmtcheck` 121 llamadas, 0 sospechosas; cadena de 6 parches idempotente. Queda para la PC: F5, export Off idéntico al v4.3 salvo ICT 2 → 1, los dos Playback con 0 avisos nuevos y los simulacros.
