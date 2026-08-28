---
name: sage-promote
description: Sage's self-update pass. Consolidates the run journal into knowledge items, repairs the defects sage's own runs recorded, reviews every knowledge item's statistics, promotes earned lessons into shared memory and the strongest into sage's own skill text, refreshes the model lineup, and retires knowledge that was falsified. Disuse removes nothing: an unused knowledge item is reported for the user to judge. Runs only on the user's word, never inside a run.
disable-model-invocation: true
---

# sage-promote

One pass, on the user's word. It moves what sage's runs proved into the places future runs read: the journal into knowledge items first, shared memory second, sage's own text third, the model lineup fourth. It also runs **eviction** — a rule whose falsifier fired leaves shared memory and the corpus together, so the skill never cites a band that no longer exists. **Disuse removes nothing.** A knowledge item no run has cited is reported to the user and kept; the bar for taking one out of the corpus is two entries long and lives in `<sage>/references/memory.md`, `## Knowledge items` — the removal bar.

**This is the highest-consequence write in the system.** Stage zero, stage two and stage three rewrite the corpus every future sage run boots from, and consolidation is the only writer the knowledge-item files have at all: a sage run appends journal lines and edits nothing (sage's `references/memory.md` — the v3 protocol, which this whole skill is written against). Every step below exists to keep these edits minimal, checkable, and reversible. Read it in order and do not reorder the stages: consolidation runs first because every later stage reads the KI files it brings current, stage zero next because the later stages write into the corpus it repairs, stage two reads what stage one may have just written, and stage three runs last because its evidence is the live harness rather than run rows.

**Sage never calls this skill.** A run detects two conditions and prints one hint line (sage's `references/memory.md`, `## The hint`). The user runs `/sage-promote`. Nothing here is automatic.

## What it writes

| File | Written here | Written by a sage run |
| --- | --- | --- |
| `<sage>/memory/shared/` — a directory symlink into the repo | stage zero (a standing KI's prose fields only), stage one, a band crossing, eviction | never |
| `<sage>/memory/local/` | consolidation (minted KIs, count/use bumps, status flips), stage zero closures, `promoted` histories, the harness stamp (stage three, on every pass) | never |
| `<sage>/memory/journal.md` | consolidation only: the `mark` line and the drain-truncation, plus this pass's own `run` line at the end | every run: appended lines — **the only file a run writes** |
| `<sage>/memory/archive/` | consolidation (drained journal segments), eviction, and a user-directed removal after the stale notice's manual check | never |
| `<repo>/sage-claude/SKILL.md` and `references/` | stage zero, stage two, stage three, eviction | never **on its own trigger** — a run never promotes a rule into skill text off its own memory read. This column does not describe the by-hand path: a run editing this corpus on the user's explicit word is build-authoring, which `<sage>/references/topologies.md` #12 scopes |
| `<repo>/sage-claude/bin/*.sh` | stage zero | never |
| `<repo>/claude-agents*/*.md` | stage three | never |
| the installed `<sage>` tree | the landing step only, byte-copied from the repo | never |
| the installed `~/.claude/agents/*.md` tree | the landing step of stage three only, byte-copied | never |

`<sage>` is the installed sage skill directory, resolved by preflight step 0. `<repo>` is whatever the preflight's `readlink` resolves. **The installer gives this skill nothing** — no seed tree, no drift check, no symlink of its own. It is a plain text skill that reads and writes another skill's tree, so the preflight below is the only guard those writes get.

**Never touched by this skill:** `install.sh`, `memory/local-seed/`, and this file. An installer change that a promotion appears to need is a finding for the user, not an edit — and stage zero says what to do with a defect KI that names one of them: escalate it, never close it.

## Preflight

Runs once, before any stage, in this order. **Any check failing stops the pass with zero bytes written** and one printed line naming the check that failed and the file it failed in — except step 2, which is scoped inside the step. Do not repair anything to make a check pass — a pass that repairs the shape it is validating cannot detect damage it caused itself.

0. **Resolve sage's root, and fail closed.** Enumerate the candidates — `~/.claude/skills/sage/`, and a project-local `.claude/skills/sage/` under the working directory — and keep each one that holds **both** `SKILL.md` and `memory/journal.md`. **Exactly one qualifying root continues the pass; zero or two stop it**, printing the paths tried so the user names the one they meant. Never break a tie by precedence, never create anything, and never promote into a sage you did not find.
1. **Resolve the ground.** Two commands: `[ -L <sage>/memory/shared ]` proves the shared directory is a symlink, then `readlink -f` canonicalizes the target (`-f` also resolves a relative link target). The canonical path must end in `/sage-claude/memory/shared` **as whole path segments**, and `<repo>` is the non-empty prefix left when that suffix is cut. Every stage-two and stage-three edit lands under `<repo>` first. Not a symlink, a target that does not exist, or a suffix that does not match at a `/` boundary → stop. Never guess a repo path, and never create a replacement directory: a second physical copy of shared memory is the fork this design exists to prevent.
2. **Prove the two trees agree.** `diff -rq <repo>/sage-claude/ <sage>/ -x memory`. It covers sage's own tree only; stage three's agent-file edits are proved separately, at their own landing, against `~/.claude/agents/`.

   A pre-existing divergence **does not stop the whole pass.** It switches off stage zero, stage two, stage three, and **the whole of eviction**, with zero corpus bytes written and one surfaced line naming the divergence. Consolidation, the KI review and stage one still run: they write only `memory/`, and a rule promoted whose skill-text edit was skipped keeps a live → skill candidacy for the next pass. **Eviction has no such return path, which is why it is gated whole and never split** — see `## Eviction`. The corpus stages each end by proving this same command clean again.

3. **Check the structural invariants** — `<sage>/references/memory.md`, `## Structural invariants`, is the contract and it is complete. The journal sentinel or a broken `shared` symlink → stop. **A malformed KI file does not stop the pass**: quarantine it — skip it in every stage, name it in the report — per that section's quarantine rule. Damage is per-file now; that containment is half of what v3 bought.
4. **Read the four inputs.** The journal (everything after the last `mark` line), the KI files (`bin/sage-index.sh` for the index, then the files), `<sage>/references/memory.md` (KI shapes, journal grammar, invariants, the compression floor), and the corpus itself — sage's `SKILL.md` and `references/`, read from the `<sage>` copy.
5. **Print the opening slate before writing anything:**

```
sage-promote preflight
  repo:   <the derived <repo>>
  trees:  <identical | divergent: <files> — stages zero, two, three and eviction are off>
  journal: <n> lines to consolidate (<n> run, <n> obs, <n> use)
  quarantined: <none | the malformed KI files, by name>
  stage zero  → repair: <n> defect KIs (<n> escalated)
```

The promotion slate is printed later, by the KI review — it cannot be built until consolidation has ingested the journal, which is the one ordering v3 changes.

**A pass that finds an empty journal and a clean review slate is a healthy pass, not a failure to fix.** Print the report with zeros and stop. Promote nothing on judgment: never lower a threshold, round a count up, or widen a signal to give the pass something to write.

## The checker seat

Every corpus write below passes one refuting checker before it lands — stage one's batch refuter, and the write machinery's degradation gate. Two rules pick who sits in that seat.

- **The maker of every edit in this pass is you**, so the checker must be a different model, and a different family where one exists. `verifier-alt` in your live agent list → it takes the seat, dispatched **with no `model` parameter**: its file already names the outside-family model, and the parameter silently wins over the file (`<sage>/references/harness.md`, The alt lane). Availability is a live-session fact: read it off the agent types in your own context, never off the filesystem. Every checker brief requires a `MODEL-FAMILY:` line in the report, and the cross-family claim stands only when that line — or one grep of the checker's transcript — names an outside family. `unknown` is an absent measurement; settle it with the grep.
- No alt checker in the list → `verifier` takes the seat. Never let the seat land on the model that wrote the edits — under a non-frontier parent the frontier `verifier` already differs; a frontier parent gives the seat a different in-family model as a logged override, keeping the effort level in the brief and marking it `high (unverified: model override)`. Either way the report names the residual same-family bias next to the gate's verdict.

The lane reaches one non-checker seat too: stage three's vendor-docs fetch may run on `web-researcher-alt` when it is in the live agent list — that twin buys price and window headroom, never diversity. The same no-`model`-parameter rule applies.

## The write machinery

Stage zero, stage two, stage three, and eviction all write the corpus. They share one procedure, defined here once. A stage that says "under the write machinery" means every numbered step below, in order.

1. **Draft before you write.** For every edit, hold the exact old text and the exact new text. **The reverse of the draft is the rollback. No draft, no write.** This is why rollback is never `git checkout`: a checkout cannot tell this batch's edits from pre-existing dirt. Every edit is written to the `<repo>` copy; the installed tree changes only at step 5's byte-copy.
2. **Replace, never accrete.** Where the target already holds weaker or hedged text on the subject, the new clause replaces it. The corpus may grow by at most the clause itself.
3. **Check the whole corpus once, after the batch's last edit** — not per edit. Four checks, and a failing edit reverts by its draft:
   - **one home** — each promoted rule stands at full strength exactly once across sage's `SKILL.md` and `references/`, verified by grep. Every other mention defers or points.
   - **no contradiction** — every grep hit on the edit's subject agrees with or defers to the new clause.
   - **floor audit** — everything the batch removed, item by item against `<sage>/references/memory.md`, `## The compression floor`. Replacement under step 2, and a retirement removal carrying its named observation, are licensed. Silent loss is not.
   - **class check** — no confirmation count, no date, and no absolute cost entered skill text. Ratios and bands may.
4. **The degradation gate.** Dispatch **one refuting checker (`## The checker seat`) over the frozen corpus diff — one for the batch, never one per edit** — briefed to default to refuted. Its mandate: name a case the pre-edit corpus handled that the post-edit corpus handles worse, a second home for a rule, a lost floor item, or a behavior change wider than the edits claim. A refuted edit reverts by its draft; the batch's surviving edits stand. When any edit reverts, re-run step 3's four checks on the final corpus before landing.

   **What this gate cannot see is a null effect, and step 3 cannot either** — all four of its targets are degradations, and none of step 3's checks tests behaviour. Where this batch changes text whose whole job is to make a fresh actor do something, that residue belongs to `<sage>/references/topologies.md` #12, which owns the procedure, the verdict rule and the pricing.
5. **Land the survivors in two copies.** The repo copy is already written. Byte-copy the edited files into the installed tree, then prove them identical with the preflight's `diff -rq`. A copy that fails to prove → surface and stop. **Never hand-edit the installed tree into agreement.**
6. **Print the git diff** from the repo. The drafts stay the rollback; the diff is only the report.

**Memory-only writes take the checks, not the machinery.** Consolidation, the KI review's bookkeeping, and stage one write `memory/` — one physical copy, no landing step, no repo/installed pair. They run under their own guards (consolidation's count reconciliation, the cell rule below) rather than the six steps above; only stage one's new-rule batch takes the degradation gate's refuting checker, because it is the one memory write that mints standing claims.

## The cell rule

Everything this skill writes into a KI's frontmatter about a rule's state is a **claim that a write landed somewhere else**: a `promoted` history entry — `shared <date>`, `band <b> <date>`, `skill <date>`, `retired <date>`, `refused <date>` — a `status` flip, a minted stats sidecar. **Verify the artifact, never the cell.**

1. **Read the artifact back with a command, from the file on disk** — never from your draft, and never from the tool result that said the write succeeded. For a shared-KI write, print the file's own field:

   ```sh
   awk -v f="<sage>/memory/shared/<slug>.md" 'BEGIN{ok=0} /^band: /{print;ok=1} END{exit !ok}' "$(eval echo "<sage>")/memory/shared/<slug>.md"
   ```

   — or simply `grep -c '^band: ' <file>` with the id checked first; the point is the read hits the landed file, exits non-zero on absence, and never trusts empty output at exit 0. For a corpus write, grep the landed file for the clause stage two step 1 located — its instruction half and its `(calibration: <band>)` tag. For a removal, grep for that string's absence.
2. **The read-back fails → write no history entry, and flip no `status`.** There is nothing to roll back: the write is what did not happen. Name the KI in the report's user-facing tail. A missing entry re-qualifies the candidate on the next pass; an entry claiming a landing that never happened can disqualify it for ever.
3. **Re-verify every claim this pass wrote, once, before the report — on every exit path, a stopped pass included.** A read-back proves the artifact at read-back time only; a later revert restores old text and never touches the frontmatter that already claimed it. A claim whose artifact no longer carries the text is **undone, not amended** — and undone **whole**: the `promoted` entry, the `status` flip, and the minted stats sidecar all revert together. A half-undone promotion — the flip standing, the artifact gone — is the permanent false state this section exists to prevent, because a KI whose status is not `watching` is invisible to every promotion signal.
4. **Which false entries self-correct, and which do not.** A false `shared` on a lesson KI travels with the `status` flip to `promoted →` — invisible for ever; that is why the flip reverts whole. A false `band` re-fires the crossing arithmetic on the next review. A false `retired` leaves the rule in `shared/` with its falsifier observed, so retirement stays live. A false `skill` is caught by stage two's corpus re-check, because a `skill` entry asserts a standing home a grep can find. **Nothing catches a false `refused`** — a true refusal and a false one look identical, neither has a home to find — which is why step 5 makes it a rule about the write rather than a check afterwards.

   **A fourth case is not a false entry at all, and it hides behind a true one.** A refusal can be **partial** (`## Stage two` step 5): the `refused` entry true, the `skill` entry the same edit earned never written. Stage two's step 0 is its only detector, and step 5's rule — write both entries when the gate refutes only a part — is what keeps the case from arising.
5. **`refused` is the one entry with no artifact to read back**, because it records a write deliberately not made. Write it only from a refutation actually recorded this pass — stage one step 5, stage two step 5, or the degradation gate. It suppresses the → skill signal exactly as a `skill` entry does, and nothing anywhere re-fires on it.

The recogniser, from a real pass: it recorded a `band established` entry for two rules while both shared blocks still read `recurring`, and git showed neither had changed. Only the band arithmetic re-firing two passes later caught it. Read the file back before you write the claim.

## Consolidation

**The first stage, and the journal's only drain.** Candidates: every payload line after the last `mark` in `<sage>/memory/journal.md`. In v2 this ran automatically at a run's Step 2, which put the highest-frequency structured write on the least-supervised path; v3 moves it here, whole.

1. **Ingest, in journal order.**
   - An `obs` line with a kind and class → **mint a local KI file** of that kind, carrying every field invariant 2 and the field contract require of it: `id:` (the slug), `kind:`, `class:` (from the line), `status: watching`, `count: 1`, `first:`/`last:` from the line's date, `created:` from that same date and `last-used: —`, `promoted: —`, `contradicts:` where the kind is `contradiction`, and the falsifier in the body where the line carries one. A mint the invariants would quarantine is a mint that never should have been written. Where an existing KI already records the same observation, treat the line as a `confirm` of it instead — one KI per observation, because three separate count-1 KIs fire no threshold ever.
   - A `confirm <ki-id>` line → bump that KI's `count`, extend `last`, and add `+ local run` to `provenance` where the confirmation is this machine's. The named KI missing → surface the line as a question, ingest nothing for it.
   - A `settle <ki-id>` line → flip that KI's `status` to `settled → <artifact>` **only after checking the named artifact exists** — one `ls` or grep; the closure evidence bar in `references/memory.md` binds this flip, and a line whose artifact does not resolve is surfaced, not applied.
   - A `use` line → bump `uses` and `last-used` on each named KI's **local record**: the stats sidecar (`local/<id>.stats.md`) where the id names a shared KI — minted with zeroed stats and `created:` set to the shared KI's own filing date if none exists yet — and the KI file itself where the id is local. **A file under `shared/` never gains a stat**: that is the machine-specific-data fork the shared/local split exists to prevent. A `miss` appends one dated line under a `Misses` heading in the same local record and bumps `misses`. Absent usage fields on a touched KI are added, not errors (`references/memory.md`, the field contract). These are the KI review's raw signal.
   - A `run` line → stays in the journal until the drain below; run lines are pricing data, not KI content.
   - A line that parses as none of these → print it as a question; never guess, never drop.
2. **Reconcile a migrated count against the archive — once per KI, never every pass.** A `confirm` line is not the only record a confirmation ever had. KIs carried over from v2 hold counts that were maintained by hand, and `<sage>/memory/archive/` narrates confirmations and citations that never became journal lines, so consolidation alone can never see them. For every stats sidecar and local KI whose frontmatter carries no `reconciled:` field:

   - Grep the archive for the KI's `id` **and** its prose title — both spellings, since v2 wrote titles and v3 writes slugs.
   - **Read every hit before counting it, and classify it.** A passage stating a `Count` is a count. A passage narrating a run that *cited* the rule is a **use**, not a confirmation — it bumps `uses:` and `last-used:`, never `count:`. Getting this backwards is the recorded failure this step exists to prevent: the two live instances that produced this procedure were read as under-counts when what the archive actually narrated was three uses apiece. A `grep -c` counts mentions, so it settles neither.
   - Raise `count:` only where the archive states a higher **count** than the sidecar does, and append `+ local run` to `provenance:` where the archive names a run on this machine rather than a seed. **Add** the citations to `uses:` — the archive and the journal are disjoint sources, so this sums rather than overwrites — and take the later of the two `last-used:` dates. Record the prior `uses:` alongside the new one, or the block's arithmetic cannot be checked from the block.
   - Write the archive's `file:line` for every figure you moved into the KI's body under a `## Reconciled` heading, so the next pass can check the arithmetic rather than repeat it.

   Then stamp `reconciled: <date>` into the frontmatter. **A sidecar carrying it is skipped for ever after** — this is a migration debt, not a recurring stage, and re-running it double-counts. A pass that reconciles nothing writes the stamp anyway, so the walk shortens to zero.

3. **Drain.** Append a `mark` line, move every payload line above it **except the newest three `run` lines** verbatim into `<sage>/memory/archive/journal-<first-date>-<last-date>.md`, and rewrite the live journal as: sentinel, header, the kept `run` lines, the `mark`. The newest-three rule is Step 2's same-shape pricing window; the archive is where a provenance grep goes.
4. **Two checks guard the write, both must pass or the stage reverts to the pre-stage journal and KI state** (hold both in drafts, exactly as the write machinery holds corpus edits): every drained line survives verbatim in the archive — count in equals count out; every KI file touched still passes the frontmatter invariants. A human approving a diff is not this safeguard: the one recorded v2 corruption landed *through* an approved diff.

## Stage zero — corpus repair

Candidates: every local KI whose `kind` is `defect` and whose `status` begins `watching` — including ones consolidation just minted.

**It runs before the promotion stages, and the order is the whole point.** A defect KI records a fault in the corpus the later stages are about to write into. Repair first, promote into the repaired corpus second.

1. **Re-verify before you repair.** A defect KI is a lead, not a spec: re-check it against the file it names with one command. No longer reproduces → `status: settled → no longer reproduces <date>`. Its subject gone → `dropped → <what was removed> <date>`.
2. **Repair the survivors as one batch, under the write machinery**, so the degradation gate sees the whole repair.
3. **What this stage may write:** `<repo>/sage-claude/SKILL.md`, `references/`, `bin/*.sh` — landing at the machinery's step 5 — **and the prose fields of a standing KI in `memory/shared/`**: the Rule sentence, `- Qualifier:`, `- Recogniser:`, `- Falsifier:` of a KI that stays. A field that is simply untrue is a repair, and repairs are this stage's. **The boundary is hard and single-owner:** stage zero may never add a shared KI, remove one, or touch a `band:` field — band is the review's arithmetic, and removal is eviction's. A shared-KI repair needs no landing copy (the directory is a symlink; both trees hold the one file), but every other machinery step binds — and **brief the gate to re-measure the claim the field makes, not to read the diff**: both repairs this clause was written for were factually wrong, passed all four text checks, and were killed only because the gate sampled the world.
4. **What it may not write:** `install.sh`, `memory/local-seed/` and this file. A defect KI naming one of them is **escalated, never closed**: print it as a finding and set `status: watching (escalated <date>: <path> is on the never-touched list)`.
5. **Close every repaired KI** — `status: settled → <file> <date>`, under `## The cell rule`: grep the named file for the repair before flipping. A repair that leaves its KI open is re-done by the next pass; a KI closed without the artifact is permanent false peace.
6. Print the slate: repaired, escalated, no-longer-reproduces.

## The KI review

**The anti-blindness stage, new in v3.** After consolidation and stage zero, walk every KI — `bin/sage-index.sh` is the walk — read its stats, and build the slate the remaining stages execute. v2 computed these signals as run-side hint triggers that runs never acted on; v3 computes them here, where the actor is.

| signal | threshold | routes to |
| --- | --- | --- |
| portable `lesson` KI: `count` ≥ 3, `status` `watching`, `promoted` records no `refused` dated after `last` | promote to `shared/` | stage one |
| stats sidecar: `count` ≥ 6, `promoted` records neither `skill` nor `refused` | promote into skill text | stage two |
| stats `count`-derived band (thresholds in `references/memory.md`: 3 recurring, 6 established) **exceeds** the shared KI's `band:` | band raise — **upward only**: a count below the standing band is a machine that has seen less, never a crossing | stage one (crossing) |
| a shared KI's falsifier observed, or a `contradiction` KI naming it reaches `count` 2 | retirement | eviction |
| `misses` ≥ 2 on any KI (an absent `misses` field reads as 0) | repair or retire — judged, with the miss notes as the evidence; a repairable misread mints a `defect` KI for the next pass's stage zero, a wrong rule routes to eviction. **A miss is the KI misleading a run — its falsifier firing in miniature — which is why this row may remove and the stale row may not** | judged |
| `bin/sage-index.sh --stale 3` names the KI: nothing has cited it for three months or more, measured from `last-used:` — or from `created:` where nothing ever has | **notify the user, remove nothing** | `## The stale notice`, below |
| `gap` KI whose measurement landed (its own text names what it waits for) | settle against the artifact | this stage, under the closure bar |

Print the full slate — one line per candidate with its signal — before executing anything. The user sees what the pass is about to do while it is still nothing but a list.

## The stale notice

**A knowledge item is never removed for being unused.** The removal bar — the whole list of what may take a KI out of the corpus — is `<sage>/references/memory.md`, `## Knowledge items`, `### The removal bar`. **Read it there and do not restate it here:** this is the skill that executes removal, so a copy of the bar living in this file is the copy that goes stale while still being the one acted on. Disuse is not on that list, whatever its entries are on the day you read them. What disuse earns is this notice.

It is a command, not a judgment:

```sh
<sage>/bin/sage-index.sh --stale 3 <sage>/memory
```

Three months is the bar. Every line it prints goes into the report's `stale:` block verbatim, oldest first, and the trailing `#` line — the KIs whose age no date proves — goes with it. **Print the block whole and never trim it to a sample**: a truncated notice reads as a short list, which is the one thing this block must not do. Then stop. The pass takes no action on any line of it.

**The manual check, and it is the user's to run.** The notice asks a question this pass cannot answer, because the counter measures what runs *reported*, not what they *used*, and the two have already diverged here: runs report the cost bands they price from and skip the rules they read at Step 2. So the disposition is a `/sage` run on the user's word, with this brief:

> For each KI in the stale block, read the run records since its `last-used:` date and answer one question with evidence: **is there a workflow in that window that would have gone better had this KI been read?** Name the run and the decision it would have changed, or say there was none. Only then say whether the KI is wrong, redundant, or simply uncalled-for.

The three answers route differently, and only one of them removes anything:

| The check finds | What it means | What happens |
| --- | --- | --- |
| A run that would have gone better with it | The KI is live and the **reporting** is broken, not the KI | Keep it. Mint a `defect` KI against the `use`-line duty in `<sage>/references/memory.md`, `## Append at Step 6`, naming the run that missed it |
| No such run, and the KI is still true | Nothing has needed it yet | Keep it, unchanged. A KI that has not paid out is not a KI that is wrong, and a corpus holding only knowledge it already uses can never tell a run something it does not already do |
| The KI is wrong, or its subject is gone | Falsified, or unfixable — the removal bar's own two entries | On the user's word: `status: archived → <the user's reason> <date>`, file moved to `archive/`, reversible by moving it back |

**Never take the third branch on your own reading.** The user's word licenses it, for the same reason rail 1 in a sage run needs one: it is the only act in this pass with no automatic way back.

## Stage one — into shared memory

Candidates: the KI review's → shared and band-crossing lines.

1. For each promotion candidate, draft the shared KI: `id`, `kind: rule`, `class: portable`, `band` from its count (3–5 `recurring`, 6+ `established`), `status: live`, and the body's four parts — the **rule** as a bold sentence, `- Qualifier:`, `- Recogniser:`, `- Falsifier:`. The falsifier is the observation that would retire the rule, stated concretely enough that a later run recognises it without the rule's history. **A candidate whose falsifier you cannot state is not ready:** leave it watching and print which one.
2. Dispatch **one refuting checker (`## The checker seat`) over the whole batch, briefed to default to refuted**. A rule survives only on evidence the checker can name. One dispatch for the batch. **A band crossing skips the refuter** — a crossing is arithmetic, upward only, adding confidence a count already earned; a downward rewrite is eviction's alone.
3. **Mint the id first, then write the survivors** — one `shared/<slug>.md` each. The id is the join: stats sidecars' `for:`, `use` lines, and skill-text citations all key on it. A crossing rewrites only the standing KI's `band:` line.
4. **Land the bookkeeping in `local/`, every claim under `## The cell rule`** — read the shared file back from disk before writing any of it: mint the stats sidecar (`for:` the new id, `count`/`first`/`last`/`provenance` carried verbatim from the lesson KI, `created:` and `last-used:` carried verbatim too — invariant 2 requires both on every local KI and a sidecar missing them is quarantined on the next preflight, which silently disqualifies the rule for ever — and `promoted: shared <date>`), flip the lesson KI's `status` to `promoted → <id>`, append `shared <date>` to its `promoted`. **Writing the shared KI without minting the sidecar is the v2 defect moved one file over** — every later signal reads counts from sidecars, so a rule without one can never band-raise, never reach skill text, never retire on contradictions. For a crossing: append `band <new band> <date>` to the sidecar's `promoted` — ` · ` separated, **append, never overwrite** — the → skill guard and eviction read the earlier entries.
5. Send each refuted candidate back **with the refutation attached**: `status` stays `watching`, `refused <date>` appended to its `promoted`, the refutation added to its body. **The refusal goes in `promoted`, never in `status`** — a refused candidate is not closed, it is ineligible until evidence newer than the refusal arrives, and the review's first signal reads exactly that.
6. Print the diff.

## Stage two — into skill text

Candidates: every rule the KI review routed here, re-checked **when this stage begins** — stage one may have just minted the qualifying sidecar. **Re-check the corpus, not only the frontmatter**: a rule whose `promoted` records `skill` but for which step 1's grep finds no standing home is a candidate, not a landed rule. Never apply that absence test to a `refused` entry — a refusal records a home deliberately not made. The **inverse** test is step 0, and it is safe on any entry.

0. **Repair a frontmatter history that records no landing, before reading a single candidate.** For every stats sidecar whose `promoted` records no `skill` entry, grep `<sage>`'s `SKILL.md` and `references/` for the rule's subject. A hit carrying the rule at full strength **and a `(calibration: <band>)` tag** is a standing home the history does not record — the tag is the discriminator, because step 2 writes one on every landing and a merely mechanical mention never has one. Date it from the repo's own history, and write nothing until this answers:

   ```sh
   git -C <repo> log -S'<a distinctive phrase from the landed clause>' --format='%h %ad' --date=short -- sage-claude/SKILL.md
   ```

   Exactly one commit → append `skill <that commit's date> (cell repair <today>: home found standing, dated by git log -S <sha>)`. **Zero commits, or more than one → write nothing and name the KI in the report's tail.** Substitute the `references/` file where the home is there. This writes frontmatter and nothing else — no corpus byte, no status flip — so it is outside the write machinery; like the rest of this stage it does not run on divergent trees. It is licensed against the cell rule's no-repairing-earlier-passes line because two commands decide it, and it is the only detector for a **partial refusal** from a pass that predates step 5's rule.

1. **Find the rule's one home.** Grep sage's `SKILL.md` and `references/`. Exactly one location may carry the rule at full strength: the step whose instructions the rule changes. A citation already standing → the edit is a band-tag update in place. Standing text that **contradicts** the rule → a conflict, not an edit: the older sentence is a retirement candidate under eviction's evidence bar, or both stand and the conflict becomes a `contradiction` KI.
2. **Write the fewest words that clear the compression floor** — the clause, its qualifier, the recognising anecdote where the floor demands one, and `(calibration: <band>)`. No count, date, cost, or falsifier. **A rule that needs a paragraph is not distilled yet** — it stays in `shared/` unwritten, with one lesson-KI line saying why.
3. Land every edit **under the write machinery**, all six steps.
4. Append `skill <date>` to each landed rule's sidecar `promoted`, under `## The cell rule`.
5. For each rule the degradation gate refuted: the edit reverts by its draft, **the rule keeps full standing in `shared/`**, the refutation goes to its sidecar's body, and `refused <date>` is appended to `promoted`. **A gate that refutes only *part* of an edit writes both entries** — `skill <date>` for what landed and `refused <date>` naming the part that did not. Writing only the refusal is the measured five-day-silent failure step 0 exists to catch: the missing `skill` suppresses exactly what `refused` already suppresses, so no signal ever changes behaviour and nothing notices.

## Stage three — model lineup refresh

Same user word, same write machinery, **different evidence**: this stage re-checks what changed *underneath* the rules — the model lineup the tiers resolve to. **Step 1 always runs when promote does**; the hint is only the prompt to run promote, never the gate on this stage.

1. **Enumerate the live lineup against the recorded one.** Three sources: the Agent tool schema's accepted `model` values in the live session; `claude --version` and the changelog, against the `harness-stamp` KI; **the vendor's model docs** — one `web-researcher` (`web-researcher-alt` when live — `## The checker seat`) whose brief names the snapshot table's recorded facts as its ground truth. The first two see only names and builds; the vendor docs are the only source that sees a price, window, latency or positioning change behind an unchanged name, so that fetch runs whenever the stage does. Compare against three recorded surfaces: `<sage>/references/harness.md`'s tier snapshot table; every `model:` line in the repo's agent sources (`grep '^model:' <repo>/claude-agents*/*.md`); and the alt lane's configured models (`~/.claude/subagents-alt-models.conf` or `SUBAGENTS_ALT_CONF`, plus installed `*-alt.md` frontmatter — the conf is the machine owner's file: a stale model there is a finding, never an edit).

   All three lists empty → **re-date the harness stamp, then** print `lineup unchanged` and the stage ends. **Re-dating on a no-change pass is the difference between a live sensor and a dead one**: the stamp records what was last **verified**, and a pass that enumerated the lineup and found it unmoved has verified it. Leave it behind the build and the lineup hint fires on every later run carrying no information. **Re-sort the stamp's prose; never rewrite it**: only what this pass actually checked moves into the "verified live under `<build>`" list; everything untouched keeps its older attribution verbatim — an overclaiming stamp is worse than a stale one because a stale one is visibly stale. The stamp is the artifact itself, not a claim about one, so it takes the read-back without the cell rule's machinery: `grep '^sage-harness-stamp:' <sage>/memory/local/harness-stamp.md` must show the build `claude --version` just reported, or the write did not land — name it in the tail and leave the stage's other work standing.

2. **Study every new model before placing it. Two measurements, never a headline:** one no-op identity probe on a scoped saved agent, reading `message.model` from the returned transcript; one `web-researcher` fetch of the vendor's own pricing, window, latency and positioning pages, with a URL and fetch date per claim. Newcomers study independently, so study them in parallel; three or more with the `Workflow` tool available → one Workflow pipeline. Placing them (step 3) stays yours.
3. **Place by role, not by name.** Fit each newcomer into fast / standard / frontier / apex by price ratio, window, latency, vendor positioning. **Write the rejects down with the same care as the placements** — a rejection is a result and goes in the diff so the next refresh does not re-buy the study. A model above the current apex re-opens the parent-seat question itself.
4. **Re-derive allocations for changed current models.** A price cut, window change, deprecation or capability flip moves the snapshot table's rows, the roles' `model:` frontmatter, the parent- and checker-seat paragraphs, and any SKILL.md clause naming the ordering — **rewritten, not annotated**.
5. **Every edit goes through the write machinery.** Its gate is briefed: name a dispatch the old lineup served that the new one serves worse. Agent-source edits land repo-first, then the installed `~/.claude/agents/` copy, byte-identical. **Absolute prices stay out of skill text — ratios only.**
6. Probe transcripts and placement lessons append to the journal as ordinary `obs` lines, and the refreshed facts re-date the stamp — the same re-dating as step 1's early exit, under the same two rules.

## Eviction

Symmetric to promotion, on the same user word. A falsifier firing routes here from the KI review; **nothing rewrites `shared/` on its own.** A rule qualifies when its `Falsifier` fired — the named observation happened — or when a `contradiction` KI naming it reached two confirmations. **Those two are the whole of what qualifies a rule for eviction, and disuse is not among them**: a rule nothing has cited leaves through `## The stale notice`'s manual check, on the user's word, or it does not leave at all (`<sage>/references/memory.md`, the removal bar).

**The three steps below are one transaction, in this order: corpus first, then the sidecar entry, and the `shared/` move last. Run all three or none.** After every prefix of it, the rule is either still in `shared/` (so retirement stays live and the next pass finishes — each step treats work already done as done) or already marked `retired` in its sidecar (so nothing re-promotes it). The reverse order is permanent damage: take the file out of `shared/` first and fail before the corpus cut, and skill text cites a band for a rule that no longer exists — unreachable by every signal the system has, because retirement needs a rule whose falsifier fired and the rule is gone. If anything blocks step 1 — divergent trees, a landing that will not prove — **run none of the three**.

1. **Retirement reaches skill text first.** Grep the corpus for the rule's clause and citation; remove the hit, or cut it back to what the surviving evidence supports, **under the write machinery**, with the retiring observation named in the diff. A clause a prior pass already cut is this step done. The compression floor does not shield this cut: the floor guards against cuts sold as shortening, and this is a spec change on named evidence.
2. Append `retired <date>` to the rule's sidecar `promoted`, under `## The cell rule` — step 1's cut is the write this entry claims, so grep for the clause's absence. This lands **before** the file moves, because it closes the re-promotion window. An entry already there is this step done.
3. Move `shared/<slug>.md` into `archive/` **with the observation attached in the file**, `status: retired → <the observation> <date>`. One grep then settles why a rule that used to be there is gone. The stats sidecar stays in `local/` — it is the record that the rule existed and what it counted.

**Clause-level retirement** — a falsifier or two contradictions killing one sentence inside a KI whose rule keeps standing — is stage zero's: file a `defect` KI so the repair stage cuts the sentence and the rule stays. Do not stretch this transaction to cover it.

## The report

Print this, and only this, at the end. One block, whatever the stages did.

```
sage-promote — <date>
  consolidation:       <n> lines ingested (<n> KIs minted, <n> confirms, <n> settles, <n> use bumps), <n> archived, <n> questions
  stage zero  → repair: <n> repaired, <n> escalated, <n> no longer reproduce
  KI review:           <n> → shared, <n> → skill, <n> crossings, <n> retirement, <n> miss-flagged
  stale notice:        <n> KI(s) unused >= 3 months, <n> not assessable — reported, nothing removed
  stage one   → shared: <n> written, <n> refuted, <n> not ready
  stage two   → skill:  <n> landed, <n> refused, <n> conflicts filed
  stage three → lineup: <lineup unchanged | n new, n removed, n re-derived>, stamp → <build> <date>
  eviction:            <n> retired, <n> corpus removals
  trees:               <identical, or the divergence that switched the corpus stages off>
  quarantined:         <none | the KI files skipped, by name>
```

Then the git diff, and then — and only then — anything that needs the user's eyes: a check that stopped the pass, a falsifier that could not be stated, a conflict left standing, a journal line that would not parse, an escalated defect.

Append this pass's own `run` line to the journal, like any run.

## Aborts

| Condition | Effect |
| --- | --- |
| Preflight step 0, 1 or the journal/symlink invariants fail | whole pass stops, zero bytes written, one line naming the check |
| A KI file fails the frontmatter invariants | that KI only: quarantined — skipped by every stage, named in the report |
| Consolidation's count reconciliation or invariant check fails | the stage reverts whole to the pre-stage journal and KI state; later stages still run on the un-ingested state, and the report says so |
| A `settle` or `confirm` line names a missing KI or artifact | that line only: surfaced as a question, nothing applied |
| A candidate's falsifier cannot be stated | that rule only: stays watching, named in the report |
| Stage one's refuter refutes a rule | that rule only: back to watching with the refutation, `refused` on its history |
| The whole-corpus check fails on an edit | that edit reverts by its draft; the batch's others stand |
| The degradation gate refutes an edit | that edit reverts; `refused <date>` on its history |
| The landing `diff -rq` fails to prove | stop and surface; never hand-edit the installed tree |
| A read-back fails | that claim only: nothing written, the KI named in the report |
| A pass-end re-verification fails | that candidate only: every claim this pass wrote for it is undone whole and named |
| Stage three's stamp read-back does not match the build | that write only: named in the tail, the stage's other work stands |

**The blind spot, stated so you compensate for it.** Every check above catches structural damage and unsupported edits. **None of them catches a rule that is simply wrong.** A perfectly shaped `shared/` full of false claims passes every marker. Falsifiers, recorded misses, and eviction are the only defence against that — and they run on the user's word, which is the whole reason this skill is never automatic.
