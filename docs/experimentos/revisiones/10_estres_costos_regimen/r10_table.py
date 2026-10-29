import json, re
O = json.load(open("/home/user/nqmaster-research/research/mine/exp10_stress.json"))
C = O["celdas"]
def f(v): 
    s = f"{round(v):,}".replace(",", ".")
    return s.replace("-", "−")
def p(v): return f"{v:.1f}".replace(".", ",")
rows = {}
names = {0.0: "Edge completo", 0.35: "−35 %", 0.68: "Edge de 2015-19 (−68 %)", 1.0: "Edge cero"}
for hc in (0.0, 0.35, 0.68, 1.0):
    for x in (0, 1, 2, 3):
        b = [C[f"x{x} | hc{hc} | {per} | bootstrap"] for per in ("T1", "T2")]
        c = [C[f"x{x} | hc{hc} | {per} | contiguo"] for per in ("T1", "T2")]
        line = (f"| {names[hc] if x==0 else ''} | +{x} | {f(b[0]['plan']['med_mes'])} / {f(b[1]['plan']['med_mes'])} | {f(b[0]['plan']['media_mes'])} / {f(b[1]['plan']['media_mes'])} | "
                f"{f(b[0]['plan']['p10_mes'])} / {f(b[1]['plan']['p10_mes'])} | {p(b[0]['plan']['P_anio_neg'])} / {p(b[1]['plan']['P_anio_neg'])} | {p(b[0]['plan']['neg60'])} / {p(b[1]['plan']['neg60'])} | "
                f"{round(b[0]['asiento_L150']['p22_3'])} / {round(b[1]['asiento_L150']['p22_3'])} | {b[0]['n_cumple']} / {b[1]['n_cumple']} | "
                f"{f(c[0]['plan']['med_mes'])} / {f(c[1]['plan']['med_mes'])} · {f(c[0]['plan']['p10_mes'])} / {f(c[1]['plan']['p10_mes'])} · {round(c[0]['plan']['neg60'])} / {round(c[1]['plan']['neg60'])} |")
        print(line)
# n contiguous
print("n contig plan", C["x0 | hc0.0 | T1 | contiguo"]["plan"]["n_caminos"], C["x0 | hc0.0 | T2 | contiguo"]["plan"]["n_caminos"])
print("cumple detail x0 hc0.35:", {per: C[f"x0 | hc0.35 | {per} | bootstrap"]["cumple_d1"] for per in ("T1","T2")})
print("cumple detail contig x0..3 hc0:", {(x,per): C[f"x{x} | hc0.0 | {per} | contiguo"]["cumple_d1"] for x in range(4) for per in ("T1","T2")})
