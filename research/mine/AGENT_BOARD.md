# Tablero compartido de agentes (desde 2026-10-21)

Cada agente que trabaja en NQMaster lee este archivo al empezar y **agrega** (nunca borra) una entrada cuando tiene un resultado que otro agente puede usar. Formato:

```
## <fecha hora UTC> | <workstream> | <tipo: HALLAZGO / DATO / PEDIDO / RESPUESTA>
- qué: una línea
- archivo: ruta exacta (json/csv/py) que el otro agente puede leer
- para quién: workstream que debería usarlo
```

Reglas:
- Solo hechos medidos con su archivo; nada de opiniones.
- Un PEDIDO a otro workstream se responde con una entrada RESPUESTA (o con un SendMessage directo al agente).
- Ninguna entrada autoriza editar NQMaster.cs / GoldMaster.cs ni hacer git commit: eso lo hace solo el coordinador.

Workstreams activos:
- prop_wf: optimizador walk-forward de políticas de cuenta 50K (prop_wf.py)
- survey: relevamiento de firmas con bots + puntuación (prop_survey_sim.py, propfirms_2026-10-21.json)
- b13: lote 13, doble techo/suelo con barrido + IB a VWAP (families13.py)

---
