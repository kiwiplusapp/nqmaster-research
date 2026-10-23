# Round 5 integration (2026-10-21), copied from the session scratchpad (summ.py). Run from research/mine. Outputs: integ_paired.json (reads research/tmp/integ_paired.pkl from integ_paired.py)
import pickle, numpy as np, json
D = pickle.load(open("../tmp/integ_paired.pkl", "rb"))
def m(x): return x[:, 0] / 12
res = {}
print("== per seat ($/month, coupon, rotation) med p10 Pneg busts/yr evals/yr pay62")
for hc in (0.0, 0.35, 1.0):
    for per in ("T1", "T2"):
        for nm in ("L150 6c/3c", "Flex50 2c/2c", "Flex50 2c/1c", "Pro50 4c/1c", "Pro50 4c/2c", "MFFU 1x8", "MFFU fix2", "MFFU fix3"):
            x = D[(nm, "coupon", "rot", hc, per)]; v = m(x); f = x[:, 5]
            r = dict(med=round(float(np.median(v))), p10=round(float(np.percentile(v, 10))), Pneg=round(100 * float((v < 0).mean()), 1),
                     busts=round(float(x[:, 3].mean()), 2), evals=round(float(x[:, 1].mean()), 1), pay62=round(100 * float(((f >= 0) & (f < 62)).mean()), 1))
            xl = D[(nm, "list", "rot", hc, per)]; r["med_list"] = round(float(np.median(m(xl)))); r["Pneg_list"] = round(100 * float((m(xl) < 0).mean()), 1)
            if (nm, "coupon", "end", hc, per) in D:
                xe = D[(nm, "coupon", "end", hc, per)]; r["med_end"] = round(float(np.median(m(xe))))
            res[f"{nm} | hc{hc} | {per}"] = r; print(hc, per, nm, r)
def pair(a, b, fee, hc, per):
    g = m(D[(a, fee, "rot", hc, per)]) - m(D[(b, fee, "rot", hc, per)])
    return dict(med=round(float(np.median(g))), ci90=[round(float(np.percentile(g, 5))), round(float(np.percentile(g, 95)))], P=round(float((g > 0).mean()), 3))
print("== paired gains (challenger - incumbent)")
pairs = [("Flex50 2c/2c", "L150 6c/3c"), ("Pro50 4c/1c", "L150 6c/3c"), ("Pro50 4c/2c", "L150 6c/3c"), ("Flex50 2c/2c", "Pro50 4c/1c"),
         ("Flex50 2c/2c", "Pro50 4c/2c"), ("Pro50 4c/1c", "Flex50 2c/2c"), ("Pro50 4c/2c", "Flex50 2c/2c"), ("Flex50 2c/1c", "Pro50 4c/1c"), ("Pro50 4c/1c", "Flex50 2c/1c"),
         ("L150 6c/3c", "Flex50 2c/2c"), ("L150 6c/3c", "Pro50 4c/1c"), ("MFFU fix2", "MFFU 1x8"), ("MFFU fix3", "MFFU 1x8")]
P = {}
for a, b in pairs:
    for fee in ("coupon", "list"):
        for hc in (0.0, 0.35, 1.0):
            for per in ("T1", "T2"):
                k = f"{a} vs {b} | {fee} | hc{hc} | {per}"; P[k] = pair(a, b, fee, hc, per)
                if hc == 0.35 or hc == 1.0: print(k, P[k])
def rule(a, b, mffu=False):
    ok = True
    for fee in ("coupon", "list"):
        for per in ("T1", "T2"):
            p = P[f"{a} vs {b} | {fee} | hc0.35 | {per}"]
            pa = 100 * (m(D[(a, fee, "rot", 0.35, per)]) < 0).mean(); pb = 100 * (m(D[(b, fee, "rot", 0.35, per)]) < 0).mean()
            if not (p["med"] > 0 and p["P"] >= 0.80 and pa <= pb + 3): ok = False
            if mffu and np.median(m(D[(a, fee, "rot", 1.0, per)])) < np.median(m(D[(b, fee, "rot", 1.0, per)])) - 100: ok = False
    return ok
verdict = {f"{a} replaces {b}": rule(a, b, a.startswith("MFFU")) for a, b in pairs}
print(verdict)
json.dump(dict(seats=res, paired=P, rule=verdict), open("integ_paired.json", "w"), indent=1)
