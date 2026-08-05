# Evidence menu: game development

Moved out of the `subagents` skill (`references/patterns.md`) on 2026-08-05. The skill's own note
said engine-specific material belongs in a project-level reference, and the block was violating it —
every invocation paid for domain content most tasks never use.

Drop this file into a game project (e.g. `.claude/` or alongside the project's `CLAUDE.md`) and point
at it from there. It is not loaded by the skill.

## Acceptance evidence

A playable scene or checkpoint per increment; expected player-visible behavior stated up front;
frame-time and memory budgets where relevant; screenshots or captures for visual work; input and
edge-case checks; debug overlays for state that is otherwise hard to observe.

## Criterion classification

Mark each criterion **machine-verifiable / agent-observable-but-subjective / human-only**. Agents may
prepare playtest checklists and captures. *Game feel, pacing, and fun are human-only* — a phase can
be technically complete while explicitly awaiting a human playtest, and the report should say so
rather than let a green reviewer imply otherwise.

(The classification rule itself stayed in the skill; it is domain-general. This file keeps the
game-specific reading of it.)

## Engine-specific review lenses

Per-engine lenses — Godot node lifecycle, signal connection and disconnection, resource ownership and
`preload` vs `load`, scene instancing cost — belong with the project that uses that engine, not in a
generic orchestration skill. Add them here, scoped to the engine actually in use.
