"""Report page 'Perfil final NQ + Oro' (update 2026-10-07): 5 x LucidFlex 150K plan, new overnight modules, code reviews, NT validator.
Reads acct_bigger.csv, acct_150k.csv, multi150c.csv, multi50.csv, nqdrive_lc.csv, gnq_port.csv, nqdrive_port.csv, morning_bugs.json.
Usage: python report_150k.py <out.html>"""
import sys, json, pandas as pd
OUT = sys.argv[1]
f0 = lambda v: f"{v:,.0f}".replace(",", ".")
f1 = lambda v: f"{v:.1f}".replace(".", ",")
f2 = lambda v: f"{v:.2f}".replace(".", ",")
HL = ' class="hl"'
B = pd.read_csv("acct_bigger.csv"); B["cand"] = B.cuenta + " " + B.k_eval.astype(str) + " / " + B.k_fondeada.astype(str)
B2 = pd.read_csv("acct_150k.csv"); B2 = B2[(B2.c1 == 1687.5) & (B2.X == 6000.0)].copy(); B2["cuenta"] = "150K"
B2["cand"] = "150K " + B2.k_eval.astype(str) + " / " + B2.k_fondeada.astype(str)
B = pd.concat([B[B.cuenta != "150K"], B2], ignore_index=True)
SB = B.groupby("cand").agg(mean9=("mo", "mean"), min9=("mo", "min"), ev=("evals", "sum"), ps=("passes", "sum"), evy=("evals", "mean")).reset_index(); SB["pr"] = 100 * SB.ps / SB.ev
N = pd.read_csv("nqdrive_lc.csv"); SN = N.groupby(["cuenta", "cand"]).agg(mean9=("mo", "mean"), min9=("mo", "min")).reset_index()
def sn(c, k): r = SN[(SN.cuenta == c) & (SN.cand == k)].iloc[0]; return r.mean9, r.min9
M = pd.read_csv("multi150c.csv"); M0 = pd.read_csv("multi150b.csv")
top_mean, top_min = sn("150K 6c/3c", "+LF06+LF0430"); m50_mean, m50_min = sn("50K 2c/2c", "+LF06+LF0430")
rows_size = [("150K", "6 / 3", "con NF05 + LF06 + LF0430", top_mean, top_min, True), ("150K", "6 / 3", "sin módulos nuevos", *SB[SB.cand == "150K 6 / 3"][["mean9", "min9"]].iloc[0], False),
             ("100K", "4 / 3", "sin módulos nuevos", *SB[SB.cand == "100K 4 / 3"][["mean9", "min9"]].iloc[0], False),
             ("50K", "2 / 2", "con NF05 + LF06 + LF0430", m50_mean, m50_min, False), ("50K", "2 / 2", "sin módulos nuevos", *SB[SB.cand == "50K 2 / 2"][["mean9", "min9"]].iloc[0], False)]
srows = "".join(f"<tr{HL if h else ''}><td><b>{a}</b></td><td>{k}</td><td>{t}</td><td>${f0(m)}</td><td>${f0(n)}</td></tr>" for a, k, t, m, n, h in rows_size)
def mrow(df, plan, lab, hl=False):
    x = df[df.plan == plan].set_index("per")
    return (f"<tr{HL if hl else ''}><td><b>{lab}</b></td>" + "".join(f"<td>${f0(x.loc[p, 'mes_prom'])}</td>" for p in ("IS", "C24", "REAL"))
            + "".join(f"<td>${f0(x.loc[p, 'mes_p10'])}</td>" for p in ("IS", "C24", "REAL")) + f"<td>≤ {f1(x.P_anio_negativo.max())}%</td><td>${f0(x.capital_p90.min())}-{f0(x.capital_p90.max())}</td></tr>")
mrows = mrow(M, "150K 6c/3c + NF05 LF06 LF0430", "5 × 150K, 6 / 3 (recomendado)", True) + mrow(M0, "150K 6c/3c", "5 × 150K, 6 / 3, sin módulos nuevos") + mrow(M, "50K 2c/2c + NF05 LF06 LF0430", "5 × 50K, 2 / 2")
G = pd.read_csv("gnq_port.csv"); Q = pd.read_csv("nqdrive_port.csv")
def g(df, s, per, k): return df[(df.set == s) & (df.per == per)][k].iat[0]
port = (f"<tr><td>Ultra (antes)</td>" + "".join(f"<td>{f2(g(G, 'Ultra', p, 'sharpe'))}</td>" for p in ("IS", "C24", "REAL")) + "".join(f"<td>{f1(g(G, 'Ultra', p, 'wr'))}%</td>" for p in ("IS", "C24", "REAL")) + "".join(f"<td>{f2(g(G, 'Ultra', p, 'tpd'))}</td>" for p in ("IS", "C24", "REAL")) + "</tr>"
        + f"<tr class='hl'><td><b>Ultra + NF05 + LF06 + LF0430</b></td>" + "".join(f"<td><b>{f2(g(Q, '+LF06+LF0430', p, 'sharpe'))}</b></td>" for p in ("IS", "C24", "REAL")) + "".join(f"<td>{f1(g(Q, '+LF06+LF0430', p, 'wr'))}%</td>" for p in ("IS", "C24", "REAL")) + "".join(f"<td>{f2(g(Q, '+LF06+LF0430', p, 'tpd'))}</td>" for p in ("IS", "C24", "REAL")) + "</tr>")
CB = pd.read_csv("combo_sim.csv")
def crow(plan, hl=False):
    x = CB[CB.plan == plan].set_index("per")
    return (f"<tr{HL if hl else ''}><td><b>{plan}</b></td>" + "".join(f"<td>${f0(x.loc[p, 'mes_prom'])}</td>" for p in ("IS", "C24", "REAL"))
            + f"<td>${f0(x.loc['REAL', 'mes_p10'])}</td><td>≤ {f1(x.P_anio_negativo.max())}%</td><td>${f0(x.capital_p90.min())}-{f0(x.capital_p90.max())}</td></tr>")
crows = crow("5 Lucid 150K") + crow("5 Lucid + 5 Apex 150K", True) + crow("5 Lucid + 10 Apex 150K") + crow("5 Lucid + 20 Apex 150K")
YR = pd.read_csv("year150.csv")
yrows = "".join(f"<tr><td>{int(r.anio)}{' (' + f1(r.meses) + ' meses)' if r.meses < 11.5 else ''}</td><td>{r.datos}</td><td>${f0(r.mes_inicio_enero)}</td><td>${f0(r.mes_prom_todos_los_inicios)}</td><td>{'−' if r.peor_inicio < 0 else ''}${f0(abs(r.peor_inicio))}</td></tr>" for r in YR.itertuples())
BUGS = json.load(open("morning_bugs.json", encoding="utf-8"))
brows = "".join(f"<li><span class='tag {b['estado']}'>{b['estado_txt']}</span> <b>{b['titulo']}</b>: {b['detalle']}</li>" for b in BUGS)
page = f"""<title>Perfil final NQ + Oro</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,600&family=Public+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: one 940px briefing column; wide tables scroll inside their frames. */
:root {{ --bg: #f4f5f2; --panel: #ffffff; --ink: #1a221f; --muted: #5a6661; --rule: #dbe1dd; --accent: #22684f; --hl: #eaf3ee; --okbg: #e2f0e8; --ok: #22684f; --warnbg: #f7efd7; --warn: #8a6100;
  --display: "Newsreader", Georgia, serif; --body: "Public Sans", "Segoe UI", system-ui, sans-serif; --mono: "IBM Plex Mono", Consolas, monospace; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #121715; --panel: #1a2120; --ink: #e4ebe7; --muted: #9aa7a1; --rule: #2c3633; --accent: #6cc79f; --hl: #1d2c25; --okbg: #1c3226; --ok: #7fd3a6; --warnbg: #352c13; --warn: #e5bf5f; color-scheme: dark; }} }}
:root[data-theme="dark"] {{ --bg: #121715; --panel: #1a2120; --ink: #e4ebe7; --muted: #9aa7a1; --rule: #2c3633; --accent: #6cc79f; --hl: #1d2c25; --okbg: #1c3226; --ok: #7fd3a6; --warnbg: #352c13; --warn: #e5bf5f; color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--ink); font: 16px/1.6 var(--body); margin: 0; }}
.wrap {{ max-width: 940px; margin: 0 auto; padding-inline: 20px; padding-block: 36px 64px; display: grid; gap: 26px; }}
.wrap > *, section > * {{ min-width: 0; }}
h1 {{ font: 600 clamp(30px, 5vw, 44px)/1.08 var(--display); margin: 0; text-wrap: balance; }}
h2 {{ font: 600 24px/1.2 var(--display); margin: 0; text-wrap: balance; }}
p {{ margin: 0; max-width: 70ch; }} .muted {{ color: var(--muted); font-size: 14.5px; }}
.eyebrow {{ font: 500 12px/1.4 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
section {{ display: grid; gap: 14px; padding-top: 22px; border-top: 1px solid var(--rule); }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; }}
.kpi {{ background: var(--panel); border: 1px solid var(--rule); border-radius: 10px; padding: 14px 16px; display: grid; gap: 4px; align-content: start; }}
.kpi b {{ font: 600 26px/1.1 var(--display); font-variant-numeric: tabular-nums; color: var(--accent); }} .kpi span {{ font-size: 13.5px; color: var(--muted); }}
.tw {{ overflow-x: auto; border: 1px solid var(--rule); border-radius: 10px; background: var(--panel); }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; font-variant-numeric: tabular-nums; }}
th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--rule); vertical-align: top; }}
th {{ font: 500 11.5px/1.3 var(--mono); letter-spacing: .04em; text-transform: uppercase; color: var(--muted); white-space: nowrap; }}
tbody tr:last-child td {{ border-bottom: 0; }} tr.hl td {{ background: var(--hl); }}
ul {{ margin: 0; padding-left: 20px; display: grid; gap: 9px; max-width: 78ch; }}
.tag {{ font: 600 11.5px var(--body); padding: 2px 8px; border-radius: 999px; white-space: nowrap; }}
.tag.ok {{ background: var(--okbg); color: var(--ok); }} .tag.warn {{ background: var(--warnbg); color: var(--warn); }}
.cfg td:first-child {{ white-space: nowrap; font-weight: 600; }}
code {{ font: 13px var(--mono); background: var(--hl); padding: 1px 5px; border-radius: 4px; }}
</style>
<div class="wrap">
<header style="display:grid;gap:10px">
  <div class="eyebrow">NQMaster + GoldMaster · LucidFlex · actualizado 7-oct-2026</div>
  <h1>Perfil final NQ + Oro</h1>
  <p>Lucid permite como máximo 5 cuentas fondeadas por hogar. Con ese límite, la cuenta de 150K deja más dinero que la de 50K. Además se sumaron tres módulos nocturnos nuevos, robustos desde 2015, y se corrigieron los errores de tres revisiones de código.</p>
</header>
<div class="kpis">
  <div class="kpi"><b>${f0(top_mean)}</b><span>por mes por cuenta 150K, promedio de 9 pruebas (peor ${f0(top_min)})</span></div>
  <div class="kpi"><b>${f0(M[M.plan.str.startswith('150K')].mes_prom.min())}-{f0(M[M.plan.str.startswith('150K')].mes_prom.max())}</b><span>por mes con 5 cuentas de 150K (tres períodos)</span></div>
  <div class="kpi"><b>≤ {f1(M[M.plan.str.startswith('150K')].P_anio_negativo.max())}%</b><span>probabilidad de cerrar un año en pérdida</span></div>
  <div class="kpi"><b>3,31-3,71</b><span>Sharpe anual del portafolio NQ (antes 3,12-3,59)</span></div>
</div>
<section>
  <h2>La configuración: 5 cuentas LucidFlex 150K</h2>
  <div class="tw"><table class="cfg"><thead><tr><th>Fase</th><th>NQMaster (MNQ)</th><th>GoldMaster (MGC)</th></tr></thead><tbody>
  <tr><td>Evaluación</td><td>Ultra · Contracts 6 · PropMode Eval · StartBalance 150000 · PropTrailingDD 4500 · EvalTarget 9000 · ConsistencyPct 50 · EvalProfitStop 4200</td><td>Robust · Contracts 6 · StartBalance 150000 · EvalTarget 9000 · AccountProfitStop 4200</td></tr>
  <tr><td>Fondeada</td><td>Contracts 3 · PropMode Funded · StartBalance 150000 · PropTrailingDD 4500 · FundedCushionSafe 1700 · FundedCushionFull 3400 · FundedPayoutAt 6000</td><td>Robust · Contracts 3 · StartBalance 150000 · EvalTarget 0 · AccountProfitStop 0</td></tr>
  </tbody></table></div>
  <p class="muted">NF05, LF06 y LF0430 ya vienen activados en Ultra. Cargar al menos 120 días en los gráficos de 1 minuto. Con 6 contratos, el peor día llega a 66 micros, debajo del límite de 100 de la evaluación. Con 3 contratos llega a 33, debajo de los 40 con que arranca la fondeada. Paso a paso: <code>OPERAR_5x150K.md</code>.</p>
  <div class="tw"><table><thead><tr><th>Perfil (150K, 6 / 3)</th><th>Win rate real</th><th>PF real</th><th>$ / mes por cuenta</th><th>Peor prueba</th><th>Fondeadas quemadas por año</th></tr></thead><tbody>
  <tr class="hl"><td><b>Ultra + noche + oro Robust (recomendado)</b></td><td>63,6%</td><td>1,43</td><td><b>$2.168</b></td><td>$1.981</td><td>2,8</td></tr>
  <tr><td><b>Win rate alto:</b> WR70Plus con NightOnWr70 + oro WinRate</td><td><b>69,5%</b></td><td><b>1,50</b></td><td>$1.903</td><td>$1.739</td><td><b>1,3</b></td></tr>
  </tbody></table></div>
</section>
<section>
  <h2>Por qué 150K</h2>
  <p>Reglas LucidFlex (octubre 2026):</p>
  <ul>
    <li><b>Objetivo y pérdida máxima:</b> 50K $3.000 / $2.000; 100K $6.000 / $3.000; 150K $9.000 / $4.500.</li>
    <li><b>Tope por cobro:</b> 50K $2.000; 100K $2.500; 150K $3.000. Cada cobro es el 50% de la ganancia, al 90%, con 5 cobros por cuenta.</li>
    <li><b>Límite de cuentas:</b> 5 fondeadas, 10 en total y $750K combinados.</li>
  </ul>
  <p>Con tamaño proporcional al límite de pérdida, esto deja cada cuenta:</p>
  <div class="tw"><table><thead><tr><th>Cuenta</th><th>Contratos eval / fondeada</th><th>Módulos</th><th>$ / mes promedio</th><th>Peor de 9 pruebas</th></tr></thead><tbody>{srows}</tbody></table></div>
  <p class="muted">Con 150K y 6 contratos, la evaluación pasa el 40% de las veces, en unos 9 días hábiles, con unas 13 evaluaciones por año y por cuenta (~$285 cada una, ya descontadas). Si vas a tener menos de 5 cuentas y el capital es la restricción, la 50K rinde más por dólar invertido en evaluaciones.</p>
</section>
<section>
  <h2>Con 5 cuentas</h2>
  <p>Las cuentas operan los mismos trades y las evaluaciones arrancan con 5 días de diferencia. Son 1.500 años simulados por período.</p>
  <div class="tw"><table><thead><tr><th>Plan</th><th>$/mes 2020-23</th><th>$/mes 2024-26 CFD</th><th>$/mes 2024-26 real</th><th>Año malo 2020-23</th><th>Año malo 24-26 CFD</th><th>Año malo real</th><th>P(año en pérdida)</th><th>Capital inicial (90%)</th></tr></thead><tbody>{mrows}</tbody></table></div>
  <p class="muted">"Año malo" es el 10% de años más flojos, en $ por mes. El capital inicial cubre las evaluaciones antes de los primeros cobros.</p>
  <p>Año por año, una cuenta 150K que arranca en enero:</p>
  <div class="tw"><table><thead><tr><th>Año</th><th>Datos</th><th>$/mes arrancando en enero</th><th>Promedio de todos los arranques del año</th><th>Peor arranque</th></tr></thead><tbody>{yrows}</tbody></table></div>
  <p class="muted">Todos los años terminan positivos arrancando en enero. Pero hay rachas flojas: una cuenta que empezó a mitad de 2023 pudo perder ~$300 por mes durante varios meses. Por eso conviene escalonar las cuentas.</p>
</section>
<section>
  <h2>Escalar más allá de 5 cuentas: sumar Apex</h2>
  <p>Apex permite hasta 20 cuentas PA. Cada Apex 150K, con 5 contratos en evaluación y 2 en la PA, deja ~$1.953 por mes (peor prueba $1.719). Con todas las cuentas operando los mismos trades:</p>
  <div class="tw"><table><thead><tr><th>Plan</th><th>$/mes 2020-23</th><th>$/mes 24-26 CFD</th><th>$/mes real</th><th>Año malo real</th><th>P(año en pérdida)</th><th>Capital inicial (90%)</th></tr></thead><tbody>{crows}</tbody></table></div>
  <p class="muted">Antes de escalar: todas las cuentas mandan las mismas órdenes al mismo tiempo. Con el volumen real de MNQ y NQ, las órdenes de madrugada representan el 1-2% del volumen del minuto con 5 cuentas, el 2-4% con 10 y el 4-10% con 25 (hasta 20% en días tranquilos). Hasta unas 10 cuentas el impacto es chico. Las reglas de Apex usadas (costo de evaluación $150, mínimo diario $250 para calificar) hay que confirmarlas, y también que ambas firmas permitan trading automático y copiar operaciones. Crecer de a poco y medir el deslizamiento real.</p>
</section>
<section>
  <h2>Tres módulos nuevos: revertir la madrugada</h2>
  <p>Apliqué al Nasdaq las familias que había encontrado para el oro, con 16 horas ancla y unas 16.000 configuraciones. Solo entró lo que se sostuvo en 2015-19, que nunca se usó para elegir, aguantó +4 ticks de deslizamiento y subió el dinero por cuenta.</p>
  <div class="tw"><table><thead><tr><th>Módulo</th><th>Regla</th><th>PF 2020-23 / 24-26 / real</th><th>2015-19</th><th>+4 ticks</th></tr></thead><tbody>
  <tr><td><b>NF05</b></td><td>05:00: si se movió ≥ 0,35 ATR desde las 20:00, en contra. Stop 0,2 ATR, objetivo 2R.</td><td>1,65 / 1,32 / 1,33</td><td>1,61</td><td>1,29</td></tr>
  <tr><td><b>LF06</b></td><td>06:00: si se movió ≥ 0,2 ATR desde las 04:00, en contra. Stop 0,2 ATR, objetivo 0,5R. Win rate ~74%.</td><td>1,49 / 1,40 / 1,45</td><td>1,20</td><td>1,32</td></tr>
  <tr><td><b>LF0430</b></td><td>04:30: si se movió ≥ 0,1 ATR desde las 04:00, en contra y a favor de la tendencia. Stop 0,35 ATR, objetivo 0,5R.</td><td>1,52 / 1,46 / 1,43</td><td>1,10</td><td>1,36</td></tr>
  </tbody></table></div>
  <div class="tw"><table><thead><tr><th>Portafolio NQ</th><th>Sharpe 2020-23</th><th>Sharpe 24-26</th><th>Sharpe real</th><th>WR 2020-23</th><th>WR 24-26</th><th>WR real</th><th>Trades/día 20-23</th><th>24-26</th><th>real</th></tr></thead><tbody>{port}</tbody></table></div>
  <p class="muted">En la cuenta 150K, los tres módulos suben el dinero en las 9 de 9 pruebas: de ${f0(SB[SB.cand == '150K 6 / 3'].mean9.iat[0])} a ${f0(top_mean)} por mes por cuenta. Las rupturas de rango nocturnas no funcionan en el Nasdaq: ninguna de 1.536 configuraciones pasó el filtro.</p>
</section>
<section>
  <h2>Errores encontrados y corregidos</h2>
  <ul>{brows}</ul>
</section>
<section>
  <h2>Validar NinjaTrader contra la investigación</h2>
  <ul>
    <li>Correr NQMaster Ultra en MNQ 1 minuto, del 01/02/2024 a hoy, con Contracts 1, PropMode Off y comisión $1,90. Exportar la pestaña Trades a CSV.</li>
    <li>En <code>research/mine</code>, correr <code>python nt_compare.py "archivo.csv" --set ultra</code>. Para GoldMaster, usar <code>--set gold_robust</code>.</li>
    <li>El informe compara módulo por módulo los trades que coinciden en día, dirección y minuto, el win rate, el PF y el $ por contrato. También lista los trades sin pareja.</li>
    <li>Con la exportación vieja de septiembre, los trades que coinciden dan $34.315 en la investigación y $33.452 en NinjaTrader (−2,5%).</li>
  </ul>
</section>
<section>
  <h2>Probado y descartado</h2>
  <ul>
    <li><b>Filtrar un lado (solo largos o solo cortos) por módulo:</b> elegido con 2020-23, se equivoca en 3 de 5 casos.</li>
    <li><b>Más módulos de oro (LATE1430, DRIVE11, ASIA05):</b> ±$10 por mes.</li>
    <li><b>3 contratos en la fondeada con colchón grande:</b> +$5 por mes.</li>
    <li><b>Petróleo:</b> 1 de 38.000 configuraciones sobrevive.</li>
    <li><b>Pesos por módulo con máximo Sharpe:</b> no se sostienen fuera de muestra.</li>
    <li><b>480 reglas de tamaño en la evaluación:</b> +1,9 puntos en la probabilidad de pasar en ≤ 22 días.</li>
  </ul>
</section>
<section>
  <h2>Próximos pasos</h2>
  <ul>
    <li>Compilar en NinjaTrader (F5) y correr el validador con NQMaster Ultra y GoldMaster Robust en 2024-26.</li>
    <li>Dos semanas en Sim con la configuración 150K. Después, empezar las evaluaciones escalonadas con 5 días de diferencia.</li>
    <li>Dejar el grabador de order flow en MNQ y MGC para juntar datos.</li>
  </ul>
</section>
</div>
"""
open(OUT, "w", encoding="utf-8").write(page); print("ok", len(page))
