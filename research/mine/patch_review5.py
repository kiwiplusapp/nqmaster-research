"""Fifth code review (2026-10-07), low-severity timing items:
(1) ORB waits for a deferred module only when that module's entry is opposite to ORB's direction (deferDir);
(2) deferral length per caller (1 bar on the 1-minute series, 2 for MSEQ / MSEQS whose retry resolves within 2 bars, 5 for ICT) and
    deferUntil never shortened (Math.Max);
(3) the MSEQ / MSEQS retry is dropped when the bar's low / high touched the stop (research trade already stopped out)."""
p = r"D:\NinjaTrader Strategy\NQMaster.cs"
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    n = s.count(a); assert n == 1, (n, a[:100]); s = s.replace(a, b)
rep("(pend5Dir == 1 ? Close[0] <= pend5Stop : Close[0] >= pend5Stop)", "(pend5Dir == 1 ? Low[0] <= pend5Stop : High[0] >= pend5Stop)")
rep("\t\t\tif (CurrentBars[0] <= deferUntil) return;\t\t\t// a deferred module enters first\n",
    "\t\t\tif (CurrentBars[0] <= deferUntil && trendDir == -deferDir) return;	// an opposite deferred module enters first\n")
rep("if (!DirectionAllowed(1)) { if (lastDeferred) { pend5 = mseq;", "if (!DirectionAllowed(1, 2)) { if (lastDeferred) { pend5 = mseq;")
rep("if (!DirectionAllowed(-1)) { if (lastDeferred) { pend5 = mseqs;", "if (!DirectionAllowed(-1, 2)) { if (lastDeferred) { pend5 = mseqs;")
rep("\t\tprivate bool lastDeferred; private int deferUntil = -1;", "\t\tprivate bool lastDeferred; private int deferUntil = -1, deferDir;")
rep("\t\tprivate bool DirectionAllowed(int d)\n", "\t\tprivate bool DirectionAllowed(int d) { return DirectionAllowed(d, BarsInProgress == 1 ? 5 : 1); }\n\t\tprivate bool DirectionAllowed(int d, int deferBars)\n")
rep("\t\t\tif (blocked) { lastDeferred = true; deferUntil = CurrentBars[0] + (BarsInProgress == 1 ? 5 : 1); return false; }",
    "\t\t\tif (blocked) { lastDeferred = true; deferUntil = Math.Max(deferUntil, CurrentBars[0] + deferBars); deferDir = d; return false; }")
open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched")
