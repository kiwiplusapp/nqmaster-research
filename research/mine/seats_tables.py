"""Markdown tables from seats_plan.json / seats_plan_gold.json (2026-10-17 plan to $250-300 per day). Usage: python3 seats_tables.py"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
J = {}
for f in ("seats_plan.json", "seats_plan_gold.json"):
    p = os.path.join(HERE, f)
    if os.path.exists(p): J.update(json.load(open(p)))
SETS = [k.split(" | ")[0] for k in J]; SETS = list(dict.fromkeys(SETS))
PLANS = ["1 MFFU 50K 1c", "3 MFFU 50K 1c", "3 MFFU step-up", "5 Lucid Flex 50K 1c", "5 Lucid Flex 50K 2c", "1 Lucid 150K 6c/3c", "5 Lucid 150K 6c/3c",
         "3 MFFU 1c + 5 Lucid 1c", "3 MFFU 1c + 5 Lucid 2c", "3 MFFU step-up + 5 Lucid 2c", "3 MFFU 1c + 5 Lucid 150K"]
def cell(r, k, a, b): return f"{r[k][a]} / {r[k][b]}" if k in r else ""
for s in SETS:
    print(f"\n### {s}\n")
    print("| Plan | Edge | Historia $/día T1 / T2 | Bootstrap mediana | p10 | P(≥$250/día) | P(año negativo) |")
    print("|---|---|---|---|---|---|---|")
    for e in ("0", "35", "50", "100"):
        R = J.get(f"{s} | edge-{e}%", {})
        for pl in PLANS:
            if pl not in R: continue
            r = R[pl]
            print(f"| {pl} | −{e}% | {r['T1_hist']['mean_day']} / {r['T2_hist']['mean_day']} | {r['T1_boot']['median_day']} / {r['T2_boot']['median_day']} | {r['T1_boot']['p10_day']} / {r['T2_boot']['p10_day']} | {r['T1_boot']['P_ge_250_day']:.0f}% / {r['T2_boot']['P_ge_250_day']:.0f}% | {r['T1_boot']['P_neg_year']:.0f}% / {r['T2_boot']['P_neg_year']:.0f}% |")
