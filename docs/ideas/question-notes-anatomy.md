# Question Notes — the anatomy

The method I recommend is **Question Notes**: one discipline of four rules, one note format, three instruments you reach for by job — individually documented parts assembled into a combination that **has never been tested**. No study, no long-run practitioner account, nothing; the hybrid at its centre, atomic text notes plus a visual map with a rule about which carries what, is undocumented and I found no source describing it. The unit is a *question you had to stop and think about*, written down the moment it appears; a note exists only when that question gets an answer you had to construct rather than copy. The parts are evidence-backed; the assembly is my design.

## The scope claim, stated first because it is the whole pitch

**The evidence licenses the acts, not the archive.**

Measured: retrieval practice and distributed practice are both **high utility** in Dunlosky, Rawson, Marsh, Nathan & Willingham (2013), *Improving Students' Learning With Effective Learning Techniques*, Psychological Science in the Public Interest 14(1):4-58 ([psychologicalscience.org](https://www.psychologicalscience.org/publications/journals/pspi/learning-techniques.html)); self-explanation and elaborative interrogation **moderate**; summarization, rereading and highlighting **low**. `[measured]` Why highlighting rates low is a separate matter: every route to the paper's full text failed here, so I cannot give you its own reasons in its own words. The explanation usually offered — that highlighting isolates facts from the relations between them — is one I find persuasive and cannot attribute to this paper `[inference]`.

Not measured, anywhere, for any note system: that a growing corpus repays its cost over years. I found no re-read-rate data and no time-cost data for any personal knowledge system, and the only two long-run outcomes documented in my material are abandonments — Joan Westenberg, *I Deleted My Second Brain* (2025), ten thousand notes over seven years, deleted `[practice]`; and Robert Minto, *Rank and File* (Real Life, 2021), whose network was "useless" for constructing an argument after years, so he wrote his dissertation conventionally `[practice]`.

The claim is narrow and the narrowness is the pitch. For a textbook you can buy a question bank. For a codebase of eight hundred files, an undocumented production system, or your own half-formed idea, **there is no question bank and nobody will write you one**; writing the questions down is the only way to have retrieval prompts at all. The corpus is a by-product of doing the measured acts on material that has none, not an asset you accumulate. Keep it small on purpose.

That is a boundary, not an apology: inside it the method runs the two highest-rated techniques in the literature; outside it — "my notes will compound into a second brain" — there is nothing to stand on.

## How I mark evidence

Every sourced claim carries one tag, so you can tell measured evidence from practice from opinion.

- `[measured]` — a controlled study or meta-analysis, with source, year and journal.
- `[observed]` — a study that recorded behaviour without testing a remedy.
- `[practice]` — a documented practitioner account. Real experience, no controls.
- `[inference]` — my reasoning from a source; the source does not say it. Discard it if you disagree and nothing measured is lost.
- `[contested]` — the sources disagree and I will not resolve it for you.

Where I reached only an abstract or a secondary summary, I say so at the claim.

## The four rules

### R-1. The question is the durable artifact

Write down every question you had to stop and think about, in one running list, immediately, whether or not you can answer it. Open questions are first-class and permanent, not scratch to be tidied away.

*Why this part exists:* Sillito, Murphy & De Volder (2006), *Questions Programmers Ask During Software Evolution Tasks*, FSE 2006, observed working programmers on systems from 60 KLOC to over a million lines and recorded exactly the failure this fixes. Participants "often jumped around between various activities or explorations, at times leaving questions only partially answered, sometimes forgetting what they had learned", and one notices "we were retracing steps we had done before and weren't aware of it." `[observed]` The failure is observed in the field. **The question log as its remedy is my inference — no study has tested one.** `[inference]` I keep the two apart; it would be easy to launder the first into the second.

### R-2. The cue and the answer are separate surfaces

The note's title *is* the question, written as a question. The answer starts one line below it. Never put the answer in the title.

*Why this part exists:* it is the only mechanism I found that makes retrieval practice possible inside a note file. Search, backlinks and the Obsidian graph show you titles, so a question-title is a visible prompt with the answer hidden every time you pass it. An answer-title destroys that: you cannot see the cue without seeing the answer, and no retrieval is left to practise. This is the cue column of Cornell notes (Pauk), adopted as a mechanism only — **Cornell as a whole system has inconclusive evidence**, some gains and several nulls, with popularity plainly outrunning validation `[contested]`.

### R-3. The body is a self-explanation, not a summary

Write *why it is so* and *what would be different if it were not* — not what the source said.

*Why this part exists:* this is the rule where the format itself selects a rated technique over a rated-worse one. Self-explanation (Chi, Bassok, Lewis, Reimann & Glaser 1989, Cognitive Science 13:145-182; Chi, de Leeuw, Chiu & LaVancher 1994, Cognitive Science 18:439-477) and elaborative interrogation are both **moderate** in Dunlosky et al. 2013; summarization is **low** `[measured]`. (Whether highlighting actively *harms* higher-order learning, as opposed to simply not helping, is a reason I could not verify in the paper's own text — see the note at the top `[inference]`.) "Write it in your own words" becomes testable: if what you are writing could be checked by diffing it against the source, you are summarizing — the thing rated low. Write the *why* instead.

### R-4. A relation is written, never implied

Every link carries one sentence saying why those two notes belong together. A bare `[[link]]` is not a relation.

*Why this part exists:* Andy Matuschak's evergreen notes require a one-sentence articulation of *why* two notes connect `[practice]`. The deeper reason: relations are where the difficulty lives. In cognitive load theory (John Sweller, *Cognitive Load During Problem Solving: Effects on Learning*, Cognitive Science 12:257-285, 1988; the element-interactivity construct is developed in his later work rather than in that first paper), element interactivity — parts only meaningful when held together — drives intrinsic load, and your three jobs are all high-interactivity material. **Mark this one: no source I reached says anything about note *format* for high-interactivity material. The step from theory to format is mine.** `[inference]` Not inference is the failure it prevents: an unlinked pile is the collector's fallacy (Christian Tietze, 2014, [zettelkasten.de/posts/collectors-fallacy/](https://zettelkasten.de/posts/collectors-fallacy/), crediting Umberto Eco, *How to Write a Thesis*) — collecting is immediately rewarding, processing is not, so the pile grows and the understanding does not `[practice]`.

## The note file

Plain markdown; no plugin or tool beyond a directory and an editor.

```markdown
# <the question, written as a question>

**Answer.** <one sentence>

**Why.** <2-5 sentences: why it is so, and what would be different if it were not>

**Settled by.** <file:line | citation + URL | the command that decides it>

**Links.** - [[other note]] — <why these two belong together>

**Status.** open | answered <date> | stale-since <date>
```

The title carries R-2. **Answer** is one sentence so reuse costs a glance, not a re-read — a claim you can trust without opening the body is Matuschak's "titles like APIs" `[practice]`. **Why** carries R-3. **Settled by** makes the note falsifiable: it names what would tell you the note is now wrong. **Links** carries R-4. **Status** lets an open question sit for six months without pretending to be an answer. In practice you will rarely see `open` on a note *file*: an unanswered question normally stays as a line in `OPEN.md` and only becomes a file once it has an answer. Use `open` for the case where you started writing a note and could not finish it — a partial answer is worth keeping and worth marking as partial. The field has to exist at all because a format with no open state converts open questions back into scratch — the failure R-1 exists to stop.

On typed versus handwritten: **the evidence does not currently support telling you which to use.** The strong original claim (Mueller & Oppenheimer 2014) did not replicate: Morehead, Dunlosky & Rawson (2019), *How Much Mightier Is the Pen than the Keyboard for Note-Taking? A Replication and Extension*, Educational Psychology Review 31(3):753-780, found small, non-significant effects favouring longhand and no consistent group differences `[measured]`. The later meta-analytic picture is contested: two independent reads of the 2024 meta-analysis on typed versus handwritten lecture notes returned **opposite signs** — one no effect, one favouring handwriting — and neither reached the paper's text. Unsettled; I will not average or pick a side `[contested]`. Choose on decidable grounds: speed, searchability, whether you can link. This method needs links and search, which is why I write it for files.

## The three instruments

One stance, three instruments, because the three jobs differ in *kind* of material, not just topic.

### (a) A big complicated system → the map note

Built when roughly seven to twelve answered questions cluster, not before. One focus question at the top, then relations as concept — relation — concept, plus cross-links between clusters (construction rules from Joseph Novak & Alberto Cañas, *The Theory Underlying Concept Maps and How to Construct and Use Them*, Technical Report IHMC CmapTools 2006-01 Rev 01-2008, Florida IHMC, [cmap.ihmc.us](https://cmap.ihmc.us/Publications/ResearchPapers/TheoryUnderlyingConceptMaps.pdf)) `[practice]`. Plain markdown: indented relation lines or a fenced ` ```mermaid ` block, both rendering in Obsidian with no plugin.

*Why this part exists, honestly graded:* Nesbit & Adesope (2006), Review of Educational Research 76(3):413-448, pooled 67 effect sizes from 55 studies and 5,818 participants, associating concept-map use with increased knowledge retention, with effects small to large depending on how maps were used and what they were compared against `[measured]`. **No specific pooled effect size was retrievable, so I quote none.** Schmidt, Wollermann, Abele & Müller (2024), *Concept Maps to Assess System Understanding*, Behavioral Sciences (PMC11428796), n=24: map explanations carried more correct functional (relational) propositions than verbal ones, 12.1 against 9.3, at about 4.5x the time — but that measured maps as an *explanation and assessment* format, not a learning intervention, on everyday mechanical systems `[measured]`. And Karpicke & Blunt (2011), Science 331(6018):772-775, found retrieval practice beat elaborative study by concept mapping even on a concept-map outcome test — formally contested by Mintzes, Cañas et al. ([doi:10.1126/science.1203698](https://doi.org/10.1126/science.1203698)), who argued the mapping group was insufficiently trained to represent the technique fairly, with a rebuttal from the authors `[measured, contested]`.

From all three: **maps represent relations; retrieval is how you learn them.** Do not substitute one for the other.

### (b) A new codebase → the question thread, the why-note, and the map. Explicitly *not* durable fact notes.

Code facts are re-derivable on demand — grep, the language server, the compiler — and decay on the next commit, so a durable note recording one is worth close to nothing and goes wrong without telling you. Keep what the code does *not* contain:

- the **open-question thread** for the session, which kills the re-ask and retrace failure Sillito et al. observed;
- the **why**, in ADR shape — Context / Decision / Consequences (Michael Nygard, 2011, *Documenting Architecture Decisions*) — short, immutable, one file per decision, because large living architecture documents are, in Nygard's words, "never kept up to date" `[practice, primary]`. Rationale is not re-derivable from source at all;
- the **architecture map**, slow-changing, and the thing Sillito's participant N9 asked for outright: "I think I would need some kind of overview document that says... this is the architecture of how the thing works and the main classes involved" `[observed]`.

Two more exist for occasional use: a **state table** (Felienne Hermans, *The Programmer's Brain*) when a flow will not fit in your head, and an **effect sketch** (Michael Feathers, *Working Effectively with Legacy Code*) before editing `[practice]`.

*The ceiling,* stated as a limit and not smuggled in as support: Peter Naur, *Programming as Theory Building* (1985), argues the theory of a program cannot be written down — "program revival, that is reestablishing the theory of a program merely from the documentation, is strictly impossible" `[practice, primary]`; his Case 2 maintainers of a 200,000-line system "were unable to conceive of any kind of additional documentation that would be useful to them". Naur's unit is a *theory*, a coherent explanatory grasp, explicitly not a set of discrete question-answer facts, so he cannot be used to justify the atom and I do not use him that way. Notes **scaffold** theory-building; they never contain it. That is why path (b) keeps relations and reasons and throws away facts.

### (c) Brainstorming, connecting, applying → the argument map, on top of R-4

When the output is a position rather than a description, build an argument map: conclusion, premises and co-premises, objections, alternatives — inferential structure, not associative (Davies 2011, *Concept mapping, mind mapping and argument mapping: what are the differences and do they matter?*, Higher Education 62:279-301 — a taxonomy of the three formats, not a measurement of any of them).

*Why this part exists, and why R-4 alone will not do:* Minto is the counterexample. After years his note network could not supply an argument's *structure* — raw material, no shape `[practice]`. A link graph is what failed him, so more links are not the answer. Argument mapping is, and it is the best-measured member of the visual family: Claudia María Álvarez Ortiz, *Does Philosophy Improve Critical Thinking Skills?* (MA thesis, University of Melbourne, 2007), [full text](https://www.reasoninglab.com/wp-content/uploads/2017/05/Alvarez-Final_Version.pdf), reports 0.68 SD (95% CI [.51, .86]) for semester-long courses using some argument mapping, 0.78 SD (CI [.67, .89]) with heavy practice — figures and intervals confirmed against the paper itself `[measured]`. Tim van Gelder's *Using Argument Mapping to Improve Critical Thinking Skills* (2015), in the Palgrave Handbook of Critical Thinking in Higher Education, Palgrave Macmillan US, 183-192, [doi:10.1057/9781137378057_12](https://doi.org/10.1057/9781137378057_12), is widely cited for a weighted average near 0.85. The chapter is closed-access and I did not reach its text, so I neither confirm that figure nor rest anything on it: what follows stands on Alvarez-Ortiz alone. **What those figures measured matters more than their size:** critical-thinking test gains, over a taught semester course, with an instructor — not one person mapping one argument alone. The step from that result to this instrument is mine `[inference]`. And do not read "best-measured" as "largest": the numbers above are standard deviations on critical-thinking tests, Nesbit's are retention effects and Farrand's are recall percentages, and ranking them against each other would be comparing three different outcomes. Its weakness travels with it: several influential studies lacked a no-intervention or comparable active control, and argument mapping has rarely been compared head-to-head with other critical-thinking methods `[contested]`.

## The recall pass

Read the title, say the answer, *then* look. That is retrieval practice — one of the two high-utility techniques — running on prompts that would not otherwise exist.

Run it **only** over notes whose answers do not decay: concepts, mechanisms, reasons, invariants, decisions. **Never over codebase facts**, which the next commit can falsify — rehearsing a fact that changed silently teaches you the wrong thing.

On spacing: Cepeda, Pashler, Vul, Wixted & Rohrer (2006), Psychological Bulletin 132, pooled 839 assessments from 317 experiments across 184 articles `[measured]`. The gap depends on how long you want to remember, and the finding is a range, not a rule of thumb — Cepeda, Vul, Rohrer, Wixted & Pashler (2008), Psychological Science 19:1095-1102, verbatim: "the optimal gap declined from about 20 to 40% of a 1-week test delay to about 5 to 10% of a 1-year test delay" `[measured]`. Days if you need it next week, weeks if you need it next year. Anyone quoting you a single flat percentage is quoting a midpoint of that range as if it were a law.

## The rejected alternatives, under one standard

One standard for all of them: is there controlled evidence, and does it work on *your* three jobs?

**Mind mapping.** Farrand, Hussain & Hennessy (2002), Medical Education 36:426-431, n=50: +10% at one week — but the 95% CI is −1% to +22%, which crosses zero, so that headline result is **not statistically significant**; the adjusted figure of +15% (CI 3%–27%) does not cross zero. `[measured, snippet-level — no route reached this paper's text, and it is the weakest-verified citation in these documents]`. Rejected for the system jobs anyway, on Davies's grounds: radial and associational, "hard for others to read", prone to losing the big picture on complex topics — the exact material at issue. Fine for association.

**Cornell as a system.** Evidence explicitly inconclusive `[contested]`. The cue-column mechanism is adopted as R-2; the system is not.

**Sketchnoting.** No controlled study found. Unevidenced. Rejected.

**Building a Second Brain / PARA / progressive summarization.** No controlled research either way — *no evidence offered*, not evidence against `[practice]`. Progressive summarization is layered highlighting, rated low. Rejected.

**Pure Zettelkasten.** Silent on codebases, silent in its own terms on learning a large system, unanswered by Minto. Its atomicity and written-reason link are what R-4 adopts (Luhmann, *Communicating with Slip Boxes*; Matuschak). The rest is not for your jobs.

## Limitations

**The combination is untested.** Every part is graded above; the assembly has no study and no long-run account behind it, and that is its largest single weakness. Having no book behind it is not an advantage: an unbranded untested composite is the same object as a branded untested one.

**Both long-run outcomes documented in the material behind this method are abandonments.** (Two accounts are not a survey of the field — I did not find others, which is not the same as their not existing.) Westenberg deleted ten thousand notes; Minto's network could not build his argument. Nothing here immunises you. Keeping the corpus small, making the question the unit, and R-3's ban on restating are design responses, not evidence.

**It costs more than it returns where a question bank exists**, and on short-lived work. For a language feature or a certification, buy the exercises. For a one-afternoon bug, a throwaway script, or a codebase you will not open again, the overhead is immediate and the payoff deferred and unmeasured.

**Path (b) will not give you a theory of a program.** Naur's constraint is a category limit, not a documentation-quality problem: his second team, with complete documentation *and* personal advice from the first, still made changes that violated the design's own logic. Notes make you faster at rebuilding the theory yourself; time spent trying to write one down is time not spent reading code.

**Parts of this evidence base were reached only through abstracts, landing pages and secondary summaries — and this limitation runs in one direction, so read it accordingly.** Five sources here were not reached in full text by the routes I tried: Dunlosky's own paper (SAGE paywalled; the PDF returned metadata only), van Gelder 2015 (identified to title, venue, pages and DOI, but the chapter is closed-access and no mirror served it), Karpicke & Blunt's original Science paper (403 on both DOIs; only the authors' published rebuttal was reached, though an open-access copy may well exist), Morehead, Dunlosky & Rawson 2019 (Springer login wall; ERIC 404), and Farrand 2002 (publisher 403). Every one of them is identified to volume and page, so you can go and check what I could not.

What I will **not** claim is that those were the only routes. A later check found Naur's full text — carrying both of the quotes above verbatim — at a mirror I had not tried, which is why Naur is no longer on this list. **Treat every "could not reach" here as a fact about my searching, not about the source**, and expect the error to run pessimistic: this apparatus understates the evidence actually available rather than overstating it. I have not verified the full text of everything I cite; where that matters I say so at the claim.
