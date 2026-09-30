# Memory contract

The layout, the ownership rules, the lessons contract, the structural invariants and the compression floor of sage memory v4. `/sage-promote` reads this file before it triages. Whoever writes corpus text reads `## The compression floor` and `## The editing test`. A sage run reads `~/.claude/skills/sage/references/memory.md` instead and needs nothing here.

**Contents:** [The layout](#the-layout) · [Ownership](#ownership) · [lessons.md](#lessonsmd) · [From inbox line to lesson](#from-inbox-line-to-lesson) · [Structural invariants](#structural-invariants) · [The editing test](#the-editing-test) · [The compression floor](#the-compression-floor)

## The layout

`<mem>` is `~/.claude/skills/sage/memory/`. `<repo>` is the path in `<mem>/source-repo`.

| Path | Holds | Written by |
| --- | --- | --- |
| `<repo>/sage-claude/memory/lessons.md` | the curated lessons: the source of truth | `/sage-promote` only |
| `<mem>/lessons.md` | the installed copy of the repo file | `install.sh` (the template always wins) and the landing step of `/sage-promote` |
| `<mem>/runs.log` | run lines only, never drained | every run appends one line; `/sage-promote` appends its own |
| `<mem>/inbox.log` | observation lines, append-only; the lines after the last batch wait for triage | every run appends; nothing rewrites it |
| `<mem>/lineup.json` | the lineup snapshot: pinned agent models, alt models, price ratio, changelog cursor | `sage-lineup-check.sh --ack <token>` only |
| `<mem>/archive/inbox-lines-<from>.log` | one batch of drained inbox lines, from inbox line `<from>` | `sage-promote-prep.sh --drain` only |
| `<mem>/archive/v3/` | the whole v3 memory, moved once | `sage-memory-migrate.sh`, run by the installer |
| `<mem>/source-repo` | one line: the repo's absolute path | `install.sh` |

## Ownership

Two properties from the v3 design and the clone model survive into v4. Every writer above keeps them.

1. **A sage run only appends to memory.** It writes `runs.log` and `inbox.log` with `>>` and nothing else. v2 let runs hand-edit table files, and every recorded corruption came from that path. A plain appended line has no table to break. Every restructuring write belongs to `/sage-promote`, on the user's word.
2. **The repo copy is the source of truth for shared text.** `/sage-promote` writes `<repo>` first and lands the installed copy after. The installer overwrites a differing installed copy. So an interrupted pass leaves the repo ahead, never the installed copy, and a hand edit in the wrong place is lost on the next install.

`lessons.md` is the only shared memory file. Per-machine facts stay in `runs.log`, `inbox.log` and `archive/`. A count written into a shared file forks across machines: a machine that has seen less writes the number back down in a clean edit no merge catches.

## lessons.md

**Cap: about 1,500 words.** One bullet per lesson or band:

```
- **<id>** — <rule, one sentence>. When: <recogniser>. Falsifier: <text>. Runs: <run ids>.
```

- `<id>` is a stable slug. A run cites it in `changed-by: <id> <how>` on its run line. Never rename an id that a run line cites.
- **The rule** is one sentence in the imperative. A rule that needs a paragraph is not distilled yet. It stays out.
- **When** is the recogniser: the shape of task or evidence where the rule applies. A reader must match it without the rule's history.
- **Falsifier** is the observation that would remove the rule, stated concretely.
- **Runs** lists the run ids that confirmed it, oldest first.
- **A band** is a cost or duration range for a named class of work. It may carry figures and run ids, because a run prices from them.
- **No machine path, ever.** A path that exists on one machine does not resolve on another. `sage-lint.sh --corpus` checks this.
- No secret, token or credential. The same lint checks this.

A lesson that already stands at full strength in the sage corpus does not also go into `lessons.md`. One home per rule.

**Removal.** A lesson leaves `lessons.md` for two reasons only:

1. its falsifier fired, or a `contradiction` line on it survived triage;
2. the user said so, for example to meet the cap.

Disuse is not a reason. A lesson no run cited is evidence about the runs, not about the lesson.

## From inbox line to lesson

Inbox grammar:

```
<YYYY-MM-DD> obs <session> | <kind> <class> | <observation> | falsifier: <text>
```

`kind` is one of `lesson`, `gap`, `defect`, `contradiction`, `confirm`, `correction`. `class` is `portable` or `local`.

- **A lesson needs a falsifier.** A line with no falsifier that the triage can state never lands.
- **Only class `portable` lands in `lessons.md`.** A `local` fact holds on one machine only. Its evidence stays in `runs.log` and the archive, where a Step 2 grep finds it.
- **`confirm`** adds a run id to an existing bullet's `Runs:` field.
- **`contradiction`** is evidence against a bullet. It removes or narrows the bullet only after the refuting gate.
- **`correction`** starts its observation with the date and session of the line it corrects. Triage applies the corrected text in place of the old line. Both lines stay in the archive.
- **`defect`** and **`gap`** never become lessons. They become a corpus fix or a GitHub issue with the label `sage-corpus`.

## Structural invariants

A check written from this section alone is a complete check.

1. **Sentinels.** Line 1 of `runs.log` starts with `# sage-local-memory v4 — runs.log:`. Line 1 of `inbox.log` starts with `# sage-local-memory v4 — inbox.log:`. Without its sentinel a file is not sage memory, and `/sage-promote` stops before it reads further.
2. **Run lines.** Every line after line 1 of `runs.log` matches `^<YYYY-MM-DD> run <session> | `. v4 lines carry `agents= spend= wall= target= effort= outcome=`. Migrated v3 lines carry `est=` and `actual=`. Both shapes are valid.
3. **Inbox lines.** Every line after line 1 of `inbox.log` matches `^<YYYY-MM-DD> obs <session> | <kind> <class> | `, with `kind` and `class` from the lists above. One legacy shape stays valid: a migrated v3 line `<date> obs <session> | confirm <v3-ki-id> | <what happened>`. Triage reads it as a `confirm` whose KI now sits in `archive/v3/`: it adds a run id to the matching `lessons.md` bullet, or drops with the reason `KI not in lessons.md`.
4. **`runs.log` never shrinks.** Its line count after any write is at least its line count before.
5. **Every drained line is in exactly one batch, and `inbox.log` is never rewritten.** The batch files tile inbox lines 1 to `<to>` in order, each byte-equal to those lines. A rewrite could drop a line a run appended during it, so a batch file, written in one rename, marks what is done.
6. **The repo copy and the installed copy of `lessons.md` are byte-identical** between passes.
7. **`source-repo`** names a directory that holds `sage-claude/memory/lessons.md`.

**On failure, stop. Never repair.** A line that fails 2 or 3 is a question for triage, never silently dropped or rewritten. A writer that repairs the shape it validates cannot detect damage it caused itself.

**The blind spot.** These checks catch structural damage, never a wrong lesson. A perfectly shaped `lessons.md` full of false rules passes every marker. Falsifiers and contradiction lines are the only defence.

## The editing test

For a fact that could sit in more than one place. It governs every corpus file.

- **Skill text carries the rule and the anecdote that makes it recognisable.** It never carries the arithmetic behind the rule.
- **Harness facts go to `~/.claude/skills/sage/references/harness.md` as rules.** Their measurement, date and population go to `harness-measurements.md` beside it. That file is the declared home for dated figures, so its dates are deliberate. A run never reads it.
- **Counts, dates and absolute costs go to `runs.log`, a `lessons.md` band, or `harness-measurements.md`.** Never to other skill text.
- **A number survives in skill text only where the sentence exists to stop a run using it.** A warning against pricing from one observation loses its point without the figure.
- **A pointer must resolve on the machine that reads it.** Cite a lesson by its `<id>`, never by line number. Never cite a run, figure or date that only the authoring machine has.

## The compression floor

Never removed under any "make it shorter". A cut that changes what a fresh instance does is a spec change, not compression.

- The **undated anecdote** that makes a rule recognisable.
- Any **number the skill computes with**: a ratio, a band, a boot cost, a discount factor.
- A rule's **qualifier**.
- The **literal command** that satisfies it.
- The **completion criterion**.
- A **precedence sentence** wherever two rules can both fire.
- The **strength band**.
- Whether a constraint **binds or is only asked for**.

Cut past the floor and a rule breaks in a known order. The trigger word goes, so it fires on everything or on nothing. The literal command goes, so "verify" is satisfied by asking a second model, which is the failure, not the fix. The anecdote goes, so the rule has no shape left to match. The band goes, so it can no longer be traded off against anything.
