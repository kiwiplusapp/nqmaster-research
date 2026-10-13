# NQMaster: best-practices audit, and whether to build a Python AI system (2026-10-12)

Scope: the NQMaster / GoldMaster project (NinjaTrader 8, MNQ + MGC, prop accounts at Lucid Trading and MyFundedFutures).
Evidence comes from `claude/memory/ifvg-sniper-nt8-project.md` (the research log), `NQMASTER_GUIA.md`, `research/mine/propfirms_2026.md`
and the scripts and result files named below. External sources are listed at the end ([S#]). All web sources were accessed on 2026-10-12.
Where a source is a vendor with a commercial interest, it is flagged.

---

## Executive summary

**Part A, audit (34 practices):** 15 Done, 16 Partly, 3 Missing.

The research side is unusually strong for a retail project. It has deflated Sharpe ratios and PBO/CSCV, an edge haircut, plateau checks,
16 years of real futures data, NinjaTrader trades reconciled with the research (96% matched), and a CUSUM edge monitor.
The gaps are mostly in **deployment and operations**:

| # | Gap | Recommendation |
|---|---|---|
| 1 | **No forward incubation of a frozen version, and the "out-of-sample" periods are used up.** C24/REAL/2026 have been checked hundreds of times since Sept 2026, and the strategy code keeps changing (28 `NQMaster_backup_pre_*.cs` versions; 21 commits to `NQMaster.cs` between 2026-10-05 and 2026-10-10). | Freeze **v1.0**. Treat everything from 2026-10-13 on as a sealed forward holdout. Run 4-8 weeks on Sim / the first eval with daily reconciliation before adding accounts. |
| 2 | **No alerting, a single home PC, no incident runbook.** Edge-monitor alarms and `STALE ORDER` messages only go to NinjaTrader's Output window (no `Alert`/`SendMail` in either strategy). The C: drive filled up on 2026-10-03. | Python watchdog: tail the NT logs and a heartbeat file, push alerts to the phone. Add a UPS and a backup internet line. Write a one-page runbook (disconnect, platform crash, stuck order, rule breach). Get Lucid/MFFU's VPS policy in writing. |
| 3 | **Change management.** Patches ship "parse-checked, NOT compiled". There is no version stamp in the live output and no automated regression run. | Release checklist: compile, run a "golden" Strategy Analyzer regression against the stored trade list with `nt_compare.py`, print the version on start-up, change on a fixed schedule only. |
| 4 | **Fill realism below one minute.** The whole portfolio has never been replayed on ticks. The one module that was (08:20 breakout) went from PF 1.46 to 0.96-1.09. Live slippage is not measured. | Re-run Ultra in Strategy Analyzer with High order-fill resolution (a 1-tick series) for the last 6-12 months, per module. Log the slippage of every live fill. |
| 5 | **The edge is a post-2020 regime and the rule set is complex.** Cost-normalised Ultra PF was ~0.9-1.2 in 2010-19. 5-8 modules are rated chance-level but kept. There are no permutation ("monkey") tests. | Write down each module's mechanism and its kill condition. Pre-define a defensive fallback (the 6 durable modules) that the edge monitor triggers. Add per-module permutation tests. |

**Part B, a Python AI system:**

- **Execution at Lucid / MFFU:** Both firms allow automated trading, and neither mentions "AI": an AI bot is simply a bot, and you remain responsible for its errors.
  - Neither firm offers a documented order API for self-built programs. MFFU is Tradovate/NinjaTrader-based. Lucid is CQG (NinjaTrader/Tradovate/TradingView) plus Rithmic platforms. Personal Tradovate API keys reportedly cannot reach prop accounts.
  - **The realistic route is to keep NinjaTrader as the execution engine** and run Python around it.
  - A Python program that sends orders itself is technically possible only through Lucid's Rithmic feed. That needs Rithmic's R|Protocol conformance test and Lucid's written OK. For MFFU there is no documented route except through a supported platform.
  - Outside prop firms, a full Python stack is straightforward: IBKR TWS API, AMP + Rithmic API ($125/mo), or Tradovate API (live account > $1,000 + add-on + CME data licence). But losses are then your own: about $41k of capital per base contract at a 20% volatility target.
- **Real-time news:** At retail speed it is a **risk filter, not an edge**.
  - E-mini futures price macro surprises in ~5 ms [S29].
  - The project's own tick test lost the edge at 50 ms of latency.
  - MFFU funded accounts ban trading ±2 min around Tier-1 news, and MFFU forbids exploiting simulated fills.
  - Automate the scheduled-event calendar (free official sources). If wanted, test an unscheduled-shock pause in shadow mode.
  - Do not build a news-reaction or LLM-sentiment alpha for NQ intraday: there is look-ahead/memorization bias, decaying returns, and latency [S24-S27].
- **"Self-improving AI":** The literature and this project agree. Every adaptive layer tried here failed out of sample:
  - ML meta-labeling (3 times)
  - walk-forward rotation
  - equity-curve module switching
  - IS-optimised weights and filters
  - context-filter mining
  - the order-flow boost

  A self-modifying live system cannot even tell whether a change helped: separating a +0.3 Sharpe improvement from noise takes years.
  The safe version is **offline, scheduled retraining with pre-registered promotion gates, a champion/challenger in shadow mode, human approval, versioned releases and the existing CUSUM monitor**. An LLM is useful as a research and operations assistant, not as the trader.
- **Plan:**
  - Phase 0 (2 weeks): freeze and incubate; written answers from the firms; UPS and backup internet.
  - Phase 1 (1-2 months, ~40-80 h): Python operations sidecar (alerts, reconciliation, news calendar).
  - Phase 2 (2-6 months, ~80-150 h): research platform with a trial registry and champion/challenger gates.
  - Phase 3 (optional, after 6+ months of live evidence): Python execution for an own-brokerage account.

---

## Part A — Best-practices audit checklist

Scoring: **Done** = practice in place with evidence; **Partly** = present but incomplete or not systematic; **Missing** = absent.
Where a practice is "done" but its *result* is a risk (e.g. regime dependence), the score rates the practice and the risk is called out separately.

### A1. Research design and data

| # | Best practice (source) | Score | Evidence in this project | Recommendation |
|---|---|---|---|---|
| 1 | Start from an ex-ante economic hypothesis and state it before testing; prefer ideas with a mechanism (Arnott, Harvey & Markowitz 2019 step 1 [S7]; Aronson [S8]) | **Partly** | Some modules have a documented rationale (ORB / intraday momentum, the noise-area idea of Zarattini 2024, overnight reversal). Most came out of mining: `run_mine.py` 9,254 configs; `run_mine_db.py` 45,278 + 8,208; ~100k configs overall. `db_long.json` shows the Ultra edge is a **post-2020 regime** with no documented cause. | One paragraph per module: mechanism, who loses money to it, and what would make it stop working. Use this to choose the defensive set (item 13). |
| 2 | Clean, tradable, point-in-time data: real contract, correct roll and timezone/DST, holidays (Chan [S11]) | **Done** | Moved from CFD to real MNQ exports (`prep_nt.py`). Databento NQ/GC 2010-26 with forward roll adjustment (`prep_databento.py`, 66 rolls; 1m corr 0.993 vs NT). histdata DST issue documented. Holiday/early-close bug found and fixed (NQPullbackDayEngine). Missing 2025-07-14 flagged. | Fix the research replica's remaining artifact: it turns the trend filter off for ~20 days after holiday closures. This explains 182 NT-only trades in `research/nt_exports/2026-10-09/`. |
| 3 | Guard against look-ahead / peeking (LdP AFML [S5]; Chan [S11]) | **Done** | Several look-ahead bugs found and fixed: FVG order-priority, the overnight-range filter for LON/ON07, ZigZag repaint, ICT fill-then-stop (`ict_fix.py`), 08:20 intrabar sequencing (`orb0820_ticks.py`). "Bar-by-bar state machine" is a standing rule. | Add an automated truncation test: recompute every signal with the data cut at time t; it must be unchanged. |
| 4 | Know the statistical power and the effective sample size (Harvey & Liu [S4]; Carver [S10]) | **Done** | `robust_lab.py`: ~380 effective independent days out of 657 REAL, 12.3 effective bets out of 14 modules. Eval pass-rate noise of ±8-10 points stated explicitly. | — |
| 5 | Record every trial so multiple-testing corrections can use the true number of trials (LdP [S5][S6]; Harvey, Liu & Zhu [S3]) | **Done** | The memory file logs config counts per study and every rejected idea, with dates. DSR is run at 50k and 300k trials. | Turn it into a machine-readable registry (CSV: date, family, configs, data used, decision). Phase 2 needs it to compute DSR automatically. |

### A2. Overfitting control and statistical validity

| # | Best practice (source) | Score | Evidence | Recommendation |
|---|---|---|---|---|
| 6 | Truly untouched holdout; each holdout used once (Arnott et al. [S7]; LdP [S5]) | **Partly** | Formal splits exist: IS 2020-23, C24, REAL 2024-26, 2015-19, the 2026 holdout in the MaxPlus2 protocol, 2010-19 Databento. But C24/REAL/2026 have decided hundreds of accept/reject choices since Sept 2026 (every new module, rule and prop policy), so they are no longer clean. | Seal **2026-10-13 onward** as the forward holdout. Promote nothing on it until ≥ 6 months have accumulated, and count the 2010-19 block as a hard gate. |
| 7 | Walk-forward analysis (Pardo [S9]) | **Done** | `audit_wf*.csv` (walk-forward rules A/B/C vs fixed: no gain), `ml26.py` and `meta5.py` (walk-forward ML), walk-forward rotation of 93 streams (88% negative). | — |
| 8 | Multiple-testing correction: deflated Sharpe, haircut, t > 3 (Bailey & LdP 2014 [S2]; HLZ 2016 [S3]; White 2000 [S14]) | **Done** | `audit_dsr.csv`: Ultra DSR 1.00 CFD / 0.93 REAL at 300k trials. `robust_lab.json`: DSR ~1.0 / 0.95 at 50k. | — |
| 9 | Probability of backtest overfitting via CSCV (Bailey, Borwein, LdP & Zhu 2017 [S1]) | **Done** | `robust_lab.py`: PBO 40% for "pick the best mined config" (IS Sharpe 2.05 → OOS 0.59); module-variant PBO CRT11 2%, LON/MSEQ 0.1%, ICT 16%. `wrq_pbo.py` ~0.56 for exit/filter tweaks. `audit_family.py`. | — |
| 10 | For ML: purged / embargoed k-fold or CPCV, meta-labeling done correctly (LdP AFML ch. 3, 7, 12 [S5]) | **Partly** | ML studies (`ml26.py`, `meta5.py`, the 16-year meta-labeling) used walk-forward with prior-year calibration. No purging or embargo appears anywhere in the research code. Impact was low because all ML was rejected. | Mandatory for any Python ML: purged k-fold with an embargo ≥ the maximum holding time, CPCV, and the trial count added to the registry. |
| 11 | Parameter stability / plateaus rather than peaks (Pardo [S9]; Davey [S12]) | **Done** | `audit_neighbours.csv`, `robust_lab` plateaus. Isolated parameter cells are flagged (SVWAP22, ENG0408, ON07, LATEFH, ENG10). Night modules sit on plateaus. | — |
| 12 | Benchmark against randomness: Monte Carlo permutation, White's Reality Check, random-entry "monkey" tests (Aronson [S8]; White [S14]; Davey [S12]) | **Partly** | Bootstrap and Monte Carlo of trade sequences exist, plus a zero-edge baseline for eval pass rates (~44-50%). **No** permutation or random-entry test exists (no `permutation`/`shuffle` anywhere in `research/`). | Per module: keep the time of day and the exits, randomise the direction and/or the day, run 1,000×, report a p-value. This is cheap with the existing engine. |
| 13 | Robustness across regimes and long history (Carver [S10]; Chan [S11]) | **Done** (risk flagged) | 16 years of real futures (`db_long.json`): Ultra cost-normalised PF by year 2010-19 was 1.04/1.08/0.96/0.87/1.12/0.95/1.21/1.17/1.21/1.09, against 1.33-1.69 for 2020-26. ATR/VIX terciles, trend vs range days (range days PF 0.74-0.85). | This is the **main strategic risk**: the edge may be a regime. Pre-define the 6 durable modules (NF05, CRT11, VOLB, MSEQS, ORB60, ORB90: norm PF 1.18/1.24/1.60/1.68 across the 4 blocks) as the fallback when the edge monitor alarms. |
| 14 | Control complexity / degrees of freedom (Carver [S10]; LdP [S6]) | **Partly** | Good discipline on additions: only 4 of ~2,550 trade-quality rules accepted. But Ultra has ~20 NQ modules, context and confluence rules, x2 boosts, prop gating and step-up. The audit rates ON07, LATEFH, ENG10, MOM1030/MOM13 (without agreement) and 3 gold modules as chance-level, yet they stay on (`final3y_weak.py` argues Ultra still ≥ lean). | Count the free parameters per profile. If the forward holdout under-performs, fall back to Lean or Core before changing anything else. |
| 15 | Expected-performance haircut (Harvey & Liu 2015 [S4]) | **Done** | `audit_haircut.csv`, `final3y_haircut.py`: +1 tick and 35% of the edge removed → Ultra ~$1,700/mo per base contract. `final3y_conf.py`: P(positive year) 82%; P(≥ 80% of backtest) 25%. | — |

### A3. Execution realism

| # | Best practice (source) | Score | Evidence | Recommendation |
|---|---|---|---|---|
| 16 | Realistic costs plus a cost stress test (Chan [S11]; Davey [S12]) | **Done** | $1.90 commission + 1 tick per side everywhere. +4 ticks/side → PF 1.30/1.35/1.39. Breakeven slippage 15-23 ticks (`robust_lab.json`). | — |
| 17 | Fill model fit for the strategy: intrabar sequencing, limit fills need a trade-through, tick-level checks when targets are small (NT fill-resolution docs [S20]; Chan [S11]) | **Partly** | Research runs on 1-minute bars. Many targets are 0.3-0.75R, where same-bar stop/target ordering matters. Biases already found this way: ICT (PF 1.53 → 1.23), the 08:20 breakout (1m PF 1.46 → ticks 0.96-1.09). The full portfolio has never been tick-replayed. NT validation used the default fill resolution. | Strategy Analyzer with **High order-fill resolution (1-tick series)**, Ultra, last 6-12 months; compare PF per module with the 1m research. Any module that drops > 0.15 PF goes on the watch list. |
| 18 | Latency and order-type realism: stop-market slippage, queue position for limits (FIA [S15]; Chordia et al. [S29]) | **Partly** | Latency tested only for 08:20 (0/50/250 ms). Limit entries on clock modules rejected for adverse selection (good). No live slippage statistics exist yet. | Log the intended vs filled price of every live fill (Python reconciliation, Phase 1). Alarm if mean slippage > 1 tick per side over 50 fills. |
| 19 | Capacity / market impact (Carver [S10]) | **Done** | `liquidity.py`: household orders vs real minute volume. Night modules are the bottleneck; ~10 accounts is the practical limit. | — |
| 20 | Backtest ↔ platform reconciliation (Davey [S12]) | **Done** | `nt_compare.py`: 1,936/2,023 research trades matched (95.7%), $51,504 vs $51,497, daily corr 0.968. GoldMaster 99.7%. The zombie-order bug (0 shorts after 2025-08-12) was found this way. | Extend it to live executions (item 28). Prop modes (Eval/Funded gating, Estable, profit stops, step-up) were **not** part of the 10-09 NT validation: validate them once. |

### A4. Risk and position sizing

| # | Best practice (source) | Score | Evidence | Recommendation |
|---|---|---|---|---|
| 21 | Size by risk: volatility targeting, risk budget per strategy (Carver [S10]) | **Partly** | Inverse-ATR and inverse-vol sizing tested: no Sharpe gain. Fixed contracts per module chosen. In prop accounts the trailing drawdown is the binding constraint and is simulated in detail. For an own-capital account no volatility target is defined. | For own capital: Ultra has a daily σ of ≈ $519 per base contract, i.e. ≈ $8.2k per year (`final3y_trades.pkl`, REAL 2024-26). At a 20% annual vol target that is **≈ $41k of equity per base contract**. |
| 22 | Kelly / risk of ruin; size well below full Kelly because of estimation error (Kelly 1956; MacLean, Thorp & Ziemba [S13]) | **Partly** | Prop ruin (eval and funded busts per year) is modelled extensively (`acct_*`, `lc_lib.py`, `final3y_acct.py`, Monte Carlo/bootstrap). No Kelly calculation exists. From the same trade file: full Kelly = 4.8 base contracts per $10k at the backtested edge, 3.1 at 35% haircut. That is clearly unusable, which shows that estimation error and fat tails (worst day −$1,748 per base contract), not Kelly, must set the size. | State the policy explicitly: own capital ≤ ¼ Kelly *and* the vol target above, whichever is smaller. Prop: keep the lifecycle simulations. |
| 23 | Diversify across uncorrelated forecasts and instruments (Carver [S10]) | **Partly** | 12.3 effective bets out of 14 modules; gold correlation ~0. But it is a single underlying (NQ) and a single regime. ES, EUR, silver, oil and other index micros were tested and rejected (costs or no edge). | Accept it, and price the concentration into expectations. Re-test other markets only with new data or new ideas. |
| 24 | Stress tests and drawdown expectations set in advance (Davey [S12]) | **Done** | Monte Carlo 1-year maxDD median $4.8k / p95 $6.8k. With the haircut, p95 $10.3k (`audit_final.csv`). Worst month −$3.1k. Range-day stress. | Write the "expected worst case" next to the pause rules, so a normal drawdown is not mistaken for a broken edge. |

### A5. Deployment, live monitoring and change management

| # | Best practice (source) | Score | Evidence | Recommendation |
|---|---|---|---|---|
| 25 | **Incubation / forward paper test of a frozen version before risking capital** (Davey [S12]; Chan [S11]) | **Missing** | All evidence is backtest (research, then NT Strategy Analyzer). No forward record of the current rule set exists. Code changed almost daily up to 2026-10-10 (21 commits to `NQMaster.cs` in 6 days: warm-up, step-up, order-flow, news blackout, Estable, LucidPro stop). | Freeze v1.0. Run it on Sim101 *and* the first eval for 4-8 weeks. Pass condition: live vs replica trade match ≥ 90%, slippage ≤ 1 tick per side, no unexplained orders. |
| 26 | Live performance monitoring with a statistical decay detector (SR 11-7 "ongoing monitoring" [S17]) | **Done** | `EdgeMonitor` CUSUM with calibrated k/h (Ultra 0.0755/16.21; false alarm 1.5%/yr; dead edge detected ~158 trading days, negative edge ~92). The pause rule is in the playbook. | Weakness: `EdgeMonitorPause` defaults to false and the alarm only prints (see item 31). |
| 27 | Kill switch and pre-trade risk limits: max order size, max position, price collar, order-rate throttle, cancel-on-disconnect (FIA 2024 [S15]; EU RTS 6 [S18]) | **Partly** | Pause file, `NQAccountGuard` (`Account.Flatten`), daily loss/profit stops, `FlattenTime` 15:56, protective-reject flatten, stale-order watchdog, FOMC skip. **No** hard cap on net position or order size independent of module logic, no order-rate guard, no remote kill. | Add `MaxNetContracts` (e.g. 12 MNQ at Contracts 1) and `MaxOrdersPerMinute`. Before sending, if the cap would be exceeded: block and alert. Remote kill = pause file in a synced folder + phone alert. |
| 28 | Reconcile live vs backtest daily (Davey [S12]; SR 11-7 outcomes analysis [S17]) | **Partly** | `nt_compare.py` handles Strategy Analyzer exports. There is no daily routine for live executions, and no slippage or missed-trade log. | Phase 1 Python job: each night, export NT executions, run the replica on the same day's data, report missing/extra trades, slippage and P&L gap. |
| 29 | Change management: version control, code review, regression tests, staged rollout, rollback (SEC Knight Capital order [S16]; SR 11-7 [S17]) | **Partly** | Git repo, 28 NQMaster + 11 GoldMaster pre-change backups, reproducible `patch_*.py`, 5 code reviews, NT validation after the big changes. But changes ship "mcs parse OK, NOT compiled". There is no version string in the output, no automated compile + regression run, and a very high change rate. | Release checklist (Phase 0). Allow at most one release per month outside emergencies. |

### A6. Operational resilience

| # | Best practice (source) | Score | Evidence | Recommendation |
|---|---|---|---|---|
| 30 | Infrastructure redundancy: UPS, backup connectivity, standby machine or VPS (FIA [S15]) | **Partly** | A cold spare exists: second PC with `tools/instalar_en_pc.ps1`. Otherwise everything runs on one home Windows PC; its C: drive filled to 0 GB on 2026-10-03. No VPS. Lucid/MFFU pages do not address VPS; Topstep bans it [S45]. | UPS + 4G/5G failover router. Ask both firms in writing whether a VPS is allowed. Keep the second PC warm (same version, logged in to data only). |
| 31 | **Alerting and heartbeat to a human** (Knight Capital: 97 error e-mails "not built as alerts" [S16]) | **Missing** | No `Alert()`, `SendMail()` or push in `NQMaster.cs` / `GoldMaster.cs`. Edge alarm, `STALE ORDER dropped`, eval-target and drawdown events go only to the Output window and dashboard. | Phase 1: NT `Alert()` + a Python log tailer with a heartbeat file, sending Telegram/e-mail for: no heartbeat > 2 min in session, rejected or stale order, position without a stop, edge alarm, daily loss hit. |
| 32 | Defined behaviour on disconnect, restart and platform failure (NT `ConnectionLossHandling` docs [S19]) | **Partly** | `StartBehavior = WaitUntilFlat`, prop state persisted in a file, stale-order watchdog, `IgnoreAllErrors` + flatten on protective reject. `ConnectionLossHandling` is not set explicitly (default Recalculate), and disconnect scenarios have never been tested. | Test on Sim: pull the network cable with an open position, restart NT mid-session. Choose `ConnectionLossHandling` explicitly and document what happens. |
| 33 | Written incident runbook (FIA [S15]; SR 11-7 [S17]) | **Missing** | The guides cover settings and plans, not incidents. | One page: whom to call (each firm's broker/desk), how to flatten from the phone/Tradovate web, when to pause, how to restart cleanly, how to report a platform fault to the firm. |

### A7. Prop-firm rule compliance (project-specific)

| # | Best practice | Score | Evidence | Recommendation |
|---|---|---|---|---|
| 34 | Encode the firm's rules in the strategy and confirm grey areas in writing | **Partly** | `NewsBlackout` / `NewsTimes`, consistency targets, `FlattenTime`, opposite-position blocking, max-micros analysis, PropMode Eval/Funded. Still open: MFFU wording on "any data release" (−15-18% of Ultra P&L if strict); VPS. 2027 CPI/NFP dates must be typed in by hand. | Get written answers. Automate the calendar from official BLS/Fed/BEA schedules (Phase 1). |

### Score count

| Section | Done | Partly | Missing |
|---|---|---|---|
| A1 Research design and data (1-5) | 4 | 1 | 0 |
| A2 Overfitting and validity (6-15) | 6 | 4 | 0 |
| A3 Execution realism (16-20) | 3 | 2 | 0 |
| A4 Risk and sizing (21-24) | 1 | 3 | 0 |
| A5 Deployment and monitoring (25-29) | 1 | 3 | 1 |
| A6 Operational resilience (30-33) | 0 | 2 | 2 |
| A7 Prop compliance (34) | 0 | 1 | 0 |
| **Total (34)** | **15** | **16** | **3** |

Reading: the statistical validation of the edge is close to institutional standard. The weakest area is everything after "the backtest is right":
forward incubation, alerting, resilience, release discipline. These are the areas where a system that worked in testing usually fails in live trading.

---

## Part B — Moving to a proprietary Python system with ML, real-time news and a "self-improving AI"

### B1. Execution: can a self-built Python program trade Lucid and MFFU accounts?

**Firm rules and access routes (as of Oct 2026)**

| | Lucid Trading | MyFundedFutures (MFFU) |
|---|---|---|
| Automation policy | Automated systems and copiers permitted, in eval and funded. Trader responsible for software errors. HFT, hedging across accounts and microscalping prohibited (flag if > 50% of profit comes from trades ≤ 5 s). Help-center art. 11404728 (2026-08-26) in `propfirms_2026.md`; [S35] reviewed 2026-09-23; [S36] modified 2026-09-28. | "Automated trading strategies tailored to their own specific settings" allowed, as long as they "do not aim to exploit the favorable fills offered in the Simulated Environment". HFT not allowed. Live accounts with automation must follow CME guidelines. No copy trading between traders (own accounts OK). Fair Play art. 8444599, updated 2026-08-24 [S37]; copy-trading art. [S40]. |
| "AI" mentioned? | No. An AI-driven bot is treated as automated trading. | No. |
| Platforms | CQG feed: NinjaTrader, Tradovate, TradingView. Rithmic feed: R\|Trader Pro, Sierra Chart, MultiCharts, Quantower, MotiveWave, ATAS, Bookmap, Jigsaw, Tradesea. "All listed platforms work with all Lucid account types" [S33]. ProjectX / LucidX not on the list (checked 2026-10-11 [S34]). | NinjaTrader, Hyperprop, Tradovate, TradingView, Quantower, Volumetrica, DeepChart/DeepDom, ATAS [S38]. Tradovate login and data agreement [S39]. No Rithmic, no API product listed. |
| Documented order API for your own code? | None documented. | None documented. |
| Python route 1: NinjaTrader as the execution host | **Yes.** It is how NQMaster runs today. Python can talk to NT through files (the current pause file / `NewsTimes`), the ATI Order Instruction Files [S52], `NinjaTrader.Client.dll`, or a custom NinjaScript AddOn socket. | **Yes**, same. |
| Python route 2: direct broker API | **Rithmic R\|Protocol** (WebSocket + protobuf; Python via `async_rithmic`) is technically possible on Lucid's Rithmic-feed accounts. Production access requires passing **Rithmic's conformance test** [S46], and Lucid must confirm a self-built app is allowed. Tradovate API: personal API keys reportedly cannot see firm-managed accounts [S41] (vendor source). | Tradovate API is the only plausible one, and it reportedly does not work for prop accounts [S41][S42] (vendor sources). There is no Rithmic. **Not available in practice.** |
| VPS | Not addressed in the pages found. Ask. | Not addressed in the pages found. Ask. (For contrast, Topstep explicitly bans VPS/VPN for order placement and offers the ProjectX API at $29/mo [S45].) |
| Going live | Moving live closes all sim accounts; LucidLive is a real brokerage account with its own onboarding. Confirm automation there [S35]. | Automatic at a $10k single-day profit or at the risk team's discretion. Live automation must follow CME rules [S37]. |

**What this means**
1. A Python "brain" that places orders itself is **not a practical option at MFFU**. At Lucid it is possible only via Rithmic conformance plus written permission.
2. The supported and already validated path is **NinjaTrader executes, Python advises**. Keep all order logic, stops, rule guards and position state in NinjaScript.
   - Python changes only *slow* inputs read at session start: pause on/off, news times, the module enable list, size.
   - Do not route core orders through ATI/OIF files. Those orders bypass NinjaScript's managed position tracking (`WaitUntilFlat`, stale-order watchdog, opposite-entry blocking). That would re-open the class of bugs fixed in reviews 2-5 and the zombie-order fix.
3. An AI that trades in sim accounts can break the MFFU "exploit simulated fills" clause, for example by fading news spikes that would not fill in a real market. The bot owner carries that risk.

**Outside prop firms (own brokerage account)**

| Route | Python API | Indicative costs | Notes |
|---|---|---|---|
| Interactive Brokers | TWS API / IB Gateway; `ib_async` | Commission: tiered from ~$0.25, fixed $0.85 per contract [S50]. CME micro fee offset ~$0.35 + regulatory, per side [S50]. API data needs an IBKR Pro account, $500 equity and market-data subscriptions [S49]. | Mature, well documented. Bracket/OCA orders native. Roughly $1.2-1.8 per round turn all-in for MNQ (verify), vs $1.90 assumed in the research. |
| AMP Futures + Rithmic | R\|API (C++/.NET); R\|Protocol from Python (`async_rithmic`) | R\|API $100/mo + $25 user ID = **$125/mo**; $0.10 per contract routing on live [S47][S48]. Conformance test for production [S46]. | Lowest-latency retail-accessible route. Highest engineering effort. |
| Tradovate (NinjaTrader group) | REST/WebSocket API | Live account with > $1,000; API add-on ~$25/mo [S42][S43]. Forum and vendor sources cite a **CME licence of ~$290/mo** for API market data [S44] (verify). | Data licensing makes it expensive for one person. |
| NinjaTrader brokerage + NT8 | Keep current code | Current setup | No rewrite. Lowest risk. |
| Market data for a Python stack | Databento | CME Standard plan **$199/mo** from 2026-06-22 ($179 grandfathered), live + history [S51] | Already used for research (16-year history). |

**Capital, if it is own money:** the prop firm no longer absorbs losses. `final3y_conf.py` shows the prop structure stays near break-even even if the edge vanished; an own account does not.
- From the REAL 2024-26 Ultra trades: daily σ ≈ $519 per base contract; p95 one-year drawdown at 35% haircut ≈ $10.3k.
- At a 20% annual vol target: ≈ $41k per base contract (≈ 1 MNQ per module).
- Full Kelly at the backtested edge would be 4.8 base contracts per $10k. That shows how misleading Kelly is when the edge estimate is uncertain.

### B2. Real-time news

**Feeds (indicative 2026 prices; verify before buying)**

| Source | What | Indicative price | Latency class | Source |
|---|---|---|---|---|
| Official calendars (BLS, BEA, Federal Reserve) | Scheduled release times, months ahead | Free | n/a: only the schedule | already used in `research/news.py` |
| FinancialJuice | Headlines + squawk | PRO ~$69/quarter (~$23/mo), ELITE ~$99/quarter; free tier delayed ≥ 15 s | seconds | [S53] (competitor's comparison page) |
| Benzinga Pro | Newsfeed, squawk, API on higher tiers | ~$37 to ~$197/mo; higher tiers ~$457/mo; sources conflict on tier names | seconds | [S54] |
| Newsquawk | Headlines + audio squawk | $199/mo (one channel) to $399/mo (all) | seconds | [S53] |
| Trading Economics API | Calendar + streaming | ~$149-299/mo billed yearly (aggregator, unverified) | seconds | [S55] |
| Bloomberg Terminal / LSEG Workspace | Full news + data | ~$32k/yr / ~$22k/yr per seat | sub-second to seconds | [S56] |
| Machine-readable macro feeds (e.g. Deutsche Börse AlphaFlash) | Numeric release values, co-located | Institutional, on request | milliseconds | [S57] |

**Evidence on retail-speed news trading in NQ**
- **Institutional speed wins.** SPY and E-mini futures react to macro surprises within ~5 ms, and trading intensity jumps > 100×. Even then, the speed rents are small: ~$50k per event in ES [S29]. A NinjaTrader bot on a home connection is 2-4 orders of magnitude slower.
- **This project's own tests agree:**
  - `orb0820_ticks.py`: the 08:20 range breakout, PF 1.46 on 1-minute bars, becomes PF 1.09 when filled at the triggering print, 0.98 at 50 ms and 0.96 at 250 ms. CPI/NFP days averaged 34 ticks of entry slippage (p90 168).
  - The pre-8:30 news ORB was rejected earlier as "slippage-dependent".
  - Holding through releases is fine: the blackout costs Ultra 2.4-5.7% (`news_cost.py`).
  - Skipping FOMC helped; skipping CPI/NFP did not.
- **Rules restrict news trading.** MFFU Rapid funded: no positions or orders ±2 min around Tier-1 releases. LucidDaily funded: red-folder news is a hard breach (`propfirms_2026.md`).

**LLM headline sentiment: evidence and pitfalls**
- Lopez-Lira & Tang (v6, Oct 2025): GPT-4 captures the *initial* reaction, which is not tradable (~90% hit rate). Predictability of the later drift is concentrated in small stocks and negative news, and **strategy returns decline as LLM adoption rises** [S24]. Neither situation applies to an NQ index future at 1-minute horizons.
- **Look-ahead and memorization:** an LLM tested on dates inside its training window can "know" the outcome. Masking names or dates does not fix it, and only post-cutoff data is a valid test (Lopez-Lira, Tang & Zhu 2025 [S26]). Company knowledge can also distract the model (Glasserman & Lin [S25]). Any LLM backtest on 2020-2026 news with a current model is therefore contaminated by construction.
- Long-horizon evaluation: LLM timing strategies lose their reported edge over 20 years and 100+ symbols (FINSABER [S27]).
- Live anecdote: in Alpha Arena season 1 (Oct-Nov 2025, $10k each, real crypto perps), 4 of 6 frontier LLMs lost money in 17 days. The organisers themselves warn the test had no statistical controls [S28].
- Regulators warn that AI "can't predict the future or sudden market changes" and that AI trading-bot claims are a common fraud vector (CFTC, Jan 2024 [S31]; SEC "AI washing" actions, Mar 2024 [S32]).

**Bottom line on news:** use it to *avoid* risk, not to predict.
1. Automate the scheduled calendar: FOMC, minutes, CPI, NFP from official schedules into `NewsTimes`, so 2027 dates are not typed by hand.
2. Optional experiment: an "unscheduled shock" pause (headline keywords or LLM severity score from a $25-200/mo feed). Run it in **shadow mode for ≥ 6 months**, logging what it would have paused and the P&L of those trades. Adopt it only if it passes the same gates as any rule (it must be tested on post-cutoff data only).

### B3. "An AI brain that keeps improving itself"

**What the literature says**
- Markets are non-stationary (concept drift [S21]; adaptive markets), so models do need to be re-checked over time. But finance has very low signal-to-noise and few independent samples. Re-fitting more often mostly fits noise (Arnott, Harvey & Markowitz [S7]).
- López de Prado lists the standard reasons ML funds fail: backtest overfitting, cross-validation leakage, non-IID labels, and the lone-researcher "Sisyphus" setup [S6].
- Kelly, Malamud & Zhou [S23] show that complex models *can* help. Their setting is monthly market timing with decades of data and disciplined rolling estimation, not ~380 effective days of intraday NQ.
- ML systems pick up hidden feedback loops, entanglement and configuration debt (Sculley et al. [S22]).
- Model-risk practice (Fed SR 11-7 [S17]) requires independent "effective challenge", ongoing monitoring, outcomes analysis and controlled change.
- Knight Capital lost $460M in 45 minutes from an uncontrolled code deployment [S16]. A self-modifying trading system is that failure mode by design.

**What this project already shows.** Every adaptive layer failed out of sample:

| Adaptive idea tried | Result |
|---|---|
| ML meta-labeling, HGB 34 features (`ml26.py`) | OOS PF ~1.0 |
| Meta-model on 16 primary strategies (`meta5.py`) | 2026 PF 0.91 |
| ML meta-labeling on 16 years (Databento) | failed walk-forward |
| Walk-forward rotation of 93 streams | 88% of variants negative |
| Equity-curve module switching (last 20/40/60 trades) | Sharpe 3.41 → 2.98-3.18 (worse) |
| Per-module IS-optimised filters / weights (`optA.py`, `optB.py`, `eval_opt.py`) | IS Sharpe 2.84 → 3.64, OOS flat |
| Context-filter mining (`ctxmine.py`) | IS vs OOS correlation 0.04 |
| ~2,550 exit/filter tweaks (`wrq_*`) | IS→OOS gain correlation ~0.0-0.1, PBO ~0.56; 4 kept |
| Order-flow size boost (`of_validate.py`) | worked Apr-Oct 2026, failed on 11 new months |
| Joint sizing-policy search (`gate_joint.py`) | IS 97% pass → OOS 56-81% |

**Why "self-improvement" cannot be verified at a useful pace.** With daily returns roughly iid, the standard error of the *difference* in annualised Sharpe between a champion and a challenger with correlation ρ over T years is about √(2(1−ρ)/T). Reaching t = 2 needs T ≈ 8(1−ρ)/ΔSR² years:

| Challenger vs champion correlation ρ | True improvement ΔSR = 0.3 | ΔSR = 0.5 |
|---|---|---|
| 0.80 | 17.8 years | 6.4 years |
| 0.90 | 8.9 years | 3.2 years |
| 0.95 | 4.4 years | 1.6 years |

The project's own CUSUM needs ~92-158 trading days just to detect a dead or negative edge.
An AI that retrains weekly and keeps whatever "looks better" would be choosing almost entirely on noise. That is exactly the IS→OOS behaviour measured above.
It would also break the property validated on 2026-10-09: NT and research agree on 96% of trades.

**Safe architecture (what "improving" should mean)**
1. **Frozen champion** in NinjaTrader (versioned, reconciled daily).
2. **Offline research loop** in Python on a fixed cadence (quarterly). Candidates come from a human-written hypothesis or an ML/LLM-generated idea, and every trial is written to the registry.
3. **Pre-registered promotion gates:**
   - minimum trades
   - PF and Sharpe on IS, C24, REAL and 2010-19 cost-normalised
   - DSR using the *total* trial count
   - PBO < 0.2
   - +4 ticks stress
   - permutation p < 0.05
   - **≥ 3-6 months in shadow mode** on live data, with the replica computing what the challenger would have traded
4. **Human approval** with a written rationale. Release through the change-management checklist; rollback = previous version.
5. **Monitoring:** CUSUM, live reconciliation, pre-trade caps, kill switch.
6. **Safe roles for an LLM:** coding assistant, code review, log and incident triage, nightly report writing, literature search, hypothesis generation. **Not** live parameter changes, and not a trading decision engine.

### B4. Recommended architecture and phased plan

```
                 +-----------------------------+
 Official BLS/   |  Python "sidecar" (Windows   |  Telegram / e-mail
 Fed/BEA  ------>|  service, same PC or 2nd PC) |----------------------> Federico (phone)
 calendars       |  - calendar -> NewsTimes     |
                 |  - heartbeat + log watchdog  |<---- NT logs, Output, trace, executions export
 Databento /     |  - nightly reconciliation    |
 NT exports ---->|  - edge/slippage dashboard   |
                 |  - shadow challengers (no    |
                 |    orders)                   |
                 +-------------+---------------+
                               | files only: pause_trading.txt, NewsTimes,
                               | session-start params (read at 18:00 ET, never intraday)
                               v
                 +-----------------------------+
                 | NinjaTrader 8 (execution)    |---> Lucid (CQG/Tradovate) / MFFU (Tradovate)
                 | NQMaster + GoldMaster v1.0   |
                 | all order logic, stops,      |
                 | rule guards, caps, kill      |
                 +-----------------------------+
 Offline (separate, quarterly): research repo + trial registry + gates --> human approval --> new versioned release
```

| Phase | When / effort | Build | Keep in NinjaTrader | Cost |
|---|---|---|---|---|
| **0. Freeze and harden** | Now – 2 weeks; ~10-20 h | v1.0 tag. Compile + golden Strategy Analyzer regression (`nt_compare.py`). Version printed at start. Explicit `ConnectionLossHandling`. `MaxNetContracts` / order-rate caps. Disconnect drill on Sim. Runbook. Written questions to Lucid and MFFU (VPS; Python-assisted NT; MFFU news wording). UPS + 4G/5G failover. | Everything | ~$150-400 one-off hardware |
| **1. Operations sidecar (Python)** | Weeks 2-8; ~40-80 h | Log tailer + heartbeat → phone alerts. Nightly live-vs-replica reconciliation (missed/extra trades, slippage per order type). Calendar auto-update into `NewsTimes`. Dashboard (edge CUSUM, per-module P&L, slippage). | Execution, risk, all signals | ~$0-30/mo (+ VPS only if the firms OK it; vendor prices typically tens to ~$150/mo, unverified) |
| **2. Research platform with gates** | Months 2-6; ~80-150 h | Machine-readable trial registry. Automatic DSR / PBO / permutation report per candidate. Sealed forward holdout. Champion/challenger shadow runner on live data. Purged CV / CPCV for any ML. Quarterly promotion review. | Same | Databento $199/mo optional (NT exports may be enough). LLM API for assistant tasks, low |
| **3. Optional own-brokerage Python execution** | After ≥ 6 months of live evidence; ~150-300 h | Port the frozen champion to Python (IBKR `ib_async` or Rithmic `async_rithmic`). Run it in parallel on paper, then a small account sized by vol target. Reconcile against NT. | Prop accounts stay on NT | Rithmic API $125/mo or IBKR data; capital ≈ $41k per base contract |
| **Not recommended** | — | A self-modifying online-learning bot in the live loop. News-reaction alpha. LLM-sentiment trading of NQ intraday. Routing core orders through ATI/OIF. | — | — |

**Realistic vs hype**

| Claim | Assessment |
|---|---|
| "ML on past trades will find what we missed" | Tried 3 times plus ~2,550 tweaks and context mining; out-of-sample gain ≈ 0. Possible in principle with new, independent data, not with more fitting of the same 380 effective days. |
| "Real-time news gives an edge" | At retail latency, no (5 ms institutional reaction; own tick test). Yes as a risk filter, and the scheduled part is already done. |
| "AI that keeps improving itself" | Improvements of realistic size cannot be verified in less than years. Self-modification would wipe out the validated NT ↔ research agreement and adds Knight-type deployment risk. |
| "Python gives more control than NinjaTrader" | True for research and operations (already the case). For prop execution it is mostly *less* available (no documented API at MFFU; Rithmic conformance at Lucid). |
| "A Python operations layer, gates and monitoring will make the existing edge safer to run" | **Realistic and the highest-value next step.** |

---

## Sources

Academic and practitioner literature
- [S1] Bailey, Borwein, López de Prado & Zhu (2017), "The Probability of Backtest Overfitting", *Journal of Computational Finance* 20(4). https://papers.ssrn.com/abstract=2326253
- [S2] Bailey & López de Prado (2014), "The Deflated Sharpe Ratio", *Journal of Portfolio Management* 40(5). https://papers.ssrn.com/abstract=2460551
- [S3] Harvey, Liu & Zhu (2016), "…and the Cross-Section of Expected Returns", *Review of Financial Studies* 29(1). https://papers.ssrn.com/abstract=2513152 ; https://www.nber.org/papers/w20592
- [S4] Harvey & Liu (2015), "Backtesting", *Journal of Portfolio Management* (Fall 2015). https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF
- [S5] López de Prado (2018), *Advances in Financial Machine Learning*, Wiley (purged CV, CPCV, meta-labeling, backtest overfitting). Book.
- [S6] López de Prado (2018), "The 10 Reasons Most Machine Learning Funds Fail", *JPM* 44(6). https://www.garp.org/hubfs/Whitepapers/a1Z1W0000054x6lUAA.pdf
- [S7] Arnott, Harvey & Markowitz (2019), "A Backtesting Protocol in the Era of Machine Learning", *Journal of Financial Data Science* 1(1). https://papers.ssrn.com/abstract=3275654
- [S8] Aronson (2006), *Evidence-Based Technical Analysis*, Wiley. Review: https://www.cxoadvisory.com/technical-trading/evidence-based-technical-analysis-applying-the-scientific-method-and-statistical-inference-to-trading-signals-chapter-by-chapter-review
- [S9] Pardo (2008), *The Evaluation and Optimization of Trading Strategies*, 2nd ed., Wiley (walk-forward analysis). Book.
- [S10] Carver (2015), *Systematic Trading*, Harriman House (vol targeting, forecast and instrument diversification). https://harriman-house.com/systematic-trading
- [S11] Chan (2013), *Algorithmic Trading: Winning Strategies and Their Rationale*, Wiley; Chan (2021), *Quantitative Trading*, 2nd ed., Wiley. Books.
- [S12] Davey (2014), *Building Winning Algorithmic Trading Systems*, Wiley (Monte Carlo, walk-forward, incubation, random-entry tests). Catalog record: https://emu.tind.io/record/180468
- [S13] Kelly (1956), "A New Interpretation of Information Rate", *Bell System Technical Journal*; MacLean, Thorp & Ziemba (2010), "Good and bad properties of the Kelly criterion", *Quantitative Finance*. Papers.
- [S14] White (2000), "A Reality Check for Data Snooping", *Econometrica* 68(5). Paper.
- [S21] Gama, Žliobaitė, Bifet, Pechenizkiy & Bouchachia (2014), "A Survey on Concept Drift Adaptation", *ACM Computing Surveys* 46(4), doi 10.1145/2523813. https://research.tue.nl/en/publications/a-survey-on-concept-drift-adaptation/
- [S22] Sculley et al. (2015), "Hidden Technical Debt in Machine Learning Systems", NeurIPS. https://proceedings.neurips.cc/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf
- [S23] Kelly, Malamud & Zhou (2024), "The Virtue of Complexity in Return Prediction", *Journal of Finance* 79(1). https://www.sfi.ch/en/publications/the-virtue-of-complexity-in-return-prediction
- [S24] Lopez-Lira & Tang, "Can ChatGPT Forecast Stock Price Movements?", arXiv 2304.07619 v6 (revised Oct 2025). https://arxiv.org/abs/2304.07619v6
- [S25] Glasserman & Lin (2023), "Assessing Look-Ahead Bias in Stock Return Predictions Generated by GPT Sentiment Analysis", arXiv 2309.17322. https://arxiv.org/abs/2309.17322
- [S26] Lopez-Lira, Tang & Zhu (2025), "The Memorization Problem: Can We Trust LLMs' Economic Forecasts?", arXiv 2504.14765 / SSRN 5217505. https://arxiv.org/html/2504.14765v2
- [S27] Li, Kim, Cucuringu & Ma, "Can LLM-based Financial Investing Strategies Outperform the Market in Long Run?" (FINSABER), arXiv 2505.07078 (v5 Feb 2026). https://arxiv.org/abs/2505.07078
- [S28] Alpha Arena season 1 coverage (Oct 18 – Nov 3, 2025). https://www.gncrypto.news/news/qwen-wins-alpha-arena-season-1-with-22-percent-returns/
- [S29] Chordia, Green & Kottimukkalur (2018), "Rent Seeking by Low-Latency Traders: Evidence from Trading on Macroeconomic Announcements", *RFS* 31(12). https://ideas.repec.org/a/oup/rfinst/v31y2018i12p4650-4687..html

Regulation, industry practice and incidents
- [S15] FIA (July 2024), "Best Practices for Automated Trading Risk Controls and System Safeguards". https://fia.org/sites/default/files/2024-07/FIA_WP_AUTOMATED%20TRADING%20RISK%20CONTROLS_FINAL_0.pdf
- [S16] SEC (2013-10-16), Knight Capital settlement, press release 2013-222. https://www.sec.gov/news/press-release/2013-222
- [S17] Federal Reserve SR 11-7, "Guidance on Model Risk Management" (2011). https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm
- [S18] Commission Delegated Regulation (EU) 2017/589 (MiFID II RTS 6, algorithmic trading controls, kill functionality). https://eur-lex.europa.eu/eli/reg_del/2017/589/oj
- [S31] CFTC Customer Advisory (2024-01-25), "AI Won't Turn Trading Bots into Money Machines". https://www.cftc.gov/LearnAndProtect/AdvisoriesAndArticles/AITradingBots.html
- [S32] SEC press release 2024-36 (2024-03-18), "AI washing" charges. https://www.sec.gov/newsroom/press-releases/2024-36

Platforms, prop firms and brokers
- [S19] NinjaTrader 8 help, `ConnectionLossHandling`. https://ninjatrader.com/support/helpGuides/nt8/connectionlosshandling.htm
- [S20] NinjaTrader forum (support staff): historical fill processing, High fill resolution vs Tick Replay. https://forum.ninjatrader.com/forum/ninjatrader-8/strategy-development/1056413-historical-fill-processing-in-nt8?p=1056451 ; https://forum.ninjatrader.com/forum/ninjatrader-8/strategy-development/106295-tick-replay-backtest-and-order-fill?p=1044049
- [S52] NinjaTrader 8 help, File Interface (ATI Order Instruction Files). https://static.ninjatrader.com/support/helpGuides/nt8/file_interface.htm
- [S33] Lucid Trading help center, "Lucid Trading Supported Platforms" (accessed 2026-10-12). https://intercom.help/lucid-trading/en/articles/11404614-lucid-trading-supported-platforms
- [S34] ProptradingVibes, Lucid platforms / ProjectX (updated 2026-10-11). https://proptradingvibes.com/blog/lucid-trading-projectx-no-longer-supported
- [S35] CrossTrade, "Lucid Trading and AI Workflows for NinjaTrader" (last reviewed 2026-09-23; vendor). https://crosstrade.io/learn/prop-firm-ai-trading/lucid-trading
- [S36] TradersPost, Lucid Trading review (modified 2026-09-28; vendor). https://blog.traderspost.io/article/lucid-trading-review-2025
- [S37] MFFU help center, Fair Play / automation, art. 8444599 (updated 2026-08-24). https://help.myfundedfutures.com/en/articles/8444599
- [S38] MFFU, "Overview of Supported Platforms at MFFU". https://help.myfundedfutures.com/en/articles/8528335-overview-of-supported-platforms-at-mffu
- [S39] MFFU, "Connecting to Different Platforms at MFFU" (2026-08-24). https://help.myfundedfutures.com/en/articles/8528337-connecting-to-different-platforms-at-mffu
- [S40] MFFU, "Copy Trading at MyFundedFutures" (2026-08-24). https://help.myfundedfutures.com/en/articles/10771500-copy-trading-at-myfundedfutures
- [S41] PickMyTrade, "Prop accounts block API automation" (2026-07-08; vendor of a competing bridge). https://pickmytrade.trade/debugging/prop-accounts-block-api-automation/
- [S42] PickMyTrade, "Tradovate API Access Without $1,000 Minimum: 2026 Options" (vendor). https://blog.pickmytrade.trade/tradovate-api-access-without-1000-minimum-2026-options/
- [S43] Tradovate community, "How Do I Access the API?". https://community.tradovate.com/t/how-do-i-access-the-api/2380
- [S44] Tradovate community, CME sub-vendor requirement ~$290/month. https://community.tradovate.com/t/is-cme-sub-vendor-requirement-for-api-access-is-290-per-month/6215
- [S45] Topstep help center, "TopstepX API Access" (ProjectX $29/mo; VPS/VPN banned). https://help.topstep.com/en/articles/11187768
- [S46] `async_rithmic` documentation, "Connecting to Rithmic" (conformance test for production). https://async-rithmic.readthedocs.io/en/stable/connection.html
- [S47] AMP Futures, R|API page ($100/mo + $25 user ID; $0.10/contract). https://www.ampfutures.com/platforms/r-api/
- [S48] AMP FAQ, Rithmic technology fees. https://faq.ampfutures.com/hc/en-us/articles/360060137993-Rithmic-Pricing
- [S49] IBKR Campus, API market data subscriptions. https://www.interactivebrokers.com/campus/ibkr-api-page/market-data-subscriptions/
- [S50] IBKR commissions overview (futures tiered $0.25-0.85, fixed $0.85) and CME fee-offset table (micro E-mini $0.352). https://investors.interactivebrokers.com/en/pricing/commissions-home.php ; https://www.interactivebrokers.co.jp/en/accounts/fees/CME.php
- [S51] Databento, "Updates to subscription pricing" (2026-05-29; CME Standard $199/mo from 2026-06-22). https://databento.com/blog/updates-to-subscription-pricing

News and data vendors
- [S53] Newsquawk pricing and Newsquawk-vs-FinancialJuice comparison (competitor's page for FJ prices). https://newsquawk.com/pricing ; https://www.newsquawk.com/compare/newsquawk-vs-financialjuice
- [S54] Benzinga Pro review 2026 (independent site) and Subger price listing (conflicting tiers). https://daytradingtoolkit.com/reviews/benzinga-pro-review ; https://subger.com/en/service/benzinga-pro-sub
- [S55] Trading Economics API plans (aggregator, unverified). https://apis.io/plans/tradingeconomics/tradingeconomics-plans-pricing/
- [S56] NeuGroup, Bloomberg Terminal 2025 pricing; PageCrawl, terminal alternatives (LSEG ~$22k/yr). https://connect.neugroup.com/public/blogs/bloomberg-terminals-how-much-more-youll-pay-next-year ; https://pagecrawl.io/blog/bloomberg-terminal-alternatives
- [S57] Deutsche Börse, AlphaFlash machine-readable macro news (press release). https://www.deutsche-boerse.com/dbg-en/investor-relations/announcements-and-services/press-releases/Deutsche-B-rse-Launches-Fastest-Algo-News-Feed-with-Macroeconomic-Information-479128

Internal evidence (this repository)
- `claude/memory/ifvg-sniper-nt8-project.md`; `NQMASTER_GUIA.md`; `research/mine/propfirms_2026.md` (Lucid arts. 11404728, 16558826; MFFU arts. 16158363, 13745661).
- Validation and audit: `research/mine/robust_lab.py` / `robust_lab.json`, `audit_dsr.csv`, `audit_final.csv`, `audit_haircut.csv`, `audit_wf_agg.csv`, `audit_neighbours.csv`, `wrq_pbo.py`, `db_long.py` / `db_long.json`, `final3y_*.py|json`, `nt_compare.py`, `research/nt_exports/2026-10-09/`.
- Adaptive / ML attempts: `research/ml26.py`, `research/meta5.py`, `research/ctxmine.py`, `research/optA.py`, `research/mine/rotation.py`, `research/mine/of_validate.py` / `of_validate.json`.
- News and latency: `research/news.py`, `research/mine/news_cost.py`, `research/mine/orb0820_ticks.py` / `orb0820_ticks.json`.
- Sizing numbers in B1/A4 (daily σ $519, annual vol $8.2k, Kelly 4.8 / 3.1 per $10k) computed for this report from `research/mine/final3y_trades.pkl` (Ultra, REAL MNQ 2024-02..2026-09, 657 days).

Caveats: prop-firm rules change often. VPS policy and Python/API permissions at Lucid and MFFU were **not** found in official text and must be confirmed in writing.
Vendor blogs (PickMyTrade, CrossTrade, TradersPost) have commercial interests. News-feed prices come partly from competitor pages or aggregators.
