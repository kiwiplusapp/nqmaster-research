"""Patch NQMaster.cs: prop-account cushion gating (research/mine/acct_policy*.py, acct_final.py).
Cushion = account equity - liquidation threshold (EOD trailing $2,000 that locks at start+100 once the EOD peak reaches start+2,100).
Eval   : cushion >= EvalCushionFull -> FULL (profile as is), else SAFE; own account daily stop EvalDailyStop ($700).
Funded : cushion <  FundedCushionSafe -> SAFE, else NO-BOOST (never x2).
SAFE     = no x2 sizing (context / confluence / ICT multiplier / VW13 double) and VOLB, LON, MOM1030, MOM11 off.
NO-BOOST = every module of the profile, no x2 sizing. Skip rules (ON07 context, REV06 after LON) stay active."""
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b, cnt=1):
    global s
    n = s.count(a); assert n == cnt, (n, a[:90]); s = s.replace(a, b)
rep("public enum NQMasterProfile { MaxSharpe, WinRate70, Gold, Custom, MaxTrades, MaxPlus, MaxPlus2, Ultra, WR70Plus, Core }",
    "public enum NQMasterProfile { MaxSharpe, WinRate70, Gold, Custom, MaxTrades, MaxPlus, MaxPlus2, Ultra, WR70Plus, Core }\n\tpublic enum NQMasterPropMode { Off, Eval, Funded }")
rep("\t\t\tpublic bool PriceTarget;\n", "\t\t\tpublic bool PriceTarget;\n\t\t\tpublic bool BaseOn;\n")
# defaults
rep("EdgeMonitor = true; EdgeMonitorPause = false; EdgeMonitorStart = \"2026-10-05\"; EdgeK = 0; EdgeH = 0;",
    "EdgeMonitor = true; EdgeMonitorPause = false; EdgeMonitorStart = \"2026-10-05\"; EdgeK = 0; EdgeH = 0;\n\t\t\t\tPropMode = NQMasterPropMode.Off; PropTrailingDD = 2000; EvalCushionFull = 900; EvalDailyStop = 700; FundedCushionSafe = 1500; FundedPayoutAt = 6000;\n\t\t\t\tPropPeakOverride = 0; PropThresholdOverride = 0; AtrStartMax = 1.15;")
rep("\t\t\t\tBuildModules();\n\t\t\t\tEdgeParams();\n", "\t\t\t\tBuildModules();\n\t\t\t\tforeach (Mod m in mods) m.BaseOn = m.On;\n\t\t\t\tEdgeParams();\n")
rep("\t\t\t\teqPeak = netPnl;	// adaptive size measures the drawdown from the moment the strategy goes live\n",
    "\t\t\t\teqPeak = netPnl;	// adaptive size measures the drawdown from the moment the strategy goes live\n\t\t\t\tPropGoLive();\n")
rep("\t\t\t\tNewSession();\n\t\t\t\tsessHi = High[0]; sessLo = Low[0];", "\t\t\t\tNewSession();\n\t\t\t\tPropSessionStart();\n\t\t\t\tsessHi = High[0]; sessLo = Low[0];")
rep("\t\t\tDailyLossCheck();\n", "\t\t\tDailyLossCheck();\n\t\t\tPropDailyCheck();\n")
# boosts off outside FULL
rep("\t\t\tif (!CtxOn || !cond) return q;\n", "\t\t\tif (!CtxOn || !cond || noBoost) return q;\n")
rep("if (RulesOn && m11Dir == -d && onSum * d > 0 && entryMin > 660) { q *= 2;", "if (RulesOn && !noBoost && m11Dir == -d && onSum * d > 0 && entryMin > 660) { q *= 2;")
rep("? IctMultiplier : 1);", "? (noBoost ? 1 : IctMultiplier) : 1);")
rep("if (m.DoubleDist > 0 && Math.Abs(Close[0] - reference) >= m.DoubleDist * atrDaily) tq = 2 * Qty();", "if (m.DoubleDist > 0 && !noBoost && Math.Abs(Close[0] - reference) >= m.DoubleDist * atrDaily) tq = 2 * Qty();")
rep("\t\t\tif (dayStopped) { status = \"daily loss limit\"; return false; }\n", "\t\t\tif (dayStopped) { status = \"daily loss limit\"; return false; }\n\t\t\tif (propStopped) { status = \"prop daily stop\"; return false; }\n")
prop = r'''
		// ---- prop-account cushion gating (research/mine/acct_final.py; Lucid Flex 50K, 1 contract per module, MNQ + MGC 2024-26)
		// Eval  : FULL while the cushion over the liquidation threshold is >= EvalCushionFull ($900), SAFE below; own daily stop $700.
		//         Pass 88.9% vs 78.0% (busts 11% vs 22%) when evals are also started only with ATR < 1.15 x its 60-day median.
		// Funded: SAFE while cushion < FundedCushionSafe ($1,500), NO-BOOST above; request payouts at >= $6,000 profit.
		//         Accounts lost within 12 months 25% vs 44%; cash per account ~$6.8k vs ~$5.6k.
		private enum GateMode { Full, NoBoost, Safe }
		private GateMode gate = GateMode.Full; private bool noBoost, propStopped;
		private double propPeak = double.NaN, propThr = double.NaN, propCushion = double.NaN, propDayStart = double.NaN, atrStartRatio = double.NaN;
		private bool propLive;
		private string PropFile { get { try { return Path.Combine(Core.Globals.UserDataDir, "nqmaster_prop_" + (Account != null ? Account.Name : "acct") + ".txt"); } catch { return null; } } }
		private double PropEquity()
		{
			if (State == State.Realtime) return Account.Get(AccountItem.CashValue, Currency.UsDollar);
			return StartBalance + netPnl;
		}
		private void PropGoLive()
		{
			if (PropMode == NQMasterPropMode.Off) return;
			propLive = true; propPeak = Math.Max(StartBalance, PropEquity());
			try { string f = PropFile; if (f != null && File.Exists(f)) { double v; if (double.TryParse(File.ReadAllText(f).Trim(), NumberStyles.Any, CultureInfo.InvariantCulture, out v)) propPeak = Math.Max(propPeak, v); } } catch { }
			if (PropPeakOverride > 0) propPeak = PropPeakOverride;
			PropSessionStart();
		}
		private void PropSessionStart()
		{
			gate = GateMode.Full; noBoost = false; propStopped = false;
			if (PropMode != NQMasterPropMode.Off)
			{
				double eq = PropEquity(); propDayStart = eq;
				if (double.IsNaN(propPeak)) propPeak = Math.Max(StartBalance, PropPeakOverride > 0 ? PropPeakOverride : eq);
				if (eq > propPeak) { propPeak = eq; if (propLive) try { File.WriteAllText(PropFile, propPeak.ToString("0.00", CultureInfo.InvariantCulture)); } catch { } }
				propThr = propPeak >= StartBalance + PropTrailingDD + 100 ? StartBalance + 100 : propPeak - PropTrailingDD;
				if (PropThresholdOverride > 0) propThr = PropThresholdOverride;
				propCushion = eq - propThr;
				if (PropMode == NQMasterPropMode.Eval) gate = propCushion >= EvalCushionFull ? GateMode.Full : GateMode.Safe;
				else gate = propCushion >= FundedCushionSafe ? GateMode.NoBoost : GateMode.Safe;
				noBoost = gate != GateMode.Full;
			}
			foreach (Mod m in mods)
				m.On = m.BaseOn && !(gate == GateMode.Safe && (m.Sig == "VOLB" || m.Sig == "LON" || m.Sig == "MOM1030" || m.Sig == "MOM11"));
			atrStartRatio = double.NaN;
			if (atrHist != null && atrHist.Count >= 20 && !double.IsNaN(todayAtr) && todayAtr > 0)
			{
				List<double> srt = new List<double>(atrHist.Count > 60 ? atrHist.GetRange(atrHist.Count - 60, 60) : atrHist); srt.Sort(); int nn = srt.Count;
				double med = nn % 2 == 1 ? srt[nn / 2] : 0.5 * (srt[nn / 2 - 1] + srt[nn / 2]); atrStartRatio = med > 0 ? todayAtr / med : double.NaN;
			}
			if (PropMode != NQMasterPropMode.Off) Log(string.Format("PROP {0}: equity {1:0} | threshold {2:0} | cushion {3:0} -> {4}", PropMode, PropEquity(), propThr, propCushion, gate));
		}
		private void PropDailyCheck()
		{
			if (PropMode != NQMasterPropMode.Eval || EvalDailyStop <= 0 || propStopped || double.IsNaN(propDayStart)) return;
			double now = State == State.Realtime ? Account.Get(AccountItem.CashValue, Currency.UsDollar) + Account.Get(AccountItem.UnrealizedProfitLoss, Currency.UsDollar)
				: StartBalance + netPnl + (Position.MarketPosition == MarketPosition.Flat ? 0 : Position.GetUnrealizedProfitLoss(PerformanceUnit.Currency, Closes[0][0]));
			if (now - propDayStart <= -EvalDailyStop) { propStopped = true; FlattenAll("prop daily stop"); Log(string.Format("PROP DAILY STOP: {0:0} today", now - propDayStart)); }
		}
'''
rep("\t\tprivate bool lastDeferred;\n", prop + "\n\t\tprivate bool lastDeferred;\n")
rep('''			if (EdgeMonitor && !double.IsNaN(edgeH) && edgeH > 0) txt += string.Format("\\nEdge monitor: {0:0}% of alarm ({1} days){2}", 100 * edgeS / edgeH, edgeDays, edgeAlarm ? " | ALARM" : "");''',
    '''			if (EdgeMonitor && !double.IsNaN(edgeH) && edgeH > 0) txt += string.Format("\\nEdge monitor: {0:0}% of alarm ({1} days){2}", 100 * edgeS / edgeH, edgeDays, edgeAlarm ? " | ALARM" : "");
			if (PropMode != NQMasterPropMode.Off) txt += string.Format("\\nProp {0}: mode {1} | cushion ${2:0} (threshold ${3:0})", PropMode, gate, propCushion, propThr);
			if (PropMode == NQMasterPropMode.Funded && PropEquity() - StartBalance >= FundedPayoutAt) txt += string.Format("\\nPAYOUT: profit >= ${0:0} -> request it", FundedPayoutAt);
			if (!double.IsNaN(atrStartRatio)) txt += string.Format("\\nATR ratio {0:0.00}: {1}", atrStartRatio, atrStartRatio < AtrStartMax ? "OK to start a new eval" : "do NOT start a new eval today");''')
rep('''		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "h (0 = profile calibration)", Order = 5, GroupName = "06. Edge monitor")] public double EdgeH { get; set; }''',
    '''		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "h (0 = profile calibration)", Order = 5, GroupName = "06. Edge monitor")] public double EdgeH { get; set; }
		[NinjaScriptProperty][Display(Name = "Prop mode (Off / Eval / Funded)", Order = 1, GroupName = "07. Prop account (cushion gating)")] public NQMasterPropMode PropMode { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Trailing drawdown $ (EOD, locks at start+100)", Order = 2, GroupName = "07. Prop account (cushion gating)")] public double PropTrailingDD { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: full mode when cushion >= $", Order = 3, GroupName = "07. Prop account (cushion gating)")] public double EvalCushionFull { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Eval: account daily stop $ (0 = off)", Order = 4, GroupName = "07. Prop account (cushion gating)")] public double EvalDailyStop { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Funded: safe mode when cushion < $", Order = 5, GroupName = "07. Prop account (cushion gating)")] public double FundedCushionSafe { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Funded: request payout at profit >= $", Order = 6, GroupName = "07. Prop account (cushion gating)")] public double FundedPayoutAt { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Highest end-of-day balance so far $ (0 = auto)", Order = 7, GroupName = "07. Prop account (cushion gating)")] public double PropPeakOverride { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Liquidation threshold $ override (0 = auto)", Order = 8, GroupName = "07. Prop account (cushion gating)")] public double PropThresholdOverride { get; set; }
		[NinjaScriptProperty][Range(0, 10)][Display(Name = "Start new evals only when ATR / 60-day median <", Order = 9, GroupName = "07. Prop account (cushion gating)")] public double AtrStartMax { get; set; }''')
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
