---
name: sage-promote
description: Sage's self-update pass. Promotes earned lessons into shared memory, then the strongest of those into sage's own skill text, refreshes the model lineup its tiers resolve to, and retires rules whose falsifier fired. Runs only on the user's word, never inside a run.
disable-model-invocation: true
---

# sage-promote

One pass, on the user's word. It moves what sage's runs proved into the places future runs read: shared memory first, sage's own text second, the model lineup third. It also runs **eviction** — a rule whose falsifier fired leaves shared memory and the corpus together, so the skill never cites a band that no longer exists.

**This is the highest-consequence write in the system.** Stages two and three rewrite the corpus every future sage run boots from. Every step below exists to keep that edit minimal, checkable, and reversible. Read it in order and do not reorder the stages: stage two reads blocks stage one may have just written, and stage three runs last because its evidence is the live harness rather than run rows.

**Sage never calls this skill.** A run detects candidates and prints one hint line (sage's `references/memory.md`, `## The hint`). The user runs `/sage-promote`. Nothing here is automatic.

## What it writes

| File                                                | Written here                                      | Written by a sage run            |
| --------------------------------------------------- | ------------------------------------------------- | -------------------------------- |
| `<sage>/memory/shared.md` — a symlink into the repo | stage one, eviction                               | never                            |
| `<sage>/memory/local.md`                            | `Promoted` cells, watch-list rows, one run row    | every run: appends, consolidates |
| `<sage>/memory/local-archive.md`                    | eviction                                          | consolidation                    |
| `<repo>/sage-claude/SKILL.md` and `references/`     | stage two, stage three, eviction                  | never                            |
| `<repo>/claude-agents*/*.md`                        | stage three                                       | never                            |
| the installed `<sage>` tree                          | the landing step only, byte-copied from the repo  | never                            |
| the installed `~/.claude/agents/*.md` tree          | the landing step of stage three only, byte-copied | never                            |

`<sage>` is the installed sage skill directory, resolved by preflight step 0. `<repo>` is whatever the preflight's `readlink` resolves. **The installer gives this skill nothing** — no seed file, no drift check, no symlink of its own, no executable bit to repair. It is a plain text skill that reads and writes another skill's tree, so the preflight below is the only guard those writes get.

**Never touched by this skill:** `install.sh`, `memory/local-seed.md`, and this file. An installer change that a promotion appears to need is a finding for the user, not an edit.

## Preflight

Runs once, before any stage, in this order. **Any check failing stops the pass with zero bytes written** and one printed line naming the check that failed and the file it failed in — except step 2, which is scoped inside the step because only some stages depend on it. Do not repair anything to make a check pass — a pass that repairs the shape it is validating cannot detect damage it caused itself.

0. **Resolve sage's root, and fail closed.** This skill installs beside sage, never inside it, so it cannot assume a path. Enumerate the candidates — `~/.claude/skills/sage/`, and a project-local `.claude/skills/sage/` under the working directory — and keep each one that holds **both** `SKILL.md` and `memory/local.md`. **Exactly one qualifying root continues the pass; zero or two stop it**, printing the paths you tried so the user names the one they meant. **Never break a tie by precedence** — never create the directory, and never promote into a sage you did not find. A promotion written to the wrong root is invisible to the sage that will actually run, and it looks from here like a clean pass.

1. **Resolve the ground.** Two commands: `[ -L <sage>/memory/shared.md ]` proves it is a symlink, then `readlink -f` canonicalizes the target (`-f` also resolves a relative link target, which a bare `readlink` hands back unresolved). The canonical path is the physical file of shared memory, not the repo: it must end in `/sage-claude/memory/shared.md` **as whole path segments**, and `<repo>` is the non-empty prefix left when that suffix is cut — `/x/not-sage-claude/memory/shared.md` matches no `/` boundary and stops. Every stage-two and stage-three edit lands under `<repo>` first. Not a symlink, a target that does not exist, or a suffix that does not match at a `/` boundary → stop. Never guess a repo path, and never write a replacement file: a second physical copy of shared memory is the fork this design exists to prevent.
2. **Prove the two trees agree.** `diff -rq <repo>/sage-claude/ <sage>/ -x memory`. It covers sage's own tree only; stage three's agent-file edits are proved separately, at their own landing, against `~/.claude/agents/`.

   A pre-existing divergence **does not stop the whole pass.** It switches off stage two, stage three, and **the whole of eviction**, with zero corpus bytes written and one surfaced line naming the divergence. Stage one still runs: it writes only memory, and a rule it promotes whose skill-text edit was skipped keeps a live `→ skill text` trigger waiting for the next pass. **Eviction has no such return path, which is why it is gated whole and never split** — see `## Eviction`. The corpus stages each end by proving this same command clean again, so a pass that starts divergent could never prove it landed.

3. **Check the structural invariants** of `local.md` and `shared.md`. `<sage>/references/memory.md`, `## Structural invariants`, is the contract, and it is complete: a check written from that section and nothing else is a complete check. Damage → stop, naming the marker.
4. **Read the four inputs.** `local.md` (Rules, Watch list, Bands, the harness stamp), `shared.md` (the standing blocks and their `- Band:` fields), `<sage>/references/memory.md` (`## The hint` for the triggers, `## Structural invariants`, `## The compression floor`), and the corpus itself — sage's `SKILL.md` and `references/`, read from the `<sage>` copy.
5. **Build the slate, then print it before writing anything.**

```
sage-promote preflight
  repo:   <the derived <repo>, from the readlink -f target>
  trees:  <identical (diff -rq clean) | divergent: <files> — stages two, three and eviction are off>
  stage one   → shared: <n> candidates, <n> band crossings
  stage two   → skill:  <n> candidates
  stage three → lineup: always runs
  eviction:            <n> falsifiers fired
```

Printing the slate first is what makes the pass consistent between runs: everything below acts on this list, and a stage whose count is zero is skipped in one printed line rather than silently.

**An all-zero slate with `lineup unchanged` is a healthy pass, not a failure to fix.** Print the report with zeros and stop. Promote nothing on judgment: never lower a threshold, round a count up, or widen a trigger to give the pass something to write. The bar is what keeps the corpus moving only on evidence, and a pass that writes nothing is the bar working.

## The checker seat

Every write below passes one refuting checker before it lands — stage one's batch refuter, and the write machinery's degradation gate. Two rules pick who sits in that seat.

- **The maker of every edit in this pass is you**, so the checker must be a different model, and a different family where one exists. `verifier-alt` in your live agent list → it takes the seat, dispatched **with no `model` parameter**: its file already names the outside-family model, and the parameter silently wins over the file (`<sage>/references/harness.md`, The alt lane — the availability rule, the config, and the measured cost of passing a model anyway). Availability is a live-session fact: read it off the agent types in your own context, never off the filesystem. The seat is not yet the diversity: every checker brief requires a `MODEL-FAMILY:` line in the report, and the cross-family claim stands only when that line — or one grep of the checker's transcript, with the command the alt-lane section gives — names an outside family. `unknown` is an absent measurement, so settle it with the grep; an Anthropic identity is a same-family check, recorded as such.
- No alt checker in the list → `verifier` takes the seat. Never let the seat land on the model that wrote the edits — under a non-frontier parent the frontier `verifier` already differs; a frontier parent gives the seat a different in-family model as a logged override — keeping the effort level in the brief and marking it `high (unverified: model override)`, because an override can cost the file's `effort` setting. Either way the report names the residual same-family bias next to the gate's verdict.

The lane reaches one non-checker seat too: stage three's vendor-docs fetch may run on `web-researcher-alt` when it is in the live agent list — that twin buys price and window headroom, never diversity, so taking it is a cost call, not a judgment call. The same no-`model`-parameter rule applies.

## The write machinery

Stage two, stage three, and eviction all write the corpus. They share one procedure, defined here once. A stage that says "under the write machinery" means every numbered step below, in order. The shape is one explore–write–review loop: the preflight and the stages' greps map the ground, you draft and write, one independent checker reviews the batch, and only survivors land — no edit of your own lands unreviewed.

1. **Draft before you write.** For every edit, hold the exact old text and the exact new text. **The reverse of the draft is the rollback. No draft, no write.** This is why rollback is never `git checkout`: a checkout cannot tell this batch's edits from pre-existing dirt in the working tree. Every edit is written to the `<repo>` copy; the installed tree changes only at step 5's byte-copy.
2. **Replace, never accrete.** Where the target already holds weaker or hedged text on the subject, the new clause replaces it. The corpus may grow by at most the clause itself. Growth beyond that means something that should have been replaced was kept.
3. **Check the whole corpus once, after the batch's last edit** — not per edit. Four checks, and a failing edit reverts by its draft:
   - **one home** — each promoted rule stands at full strength exactly once across sage's `SKILL.md` and `references/`, verified by grep. Every other mention defers or points.
   - **no contradiction** — every grep hit on the edit's subject agrees with or defers to the new clause.
   - **floor audit** — everything the batch removed, item by item against `<sage>/references/memory.md`, `## The compression floor`. Replacement under step 2, and a retirement removal carrying its named observation, are licensed. Silent loss is not.
   - **class check** — no confirmation count, no date, and no absolute cost entered skill text. Ratios and bands may; they are what the skill computes with.
4. **The degradation gate.** Dispatch **one refuting checker (`## The checker seat`) over the frozen corpus diff — one for the batch, never one per edit** — briefed to default to refuted. Its mandate: name a case the pre-edit corpus handled that the post-edit corpus handles worse, a second home for a rule, a lost floor item, or a behavior change wider than the edits claim. A refuted edit reverts by its draft; the batch's surviving edits stand. A revert restores the exact old text, so when any edit reverts, re-run step 3's four checks on the final corpus before landing — the survivors were checked against a corpus that still held the reverted text.
5. **Land the survivors in two copies.** The repo copy is already written. Byte-copy the edited files into the installed tree, then prove them identical with the preflight's `diff -rq`. A copy that fails to prove → surface and stop. **Never hand-edit the installed tree into agreement** — that is how the two copies fork while both look correct.
6. **Print the git diff** from the repo. The drafts stay the rollback; the diff is only the report.

## Stage one — into shared memory

Candidates: every `local.md` Rules row and Watch-list row whose `→ shared.md` trigger fired.

1. For each candidate, write the five fields in the order `shared.md` fixes — **rule, qualifier, recogniser, band, falsifier**. The falsifier is the observation that would retire the rule, stated concretely enough that a later run recognises it without re-reading the rule's history. **Falsifiers are sage's own machinery: none exists anywhere in `/subagents`, so write one rather than go looking for one to port.** **A candidate whose falsifier you cannot state is not ready:** leave it on the watch list and print which one you could not write.
2. Dispatch **one refuting checker (`## The checker seat`) over the whole batch, briefed to default to refuted**. A rule survives only on evidence the checker can name. One dispatch for the batch, not one per rule — the batch is what pays the boot cost.
   **A band crossing skips the refuter.** A crossing is arithmetic — the count against `shared.md`'s own thresholds — not a claim, and there is nothing for a refuter to attack.
3. Write the survivors into `shared.md`, one `##` block each. A band crossing rewrites only its standing block's `- Band:` field and nothing else.
4. Append to that rule's `Promoted` cell in `local.md`: `shared <date>`, or `band <new band> <date>` for a crossing. **The cell is a history: append with ` · ` — space, middle dot, space — never overwrite** — the → skill text guard and eviction both read its earlier entries.
5. Send each refuted rule back to the watch list **with the refutation attached**, status `watching`. It is not written to `shared.md`.
6. Print the diff.

## Stage two — into skill text

Candidates: every rule whose `→ skill text` trigger holds **when this stage begins**. Re-check here rather than trusting the preflight slate — stage one may have just written the qualifying block or moved the band.

1. **Find the rule's one home.** Grep sage's `SKILL.md` and `references/` for the rule's subject. Exactly one location may carry the rule at full strength: the step whose instructions the rule changes.
   - A citation already standing → the edit is a band-tag update in place, nothing more.
   - Standing text that **contradicts** the rule → this is a conflict, not an edit. The older sentence is a retirement candidate and needs eviction's evidence bar. Either name the retiring observation in the diff, or leave both standing and put the conflict on the watch list.
2. **Write the fewest words that clear the compression floor** — the clause, its qualifier, the recognising anecdote where the floor demands one, and `(calibration: <band>)`. Nothing of the other homes' content classes: no count, date, cost, or falsifier. **A rule that needs a paragraph is not distilled yet.** It stays in `shared.md` unwritten, with one watch-list line saying why.
3. Land every edit **under the write machinery**, all six steps.
4. Append `skill <date>` to each landed rule's `Promoted` cell in `local.md` — the guard the → skill text trigger reads.
5. For each rule the degradation gate refuted: the edit reverts by its draft, **the rule keeps full standing in `shared.md`**, the refutation goes to the watch list, and `refused <date>` is appended to its `Promoted` cell. That entry is what stops the hint offering the rule again until a band crossing or the user's word reopens it.

## Stage three — model lineup refresh

Same user word, same write machinery, **different evidence**. Stages one and two promote what runs have proven. This stage re-checks what changed _underneath_ them — the model lineup the tiers resolve to.

It is how a newly released model (a tier above apex, a cheaper fast model) enters sage within one promote instead of waiting for failures to surface it, and how a shift among current models (the standard model besting the frontier one on the checker seat; the fast model falling behind so the standard one becomes the small model) moves the **allocations** rather than just a note.

**Step 1 always runs when promote does.** This stage has no precomputed candidate list, and the hint is only the prompt to run promote — never the gate on this stage.

1. **Enumerate the live lineup against the recorded one.** Three sources:
   - the Agent tool schema's accepted `model` values in the live session;
   - `claude --version` and the changelog, against `local.md`'s harness stamp;
   - **the vendor's model docs** — one `web-researcher` (`web-researcher-alt` when it is in the live agent list — `## The checker seat`) whose brief names the snapshot table's recorded facts as its ground truth.

   The first two see only names and builds. The vendor docs are the **only** source that can see a price, window, latency, or positioning change behind an unchanged name, so that fetch runs whenever the stage does, never as a tiebreaker. A brief that names its target pages keeps it cheap.

   Compare against three recorded surfaces: `<sage>/references/harness.md`'s tier snapshot table; every `model:` line in the repo's agent sources — `grep '^model:' <repo>/claude-agents*/*.md`, which covers the base roles only, since the alt templates in `claude-agents-alt/` carry no `model:` lines; and the alt lane's configured models — `~/.claude/subagents-alt-models.conf` (or the path `SUBAGENTS_ALT_CONF` names) plus the installed `~/.claude/agents/*-alt.md` frontmatter. The conf is the machine owner's file: a deprecated or renamed alt model there is a finding for the user, never an edit.

   Collect three lists: **new** models, **removed** models, **changed facts** about current ones (price, window, latency, deprecation, capability order). All three empty → print `lineup unchanged` and the stage ends there. That determination is only step 1's own enumeration to make.

2. **Study every new model before placing it. Two measurements, never a headline.**
   - One **no-op identity probe** on a scoped saved agent, reading `message.model` from the returned transcript. That field is the only one that establishes what actually ran, and it proves both that the name is dispatchable and what it resolves to.
   - One `web-researcher` fetch of the vendor's own pricing, window, latency, and positioning pages, with a URL and a fetch date per claim.

   A reader's structural claim is a lead, not ground truth. The placement decision rests on the probe and the primary source, never on a summary.

   Newcomers study independently, so study them in parallel. One or two → plain background dispatches. Three or more, where the harness offers the `Workflow` tool → run the study as one Workflow pipeline, a probe stage and a vendor-docs stage per newcomer: the fan-out becomes deterministic control flow and the transcripts stay out of your context. Workflow runs the study only; placing every model (step 3) stays yours.

3. **Place by role, not by name.** Fit each newcomer into the ladder — fast / standard / frontier / apex — by price ratio, window, latency, and where the vendor positions it. **Write the rejects down with the same care as the placements:** the seats it must not take, and why. A model above the current apex re-opens the parent-seat question itself. A rejection is a result — it goes in the diff so the next refresh does not re-buy the study.
4. **Re-derive allocations for changed current models.** A price cut, a window change, a deprecation, or a capability flip moves allocations, not just notes: the snapshot table's rows, the roles' `model:` frontmatter in the repo's agent sources, the parent-seat and checker-seat paragraphs, and any clause in sage's `SKILL.md` that names the ordering. A deprecated model's tier falls to the nearest surviving fit — retire the fast model and the cheapest survivor becomes fast, with every row that named the old model **rewritten, not annotated**.
5. **Every edit goes through the write machinery.** Its degradation gate is briefed for this stage as: name a dispatch the old lineup served that the new one serves worse. Agent-source edits land the same way — the repo copy first, then the installed `~/.claude/agents/` copy, byte-identical.
   **Absolute prices stay out of skill text — ratios only**, per the class check.
6. The probe transcripts and any placement lesson append to `local.md` as ordinary run evidence, and the refreshed lineup's facts re-date the harness stamp.

## Eviction

Symmetric to promotion — and, like falsifiers, absent from `/subagents` entirely — and it runs here on the same user word. A falsifier firing surfaces as a hint line like any other; **it never rewrites `shared.md` on its own.**

A rule qualifies when its `Falsifier` fired — the named observation happened — or when two watch-list confirmations contradict it.

**The three steps below are one transaction, in this order: corpus first, then the `Promoted` cell, and the `shared.md` move last. Run all three or none.** The order is what makes a failure at any point recoverable: after every prefix of it, the rule is either still in `shared.md` (so the `→ retirement` trigger stays live and the next pass finishes the job — each step treats work it finds already done as done) or already marked `retired` in its cell (so no trigger re-promotes it). The reverse order is permanent damage: take the rule out of `shared.md` first and fail before the corpus cut, and the corpus cites a band for a rule that no longer exists — by this skill's own reckoning the worst false confidence it can carry — and **nothing can ever repair it**: `→ retirement` needs a rule whose falsifier fired, and the rule is gone; `→ skill text` needs a rule _in_ `shared.md`, and it is not there either. The stale citation is unreachable by every trigger the system has, and the next pass reports clean over a corpus that is still wrong. So if anything blocks step 1 — a divergent tree at preflight step 2, a landing that will not prove — **run none of the three**: the whole eviction defers to the next pass with zero bytes written. A landing that fails *inside* step 1 stops and surfaces like any landing failure: the trees diverge, the next preflight switches the corpus stages off, and the pass after the user repairs the trees finds step 1 already done and completes the rest — the rule stood in `shared.md` the whole time, so no trigger was lost. Deferring a retirement by one pass is merely slow. Splitting one against this order is permanent.

1. **Retirement reaches skill text first.** A rule whose `Promoted` cell records `skill` still stands in the corpus, citing a band this eviction is about to remove — the worst false confidence the skill can carry. Grep the corpus for its clause and its citation. Remove the hit, or cut it back to whatever weaker statement the surviving evidence supports, **under the write machinery**, with the retiring observation named in the diff. A clause a prior pass already cut — the grep finds no hit — is this step done, not an error.
   The compression floor does not shield this cut: the floor guards against cuts sold as shortening, and this is a spec change made on named evidence.
2. Append `retired <date>` to that rule's `Promoted` cell in `local.md` — with ` · `, never overwriting. This lands **before** the rule leaves `shared.md`, because it is what closes the re-promotion window: a rule already out of `shared.md` whose cell does not yet say `retired` re-qualifies for the `→ shared.md` trigger on its old count. A cell that already says `retired` is this step done.
3. Move the rule out of `shared.md` into `local-archive.md` **with the observation attached, not deleted**, tagged `retired: <the observation>`. One grep then settles why a rule that used to be there is gone.

## The report

Print this, and only this, at the end. One block, whatever the stages did.

```
sage-promote — <date>
  stage one   → shared: <n> written, <n> refuted, <n> band crossings, <n> not ready
  stage two   → skill:  <n> landed, <n> refused, <n> conflicts to the watch list
  stage three → lineup: <lineup unchanged | n new, n removed, n re-derived>
  eviction:            <n> retired, <n> corpus removals
  trees:               <the last diff -rq result: identical, or the divergence that switched the corpus stages off>
  local.md:            <n> Promoted cells appended, <n> watch-list rows
```

Then the git diff, and then — and only then — anything that needs the user's eyes: a check that stopped the pass, a rule whose falsifier you could not state, a conflict left standing, an installer change a promotion appeared to need.

Append one row to `local.md`'s Run log for this pass, like any run.

## Aborts

| Condition                                | Effect                                                          |
| ---------------------------------------- | --------------------------------------------------------------- |
| Any preflight check fails                | whole pass stops, zero bytes written, one line naming the check |
| A candidate's falsifier cannot be stated | that rule only: stays on the watch list, named in the report    |
| Stage one's refuter refutes a rule       | that rule only: back to the watch list with the refutation      |
| The whole-corpus check fails on an edit  | that edit reverts by its draft; the batch's other edits stand   |
| The degradation gate refutes an edit     | that edit reverts by its draft; `refused <date>` on its cell    |
| The landing `diff -rq` fails to prove    | stop and surface; never hand-edit the installed tree            |

**The blind spot, stated so you compensate for it.** Every check above catches structural damage and unsupported edits. **None of them catches a rule that is simply wrong.** A perfectly shaped `shared.md` full of false bands passes every marker. Falsifiers and eviction are the only defence against that, and they run on the user's word rather than on a check — which is the whole reason this skill is never automatic.
