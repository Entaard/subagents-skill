# Shared ground truth for the sage study (collected by the parent, 2026-09-29)

## Repo and install
- Source repo: /app/code/subagents-skill (git, main, clean). Claude sage source: `sage-claude/` (SKILL.md + references/*.md + bin/*.sh + memory/ seeds). Promotion skill source: `claude-skills/sage-promote/SKILL.md` + `references/memory-contract.md`. Saved agents: `claude-agents/*.md`, alt twins `claude-agents-alt/*.md.in`. Installer `install.sh` (67 KB).
- `sage/` is the separate Codex sage (Python state helper, ~11.6k words). NOT in scope except as a comparison point.
- Installed copy: `~/.claude/skills/sage/` (identical to repo except memory), `~/.claude/skills/sage-promote/`, `~/.claude/agents/*.md`. Installed memory: `~/.claude/skills/sage/memory/` — `journal.md` (live), `archive/journal-*.md` (drained), `local/` (108 files: 56 lesson, 23 defect, 9 band, 5 gap, sidecars), `shared/` (12 KIs).
- Harness: Claude Code 2.1.284. Parent model opus[1m] = Opus 5.5. Settings: auto permission mode; SessionStart(compact) hook; PreToolUse(Agent) hook `sage-alt-guard.sh`.
- Alt lane: `~/.claude/subagents-alt-models.conf` — explorer-alt=api-plan-gpt-6-luna, verifier-alt=api-plan-gpt-6-sol, refuter-alt=api-plan-gpt-6-astra, web-researcher-alt=api-plan-gpt-6-luna.

## Corpus size (words)
- SKILL.md 2402 (cortex budget 2500). Run-loaded budget 20,000 words (SKILL + every step file + script run blocks); last measured 19,974.
- references: dispatch 3700, harness 3047, topologies 2644, execute 2491, verify 1871, record 1346, memory 1254, authoring 1189, decompose 1085, alt-lane 996, harness-measurements 4380.
- bin: sage-lint.sh 16287, sage-watch.sh 8349, sage-alt-guard.sh 1820, sage-index.sh 1730.
- sage-promote SKILL.md 8546 + memory-contract.md 3291.
- Codex sage for comparison: SKILL 515 words, whole skill ~11.6k.

## Harness features that exist in this build but sage does not use
- `Workflow` tool (deterministic multi-agent scripts: agent()/parallel()/pipeline()/phase(), resumable by run id). Sage mentions "workflow" only in harness.md:113 context (sidecar meta). Opt-in requires user words / skill instructions.
- `fork` subagent_type (inherits full parent context) — sage forbids it for reviewers only.
- `isolation: "worktree"` on Agent — sage mentions it for parallel writers.
- `Monitor` tool — sage uses it for the watchdog loop.
- `ScheduleWakeup`, `CronCreate` — unused.

## Session transcripts of /sage runs
Location: `~/.claude/projects/<project-dir>/<session-id>.jsonl`; subagent transcripts at `<session-id>/subagents/agent-<id>.jsonl` + `.meta.json` (agentType, description, spawnDepth). Each session has a `cost-state` record (totalDuration, totalAPIDuration, totalToolDuration, modelUsage per model with outputTokens/cacheRead/cacheCreation/costUSD) and `system/turn_duration` records (durationMs per user turn). Parent thinking blocks are stored with EMPTY text (redacted) — do not try to read reasoning.

Per-session figures (dur = wall incl. idle; api = sum of API time; tool = tool exec time; turns_sum = sum of turn_duration):
| session | project | date | dur | api | tool | turns_sum | $ | parent out tokens |
|---|---|---|---|---|---|---|---|---|
| 42dd56d4 | subagents-skill | 09-03 | 403m | 64m | 3m | 61m | 27 | fable 92k |
| a58bd85c | Testing-Tools | 09-03 | 1010m | 152m | 109m | 327m | 77 | opus5 545k |
| bc00ef0a | subagents-skill | 09-04 | 63m | 73m | 1m | 58m | 32 | fable 82k |
| d4096102 | subagents-skill | 09-04 | 96m | 106m | 4m | 145m | 55 | fable 298k |
| d6ca31ad | Cortex-Core-XCortex(mnt) | 09-05 | 260m | 143m | 24m | 101m | 94 | fable 204k |
| 056e20a8 | Cortex-Core-XCortex | 09-07 | 114m | 42m | 3m | 41m | 23 | fable 55k |
| b1457e61 | TDD-TUI | 09-07 | 1173m | 38m | 4m | 53m | 23 | opus5 127k |
| cf94c4c4 | TDD-TUI | 09-08 | 1674m | 64m | 13m | 75m | 44 | opus5 240k |
| 61de7190 | Cortex-Core-XCortex | 09-09 | 2598m | 185m | 24m | 175m | 173 | fable 153k + opus5 496k |
| cf35cb78 | TDD-TUI | 09-09 | 58m | 45m | 7m | 58m | 23 | opus5 166k |
| e4bebf20 | XCortex-teach | 09-11 | ? | ? | ? | 169m | ? | ? |
| 21c23a0e | subagents-skill | 09-16 | 989m | 22m | 0m | 21m | 14 | opus5 79k |
| c81599fd | TDD-TUI | 09-21 | 41m | 39m | 15m | 53m | 22 | opus5 140k |
| 9832cdf3 | subagents-skill | 09-23 | 36m | 38m | 2m | 49m | 30 | opus5.5 112k |
| cc4a3413 | subagents-skill | 09-24 | 1394m | 57m | 2m | 109m | 16 | opus5.5 314k |
| 54dd10c5 | TDD-TUI | 09-28 | 200m | 122m | 18m | 163m | 22 | opus5.5 270k |

Full paths: `/root/.claude/projects/-app-code-subagents-skill/{42dd56d4-6e8c-4951-ac5f-d7396aa787c4,bc00ef0a-778a-46dd-870d-15ad8c076fb3,d4096102-b0ac-4ab6-a444-b36af13ff0ab,21c23a0e-35a2-4d17-8166-d450966e5221,9832cdf3-237b-46e6-850a-2218ace444d1,cc4a3413-9751-4136-9f5c-9cf611e28935}.jsonl`; `/root/.claude/projects/-app-code-AnhNguyen-TDD-Ci-Express-TUI/{b1457e61-596b-4794-8b6e-ed93440fc430,cf94c4c4-2dc0-40d4-abb6-169a36c4432d,cf35cb78-8941-4efd-a898-820f9e07fdf0,c81599fd-dd4e-4481-ae09-7173865d9ccd,54dd10c5-7587-45c5-a0e0-8669e58bfe05}.jsonl`; `/root/.claude/projects/-app-code-Cortex-Core-XCortex/{056e20a8-1cdd-45f7-8dd6-17080e78acf7,61de7190-3ba5-44d5-9f4b-23c90242213f}.jsonl`; `/root/.claude/projects/-mnt-c-Code-Cortex-Core-XCortex/d6ca31ad-2c9c-44a6-b8d2-edefad4cedc4.jsonl`; `/root/.claude/projects/-mnt-c-Code-OrangeLogic-Testing-Tools/a58bd85c-4c10-4d73-a2dd-ad2a44327730.jsonl`; `/root/.claude/projects/-mnt-c-Code-Cortex-Core-XCortex-teach/e4bebf20-f68b-44a4-960a-62cd20653856.jsonl`.

Sample parent breakdown, 54dd10c5 (the 3.5h Go TUI defect run): 131 parent API messages, 270k output tokens; tool_use input chars 126k of which Bash 78k (general), Bash touching the ledger 29k, Agent briefs 15k; visible text 22k chars. Tool calls: Bash 117, Agent 4.

## Journal run lines (agents / est / actual / wall) — all 29 are in scratchpad/run-lines.txt
Highlights: e4bebf20 12 agents est 1.3M actual 1.82M 135 min; 61de7190 8 agents est 800k actual 3.04M 170 min; d4096102 wall 185 min vs est 90 (whole-file prose compression did not converge); 54dd10c5 3.5 h; a58bd85c ~2 h; 42dd56d4 92 min; d6ca31ad 95 min; cf94c4c4 90 min.

Scratch files: `/tmp/claude-0/-app-code-subagents-skill/490ef7e5-fac4-4973-aed3-a805887ce97f/scratchpad/{run-lines,use-lines,obs-lines}.txt` (all journal lines, archived + live).
Ledgers from runs in this repo: `/app/code/subagents-skill/.claude/plans/sage-ledger-*.md` (newest: cc4a3413, 9832cdf3, 21c23a0e). Ledgers from other repos live in each repo's `.claude/plans/`.

## Prior improvement docs in the repo (context, do not redo them)
- `sage_codex_top5_quality_token_improvements.md` and `sage-top5-implementation-review.md` — about the Codex sage.
- `docs/ideas/*` — superpowers / memory-palace comparisons.

## /sage-promote session transcripts
| session | date | turns_sum | api | $ | subagents |
|---|---|---|---|---|---|
| 10073688 (subagents-skill) | 09-03 | 68m | 50m | 31 | 12 |
| 36251b5f (subagents-skill) | 09-04 | 35m | 38m | 18 | 5 |
| 9462d74c (subagents-skill) | 09-10 | 18m | 24m | 13 | 5 |
| 3171baff (subagents-skill) | 09-16 | 66m | 55m | 40 | 4 |
| 541aa308 (Cortex-Core-XCortex) | 09-23 | 52m | 32m | 19 | 10 |
Paths: `/root/.claude/projects/-app-code-subagents-skill/<id>*.jsonl` (full ids: 10073688-3b05-4030-b051-b4ba8890c5d8, 36251b5f-1f1f-44d1-9543-0146ce7fbe63, 9462d74c-832d-4fde-b289-939eebe7927e, 3171baff-a8e7-45ec-8d28-c2e68cfc2958) and `/root/.claude/projects/-app-code-Cortex-Core-XCortex/541aa308-1306-4f24-b954-593ce96a166f.jsonl`.
Other-repo ledgers: `/app/code/AnhNguyen_TDD_Ci_Express_TUI/.claude/plans/sage-ledger-*.md` (54dd10c5, c81599fd, cf35cb78, cf94c4c4, b1457e61), `/app/code/Cortex_Core/.claude/plans`, `/mnt/c/Code/Cortex_Core/XCortex/.claude/plans`, `/mnt/c/Code/Cortex_Core/XCortex/teach/.claude/plans`.

## Parent reasoning share (parent-computed, 2026-09-29)
Output tokens vs visible output (text + tool_use input chars / 4), parent only, deduped by message id:
| session | effort | parent out tokens | visible ~tokens | hidden reasoning share |
|---|---|---|---|---|
| 54dd10c5 | high | 270.6k | 37.3k | ~86% |
| cc4a3413 | xhigh | 314.2k | 26.0k | ~92% |
| 9832cdf3 | xhigh | 105.2k | 29.5k | ~72% |
| c81599fd | xhigh | 93.8k | 27.7k | ~70% |
| d4096102 | high (fable 5.1) | 298.7k | 140.4k | ~53% |
The effort level is in each assistant record's `effort` field. The user runs `/effort xhigh` as the session default.
