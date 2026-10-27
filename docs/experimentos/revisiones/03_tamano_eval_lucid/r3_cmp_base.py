import json, math
R = "/home/user/nqmaster-research/research/mine/"
E = json.load(open(R + "exp03_eval_size.json")); B = json.load(open(R + "objective_baseline.json"))
def cmp(a, b, tag):
    common = [q for q in a if q in b and isinstance(a[q], (int, float)) and isinstance(b[q], (int, float))]
    mx = 0; worst = None
    for q in common:
        d = abs(a[q] - b[q]) if not (isinstance(a[q], float) and math.isnan(a[q])) else 0
        if d > mx: mx = d; worst = q
    cu = (a.get("cumple") == b.get("cumple")) if "cumple" in a and "cumple" in b else None
    only_a = [q for q in a if q not in b]; only_b = [q for q in b if q not in a and not q.startswith(("evals_perdidas_mes [", "cuentas_perdidas_mes [", "aprobacion [", "dias_aprobar ["))]
    print(f"{tag:40s} campos comunes {len(common):3d} max|dif| {mx:.3g} ({worst}) cumple igual {cu}  solo-exp03 {only_a} solo-base {only_b}")
for hc in ("0.0", "0.35", "1.0"):
    for per in ("T1", "T2"):
        cmp(E["asiento"][f"L150 6c/3c | hc{hc} | {per}"], B["asientos"][f"L150 6c/3c | hc{hc} | {per} | coupon"], f"asiento hc{hc} {per}")
        cmp(E["plan"][f"plan k6 | hc{hc} | {per}"], B["plan"][f"5 L150 + 3 MFFU | hc{hc} | {per} | coupon"], f"plan hc{hc} {per}")
        cmp(E["asiento_contiguo"][f"L150 6c/3c | hc{hc} | {per}"], B["asientos_contiguo"][f"L150 6c/3c | hc{hc} | {per} | coupon"], f"asiento_contig hc{hc} {per}")
        cmp(E["plan_contiguo"][f"plan k6 | hc{hc} | {per}"], B["plan_contiguo"][f"5 L150 + 3 MFFU | hc{hc} | {per} | coupon"], f"plan_contig hc{hc} {per}")
