"""diag_partition.py (2026-10-30, diagnostico 11 / frente 5D): repartir los modulos entre plazas en vez de que todas operen lo mismo.

Pregunta (diagnostico 06: el plan es una sola cuenta multiplicada): si la mitad de las plazas opera el grupo de modulos A y la otra mitad el
grupo B, con el doble de contratos para conservar la exposicion del plan, los quiebres dejan de coincidir. Pero cada plaza queda menos
diversificada. Pre-registro en docs/PLAN_2026-10-30_diag11.md.

Datos: six_ultra6_trades.pkl (real NQ 2020-10 .. 2026-10, $ por contrato con costos de la lista), sin CA04V / GD03 / ENG26 (fuera del set
2027). Dias sin trades = 0. T1 = 2020-23 (aca se elige la particion), T2 = 2024-26 (control).
Particiones: (a) "alterna": modulos ordenados por $/dia de T1, A / B alternados (medias parecidas); (b) "favorable": entre 2.000 particiones
al azar con medias de T1 a +-10 %, la de menor correlacion diaria A-B en T1 (lo mas a favor de la idea).
Proxy de quiebre por plaza: caminos bootstrap de 252 dias (bloques de 21, 2.000 caminos, rng 20261030), caida maxima desde el pico (incluye el
saldo inicial) >= umbral por contrato: 1.500 (Lucid 150K fondeada 3c, trailing 4.500) y 2.000 (MFFU 50K 1c). Base = conjunto completo x1;
particion = grupo x2 (misma exposicion del plan).
Por par de plazas (una de cada lado en la particion, dos iguales en la base): quiebres esperados por par-anio y P(las dos quiebran en el mismo
camino). Criterio pre-registrado: la particion pasa al motor de campana solo si, en T1 y en T2 y con los dos umbrales, los quiebres esperados
por par suben <= 10 % y P(las dos quiebran) baja >= 30 %. Si no, 5D queda cerrado.
Post-hoc (NO pre-registrado, agregado al ver que el proxy satura cerca de 100 %): quiebres por plaza-anio con renovacion (al quebrar, la
plaza arranca de nuevo) y coincidencia de quiebres entre las dos plazas (+-5 dias). Solo informa; no cambia el veredicto pre-registrado.
Run (desde research/mine): python3 diag_partition.py  -> diag_partition.json"""
import os, json, pickle, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "diag_partition.json")
NB, L, BL, SEED = 2000, 252, 21, 20261030
THR = (1500.0, 2000.0)


def daily():
    T = pickle.load(open(os.path.join(HERE, "six_ultra6_trades.pkl"), "rb"))["Ultra6"]
    T = T[~T["mod"].isin(["CA04V", "GD03", "ENG26"])].copy()
    T["pnl"] = T.u * T.w
    return T.pivot_table(index="date", columns="mod", values="pnl", aggfunc="sum").fillna(0.0)


def boot_idx(n, rng):
    nb = -(-L // BL); st = rng.integers(0, n - BL + 1, size=(NB, nb))
    return (st[:, :, None] + np.arange(BL)[None, None, :]).reshape(NB, -1)[:, :L]


def maxdd(x):                       # x: (NB, L) daily P&L -> max drawdown from the running peak, start included
    eq = np.cumsum(x, axis=1); pk = np.maximum.accumulate(np.concatenate([np.zeros((len(x), 1)), eq], axis=1), axis=1)[:, 1:]
    return (pk - eq).max(axis=1)


def pair_stats(a, b, idx):
    """a, b: daily P&L vectors of the two seats (same days); idx: bootstrap day indices (shared path = same market)."""
    da, db = maxdd(a[idx]), maxdd(b[idx]); r = {}
    for t in THR:
        ba, bb = da >= t, db >= t
        r[str(int(t))] = dict(p_quiebre_a=round(100 * ba.mean(), 1), p_quiebre_b=round(100 * bb.mean(), 1),
                              quiebres_por_par=round(float(ba.mean() + bb.mean()), 3), p_ambas=round(100 * (ba & bb).mean(), 1))
    r["media_dia_par"] = round(float((a + b).mean()), 1)
    return r


from numba import njit


@njit(cache=True)
def renewal(x, thr):
    """x: (NB, L) daily P&L of one seat; a bust when equity falls thr below its running peak (start included); the seat then restarts
    (new account: peak = equity). Returns the bust count per path and a (NB, L) 0/1 matrix of bust days."""
    nb, n = x.shape; cnt = np.zeros(nb); day = np.zeros((nb, n), np.uint8)
    for i in range(nb):
        eq = 0.0; pk = 0.0
        for j in range(n):
            eq += x[i, j]
            if eq > pk: pk = eq
            if pk - eq >= thr: cnt[i] += 1; day[i, j] = 1; pk = eq
    return cnt, day


def posthoc(a, b, idx, W=5):
    """NO PRE-REGISTRADO (el proxy pre-registrado satura cerca de 100 %): quiebres por plaza-anio con renovacion, y fraccion de los quiebres
    de A que caen a +-W dias de un quiebre de B en el mismo camino (coincidencia)."""
    r = {}
    for t in THR:
        ca, da = renewal(np.ascontiguousarray(a[idx]), t); cb, db = renewal(np.ascontiguousarray(b[idx]), t)
        near = np.zeros_like(db)
        for k in range(-W, W + 1): near |= np.roll(db, k, axis=1)
        co = (da & near).sum() / max(1, da.sum())
        r[str(int(t))] = dict(quiebres_a=round(float(ca.mean()), 2), quiebres_b=round(float(cb.mean()), 2), quiebres_por_par=round(float(ca.mean() + cb.mean()), 2),
                              coincidencia=round(100 * float(co), 1))
    return r


def main():
    D = daily(); t1 = D.index < 20230101; mods = list(D.columns)
    m1 = D[t1].mean(); order = m1.sort_values(ascending=False).index.tolist()
    alt = (order[0::2], order[1::2])
    rng = np.random.default_rng(SEED); tot = m1.sum(); best, bc = None, 9.0
    for _ in range(2000):
        msk = rng.random(len(mods)) < 0.5; A = [m for m, k in zip(mods, msk) if k]; B = [m for m, k in zip(mods, msk) if not k]
        if not A or not B or abs(m1[A].sum() - tot / 2) > 0.1 * tot / 2: continue
        c = np.corrcoef(D.loc[t1, A].sum(axis=1), D.loc[t1, B].sum(axis=1))[0, 1]
        if c < bc: bc, best = c, (A, B)
    res = dict(modulos=mods, corr_media_entre_modulos_T1=round(float(np.corrcoef(D[t1].T.values)[np.triu_indices(len(mods), 1)].mean()), 3),
               particiones={"alterna": dict(A=alt[0], B=alt[1]), "favorable": dict(A=best[0], B=best[1])}, periodos={})
    for per, msk in (("T1 2020-23", t1), ("T2 2024-26", ~t1)):
        X = D[msk]; full = X.sum(axis=1).to_numpy(); idx = boot_idx(len(X), np.random.default_rng(SEED))
        out = dict(dias=int(msk.sum()), base=pair_stats(full, full, idx))
        out["posthoc_renovacion"] = dict(base=posthoc(full, full, idx))
        for nm, (A, B) in (("alterna", alt), ("favorable", best)):
            a = 2 * X[A].sum(axis=1).to_numpy(); b = 2 * X[B].sum(axis=1).to_numpy()
            out[nm] = pair_stats(a, b, idx); out[nm]["corr_A_B"] = round(float(np.corrcoef(a, b)[0, 1]), 3)
            out["posthoc_renovacion"][nm] = posthoc(a, b, idx)
        res["periodos"][per] = out
    res["posthoc_edge"] = {}                        # post-hoc tambien con -35 % y edge cero (resta pareja de la media diaria de cada plaza)
    for per, msk in (("T1", t1), ("T2", ~t1)):
        X = D[msk]; idx = boot_idx(len(X), np.random.default_rng(SEED)); A, B = best
        for hc in (0.35, 1.0):
            full = X.sum(axis=1).to_numpy(); a = 2 * X[A].sum(axis=1).to_numpy(); b = 2 * X[B].sum(axis=1).to_numpy()
            full, a, b = full - hc * full.mean(), a - hc * a.mean(), b - hc * b.mean()
            res["posthoc_edge"]["%s edge -%d%%" % (per, round(hc * 100))] = dict(base=posthoc(full, full, idx), favorable=posthoc(a, b, idx))
    ok = True
    for per, o in res["periodos"].items():
        for nm in ("alterna", "favorable"):
            for t in THR:
                b0, p = o["base"][str(int(t))], o[nm][str(int(t))]
                pasa = p["quiebres_por_par"] <= 1.10 * b0["quiebres_por_par"] and p["p_ambas"] <= 0.70 * b0["p_ambas"]
                o[nm][str(int(t))]["pasa"] = bool(pasa)
                if nm == "favorable": ok = ok and pasa
    res["veredicto"] = "la particion pasa al motor de campana" if ok else "no pasa: 5D cerrado"
    json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)
    for per, o in res["periodos"].items():
        print(per, "dias", o["dias"])
        for nm in ("base", "alterna", "favorable"):
            s = o[nm]; print("  %-9s $/dia par %6.1f corr %s | " % (nm, s["media_dia_par"], s.get("corr_A_B", "-")) +
                  " | ".join("DD>=%s: quiebre %.1f/%.1f %% por par %.3f ambas %.1f %%%s" % (t, s[t]["p_quiebre_a"], s[t]["p_quiebre_b"], s[t]["quiebres_por_par"], s[t]["p_ambas"],
                             "" if nm == "base" else (" PASA" if s[t]["pasa"] else " no")) for t in ("1500", "2000")))
    print(res["veredicto"])
    print("POST-HOC (no pre-registrado): quiebres por plaza en 252 dias con renovacion; coincidencia = % de quiebres de A a +-5 dias de uno de B")
    for per, o in res["periodos"].items():
        for nm in ("base", "alterna", "favorable"):
            q = o["posthoc_renovacion"][nm]
            print("  %s %-9s " % (per[:2], nm) + " | ".join("DD>=%s: %.2f + %.2f = %.2f por par, coincidencia %.1f %%" % (t, q[t]["quiebres_a"], q[t]["quiebres_b"], q[t]["quiebres_por_par"], q[t]["coincidencia"]) for t in ("1500", "2000")))
    for k, v in res["posthoc_edge"].items():
        print("  %-14s " % k + " | ".join("DD>=%s base %.2f favorable %.2f (coincidencia %.0f %%)" % (t, v["base"][t]["quiebres_por_par"], v["favorable"][t]["quiebres_por_par"], v["favorable"][t]["coincidencia"]) for t in ("1500", "2000")))


if __name__ == "__main__":
    main()
