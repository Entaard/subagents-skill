<!-- generated from sage/policy/implementation.md sha256:de8a135a3451cf6a9b5bf89e0b61aa4faad0a93267b60c77d2879e12c26dcbe1; do not edit -->

# Software implementation policy

Policy owner: `policy.implementation`

This is the canonical implementer reference for Sage software mutation. A mutation writer reads the clean-code section before editing. It reads the testing and mocking sections when it will add or change tests, and the concurrency section only when the observable change shares mutable state across threads, tasks, or processes or changes async coordination. These rules apply to every touched line, including tests. Repository-specific standards win where they deliberately differ.

## Clean code

### The one-read test

A reader with no repository memory understands a function by reading its body once, top to bottom. Every line stays at one level, every call name states its whole job, and nothing happens that the body does not show. A reader opens a callee only to learn how a named step works. When the rules below conflict, this test decides.

1. Understand why the current code behaves as it does before changing it.
2. Fix the cause rather than disabling a warning, type check, error, or test.
3. Clean every touched line; keep unrelated refactoring outside the lease.
4. Treat a name as a contract: the code does all and only what the name promises. A name that needs a comment is incomplete.
5. Name the domain concept, not the mechanism, and rename when meaning drifts.
6. Use one word for one idea across the codebase; do not use one word for different acts.
7. Prefer the repository's domain language from `CONTEXT.md` or equivalent.
8. Match name length to scope.
9. Give a function one job at one level of detail.
10. Extract to name an honest concept, not merely to shorten a body. Stop splitting when the caller no longer reads as one story.
11. A function either changes the world or answers a question, not both.
12. Arguments are inputs. Keep them few, do not mutate them, split boolean modes, and name a type for values that always travel together.
13. Pass clocks, randomness, configuration, and collaborators as dependencies. Compose defaults at the system boundary.
14. Name conditions, magic values, and boundaries; prefer positive predicates.
15. Return early for terminal cases so the happy path stays straight; isolate error handling.
16. Ask only immediate collaborators. Hide message chains behind the object that owns the walk.
17. Merge duplicated decisions that must change together. Keep merely similar code separate until the shared abstraction is real.
18. Branch on a type once, behind polymorphism or one shared lookup.
19. Order files top-down: public entry points first, each helper after its first caller, and values just before use.
20. Give a module, class, or file one reason to change.
21. Prefer a small interface over a deep implementation; expose only what callers need.
22. A type either hides fields and offers behavior or exposes data without rules; avoid an unstable half of each.
23. Put behavior beside the data it primarily uses.
24. Give domain concepts types that make invalid states difficult or impossible.
25. Put one owned adapter around third-party types and APIs.
26. Fail through the language's error channel with operation, subject, and cause context.
27. Avoid untyped nothing values. Return empty collections, typed absence, safe values, or loud argument failures.
28. Comments state reasons a reader cannot derive, never what the code already states.
29. A comment states only facts owned by its scope; move outside facts to their owner.
30. Delete summaries that paraphrase names or bodies.
31. Keep a necessary reason comment to one through three lines; place longer rationale in an owned decision record.
32. Comment density never requires another comment.
33. Delete dead or commented-out code, change histories, author/ticket notes, and narratives version control already preserves.
34. Delete a factually wrong comment by default; retain only a short surviving reason that passes rules 28–31.

Let formatters, linters, and type checkers own indentation, width, spacing, blank lines, import order, braces, alignment, and file naming. Follow the repository tool or existing file where no tool decides.

## Testing and mocking

### Test loop

1. Test code is production code and follows the clean-code rules.
2. Tests are fast, independent in any order, repeatable without a live network, self-checking, and timely.
3. Test edges and the neighborhood around a bug.
4. Work red before green in vertical tracer-bullet slices: one public seam, one failing test, one minimal implementation, then repeat. Horizontal batches of imagined tests are not this loop.
5. Test only public seams agreed in the admitted plan. A test observes behavior a caller cares about through the public API and survives internal refactoring.
6. Give a test one logical assertion and name what behavior it proves, not how the implementation performs it.
7. Avoid implementation-coupled tests: private methods, internal collaborators, call counts/order, or side-channel inspection in place of the public result.
8. Avoid tautologies: expected values come from a literal worked example, specification, independent oracle, or baseline, never the same computation as the implementation.

Mock only system boundaries: external APIs, time, randomness, and sometimes a database or filesystem when a real test boundary is impractical. Prefer a test database where proportionate. Do not mock owned classes, modules, or internal collaborators. Inject each external dependency. Give adapters specific SDK-style operations with one return shape per operation rather than a generic conditional fetcher; this keeps mocks branch-free and makes the exercised operation visible.

## Implementation concurrency

These rules concern code-level concurrency, not Sage worker scheduling. The ownership test decides conflicts: for every mutable value reachable by concurrent actors, name one owner. Prefer, in order, one thread; one queue or channel; a standard-library thread-safe type; or one lock held for every read and write. A comment or remembered convention is not ownership.

1. Make and test the single-threaded logic first.
2. Separate concurrency coordination from the work it coordinates.
3. Prefer standard thread-safe collections, atomics, channels, pools, and immutable structures, while checking their actual guarantees for compound operations.
4. Name the execution model—producer/consumer, readers/writers, or competing resources—and use its standard solution.
5. Give each shared value one small-reach owner and share the smallest value that works.
6. Copy per worker and merge once when measurement has not shown the copy cost unacceptable.
7. Start workers with their own inputs and outputs so they need no shared reach.
8. Keep one correct critical section small and move file, network, callback, and wait work outside it; never split an invariant across two locked regions.
9. While holding a lock, call only controlled code. Provide one synchronized operation when callers need an atomic pair.
10. Before start, define the stop signal, in-flight drain behavior, and bounded join timeout.
11. Force rare interleavings at the relevant boundaries behind a test-only switch or scheduler harness and repeat them; do not wait for chance.
12. Treat one flaky concurrency failure as a defect. Reproduce the interleaving and fix the code; retries, skips, and sleeps do not settle it.

Correctness wins over a smaller critical section. Separation wins over keeping threading beside business logic. Copying wins until measured memory cost proves otherwise. Run the ownership test on the result.

## Deliberate Sage adaptations

The source clean-code workflow asks for user confirmation of test seams. Sage co-locates that decision in the root-owned admitted plan: the root chooses the public seams and criteria before dispatch, so a writer does not reopen them independently. Code-level concurrency is distinct from orchestration concurrency and loads only from the observable implementation branch described above. These adaptations change routing and ownership, not the clean-code, test, mocking, or concurrency obligations.

Completion criterion: the writer reports which sections fired, the public seams tested, focused red/green evidence, and any deliberate repository-standard override. For concurrent code, every shared mutable value has one named owner and shutdown behavior is tested.

Normative clauses are adapted from the MIT-licensed source skills named by the Phase 0 invariant inventory.
