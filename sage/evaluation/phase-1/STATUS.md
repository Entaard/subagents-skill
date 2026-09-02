# Phase 1 pilot status

Status: **blocked before outcomes** on Codex CLI 0.151.0 (checked 2026-09-01).

The frozen start gate requires one hard 250,000-token cap in the same normalized input-plus-output unit for the complete control or treatment arm. The pinned experimental App Server schema exposes `inputTokens`, `outputTokens`, `totalTokens`, and `modelContextWindow`. It also exposes an unqualified integer `ThreadGoal.tokenBudget`. The schema does not bind that budget to normalized input-plus-output accounting, hard enforcement, or aggregate root-and-subagent arm scope. Therefore it is not valid evidence for the frozen cap.

The schema also supplies only the context-window denominator, not a supported current occupied-context numerator. That makes the context-benefit metric unavailable; unlike normalized spend, this alone is not a start blocker.

RL-01 additionally requires an external pinned driver that can force a native start branch, kill and restart the root at the declared boundary, and hide its oracle until the recovery terminal is durable. The in-session Light collaboration surface does not provide that driver boundary. A prose or simulated substitute is explicitly invalid under the frozen fixture.

`pilot.py preflight` regenerates and inspects the local schema, verifies all frozen hashes and baseline corpus paths, hashes the completed treatment and evaluation components, and emits the exact failed gates. `pilot.py run` exits before producing an arm outcome whenever any start gate is failed. No paired task, score, causal label, rerun, or decision-gate result has been fabricated.

Re-run when a pinned harness provides both missing controls:

```text
python3 sage/evaluation/phase-1/pilot.py preflight --output /tmp/sage-phase1-preflight.json
python3 sage/evaluation/phase-1/pilot.py run --output /tmp/sage-phase1-run-gate.json
```
