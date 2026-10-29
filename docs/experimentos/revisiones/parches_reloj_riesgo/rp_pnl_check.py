# replica of PnlAtStops (NQMaster.cs:2308-2322) for hand cases; MNQ tick 0.25, point value 2
TS, PV = 0.25, 2.0
def pnl(entry, dir_, qty, xv, is_px):
    sp = xv if is_px else entry - dir_ * xv * TS
    return (sp - entry) * dir_ * qty * PV
cases = [("long ticks 40t x6", 20000.0, 1, 6, 40, False, -40*TS*6*PV),
         ("short ticks 40t x6", 20000.0, -1, 6, 40, False, -40*TS*6*PV),
         ("long price stop 19990 x3", 20000.0, 1, 3, 19990.0, True, -10*3*PV),
         ("short price stop 20010 x3", 20000.0, -1, 3, 20010.0, True, -10*3*PV),
         ("VOLB long BE +0.1R (R=20)", 20000.0, 1, 2, 20002.0, True, +2*2*PV),
         ("VOLB short BE +0.1R (R=20)", 20000.0, -1, 2, 19998.0, True, +2*2*PV),
         ("long slipped fill ticks (entry 20003, 40t)", 20003.0, 1, 1, 40, False, -40*TS*PV),
         ("long slipped fill price (entry 20003, stop 19990)", 20003.0, 1, 1, 19990.0, True, -13*PV)]
for name, e, d, q, xv, px, exp in cases:
    got = pnl(e, d, q, xv, px); print(f"{name:52s} got {got:9.2f} expected {exp:9.2f} {'OK' if abs(got-exp)<1e-9 else 'MISMATCH'}")
