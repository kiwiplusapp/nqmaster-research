"""r4_report_check.py: cada cifra de las tablas de docs/experimentos/04_umbral_retiro_lucid.md contra exp04_payout_x.json."""
import json, re
R = "/home/user/nqmaster-research/"
J = json.load(open(R + "research/mine/exp04_payout_x.json")); B = json.load(open(R + "research/mine/objective_baseline.json"))
txt = open(R + "docs/experimentos/04_umbral_retiro_lucid.md").read().split("\n")
INC = 6000


def num(s):
    s = s.strip().replace("−", "-").replace("%", "").replace("+", "").strip()
    return float(s.replace(".", "").replace(",", "."))


def pair(s): return [num(x) for x in s.split("/")]


def close(rep, val, dec):
    return abs(rep - round(val, dec)) <= 0.5 * 10 ** (-dec) + 1e-9 or abs(rep - val) <= 0.5 * 10 ** (-dec) + 1e-9


sec = None; edge = None; bad = 0; n = 0
for ln in txt:
    if ln.startswith("## Plan completo (8 cuentas)"): sec = "plan"
    elif ln.startswith("## Plan completo, historia contigua"): sec = "plan_contiguo"
    elif ln.startswith("## Asiento Lucid 150K"): sec = "asiento"; edge = "0.0"
    elif ln.startswith("## "): sec = None
    if sec is None or not ln.startswith("|"): continue
    c = [x.strip() for x in ln.strip().strip("|").split("|")]
    if "Edge completo" in c[0]: edge = "0.0"; continue
    if "35 %" in c[0] or "−35" in c[0]: edge = "0.35"; continue
    if not re.fullmatch(r"[\d\.]+", c[0]): continue
    X = int(c[0].replace(".", ""))
    if sec in ("plan", "plan_contiguo"):
        rr = [J[sec][f"plan X{X} | hc{edge} | {p}"] for p in ("T1", "T2")]
        checks = [("med_mes", pair(c[1]), 0), ("p10_mes", pair(c[2]), 0), ("neg60", pair(c[3]), 1), ("evals_perdidas_mes", pair(c[4]), 2), ("cuentas_perdidas_mes", pair(c[5]), 2)]
        for q, rep, dec in checks:
            for i in range(2):
                n += 1
                if not close(rep[i], rr[i][q], dec): bad += 1; print(f"DIFF {sec} X{X} hc{edge} T{i+1} {q}: informe {rep[i]} json {rr[i][q]:.4f}")
        cm = re.findall(r"\d+", c[6].split("✓")[0].split("✗")[0])[:2]
        for i in range(2):
            n += 1; s = sum(rr[i]["cumple"].values())
            if int(cm[i]) != s: bad += 1; print(f"DIFF {sec} X{X} hc{edge} T{i+1} cumple: informe {cm[i]} json {s}")
        if sec == "plan":
            marks = re.findall(r"[✓✗]{6}", c[6])
            for i, mk in enumerate(marks):
                n += 1; exp = "".join("✓" if v else "✗" for v in rr[i]["cumple"].values())
                if mk != exp: bad += 1; print(f"DIFF marcas X{X} hc{edge} T{i+1}: {mk} json {exp}")
            if X != INC:
                parts = c[7].split("/")
                for i, p in enumerate(parts):
                    g = J["pareado"][f"plan X{X} vs X{INC} | hc{edge} | T{i+1}"]
                    m = re.match(r"\s*([+\-−]?[\d,]+) % \((?:P ganar )?([\d,]+)\)", p)
                    rel, pg = num(m.group(1)), num(m.group(2)); n += 2
                    if not close(rel, 100 * g["rel"], 1): bad += 1; print(f"DIFF pareado rel X{X} hc{edge} T{i+1}: informe {rel} json {100*g['rel']:.3f}")
                    if not close(pg, g["P_gain"], 2): bad += 1; print(f"DIFF pareado P_gain X{X} hc{edge} T{i+1}: informe {pg} json {g['P_gain']:.3f}")
    else:
        rr = [J["asiento"][f"L150 X{X} | hc0.0 | {p}"] for p in ("T1", "T2")]
        checks = [("med_mes", pair(c[1]), 0), ("p10_mes", pair(c[2]), 0), ("neg60", pair(c[3]), 1), ("neg60_mtm", pair(c[4]), 1), ("evals_perdidas_mes", pair(c[5]), 3), ("cuentas_perdidas_mes", pair(c[6]), 3), ("retiros_anio", pair(c[7]), 1)]
        for q, rep, dec in checks:
            for i in range(2):
                n += 1
                if not close(rep[i], rr[i][q], dec): bad += 1; print(f"DIFF asiento X{X} T{i+1} {q}: informe {rep[i]} json {rr[i][q]:.4f}")
print(f"tablas del informe: {n} cifras comparadas, {bad} distintas del JSON")

# afirmaciones del texto
XS = (4600, 5000, 6000, 7000, 8000, 10000, 12000)
P = lambda X, hc, p: J["plan"][f"plan X{X} | hc{hc} | {p}"]
print("aprobacion plan hc0 T1/T2:", sorted({(round(P(X, '0.0', 'T1')['aprobacion'], 1), round(P(X, '0.0', 'T2')['aprobacion'], 1)) for X in XS}))
print("dias_aprobar plan hc0 T1/T2:", sorted({(P(X, '0.0', 'T1')['dias_aprobar'], P(X, '0.0', 'T2')['dias_aprobar']) for X in XS}))
print("neg60 hc0.35 bootstrap rango:", min(P(X, '0.35', p)['neg60'] for X in XS for p in ('T1', 'T2')), max(P(X, '0.35', p)['neg60'] for X in XS for p in ('T1', 'T2')))
print("evals perdidas/mes rango hc0:", min(P(X, '0.0', p)['evals_perdidas_mes'] for X in XS for p in ('T1', 'T2')), max(P(X, '0.0', p)['evals_perdidas_mes'] for X in XS for p in ('T1', 'T2')),
      "| hc0.35:", min(P(X, '0.35', p)['evals_perdidas_mes'] for X in XS for p in ('T1', 'T2')), max(P(X, '0.35', p)['evals_perdidas_mes'] for X in XS for p in ('T1', 'T2')))
for X in (10000, 12000):
    print(f"X{X}: P_loss5 plan", [round(J['pareado'][f'plan X{X} vs X{INC} | hc{hc} | {p}']['P_loss5'], 2) for hc in ('0.0', '0.35') for p in ('T1', 'T2')], "rel %", [round(100 * J['pareado'][f'plan X{X} vs X{INC} | hc{hc} | {p}']['rel'], 1) for hc in ('0.0', '0.35') for p in ('T1', 'T2')])
for X in (4600, 5000, 7000):
    print(f"X{X}: rel % / P_gain", [(round(100 * J['pareado'][f'plan X{X} vs X{INC} | hc{hc} | {p}']['rel'], 1), round(J['pareado'][f'plan X{X} vs X{INC} | hc{hc} | {p}']['P_gain'], 2)) for hc in ('0.0', '0.35') for p in ('T1', 'T2')])
# fondeadas quemadas: fraccion L150 (plan - MFFU de la base)
for hc in ("0.0", "0.35"):
    for p in ("T1", "T2"):
        mf = B["plan"][f"5 L150 + 3 MFFU | hc{hc} | {p} | coupon"]["cuentas_perdidas_mes [MFFU 1x8]"]; inc = P(INC, hc, p)["cuentas_perdidas_mes"] - mf
        print(f"fondeadas L150 en el plan hc{hc} {p}: X6000 {inc:.3f} (MFFU {mf:.3f}); ratio X/6000: " + " ".join(f"X{X} {(P(X, hc, p)['cuentas_perdidas_mes'] - mf) / inc:.2f}" for X in (4600, 10000, 12000)) +
              f" | plan total ratio X10000 {P(10000, hc, p)['cuentas_perdidas_mes'] / P(INC, hc, p)['cuentas_perdidas_mes']:.2f} X12000 {P(12000, hc, p)['cuentas_perdidas_mes'] / P(INC, hc, p)['cuentas_perdidas_mes']:.2f}")
    S = lambda X, p: J["asiento"][f"L150 X{X} | hc{hc} | {p}"]
    print(f"asiento hc{hc}: fondeadas ratio X10000 {[round(S(10000, p)['cuentas_perdidas_mes'] / S(INC, p)['cuentas_perdidas_mes'], 2) for p in ('T1', 'T2')]} X12000 {[round(S(12000, p)['cuentas_perdidas_mes'] / S(INC, p)['cuentas_perdidas_mes'], 2) for p in ('T1', 'T2')]}; mtm X4600 {[round(S(4600, p)['neg60_mtm'], 1) for p in ('T1', 'T2')]} X12000 {[round(S(12000, p)['neg60_mtm'], 1) for p in ('T1', 'T2')]}")
    print(f"asiento X6000 hc{hc}: med {[round(S(INC, p)['med_mes']) for p in ('T1', 'T2')]} p10 {[round(S(INC, p)['p10_mes']) for p in ('T1', 'T2')]} fondeadas/anio {[round(12 * S(INC, p)['cuentas_perdidas_mes'], 2) for p in ('T1', 'T2')]}")
print("contiguo hc0.35 neg60 T1/T2:", {X: (round(J['plan_contiguo'][f'plan X{X} | hc0.35 | T1']['neg60'], 1), round(J['plan_contiguo'][f'plan X{X} | hc0.35 | T2']['neg60'], 1)) for X in XS})
print("rango contiguo hc0.35 neg60:", min(J['plan_contiguo'][f'plan X{X} | hc0.35 | {p}']['neg60'] for X in XS for p in ('T1', 'T2')), max(J['plan_contiguo'][f'plan X{X} | hc0.35 | {p}']['neg60'] for X in XS for p in ('T1', 'T2')))
print("plan neg60_mtm hc0.35 bootstrap:", {X: (round(P(X, '0.35', 'T1')['neg60_mtm'], 1), round(P(X, '0.35', 'T2')['neg60_mtm'], 1)) for X in XS})
