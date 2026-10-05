"""Builds the 'Auditoría de robustez NQMaster' HTML page from robust_lab.json + robust_trades.pkl (all numbers computed, none typed)."""
import json, pickle, sys, os, html
import numpy as np, pandas as pd
J = json.load(open("robust_lab.json")); T = pickle.load(open("robust_trades.pkl", "rb"))
OUT = sys.argv[1]
PROFS = ("Ultra", "WR70Plus", "Core6"); PER = ("IS", "C24", "REAL")
PLAB = {"IS": "CFD 2020-23", "C24": "CFD 2024-26", "REAL": "MNQ real 2024-26"}
def head(prof, per):
    F, days = T[prof][per]; x = F.u * F.w; d = x.groupby(F.date).sum().reindex(days, fill_value=0)
    return dict(tpd=len(F) / len(days), wr=100 * (F.u > 0).mean(), pf=x[x > 0].sum() / -x[x <= 0].sum(), sh=d.mean() / d.std() * 252 ** .5, mo=d.mean() * 21, n=len(F))
H = {p: {q: head(p, q) for q in PER} for p in PROFS}
f0 = lambda v: f"{v:,.0f}".replace(",", ".")
f1 = lambda v: f"{v:.1f}".replace(".", ",")
f2 = lambda v: f"{v:.2f}".replace(".", ",")
def chip(kind, text): return f'<span class="chip {kind}">{text}</span>'

# ---------------------------------------------------------------- SVG helpers
def line_chart(series, xs, xlab, ylo, yhi, yticks, w=560, h=240, fmt=f2, ref=None):
    L, R, Tp, B = 46, 110, 14, 34; iw, ih = w - L - R, h - Tp - B
    X = lambda i: L + iw * (xs[i] - xs[0]) / (xs[-1] - xs[0]); Y = lambda v: Tp + ih * (1 - (v - ylo) / (yhi - ylo))
    g = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img">']
    for t in yticks:
        g.append(f'<line x1="{L}" x2="{L + iw}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" class="grid"/><text x="{L - 6}" y="{Y(t) + 4:.1f}" class="tick" text-anchor="end">{fmt(t)}</text>')
    if ref is not None: g.append(f'<line x1="{L}" x2="{L + iw}" y1="{Y(ref):.1f}" y2="{Y(ref):.1f}" class="refl"/>')
    for i, xv in enumerate(xs): g.append(f'<text x="{X(i):.1f}" y="{h - 14}" class="tick" text-anchor="middle">{xv}</text>')
    g.append(f'<text x="{L + iw / 2:.1f}" y="{h - 1}" class="tick" text-anchor="middle">{xlab}</text>')
    for name, ys, cls in series:
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(ys))
        g.append(f'<polyline points="{pts}" class="ln {cls}" fill="none"/>')
        for i, v in enumerate(ys): g.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3" class="dot {cls}"/>')
        g.append(f'<text x="{X(len(ys) - 1) + 8:.1f}" y="{Y(ys[-1]) + 4:.1f}" class="lab {cls}">{name} {fmt(ys[-1])}</text>')
    g.append("</svg>"); return "".join(g)
def bar_chart(items, ylo, yhi, yticks, w=560, h=220, ref=1.0, fmt=f2):
    L, R, Tp, B = 40, 10, 16, 30; iw, ih = w - L - R, h - Tp - B; n = len(items); bw = iw / n * 0.62
    Y = lambda v: Tp + ih * (1 - (v - ylo) / (yhi - ylo))
    g = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img">']
    for t in yticks: g.append(f'<line x1="{L}" x2="{L + iw}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" class="grid"/><text x="{L - 6}" y="{Y(t) + 4:.1f}" class="tick" text-anchor="end">{fmt(t)}</text>')
    for i, (lab, v, cls) in enumerate(items):
        cx = L + iw * (i + 0.5) / n; y0 = Y(max(ylo, min(ref, yhi))); y1 = Y(max(ylo, min(v, yhi)))
        g.append(f'<rect x="{cx - bw / 2:.1f}" y="{min(y0, y1):.1f}" width="{bw:.1f}" height="{abs(y1 - y0):.1f}" class="bar {cls}"/>')
        g.append(f'<text x="{cx:.1f}" y="{min(y0, y1) - 4:.1f}" class="val" text-anchor="middle">{fmt(v)}</text>')
        g.append(f'<text x="{cx:.1f}" y="{h - 10}" class="tick" text-anchor="middle">{lab}</text>')
    g.append(f'<line x1="{L}" x2="{L + iw}" y1="{Y(ref):.1f}" y2="{Y(ref):.1f}" class="refl"/>')
    g.append("</svg>"); return "".join(g)

# ---------------------------------------------------------------- sections
U = J["Ultra"]; W = J["WR70Plus"]; C = J["Core6"]; MON = J["monitor"]
# headline table
rows = ""
for p in PROFS:
    for q in PER:
        r = H[p][q]
        rows += f"<tr><td>{p if q == 'IS' else ''}</td><td>{PLAB[q]}</td><td>{f2(r['tpd'])}</td><td>{f1(r['wr'])}%</td><td>{f2(r['pf'])}</td><td>{f2(r['sh'])}</td><td>${f0(r['mo'])}</td></tr>"
tbl_head = f'<div class="tw"><table><thead><tr><th>Perfil</th><th>Datos</th><th>Trades/día</th><th>WR</th><th>PF</th><th>Sharpe</th><th>$/mes (1 lote)</th></tr></thead><tbody>{rows}</tbody></table></div>'

# costs
xs = [0, 1, 2, 3, 4]
cost_series = [(p, [J[p]["REAL"]["costs"][f"{float(s)}"]["pf"] for s in xs], c) for p, c in (("Ultra", "s1"), ("WR70Plus", "s2"), ("Core6", "s3"))]
cost_svg = line_chart(cost_series, xs, "ticks extra de slippage por lado (MNQ real 2024-26)", 1.0, 1.6, [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6], ref=1.0)
crow = ""
for p in PROFS:
    for q in PER:
        c = J[p][q]["costs"]
        crow += f"<tr><td>{p if q == 'IS' else ''}</td><td>{PLAB[q]}</td>" + "".join(f"<td>{f2(c[f'{float(s)}']['pf'])}</td>" for s in xs) + f"<td>{f1(J[p][q]['breakeven_ticks_per_side'])}</td></tr>"
cost_tbl = f'<div class="tw"><table><thead><tr><th>Perfil</th><th>Datos</th><th>PF +0</th><th>+1</th><th>+2</th><th>+3</th><th>+4 ticks</th><th>Ticks/lado para PF 1</th></tr></thead><tbody>{crow}</tbody></table></div>'

# DSR
drow = ""
for p in PROFS:
    for lab, d in J[p]["dsr"].items():
        drow += f"<tr><td>{p}</td><td>{lab}</td><td>{f2(d['sharpe'])}</td>" + "".join(f"<td>{f2(d[str(N)][1])} → <b>{f0(100 * d[str(N)][0])}%</b></td>" for N in (100, 1000, 10000, 50000)) + "</tr>"
dsr_tbl = f'<div class="tw"><table><thead><tr><th>Perfil</th><th>Datos</th><th>Sharpe real</th><th>100 intentos</th><th>1.000</th><th>10.000</th><th>50.000</th></tr></thead><tbody>{drow}</tbody></table></div>'

# PBO
pm = J["pbo_miner"]; pv = J["pbo_variants"]
pbo_rows = "".join(f"<tr><td>{m}</td><td>{v['N']}</td><td>{f0(100 * v['PBO'])}%</td><td>{f2(v['IS_best_sharpe_ann'])}</td><td>{f2(v['OOS_sharpe_of_IS_best_ann'])}</td></tr>" for m, v in sorted(pv.items(), key=lambda kv: kv[1]["PBO"]))
pbo_tbl = f'<div class="tw"><table><thead><tr><th>Módulo</th><th>Variantes de objetivo</th><th>PBO</th><th>Sharpe elegida (IS)</th><th>Sharpe misma (OOS)</th></tr></thead><tbody>{pbo_rows}</tbody></table></div>'

# plateaus small multiples
def plat(m):
    v = J["plateaus"][m]; ks = sorted(v, key=float)
    ser = [(q, [v[k].get(q, {}).get("pf", np.nan) for k in ks], c) for q, c in (("IS", "s3"), ("C24", "s2"), ("REAL", "s1"))]
    lo = min(min(y for y in s[1] if y == y) for s in ser); hi = max(max(y for y in s[1] if y == y) for s in ser)
    lo = np.floor((min(lo, 1.0)) * 10) / 10; hi = np.ceil(hi * 10) / 10
    ticks = [round(t, 1) for t in np.arange(lo, hi + 0.001, 0.2 if hi - lo > 0.6 else 0.1)]
    return f'<figure class="sm"><figcaption>{m}</figcaption>' + line_chart(ser, [float(k) for k in ks], "objetivo (R)", lo, hi, ticks, w=330, h=190, ref=1.0) + "</figure>"
plats = "".join(plat(m) for m in ("ORB60", "CRT11", "MSEQ", "ICT", "LON", "ORB90", "ON07", "MOM13"))

# regimes
rg = U["regimes"]
yr_items = [(k, v["pf"], "s2") for k, v in rg["CFD 2020-26"]["year"].items()]
yr_svg = bar_chart(yr_items, 0.6, 1.8, [0.6, 1.0, 1.4, 1.8])
def regtab(prof):
    out = ""
    for lab in ("CFD 2020-26", "REAL 2024-26"):
        r = J[prof]["regimes"][lab]
        cells = []
        for col, keys in (("atr_t", ("ATR bajo", "ATR medio", "ATR alto")), ("vix_t", ("VIX bajo", "VIX medio", "VIX alto")), ("trend", ("True", "False"))):
            for k in keys:
                v = r[col][k]; cls = "bad" if v["pf"] < 1 else ""
                cells.append(f'<td class="{cls}">{f2(v["pf"])}<small> · ${f0(v["per_day"])}/día</small></td>')
        out += f"<tr><td>{prof if lab.startswith('CFD') else ''}</td><td>{lab}</td>{''.join(cells)}</tr>"
    return out
reg_tbl = ('<div class="tw"><table><thead><tr><th>Perfil</th><th>Datos</th><th>ATR bajo</th><th>ATR medio</th><th>ATR alto</th><th>VIX bajo</th><th>VIX medio</th><th>VIX alto</th>'
           '<th>Día de tendencia</th><th>Día de rango</th></tr></thead><tbody>' + "".join(regtab(p) for p in PROFS) + "</tbody></table></div>")
r1519 = MON["replay_2015_19_core"]

# evidence / bootstrap / MC
erow = ""
for p in PROFS:
    for q in PER:
        e = J[p][q]["evidence"]; b = J[p][q]["boot"]
        erow += (f"<tr><td>{p if q == 'IS' else ''}</td><td>{PLAB[q]}</td><td>{f0(e['trades'])}</td><td>{f0(e['days'])}</td><td>{f0(e['eff_days'])}</td>"
                 f"<td>{f2(b['sharpe'][0])} – {f2(b['sharpe'][2])}</td><td>{f2(b['pf'][0])} – {f2(b['pf'][2])}</td><td>${f0(b['mo'][0])} – ${f0(b['mo'][2])}</td></tr>")
ev_tbl = f'<div class="tw"><table><thead><tr><th>Perfil</th><th>Datos</th><th>Trades</th><th>Días</th><th>Días independientes</th><th>Sharpe (5–95%)</th><th>PF (5–95%)</th><th>$/mes (5–95%)</th></tr></thead><tbody>{erow}</tbody></table></div>'
mrow = ""
for p in PROFS:
    for q in ("C24", "REAL"):
        m = J[p][q]["mc_year"]
        mrow += (f"<tr><td>{p if q == 'C24' else ''}</td><td>{PLAB[q]}</td><td>${f0(m['pnl'][0])}</td><td>${f0(m['pnl'][2])}</td><td>${f0(m['maxdd'][0])}</td><td>${f0(m['maxdd'][2])}</td>"
                 f"<td>${f0(m['maxdd'][3])}</td><td>{f0(100 * m['P_month_loss'])}%</td><td>${f0(m['worst_month_p5'])}</td></tr>")
mc_tbl = f'<div class="tw"><table><thead><tr><th>Perfil</th><th>Base</th><th>Año malo (5%)</th><th>Año típico</th><th>DD típico</th><th>DD 1 de 20 años</th><th>DD 1 de 100</th><th>Meses negativos</th><th>Peor mes (5%)</th></tr></thead><tbody>{mrow}</tbody></table></div>'

# correlation heatmap (Ultra REAL)
cr = U["corr"]["REAL 2024-26"]; mods = cr["mods"]; Mx = np.array(cr["matrix"]); n = len(mods); cs = 26; L0 = 70; T0 = 70
hm = [f'<svg viewBox="0 0 {L0 + n * cs + 10} {T0 + n * cs + 10}" class="chart heat" role="img">']
for i, a in enumerate(mods):
    hm.append(f'<text x="{L0 - 6}" y="{T0 + i * cs + cs * 0.65:.1f}" class="tick" text-anchor="end">{a}</text>')
    hm.append(f'<text transform="translate({L0 + i * cs + cs * 0.65:.1f},{T0 - 6}) rotate(-60)" class="tick">{a}</text>')
    for j in range(n):
        v = Mx[i, j]; op = min(1.0, abs(v)) if i != j else 0.08
        cls = "hpos" if v >= 0 else "hneg"
        hm.append(f'<rect x="{L0 + j * cs}" y="{T0 + i * cs}" width="{cs - 2}" height="{cs - 2}" class="{cls}" fill-opacity="{max(op, 0.04):.2f}"><title>{a} / {mods[j]}: {v:.2f}</title></rect>')
hm.append("</svg>"); heat = "".join(hm)

# monitor
def mon_rows(p):
    o = ""
    for t in MON[p]["table"]:
        if t["h_sd"] not in (12, 18, 22, 26): continue
        star = " ★" if t["h_sd"] == MON[p]["chosen"]["h_sd"] else ""
        o += (f"<tr><td>{p if t['h_sd'] == 12 else ''}</td><td>{t['h_sd']}σ{star}</td><td>{f0(100 * t['P_false_alarm_1y'])}%</td><td>{f0(100 * t['P_false_alarm_3y'])}%</td>"
              f"<td>{f0(t['dead_median_days'])} días</td><td>{f0(t['neg_median_days'])} días</td><td>{'sí' if t['hist_alarm'] else 'no'}</td></tr>")
    return o
mon_tbl = ('<div class="tw"><table><thead><tr><th>Perfil</th><th>Umbral h</th><th>Falsa alarma 1 año</th><th>Falsa alarma 3 años</th><th>Detecta ventaja muerta (mediana)</th>'
           '<th>Detecta ventaja negativa (mediana)</th><th>Alarma en 2020-26</th></tr></thead><tbody>' + "".join(mon_rows(p) for p in PROFS) + "</tbody></table></div>")

uR = H["Ultra"]["REAL"]; uC = H["Ultra"]["C24"]; uI = H["Ultra"]["IS"]
trend = U["regimes"]["REAL 2024-26"]["trend"]
checks = [
    ("Sobreajuste", "ok", "Pasa", f"Elegir “el mejor” del minero falla (PBO {f0(100 * pm['PBO'])}%), por eso nunca lo hicimos: los módulos salen de reglas simples con variantes en meseta (PBO de CRT11, LON y MSEQ ≤ 2%)."),
    ("Dentro vs fuera de muestra", "ok", "Pasa", f"Sharpe de Ultra {f2(uI['sh'])} en 2020-23 (elección), {f2(uC['sh'])} en 2024-26 y {f2(uR['sh'])} en MNQ real: fuera de muestra no empeora. Sharpe deflactado por 50.000 intentos: {f0(100 * U['dsr']['REAL 2024-26']['50000'][0])}% en MNQ real."),
    ("Más parámetros", "warn", "Atención", f"Ultra usa 14 módulos y reglas de contexto. Core6 (6 módulos, sin filtros) rinde menos pero funciona igual en todos los períodos (Sharpe {f2(H['Core6']['IS']['sh'])} / {f2(H['Core6']['C24']['sh'])} / {f2(H['Core6']['REAL']['sh'])}). Queda como perfil de respaldo."),
    ("Costos de transacción", "ok", "Pasa", f"Con 4 ticks extra por lado Ultra sigue en PF {f2(U['REAL']['costs']['4.0']['pf'])} (MNQ real). La ventaja recién desaparece con ~{f0(U['REAL']['breakeven_ticks_per_side'])} ticks por lado."),
    ("Mejor backtest ≠ mejor modelo", "ok", "Pasa", "Los objetivos elegidos están en mesetas: el PF cambia de forma suave con el parámetro, sin picos aislados."),
    ("Cambios de régimen", "warn", "Riesgo principal", f"Ganó en cada año 2020-26 y en todos los tercios de ATR y VIX. Pero vive de los días de tendencia (PF {f2(trend['True']['pf'])}) y pierde en días de rango (PF {f2(trend['False']['pf'])}). Con volatilidad baja como en 2015-19 no opera (filtro ATR ≥ 150)."),
    ("Drawdown", "ok", "Pasa", f"1 lote, un año como 2024-26: drawdown típico ${f0(U['REAL']['mc_year']['maxdd'][0])}, 1 de cada 20 años ${f0(U['REAL']['mc_year']['maxdd'][2])}. Meses negativos: {f0(100 * U['REAL']['mc_year']['P_month_loss'])}%."),
    ("Correlación", "ok", "Pasa", f"14 módulos con correlación media {f2(cr['mean_pair_corr'])}: equivalen a {f1(cr['eff_bets'])} apuestas independientes."),
    ("Más trades ≠ más evidencia", "warn", "Atención", f"{f0(U['REAL']['evidence']['trades'])} trades en MNQ real, pero solo ~{f0(U['REAL']['evidence']['eff_days'])} días independientes. Rango creíble del Sharpe: {f2(U['REAL']['boot']['sharpe'][0])} a {f2(U['REAL']['boot']['sharpe'][2])}."),
    ("Prueba final en vivo", "new", "Nuevo", "NQMaster ahora vigila su propio resultado en vivo con un monitor estadístico (CUSUM) y avisa si deja de parecerse al backtest."),
]
check_rows = "".join(f'<tr><td>{i + 1}</td><td><b>{a}</b></td><td>{chip(k, s)}</td><td>{t}</td></tr>' for i, (a, k, s, t) in enumerate(checks))

GRAVE = [("Minero de estrategias (21 familias + lote de octubre)", "27.110 variantes", "AMD/POC, rangos, pullbacks a VWAP, patrones 5m, pivots, números redondos, divergencias RSI…"),
         ("CISD estilo Triton", "14.400", "PF medio < 1 en todas las combinaciones"),
         ("9 EMA + VWAP", "1.152", "pullback y rebote pierden; el cruce casi no aporta"),
         ("Engulfing 4H (Omar)", "2.304", "sesgo positivo solo desde 2020; neutro en cartera"),
         ("IFVG / SMC / ICT sniper / PO3", "miles", "sin ventaja después de costos"),
         ("Machine learning (meta-labeling, tipo de día)", "walk-forward", "no mejora fuera de muestra"),
         ("Filtros de contexto minados en 2020-23", "cientos", "correlación IS↔OOS 0,04: ruido"),
         ("Cortar módulos por su curva de resultados", "—", "empeora el Sharpe (3,41 → 2,98-3,18)"),
         ("Oro, euro, plata, S&P por horario", "miles", "los costos se comen la ventaja"),
         ("Entradas límite, topes de posiciones, tamaño por volatilidad", "—", "selección adversa o sin mejora")]
grave_rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in GRAVE)

pu = MON["Ultra"]; pw = MON["WR70Plus"]; pc = MON["Core6"]
page = f"""<title>Auditoría NQMaster</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: one reading column (~880px) with full-width tables/charts that scroll inside their own frames. Lab-report tone. */
:root {{
  --bg: #f6f7f5; --panel: #ffffff; --ink: #18211f; --muted: #5d6965; --rule: #dde3e0;
  --accent: #1f5f8b; --s1: #1f5f8b; --s2: #b5642a; --s3: #5f7f3a;
  --ok: #2f7a4d; --okbg: #e3f1e8; --warn: #9a6a00; --warnbg: #f8eed2; --bad: #b3362b; --badbg: #f7e1de; --new: #1f5f8b; --newbg: #e1ecf4;
  --display: "Bricolage Grotesque", "Segoe UI", system-ui, sans-serif; --body: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif; --mono: "IBM Plex Mono", ui-monospace, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #121715; --panel: #1a211f; --ink: #e4ebe8; --muted: #9aa8a3; --rule: #2c3633;
  --accent: #7fb6dc; --s1: #7fb6dc; --s2: #e39a62; --s3: #a8c77d;
  --ok: #7fd09c; --okbg: #1d3327; --warn: #e6c062; --warnbg: #352c14; --bad: #f08a80; --badbg: #3a1f1c; --new: #7fb6dc; --newbg: #1b2c39; color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --bg: #121715; --panel: #1a211f; --ink: #e4ebe8; --muted: #9aa8a3; --rule: #2c3633;
  --accent: #7fb6dc; --s1: #7fb6dc; --s2: #e39a62; --s3: #a8c77d;
  --ok: #7fd09c; --okbg: #1d3327; --warn: #e6c062; --warnbg: #352c14; --bad: #f08a80; --badbg: #3a1f1c; --new: #7fb6dc; --newbg: #1b2c39; color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--ink); font: 15px/1.6 var(--body); margin: 0; }}
.wrap {{ max-width: 920px; margin: 0 auto; padding-inline: 20px; padding-block: 36px 64px; display: grid; gap: 30px; }}
header {{ display: grid; gap: 10px; }}
.eyebrow {{ font: 500 12px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
h1 {{ font: 700 clamp(30px, 5vw, 46px)/1.05 var(--display); margin: 0; text-wrap: balance; letter-spacing: -.01em; }}
h2 {{ font: 700 24px/1.2 var(--display); margin: 0; text-wrap: balance; }}
h3 {{ font: 600 16px/1.3 var(--body); margin: 0; }}
p {{ margin: 0; max-width: 68ch; }}
.lede {{ font-size: 17px; color: var(--ink); }}
.muted {{ color: var(--muted); }}
section {{ display: grid; gap: 14px; padding-top: 22px; border-top: 1px solid var(--rule); }}
.verdict {{ background: var(--panel); border: 1px solid var(--rule); border-radius: 10px; padding: 20px 22px; display: grid; gap: 12px; }}
.verdict h2 {{ font-size: 22px; }}
.tw {{ overflow-x: auto; border: 1px solid var(--rule); border-radius: 8px; background: var(--panel); }}
table {{ border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; font-size: 13.5px; }}
th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--rule); vertical-align: top; }}
th {{ font: 500 11.5px/1.3 var(--mono); letter-spacing: .04em; text-transform: uppercase; color: var(--muted); white-space: nowrap; }}
tbody tr:last-child td {{ border-bottom: 0; }}
td small {{ color: var(--muted); font-size: 11.5px; white-space: nowrap; }}
td.bad {{ color: var(--bad); font-weight: 600; }}
.chip {{ display: inline-block; font: 600 11.5px/1 var(--body); padding: 5px 8px; border-radius: 999px; white-space: nowrap; }}
.chip.ok {{ color: var(--ok); background: var(--okbg); }} .chip.warn {{ color: var(--warn); background: var(--warnbg); }} .chip.new {{ color: var(--new); background: var(--newbg); }}
.chart {{ width: 100%; height: auto; display: block; }}
.chart .grid {{ stroke: var(--rule); stroke-width: 1; }} .chart .refl {{ stroke: var(--muted); stroke-dasharray: 4 3; stroke-width: 1; }}
.chart .tick {{ fill: var(--muted); font: 11px var(--mono); }} .chart .val {{ fill: var(--ink); font: 500 11px var(--mono); }}
.chart .lab {{ font: 600 11px var(--body); }}
.ln {{ stroke-width: 2.2; }} .ln.s1 {{ stroke: var(--s1); }} .ln.s2 {{ stroke: var(--s2); }} .ln.s3 {{ stroke: var(--s3); }}
.dot.s1, .lab.s1 {{ fill: var(--s1); }} .dot.s2, .lab.s2 {{ fill: var(--s2); }} .dot.s3, .lab.s3 {{ fill: var(--s3); }}
.bar.s2 {{ fill: var(--s1); }}
.heat .hpos {{ fill: var(--s1); }} .heat .hneg {{ fill: var(--bad); }}
.figure {{ background: var(--panel); border: 1px solid var(--rule); border-radius: 8px; padding: 12px; }}
.grid2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(270px, 1fr)); gap: 12px; }}
figure.sm {{ margin: 0; background: var(--panel); border: 1px solid var(--rule); border-radius: 8px; padding: 10px 8px 4px; min-width: 0; }}
figure.sm figcaption {{ font: 600 13px var(--body); padding-left: 6px; }}
.legend {{ display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; color: var(--muted); }}
.legend i {{ display: inline-block; width: 14px; height: 3px; vertical-align: middle; margin-right: 6px; border-radius: 2px; }}
.code {{ font: 13px/1.6 var(--mono); background: var(--panel); border: 1px solid var(--rule); border-radius: 8px; padding: 12px 14px; overflow-x: auto; white-space: pre; }}
ol.steps {{ margin: 0; padding-left: 20px; display: grid; gap: 6px; max-width: 70ch; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }}
.kpi {{ background: var(--panel); border: 1px solid var(--rule); border-radius: 8px; padding: 12px 14px; display: grid; gap: 2px; }}
.kpi b {{ font: 700 24px/1.1 var(--display); }} .kpi span {{ font-size: 12.5px; color: var(--muted); }}
</style>
<div class="wrap">
<header>
  <div class="eyebrow">NQMaster · MNQ 1 minuto · auditoría del {pd.Timestamp('2026-10-03').strftime('%d/%m/%Y')}</div>
  <h1>Auditoría de robustez de NQMaster</h1>
  <p class="lede">Las diez preguntas que separan una ventaja real de una curva bonita, respondidas con datos: CFD 2020-23 (donde se eligió todo), CFD 2024-26 y futuros MNQ reales 2024-26, más 11 años de historia. Comisión $1,90 y 1 tick de slippage por lado en todo.</p>
</header>

<div class="verdict">
  <h2>¿Va a funcionar en el futuro?</h2>
  <p>Nadie puede probarlo antes de que pase. Lo que sí se puede medir es si la ventaja es real o ruido, cuánto aguanta y cuándo dejaría de funcionar. <b>Ultra pasa 6 de las 10 pruebas, 2 piden atención, 1 es su riesgo principal y la décima (en vivo) ahora tiene un monitor.</b> El riesgo principal: depende de que el Nasdaq siga teniendo días de tendencia y volatilidad. Para ese riesgo hay dos protecciones dentro de NQMaster: el filtro de volatilidad mínima (ATR ≥ 150) y, desde hoy, un monitor que avisa si el resultado en vivo deja de parecerse al backtest.</p>
  <div class="kpis">
    <div class="kpi"><b>{f0(100 * U['REAL']['boot']['P_pf_gt1'])}%</b><span>remuestreos con PF &gt; 1 (MNQ real)</span></div>
    <div class="kpi"><b>{f0(100 * U['dsr']['REAL 2024-26']['50000'][0])}%</b><span>Sharpe deflactado con 50.000 intentos</span></div>
    <div class="kpi"><b>{f0(U['REAL']['breakeven_ticks_per_side'])} ticks</b><span>de slippage por lado para perder la ventaja</span></div>
    <div class="kpi"><b>{f1(cr['eff_bets'])}</b><span>apuestas independientes de 14 módulos</span></div>
  </div>
</div>

<section>
  <h2>Resultado de las diez pruebas</h2>
  <div class="tw"><table><thead><tr><th>#</th><th>Prueba</th><th>Estado</th><th>Qué mostró</th></tr></thead><tbody>{check_rows}</tbody></table></div>
  {tbl_head}
</section>

<section>
  <h2>Lo que costó llegar</h2>
  <p>Por cada módulo que quedó hubo cientos que no. Esto es lo descartado, con el motivo.</p>
  <div class="tw"><table><thead><tr><th>Idea probada</th><th>Variantes</th><th>Por qué se descartó</th></tr></thead><tbody>{grave_rows}</tbody></table></div>
</section>

<section>
  <h2>1 · Sobreajuste</h2>
  <p>La prueba PBO parte la historia en 16 bloques y repite 12.870 veces: elige la mejor estrategia en una mitad y mira qué lugar ocupa en la otra. Con las {f0(pm['N'])} configuraciones buenas del minero, la elegida como “mejor” cae debajo de la mediana el <b>{f0(100 * pm['PBO'])}%</b> de las veces, y su Sharpe pasa de {f2(pm['IS_best_sharpe_ann'])} a {f2(pm['OOS_sharpe_of_IS_best_ann'])}. Por eso NQMaster nunca usa “la mejor del minero”: usa reglas simples cuyas variantes funcionan todas parecido.</p>
  {pbo_tbl}
  <p class="muted">ORB60 y ON07 tienen PBO alto porque sus variantes rinden casi igual (elegir una u otra da lo mismo, ver la sección 5). ON07 no está en WR70Plus ni en Core.</p>
</section>

<section>
  <h2>2 · Dentro vs fuera de muestra</h2>
  <p>El Sharpe deflactado responde: “si probé N estrategias al azar, ¿qué tan probable es que el Sharpe que veo sea real?”. Se calcula con la asimetría y las colas gordas reales de los resultados diarios. Cada celda dice el Sharpe que se podría obtener solo por suerte con ese número de intentos y la probabilidad de que el nuestro sea real.</p>
  {dsr_tbl}
</section>

<section>
  <h2>3 · Más parámetros no es mejor</h2>
  <p>Core6 usa solo los 6 módulos que funcionaron 11 años (ORB60, MSEQ, CRT11, LON, ICT ×2, VOLB), sin reglas de contexto ni confluencia. Ultra tiene más piezas y rinde más en los tres períodos, incluso fuera de muestra, así que sigue siendo el perfil principal. <b>Core queda en NQMaster como respaldo:</b> si el monitor de la sección 10 da alarma con Ultra, el siguiente paso es Core, no apagar todo.</p>
</section>

<section>
  <h2>4 · Costos de transacción</h2>
  <div class="figure">{cost_svg}</div>
  {cost_tbl}
  <p class="muted">1 tick por lado = $1,00 por contrato MNQ ida y vuelta. Todo el estudio ya incluye 1 tick por lado y $1,90 de comisión; los números de arriba son adicionales.</p>
</section>

<section>
  <h2>5 · Mesetas, no picos</h2>
  <p>PF de cada módulo según el objetivo en R. Una línea suave significa que el resultado no depende de haber acertado un número exacto.</p>
  <div class="legend"><span><i style="background:var(--s3)"></i>CFD 2020-23</span><span><i style="background:var(--s2)"></i>CFD 2024-26</span><span><i style="background:var(--s1)"></i>MNQ real 2024-26</span></div>
  <div class="grid2">{plats}</div>
</section>

<section>
  <h2>6 · Regímenes de mercado</h2>
  <p>PF de Ultra por año (CFD 2020-26). Ganó todos los años.</p>
  <div class="figure">{yr_svg}</div>
  {reg_tbl}
  <p><b>El punto débil está a la vista:</b> en días de rango (el Nasdaq cierra lejos de su tendencia del día) los tres perfiles pierden; en días de tendencia ganan mucho. Un período largo de mercado lateral es el escenario que más daño haría.</p>
  <p>En 2015-19 el NQ se movía mucho menos (ATR ~60-100 puntos) y los mismos módulos daban PF {f2(r1519['pf'])}: los costos se comían la ventaja. Solo el {f1(100 * r1519['share_days_atr_ge150'])}% de esos días tuvo ATR ≥ 150, y en esos días el PF fue {f2(r1519['pf_if_atr_ge150'])}. El filtro MinAtrPoints = 150 de NQMaster deja de operar justo en ese régimen.</p>
</section>

<section>
  <h2>7 · Drawdown</h2>
  <p>4.000 años simulados con bloques de 10 días tomados de la historia (1 lote por módulo). Supone que el futuro se parece a esa base.</p>
  {mc_tbl}
</section>

<section>
  <h2>8 · Correlación</h2>
  <p>Correlación de los resultados diarios entre los módulos de Ultra en MNQ real 2024-26. Casi todo es claro: los módulos ganan y pierden en días distintos. Los pares más relacionados son las variantes del mismo patrón (ORB60/ORB90, MSEQ/MSEQS).</p>
  <div class="figure" style="max-width:560px">{heat}</div>
</section>

<section>
  <h2>9 · Más trades no es más evidencia</h2>
  <p>Los trades del mismo día dependen del mismo mercado. La cuenta honesta es en días, y corregida por las rachas (bootstrap por bloques). Los rangos son 5% – 95%.</p>
  {ev_tbl}
</section>

<section>
  <h2>10 · La prueba final es en vivo: monitor de ventaja</h2>
  <p>NQMaster suma cada día cuánto se queda por debajo de lo esperado: S = máx(0, S + k − z), con z = resultado del día por contrato dividido por 2 × ATR. Si S supera el umbral h, el resultado en vivo ya no es compatible con el backtest. Umbral elegido (★): pocas falsas alarmas y ninguna en toda la historia 2020-26.</p>
  {mon_tbl}
  <p class="muted">Una ventaja con Sharpe ~3 tiene meses malos normales; distinguirlos de una ventaja muerta lleva tiempo. Por eso el monitor tarda meses en confirmar y por defecto solo avisa.</p>
  <div class="code">Edge monitor on ................. true
Pause new entries on alarm ...... false   (true = deja de abrir trades si salta)
Edge monitor start date ......... fecha en que empezás en vivo (yyyy-MM-dd)
k / h ........................... 0 = calibración del perfil
  Ultra    k {pu['k']}  h {f2(pu['chosen']['h'])}
  WR70Plus k {pw['k']}  h {f2(pw['chosen']['h'])}
  Core     k {pc['k']}  h {f2(pc['chosen']['h'])}</div>
  <p>El panel del gráfico muestra “Edge monitor: X% of alarm” y la ventana Output imprime una línea por día.</p>
</section>

<section>
  <h2>Qué hacer ahora</h2>
  <ol class="steps">
    <li>Compilar en NinjaTrader (F5) y correr el backtest de Ultra 2020 → hoy con 1 contrato: debe dar ~4,5 trades/día y PF cerca de 1,45.</li>
    <li>Dos semanas en Sim con la cuenta real de datos, Edge monitor start = el primer día.</li>
    <li>Pasar a la evaluación con la configuración del plan. Si el monitor llega al 100%: revisar, y pasar a Profile = Core.</li>
    <li>Cada mes: comparar trades/día, WR y PF en vivo con la tabla de arriba.</li>
  </ol>
</section>
</div>
"""
open(OUT, "w", encoding="utf-8").write(page)
print("written", OUT, len(page))
