
- Continue working with the sage in the same session?
- Terminal rule is 40%? Since we have successor sages now, remove the terminal rule.
- I feel sage is more costly than the previous version of subagents. What are the most costly steps and flows?
- Roughly how is sage's performance vs subagents?
- Check the sage and subagents skills to see if they try to pass Anthropic model names into the alt custom agents.
- Do the sage and subagents skills use the alt agents when the alt agents are available?
- Remove the cap number of successor sages.

----

watchdog didnt stop after the work was finished:

should it stop when the run is finished? Just a question, dont attempt to fix it now

● Yes, it should. And the skill does not say so, which looks like a real gap.

  Step 4 says to host the watchdog on Monitor with persistent: true. ## Handover says a supervising parent keeps hosting it. Step 6 lists its closing obligations — bring the ledger current, write the run record, append the memory row, print three
  things — and stopping the watchdog is not among them. It relies on the session ending instead.

  Three concrete failure modes follow, and they get worse the longer the session lives.

  The occupancy rungs never stop firing. occ-40pct is the parent's terminal rung, and no SAGE_OCC_ACK silences it. That is deliberate for a live run. After the run ends it means that if I keep working in this session and cross 40%, the watchdog fires a
  handover alarm for a run that finished an hour ago. There is nothing to hand over.

  It would adopt the next wave with the wrong numbers. It watches a fixed subagents/ directory, and that is this session's directory. Any agent you dispatch later lands there. The old watchdog would price those units against this run's estimates file,
  so the spend rungs would be relative to the wrong rows. That is the same defect as having no estimates file, except it looks healthy.

  Its filter outlives its reason. The grep -v mutes tool-repeat for one agent id running one command. That id is finished. The filter now just carries a small permanent blind spot for no benefit.

  The cheap fix is one line in Step 6: stop the watchdog as part of closing, in the same place the memory row is appended. That also gives the surfaced-event list something honest to say when it could not be stopped.

  There is one argument the other way, and it is weak. If you follow up in the same session with more agent work, a live watchdog is already there. But it is the wrong watchdog by then, for the reasons above, and starting a fresh one costs one call.

----

previous session's surfaced:

  Surfaced

  - Criterion 7 is Awaiting human. I could not test what happens when your gateway cannot serve a configured model. The Agent
  tool's model parameter is a closed enum, so a bad value dies in schema validation and would measure the tool, not the
  harness. The mitigation ships anyway: each alt agent must open its report with MODEL-FAMILY:, and a run may record family
  diversity only when that line names a non-Anthropic identity.
  - Whether agent frontmatter honours the [1m] suffix is unsettled. The falsifier is recorded: an alt unit whose report names
  an Anthropic identity, on a machine whose gateway serves the configured model.
  - Zero cross-family verification this run. All seven review lenses self-reported Anthropic Opus 5. That is exactly the gap
  this deliverable closes, and it could not close it for itself.
  - A sage-watch.sh defect, out of lease. Its tool-repeat counter is a high-water mark, so once any command is called four
  times the rung fires on every later sample for that unit's life. I measured it three times on a writer whose tree was
  demonstrably still changing. It made me filter the rung mid-run.
  - Discoverability gap. Removing the installer's interactive prompt was correct, because its only trigger was
  ANTHROPIC_BASE_URL, which means a proxy and not a gateway. But a new user who never opens harness.md now has no way to learn
  the lane exists. One README.md line would close it. README.md was outside the write lease.
- One finding I filed was wrong and is retracted. I claimed the watchdog's estimates file never matches its keys. It matches
  fine; 150k is the documented per-unit floor. My test used four cases all below that floor, so it could not tell a broken
  mechanism from a working clamp.

----
