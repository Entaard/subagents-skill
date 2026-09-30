# Replays of the 54dd10c5 task (V1 and V2)

Date: 2026-09-29. One sample per arm, on the user's budget choice ("V1 + V2, 1 sample per arm"). One sample is a weak signal: read these as observations, not as a measured effect.

## Method

- **Task:** the first user message of session 54dd10c5 (the tddmon TUI stderr, sync-deadline and webhook-secret defect), with the real webhook key and token replaced by fake values.
- **Baseline:** commit `c13301b`, cloned from a git bundle that stops at that commit, so the later fix commit is unreachable.
- **Isolation:** each arm runs `claude -p` in a fresh sandbox `HOME` with a clean environment, the credentials linked, and the sage memory copied with every `54dd10c5` line removed.
- **Scoring:** an independent hostile-input Go test (`hostile_webhook_test.go`, six cases: expired context, invalid URL, control-character URL, echoed error body, percent-encoded echo, invalid redirect `Location`) plus `go vet ./...` and `go test -race ./...` on a copy of each arm's final tree. The last three cases are the leak classes that survived the original run's first two fixes.

## Results

| Arm | Corpus | Parent effort | Wall | Cost | Parent output | Units | Hostile cases | vet / race |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V1-medium | old | medium | 27 min | $5.58 | 77k | 1 | 3 of 6 pass; echoed body, encoded echo and bad redirect leak the key and token | pass / fail (the probe's leaks) |
| V1-high | old | high (a later hand-back turn ran at the session's medium) | 102 min | $20.37 | 351k | 9 | 6 of 6 | pass / pass |
| V2-high | new | high | 68 min, stopped by a gateway HTTP 503 before its review round | $10.99 | 281k | 3 | 6 of 6 | pass / pass |

## What the replays show

- **Parent effort.** `medium` was about 4× faster and cheaper than `high`, but it shipped the leak class the original run needed two extra rounds to find. The plan's rule was: use `medium` only if V1 shows no quality loss. V1 showed one, so the skill's default is `high`. The two V1 arms also bought different numbers of review rounds, so effort alone is not proven to be the cause.
- **Skill frontmatter effort** controls the turn that invokes the skill. A later turn that a subagent's hand-back message starts runs at the session effort (V1-high: 173 records at `high`, 100 at `medium`).
- **The framing critic paid on its first real run.** In V2 it found the echoed-body leak (V2 finding F1, stage `frame`, major) before any code existed. V2's fix then passed all six hostile cases before any review round ran. V1-medium never found that class.
- **Bookkeeping moved to the helper.** V2 wrote its ledger only through `sage-ledger.sh` (8 calls, 0 hand edits of the ledger). The original run hand-wrote the ledger with Python replace heredocs.
- **Framing takes time up front.** V2 spent 35 minutes testing premises and planning before its first dispatch, against a 60-minute wall target.
- **V2 did not finish.** A gateway HTTP 503 ended it after 68 minutes, with the review wave and the final run still planned. The V2 wall time is therefore not comparable with V1-high's full run.

## Defect found by the replay

The V2 ledger was named after a session id the parent took from a path, not the harness's session id, so the elapsed-time hook never found it and printed no clock line. Fixed: `SKILL.md` Step 2 now names the ledger `.claude/plans/sage-ledger-${CLAUDE_SESSION_ID}.md`. The skill loader expands that variable; a probe confirmed the expanded path.

## Not done

- V3 (the framing-escape replays of cf35cb78, c81599fd and a58bd85c) was not run, on the user's budget choice.
- No arm had three samples. A second V2 run would settle the wall time and test the review wave on the new corpus.
