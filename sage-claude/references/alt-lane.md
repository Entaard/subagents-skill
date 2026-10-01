# The alt lane

Read this only when a plan wants a cross-family checker and `command -v codex` succeeds.

Two checker seats run on OpenAI models through the Codex CLI. `../bin/sage-codex.sh` starts them. The seat files in `../codex/` pin each seat's model and effort:

| Seat | Model | Effort | Takes |
| --- | --- | --- | --- |
| `verifier-alt` | `gpt-6.1-sol` | `xhigh` | routine review of a frozen artifact |
| `refuter-alt` | `gpt-6-astra` | `medium` | every refute-by-default check: adversarial verification, the pass at your own work, the framing critic, a promote gate |

Both buy one thing: a second model family for the checker half of a maker/checker pair. No Claude model can supply it. Readers, researchers and writers stay on the Claude roster in `harness.md`.

**A seat is not an agent.** It is not in your agent list, and the Agent tool cannot start it. Start it with Bash, `run_in_background: true`:

```sh
C=~/.claude/skills/sage/bin/sage-codex.sh
$C --probe refuter-alt <scratch>/probe-refuter-alt
$C refuter-alt <brief-file> <scratch>/<unit-id> <repo-dir>
```

**The script takes no model and no effort argument.** The seat file decides both, so no brief can move a seat off its pin.

**Probe each seat you plan to use**, once per run, before its first brief. A receipt with `outcome=done` clears that seat. Any other outcome drops it for the run. Never infer one seat from the other. With `refuter-alt` dropped, `verifier-alt` takes its checks with a refute brief. With both dropped, the checker rule in `verify.md` picks an in-family seat.

**Brief a seat like any checker**, with the task brief in `dispatch.md`, written to a file outside the unit's directory. Give each unit a new directory outside the repo. The script refuses a directory that is not empty or that overlaps the repo. The unit reads the repo but cannot write to it, and it runs its checks on copies inside its own directory. It has no network, no web tool, no Agent tool and no skills, so a check that needs any of these goes to a Claude checker. Its window is about a quarter of a Claude seat's, so scope the brief to what the check needs.

**A Codex unit takes no steer.** No message reaches it while it runs. A stuck unit ends at the script's time limit as `outcome=timeout`. A wrong-brief or could-not-finish failure gets one re-run in a new directory with the brief corrected. A second failure drops the seat for the run.

**Harvest.** The Bash completion notice is the wake signal. Read `<unit-dir>/receipt.txt` first, and `<unit-dir>/report.md` only when the receipt says `outcome=done`. Any other outcome is a failed unit, never a verdict.

**The receipt is the only proof of the family.** The script reads `model=` and `effort=` from the session file that Codex itself wrote. `source=session` with an OpenAI model name is a cross-family check. `source=unverified` is a same-family check, and the residual bias disclosure applies (`verify.md`). The report carries no identity line, and a brief never asks for one.

**Record the seat's effort and contribution**, because no other sensor sees a Codex unit. `sage-watch.sh` reads only Claude transcripts.

- **Plan row:** `agent="refuter-alt (gpt-6-astra medium, codex)"`. At harvest, `agentId` is the receipt's `thread=` and `evidence` is the receipt's path.
- **Findings:** each finding the unit reports gets `author=unit`, and its evidence cell starts with the seat name.
- **Run record:** one entry per unit on the `Alt lane:` line (`record.md`). Start each entry with the seat name, then copy `model=`, `effort=`, `outcome=` and `spend=` with their values from the receipt. Then name what it contributed: its finding ids with their triage, refuted or survives per claim, and any finding no other checker raised. A unit that contributed nothing says so. The lint's `alt-record` check fires when the line has fewer complete entries for a seat than the Plan has rows for it. No check can see the contribution, so it is yours to write.
- **Cost:** add each receipt's `spend=` to the run's Cost line as Codex spend, apart from the Claude figure.
