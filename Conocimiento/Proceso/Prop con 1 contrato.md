# Prop con 1 contrato: más aprobaciones y menos cuentas quemadas
Volver a [[00 - MAPA]] · Guía: sección "Cuentas de prop con 1 contrato" en `NQMASTER_GUIA.md`

- **La física del problema:** con tamaño fijo, la probabilidad de llegar a +$3.000 antes de perder $2.000 depende de la ganancia diaria media dividida por la varianza diaria (μ/σ²). Ultra tiene μ/σ² ≈ 0,00045 por dólar. El DD de $2.000 equivale a ~4 días malos.
- **Hallazgo 1:** los ×2 de NQMaster (contexto, confluencia, ICT ×2) suben más la varianza que la ganancia. ORB60 sin ×2 tiene casi el doble de μ/σ². VOLB, LON, MOM1030 y MOM11 son los de peor μ/σ².
- **Hallazgo 2:** con tamaño fijo hay una frontera. Más módulos y ×2 dan más velocidad pero menos aprobación. Elegir subconjuntos con 2020-23 NO se sostuvo fuera de muestra.
- **Hallazgo 3:** cambiar de modo según el colchón sobre el nivel de liquidación (FULL ≥ $900, SAFE por debajo) más un stop diario de $700 mejora la aprobación sin perder velocidad.
- **Hallazgo 4:** empezar la evaluación con ATR alto (≥ 1,15 veces la mediana de 60 días) baja la aprobación 7-14 puntos en los tres períodos. Con ATR bajo se tarda mucho. También mejora empezar después de 10 días malos de la estrategia (+4 a +12 puntos), pero ocurre pocas veces (~20% de los días).
- **Hallazgo 5 (fondeada):** SAFE con colchón < $1.500, NO-BOOST por encima y cobro a $6.000 → cuentas quemadas en 12 meses: 44% → 22-25%; cobro por cuenta $5,5k → $6,8k (en 2024-26).
- **No mejora:** la velocidad. Con 1 contrato, ser más rápido exige más ganancia por unidad de riesgo, y la ventaja por trade ya está en su techo.
