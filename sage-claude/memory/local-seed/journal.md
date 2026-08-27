<!-- sage-local-memory v3 -->
# Sage journal

Append-only. Line 1 is the sentinel; nothing may rewrite it. Payload lines follow the grammar `date type session | payload`, types `run`, `obs`, `use`, `mark`:

```
<date> run <session> | <task class> | agents=N est=X actual=Y wall=W | <note>
<date> obs <session> | <kind> <class> | <observation> | falsifier: <...>
<date> obs <session> | confirm <ki-id> | <what happened>
<date> obs <session> | settle <ki-id> | artifact: <...>
<date> use <session> | <ki-id> hit | <ki-id> miss: <why>
<date> mark promote | drained through here by the <date> pass
```

Write one line per fact; never reflow an existing line.

2026-08-04 run seed | web research sweep, agents fetching primary sources **(seed)** | agents=5 est=225k actual=451k wall=~25 min | Off by 2–3×. Fetch-heavy web research runs 70–120k per agent, not the 15–40k exploration band.
2026-08-04 run seed | completeness critic over ~25k words of notes plus 4 skill files **(seed)** | agents=1 est=35k actual=172k wall=~10 min | Off by 5×. A critic's cost tracks the corpus it must read, not the number of drafts it reviews.
2026-08-05 run seed | 2 reviewers on a small prose diff against a written spec **(seed)** | agents=2 est=120k actual=193k wall=~7 min | Off by 1.6× on a *small* diff — the reviewers still held a 6.6k-word skill plus a 2.8k-word spec.
2026-08-05 run seed | no-op boot probes, haiku **(seed)** | agents=2 est=15k actual=21k wall=<1 min | Dispatch floor measured: scoped agent 4,962; general-purpose 16,036. The ~3× ratio is the portable half.
2026-08-05 run seed | 45-item review across 8 skill files: 1 inline writer, 2 verifiers on a frozen set **(seed)** | agents=2 est=140–200k actual=161k (68k + 93k) wall=~5 min | **Estimate held** — first hit on the review band. Coordination check paid partially: the two lenses returned disjoint findings, but the run's worst defect surfaced only from *running* the installer, which no diff reader could see.
2026-08-06 run seed | review and optimise a skill: 2 web researchers, 1 docs fact-check, 1 blind critic, then 2 verifiers on the frozen diff **(seed)** | agents=6 est=470k actual=401k wall=~35 min | Brief style, not task class, sets web-research cost: URL-named briefs came back at 13.7k and 33.7k against a 70–120k open-ended band. A sonnet refuter against opus-authored prose killed 4 claims, 3 of them defects introduced during the fix round.
