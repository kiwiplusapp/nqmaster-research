import json
D="/home/user/nqmaster-research/research/mine/"
X=json.load(open(D+"exp05_budget.json"))
for k,v in X["pareado"].items():
    if k.startswith("plan sin") or "T6000" in k: print(k, v)
print()
for k in ("plan T4000 | hc1.0 | T2","plan sin | hc1.0 | T2"):
    v=X["plan"][k]; print(k, {q:v[q] for q in ("dias_pausa_plan_anio","pausas_plan_anio","evals_anio","med_mes","p10_mes","neg60","evals_perdidas_mes")})
for k,v in X["asiento"].items():
    if "T4000" in k or " sin " in k:
        if "hc1.0" in k: print(k, {q:v[q] for q in ("dias_pausa_anio","pausas_anio","evals_anio","med_mes","p10_mes","evals_perdidas_mes")})
print()
for k,v in X["plan_contiguo"].items():
    if "hc1.0" in k or "A4000" in k: print(k, "neg60",round(v["neg60"],2),"cero",round(v["neg60_cero"],2),"p10",round(v["p10_mes"]),"Pneg",round(v["P_anio_neg"],1))
print()
for c in ("sin","T4000","A4000","T1500"):
  for hc in (0.0,0.35,1.0):
    for per in ("T1","T2"):
      v=X["plan"][f"plan {c} | hc{hc} | {per}"]; print(c,hc,per,{m:int(b) for m,b in v["cumple"].items()}, "neg60",round(v["neg60"],2),"cero",round(v["neg60_cero"],2))
