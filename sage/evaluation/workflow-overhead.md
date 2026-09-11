# Workflow overhead experiments (v1, experimental)

Use this lane for new direct-Codex versus Sage trials, or component ablations. The frozen routing-only `pairing.py` v2/v3 protocol and historical scores retain their original interpretation. This document is an experiment procedure, not a completed trial or a new accepted-results protocol.

Before either arm, freeze the original request, raw input files, initial artifact digests, permitted tools/effects, requested root model/effort, acceptance criteria and checks. Keep them identical between arms, except for the declared treatment. Request the same root in both; effective identity remains unknown unless the runtime exposes it. Alternate arm order and use isolated copies. Give a scorer the final artifact and acceptance contract without the arm label or builder rationale. Correctness and absence of major defects take precedence over presentation or token volume.

In a whole-workflow pair, direct Codex is the baseline and installed Sage is the treatment. In a component pair, both arms use the same installed Sage release except for one selected change (checkpoint output, work packets, check bindings, or cards). Route workers identically for component pairs; routing itself needs its separate existing experiment. Never label an adaptation of a historical run a new blinded trial.

## Case matrix

Freeze concrete fixtures and executable checks for each selected case **before execution**. These case definitions are admission criteria, not fabricated prompts/results:

| Case | Required fixture and acceptance observation |
| --- | --- |
| Small task | One bounded file edit with an exact expected diff; verify the edited artifact and measure coordinator setup as well as edit work. |
| Ambiguous multiple-file task | A public interface change with at least two consumers and an explicit unresolved design question; verify both callers, final interface coherence and repair count. |
| Evidence-heavy research | A frozen primary-source corpus with conflicting claims; score source support, contradiction handling, uncertainty and complete coverage using exact source locators. |
| Fix-induced regression | A candidate whose local fix breaks another required behavior; verify that integration detects the regression and that an old pass cannot certify the final artifact. |
| Knowledge invalidation | Prior selected record plus a changed generation/status or qualifier and a distracting higher-ranked result; require exact prior-record invalidation even when top-N omits it. |
| Interrupted promotion | Integrity-valid current generation plus isolated partial staging and an interrupted writer; require effect reconciliation, unchanged current pointer and source validation before a safe retry. |

Record which cases/components were run and which were not. The offline regression suite can supply reproducible failure fixtures, but its pass is not evidence of live model behavior or lower usage. Run components separately before a combined treatment; a combined result cannot identify the causal component.

## Observed usage

`usage.py OBSERVATIONS.json` is a small reporting utility for a supplied observation vector, **not a native telemetry collector or billing meter**. Use it only when source telemetry exists. Preserve that source independently and have the evaluator verify its scope, IDs, model fields and accounting definitions. If it does not exist, record unknown usage and refrain from a total-token comparison.

Input schema `sage-observed-usage-v1` has `tasks` and `requests`. Each task has a unique `id`, boolean `accepted`, `coverage` (`complete|partial|unknown`) and the SHA-256 of its scored artifact. Every request has:

```json
{"id":"native-request-id","task_id":"case-arm-id","attempt":1,"source":"retained-telemetry-locator","model":null,"input_tokens":null,"cached_input_tokens":null,"output_tokens":null,"reasoning_tokens":null,"reasoning_in_output":null,"wall_seconds":null,"kind":"leaf_request"}
```

Use disjoint leaf requests only: exclude parent aggregates, preserve native request IDs, include root synthesis, workers, failed attempts, repairs and review, and identify attempts explicitly. Input includes its cached subset. Set `reasoning_in_output` from that source's definition; reasoning is added only when explicitly outside output. Missing counts/definitions remain unknown. `coverage:complete` is an evaluator assertion that all task requests are present; the utility cannot discover omitted requests or authenticate prose locators. Estimates must stay outside this observed vector.

The summary reports observed tokens as a lower bound, and reports a total and tokens per accepted outcome only with complete task coverage/counts. All failed-attempt usage contributes to the numerator. Only accepted tasks contribute to the denominator; zero accepted tasks gives an undefined (`null`) ratio. Keep per-task outcomes alongside the aggregate. Compare only arms with equivalent coverage; request count, latency, token volume and money remain separate. Prices, subscription percentages and effective model identity cannot be inferred from these totals.

Promotion overhead belongs in a separately labeled task/window. A promoted record has no demonstrated return until qualifying forward cases show its effect; report that window and all costs rather than assuming a positive amortized benefit.

## Release evidence

Capture baseline output sizes before implementation, focused deterministic regressions, the full offline gate, the installed-path gate and a review of the final frozen artifact. Report each separately from the live comparisons. Reversible optional interfaces may ship as uncalibrated improvements; generalized quality, routing or token-saving claims require the live evidence above.
