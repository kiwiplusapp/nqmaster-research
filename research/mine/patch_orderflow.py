"""2026-10-09: opt-in order-flow size boost for NQMaster (research/mine/of_trades.py, of_boost.py).
Session cumulative delta (aggressor buy - sell volume since 18:00 ET / total) read from OnMarketData (Tick Replay in backtests),
oriented with the trade; >= OrderFlowCvdMin (0.015) -> size x OrderFlowBoost. Resting stop / limit entries are re-sized every
1-minute bar until they fill (research measured the delta at the fill bar). Default OFF: with it off the strategy is unchanged.
Run from the repo root: python3 research/mine/patch_orderflow.py"""
import re, sys
P = sys.argv[1] if len(sys.argv) > 1 else "NQMaster.cs"
s = open(P, encoding="utf-8").read()


def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: sys.exit(f"expected {n} x, found {c}: {old[:90]!r}")
    s = s.replace(old, new)


# ---- Mod fields
rep("\t\t\tpublic Order SeenOrd, CancelOrd; public int SeenBar = -1, CancelBar = -1;	// stale-order watchdog (PurgeStaleEntries)\n",
    "\t\t\tpublic Order SeenOrd, CancelOrd; public int SeenBar = -1, CancelBar = -1;	// stale-order watchdog (PurgeStaleEntries)\n"
    "\t\t\tpublic int OfQ0, OfWant; public Order OfChangeOrd, OfNoChange; public int OfChangeBar = -1;	// order-flow boost: size before the boost, last re-size\n")

# ---- defaults
rep("OrbPriorCloseAtr = 0.10; VolbBreakEven = true; MomAgreement = true; VolbTrendLastEntry = 1047; NewsBlackout = false; NewsTimes = \"\";\n",
    "OrbPriorCloseAtr = 0.10; VolbBreakEven = true; MomAgreement = true; VolbTrendLastEntry = 1047; NewsBlackout = false; NewsTimes = \"\";\n"
    "\t\t\t\tUseOrderFlowBoost = false; OrderFlowCvdMin = 0.015; OrderFlowBoost = 2; OrderFlowStack = false;\n")

# ---- end-of-run summary
rep("\t\t\t\tif (mods != null && totalTrades == 0 && rthDaysSeen < 25)\n",
    "\t\t\t\tif (UseOrderFlowBoost && mods != null)\n"
    "\t\t\t\t\tPrint(ofTicks == 0 ? \"NQMaster | ORDER FLOW BOOST was on but NO TICK DATA arrived, so nothing was boosted. Backtests need Tick Replay: Tools > Options > Market data > 'Show Tick Replay', then tick 'Tick Replay' in the Strategy Analyzer data series.\"\n"
    "\t\t\t\t\t\t: string.Format(\"NQMaster | order flow: {0:N0} trades read, {1} of {2} entries filled with the boost ({3:0.0}%; research Apr-Oct 2026: ~16%).\", ofTicks, ofBoosted, ofEntries, ofEntries > 0 ? 100.0 * ofBoosted / ofEntries : 0));\n"
    "\t\t\t\tif (mods != null && totalTrades == 0 && rthDaysSeen < 25)\n")

# ---- pend5 (MSEQ / MSEQS one-shot retry at market)
rep("ArmPriceBracket(pend5, pend5Dir, pend5Stop); Order po = pend5Dir == 1 ? EnterLong(0, pend5Qty, pend5.Sig) : EnterShort(0, pend5Qty, pend5.Sig);",
    "ArmPriceBracket(pend5, pend5Dir, pend5Stop); int pq = OfApply(pend5, pend5Qty, pend5Dir); Order po = pend5Dir == 1 ? EnterLong(0, pq, pend5.Sig) : EnterShort(0, pq, pend5.Sig);")
# re-size resting entries after the parked ones are handled
rep("\t\t\tManageParked(openMin, closeMin);\n\n",
    "\t\t\tManageParked(openMin, closeMin);\n\t\t\tif (UseOrderFlowBoost) OfRefresh();\n\n")

# ---- ORB
rep("\t\t\tbool through = PastLevel(d, entry);\n\t\t\to.Dir = d;\n\t\t\tOrder r = d == 1 ? (through ? EnterLong(0, oq, o.Sig) : EnterLongStopMarket(0, true, oq, entry, o.Sig)) : (through ? EnterShort(0, oq, o.Sig) : EnterShortStopMarket(0, true, oq, entry, o.Sig));",
    "\t\t\tbool through = PastLevel(d, entry);\n\t\t\to.Dir = d;\n\t\t\toq = OfApply(o, oq, d);\n\t\t\tOrder r = d == 1 ? (through ? EnterLong(0, oq, o.Sig) : EnterLongStopMarket(0, true, oq, entry, o.Sig)) : (through ? EnterShort(0, oq, o.Sig) : EnterShortStopMarket(0, true, oq, entry, o.Sig));")
# ---- VOLB market + stop
rep("{ ArmPriceBracket(volb, d, Instrument.MasterInstrument.RoundToTickSize(rthOpenPx)); Order vm = d == 1 ? EnterLong(0, Qty(), volb.Sig) : EnterShort(0, Qty(), volb.Sig); if (vm != null) volb.Entry = vm; }",
    "{ ArmPriceBracket(volb, d, Instrument.MasterInstrument.RoundToTickSize(rthOpenPx)); int vq = OfApply(volb, Qty(), d); Order vm = d == 1 ? EnterLong(0, vq, volb.Sig) : EnterShort(0, vq, volb.Sig); if (vm != null) volb.Entry = vm; }")
rep("\t\t\tOrder vr = d == 1 ? EnterLongStopMarket(0, true, Qty(), lvl, volb.Sig) : EnterShortStopMarket(0, true, Qty(), lvl, volb.Sig);",
    "\t\t\tint vsq = OfApply(volb, Qty(), d);\n\t\t\tOrder vr = d == 1 ? EnterLongStopMarket(0, true, vsq, lvl, volb.Sig) : EnterShortStopMarket(0, true, vsq, lvl, volb.Sig);")
# ---- ENG10 market + stop
rep("\t\t\t\tOrder em = e10d == 1 ? EnterLong(0, Qty(), eng10.Sig) : EnterShort(0, Qty(), eng10.Sig);",
    "\t\t\t\tint eq = OfApply(eng10, Qty(), e10d);\n\t\t\t\tOrder em = e10d == 1 ? EnterLong(0, eq, eng10.Sig) : EnterShort(0, eq, eng10.Sig);")
rep("\t\t\telse { Order er = e10d == 1 ? EnterLongStopMarket(0, true, Qty(), e10px, eng10.Sig) : EnterShortStopMarket(0, true, Qty(), e10px, eng10.Sig); if (er != null) eng10.Entry = er; }",
    "\t\t\telse { int esq = OfApply(eng10, Qty(), e10d); Order er = e10d == 1 ? EnterLongStopMarket(0, true, esq, e10px, eng10.Sig) : EnterShortStopMarket(0, true, esq, e10px, eng10.Sig); if (er != null) eng10.Entry = er; }")
# ---- clock-time modules
rep("\t\t\tOrder tr = d == 1 ? EnterLong(0, tq, m.Sig) : EnterShort(0, tq, m.Sig);",
    "\t\t\ttq = OfApply(m, tq, d);\n\t\t\tOrder tr = d == 1 ? EnterLong(0, tq, m.Sig) : EnterShort(0, tq, m.Sig);")
# ---- CRT11
rep("\t\t\tOrder cr = d == 1 ? EnterLong(0, cq, crt.Sig) : EnterShort(0, cq, crt.Sig);",
    "\t\t\tcq = OfApply(crt, cq, d);\n\t\t\tOrder cr = d == 1 ? EnterLong(0, cq, crt.Sig) : EnterShort(0, cq, crt.Sig);")
# ---- LON limit
rep("\t\t\t\tOrder lr = lon.Dir == 1 ? EnterLongLimit(0, true, Qty(), lim, lon.Sig) : EnterShortLimit(0, true, Qty(), lim, lon.Sig);",
    "\t\t\t\tint lq = OfApply(lon, Qty(), lon.Dir);\n\t\t\t\tOrder lr = lon.Dir == 1 ? EnterLongLimit(0, true, lq, lim, lon.Sig) : EnterShortLimit(0, true, lq, lim, lon.Sig);")
# ---- MSEQ / MSEQS / RSI2
rep("else { ArmPriceBracket(mseq, 1, stopm); Order mo = EnterLong(0, mq, mseq.Sig);",
    "else { ArmPriceBracket(mseq, 1, stopm); Order mo = EnterLong(0, OfApply(mseq, mq, 1), mseq.Sig);")
rep("else { ArmPriceBracket(mseqs, -1, stops); Order so = EnterShort(0, sq, mseqs.Sig);",
    "else { ArmPriceBracket(mseqs, -1, stops); Order so = EnterShort(0, OfApply(mseqs, sq, -1), mseqs.Sig);")
rep("\t\t\t\t\tOrder rr = d == 1 ? EnterLong(0, Qty(), rsi.Sig) : EnterShort(0, Qty(), rsi.Sig);",
    "\t\t\t\t\tint rq = OfApply(rsi, Qty(), d);\n\t\t\t\t\tOrder rr = d == 1 ? EnterLong(0, rq, rsi.Sig) : EnterShort(0, rq, rsi.Sig);")
# ---- ICT limit
rep("\t\t\t\tOrder ir = d == 1 ? EnterLongLimit(0, true, iq, lim, ict.Sig) : EnterShortLimit(0, true, iq, lim, ict.Sig);",
    "\t\t\t\tint iqo = OfApply(ict, iq, d);\n\t\t\t\tOrder ir = d == 1 ? EnterLongLimit(0, true, iqo, lim, ict.Sig) : EnterShortLimit(0, true, iqo, lim, ict.Sig);")
# ---- parking keeps the size BEFORE the boost (re-applied when the order is re-placed)
rep("o.ParkPx = o.ParkLimit ? e.LimitPrice : e.StopPrice; o.ParkQty = Math.Max(1, e.Quantity); Log(o.Sig + \" order parked (opposite trade)\"); }",
    "o.ParkPx = o.ParkLimit ? e.LimitPrice : e.StopPrice; o.ParkQty = Math.Max(1, UseOrderFlowBoost && o.OfQ0 > 0 ? o.OfQ0 : e.Quantity); Log(o.Sig + \" order parked (opposite trade)\"); }")
rep("\t\t\t\tOrder r = null;\n\t\t\t\tif (o.ParkLimit) r = o.Dir == 1 ? EnterLongLimit(0, true, o.ParkQty, o.ParkPx, o.Sig) : EnterShortLimit(0, true, o.ParkQty, o.ParkPx, o.Sig);",
    "\t\t\t\tOrder r = null;\n\t\t\t\tint pkq = OfApply(o, o.ParkQty, o.Dir);\n\t\t\t\tif (o.ParkLimit) r = o.Dir == 1 ? EnterLongLimit(0, true, pkq, o.ParkPx, o.Sig) : EnterShortLimit(0, true, pkq, o.ParkPx, o.Sig);")
rep("\t\t\t\telse r = o.Dir == 1 ? EnterLongStopMarket(0, true, o.ParkQty, o.ParkPx, o.Sig) : EnterShortStopMarket(0, true, o.ParkQty, o.ParkPx, o.Sig);",
    "\t\t\t\telse r = o.Dir == 1 ? EnterLongStopMarket(0, true, pkq, o.ParkPx, o.Sig) : EnterShortStopMarket(0, true, pkq, o.ParkPx, o.Sig);")

# ---- watchdog: a size change that never completes
rep("\t\t\t\telse if (age >= 2 && e.OrderType == OrderType.Market && s != OrderState.PartFilled) why = \"market entry never filled\";\n",
    "\t\t\t\telse if (age >= 2 && e.OrderType == OrderType.Market && s != OrderState.PartFilled) why = \"market entry never filled\";\n"
    "\t\t\t\telse if (m.OfChangeOrd == e && CurrentBars[0] - m.OfChangeBar >= 2 && (s == OrderState.ChangePending || s == OrderState.ChangeSubmitted)) why = \"size change never confirmed\";\n")

# ---- fill statistics
rep("\t\t\t\tif (first)\n\t\t\t\t{\n",
    "\t\t\t\tif (first)\n\t\t\t\t{\n\t\t\t\tif (UseOrderFlowBoost) { ofEntries++; if (m.OfQ0 > 0 && execution.Order.Quantity > m.OfQ0) ofBoosted++; }\n")

# ---- dashboard line
rep("\t\t\tif (zombieCount > 0) txt += string.Format(\"\\nStale orders dropped: {0} (see Output)\", zombieCount);\n",
    "\t\t\tif (zombieCount > 0) txt += string.Format(\"\\nStale orders dropped: {0} (see Output)\", zombieCount);\n"
    "\t\t\tif (UseOrderFlowBoost) txt += \"\\n\" + OfStatus();\n")

# ---- the order-flow block (before the Properties region)
BLOCK = r'''
		#region Order-flow boost
		// ---- order-flow size boost (EXPERIMENTAL, default off). research/mine/of_trades.py + of_boost.py, Databento NQ trades
		// 2026-04-01..10-08 (645 Ultra trades, real NQ futures): session cumulative delta = (aggressor buy - sell volume since 18:00 ET)
		// / session volume, oriented with the trade, measured when the entry fills. Top 20% (>= 0.015): PF 4.81 IS (Apr-Jun) / 3.22 OOS
		// (Jul-Oct) vs 1.83 / 1.13 for the rest; x2 on those (never above 2x the base size): $ +32%, PF 1.43 -> 1.54, max DD +8%.
		// NOT statistically significant (1 of ~30 order-flow cells tested, rank correlation 0.06): treat it as a test, not an edge.
		// Aggressor side from the tick stream as OrderFlowRecorder.cs: trade at/above the ask = buy, at/below the bid = sell, otherwise
		// tick rule. Historical runs need Tick Replay; a session joined mid-way (no Tick Replay history) never boosts until the next
		// 18:00 ET start. Market entries use the delta at the bar close before the fill (= research); resting stop / limit entries
		// (ORB, VOLB, ENG10, LON, ICT) are re-sized every 1-minute bar until they fill.
		private double ofBuy, ofSell, ofLastPx = double.NaN, ofBid = double.NaN, ofAsk = double.NaN;
		private int ofLastDir = 1, ofSessDay = -1, ofBoosted, ofEntries; private bool ofSessFull; private long ofMinKey = -1, ofTicks;
		protected override void OnMarketData(MarketDataEventArgs e)
		{
			if (!UseOrderFlowBoost || BarsInProgress != 0) return;
			if (e.MarketDataType == MarketDataType.Bid) { ofBid = e.Price; return; }
			if (e.MarketDataType == MarketDataType.Ask) { ofAsk = e.Price; return; }
			if (e.MarketDataType != MarketDataType.Last) return;
			long mk = e.Time.Ticks / TimeSpan.TicksPerMinute;
			if (mk != ofMinKey)
			{
				ofMinKey = mk;
				DateTime sd = ToEt(e.Time).AddHours(6);					// session date: 18:00 ET starts the next day's session
				int key = sd.Year * 10000 + sd.Month * 100 + sd.Day;
				if (key != ofSessDay) { ofSessFull = ofSessDay > 0; ofSessDay = key; ofBuy = 0; ofSell = 0; }
			}
			double b = e.Bid > 0 ? e.Bid : ofBid, a = e.Ask > 0 ? e.Ask : ofAsk, px = e.Price;
			int dir;
			if (!double.IsNaN(a) && a > 0 && px >= a) dir = 1;
			else if (!double.IsNaN(b) && b > 0 && px <= b) dir = -1;
			else if (!double.IsNaN(ofLastPx) && px > ofLastPx) dir = 1;
			else if (!double.IsNaN(ofLastPx) && px < ofLastPx) dir = -1;
			else dir = ofLastDir;
			ofLastPx = px; ofLastDir = dir; ofTicks++;
			if (dir == 1) ofBuy += e.Volume; else ofSell += e.Volume;
		}
		private double OfCvd() { return (ofSessFull && ofBuy + ofSell > 0) ? (ofBuy - ofSell) / (ofBuy + ofSell) : double.NaN; }
		private bool OfAgrees(int d) { double c = OfCvd(); return !double.IsNaN(c) && d * c >= OrderFlowCvdMin; }
		// size after the boost; q = the module's size before it (already including context / confluence / ICT x2)
		private int OfQty(int q, int d, string who)
		{
			if (!UseOrderFlowBoost || q <= 0 || noBoost || OrderFlowBoost <= 1 || Profile == NQMasterProfile.Gold || !OfAgrees(d)) return q;
			int nq = OrderFlowStack ? q * OrderFlowBoost : Math.Max(q, Qty() * OrderFlowBoost);
			if (nq != q && who != null) Log(string.Format("{0} order-flow x{1}: session delta {2:+0.000;-0.000} with the trade -> {3} contracts", who, OrderFlowBoost, d * OfCvd(), nq));
			return nq;
		}
		private int OfApply(Mod m, int q, int d) { m.OfQ0 = q; return OfQty(q, d, m.Sig); }
		// resting stop / limit entries follow the delta until they fill (one size change per 1-minute bar at most)
		private void OfRefresh()
		{
			foreach (Mod m in mods)
			{
				Order e = m.Entry;
				if (e == null || m.InTrade || m.OfQ0 <= 0 || e.Filled > 0 || zombies.Contains(e) || m.OfNoChange == e) continue;
				if (e.OrderState != OrderState.Working && e.OrderState != OrderState.Accepted) continue;
				if (m.OfChangeOrd == e && m.OfWant != e.Quantity)
				{
					if (CurrentBars[0] - m.OfChangeBar < 2) continue;		// change still in flight
					m.OfNoChange = e; Log(string.Format("{0} order-flow re-size was not applied by NinjaTrader: this order keeps {1} contracts", m.Sig, e.Quantity)); continue;
				}
				if (e.OrderType != OrderType.StopMarket && e.OrderType != OrderType.Limit) continue;
				int d = e.OrderAction == OrderAction.Buy ? 1 : -1;
				int want = OfQty(m.OfQ0, d, null);
				if (want == e.Quantity) continue;
				int was = e.Quantity;
				try { m.OfChangeOrd = e; m.OfChangeBar = CurrentBars[0]; m.OfWant = want; ChangeOrder(e, want, e.LimitPrice, e.StopPrice); Log(string.Format("{0} resting entry re-sized {1} -> {2} (session delta {3:+0.000;-0.000} with the trade)", m.Sig, was, want, d * OfCvd())); }
				catch (Exception ex) { m.OfNoChange = e; Log(m.Sig + " order-flow re-size failed: " + ex.Message); }
			}
		}
		private string OfStatus()
		{
			if (ofTicks == 0) return "Order flow boost: NO TICK DATA (backtest: enable Tick Replay)";
			if (!ofSessFull) return "Order flow boost: waiting for the next 18:00 ET session (joined mid-session)";
			double c = OfCvd();
			return string.Format("Order flow: session delta {0:+0.000;-0.000} ({1:N0} contracts) | x{2} for {3} >= {4:0.000} | boosted {5}/{6}",
				c, ofBuy + ofSell, OrderFlowBoost, double.IsNaN(c) ? "-" : c >= OrderFlowCvdMin ? "LONGS" : c <= -OrderFlowCvdMin ? "SHORTS" : "none", OrderFlowCvdMin, ofBoosted, ofEntries);
		}
		#endregion

		#region Properties
'''
rep("\n\t\t#region Properties\n", BLOCK)

# ---- properties (group 09)
rep("\t\t#endregion\n\t}\n}",
    "\t\t[NinjaScriptProperty][Display(Name = \"Order-flow boost on (EXPERIMENTAL; backtests need Tick Replay)\", Order = 1, GroupName = \"09. Order flow (experimental)\")] public bool UseOrderFlowBoost { get; set; }\n"
    "\t\t[NinjaScriptProperty][Range(0.0, 1.0)][Display(Name = \"Session delta with the trade >= (0.015 = research top 20%)\", Order = 2, GroupName = \"09. Order flow (experimental)\")] public double OrderFlowCvdMin { get; set; }\n"
    "\t\t[NinjaScriptProperty][Range(1, 5)][Display(Name = \"Size multiplier when the delta agrees\", Order = 3, GroupName = \"09. Order flow (experimental)\")] public int OrderFlowBoost { get; set; }\n"
    "\t\t[NinjaScriptProperty][Display(Name = \"Stack on other x2 boosts (off = never above multiplier x base size)\", Order = 4, GroupName = \"09. Order flow (experimental)\")] public bool OrderFlowStack { get; set; }\n"
    "\t\t#endregion\n\t}\n}")

open(P, "w", encoding="utf-8").write(s)
print("patched", P)
