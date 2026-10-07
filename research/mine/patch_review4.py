"""Fourth code review (2026-10-07).
NQMaster: (1) PropPeakOverride applied when the file has no stored override (old 4-field files); (2) a file older than EvalStartDate does not
give its peak to a new eval (Eval mode); (3) an opposite MARKET entry already sent on this bar blocks like an open position (no cancel, no
deferral; research: the first trade wins) - same behaviour in backtest and live; market entries capture their Order; (4) ORB waits while a
deferred module enters; (5) MSEQ / MSEQS blocked by an opposite stop/limit order retry once on the next 1-minute bar instead of losing the
trade.
GoldMaster: stale NQMaster file (older than EvalStartDate) gives no peak; EvalMode cushion uses ReadNqProp."""
P = r"D:\NinjaTrader Strategy\{}.cs"
def patch(name, reps):
    s = open(P.format(name), encoding="utf-8").read()
    for a, b in reps:
        n = s.count(a); assert n == 1, (name, n, a[:110]); s = s.replace(a, b)
    open(P.format(name), "w", encoding="utf-8", newline="\n").write(s); print(name, "patched", len(reps))
NQ = [
# (1) + (2) prop file peak
("\t\t\t\t\tif (a.Length > 0 && double.TryParse(a[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) propPeak = Math.Max(propPeak, v);\n"
 "\t\t\t\t\tint fd = 0; double ds, bd, ov;\n"
 "\t\t\t\t\tbool fresh = a.Length >= 4 && int.TryParse(a[1], out fd) && fd >= EvalStartInt();	// older than EvalStartDate = another eval\n",
 "\t\t\t\t\tint fd = 0; double ds, bd, ov;\n"
 "\t\t\t\t\tbool fresh = a.Length >= 4 && int.TryParse(a[1], out fd) && fd >= EvalStartInt();	// older than EvalStartDate = another eval\n"
 "\t\t\t\t\tbool stalePeak = PropMode == NQMasterPropMode.Eval && a.Length >= 4 && !fresh;				// a new eval does not inherit an old peak\n"
 "\t\t\t\t\tif (!stalePeak && a.Length > 0 && double.TryParse(a[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) propPeak = Math.Max(propPeak, v);\n"),
("\t\t\tif (PropPeakOverride > 0) propPeak = Math.Abs(PropPeakOverride - storedOverride) > 0.01 ? PropPeakOverride : Math.Max(propPeak, PropPeakOverride);\n",
 "\t\t\tbool newOverride = double.IsNaN(storedOverride) || Math.Abs(PropPeakOverride - storedOverride) > 0.01;\n"
 "\t\t\tif (PropPeakOverride > 0) propPeak = newOverride ? PropPeakOverride : Math.Max(propPeak, PropPeakOverride);\n"),
# (3) opposite market entry = like an open position
("\t\t\tif ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return false;\n\t\t\tbool blocked = false;\n",
 "\t\t\tif ((d == 1 && Position.MarketPosition == MarketPosition.Short) || (d == -1 && Position.MarketPosition == MarketPosition.Long)) return false;\n"
 "\t\t\t// an opposite MARKET entry already sent (fills at the next open) counts as an open position: research keeps the first trade\n"
 "\t\t\tforeach (Mod m in mods) if (Working(m.Entry) && m.Dir == -d && m.Entry.OrderType == OrderType.Market) return false;\n\t\t\tbool blocked = false;\n"),
# capture market entries
("\t\t\tif (d == 1) EnterLong(0, tq, m.Sig); else EnterShort(0, tq, m.Sig);\n", "\t\t\tOrder tr = d == 1 ? EnterLong(0, tq, m.Sig) : EnterShort(0, tq, m.Sig);\n\t\t\tif (tr != null) m.Entry = tr;\n"),
("\t\t\tif (d == 1) EnterLong(0, cq, crt.Sig); else EnterShort(0, cq, crt.Sig);\n", "\t\t\tOrder cr = d == 1 ? EnterLong(0, cq, crt.Sig) : EnterShort(0, cq, crt.Sig);\n\t\t\tif (cr != null) crt.Entry = cr;\n"),
("\t\t\t\t\tif (d == 1) EnterLong(0, Qty(), rsi.Sig); else EnterShort(0, Qty(), rsi.Sig);\n", "\t\t\t\t\tOrder rr = d == 1 ? EnterLong(0, Qty(), rsi.Sig) : EnterShort(0, Qty(), rsi.Sig);\n\t\t\t\t\tif (rr != null) rsi.Entry = rr;\n"),
("\t\t\t\tif (e10d == 1) EnterLong(0, Qty(), eng10.Sig); else EnterShort(0, Qty(), eng10.Sig);\n", "\t\t\t\tOrder em = e10d == 1 ? EnterLong(0, Qty(), eng10.Sig) : EnterShort(0, Qty(), eng10.Sig);\n\t\t\t\tif (em != null) eng10.Entry = em;\n"),
("{ ArmPriceBracket(volb, d, Instrument.MasterInstrument.RoundToTickSize(rthOpenPx)); if (d == 1) EnterLong(0, Qty(), volb.Sig); else EnterShort(0, Qty(), volb.Sig); }",
 "{ ArmPriceBracket(volb, d, Instrument.MasterInstrument.RoundToTickSize(rthOpenPx)); Order vm = d == 1 ? EnterLong(0, Qty(), volb.Sig) : EnterShort(0, Qty(), volb.Sig); if (vm != null) volb.Entry = vm; }"),
# (4) ORB waits for a deferred module
("\t\t\tif (o.Parked || !o.Armed || o.InTrade || Working(o.Entry) || o.Trades >= 2) return;\n",
 "\t\t\tif (o.Parked || !o.Armed || o.InTrade || Working(o.Entry) || o.Trades >= 2) return;\n\t\t\tif (CurrentBars[0] <= deferUntil) return;			// a deferred module enters first\n"),
# (5) MSEQ / MSEQS: one-shot retry on the next 1-minute bar
("\t\t\t\tif (ok && DirectionAllowed(1))\n\t\t\t\t{\n\t\t\t\t\tdouble c0 = Closes[1][0]; double stop = Instrument.MasterInstrument.RoundDownToTickSize(c0 - (c0 - mainLow) * 1.75);\n"
 "\t\t\t\t\tif (stop < c0) { ArmPriceBracket(mseq, 1, stop); EnterLong(0, CtxBoost(LateQty(1, closeMin), FeatPos(1, Closes[0][0]) >= 0.9686 || FeatM30(1) >= 0.1728 || FeatRet5(1) >= 2.0674, \"MSEQ\"), mseq.Sig); Log(\"MSEQ BUY | SL \" + Fmt(stop)); }\n",
 "\t\t\t\tdouble c0m = Closes[1][0]; double stopm = Instrument.MasterInstrument.RoundDownToTickSize(c0m - (c0m - mainLow) * 1.75);\n"
 "\t\t\t\tif (ok && stopm < c0m)\n\t\t\t\t{\n"
 "\t\t\t\t\tint mq = CtxBoost(LateQty(1, closeMin), FeatPos(1, Closes[0][0]) >= 0.9686 || FeatM30(1) >= 0.1728 || FeatRet5(1) >= 2.0674, \"MSEQ\");\n"
 "\t\t\t\t\tif (!DirectionAllowed(1)) { if (lastDeferred) { pend5 = mseq; pend5Dir = 1; pend5Stop = stopm; pend5Qty = mq; pend5Bar = CurrentBars[0]; } }\n"
 "\t\t\t\t\telse { ArmPriceBracket(mseq, 1, stopm); Order mo = EnterLong(0, mq, mseq.Sig); if (mo != null) mseq.Entry = mo; Log(\"MSEQ BUY | SL \" + Fmt(stopm)); }\n"),
("\t\t\t\tif (ok && DirectionAllowed(-1))\n\t\t\t\t{\n\t\t\t\t\tdouble c0 = Closes[1][0]; double stop = Instrument.MasterInstrument.RoundToTickSize(c0 + (mainHigh - c0) * 1.75);\n"
 "\t\t\t\t\tif (stop > c0) { ArmPriceBracket(mseqs, -1, stop); EnterShort(0, LateQty(-1, closeMin), mseqs.Sig); Log(\"MSEQS SELL | SL \" + Fmt(stop)); }\n",
 "\t\t\t\tdouble c0s = Closes[1][0]; double stops = Instrument.MasterInstrument.RoundToTickSize(c0s + (mainHigh - c0s) * 1.75);\n"
 "\t\t\t\tif (ok && stops > c0s)\n\t\t\t\t{\n"
 "\t\t\t\t\tint sq = LateQty(-1, closeMin);\n"
 "\t\t\t\t\tif (!DirectionAllowed(-1)) { if (lastDeferred) { pend5 = mseqs; pend5Dir = -1; pend5Stop = stops; pend5Qty = sq; pend5Bar = CurrentBars[0]; } }\n"
 "\t\t\t\t\telse { ArmPriceBracket(mseqs, -1, stops); Order so = EnterShort(0, sq, mseqs.Sig); if (so != null) mseqs.Entry = so; Log(\"MSEQS SELL | SL \" + Fmt(stops)); }\n"),
("\t\t\tManageParked(openMin, closeMin);\n",
 "\t\t\t// MSEQ / MSEQS deferred by an opposite stop/limit order: one retry on the next 1-minute bars (research enters them at market)\n"
 "\t\t\tif (pend5 != null)\n\t\t\t{\n"
 "\t\t\t\tif (pend5.InTrade || CurrentBars[0] > pend5Bar + 2 || (pend5Dir == 1 ? Close[0] <= pend5Stop : Close[0] >= pend5Stop)) pend5 = null;\n"
 "\t\t\t\telse if (CurrentBars[0] > pend5Bar && DirectionAllowed(pend5Dir))\n\t\t\t\t{\n"
 "\t\t\t\t\tArmPriceBracket(pend5, pend5Dir, pend5Stop); Order po = pend5Dir == 1 ? EnterLong(0, pend5Qty, pend5.Sig) : EnterShort(0, pend5Qty, pend5.Sig);\n"
 "\t\t\t\t\tif (po != null) pend5.Entry = po; Log(pend5.Sig + \" entered after the deferral\"); pend5 = null;\n\t\t\t\t}\n\t\t\t}\n"
 "\t\t\tManageParked(openMin, closeMin);\n"),
("\t\tprivate bool lastDeferred; private int deferUntil = -1;", "\t\tprivate bool lastDeferred; private int deferUntil = -1;\n\t\tprivate Mod pend5; private int pend5Dir, pend5Qty, pend5Bar; private double pend5Stop;"),
("\t\t\tforeach (Mod m in mods) m.Parked = false;\n\t\t}", "\t\t\tforeach (Mod m in mods) m.Parked = false;\n\t\t\tpend5 = null;\n\t\t}"),
]
patch("NQMaster", NQ)
GOLD = [
("\t\t\t\t\tif (date < esd) { date = 0; return true; }			// written before EvalStartDate: another eval, ignore its day data\n",
 "\t\t\t\t\tif (date < esd) { date = 0; peak = double.NaN; return true; }	// written before EvalStartDate: another eval, ignore its data\n"),
("\t\t\tif (State == State.Realtime)\n\t\t\t\ttry\n\t\t\t\t{\n"
 "\t\t\t\t\tstring f = Path.Combine(Core.Globals.UserDataDir, \"nqmaster_prop_\" + Account.Name + \".txt\"); double v;\n"
 "\t\t\t\t\tif (File.Exists(f) && double.TryParse(File.ReadAllText(f).Trim().Split(';')[0], NumberStyles.Any, CultureInfo.InvariantCulture, out v)) pk = v - StartBalance;\n"
 "\t\t\t\t}\n\t\t\t\tcatch { }\n",
 "\t\t\tif (State == State.Realtime)\n\t\t\t{\n"
 "\t\t\t\tdouble fpk, fds, fbd; int fdt;\n"
 "\t\t\t\tif (ReadNqProp(out fpk, out fdt, out fds, out fbd) && !double.IsNaN(fpk)) pk = fpk - StartBalance;\n\t\t\t}\n"),
]
patch("GoldMaster", GOLD)
