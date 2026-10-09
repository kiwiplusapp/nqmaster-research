"""acct1c: final candidate table (reads acct1c_eval.csv, acct1c_life*.csv; no simulation) -> acct1c_final.csv"""
import pandas as pd
pd.set_option("display.width", 320); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 60)
L1 = pd.read_csv("acct1c_life.csv"); L2 = pd.read_csv("acct1c_life2.csv"); L3 = pd.read_csv("acct1c_life3.csv"); E = pd.read_csv("acct1c_eval.csv")
C12, C9, UF = "Flex U/EST C1200 oroWRx2 G1400", "Flex U/EST C900 oroWRx2 G1400", "Flex U fijo oroR G1400"
CAND = {   # name: (life frame, eval, fprof, X, extra filter, eval-table key (eval, firm, G))
    "A  eval Estable C1200 1c -> fondeada 1c Ultra": (L2, C12, "1c Ultra completo", 4000.0, None, ("U/EST C1200 + oro WinRate x2", "Flex50", 1400.0)),
    "B  eval Estable C1200 1c -> fondeada 1c, 2c desde colchon 2100": (L2, C12, "Ultra 1c -> 2c desde colchon 2100", 4000.0, None, ("U/EST C1200 + oro WinRate x2", "Flex50", 1400.0)),
    "C  eval Estable C1200 1c -> fondeada 1c, 2c desde colchon 1500": (L2, C12, "Ultra 1c -> 2c desde colchon 1500", 4000.0, None, ("U/EST C1200 + oro WinRate x2", "Flex50", 1400.0)),
    "D  eval Estable C1200 1c -> fondeada AdaptiveSize 2->1 DD1000, oro x2": (L3, C12, "NQ Adaptive 2->1 DD 1000 + oro Robust x2", 4000.0, None, ("U/EST C1200 + oro WinRate x2", "Flex50", 1400.0)),
    "E  eval Estable C1200 1c -> fondeada 2c escalones 750/1500": (L2, C12, "2c Ultra escalones 750/1500", 4000.0, None, ("U/EST C1200 + oro WinRate x2", "Flex50", 1400.0)),
    "F  eval Estable C1200 1c + ATR<1.15 -> fondeada 1c Ultra": (L2, C12 + " ATR", "1c Ultra completo", 4000.0, None, ("U/EST C1200 + oro WinRate x2", "Flex50", 1400.0)),
    "G  eval Estable C900 1c -> fondeada 1c, 2c desde colchon 1500": (L2, C9, "Ultra 1c -> 2c desde colchon 1500", 4000.0, None, ("U/EST C900 + oro WinRate x2", "Flex50", 1400.0)),
    "H  eval Ultra fijo 1c -> fondeada 2c Ultra": (L2, UF, "2c Ultra completo", 4000.0, None, ("U fijo + oro Robust x1", "Flex50", 1400.0)),
    "I  eval Ultra fijo 1c -> fondeada 1c Ultra": (L2, UF, "1c Ultra completo", 4000.0, None, ("U fijo + oro Robust x1", "Flex50", 1400.0)),
    "J  eval Ultra fijo 1c -> fondeada AdaptiveSize 2->1 DD1500, oro x2": (L3, UF, "NQ Adaptive 2->1 DD 1500 + oro Robust x2", 4000.0, None, ("U fijo + oro Robust x1", "Flex50", 1400.0)),
}
rows = []
for nm, (Lf, ev, fp, X, _, ek) in CAND.items():
    s = Lf[(Lf["eval"] == ev) & (Lf.fprof == fp) & (Lf.X == X)]
    assert len(s) == 9, (nm, len(s))
    r = dict(setup=nm)
    for p in ("IS", "C24", "REAL"):
        for t, tn in (("historia", "H"), ("costo +1 tick", "T"), ("Monte Carlo", "MC")):
            r[f"{p}_{tn}"] = round(s[(s.per == p) & (s.test == t)].mo.iloc[0])
    r["mes_media9"] = round(s.mo.mean()); r["mes_peor9"] = round(s.mo.min()); r["P_anio_neg_max"] = round(s.ploss.max(), 1)
    r["cash_mes_fondeado"] = round(s.cash_per_funded_month.mean()); r["cash_mes_fondeado_peor"] = round(s.cash_per_funded_month.min())
    r["quemas_fond_anio"] = round(s.fbust.mean(), 1); r["pagos_anio"] = round(s.payouts.mean(), 1); r["evals_anio"] = round(s.evals.mean(), 1)
    r["fondeado_%tiempo"] = round(s.funded_share.mean())
    e = E[(E["eval"] == ek[0]) & (E.firm == ek[1]) & (E.G == ek[2]) & (E.start == ("ATR<1.15" if "ATR" in ev else "todos"))]
    h = e[e.test == "historia"].set_index("per"); b = e[e.test == "bootstrap"].set_index("per"); tt = e[e.test == "costo +1 tick"].set_index("per")
    r["aprob_hist_IS/C24/REAL"] = "/".join(f"{h.loc[p, 'pass_pct']:.0f}" for p in ("IS", "C24", "REAL"))
    r["aprob_+1tick"] = "/".join(f"{tt.loc[p, 'pass_pct']:.0f}" for p in ("IS", "C24", "REAL"))
    r["aprob_boot"] = "/".join(f"{b.loc[p, 'pass_pct']:.0f}" for p in ("IS", "C24", "REAL"))
    r["mediana_dias_hist"] = "/".join(f"{h.loc[p, 'med_days']:.0f}" for p in ("IS", "C24", "REAL"))
    r["P<=22d"] = round(h.p22.mean()); r["P<=33d"] = round(h.p33.mean()); r["fondeada<=33d_reintentando"] = round(h.fund33.mean())
    rows.append(r)
F = pd.DataFrame(rows); F.to_csv("acct1c_final.csv", index=False)
print(F.drop(columns=[c for c in F.columns if c[:3] in ("IS_", "C24", "REA")]).to_string(index=False))
print(F[["setup"] + [c for c in F.columns if c[:3] in ("IS_", "C24", "REA")]].to_string(index=False))
