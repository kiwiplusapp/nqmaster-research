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

## 2026-10-21 04:46 UTC | b13 | HALLAZGO
- qué: lote 13 (doble techo/suelo con barrido + IB a VWAP, 3.600 celdas): 0 sobrevivientes (66 pasan s1, 4 pasan T2, 0 pasan 2010-18); P(T2|s1) 6,1% = tasa base 6,0%. Continuación del barrido pierde (mediana PF 0,89-0,98), reversión solo gana 2023-26; filtros VWAP/SMA200 ~+0,0-0,06 PF. Nada para agregar a NQMaster ni a las políticas de cuenta.
- archivo: research/mine/b13_select.json, research/mine/b13_report.md, research/mine/results_b13_staged.csv
- para quién: coordinador, prop_wf (sin cambio de stream de P&L)

## 2026-10-21 UTC | survey | DATO
- qué: reglas máquina-legibles de 18 planes 50K de firmas que permiten bots + NT8 (Lucid Flex/Pro/Daily, MFFU Rapid EOD/Rapid/Builder, Bulenox Opt1/Opt2, FundedNext Rapid Pro/Daily/Flex, Tradeify Select/Growth, FTMO Futures Growth/Pro, TradeDay Fast Pass, Trading Pit Prime) + firmas excluidas con cita de la cláusula. Mejor geometría (sin consistencia ni DLL en eval): Bulenox Opt1 (T3000 / D2500 intradía), Lucid Pro DLL off (T3000 / D2000 EOD), FundedNext Rapid Pro (T3000 / D2000 EOD); con DLL blando: MFFU Builder (DLL 1000), Tradeify Growth (DLL 1250); FTMO Pro D3000=T pero DLL duro 1000 + 50% consistencia. Primera corrida (NQ-only, k chosen T1): pase serie <=22 días hábiles Lucid Pro / FundedNext Rapid Pro k4 96/99% (T1/T2), Bulenox Opt1 k4 95/100%, MFFU Rapid EOD 38/48%.
- archivo: research/mine/propfirms_2026-10-21.json (plans_50k; claves documentadas en prop_survey_sim.py), resultados prop_survey_sim.json
- para quién: prop_wf

## 2026-10-21 UTC | survey | HALLAZGO
- qué: puntuación final de 18 planes 50K con bots + NT8 (NQ-only, +1 tick, k elegido en T1). Financiado en <=22 días hábiles con re-compras, k4 (T1/T2; -35% edge): Lucid Pro DLL off 96/99 (88/96) ~$235; FundedNext Rapid Pro 96/99 (88/96) ~$305; Bulenox Opt1 95/100 (88/96) ~$350 con activación; MFFU Builder 92/89; Lucid Flex 81/89; MFFU Rapid EOD solo 38/48 (consistencia 30%). Ingreso neto 12 meses por cuenta (1c fondeada): MFFU Rapid EOD $12.6k/$19.6k (-35% $5.8k/$7.8k) > Bulenox Opt1 $7.0k/$10.6k > Lucid Pro $6.9k/$7.6k > FundedNext Rapid Pro $3.4k/$2.9k (tope 5 x $1,200). La consistencia de eval es la palanca dominante; un DLL duro (FTMO Pro) destruye el pase.
- archivo: research/mine/prop_survey_sim.json, research/mine/prop_survey_report.md, research/mine/propfirms_2026-10-21.md
- para quién: prop_wf, coordinador
