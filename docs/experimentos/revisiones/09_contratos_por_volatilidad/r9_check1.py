"""r9_check1: (a) diff textual race vs race_v, seat_flow vs seat_flow_v; (b) V0 del JSON de exp09 contra objective_baseline.json."""
import os, sys, json, inspect, difflib
MINE = "/home/user/nqmaster-research/research/mine"; os.chdir(MINE); sys.path.insert(0, MINE)
import prop_wf as P, objective as O, exp09_volsize as X


def body(f):
    src = inspect.getsource(f.py_func if hasattr(f, "py_func") else f).splitlines()
    return [l for l in src if not l.strip().startswith('"""') and not l.strip().startswith("@")]


for a, b in ((P.race, X.race_v), (O.seat_flow, X.seat_flow_v)):
    print("=" * 30, a.__name__ if hasattr(a, "__name__") else a, "vs", b.__name__ if hasattr(b, "__name__") else b)
    for l in difflib.unified_diff(body(a), body(b), lineterm="", n=0): print(l)

B = json.load(open("objective_baseline.json")); E = json.load(open("exp09_volsize.json"))
keys = ("med_mes", "p10_mes", "p90_mes", "neg60", "neg60_mtm", "evals_perdidas_mes", "aprobacion", "dias_aprobar", "dias_aprobar_p75", "evals_anio", "retiros_anio", "cuentas_perdidas_mes")
mx = 0.0; nchk = 0
for hc in (0.0, 0.35):
    for per in ("T1", "T2"):
        for src, bp, bs in (("bootstrap", "plan", "asientos"), ("contiguo", "plan_contiguo", "asientos_contiguo")):
            c = E["celdas"][f"V0 | {src} | hc{hc} | {per}"]
            pb = B[bp][f"5 L150 + 3 MFFU | hc{hc} | {per} | coupon"]; sb = B[bs][f"L150 6c/3c | hc{hc} | {per} | coupon"]
            for k in keys:
                for nm, x, y in (("plan", c["plan"].get(k), pb.get(k)), ("asiento", c["asiento_L150"].get(k), sb.get(k))):
                    if x is None or y is None: continue
                    d = abs(x - y); nchk += 1; mx = max(mx, d)
                    if d > 1e-9: print("DIFF", src, hc, per, nm, k, x, y)
            p22b = B["asientos"][f"L150 6c/3c | hc{hc} | {per} | coupon"]["p22_3"]
            if abs(c["asiento_L150"]["p22_3"] - p22b) > 1e-9: print("DIFF p22", src, hc, per, c["asiento_L150"]["p22_3"], p22b)
            # D1 sobre la base (como objective.table_d1)
            se = dict(sb); se["p22_3"] = p22b; v = O.verdict_d1(pb, se)
            if v != c["cumple_d1"]: print("DIFF verdict", src, hc, per, v, c["cumple_d1"])
print(f"V0 vs objective_baseline.json: {nchk} cifras comparadas, max |diff| = {mx}")
