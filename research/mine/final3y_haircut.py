"""final3y: recommended setups under a forward edge haircut (h x mean daily P&L removed from every day, eval and funded vectors;
audit_ realistic case = 35%). History + 600 bootstrap years on REAL 2024-02..2026-09. -> final3y_haircut.json"""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import acct1c_lib as A
from final3y_acct import evarr, fuarr, FIRMS, BUF, nd, life_m, eval_stats
CASES = [("MyFundedFutures Rapid EOD 50K", "Ultra fixed", "Ultra 1c"), ("MyFundedFutures Rapid EOD 50K", "Estable (Ultra / Estable gear, C1200)", "Ultra 1c"),
         ("MyFundedFutures Rapid EOD 50K", "Ultra fixed", "Ultra 1c -> 2c from $3,000 cushion"), ("Lucid Flex 50K", "Ultra fixed", "Ultra 1c"),
         ("Lucid Flex 50K", "Estable (Ultra / Estable gear, C1200)", "Ultra 1c"), ("Lucid Flex 50K", "Ultra fixed", "Ultra 1c -> 2c from $1,500 cushion")]
if __name__ == "__main__":
    hidx = np.arange(nd, dtype=np.int64); IDX = [A.boot_idx(nd, q, 253, 10, 31) for q in range(600)]; OUT = []
    for firm, ev, fn in CASES:
        F = FIRMS[firm]; t0, t1, t2, c1, c2 = F["funds"][fn]
        EL0, EC0, C = evarr(ev, F["G"], False); FL0, FC0 = fuarr((t0, t1, t2), F["news"], False)
        for h in (0.0, 0.25, 0.35, 0.5):
            me = h * EC0.mean(1, keepdims=True); mf = h * FC0.mean(1, keepdims=True)
            EL = np.ascontiguousarray(EL0 - me); EC = np.ascontiguousarray(EC0 - me); FL = np.ascontiguousarray(FL0 - mf); FC = np.ascontiguousarray(FC0 - mf)
            o = np.zeros((nd, 2))
            m = A.eval_all(EL, EC, C, 3000.0, 2000.0, F["cons"], hidx, 60, o) if firm.startswith("Lucid") else eval_stats(EL, EC, C, 3000.0, 2000.0, F["cons"], 4, hidx, 60, o)
            es = A.esumm(o[:m]); okst = np.ones(nd, np.bool_)
            def run(idx, step, out):
                if firm.startswith("Lucid"): return A.life(EL, EC, C, 3000.0, 2000.0, F["cons"], okst, F["fee"], FL, FC, c1, c2, 0, 4000.0, 150.0, 2000.0, 2000.0, idx, 252, step, out)
                return life_m(EL, EC, C, 3000.0, 2000.0, F["cons"], 4, F["fee"], FL, FC, c1, c2, BUF[fn], 0, idx, 252, step, out)
            out = np.zeros((nd, 9)); mm = run(hidx, 3, out); Hh = out[:mm]
            Lb = np.zeros((600, 9)); o1 = np.zeros((2, 9))
            for q, idx in enumerate(IDX): run(idx, 252, o1); Lb[q] = o1[0]
            fm = Lb[:, 6].sum() / 21.0
            OUT.append(dict(firm=firm, eval=ev, funded=fn, haircut=h, pass_pct=round(es["pass_pct"], 1), med_days=es["med_days"],
                            hist_month=round(Hh[:, 0].mean() / 12), boot_month=round(Lb[:, 0].mean() / 12), boot_p10=round(np.percentile(Lb[:, 0], 10) / 12),
                            boot_neg_year=round(100 * (Lb[:, 0] < 0).mean(), 1), cash_per_funded_month=round(Lb[:, 7].sum() / max(fm, 1e-9))))
            print(OUT[-1], flush=True)
    json.dump(OUT, open("final3y_haircut.json", "w"), indent=1)
