"""Third code review (2026-10-07) of the parking logic and prop-file handling.
NQMaster: (1) a parked order is not re-placed while a deferred module is waiting to enter (it parked that order) -> counter-trend MOM11 /
MOM1130 / LATEFH entries are no longer lost; (2) PropPeakOverride is applied once (stored as the 5th field of the prop file), later
restarts keep max(file peak, override); (3) best day recovered only from the immediately previous session, file day start / best day
ignored when older than EvalStartDate (new eval on a reused account name); (4) ORB does not re-arm while parked; (5) Enter* return
values captured (order references fresh in the same bar); (6) a level traded while the cancel is pending is latched (ParkHit);
(7) ORB / ENG10 / LON / ICT setups blocked by an opposite POSITION at placement are parked instead of dropped (research places them and
only drops a fill against the open opposite position).
GoldMaster: the NQMaster file's best day / day start ignored when older than EvalStartDate."""
P = r"D:\NinjaTrader Strategy\{}.cs"
def patch(name, reps):
    s = open(P.format(name), encoding="utf-8").read()
    for a, b in reps:
        n = s.count(a); assert n == 1, (name, n, a[:110]); s = s.replace(a, b)
    open(P.format(name), "w", encoding="utf-8", newline="\n").write(s); print(name, "patched", len(reps))
NQ = [
("\t\t\tpublic bool Parked, ParkLimit; public double ParkPx; public int ParkQty;", "\t\t\tpublic bool Parked, ParkLimit, ParkHit; public double ParkPx; public int ParkQty;"),
# (4) ORB re-arm guard; (7) ORB parked when an opposite position blocks it; (5) capture order
("\t\t\tif (!o.Armed && !o.InTrade && !Working(o.Entry) && o.Trades > 0", "\t\t\tif (!o.Parked && !o.Armed && !o.InTrade && !Working(o.Entry) && o.Trades > 0"),
("\t\t\to.Armed = false;\n\t\t\tif (!DirectionAllowed(d)) { if (lastDeferred) o.Armed = true; return; }\n"
 "\t\t\tSetStopLoss(o.Sig, CalculationMode.Ticks, st, false);\n\t\t\tSetProfitTarget(o.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(st * o.R)));\n"
 "\t\t\tbool through = PastLevel(d, entry);\n\t\t\to.Dir = d;\n"
 "\t\t\tbool oc = o == orb ? (FeatGap(d) >= 0.3311 || FeatRet5(d) >= 1.8118 || atrRatio >= 1.2615) : (FeatVw(d, entry) < 0.1231 || FeatOpen(d, entry) >= 0.5458);\n"
 "\t\t\tint oq = CtxBoost(Qty(), oc, o.Sig);\n"
 "\t\t\tif (d == 1) { if (through) EnterLong(0, oq, o.Sig); else EnterLongStopMarket(0, true, oq, entry, o.Sig); }\n"
 "\t\t\telse { if (through) EnterShort(0, oq, o.Sig); else EnterShortStopMarket(0, true, oq, entry, o.Sig); }\n",
 "\t\t\to.Armed = false;\n"
 "\t\t\tSetStopLoss(o.Sig, CalculationMode.Ticks, st, false);\n\t\t\tSetProfitTarget(o.Sig, CalculationMode.Ticks, Math.Max(1, (int)Math.Round(st * o.R)));\n"
 "\t\t\tbool oc = o == orb ? (FeatGap(d) >= 0.3311 || FeatRet5(d) >= 1.8118 || atrRatio >= 1.2615) : (FeatVw(d, entry) < 0.1231 || FeatOpen(d, entry) >= 0.5458);\n"
 "\t\t\tint oq = CtxBoost(Qty(), oc, o.Sig);\n"
 "\t\t\tif (!DirectionAllowed(d)) { if (lastDeferred) o.Armed = true; else if (!PastLevel(d, entry)) { o.Dir = d; ParkSetup(o, false, Instrument.MasterInstrument.RoundToTickSize(entry), oq); } return; }\n"
 "\t\t\tbool through = PastLevel(d, entry);\n\t\t\to.Dir = d;\n"
 "\t\t\tOrder r = d == 1 ? (through ? EnterLong(0, oq, o.Sig) : EnterLongStopMarket(0, true, oq, entry, o.Sig)) : (through ? EnterShort(0, oq, o.Sig) : EnterShortStopMarket(0, true, oq, entry, o.Sig));\n"
 "\t\t\tif (r != null) o.Entry = r;\n"),
("\t\t\tif (d == 1) EnterLongStopMarket(0, true, Qty(), lvl, volb.Sig); else EnterShortStopMarket(0, true, Qty(), lvl, volb.Sig);\n",
 "\t\t\tOrder vr = d == 1 ? EnterLongStopMarket(0, true, Qty(), lvl, volb.Sig) : EnterShortStopMarket(0, true, Qty(), lvl, volb.Sig);\n\t\t\tif (vr != null) volb.Entry = vr;\n"),
# (7) ENG10 parked when an opposite position blocks it; (5)
("\t\t\tif (!DirectionAllowed(e10d)) { if (!lastDeferred) eng10Retry = false; return; }\n",
 "\t\t\tif (!DirectionAllowed(e10d))\n\t\t\t{\n"
 "\t\t\t\tif (!lastDeferred) { eng10Retry = false; if (!PastLevel(e10d, e10px)) { ArmPriceBracket(eng10, e10d, e10sl); ParkSetup(eng10, false, e10px, Qty()); } }\n"
 "\t\t\t\treturn;\n\t\t\t}\n"),
("\t\t\telse if (e10d == 1) EnterLongStopMarket(0, true, Qty(), e10px, eng10.Sig); else EnterShortStopMarket(0, true, Qty(), e10px, eng10.Sig);\n",
 "\t\t\telse { Order er = e10d == 1 ? EnterLongStopMarket(0, true, Qty(), e10px, eng10.Sig) : EnterShortStopMarket(0, true, Qty(), e10px, eng10.Sig); if (er != null) eng10.Entry = er; }\n"),
# (7) LON
("\t\t\t\tif (risk <= 0 || risk > 0.25 * atrDaily || !DirectionAllowed(lon.Dir)) { lonStage = 3; return; }\n\t\t\t\tArmPriceBracket(lon, lon.Dir, stop);\n"
 "\t\t\t\tif (lon.Dir == 1) EnterLongLimit(0, true, Qty(), lim, lon.Sig); else EnterShortLimit(0, true, Qty(), lim, lon.Sig);\n",
 "\t\t\t\tif (risk <= 0 || risk > 0.25 * atrDaily) { lonStage = 3; return; }\n"
 "\t\t\t\tif (!DirectionAllowed(lon.Dir)) { lonStage = 3; ArmPriceBracket(lon, lon.Dir, stop); ParkSetup(lon, true, lim, Qty()); return; }\n"
 "\t\t\t\tArmPriceBracket(lon, lon.Dir, stop);\n"
 "\t\t\t\tOrder lr = lon.Dir == 1 ? EnterLongLimit(0, true, Qty(), lim, lon.Sig) : EnterShortLimit(0, true, Qty(), lim, lon.Sig);\n\t\t\t\tif (lr != null) lon.Entry = lr;\n"),
# (7) ICT
("\t\t\t\tif (!DirectionAllowed(d)) { if (lastDeferred) ictAct[s] = true; continue; }\n"
 "\t\t\t\tict.Dir = d; ictExtPend = ictExt[s]; ictExpiry = CurrentBars[1] + 20;\n\t\t\t\tArmPriceBracket(ict, d, stop);\n"
 "\t\t\t\tint iq = Qty() * ((Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Core || Profile == NQMasterProfile.Custom) ? (noBoost ? 1 : IctMultiplier) : 1);\n"
 "\t\t\t\tif (d == 1) EnterLongLimit(0, true, iq, lim, ict.Sig); else EnterShortLimit(0, true, iq, lim, ict.Sig);\n",
 "\t\t\t\tint iq = Qty() * ((Profile == NQMasterProfile.MaxPlus || Profile == NQMasterProfile.MaxPlus2 || Profile == NQMasterProfile.Ultra || Profile == NQMasterProfile.WR70Plus || Profile == NQMasterProfile.Core || Profile == NQMasterProfile.Custom) ? (noBoost ? 1 : IctMultiplier) : 1);\n"
 "\t\t\t\tif (!DirectionAllowed(d))\n\t\t\t\t{\n\t\t\t\t\tif (lastDeferred) ictAct[s] = true;\n"
 "\t\t\t\t\telse { ict.Dir = d; ictExtPend = ictExt[s]; ictExpiry = CurrentBars[1] + 20; ArmPriceBracket(ict, d, stop); ParkSetup(ict, true, lim, iq); }\n"
 "\t\t\t\t\tcontinue;\n\t\t\t\t}\n"
 "\t\t\t\tict.Dir = d; ictExtPend = ictExt[s]; ictExpiry = CurrentBars[1] + 20;\n\t\t\t\tArmPriceBracket(ict, d, stop);\n"
 "\t\t\t\tOrder ir = d == 1 ? EnterLongLimit(0, true, iq, lim, ict.Sig) : EnterShortLimit(0, true, iq, lim, ict.Sig);\n\t\t\t\tif (ir != null) ict.Entry = ir;\n"),
# parking helpers: ParkSetup, latched hit, deferral gate, captured orders
("\t\t\t{ o.Parked = true; o.ParkLimit = e.OrderType == OrderType.Limit; o.ParkPx = o.ParkLimit ? e.LimitPrice : e.StopPrice; o.ParkQty = Math.Max(1, e.Quantity); Log(o.Sig + \" order parked (opposite trade)\"); }\n",
 "\t\t\t{ o.Parked = true; o.ParkHit = false; o.ParkLimit = e.OrderType == OrderType.Limit; o.ParkPx = o.ParkLimit ? e.LimitPrice : e.StopPrice; o.ParkQty = Math.Max(1, e.Quantity); Log(o.Sig + \" order parked (opposite trade)\"); }\n"),
("\t\tprivate bool OppBusy(int d, Mod self)\n",
 "\t\t// a setup blocked by an opposite POSITION at placement time: kept and placed when free (research drops only a fill against it)\n"
 "\t\tprivate void ParkSetup(Mod o, bool limit, double px, int qty)\n\t\t{\n"
 "\t\t\to.Parked = true; o.ParkHit = false; o.ParkLimit = limit; o.ParkPx = px; o.ParkQty = Math.Max(1, qty);\n"
 "\t\t\tLog(string.Format(\"{0} setup parked @ {1} (opposite position open)\", o.Sig, Fmt(px)));\n\t\t}\n"
 "\t\tprivate bool OppBusy(int d, Mod self)\n"),
("\t\t\t\tif (!o.Parked || Working(o.Entry)) continue;					// the cancel is still pending\n"
 "\t\t\t\tbool hit = o.ParkLimit ? (o.Dir == 1 ? Low[0] <= o.ParkPx : High[0] >= o.ParkPx) : (o.Dir == 1 ? High[0] >= o.ParkPx : Low[0] <= o.ParkPx);\n"
 "\t\t\t\tif (o.InTrade || hit || ParkExpired(o, openMin, closeMin)) { o.Parked = false; Log(o.Sig + \" parked order dropped\" + (hit ? \" (level traded while blocked)\" : \"\")); continue; }\n"
 "\t\t\t\tif (OppBusy(o.Dir, o)) continue;\n\t\t\t\to.Parked = false;\n"
 "\t\t\t\tif (o.ParkLimit) { if (o.Dir == 1) EnterLongLimit(0, true, o.ParkQty, o.ParkPx, o.Sig); else EnterShortLimit(0, true, o.ParkQty, o.ParkPx, o.Sig); }\n"
 "\t\t\t\telse if (PastLevel(o.Dir, o.ParkPx)) { Log(o.Sig + \" parked order dropped (level passed)\"); continue; }\n"
 "\t\t\t\telse if (o.Dir == 1) EnterLongStopMarket(0, true, o.ParkQty, o.ParkPx, o.Sig); else EnterShortStopMarket(0, true, o.ParkQty, o.ParkPx, o.Sig);\n",
 "\t\t\t\tif (!o.Parked) continue;\n"
 "\t\t\t\tif (o.ParkLimit ? (o.Dir == 1 ? Low[0] <= o.ParkPx : High[0] >= o.ParkPx) : (o.Dir == 1 ? High[0] >= o.ParkPx : Low[0] <= o.ParkPx)) o.ParkHit = true;	// latched\n"
 "\t\t\t\tif (Working(o.Entry)) continue;									// the cancel is still pending\n"
 "\t\t\t\tif (o.InTrade || o.ParkHit || ParkExpired(o, openMin, closeMin)) { o.Parked = false; Log(o.Sig + \" parked order dropped\" + (o.ParkHit ? \" (level traded while blocked)\" : \"\")); continue; }\n"
 "\t\t\t\tif (CurrentBars[0] <= deferUntil) continue;						// the module that parked it enters first\n"
 "\t\t\t\tif (OppBusy(o.Dir, o)) continue;\n\t\t\t\to.Parked = false;\n"
 "\t\t\t\tOrder r = null;\n"
 "\t\t\t\tif (o.ParkLimit) r = o.Dir == 1 ? EnterLongLimit(0, true, o.ParkQty, o.ParkPx, o.Sig) : EnterShortLimit(0, true, o.ParkQty, o.ParkPx, o.Sig);\n"
 "\t\t\t\telse if (PastLevel(o.Dir, o.ParkPx)) { Log(o.Sig + \" parked order dropped (level passed)\"); continue; }\n"
 "\t\t\t\telse r = o.Dir == 1 ? EnterLongStopMarket(0, true, o.ParkQty, o.ParkPx, o.Sig) : EnterShortStopMarket(0, true, o.ParkQty, o.ParkPx, o.Sig);\n"
 "\t\t\t\tif (r != null) o.Entry = r;\n"),
# (2) PropPeakOverride applied once (5th field); (3) best day only from the previous session, stale files ignored
("\"{0:0.00};{1};{2:0.00};{3:0.00}\", propPeak, tradeDay, propDayStart, propBestDay)", "\"{0:0.00};{1};{2:0.00};{3:0.00};{4:0.00}\", propPeak, tradeDay, propDayStart, propBestDay, PropPeakOverride)"),
("\t\t\t\t\tint fd; double ds, bd;\n"
 "\t\t\t\t\tif (a.Length >= 4 && int.TryParse(a[1], out fd) && double.TryParse(a[2], NumberStyles.Any, CultureInfo.InvariantCulture, out ds))\n"
 "\t\t\t\t\t{ if (fd == today) propDayStart = ds; else if (fd < today) savedPrevDayStart = ds; }\n"
 "\t\t\t\t\tif (a.Length >= 4 && double.TryParse(a[3], NumberStyles.Any, CultureInfo.InvariantCulture, out bd)) propBestDay = Math.Max(propBestDay, bd);\n",
 "\t\t\t\t\tint fd = 0; double ds, bd, ov;\n"
 "\t\t\t\t\tbool fresh = a.Length >= 4 && int.TryParse(a[1], out fd) && fd >= EvalStartInt();	// older than EvalStartDate = another eval\n"
 "\t\t\t\t\tif (fresh && double.TryParse(a[2], NumberStyles.Any, CultureInfo.InvariantCulture, out ds))\n"
 "\t\t\t\t\t{ if (fd == today) propDayStart = ds; else if (fd == prevSessDay) savedPrevDayStart = ds; }\n"
 "\t\t\t\t\tif (fresh && double.TryParse(a[3], NumberStyles.Any, CultureInfo.InvariantCulture, out bd)) propBestDay = Math.Max(propBestDay, bd);\n"
 "\t\t\t\t\tif (a.Length >= 5 && double.TryParse(a[4], NumberStyles.Any, CultureInfo.InvariantCulture, out ov)) storedOverride = ov;\n"),
("\t\t\tif (PropPeakOverride > 0) propPeak = PropPeakOverride;		// manual correction (e.g. a stale file after an account reset)\n",
 "\t\t\t// manual correction (e.g. a stale file after an account reset): applied once; later restarts keep the higher saved peak\n"
 "\t\t\tif (PropPeakOverride > 0) propPeak = Math.Abs(PropPeakOverride - storedOverride) > 0.01 ? PropPeakOverride : Math.Max(propPeak, PropPeakOverride);\n"),
("\t\tprivate bool propLive; private double propBestDay = 0, savedPrevDayStart = double.NaN; private int propRestoredDay = -1;",
 "\t\tprivate bool propLive; private double propBestDay = 0, savedPrevDayStart = double.NaN, storedOverride = double.NaN; private int propRestoredDay = -1, prevSessDay, curSessDay;\n"
 "\t\tprivate int EvalStartInt() { DateTime st; return DateTime.TryParseExact(EvalStartDate ?? \"\", \"yyyy-MM-dd\", CultureInfo.InvariantCulture, DateTimeStyles.None, out st) ? st.Year * 10000 + st.Month * 100 + st.Day : 0; }"),
("\t\t\t\tDateTime tradeDay = etOpen.Hour >= 18 ? etOpen.Date.AddDays(1) : etOpen.Date;\n",
 "\t\t\t\tDateTime tradeDay = etOpen.Hour >= 18 ? etOpen.Date.AddDays(1) : etOpen.Date;\n\t\t\t\tprevSessDay = curSessDay; curSessDay = tradeDay.Year * 10000 + tradeDay.Month * 100 + tradeDay.Day;\n"),
]
patch("NQMaster", NQ)
GOLD = [
("\t\t\tpeak = dayStart = bestDay = double.NaN; date = 0;\n",
 "\t\t\tpeak = dayStart = bestDay = double.NaN; date = 0;\n\t\t\tDateTime es; int esd = DateTime.TryParseExact(EvalStartDate ?? \"\", \"yyyy-MM-dd\", CultureInfo.InvariantCulture, DateTimeStyles.None, out es) ? es.Year * 10000 + es.Month * 100 + es.Day : 0;\n"),
("\t\t\t\t\tint.TryParse(a[1], out date);\n",
 "\t\t\t\t\tint.TryParse(a[1], out date);\n\t\t\t\t\tif (date < esd) { date = 0; return true; }			// written before EvalStartDate: another eval, ignore its day data\n"),
]
patch("GoldMaster", GOLD)
