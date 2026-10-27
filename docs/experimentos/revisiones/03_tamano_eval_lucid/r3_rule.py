import json
J = json.load(open("/home/user/nqmaster-research/research/mine/exp03_eval_size.json")); KS = (1, 2, 3, 4, 5, 6)
P = lambda k, hc, per, sec="plan": J[sec][f"plan k{k} | hc{hc} | {per}"]
print("Paso 1 (T1, hc0 + hc0.35; desempate mediana hc0.35):")
for k in KS:
    a, b = P(k, 0.0, "T1"), P(k, 0.35, "T1"); print(f"  k{k}: {sum(a['cumple'].values())}+{sum(b['cumple'].values())} = {sum(a['cumple'].values())+sum(b['cumple'].values())}  med hc0.35 {b['med_mes']:.0f}  M5 hc0 {a['dias_aprobar']} hc0.35 {b['dias_aprobar']}")
print("Lecturas alternativas del paso 1:")
def score(k, hcs, pers=("T1",), sec="plan"): return sum(sum(P(k, hc, p, sec)["cumple"].values()) for hc in hcs for p in pers)
for nm, f in (("incl. hc1.0", lambda k: (score(k, (0.0, 0.35, 1.0)), P(k, 0.35, "T1")["med_mes"])),
              ("solo hc0.35 (lexicografico: hc0.35 primero)", lambda k: (score(k, (0.35,)), score(k, (0.0,)), P(k, 0.35, "T1")["med_mes"])),
              ("solo hc0", lambda k: (score(k, (0.0,)), P(k, 0.35, "T1")["med_mes"])),
              ("desempate por ganancia pareada hc0.35 T1 (mediana de g)", lambda k: (score(k, (0.0, 0.35)), 0.0 if k == 6 else J["pareado"][f"plan k{k} vs k6 | hc0.35 | T1"]["med"])),
              ("contiguo T1 (misma regla)", lambda k: (score(k, (0.0, 0.35), sec="plan_contiguo"), P(k, 0.35, "T1", "plan_contiguo")["med_mes"]))):
    sc = {k: f(k) for k in KS}; w = max(KS, key=lambda k: sc[k]); print(f"  {nm:55s} gana k{w}  {sc}")
print("Paso 2 hipotetico (si cada k hubiese sido k*):")
for k in (1, 2, 3, 4, 5):
    lost = [f"hc{hc}:{m}" for hc in (0.0, 0.35) for m, v in P(6, hc, "T2")["cumple"].items() if v and not P(k, hc, "T2")["cumple"][m]]
    g = J["pareado"][f"plan k{k} vs k6 | hc0.35 | T2"]; okg = (g["med"] > 0 and g["P_gain"] >= 0.8) or (g["rel"] >= -0.05 and g["P_loss5"] <= 0.2)
    ci = [P(6, 0.0, p, "plan_contiguo")["neg60"] for p in ("T1", "T2")]; ck = [P(k, 0.0, p, "plan_contiguo")["neg60"] for p in ("T1", "T2")]
    ci35 = [P(6, 0.35, p, "plan_contiguo")["neg60"] for p in ("T1", "T2")]; ck35 = [P(k, 0.35, p, "plan_contiguo")["neg60"] for p in ("T1", "T2")]
    okc = all(x <= y + 2 for x, y in zip(ck, ci)); okc35 = all(x <= y + 2 for x, y in zip(ck35, ci35))
    print(f"  k{k}: pierde {lost}; pareado hc0.35 T2 med {g['med']:+.0f} rel {100*g['rel']:+.1f}% P_gain {g['P_gain']:.2f} P_loss5 {g['P_loss5']:.2f} -> {okg}; neg60 contiguo hc0 {[round(x,1) for x in ck]} vs {[round(x,1) for x in ci]} -> {okc}; (hc0.35: {[round(x,1) for x in ck35]} vs {[round(x,1) for x in ci35]} -> {okc35}); CONFIRMA {not lost and okg and okc}")
