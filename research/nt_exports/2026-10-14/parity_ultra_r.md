# Paridad NinjaTrader vs investigación: ultra_r (20240122-20261008)

- Commit 31e7c38, NQMaster.cs SHA-256 635d8f72ca86e2b2, export `ultra_trades.csv`, generado 2026-10-15.
- G1 emparejados 94.6% (umbral 92.0%) | G2 $ emparejados NT vs investigación +0.8% (±3.0%) | G3 correlación diaria 0.968 (≥ 0.95)
- Resultado: **FALLA: G4 ICT 82.4%; G4 MSEQS 55.6%**

```
 module  research  nt  matched   pct  res_matched_usd  nt_matched_usd  res_usd  nt_usd gate
  CRT11        64  62       60  93.8             4260            4104     4005    4162   ok
    ICT        51  59       42  82.4             1073             928      321    1356 FAIL
 LATE15        96 101       96 100.0             1185            1198     1185    1462   ok
 LF0430        86  89       85  98.8             1884            1960     2016    1857   ok
   LF06        73  74       72  98.6             1184             986     1247     969   ok
    LON       172 170      159  92.4             3996            3731     4680    4220   ok
MOM1030       100 107       96  96.0             1180            1303     1320    1354   ok
  MOM11       540 529      526  97.4             4884            4469     5390    4726   ok
  MOM13       185 195      176  95.1             3352            3310     3164    3597   ok
   MSEQ       164 166      152  92.7             1988            2234     1443    2316   ok
  MSEQS        27  15       15  55.6             1084            1078     1863    1078 FAIL
   NF05       120 114      112  93.3             2685            2638     2849    2319   ok
   ON07       261 267      244  93.5             1340            1273     1330    1625   ok
  ORB60       134 134      131  97.8             5883            5893     6123    6212   ok
  ORB90       111 112      109  98.2             2991            2992     3504    3416   ok
  REV06       211 224      202  95.7              -80             -98      231     197   ok
   VOLB       504 484      461  91.5            18881           20369    19022   19744   ok
   VW13       151 161      148  98.0              618             505      647     545   ok
```
