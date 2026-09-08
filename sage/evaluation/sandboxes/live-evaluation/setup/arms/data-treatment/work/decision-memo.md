# North Pier Museum — queue-sign decision

Recommend the small, reversible new-sign pilot contemplated in N5. These data do **not establish that the sign improves completion**, and do not justify permanent adoption. The within-crowd results make another controlled weekend worth testing; staff-selected assignment prevents a causal conclusion (N2). This is a recommendation only: no scheduling, spending, staffing change or announcement has been performed or authorized (N5).

Completion means reaching the final station; rows contain disjoint visitors (N1). The table uses only rows with observed completion counts. Each percentage is a pooled completed/visitor fraction, not an average of row percentages. Differences are new minus old in absolute percentage points (pp).

| Group | Old: completed/visitors | New: completed/visitors | Difference | Source rows |
|---|---:|---:|---:|---|
| Overall, observed rows | 302/410 = 73.66% | 229/380 = 60.26% | −13.40 pp | M01–M08 |
| Quiet | 272/340 = 80.00% | 77/90 = 85.56% | +5.56 pp | M01, M02, M05, M06 |
| Busy, observed rows | 30/70 = 42.86% | 152/290 = 52.41% | +9.56 pp | M03, M04, M07, M08 |
| Week 1 | 156/210 = 74.29% | 109/190 = 57.37% | −16.92 pp | M01–M04 |
| Week 2, observed rows | 146/200 = 73.00% | 120/190 = 63.16% | −9.84 pp | M05–M08 |

Overall 95% Wilson intervals (z=1.96) are **69.19%–77.69%** for old (302/410) and **55.26%–65.06%** for new among observed rows (229/380). These are descriptive binomial intervals conditional on those observed counts. They neither address M09's missing outcomes nor remove selection bias; shared session conditions can also invalidate the independent-binomial precision assumption. Their separation is not proof that changing the sign causes harm (N2–N4).

M09 contains 20 known visitors and an unrecoverable completion export (N3). It remains explicitly missing. Let its completed count be any integer k from 0 to 20. The full-cohort new fraction is (229+k)/400, or **57.25%–62.25%**, versus old's 73.66%; the difference is **−16.41 to −11.41 pp**. Thus missingness can move that comparison through 5.00 pp, but cannot reverse its sign. Relative to the observed-row comparison, the change ranges from −3.01 to +1.99 pp.

The affected busy comparison becomes (152+k)/310 = 49.03%–55.48%, versus 30/70, a **+6.18 to +12.63 pp** difference. Week 2 becomes (120+k)/210 = 57.14%–66.67%, versus 146/200, a **−15.86 to −6.33 pp** difference. Quiet and week 1 are unchanged. These are sharp count bounds, not confidence intervals or imputations; `summary.json` enumerates all 21 possibilities, including conditional overall Wilson intervals.

The apparent reversal is explained descriptively by crowd composition: busy visits account for 290/380 (76.32%) of observed new-sign visits, but only 70/410 (17.07%) of old-sign visits; including M09 makes new's busy share 310/400 (77.50%). Busy completion is much lower under either sign (M01–M09; N2). Within each week, new also leads in quiet and busy rows; even week-2 busy remains positive across M09's full range (+3.13 to +15.62 pp). Week-level pooling therefore does not solve the crowd imbalance.

Crowd labels were recorded before sessions, but sign choice was not randomized. Adjustment for quiet/busy cannot remove uncontrolled visitor mix, residual crowding or staff selection. Only two weeks and aggregate groups are available, with no visitor-level adjustment or reliable session-dependence estimate. Staffing and route length were reportedly constant, which removes neither remaining confounding nor uncertainty about another exhibit (N2, N4). The missing export is documented, but its missingness mechanism is not established (N3).

Propose one weekend with 16 sessions in eight matched pairs, balanced across preclassified quiet/busy blocks and day/time as feasible. Randomize sign order within each pair before opening, clear the prior group before switching, retain session IDs, and independently reconcile entry/completion counts daily with a backup export. Keep staffing, route and completion definition fixed. Predeclare a visitor-weighted within-block comparison standardized to an equal quiet/busy mix, plus block results and session-randomization-based uncertainty; that mix is a proposed pilot target, not an estimate of the museum's usual traffic.

Before collecting data, provisionally define +5 pp as a practically useful gain. Valid randomized evidence with an interval wholly above +5 pp and no material block-specific harm would support broader adoption; an upper bound below +5 pp would undermine the benefit case, and credible harm would favor the old sign. An inconclusive interval or renewed missingness warrants no efficacy claim. This small weekend may establish feasibility rather than precision; any extension requires a separate decision (N5).

Reproduce with `python3 work/analysis.py` from the arm directory (or use the script's absolute path from anywhere). The stdlib script writes `work/summary.json` deterministically and embeds SHA-256 hashes of both raw sources.
