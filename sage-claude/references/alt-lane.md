# The alt lane

Read this only when an alt agent (`explorer-alt`, `verifier-alt`, `refuter-alt`, `web-researcher-alt`) is in your live agent list, or when a plan wants one.

Three are the reader roles `explorer`, `verifier` and `web-researcher`, on a model from outside this harness's family. `refuter-alt` is `verifier`'s refuting half, on its own model. `install.sh` installs one only when `~/.claude/subagents-alt-models.conf` (or `SUBAGENTS_ALT_CONF`) names a model for it, one `<name>=<model>` per line. This repo ships no model name.

**Availability is a live-session fact, never a filesystem fact.** Read it off the agent types in your own context, never off the filesystem or `/agents`. No alt agent in your live list → plan as if this lane did not exist.

**Listed is necessary, not sufficient.** An alt agent can be listed while its model is unreachable, and the dispatch then fails with HTTP 404 `model_not_found`. One 404 says a name did not resolve, never why or how widely. **So clear each alt role you plan to use, one at a time, and never infer one role from another**: send that role a one-line brief that asks only for its `MODEL-FAMILY:` line. A reply clears that role. A 404 drops it. Two roles down is reason enough to treat the lane as off.

**An alt dispatch passes no `model` parameter.** Not a different model, not the same one, not one you mean to log. The parameter silently outranks the agent file, so passing one replaces the outside-family model and removes the agent's only reason to exist, with no error. `../bin/sage-alt-guard.sh` enforces this as a `PreToolUse` hook. A blocked alt dispatch is the guard, not a fault.

**The seats.** `verifier-alt` and `refuter-alt` buy a second model family for the checker half of a maker/checker pair, which no same-family model can supply. `refuter-alt` takes every refute-by-default check: adversarial verification, the pass at your own work, the framing critic, a promote gate. `verifier-alt` takes routine review of a frozen artifact. With `refuter-alt` absent or dropped by its probe, `verifier-alt` takes its checks with a refute brief. `explorer-alt` and `web-researcher-alt` buy price and window headroom for bulk reading, not diversity. Add a new alt role only after the need recurs across runs.

**The transcript outranks the self-report.** `message.model` in the unit's own transcript is the only field that establishes which model ran:

```bash
grep -o '"model":"[^"]*"' <output_file> | sort -u
```

A non-Anthropic name there is family diversity. An Anthropic name is a same-family check, whatever was requested and whatever the report says: the two have disagreed on record. Only where the grep returns nothing does the report's `MODEL-FAMILY:` line decide. `unknown` there is an absent measurement, not a same-family verdict. A missing line with no grep behind it stays a same-family check.

**Take an alt row's spend from its transcript** with `sage-watch.sh --status`, never from the returned token count, which is wrong in both directions on this lane. A `spend=0` on a row with real work is missing usage data, not a small row.
