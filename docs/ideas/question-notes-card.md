# Question Notes — card

*One page, for the wall. Nothing here is evidence on its own: this card compresses, and compression drops the grading. Every claim below is tagged and sourced at its origin in `question-notes-anatomy.md` — read it there before trusting a number off this page.*

## The four rules

**R-1. The question is the durable artifact.** Every question you stop on goes into `OPEN.md` immediately, answered or not. Open questions are permanent, not scratch.

**R-2. The cue and the answer are separate surfaces.** The title is the question. The answer starts one line below. Never put the answer in the title.

**R-3. The body is a self-explanation, not a summary.** Write why it is so, and what would be different if it were not. If a diff against the source could produce it, delete it.

**R-4. A relation is written, never implied.** Every link carries one sentence saying why the two belong together.

## The note

```markdown
# <the question, written as a question>

**Answer.** <one sentence>

**Why.** <2-5 sentences: why it is so; what would be different if it were not>

**Settled by.** <file:line | citation + URL | the command that decides it>

**Links.** - [[other note]] — <why these two belong together>

**Status.** open | answered <date> | stale-since <date>
```

`open` is for a note you started and could not finish. A question you have not answered at all stays a line in `OPEN.md` and never becomes a file.

## No note when

The answer is re-derivable in under a minute by grep, the compiler, or `kubectl explain`. Tick the line and move on.

## The three instruments

**(a) Big complicated system → the map note.** One focus question at the top; relations as concept — relation — concept; cross-links between clusters. Build it when 7-12 answered questions cluster, never before.

**(b) New codebase → the question thread, the why-note (ADR: Context / Decision / Consequences), the architecture map.** Keep relations and reasons. Never durable fact notes: facts are re-derivable and the next commit falsifies them.

**(c) Brainstorming, connecting, applying → the argument map.** Conclusion, premises, co-premises, objections. Mark each premise checked / believed / assumed; every unchecked one becomes a question. Links alone will not give you an argument's shape.

## The recall rule

Read the title. Say the answer. Then look.

Only over notes that do not decay: concepts, mechanisms, reasons, invariants, decisions. **Never over codebase facts.**

Gap scales with how long you need it: days for this sprint, weeks for next year (Cepeda et al. 2008, Psychological Science 19:1095-1102 — the optimal gap falls from about 20-40% of a one-week delay to about 5-10% of a one-year delay) `[measured]`.

Path B's why-notes, ADRs and traces **do** belong in the pass. Only its *facts* are excluded.

## Where it lives

One place, separate from your project vaults: `~/Projects/notes/questions/` — `OPEN.md`, `questions/`, `maps/`, `decisions/`. Plain markdown, no plugin.

## The honest line

The parts are documented and separately graded. The combination is untested. Keep the corpus small on purpose.
