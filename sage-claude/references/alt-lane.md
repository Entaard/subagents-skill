# The alt lane

Read this only when an alt agent — `explorer-alt`, `verifier-alt` or `web-researcher-alt` — is in your live agent list, or when a plan wants one. A run with no alt agent listed plans without this lane and never opens this file.

The three are the same three reader roles as `explorer`, `verifier` and `web-researcher`, on a model from outside this harness's family. `install.sh` installs one only when `~/.claude/subagents-alt-models.conf` (`SUBAGENTS_ALT_CONF` overrides the path) names a model for it: one `<name>=<model>` per line, blank lines and `#` comments ignored. This repo ships no model name. Re-run `install.sh` after editing the file, then start a new session before dispatching the agent it installed.

**Availability is a live-session fact, never a filesystem fact.** Read it off the agent types listed in your own context — never off the filesystem, never off `/agents`. A file added mid-session is not yet dispatchable. No alt agent in your live list → plan exactly as you would without this lane. This is the full statement of the rule; every other mention in this corpus points here.

**Listed is necessary, not sufficient.** An alt agent can sit in the live list while its model is unreachable, and the dispatch then fails with HTTP 404 `model_not_found` (`harness-measurements.md`, Spawning measurements). One 404 says a name did not resolve, never why or how widely: the three files name models on independent lifecycles, and no grep of them separates one retirement from a lane switched off. **So clear each alt role you plan to use, one at a time, and never infer one role from another**: send that role a one-line brief asking only for its `MODEL-FAMILY:` line. A reply clears that role only; a 404 drops it. Two roles down is reason enough to treat the lane as off, unless the plan wants the third. Inferring one role from another is what lets a `verifier-alt` 404 arrive at Step 5, in the checker seat, where it is most expensive.

**An alt dispatch passes no `model` parameter.** Not a different model, not the same model, not one you intend to log as a deviation — none. The parameter silently outranks agent-file frontmatter (`harness.md`, Models and effort), so passing one replaces the outside-family model with whatever you named, and the agent's only reason to exist is gone with no error raised (`harness-measurements.md`, Spawning measurements). This is the one dispatch class the "name the model explicitly" rule does not reach, because the file already named it. `../bin/sage-alt-guard.sh` enforces it as a `PreToolUse` hook; a blocked alt dispatch is the guard, not a fault.

**Per-role benefit.** `verifier-alt` buys a second model family for the checker half of a maker/checker pair, the one property no same-family model supplies. `explorer-alt` and `web-researcher-alt` buy price and window headroom for bulk reading. Neither buys diversity. **Add a further alt role only after the need has recurred across runs**, never for one plan.

**Filling an alt row's Model cell.** You resolve no tier for an alt row — its file holds the model. Read the name it requests with one grep of the installed file:

```bash
grep '^model:' ~/.claude/agents/verifier-alt.md
```

That is a filesystem read for a **name**, which is fine; the ban above is on reading the filesystem for **availability**. Write the cell like any other, tier in brackets, lane named: a machine that set `verifier-alt` to `gpt-5.6-sol[1m]` writes `gpt-5.6-sol[1m] (frontier, alt)` — the shape, not a shipped default.

**Settle the family claim by measurement, and take either measurement.** Record family diversity when the checker's report names a non-Anthropic identity in its required `MODEL-FAMILY:` line, or when the grep below does. An Anthropic identity from either is a same-family check, whatever model was requested. `unknown` is neither: it is an **absent measurement**, not a same-family verdict — a unit that really ran outside the family has reported `unknown` honestly, because a model that cannot observe its own identity has nothing else to write (`harness-measurements.md`, Spawning measurements). `message.model` in the unit's own transcript (`output_file`) is the only field that establishes which model ran; the sidecar's `model` field records a dispatch-time *override*, so it is empty on exactly the alt rows you care about:

```bash
grep -o '"model":"[^"]*"' <output_file> | sort -u
```

A missing `MODEL-FAMILY:` line with no grep behind it stays a same-family check. The configured name is what the file **requests**; what actually **ran** is this measurement's to settle, and adversarial verification (`verify.md`) rules on it.
