import pickle, numpy as np, pandas as pd
from life25 import pa_run
from evalfast import run as eval_run
T = pickle.load(open("feat_trades2.pkl", "rb"))
exec(open("minute_path.py").read().split("def build(")[0])      # imports
from ict import load
def sm(om): return (np.asarray(om) - 1080) % 1440
def build(tag, F, days):
    D = load(tag + ".npz"); date = D["date"]; smm = sm(D["om"]); o, h, l, c = D["o"], D["h"], D["l"], D["c"]
    first = pd.Series(np.arange(len(date))).groupby(date).first(); last = pd.Series(np.arange(len(date))).groupby(date).last()
    out = {}
    for d, g in F.groupby("date"):
        if d not in first.index: continue
        a, b = first[d], last[d] + 1; mm = smm[a:b]; n = b - a
        fav = np.zeros(n); adv = np.zeros(n); rel = np.zeros(n)
        for r in g.itertuples():
            q = r.w
            if q == 0: continue
            i0 = min(np.searchsorted(mm, r.tin), n - 1); i1 = min(max(np.searchsorted(mm, r.tout - 1), i0), n - 1)
            e = o[a + i0] + 0.25 * r.d
            if i1 > i0:
                seg = slice(a + i0, a + i1)
                fv = (h[seg] - e) * 2 if r.d == 1 else (e - l[seg]) * 2; av = (l[seg] - e) * 2 if r.d == 1 else (e - h[seg]) * 2
                fav[i0:i1] += q * fv; adv[i0:i1] += q * av
            rel[i1:] += q * r.u
        out[d] = (fav, adv, rel)
    di, fv, av, rl = [], [], [], []
    for k, d in enumerate(days):
        if d not in out: continue
        fav, adv, rel = out[d]
        nz = np.nonzero((fav != 0) | (adv != 0) | (np.diff(np.r_[0.0, rel]) != 0))[0]
        di.append(np.full(len(nz), k)); fv.append(rel[nz] + fav[nz]); av.append(rel[nz] + adv[nz]); rl.append(rel[nz])
    return dict(day=np.concatenate(di), fav=np.concatenate(fv), adv=np.concatenate(av), rel=np.concatenate(rl), ndays=len(days))
def life2(PE, PP, E, H=252, step=3):
    nd = PE["ndays"]; out = []
    for s in range(0, nd - H, step):
        i = s; cash = fees = 0.0; npa = nbust = pays = 0
        while i < s + H:
            fees += 17.70
            r, used = eval_run(PE["day"], PE["fav"], PE["adv"], PE["rel"], nd, i, 1500.0, 1500.0, min(21, s + H - i), 0, E, 1, 0.0, 0.0, 0.0)
            j = i + used
            if r != 1: i = j; continue
            fees += 90; npa += 1
            c, k, st, dend = pa_run(PP["day"], PP["fav"], PP["adv"], PP["rel"], nd, j, s + H, 0, 1, 1, 1e9)
            cash += c; pays += k; nbust += st == -1; i = dend + 1
        out.append((cash - fees, pays, npa, nbust))
    a = np.array(out)
    return dict(net_mo=round(a[:, 0].mean() / 12), p10_mo=round(np.percentile(a[:, 0], 10) / 12), payouts_yr=round(a[:, 1].mean(), 1), PAs_yr=round(a[:, 2].mean(), 1), PA_busts_yr=round(a[:, 3].mean(), 1))
SUBS = {"PA = MaxPlus completo": None,
        "PA sin LON/MOM13/ON07 (winrate bajo)": ["LON", "MOM13", "ON07"],
        "PA sin LON/MOM13/ON07/CRT11": ["LON", "MOM13", "ON07", "CRT11"],
        "PA sin LON": ["LON"], "PA sin MOM13": ["MOM13"], "PA sin ON07": ["ON07"],
        "PA ICT x1": "ICT1"}
if __name__ == "__main__":
    rows = []
    for p, (F, days) in T.items():
        tag = "mnq_fut" if p == "REAL" else "nq_1m"; days = np.array(days)
        F = F.copy(); F["w"] = F.base_w
        PE = build(tag, F, days)
        for nm, ex in SUBS.items():
            G = F.copy()
            if ex == "ICT1": G["w"] = 1.0
            elif ex: G.loc[G["mod"].isin(ex), "w"] = 0.0
            PP = PE if ex is None else build(tag, G, days)
            r = life2(PE, PP, 4); r.update(per=p, pa=nm); rows.append(r); print(p, nm, r, flush=True)
    g = pd.DataFrame(rows)
    for c in ("net_mo", "p10_mo", "payouts_yr", "PA_busts_yr"):
        print(c); print(g.pivot(index="pa", columns="per", values=c).reindex(list(SUBS))[["IS", "C24", "REAL"]].to_string())
