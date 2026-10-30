# Emulates the C# edge-monitor state machine (EdgeStep) and patch_edge_restore's restore + replay, against a continuous run.
import random
K, H, HW, F = 0.0899, 26.93, 9.22, 252
class St:
    def __init__(s): s.S=0.0; s.days=0; s.alarm=False; s.fb=0; s.warned=False; s.last=0; s.events=[]
    def copy(s):
        t=St(); t.__dict__.update({k:(list(v) if isinstance(v,list) else v) for k,v in s.__dict__.items()}); return t
    def key(s): return (round(s.S,9), s.days, s.alarm, s.fb, s.warned, s.last)
def step(s, d, z):
    if s.fb > 0:
        s.fb -= 1; s.last = d
        if s.fb == 0: s.alarm=False; s.S=0.0; s.events.append(("fbend",d))
        return
    s.S = max(0.0, s.S + K - z); s.days += 1; s.last = d
    if s.S <= 0: s.warned=False
    if not s.warned and not s.alarm and s.S > HW: s.warned=True; s.events.append(("warn",d))
    if not s.alarm and s.S > H: s.alarm=True; s.fb=F; s.S=0.0; s.events.append(("alarm",d))
def run(seed, ndays=900, W=84, mu=0.0):
    rng = random.Random(seed)
    z = [rng.gauss(mu, 0.8) for _ in range(ndays+1)]
    truth = St()
    for d in range(1, ndays+1): step(truth, d, z[d])
    saved = None; inst = None; maxgap = 0; d = 1
    while d <= ndays:
        # restart at day d: history covers days [d-W, d-1], rebuilt from the window start
        rb = St(); rec = [(x, z[x]) for x in range(max(1, d-W), d)]
        for x, zz in rec: step(rb, x, zz)
        if saved is None: inst = rb
        else:
            inst = saved.copy()
            for x, zz in rec:
                if x > saved.last: step(inst, x, zz)
            cover = max(1, d-W)
            if cover > saved.last + 1: maxgap = max(maxgap, cover - saved.last - 1)
        saved = inst.copy()                       # save at go-live
        run_len = rng.choice([1, 1, 2, 5, 20, 60]); on18 = rng.random() < 0.6
        end = min(ndays+1, d+run_len)
        for x in range(d, end):
            if x < end - 1 or on18: step(inst, x, z[x]); saved = inst.copy()   # day closed live (NT running at 18:00), saved then
        d += run_len + rng.choice(OFFS)     # PC off for a while (days not seen live)
    # final restart to close the remaining days
    rb_days = [(x, z[x]) for x in range(max(1, ndays+1-W), ndays+1)]
    fin = saved.copy()
    if max(1, ndays+1-W) > saved.last + 1: maxgap = max(maxgap, max(1, ndays+1-W) - saved.last - 1)
    for x, zz in rb_days:
        if x > saved.last: step(fin, x, zz)
    return truth, fin, maxgap
import sys
OFFS = [0, 0, 0, 1, 3, 10, 40] if len(sys.argv) < 2 else [0, 0, 1, 3, 10, 40, 100]
ok = gap = 0
for seed in range(400):
    for mu in (0.18, 0.0, -0.09):
        t, f, g = run(seed, mu=mu)
        if g > 0: gap += 1; continue
        assert t.key() == f.key() and t.events == f.events, (seed, mu, t.key(), f.key())
        ok += 1
print("identical to the continuous run:", ok, "| runs with a gap (PC off longer than the history):", gap)
