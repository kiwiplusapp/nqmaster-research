"""perturb_lab (2026-10-19): parameter-perturbation robustness audit of every module of the 2027 NQMaster default
(Ultra + SO04 / RV11 / ORFAIL / CAM3, nt_compare --set ultra_d4), on real Databento NQ 2010-06..2026-10.
Per module (perturb_lib.SPEC: 3-5 key parameters: anchor time, threshold x ATR, stop, target R, window / lookback):
  oat   one-at-a-time: pct params at -20/-10/+10/+20 %, clock params at -30/-15/+15/+30 min, int params rounded
  fact  factorial 5^3 grid of the first 3 parameters (plateau search, chosen on T1 only)
  draw  200 random joint draws (all of the module's parameters at once, uniform +-20 % / +-30 min), seeded per (module, draw)
  sys   200 whole-system draws: every module at its draw j simultaneously
  slip  base with +1 / +2 / +4 ticks per side (real views)
Each cell: the module alone (standalone PF / WR / Sharpe per period) and the whole portfolio with that module replaced
(conflict filter, agreement, confluence, context rules, MinATR 150 as in cand16 / six_build): A 2010-14, B 2015-19 cost-normalised,
T1 2020-23, T2 2024-26 real $.  Results: perturb_cells.csv (every cell), module trades in <scratch>/pt/.  Resumable.
Run: cd research/mine && python3 perturb_lab.py   (2 processes, ~1 h).  Analysis / report: perturb_analysis.py"""
import os, sys, json, time, pickle, itertools, numpy as np, pandas as pd
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import perturb_lib as P
SCR = os.environ.get("PERTURB_SCRATCH", "/tmp/claude-0/-home-user-nqmaster-research/176a42ca-c215-52e2-84dc-57e214e477d4/scratchpad")
PT = os.path.join(SCR, "pt"); os.makedirs(PT, exist_ok=True)
NDRAW = int(os.environ.get("PERTURB_NDRAW", "200"))
PCT = (-0.2, -0.1, 0.0, 0.1, 0.2); TIM = (-30, -15, 0, 15, 30)
BASE = {}


def levels(kind):
    return TIM if kind == "time" else PCT


def eps_draw(mod, j):
    rng = np.random.default_rng([P.MODS.index(mod) + 1, j + 1]); sp = P.SPEC[mod]
    return {k: float(rng.uniform(-30, 30)) if kind == "time" else float(rng.uniform(-0.2, 0.2)) for k, kind in sp["pert"].items()}


def tasks():
    T = []
    for mod in P.MODS:
        sp = P.SPEC[mod]; keys = list(sp["pert"]); prim = keys[:3]
        T.append(("base", mod, 0, {}))
        for cell in itertools.product(*[levels(sp["pert"][k]) for k in prim]):
            eps = {k: v for k, v in zip(prim, cell) if v != 0}
            if eps: T.append(("fact", mod, len(T), eps))
        for k in keys[3:]:
            for v in levels(sp["pert"][k]):
                if v != 0: T.append(("oat", mod, len(T), {k: v}))
        for j in range(NDRAW): T.append(("draw", mod, j, eps_draw(mod, j)))
    for k in (1, 2, 4): T.append(("slip", "ALL", k, {}))
    for j in range(NDRAW): T.append(("sys", "ALL", j, {}))
    return T


def key(kind, mod, idx, eps):
    return f"{kind}|{mod}|{idx}|{json.dumps(eps, sort_keys=True)}"


def init():
    P.init(); BASE.update(pickle.load(open(os.path.join(SCR, "base_parts.pkl"), "rb")))


def flat(prefix, M):
    return {f"{prefix}{per}_{k}": v for per, m in M.items() for k, v in m.items()}


def run(task):
    kind, mod, idx, eps = task; t0 = time.time(); row = dict(kind=kind, mod=mod, idx=idx, eps=json.dumps(eps, sort_keys=True))
    try:
        if kind in ("base", "fact", "oat", "draw"):
            p = P.perturbed(mod, eps); row["params"] = json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in p.items()}, default=str)
            tr = P.compact(P.sim_module(mod, p))
            parts = dict(BASE); parts[mod] = tr
            row.update(flat("m_", P.module_metrics(tr))); row.update(flat("p_", P.port_metrics(parts)))
            if kind in ("draw", "fact", "base"): pickle.dump(tr, open(os.path.join(PT, f"{mod}_{kind}_{idx}.pkl"), "wb"))
        elif kind == "slip":
            P.G["slip"] = 0.25 * (1 + idx); parts = {m: P.compact(P.sim_module(m, P.SPEC[m]["base"])) for m in P.MODS}; P.G["slip"] = 0.25
            row.update(flat("p_", P.port_metrics(parts)))
        elif kind == "sys":
            parts = {m: pickle.load(open(os.path.join(PT, f"{m}_draw_{idx}.pkl"), "rb")) for m in P.MODS}
            row.update(flat("p_", P.port_metrics(parts)))
    except Exception as e:
        import traceback; row["err"] = repr(e)[:300]; traceback.print_exc()
    row["secs"] = round(time.time() - t0, 2)
    return row


if __name__ == "__main__":
    out = os.path.join(HERE, "perturb_cells.csv")
    done = set()
    if os.path.exists(out):
        R0 = pd.read_csv(out); done = set(key(r.kind, r["mod"], r.idx, json.loads(r.eps)) for _, r in R0.iterrows()); rows = R0.to_dict("records")
    else: rows = []
    if not os.path.exists(os.path.join(SCR, "base_parts.pkl")):
        P.init(); parts = {m: P.compact(P.sim_module(m, P.SPEC[m]["base"])) for m in P.MODS}; pickle.dump(parts, open(os.path.join(SCR, "base_parts.pkl"), "wb"))
    T = [t for t in tasks() if key(*t) not in done]
    if os.environ.get("PERTURB_LIMIT"): T = T[: int(os.environ["PERTURB_LIMIT"])]
    mods_t = [t for t in T if t[0] != "sys"]; sys_t = [t for t in T if t[0] == "sys"]
    print("tasks", len(T), "module", len(mods_t), "sys", len(sys_t), "done", len(done), flush=True)
    t0 = time.time()
    with Pool(int(os.environ.get("PERTURB_PROCS", "2")), initializer=init) as pool:
        for stage in (mods_t, sys_t):
            for k, row in enumerate(pool.imap_unordered(run, stage, chunksize=4)):
                rows.append(row)
                if k % 200 == 0:
                    pd.DataFrame(rows).to_csv(out, index=False); print(k, len(stage), round(time.time() - t0), "s", row["kind"], row["mod"], row.get("err", ""), flush=True)
            pd.DataFrame(rows).to_csv(out, index=False)
    R = pd.DataFrame(rows); R.to_csv(out, index=False)
    print("done", len(R), round(time.time() - t0), "s; errors", int(R["err"].notna().sum()) if "err" in R else 0, flush=True)
