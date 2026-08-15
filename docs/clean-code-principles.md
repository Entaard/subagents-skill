# Clean Code: core principles

Source: Robert C. Martin, *Clean Code: A Handbook of Agile Software Craftsmanship*, Prentice Hall, 2009.
Chapters 7, 8, 11, 12 and 13 have guest authors (Michael Feathers, James Grenning, Kevin Dean Wampler, Jeff Langr, Brett L. Schuchert). Chapter 10 is co-written with Jeff Langr.

This doc lists the principles from the book. It does not repeat the code examples. Section 16 is the complete smell and heuristic list from Chapter 17, in the book's own codes (C1, F3, G14 and so on). Use those codes when you cite a rule.

Read section 17 before you apply this as a rulebook. The book states its own limits.

---

## 1. The short list

If you keep only ten rules, keep these:

1. Code is read far more often than it is written. Optimise for the reader.
2. Names must reveal intent.
3. Functions must be small and do one thing.
4. A function must stay at one level of abstraction.
5. Remove duplication.
6. A comment is a failure to express yourself in code.
7. A class must have one reason to change.
8. Depend on abstractions, not on concrete details.
9. Test code is production code. Keep it clean.
10. Leave the code cleaner than you found it.

---

## 2. What "clean" means

The book collects definitions from several engineers. The shared points are:

- **Clean code does one thing well.** Bad code has muddled intent. (Bjarne Stroustrup)
- **Clean code reads like well-written prose.** It never hides the designer's intent. (Grady Booch)
- **Clean code can be read and changed by someone other than the author.** It has tests. It has meaningful names. It gives one way to do one thing. It has minimal, explicit dependencies. (Dave Thomas)
- **Clean code looks like someone cared.** You cannot see an obvious way to improve it. (Michael Feathers)
- **Clean code has no duplication, high expressiveness, and small early abstractions.** (Ron Jeffries)
- **Clean code holds no surprises.** Each routine is close to what you expected. (Ward Cunningham)

### The cost argument

- A mess slows the team down. Productivity falls toward zero as the mess grows.
- Adding people to a messy code base does not fix it. New people make more mess.
- A grand rewrite is a trap. The rewrite team must chase a moving target. This can take years.
- You do not meet a deadline by making a mess. The mess slows you down at once.
- The only way to go fast is to keep the code clean at all times.

### Why reading matters

The ratio of time spent reading code to writing code is well over 10 to 1. You read old code to write new code. So make the code easy to read, even when that makes it harder to write.

---

## 3. The two rules that hold the rest together

**The Boy Scout Rule.** "Leave the campground cleaner than you found it." Every check-in should leave the code a little cleaner. The cleanup can be small. Rename one variable. Split one long function. Remove one small duplication.

**We are authors.** You write for readers. Readers judge your work. This is why every rule below points at the reader.

---

## 4. Names (Chapter 2)

- **Use intention-revealing names.** A name must say why the thing exists, what it does, and how it is used. If a name needs a comment, the name has failed.
- **Avoid disinformation.** Do not use a word whose common meaning differs from your meaning. Do not call something a `List` when it is not a list. Do not use names that differ in small ways. Never use lowercase `l` or uppercase `O` as variable names.
- **Make meaningful distinctions.** Do not add number series (`a1`, `a2`) or noise words (`Info`, `Data`, `Object`, `Variable`) just to satisfy the compiler. If two names differ, they must mean different things.
- **Use pronounceable names.** You cannot discuss a name you cannot say. Programming is a social activity.
- **Use searchable names.** Single letters and raw numbers are hard to find. Use single-letter names only for local variables inside short methods. Name length should match scope size.
- **Avoid encodings.** Do not use Hungarian notation. Do not use member prefixes such as `m_`. Modern languages and tools carry that information already.
- **Avoid mental mapping.** The reader should not translate your name into a name they already know. Clarity beats cleverness.
- **Class names are nouns.** `Customer`, `Account`, `AddressParser`. Avoid `Manager`, `Processor`, `Data`, `Info`. A class name is never a verb.
- **Method names are verbs.** `postPayment`, `deletePage`, `save`. Use `get`, `set` and `is` for accessors, mutators and predicates. Prefer named static factory methods over overloaded constructors.
- **Do not be cute.** Say what you mean. `DeleteItems`, not `HolyHandGrenade`.
- **Pick one word per concept.** Do not mix `fetch`, `retrieve` and `get` for the same idea. Do not mix `controller`, `manager` and `driver` in one code base.
- **Do not pun.** Do not reuse one word for two different ideas. If the semantics differ, use `insert` or `append`, not `add`.
- **Use solution domain names.** Your readers are programmers. Pattern names, algorithm names and maths terms are good names.
- **Use problem domain names.** When no technical term exists, take the name from the business domain. A maintainer can then ask a domain expert.
- **Add meaningful context.** Put names inside well-named classes or functions. Create an `Address` class instead of prefixing seven loose variables.
- **Do not add gratuitous context.** Do not prefix every class with the application initials. Shorter names are better when they stay clear.

---

## 5. Functions (Chapter 3)

- **Small.** The first rule is that functions must be small. The second rule is that they must be smaller than that. Functions should hardly ever be 20 lines long.
- **Blocks and indenting.** A block inside `if`, `else` or `while` should be one line long, and that line is usually a function call. Indent level should not go past one or two.
- **Do one thing.** A function does one thing when all its steps are one level of abstraction below its name. Test: if you can extract another function from it with a name that is not just a restatement of the code, it does more than one thing.
- **No sections.** A function you can split into named sections (declarations, init, main loop) does more than one thing.
- **One level of abstraction per function.** Mixing high-level concepts with low-level details always confuses the reader.
- **The Stepdown Rule.** Code should read top to bottom as a narrative. Each function is followed by the functions one level below it.
- **Switch statements.** A switch always does N things. Tolerate one only when it appears once, builds polymorphic objects, and hides behind an abstraction. Otherwise it breaks SRP and the Open Closed Principle.
- **Use descriptive names.** A long clear name beats a short cryptic name. A long clear name beats a long comment. Keep the phrasing consistent across related functions.
- **Few arguments.** Zero is ideal. Then one. Then two. Avoid three. More than three needs a very strong reason. Arguments cost conceptual effort and multiply test cases.
- **Flag arguments are wrong.** A boolean argument announces that the function does two things. Split it into two functions.
- **Avoid output arguments.** Readers expect arguments to be inputs. If a function must change state, it should change the state of its own object.
- **Group arguments into objects.** If two or three arguments always travel together, they are probably a concept that deserves a name.
- **No side effects.** A side effect is a lie. It creates hidden temporal coupling and order dependency. If a temporal coupling is required, put it in the name.
- **Command Query Separation.** A function either does something or answers something. Never both.
- **Prefer exceptions to error codes.** Error codes force the caller to check at once and produce deep nesting. Exceptions let you separate the error path from the happy path.
- **Extract try/catch blocks.** Move the bodies of `try` and `catch` into their own functions.
- **Error handling is one thing.** If a function contains `try`, `try` is its first word and nothing follows the `catch` or `finally` block.
- **Do not repeat yourself.** Duplication may be the root of all evil in software. Many design ideas exist only to remove it.
- **Structured programming.** Dijkstra's single-entry, single-exit rule matters little in small functions. Multiple `return`, `break` and `continue` are fine there. Avoid `goto`.
- **How you get there.** Nobody writes clean functions on the first try. Write a rough draft with tests, then refactor: split, rename, remove duplication, reorder.

---

## 6. Comments (Chapter 4)

The base position: **a comment is a failure**. You needed a comment because you could not express the idea in code. Comments also decay. Code is the only source of truth. Inaccurate comments are worse than no comments.

- **Do not use comments to excuse bad code.** Clean the code instead.
- **Explain yourself in code.** Replace the comment with a well-named function or variable.

### Comments worth keeping

- Legal comments, such as copyright and licence headers. Point at an external licence file where possible.
- Informative comments, such as the format a regular expression matches. Prefer a better name first.
- Explanation of intent, which records why a decision was made.
- Clarification of an obscure value you cannot change, such as one from a standard library.
- Warning of consequences, such as "this test takes a long time".
- `TODO` comments, when you scan and remove them regularly.
- Amplification, which marks something as more important than it looks.
- Javadoc for a public API.

### Comments to remove

Mumbling. Redundant comments. Misleading comments. Mandated comments (a Javadoc on every function). Journal or change-log comments. Noise comments. Position markers. Closing brace comments. Attributions and bylines. **Commented-out code.** HTML in comments. Nonlocal information. Too much information. Comments with no obvious link to the code. Javadoc for non-public code.

Version control remembers deleted code. Delete it.

---

## 7. Formatting (Chapter 5)

Formatting is communication. Communication is the professional's first job. Your style outlives your code.

- **File size.** Large systems can be built from files of about 200 lines, with an upper limit near 500. This is a strong preference, not a hard rule.
- **The newspaper metaphor.** The name tells you the topic. High-level concepts come first. Detail increases as you read down.
- **Vertical openness.** Separate concepts with blank lines.
- **Vertical density.** Keep closely related lines together.
- **Vertical distance.** Related concepts should stay vertically close. Declare local variables as close to their use as possible, which in a short function means the top of it. Declare loop counters inside the loop statement. Put instance variables in one known place. Keep a caller and its callee close together. Code with conceptual affinity belongs together even without a direct dependency.
- **Vertical ordering.** Call dependencies point downward. The caller goes above the callee. The reader moves from high level to detail.
- **Line width.** Prefer short lines. 80 is arbitrary, and 100 or 120 is acceptable. Beyond that is careless. The author's own limit is 120.
- **Horizontal openness.** Use spaces to show which things belong together and which do not. No space between a function name and its opening bracket. Spaces around low-precedence operators.
- **Do not align horizontally.** Column-aligned declarations point the eye at the wrong thing and break under reformatting.
- **Indentation.** Indentation shows scope. Do not collapse short `if` or `while` bodies onto one line.
- **Team rules win.** The team agrees on one style. Every member uses it. Encode it in the formatter. Your personal preference does not matter.

---

## 8. Objects and data structures (Chapter 6)

- **Hide implementation, do not just wrap it.** Adding getters and setters to every private field does not create abstraction. Expose an interface that lets callers work with the essence of the data.
- **Object and data structure are opposites.** Objects hide data and expose behaviour. Data structures expose data and have no meaningful behaviour.
- **The trade-off is real.** Procedural code makes it easy to add new functions without touching existing data structures. Object-oriented code makes it easy to add new types without touching existing functions. The opposite is hard in each case. Pick the side that matches the change you expect.
- **The Law of Demeter.** A method `f` of class `C` should call only methods of: `C` itself, objects `f` creates, objects passed to `f`, and objects held in instance variables of `C`. It should not call methods on objects returned by those calls. Talk to friends, not to strangers.
- **Avoid train wrecks.** `a.getB().getC().doSomething()` spreads knowledge of the whole object graph into one function.
- **Avoid hybrids.** A class that is half object and half data structure is the worst of both. It resists new functions and new types.
- **DTOs are fine.** A class with public fields and no behaviour is a valid data structure, useful at database and message boundaries.
- **Active Record is a data structure.** Do not put business rules in it. Put the rules in separate objects that hide the Active Record inside.

---

## 9. Error handling (Chapter 7)

Error handling is important. If it hides the logic, it is wrong.

- **Use exceptions, not return codes.** Return codes clutter every caller and are easy to forget.
- **Write the try-catch-finally block first.** A `try` block is like a transaction. Define what the caller can expect when things fail, then fill in the body.
- **Prefer unchecked exceptions.** Checked exceptions break encapsulation and violate the Open Closed Principle. A low-level change forces signature changes all the way up.
- **Provide context with exceptions.** A stack trace does not tell you intent. Say which operation failed and how.
- **Define exception classes around how callers will catch them.** Wrap a third-party API so it throws one exception type you control. This removes duplicated catch blocks and cuts your dependency on that API.
- **Define the normal flow.** Use the Special Case pattern so the client never handles the exceptional branch. Return an object that already does the right thing.
- **Do not return null.** Return an empty collection or a special case object, or throw. One missing null check breaks the system.
- **Do not pass null.** Forbid null arguments by default. Then a null in an argument list is a clear signal of a bug.

---

## 10. Boundaries (Chapter 8)

- **Do not pass third-party types around your system.** Wrap them. Keep a broad interface such as `Map` inside one class that exposes only what you need.
- **Write learning tests.** Learn a third-party API by writing tests against it. You had to learn it anyway, so the tests cost nothing extra.
- **Learning tests pay off later.** Run them against each new release of the dependency. They tell you at once when behaviour changed.
- **Write the interface you wish you had.** When the other side does not exist yet, define your own interface and keep working. Add an Adapter when the real API arrives.
- **Boundaries need seams.** The wrapper gives you one place to change and an easy point for test doubles.

---

## 11. Unit tests (Chapter 9)

### The Three Laws of TDD

1. You may not write production code until you have written a failing unit test.
2. You may not write more of a unit test than is sufficient to fail. Not compiling counts as failing.
3. You may not write more production code than is sufficient to pass the current failing test.

These laws produce a cycle of about thirty seconds.

### Rules for test code

- **Test code is as important as production code.** It is not a second-class citizen. Dirty tests are as bad as no tests, or worse. Dirty tests grow expensive, then get abandoned, and then the production code rots.
- **Tests enable the "-ilities".** Tests are what keep production code flexible, maintainable and reusable. Without tests you fear change, so you stop cleaning.
- **Readability first.** Readability matters more in tests than in production code. Say much with few expressions.
- **Build a domain-specific testing language.** Grow a set of helper functions and a `given / when / then` shape so each test reads as intent.
- **Apply a dual standard.** Test code must be clean and readable. It does not have to be as efficient as production code, because it runs in a different environment.
- **Minimise asserts per test.** One assert per test is a good guideline, not a law. Multiple asserts are acceptable.
- **One concept per test.** This rule matters more than the assert count. Split a test that checks three unrelated things.

### F.I.R.S.T.

- **Fast.** Slow tests do not get run.
- **Independent.** No test sets up another. Run them in any order.
- **Repeatable.** They run in any environment, including a laptop with no network.
- **Self-Validating.** They pass or fail. No log reading. No manual file comparison.
- **Timely.** Write the test just before the production code it covers. Tests written afterwards find untestable code.

---

## 12. Classes (Chapter 10)

- **Class organisation.** Public static constants, then private static variables, then private instance variables, then public functions. Put a private helper right below the public function that uses it, following the Stepdown Rule.
- **Encapsulation.** Keep variables and helpers private. Loosen to protected or package scope only when a test needs it, and only as a last resort.
- **Classes must be small.** Measure size in responsibilities, not lines. A class needing 70 public methods is a "God class".
- **The class name is a size test.** If you cannot derive a concise name, the class is probably too large. Weasel words such as `Processor`, `Manager` or `Super` hint at aggregated responsibilities. You should also be able to describe the class in about 25 words without using "if", "and", "or" or "but".
- **Single Responsibility Principle.** A class or module has one, and only one, reason to change.
- **Many small classes beat a few large ones.** A system of small classes has no more moving parts. It just labels the drawers.
- **Cohesion.** Keep instance variables few. Each method should use one or more of them. When cohesion falls, split the class.
- **Splitting functions leads to splitting classes.** When extracting methods pushes variables up to instance level, that group of variables and methods is usually a class waiting to appear.
- **Organise for change.** Restructure when you find yourself opening a class to change it. Do not restructure a class that is logically finished.
- **Isolate from change (Dependency Inversion Principle).** Depend on abstractions, not on concrete details. Inject the abstraction. This makes the system testable and flexible at the same time.

---

## 13. Systems (Chapter 11)

- **Separate construction from use.** Wire objects together in a startup process. Keep that separate from runtime logic. Lazy initialisation inside business code mixes two responsibilities and hard-codes a dependency.
- **Separation of main.** Build all objects in `main` or a module it calls. Pass them into the application. The application knows nothing about construction.
- **Use factories when the application must decide when to create an object.** Give the application an abstract factory, and keep the concrete factory in the construction layer.
- **Dependency injection.** An object does not resolve its own dependencies. Something else provides them.
- **Systems can grow.** You cannot get a system right the first time. Implement today's stories, then refactor and extend. Architecture can grow incrementally when concerns stay separated.
- **Separate cross-cutting concerns.** Persistence, transactions, security and logging cut across the domain. Handle them with aspects or aspect-like mechanisms, not by scattering them into every class.
- **Test-drive the architecture.** Write domain logic as plain objects with no architecture coupling. Big Design Up Front is harmful because it resists change.
- **Optimise decision making.** Delay decisions until the last responsible moment. A premature decision uses less information.
- **Use standards only when they add demonstrable value.** Do not adopt a heavy standard just because it is a standard.
- **Use a domain-specific language.** A DSL narrows the gap between a domain idea and the code that implements it.

At every level, from code to system, the modules should be simple and the intent clear.

---

## 14. Simple design (Chapter 12)

Kent Beck's four rules of simple design, in priority order:

1. **Runs all the tests.** A system you cannot verify should not be deployed. Testable design forces small, single-purpose classes and low coupling.
2. **Contains no duplication.** Duplication is the primary enemy of good design. It adds work, risk and complexity. Remove it even at three or four lines.
3. **Expresses the intent of the programmer.** Use good names. Keep functions and classes small. Use standard nomenclature such as pattern names. Write expressive tests. Most of all, try.
4. **Minimises the number of classes and methods.** Do not take rules 2 and 3 so far that you produce hundreds of trivial classes. This is the lowest priority of the four.

Rule 1 gives you the safety net. Rules 2 to 4 are what you apply during refactoring.

---

## 15. Concurrency (Chapter 13)

Concurrency is a decoupling strategy. It separates *what* gets done from *when* it gets done.

- **Apply SRP to concurrency.** Keep concurrency code separate from other code. It has its own life cycle and its own failure modes.
- **Limit the scope of data.** Take encapsulation seriously. Restrict access to any data that may be shared. Fewer critical sections means fewer places to get wrong.
- **Use copies of data.** Avoid sharing where you can. Copy, work, then merge in one thread.
- **Keep threads as independent as possible.** Each thread should work on data it does not share.
- **Know your library.** Use thread-safe collections. Use the executor framework for unrelated tasks. Prefer non-blocking solutions. Know which library classes are not thread safe.
- **Know your execution models.** Learn Producer-Consumer, Readers-Writers and Dining Philosophers, and the problems each one has.
- **Beware dependencies between synchronized methods.** Avoid calling more than one method on a shared object. If you must, use client-based locking, server-based locking, or an adapted server.
- **Keep synchronized sections small.** Locks are expensive and they create contention. Use as few critical sections as you can, and keep each one short.
- **Plan shutdown early.** Graceful shutdown is hard, and deadlock during shutdown is common. It will take longer than you expect.
- **Test threaded code hard.** Write tests that can expose problems. Run them often, on many platforms, with more threads than processors, and with varied configuration. Treat any spurious failure as a real threading defect, not as a fluke.
- **Get the non-threaded code working first.** Make threading pluggable and tunable so you can vary it without rewriting.
- **Instrument the code to force failures.** Insert jiggle points by hand or by tool, so rare interleavings appear more often.

---

## 16. Full smells and heuristics list (Chapter 17)

### Comments

- **C1 Inappropriate Information.** Do not put change history, authorship or ticket metadata in comments. That belongs in other systems.
- **C2 Obsolete Comment.** An old, wrong or irrelevant comment. Update it or delete it.
- **C3 Redundant Comment.** It says what the code already says. `i++; // increment i`.
- **C4 Poorly Written Comment.** If it is worth writing, write it well. Be brief and correct.
- **C5 Commented-Out Code.** Delete it. Version control remembers it.

### Environment

- **E1 Build Requires More Than One Step.** One command to check out. One command to build.
- **E2 Tests Require More Than One Step.** One command, or one button, runs every test.

### Functions

- **F1 Too Many Arguments.** None is best, then one, two, three. More than three is very questionable.
- **F2 Output Arguments.** Counter-intuitive. Change the state of the object the method is called on.
- **F3 Flag Arguments.** A boolean argument says the function does more than one thing. Remove it.
- **F4 Dead Function.** A method nobody calls. Delete it.

### General

- **G1 Multiple Languages in One Source File.** Minimise the number of languages per file. Ideally one.
- **G2 Obvious Behaviour Is Unimplemented.** Follow the Principle of Least Surprise. Implement what a reader would reasonably expect.
- **G3 Incorrect Behaviour at the Boundaries.** Do not trust intuition about corner cases. Prove them with tests.
- **G4 Overridden Safeties.** Turning off compiler warnings or ignoring failing tests is risky.
- **G5 Duplication.** One of the most important rules in the book. Find every form of it and remove it.
- **G6 Code at Wrong Level of Abstraction.** Keep high-level concepts and low-level details fully separated.
- **G7 Base Classes Depending on Their Derivatives.** A base class should know nothing about its subclasses.
- **G8 Too Much Information.** A well-defined module has a small interface. Expose little, couple less.
- **G9 Dead Code.** Code that never executes. Delete it, or it drifts out of date and misleads.
- **G10 Vertical Separation.** Declare variables and private functions close to where they are used.
- **G11 Inconsistency.** Do similar things the same way, every time.
- **G12 Clutter.** Empty default constructors, unused variables, meaningless comments. Remove them.
- **G13 Artificial Coupling.** Do not put a general concept inside a specific class.
- **G14 Feature Envy.** A method that manipulates another object's data through accessors belongs in that other class.
- **G15 Selector Arguments.** A dangling `false` at the end of a call. Split the function instead.
- **G16 Obscured Intent.** Dense expressions, magic numbers and encodings hide meaning.
- **G17 Misplaced Responsibility.** Put code where a reader expects to find it.
- **G18 Inappropriate Static.** If a function might ever need to be polymorphic, do not make it static.
- **G19 Use Explanatory Variables.** Break a calculation into named intermediate values.
- **G20 Function Names Should Say What They Do.** If you must read the implementation to know what the call does, the name is wrong.
- **G21 Understand the Algorithm.** Understand the solution. Do not tune `if` statements until the tests pass.
- **G22 Make Logical Dependencies Physical.** Do not assume something about another module. Ask that module for it.
- **G23 Prefer Polymorphism to If/Else or Switch/Case.** Consider polymorphism first. Follow the "one switch" rule.
- **G24 Follow Standard Conventions.** The team has a coding standard. Everyone follows it. The code is the documentation of it.
- **G25 Replace Magic Numbers with Named Constants.** Hide `86400` behind `SECONDS_PER_DAY`. This also applies to strings and other literals.
- **G26 Be Precise.** Do not use floating point for money. Do not skip a null check. Do not assume a query returns one row.
- **G27 Structure over Convention.** A structure that enforces a decision beats a naming convention that only suggests it.
- **G28 Encapsulate Conditionals.** `if (shouldBeDeleted(timer))` beats a compound boolean expression.
- **G29 Avoid Negative Conditionals.** Positives are easier to read.
- **G30 Functions Should Do One Thing.** A function with several sequential sections should become several functions.
- **G31 Hidden Temporal Couplings.** If calls must happen in order, structure the arguments so the order is forced and visible.
- **G32 Do Not Be Arbitrary.** Have a reason for your structure, and let the structure show that reason.
- **G33 Encapsulate Boundary Conditions.** Do not scatter `+1` and `-1`. Name the boundary value once.
- **G34 Functions Should Descend Only One Level of Abstraction.** Every statement sits one level below the function name.
- **G35 Keep Configurable Data at High Levels.** Do not bury a default value in a low-level function. Pass it down from the top.
- **G36 Avoid Transitive Navigation.** If A uses B and B uses C, users of A should not know about C. This is the Law of Demeter again.

### Java-specific

- **J1 Avoid Long Import Lists by Using Wildcards.** Import the package when you use two or more classes from it.
- **J2 Do Not Inherit Constants.** Do not hide constants in an interface and inherit them. Use a static import or an enum.
- **J3 Constants versus Enums.** Use enums, not `public static final int`. Enums carry meaning, methods and fields.

### Names

- **N1 Choose Descriptive Names.** Names are 90 percent of what makes software readable. Re-evaluate them as meanings drift.
- **N2 Choose Names at the Appropriate Level of Abstraction.** Do not name for the implementation.
- **N3 Use Standard Nomenclature Where Possible.** Use pattern names and language conventions such as `toString`.
- **N4 Unambiguous Names.** The name must say what the function or variable does, not roughly gesture at it.
- **N5 Use Long Names for Long Scopes.** `i` is fine in a five-line loop. It is not fine across a class.
- **N6 Avoid Encodings.** No type prefixes, no scope prefixes, no subsystem prefixes.
- **N7 Names Should Describe Side-Effects.** A `getX` that also creates X should say so, for example `createOrReturnX`.

### Tests

- **T1 Insufficient Tests.** Test everything that could possibly break.
- **T2 Use a Coverage Tool.** It shows the gaps quickly.
- **T3 Do Not Skip Trivial Tests.** They are cheap and they document.
- **T4 An Ignored Test Is a Question about an Ambiguity.** Express an unclear requirement as an ignored test.
- **T5 Test Boundary Conditions.** People get the middle right and the edges wrong.
- **T6 Exhaustively Test Near Bugs.** Bugs cluster. When you find one, test that function hard.
- **T7 Patterns of Failure Are Revealing.** The shape of the red and green output can point at the cause.
- **T8 Test Coverage Patterns Can Be Revealing.** Look at what the passing tests do and do not execute.
- **T9 Tests Should Be Fast.** A slow test gets dropped when time is tight.

---

## 17. Limits and caveats

The book states these itself. Keep them in view.

- **This is one school of thought.** The author calls it "the Object Mentor School of Clean Code" and says other schools have equal claim to professionalism. He also expects readers to disagree with some rules.
- **The rules are not the goal.** Chapter 17 ends by saying the heuristic list implies a value system, and that you do not become a craftsman by learning a list. Values drive disciplines. The list is a symptom of the values, not a replacement for them.
- **The numbers are preferences, not measurements.** The author says outright that he cannot cite research showing small functions are better. The size limits come from experience.
- **The context is Java in 2009.** Some items are dated: `J1` on wildcard imports, `J3` on enums, checked exceptions, and the assumption that the IDE colours member variables. Translate the intent, not the syntax.
- **Some rules pull against each other.** Rule 4 of simple design (minimise classes and methods) limits rules 2 and 3. "Small classes" fights "minimal class count". The book expects judgement, not mechanical application.
- **The list is not complete.** The author says a complete list may not be possible.

---

## How to use this doc with agents

- Cite rules by code when you review. "This breaks G30 and F3" is checkable. "This is not clean" is not.
- Section 1 is a good short brief for an implementer agent. Section 16 is a good checklist for a reviewer agent.
- Always pair a finding with the concrete change it implies. The book's rules describe transformations, not verdicts.
- Do not treat section 16 as a lint config. Section 17 explains why.
