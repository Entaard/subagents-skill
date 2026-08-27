# Question Notes — the playbook

This is how you run the method. The reasoning behind every part is in `question-notes-anatomy.md`; here you get the steps. Evidence tags are the same as there: `[measured]` a controlled study or meta-analysis, `[observed]` recorded behaviour with no remedy tested, `[practice]` a documented practitioner account, `[inference]` my reasoning rather than a finding, `[contested]` sources disagree.

**The four rules in shorthand**, because the steps below cite them by number: **R-1** the question is the durable artifact; **R-2** the cue and the answer are separate surfaces — the title is the question, the answer starts below it; **R-3** the body is a self-explanation, not a summary; **R-4** a relation is written, never implied. The anatomy argues each one. You only need the names to follow the steps.

## Setup, once

**Make one new place, separate from both vaults you already have.** You have `Xubi` (97 notes) and `RPG-ideas` (68 notes), and both are project-scoped. Question Notes is not project-scoped, and the reason is a decidable one rather than a promise: Obsidian cannot link or search across vaults, and R-4 requires links. A question you wrote against Kubernetes and a question you wrote against C# cannot be linked *at all* if they live in different vaults. One place keeps that option open. It does not make cross-domain collisions pay off — that is the accumulating-corpus claim the anatomy's scope section says has nothing measured behind it, and nothing here changes that `[inference]`.

```
mkdir -p ~/Projects/notes/questions/{questions,maps,decisions}
```

That is the floor: a directory of `.md` files, readable by `nvim`, `grep`, and `rg`. Open it as a third Obsidian vault if you want backlinks and graph view — the format below does not depend on it, and no step in this playbook requires a plugin or an install.

Three files and folders, and nothing else:

- `OPEN.md` — the running question list. One file, append-only during a session.
- `questions/` — one file per answered question. Filename *is* the question.
- `maps/` and `decisions/` — the instruments, created only when a path calls for them.

Filenames: `questions/how-does-a-request-reach-its-handler-in-omnisharp.md`. Long, ugly, greppable, and readable as a prompt in a search result list — which is the point of R-2. The rule for turning a question into a filename: lowercase it, replace each space with a hyphen, drop the question mark and every other punctuation mark, and stop at about eight words — unless cutting there would leave two questions indistinguishable in a file listing, in which case keep the words that tell them apart. It does not have to be pretty; it has to read as a prompt and it has to be findable.

## The daily loop

Do these in order. They are actions, not intentions.

**"Session" here means one sitting with the material** — an hour, an afternoon, whatever you actually do in one go, from opening `OPEN.md` at step 1 to closing it at step 7. Every "after a few sessions" below is counted in those. One session will not reach the map trigger (seven to twelve clustered notes) or the weekly recall pass, and is not meant to: leaving `maps/` and `decisions/` empty after a first sitting is the correct outcome, not a step you skipped.

1. **Open `OPEN.md` before you open the code or the docs.** Read the questions already there. This is the whole defence against the failure Sillito, Murphy & De Volder (2006, *Questions Programmers Ask During Software Evolution Tasks*, FSE 2006) observed in working programmers: re-asking questions they had already answered and retracing work they had already done, unaware of it `[observed]`.

2. **Append every question that makes you stop, the moment it makes you stop.** One line, prefixed `- [ ]`. Do not chase it, do not answer it, do not tidy the phrasing. If you were mid-task, you are still mid-task.

3. **Chase exactly one question at a time.** When you reach an answer, decide the next step by one test: *could I re-derive this in under a minute with grep, the compiler, or `kubectl explain`?* If yes, tick the line in `OPEN.md` and move on — no note. If no, go to step 4.

4. **Write the note.** Title is the question, verbatim, as a question. Then:

```markdown
# <the question>

**Answer.** <one sentence>

**Why.** <2-5 sentences: why it is so, and what would be different if it were not>

**Settled by.** <file:line | citation + URL | the command that decides it>

**Links.** - [[other note]] — <why these two belong together>

**Status.** answered 2026-08-26
```

5. **Write the `Why` before you write the `Answer` if you get stuck.** If your `Why` restates the source, delete it and start again with the sentence "This is so because..." — self-explanation is rated moderate and summarization low by Dunlosky et al. (2013, *Improving Students' Learning With Effective Learning Techniques*, Psychological Science in the Public Interest 14(1):4-58) `[measured]`. That writing this **Why** field *is* the same act as Chi-style self-explanation is my reading of the two, not something either study tested `[inference]`.

6. **Link on the way out, with a reason.** Before saving, grep the corpus for one word from your title and link the closest hit, with the sentence saying why. `rg -l "<word>" ~/Projects/notes/questions` takes three seconds. A bare link is not a link (R-4). "The corpus" means everything under `questions/`, across every subject — not this session's notes and not this project's. That is the whole reason it is one directory. Skip this step for your first three or four notes: with an almost-empty corpus there is no closest hit, and forcing one manufactures a relation you have not actually got.

7. **Close the session by re-reading `OPEN.md` and deleting nothing.** Unanswered questions stay unanswered: they remain `- [ ]` lines in `OPEN.md` and do not become note files. (`Status. open` is a field on a note *file* — for one you started and could not finish — so it does not belong on a checkbox line.) They are the agenda for the next session, and they are the part of this method that most people throw away.

8. **Once a week, spend fifteen minutes on two things:** run the recall pass (below), and check whether seven to twelve notes have piled up around one subject. If they have, that is the signal to build a map — not before.

### The recall pass

Read the title. Say the answer out loud before you look. Then look.

Run it **only** over notes whose answers do not decay — concepts, mechanisms, reasons, invariants, decisions. **Never over codebase facts**; the next commit can silently falsify them, and rehearsing a stale one trains you into a wrong belief. Retrieval practice and distributed practice are the two techniques rated high utility by Dunlosky et al. `[measured]`, and the interval scales with how long you need to keep the material: Cepeda, Vul, Rohrer, Wixted & Pashler (2008, Psychological Science 19:1095-1102) report verbatim that "the optimal gap declined from about 20 to 40% of a 1-week test delay to about 5 to 10% of a 1-year test delay" `[measured]`. In practice: days for something you need this sprint, weeks for something you want next year.

---

# The three paths

The three jobs you asked about need three different procedures, because the material differs in kind. Do not run one procedure and rename it.

## Path A — learning a big, complicated system

**Ends in:** a map note. The map is the deliverable; the question notes are the inputs.

1. Write the **focus question** for the whole system first, in `maps/<system>.md`. One question, the thing you actually need the system to answer for you. Everything else is scoped by it (Novak & Cañas's construction rule for concept maps).
2. Learn by chasing questions, not by reading in order. Follow the daily loop. Do not draw anything yet.
3. When seven to twelve notes have clustered, open the map note and write each relation as a line: **concept — relation — concept**. Only relations you have a note for.
4. Add **cross-links between clusters** — the relations that connect one part of the map to a different part. These are what a list of facts cannot hold, and they are the reason the map exists.
5. Re-read the map against your notes and fix it. Iterate; maps are meant to be revised as understanding changes.
6. Feed the map's gaps back into `OPEN.md` as new questions. A missing arrow is a question.

Grade what you are doing here honestly: Nesbit & Adesope (2006, Review of Educational Research 76(3):413-448; 67 effect sizes, 55 studies, 5,818 participants) associate concept-map use with increased retention `[measured]`, and Schmidt et al. (2024, Behavioral Sciences, PMC11428796, n=24) found map explanations carried more correct relational propositions than verbal ones, 12.1 against 9.3, at roughly 4.5x the time `[measured]` — but that measured maps as an explanation format, and Karpicke & Blunt (2011, Science 331(6018):772-775) found retrieval practice beat concept mapping even on a concept-map test, a result formally contested by Mintzes, Cañas et al. `[contested]`. So: build the map to *see* the relations, and run the recall pass to *learn* them. The map is not the studying.

### Worked example — Kubernetes control plane

Focus question, at the top of `maps/kubernetes-control-plane.md`: *"When I apply a Deployment, what actually decides that a container starts on a node?"*

After a week of chasing that, notes exist for questions like *"Why does no component write to etcd except the API server?"* and *"What does the scheduler actually change when it schedules a pod?"*. The map:

```markdown
# Focus: When I apply a Deployment, what actually decides that a container starts on a node?

kubectl — sends a desired-state object to → kube-apiserver
kube-apiserver — is the only component that reads and writes → etcd
deployment controller — watches the API server and creates → ReplicaSet
replicaset controller — watches the API server and creates → Pod objects (nodeName empty)
kube-scheduler — watches for pods with no nodeName and sets → pod.spec.nodeName
kubelet on that node — watches for pods bound to itself and starts → containers

Cross-links:
- the controllers never talk to each other. Each one LEARNS by watching the API
  server and ACTS by writing back to it — which is why the control plane keeps
  working when one controller is down: nothing is waiting on a call from anything else
- exactly two arrows leave that pattern, and they are the system's edges: the API
  server talks straight to etcd, and the kubelet talks straight to the container
  runtime. Everything between those two edges is watch-and-write through the API
  server. Knowing where a pattern stops is worth more than the pattern
- "desired state" lives in etcd; "actual state" is reported back by the kubelet —
  the reconciliation gap between them is the whole design

Open: what happens to a bound pod if the kubelet never reports back? -> OPEN.md
```

Notice the shape of the payoff. The individual facts you could have looked up; the first cross-link — that controllers only ever watch and write, and never call each other — is the thing that makes the rest predictable, and it only became visible once the relations were written down next to each other. Confirm each arrow against kubernetes.io before you trust it; the `Settled by` field of the source notes is where that citation lives.

## Path B — exploring a new codebase

**Ends in:** an open-question thread, a small number of *why*-notes, and eventually an architecture map. **Deliberately not a set of fact notes.**

This path shares Path A's daily loop, and it ends in the same kind of map. Three things are its own, and they are what make it a different path rather than Path A with different nouns: what you **refuse** to write, the ADR, and which notes are eligible for the recall pass. Code facts are re-derivable on demand and decay on the next commit, so notes about them are worth less than nothing — they go wrong silently. Keep only what the source does not contain: the open questions, the reasons, and the relations.

1. **Start `OPEN.md` with three or four questions before you read any code.** Use Sillito et al.'s four categories to phrase them, which run roughly in the order you will need them:
   - **Finding an initial focus point** — where does this thing start? *"Where does a request enter the system?"*
   - **Building on that point** — what does the thing I just found touch? *"What calls this, and what does it call?"*
   - **Understanding one subgraph** — how does one connected piece work as a whole? *"How does the request pipeline get assembled at startup?"*
   - **Comparing subgraphs** — how do two pieces relate, or differ? *"Is LSP a third transport, or layered on the stdio one?"*
2. **Chase one question by reading and by running the tools**, not by reading files top to bottom.
3. **Record the trace, not the facts.** When the answer is a path through several files, that path is a relation and it is worth a note. When the answer is "this method returns a `Task<T>`", it is a fact — tick it and move on. For everything in between — an answer that lives in two branches of one file, say — use this test instead: **did the answer change a belief you were holding?** If it did, it is a trace and worth writing. If it only filled a blank, it is a fact.
4. **When you find a decision rather than a mechanism, write it as an ADR** in `decisions/`: Context / Decision / Consequences, short and immutable (Michael Nygard, 2011, *Documenting Architecture Decisions*) `[practice]`. Rationale is the one thing you can never re-derive from source. Nygard's own reason for the format is that large architecture documents are "never kept up to date".

   You will not find decisions by reading code, and this is the step most likely to go unused: source records what was chosen and never what was rejected. **Four things trigger an ADR and nothing else does** — a comment or commit message that names a tradeoff or an alternative; a design doc, RFC or PR discussion; a piece of code deliberately harder than the obvious version, where you can answer "why not the obvious one?" — this one asks you to supply the obvious version yourself, so it gets easier the longer you have been in the codebase, and early on you will mostly skip it; or a decision *you* are making now about how you will work with this codebase. If none of the four turns up in a session, write no ADR. An empty `decisions/` is the correct outcome, not a missed step.
5. **After a few sessions, draw the architecture map** — the overview Sillito's participant N9 asked for outright: "I think I would need some kind of overview document that says... this is the architecture of how the thing works and the main classes involved" `[observed]`.
6. **Keep codebase *facts* out of the recall pass — but not the rest of what this path produces.** This is the one place it is easy to over-correct. Facts decay on the next commit and rehearsing a stale one trains you into a wrong belief. But the why-notes, the ADRs and the traces you kept are reasons and structure, and they do not decay that way — they are exactly the non-decaying material the pass is for, and Path B would otherwise be the one job of the three that never touches either high-utility technique. Mark every note in this path `Status. answered <date>` with a `Settled by` naming a commit, so a future you knows what to re-check before trusting a line number.

Keep the ceiling in view. Naur (1985, *Programming as Theory Building*) argues that reconstructing the theory of a program "merely from the documentation, is strictly impossible" `[practice]`. These notes make you faster at rebuilding the theory yourself. They do not contain it, and there is no note-taking method that changes that.

### Worked example — how a request reaches its handler in OmniSharp

Real codebase, on your disk: `~/Projects/omnisharp-roslyn` — about 800 C# files (`git ls-files '*.cs' | wc -l` returns 808 at this commit; count it yourself rather than trusting this line). The day-one question, which cannot be answered by reading any single file:

`OPEN.md` after twenty minutes:

```markdown
- [x] When an editor sends a request, how does it reach the code that answers it?
- [ ] How does a handler get chosen when two handlers export the same endpoint name?
- [ ] What decides which language a request is routed to? (saw IPredicateHandler, didn't chase)
- [ ] Why is there both an Http driver and a Stdio driver with separate hosts?
```

The answered one becomes `questions/how-does-a-request-reach-its-handler-in-omnisharp.md`:

```markdown
# When an editor sends a request, how does it reach the code that answers it?

**Answer.** The command string on the wire is looked up in a dictionary of endpoint
handlers that was built at startup from MEF export metadata, so the attribute on the
request model — not any routing code — is what binds a name to a handler.

**Why.** `OmniSharpEndpointAttribute` is a `[MetadataAttribute]` that subclasses
`ExportAttribute` and exports as `typeof(IRequest)`, carrying EndpointName, RequestType
and ResponseType. At startup the host asks the composition container for every
`Lazy<IRequest, OmniSharpEndpointMetadata>` and every
`Lazy<IRequestHandler, OmniSharpRequestHandlerMetadata>`, then pairs them by matching
EndpointName. If the attribute were absent, the endpoint would simply not exist at
runtime — there is no central route table to fall back on, and nothing would fail at
compile time. That is what makes this hard to read from the source: the binding is not
written anywhere, it is assembled.

**Settled by.** src/OmniSharp.Abstractions/Mef/OmniSharpEndpointAttribute.cs:6-19;
src/OmniSharp.Stdio/Host.cs:60-64 (GetExports) and Host.cs:216
(`_endpointHandlers.TryGetValue(request.Command, out var handler)`);
src/OmniSharp.Host/Endpoint/EndpointHandler.cs:32 (filters handlers where
`x.Metadata.EndpointName == metadata.EndpointName`). HEAD c16eb2a1.

**Links.**
- [[what-does-omnisharp-do-when-two-handlers-export-the-same-endpoint]] — same lookup,
  and it is the case where pairing by name stops being a one-to-one mapping.

**Status.** answered 2026-08-26 — verify against HEAD before trusting the line numbers.
```

Look at what is *not* in that file. Not the signature of `HandleRequest`. Not the list of endpoint names. Not what `Lazy<T>` does. All of those are one `rg` away and all of them will move. What survives is the relation — wire command → dictionary → export metadata → handler — and the sentence that makes it predictable: *the binding is assembled at startup, not written down.* That sentence is what lets you answer the next question, which is why the trace of a concrete endpoint is worth keeping as an example rather than as a fact:

```markdown
# What does one endpoint look like end to end, concretely?

**Answer.** QuickInfo: the request model carries the endpoint attribute, the service
carries the handler attribute, and nothing else connects them.

**Why.** Neither file mentions the other. A constant in a third file is the only thing
that pairs them, and the pairing is done by the container at startup rather than written
anywhere. That is why adding an endpoint costs two attributes and no wiring: there is no
route table to edit, so there is nothing to forget to edit. The same property is where it
fails — misspell the constant on either side and the pair simply never forms. Nothing
complains at compile time and nothing complains at startup; the failure surfaces only when
something calls the endpoint, as a `NotSupportedException`. Which one you get says which
side you broke: `Host.cs:222` if the name never reached the dictionary at all, and
`EndpointHandler.cs:232` if it did but no handler matched it. The binding is late, and so
is the error.

**Settled by.** src/OmniSharp.Abstractions/Models/v1/QuickInfoRequest.cs:5;
src/OmniSharp.Roslyn.CSharp/Services/QuickInfoProvider.cs:18;
src/OmniSharp.Stdio/Host.cs:222 and src/OmniSharp.Host/Endpoint/EndpointHandler.cs:232
(the two throws). HEAD c16eb2a1.

**Links.** - [[how-does-a-request-reach-its-handler-in-omnisharp]] — this is the concrete
instance of that mechanism; keep them together or neither makes sense alone.

**Status.** answered 2026-08-26.
```

Two notes, four open questions, no fact notes. After a few more sessions those cluster into `maps/omnisharp-request-pipeline.md`, built exactly as in Path A.

## Path C — brainstorming, connecting, applying

**Ends in:** an argument map. Not a link graph, and not a concept map.

This is the path where linking is not enough, and I want to be specific about why. Robert Minto (*Rank and File*, Real Life, 2021) spent years building a note network and found it "useless" when he had to actually construct an argument: it gave him raw material and no shape `[practice]`. A link graph is the thing that failed him, so adding more links is not the fix. What represents shape is inferential structure — premises, co-premises, objections, conclusion (Davies 2011, Higher Education 62:279-301) — and argument mapping is the best-measured member of this family: Álvarez Ortiz, *Does Philosophy Improve Critical Thinking Skills?* (MA thesis, University of Melbourne, 2007; full text at reasoninglab.com/wp-content/uploads/2017/05/Alvarez-Final_Version.pdf) reports 0.68 SD (95% CI [.51, .86]) for semester courses using some argument mapping and 0.78 SD (CI [.67, .89]) with heavy practice — figures and intervals confirmed against the paper itself `[measured]`. **Read what those numbers measured:** gains on critical-thinking tests, over a taught semester course, with an instructor. Not one person mapping one argument at a desk. That the same structure helps *you*, here, is my step from their result and not their finding `[inference]`. The criticism travels with it too: several influential studies lacked a comparable active control `[contested]`.

1. **State the conclusion you are tempted by, as a single sentence.** If you cannot, you are still in Path A.
2. **List the premises that would have to be true for it to hold** — each one as a claim you could be wrong about, not as a topic.
3. **Mark each premise with where it comes from:** a note you already have, a thing you believe but never checked, or an assumption. The second category is the interesting one.
4. **Write the strongest objection to each premise**, including co-premises the argument needs but you never stated.
5. **Turn every unchecked premise into a question in `OPEN.md`.** This is the join between this path and the other two: Path C generates the questions that Paths A and B answer.
6. **Redraw after you get answers.** The map's job is to show you which single premise the whole conclusion actually rests on.

### Worked example

You are tempted by: *"We should move our scheduled jobs out of the .NET service and into Kubernetes CronJobs."*

`maps/argument-move-jobs-to-cronjobs.md`:

```markdown
CONCLUSION: Move the scheduled jobs out of the service and into Kubernetes CronJobs.

  P1. The jobs currently block deploys, because a running job delays pod shutdown.
      [from note: why-does-our-rollout-wait-90-seconds] — checked
  P2. CronJobs would isolate job failure from request-serving failure.
      [assumption — never tested] -> OPEN.md
  P3. Operating a CronJob costs less than operating the in-process scheduler.
      [belief, unchecked] -> OPEN.md
      OBJECTION: adds image build + RBAC + a second config surface per job.
      CO-PREMISE the argument needs but I never stated: the jobs do not need
      the service's warm in-memory cache. If they do, P3 inverts.

  OBJECTION TO CONCLUSION: CronJob missed-schedule semantics under
  startingDeadlineSeconds differ from the current scheduler's catch-up behaviour.
  -> OPEN.md: "what happens to a missed CronJob schedule, exactly?"

  WHAT THE ARGUMENT ACTUALLY RESTS ON: the co-premise under P3, not P1.
```

The last line is the output. You began convinced by P1 — the deploy pain, the thing you feel weekly — and the map shows the decision turns on an unstated assumption about cache warmth that nobody had said out loud. A pile of linked notes about CronJobs would never have surfaced that, because "what does this argument need that I have not said?" is not a question a link graph can be asked.

---

## Your first hour

Nothing to install. You have `nvim`, `rg`, and Obsidian already.

1. **Minutes 0-2.** `mkdir -p ~/Projects/notes/questions/{questions,maps,decisions}` and `touch ~/Projects/notes/questions/OPEN.md`.
2. **Minutes 2-5.** Open `~/Projects/omnisharp-roslyn` — a real codebase you did not write, about 800 C# files. Write four questions into `OPEN.md` from the README and the output of `ls src` **only** — project and directory names, no file contents. Directory structure is enough to ask good questions from, and staying out of the files is what stops you answering a question before you have written it down.
3. **Minutes 5-40.** Chase exactly one — and **not the question this playbook already worked through above.** You have read its answer, so writing it up would be copying rather than deriving, and R-2 exists precisely to stop you meeting an answer where a cue should be. Pick one of your own. If you want a route with something real at the end of it, try *"Why is there both an Http driver and a Stdio driver with separate hosts?"*: start from `src/OmniSharp.Http/` and `src/OmniSharp.Stdio/` and compare how each gets from a received request to a handler. Append every new question that stops you; do not chase them.
4. **Minutes 40-55.** Write one note in the format above. Filename is the question. Force yourself to write **Why** in five sentences that a diff against the source could not produce. If you catch yourself restating what the code says, delete it and write the sentence beginning "This is so because...".
5. **Minutes 55-60.** Fill in `Settled by` with real `file:line` references and the current commit hash. Read `OPEN.md` once. Stop.

That hour is written around Path B because a codebase is the concrete thing sitting on your disk. The other two start just as small and you do not need a separate hour for them: **Path A** begins and ends with step 1 — write the focus question at the top of a map file, and stop. **Path C** begins and ends with its step 1 — write the conclusion you are tempted by as one sentence, and stop. Both are five-minute artifacts, and both are enough to have started.

You now have one finished note and three open questions, which is the whole method running at its smallest size. Do that four more times before you build anything else. Add a map when notes cluster; add an ADR when you meet a decision rather than a mechanism; add the argument map when you have to take a position.

Keep it small on purpose. The two long-run outcomes documented anywhere in the evidence behind this method are both abandonments of large corpora `[practice]`, and nothing here protects you from that except the discipline of writing few notes and throwing away facts.
