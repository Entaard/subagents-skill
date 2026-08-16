---
name: clean-code
description: Rules for writing and changing code in this ecosystem. Covers names, function shape, modules, errors, comments, and the red-green test loop. Use when an agent or a user writes or changes code under this ecosystem's standards, or when the user asks for clean-code by name. Do not use this for a generic test-driven-development request outside this ecosystem.
---

# Clean code rules for an implementer agent

Consolidated from a larger rule set. These rules govern the code you write, in any language.

Load this whole file for any agent that writes or changes code. It is not a review checklist. It is what you apply while you type.

---

## The one-read test

**A reader understands what a function does by reading its body once, top to bottom. They never open a callee to learn *what* happened. They open a callee only to learn *how* one step works.**

The reader is a person or an AI agent with no memory of this codebase. Every file they must open costs them. Write so they open one.

The test applies hardest to a public entry point. That is where a reader lands.

A body passes when three things are true:

1. Every line reads at the same level of detail.
2. Every call states its whole job in its name.
3. Nothing happens that the body does not show.

```
# Fails. What does this do? You must open all four callees to find out.
function handleOrder(order):
    validate(order)
    process(order)
    update(order)
    notify(order)

# Passes. The body is the whole story. Open a callee only for the how.
function placeOrder(order):
    rejectIfOutOfStock(order)
    charge(order.customer, order.total)
    reserveStock(order.items)
    sendConfirmationEmail(order.customer, order)
```

Both versions have four calls and the same structure. Naming carries the whole difference, not size.

**When two rules below disagree, the one-read test decides.**

---

## How you work

1. **Understand before you change.** Know why the current code behaves as it does. Do not adjust conditions until the tests turn green.
2. **Fix the cause, not the signal.** When a check fails, change the code. Leave the warning, the type check, and the test in place.
3. **Clean what you touched before you hand the change over.** Write every line you touch by these rules, even where the surrounding code breaks them. Do not refactor code your change did not touch. Review still checks the result.

## Names

4. **The name is a contract.** It states the whole job. The function does everything the name promises. It does nothing the name does not promise. `getUser` never creates a user. If a reader must open the body to learn what a call does, the name is wrong. If the name needs a comment, the name is wrong.
5. **Name the concept, not the mechanism.** `chargeCard`, not `postToStripeV2Endpoint`. Rename when the meaning drifts.
6. **One word per idea, across the whole codebase.** Do not mix `get`, `fetch`, `load`, and `retrieve` for one act. Do not use `add` for two different acts.
7. **Take names from the domain.** Use the project's own vocabulary. Read `CONTEXT.md` when it exists. A name a domain expert recognises beats an invented one.
8. **Match name length to scope.** `i` is fine inside a three-line loop. A field that crosses a module needs full words.

## Function bodies

9. **One job, one level.** Every statement sits one level below the function's name. A high-level step next to a byte-level detail breaks the read.
10. **Extract to name a concept. Do not extract to shorten.** A new function must earn an honest name and read as one step at the call site. Parts that only make sense together belong together. Length is a signal, not a limit. When a body outgrows one screen, count its jobs, not its lines.
11. **Do something or answer something, never both.** A function that returns a value leaves the world unchanged. A function that changes the world says so in its name.
12. **Arguments are inputs.** Keep the list short. Three is already a lot. A boolean argument means the function has two jobs, so split it. Never write to an argument. Arguments that always travel together are a type waiting to be named.
13. **Take dependencies as parameters.** A function receives its clock, its random source, its configuration, and its collaborators. It does not reach out for them. Defaults live at the top of the system and pass down.
14. **Name every condition and every boundary.** Replace a compound test with a named predicate. Replace a raw number or string with a named constant. Replace a scattered `+1` with a named boundary. Prefer the positive form: `isOpen`, not `notClosed`.
15. **Keep the happy path straight.** Return early on the cases that end the work. Then let the main flow run without nesting. Error handling lives in its own place.
16. **Ask your neighbours only.** Call methods on your own object, on your arguments, on what you created, and on your own fields. Do not chain through what those calls return. `a.b().c().d()` forces the reader to learn a whole object graph.
17. **Remove real duplication.** Two copies of one decision drift apart, so merge them. Two copies that only look alike stay apart. When you are unsure, wait for the third copy.
18. **Branch on a type once.** Repeated switches on the same type belong behind one abstraction. Use polymorphism, or one lookup table that every site shares.
19. **Order the file top down.** Public entry points first. Each helper sits below its first caller. Declare a variable just above its first use. The reader moves from purpose to detail and never scrolls back.

## Modules and state

A few words matter here and in the test loop below.

- **Interface**: the part of a module a caller can see and call.
- **Deep module**: a small interface over a large implementation. It hides much and exposes little.
- **Seam**: the public boundary where you observe behavior in a test, without reaching inside.
- **Adapter**: your own interface in front of a type you do not own.

20. **One reason to change.** A module, class, or file holds one job. When you cannot name that job in one short phrase without "and", split it.
21. **Small interface, deep implementation.** Hide the work. Expose the least a caller needs to use the module correctly. A module whose interface is nearly as large as its implementation earns nothing.
22. **Choose behaviour or data.** An object hides its fields and offers behaviour. A data holder exposes its fields and holds no rules. A type that does half of each resists both kinds of change.
23. **Put the method with the data it uses.** A function that mostly reads another type's fields belongs on that type.
24. **Give a domain concept its own type.** Money is not a float. An identifier is not an integer you can add. Let the type make wrong states impossible. A rule the compiler enforces beats a rule a comment requests.
25. **Wrap what you do not own.** A third-party type stops at one adapter. The rest of the codebase talks to your own interface. That gives you one place to change and one seam for tests.

**Shared state across threads is a different problem.** When your change lets two threads, tasks, or processes reach the same mutable state, or adds a queue, a background task, or async coordination, apply the `concurrency` skill's rules as well as these. If you cannot load a skill, read `~/.claude/skills/concurrency/SKILL.md` instead.

## Failure

26. **Fail through the language's error channel, with context.** Use the mechanism a caller cannot ignore by accident. Do not hide a failure inside a normal return value. The message says which operation failed, on what, and why. A stack trace only says where.
27. **Do not pass or return "nothing".** Return an empty collection, a typed absence, or a value that already does the safe thing. Fail loudly on a missing argument. One forgotten check breaks the system.

## Comments

28. **Write why, never what.** The code states what it does. A comment records the reason a reader cannot derive: a constraint, a trade-off, a warning, or a rejected alternative.
29. **Delete what version control already remembers.** Dead code, unused functions, commented-out code, change logs, author names, ticket numbers, and "fixed in this PR" notes. All of them mislead the next reader.

## Tests

30. **Test code is production code.** Every rule above applies to it. Dirty tests get abandoned. Then the production code rots.
31. **F.I.R.S.T.** Fast. Independent, so no test sets up another and any order works. Repeatable, so it passes on a laptop with no network. Self-checking, so it passes or fails without a human reading logs. Timely, so you write it before the code it covers.
32. **Test the edges, and test around a bug.** People get the middle right and the edges wrong. Bugs cluster, so when you find one, test its neighbourhood hard.

### The loop

- **Red before green.** Write the failing test first. Then write only enough code to make it pass. Do not add a feature before its test exists.
- **One slice at a time.** One seam, one test, one minimal implementation, per cycle.

### Seams

**Test only at seams the user pre-agreed.** Before you write a test, list the seams under test. Confirm the list with the user. Do not write a test at an unconfirmed seam. You cannot test everything. Agreeing the seams first sends your testing effort to the critical paths and the complex logic, not to every edge case.

Ask: "What is the public interface, and which seams should we test?"

### Anti-patterns

- **Implementation-coupled.** The test mocks an internal collaborator. Or it tests a private method. Or it checks a side channel, such as querying the database instead of using the interface. The tell: the test breaks when you refactor, even though behavior did not change.
- **Tautological.** The expected value uses the same computation as the code (`expect(add(a, b)).toBe(a + b)`, a snapshot built by hand the same way, a constant asserted equal to itself). The test then passes by construction. It can never disagree with the code. Take the expected value from an independent source: a known-good literal, a worked example, or the spec.
- **Horizontal slicing.** Writing all the tests first, then all the implementation. Bulk tests check *imagined* behavior. You test the shape of things, not what a user sees. The tests go blind to real changes. And you lock in a test structure before you understand the implementation. Work in **vertical slices** instead: one test, then one piece of implementation, then repeat. Each test is a **tracer bullet**. It responds to what the last cycle taught you.

Read [tests.md](tests.md) for what a good test looks like, with examples. Read [mocking.md](mocking.md) for where to mock and how to design for it. Both are companion files of this skill.

---

## When rules fight

These rules do fight each other. Three fights come up often.

- **"Small" fights "few".** Splitting improves each part and adds parts. Stop splitting when the caller stops reading as one story.
- **"No duplication" fights "no wrong abstraction".** Two copies that will change together must merge. Two copies that only look alike must stay apart.
- **"Hide the detail" fights "one read".** Hiding a step behind an honest name helps the reader. Hiding it behind a vague name hurts. The name carries the whole difference.

Run the one-read test on the result. It settles all three.

## Let tooling own these

Your formatter, linter, and type checker decide the following. Do not reason about them and do not report them.

Indentation, line width, spacing, blank lines, import order, brace style, column alignment, and file naming.

For everything in that list, follow whatever the repo already does. When the repo is inconsistent and no formatter config decides, match the file you are editing.

---

Portions adapted from mattpocock/skills (github.com/mattpocock/skills), MIT license.
