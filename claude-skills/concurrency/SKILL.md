---
name: concurrency
description: Rules for writing and changing code that runs at the same time as other code. Use when a change shares mutable state across threads, tasks, or processes. Use when a change adds or alters locking, background work, queues, or async coordination. Use when a threading test fails only sometimes, or when the user asks for concurrency by name. Do not use for ordinary single-threaded changes.
---

# Concurrency rules for an implementer agent

Consolidated from a larger rule set. These rules govern code that runs at the same time as other code, in any language.

They add to the `clean-code` rules. They do not replace them. Read this file when your change shares mutable state across threads, tasks, or processes.

---

## The ownership test

**For every piece of state that two threads can reach, name the one thing that owns it. Shared state with no owner is a defect you have not found yet.**

An owner is one of four things. They are listed in the order you should prefer them:

1. **One thread.** No other thread touches the state.
2. **One queue or channel.** Threads pass the state along instead of sharing it.
3. **A thread-safe type** from the language or its standard library.
4. **One lock.** Every read and every write holds it.

"The programmer remembers to lock it" is not an owner. A comment is not an owner.

Prefer an owner that removes the sharing over one that manages it. The first two share nothing at all. The third makes a tested library do the coordination. Your own lock comes last, because it is the only one of the four where the coordination is yours to get wrong.

Concurrency bugs are timing bugs. They survive a thousand test runs and then fail in production. You cannot find them by reading the code once. Testing cannot find them all either. So you design them out instead. That is the job this test does.

**When two rules below disagree, the ownership test decides.**

---

## Before you write it

1. **Get the single-threaded version working first.** Write the logic. Make it correct. Make its tests pass. Add threads only after that. A bug you carry into concurrent code becomes a bug you can no longer reproduce.
2. **Keep concurrency code separate.** Put the thread handling in its own module. Keep the work it coordinates in another. Code that starts a thread does not also decide a price.
3. **Use the library's thread-safe types.** Read what your language and its standard library already give you: concurrent collections, atomics, channels, task pools, immutable structures. Reach for one before you write a lock. Read what they do *not* promise, too. A collection can be safe for one call and unsafe for a check-then-act pair.
4. **Match the problem to a known execution model.** Most problems take one of three shapes. Producer-consumer: one side makes work, the other takes it. Readers-writers: many readers, few writers, and no reader may see a half-written value. Competing for shared resources (the dining philosophers problem): every thread holds part of what another thread needs. Name your shape, then use the standard solution for it. Invented coordination schemes are where deadlocks live.

## Shared state

5. **Give every shared thing one owner.** Keep that owner's reach small. Share the smallest thing that works. Pass one value, not the object that holds it. Every extra field inside a lock is one more place to get wrong. An immutable value passes the ownership test for free, because nothing can change it.
6. **Copy rather than share.** Give each thread its own copy of the data. Let it work alone. Merge the results at one point afterwards. A copy costs memory. Memory is cheaper than a lock you got wrong. Measure the cost before you reject this on cost.
7. **Keep threads independent.** A thread takes what it needs as arguments when it starts. It reads its own data and writes its own data. It does not reach into a shared object while it runs. Independent threads need no coordination, so they cannot deadlock.
8. **Keep the critical section small.** Lock the smallest region that keeps the invariant true. Move the slow work outside it: no file access, no network calls, no waiting on another thread. One warning. Do not split one critical section into two to make each one smaller. Two locked regions with a gap between them protect nothing.
9. **While you hold a lock, call only code you control.** Keep callbacks, overridable methods, and other locked methods outside the critical section. Code you do not control may take a second lock in the opposite order. Both threads then stop forever. Where a caller must run two synchronised methods as one unit, do not make the caller hold both locks. Give the pair one method that owns the whole operation.

## Shutdown

10. **Plan shutdown before you start the first thread.** Decide three things while you write the start code, not after the first hang report. How does a thread get told to stop? How does it finish the work already in flight? How long does the caller wait before it gives up? A thread waiting for work that will never arrive does not stop on its own. A producer that stops first leaves its consumer waiting forever.

## Tests

11. **Force the rare interleaving. Do not wait for it.** A timing bug appears once in a thousand runs. On your machine it never appears at all. Add delays at the points where the order matters, then run the test many times. Some languages ship a scheduler or a test harness that does this for you. Use it where it exists. Where you add delays by hand, put them behind a switch. Keep them out of shipped code.
12. **Treat a flaky threading test as a real defect.** A test that passes ninety-nine times and fails once has found a bug. Find the interleaving that fails, then fix the code. A retry, a skip, or a sleep hides the report and keeps the bug. Every flaky test you explain away trains you to explain away the next one. One of those is a production outage.

---

## When rules fight

- **"Keep concurrency code separate" fights the one-read test.** Moving the thread handling to its own module sends the reader to a second file. Accept that cost. Threading mixed into business logic makes both unreadable. The reader must then hold the timing in their head on every line.
- **"Copy rather than share" fights memory cost.** Copy first. Share only when a measurement, not a guess, says the copy is too expensive.
- **"Keep the critical section small" fights correctness.** Correctness wins. A larger critical section that holds the invariant beats two small ones that lose it.

Run the ownership test on the result. It settles all three.
