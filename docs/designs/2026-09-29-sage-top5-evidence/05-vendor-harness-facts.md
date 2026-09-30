# Vendor and harness facts (fetched 2026-09-29, build 2.1.284)

The web agent returned this as text (the harness refused its file write). The parent checked the starred items against the raw sources in this directory.

## harness.md is wrong or stale
1. * `sonnet` = Sonnet 5.5 on 2.1.284 (CHANGELOG.md:5 "Added Claude Sonnet 5.5 (`claude-sonnet-5-5`), now the default Sonnet model"). This account gets HTTP 403 on claude-sonnet-5-5. explorer, web-researcher, implementer (all `model: sonnet`) fail. Sonnet 5 is Legacy, retirement not before 2027-06-30.
2. The Agent tool `model` schema is an alias enum (sonnet|opus|haiku|fable). Alias targets moved: fable 2.1.257, opus 2.1.280, sonnet 2.1.284. The real answer is `resolvedModel` / `modelsUsed` on the Agent result (docs/hooks.md:1754-1765).
3. A saved agent file can pin a full id (`model: claude-sonnet-5`). The per-invocation `model` beats frontmatter, so passing `model: sonnet` to a pinned agent undoes the pin. `ANTHROPIC_DEFAULT_SONNET_MODEL=claude-sonnet-5` repins the alias for a session.
4. * Precedence changed in 2.1.251 (CHANGELOG.md:1745): per-invocation param → frontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → main model. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (2.1.257, CHANGELOG.md:1577) forces one model.
5. * Effort levers: frontmatter; `CLAUDE_CODE_EFFORT_LEVEL` env; `maxEffortLevel` setting caps it (2.1.267, CHANGELOG.md:1273); Workflow `agent()` takes `effort` per call. Agent tool: no effort param.
6. A plain dispatch inherits the session effort (Claude Code default: medium on Opus 5.5 / Sonnet 5.5). So with `/effort xhigh`, every plain dispatch runs xhigh.
7. `run_in_background` is removed from the Agent tool in interactive fork mode.
8. * `omitClaudeMd: true` frontmatter (2.1.271, CHANGELOG.md:974) lets custom agents skip CLAUDE.md. Also new: `experimental.cacheTtl`, `memory`, `color`, `initialPrompt`.
9. `isolation: worktree` branches from the default branch, not HEAD, unless `worktree.baseRef: "head"`. `isolation: "remote"` exists.
10. Agent directories are watched; the next delegation uses an edited definition with no restart (except a first agents dir created after session start, `--add-dir`, `--disable-slash-commands`).
11. `TaskStop` accepts an agent ID or name.
12. Still true: concurrency 20, depth 3, Agent Teams experimental, `--max-budget-usd` halts background agents. New: ultracode sessions exempt from the cap of 20. * Monitor watches have a 30-minute deadline; `persistent` removed (2.1.271, CHANGELOG.md:1035) — sage's watchdog step 3 says `persistent: true`.
13. Prices: Sonnet 5.5 $2/$10, Opus 5.5 $4/$20, Fable 5.1 $10/$50 (1:2:5). Cache reads 1:1:1.25. 1M window, 128K max output.
14. * `SubagentHandback` (auto mode, 2.1.271): the report travels in that tool call; the Agent result's `content` is a short note (docs/hooks.md:1753, tools-reference.md:53). SubagentStop's `last_assistant_message` is not the report. sage-watch's `done` rule ("text block and no tool_use") may misread such a unit — unverified.

## What changes how an orchestration skill should be written
1. * Workflow tool: "who decides what runs next" — subagents: Claude turn by turn; workflows: the script, dozens to hundreds of agents, resumable (docs/workflows.md). `agent()` takes model, effort, schema, isolation, agentType. Opt-in only (user asks, or ultracode). 16 concurrent, 1,000 per run, no mid-run user input, resume same session only. Blog: "dynamic workflows often use more tokens and are best suited for complex, high value tasks"; they combat agentic laziness, self-preferential bias, goal drift.
2. Pin models in agent files; check `resolvedModel` after each dispatch.
3. * Write less instruction. "We removed over 80% of Claude Code's system prompt for models like Claude Opus 5 and Claude Fable 5 with no measurable loss" (blog/cd_the-new-rules-of-context-engineering...txt:49). Then/now: rules → judgement; examples → interface design; everything upfront → progressive disclosure; repeat yourself → simple tool descriptions. "Avoid making them [skills] overconstrained, except in highly important areas." Drop "CRITICAL: You MUST", "think carefully" lines; explicit verification instructions cause over-verification (Opus 5 guide). `/doctor prompt-audit` (2.1.283, CHANGELOG.md:112) audits skills and agents for old-model patterns. After compaction a skill re-attaches only its first 5,000 tokens (25,000 total).
4. * Effort is the main cost/latency control. Opus 5.5 guide: "Start at `medium`, the default on Claude Opus 5.5 ... Claude Opus 5.5 at `medium` matches or exceeds Claude Opus 5 at `high`"; "At a given level, Claude Opus 5.5 tends to think more per turn than Claude Opus 5, especially at `xhigh` and `max`. If you keep the effort value you set for Claude Opus 5, expect longer turns". Effort blog (2026-09-25): one build took 1.5 min at low, 67 min at max; "implementing on low effort, reviewing what it built, and then running verification on high effort"; higher effort "does not fix when the model has the wrong approach".
5. Damp self-delegation: Opus 5 delegates more readily; Sonnet 5.5 at xhigh/max launches its own reviewers; "most traditional coding tasks do not need a panel of 5 reviewers".
6. Maker/checker separation "proves to be a strong lever"; the evaluator is "worth the cost when the task sits beyond what the current model does reliably solo" (anthropic.com/engineering/harness-design-long-running-apps).
7. * Time signals: Opus 5.5 paces to an elapsed-time budget line (`elapsed 340s / 1200s`); teams finished considerably sooner with comparable quality. Text-only end of turn is "a report rather than proof the task is done".
8. The Agent result's `totalTokens` covers only the final request; transcripts remain the source of truth for spend.

## Not found
Version that added the agents-directory watcher; whether Workflow `agent({model})` accepts a full id; whether fallback covers a 403; `.meta.json` schema; whether the parent can trigger `/compact`.

## Source keys
CL = raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md (local: CHANGELOG.md). docs/*.md = code.claude.com/docs/en/*. platform/*.md = platform.claude.com/docs/en/*. blog/* = claude.dev/blog/*, anthropic.com/engineering/*.
