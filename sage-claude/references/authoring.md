# Authoring the corpus

Your job here: before writing or rewriting a piece of guidance, name the **baseline failure** it is meant to prevent, then take the form this file assigns to that failure. Read at the moment of authoring, whichever path is doing it — a `/sage-promote` stage that writes skill text, or a run editing this corpus on the user's word. `topologies.md` #12 owns that trigger set and this file follows it. Not read at Step 2 of an ordinary run, which writes no guidance and would only be paying to read it.

**This file claims no calibration band, and the omission is the point.** A band in this corpus counts *this* system's confirmations, and `memory.md`'s knowledge-item section is the one place those thresholds are written down — read them there rather than from here. Every row below is imported from another system's measurements and has no confirmation here — and the four rows do not share one evidence class, so a single tag over the file would be false in both directions at once. The compression floor asks for a strength band **per rule** rather than per file (`memory.md`, The compression floor). Each row states its own provenance instead. The entry point for raising any of them to a real band is an `obs` line in the journal, which `/sage-promote`'s consolidation turns into a knowledge item.

## Match the form to the failure

| Baseline failure | Right form | Wrong form |
| --- | --- | --- |
| Skips or violates a rule under pressure — knows better, does it anyway | Prohibition + rationalisation table + red flags | Soft guidance ("prefer…", "consider…") |
| Complies, but the output has the wrong shape — bloated prompt, buried verdict, restated spec | Positive recipe or contract: state what the output **is**, its parts, in order | Prohibition list ("don't restate", "never narrate") |
| Omits a required element from something it already produces | Structural: a REQUIRED field or slot in the template it already fills in | Prose reminders near the template |
| Behaviour should depend on a condition | Conditional keyed to an **observable predicate** | Unconditional rule + exemption clauses |

**Where each right form already stands in this corpus**, because a form named without an instance is the very failure the anchoring checklist below tests for. Row 2: the thirteen-field Task brief in `dispatch.md`, which states what a brief **is**, its parts, in order. Row 3: that same template's `Must not do:` and `Allowed tools:` lines — slots the author fills, not prose beside them. Row 4: the failure ladder in `../SKILL.md` Step 4, which keys the next rung to an observable predicate, the failure's **signature**, rather than to an attempt count with exemptions. **Row 1 has no instance here, and that is the honest answer** — this corpus carries no rationalisation table at all. Whether it needs one is an open question, not a gap this file is asserting.

**The evidence is uneven, and importing four rows at one strength would be the same error the table warns about.** Row 2, and both corollaries below, come from a head-to-head wording campaign on another system, repeated several times per phrasing on a dispatch-composition task. The prohibition arm produced clearly more of the unwanted content than the positive-recipe arm, and trended worse than a no-guidance control. **Take the direction; read the size against the control as a trend rather than a result** — that hedge is the source's own, and dropping it is how this row would get quoted as settled. Row 3's nearest support is a single live-run anecdote, not a wording test. Row 1 has a **worked bulletproofing record** rather than a head-to-head test — one skill's guidance was watched failing, a sentence was added, and the next iteration complied and cited it — which is evidence of a different kind and a weaker one, because it has no arm to compare against. **Row 4 carries no measurement anywhere**: it is asserted in the source skill, and nothing there or here backs it. None of it has been reproduced against this corpus, and `topologies.md` #12 is the instrument that would do it.

**The narrower classifier under row 2 is the operative half, and it is what stops this table being read as "prohibitions are bad".** They are not, and reaching for a rewrite on that reading is the likeliest way to make this corpus worse. Prohibitions on a **single discrete directive** were measured *working*, in the same campaign and against its own control. Phrase-level tripwires on concrete tokens fire reliably. Recognition tables work because they are read at decision time rather than at composition time. It is **composition** prohibitions that backfire, and only where the model has its own agenda for the output, because restating a specification feels to it like helpful curation. Ties go to the shorter phrasing. So a negative here is a conversion candidate only once you can say which of the two kinds it is — and a mechanism directive such as "hand off via artifacts, never via transcript" is the first kind, which means converting it is a loss, not a repair.

## Two corollaries

- **Nuance clauses cost more than they buy.** "Don't X unless it matters" reopens the negotiation the recipe closed: appending a single nuance clause to a winning recipe degraded it from consistent to noisy in the same wording tests.
- **Exemption clauses do not scope.** "This limit doesn't apply to code blocks" still suppresses code blocks. Where part of the output must be exempt, restructure so the rule cannot reach that part, rather than carving an exception out of a rule that will keep reaching anyway.

## Anchoring — a line to hold, not a repair to make

Abstract guidance sitting beside concrete commands loses to the concrete commands. An abstract step reading "you know your own toolkit" passed a small minority of its runs, and the repaired version passed every one. **Three changes landed together** — naming the candidate tools outright, a bridge sentence granting the authorisation the tool's own guardrail wanted, and a red flag naming the anti-pattern — so the result belongs to the batch and the direction is what transfers, not a figure for tool-naming alone. This corpus mostly already does this — its briefs name exact paths and exact commands, and `../SKILL.md` Step 3 carries the measured discount that behaviour earns. So this is a checklist that stops a rewrite losing ground, never a defect to go fix.

Run it over any edit to this corpus:

- Does every abstract instruction sit next to the concrete names, paths or commands that satisfy it?
- Is each negative in the edit a discrete directive rather than a composition instruction? Only the second is a conversion candidate.
- Has a nuance clause been appended to something that already worked?
- Does an exemption clause try to scope a rule that will not scope?
- Does a required element live in a slot of the template, or only in prose near it?
