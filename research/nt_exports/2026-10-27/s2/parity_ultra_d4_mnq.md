# Paridad NinjaTrader vs investigación: ultra_d4_mnq (20240122-20260925)

- Commit e53a826, NQMaster.cs SHA-256 cc319383cde3a0ca, export `trades_off_2024-01-01_hoy_v43.csv`, generado 2026-10-27.
- G1 emparejados 98.5% (umbral 92.0%) | G2 $ emparejados NT vs investigación -1.6% (±3.0%) | G3 correlación diaria 0.981 (≥ 0.95)
- Resultado: **PASA**

```
 module  research  nt  matched   pct  res_matched_usd  nt_matched_usd  res_usd  nt_usd gate
   CAM3        36  38       33  91.7              120             101       37      35   ok
  CPI09        25  27       24  96.0             1493            1371     1646    1599   ok
  CRT11        61  60       58  95.1             4066            3863     3775    3921   ok
    ICT        61  64       61 100.0              889             914      889    1266   ok
 LATE15        99 100       99 100.0             1351            1368     1351    1501   ok
 LF0430        85  87       84  98.8             1732            1805     1675    1736   ok
   LF06        73  75       73 100.0             1115            1067     1115    1053   ok
    LON       164 168      162  98.8             4172            4173     4408    4256   ok
MOM1030       104 119      104 100.0             1661            1485     1661    1930   ok
  MOM11       501 500      493  98.4             5713            5087     5740    4774   ok
  MOM13       191 195      188  98.4             3558            3557     3575    3693   ok
   MSEQ       155 163      155 100.0             2677            2662     2677    2179   ok
  MSEQS        22  22       22 100.0             1999            1997     1999    1997   ok
   NF05        98 100       98 100.0             2845            2785     2845    2619   ok
   ON07       257 264      257 100.0             1666            1588     1666    1435   ok
  ORB60       127 134      127 100.0             6380            6380     6380    6546   ok
  ORB90       106 112      106 100.0             3867            3899     3867    3683   ok
 ORFAIL       109 110      109 100.0             1342            1281     1342    1430   ok
  REV06       213 221      213 100.0              869             642      869     662   ok
   RV11        28  28       27  96.4             1136            1360     1215    1251   ok
   SO04        63  64       63 100.0             1429            1449     1429    1347   ok
   VOLB       475 465      449  94.5            17023           17124    17224   17750   ok
   VW13       156 159      156 100.0              756             795      756     620   ok
```

Entry-minute offset of the matched pairs (NinjaTrader minus research; review 2026-10-27: a pair one bar later is the same trade deferred by an opposite working order, which the research does not model): 164 of 3161 pairs late; on those, research $2054 vs NT $1052.

```
 module  pairs  nt_same_bar  nt_1_bar_later  nt_later_2plus  nt_earlier  usd_research_late  usd_nt_late
   CAM3     33           21              12               0           0               -408         -426
  CPI09     24           24               0               0           0                  0            0
  CRT11     58           47              11               0           0               1356         1149
    ICT     61           55               6               0           0                -19            6
 LATE15     99           99               0               0           0                  0            0
 LF0430     84           84               0               0           0                  0            0
   LF06     73           72               1               0           0                 71           72
    LON    162          162               0               0           0                  0            0
MOM1030    104          104               0               0           0                  0            0
  MOM11    493          440              53               0           0                570         -109
  MOM13    188          188               0               0           0                  0            0
   MSEQ    155          153               2               0           0                268          244
  MSEQS     22           22               0               0           0                  0            0
   NF05     98           93               5               0           0                563          558
   ON07    257          257               0               0           0                  0            0
  ORB60    127          126               1               0           0                 84           84
  ORB90    106          106               0               0           0                  0            0
 ORFAIL    109           39              70               0           0               -404         -506
  REV06    213          213               0               0           0                  0            0
   RV11     27           26               1               0           0               -100           95
   SO04     63           63               0               0           0                  0            0
   VOLB    449          445               1               0           3                 13           13
   VW13    156          155               1               0           0                 60         -128
```
