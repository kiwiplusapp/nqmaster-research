# Paridad NinjaTrader vs investigación: ultra_d4 (20240122-20261008)

- Commit 38462e5, NQMaster.cs SHA-256 565e795a36fb6e8b, export `standard_2024-today_trades_ultra_1_contract.csv`, generado 2026-10-26.
- G1 emparejados 91.0% (umbral 92.0%) | G2 $ emparejados NT vs investigación +1.1% (±3.0%) | G3 correlación diaria 0.918 (≥ 0.95)
- Resultado: **FALLA: G4 CAM3 56.2%; G4 ICT 80.4%; G4 MSEQS 55.6%; G4 ORFAIL 34.3%; G4 RV11 53.8%; G4 SO04 89.2%; G1 91.0% < 92.0; G3 0.918 < 0.95**

```
 module  research  nt  matched   pct  res_matched_usd  nt_matched_usd  res_usd  nt_usd gate
   CAM3        32  26       18  56.2              280             296     -148     287 FAIL
  CPI09        26  27       24  92.3             1493            1371     1491    1599   ok
  CRT11        64  61       59  92.2             4352            4186     4005    4245   ok
    ICT        51  58       41  80.4             1185            1186      321    1815 FAIL
 LATE15        96 101       96 100.0             1185            1187     1185    1451   ok
 LF0430        86  88       84  97.7             1893            1970     2016    1867   ok
   LF06        73  75       72  98.6             1184             995     1247    1053   ok
    LON       172 170      158  91.9             4012            3747     4680    4348   ok
MOM1030       100 115       97  97.0             1211            1336     1320    1726   ok
  MOM11       527 519      507  96.2             4978            4559     5141    4894   ok
  MOM13       185 197      175  94.6             3360            3324     3164    3754   ok
   MSEQ       164 166      152  92.7             1988            2234     1443    2316   ok
  MSEQS        27  15       15  55.6             1084            1078     1863    1078 FAIL
   NF05       110 103      101  91.8             3000            2942     3163    2623   ok
   ON07       261 270      244  93.5             1340            1275     1330    1424   ok
  ORB60       134 134      130  97.0             5782            5788     6123    6174   ok
  ORB90       111 112      108  97.3             2890            2898     3504    3312   ok
 ORFAIL       105  40       36  34.3             1205            1250     1469    1920 FAIL
  REV06       211 225      201  95.3             -108            -118      231     244   ok
   RV11        39  29       21  53.8              865            1093      928    1434 FAIL
   SO04        65  66       58  89.2             1227            1266     1266    1342 FAIL
   VOLB       496 477      447  90.1            16408           17574    16388   20211   ok
   VW13       151 160      147  97.4              584             635      647     674   ok
```
