# Perfil MaxPlus (ORB90 + MSEQS)

Pedido: más trades, mayor PF total y mantener el winrate.

**Módulos nuevos:**
- **ORB90**: igual que [[ORB60 Pullback Day]], pero con rango de 90 minutos. Objetivo 0.6R, stop con tope de 0.35 ATRd, solo días pullback y a favor de la tendencia, entradas hasta las 13:00. PF 1.45 / 1.36 / 1.44 (CFD 2020-23 / CFD 2024-26 / MNQ real). Todos los targets probados (0.6, 0.75, 1R) dan PF ≥ 1.28 en los tres tramos.
- **MSEQS**: MSEQ en espejo, en corto (vela alcista principal + 5 velas bajistas de 5m, cada una cerrando más abajo y sin superar su máximo). Solo opera en días en que el ORB60 ya entró en corto, después de esa entrada, entre 10:30 y 15:45. Stop a 1.75x la distancia, objetivo 0.75R. PF 2.76 / 1.88 / 2.03; todas las variantes con N=5 dan PF > 1.26. Son pocos trades (~8 por año).

**Portfolio (solo NQ, sin FOMC, comisión $1.90):**

| Tramo | Trades/día MaxSharpe → MaxPlus | WR | PF | $/mes |
|---|---|---|---|---|
| CFD 2020-23 | 3.92 → 4.20 | 66.5 → 66.6 | 1.308 → 1.339 | 728 → 892 |
| CFD 2024-26 | 3.92 → 4.17 | 65.9 → 65.7 | 1.309 → 1.318 | 950 → 1087 |
| MNQ real 2024-26 | 3.67 → 3.93 | 66.9 → 66.8 | 1.351 → 1.369 | 1023 → 1200 |

MNQ real total: 2,583 trades, WR 66.8%, PF 1.369, $37,539 (MaxSharpe: 2,413 trades, PF 1.351, $32,012).

Apex 50K, adaptativo 2→1, 30 días: 38% de pases con 12% de quemadas, contra 31% / 5% con MaxSharpe. El ORB90 opera los mismos días que el ORB60, así que concentra riesgo en esos días.

**Descartado en esta búsqueda:**
- Minado de filtros de contexto sobre ~106k configuraciones (research/ctxmine.py): la correlación del PF entre 2020-23 y fuera de muestra es ~0.04, así que no sirve.
- CRT en otras horas, ICT en otras ventanas (research/ictx.py), gap fill (research/gapfill.py), ORB NR4/NR7/inside day y ORB60 con más reentradas o ventana extendida.
- Stops más anchos en los módulos MOM y RSI2 (research/widestop.py).
- Selección de subconjuntos de módulos solo con 2020-23: no se sostiene fuera de muestra.
- Continuación en días sin pullback (research/orbcont_all.py): PF < 1.
- Única pista sólida: la ventaja se concentra en los días pullback con ORB disparado.

## Control de riesgo (actualización)
- **Riesgo igual por módulo:** los pesos por volatilidad inversa se calcularon solo con 2020-23 y se redondearon a contratos enteros. Resultado: ICT pasa a 2 contratos (su stop es el más chico) y el resto queda en 1. Queda como `IctMultiplier = 2`, activo solo en MaxPlus.
  - PF: 1.344 / 1.324 / 1.376.
  - Sharpe: 2.85 / 2.82 / 3.20.
  - $/mes: 927 / 1,140 / 1,259.
  - Los tres mejoran sobre el perfil sin el cambio (tramos 2020-23 / 2024-26 / MNQ real).
- **Probado y descartado:** límite de 2 o 3 posiciones simultáneas, máximo 1 o 2 posiciones en la misma dirección, stop diario de $300/$500 y tope de ganancia diaria de $600/$1000. Todos bajan el Sharpe fuera de muestra (research/riskrules.py). Pesos por Sharpe: sobreajustan.
- **Evaluación Apex, política elegida:** 2 contratos, que bajan a 1 si el drawdown desde el pico supera $600 (`SizeDownDrawdown` = 600).
  - A 30 días: 37% de pases con 10% de quemadas en MNQ real y 28% / 9% en CFD 2024-26.
  - Sin límite de tiempo: 84% de pases con 15% de quemadas.
  - Proteger ganancias cerca del objetivo (bajar a 1 contrato con +$1500/+$2000) no cambia el resultado.
- **También descartado:**
  - SMT NQ/ES en el ICT: mejora mínima con 20-37 trades (research/smt.py).
  - Ventana 16:00-16:55: PF 0.7-0.8 (research/postclose.py).

## Reglas de confluencia (2026-09-29, research/improve1.py, improve2.py)
- **A:** los módulos de la tarde (CRT11, MOM13, MSEQ y MSEQS con entrada después de las 11:00) operan con **doble tamaño** cuando van **en contra del trade de MOM11** y **a favor de la dirección overnight** (signo de ON07 + REV06 + LON).
  - PF de esos trades: 2.06 / 1.81 / 1.63, contra 1.38 / 1.16 / 1.22 del resto.
  - Se cumple todos los años de 2020 a 2026 (PF 1.5-2.7 por año). Lo aportan sobre todo CRT11, y también MOM13 y MSEQ.
- **B:** **se salta REV06** si LON ya entró en la misma dirección.
  - PF de esos REV06: 0.83 / 0.92 / 1.12, contra 1.37 / 1.29 / 1.20 del resto.
- **Portafolio (1 contrato base):**
  - PF: 1.344→1.389 / 1.324→1.365 / 1.376→1.397.
  - Sharpe: 2.85→3.06 / 2.82→3.01 / 3.20→3.22.
  - $/mes: 927→1049 / 1140→1314 / 1259→1368.
- **Ciclo Apex 25K:** casi igual (−4% a +5%). Pasar la evaluación con 1 contrato mejora: 38→45 / 34→40 / 46→49%.
- Queda activo con `UseConfluence = true` (solo en MaxPlus y Custom).

## Probado y descartado (2026-09-29)
- Stop por tiempo en ORB60/ORB90/CRT11/MSEQ/MSEQS (15 a 180 min): peor; los trades necesitan tiempo (research/timestop.py).
- Filtro por régimen de volatilidad (ATR del día ÷ mediana de 100 días) por módulo: lo que es malo en 2020-23 sale bueno en 2024-26 (research/regime.py).
- Días de CPI/NFP: PF normal (1.1-1.5), no hace falta saltarlos.
- En la cuenta fondeada, sacar módulos de winrate bajo (LON/MOM13/ON07/CRT11) o poner ICT x1: 5-25% menos dinero (research/pa_subsets.py).
- Sumar MOM1130/RSI2 a MaxPlus para el ciclo Apex: +0-7% de dinero, pero Sharpe más bajo; no vale la pena.
- Entradas con orden límite y quitar el filtro de conflictos (ver Evaluaciones prop firm).
