"""Audit of NQMaster.PropCycle (the account rules engine behind the dashboard) against the research simulators.
Random day paths (intraday low / close per minute) for every firm model; the same paths go through
  eval  : research/mine/prop_wf.py race()            (minute race, EOD trailing, consistency, minimum days)
  flex  : research/mine/acct1c_lib.py fu_flex()      (Lucid Flex funded)
  pro   : research/mine/acct1c_lib.py fu_pro()       (Lucid Pro / FundedNext funded)
  mffu  : research/mine/mffu_rapid.py fu_m()         (MFFU Rapid funded, keep a balance)
and through the C# class extracted from NQMaster.cs (compiled with mono mcs). Every case must give the same outcome
(pass / bust / completed / open), the same day, the same payouts and the same cash.  Run: python3 tools/propcycle_test/run_test.py"""
import os, re, sys, subprocess, tempfile, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "research", "mine")); os.chdir(os.path.join(ROOT, "research", "mine"))   # the research libraries read files relative to research/mine
import prop_wf, acct1c_lib as A, mffu_rapid as M
from propcycle import PropCycle as PyCycle

src = open(os.path.join(ROOT, "NQMaster.cs"), encoding="utf-8-sig").read()
m = re.search(r"// <propcycle>.*?// </propcycle>", src, re.S)
assert m, "PropCycle markers not found in NQMaster.cs"
harness = open(os.path.join(HERE, "Harness.cs")).read().replace("//PROPCYCLE//", m.group(0))
FIRMS = {  # mode, T, D, cons, mind, Q, cap1, cap2, X, npmax
    "LucidFlex25K": [("eval", 1250, 1000, 0.5, 1, 0, 0, 0, 0, 0), ("flex", 0, 1000, 0, 1, 100, 1000, 1000, 1500, 5)],
    "LucidFlex50K": [("eval", 3000, 2000, 0.5, 1, 0, 0, 0, 0, 0), ("flex", 0, 2000, 0, 1, 150, 2000, 2000, 4000, 5)],
    "LucidFlex150K": [("eval", 9000, 4500, 0.5, 1, 0, 0, 0, 0, 0), ("flex", 0, 4500, 0, 1, 250, 3000, 3000, 6000, 5)],
    "LucidPro25K": [("eval", 1250, 1000, 0.0, 1, 0, 0, 0, 0, 0), ("pro", 0, 1000, 0, 1, 0, 1000, 1500, 1000, 5)],
    "LucidPro50K": [("eval", 3000, 2000, 0.0, 1, 0, 0, 0, 0, 0), ("pro", 0, 2000, 0, 1, 0, 2000, 2500, 2000, 5)],
    "MFFU50K": [("eval", 3000, 2000, 0.3, 4, 0, 0, 0, 0, 0), ("mffu", 0, 2000, 0, 1, 0, 0, 0, 4100, 0)],
    "MFFU50Kladder": [("mffu", 0, 2000, 0, 1, 0, 0, 0, 11100, 0)],
}
rng = np.random.default_rng(int(os.environ.get("SEED", "7")))
cases, txt = [], []
ND, NM = 120, 30
for firm, specs in FIRMS.items():
    for spec in specs:
        mode, T, D, cons, mind, Q, c1, c2, X, npm = spec
        for k in range(int(os.environ.get("NCASE", "60"))):
            sc = D / 2000.0 * rng.choice([0.5, 1.0, 1.6]); mu = rng.choice([-20, 0, 40, 90, 160]) * sc
            steps = rng.normal(mu / NM, 70 * sc / np.sqrt(NM) * 3, (ND, NM))
            CL = np.cumsum(steps, axis=1); LO = CL - np.abs(rng.normal(0, 25 * sc, (ND, NM)))
            CL = np.round(CL, 2); LO = np.round(LO, 2)
            cid = f"{firm}:{mode}:{k}"; cases.append((cid, spec, LO, CL))
            txt.append(f"{cid} {mode} {T} {D} {cons} {mind} {Q} {c1} {c2} {X} {npm} {ND} {NM}")
            for d in range(ND):
                txt.append(" ".join(f"{v:.2f}" for v in LO[d])); txt.append(" ".join(f"{v:.2f}" for v in CL[d]))

def research(spec, LO, CL):
    mode, T, D, cons, mind, Q, c1, c2, X, npm = spec
    n = LO.shape[0]; idx = np.arange(n, dtype=np.int64)
    if mode == "eval":
        ep = np.array([T, D, cons, mind, 0, 0, 0, 1, 1, 0, 0, 0, 0, 100.0, 0], np.float64)
        r, d = prop_wf.race(np.ascontiguousarray(np.minimum(LO, CL)), np.ascontiguousarray(CL), np.zeros(n), idx, 0, n, ep)
        return (int(r), int(d), 0.0, 0)
    FL1 = np.minimum(LO, CL).min(axis=1); FC1 = CL[:, -1]
    FL = np.ascontiguousarray(np.vstack([FL1] * 3)); FC = np.ascontiguousarray(np.vstack([FC1] * 3))
    if mode == "flex": cash, mm, st, d = A.fu_flex(FL, FC, -1e9, -1e9, idx, 0, n, float(X), float(D), float(Q), float(c1))
    elif mode == "pro": cash, mm, st, d = A.fu_pro(FL, FC, -1e9, -1e9, idx, 0, n, float(X), float(D), float(c1), float(c2), 0.4, npm, 3)
    else: cash, mm, st, d = M.fu_m(FL, FC, -1e9, -1e9, idx, 0, n, float(X), float(D), npm)
    return (int(st), int(d), round(float(cash), 2), int(mm))

with tempfile.TemporaryDirectory() as tmp:
    open(os.path.join(tmp, "H.cs"), "w").write(harness); open(os.path.join(tmp, "paths.txt"), "w").write("\n".join(txt) + "\n")
    subprocess.run(["mcs", "-langversion:5", "-out:" + os.path.join(tmp, "h.exe"), os.path.join(tmp, "H.cs")], check=True, capture_output=True)
    subprocess.run(["mono", os.path.join(tmp, "h.exe"), os.path.join(tmp, "paths.txt"), os.path.join(tmp, "out.txt")], check=True)
    out = {l.split()[0]: l.split()[1:] for l in open(os.path.join(tmp, "out.txt")).read().split("\n") if l.strip()}
def python_port(spec, LO, CL):
    mode, T, D, cons, mind, Q, c1, c2, X, npm = spec
    p = PyCycle(model={"flex": 0, "pro": 1}.get(mode, 2), T=T, D=D, cons=cons, Q=Q, cap1=c1, cap2=c2, X=X, npmax=npm, mindays=mind)
    p.start(mode != "eval"); cash = 0.0
    for d in range(LO.shape[0]):
        raw0 = p.raw; last = 0.0
        for j in range(LO.shape[1]):
            r = p.bar(raw0 + min(LO[d, j], CL[d, j]), raw0 + CL[d, j])
            if r: return (r, max(d, mind - 1) if r == 1 else d, round(cash, 2), p.pays)
            last = CL[d, j]
        cash += p.split * p.day_close(raw0 + last)
        if not p.alive: return (1, d, round(cash, 2), p.pays)
    return (0, LO.shape[0], round(cash, 2), p.pays)

bad = 0; kinds = {}; badpy = 0
for cid, spec, LO, CL in cases:
    r = research(spec, LO, CL); c = out[cid]; cs = (int(c[0]), int(c[1]), round(float(c[2]), 2), int(c[3]))
    kinds[(spec[0], r[0])] = kinds.get((spec[0], r[0]), 0) + 1
    if cs[0] != r[0] or cs[1] != r[1] or cs[3] != r[3] or abs(cs[2] - r[2]) > 0.05:   # cash: 1-cent float rounding allowed
        bad += 1
        if bad <= 15: print("MISMATCH", cid, "research", r, "NQMaster", cs)
    py = python_port(spec, LO, CL)
    if py[0] != r[0] or py[1] != r[1] or py[3] != r[3] or abs(py[2] - r[2]) > 0.05:
        badpy += 1
        if badpy <= 15: print("MISMATCH python port", cid, "research", r, "port", py)
print("cases", len(cases), "mismatches C# vs research", bad, "| python port vs research", badpy)
print("outcomes (mode, result): count ->", dict(sorted(kinds.items())))
sys.exit(1 if bad or badpy else 0)
