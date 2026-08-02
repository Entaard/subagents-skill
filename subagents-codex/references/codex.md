# OpenAI Codex mechanics

Verified against the Codex docs (learn.chatgpt.com — current home; developers.openai.com/codex redirects there) 2026-08. Model names and defaults drift — check the Models doc / `/model` when precision matters.

## Spawning

- Subagents are native and on by default (`agents.enabled = true`). In chat, delegate in natural language and be explicit about fan-out and joins: *"Spawn one agent per module below, run them in parallel, wait for all, then merge by category."*
- Built-in agent types: `default`, `worker` (implementation), `explorer` (read-heavy exploration).
- Steering: ask Codex directly to steer, stop, or close a subagent thread; `/agent` switches between active threads; a background thread's approval prompt can surface in the main view (press `o` to open the source thread before approving). Steering an existing thread is cheaper than respawning.
- `/fork` (or `codex fork`) branches the conversation **with full history** — that is not a subagent. Use fork to branch a discussion; use subagents for bounded work that returns a distilled summary. Confusing the two re-creates the context pollution subagents exist to prevent.
- **Known gap** (open bug openai/codex#15250, as of 2026-08): custom agents defined in `.codex/agents/*.toml` may not be spawnable *by name* through the tool-call interface — only generic `agent_type` + inline overrides. Prefer inline per-dispatch briefs + overrides; treat named custom agents as a convenience that may not resolve.

## Config (`~/.codex/config.toml` or project `.codex/`)

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 4   # no documented default — set it explicitly
default_subagent_model = "gpt-5.6-terra"
default_subagent_reasoning_effort = "medium"
```

Custom agent (optional, one file per agent, `.codex/agents/<name>.toml`):

```toml
name = "explorer-ro"
description = "Read-only repository exploration"
developer_instructions = "Explore only. Return the agent report format. Never modify files."
model = "gpt-5.6-terra"
model_reasoning_effort = "low"
sandbox_mode = "read-only"
```

Precedence for model/effort: the custom agent file's own values win; otherwise explicit spawn value → `[agents]` default → parent's value.

**Sandbox/approval inheritance:** subagents inherit the parent turn's **live** sandbox and approval settings, and live overrides (`/permissions`, `--yolo`) take precedence over a custom agent file's static `sandbox_mode`. A "read-only reviewer" is only as read-only as the parent turn — state the no-source-edit rule in the brief regardless.

## Models and effort (as of 2026-08 — verify against the Models doc)

| Tier (core skill) | Model | Notes |
| --- | --- | --- |
| fast | `gpt-5.6-luna` (or `gpt-5.3-codex-spark` for near-instant iteration) | narrow, high-volume, latency-sensitive |
| standard | `gpt-5.6-terra` | parallel workers returning distilled results |
| frontier | `gpt-5.6` / `gpt-5.6-sol` | demanding reasoning, correctness/security review |

Reasoning efforts: `low`, `medium` (default), `high`, `xhigh`, `max`, `ultra`. Note **`ultra` enables proactive delegation** — Codex may spawn subagents on its own initiative. If this skill is in manual mode, don't run the parent at `ultra`, or its proactive delegation will bypass your plan gate; `high`/`max` keeps delegation on your terms.

## Scripted subagents (`codex exec`)

For deterministic fan-out (migrations, batch verification), shell out one `codex exec` per unit:

```bash
codex exec -m gpt-5.6-terra --sandbox workspace-write --cd "$WORKTREE" \
  -o "$SCRATCH/unit-07-report.md" "$(cat "$SCRATCH/unit-07-brief.md")"
```

- Defaults: sandbox is `read-only` unless raised; `--output-schema <file>` enforces structured JSON reports; `--json` streams events; `codex exec resume --last` continues a session. (`-c key=value` generic overrides: unverified — prefer the documented flags above.)
- Run units in parallel with shell job control up to the cap; collect the `-o` report files; the ledger tracks unit → file.

## Worktrees, skills, AGENTS.md

- Codex-managed worktrees (Handoff, `$CODEX_HOME/worktrees`, `.worktreeinclude`) are a **ChatGPT desktop app** feature. In the CLI, isolate parallel writers manually: `git worktree add` + one `codex exec --cd <worktree>` each, one integration owner merging. `AGENTS.override.md` (gitignored) is auto-copied into managed worktrees.
- Skill install: `.agents/skills/subagents/` (repo) or `~/.agents/skills/subagents/` (user). Explicit invocation: `$subagents` or `/skills`. Implicit invocation is controlled by `agents/openai.yaml` → `policy.allow_implicit_invocation` (this skill ships it `true`; flip to `false` if it triggers too eagerly). Same-named skills at different scopes are **not merged** — avoid installing at two scopes.
- AGENTS.md nests; the closest file wins. A durable `subagents-mode: auto` line belongs in the AGENTS.md of projects where you want auto mode by default.
