# Sage alt lane on the Codex CLI

Status: designed and implemented 2026-09-30, on the user's word. It replaces the alt agent files that `install.sh` rendered from `claude-agents-alt/`.

## The problem

The alt lane gave sage a checker from outside the Claude family. It worked like this: `install.sh` rendered Claude Code agent files whose `model:` line named an OpenAI model, and the LiteLLM gateway served that model on the Anthropic route.

That route stopped working. On 2026-09-30:

- A direct Messages API call for `gpt-6-luna` returned HTTP 401: `No ChatGPT OAuth token available and CHATGPT_DISABLE_DEVICE_LOGIN is set. Send your own ChatGPT OAuth token in the Authorization header (BYOK)`.
- `claude -p --model gpt-6-luna` hung for 120 seconds, twice. The only output was `[claude-code:unrecognized_model]` on stderr.

Claude Code cannot send a ChatGPT token for one subagent only. So the old design cannot be repaired from this repo.

## The decision

The sage parent runs `sage-claude/bin/sage-codex.sh` with Bash. The script calls `codex exec`, which sends the user's own ChatGPT token from `~/.codex/auth.json`.

**Two seats only**, on the user's word:

| Seat | Model | Effort | Use |
| --- | --- | --- | --- |
| `verifier-alt` | `gpt-6.1-sol` | `xhigh` | review of a frozen artifact |
| `refuter-alt` | `gpt-6-astra` | `medium` | adversarial checks |

`explorer-alt` and `web-researcher-alt` are removed. The user judged Opus 5.5 and Sonnet 5.5 cheap and strong enough for reading and research. No alt implementer was ever built.

**Not in scope**, on the user's word: steering a running Codex unit, and any spend or window limit for the lane.

## Rejected: a Claude relay agent

The first idea was a cheap Claude agent (Sonnet 5.5 at low effort) that passes the brief to Codex and the report back. It was rejected for four reasons:

1. **It can change the text.** A relay that summarises or "fixes" a refuter's report puts an Anthropic model into the verdict. The lane exists to keep the verdict outside that family.
2. **It copies every byte twice.** The relay types the brief into a command and types the report into its answer. Long briefs with quotes and `$` also break shell quoting.
3. **It hits the foreground Bash limit** of 10 minutes. A high-effort review can take longer.
4. **It breaks the evidence.** The old family proof was `message.model` in the unit's transcript. A relay's transcript names a Claude model, so every alt unit would count as a same-family check.

## How the script works

- **The seat file pins the model and effort.** `sage-claude/codex/<seat>.md` has `model:` and `effort:` front matter. Its body becomes the Codex developer instructions. The script takes no model or effort argument.
- **The brief goes on stdin**, from a file. The shell never expands it. The unit directory must be new or empty and must not overlap the repo, so the brief cannot be a file the script writes, and the unit cannot write the tree under review.
- **Isolation.** Codex runs with the unit directory as its working root, under `workspace-write`. The repo and `/tmp` are read-only. `TMPDIR` points inside the unit directory, so test suites that call `mktemp` still run. The network is off and the web tool is disabled. The user's Codex plugins, hooks, apps, memories and MCP servers are off, and key- and token-shaped environment variables are removed from the unit's shell.
- **The receipt.** `<unit-dir>/receipt.txt` is one line. The script parses the Codex events and the session file with `jq`, so key order and spacing do not change the result. It names the outcome (`done`, `failed`, `auth-failed`, `rate-limited`, `timeout`, `no-codex`), the model and effort that ran, the token counts and the wall time. A line jq cannot parse is skipped. The script checks each record's structure, not its JSON syntax: Codex writes strict JSON, and the model's own text always sits inside a JSON string. Only the message field of an error decides the outcome. A blank or control character in a value read from Codex becomes `_`, so no value can add a receipt field. The exit status comes from the computed outcome, never from the receipt text. The model and effort come from the Codex session file's `turn_context` record, which Codex writes, not the model. Only a record whose `cwd` is this unit's directory counts. When no such record is found, the receipt says `source=unverified`, and the unit counts as a same-family check.
- **Trust.** `SAGE_CODEX_BIN`, `SAGE_CODEX_SESSIONS` and `SAGE_CODEX_TIMEOUT` exist for the self-test. Whoever sets them can run another program or supply forged session files. So the pin and the receipt protect against a brief and a command line, not against the caller's own environment.

## What changed for the sage run

- `references/alt-lane.md` is rewritten for the script: probe, brief, harvest, the receipt as the family proof, and how to record the seat.
- The run record gains an `Alt lane:` line: per unit, the receipt's model, effort, outcome and spend, and what the unit contributed. The lint's new `alt-record` check fires when a Plan row names a seat and this line is missing, or has fewer complete entries for that seat than the Plan has rows for it. An entry starts at a seat name and is complete when `model=`, `effort=`, `outcome=` and `spend=` each carry a value. This is the only place a Codex unit's effort shows, because `sage-watch.sh` reads only Claude transcripts.
- The Agent-tool rules for the alt lane are removed: the "no `model` parameter" rule, its `sage-alt-guard.sh` hook, the `MODEL-FAMILY:` self-report, and the transcript grep.
- `sage-lineup-check.sh` watches the seat files' `model:` and `effort:` lines instead of `~/.claude/subagents-alt-models.conf`, which no longer controls anything.
- `/sage-promote` starts its gate on `refuter-alt` through the script.

## Migration

`install.sh` removes the alt agent files earlier versions rendered, but only a file that carries the old generated-file marker. It also removes the old guard hook entry from `~/.claude/settings.json`, matched on its exact command path. A user's own agent at an alt name is left in place. `~/.claude/subagents-alt-models.conf` is left in place, unread. The user can delete it.

## Open items

1. **`~/.codex/AGENTS.md` and Codex's built-in skill list still reach the unit.** `--ignore-user-config` would remove them, but it also removes the model provider, and its one probe failed on a 429. A Codex config profile that carries only the provider would fix this.
2. **Rate limits.** Every Codex run logged a 429 on its model-list refresh, and one turn failed on a 429. The script reports that as `outcome=rate-limited`. No retry is built in.
3. **The window is smaller.** Both seats reported a model context window of 258,400 tokens, against 1M on the Claude seats. `alt-lane.md` tells the parent to scope the brief.
