Q: What the sage-watch.sh really buys? At what cost? Fanout 2 sub agents, 1 attacker and 1 defender for the flow.

Answer:

The measurement that reframes everything

On a settled corpus, every rung is suppressed. I ran the probe's own --status mode over all 185 transcripts it can read:

done=yes    177
done=stale    8
done=no       0

Each rung fires only when the unit is not presumed finished (sage-watch.sh:159-166). So historical transcripts cannot measure how often a rung is right. They can only show which thresholds an ordinary unit crosses on its way to finishing normally. Read that way, the numbers are unkind.

What it buys

One thing, clearly: it sees units that die and never return. 8 of 185 units (4.3%) end mid-tool-call and never produce a final turn. A dead unit sends no completion notification, so without the probe the parent waits at a barrier forever. idle-600 and idle-1800 are the only sensors for this.

That value is smaller than it looks. harness.md:188 says SendMessage "cannot reach a genuinely hung one", and SendMessage drains at the receiver's next tool round. A unit with no tool round coming never gets the message. So the rung buys knowing, not recovering. Knowing is still worth the parent stopping its wait.

What it does not buy: a unique occupancy sensor. The parent can read its own occupancy (harness.md:196, SKILL.md:267). occ-30pct and occ-40pct automate a free check. They add value only between the parent's own check points, and occ-40pct survives the ack a supervisor sets after handover.

What it costs

53% of the file is comment. 344 comment lines against 260 code lines. harness.md:152 requires the header's figures to match harness.md "figure for figure", so every stamped number has two homes and decays in both.

The stamped figures were already stale on their stamp date. Header claims 212 transcripts measured 2026-08-18, which is today. Measured today with the probe's own glob:

┌─────────────┬─────────┬──────────┐
│   figure    │ stamped │ measured │
├─────────────┼─────────┼──────────┤
│ transcripts │ 212     │ 185      │
├─────────────┼─────────┼──────────┤
│ spend p50   │ 133k    │ 169k     │
├─────────────┼─────────┼──────────┤
│ spend p90   │ 498k    │ 388k     │
├─────────────┼─────────┼──────────┤
│ spend p99   │ 3.0M    │ 692k     │
├─────────────┼─────────┼──────────┤
│ repeat max  │ 5       │ 11       │
└─────────────┴─────────┴──────────┘

tool-repeat fires on the red-green loop, not on distress. 8 units reach repeat >= 4. All 8 finished normally. The top one repeats a go test -run TestQueue command 11 times. The rung compares input strings and cannot see the edits between calls. While such a unit is alive, done=no and the rung sends a steer into healthy TDD.

The spend rungs at the 150k floor fire on ordinary work. Against the floor:

n=185   >2x(300k)=41 (22%)   >4x(600k)=6 (3.2%)   >6x(900k)=0

spend-2x catches about a fifth of normal units mid-flight. spend-4x sends a message to 3%. spend-6x, the only rung that surfaces to the user, has never been reachable — corpus max spend is 817k against a 900k threshold.

The floor also breaks the argument the relative rungs exist for. harness.md:184 says a fixed threshold "never sees a 40k explorer spinning". I passed explorer 40k:

est=150k

The floor overrode it. That explorer's rungs sit at 7.5x, 15x, and 22.5x its real budget. The spinning explorer stays invisible.

It is stateless, so every crossed rung repeats forever. No file write anywhere. spend and repeat are monotone, so one crossing at minute 5 of a 20-minute unit emits a line every 60s until the unit finishes. Roughly 15 notifications for one event. The cost is interrupt volume, not tokens: the text is about 600 tokens per run against a measured parent burn of 7.7k tokens per minute (harness.md:186).

Where each side was wrong

The attacker reported "10 not-done transcripts". I measure 0. Their count included their own live transcripts and the 8 stale ones. The correct statement is the one above: on a settled corpus nothing is not-done, which is why the corpus cannot score precision.

The defender claimed the probe reads occupancy no other source provides. It does not. The defender found and retracted this itself.

Both agents agreed the dedup of streaming partials and the done predicate are correct and necessary. I confirmed the done predicate: 177/185 (95.7%) resolve on clauses (a) or (b), close to the claimed 96.2%.

Verdict

The probe's core arithmetic is right and its safety posture is right. Its ladder is mostly not worth its surface. Two rungs only log. One fires on healthy test loops. One has never been reachable. One duplicates a free sensor.

Keep: the dedup, the done predicate, idle-1800, spend-4x, and one occupancy threshold that survives the ack. Delete idle-600, spend-2x, tool-repeat, and spend-6x. Replace the 150k floor with the plan's real estimate, or the relative rungs are not relative. Add a state file so a crossing notifies once.

That is a probe of roughly 60 lines with the same value, and one set of stamped figures instead of two.
