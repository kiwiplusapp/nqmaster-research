import json
D="/home/user/nqmaster-research/research/mine/"
B=json.load(open(D+"objective_baseline.json")); X=json.load(open(D+"exp05_budget.json"))
print(X.keys()); print(X["regla"])
keys_cmp=["med_mes","p10_mes","p90_mes","P_anio_neg","neg60","neg60_mtm","neg60_cero","evals_anio","evals_perdidas_mes","cuentas_perdidas_mes","aprobacion","dias_aprobar","med_mes21","p10_mes21"]
for c in ("sin","T4000","T6000","T2500","A4000","T1500"):
  for sec_b,sec_x in (("plan","plan"),("plan_contiguo","plan_contiguo")):
    nd=0; tot=0; diffs=[]
    for hc in (0.0,0.35,1.0):
      for per in ("T1","T2"):
        b=B[sec_b][f"5 L150 + 3 MFFU | hc{hc} | {per} | coupon"]; x=X[sec_x][f"plan {c} | hc{hc} | {per}"]
        for k in keys_cmp:
          if k in b and k in x:
            tot+=1
            if abs(b[k]-x[k])>1e-9: nd+=1; diffs.append((hc,per,k,round(b[k],3),round(x[k],3)))
        if b["cumple"]!=x["cumple"]: diffs.append((hc,per,"cumple",b["cumple"],x["cumple"]))
    print(c, sec_x, "comparados",tot,"difs",nd, diffs[:6])
# seats
for c in ("sin","T4000"):
  nd=0; tot=0; ex=[]
  for hc in (0.0,0.35,1.0):
    for per in ("T1","T2"):
      for nm in ("L150 6c/3c","MFFU 1x8"):
        b=B["asientos"][f"{nm} | hc{hc} | {per} | coupon"]; x=X["asiento"][f"{nm} {c} | hc{hc} | {per}"]
        for k in keys_cmp:
          if k in b and k in x:
            tot+=1
            if abs(b[k]-x[k])>1e-9: nd+=1; ex.append((nm,hc,per,k,b[k],x[k]))
  print("asiento",c,"comparados",tot,"difs",nd,ex[:4])
# pausa
for sec in ("plan",):
  for k,v in X[sec].items():
    if v.get("dias_pausa_plan_anio",0)>0 or v.get("pausas_plan_anio",0)>0: print(k, v["dias_pausa_plan_anio"], v["pausas_plan_anio"])
for k,v in X["asiento"].items():
  if v["dias_pausa_anio"]>0: print("asiento",k,round(v["dias_pausa_anio"],2),round(v["pausas_anio"],3))
