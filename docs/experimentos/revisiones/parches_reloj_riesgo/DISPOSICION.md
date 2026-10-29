# Disposición de la revisión adversarial de patch_clock_check.py y patch_open_risk.py (29-oct)

El informe del revisor está tal cual en `review_patches_clock_risk.md` (misma carpeta). Ambos parches pasaron a v2 y `NQMaster.cs` se regeneró desde el backup con la cadena completa (`docs/ESTADO.md`, "Regenerar NQMaster.cs"); `check.sh` verde; falta F5.

| Hallazgo | Qué se hizo |
|---|---|
| (media) El control de reloj v1 no puede ver errores de zona horaria, de reloj ni de horario de verano: solo la plantilla de sesión | **v2:** el aviso de fin de sesión ahora dice lo que detecta (plantilla distinta de CME US Index Futures ETH) y se agrega un segundo chequeo con referencia independiente: la hora ET de la barra calculada desde UTC con la regla fija de EE.UU. contra `ToEt()` (reglas de Windows). La regla fija coincide con la base de zonas horarias de Python en 455.808 instantes de 2010-2035. Un error del reloj de la PC no afecta la hora de las barras (vienen del feed); `LateBar` ya cubre la PC adelantada. |
| (media) Sin alerta el día en que se habilita | **v2:** `ClockCheck()` corre también al pasar a vivo, con los valores ya calculados (sin volver a llamar a `SessionBounds`). |
| (baja) Posición virtual del histórico al habilitar con WaitUntilFlat | **v2:** en la CUENTA REAL la línea no aparece mientras la posición de la cuenta no coincide en signo con la de la estrategia. |
| (baja) Solo cubre esta instancia de NQMaster | **v2:** el rótulo lo dice ("de NQMaster (este gráfico)") y el runbook también. |
| (baja) Sin comisión ni slippage | **v2:** resta la comisión de salida ($1,90 ida y vuelta / 2) y 1 tick por lote. |
| (baja) Con Tick1, registrar `XStopV` con `fillBip == 0` podía poner un `StopX` extra en la ventana inicial | **v2:** campos propios del panel (`RStopV` / `RStopPx`); `BracketStop` deja los campos de los brackets como estaban. |
| (baja) En backtest el aviso salía en cada sesión | **v2:** en histórico avisa una vez por corrida y cuenta las sesiones (línea final al terminar); en vivo, una vez por sesión. |
| (info) Línea oculta en silencio si salta el catch | Se deja: el panel no debe romperse por esta línea. |
