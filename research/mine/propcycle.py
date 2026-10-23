"""Python port of NQMaster.PropCycle (the account rules engine behind the dashboard; C# between the <propcycle> markers of NQMaster.cs).
Same semantics line by line; tools/propcycle_test/run_test.py checks the C# class, this port and the research simulators against each other."""


class PropCycle:
    def __init__(s, firm="", model=0, T=0.0, D=0.0, cons=0.0, Q=0.0, cap1=0.0, cap2=0.0, X=0.0, npmax=5, mindays=1, fee=0.0, act=0.0):
        s.firm, s.model, s.T, s.D, s.cons, s.Q, s.cap1, s.cap2, s.X = firm, model, T, D, cons, Q, cap1, cap2, X
        s.npmax, s.mindays, s.fee, s.act = npmax, mindays, fee, act
        s.lock, s.buf, s.pcons, s.split, s.cycle_min_days = 100.0, D + 100.0, 0.4, 0.9, 3
        s.start(False)

    def start(s, funded):
        s.funded, s.alive = funded, True
        s.raw = s.wd = s.pk = s.day_start = s.cyc_start = 0.0
        s.best = s.cyc_best = -1e9
        s.days = s.qd = s.nd = s.pays = 0
        s.locked = False

    @property
    def bal(s): return s.raw - s.wd

    @property
    def thr(s): return s.lock if (s.locked or s.pk >= s.D + s.lock) else s.pk - s.D

    def target_met(s, prof):
        if prof < s.T: return False
        return s.cons <= 0 or max(s.best, prof - s.day_start) <= s.cons * prof

    def bar(s, raw_low, raw_close):
        if not s.alive: return 0
        if raw_low - s.wd <= s.thr: s.alive = False; return -1
        if not s.funded and s.target_met(raw_close - s.wd): s.alive = False; return 1
        return 0

    def day_close(s, raw_close):
        s.raw = raw_close; s.days += 1
        bal = s.bal; c = bal - s.day_start; amt = 0.0
        if not s.funded:
            s.best = max(s.best, c); s.pk = max(s.pk, bal); s.day_start = bal; return 0.0
        s.nd += 1; s.pk = max(s.pk, bal)
        if s.model == 0:
            if c >= s.Q: s.qd += 1
            if s.qd >= 5 and bal - s.cyc_start > 0 and bal >= s.X:
                a = min(s.cap1, 0.5 * bal)
                if a >= 500: amt = a; s.qd = 0; s.locked = True
        elif s.model == 1:
            s.cyc_best = max(s.cyc_best, c)
            prof = bal - s.cyc_start; cap = s.cap1 if s.pays == 0 else s.cap2; a = min(cap, bal - s.buf)
            if s.nd >= s.cycle_min_days and prof >= 500 and a >= max(500, min(s.X, cap)) and s.cyc_best <= s.pcons * prof:
                amt = a; s.cyc_best = -1e9; s.nd = 0
        elif bal - s.X >= 500: amt = bal - s.X
        if amt > 0: s.wd += amt; s.pays += 1; s.cyc_start = s.bal
        s.day_start = s.bal
        if amt > 0 and s.npmax > 0 and s.pays >= s.npmax: s.alive = False
        return amt


# preset -> firm rules (same as NQMaster.FirmRules + the preset values used by CycleInit)
PRESETS = {
    "Lucid25K": dict(firm="Lucid Flex 25K", model=0, T=1250, D=1000, cons=0.5, Q=100, cap1=1000, cap2=1000, payout_at=1500, fee=89),
    "Lucid50K": dict(firm="Lucid Flex 50K", model=0, T=3000, D=2000, cons=0.5, Q=150, cap1=2000, cap2=2000, payout_at=4000, fee=146),
    "Lucid150K": dict(firm="Lucid Flex 150K", model=0, T=9000, D=4500, cons=0.5, Q=250, cap1=3000, cap2=3000, payout_at=6000, fee=285),
    "LucidPro25K": dict(firm="Lucid Pro 25K", model=1, T=1250, D=1000, cons=0.0, cap1=1000, cap2=1500, payout_at=2100, fee=123),
    "LucidPro50K": dict(firm="Lucid Pro 50K", model=1, T=3000, D=2000, cons=0.0, cap1=2000, cap2=2500, payout_at=4100, fee=192),
    "FundedNext25K": dict(firm="FundedNext Rapid Pro 25K (aprox.)", model=1, T=1500, D=1000, cons=0.0, cap1=1200, cap2=1200, payout_at=1500, fee=80),
    "Mffu50K": dict(firm="MFFU Rapid EOD 50K", model=2, T=3000, D=2000, cons=0.3, mindays=4, npmax=0, payout_at=4600, fee=157),
}


def from_preset(name, fee=None, act=0.0, payout_at=None):
    p = dict(PRESETS[name]); pa = payout_at or p.pop("payout_at"); p.pop("payout_at", None)
    if fee: p["fee"] = fee
    c = PropCycle(act=act, **p)
    c.X = pa if c.model == 0 else (max(500.0, pa - c.buf) if c.model == 1 else pa - 500.0)
    return c
