"""Compara las tablas del informe 07 con el JSON (bootstrap, cambio de regimen y contiguo)."""
import json, re
J = json.load(open("/home/user/nqmaster-research/research/mine/exp07_pause_rules.json"))
md = open("/home/user/nqmaster-research/docs/experimentos/07_reglas_pausa.md").read().splitlines()
SEC = {"Edge completo": "completo", "−35 % de edge": "-35%", "Edge cero todo el año": "cero", "Edge completo hasta el día 63, cero después": "muere63",
       "Edge completo hasta el día 126, cero después": "muere126"}
RL = {"sin regla (base)": "R0", "R1: acumulado < 0 desde el día 60": "R1", "R4: dos trimestres negativos": "R4", "R1 + R4": "R14"}
num = lambda s: float(s.replace(".", "").replace(",", ".").replace("−", "-"))
part = None; sc = None; bad = 0; n = 0
for ln in md:
    if ln.startswith("## Bootstrap"): part = "escenarios"
    elif ln.startswith("## Cambio"): part = "escenarios"
    elif ln.startswith("## Historia contigua"): part = "contiguo"
    elif ln.startswith("## Saldo"): part = None
    if not part or not ln.startswith("|"): continue
    cells = [c.strip() for c in ln.strip("|").split("|")]
    lab = cells[0].strip("*")
    if lab in SEC: sc = SEC[lab]; continue
    if lab not in RL: continue
    rule = RL[lab]
    for k, per in enumerate(("T1", "T2")):
        r = J[part][f"{sc} | {per} | {rule}"]
        got = [num(cells[c].split("/")[k]) for c in range(1, 6)]
        exp = [round(r["med_mes"]), round(r["p10_mes"]), round(r["P_anio_neg"], 1), round(r["neg60"], 1), round(r["pausados_pct"])]
        n += 1
        if any(abs(a - b) > (0.051 if i in (2, 3) else 0.51 if i == 4 else 0.5) for i, (a, b) in enumerate(zip(got, exp))):
            bad += 1; print("DIF", part, sc, per, rule, got, exp)
        if part == "escenarios" and rule != "R0":
            pc = cells[6].split("·")[k].split("/"); g = J["pareado"][f"{sc} | {per} | {rule} vs R0"]
            if abs(num(pc[0]) - g["P_gain"]) > 0.0051 or abs(num(pc[1]) - g["P_loss5"]) > 0.0051: bad += 1; print("DIF pareado", sc, per, rule, pc, g["P_gain"], g["P_loss5"])
        if part == "escenarios" and len(cells) > 7 and rule != "R0":
            dm = cells[7].split("/")[k].strip(); jm = r.get("demora_mediana_desde_cambio")
            if jm is not None and abs(num(dm) - jm) > 0.51: bad += 1; print("DIF demora", sc, per, rule, dm, jm)
print(f"{n} filas-periodo comparadas, {bad} diferencias")
print("claves 'cumple' en el JSON:", list(J["escenarios"]["completo | T1 | R0"]["cumple"].keys()), "| OUT['pausa'] =", J["pausa"])
