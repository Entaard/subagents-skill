# Why recent Codex usage was so large, and how Sage should change

**Investigation date:** 2026-09-02 (Asia/Ho_Chi_Minh)  
**Scope:** local Codex and Claude Code telemetry, `ccusage`, the current Codex Sage skill, the Claude-Sage skill and its notes/memory, plus official OpenAI and Anthropic documentation.

## Executive conclusion

The Codex quota drop is real and is explained by the interaction of four measured factors:

1. A small number of long autonomous roots made thousands of model/tool cycles. Each cycle sent much of the live conversation again, so a five-turn user conversation could generate hundreds of model invocations.
2. GPT-5.6 Sol handled 76% of recent Codex token volume, and the four largest roots were Sol at `max` reasoning. Sol is inexpensive relative to top Claude API models, but it is the most expensive GPT-5.6 Codex tier and its cached input is 20 times the Codex credit rate of Luna.
3. Sage-style fan-out multiplied the work: 33 explicit subagent rollouts were visible. The largest Sage-related work groups regularly contained six or seven children.
4. The Codex runs repeatedly carried large contexts through long phases and 27 compactions. Compaction was a marker of sessions that had already become very long; it did not reset cumulative usage.

The apparent price paradox is therefore not a paradox. A cheaper token does not compensate for many more model calls, repeated 200K-class prompts, Sol/max placement, and several concurrent workers. The $100 subscription is also not a $100 API-credit wallet, so API-equivalent dollar proxies cannot be compared with the weekly subscription percentage.

The comparison with Claude needs care:

- There was no bounded-project Claude Code usage in the exact Aug 31–Sep 2 Codex window.
- The nearest high-confidence Claude-Sage cohort, Aug 27–29, was larger in total: about 930.0M raw tokens across 20 parent sessions and 76 active child transcripts, versus about 473.6M Codex tokens across 86 rollouts.
- Recent Codex work was nevertheless denser per large work group. The five largest Codex Sage-related groups averaged 73.9M tokens; the marked Claude-Sage cohort averaged 46.5M per parent-plus-children group, while its median representative group was 29.4M. These are workload indicators, not a controlled efficiency benchmark.

The context-window finding is the most important Sage design issue:

- The current Codex host does not expose a 284K effective window. Local model metadata says 272,000 configured tokens and live token events say 258,400 effective tokens, exactly 95% of the configured value.
- Across 27 recent Codex compactions, the last recorded pre-compaction request had a median 222,972 input tokens, or 86.3% of the 258,400 effective window. The range was 71.3%–95.9%, so “Codex compacts at 90%” is a useful approximation, not a stable contract.
- Claude-Sage’s 30% handover policy is about 301,914 tokens on its locally measured 1,006,380-token window. The same rule on current Codex would fire at 77,520 tokens—roughly 145K before the recent median pre-compaction observation.
- The current Codex Sage implementation does not automatically fire that rule because its declared native adapter has no supported occupied-token/window sensor. Blindly enabling the same percentage would create the opposite problem: premature handovers, cold-start rehydration, and overlapping root/successor work.

Sage should therefore replace the portable “30% occupied” rule with a host-adaptive absolute-headroom policy, add a trustworthy Codex telemetry adapter, separate live occupancy from cumulative spend, and make model/fan-out/cycle rails first-class.

## 1. What the Codex telemetry says

The initial report in [`codex-massive-usage.md`](codex-massive-usage.md) captured 456.04M tokens and a $301.97 `ccusage` proxy. Usage continued during this investigation, so the later daily snapshot reached 473.63M tokens and $314.46. This is ordinary snapshot drift, not a retrospective change to old sessions.

### Daily totals

| Local day | Total tokens | Cached input | Uncached input | Output | `ccusage` proxy |
|---|---:|---:|---:|---:|---:|
| 2026-08-31 | 130.20M | 121.08M | 8.32M | 0.80M | $77.80 |
| 2026-09-01 | 322.30M | 310.21M | 10.70M | 1.39M | $221.64 |
| 2026-09-02 snapshot | 21.13M | 19.93M | 1.10M | 0.10M | $15.02 |
| **Total** | **473.63M** | **451.21M** | **20.12M** | **2.30M** | **$314.46** |

Reasoning output was about 0.998M tokens and is a subset of the model-output accounting rather than an additional amount to add to the total.

### Concentration by model

| Model | Tokens | Share | Interpretation |
|---|---:|---:|---|
| GPT-5.6 Sol | 359.66M | 76.0% | Dominant volume and dominant quota-weighted cost |
| GPT-5.6 Luna | 65.43M | 13.8% | High-volume low-cost work |
| GPT-5.6 Terra | 40.03M | 8.5% | Underused relative to its intended everyday-workhorse role |
| GPT-5.5 fallback reviews | 8.33M | 1.8% | Automatic review fallback |
| GPT-5.4 mini | 0.17M | <0.1% | Negligible |

The current machine default is Sol with `xhigh` reasoning, but the four largest roots recorded Sol with `max`, showing that per-session placement or earlier settings escalated beyond the current default.

### Execution shape

The recent corpus contained 86 rollout files; 84 completed/parseable rollouts classified as 32 user roots, 33 explicit subagents, and 19 automatic guardian reviews. Across those parseable files:

| Signal | Measured amount | What it means |
|---|---:|---|
| Reasoning/model-response records | 5,301 | A proxy for autonomous model cycles, not a guaranteed billable-request count |
| Tool calls | 4,035 | Each tool round can cause another large model request |
| Compactions | 27 | Long sessions crossed the host’s context-management boundary repeatedly |
| Cached share | 95.3% | Most input volume was old context replayed to another model call |
| Fast-mode files | 0 | Fast mode did not cause this spike |
| Guardian-review tokens | 8.26M | Only about 1.7% of tokens; not a primary cause |

The four largest individual roots alone contributed about 196.8M tokens, or 41.6% of the snapshot. They had only two to five user turns each but 273–583 model-response records and 236–453 tool calls. That is the central mechanism: “one user turn” was a long-running agent loop, not one request and one answer.

### Quota evidence

Local rate-limit events show the weekly Codex meter reaching 65%, then 66%, then 67% during Sep 2, with `service_tier: "default"`. The meter is authoritative for remaining subscription usage. The local token totals explain where activity concentrated, but OpenAI does not publish a denominator that converts this account’s included weekly percentage into API dollars.

## 2. Was Codex actually larger than Claude-Sage?

There is no single honest yes/no answer without defining the comparison unit.

| Comparison | Codex | Claude Code / Claude-Sage | Verdict |
|---|---:|---:|---|
| Same Aug 31–Sep 2 wall-clock window | 473.63M | 0 in the bounded project | No simultaneous Claude workload existed |
| Nearest marked Sage cohort | 473.63M across 86 rollouts | 930.04M across 20 parents + 76 active child transcripts | Claude cohort was larger in aggregate |
| Large-work-group intensity | Top five Codex groups: mean 73.9M, median 86.5M | Marked Claude groups: mean 46.5M; representative p50 29.4M | Recent Codex groups were denser |
| API-equivalent proxy | `ccusage`: $314.46, with known price-table caveats | Illustrative cohort proxy: $2,410, with unverified future-style model mapping | Neither is subscription billing; do not compare directly |

The marked Claude cohort contained approximately:

- 15K ordinary input tokens;
- 32.85M cache-creation tokens;
- 891.08M cache-read tokens;
- 6.10M output tokens.

Like Codex, Claude-Sage was dominated by context caching and repeated reads, not by the small “ordinary input” counter. Its parent layer was mostly `claude-opus-5`; its children also used Fable, Sonnet, and Haiku.

The user’s impression is therefore directionally supported at the per-large-run level, but not as a statement about the whole available Claude-Sage corpus. A controlled efficiency claim would require matched tasks, identical acceptance criteria, equivalent model-quality targets, and a consistent accounting method.

## 3. Why cheaper GPT pricing did not protect the quota

Official OpenAI documentation currently lists ChatGPT/Codex credit rates per million tokens of 100/10/500 for Sol input/cached/output, 50/5/300 for Terra, and 5/0.5/30 for Luna. Thus, within Codex:

- Sol cached input costs 2× Terra and 20× Luna credits.
- Sol ordinary input costs 2× Terra and 20× Luna credits.
- Sol output costs about 1.67× Terra and 16.67× Luna credits.

The official API rate card tells the same relative story: Sol is $4/$0.40/$20 per million input/cached/output, while Luna is $0.20/$0.02/$1.20. See the [GPT-5.6 model comparison](https://developers.openai.com/api/docs/models/compare) and [Codex pricing](https://learn.chatgpt.com/docs/pricing).

So “GPT is cheaper than Claude” is true only per comparable API token. Four effects overwhelmed it here:

1. Sol, not Luna, carried three quarters of the volume.
2. A few roots made hundreds of calls and repeatedly reread 100K–240K-class prompts.
3. Subagents created independent contexts and their own tool loops.
4. Subscription quota weights, rolling limits, and included allowances are provider-specific and are not API-dollar balances.

`ccusage` remains useful for token/category/session comparisons. Its dollar column is an API-equivalent proxy whose model table and semantics can lag the live Codex credit system.

## 4. What Sage contributed—with and without explicit `$sage`

### Without Sage

Codex can still become expensive because the machine default is a high-end model at high reasoning, a single user turn can run hundreds of tool/model cycles, and no native token or quota rail stops a long autonomous root. Several non-Sage roots exist in the corpus. The base failure mode is therefore **unbounded cycle count × growing cached prompt × expensive placement**.

### With Sage or Sage-shaped development work

Sage adds useful independence and context isolation, but it also deliberately buys more work:

- multiple bounded readers or implementers;
- independent Standards and Spec review;
- adversarial verification;
- fix verification and dry rounds;
- fresh-context children that reread their assigned corpus;
- quality-first placement when ambiguity is high.

The Claude-Sage notes explicitly record a quality-first preference and a 4× estimate ceiling, together with the warning that raised ceilings tend to be consumed. The promoted memory also records that a dry verification round is not cheap because it must reread the corpus. These are sensible reliability policies, not cost-minimization policies.

The current Codex Sage skill is more explicit about bounded admission and model placement, but two limitations remain:

1. Its Light-mode spend sensor is `unknown`, so token/cost caps are advisory or absent. Finite agents, attempts, concurrency, revisions, and admission time are the real stops.
2. Its automatic 30% handover is disabled unless one supported sensor supplies both occupancy and effective window. The native collaboration API does not currently supply that pair.

Not every expensive recent run was governed by the final Sage skill; several were building, reviewing, or revising Sage itself. The policy should therefore not be credited with controls that did not yet exist, nor blamed for every non-Sage root. What the corpus does show is that Sage-shaped work—many independent seats, repeated review, and long orchestrator sessions—was a major multiplier.

## 5. Context-window and compaction findings

### Four different numbers must not be conflated

| Number | Current evidence | Meaning |
|---|---:|---|
| GPT-5.6 API context maximum | 1,050,000 | Vendor model capability, not the active Codex host budget |
| Codex host configured window | 272,000 | Current local `models_cache.json` value |
| Codex host maximum option | 872,000 | Local host metadata; relationship to the 1.05M API maximum is undocumented |
| Codex effective window | 258,400 | Live `token_count` denominator, equal to 95% of 272K |
| Claude documented maximum | 1,000,000 | Current Claude Opus 5 model maximum |
| Claude-Sage local window | 1,006,380 | Local measured/configured value used by the Sage watchdog |

Official OpenAI documentation gives GPT-5.6 Sol a 1.05M API context and 128K maximum output, and applies a higher long-context price tier beyond 272K input. The active Codex host is nevertheless using a 272K configured window. See [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol). Anthropic documents a 1M context for [Claude Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview).

The user’s approximately 284K observation appears in older local telemetry as a **request occupancy** of 284,810 inside an older 353,400 effective window. It was not that build’s window denominator, and the current build has since changed. Host/build/model metadata must travel with every context number.

### Observed Codex compaction

For the 27 recent compactions, the last recorded request before each compaction was:

| Statistic | Input tokens | Share of 258,400 effective window |
|---|---:|---:|
| Minimum | 184,250 | 71.3% |
| Median | 222,972 | 86.3% |
| Mean | 221,440 | 85.7% |
| Maximum | 247,915 | 95.9% |

These are lower bounds when the request that triggered compaction had not yet emitted a token event. OpenAI documents configurable `model_context_window` and `model_auto_compact_token_limit`, but does not publish the current default threshold percentage in the [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference). The empirical “about 90%” description is reasonable for planning, but not enforceable policy.

Compaction reduces live occupancy; it does not erase already consumed tokens. In one root, cumulative input grew from 11.61M tokens around a 215.7K pre-compaction request to 46.10M by the next compaction. The roughly 34.49M increase is 170.8 times the later pre-compaction request size. This is why a session can have a 258K live window yet accumulate tens of millions of input tokens.

### Why Claude’s 30% rule does not port

| Window basis | 30% handover | 90% occupancy | Distance between them |
|---|---:|---:|---:|
| Claude nominal 1M | 300,000 | 900,000 | 600,000 |
| Claude-Sage local 1,006,380 | 301,914 | 905,742 | 603,828 |
| Hypothesized Codex 284K | 85,200 | 255,600 | 170,400 |
| Current Codex effective 258,400 | 77,520 | 232,560 | 155,040 |

Claude-Sage’s 30% handover is a reliability and context-clarity policy, not a proven cost optimum. It leaves large absolute slack for the parent to write a handoff and supervise in-flight workers. Local notes estimate 5K–8K output tokens for a handoff note and at least about 21 minutes of slack from the threshold to a previously observed lower-bound occupancy under a seven-agent burn rate.

That policy also has costs: a fresh successor must rehydrate artifacts, the original parent remains as supervisor, and both contexts may overlap. An early handover can increase total spend even when it reduces context-loss risk.

On current Codex, 30% means 77.5K—less than many substantial phases and only about one third of the recent median pre-compaction request. Blindly copying the percentage would produce frequent cold starts. Copying Claude’s absolute 302K threshold would never fire. Keeping the current “no supported sensor, no automatic action” behavior avoids false enforcement but lets roots cross several native compactions with no Sage handover.

## 6. Recommended changes to the new Sage skill

### P0 — fix context and telemetry semantics

#### 1. Replace the universal 30% rule with absolute headroom

Define:

```text
remaining = effective_window - current_occupancy
required_headroom = max(
  p95_next_turn_growth,
  2 * bounded_handoff_payload,
  recovery_reserve
)
```

Prepare a checkpoint when `remaining <= required_headroom`. Hand over at a clean phase boundary, or immediately when the headroom rail is breached and another substantive turn is required.

The policy must record how every term was measured. If growth data is unavailable, use a conservative host-specific pilot value and label it estimated.

#### 2. Add a Codex JSONL context sensor, but do not claim support before validation

This machine exposes `CODEX_SESSION_ID` and `CODEX_THREAD_ID`, and the exact root rollout contains a latest `token_count` event with both `last_token_usage.input_tokens` and `model_context_window`. A candidate adapter can bind the environment ID to an exact rollout filename and read the pair from one event.

The adapter should fail closed when the ID is absent, more than one candidate matches, the event is stale, or the numerator/denominator semantics differ. Until fixtures and host-version checks prove those properties, Sage should describe this as an observed local sensor, not a guaranteed Codex capability.

#### 3. Separate three rails

Sage currently risks treating “context” as one number. Record and enforce separately:

- **occupancy rail:** can the next turn fit safely?
- **cumulative spend rail:** how many input/cache/output tokens or credits has the run consumed?
- **progress rail:** did the last cycles close a criterion or produce new evidence?

Compaction resets the first, not the second or third.

### P1 — reduce the measured cost multipliers

#### 4. Change the default model-placement profile

Use:

- Terra medium/high for the root policy actor and substantial everyday synthesis;
- Luna medium for scoped scans, mechanical extraction, and high-volume bounded reads;
- Sol high/xhigh for ambiguous architecture or adjudication;
- Sol `max` only for one narrow, explicitly justified unit with an independent acceptance method.

Every worker must receive an explicit model and effort. Never let a child silently inherit a Sol/max root.

#### 5. Add cycle and compaction rails

Pilot these as observable, retunable defaults:

- advisory replan at 25 root turns or 40 tool calls without criterion closure;
- mandatory replan at 50 tool calls without criterion closure;
- first compaction in a phase: validate and reread durable state;
- second compaction in the same phase: replan or hand over;
- third compaction without criterion progress: stop admissions and surface no-progress.

The recent roots with 236–453 tool calls demonstrate that agent-count caps alone are insufficient.

#### 6. Lower default fan-out

Default to two concurrent children and three total. Expand only when each additional mandate is disjoint, independently checkable, and expected to change a decision. Keep the current principle that zero delegation is valid.

#### 7. Bound worker occupancy and return size

Size a leaf unit to finish below 70% of its own effective window: about 181K on current Codex and about 700K on a 1M Claude host. At the rail, the worker should return a compact result or split a successor unit rather than compacting repeatedly inside a supposedly bounded task.

Cap a handoff payload at:

```text
min(8K tokens, 1% of effective_window)
```

That is about 2,584 tokens on current Codex and 8K on Claude. Store detailed evidence in artifacts and pass locators plus hashes, not transcript replay.

#### 8. Avoid root/successor overlap

After policy authority transfers, the old root should supervise only unresolved native handles and stop substantive analysis/tool work. The successor becomes the sole policy actor. Record overlap tokens and time so the handover’s cost is measurable.

#### 9. Reuse context only where it is cheaper and safe

Claude-Sage memory reports narrow re-verdicts on the same verifier thread as roughly 4–7 times cheaper than fresh full readers. Preserve fresh context for independent initial review, but steer an existing verifier for a tightly scoped recheck when independence from its earlier judgment is not required.

### P2 — make cost policy explicit and testable

#### 10. Replace the blanket 4× compatibility multiplier

The local memory already warns that higher ceilings tend to be consumed. Use a named run profile:

- `economy`: smallest capable models, low fan-out, one review lens unless risk requires more;
- `balanced`: Terra root, Luna readers, risk-based independent review;
- `quality-first`: wider evidence and stronger models, with the projected quota effect surfaced before admission.

The user’s historical quality-first preference can remain a profile, but it should not silently become the Codex default for every task.

#### 11. Record before/after quota observations per phase

Capture `/status` or an equivalent supported quota observation before and after each long phase. Bind it to the phase, root model/effort, children, tool calls, compactions, and cumulative `ccusage` delta. This is the missing dataset needed to convert local token proxies into practical subscription-budget guidance.

#### 12. Run a matched handover experiment

Compare two sets of same-shape tasks:

- early handover using the old 30% rule;
- native compaction inside a phase, with durable checkpointing and handover only at phase/headroom boundaries.

Measure total input/cache/output, root-successor overlap, handoff and rehydration tokens, time to the successor’s first productive action, compactions, defects, recovery failures, and criteria completed. Early handover is better only if the reliability improvement offsets its additional contexts and overlap.

## 7. Proposed telemetry contract

Every context decision should record:

| Field | Why it is required |
|---|---|
| Host, build, model, effort | Window and behavior drift across versions and placements |
| Model maximum | Vendor capability; prevents confusion with host budget |
| Configured and effective windows | The actual denominator and its provenance |
| Current occupancy and semantics | Latest request, body-only, total, or another measure |
| Cumulative input/cache/output | Spend does not reset at compaction |
| Compaction pre/post/duration/trigger | Distinguishes observed behavior from default guarantees |
| Root turns and tool calls | Captures the main amplification mechanism |
| Phase and criterion progress | Makes no-progress falsifiable |
| Handoff payload size | Measures checkpoint overhead |
| Successor rehydration tokens/time | Measures cold-start cost |
| Root-successor overlap | Detects duplicated orchestration spend |

Automatic enforcement is allowed only when numerator and denominator come from one validated sensor and the sensor is bound to the correct native root. Otherwise the run should use explicit checkpoints and report the capability gap.

## 8. Reproducibility and limitations

Core commands:

```sh
ccusage codex daily --json --since 2026-08-31 --until 2026-09-02 --timezone Asia/Ho_Chi_Minh --offline
ccusage codex session --json --since 2026-08-31 --until 2026-09-02 --timezone Asia/Ho_Chi_Minh --offline
ccusage claude daily --since 20260831 --until 20260902 --timezone Asia/Ho_Chi_Minh --json --offline
jq '.models[] | select(.slug == "gpt-5.6-sol") | {context_window,max_context_window,effective_context_window_percent}' ~/.codex/models_cache.json
```

Primary local sources:

- [`codex-massive-usage.md`](codex-massive-usage.md)
- [`sage-claude/SKILL.md`](sage-claude/SKILL.md)
- [`sage-claude/references/harness.md`](sage-claude/references/harness.md)
- [`sage-claude/references/dispatch.md`](sage-claude/references/dispatch.md)
- [`sage-claude/memory/shared`](sage-claude/memory/shared)
- [Claude project memory](/Users/tuananhnguyen/.claude/projects/-Users-tuananhnguyen-Projects-notes-subagents-skill/memory/MEMORY.md)
- [Current Codex Sage mapping](/Users/tuananhnguyen/.agents/skills/sage/references/codex.md)
- [Current Codex model cache](/Users/tuananhnguyen/.codex/models_cache.json)

Material limitations:

- The Codex snapshot changed while this audit ran; exact totals are timestamped observations.
- Local Codex telemetry does not provide dependable parent/work-group linkage for every worker, so some Sage/non-Sage grouping remains inferred.
- Raw Codex and Claude token categories are not fully equivalent.
- Future-style Claude model identifiers in the local corpus lack a verified price mapping.
- OpenAI does not publish the exact weekly subscription denominator or the current default auto-compaction threshold.
- Neither provider’s API-equivalent dollar proxy is the user’s subscription bill.

## Final assessment

The recent Codex spike was not caused by one mysterious billing defect, fast mode, or automatic guardian reviews. It was the predictable product of **Sol/max placement × hundreds of tool/model cycles × repeated large cached contexts × Sage-shaped fan-out**. The smaller active Codex window did not cap cumulative spend; it caused long sessions to compact and continue, while cumulative input kept rising.

Claude-Sage’s 30% handover was designed in a host where 30% is about 302K tokens and leaves hundreds of thousands of tokens of slack. Codex currently has only 258.4K effective tokens. The percentage is therefore not portable. Sage should base handover on measured absolute headroom and phase boundaries, while separately bounding cumulative spend and no-progress cycles. That change, combined with Terra/Luna defaults and strict Sol/max admission, addresses both the context-reliability problem and the quota problem revealed by these runs.
