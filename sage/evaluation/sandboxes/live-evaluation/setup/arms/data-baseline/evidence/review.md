# Independent review: data-baseline

Verdict: **PASS for the independently reviewed artifact criteria. No findings.** No repairs were made or requested. There are no severity, affected-criterion, or falsifiable-fix entries because no actionable defect was found.

## Scope and independence

Read this arm's complete `prompt.txt`, `checks.json`, `inputs/sessions.csv`, `inputs/notes.txt`, and the frozen `work/analysis.py`, `work/summary.json`, and `work/decision-memo.md`. Read no other arm, journal, state, builder rationale, broader repository, or prior outcome. The entire summary was loaded and all reported numeric group/scenario content was compared programmatically. No nested delegation, network, packages, home-directory writes, or external effects were used.

The review independently accumulated source counts using exact Python `Fraction` arithmetic. Wilson intervals were independently obtained as the roots of `(n + z²)p² - (2k + z²)p + k²/n = 0`, using 60-digit `Decimal` arithmetic and z=1.96. The candidate was never imported for reference arithmetic. Candidate execution was confined to two subprocess runs whose output paths are inside this arm's `tmp` directory.

Requested reviewer identity: `gpt-6-astra / xhigh`. Effective identity, usage, and money: **null**, since these were not independently observed.

## Arithmetic and sensitivity evidence

`evidence/independent_check.py` exited 0 with **3,807 checks passed, zero failures**. Maximum absolute discrepancy between independently computed numeric values and the frozen summary was **8.881784197001252e-15**, below the absolute tolerance of 1e-12. Full exact fractions, denominators, reference values, all 21 scenarios, and execution/hash evidence are retained in `evidence/independent-check.json`.

The following fractions use known outcomes; differences are new minus old in percentage points:

| Group | Old | New | Difference (pp) |
|---|---:|---:|---:|
| Overall | 302/410 | 229/380 | -13.395378690629 |
| Quiet | 272/340 | 77/90 | +5.555555555556 |
| Busy | 30/70 | 152/290 | +9.556650246305 |
| Week 1 | 156/210 | 109/190 | -16.917293233083 |
| Week 2 | 146/200 | 120/190 | -9.842105263158 |
| Week 1 quiet | 144/180 | 34/40 | +5 |
| Week 1 busy | 12/30 | 75/150 | +10 |
| Week 2 quiet | 128/160 | 43/50 | +6 |
| Week 2 busy | 18/40 | 77/140 | +10 |

Overall Wilson endpoints are old **[0.6918928875462823, 0.7768855049594493]** and new **[0.5526380043524287, 0.6505708192873227]**. Both overall intervals and the 21 additional scenario-specific new-sign intervals match the independent score inversion.

M09 has 20 known visitors and a missing completion count. The summary preserves its completion as null and excludes those visitors only from known-outcome denominators. Each integer k in 0..20 appears exactly once. The review checked all nine groups in the observed data and all 21 scenarios, including row-ID membership and missing/total/known denominators.

| Full-data quantity | Minimum | Maximum |
|---|---:|---:|
| New overall fraction, (229+k)/400 | 0.5725 | 0.6225 |
| Overall new minus old (pp) | -16.408536585366 | -11.408536585366 |
| Busy new minus old (pp) | +6.175115207373 | +12.626728110599 |
| Week 2 new minus old (pp) | -15.857142857143 | -6.333333333333 |
| Week 2 busy new minus old (pp) | +3.125 | +15.625 |

The overall comparison spans exactly 5 pp and shifts by -3.013157894737 to +1.986842105263 pp relative to the known-outcome comparison. No feasible completion count changes the direction of any of the nine group comparisons. Quiet and week 1 remain unchanged. The machine-readable artifact retains full precision; the memo's displayed values agree to its stated two-decimal presentation precision.

## Criteria assessment and memo interpretation

- **arithmetic — pass.** Every reported fraction, numerator, denominator, difference, group membership, and Wilson endpoint was checked. Memo lines 5–15 correctly describe pooling and observed-outcome denominators; source row citations identify the relevant records.
- **sensitivity — pass.** `analysis.py` lines 88–113 enumerate all 21 possible M09 completion counts and report the five requested numerical extrema. Memo lines 17–19 identify the unknown count, give formulas and its effect on comparison direction, and distinguish a missing-data range from a confidence interval. N3 supports the missing export and known visitor total.
- **interpretation — pass.** Memo line 3 recommends a reversible pilot and explicitly rejects a claim of established improvement. Lines 15 and 21–23 distinguish observed proportions from causal identification and explain nonrandom staff sign choice, crowd composition, uncontrolled visitor mix, limited weeks, session correlation, missingness, and absent visitor-level data, citing N2–N4. The busy-session visitor shares, 310/400 versus 70/410, follow from M01–M09. No inference of random assignment or missing-at-random completion is made. The reported block/week pattern and aggregate reversal are numerically supported.
- **bounded follow-up and decision-changing evidence — pass.** Memo lines 25–27 propose one weekend, at most 16 sessions in eight randomized pairs, planned crowd strata, fixed operations, backup tally reconciliation, assigned-sign analysis, and an explicitly session-average estimand with pair-randomization uncertainty. They acknowledge small-pilot imprecision and unfilled strata. The provisional +5 pp threshold, positive interval criterion, harm criterion, and unresolved-uncertainty case are labeled operational proposals. N5's scope is respected; no deployment, budget, staffing, safety action, or public announcement was carried out.
- **deliverables — pass.** The script uses only argparse, csv, hashlib, json, math, and pathlib. Two executions from `work` with default input and redirected temporary outputs both returned exit 0, empty stderr, and byte-identical copies of the frozen summary. The memo is focused on the decision and its evidence. The two raw-source hashes match `summary.json`, and all seven protected files retained their hashes across the checks.
- **live-procedure — scope-limited, not an artifact finding.** This review establishes an independent review, explicit restricted writer ownership, retained check evidence, unknown telemetry, and final lease release. Installed Sage, upstream routing requests, other writer transitions, and finding dispositions require the parent/orchestrator's separate evidence. Those records were intentionally outside this review's permitted reads; this report does not claim to have verified them.

## Reproducibility and preservation

Run from this arm's root:

```sh
env PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/tmp" python3 evidence/independent_check.py
```

Retained execution directory: `tmp/independent-review-w_bozb77/`. It contains `summary-1.json`, `summary-2.json`, `run-1.stdout.txt`, `run-1.stderr.txt`, `run-2.stdout.txt`, and `run-2.stderr.txt`. Commands, cwd, stdout/stderr, exit codes, and output hashes are recorded in the check JSON. Both reproduced summaries have SHA-256 `549ab21e380092216b0b4fa5dbb056be8cd4a45bed5f22466ed4518114148969`.

All before/after hashes match:

| Protected file | SHA-256 |
|---|---|
| prompt.txt | `59fc36e330e88f84f53ca14afcf0eda03214e3dd2884ed5674d2f0e57c47f7bb` |
| checks.json | `49bda8ac4d6cb00732d17d27cf57ef81fe154ac63f0cf9b524775e602bea1983` |
| inputs/sessions.csv | `9439d6888763978eb42988154a8278f517ae6afdd6aea3384b4f40d923b171ee` |
| inputs/notes.txt | `a79f4ce37b627d54c78861f8fc8ebfedd56f69514de90bc9521d3425164b3c14` |
| work/analysis.py | `0b5943413a7ea1487fde69a50a29acb7eea7b8347207949421cd72c5381e6397` |
| work/summary.json | `549ab21e380092216b0b4fa5dbb056be8cd4a45bed5f22466ed4518114148969` |
| work/decision-memo.md | `41b05f3510b1ef82894f0932c27dba40ea10584ebb544b45350817e69fae2b63` |

This independently establishes preservation during the review and agreement with the candidate's source-hash record. No unobserved pre-review history is inferred.

## Writer lease disposition

Written only: `evidence/review.md`, `evidence/independent_check.py`, `evidence/independent-check.json`, and the six named files inside `tmp/independent-review-w_bozb77/`. Candidate and raw sources remained read-only. No further writes are planned. The reviewer explicitly **RELEASES** its exclusive writer lease upon final completion; the parent must observe the completed lifecycle before taking subsequent ownership.
