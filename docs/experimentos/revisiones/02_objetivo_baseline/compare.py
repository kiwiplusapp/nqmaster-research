import json
R = "/home/user/nqmaster-research/research/mine/"
O = json.load(open(R + "objective_baseline.json")); IP = json.load(open(R + "integ_paired.json"))["seats"]; PO = json.load(open(R + "integ_port.json"))
bad = 0
print("== asientos (coupon, rot) objective vs integ_paired.json: med p10 Pneg busts/yr evals/yr")
for k, r in O["asientos"].items():
    nm, hc, per, fee = [x.strip() for x in k.split("|")]
    if fee != "coupon": continue
    ref = IP[f"{nm} | {hc} | {per}"]
    got = dict(med=round(r["med_mes"]), p10=round(r["p10_mes"]), Pneg=round(r["P_anio_neg"], 1), busts=round(r["cuentas_perdidas_mes"] * 12, 2), evals=round(r["evals_anio"], 1))
    exp = {q: ref[q] for q in got}
    ok = got == exp; bad += not ok
    print(("OK " if ok else "DIFF"), k, "got", got, "ref", exp)
    # list fee
    rl = O["asientos"].get(f"{nm} | {hc} | {per} | list")
    if rl is not None:
        gl = dict(med_list=round(rl["med_mes"]), Pneg_list=round(rl["P_anio_neg"], 1)); el = {q: ref[q] for q in gl}
        okl = gl == el; bad += not okl; print(("OK " if okl else "DIFF"), "   list:", gl, el)
print("== plan (coupon, rot) objective vs integ_port.json: med p10 p90 Pneg")
for k, r in O["plan"].items():
    nm, hc, per, fee = [x.strip() for x in k.split("|")]
    ref = PO[f"{hc} | {per} | coupon | rot"]
    got = dict(med=round(r["med_mes"]), p10=round(r["p10_mes"]), p90=round(r["p90_mes"]), Pneg=round(r["P_anio_neg"], 1)); exp = {q: ref[q] for q in got}
    ok = got == exp; bad += not ok; print(("OK " if ok else "DIFF"), k, "got", got, "ref", exp)
print("diferencias:", bad)
# internal consistency: evals_perdidas vs aprobacion vs evals_anio
print("== consistencia interna (asientos coupon): evals/anio ~ aprobadas + perdidas + abiertas ; retiros/anio ; p22_1 vs aprobacion")
for k, r in O["asientos"].items():
    if not k.endswith("coupon"): continue
    lost = r["evals_perdidas_mes"] * 12; opened = r["evals_abiertas_fin"]; ev = r["evals_anio"]
    passed = ev - lost - opened; apr = 100 * passed / (passed + lost)
    print(f"{k:38s} evals/yr {ev:5.2f} = perd {lost:5.2f} + abiertas {opened:5.3f} + aprob {passed:5.2f} -> aprob% {apr:5.1f} (json {r['aprobacion']:5.1f}); p22_1 {r['p22_1']:5.1f}; retiros/yr {r['retiros_anio']:5.2f} fondeadas/yr {passed:4.2f} busts/yr {r['cuentas_perdidas_mes']*12:4.2f} -> retiros por fondeada {r['retiros_anio']/passed:4.2f}")
