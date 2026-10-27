"""r4_base_compare.py: X = 6.000 de exp04 contra objective_baseline.json y exp03 k6 (solo lectura)."""
import json, math
R = "/home/user/nqmaster-research/research/mine/"
d = json.load(open(R + "exp04_payout_x.json")); b = json.load(open(R + "objective_baseline.json")); e3 = json.load(open(R + "exp03_eval_size.json"))


def cmp(a, c, tag):
    keys = sorted(set(a) & set(c)); diffs = []
    for k in keys:
        x, y = a[k], c[k]
        if isinstance(x, dict) or isinstance(y, dict):
            if x != y: diffs.append((k, x, y))
            continue
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            if not (x == y or (math.isnan(x) and math.isnan(y))): diffs.append((k, x, y))
    mx = max([abs(x - y) for k, x, y in diffs if isinstance(x, (int, float))], default=0.0)
    print(f"{tag}: {len(keys)} campos comunes, {len(diffs)} distintos (max abs {mx:.3g}); solo en exp04: {sorted(set(a)-set(c))[:6]} ; solo en base: {sorted(set(c)-set(a))[:8]}")
    for k, x, y in diffs[:6]: print("   ", k, x, y)


for hc in ("0.0", "0.35", "1.0"):
    for per in ("T1", "T2"):
        cmp(d["asiento"][f"L150 X6000 | hc{hc} | {per}"], b["asientos"][f"L150 6c/3c | hc{hc} | {per} | coupon"], f"asiento hc{hc} {per}")
        cmp(d["plan"][f"plan X6000 | hc{hc} | {per}"], b["plan"][f"5 L150 + 3 MFFU | hc{hc} | {per} | coupon"], f"plan    hc{hc} {per}")
        cmp(d["asiento_contiguo"][f"L150 X6000 | hc{hc} | {per}"], b["asientos_contiguo"][f"L150 6c/3c | hc{hc} | {per} | coupon"], f"as.cont hc{hc} {per}")
        cmp(d["plan_contiguo"][f"plan X6000 | hc{hc} | {per}"], b["plan_contiguo"][f"5 L150 + 3 MFFU | hc{hc} | {per} | coupon"], f"pl.cont hc{hc} {per}")
        cmp(d["plan"][f"plan X6000 | hc{hc} | {per}"], e3["plan"][f"plan k6 | hc{hc} | {per}"], f"exp03 k6 plan hc{hc} {per}")
        cmp(d["asiento"][f"L150 X6000 | hc{hc} | {per}"], e3["asiento"][f"L150 6c/3c | hc{hc} | {per}"], f"exp03 k6 asiento hc{hc} {per}")
print("n_caminos contiguo plan:", {k: v["n_caminos"] for k, v in d["plan_contiguo"].items() if "X6000" in k})
print("n_caminos contiguo asiento:", {k: v["n_caminos"] for k, v in d["asiento_contiguo"].items() if "X6000" in k})
