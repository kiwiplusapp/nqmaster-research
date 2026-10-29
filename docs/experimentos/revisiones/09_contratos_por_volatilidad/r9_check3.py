"""r9_check3: arnes que replica exp09_volsize.main (mismos caminos, sin escribir el JSON) para:
 (a) reproducir V0 / V1 del JSON (valida el arnes),
 (b) diagnostico: V1 con exposicion media igual a V0 en cada periodo (ATR_ref elegido para que el k medio de la eval sea ~6; usa el periodo entero: solo diagnostico),
 (c) sensibilidad: haircut -35 % proporcional al ATR del dia (h_t = hc x media del P&L x ATR_t / ATR medio del periodo) en vez de constante,
 (d) orden de suma del plan (L150 primero, como objective.contiguous) para el neg60_mtm contiguo hc0 T2."""
import os, sys, json, time, numpy as np
MINE = "/home/user/nqmaster-research/research/mine"; os.chdir(MINE); sys.path.insert(0, MINE)
import prop_wf as P, objective as O, exp09_volsize as X, exp03_eval_size as E3
H = O.H; L = H + 25; MAXEV = O.MAXEV
days, M, FU0, PER = O.setup(); atr = X.atr_days(days); n = len(days); idx = np.arange(n, dtype=np.int64)
rng_s = np.random.default_rng(20261021); rng_p = np.random.default_rng(4242); PS = {}; PP = {}
for hc in P.HC:
    for per, ii in PER.items(): PS[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, H, rng_s) for _ in range(1000)]
for hc in P.HC:
    for per, ii in PER.items(): PP[(hc, per)] = [P.boot_idx(ii[0], ii[-1] + 1, L, rng_p) for _ in range(1000)]
E = json.load(open("exp09_volsize.json"))


def hc_prop(fin, hc):
    h = np.zeros(n)
    for per, ii in PER.items(): h[ii] = hc * fin[ii].mean() * atr[ii] / atr[ii].mean()
    rest = days >= P.T2_END; h[rest] = hc * fin[rest].mean() * atr[rest] / atr[rest].mean() if rest.any() else 0
    return h


def cells(ke, kf, hc, pers=("T1", "T2"), prop=False, contig=True):
    FU = P.Fund(days, M)
    if prop:
        for mix in ((300, 4), (0, 4), (0, 8)): FU.H[(hc, mix)] = hc_prop(M[mix][2], hc)
        Hm = {m: FU.h(hc, m) for m in ((0, 4), (0, 8))}
    else: Hm = {m: P.haircut(days, M[m][2], hc) for m in ((0, 4), (0, 8))}
    AM = O.seat_args(FU, hc, X.MF, Hm); AL = X.l150_args(FU, hc, Hm, kf); out = {}; net = {}
    for per in pers:
        ii = PER[per]; st = np.arange(ii[0], ii[-1] + 2 - H, 5); stp = np.arange(ii[0], ii[-1] + 2 - L, 5)
        se_b = X.seat_cell(M, AL, PS[(hc, per)], ke); se_b["p22_3"] = X.p22_v(days, M, AL, ii, ke)
        pl_b, tot = X.plan_cell(M, AL, AM, PP[(hc, per)], ke); net[per] = tot
        out[("bootstrap", per)] = (pl_b, se_b, O.verdict_d1(pl_b, se_b))
        if contig:
            se_c = X.seat_cell(M, AL, [idx[s0:s0 + H] for s0 in st], ke); se_c["p22_3"] = se_b["p22_3"]
            pl_c, _ = X.plan_cell(M, AL, AM, [idx[s0:s0 + L] for s0 in stp], ke)
            out[("contiguo", per)] = (pl_c, se_c, O.verdict_d1(pl_c, se_c))
    return out, net


def show(tag, R):
    for (src, per), (pl, se, v) in R.items():
        print(f"  {tag:18s} {src:9s} {per} med {pl['med_mes']:7.0f} p10 {pl['p10_mes']:7.0f} neg60 {pl['neg60']:5.1f} p22 {se['p22_3']:5.1f} dias {se['dias_aprobar']:3.0f} cumple {sum(v.values())}/5 " + " ".join(("+" if x else "-") + k for k, x in v.items()), flush=True)


t0 = time.time()
KV0 = X.kvecs(days, atr, "V0"); KV1 = X.kvecs(days, atr, "V1")
# (a) validacion del arnes: V1 hc0.35 T1 contra el JSON
R1, N1 = cells(*KV1, 0.35, ("T1",)); R0, N0 = cells(*KV0, 0.35, ("T1",))
for mo, R in (("V0", R0), ("V1", R1)):
    for src in ("bootstrap", "contiguo"):
        j = E["celdas"][f"{mo} | {src} | hc0.35 | T1"]; pl = R[(src, "T1")][0]
        print(f"arnes {mo} {src}: med {pl['med_mes']:.4f} vs JSON {j['plan']['med_mes']:.4f}; neg60 {pl['neg60']:.4f} vs {j['plan']['neg60']:.4f}")
g = E3.paired(N1["T1"], N0["T1"]); print("arnes pareado hc0.35 T1", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in g.items()}, "JSON", E["pareado"]["V1 vs V0 | hc0.35 | T1"]["P_gain"], f"{time.time()-t0:.0f}s")

# (b) V1 con exposicion igual a V0 por periodo (diagnostico con lookahead)
ke_n = np.zeros(n); kf_n = np.zeros(n)
for per, ii in PER.items():
    best = None
    for ref in np.arange(200.0, 360.0, 0.25):
        ke = np.clip(np.round(6.0 * ref / atr[ii]), 3, 9); d = abs(ke.mean() - 6.0)
        if best is None or d < best[0]: best = (d, ref)
    ref = best[1]; ke_n[ii] = np.clip(np.round(6.0 * ref / atr[ii]), 3, 9); kf_n[ii] = np.clip(np.round(3.0 * ref / atr[ii]), 2, 4)
    print(f"(b) {per}: ref igual-exposicion {ref:.2f} -> k eval medio {ke_n[ii].mean():.3f}, k fondeada medio {kf_n[ii].mean():.3f}")
rest = days >= P.T2_END; ke_n[rest] = 6; kf_n[rest] = 3
for hc in (0.0, 0.35):
    Rn, Nn = cells(ke_n, kf_n, hc, contig=True); R0, N0 = cells(*KV0, hc, contig=False); show(f"V1=exp hc{hc}", Rn)
    for per in ("T1", "T2"):
        g = E3.paired(Nn[per], N0[per]); print(f"  (b) V1 igual-exposicion vs V0 hc{hc} {per}: gan. mediana {g['med']:.0f} ({100*g['rel']:.1f} %), P(ganar) {g['P_gain']:.2f}, P(perder>5%) {g['P_loss5']:.2f}", flush=True)

# (c) haircut proporcional al ATR (lectura alternativa de -35 %)
Rp0, Np0 = cells(*KV0, 0.35, prop=True); Rp1, Np1 = cells(*KV1, 0.35, prop=True)
show("V0 hc-prop", Rp0); show("V1 hc-prop", Rp1)
for per in ("T1", "T2"):
    g = E3.paired(Np1[per], Np0[per]); print(f"  (c) hc proporcional V1 vs V0 {per}: gan. mediana {g['med']:.0f} ({100*g['rel']:.1f} %), P(ganar) {g['P_gain']:.2f}, P(perder>5%) {g['P_loss5']:.2f}")
sc = {}
for mo in ("V0", "V1"):
    s = sum(E["celdas"][f"{mo} | {src} | hc0.0 | T1"]["n_cumple"] for src in ("bootstrap", "contiguo"))
    Rp = Rp0 if mo == "V0" else Rp1; s += sum(sum(Rp[(src, "T1")][2].values()) for src in ("bootstrap", "contiguo")); sc[mo] = s
print("(c) puntaje T1 con -35 % proporcional:", sc, f"{time.time()-t0:.0f}s")

# (d) orden de suma del plan contiguo hc0 T2 (L150 primero, como objective.contiguous)
FU = P.Fund(days, M); Hm = {m: P.haircut(days, M[m][2], 0.0) for m in ((0, 4), (0, 8))}; AM = O.seat_args(FU, 0.0, X.MF, Hm); AL = O.seat_args(FU, 0.0, X.L150, Hm)
ii = PER["T2"]; stp = np.arange(ii[0], ii[-1] + 2 - L, 5); flows = np.zeros((len(stp), L)); mtms = np.zeros((len(stp), L)); tot = np.zeros(len(stp)); evs = []; nev = []
for b, s0 in enumerate(stp):
    bi = idx[s0:s0 + L]; ev_all = np.zeros((8 * MAXEV, 5)); kk = 0
    for A, cnt in ((AL, 5), (AM, 3)):
        for s in range(cnt):
            f = np.zeros(L); mm = np.zeros(L); ev = np.zeros((MAXEV, 5)); k = O.run_seat(M, A, bi, 5 * s, H, f, mm, ev)
            flows[b] += f; mtms[b] += mm; tot[b] += f.sum() / 12.0; ev_all[kk:kk + k] = ev[:k]; kk += k
    evs.append(ev_all); nev.append(kk)
r = E3.plan_metrics(flows, mtms, evs, nev, tot)
print(f"(d) contiguo hc0 T2 con L150 primero: neg60_mtm {r['neg60_mtm']:.6f} (base 23.922754, exp09 23.918374); neg60 {r['neg60']:.6f}")
