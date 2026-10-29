"""r8: re-run exp08's __main__ logic in memory (no write) and diff against exp08_monitor.json."""
import os, sys, json, numpy as np
M = "/home/user/nqmaster-research/research/mine"; sys.path.insert(0, M); sys.path.insert(0, os.path.dirname(M)); os.chdir(M)
SP = "/tmp/claude-0/-home-user-nqmaster-research/f66dc1ad-495a-5c1f-8f75-823556ecd370/scratchpad"
import exp08_monitor as E
J = json.load(open("exp08_monitor.json"))
OUT = {"control": {}, "politicas": {}}
for wn in ("os_adapt_set", False):
    days, atr, mods, Mv, N, post = E.build(with_new=wn)
    for pol in ("A", "W252"):
        x, al, wa, off, half = E.run(days, atr, mods, Mv, N, post, pol, 0.0758, 18.57, 1e18, zmode="os_adapt")
        rec = E.summary(days, x); r = dict(alarmas=len(al), **{q: rec[q] for q in E.PER})
        OUT["control"][f"{wn}:{pol}"] = r
        print(f"control build({wn!r}) {pol}: {r}\n   json: {J['control_os_adapt'][pol]}")
days, atr, mods, Mv, N, post = E.build(with_new=True)
same = True
for pol in ("A", "W252", "P63", "P126", "P252", "D252", "WH"):
    x, al, wa, off, half = E.run(days, atr, mods, Mv, N, post, pol, E.K, E.Hh, E.HW)
    rec = E.summary(days, x); rec.update(alarmas=al, dias_en_respuesta=off, dias_medio_tamano=half); OUT["politicas"][pol] = rec
    ok = all(rec[k] == J["politicas"][pol][k] for k in rec); same &= ok
    print(pol, "matches json" if ok else f"DIFFERS: {rec} vs {J['politicas'][pol]}")
print("all policies identical to json:", same)
json.dump(OUT, open(f"{SP}/r8_rerun.json", "w"), indent=1, default=str)
