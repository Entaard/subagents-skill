# Study the sage

## TODO

- Why isn't diff-review skill loaded into the verifier agent, like the clean-code one?
- A new great sage to orchestrate multiple sages to do a task.
- I think the strengh bands - `(calibration: established)`, `(recurring)`, `(provisional)` - are being promoted differently among machines. Machine A
    promotes one rule to established and commits the changes. Then machine B pulls and installs the latest skills, and promotes the same rule back
    to recurring, because that's what its memory said.
- Sage extreme mode (or a new sage-extreme skill, referencing the sage skill with some overrides) - use the parent session model for all subagents.
    Moreover, give the subagents the ability to spawn nested subagents if needed.

### Inquiries on `# Sage`

- "Your job: decompose one task into units, place each on the cheapest model that can hold it" -> does the "cheapest" word cost the sage to prioritize
    saving tokens instead of focusing on result quality?
- "Not smarter than its model. Better spent." -> same concern. I think my initial idea was misinterpreted. We may need to restate this to avoid the
    sage focusing on saving cost above all else, including the result quality. The sage's main focus is result quality. Everything it does is to give
    the best result for the assigned task. Saving cost is second to this. For example, the sage should not assign Fable to do simple exploration work,
    which can be done by Haiku efficiently.
- "Autonomy is legibility, recorded rather than shown." -> should improve this a bit. Show the link to the ledgers and plans in the final report, so
    that the human can easily check them if they want to.

### Inquiries on `## Defaults`

- "Max concurrent subagents: 4" -> I feel the default value is too low. Check the previous runs reports to find if we have a better number.
- "Subagent report size: ask for 1–2k tokens returned, details to files — units that cannot write distill instead" ->
    - How do we know that 1-2k tokens is a good number for a subagent report?
    - Should this range be varied depending on the subagent's task? For example, is there any case that a verifier has to review thousands of lines
        of code changes in one single PR? If yes, and if the PR has 100 bugs, would the 2k limit prevent the agent from reporting everything?
    - Is this range also applied to distill? What is more effective between report and distill? Why don't we use distillation all the time?
- Fixing subagent: "Fix rounds per unit: 2 delegated attempts (steer once → one tier up), then inline — cut short on a repeated failure signature" ->
    - "one tier up" means to increase the model tier, e.g. Haiku to Sonnet, or Sonnet to Opus, right? What about increase the effort, should the sage
        also do that if possible, e.g. with custom subagents?
    - Before increasing the tier, I think the sage should also consider using a new subagent with the same tier (can be higher effort), with briefing
        that includes what fails last time so that the new agent can avoid. Sometimes, a new fresh agent of the same tier can produce better result.
    - I don't think the last inline fallback is a good idea, but I understand the intention. Is there any chance that a subagent with the same model
        and effort as the main agent still fails the task? If yes, will falling back the task on the main agent not resulting in the same failure?
        Or should the main agent try to improve its briefing instead?
- Implementation - review loop: "Review depth" -> if I understand correctly, currently the sage has 2 review rounds: 1 review round, and another round
    to verify the fix. If that's correct, what about an infinite number of follow-up review-pairs (the only limit is the token ceiling)? The follow-up
    reviews should only focus on critical and major issues, which in most cases should be none if the implementers and the 2 previous review rounds
    work correctly.
    - "discovery sweeps stop on dry rounds instead", does it mean we also verify discovery tasks? And these verifications stop earlier than the normal
        ones? If yes, it's ok for me.
- "Handover" -> Should we reduce the gate of summoning a successor sage from 30% to 25% (or maybe lower)? This would give the parent more "clear mind" to continue the
    main orchestration of 1 or more successors. Should be checked thoroughly based on reports we're having rather than guessing, because lowering this
    gate threshold means more handover. Also, keeps the 30% threshold on the successor sages, as they're gone after handover.

### Inquiries on `## Step 1 — Decompose`

- "The user answered "is this task worth agents at all" by invoking sage." -> Looks redundant by the next sentences.
- "Scout before you study" ->
    - "Reading the codebase to build one" -> not all tasks start from a codebase, so does this claim somehow hinder the sage?
    - "the saved `explorer` type only" -> does this include the `explorer-alt` if it's available?

### Inquiries on `## Step 2 — Plan and record`

- "**Build the measurement harness first.**" -> I don't understand this fully. Could you elaborate and give one or two examples?

### Inquiries on `## Step 3 - Brief`

- "- Escalate one tier on retry rather than repeating the same dispatch — above frontier the next tier is apex, so a failing frontier unit gets one
    apex dispatch before the parent takes it inline. Where the harness resolves no apex model, the ladder tops out at frontier as before." ->
    Similar to the "Fixing subagent" inquiry above. Also, look like they are duplicated, right? If yes, what can we do about the duplication?

### Inquiries on `## Step 4 - Execute and watch`

- "Failure ladder per unit" -> same question with "Fixing subagent". This looks more detailed than the previous 2. Is it needed to repeat and escalate
    a rule / concept like this multiple times in multiple steps when writing a skill? If yes, I think I understand it, but they look hard for modifications
    work later. Anything we can do about it? Maybe define a detailed rule in another file, and reference the rule name instead?
- "It exists because asking was already tried" -> this part has multiple problems:
    - It mentions a document that isn't a part of the sage skill. Consequence: I already removed the document when everything in it was fixed, leaving
        this note referecing an obsoleted information.
    - Why a proof was written as-is into the skill's corpus? If there's no good reason for it, I expect the skill corpus to only content "lessons",
        not logs of previous runs.
- Up to now, I see the "missing `jq`" in lots of places. That is bad. Now we have `jq`, in the future scripts we'll have another tool needs installation,
    and extra lines of warnings and precautions and workarounds like this. My suggestions either or both of the followings:
    - Have and extra skill - sage-setup - to install the needed tools.
    - Install the needed tools in install.sh. Note and guide user to manually do it or ask another agent to do it if the installation script isn't working.
    The we can remove all the extra handlers for the missing xx tools.

### Inquiries on `## Step 5 — Verify and integrate`

- I find this step the most overstating and confusing. Most of its rules and practices are already embeded in the verifier agent, the diff-review skill,
    and any other code review skill (Claude's default skill or skill on the marketplace). For example, when dispatching a verifier, the parent already
    gives it just enough brief, so the extra explanation "A reviewer's value is its clean context, not the head count" looks duplicated. Or, I believe
    the diff-review skill already has the needed 2-state review, even with 2 subagents explicitly in standalone mode, making the "two-stage review"
    notes look duplicated. I think this step needs to be recheck carefully to see if any knowledge can be embeded (or already embeded) in the verifier
    agent and the diff-review skill, and remove the duplication here, unless the orchestrators (parent included) need them to verify the work themselves.
- Again, should the verifier has the ability to use diff-review?
- Step 4 and step 5 should be merged. This will change the sage quite a bit, so fight me hard if needed. I think Execution should mean a loop of
    implementation and verification, until the "done" is reached, or we run out of budget. This is also my previous suggestion on "Implementation -
    review loop" above. I get this idea from real engineer work. Dev and QA teams never stop after one or two rounds. They stop only when the feature
    is delivered as planned - the requirements are satisfied. In the loop, the dev team or the qa team members maybe replaced with new members, or
    if after many loops and replacements, the feaure isn't delivered, the managers would have to reverify or change the initial plan. Since the agents
    are autonomous, and the human users don't have unlimited budgets, as in the "Implementation - review loop", I suggest we have a bit workaround,
    by reviewing hard the 1st and 2nd round as we're currently doing, then have follow-up review-fix loop until there's no critical and major issues
    left. This would cover:
    - Make sure review-fixes don't introduce regressions, by real review action, not by depending on the current orchestrator decision.
    - Make sure the delivered result is at least clean of major-and-above issues.

### Inquiries on `## Handover`

- Again, there're some mentioning of real logs, like "measured 2026-08-18", or "2026-08-20, generation 2". I already mention this above, I don't think
    that it's should be done like that. In a corpus, you don't prove every rule, every claim, every decision, or every prohibition. The corpus should
    only contain the lessons from the real events. The events should already be in the memories or some other proof documents, that are only summoned
    when the decision is challenged.
