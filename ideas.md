
- Introduce "experiment" behavior for the sage. Beside the normal plan, the sage might dispatch additional agents with unscripted models, for example,
    using Fable as an extra verifier; or using Haiku or lower-tier alt model (gpt 5.6 luna) as an extra verifier; etc. This is to explore the capabilities
    of models usages and allocations, in search of valuable allocations that are never published by Anthropic or OpenAI or orther AI companies. Real
    example, my colleague claimed that in one session, gpt 5.6 luna max effort was able to find 30 genuine problems from a plan written by Fable.
    - One catch for the experiment though, I don't think the sage should experiment on lowering the model tier of the orchestration agent (the sage successors).
    Same case for the implementer agents - haiku or gpt 5.6 luna shouldn't be used for it, I think.
- Does sage have the explore - plan - implement - verify loop?
- Continue working with the sage in the same session?
- I feel sage is more costly than the previous version of subagents. What are the most costly steps and flows?
- Roughly how is sage's performance vs subagents?
- Do the sage and subagents skills use the alt agents when the alt agents are available?

