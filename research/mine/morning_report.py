"""Morning report 'Perfil final NQ + Oro' from final_verify2.csv, final_verify.csv, eval_pol50.csv, final_by_year.csv, perfiles_1c.csv
and morning_bugs.json. Usage: python morning_report.py <out.html>"""
import sys, json, pandas as pd
OUT = sys.argv[1]
V2 = pd.read_csv("final_verify2.csv"); V1 = pd.read_csv("final_verify.csv"); EP = pd.read_csv("eval_pol50.csv")
Y = pd.read_csv("final_by_year.csv"); P1 = pd.read_csv("perfiles_1c.csv"); B = json.load(open("morning_bugs.json", encoding="utf-8"))
f0 = lambda v: f"{v:,.0f}".replace(",", ".")
f1 = lambda v: f"{v:.1f}".replace(".", ",")
f2 = lambda v: f"{v:.2f}".replace(".", ",")
HL = ' class="hl"'
TESTS = ["historia", "costo +1 tick", "Monte Carlo"]; PER = [("C24", "2024-26 CFD"), ("IS", "2020-23 CFD"), ("REAL", "2024-26 real")]
ROB, WIN = "gating + oro Robust", "gating + oro WinRate (EQ2)"
EASY = "1 -> 2 desde el dia 8 (1 si colchon < 1000)"
CAND = [("Perfil final", lambda p, t: V2[(V2.fund == ROB) & (V2.evalp == "fijo 2") & (V2.per == p) & (V2.test == t)].mo.iat[0]),
        ("Modo pasar fácil", lambda p, t: V2[(V2.fund == ROB) & (V2.evalp == EASY) & (V2.per == p) & (V2.test == t)].mo.iat[0]),
        ("Perfil de ayer (oro WinRate en fondeada)", lambda p, t: V2[(V2.fund == WIN) & (V2.evalp == "fijo 2") & (V2.per == p) & (V2.test == t)].mo.iat[0]),
        ("Ultra anterior, 2 contratos", lambda p, t: V1[(V1.cand == "Ultra anterior 2c (referencia)") & (V1.per == p) & (V1.test == t)].mo.iat[0]),
        ("Todo con 1 contrato", lambda p, t: V1[(V1.cand.str.startswith("1 contrato")) & (V1.per == p) & (V1.test == t)].mo.iat[0])]
vrows = ""; MEAN = {}
for lab, g in CAND:
    vals = [g(p, t) for p, _ in PER for t in TESTS]; MEAN[lab] = (sum(vals) / len(vals), min(vals))
    vrows += f"<tr{HL if lab == 'Perfil final' else ''}><td><b>{lab}</b></td>" + "".join(f"<td>${f0(v)}</td>" for v in vals) + f"<td><b>${f0(MEAN[lab][0])}</b></td><td>${f0(MEAN[lab][1])}</td></tr>"
def ep(k0, kdd, c1, dsw, kl, goal):
    q = EP[(EP.k0 == k0) & (EP.kdd == kdd) & (EP.c1 == c1) & (EP.dsw == dsw) & (EP.kl == kl) & (EP.goal == goal)]; return q[["p_pass", "p15", "p22", "med", "bust"]].mean()
SPD = [("2 contratos fijos (perfil final)", ep(2, 1, 0.0, 999, 2, 1500.0), MEAN["Perfil final"][0]),
       ("Modo pasar fácil: 1 contrato, 2 desde el día 9", ep(1, 1, 1000.0, 8, 2, 2100.0), MEAN["Modo pasar fácil"][0]),
       ("1 contrato fijo", ep(1, 1, 0.0, 999, 1, 1500.0), V2[(V2.fund == ROB) & (V2.evalp == "fijo 1")].mo.mean())]
srows = "".join(f"<tr{HL if i == 0 else ''}><td><b>{n}</b></td><td>{f1(r.p_pass)}%</td><td>{f1(r.p15)}%</td><td>{f1(r.p22)}%</td><td>{f0(r.med)} días</td><td>{f1(r.bust)}%</td><td>${f0(m)}</td></tr>" for i, (n, r, m) in enumerate(SPD))
yrows = "".join(f"<tr><td>{r.src}</td><td>{r.year}</td><td>{f0(r.trades)}</td><td>{f1(r.wr)}%</td><td>{f2(r.pf)}</td><td>${f0(r.net)}</td><td>{r.months_pos}%</td></tr>" for r in Y.itertuples())
prow = ""
for nm in ["Ultra ampliado + Oro Robust", "Ultra ampliado + Oro WinRate", "NQ Ultra ampliado", "WR70Plus + Oro WinRate", "NQ WR70Plus", "NQ Core", "Oro WinRate", "Oro Robust"]:
    r = P1[(P1.perfil == nm) & (P1.per == "REAL")].iloc[0]; ri = P1[(P1.perfil == nm) & (P1.per == "IS")].iloc[0]
    prow += f"<tr><td>{nm}</td><td>{f1(r.wr)}%</td><td>{f2(r.pf)}</td><td>{f2(r.tpd)}</td><td>${f0(r.mo)}</td><td>${f0(ri.mo)}</td></tr>"
brows = "".join(f"<li><span class='tag {b['estado']}'>{b['estado_txt']}</span> <b>{b['titulo']}</b>: {b['detalle']}</li>" for b in B)
ea = SPD[0][1]
page = f"""<title>Perfil final NQ + Oro</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,600&family=Public+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: one 920px briefing column; wide tables scroll inside their frames. */
:root {{ --bg: #f4f5f2; --panel: #ffffff; --ink: #1a221f; --muted: #5a6661; --rule: #dbe1dd; --accent: #22684f; --hl: #eaf3ee; --okbg: #e2f0e8; --ok: #22684f; --warnbg: #f7efd7; --warn: #8a6100;
  --display: "Newsreader", Georgia, serif; --body: "Public Sans", "Segoe UI", system-ui, sans-serif; --mono: "IBM Plex Mono", Consolas, monospace; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #121715; --panel: #1a2120; --ink: #e4ebe7; --muted: #9aa7a1; --rule: #2c3633; --accent: #6cc79f; --hl: #1d2c25; --okbg: #1c3226; --ok: #7fd3a6; --warnbg: #352c13; --warn: #e5bf5f; color-scheme: dark; }} }}
:root[data-theme="dark"] {{ --bg: #121715; --panel: #1a2120; --ink: #e4ebe7; --muted: #9aa7a1; --rule: #2c3633; --accent: #6cc79f; --hl: #1d2c25; --okbg: #1c3226; --ok: #7fd3a6; --warnbg: #352c13; --warn: #e5bf5f; color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--ink); font: 16px/1.6 var(--body); margin: 0; }}
.wrap {{ max-width: 920px; margin: 0 auto; padding-inline: 20px; padding-block: 36px 64px; display: grid; gap: 26px; }}
.wrap > * {{ min-width: 0; }}
h1 {{ font: 600 clamp(30px, 5vw, 44px)/1.08 var(--display); margin: 0; text-wrap: balance; }}
h2 {{ font: 600 24px/1.2 var(--display); margin: 0; text-wrap: balance; }}
p {{ margin: 0; max-width: 68ch; }} .muted {{ color: var(--muted); font-size: 14.5px; }}
.eyebrow {{ font: 500 12px/1.4 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
section {{ display: grid; gap: 14px; padding-top: 22px; border-top: 1px solid var(--rule); }}
section > * {{ min-width: 0; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; }}
.kpi {{ background: var(--panel); border: 1px solid var(--rule); border-radius: 10px; padding: 14px 16px; display: grid; gap: 4px; align-content: start; }}
.kpi b {{ font: 600 26px/1.1 var(--display); font-variant-numeric: tabular-nums; color: var(--accent); }} .kpi span {{ font-size: 13.5px; color: var(--muted); }}
.tw {{ overflow-x: auto; border: 1px solid var(--rule); border-radius: 10px; background: var(--panel); }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; font-variant-numeric: tabular-nums; }}
th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--rule); vertical-align: top; }}
th {{ font: 500 11.5px/1.3 var(--mono); letter-spacing: .04em; text-transform: uppercase; color: var(--muted); white-space: nowrap; }}
tbody tr:last-child td {{ border-bottom: 0; }} tr.hl td {{ background: var(--hl); }}
ul {{ margin: 0; padding-left: 20px; display: grid; gap: 9px; max-width: 76ch; }}
.tag {{ font: 600 11.5px var(--body); padding: 2px 8px; border-radius: 999px; white-space: nowrap; }}
.tag.ok {{ background: var(--okbg); color: var(--ok); }} .tag.warn {{ background: var(--warnbg); color: var(--warn); }}
.cfg td:first-child {{ white-space: nowrap; font-weight: 600; }}
.note {{ background: var(--panel); border: 1px solid var(--rule); border-radius: 10px; padding: 14px 16px; display: grid; gap: 8px; }}
</style>
<div class="wrap">
<header style="display:grid;gap:10px">
  <div class="eyebrow">NQMaster + GoldMaster · Lucid Flex 50K · noche del 6-oct-2026</div>
  <h1>Perfil final NQ + Oro</h1>
  <p>La mejor configuración que encontré para cuentas Lucid Flex 50K, recalculada con los datos corregidos esta noche. Se probó en tres períodos, cada uno con historia, costos más altos y Monte Carlo. Incluye los arreglos de código de las dos estrategias.</p>
</header>
<div class="kpis">
  <div class="kpi"><b>${f0(MEAN['Perfil final'][0])}</b><span>por mes por cuenta, promedio de 9 pruebas (peor prueba ${f0(MEAN['Perfil final'][1])})</span></div>
  <div class="kpi"><b>{f0(ea.med)} días</b><span>mediana para pasar la evaluación; {f0(ea.p22 / ea.p_pass * 100)}% de las que pasan lo hacen en ≤ 22 días</span></div>
  <div class="kpi"><b>63-64%</b><span>win rate del perfil de evaluación, con PF 1,39-1,44 y unos 6 trades por día</span></div>
  <div class="kpi"><b>≤ 1,4%</b><span>probabilidad de cerrar un año en pérdida (Monte Carlo)</span></div>
</div>
<section>
  <h2>La configuración</h2>
  <div class="tw"><table class="cfg"><thead><tr><th>Fase</th><th>NQMaster (MNQ)</th><th>GoldMaster (MGC)</th></tr></thead><tbody>
  <tr><td>Evaluación</td><td>Ultra (ampliado) · Contracts 2 · PropMode Eval · EvalTarget 3000 · ConsistencyPct 50 · EvalProfitStop 1400</td><td>Robust · Contracts 2 · EvalTarget 3000 · StartBalance 50000 · AccountProfitStop 1400</td></tr>
  <tr><td>Fondeada</td><td>Contracts 2 · PropMode Funded · FundedCushionSafe 750 · FundedCushionFull 1500 · cobro a $4.000</td><td><b>Robust</b> (antes WinRate) · Contracts 2 · EvalTarget 0 · AccountProfitStop 0</td></tr>
  <tr><td>Modo pasar fácil (opcional)</td><td>Contracts 1 · EvalMode on · EvalStartDate = día de inicio · EvalLateDay 8 · EvalLateGoal 2100 · EvalLateContracts 2 · EvalLateMinCushion 1000</td><td>Contracts 1 · EvalMode on · mismos valores (vienen por defecto)</td></tr>
  </tbody></table></div>
  <p class="muted">Cargar al menos 120 días de datos en los gráficos de 1 minuto. GoldMaster ahora no opera hasta tener 60 días de mercado para calcular bien el ATR y la tendencia.</p>
</section>
<section>
  <h2>Qué tan rápido pasa la evaluación</h2>
  <p>Promedio de los tres períodos, empezando la evaluación cada día de la historia.</p>
  <div class="tw"><table><thead><tr><th>Tamaño en la evaluación</th><th>Pasa</th><th>Pasa en ≤ 15 días</th><th>Pasa en ≤ 22 días</th><th>Mediana</th><th>Se quema</th><th>$ / mes por cuenta</th></tr></thead><tbody>{srows}</tbody></table></div>
  <div class="note">
    <p><b>Por qué no llega al 80% en 15-22 días.</b> Con un límite de $2.000 que sigue al pico, la probabilidad de pasar depende de la ganancia diaria comparada con su variación. Más contratos hacen la evaluación más rápida pero no más segura. Para pasar el 80% de las veces en unos 18 días, el sistema necesitaría un Sharpe anual de alrededor de 5. Hoy tiene 3,3-3,9 (NQ + oro).</p>
    <p>Con 2 contratos, la evaluación se define rápido: casi todas las que pasan lo hacen en 2-3 semanas, pero solo pasa la mitad. El modo pasar fácil sube la tasa al 62% con la misma probabilidad de pasar en ≤ 22 días, a cambio de un 10% menos de dinero por mes.</p>
  </div>
</section>
<section>
  <h2>Cuánto deja por cuenta</h2>
  <p>$ por mes por cuenta Lucid 50K, con evaluaciones compradas, cuentas quemadas y cobros incluidos.</p>
  <div class="tw"><table><thead><tr><th></th>{''.join(f'<th>{pl}<br>{t}</th>' for _, pl in PER for t in TESTS)}<th>Promedio</th><th>Peor</th></tr></thead><tbody>{vrows}</tbody></table></div>
  <p class="muted">Con 2 contratos se compran unas 9-14 evaluaciones y se queman unas 3-4 fondeadas por cuenta y por año. Todo eso ya está descontado en las cifras.</p>
</section>
<section>
  <h2>Cada perfil con 1 contrato</h2>
  <p>Trading sin reglas de prop, filtro de posiciones opuestas aplicado, días de FOMC excluidos.</p>
  <div class="tw"><table><thead><tr><th>Perfil</th><th>Win rate (real)</th><th>PF (real)</th><th>Trades / día</th><th>$ / mes 2024-26 real</th><th>$ / mes 2020-23</th></tr></thead><tbody>{prow}</tbody></table></div>
  <p class="muted">WR70Plus llega al 71% de win rate y PF 1,5, pero deja un 8% menos en la cuenta de prop que Ultra ampliado.</p>
</section>
<section>
  <h2>Año por año</h2>
  <p>Ultra ampliado + oro WinRate, 1 contrato. Todos los años 2020-2026 terminan positivos.</p>
  <div class="tw"><table><thead><tr><th>Datos</th><th>Año</th><th>Trades</th><th>Win rate</th><th>PF</th><th>Ganancia</th><th>Meses +</th></tr></thead><tbody>{yrows}</tbody></table></div>
</section>
<section>
  <h2>Errores encontrados y corregidos</h2>
  <ul>{brows}</ul>
</section>
<section>
  <h2>Descartado esta noche</h2>
  <ul>
    <li><b>Petróleo (MCL):</b> de 38.000 configuraciones, solo una se sostiene en 2011-19, y con unos 25 trades por año. No suma nada útil.</li>
    <li><b>Pesos por módulo con máximo Sharpe:</b> elegidos con 2020-23, no mejoran 2024-26. La mejora aparente era ruido de las medias.</li>
    <li><b>Tamaño dinámico en la evaluación para pasar más rápido:</b> 480 reglas probadas. La mejor sube la probabilidad de pasar en ≤ 22 días de 44,8% a 46,7%; no compensa.</li>
  </ul>
</section>
<section>
  <h2>Próximos pasos</h2>
  <ul>
    <li>Compilar en NinjaTrader (F5 en el editor) y correr las dos estrategias 2 semanas en una cuenta Sim con esta configuración.</li>
    <li>Pasar los trades de Strategy Analyzer de 2024-26 para comparar contra la investigación módulo por módulo.</li>
    <li>Dejar el grabador de order flow en MNQ y MGC: es la vía que queda para subir la ventaja por operación.</li>
  </ul>
</section>
</div>
"""
open(OUT, "w", encoding="utf-8").write(page); print("ok", len(page))
