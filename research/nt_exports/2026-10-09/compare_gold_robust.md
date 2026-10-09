# NinjaTrader vs investigación (gold_robust, 20250331-20260928)

- Trades: investigación 321, NinjaTrader 326, coinciden 320 (99.7% de la investigación).
- $ por contrato: investigación 12,077, NinjaTrader 11,992. Correlación diaria 0.991.
- En los trades que coinciden: investigación 12,195, NinjaTrader 12,116.

```
 module  res_n  nt_n  matched  only_res  only_nt  res_wr  nt_wr  res_pf  nt_pf  res_net  nt_net  matched_res  matched_nt  corr
   ASIA    161   162      160         1        2    55.9   55.6    1.25   1.27     4712    4999         4830        5045 0.998
ENG0206     55    56       55         0        1    65.5   66.1    1.32   1.35     1460    1599         1460        1395 1.000
ENG0408     43    45       43         0        2    72.1   71.1    2.83   2.60     3117    3024         3117        3095 1.000
 OD1030     27    28       27         0        1    70.4   67.9    4.37   3.24     2161    1923         2161        2134 1.000
SVWAP22     35    35       35         0        0    68.6   68.6    1.35   1.23      626     447          626         447 0.996
  TOTAL    321   326      320         1        6    62.3   62.0    1.44   1.43    12076   11992        12194       12116   NaN
```

Trades sin pareja: /tmp/claude-0/-home-user-nqmaster-research/c6cc5ef6-fbab-51d6-8437-b8f6d9d1ef6e/scratchpad/cmp_gold_robust_mismatch.csv
