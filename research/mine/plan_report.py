"""Builds the 'Plan de cuentas NQ + Oro' page from acct_mc_all.csv and acct_multi.csv (numbers computed, none typed)."""
import sys, json, pandas as pd
M = pd.read_csv("acct_mc_all.csv"); U = pd.read_csv("acct_multi.csv"); OUT = sys.argv[1]
PROTS = ["HOY", "APROBACION", "EQUILIBRIO", "EQ2", "INGRESO"]
LAB = {"HOY": "Hoy", "APROBACION": "Aprobación", "EQUILIBRIO": "Equilibrio", "EQ2": "EQ2", "INGRESO": "Ingreso"}
TESTS = {"historia": "Historia", "costo +1 tick/lado": "Costo +1 tick", "Monte Carlo 2000 años": "Monte Carlo"}
M["test"] = M["test"].str.replace("a�os", "años")
PL = {"IS": "2020-23 (CFD)", "C24": "2024-26 (CFD)", "REAL": "2024-26 (MNQ + MGC reales)"}
f0 = lambda v: f"{v:,.0f}".replace(",", ".")
f2 = lambda v: f"{v:.2f}".replace(".", ",")
def g(p, per, t, k): return M[(M.prot == p) & (M.per == per) & (M.test == t)][k].iat[0]
data = {per: {p: [int(g(p, per, t, "mo")) for t in TESTS] for p in PROTS} for per in PL}
bust = {per: {p: [float(g(p, per, t, "fbust")) for t in TESTS] for p in PROTS} for per in PL}
multi = {per: {p: [int(U[(U.per == per) & (U.prot == p) & (U.cuentas == n)].mes_prom.iat[0]) for n in (1, 3, 5)] for p in ("HOY", "EQUILIBRIO")} for per in PL}
multi10 = {per: {p: [int(U[(U.per == per) & (U.prot == p) & (U.cuentas == n)].mes_p10.iat[0]) for n in (1, 3, 5)] for p in ("HOY", "EQUILIBRIO")} for per in PL}
rows = ""
for per in PL:
    for t in TESTS:
        cells = "".join(f"<td>${f0(g(p, per, t, 'mo'))}<small>{f2(g(p, per, t, 'fbust'))}</small></td>" for p in PROTS)
        rows += f"<tr><td>{PL[per] if t == 'historia' else ''}</td><td>{TESTS[t]}</td>{cells}</tr>"
eq_r = g("EQUILIBRIO", "REAL", "historia", "mo"); hoy_r = g("HOY", "REAL", "historia", "mo")
page = f"""<title>Plan de cuentas NQ + Oro</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: single 900px column, prop-desk briefing; charts and tables scroll inside their frames. */
:root {{
  --bg: #f5f6f3; --panel: #ffffff; --ink: #1b2420; --muted: #5c6862; --rule: #dce2de;
  --hoy: #8a918d; --apr: #6b5bd2; --eq: #1f7a5c; --eq2: #2f6fb0; --ing: #c26a2b; --warn: #9a6a00; --warnbg: #f7efd8;
  --display: "Fraunces", Georgia, serif; --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif; --mono: "JetBrains Mono", Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #131816; --panel: #1b2220; --ink: #e5ece8; --muted: #9ba9a3; --rule: #2d3734;
  --hoy: #9aa19d; --apr: #9d91ee; --eq: #5cc39c; --eq2: #6fa8e0; --ing: #e59a62; --warn: #e6c062; --warnbg: #352c14; color-scheme: dark; }} }}
:root[data-theme="dark"] {{ --bg: #131816; --panel: #1b2220; --ink: #e5ece8; --muted: #9ba9a3; --rule: #2d3734;
  --hoy: #9aa19d; --apr: #9d91ee; --eq: #5cc39c; --eq2: #6fa8e0; --ing: #e59a62; --warn: #e6c062; --warnbg: #352c14; color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--ink); font: 16px/1.6 var(--body); margin: 0; }}
.wrap {{ max-width: 920px; margin: 0 auto; padding-inline: 20px; padding-block: 36px 64px; display: grid; gap: 28px; }}
h1 {{ font: 600 clamp(30px, 5vw, 44px)/1.08 var(--display); margin: 0; text-wrap: balance; }}
h2 {{ font: 600 23px/1.2 var(--display); margin: 0; text-wrap: balance; }}
p {{ margin: 0; max-width: 68ch; }} .muted {{ color: var(--muted); }}
.eyebrow {{ font: 500 12px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
section {{ display: grid; gap: 14px; padding-top: 22px; border-top: 1px solid var(--rule); }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }}
.kpi {{ background: var(--panel); border: 1px solid var(--rule); border-radius: 10px; padding: 14px 16px; display: grid; gap: 4px; min-width: 0; }}
.kpi b {{ font: 600 26px/1.1 var(--display); font-variant-numeric: tabular-nums; }} .kpi span {{ font-size: 13.5px; color: var(--muted); }}
.kpi s {{ color: var(--muted); font-size: 14px; }}
.frame {{ background: var(--panel); border: 1px solid var(--rule); border-radius: 10px; padding: 14px; }}
.chart {{ position: relative; height: 300px; }}
.tw {{ overflow-x: auto; border: 1px solid var(--rule); border-radius: 10px; background: var(--panel); }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; font-variant-numeric: tabular-nums; }}
th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--rule); vertical-align: top; }}
th {{ font: 500 11.5px/1.3 var(--mono); letter-spacing: .04em; text-transform: uppercase; color: var(--muted); white-space: nowrap; }}
tbody tr:last-child td {{ border-bottom: 0; }} td small {{ display: block; color: var(--muted); font-size: 12px; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 14px; font-size: 13px; color: var(--muted); }}
.legend i {{ display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }}
.note {{ background: var(--warnbg); color: var(--ink); border-radius: 10px; padding: 12px 16px; font-size: 15px; }}
.tabs {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.tabs button {{ font: 600 13px var(--body); padding: 6px 12px; border-radius: 999px; border: 1px solid var(--rule); background: var(--panel); color: var(--ink); cursor: pointer; }}
.tabs button[aria-pressed="true"] {{ background: var(--ink); color: var(--bg); border-color: var(--ink); }}
.tabs button:focus-visible {{ outline: 2px solid var(--eq2); outline-offset: 2px; }}
ul {{ margin: 0; padding-left: 20px; display: grid; gap: 6px; max-width: 70ch; }}
</style>
<div class="wrap">
<header style="display:grid;gap:10px">
  <div class="eyebrow">NQMaster + GoldMaster · Lucid Flex 50K · 1 contrato por módulo · 5-oct-2026</div>
  <h1>Plan de cuentas NQ + Oro</h1>
  <p>Ciclo completo de 12 meses por cuenta: evaluación, fondeada, cobros y costo de cada evaluación. Probado en tres bases de datos, con costos más altos y con 2.000 años simulados.</p>
</header>
<div class="kpis">
  <div class="kpi"><b>${f0(eq_r)}</b><span>por mes por cuenta con EQUILIBRIO (MNQ + MGC reales) <s>hoy ${f0(hoy_r)}</s></span></div>
  <div class="kpi"><b>{f2(g('EQUILIBRIO', 'REAL', 'historia', 'fbust'))}</b><span>fondeadas quemadas por año <s>hoy {f2(g('HOY', 'REAL', 'historia', 'fbust'))}</s></span></div>
  <div class="kpi"><b>20 días</b><span>mediana para aprobar <s>hoy 22</s></span></div>
  <div class="kpi"><b>9 / 9</b><span>pruebas donde EQUILIBRIO gana más que hoy</span></div>
</div>

<section>
  <h2>Ingreso por cuenta, protocolo por protocolo</h2>
  <div class="tabs" role="group" aria-label="Período">
    <button type="button" id="t-REAL" aria-pressed="true">2024-26 real</button><button type="button" id="t-C24" aria-pressed="false">2024-26 CFD</button><button type="button" id="t-IS" aria-pressed="false">2020-23 CFD</button>
  </div>
  <div class="legend">{''.join(f'<span><i style="background:var(--{c})"></i>{LAB[p]}</span>' for p, c in zip(PROTS, ('hoy', 'apr', 'eq', 'eq2', 'ing')))}</div>
  <div class="frame"><div class="chart"><canvas id="c1" role="img" aria-label="Ingreso mensual por cuenta según protocolo y prueba">Ingreso mensual por cuenta</canvas></div></div>
  <p class="muted">Cada grupo es una prueba: historia real, costos +1 tick por lado y Monte Carlo de 2.000 años.</p>
</section>

<section>
  <h2>Todas las pruebas</h2>
  <p>$ por mes por cuenta, y debajo, fondeadas quemadas por año.</p>
  <div class="tw"><table><thead><tr><th>Datos</th><th>Prueba</th>{''.join(f'<th>{LAB[p]}</th>' for p in PROTS)}</tr></thead><tbody>{rows}</tbody></table></div>
  <ul>
    <li><b>Hoy:</b> evaluación y fondeada con Ultra completo, cobro a $5.000.</li>
    <li><b>Aprobación:</b> SAFE con colchón &lt; $900 + stop diario $700 + empezar solo con ATR normal; fondeada SAFE / sin ×2, cobro a $6.000. Es el que más aprueba (95 / 82 / 89%), pero gana mucho menos.</li>
    <li><b>Equilibrio (recomendado):</b> evaluación con Ultra + oro Robust; fondeada SAFE con colchón &lt; $750, completa por encima, cobro a $5.000.</li>
    <li><b>EQ2:</b> como Equilibrio, pero con un nivel sin ×2 entre $750 y $1.500 y cobro a $4.000.</li>
    <li><b>Ingreso:</b> fondeada con oro Robust también y cobro a $4.000. Es el que más gana, pero quema tantas fondeadas como hoy.</li>
  </ul>
</section>

<section>
  <h2>Varias cuentas a la vez</h2>
  <p>Todas operan la misma estrategia, así que los años malos llegan juntos. Ingreso total por mes (Monte Carlo); la línea es el 10% de los peores años.</p>
  <div class="frame"><div class="chart"><canvas id="c2" role="img" aria-label="Ingreso mensual total con 1, 3 y 5 cuentas">Ingreso con varias cuentas</canvas></div></div>
</section>

<section>
  <h2>Configuración</h2>
  <div class="tw"><table><thead><tr><th>Fase</th><th>NQMaster (MNQ)</th><th>GoldMaster (MGC)</th></tr></thead><tbody>
  <tr><td><b>Evaluación</b></td><td>Profile Ultra · Contracts 1 · PropMode <b>Eval</b> · EvalTarget 3000 · ConsistencyPct 50</td><td>Profile <b>Robust</b> · Contracts 1 · EvalTarget 3000 · StartBalance 50000</td></tr>
  <tr><td><b>Fondeada</b></td><td>PropMode <b>Funded</b> · FundedCushionSafe 750 · cobro cuando el panel avise ($5.000)</td><td>Profile <b>WinRate</b> · EvalTarget 0</td></tr>
  <tr><td>EQ2 (opcional)</td><td>FundedCushionFull 1500 · FundedPayoutAt 4000</td><td>igual</td></tr>
  </tbody></table></div>
</section>

<section>
  <h2>Qué se puede y qué no</h2>
  <ul>
    <li>Con 1 contrato no se puede aprobar en más porcentaje y a la vez más rápido. Los dos dependen de la ganancia diaria dividida por su varianza, y la ventaja por trade ya está en su techo.</li>
    <li>El porcentaje de aprobación es una medida ruidosa: cambia ±5-8 puntos con cualquier detalle. El ingreso del ciclo completo es mucho más estable, por eso se optimizó eso.</li>
    <li>Esperar a un ATR "normal" para empezar la evaluación sube la aprobación, pero la espera cuesta más ingreso del que recupera.</li>
    <li>Elegir el mejor conjunto de módulos con 2020-23 no se sostuvo en 2024-26.</li>
    <li>Petróleo (MCL): 38.000 variantes. Las pocas que ganaban en 2020-26 pierden en 2011-19, y el costo es 2,3% del ATR por operación.</li>
  </ul>
  <div class="note">Los dos sistemas dependen del régimen actual: Nasdaq con volatilidad alta y oro con tendencia desde 2020. Por eso NQMaster y GoldMaster tienen monitores de ventaja (CUSUM) que avisan si el resultado en vivo deja de parecerse al backtest. En NQ tarda ~7 meses en confirmarlo y en oro ~14.</div>
</section>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
const DATA = {json.dumps(data)}, BUST = {json.dumps(bust)}, MULTI = {json.dumps(multi)}, M10 = {json.dumps(multi10)};
const PROTS = {json.dumps(PROTS)}, LAB = {json.dumps(LAB)}, VARS = ["hoy", "apr", "eq", "eq2", "ing"];
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const money = v => "$" + Math.round(v).toLocaleString("es-AR");
let per = "REAL", c1, c2;
function draw() {{
  const grid = css("--rule"), tick = css("--muted");
  const base = {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ grid: {{ display: false }}, ticks: {{ color: tick }} }}, y: {{ grid: {{ color: grid }}, ticks: {{ color: tick, callback: money }}, beginAtZero: true }} }} }};
  if (c1) c1.destroy(); if (c2) c2.destroy();
  c1 = new Chart(document.getElementById("c1"), {{ type: "bar", data: {{ labels: ["Historia", "Costo +1 tick", "Monte Carlo"],
    datasets: PROTS.map((p, i) => ({{ label: LAB[p], data: DATA[per][p], backgroundColor: css("--" + VARS[i]), borderRadius: 4, maxBarThickness: 26 }})) }},
    options: {{ ...base, plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: c => c.dataset.label + ": " + money(c.parsed.y) + " · " + BUST[per][PROTS[c.datasetIndex]][c.dataIndex].toFixed(2).replace(".", ",") + " fondeadas quemadas/año" }} }} }} }} }});
  c2 = new Chart(document.getElementById("c2"), {{ type: "bar", data: {{ labels: ["1 cuenta", "3 cuentas", "5 cuentas"],
    datasets: [{{ label: "Hoy", data: MULTI[per]["HOY"], backgroundColor: css("--hoy"), borderRadius: 4, maxBarThickness: 34 }},
               {{ label: "Equilibrio", data: MULTI[per]["EQUILIBRIO"], backgroundColor: css("--eq"), borderRadius: 4, maxBarThickness: 34 }},
               {{ type: "line", label: "Equilibrio, 10% peores años", data: M10[per]["EQUILIBRIO"], borderColor: css("--ink"), borderDash: [5, 4], pointRadius: 4, pointBackgroundColor: css("--ink"), borderWidth: 2 }}] }},
    options: {{ ...base, plugins: {{ legend: {{ display: true, labels: {{ color: tick, boxWidth: 12 }} }}, tooltip: {{ callbacks: {{ label: c => c.dataset.label + ": " + money(c.parsed.y) }} }} }} }} }});
}}
["REAL", "C24", "IS"].forEach(p => document.getElementById("t-" + p).addEventListener("click", () => {{
  per = p; ["REAL", "C24", "IS"].forEach(q => document.getElementById("t-" + q).setAttribute("aria-pressed", q === p ? "true" : "false")); draw(); }}));
draw();
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
new MutationObserver(draw).observe(document.documentElement, {{ attributes: true, attributeFilter: ["data-theme"] }});
</script>
"""
open(OUT, "w", encoding="utf-8").write(page); print("written", len(page))
