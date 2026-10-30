# Emulacion del revisor (no es prueba del C#): EdgeStep + EdgeRestore de c1bf37e con lo que emul.py no modela:
# ATR valido desde el 2.o dia cargado (edgeCoverFrom), calentamiento de ~14 dias con z = 0 (modulos quietos, pero el dia cuenta),
# guardado al pasar a vivo (EdgeSave al final de EdgeRestore) y el aviso de hueco. Dias = sesiones consecutivas (sin fines de semana).
import random
K, H, HW, F = 0.0899, 26.93, 9.22, 252
WARM = 14   # AtrMin 14 / WarmupDays 15: los modulos no operan, el dia se cuenta igual (counted no mira atrCount)
class St:
    def __init__(s): s.S = 0.0; s.days = 0; s.alarm = False; s.fb = 0; s.warned = False; s.last = 0
    def copy(s): t = St(); t.__dict__.update(s.__dict__); return t
def step(s, d, z):
    if s.fb > 0:
        s.fb -= 1; s.last = d
        if s.fb == 0: s.alarm = False; s.S = 0.0
        return
    s.S = max(0.0, s.S + K - z); s.days += 1; s.last = d
    if s.S <= 0: s.warned = False
    if not s.warned and not s.alarm and s.S > HW: s.warned = True
    if not s.alarm and s.S > H: s.alarm = True; s.fb = F; s.S = 0.0
def history(first, golive, z):
    """dias que cierra el historico cargado desde 'first' hasta golive-1: (dia, z) contados y edgeCoverFrom"""
    rec = []; cover = 0
    for x in range(first, golive):
        if x == first: continue                      # 1.er dia: todayAtr NaN -> ni cuenta ni fija edgeCoverFrom
        if cover == 0: cover = x
        rec.append((x, 0.0 if x - first <= WARM else z[x]))
    return rec, cover
def restore(saved, rec, cover):
    st = saved.copy(); n = 0
    for x, zz in rec:
        if x > st.last: step(st, x, zz); n += 1
    gap = cover > saved.last + 1
    return st, gap          # el C# guarda st al pasar a vivo (EdgeSave) haya hueco o no
def truth(z, upto):
    t = St()
    for d in range(1, upto): step(t, d, z[d])
    return t
rng = random.Random(7)
print("A) hueco + remedio del runbook (subir Days to load y volver a habilitar)")
for mu in (0.18, 0.0):
    agg = []
    for seed in range(300):
        r = random.Random(seed); z = [r.gauss(mu, 0.8) for _ in range(400)]
        live = truth(z, 101)                          # NT corrio hasta el dia 100 y guardo d = 100
        rec, cov = history(250 - 84, 250, z)          # vuelve el dia 250 con ~84 sesiones cargadas
        st1, gap = restore(live, rec, cov); saved = st1.copy()   # aviso de hueco + EdgeSave al pasar a vivo
        rec2, cov2 = history(60, 250, z)              # vuelve a habilitar con Days to load alto
        st2, gap2 = restore(saved, rec2, cov2)
        t = truth(z, 250)
        agg.append((gap, gap2, st2.days, t.days, st2.S, t.S))
    g1 = sum(a[0] for a in agg); g2 = sum(a[1] for a in agg)
    lost = sum(a[3] - a[2] for a in agg) / len(agg)
    print("  mu %.2f: aviso de hueco %d/300, tras subir Days to load sigue el hueco %d/300; dias perdidos promedio %.1f (de %d)"
          % (mu, g1, g2, lost, agg[0][3]))
print("B) fecha guardada dentro del calentamiento del historico (sin aviso de hueco)")
for mu in (0.18, 0.0):
    diffs = []; gaps = 0
    for seed in range(2000):
        r = random.Random(seed); z = [r.gauss(mu, 0.8) for _ in range(400)]
        first = 250 - 84; dsave = first + 2               # NT apagado ~80 sesiones; d cae en el 3.er dia cargado
        live = truth(z, dsave + 1)
        rec, cov = history(first, 250, z)
        st, gap = restore(live, rec, cov); gaps += gap
        t = truth(z, 250)
        if not (t.alarm or st.alarm or t.fb or st.fb): diffs.append(st.S - t.S)
    print("  mu %.2f: avisos de hueco %d/2000; S repuesto - S continuo: media %+.2f (h = %.2f), n=%d"
          % (mu, gaps, sum(diffs) / len(diffs), H, len(diffs)))
