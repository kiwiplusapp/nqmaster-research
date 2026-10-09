"""2026-10-09: automatic funded step-up (research/mine/final3y_acct.py, MyFundedFutures Rapid EOD 50K: 1 contract until the cushion
over the EOD-trailing threshold is >= $3,000, then 2; withdraw down to start + $6,100). NQMaster uses its prop cushion (day start);
GoldMaster computes the same cushion (realtime: account cash + NQMaster's prop-file peak; historical: its own P&L)."""
import sys
R = sys.argv[1] if len(sys.argv) > 1 else "."
def sub(s, a, b, n=1):
    assert s.count(a) == n, (a[:70], s.count(a)); return s.replace(a, b)

p = R + "/NQMaster.cs"; s = open(p, encoding="utf-8").read()
s = sub(s, "EvalSafeSet = NQMasterSafeSet.Estable; FundedProfitStop = 0;",
        "EvalSafeSet = NQMasterSafeSet.Estable; FundedProfitStop = 0; FundedStepUpCushion = 0; FundedStepUpContracts = 2;")
s = sub(s, """			if (!AdaptiveSize) return Contracts;
			return (eqPeak - netPnl) > SizeDownDrawdown ? SizeLow : SizeHigh;""",
"""			if (StepUpOn) return FundedStepUpContracts;
			if (!AdaptiveSize) return Contracts;
			return (eqPeak - netPnl) > SizeDownDrawdown ? SizeLow : SizeHigh;""")
s = sub(s, """		private int Qty()
		{
			if (EvalMode)""",
"""		// ---- funded step-up (research/mine/final3y_acct.py, MyFundedFutures Rapid EOD 50K, Ultra + gold Robust, REAL 2024-26): 1 contract
		// until the cushion over the EOD-trailing threshold (day start) is >= FundedStepUpCushion ($3,000 = balance >= start + $3,100 once
		// the threshold has locked at start + $100), then FundedStepUpContracts (2); back to Contracts below. Withdraw down to start + $6,100.
		// $ per account per month (history / +1 tick / resampled): 3,888 / 3,592 / 3,336 vs 2,137 / 1,984 / 2,012 at 1 contract.
		private bool StepUpOn { get { return PropMode == NQMasterPropMode.Funded && FundedStepUpCushion > 0 && !double.IsNaN(propCushion) && propCushion >= FundedStepUpCushion; } }
		private int Qty()
		{
			if (EvalMode)""")
s = sub(s, """			if (PropMode != NQMasterPropMode.Off) Log(string.Format("PROP {0}: equity {1:0} | threshold {2:0} | cushion {3:0} -> {4}", PropMode, PropEquity(), propThr, propCushion, gate));""",
"""			if (PropMode != NQMasterPropMode.Off) Log(string.Format("PROP {0}: equity {1:0} | threshold {2:0} | cushion {3:0} -> {4}{5}", PropMode, PropEquity(), propThr, propCushion, gate,
				StepUpOn ? string.Format(" | STEP-UP {0} contracts", FundedStepUpContracts) : ""));""")
s = sub(s, """			if (PropMode == NQMasterPropMode.Funded && PropEquity() - StartBalance >= FundedPayoutAt)""",
"""			if (PropMode == NQMasterPropMode.Funded && FundedStepUpCushion > 0) txt += string.Format("\\nSize: {0} contracts per module ({1})", Qty(), StepUpOn ? "step-up on" : string.Format("step-up at cushion ${0:0}", FundedStepUpCushion));
			if (PropMode == NQMasterPropMode.Funded && PropEquity() - StartBalance >= FundedPayoutAt)""")
s = sub(s, """public double FundedProfitStop { get; set; }""",
"""public double FundedProfitStop { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Funded: step-up when cushion >= $ (0 = off; MyFundedFutures 3000)", Order = 16, GroupName = "07. Prop account (cushion gating)")] public double FundedStepUpCushion { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Funded: step-up contracts per module", Order = 17, GroupName = "07. Prop account (cushion gating)")] public int FundedStepUpContracts { get; set; }""")
s = sub(s, """				PropSessionStart();
				sessHi = High[0]; sessLo = Low[0];""", """				PropSessionStart();
				edgeDayQty = Qty();                                  // after the prop cushion is known (funded step-up)
				sessHi = High[0]; sessLo = Low[0];""")
open(p, "w", encoding="utf-8").write(s)

p = R + "/GoldMaster.cs"; s = open(p, encoding="utf-8").read()
s = sub(s, "ConsistencyPct = 50; EvalBestDaySoFar = 0;", "ConsistencyPct = 50; EvalBestDaySoFar = 0; FundedStepUpCushion = 0; FundedStepUpContracts = 2;")
s = sub(s, """			EvalSessionStart();
			svPv = 0;""", """			EvalSessionStart();
			StepUpSessionStart();
			svPv = 0;""")
s = sub(s, """		private int Qty()
		{
			if (EvalMode && evalDayIndex >= EvalLateDay && evalEqDayStart < EvalLateGoal && (EvalLateMinCushion <= 0 || double.IsNaN(evalCushion) || evalCushion >= EvalLateMinCushion)) return EvalLateContracts;
			return Contracts;
		}""", """		// ---- funded step-up (same rule as NQMaster, research/mine/final3y_acct.py): FundedStepUpContracts while the account cushion over the
		// EOD-trailing threshold ($2,000, locks at start + $100) is >= FundedStepUpCushion at the session start. Realtime: account cash and the
		// higher of this strategy's realtime peak and NQMaster's prop-file peak; historical: this strategy's own P&L.
		private double stepHistPeak = double.NaN, stepRtPeak = double.NaN, stepCushion = double.NaN;
		private void StepUpSessionStart()
		{
			stepCushion = double.NaN;
			if (FundedStepUpCushion <= 0 || EvalMode) return;
			bool rt = State == State.Realtime; double eq, pk;
			if (rt)
			{
				eq = Account.Get(AccountItem.CashValue, Currency.UsDollar) - StartBalance;
				stepRtPeak = double.IsNaN(stepRtPeak) ? Math.Max(0, eq) : Math.Max(stepRtPeak, eq); pk = stepRtPeak;
				double fpk, fds, fbd; int fdt;
				if (ReadNqProp(out fpk, out fdt, out fds, out fbd) && !double.IsNaN(fpk)) pk = Math.Max(pk, fpk - StartBalance);
			}
			else { eq = netPnl; stepHistPeak = double.IsNaN(stepHistPeak) ? Math.Max(0, eq) : Math.Max(stepHistPeak, eq); pk = stepHistPeak; }
			double thr = pk >= 2100 ? 100 : pk - 2000; stepCushion = eq - thr;
			if (PrintLog && stepCushion >= FundedStepUpCushion) Print(string.Format("{0} | GOLD | STEP-UP: cushion {1:0} -> {2} contracts", sessionDate, stepCushion, FundedStepUpContracts));
		}
		private int Qty()
		{
			if (EvalMode && evalDayIndex >= EvalLateDay && evalEqDayStart < EvalLateGoal && (EvalLateMinCushion <= 0 || double.IsNaN(evalCushion) || evalCushion >= EvalLateMinCushion)) return EvalLateContracts;
			if (!EvalMode && FundedStepUpCushion > 0 && !double.IsNaN(stepCushion) && stepCushion >= FundedStepUpCushion) return FundedStepUpContracts;
			return Contracts;
		}""")
s = sub(s, """public double AccountProfitStop { get; set; }""", """public double AccountProfitStop { get; set; }
		[NinjaScriptProperty][Range(0, double.MaxValue)][Display(Name = "Funded: step-up when account cushion >= $ (0 = off; MyFundedFutures 3000)", Order = 15, GroupName = "02. Risk / account")] public double FundedStepUpCushion { get; set; }
		[NinjaScriptProperty][Range(1, 50)][Display(Name = "Funded: step-up contracts per module", Order = 16, GroupName = "02. Risk / account")] public int FundedStepUpContracts { get; set; }""")
open(p, "w", encoding="utf-8").write(s)
print("patched")
