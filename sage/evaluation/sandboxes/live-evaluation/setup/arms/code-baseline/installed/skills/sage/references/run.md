# Run and state

Read this for every new persisted run. Use the source helper at `sage/scripts/sage_state.py` when operating in this repository. After installation, use `<target-root>/sage/bin/sage_state.py`. Resolve the path explicitly; never infer a state root from the task repository. Use the installation's configured state root; absent an override, resolve the standard `~/.codex/sage` directory to an absolute path and state it before access. The later installer owns `<target-root>/skills/{sage,sage-promote}` and `<target-root>/sage/bin/{sage_state.py,sage_knowledge.py}`; source-tree success is not installed integration.

## Shape the outcome

Define each criterion as an observable outcome and add the excellence conditions that distinguish a merely valid artifact from an excellent one. Choose evidence by situation:

- Software: requested behavior, regression protection, relevant quality constraints, and maintainable integration.
- Research/evidence/data: source authority and recency, traceable claims, counterevidence, uncertainty, and reproducible transformations.
- Writing/design: audience fit, argument or visual hierarchy, coherence, finish, and delivery-format fidelity.
- UI/interactive/game: real flows and inputs, visual/usability behavior, error states, scoped performance, and platform/viewports. Compilation alone is not experience evidence.

Stage a large outcome into dependency-ordered milestones without shrinking its declared target. Report milestones not built or observed as unsupported scope.

## Plan and record

Use a compact graph. Every task records the frozen fields in `docs/CONTRACTS.md`: stable ID/revision, objective, falsifiable completion, dependencies, owner, effect/scope, inputs/returns, risk, verification, requested model/effort, and fork. Commit finite, task-specific attempt and revision allowances plus a no-progress condition. A retry records the unmet criterion, evidence, failure cause, and strategy change. Never use an automatic model ladder after a retry count.

Prefer `init`, batched `append`, and boundary `snapshot` calls. Example tiny run:

```text
python3 SAGE_STATE init --run-dir RUN --run-id ID --objective TEXT --criteria criteria.json
python3 SAGE_STATE append --run-dir RUN --events wave.jsonl
python3 SAGE_STATE snapshot --run-dir RUN --write
python3 SAGE_STATE validate --run-dir RUN --terminal
python3 SAGE_STATE report --run-dir RUN --write
```

`events.jsonl` is append-only authority. Prepare a complete JSONL wave and let `append` validate the whole proposed history before atomic replacement. `snapshot.json` is a hash-bound projection; `report.md` is derived. Persist large or confidential evidence by scoped locator/hash and classification, never by copying credentials or capability secrets.

Checkpoint after plan commitment, before and after a delegation wave, before a risky effect, after integration, after fixes, and on host compaction/context warnings. Boundary checkpoints replace imaginary token percentages.

For the installed event fields, executable example, and error behavior, read [state contract](state.md). Source builders may also consult `sage/docs/CONTRACTS.md`, which remains the frozen verification authority. CLI exit `2` means contract/data rejection; exit `3` means unexpected I/O failure.
