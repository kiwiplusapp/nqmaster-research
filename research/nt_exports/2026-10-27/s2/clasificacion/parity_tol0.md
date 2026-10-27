# Paridad NinjaTrader vs investigación: ultra_d4_mnq (20240122-20260925)

- Commit e53a826, NQMaster.cs SHA-256 cc319383cde3a0ca, export `trades_off_2024-01-01_hoy_v43.csv`, generado 2026-10-27.
- G1 emparejados 93.5% (umbral 92.0%) | G2 $ emparejados NT vs investigación -0.1% (±3.0%) | G3 correlación diaria 0.981 (≥ 0.95)
- Resultado: **FALLA: G4 CAM3 58.3%; G4 CRT11 77.0%; G4 MOM11 87.8%; G4 ORFAIL 35.8%**

```
 module  research  nt  matched   pct  res_matched_usd  nt_matched_usd  res_usd  nt_usd gate
   CAM3        36  38       21  58.3              529             527       37      35 FAIL
  CPI09        25  27       24  96.0             1493            1371     1646    1599   ok
  CRT11        61  60       47  77.0             2711            2714     3775    3921 FAIL
    ICT        61  64       61 100.0              889             914      889    1266   ok
 LATE15        99 100       99 100.0             1351            1368     1351    1501   ok
 LF0430        85  87       84  98.8             1732            1805     1675    1736   ok
   LF06        73  75       72  98.6             1044             995     1115    1053   ok
    LON       164 168      162  98.8             4172            4173     4408    4256   ok
MOM1030       104 119      104 100.0             1661            1485     1661    1930   ok
  MOM11       501 500      440  87.8             5143            5196     5740    4774 FAIL
  MOM13       191 195      188  98.4             3558            3557     3575    3693   ok
   MSEQ       155 163      153  98.7             2409            2418     2677    2179   ok
  MSEQS        22  22       22 100.0             1999            1997     1999    1997   ok
   NF05        98 100       93  94.9             2283            2227     2845    2619   ok
   ON07       257 264      257 100.0             1666            1588     1666    1435   ok
  ORB60       127 134      126  99.2             6296            6296     6380    6546   ok
  ORB90       106 112      106 100.0             3867            3899     3867    3683   ok
 ORFAIL       109 110       39  35.8             1746            1787     1342    1430 FAIL
  REV06       213 221      213 100.0              869             642      869     662   ok
   RV11        28  28       26  92.9             1237            1265     1215    1251   ok
   SO04        63  64       63 100.0             1429            1449     1429    1347   ok
   VOLB       475 465      445  93.7            16620           16721    17224   17750   ok
   VW13       156 159      155  99.4              696             922      756     620   ok
```
