# The alt agent templates

`explorer-alt`, `verifier-alt`, `web-researcher-alt` are the three reader roles from
`../claude-agents/`, rendered onto a model this machine configures. `install.sh` renders each
`*.md.in` here only when `~/.claude/subagents-alt-models.conf` names a model for it
(`SUBAGENTS_ALT_CONF` overrides the path). This repo ships no model name; `__ALT_MODEL__` is the
placeholder the installer substitutes.

This file is for whoever maintains the templates. **It is never installed** — the installer globs
`*.md.in` and nothing else — which is exactly why the notes below live here.

## Why there is no "Note for the parent" in a template

A template's body becomes the rendered agent's **system prompt**. The parent never reads it.

Notes addressed to the parent used to sit in `verifier-alt.md.in` and `web-researcher-alt.md.in`.
They reached the wrong reader: the agent was told not to pass a `model` parameter it never passes,
and to edit a config file it has no Edit tool for. That is prompt tax plus a standing instruction
the agent could act on wrongly. A verifier reading its own prompt confirmed the mechanism in
2026-08.

**Parent-facing rules live in Sage's corpus, where the parent actually reads them:**
`sage-claude/references/alt-lane.md`, with a shorter statement in `references/harness.md`.
Put a new parent rule there. Put only agent-actionable text in a template.

## The rules that moved here

**An alt dispatch passes no `model` parameter.** The Agent tool's `model` parameter silently wins
over frontmatter, so passing one replaces the outside-family model with whatever was named and the
lane's whole value is gone with no error. An override can also invalidate the file's `effort`,
since available levels depend on the model. Neither loss raises anything; the only symptom is the
report's `MODEL-FAMILY:` line, and by then the unit has already run. To change a family, edit
`~/.claude/subagents-alt-models.conf`, re-run `install.sh`, then start a new session.

**Budget an alt row from its own measurements, never from the base agent's.** The base
`web-researcher` note quotes real per-agent costs (under 40k on URL-named briefs, past 90k on
open-ended ones). Those were measured on the base agent's model. They set the *shape* of the
lesson — brief style dominates cost for a research unit — and not the numbers for a different
model. Record an alt row's actual and price the next one off that.

**Say nothing model-specific in a template.** The configured model varies per machine, so a
benchmark figure or a capability claim about "this model" is false on every machine that chose a
different one. `explorer-alt.md.in` carried an MRCR long-context number for one specific model
until 2026-08; it now states the shape of the risk and leaves the number to the machine.

## Keeping a twin in step with its base agent

A twin should differ from `../claude-agents/<role>.md` in exactly seven places, and a diff showing
an eighth is a drift to fix:

1. `name:` — the `-alt` suffix.
2. `model:` — `__ALT_MODEL__` rather than a fixed model.
3. `color:` — a distinct colour, so the two are told apart in a fleet.
4. `description:` — the base text plus the model-family sentence.
5. The generated-file marker comment on the first body line. **This line is load-bearing**, not
   decoration: `install.sh` greps for it verbatim to decide whether a file at an alt path is its own
   output and therefore safe to remove. Reword it and the removal pass silently stops working, so a
   role dropped from the config keeps its stale agent file forever.
6. A "What this twin buys, and what it does not" section, with the per-role claim.
7. A "Self-identification" section and the extra `MODEL-FAMILY:` line at the top of the return
   format block.

The twins also **lack** the base agent's "Note for the parent" — deliberately, per the section above.
Do not restore it when syncing a base-agent change.

Everything else — `tools:`, `disallowedTools:`, `effort:`, the rules, the rest of the return format
— stays byte-identical, so a change to a base agent is a change to its twin in the same commit.
Check with `diff <(sed 's/__ALT_MODEL__/MODEL/' <role>-alt.md.in) ../claude-agents/<role>.md`.

Each twin also carries the `MODEL-FAMILY:` self-identification rule, because the family claim is
measured from the report rather than assumed. A model that cannot observe its own identity writes
`unknown`, which is an absent measurement rather than a same-family verdict; the parent settles it
from the unit's transcript. That procedure is in `sage-claude/references/alt-lane.md`.
