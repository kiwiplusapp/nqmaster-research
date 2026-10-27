"""2026-10-27 experiment 01 S2 (docs/PLAN_2026-10-26.md 2.4): three NinjaTrader port bugs found by the trade-by-trade parity classification
against the research rules (docs/experimentos/01_paridad.md, S2). Applies on top of patch_fillseries.py (v4.2); idempotent (refuses twice).
1. ORFAIL / CAM3: SixEnter dropped the signal when DirectionAllowed() deferred it (an opposite VOLB stop order working) and never retried,
   unlike TimeEntry / MSEQ: 62 of 69 ORFAIL and 13 of 14 CAM3 research-only trades. One retry on the next 1-minute bar, same stop / target.
2. ICT: a deferred setup re-armed the 5-minute search (ictAct) and required the trigger again -> fills 9-26 min late or never (5 lost, 4 shifted).
   The setup (direction, limit, stop, extreme, expiry, lots) is kept and the limit is placed on the next 1-minute bar when the direction is free.
3. MSEQS: gated on the FILL of ORB60 short; the validated rule (research/mine/wrq_build.py b_mseq) gates on the RAW ORB60 short signal of the
   day (price through OR low - 1 tick on a down-trend pullback day, before the ORBt prior-close filter and the stop-size checks): 7 of 12
   research-only. A virtual signal tracker replaces the fill gate; the 5-minute bar that contains the signal is already allowed (last 1-min >=).
v2 (adversarial review 2026-10-27): the ORFAIL / CAM3 retry is dropped when the deferral bar already crossed the stop (as pend5 does;
the research would have lost 1R, NinjaTrader cannot reproduce that fill) and logs a skipped bar; the pending ICT lots are re-scaled at
go-live like pend5 / parked setups; an ICT setup blocked by an opposite POSITION (not an order) is parked like the direct path.
Run from anywhere: python3 research/mine/patch_parity_s2.py"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, "NQMaster.cs")
s = open(P, encoding="utf-8-sig").read(); n0 = len(s.splitlines())
if "orbSigDir" in s: sys.exit("already patched (orbSigDir present)")
if "FillAhead(DateTime t, Order o)" not in s: sys.exit("apply patch_fillseries.py (v4.2) first")


def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count: sys.exit(f"anchor found {n} times (expected {count}): {old[:100]!r}")
    s = s.replace(old, new)


# ---- 1. ORFAIL / CAM3: fields, dispatch with one retry, session resets
rep("\t\tprivate double orfH, orfL, orfExt, orfSl, orfTp; private int orfBrk, orfBi, orfSig; private bool orfHas, orfReady, orfDone;\n",
    "\t\tprivate double orfH, orfL, orfExt, orfSl, orfTp; private int orfBrk, orfBi, orfSig, orfPend, orfPendBar = -1; private bool orfHas, orfReady, orfDone;\t// orfPend: signal deferred by an opposite working order, retried once on the next bar (S2 2026-10-27)\n")
rep("\t\tprivate double camLev, camExt, camSl, camTp; private int camSide, camBr = -1, camSig; private bool camDone = true;\n",
    "\t\tprivate double camLev, camExt, camSl, camTp; private int camSide, camBr = -1, camSig, camPend, camPendBar = -1; private bool camDone = true;\n")
rep("\t\t\tif (orfSig != 0) { int os = orfSig; orfSig = 0; SixEnter(orf, os, orfSl, orfTp); }\n"
    "\t\t\tif (camSig != 0) { int cs = camSig; camSig = 0; SixEnter(cam3, cs, camSl, camTp); }\n",
    "\t\t\t// S2 2026-10-27: a six-year signal deferred by DirectionAllowed (opposite stop order working, parked there) is retried once on the next\n"
    "\t\t\t// 1-minute bar with the same stop / target, as TimeEntry and MSEQ do (dropped if that bar crossed the stop, as pend5: the research would have\n"
    "\t\t\t// taken the trade at the signal close and lost 1R; NinjaTrader cannot place that fill); the research has no working orders and enters at once\n"
    "\t\t\tif (orfSig != 0) { int os = orfSig; orfSig = 0; SixEnter(orf, os, orfSl, orfTp); if (lastDeferred) { orfPend = os; orfPendBar = CurrentBars[0]; } }\n"
    "\t\t\telse if (orfPend != 0) { int os = orfPend; orfPend = 0; if (CurrentBars[0] != orfPendBar + 1) Log(\"ORFAIL deferred signal dropped (bar skipped)\"); else if (os == 1 ? Low[0] <= orfSl : High[0] >= orfSl) Log(\"ORFAIL deferred signal dropped (stop crossed during the deferral)\"); else { SixEnter(orf, os, orfSl, orfTp); if (!lastDeferred && Working(orf.Entry)) Log(\"ORFAIL entered after the deferral\"); } }\n"
    "\t\t\tif (camSig != 0) { int cs = camSig; camSig = 0; SixEnter(cam3, cs, camSl, camTp); if (lastDeferred) { camPend = cs; camPendBar = CurrentBars[0]; } }\n"
    "\t\t\telse if (camPend != 0) { int cs = camPend; camPend = 0; if (CurrentBars[0] != camPendBar + 1) Log(\"CAM3 deferred signal dropped (bar skipped)\"); else if (cs == 1 ? Low[0] <= camSl : High[0] >= camSl) Log(\"CAM3 deferred signal dropped (stop crossed during the deferral)\"); else { SixEnter(cam3, cs, camSl, camTp); if (!lastDeferred && Working(cam3.Entry)) Log(\"CAM3 entered after the deferral\"); } }\n")
rep("\t\t\torfHas = orfReady = orfDone = false; orfBrk = 0; orfSig = 0;\n", "\t\t\torfHas = orfReady = orfDone = false; orfBrk = 0; orfSig = 0; orfPend = 0;\n")
rep("\t\t\tcamSig = 0; camBr = -1; camSide = trendDir;", "\t\t\tcamSig = 0; camPend = 0; camBr = -1; camSide = trendDir;")

# ---- 2. ICT: deferred setup kept and placed on the next 1-minute bar
rep("\t\tprivate bool[] ictAct = new bool[2]; private double[] ictExt = new double[2]; private int[] ictExtBar = new int[2];\n",
    "\t\tprivate bool[] ictAct = new bool[2]; private double[] ictExt = new double[2]; private int[] ictExtBar = new int[2];\n"
    "\t\tprivate int ictPendDir, ictPendBar = -1, ictPendExp, ictPendQty; private double ictPendLim, ictPendStop, ictPendExtP;\t// ICT setup deferred by an opposite working order: limit placed on the next 1-minute bar (S2 2026-10-27)\n")
rep("\t\t\t\tif (ict.InTrade || Working(ict.Entry) || ict.Parked || ictTrades >= 3 || d != trendDir || atrCount < AtrMin) continue;\n",
    "\t\t\t\tif (ict.InTrade || Working(ict.Entry) || ict.Parked || ictPendDir != 0 || ictTrades >= 3 || d != trendDir || atrCount < AtrMin) continue;\n")
rep("\t\t\t\tif (!DirectionAllowed(d))\n\t\t\t\t{\n\t\t\t\t\tif (lastDeferred) ictAct[s] = true;\n",
    "\t\t\t\tif (!DirectionAllowed(d))\n\t\t\t\t{\n"
    "\t\t\t\t\t// S2 2026-10-27: deferred by an opposite working order -> keep the setup and place the limit on the next 1-minute bar (the research\n"
    "\t\t\t\t\t// places it at this close); re-arming the 5-minute search required the trigger again and filled 9-26 min late or not at all\n"
    "\t\t\t\t\tif (lastDeferred) { ictPendDir = d; ictPendLim = lim; ictPendStop = stop; ictPendExtP = ictExt[s]; ictPendExp = CurrentBars[1] + 20; ictPendQty = iq; ictPendBar = CurrentBars[0]; Log(string.Format(\"ICT {0} LIMIT @ {1} deferred to the next 1-minute bar\", d == 1 ? \"BUY\" : \"SELL\", Fmt(lim))); }\n")
rep("\t\t\tManageParked(openMin, closeMin);\n",
    "\t\t\tif (ictPendDir != 0)\n"
    "\t\t\t{\n"
    "\t\t\t\tint pdi = ictPendDir;\n"
    "\t\t\t\tif (ict.InTrade || Working(ict.Entry) || ict.Parked || CurrentBars[0] > ictPendBar + 5 || CurrentBars[1] >= ictPendExp || (pdi == -1 ? High[0] > ictPendExtP : Low[0] < ictPendExtP)) { ictPendDir = 0; Log(\"ICT deferred setup dropped\"); }\n"
    "\t\t\t\telse if (CurrentBars[0] > ictPendBar)\n"
    "\t\t\t\t{\n"
    "\t\t\t\t\tif (DirectionAllowed(pdi))\n"
    "\t\t\t\t\t{\n"
    "\t\t\t\t\t\tictPendDir = 0; ict.Dir = pdi; ictExtPend = ictPendExtP; ictExpiry = ictPendExp; ArmPriceBracket(ict, pdi, ictPendStop);\n"
    "\t\t\t\t\t\tint iqo = OfApply(ict, ictPendQty, pdi);\n"
    "\t\t\t\t\t\tOrder ir = iqo <= 0 ? null : (pdi == 1 ? EnterLongLimit(fillBip, true, iqo, ictPendLim, ict.Sig) : EnterShortLimit(fillBip, true, iqo, ictPendLim, ict.Sig));\n"
    "\t\t\t\t\t\tif (ir != null) { ict.Entry = ir; Log(string.Format(\"ICT {0} LIMIT @ {1} | SL {2} (after the deferral)\", pdi == 1 ? \"BUY\" : \"SELL\", Fmt(ictPendLim), Fmt(ictPendStop))); }\n"
    "\t\t\t\t\t}\n"
    "\t\t\t\t\telse if (!lastDeferred) { ictPendDir = 0; ict.Dir = pdi; ictExtPend = ictPendExtP; ictExpiry = ictPendExp; ArmPriceBracket(ict, pdi, ictPendStop); ParkSetup(ict, true, ictPendLim, ictPendQty); }\t// blocked by an opposite POSITION: parked, as the direct path\n"
    "\t\t\t\t}\n"
    "\t\t\t}\n"
    "\t\t\tManageParked(openMin, closeMin);\n")
rep("\t\t\tictAct[0] = ictAct[1] = false; ictTrades = 0;\n", "\t\t\tictAct[0] = ictAct[1] = false; ictTrades = 0; ictPendDir = 0;\n")
rep("\t\t\t\t\tif (pend5 != null) pend5Qty = Math.Max(1, (int)Math.Round(pend5Qty * (double)lq / hq));\n",
    "\t\t\t\t\tif (pend5 != null) pend5Qty = Math.Max(1, (int)Math.Round(pend5Qty * (double)lq / hq));\n"
    "\t\t\t\t\tif (ictPendDir != 0) ictPendQty = Math.Max(1, (int)Math.Round(ictPendQty * (double)lq / hq));\n")

# ---- 3. MSEQS: raw ORB60 short signal of the day instead of the ORB60 fill
rep("\t\tprivate int orbFirstDir, orbFirstMin = 9999;\n",
    "\t\tprivate int orbFirstDir, orbFirstMin = 9999;\t// first ORB60 fill of the day (log only since S2 2026-10-27)\n"
    "\t\tprivate int orbSigDir, orbSigMin = 9999;\t// RAW ORB60 short signal of the day: low through OR low - 1 tick on a down-trend pullback day (MSEQS gate, research wrq_build b_mseq)\n")
rep("\t\t\torbFirstDir = 0; orbFirstMin = 9999;\n", "\t\t\torbFirstDir = 0; orbFirstMin = 9999; orbSigDir = 0; orbSigMin = 9999;\n")
rep("\t\t\t\tif (o.On && inRth && etDate == rthDay && o.OrReady && closeMin >= Math.Max(630, RthOpen + o.Range)) ManageOrb(o, closeMin);\n",
    "\t\t\t\tif (o.On && inRth && etDate == rthDay && o.OrReady && closeMin >= Math.Max(630, RthOpen + o.Range)) ManageOrb(o, closeMin);\n"
    "\t\t\t// S2 2026-10-27: MSEQS is gated on the RAW ORB60 short signal (research b_mseq: the first ORB60 short of nt_v3_replica with only the\n"
    "\t\t\t// pullback filter), i.e. the first bar whose low trades through OR low - 1 tick on a down-trend pullback day inside the ORB window,\n"
    "\t\t\t// whether or not ManageOrb then skipped the day (ORBt prior-close filter, stop size) or the order filled. Needs ORB60 on with its 60-minute\n"
    "\t\t\t// range (the OR is only tracked for modules that are on); with ORB60 off MSEQS never opens, as before this change\n"
    "\t\t\tif (orbSigDir == 0 && orb.On && inRth && etDate == rthDay && orb.OrReady && pullbackDay && trendDir == -1 && closeMin >= Math.Max(630, RthOpen + orb.Range) && closeMin < 780 && Low[0] <= orb.OrL - TickSize) { orbSigDir = -1; orbSigMin = openMin; Log(\"ORB60 raw short signal (MSEQS gate) @ \" + Fmt(orb.OrL - TickSize)); }\n")
rep("\t\t\tif (mseqs.On && !mseqs.InTrade && !Working(mseqs.Entry) && orbFirstDir == -1 && openMin >= orbFirstMin && openMin >= 630 && openMin < 945)\n",
    "\t\t\tif (mseqs.On && !mseqs.InTrade && !Working(mseqs.Entry) && orbSigDir == -1 && closeMin > orbSigMin && openMin >= 630 && openMin < 945)\t// S2: raw signal; the 5-minute bar that contains it is allowed (last 1-minute bar >= signal bar)\n")
rep("\t\t\t// ---- MSEQS: mirrored momentum sequence (bullish main candle + 5 falling bearish candles below its high), only on days\n"
    "\t\t\t// where ORB60 has already entered SHORT (pullback down-trend day), 5m bar opening at/after that entry, 10:30-15:45\n",
    "\t\t\t// ---- MSEQS: mirrored momentum sequence (bullish main candle + 5 falling bearish candles below its high), only on days\n"
    "\t\t\t// where the RAW ORB60 short signal already happened (pullback down-trend day), from the 5m bar that contains it, 10:30-15:45\n")
open(P, "w", encoding="utf-8-sig").write(s)
print("patched", P, n0, "->", len(s.splitlines()), "lines")
