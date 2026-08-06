# Review: blind QA / test-suite track for the /subagents skill — 2026-08-06

Critical review of a proposed addition. Recommendation only; nothing here is applied to the skill.
File references use the repo paths (`subagents-claude/...`). Line numbers are from the current
commit.

**Revision v2, same day.** After round one, the user clarified the proposal and added three
directives. The clarification: the suite is a requirement-level QA test suite. It is written test
cases, not test code. The directives: gates should recommend a form, not enforce it; gate options
must survive the client UI; the final message must put the result before the run report. This
version reworks the verdict, the design, the gates, and the edit set. Round-one analysis is kept
where it still holds. The evidence tables are unchanged, and their verification status carries
over.

## The proposal under review

As stated by the user in round one:

1. A QA subagent (or team) builds a test suite in parallel with the implementer subagent(s). It
   works from the requirements only, with no knowledge of the implementation, so later
   verification is as unbiased as possible.
2. The suite is a guideline of what the final product must do, per the initial requirement.
3. Like the implementation, the suite itself is verified by another subagent.
4. When implementation finishes, it passes both the current reviewer/verifier stage and a new
   round of verification that runs the suite. This is black-box testing: checking a thing only
   through its public surface, without reading its code.
5. The process needs a gate, because not every target needs a test suite. The one gate offered:
   run it only when the target is a code implementation.

Clarified and extended in round two:

6. **The suite is not test code.** It is a QA-style suite of written cases describing expected
   behavior. The user's example, for "add SAML SSO" (single sign-on, where the app delegates
   login to an outside identity provider, the IdP): *user clicks Login → is redirected to the
   correct IdP → signs in there → returns to the original page signed in, with account fields
   synced from the IdP.*
7. **The suite drives verification downstream.** Where possible, cases become integration tests.
   Where not, the diff reviewer checks the change against the cases.
8. **Recommend, don't enforce.** Both forms are always offered; gates only set the
   recommendation. A gate hides an option only when that form cannot run at all.
9. **Two output rules for the skill itself.** Gate options must render fully in the client UI,
   and the final message must give the summarized result before any report on agent activity.

## Verdict

**Adopt, in the clarified shape.** Round one read the proposal as blind *test code* authored in
parallel with the implementation, and against that reading said: adopt the capability, reject the
shape. The clarified artifact changes the trade, because a requirement-level case suite:

- needs no code interface to call, so round one's hardest problem (interface coupling, problem 1
  below) does not exist for it;
- writes one file in scratch space, so the two-writers violation (problem 5) does not exist
  either — parallel authoring becomes safe by construction;
- costs a small unit that reads a little and writes one file, not a code writer in an isolated
  worktree;
- serves three consumers instead of one: the verifier (per-case checklist), the diff reviewer
  (coverage lens), and an optional compile step into executable tests.

What round one rejected and still rejects: the "QA team" plural (one unit is enough), a dedicated
frontier-model review round for the suite (a traceability scan plus a red-check on the executable
subset does more for less), and treating a failing case as a verdict (failures are findings, and
triage decides).

One honest limit belongs up front. **A written case is not an oracle.** An oracle is the thing
that decides what "correct" means. An executable test decides by itself: it passes or fails. A
written case decides only through a judge: a verifier reads "redirected to the correct IdP" and
must rule on what it observed. The strongest evidence in this document — tests written blind
detect 25% of faults against 14% for tests written after seeing the code (E1) — was measured on
executable tests. For written cases the same bias mechanism is argued, not measured. The design
below carries that limit explicitly: every case names its check method, a case the verifier
cannot check returns `Awaiting human` — the skill's existing third verdict — and a case only a
human can judge routes to the human checkpoint the skill already has.

The two forms, renamed to match the clarified artifact:

- **Suite only** — the written case suite plus its consumers. Possible whenever the plan
  carries a deliverable to check and checkable acceptance criteria can be extracted without
  inventing behavior.
- **Suite + executable tests** — additionally, after the implementation freezes, every case
  tagged machine-verifiable is compiled into a runnable test. Possible only when the target
  runs in this session.

Round one's "light form" survives as the compile step. Round one's "full form" (a parallel
worktree unit writing test *code* against a frozen interface) is no longer offered; the section
on the executable extension says why.

## The gap is real

Four places in the current skill argue *for* the proposal:

- The skill's opening line promises "independent evidence — tests, reproductions, measurements,
  verified findings — not a chain of agreeing opinions" (`subagents-claude/SKILL.md:10`). Tests
  are named first. Yet no pattern in `references/patterns.md` ever *produces* tests independently.
  Reviewers read code. Reading produces an opinion; a run produces a measurement. (Model-generated
  tests have driven candidate *selection* at scale (E4), though as a ranking signal over many
  samples, not as an acceptance oracle for one candidate. The acceptance role is the new part.)
- The risk rubric already names the role: "optional plan critic / independent test designer (each
  justified by a named trigger)" for high-risk work
  (`subagents-claude/references/contracts.md:103`). It is a stub. There is no pattern, no brief
  shape, no gate, and no execution slot for it. The proposal is best read as the missing
  operational half of that line.
- The two-stage review demands "explicit pass/fail per acceptance criterion"
  (`subagents-claude/SKILL.md`, Step 6). Today a reviewer produces that verdict by reading. A
  case suite turns the same reading into a fixed per-case checklist, and its executable subset
  turns it into something a command can produce. Step 6 already says "Deterministic checks run
  before model review — don't pay a reviewer to find what a compiler finds."
- The software evidence menu requires tests as evidence
  (`subagents-claude/references/patterns.md:66`) but never says who writes them. In practice the
  implementer does. Tests written by whoever wrote the code inherit its blind spots: they assert
  what the code does, not what the requirement says. That bias is measured, not assumed (E1).

One more, from the repo's own history: `improvements-2026-08.md` closes by admitting "every
finding in this review is an argument from reading, not from measurement." The skill's culture
already treats executable evidence as the missing grade above review. This proposal brings that
grade to orchestrated implementation runs.

## The artifact: a requirement-level case suite

### Shape

One scratch-space file. Numbered cases. Each case has five parts: an ID, the criterion it traces
to, the steps, the expected observable outcome, and the check method. In the user's SAML example:

```text
C3 — login round-trip through the IdP                     [traces to criterion R2]
Steps: user clicks Login → browser redirects to the configured IdP → user
signs in there → browser returns to the page they started on.
Expected: the user is signed in; displayed name and email match the IdP account.
Check [machine-verifiable]: browser-level test if the stack allows one; otherwise
trace the redirect chain in the HTTP log and read the created session record.
```

The check line is what keeps the suite honest. A case that cannot say how it will be checked is
an opinion with steps. Each check line also carries one class tag from the skill's existing
criteria taxonomy — machine-verifiable / agent-observable-but-subjective / human-only
(`references/patterns.md:68`) — because a compile rule downstream keys on the tag, and prose
alone is not decidable: C3's own check line is conditional ("if the stack allows one"), so
whether it "names an executable check" would be a judgment call. The v2 adversarial pass caught
exactly that. A conditional line tags machine-verifiable; if the toolchain cannot express it at
compile time, the case downgrades to agent-observable and the downgrade is recorded, never
silently dropped.

### Who writes it, and what "blind" now means

With test code, the thing to hide was the implementation. With requirement-level cases, the
plan's design must be hidden too. By plan time the parent has chosen an approach, so a
parent-authored case would test the chosen design, not the requirement. Concretely: if the plan
picks cookie-based sessions, the parent's case asserts a cookie; a blind case asserts the user
is still signed in on the next page load. The second survives a design change. The first does
not.

So the author is one small standard-tier unit, plain dispatch. Its inputs: the requirement text,
the approved acceptance criteria, and a minimal environment sketch the parent chooses ("a web app
with a Login button"). Not the plan's design section, not the source, not any diff. Its output:
one file in scratch space. Its rule for gaps: an ambiguity it cannot resolve from the
requirements returns as a **question**, never as a case.

The criteria are themselves an inlet the firewall has to name. The parent writes them at plan
time, after choosing an approach, so a design noun inside a criterion carries the design
straight through the blind. Two rules close most of it. Criteria handed to the author are
phrased at the requirement's observable surface — no module names, data stores, or mechanism
choices — and the user's co-sign at the gate doubles as a check that they read as the
requirement, not as the parent's design. And the skill needs one carve-out: Step 4 tells every
brief to name "the decisions already made" (`SKILL.md:150`); a blind-authoring brief is the
deliberate exception, receiving the decisions' observable consequences and never the decisions.

Timing needs an honest sentence about P5. Cognition's stated bar for safe parallelism is
strict: sequential, read-only, question-answering work — the post approves Claude Code's
research subagent partly because it "operates sequentially (never in parallel)". A case author
that runs while the implementer runs does not meet that bar as written. (v2's first draft
quoted the bar with the "sequential" clause dropped and claimed the unit passes it; the v2
adversarial pass caught the edited citation — the same clause a round-one fix had restored.)
The design runs the author in parallel anyway, on the skill's own grounds rather than
Cognition's: it writes nothing in any tree, exchanges nothing with the implementer mid-flight,
and its output binds no one until the parent consumes it at verification. The conflict
mechanism Cognition describes needs decisions that constrain another agent's actions. The skill
already accepts parallel readers on this reasoning, and the corpus records how that
disagreement was settled (`research-2026-08-agent-orchestration.md`, section 1).

### Who consumes it

1. **The verifier**, as its checklist. Step 6 already demands "explicit pass/fail per acceptance
   criterion"; the suite refines that to pass / fail / **`Awaiting human`** per case, each with
   evidence: a command run, a log line, a traced code path. The third verdict reuses the state
   the skill's evidence menu already defines for exactly this (`patterns.md:68`: "report that as
   `Awaiting human`") instead of inventing a new word, so the two-stage review's
   never-accept-a-missing-verdict rule (`SKILL.md:187`) stays satisfied. The third verdict must
   be legal: without it, a verifier that cannot execute the flow will guess, and the blind suite
   becomes a generator of confident fiction.
2. **The diff reviewer**, as a coverage lens: for each case, does the change plausibly implement
   it, and where. This is reading, not measurement. It is still an independent lens, because the
   case list was fixed before the code existed.
3. **The compile step** (the executable extension, next section): every machine-verifiable case
   becomes a runnable test once the implementation freezes.

### What the implementer sees

The approved criteria, never the suite. Guidance comes from criteria text; verification comes
from cases the implementer has not read. A target you can read is a target you can overfit. The
nearest shipped practice splits roles the same way — "have one Claude write tests, then another
write code to pass them" (P1) — though there the second Claude codes against tests it can read,
which buys guidance and spends verification value. This design keeps the suite as verification
currency.

## The executable extension (compile after freeze)

When the target runs in this session, cases are compiled into executable tests. Which cases is
not a judgment call: every case tagged machine-verifiable compiles — the tag was authored
blind, so selection cannot be steered by what the as-built code would fail. A tagged case the
toolchain cannot express downgrades to agent-observable on the verifier's checklist, and the
downgrade is recorded, never silently dropped. One unit does the compiling, after the
implementation freezes. Its inputs: the case suite, the public interface as built, and the
toolchain. Not the diff. Two more lines belong in its brief, both instructions rather than
constraints (the skill's own distinction for plain dispatches): it opens implementation files
only to extract signatures, and it never executes tests against the candidate — its one run
target is the baseline red-check below. A compile unit that iterates a test until it passes at
head reproduces E1's masking through the back door; running against the candidate belongs to
the verification stage alone. The expectations were pinned blind by the cases; the
compile step supplies only the plumbing.

Then two mechanical steps, both from round one and both kept:

- **Red-check** against the recorded baseline (the snapshot protocol already keeps it): every
  compiled test must fail there. "Red" is test jargon for a failing state. A test that already
  passes is vacuous or checks something that pre-existed; either way it is flagged. The weakness
  this catches is measured: strengthening HumanEval's tests dropped the measured pass rates of
  26 models by up to 19.3–28.9% (E3). Weak suites pass wrong code systematically.
- **Run at verification**: the suite executes inside the existing verification stage, alongside
  the build and the repo's own tests. Every failure enters the finding schema and gets triaged.

Where this sits against E1. E1's two arms are tests written after seeing faulty code (14%) and
tests written with no implementation in sight (25%). Compiled tests sit close to the independent
arm on the part that matters — what to expect — because the expectations were fixed before the
implementation existed. The plumbing does see the as-built names and shapes, and on most stacks
it extracts them from implementation source files; that is why the signature-extraction-only
and no-candidate-execution rules above exist, and they are brief text, not enforcement. The
masking mechanism E1 describes needs the logic, and the logic stays unseen only while those
rules hold. That is reasoning, not the measured condition, and the report should say so when
this form runs.

**Why parallel authoring of executable tests is no longer offered.** Round one's full form put a
code-writing QA unit in a worktree, in parallel with the implementer, against an interface
contract frozen at plan time. It bought wall-clock overlap and the exact measured arm of E1. It
paid: a second code writer (the 40–150k band), worktree isolation, a frozen-interface ceremony,
and a drift round every time the interface moved. The clarified design gets most of the
independence for a fraction of that: cases pin the expectations blind and in parallel;
compilation waits for a stable interface. It also removes the concurrent code-writing that
P5 most directly condemns; the parallel case author remains an argued exception to Cognition's
"sequential" clause, as stated in the artifact section. If a run at unusual scale truly needs the overlap, the
parent can propose it in the plan as an explicit deviation; the round-one containment still
applies to that case: interface contract frozen by the parent, QA unit in `isolation: worktree`,
drift routed through the parent as a contract change, fix leases excluding test paths.

## Round one's five problems, re-scoped

Round one found five problems with the test-code reading. The clarification dissolves two of
them for the case suite itself; they return only in the parallel-executable variant, which is no
longer offered. The other three survive and bind the case suite too.

### 1. Blind + parallel breaks on the interface — *now moot for the case suite*

Black-box test code must call something: a function, a CLI, an endpoint. A unit that is parallel
and truly blind must guess that surface, and a wrong guess means someone later "adapts" the
suite while reading the implementation — the bias walks back in through the adapter. The skill
names the failure class: "an agent that wasn't told a decision will make its own, and two units
deciding differently is how coupled work fails" (`SKILL.md`, Step 4). A written case calls
nothing, so nothing here binds it. The problem now lives only where test *code* is authored
before the interface exists, which is the variant this design dropped. The compile step runs
after freeze, when the interface is a fact.

### 2. A failing case is a claim, not a verdict — *stands, and bites harder*

Real requirements are short. A unit deriving a suite from three sentences will fill the gaps:
edge cases, error messages, tolerances, ordering. Every filled gap becomes an expectation the
user never stated — and prose cases are even cheaper to invent than asserts, because nothing has
to compile. The scale of the problem is measured: when OpenAI's annotators screened SWE-bench,
61.1% of all annotated samples were flagged for unit tests that may "unfairly mark valid
solutions as incorrect" (E6). Those were human-written repository tests.

Fix, two parts, unchanged from round one. First, **the user co-signs the expectations**: the
acceptance criteria the suite will trace to go into the orchestration plan, which the user
already approves at the Step 3 gate. Invented expectations die at the gate, before they cost
anything. Second, **failures enter the existing finding schema** (`contracts.md`, Finding
schema) and get triaged like any reviewer claim: accepted (implementation defect) / rejected
with evidence (case overreach) / user decision (real spec ambiguity). A failing case never
blocks by itself.

### 3. A frontier review of the suite overpays — *stands*

The proposal wants the suite verified by another subagent, symmetric with implementation review.
Symmetry is the wrong instinct. There is no oracle to review a suite against: the reviewer would
re-read the same requirement text the author read, and a second frontier reading mostly re-buys
problem 2. Two cheap checks give more. The **traceability scan** is the parent's: every case
cites a criterion ID from the approved plan; a case with no citation is an invented expectation;
minutes, no agent. The **red-check** covers the executable subset mechanically, as above. This
is also how the one production system in the evidence set does it: Meta's TestGen-LLM keeps only
generated tests that "clear a set of filters" — build, pass reliably, improve coverage — and
humans accept or reject what survives (E5). Mechanical filters first, human judgment second, no
model-review round in between. On high-risk work, one standard-tier reviewer with a single lens
(traceability and expectation strength) stays defensible, at the low end of the 30–80k review
band (`contracts.md:33`).

### 4. "QA team" and a new standing stage invite over-spawning — *stands*

The skill's stated classic failure mode is over-spawning (Step 1), and its cost line for
multi-agent work is ~15× chat (`SKILL.md:10`). Fix, unchanged: **one QA unit, singular, and no
new stage.** The suite's consumers are stages that already exist — the verifier runs the
checklist, the reviewer applies the coverage lens, the compiled subset joins the deterministic
checks. The whole addition to the skill is one pattern plus one gate question.

### 5. Two writers in one tree — *now moot for the case suite*

The skill forbids two writers in one tree, and its collision list names "shared tests"
explicitly (`SKILL.md`, Step 2). A case-suite author writes one file in scratch space and
touches no tree, so the rule is satisfied by construction. It binds again only if test *code* is
authored in parallel — the dropped variant. The held-out property round one wanted survives on
its own: the implementer sees criteria, never the suite.

## Offering the forms: existence gates and recommendations

The recommend-don't-enforce directive restructures round one's gate list. Round one used G1–G6
as pass/fail filters. Now only impossibility filters; everything else sets a recommendation the
user can override. The skill already has this exact convention for the Workflow backend: "put
both backends in front of them", "Say which way that cuts for *this* plan in the `Recommended:`
line rather than withholding the option" (`SKILL.md:94`), hardened by the repo's own commit
"always show workflow as an option if available" (`edd678c`). The same convention now covers
suite forms.

**Existence gates** — hide an option only when it cannot run:

- **X1 — checkable criteria (any form).** The parent can extract acceptance criteria from the
  request *without inventing behavior*, and each case can state an observable outcome and a
  check method. Quality over count: one strong criterion qualifies (a migration's "every record
  survives with equivalent semantics" is enough alone). If extraction would require invention,
  ask the user. If nothing checkable exists, the track is impossible; the plan says so in one
  line, and no form question is asked.
- **X2 — runnable target (executable option only).** The session has the toolchain to build and
  run tests. This is where the user's original gate — "only when the target is a code
  implementation" — lands: whether the target is running code decides whether tests can
  *execute*, not whether written cases may exist. A config change or a data pipeline with
  checkable outputs can still take the suite-only form.
- **X3 — something to verify (any form).** The plan carries at least one writer unit producing
  the deliverable the cases would check. With no implementation in the plan there is no
  candidate to run cases against, and under a `solo` answer no blind author can exist. The v2
  adversarial pass earned this gate: research and writing plans often satisfy X1, and without
  X3 every one of them would carry a form question whose answer is none — ceremony on exactly
  the runs the economics signal exists to spare.

**Recommendation signals** — set which option carries "(Recommended)"; never hide one:

- **R1 — existing coverage.** Repo tests already cover the criteria → recommend none; extend and
  run those instead. Independence the repo already provides is not worth paying for twice.
- **R2 — economics.** The diff fits one sentence → recommend none. (The no-writer case is X3
  now, an existence matter.) Gate precedent from shipped practice: "If you could describe the diff in one
  sentence, skip the plan" (P3); Spec Kit skips its whole spec flow for "direct edits to
  existing code", "rapid prototyping", and "simple bug fixes" (P4).
- **R3 — scale and risk.** A hard trigger from the risk rubric (the list at
  `references/contracts.md:99`; read it there rather than from a paraphrase here) recommends the
  suite; a runnable, high-risk target recommends suite + executable. One trigger points the
  other way: "behavior with no reliable test oracle" recommends none, with verification routed
  to human checkpoints and the domain's other evidence.
- **R4 — determinism.** Criteria that would flake as asserts (timing, load) recommend a written
  case with a manual check over an executable test.

When signals conflict, the precedence is fixed: R3's hard triggers outrank R1 and R2 — the risk
rubric already says a trigger means high risk "regardless of other axes" — R1 outranks R2, and
R4 never decides presence, only which form to prefer. A conflict this ordering does not settle
goes into the recommendation's one-line reason, and the user decides. Under the
recommend-don't-enforce directive that is not a failure mode; it is the mechanism.

Round one's "Never" list (subjective or visual acceptance; research and writing deliverables;
one-shots; emergencies) converts to default-none recommendations under this directive. One piece
stays structural rather than advisory: a case whose only check is human judgment routes to the
human checkpoint the evidence menu already defines, and a suite composed entirely of such cases
produces no agent-verifiable evidence — the recommendation text must say that plainly.

**Presentation at the gate.** The Step 3 plan gate gains a second question in the same
`AskUserQuestion` call — the tool takes up to four questions per call, so this adds one
decision, not a second gate ceremony, and X3 keeps it off runs with nothing to verify.
Question: "Acceptance suite?" Options: `none` / `suite only` / `suite + executable`, with the
recommended option first and tagged "(Recommended)", which is the tool's own convention. X1 or
X3 false → the question is not asked. X2 false → the third option is absent. That is the entire
enforcement surface; everything else is the recommendation tag plus a reason. Where that
content renders is part of the design: previews are per-option on single-select questions, so
the recommended option's preview carries the deciding signal and the criteria list, and each
form's preview carries its cost row from the table below; descriptions stay to one short
sentence. The plan table already occupies the `go` option's preview on the first question
(`SKILL.md:100`); the suite question's previews are its own surface. One interaction rule: a
`solo` answer on the main question voids this one, because with no subagents there is no blind
author.

Two counterexamples from round one's adversarial pass stay on record, reframed from gate
failures to recommendation calibration:

- "Add rate limiting to endpoint X: HTTP 429 after 100 requests per minute, `Retry-After` set,
  per-IP bucket." Runnable, three extractable criteria, no existing coverage. All options appear.
  The recommendation turns on one classification call the reason line must surface: read as
  ordinary HTTP behavior, R2 recommends none — a one-file change on a plan too small to carry
  the track; read as the rubric's "networking" hard trigger, R3 outranks R2 and recommends the
  suite-only form. R4 cannot argue for none either way; it only shapes which form to prefer if
  one runs (a manual-check case over a flaky assert). v2's first draft cited R4 for a none
  recommendation, which misreads its own signal; the v2 adversarial pass caught it.
- A data migration with a single criterion — every record survives with equivalent semantics.
  Round one's first draft demanded ~3 criteria and locked the track's door on exactly the kind
  of task the risk rubric's "independent test designer" line was written for. X1's
  quality-over-count clause admits it; R3's hard trigger (data migration) recommends the suite.

## Cost accounting, honestly

| Option | Adds | Estimated tokens | Basis |
| --- | --- | --- | --- |
| Suite only | 1 blind case author (standard tier, plain dispatch) + parent traceability scan + per-case checklist inside the existing verifier stage | +15–35k per run — **a guess, not a band** | no calibration row for this unit class; the nearest shape (anchored single-corpus web briefs) ran 13.7–33.7k across the two runs `calibration.md` records, and its latest note says to plan them at 15–35k — the guess adopts that band rather than undercutting it (v2's first draft guessed 10–25k, below its own basis; the adversarial pass caught it) |
| Suite + executable | additionally: 1 compile unit after freeze + red-check + suite run in the existing verification stage | +30–60k more — **a guess, not a band** | `calibration.md`: "Still uncovered: implementation units that write real code" |
| Parallel executable authoring *(not offered)* | worktree code writer + frozen interface contract + drift rounds | 40–150k writer plus 30–80k optional review (`contracts.md:33`) — **unproven** | listed to show what dropping it saves: isolation and drift, paid for wall-clock overlap only |

Break-even logic, corrected by the v2 adversarial pass: a suite-caught defect does not *save* a
fix round — fixing it still costs one. What it saves is the cost of the same defect found after
merge: the later diagnosis, the second change cycle, the blast radius. No band in this repo
prices that, so break-even is a judgment about two things — how likely the suite is to catch a
defect the reviewers miss, and what that defect would cost post-merge — not an arithmetic
identity. At a +15–35k entry price on a run that already carries a writer and a review stage
(X3 admits it, R2 does not veto it), one escaped defect every few runs plausibly pays for the
track. The executable extension earns its extra +30–60k on runnable, riskier work (R3). Every
number here is a guess or an unproven band and is labeled as such; the first real runs must
append rows to `calibration.md`.

A side benefit for the skill's own bookkeeping: the Step 7 coordination check currently answers
mostly from review disagreements. A suite-caught defect that both reviewers missed is the
cleanest positive answer that check can have.

## What this changes in the skill (proposed edit set — not applied)

Kept deliberately small; the skill's leanness discipline treats added words as a correctness
cost.

1. `references/patterns.md`: one new pattern, "**Blind acceptance suite**" (draft below, ~210
   words; a future round trims it toward the file's house style). Plus one line in the software
   evidence menu: "for gated implementation work: a requirement-level acceptance suite authored
   blind to the plan and the code; compiled subset red-checked against the baseline and run at
   verification."
2. `references/contracts.md`: replace the bare "independent test designer" phrase at line 103
   with a pointer to the new pattern. Plan template gains one optional line: `Acceptance suite:
   none | suite | suite+executable (recommended: <X> — <one-line reason>) — criteria R1..Rn`.
   Brief shapes: the implementer brief carries criterion IDs; the verifier brief carries the
   suite path and the pass / fail / `Awaiting human` rule.
3. **Result before report** (user directive): `references/contracts.md:132` and `SKILL.md`
   Step 7. The template already opens with `OUTCOME: <what the user asked for, answered first>`,
   but that is one line inside the report block, and in practice it compresses the deliverable
   to a pointer. The edit makes the order structural: the final message has two parts, fixed
   order — first **Result**, the deliverable's own summary in prose, standing on its own;
   then the Orchestration Report block. The report block never opens the message. The block's
   `OUTCOME` line may then point up at the Result section instead of restating it.
4. **Gate options must render fully** (user directive): `SKILL.md:100` (the gate bullet) and
   `references/claude-code.md:136` (the gate-surface note). The skill cannot restyle the client:
   `AskUserQuestion` renders option descriptions in a compact list, and long ones truncate. What
   the skill can enforce is where decision content lives. Added rules: option labels 1–5 words
   (the tool's own guidance) and descriptions one short sentence (this proposal's rule, not the
   tool's); anything the user needs *in order to decide* never lives only in a description — it
   goes in the option's `preview` (single-select questions only) or in text printed immediately
   above the question; a *new* orthogonal decision, like the suite form, gets its own question
   in the same call (the tool takes up to four) rather than new `go` variants — the existing
   backend pair (`go — via Workflow` / `go — hand-batched`) is explicitly exempt, because
   `SKILL.md:110` mandates that fused shape for deciding how the same approved rows run, and
   this rule must not condemn the block it sits above; `multiSelect` questions get no preview,
   so their detail must precede the question.
5. `SKILL.md` Step 3: the second gate question from the Presentation paragraph above, three
   lines. `SKILL.md` Step 4: one exception line — a blind-authoring brief receives the
   decisions' observable consequences, never the decisions, overriding "name the decisions
   already made" (`SKILL.md:150`) for that dispatch class. `SKILL.md` Step 6: two clauses — the
   deterministic-checks sentence absorbs the suite run, and the per-case verdict set is pass /
   fail / `Awaiting human`, naming the evidence menu's existing third state so the two-stage
   review's never-accept-a-missing-verdict rule (`SKILL.md:187`) stays satisfied.
6. **No new saved agent file, no change to defaults, rails, or the stop rule.**
   `references/claude-code.md` sets the bar: a role earns a file only after recurring across
   several real tasks. The case author is a plain-dispatch standard-tier writer until then; its
   brief names the model explicitly, its Effort cell reads `— (no control)` because a plain
   dispatch has no effort lever, and its tool limits are instructions rather than constraints
   (`references/claude-code.md:72` and `:76`). Under the Workflow backend the same row gains a
   real `effort`. The `verifier` file is the wrong home for the authoring job — not for
   capability reasons (its one permitted write, shell redirection to a brief-named path, could
   produce the suite file; `references/claude-code.md:18`) but because frontier price is the
   wrong tier for standard-tier authoring, and the unit that later judges the cases must not be
   the unit that wrote them.

### Draft pattern text (for a future round to trim and place)

> ## 10. Blind acceptance suite
> **Artifact:** a requirement-level case suite — numbered cases, each with steps, an expected
> observable outcome, a check method tagged machine-verifiable / agent-observable / human-only,
> and the criterion ID it traces to. Authored blind, from
> the requirement text and the user-approved criteria only — never from the plan's design or any
> code — by one small standard-tier unit that writes a single file in scratch space.
> Parallel-safe by construction; ambiguity returns as a question, never a case.
> **Offer:** whenever the plan carries a writer unit and checkable criteria exist without
> inventing behavior (one strong criterion qualifies), ask at the plan gate: none / suite only / suite + executable; the executable
> option appears only when the target runs in-session. Everything else — existing coverage,
> one-sentence diffs, scale, risk triggers — only sets which option carries "(Recommended)".
> **Consumers:** the verifier runs the suite as a checklist and reports pass / fail /
> `Awaiting human` per case, with evidence; the diff reviewer checks the change against the cases;
> after freeze, an optional compile unit turns every machine-verifiable case into an executable
> test from the as-built interface, without reading the diff or running against the candidate —
> red-check them against the baseline (all must
> fail there; a test that passes is vacuous or pre-satisfied, flag it), then run them in the
> existing verification stage.
> **Rules:** every case cites its criterion; the implementer sees criteria, never the suite; fix
> leases exclude test paths; a failing case is a finding, not a verdict — triage decides
> (implementation defect / case overreach / user decision); a case only a human can judge routes
> to the human checkpoint.

## Residual risks after the corrections

- **Judged verdicts on written cases.** A verifier can rule "pass" on a vague observation. The
  check-method line, the `Awaiting human` outcome, and human-checkpoint routing reduce this;
  they do not remove it. The report must distinguish measured passes (executable) from judged passes
  (read and ruled).
- **Wrong expectations that survive the traceability scan and the red-check**: caught only by
  triage; budget one disagreement per run for it.
- **Goodhart at fix time.** During fix rounds the implementer necessarily learns what failed and
  can special-case it. "Goodhart" here: optimizing the measure instead of the goal. Partial
  mitigation: hand the implementer the failed criterion and the observed behavior, not the case
  text or test source. Brief-level rule only; residual risk goes in the report.
- **Flaky or environment-dependent compiled tests**: the compile brief must forbid network and
  timing assumptions unless the target needs them; the red-check catches some of this by
  construction; R4 steers flake-prone criteria to written cases.
- **Recommendation erosion.** With every option always on the table, the risk moves from "gates
  applied loosely" to "recommendations rubber-stamped". The defenses are the cost line each
  option must carry at the gate, and the calibration log: every run appends actuals, and a row
  of negative coordination verdicts is the signal to tighten the recommendation rules.
- **Interface drift** now exists only in the not-offered parallel variant; if a plan deviation
  revives that variant, drift routes through the parent as a contract change, per round one.

## External evidence

Gathered 2026-08-06 by two `web-researcher` units (W1 literature, W2 shipped practice) in one
Workflow wave; verbatim reports live in the session scratchpad (`evidence-w1.md`,
`evidence-w2.md`). Grading follows the repo convention: a claim from a fetched page outranks one
from a search snippet, and no snippet-only claim is load-bearing in this document.

**Scope note (v2).** E1, E3, E4 and E5 measure *executable* tests; E6 measures human-written
repository tests. No study in this set measures a written, requirement-level case suite. The
case suite inherits the mechanism these studies support — expectations fixed independently of
the code — not their figures. Claims in this document that rest on the figures are scoped to the
executable subset.

### Literature (W1)

| ID | Claim | Figure / quote | Source (all fetched 2026-08-06) |
| --- | --- | --- | --- |
| E1 | Tests written after seeing faulty code detect far fewer faults than tests written independently | "generating tests after faulty code significantly reduces fault detection effectiveness compared to generating tests independently (14% vs. 25%)" | arxiv.org/abs/2607.05139 |
| E2 | Test-first improves LLM coding success (direction only; exact deltas not retrieved) | tests derived from the problem statement "leads to higher success in solving programming challenges" | arxiv.org/abs/2402.13521 |
| E3 | Weak suites systematically pass wrong code | 80× stronger tests dropped pass@k of 26 models by "up-to 19.3–28.9%" | arxiv.org/abs/2305.01210 (EvalPlus) |
| E4 | Independently generated tests work as a selection oracle at scale | CodeT "dual execution agreement": 65.8% pass@1 on HumanEval, +18.8 points absolute over its base model | arxiv.org/abs/2207.10397 |
| E5 | A production system verifies generated tests with mechanical filters, then human accept/reject | "75% of TestGen-LLM's test cases built correctly", "57% passed reliably", "25% increased coverage", "73% of its recommendations were accepted" | arxiv.org/abs/2402.09171 (Meta TestGen-LLM) |
| E6 | Task tests themselves needed screening; test overreach was the most-flagged defect | 68.3% of samples filtered out overall; 61.1% of all annotated samples flagged for tests that may "unfairly mark valid solutions as incorrect" (38.3% for underspecified statements); screening roughly doubled GPT-4o's score (16% → 33.2%) | openai.com/index/introducing-swe-bench-verified/ |

W1 caveats, kept as given: the TestGen-LLM percentages are abstract-level and their denominators
unconfirmed, so this document derives no new numbers from them; E2's quantitative deltas were not
retrievable; two CodeT follow-up papers were snippet-only and are not cited.

Two upgrades from the v2 round. E3 was independently re-fetched by the v2 refuter and confirmed
verbatim. E6's denominator, disputed between the two adversarial rounds, was settled by the
parent re-fetching the source: "We annotated 1,699 random samples... 38.3% of samples were
flagged for underspecified problem statements, and 61.1% were flagged for unit tests that may
unfairly mark valid solutions as incorrect" — both rates are over all annotated samples, as the
table states.

### Shipped practice (W2)

| ID | Claim | Quote | Source (all fetched 2026-08-06) |
| --- | --- | --- | --- |
| P1 | No shipped product documents blind-parallel test authorship; the nearest practice is a two-session split | "have one Claude write tests, then another write code to pass them" | code.claude.com/docs/en/best-practices |
| P2 | Fresh-context review is official guidance | a reviewer in a fresh subagent context "sees only the diff and the criteria you give it, not the reasoning that produced the change" | code.claude.com/docs/en/best-practices |
| P3 | Gate precedent: skip heavy process for small, clear changes | "If you could describe the diff in one sentence, skip the plan." | code.claude.com/docs/en/best-practices |
| P4 | Spec-driven tools derive acceptance criteria from a spec, but the implementing agent writes the tests, not a blind author | tests are generated at implement time "based on the specification and task breakdown"; the flow is skipped for "direct edits to existing code", "rapid prototyping", "simple bug fixes" | github.com/github/spec-kit |
| P5 | Cognition's bar for safe parallelism excludes code-writing units | "Actions carry implicit decisions, and conflicting decisions carry bad results" | cognition.com/blog/dont-build-multi-agents |
| P6 | Kiro gates its spec process against direct "vibe" edits; its flow includes property-based tests | "developing with specs keeps the fun of vibe coding, but fixes some of its limitations" | kiro.dev |

W2 caveats, kept as given: no fetched source states an implementer-must-not-edit-tests rule, so
that rule in this design goes beyond documented practice; the official sub-agents page fetch
truncated, so example-role wordings are snippet-only and unused; Kiro's deeper spec-format
details were unconfirmed and are unused; Devin/OpenHands/SWE-agent verification mechanics went
uncovered (secondary question, thin sources within the anchor list).

## Internal evidence

- `subagents-claude/SKILL.md:10` — "independent evidence — tests, reproductions, measurements",
  and the ~15× multi-agent cost line. (The first draft cited line 3, which is frontmatter; the
  adversarial pass grepped and corrected it.)
- `subagents-claude/references/contracts.md:103` — the "independent test designer" stub this
  proposal operationalizes.
- `subagents-claude/SKILL.md` Step 6 — deterministic checks before model review; reviewer-eagerness
  warning; clean-context reviewer principle.
- `subagents-claude/SKILL.md` Step 2 — one writer per tree; "shared tests" named on the collision
  list.
- `subagents-claude/SKILL.md:94` and repo commit `edd678c` ("always show workflow as an option if
  available") — the skill's own always-offer-and-recommend convention, which the gate rework in
  this document extends to suite forms.
- `subagents-claude/references/claude-code.md:136` — the gate-surface note: previews render on
  single-select questions only; the plan table belongs inside the decision surface.
- `subagents-claude/references/contracts.md:132` — the Orchestration Report template whose
  `OUTCOME` line the result-before-report edit makes structural.
- `subagents-claude/references/patterns.md:27` — bake-off's "criteria written before results
  return" (pre-commitment precedent).
- `subagents-claude/references/patterns.md:66-68` — software evidence menu; criteria classified
  machine-verifiable vs subjective vs human-only. In v2 this classification is load-bearing: it
  is the type system behind each case's check line.
- `AskUserQuestion` tool schema (this harness, 2026-08-06) — up to four questions per call; 2–4
  options each; labels "concise (1-5 words)"; recommended option listed first and tagged
  "(Recommended)"; previews single-select only. The truncation of long option descriptions is
  user-reported client behavior; the proposed rules are safe whether or not a given client
  truncates.
- `research-2026-08-agent-orchestration.md` — MAST: incomplete verification 8.2% of failures;
  specification the largest failure category; Cognition's coupling argument; Claude Code best
  practices: "A fresh context improves code review since Claude won't be biased toward code it
  just wrote" (all fetched 2026-08-06).
- `~/.claude/skills/subagents/calibration.md` — the "review + optimise this skill" seed row: an
  adversarial refuter refuted 4 claims, three of them defects introduced during that run's own
  fix round; the 2026-08-05 prose-review row: a refuter killed 6 of 51 draft claims. (Rows are
  named rather than numbered: the file is append-only, and inserts shift the numbers — v2's
  first draft cited "row 8" for a row that this run's own append had moved to ninth place.)
  From the file's "How to read this" section: "Still uncovered: implementation
  units that write real code", which is why every authoring and compile cost in this document is
  labeled a guess or unproven.

## This run

Produced by the /subagents process it reviews. Plan gated and approved: 3 agents, ~190k subagent
tokens estimated, Workflow backend at the user's choice, run as two scripts as disclosed at the
gate. Two anchored web researchers in one wave (16.4k and 27.0k tokens; the anchored-brief
discount from calibration's "review + optimise this skill" seed row, confirmed again), parent-authored draft, then one opus refuter
on the frozen draft (61.7k, inside the 50–95k verifier band, its third hit). Actual subagent
total: 105k against the ~190k estimate, roughly 30 minutes end to end.

The refuter returned 13 findings. All 13 were accepted; their fixes carry into v2 wherever the
sections survived. The two most instructive: the first draft's default form named an agent that
cannot write files (the `verifier` denies edit tools), and the draft's E6 usage resolved an
ambiguous denominator toward its own argument — the laundering failure mode this repo's
calibration log records twice before. Five attack angles returned "attacked, holds".

**Round two, same day.** The user clarified the artifact (a requirement-level case suite, not
test code) and gave three directives: recommend rather than enforce, option content must survive
the client UI, result before run report. The parent produced v2 inline: zero new subagents. The
clarification dissolved round one's problems 1 and 5 for the default path more cleanly than
round one's own fixes did; the frozen-interface contract and the worktree QA unit now exist
only as a documented deviation path.

**Round three: the v2 refutation, user-approved.** One opus `verifier` attacked the frozen v2
on six angles: 68.2k tokens against a 40–60k estimate, about 7.7 minutes, 19 tool uses. It
returned 14 findings: 13 accepted and fixed in place above, 1 rejected with evidence. The
rejected one is instructive. The v2 refuter argued E6's 61.1% should read as a share of the
filtered subset — directly against the v1 refuter's opposite correction. Two refuters
disagreeing was settled the way the skill says to settle it, with a command rather than a
preference: the parent re-fetched the source, which states both rates over all 1,699 annotated
samples, so the document stood. The most instructive accepted findings: the v2 rewrite had
*reintroduced* a defect the v1 round fixed (Cognition's parallelism bar quoted with its
"sequential" clause dropped — a full rewrite resets fix-round regressions, not just the review
clock); the suite-only cost guess sat below the floor of its own cited basis; the
"names an executable check" compile rule was undecidable against the document's own C3 example;
and the criteria hand-off was an unnamed hole in the blindness firewall. Three angles held:
every file:line pointer and quote, the calibration figures, and the external figures.

Known limits. E4 and E5 match the researcher reports but were not re-fetched from the primary
papers (E1 and E6 were re-fetched in round one's pass; round three added the refuter's E3 fetch
and the parent's E6 re-fetch). E2's exact deltas were never retrieved. Devin/OpenHands/SWE-agent
verification mechanics went uncovered. The 13 fixes from round three are themselves unreviewed —
the same regression class the calibration log warns about; each fix is a narrowing or a
correction against refuter-supplied evidence, which bounds that risk but does not remove it.
The stop rule does not call for a fourth round: the design's structure — the forms, the
consumers, the existence/recommendation split — survived round three unchanged, and the fixes
are corrections inside it.
