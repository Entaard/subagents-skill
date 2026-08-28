# General ideas

- The sage's cortex is still too big. Check if anything else can be made into KIs.
- Change to sage experiment idea. Not "experiment", but more like "exploration". If a task allows (e.g. non editing, non orchestrating), spawn one
    or more agents using different models than the initial plan. This is to:
    - Cover a plan's inaccuracy. A plan can never be accurate, because a model may sometimes produce much better results than expected. For example,
        a Sonnet verifier may find 4 noisy bugs, but 1 real bug that an Opus verifier misses. By the book, the sage may always summon an Opus verifier
        for the task, thus can miss the one bug.
    - Gain more experiences in unexpected areas: if the sage always carries out its own plan, it will always learn around that. Explorations like this
        help the sage to see out of its course.
- To avoid the exploration plan to be to unpredictable, should be as follow:
    - Always spawn lower tier model agents, with +1 quantity. For example, if the initial plan summons 1 Opus verifier, the exploration adds 2 Sonnet
        verifiers.
    - If the task already uses the lowest tier, don't do exploration.
    - If the task already uses many subagents with different models, don't do exploration.
