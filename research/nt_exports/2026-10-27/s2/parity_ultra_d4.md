# Paridad NinjaTrader vs investigación: ultra_d4 (20240122-20261008)

- Commit c27cbf7, NQMaster.cs SHA-256 cc319383cde3a0ca, export `trades_off_2024-01-01_hoy_v43.csv`, generado 2026-10-27.
- G1 emparejados 94.1% (umbral 92.0%) | G2 $ emparejados NT vs investigación +0.6% (±3.0%) | G3 correlación diaria 0.970 (≥ 0.95)
- Resultado: **FALLA: G4 ICT 89.5%; G4 MSEQS 81.5%; G4 RV11 67.7%**

```
 module  research  nt  matched   pct  res_matched_usd  nt_matched_usd  res_usd  nt_usd gate
   CAM3        32  39       30  93.8              -85            -111     -148    -156   ok
  CPI09        26  27       24  92.3             1493            1371     1491    1599   ok
  CRT11        64  61       59  92.2             4352            4184     4005    4242   ok
    ICT        57  65       51  89.5              777             800      193    1362 FAIL
 LATE15       100 101      100 100.0             1317            1318     1317    1451   ok
 LF0430        89  88       87  97.8             1607            1703     1730    1867   ok
   LF06        73  75       72  98.6             1184             995     1247    1053   ok
    LON       181 170      165  91.2             4656            4366     5332    4348   ok
MOM1030       106 121      102  96.2             1036            1160     1186    1768   ok
  MOM11       524 507      505  96.4             4871            4453     4972    4664   ok
  MOM13       203 198      193  95.1             3550            3509     3354    3838   ok
   MSEQ       164 167      153  93.3             1601            1840     1443    1922   ok
  MSEQS        27  22       22  81.5             2008            1997     1863    1997 FAIL
   NF05       108 103      100  92.6             3052            2988     3102    2623   ok
   ON07       280 270      262  93.6             1614            1519     1491    1424   ok
  ORB60       134 135      130  97.0             5782            5788     6123    6272   ok
  ORB90       111 113      108  97.3             2890            2898     3504    3409   ok
 ORFAIL       112 112      106  94.6              938             803     2074    1637   ok
  REV06       223 225      213  95.5               21              10      359     244   ok
   RV11        31  28       21  67.7              865            1093      841    1251 FAIL
   SO04        68  66       63  92.6             1371            1402     1410    1342   ok
   VOLB       496 471      447  90.1            16408           17574    16388   17630   ok
   VW13       160 160      156  97.5              766             817      829     674   ok
```
